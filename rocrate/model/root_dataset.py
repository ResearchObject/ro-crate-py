import datetime
import os

from .dataset import Dataset

class RootDataset(Dataset):

    def __init__(self, crate):
        default_properties = {'datePublished': datetime.datetime.now()}
        super(RootDataset, self).__init__(crate,None,'./',default_properties)

    def _empty(self):
        # default properties of the metadata entry
        # Hard-coded bootstrap for now
        val = {
                    "@id": "./",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                }
        return val

    # def write(self, base_path):
        # os.mkdir(base_path)

    def properties(self):
        parts = []
        for entity in self.crate.data_entities:
            parts.append(entity.reference())
        properties = self._jsonld
        properties.update({'hasPart':parts})
        return properties
