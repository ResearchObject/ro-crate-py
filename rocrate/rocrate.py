import os
import uuid
from pathlib import Path

from .model import contextentity
from .model.root_dataset import RootDataset
from .model.file import File
from .model.dataset import Dataset
from .model.metadata import Metadata
import zipfile
import tempfile

class ROCrate():

    def __init__(self):
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        self.uuid = uuid.uuid1()

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

    def resolve_id(relative_id):
        os.path.join(("arcp://uuid," + self.uuid), relative_id)

    def get_entities(self):
        return self.default_entities + self.data_entities + self.contextual_entities

    def set_main_entity(self, main_entity):
        self.root_dataset.setitem('mainEntity', main_entity)

    def _get_root_jsonld(self):
        self.root_dataset.properties()
        # root_graph = self.metadata.get
        #root_json_ld self._get_root_jsonld() .serialize(format='json-ld', indent=4)

    # source: file object or path (str)
    def add_file(self, source, crate_path = None , properties = None):
        file_entity = File(self, source,crate_path,properties)
        self._add_data_entity(file_entity)
        return file_entity

    def remove_file(self,file_id):
        #if file in data_entities:
        _remove_data_entity(file_id)

    def add_directory(self, source, crate_path = None , properties = None):
        dataset_entity = Dataset(source,crate_path,properties)
        self._add_data_entity(dataset_entity)

    def remove_directory(self,dir_id):
        #if file in data_entities:
        _remove_data_entity(dir_id)

    def _add_data_entity(self, data_entity):
        self._remove_data_entity(data_entity)
        self.data_entities.append(data_entity)

    def _remove_data_entity(self, data_entity):
        if data_entity in self.data_entities:
            self.data_entities.remove(data_entity)

    # write crate to local dir
    def write_crate(self, base_path):
        # write default entities (metadata, preview, root Dataset..)
        #for default_entity in self.default_entities:
        #    default_entity.write(base_path)
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


    ################################
    ##### Contextual entities ######
    ################################

    def add_person(person_dict):
        new_person = roc.Person()
        _add_context_entity(new_person)

    #TODO
    #def fetch_all(self):
        # fetch all files defined in the crate


# class ROCrateWorkflow(ROCrate):

    # def __init__(self,workflow_file):
        # super().__init__()
        # self.add_file(workflow_file)
        # self.previewmain_workflow = main_workflow_file


