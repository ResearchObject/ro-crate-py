import os

from .entity import Entity


class DataEntity(Entity):


    def filepath(self, base_path=None):
        if base_path:
            return os.path.join(base_path,self.id)
        else:
            return self.id
