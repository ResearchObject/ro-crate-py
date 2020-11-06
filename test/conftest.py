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
    PREVIEW_FILE_NAME = "ro-crate-preview.html"

    @classmethod
    def read_json_entities(cls, crate_base_path):
        metadata_path = pathlib.Path(crate_base_path) / cls.METADATA_FILE_NAME
        with open(metadata_path, "rt") as f:
            json_data = json.load(f)
        return {_["@id"]: _ for _ in json_data["@graph"]}

    @classmethod
    def check_crate(cls, json_entities, root_id="./", data_entity_ids=None):
        assert root_id in json_entities
        root = json_entities[root_id]
        assert root["@type"] == "Dataset"
        assert cls.METADATA_FILE_NAME in json_entities
        metadata = json_entities[cls.METADATA_FILE_NAME]
        assert metadata["@type"] == "CreativeWork"
        assert metadata["conformsTo"] == {"@id": cls.PROFILE}
        assert metadata["about"] == {"@id": root_id}
        if data_entity_ids:
            data_entity_ids = set(data_entity_ids)
            assert data_entity_ids.issubset(json_entities)
            assert "hasPart" in root
            assert data_entity_ids.issubset([_["@id"] for _ in root["hasPart"]])

    @classmethod
    def check_wf_crate(cls, json_entities, wf_file_name, root_id="./"):
        cls.check_crate(json_entities, root_id=root_id)
        assert json_entities[root_id]["mainEntity"]["@id"] == wf_file_name
        assert wf_file_name in json_entities
        wf_entity = json_entities[wf_file_name]
        assert isinstance(wf_entity["@type"], list)
        assert cls.WORKFLOW_TYPES.issubset(wf_entity["@type"])
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
