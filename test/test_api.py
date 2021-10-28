# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rocrate import rocrate_api as roc_api
from rocrate.rocrate import ROCrate
from rocrate.model.computerlanguage import CWL_DEFAULT_VERSION, GALAXY_DEFAULT_VERSION


def test_galaxy_wf_crate(test_data_dir, tmpdir, helpers):
    wf_id = 'test_galaxy_wf.ga'
    wf_path = test_data_dir / wf_id
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='Galaxy')
    assert isinstance(wf_crate, ROCrate)

    wf = wf_crate.dereference(wf_id)
    assert wf._default_type == "ComputationalWorkflow"
    assert wf_crate.mainEntity is wf
    lang = wf_crate.dereference("#galaxy")
    assert hasattr(lang, "name")
    assert lang.version == GALAXY_DEFAULT_VERSION
    assert wf["programmingLanguage"] is lang
    assert wf["subjectOf"] is not None
    assert helpers.WORKFLOW_TYPES.issubset(wf["subjectOf"].type)

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_id)
    wf_entity = json_entities[wf_id]
    assert "subjectOf" in wf_entity
    abstract_wf_id = wf_entity["subjectOf"]["@id"]
    abstract_wf_entity = json_entities[abstract_wf_id]
    assert helpers.WORKFLOW_TYPES.issubset(abstract_wf_entity["@type"])

    wf_out_path = out_path / wf_id
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()

    abstract_wf_out_path = out_path / abstract_wf_id
    assert abstract_wf_out_path.exists()


def test_cwl_wf_crate(test_data_dir, tmpdir, helpers):
    wf_id = 'sample_cwl_wf.cwl'
    wf_path = test_data_dir / wf_id
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='CWL')
    assert isinstance(wf_crate, ROCrate)

    wf = wf_crate.dereference(wf_id)
    assert wf_crate.mainEntity is wf
    lang = wf_crate.dereference("#cwl")
    assert hasattr(lang, "name")
    assert lang.version == CWL_DEFAULT_VERSION
    assert wf["programmingLanguage"] is lang
    assert wf["subjectOf"] is None

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_id)

    wf_out_path = out_path / wf_id
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()


def test_create_wf_include(test_data_dir, tmpdir, helpers):
    wf_id = 'test_galaxy_wf.ga'
    wf_path = test_data_dir / wf_id
    extra_file1 = test_data_dir / 'test_file_galaxy.txt'
    extra_file2 = test_data_dir / 'test_file_galaxy2.txt'
    files_list = [extra_file1, extra_file2]
    wf_crate = roc_api.make_workflow_rocrate(
        wf_path, wf_type='Galaxy', include_files=files_list
    )
    assert isinstance(wf_crate, ROCrate)

    wf = wf_crate.dereference(wf_id)
    assert wf_crate.mainEntity is wf
    lang = wf_crate.dereference("#galaxy")
    assert hasattr(lang, "name")
    assert lang.version == GALAXY_DEFAULT_VERSION
    assert wf["programmingLanguage"] is lang
    assert wf["subjectOf"] is not None
    assert helpers.WORKFLOW_TYPES.issubset(wf["subjectOf"].type)
    assert wf_crate.dereference(extra_file1.name) is not None
    assert wf_crate.dereference(extra_file2.name) is not None

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_id)

    wf_out_path = out_path / wf_id
    file1 = out_path / extra_file1.name
    file2 = out_path / extra_file2.name
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()
    assert file1.exists()
    with open(extra_file1) as f1, open(file1) as f2:
        assert f1.read() == f2.read()
    assert file2.exists()
    with open(extra_file2) as f1, open(file2) as f2:
        assert f1.read() == f2.read()
