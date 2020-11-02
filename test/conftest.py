import json
import pathlib
import shutil

import pytest


THIS_DIR = pathlib.Path(__file__).absolute().parent
TEST_DATA_NAME = 'test-data'
BASE_URL = 'https://w3id.org/ro/crate'
VERSION = '1.1'
LEGACY_VERSION = '1.0'


class Helpers:

    PROFILE = f"{BASE_URL}/{VERSION}"
    LEGACY_PROFILE = f"{BASE_URL}/{LEGACY_VERSION}"
    METADATA_FILE_NAME = 'ro-crate-metadata.json'
    LEGACY_METADATA_FILE_NAME = 'ro-crate-metadata.jsonld'
    WORKFLOW_TYPES = {"File", "SoftwareSourceCode", "ComputationalWorkflow"}
    LEGACY_WORKFLOW_TYPES = {"File", "SoftwareSourceCode", "Workflow"}

    @classmethod
    def read_json_entities(cls, crate_base_path):
        metadata_path = pathlib.Path(crate_base_path) / cls.METADATA_FILE_NAME
        with open(metadata_path, "rt") as f:
            json_data = json.load(f)
        return {_["@id"]: _ for _ in json_data["@graph"]}

    @classmethod
    def check_wf_crate(cls, json_entities, wf_file_name):
        assert json_entities["./"]["mainEntity"]["@id"] == wf_file_name
        assert wf_file_name in json_entities
        wf_entity = json_entities[wf_file_name]
        assert isinstance(wf_entity["@type"], list)
        assert set(wf_entity["@type"]) == cls.WORKFLOW_TYPES
        assert "programmingLanguage" in wf_entity


@pytest.fixture
def helpers():
    return Helpers


# pytest's default tmpdir returns a py.path object
@pytest.fixture
def tmpdir(tmpdir):
    return pathlib.Path(tmpdir)


@pytest.fixture
def test_data_dir(tmpdir):
    d = tmpdir / TEST_DATA_NAME
    shutil.copytree(THIS_DIR / TEST_DATA_NAME, d)
    return d
