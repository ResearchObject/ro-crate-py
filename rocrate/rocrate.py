#!/usr/bin/env python

# Copyright 2019-2020 The University of Manchester, UK
# Copyright 2020 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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

import importlib
import json
import os
import uuid
import requests
import zipfile
import atexit
import shutil
import tempfile

from pathlib import Path
from urllib.parse import urljoin

from .model import contextentity
from .model.root_dataset import RootDataset
from .model.file import File
from .model.dataset import Dataset
from .model.metadata import Metadata, LegacyMetadata
from .model.preview import Preview
from .model.testdefinition import TestDefinition
from .model.computationalworkflow import ComputationalWorkflow, galaxy_to_abstract_cwl
from .model.computerlanguage import ComputerLanguage, get_lang
from .model.testinstance import TestInstance
from .model.testservice import TestService, get_service
from .model.softwareapplication import SoftwareApplication, get_app, PLANEMO_DEFAULT_VERSION
from .model.testsuite import TestSuite

from .utils import is_url


class ROCrate():

    def __init__(self, source_path=None, load_preview=False, init=False):
        self.__entity_map = {}
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        # TODO: add this as @base in the context? At least when loading
        # from zip
        self.uuid = uuid.uuid4()
        self.arcp_base_uri = f"arcp://uuid,{self.uuid}/"

        # TODO: default_properties must include name, description,
        # datePublished, license
        if not source_path:
            # create a new ro-crate
            self.add(RootDataset(self), Metadata(self), Preview(self))
        elif init:
            # initialize an ro-crate from a directory tree
            self.__init_from_tree(source_path, load_preview=load_preview)
        else:
            # load an existing ro-crate
            if zipfile.is_zipfile(source_path):
                zip_path = tempfile.mkdtemp(prefix="ro", suffix="crate")
                atexit.register(shutil.rmtree, zip_path)
                with zipfile.ZipFile(source_path, "r") as zip_file:
                    zip_file.extractall(zip_path)
                source_path = zip_path
            metadata_path = os.path.join(source_path, Metadata.BASENAME)
            MetadataClass = Metadata
            if not os.path.isfile(metadata_path):
                metadata_path = os.path.join(source_path, LegacyMetadata.BASENAME)
                MetadataClass = LegacyMetadata
            if not os.path.isfile(metadata_path):
                raise ValueError('The directory is not a valid RO-crate, '
                                 f'missing {Metadata.BASENAME}')
            self.add(MetadataClass(self))
            entities = self.entities_from_metadata(metadata_path)
            self.build_crate(entities, source_path, load_preview)
            # TODO: load root dataset properties

    def __init_from_tree(self, top_dir, load_preview=False):
        top_dir = Path(top_dir)
        if not top_dir.is_dir():
            raise ValueError(f"{top_dir} is not a valid directory path")
        self.add(RootDataset(self), Metadata(self))
        if not load_preview:
            self.add(Preview(self))
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
                elif load_preview:
                    self.add(Preview(self, source))

    def entities_from_metadata(self, metadata_path):
        # Creates a dictionary {id: entity} from the metadata file
        with open(metadata_path) as metadata_file:
            metadata_jsonld = json.load(metadata_file)
        # TODO: should validate the json-ld
        if '@graph' in metadata_jsonld.keys():
            entities_dict = {}
            for entity in metadata_jsonld['@graph']:
                entities_dict[entity['@id']] = entity
                # print(entity)
            return entities_dict
        else:
            raise ValueError('The metadata file has no @graph')

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

    def build_crate(self, entities, source, load_preview):
        # add data and contextual entities to the crate
        (metadata_id, root_id) = self.find_root_entity_id(entities)
        root_entity = entities[root_id]
        root_entity_parts = root_entity['hasPart']

        # remove hasPart and id from root_entity and add the rest of the
        # properties to the build
        root_entity.pop('@id', None)
        root_entity.pop('hasPart', None)
        self.add(RootDataset(self, root_entity))

        # check if a preview is present
        if Preview.BASENAME in entities.keys() and load_preview:
            preview_source = os.path.join(source, Preview.BASENAME)
            self.add(Preview(self, preview_source))
        else:
            self.add(Preview(self))

        added_entities = []
        # iterate over data entities
        for data_entity_ref in root_entity_parts:
            data_entity_id = data_entity_ref['@id']
            # print(data_entity_id)
            entity = entities[data_entity_id]
            # basic checks should be moved to a separate function
            if '@type' not in entity.keys():
                raise Exception("Entity with @id:" + data_entity_id +
                                " has no type defined")

            # Data entities can have an array as @type. So far we just parse
            # them as File class if File is in the list. For further
            # extensions (e.g if a Workflow class is created) we can add extra
            # cases or create a mapping table for specific combinations. See
            # https://github.com/ResearchObject/ro-crate/issues/83
            entity_types = (entity['@type']
                            if isinstance(entity['@type'], list)
                            else [entity['@type']])
            if 'File' in entity_types:
                # temporary workaround, should be handled in the general case
                cls = TestDefinition if "TestDefinition" in entity_types else File
                file_path = os.path.join(source, entity['@id'])
                identifier = entity.pop('@id', None)
                if os.path.exists(file_path):
                    # referencing a file path relative to crate-root
                    instance = cls(self, file_path, identifier, properties=entity)
                else:
                    # check if it is a valid absolute URI
                    try:
                        requests.get(identifier)
                        instance = cls(self, identifier, properties=entity)
                    except requests.ConnectionError:
                        print("Source is not a valid URI")
            if 'Dataset' in entity_types:
                dir_path = os.path.join(source, entity['@id'])
                if os.path.exists(dir_path):
                    props = {k: v for k, v in entity.items() if k != '@id'}
                    instance = Dataset(self, dir_path, entity['@id'], props)
                else:
                    raise Exception('Directory not found')
            self.add(instance)
            added_entities.append(data_entity_id)

        # the rest of the entities must be contextual entities
        prebuilt_entities = [
            root_id, metadata_id, Preview.BASENAME
        ]
        for identifier, entity in entities.items():
            if identifier not in added_entities + prebuilt_entities:
                # should this be done in the extract entities?
                entity.pop('@id', None)
                # contextual entities should not have @type array
                # (see https://github.com/ResearchObject/ro-crate/issues/83)
                if entity['@type'] in [
                        cls.__name__
                        for cls in contextentity.ContextEntity.__subclasses__()
                ]:
                    module_name = 'rocrate.model.' + entity['@type'].lower()
                    SubClass = getattr(
                        importlib.import_module(module_name, package=None),
                        entity['@type']
                    )
                    instance = SubClass(self, identifier, entity)
                else:
                    instance = contextentity.ContextEntity(
                        self, identifier, entity
                    )
                self.add(instance)

    # TODO: add contextual entities
    # def add_contact_point(id, properties = {})
    # def add_organization(id, properties = {})

    # add properties: name datePublished author license identifier
    # distribution contactPoint publisher funder description url hasPart.
    # publisher should be an Organization though it MAY be a Person. funder
    # should reference an Organization

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

    def add_file(self, source=None, dest_path=None, fetch_remote=False,
                 validate_url=True, properties=None):
        return self.add(File(self, source=source, dest_path=dest_path, fetch_remote=fetch_remote,
                             validate_url=validate_url, properties=properties))

    def add_dataset(self, source=None, dest_path=None, properties=None):
        return self.add(Dataset(self, source=source, dest_path=dest_path, properties=properties))

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
                    self.root_dataset["hasPart"] += [e]
            else:
                self.contextual_entities.append(e)
            self.__entity_map[key] = e
        return entities[0] if len(entities) == 1 else entities

    # TODO
    # def fetch_all(self):
        # fetch all files defined in the crate

    # write crate to local dir
    def write_crate(self, base_path):
        Path(base_path).mkdir(parents=True, exist_ok=True)
        # write data entities
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write(base_path)

    def write_zip(self, out_zip):
        if str(out_zip).endswith('.zip'):
            out_file_path = out_zip
        else:
            out_file_path = out_zip + '.zip'
        zf = zipfile.ZipFile(
            out_file_path, 'w', compression=zipfile.ZIP_DEFLATED,
            allowZip64=True
        )
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write_zip(zf)
        zf.close()
        return zf.filename

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
        if not main_entity:
            main_entity = self.mainEntity
            if not main_entity:
                raise ValueError("crate does not have a main entity")
        suite = self.add(TestSuite(self, identifier))
        suite.name = name or suite.id.lstrip("#")
        suite["mainEntity"] = main_entity
        # note that a test dir is required (possibly empty) even if the suite
        # is going to have only instances (no definitions)
        test_dir = self.test_dir or self.add_directory(dest_path="test")
        suite_set = set(test_dir["about"] or [])
        suite_set.add(suite)
        test_dir["about"] = list(suite_set)
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
        return instance

    def add_test_definition(
            self, suite, source=None, dest_path=None, fetch_remote=False, validate_url=True, properties=None,
            engine="planemo", engine_version=PLANEMO_DEFAULT_VERSION
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
        definition.engineVersion = engine_version
        suite.definition = definition
        return definition

    def __validate_suite(self, suite):
        if isinstance(suite, TestSuite):
            assert suite.crate is self
        else:
            suite = self.dereference(suite)
            if suite is None:
                raise ValueError("suite not found")
        return suite
