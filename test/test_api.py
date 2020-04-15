import unittest
import os
from rocrate import rocrate_api as roc_api
from rocrate.rocrate import ROCrateWorkflow
from test.test_common import BaseTest

class TestAPI(BaseTest):


    def test_create_wf_crate(self):
        wf_path = os.path.join(self.test_wf_dir, 'test-workflow.ga')
        try:
            wc_crate = roc_api.make_workflow_rocrate(wf_path,wf_type = 'Galaxy')
            self.assertIsInstance(wc_crate, ROCrateWorkflow)
        except Exception as e:
            self.fail('return custom exception')

