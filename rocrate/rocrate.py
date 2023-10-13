# Copyright 2019-2023 The University of Manchester, UK
# Copyright 2020-2023 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2023 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2023 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2023 École Polytechnique Fédérale de Lausanne, CH
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
import uuid
import zipfile
import atexit
import os
import shutil
import tempfile

from collections import OrderedDict
from pathlib import Path
from urllib.parse import urljoin

from .model import (
    ComputationalWorkflow,
    ComputerLanguage,
    ContextEntity,
    DataEntity,
    Dataset,
    Entity,
    File,
    FileOrDir,
    LegacyMetadata,
    Metadata,
    Preview,
    RootDataset,
    SoftwareApplication,
    TestDefinition,
    TestInstance,
    TestService,
    TestSuite,
    WorkflowDescription,
)
from .model.metadata import WORKFLOW_PROFILE, TESTING_EXTRA_TERMS, metadata_class
from .model.computationalworkflow import galaxy_to_abstract_cwl
from .model.computerlanguage import get_lang
from .model.testservice import get_service
from .model.softwareapplication import get_app

from .utils import is_url, subclasses, get_norm_value, walk, as_list
from .metadata import read_metadata, find_root_entity_id


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
        return source

    def __read_data_entities(self, entities, source, gen_preview):
        metadata_id, root_id = find_root_entity_id(entities)
        root_entity = entities.pop(root_id)
        assert root_id == root_entity.pop('@id')
        parts = as_list(root_entity.pop('hasPart', []))
        self.add(RootDataset(self, root_id, properties=root_entity))
        MetadataClass = metadata_class(metadata_id)
        metadata_properties = entities.pop(metadata_id)
        self.add(MetadataClass(self, metadata_id, properties=metadata_properties))

        preview_entity = entities.pop(Preview.BASENAME, None)
        if preview_entity and not gen_preview:
            self.add(Preview(self, source / Preview.BASENAME, properties=preview_entity))
        self.__add_parts(parts, entities, source)

    def __add_parts(self, parts, entities, source):
        type_map = OrderedDict((_.__name__, _) for _ in subclasses(FileOrDir))
        for data_entity_ref in parts:
            id_ = data_entity_ref['@id']
            try:
                entity = entities.pop(id_)
            except KeyError:
                continue
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
            self.__add_parts(as_list(entity.get("hasPart", [])), entities, source)

    def __read_contextual_entities(self, entities):
        type_map = {_.__name__: _ for _ in subclasses(ContextEntity)}
        for identifier, entity in entities.items():
            assert identifier == entity.pop('@id')
            cls = pick_type(entity, type_map, fallback=ContextEntity)
            self.add(cls(self, identifier, entity))

    @property
    def default_entities(self):
        return [e for e in self.__entity_map.values()
                if isinstance(e, (RootDataset, Metadata, LegacyMetadata, Preview))]

    @property
    def data_entities(self):
        return [e for e in self.__entity_map.values()
                if not isinstance(e, (RootDataset, Metadata, LegacyMetadata, Preview))
                and hasattr(e, "write")]

    @property
    def contextual_entities(self):
        return [e for e in self.__entity_map.values()
                if not isinstance(e, (RootDataset, Metadata, LegacyMetadata, Preview))
                and not hasattr(e, "write")]

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

    def _get_root_jsonld(self):
        self.root_dataset.properties()

    def dereference(self, entity_id, default=None):
        canonical_id = self.resolve_id(entity_id)
        return self.__entity_map.get(canonical_id, default)

    get = dereference

    def get_by_type(self, type_, exact=False):
        type_ = set(as_list(type_))
        if exact:
            return [_ for _ in self.get_entities() if type_ == set(as_list(_.type))]
        else:
            return [_ for _ in self.get_entities() if type_ <= set(as_list(_.type))]

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

    def add_tree(self, source, dest_path=None, properties=None):
        if not source:
            raise ValueError("source must refer to an existing local directory")
        top = self.add_dataset(source, dest_path=dest_path)
        dest_path = Path(top.id).as_posix()
        for e in os.scandir(source):
            dest = dest_path / Path(e.path).relative_to(source)
            if e.is_file():
                file_ = self.add_file(source=e.path, dest_path=dest)
                top.append_to("hasPart", file_)
            if e.is_dir():
                dir_ = self.add_tree(e.path, dest_path=dest)
                top.append_to("hasPart", dir_)
        return top

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
            elif isinstance(e, (Metadata, LegacyMetadata)):
                self.metadata = e
            elif isinstance(e, Preview):
                self.preview = e
            elif hasattr(e, "write"):
                if key not in self.__entity_map:
                    self.root_dataset.append_to("hasPart", e)
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
                self.preview = None
            elif hasattr(e, "write"):
                self.root_dataset["hasPart"] = [_ for _ in self.root_dataset.get("hasPart", []) if _ != e]
                if not self.root_dataset["hasPart"]:
                    del self.root_dataset._jsonld["hasPart"]
            self.__entity_map.pop(e.canonical_id(), None)

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
            lang = get_lang(self, lang, version=lang_version)
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
        self.root_dataset.append_to(test_ref_prop, suite)
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
        suite.append_to("instance", instance)
        self.metadata.extra_terms.update(TESTING_EXTRA_TERMS)
        return instance

    def add_test_definition(
            self, suite, source=None, dest_path=None, fetch_remote=False, validate_url=False, properties=None,
            engine="planemo", engine_version=None
    ):
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
        if engine_version is not None:
            definition.engineVersion = engine_version
        suite.definition = definition
        self.metadata.extra_terms.update(TESTING_EXTRA_TERMS)
        return definition

    def add_jsonld(self, jsonld):
        """Add a JSON-LD dictionary as a contextual entity to the RO-Crate.

        The `@id` and `@type` keys must be present in the JSON-LD dictionary.

        Args:
            jsonld: A JSON-LD dictionary containing at least `@id` and `@type`.
        Return:
            The entity added to the RO-Crate.
        Raises:
            ValueError: if the jsonld object is empty or None or if the
                entity already exists (found via @id).
        """
        required_keys = {"@id", "@type"}
        if not jsonld or not required_keys.issubset(jsonld):
            raise ValueError("you must provide a non-empty JSON-LD dictionary with @id and @type set")
        entity_id = jsonld.pop("@id")
        if self.get(entity_id):
            raise ValueError(f"entity {entity_id} already exists in the RO-Crate")
        return self.add(ContextEntity(
            self,
            entity_id,
            properties=jsonld
        ))

    def update_jsonld(self, jsonld):
        """Update an entity in the RO-Crate from a JSON-LD dictionary.

        An `@id` must be present in the JSON-LD dictionary. Any other keys
        in the JSON-LD dictionary that start with `@` will be removed.

        Args:
            jsonld: A JSON-LD dictionary.
        Return:
            The updated entity.
        Raises:
            ValueError: if the jsonld object is empty or None, if @id was not
              provided, or if the entity was not found.
        """
        if not jsonld or "@id" not in jsonld:
            raise ValueError("you must provide a non-empty JSON-LD dictionary")
        entity_id = jsonld.pop("@id")
        entity: Entity = self.get(entity_id)
        if not entity:
            raise ValueError(f"entity {entity_id} does not exist in the RO-Crate")
        jsonld = {k: v for k, v in jsonld.items() if not k.startswith('@')}
        entity._jsonld.update(jsonld)
        return entity

    def add_or_update_jsonld(self, jsonld):
        """Add or update an entity from a JSON-LD dictionary.

        An `@id` must be present in the JSON-LD dictionary.

        Args:
            jsonld: A JSON-LD dictionary.
        Return:
            The added or updated entity.
        Raises:
            ValueError: if the jsonld object is empty or None or if @id was not
              provided.
        """
        if not jsonld or "@id" not in jsonld:
            raise ValueError("you must provide a non-empty JSON-LD dictionary")
        entity_id = jsonld.get("@id")
        entity: Entity = self.get(entity_id)
        if not entity:
            return self.add_jsonld(jsonld)
        return self.update_jsonld(jsonld)

    def __validate_suite(self, suite):
        if isinstance(suite, TestSuite):
            assert suite.crate is self
        else:
            suite = self.dereference(suite)
            if suite is None:
                raise ValueError("suite not found")
        return suite


def make_workflow_rocrate(workflow_path, wf_type, include_files=[],
                          fetch_remote=False, cwl=None, diagram=None):
    wf_crate = ROCrate()
    workflow_path = Path(workflow_path)
    wf_crate.add_workflow(
        workflow_path, workflow_path.name, fetch_remote=fetch_remote,
        main=True, lang=wf_type, gen_cwl=(cwl is None)
    )
    for file_entry in include_files:
        wf_crate.add_file(file_entry)
    return wf_crate
