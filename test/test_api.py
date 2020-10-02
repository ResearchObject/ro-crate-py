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


def test_cwl_wf_crate(test_data_dir, tmpdir, helpers):
    wf_path = test_data_dir / 'sample_cwl_wf.cwl'
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='CWL')
    assert isinstance(wf_crate, ROCrate)
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write_crate(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_path.name)


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
