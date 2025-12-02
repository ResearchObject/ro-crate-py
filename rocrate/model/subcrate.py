
from ..model.dataset import Dataset
from ..rocrate import ROCrate


class Subcrate(Dataset):

    def __init__(self, crate, source=None, dest_path=None, fetch_remote=False,
                 validate_url=False, record_size=False):
        """
        This is a data-entity to represent a nested RO-Crate inside another RO-Crate.        
        
        :param crate: The parent crate
        :param source: The relative path to the subcrate, or its URL
        :param dest_path: Description
        :param fetch_remote: Description
        :param validate_url: Description
        :param properties: Description
        :param record_size: Description
        """
        super().__init__(crate, source, dest_path, fetch_remote,
                         validate_url, properties=None, record_size=record_size)
        
        self.subcrate = None
    
    def load_subcrate(self):
        """
        Load the nested RO-Crate from the source path or URL.
        
        Populates the `subcrate` attribute with the loaded ROCrate instance,
        and updates the JSON-LD representation accordingly.
        """
        if self.subcrate is not None:
            return self.subcrate
        
        self.subcrate = ROCrate(self.source)

        self._jsonld = self.subcrate.get("hasParts", default={})

    def __getitem__(self, key):
        
        if self.subcrate is None:
            self.load_subcrate()

        return super().__getitem__(key)