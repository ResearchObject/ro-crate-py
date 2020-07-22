import pathlib
import shutil
import tempfile
import unittest


THIS_DIR = pathlib.Path(__file__).absolute().parent
TEST_DATA_NAME = 'test-data'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="rocrate_test_"))
        self.test_data_dir = self.tmpdir / TEST_DATA_NAME
        shutil.copytree(THIS_DIR / TEST_DATA_NAME, self.test_data_dir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
