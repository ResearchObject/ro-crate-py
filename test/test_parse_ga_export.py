import sys
import pytest
from typing import (
    Tuple,
)
from prov.model import ProvDocument
sys.path.append('./ro-crate-py')
from rocrate.rocrate import ROCrate
from tools import parse_ga_export
from rocrate.provenance_profile import ProvenanceProfile

def test_ga_history_parsing(test_data_dir, tmpdir, helpers):
    export_dir = "test_ga_history_export"
    export_path = test_data_dir / export_dir
    
    metadata_export = parse_ga_export.ga_history_export(export_path)
    prov = ProvenanceProfile(metadata_export, "PDG", "https://orcid.org/0000-0002-8940-4946")
    print(len(metadata_export['jobs_attrs']))
    # print(prov.document.serialize(format="rdf", rdf_format="turtle"))
    assert isinstance(prov, ProvenanceProfile)