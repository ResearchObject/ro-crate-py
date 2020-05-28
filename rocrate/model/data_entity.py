import os

from .entity import Entity


class DataEntity(Entity):


    def filepath(self, base_path='./'):
        return os.path.join(base_path,self.id)
