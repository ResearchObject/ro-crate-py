import sys
import os
import pytest
from typing import (
    Tuple,
)
from prov.model import ProvDocument
sys.path.append('./ro-crate-py')
from rocrate.rocrate import ROCrate
from rocrate import rocrate_api as roc_api
from rocrate.model.computerlanguage import CWL_DEFAULT_VERSION, GALAXY_DEFAULT_VERSION
from rocrate.provenance_profile import ProvenanceProfile

WF_CRATE = "https://w3id.org/workflowhub/workflow-ro-crate"
from tools.load_ga_export import load_ga_history_export, GalaxyJob, GalaxyDataset

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
    # print(jobs[0])
    assert len(jobs) == 4

def test_ga_history_parsing(test_data_dir, tmpdir, helpers):
    export_dir = "test_ga_history_export"
    export_path = test_data_dir / export_dir / "history_export"
    prov_path = "provenance"
    # prov_name = "ga_export.cwlprov"
    # crate_path = test_data_dir / export_dir / "history_export_crate"
    
    # metadata_export = load_ga_history_export(export_path)
    prov = ProvenanceProfile(export_path, "PDG", "https://orcid.org/0000-0002-8940-4946")

    # print(len(metadata_export['jobs_attrs']))
    # print(prov.document.serialize(format="rdf", rdf_format="turtle"))
    # with open("test_prov.ttl","w") as provenance_file:
    #         prov.document.serialize(provenance_file,format="rdf", rdf_format="turtle")
    assert isinstance(prov, ProvenanceProfile)

    prov.finalize_prov_profile(out_path=prov_path)
    # print(serialized_prov_docs.keys())



def test_create_wf_run_ro_crate(test_data_dir, tmpdir, helpers):
    # wf_path = base_path + "example-history-export3.ga"
    # dataset_path = base_path + "example-history-export3/datasets/"
    # wfr_metadata_path = base_path + "example-history-export3"
    # files_list = os.listdir(dataset_path)
    # files_list = [dataset_path + f for f in files_list]
    
    export_dir = "test_ga_history_export"
    wfr_metadata_path = test_data_dir / export_dir / "history_export"
    dataset_path = wfr_metadata_path / "datasets"
    files_list = os.listdir(dataset_path)
    files_list = [dataset_path / f for f in files_list]
    wf_id = 'wf_definition.ga'
    wf_path = test_data_dir / export_dir / wf_id

    # wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='Galaxy')
    wf_crate = roc_api.make_workflow_run_rocrate(workflow_path=wf_path,
                        wfr_metadata_path=wfr_metadata_path, author=None, orcid=None,
                        wf_type="Galaxy",include_files=files_list, prov_name="test_prov")
    assert isinstance(wf_crate, ROCrate)

    # wf = wf_crate.dereference(wf_id)

    out_path = test_data_dir / export_dir / "history_export_ro_crate"
    if not os.path.exists(out_path):
        out_path.mkdir()
    wf_crate.write(out_path)
    