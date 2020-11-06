from rocrate import rocrate_api as roc_api
from rocrate.rocrate import ROCrate


def test_galaxy_wf_crate(test_data_dir, tmpdir, helpers):
    wf_path = test_data_dir / 'test_galaxy_wf.ga'
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='Galaxy')
    assert isinstance(wf_crate, ROCrate)
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write_crate(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_path.name)
    wf_entity = json_entities[wf_path.name]
    assert "subjectOf" in wf_entity
    abstract_wf_id = wf_entity["subjectOf"]["@id"]
    abstract_wf_entity = json_entities[abstract_wf_id]
    assert helpers.WORKFLOW_TYPES.issubset(abstract_wf_entity["@type"])

    wf_out_path = out_path / wf_path.name
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()

    abstract_wf_out_path = out_path / abstract_wf_id
    assert abstract_wf_out_path.exists()


def test_cwl_wf_crate(test_data_dir, tmpdir, helpers):
    wf_path = test_data_dir / 'sample_cwl_wf.cwl'
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='CWL')
    assert isinstance(wf_crate, ROCrate)
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write_crate(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_path.name)

    wf_out_path = out_path / wf_path.name
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()


def test_create_wf_include(test_data_dir, tmpdir, helpers):
    wf_path = test_data_dir / 'test_galaxy_wf.ga'
    extra_file1 = test_data_dir / 'test_file_galaxy.txt'
    extra_file2 = test_data_dir / 'test_file_galaxy2.txt'
    files_list = [extra_file1, extra_file2]
    wf_crate = roc_api.make_workflow_rocrate(
        wf_path, wf_type='Galaxy', include_files=files_list
    )
    assert isinstance(wf_crate, ROCrate)
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write_crate(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_path.name)

    wf_out_path = out_path / wf_path.name
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
