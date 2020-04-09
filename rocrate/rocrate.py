



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

    def _add_data_entity(self, data_entity):
        self.data_entities.append(data_entity)


class ROCrateWorkflow(ROCrate):

    def __init__(self, main_workflow_file):
        super().__init__(self)
        self.main_workflow = main_workflow_file


