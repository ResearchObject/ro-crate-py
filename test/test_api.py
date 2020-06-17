import unittest
import os
from rocrate import rocrate_api as roc_api
from rocrate.rocrate import ROCrate
from test.test_common import BaseTest

class TestAPI(BaseTest):


    def test_create_wf_crate(self):
        wf_path = os.path.join(self.test_data_dir, 'test_galaxy_wf.ga')
        try:
            wc_crate = roc_api.make_workflow_rocrate(wf_path,wf_type = 'Galaxy')
            self.assertIsInstance(wc_crate, ROCrate)
        except Exception as e:
            self.fail('return custom exception')

    def test_create_wf_include(self):
        wf_path = os.path.join(self.test_data_dir, 'test_galaxy_wf.ga')
        extra_file1 = os.path.join(self.test_data_dir, 'test_file_galaxy.txt')
        extra_file2 =  os.path.join(self.test_data_dir, 'test_file_galaxy2.txt')
        files_list = [extra_file1,extra_file2]
        try:
            wc_crate = roc_api.make_workflow_rocrate(wf_path,wf_type = 'Galaxy', include_files = files_list)
            self.assertIsInstance(wc_crate, ROCrate)
        except Exception as e:
            self.fail('return custom exception')
