from rocrate import rocrate_api as roc_api
from rocrate.rocrate import ROCrate
from test.test_common import BaseTest


class TestAPI(BaseTest):

    def test_galaxy_wf_crate(self):
        wf_path = self.test_data_dir / 'test_galaxy_wf.ga'
        wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='Galaxy')
        self.assertIsInstance(wf_crate, ROCrate)
        out_path = self.tmpdir / 'ro_crate_out'
        out_path.mkdir()
        wf_crate.write_crate(out_path)

    def test_cwl_wf_crate(self):
        wf_path = self.test_data_dir / 'sample_cwl_wf.cwl'
        wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='CWL')
        self.assertIsInstance(wf_crate, ROCrate)
        out_path = self.tmpdir / 'ro_crate_out'
        out_path.mkdir()
        wf_crate.write_crate(out_path)

    def test_create_wf_include(self):
        wf_path = self.test_data_dir / 'test_galaxy_wf.ga'
        extra_file1 = self.test_data_dir / 'test_file_galaxy.txt'
        extra_file2 = self.test_data_dir / 'test_file_galaxy2.txt'
        files_list = [extra_file1, extra_file2]
        wf_crate = roc_api.make_workflow_rocrate(
            wf_path, wf_type='Galaxy', include_files=files_list
        )
        self.assertIsInstance(wf_crate, ROCrate)
        out_path = self.tmpdir / 'ro_crate_out'
        out_path.mkdir()
        wf_crate.write_crate(out_path)
