import unittest
import os
from rocrate.rocrate import ROCrate
from rocrate.model.file import File
from rocrate.model.person import Person
from test.test_common import BaseTest
import tempfile
import pathlib
import zipfile
import shutil

class TestAPI(BaseTest):

    def test_crate_dir_loading(self):
        # load crate from directory
        crate_dir = os.path.join(self.test_data_dir, 'read_crate')
        crate = ROCrate(crate_dir, load_preview=True)

        #check loaded entities and properties
        main_wf = crate.dereference('test_galaxy_wf.ga')
        wf_prop = main_wf.properties()

        wf_author = crate.dereference('#joe')
        author_prop = wf_author.properties()
        self.assertEqual(author_prop['@type'], 'Person')
        self.assertEqual(author_prop['name'], 'Joe Bloggs')

        # write the crate in a different directory
        out_path = os.path.join(tempfile.gettempdir(),'crate_read_out')
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        crate.write_crate(out_path)

        metadata_path = pathlib.Path(os.path.join(out_path, 'ro-crate-metadata.jsonld'))
        self.assertTrue(metadata_path.exists())




        # metadata_path = pathlib.Path(os.path.join(out_path, 'ro-crate-metadata.jsonld'))
        # self.assertTrue(metadata_path.exists())

        # preview_path = pathlib.Path(os.path.join(out_path, 'ro-crate-preview.html'))
        # self.assertTrue(preview_path.exists())
        # file1 = pathlib.Path(os.path.join(out_path, 'sample_file.txt'))
        # file2 = pathlib.Path(os.path.join(out_path, 'subdir','sample_file2.csv'))
        # file_subdir = pathlib.Path(os.path.join(out_path, 'test_add_dir','sample_file_subdir.txt'))
        # self.assertTrue(file1.exists())
        # self.assertTrue(file2.exists())
        # self.assertTrue(file_subdir.exists())


    # def test_write_zip(self):
        # crate = ROCrate()

        # # dereference added files
        # sample_file = os.path.join(self.test_data_dir, 'sample_file.txt')
        # file_returned = crate.add_file(sample_file)
        # file_returned_subdir = crate.add_file(sample_file, 'subdir/sample_file2.csv')
        # test_dir_path = os.path.join(self.test_data_dir,'test_add_dir')
        # test_dir_entity = crate.add_directory(test_dir_path, 'test_add_dir')

        # #write to zip
        # zip_path = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.zip')
        # crate.write_zip(zip_path.name)
        # zip_path.close()
        # read_zip = zipfile.ZipFile(zip_path.name, mode='r')
        # self.assertEqual(read_zip.getinfo('sample_file.txt').file_size, 12)
        # self.assertEqual(read_zip.getinfo('test_add_dir/sample_file_subdir.txt').file_size, 18)
