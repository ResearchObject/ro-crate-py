#!/usr/bin/env python

## Copyright 2019-2020 The University of Manchester, UK
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import importlib
import json
import os
import uuid
import requests
import tempfile
import zipfile

from pathlib import Path

from .model import contextentity
from .model.root_dataset import RootDataset
from .model.file import File
from .model.person import Person
from .model.dataset import Dataset
from .model.metadata import Metadata
from .model.preview import Preview


from arcp import generate
from arcp import arcp_random

class ROCrate():

    def __init__(self, source_path = None, load_preview = False):
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        self.uuid = uuid.uuid4()  # TODO: add this as @base in the context? at least for cases where I'm loading from zip
        self.metadata = Metadata(self)  # metadata init already includes itself into the root metadata
        self.default_entities.append(self.metadata)

        # TODO: default_properties must inclue name, description, datePublished, license
        if not source_path or not load_preview:
            #create preview entity and add it to default_entities
            self.preview = Preview(self)
            self.default_entities.append(self.preview)
        if not source_path:
            self.root_dataset = RootDataset(self)
            self.default_entities.append(self.root_dataset)
        else:
            #find root entity
            if zipfile.is_zipfile(source_path):
                # load from zip
                pass
            else: 
                # load from dir
                metadata_path = os.path.join(source_path,'ro-crate-metadata.jsonld')
                if not os.path.isfile(metadata_path):
                    raise ValueError('The directory is not a valid RO-crate')
                entities = self.entities_from_metadata(metadata_path)
                self.build_crate(entities, source_path,load_preview)
                ## TODO: load root dataset properties 

    def entities_from_metadata(self, metadata_path):
        # Creates a dictionary {id: entity} from the metadata file
        with open(metadata_path) as metadata_file:
            metadata_jsonld = json.load(metadata_file)
        ### TODO: should validate the json-ld
        if '@graph' in metadata_jsonld.keys():
            entities_dict = {}
            for entity in metadata_jsonld['@graph']:
                entities_dict[entity['@id']] = entity
                # print(entity)
            return entities_dict
        else:
            raise ValueError('The metadata file has no @graph')


    def build_crate(self, entities, source, load_preview):
        # add data and contextual entities to the crate
        root_id = entities['ro-crate-metadata.jsonld']['about']['@id']
        root_entity = entities[root_id]
        root_entity_parts = root_entity['hasPart']

        # remove hasPart and id from root_entity and add the rest of the properties to the build
        root_entity.pop('@id', None)
        root_entity.pop('hasPart', None)
        self.root_dataset = RootDataset(self, root_entity)
        self.default_entities.append(self.root_dataset)

        # check if a preview is present
        if 'ro-crate-preview.html' in entities.keys() and load_preview:
            preview_source = os.path.join(source,'ro-crate-preview.html')
            self.preview = Preview(self, preview_source)
            self.default_entities.append(self.preview)

        added_entities = []
        # iterate over data entities
        for data_entity_ref in root_entity_parts:
            data_entity_id = data_entity_ref['@id']
            # print(data_entity_id)
            entity = entities[data_entity_id]
            # basic checks should be moved to a separate function
            if '@type' not in entity.keys():
                raise Exception("Entity with @id:" + data_entity_id + " has no type defined")

            # Data entities can have an array as @type
            # so far I just parse them as File class if File is in the list
            # for further extensions (e.g if a class Workflow is created) I can add extra cases or create a mapping table for specific combinations
            # see https://github.com/ResearchObject/ro-crate/issues/83
            entity_types = entity['@type'] if isinstance(entity['@type'], list) else [entity['@type']]
            if 'File' in entity_types:
                file_path = os.path.join(source,entity['@id'])
                # print(file_path)
                # print(entity)
                identifier = entity.pop('@id', None)
                # print(entity)
                if os.path.exists(file_path):
                    # referencing a file path relative to crate-root
                    instance = File(self, file_path, identifier, entity)
                else:
                    # check if it is a valid absolute URI
                    try:
                        response = requests.get(identifier)
                        instance = File(self, identifier, properties=entity)
                    except requests.ConnectionError as exception:
                        print("Source is not a valid URI")
            if 'Dataset' in entity_types:
                dir_path = os.path.join(source,entity['@id'])
                if os.path.exists(dir_path):
                    instance = Dataset(self, dir_path, entity['@id'], entity.pop('@id', None))
                else:
                    raise Exception('Directory not found')
            self._add_data_entity(instance)
            added_entities.append(data_entity_id)

        # the rest of the entities must be contextual entities
        prebuilt_entities = ['./', 'ro-crate-metadata.jsonld', 'ro-crate-preview.html']  # also, filter out the entity with id= ro-crate-metadata.jsonld   and the root dataset: can assume id='./' or '.'
        for identifier, entity in entities.items():
            if identifier not in added_entities + prebuilt_entities:
                entity.pop('@id',None)  #this should be done in the extract entities?
                # contextual entities should not have @type array (see https://github.com/ResearchObject/ro-crate/issues/83)
                if entity['@type'] in [cls.__name__ for cls in contextentity.ContextEntity.__subclasses__()]:
                    module_name = 'rocrate.model.' + entity['@type'].lower()
                    SubClass = getattr(importlib.import_module(module_name, package=None), entity['@type'])
                    instance = SubClass(self, identifier, entity)
                else:
                    instance = contextentity.ContextEntity(self, identifier, entity)
                self._add_context_entity(instance)


    #TODO: add contextual entities
    # def add_contact_point(id, properties = {})
    # def add_organization(id, properties = {})

    # add properties:
    # name datePublished author license identifier distribution contactPoint publisher funder description url hasPart]
    # publisher should be an Organization though it MAY be a Person.
    # funder should reference an Organization

    @property
    def name(self):
        return self.root_dataset['name']

    @name.setter
    def name(self, value):
        self.root_dataset['name'] = value

    # TODO: should change to dateCreated or that is only for workflowhub?
    @property
    def datePublished(self):
        return self.root_dataset['datePublished']

    @datePublished.setter
    def datePublished(self, value):
        self.root_dataset['datePublished'] = value

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

    def resolve_id(self, relative_id):
        return generate.arcp_random(relative_id.strip('./'), uuid=self.uuid)

    def get_entities(self):
        return self.default_entities + self.data_entities + self.contextual_entities

    def set_main_entity(self, main_entity):
        self.root_dataset['mainEntity'] = main_entity

    def _get_root_jsonld(self):
        self.root_dataset.properties()

    def dereference(self, entity_id):
        canonical_id = self.resolve_id(entity_id)
        for entity in self.get_entities():
            if canonical_id == entity.canonical_id():
                return entity
        return None

    # source: file object or path (str)
    def add_file(self, source, crate_path = None , fetch_remote = False, properties = None):
        file_entity = File(self, source,crate_path,fetch_remote, properties)
        self._add_data_entity(file_entity)
        return file_entity

    def remove_file(self,file_id):
        #if file in data_entities:
        self._remove_data_entity(file_id)

    def add_directory(self, source, crate_path = None , properties = None):
        dataset_entity = Dataset(self,source,crate_path,properties)
        self._add_data_entity(dataset_entity)

    def remove_directory(self,dir_id):
        #if file in data_entities:
        self._remove_data_entity(dir_id)

    def _add_data_entity(self, data_entity):
        self._remove_data_entity(data_entity)
        self.data_entities.append(data_entity)

    def _remove_data_entity(self, data_entity):
        if data_entity in self.data_entities:
            self.data_entities.remove(data_entity)



    ################################
    ##### Contextual entities ######
    ################################

    def _add_context_entity(self, entity):
        if entity in self.contextual_entities: self.contextual_entities.remove(entity)
        self.contextual_entities.append(entity)

    def add_person(self, identifier, properties = {}):
        new_person = Person(self, identifier,properties)
        self._add_context_entity(new_person)
        return new_person

    #TODO
    #def fetch_all(self):
        # fetch all files defined in the crate

    ################################
    #####  ######
    ################################

    def get_info(self):
        #return dictionary with basic info to build a preview file
        info_dict = {
            'name': self.name,
            'creator': self.creator,
            'image': self.image
        }
        return info_dict

    # write crate to local dir
    def write_crate(self, base_path):
        Path(base_path).mkdir(parents=True, exist_ok=True)
        # write data entities
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write(base_path)

    def write_zip(self,out_zip):
        if out_zip.endswith('.zip'):
            out_file_path = out_zip
        else:
            out_file_path = out_zip + '.zip'
        zf = zipfile.ZipFile(out_file_path, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write_zip(zf)
        zf.close()
        return zf.filename



