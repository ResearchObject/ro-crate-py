import sys
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
    print(jobs[0])
    assert len(jobs) == 4

def test_ga_history_parsing(test_data_dir, tmpdir, helpers):
    export_dir = "test_ga_history_export"
    export_path = test_data_dir / export_dir / "history_export"
    
    # metadata_export = load_ga_history_export(export_path)
    prov = ProvenanceProfile(export_path, "PDG", "https://orcid.org/0000-0002-8940-4946")
    # print(len(metadata_export['jobs_attrs']))
    print(prov.document.serialize(format="rdf", rdf_format="turtle"))
    with open("test_prov.ttl","w") as provenance_file:
            prov.document.serialize(provenance_file,format="rdf", rdf_format="turtle")
    assert isinstance(prov, ProvenanceProfile)


def test_create_wf_run_ro_crate(test_data_dir, tmpdir, helpers):
    wf_id = 'test_galaxy_wf.ga'
    wf_path = test_data_dir / wf_id
    wf_crate = roc_api.make_workflow_rocrate(wf_path, wf_type='Galaxy')
    assert isinstance(wf_crate, ROCrate)

    wf = wf_crate.dereference(wf_id)
    assert wf._default_type == "ComputationalWorkflow"
    assert wf_crate.mainEntity is wf
    lang = wf_crate.dereference(f"{WF_CRATE}#galaxy")
    assert hasattr(lang, "name")
    assert lang.version == GALAXY_DEFAULT_VERSION
    assert wf.get("programmingLanguage") is lang
    assert wf.get("subjectOf") is not None
    assert helpers.WORKFLOW_DESC_TYPES.issubset(wf["subjectOf"].type)

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    wf_crate.write(out_path)
    json_entities = helpers.read_json_entities(out_path)
    helpers.check_wf_crate(json_entities, wf_id)
    wf_entity = json_entities[wf_id]
    assert "subjectOf" in wf_entity
    abstract_wf_id = wf_entity["subjectOf"]["@id"]
    abstract_wf_entity = json_entities[abstract_wf_id]
    assert helpers.WORKFLOW_DESC_TYPES.issubset(abstract_wf_entity["@type"])

    wf_out_path = out_path / wf_id
    assert wf_out_path.exists()
    with open(wf_path) as f1, open(wf_out_path) as f2:
        assert f1.read() == f2.read()

    abstract_wf_out_path = out_path / abstract_wf_id
    assert abstract_wf_out_path.exists()