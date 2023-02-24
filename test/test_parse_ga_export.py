import os
from rocrate.rocrate import ROCrate, make_workflow_run_rocrate
from rocrate.provenance_profile import ProvenanceProfile

from tools.load_ga_export import load_ga_history_export, GalaxyJob


def test_ga_history_loading(test_data_dir, tmpdir, helpers):
    export_dir = "test_ga_history_export"
    export_path = test_data_dir / export_dir / "history_export"

    metadata_export = load_ga_history_export(export_path)
    jobs = []
    for job in metadata_export["jobs_attrs"]:
        job_attrs = GalaxyJob()
        job_attrs.parse_ga_jobs_attrs(job)
        jobs.append(job_attrs.attributes)

        assert isinstance(job_attrs, GalaxyJob)

    assert len(jobs) == 4


def test_ga_history_parsing(test_data_dir, tmpdir, helpers):
    export_dir = "test_ga_history_export"
    export_path = test_data_dir / export_dir / "history_export"
    prov_path = tmpdir / "provenance"
    prov = ProvenanceProfile(export_path, "PDG", "https://orcid.org/0000-0002-8940-4946")

    assert isinstance(prov, ProvenanceProfile)

    prov.finalize_prov_profile(out_path=prov_path)


def test_create_wf_run_ro_crate(test_data_dir, tmpdir, helpers):

    export_dir = "test_ga_history_export"
    wfr_metadata_path = test_data_dir / export_dir / "history_export"
    dataset_path = wfr_metadata_path / "datasets"
    files_list = os.listdir(dataset_path)
    files_list = [dataset_path / f for f in files_list]
    wf_id = 'wf_definition.ga'
    wf_path = test_data_dir / export_dir / wf_id

    wf_crate = make_workflow_run_rocrate(
        workflow_path=wf_path, wfr_metadata_path=wfr_metadata_path, author=None, orcid=None,
        wf_type="Galaxy", include_files=files_list, prov_name="test_prov"
    )
    assert isinstance(wf_crate, ROCrate)

    # wf = wf_crate.dereference(wf_id)

    out_path = test_data_dir / export_dir / "history_export_ro_crate"
    if not os.path.exists(out_path):
        out_path.mkdir()
    wf_crate.write(out_path)
