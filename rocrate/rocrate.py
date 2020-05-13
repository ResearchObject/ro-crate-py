from .model import contextentity
from .model import dataset
from .model import file
from .model.metadata import Metadata
import zipfile
import tempfile

class ROCrate():

    def __init__(self):
        self.id = './'
        #self.crate_dict = {}
        self.default_entities = []
        self.data_entities = []
        self.contextual_entities = []
        #create metadata and assign it to default_entities 
        self.metadata = Metadata()
        self.default_entities.append(self.metadata)
        #create root entity with id './' and add it to the default entities
        self.default_entities.append(Dataset('./', metadata=self.metadata))
        #create preview entity and add it to default_entities
        #self.preview = Preview('ro-crate-preview.html')
        #self.default_entities.append(self.preview)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'Dataset',
            "@hasPart": []
            #name contentSize dateModified encodingFormat identifier sameAs
        }
        return val

    def _get_root_jsonld(self):
        root_graph = self.metadata.get
        #root_json_ld self._get_root_jsonld() .serialize(format='json-ld', indent=4)

    # source: file object or path (str)
    def add_file(self, source, dest_path = None , properties = None):
        file_entity = File(source,dest_path,properties,self.metadata)
        self._add_data_entity(file_entity)

    def remove_file(self,file_id):
        #if file in data_entities:
        _remove_data_entity(file_id)

    def _add_data_entity(self, data_entity):
        self.data_entities.append(data_entity)

    def _remove_data_entity():
        self.data_entities.remove(data_entity)
        self.metadata._remove_entity(data_entity)

    # write crate to local dir
    def write_crate(base_path):
        # write default entities (metadata, preview, root Dataset..)
        for default_entity in self.default_entities:
            default_entity.write(base_path)
        # write data entities
        for data_entity in data_entities:
            data_entity.write_to_file(base_path)

    def write_zip(out_zip):
        zf = zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
        write_crate(zf)
        zf.close()
        archive = zf.filename
        return archive

    def add_person(person_dict):
        new_person = roc.Person()
        _add_context_entity(new_person)

    #TODO
    #def fetch_all(self):
        # fetch all files defined in the crate 


class ROCrateWorkflow(ROCrate):

    def __init__(self, workflow_file):
        super().__init__()
        self.add_file(workflow_file)
        self.previewmain_workflow = main_workflow_file


