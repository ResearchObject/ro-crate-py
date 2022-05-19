#!/usr/bin/env python

# Copyright 2019-2022 The University of Manchester, UK
# Copyright 2020-2022 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2022 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2022 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022 École Polytechnique Fédérale de Lausanne, CH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import json
import uuid
import zipfile
import atexit
import shutil
import tempfile
import warnings

from collections import OrderedDict
from pathlib import Path
from urllib.parse import urljoin

from .model.contextentity import ContextEntity
from .model.entity import Entity
from .model.root_dataset import RootDataset
from .model.data_entity import DataEntity
from .model.file_or_dir import FileOrDir
from .model.file import File
from .model.dataset import Dataset
from .model.metadata import WORKFLOW_PROFILE, Metadata, LegacyMetadata, TESTING_EXTRA_TERMS, metadata_class
from .model.preview import Preview
from .model.testdefinition import TestDefinition
from .model.computationalworkflow import ComputationalWorkflow, WorkflowDescription, galaxy_to_abstract_cwl
from .model.computerlanguage import ComputerLanguage, get_lang
from .model.testinstance import TestInstance
from .model.testservice import TestService, get_service
from .model.softwareapplication import SoftwareApplication, get_app, PLANEMO_DEFAULT_VERSION
from .model.testsuite import TestSuite

from .utils import is_url, subclasses, get_norm_value, walk


def read_metadata(metadata_path):
    """\
    Read an RO-Crate metadata file.

    Return a tuple of two elements: the context; a dictionary that maps entity
    ids to the entities themselves.
    """
    with open(metadata_path) as f:
        metadata = json.load(f)
    try:
        context = metadata['@context']
        graph = metadata['@graph']
    except KeyError:
        raise ValueError(f"{metadata_path} must have a @context and a @graph")
    return context, {_["@id"]: _ for _ in graph}


def pick_type(json_entity, type_map, fallback=None):
    try:
        t = json_entity["@type"]
    except KeyError:
        raise ValueError(f'entity {json_entity["@id"]!r} has no @type')
    types = {_.strip() for _ in set(t if isinstance(t, list) else [t])}
    for name, c in type_map.items():
        if name in types:
            return c
    return fallback


