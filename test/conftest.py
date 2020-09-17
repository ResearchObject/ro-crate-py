import pathlib
import shutil

import pytest


THIS_DIR = pathlib.Path(__file__).absolute().parent
TEST_DATA_NAME = 'test-data'


# pytest's default tmpdir returns a py.path object
@pytest.fixture
def tmpdir(tmpdir):
    return pathlib.Path(tmpdir)


@pytest.fixture
def test_data_dir(tmpdir):
    d = tmpdir / TEST_DATA_NAME
    shutil.copytree(THIS_DIR / TEST_DATA_NAME, d)
    return d
