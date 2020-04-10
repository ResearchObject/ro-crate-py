import rocrate as rclib
import zipfile


class ROCrate():

    def __init__():
        self.create_dict = {}
        self.data_entities = []
        self.contextual_entities = []
        self.metadata = Metadata()

    def add_file(self, path)
        entity = FileDataEntity()
        #...process path
        self._add_data_entity(entity)

    def remove_file(self,file_id):
        #if file in data_entities:
        _remove_data_entity(file_id)

    def _add_data_entity(self, data_entity):
        self.data_entities.append(data_entity)

    #def _remove_data_entity():


    def write_crate(create_path):
        # write crate to local dir

    def archive_crate(crate_path,archiver='zip'):
        filename = '.'.join([os.path.basename(crate_path), archiver])
        if archiver == 'zip':
            zfp = os.path.join(os.path.dirname(crate_path), fn)
            zf = zipfile.ZipFile(zfp, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
            # write root meatadata file
            zf.write(filepath, relpath)
	    # iterate over data entities
            for data_entity in self._get_data_entities():
                #if the data entity is a local file then copy it
                filepath = data_entity. ....
                #if data_entity is a file path:
                if os.path.isfile(filepath):
                    #filepath = os.path.normpath(os.path.join(dirpath, name))
                    #relpath = os.path.relpath(filepath, os.path.dirname(bag_path))
            zf.close()
            archive = zf.filename

        return archive

    def add_person(person_dict):


class ROCrateWorkflow(ROCrate):

    def __init__(self, main_workflow_file):
        super().__init__(self)
        self.main_workflow = main_workflow_file


