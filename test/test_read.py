from rocrate.rocrate import ROCrate
from test.test_common import BaseTest
import tempfile
import pathlib


class TestAPI(BaseTest):

    def test_crate_dir_loading(self):
        # load crate from directory
        crate_dir = self.test_data_dir / 'read_crate'
        crate = ROCrate(crate_dir, load_preview=True)

        # check loaded entities and properties
        main_wf = crate.dereference('test_galaxy_wf.ga')
        wf_prop = main_wf.properties()
        self.assertEqual(wf_prop['@id'], 'test_galaxy_wf.ga')

        wf_author = crate.dereference('#joe')
        author_prop = wf_author.properties()
        self.assertEqual(author_prop['@type'], 'Person')
        self.assertEqual(author_prop['name'], 'Joe Bloggs')

        # write the crate in a different directory
        out_path = pathlib.Path(tempfile.gettempdir()) / 'crate_read_out'
        out_path.mkdir(exist_ok=True)
        crate.write_crate(out_path)

        metadata_path = out_path / 'ro-crate-metadata.jsonld'
        self.assertTrue(metadata_path.exists())