class ROCrate():

    def __init__(self, source=None, gen_preview=False, init=False, exclude=None):
        self.exclude = exclude
        self.__entity_map = {}
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        # TODO: add this as @base in the context? At least when loading
        # from zip
        self.uuid = uuid.uuid4()
        self.arcp_base_uri = f"arcp://uuid,{self.uuid}/"
        self.preview = None
        if gen_preview:
            self.add(Preview(self))
        if not source:
            # create a new ro-crate
            self.add(RootDataset(self), Metadata(self))
        elif init:
            self.__init_from_tree(source, gen_preview=gen_preview)
        else:
            source = self.__read(source, gen_preview=gen_preview)
        # in the zip case, self.source is the extracted dir
        self.source = source

    def __init_from_tree(self, top_dir, gen_preview=False):
        top_dir = Path(top_dir)
        if not top_dir.is_dir():
            raise NotADirectoryError(errno.ENOTDIR, f"'{top_dir}': not a directory")
        self.add(RootDataset(self), Metadata(self))
        for root, dirs, files in walk(top_dir, exclude=self.exclude):
            root = Path(root)
            for name in dirs:
                source = root / name
                self.add_dataset(source, source.relative_to(top_dir))
            for name in files:
                source = root / name
                if source == top_dir / Metadata.BASENAME or source == top_dir / LegacyMetadata.BASENAME:
                    continue
                if source != top_dir / Preview.BASENAME:
                    self.add_file(source, source.relative_to(top_dir))
                elif not gen_preview:
                    self.add(Preview(self, source))

    def __read(self, source, gen_preview=False):
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(errno.ENOENT, f"'{source}' not found")
        if zipfile.is_zipfile(source):
            zip_path = tempfile.mkdtemp(prefix="rocrate_")
            atexit.register(shutil.rmtree, zip_path)
            with zipfile.ZipFile(source, "r") as zf:
                zf.extractall(zip_path)
            source = Path(zip_path)
        metadata_path = source / Metadata.BASENAME
        if not metadata_path.is_file():
            metadata_path = source / LegacyMetadata.BASENAME
        if not metadata_path.is_file():
            raise ValueError(f"Not a valid RO-Crate: missing {Metadata.BASENAME}")
        _, entities = read_metadata(metadata_path)
        self.__read_data_entities(entities, source, gen_preview)
        self.__read_contextual_entities(entities)
        self.__resolve_references()
        return source

    def __resolve_references(self):
        for cid, entity in self.__entity_map.items():
            for k, v in entity.items():
                if v is None or k.startswith("@"):
                    continue
                values = v if isinstance(v, list) else [v]
                deref_values = []
                for entry in values:
                    if isinstance(entry, dict):
                        try:
                            id_ = entry["@id"]
                        except KeyError:
                            raise ValueError(f"no @id in {entry}")
                        else:
                            deref_values.append(self.get(id_, Entity(self, id_)))
                    else:
                        deref_values.append(entry)
                entity[k] = deref_values if isinstance(v, list) else deref_values[0]

    def __check_metadata(self, metadata, entities):
        if metadata["@type"] != "CreativeWork":
            raise ValueError('metadata descriptor must be of type "CreativeWork"')
        try:
            root = entities[metadata["about"]["@id"]]
        except (KeyError, TypeError):
            raise ValueError("metadata descriptor does not reference the root entity")
        if ("Dataset" not in root["@type"] if isinstance(root["@type"], list) else root["@type"] != "Dataset"):
            raise ValueError('root entity must have "Dataset" among its types')
        return metadata["@id"], root["@id"]

    def find_root_entity_id(self, entities):
        """\
        Find metadata file descriptor and root data entity.

        Return a tuple of the corresponding identifiers (metadata, root).
        If the entities are not found, raise KeyError. If they are found,
        but they don't satisfy the required constraints, raise ValueError.

        In the general case, the metadata file descriptor id can be an
        absolute URI whose last path segment is "ro-crate-metadata.json[ld]".
        Since there can be more than one such id in the crate, we need to
        choose among the corresponding (metadata, root) entity pairs. First, we
        exclude those that don't satisfy other constraints, such as the
        metadata entity being of type CreativeWork, etc.; if this doesn't
        leave us with a single pair, we try to pick one with a
        heuristic. Suppose we are left with the (m1, r1) and (m2, r2) pairs:
        if r1 is the actual root of this crate, then m2 and r2 are regular
        files in it, and as such they must appear in r1's hasPart; r2,
        however, is not required to have a hasPart property listing other
        files. Thus, we look for a pair whose root entity "contains" all
        metadata entities from other pairs. If there is no such pair, or there
        is more than one, we just return an arbitrary pair.
        """
        metadata = entities.get(Metadata.BASENAME, entities.get(LegacyMetadata.BASENAME))
        if metadata:
            return self.__check_metadata(metadata, entities)
        candidates = []
        for id_, e in entities.items():
            basename = id_.rsplit("/", 1)[-1]
            if basename == Metadata.BASENAME or basename == LegacyMetadata.BASENAME:
                try:
                    candidates.append(self.__check_metadata(e, entities))
                except ValueError:
                    pass
        if not candidates:
            raise KeyError("Metadata file descriptor not found")
        elif len(candidates) == 1:
            return candidates[0]
        else:
            warnings.warn("Multiple metadata file descriptors, will pick one with a heuristic")
            metadata_ids = set(_[0] for _ in candidates)
            for m_id, r_id in candidates:
                try:
                    root = entities[r_id]
                    part_ids = set(_["@id"] for _ in root["hasPart"])
                except KeyError:
                    continue
                if part_ids >= metadata_ids - {m_id}:
                    # if True for more than one candidate, this pick is arbitrary
                    return m_id, r_id
            return candidates[0]  # fall back to arbitrary pick

    def __read_data_entities(self, entities, source, gen_preview):
        metadata_id, root_id = self.find_root_entity_id(entities)
        MetadataClass = metadata_class(metadata_id)
        metadata_properties = entities.pop(metadata_id)
        self.add(MetadataClass(self, metadata_id, properties=metadata_properties))

        root_entity = entities.pop(root_id)
        assert root_id == root_entity.pop('@id')
        parts = root_entity.pop('hasPart', [])
        self.add(RootDataset(self, root_id, properties=root_entity))
        preview_entity = entities.pop(Preview.BASENAME, None)
        if preview_entity and not gen_preview:
            self.add(Preview(self, source / Preview.BASENAME, properties=preview_entity))
        type_map = OrderedDict((_.__name__, _) for _ in subclasses(FileOrDir))
        for data_entity_ref in parts:
            id_ = data_entity_ref['@id']
            entity = entities.pop(id_)
            assert id_ == entity.pop('@id')
            cls = pick_type(entity, type_map, fallback=DataEntity)
            if cls is DataEntity:
                instance = DataEntity(self, identifier=id_, properties=entity)
            else:
                if is_url(id_):
                    instance = cls(self, id_, properties=entity)
                else:
                    instance = cls(self, source / id_, id_, properties=entity)
            self.add(instance)

    def __read_contextual_entities(self, entities):
        type_map = {_.__name__: _ for _ in subclasses(ContextEntity)}
        for identifier, entity in entities.items():
            assert identifier == entity.pop('@id')
            cls = pick_type(entity, type_map, fallback=ContextEntity)
            self.add(cls(self, identifier, entity))

    @property
    def name(self):
        return self.root_dataset.get('name')

    @name.setter
    def name(self, value):
        self.root_dataset['name'] = value

    @property
    def datePublished(self):
        return self.root_dataset.datePublished

    @datePublished.setter
    def datePublished(self, value):
        self.root_dataset.datePublished = value

    @property
    def creator(self):
        return self.root_dataset.get('creator')

    @creator.setter
    def creator(self, value):
        self.root_dataset['creator'] = value

    @property
    def license(self):
        return self.root_dataset.get('license')

    @license.setter
    def license(self, value):
        self.root_dataset['license'] = value

    @property
    def description(self):
        return self.root_dataset.get('description')

    @description.setter
    def description(self, value):
        self.root_dataset['description'] = value

    @property
    def keywords(self):
        return self.root_dataset.get('keywords')

    @keywords.setter
    def keywords(self, value):
        self.root_dataset['keywords'] = value

    @property
    def publisher(self):
        return self.root_dataset.get('publisher')

    @publisher.setter
    def publisher(self, value):
        self.root_dataset['publisher'] = value

    @property
    def isBasedOn(self):
        return self.root_dataset.get('isBasedOn')

    @isBasedOn.setter
    def isBasedOn(self, value):
        self.root_dataset['isBasedOn'] = value

    @property
    def image(self):
        return self.root_dataset.get('image')

    @image.setter
    def image(self, value):
        self.root_dataset['image'] = value

    @property
    def CreativeWorkStatus(self):
        return self.root_dataset.get('CreativeWorkStatus')

    @CreativeWorkStatus.setter
    def CreativeWorkStatus(self, value):
        self.root_dataset['CreativeWorkStatus'] = value

    @property
    def mainEntity(self):
        return self.root_dataset.get('mainEntity')

    @mainEntity.setter
    def mainEntity(self, value):
        self.root_dataset['mainEntity'] = value

    @property
    def test_dir(self):
        rval = self.dereference("test")
        if rval and "Dataset" in rval.type:
            return rval
        return None

    @property
    def examples_dir(self):
        rval = self.dereference("examples")
        if rval and "Dataset" in rval.type:
            return rval
        return None

    @property
    def test_suites(self):
        mentions = [_ for _ in self.root_dataset.get('mentions', []) if isinstance(_, TestSuite)]
        about = [_ for _ in self.root_dataset.get('about', []) if isinstance(_, TestSuite)]
        if self.test_dir:
            legacy_about = [_ for _ in self.test_dir.get('about', []) if isinstance(_, TestSuite)]
            about += legacy_about
        return list(set(mentions + about))  # remove any duplicate refs

    def resolve_id(self, id_):
        if not is_url(id_):
            id_ = urljoin(self.arcp_base_uri, id_)  # also does path normalization
        return id_.rstrip("/")

    def get_entities(self):
        return self.__entity_map.values()

    def dereference(self, entity_id, default=None):
        canonical_id = self.resolve_id(entity_id)
        return self.__entity_map.get(canonical_id, default)

    get = dereference

    def add_file(
            self,
            source=None,
            dest_path=None,
            fetch_remote=False,
            validate_url=False,
            properties=None
    ):
        return self.add(File(
            self,
            source=source,
            dest_path=dest_path,
            fetch_remote=fetch_remote,
            validate_url=validate_url,
            properties=properties
        ))

    def add_dataset(
            self,
            source=None,
            dest_path=None,
            fetch_remote=False,
            validate_url=False,
            properties=None
    ):
        return self.add(Dataset(
            self,
            source=source,
            dest_path=dest_path,
            fetch_remote=fetch_remote,
            validate_url=validate_url,
            properties=properties
        ))

    add_directory = add_dataset

    def add(self, *entities):
        """\
        Add one or more entities to this RO-Crate.

        If an entity with the same (canonical) id is already present in the
        crate, it will be replaced (as in Python dictionaries).

        Note that, according to the specs, "The RO-Crate Metadata JSON @graph
        MUST NOT list multiple entities with the same @id; behaviour of
        consumers of an RO-Crate encountering multiple entities with the same
        @id is undefined". In practice, due to the replacement semantics, the
        entity for a given id is the last one added to the crate with that id.
        """
        for e in entities:
            key = e.canonical_id()
            if isinstance(e, RootDataset):
                self.root_dataset = e
            if isinstance(e, (Metadata, LegacyMetadata)):
                self.metadata = e
            if isinstance(e, Preview):
                self.preview = e
            if isinstance(e, (RootDataset, Metadata, LegacyMetadata, Preview)):
                self.default_entities.append(e)
            elif hasattr(e, "write"):
                self.data_entities.append(e)
                parts = self.root_dataset.setdefault("hasPart", [])
                old_e = self.__entity_map.get(key)
                if old_e:
                    # FIXME: this is not efficient
                    try:
                        del parts[parts.index(old_e)]
                    except ValueError:
                        pass
                parts.append(e)
            else:
                self.contextual_entities.append(e)
            self.__entity_map[key] = e
        return entities[0] if len(entities) == 1 else entities

    def delete(self, *entities):
        """\
        Delete one or more entities from this RO-Crate.

        Note that the crate could be left in an inconsistent state as a result
        of calling this method, since neither entities pointing to the deleted
        ones nor entities pointed to by the deleted ones are modified.
        """
        for e in entities:
            if not isinstance(e, Entity):
                e = self.dereference(e)
            if not e:
                continue
            if e is self.root_dataset:
                raise ValueError("cannot delete the root data entity")
            if e is self.metadata:
                raise ValueError("cannot delete the metadata entity")
            if e is self.preview:
                self.default_entities.remove(e)
                self.preview = None
            elif hasattr(e, "write"):
                try:
                    self.data_entities.remove(e)
                except ValueError:
                    pass
                self.root_dataset["hasPart"] = [_ for _ in self.root_dataset.get("hasPart", []) if _ != e]
                if not self.root_dataset["hasPart"]:
                    del self.root_dataset["hasPart"]
            else:
                try:
                    self.contextual_entities.remove(e)
                except ValueError:
                    pass
            self.__entity_map.pop(e.canonical_id(), None)

    # TODO
    # def fetch_all(self):
        # fetch all files defined in the crate

    def _copy_unlisted(self, top, base_path):
        for root, dirs, files in walk(top, exclude=self.exclude):
            root = Path(root)
            for name in dirs:
                source = root / name
                dest = base_path / source.relative_to(top)
                dest.mkdir(parents=True, exist_ok=True)
            for name in files:
                source = root / name
                rel = source.relative_to(top)
                if not self.dereference(str(rel)):
                    dest = base_path / rel
                    if not dest.exists() or not dest.samefile(source):
                        shutil.copyfile(source, dest)

    def write(self, base_path):
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        if self.source:
            self._copy_unlisted(self.source, base_path)
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write(base_path)

    write_crate = write  # backwards compatibility

    def write_zip(self, out_path):
        out_path = Path(out_path)
        if out_path.suffix == ".zip":
            out_path = out_path.parent / out_path.stem
        tmp_dir = tempfile.mkdtemp(prefix="rocrate_")
        try:
            self.write(tmp_dir)
            archive = shutil.make_archive(out_path, "zip", tmp_dir)
        finally:
            shutil.rmtree(tmp_dir)
        return archive

    def add_workflow(
            self, source=None, dest_path=None, fetch_remote=False, validate_url=False, properties=None,
            main=False, lang="cwl", lang_version=None, gen_cwl=False, cls=ComputationalWorkflow
    ):
        workflow = self.add(cls(
            self, source=source, dest_path=dest_path, fetch_remote=fetch_remote,
            validate_url=validate_url, properties=properties
        ))
        if isinstance(lang, ComputerLanguage):
            assert lang.crate is self
        else:
            kwargs = {"version": lang_version} if lang_version else {}
            lang = get_lang(self, lang, **kwargs)
            self.add(lang)
        lang_str = lang.id.rsplit("#", 1)[1]
        workflow.lang = lang
        if main:
            self.mainEntity = workflow
            profiles = set(_.rstrip("/") for _ in get_norm_value(self.metadata, "conformsTo"))
            profiles.add(WORKFLOW_PROFILE)
            self.metadata["conformsTo"] = [{"@id": _} for _ in sorted(profiles)]
        if gen_cwl and lang_str != "cwl":
            if lang_str != "galaxy":
                raise ValueError(f"conversion from {lang.name} to abstract CWL not supported")
            cwl_source = galaxy_to_abstract_cwl(source)
            cwl_dest_path = Path(source).with_suffix(".cwl").name
            cwl_workflow = self.add_workflow(
                source=cwl_source, dest_path=cwl_dest_path, fetch_remote=fetch_remote, properties=properties,
                main=False, lang="cwl", gen_cwl=False, cls=WorkflowDescription
            )
            workflow.subjectOf = cwl_workflow
        return workflow

    def add_test_suite(self, identifier=None, name=None, main_entity=None):
        test_ref_prop = "mentions"
        if not main_entity:
            main_entity = self.mainEntity
            if not main_entity:
                test_ref_prop = "about"
        suite = self.add(TestSuite(self, identifier))
        suite.name = name or suite.id.lstrip("#")
        if main_entity:
            suite["mainEntity"] = main_entity
        suite_set = set(self.test_suites)
        suite_set.add(suite)
        self.root_dataset[test_ref_prop] = list(suite_set)
        self.metadata.extra_terms.update(TESTING_EXTRA_TERMS)
        return suite

    def add_test_instance(self, suite, url, resource="", service="jenkins", identifier=None, name=None):
        suite = self.__validate_suite(suite)
        instance = self.add(TestInstance(self, identifier))
        instance.url = url
        instance.resource = resource
        if isinstance(service, TestService):
            assert service.crate is self
        else:
            service = get_service(self, service)
            self.add(service)
        instance.service = service
        instance.name = name or instance.id.lstrip("#")
        instance_set = set(suite.instance or [])
        instance_set.add(instance)
        suite.instance = list(instance_set)
        self.metadata.extra_terms.update(TESTING_EXTRA_TERMS)
        return instance

    def add_test_definition(
            self, suite, source=None, dest_path=None, fetch_remote=False, validate_url=False, properties=None,
            engine="planemo", engine_version=None
    ):
        if engine_version is None:
            # FIXME: this should be engine-specific
            engine_version = PLANEMO_DEFAULT_VERSION
        suite = self.__validate_suite(suite)
        definition = self.add(
            TestDefinition(self, source=source, dest_path=dest_path, fetch_remote=fetch_remote,
                           validate_url=validate_url, properties=properties)
        )
        if isinstance(engine, SoftwareApplication):
            assert engine.crate is self
        else:
            engine = get_app(self, engine)
            self.add(engine)
        definition.engine = engine
        definition.engineVersion = engine_version
        suite.definition = definition
        self.metadata.extra_terms.update(TESTING_EXTRA_TERMS)
        return definition

    def __validate_suite(self, suite):
        if isinstance(suite, TestSuite):
            assert suite.crate is self
        else:
            suite = self.dereference(suite)
            if suite is None:
                raise ValueError("suite not found")
        return suite
