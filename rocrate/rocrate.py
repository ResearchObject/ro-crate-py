import os
import uuid
# from uuid import UUID
from pathlib import Path

from .model import contextentity
from .model.root_dataset import RootDataset
from .model.file import File
from .model.person import Person
from .model.dataset import Dataset
from .model.metadata import Metadata
import zipfile
import tempfile

from arcp import generate
from arcp import arcp_random

class ROCrate():

    def __init__(self):
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        self.uuid = uuid.uuid4()

        #create metadata and assign it to data_entities
        self.metadata = Metadata(self)  # metadata init already includes itself into the root metadata
        self.default_entities.append(self.metadata)

        #create root entity (Dataset) with id './' and add it to the default entities
        # TODO: default_properties must inclue name, description, datePublished, license
        self.root_dataset = RootDataset(self)
        self.default_entities.append(self.root_dataset)

        #create preview entity and add it to default_entities
        #self.preview = Preview('ro-crate-preview.html')
        #self.default_entities.append(self.preview)


    # Properties

    @property
    def author(self):
        return self.root_dataset['author']

    @author.setter
    def author(self, value):
        # if isinstance(value, Person):
        self.root_dataset['author'] = value


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
    def add_file(self, source, crate_path = None , properties = None):
        # print('adding file' + source)
        file_entity = File(self, source,crate_path,properties)
        self._add_data_entity(file_entity)
        return file_entity

    def remove_file(self,file_id):
        #if file in data_entities:
        self._remove_data_entity(file_id)

    def add_directory(self, source, crate_path = None , properties = None):
        dataset_entity = Dataset(source,crate_path,properties)
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

    # write crate to local dir
    def write_crate(self, base_path):
        Path(base_path).mkdir(parents=True, exist_ok=True)
        # write data entities
        for writable_entity in self.data_entities + self.default_entities:
            writable_entity.write(base_path)

    def write_zip(out_zip):
        zf = zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
        write_crate(zf)
        zf.close()
        archive = zf.filename
        return archive

# class ROCrateWorkflow(ROCrate):

    # def __init__(self,workflow_file):
        # super().__init__()
        # self.add_file(workflow_file)
        # self.previewmain_workflow = main_workflow_file


