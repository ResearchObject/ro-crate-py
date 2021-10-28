#!/usr/bin/env python

# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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
import os
import uuid
import zipfile
import atexit
import shutil
import tempfile

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
from .model.metadata import Metadata, LegacyMetadata, TESTING_EXTRA_TERMS
from .model.preview import Preview
from .model.testdefinition import TestDefinition
from .model.computationalworkflow import ComputationalWorkflow, galaxy_to_abstract_cwl
from .model.computerlanguage import ComputerLanguage, get_lang
from .model.testinstance import TestInstance
from .model.testservice import TestService, get_service
from .model.softwareapplication import SoftwareApplication, get_app, PLANEMO_DEFAULT_VERSION
from .model.testsuite import TestSuite

from .utils import is_url, subclasses


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


class ROCrate():

    def __init__(self, source=None, gen_preview=False, init=False):
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
        for root, dirs, files in os.walk(top_dir):
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
        MetadataClass = Metadata
        if not metadata_path.is_file():
            metadata_path = source / LegacyMetadata.BASENAME
            MetadataClass = LegacyMetadata
        if not metadata_path.is_file():
            raise ValueError(f"Not a valid RO-Crate: missing {Metadata.BASENAME}")
        self.add(MetadataClass(self))
        _, entities = read_metadata(metadata_path)
        self.__read_data_entities(entities, source, gen_preview)
        self.__read_contextual_entities(entities)
        return source

    def find_root_entity_id(self, entities):
        """Find Metadata file and Root Data Entity in RO-Crate.

        Returns a tuple of the @id identifiers (metadata, root)
        """
        # Note that for all cases below we will deliberately
        # throw KeyError if "about" exists but it has no "@id"

        # First let's try conformsTo algorithm in
        # <https://www.researchobject.org/ro-crate/1.1/root-data-entity.html#finding-the-root-data-entity>
        for entity in entities.values():
            conformsTo = entity.get("conformsTo")
            if conformsTo and "@id" in conformsTo:
                conformsTo = conformsTo["@id"]
            if conformsTo and conformsTo.startswith("https://w3id.org/ro/crate/"):
                if "about" in entity:
                    return (entity["@id"], entity["about"]["@id"])
        # ..fall back to a generous look up by filename,
        for candidate in (
                Metadata.BASENAME, LegacyMetadata.BASENAME,
                f"./{Metadata.BASENAME}", f"./{LegacyMetadata.BASENAME}"
        ):
            metadata_file = entities.get(candidate)
            if metadata_file and "about" in metadata_file:
                return (metadata_file["@id"], metadata_file["about"]["@id"])
        # No luck! Is there perhaps a root dataset directly in here?
        root = entities.get("./", {})
        # FIXME: below will work both for
        # "@type": "Dataset"
        # "@type": ["Dataset"]
        # ..but also the unlikely
        # "@type": "DatasetSomething"
        if root and "Dataset" in root.get("@type", []):
            return (None, "./")
        # Uh oh..
        raise KeyError(
            "Can't find Root Data Entity in RO-Crate, "
            "see https://www.researchobject.org/ro-crate/1.1/root-data-entity.html"
        )

    def __read_data_entities(self, entities, source, gen_preview):
        metadata_id, root_id = self.find_root_entity_id(entities)
        entities.pop(metadata_id)  # added previously
        root_entity = entities.pop(root_id)
        assert root_id == root_entity.pop('@id')
        parts = root_entity.pop('hasPart', [])
        self.add(RootDataset(self, properties=root_entity))
        if not gen_preview and Preview.BASENAME in entities:
            self.add(Preview(self, source / Preview.BASENAME))
        type_map = OrderedDict((_.__name__, _) for _ in subclasses(FileOrDir))
        for data_entity_ref in parts:
            id_ = data_entity_ref['@id']
            entity = entities.pop(id_)
            assert id_ == entity.pop('@id')
            try:
                t = entity["@type"]
            except KeyError:
                raise ValueError(f'entity "{id_}" has no @type')
            types = {_.strip() for _ in set(t if isinstance(t, list) else [t])}
            # pick the most specific type (order guaranteed by subclasses)
            cls = DataEntity
            for name, c in type_map.items():
                if name in types:
                    cls = c
                    break
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
            # https://github.com/ResearchObject/ro-crate/issues/83
            if isinstance(entity['@type'], list):
                raise RuntimeError(f"multiple types for '{identifier}'")
            cls = type_map.get(entity['@type'], ContextEntity)
            self.add(cls(self, identifier, entity))

    @property
    def name(self):
        return self.root_dataset['name']

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
        return self.root_dataset['creator']

    @creator.setter
    def creator(self, value):
        self.root_dataset['creator'] = value

    @property
    def license(self):
        return self.root_dataset['license']

    @license.setter
    def license(self, value):
        self.root_dataset['license'] = value

    @property
    def description(self):
        return self.root_dataset['description']

    @description.setter
    def description(self, value):
        self.root_dataset['description'] = value

    @property
    def keywords(self):
        return self.root_dataset['keywords']

    @keywords.setter
    def keywords(self, value):
        self.root_dataset['keywords'] = value

    @property
    def publisher(self):
        return self.root_dataset['publisher']

    @publisher.setter
    def publisher(self, value):
        self.root_dataset['publisher'] = value

    @property
    def isBasedOn(self):
        return self.root_dataset['isBasedOn']

    @isBasedOn.setter
    def isBasedOn(self, value):
        self.root_dataset['isBasedOn'] = value

    @property
    def image(self):
        return self.root_dataset['image']

    @image.setter
    def image(self, value):
        self.root_dataset['image'] = value

    @property
    def CreativeWorkStatus(self):
        return self.root_dataset['CreativeWorkStatus']

    @CreativeWorkStatus.setter
    def CreativeWorkStatus(self, value):
        self.root_dataset['CreativeWorkStatus'] = value

    @property
    def mainEntity(self):
        return self.root_dataset['mainEntity']

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
        mentions = [_ for _ in (self.root_dataset['mentions'] or []) if isinstance(_, TestSuite)]
        about = [_ for _ in (self.root_dataset['about'] or []) if isinstance(_, TestSuite)]
        if self.test_dir:
            legacy_about = [_ for _ in (self.test_dir['about'] or []) if isinstance(_, TestSuite)]
            about += legacy_about
        return list(set(mentions + about))  # remove any duplicate refs

    def resolve_id(self, id_):
        if not is_url(id_):
            id_ = urljoin(self.arcp_base_uri, id_)  # also does path normalization
        return id_.rstrip("/")

    def get_entities(self):
        return self.__entity_map.values()

    def _get_root_jsonld(self):
        self.root_dataset.properties()

    def dereference(self, entity_id):
        canonical_id = self.resolve_id(entity_id)
        return self.__entity_map.get(canonical_id, None)

    def add_file(
            self,
            source=None,
            dest_path=None,
            fetch_remote=False,
            validate_url=True,
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
            validate_url=True,
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
                if key not in self.__entity_map:
                    self.root_dataset._jsonld.setdefault("hasPart", [])
                    self.root_dataset["hasPart"] += [e]
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
                self.root_dataset["hasPart"] = [_ for _ in self.root_dataset["hasPart"] or [] if _ != e]
                if not self.root_dataset["hasPart"]:
                    del self.root_dataset._jsonld["hasPart"]
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
        for root, dirs, files in os.walk(top):
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
            self, source=None, dest_path=None, fetch_remote=False, validate_url=True, properties=None,
            main=False, lang="cwl", lang_version=None, gen_cwl=False
    ):
        workflow = self.add(ComputationalWorkflow(
            self, source=source, dest_path=dest_path, fetch_remote=fetch_remote,
            validate_url=validate_url, properties=properties
        ))
        if isinstance(lang, ComputerLanguage):
            assert lang.crate is self
        else:
            kwargs = {"version": lang_version} if lang_version else {}
            lang = get_lang(self, lang, **kwargs)
            self.add(lang)
        workflow.lang = lang
        if main:
            self.mainEntity = workflow
        if gen_cwl and lang.id != "#cwl":
            if lang.id != "#galaxy":
                raise ValueError(f"conversion from {lang.name} to abstract CWL not supported")
            cwl_source = galaxy_to_abstract_cwl(source)
            cwl_dest_path = Path(source).with_suffix(".cwl").name
            cwl_workflow = self.add_workflow(
                source=cwl_source, dest_path=cwl_dest_path, fetch_remote=fetch_remote, properties=properties,
                main=False, lang="cwl", gen_cwl=False
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
            self, suite, source=None, dest_path=None, fetch_remote=False, validate_url=True, properties=None,
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
