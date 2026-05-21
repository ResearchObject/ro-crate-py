# Copyright 2019-2026 The University of Manchester, UK
# Copyright 2020-2026 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2026 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2026 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2026 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2026 Data Centre, SciLifeLab, SE
# Copyright 2024-2026 National Institute of Informatics (NII), JP
# Copyright 2025-2026 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025-2026 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
# Copyright 2026 Spanish National Research Council (CSIC), ES
# Copyright 2026 Helmholtz-Zentrum Dresden-Rossendorf (HZDR), DE
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

"""
RO-Crate Generator
==================
Generates multiple example RO-Crates that exercise the various features of
the RO-Crate specification (https://www.researchobject.org/ro-crate/specification/1.2/).

Usage examples:
    # Generate 10 crates with default settings
    python generate_ro_crates.py --count 10 --output-dir ./crates

    # Generate 100 crates, mix of 1.1 and 1.2, both attached and detached
    python generate_ro_crates.py --count 100 --output-dir ./crates \
        --versions 1.1 1.2 --crate-types attached detached
"""

import argparse
import json
import random
import shutil
import string
import sys
import textwrap
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from rocrate.model.contextentity import ContextEntity
from rocrate.model.testservice import get_service, SERVICE_MAP
from rocrate.rocrate import ROCrate
from rocrate.utils import iso_now

# ---------------------------------------------------------------------------
# Vocabulary data pools
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "Dave", "Elena", "Frank", "Grace", "Hiro",
    "Ingrid", "James", "Keiko", "Luca", "Maria", "Nadia", "Omar", "Petra",
    "Qiang", "Rosa", "Sven", "Tae-yang", "Uma", "Victor", "Wanjiru", "Xin",
    "Yuki", "Zara",
]
LAST_NAMES = [
    "Andersen", "Bauer", "Chen", "Dlamini", "Eriksson", "Ferreira", "Garcia",
    "Hoffmann", "Inoue", "Johansson", "Kim", "Larsson", "Martinez", "Nakamura",
    "Olsen", "Patel", "Quinn", "Rossi", "Santos", "Tanaka", "Ueda", "Vasquez",
    "Wang", "Xu", "Yamamoto", "Zhang",
]
UNIVERSITIES = [
    "University of Example",
    "Institute for Advanced Studies",
    "Global Research University",
    "National Centre for Computational Science",
    "European Institute of Technology",
    "Pacific Research Consortium",
    "Open Science Foundation",
]
LICENSES = [
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by-sa/4.0/",
    "https://creativecommons.org/licenses/by-nc/4.0/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "https://opensource.org/licenses/MIT",
    "https://www.apache.org/licenses/LICENSE-2.0",
]
KEYWORDS = [
    "genomics", "proteomics", "climate-science", "machine-learning",
    "image-analysis", "bioinformatics", "astronomy", "materials-science",
    "epidemiology", "ecology", "neuroscience", "pharmacology",
    "data-mining", "simulation", "remote-sensing", "archaeology",
]
WORKFLOW_LANGUAGES = [
    ("cwl", "https://w3id.org/cwl/v1.2", "Common Workflow Language"),
    ("nextflow", "https://nextflow.io", "Nextflow"),
    ("snakemake", "https://snakemake.readthedocs.io", "Snakemake"),
    ("galaxy", "https://galaxyproject.org", "Galaxy"),
]
ENCODINGS = [
    ("text/csv", ".csv"),
    ("application/json", ".json"),
    ("text/plain", ".txt"),
    ("application/pdf", ".pdf"),
    ("image/png", ".png"),
    ("image/svg+xml", ".svg"),
    ("application/x-hdf5", ".h5"),
    ("application/zip", ".zip"),
    ("text/tab-separated-values", ".tsv"),
    ("application/vnd.ms-excel", ".xlsx"),
]
INSTRUMENT_TYPES = [
    "Microscope", "Sequencer", "Spectrometer", "Telescope",
    "MRI Scanner", "Flow Cytometer", "Mass Spectrometer",
]
GRANT_FUNDERS = [
    "National Science Foundation",
    "European Research Council",
    "Wellcome Trust",
    "NIH",
    "EPSRC",
    "DFG",
    "ANR",
]
PLACE_NAMES = [
    "Berlin, Germany", "Cambridge, UK", "Nairobi, Kenya",
    "São Paulo, Brazil", "Singapore", "Melbourne, Australia",
    "Toronto, Canada", "Tokyo, Japan",
]
TEST_SERVICES = list(SERVICE_MAP)
PROFILES = {
    "minimal": "Minimal crate: root entity + a few files, no extras.",
    "files": "Data files with rich file-level metadata.",
    "dataset": "Directory datasets + nested datasets.",
    "remote": "Remote (URL) data entities.",
    "people": "Multiple Person contextual entities with ORCID-style IDs.",
    "provenance": "CreateAction / UpdateAction provenance chains.",
    "workflow": "ComputationalWorkflow entity with language and tools.",
    "instrument": "Instrument and equipment contextual entities.",
    "geo": "Geospatial place / geo coverage entities.",
    "license": "Per-entity licensing and rights statements.",
    "software": "SoftwareApplication / SoftwareSourceCode entities.",
    "event": "Event contextual entities.",
    "subcrate": "Nested sub-crates inside the root crate.",
    "collection": "A Dataset with hasPart references.",
    "funding": "Grant / funder entities.",
    "scholarly": "ScholarlyArticle / publication entities.",
    "testing": "Test-suite metadata (Life Monitor style).",
}

ALL_PROFILE_NAMES = list(PROFILES.keys())

# ---------------------------------------------------------------------------
# RO-Crate profile URIs
#
# When a generated crate uses one of these feature-profiles, the root data
# entity's conformsTo property references the corresponding RO-Crate Profile
# URI and a matching contextual entity (type: CreativeWork + Profile) is added.
# ---------------------------------------------------------------------------
PROFILE_URIS: dict[str, tuple[str, str, str]] = {
    # feature key → (profile URI, human name, version string)
    "workflow": (
        "https://w3id.org/workflowhub/workflow-ro-crate/1.0",
        "Workflow RO-Crate",
        "1.0",
    ),
    "testing": (
        "https://w3id.org/ro/wftest/0.1",
        "Workflow Testing RO-Crate",
        "0.1",
    ),
}

# ---------------------------------------------------------------------------
# Extra JSON-LD context entries required by certain feature-profiles.
#
# The base RO-Crate context covers Schema.org, Bioschemas, PCDM, etc.
# Terms used by the "testing" profile (TestSuite, TestInstance, …) live in a
# separate namespace that must be appended to @context.
# ---------------------------------------------------------------------------
PROFILE_EXTRA_CONTEXTS: dict[str, str] = {
    # feature key → additional context URL to append
    "testing": "https://w3id.org/ro/terms/test",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rand_str(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _rand_date(start_year: int = 2018, end_year: int = 2024) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).isoformat()


def _rand_person_id() -> str:
    # Fake ORCID-like URI
    parts = [f"{random.randint(0, 9999):04d}" for _ in range(4)]
    return "https://orcid.org/" + "-".join(parts)


def _rand_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _rand_doi() -> str:
    return f"https://doi.org/10.{random.randint(1000, 9999)}/{_rand_str(8)}"


def _make_dummy_file(path: Path, encoding: str) -> None:
    """Write minimal plausible content for a dummy file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if encoding == "text/csv":
        path.write_text("id,value,label\n1,0.5,control\n2,1.2,treated\n")
    elif encoding == "application/json":
        path.write_text(json.dumps({"version": 1, "data": [1, 2, 3]}) + "\n")
    elif encoding in ("image/png", "image/svg+xml"):
        path.write_bytes(b"\x89PNG\r\n\x1a\n" if encoding == "image/png"
                         else b"<svg xmlns='http://www.w3.org/2000/svg'/>")
    elif encoding == "application/pdf":
        path.write_bytes(b"%PDF-1.4\n%EOF\n")
    else:
        path.write_text(f"# {path.stem}\nGenerated example content.\n")


# ---------------------------------------------------------------------------
# Feature-module builders  (each returns list of entity ids added)
# ---------------------------------------------------------------------------

def _add_people(crate: ROCrate, rng: random.Random, n: int = 3) -> list:
    people = []
    for _ in range(n):
        pid = _rand_person_id()
        affil_id = f"#{_rand_str(6)}-org"
        org = crate.add(ContextEntity(crate, affil_id, properties={
            "@type": "Organization",
            "name": rng.choice(UNIVERSITIES),
            "url": f"https://example.org/{_rand_str(5)}",
        }))
        person = crate.add(ContextEntity(crate, pid, properties={
            "@type": "Person",
            "name": _rand_name(),
            "email": f"{_rand_str(6)}@example.org",
            "affiliation": org,
        }))
        people.append(person)
    return people


def _add_files(
    crate: ROCrate,
    rng: random.Random,
    staging_dir: Path,
    n: int = 4,
    base_url: str = "",
) -> list:
    """Add file data entities.

    When *base_url* is non-empty the crate is detached: entities are added
    with an absolute URL ``@id`` (no local file is copied into the crate).
    """
    entities = []
    for i in range(n):
        enc, ext = rng.choice(ENCODINGS)
        fname = f"data_{i:02d}_{_rand_str(4)}{ext}"
        props: dict[str, Any] = {
            "name": fname.split(".")[0].replace("_", " ").title(),
            "encodingFormat": enc,
            "description": f"Example {enc} data file.",
            "dateCreated": _rand_date(),
        }
        if rng.random() < 0.4:
            props["license"] = {"@id": rng.choice(LICENSES)}
        if base_url:
            # Detached: use absolute URL as @id, no local source file
            url = f"{base_url.rstrip('/')}/{fname}"
            ent = crate.add_file(url, fetch_remote=False, properties=props)
        else:
            fpath = staging_dir / fname
            _make_dummy_file(fpath, enc)
            props["contentSize"] = str(fpath.stat().st_size)
            ent = crate.add_file(str(fpath), properties=props)
        entities.append(ent)
    return entities


def _add_dataset(
    crate: ROCrate,
    rng: random.Random,
    staging_dir: Path,
    base_url: str = "",
) -> list:
    ds_name = f"dataset_{_rand_str(5)}"
    props: dict[str, Any] = {
        "name": ds_name.replace("_", " ").title(),
        "description": "A grouped dataset of related files.",
        "datePublished": _rand_date(),
    }
    if base_url:
        # Detached: reference as a web-based Dataset
        url = f"{base_url.rstrip('/')}/{ds_name}/"
        ds = crate.add_file(url, fetch_remote=False, properties={
            **props,
            "@type": "Dataset",
        })
    else:
        ds_dir = staging_dir / ds_name
        ds_dir.mkdir(parents=True, exist_ok=True)
        n_files = rng.randint(2, 5)
        for i in range(n_files):
            enc, ext = rng.choice(ENCODINGS)
            fpath = ds_dir / f"item_{i:02d}{ext}"
            _make_dummy_file(fpath, enc)
        ds = crate.add_dataset(str(ds_dir), properties=props)
    return [ds]


def _add_remote_entities(crate: ROCrate, rng: random.Random, n: int = 2) -> list:
    entities = []
    domains = ["zenodo.org", "figshare.com", "github.com", "data.example.org"]
    for _ in range(n):
        url = f"https://{rng.choice(domains)}/files/{_rand_str(8)}.zip"
        enc, _ = rng.choice(ENCODINGS)
        ent = crate.add_file(url, fetch_remote=False, properties={
            "name": f"Remote resource {_rand_str(4)}",
            "encodingFormat": enc,
            "description": "A remotely referenced data resource.",
            "contentUrl": url,
        })
        entities.append(ent)
    return entities


def _add_provenance(
    crate: ROCrate,
    rng: random.Random,
    people: list,
    data_entities: list,
) -> None:
    if not data_entities:
        return
    action_id = f"#action-{_rand_str(8)}"
    inputs = rng.sample(data_entities, k=min(2, len(data_entities)))
    outputs = rng.sample(data_entities, k=min(1, len(data_entities)))
    props: dict[str, Any] = {
        "@type": "CreateAction",
        "name": "Data processing step",
        "description": "Automated transformation of input data to output.",
        "startTime": _rand_date() + "T09:00:00",
        "endTime": _rand_date() + "T11:30:00",
        "object": [{"@id": e.id} for e in inputs],
        "result": [{"@id": e.id} for e in outputs],
    }
    if people:
        props["agent"] = {"@id": rng.choice(people).id}
    crate.add(ContextEntity(crate, action_id, properties=props))

    # Optional: an UpdateAction
    if rng.random() < 0.5 and data_entities:
        upd_id = f"#update-{_rand_str(8)}"
        target = rng.choice(data_entities)
        crate.add(ContextEntity(crate, upd_id, properties={
            "@type": "UpdateAction",
            "name": "Metadata correction",
            "object": {"@id": target.id},
            "startTime": _rand_date() + "T14:00:00",
        }))


def _add_workflow(
    crate: ROCrate,
    rng: random.Random,
    staging_dir: Path,
    people: list,
    base_url: str = "",
) -> list:
    lang_key, lang_url, lang_name = rng.choice(WORKFLOW_LANGUAGES)
    ext_map = {"cwl": ".cwl", "nextflow": ".nf",
               "snakemake": "Snakefile", "galaxy": ".ga"}
    ext = ext_map.get(lang_key, ".wf")
    wf_name = f"workflow_{_rand_str(5)}{ext}"

    # Language entity
    lang_id = f"#{lang_key}-lang"
    crate.add(ContextEntity(crate, lang_id, properties={
        "@type": ["ComputerLanguage", "SoftwareApplication"],
        "name": lang_name,
        "url": {"@id": lang_url},
        "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}",
    }))

    wf_props: dict[str, Any] = {
        "@type": ["File", "SoftwareSourceCode", "ComputationalWorkflow"],
        "name": f"{lang_name} analysis pipeline",
        "description": "A computational workflow for data analysis.",
        "programmingLanguage": {"@id": lang_id},
        "dateCreated": _rand_date(),
    }
    if people:
        wf_props["creator"] = {"@id": rng.choice(people).id}
    if rng.random() < 0.5:
        wf_props["license"] = {"@id": rng.choice(LICENSES)}

    if base_url:
        wf_url = f"{base_url.rstrip('/')}/{wf_name}"
        wf_entity = crate.add_file(wf_url, fetch_remote=False, properties=wf_props)
    else:
        wf_path = staging_dir / wf_name
        wf_path.write_text(
            f"# Example {lang_name} workflow\n"
            "# Auto-generated placeholder\n"
            f"# Version: {random.randint(1, 5)}.{random.randint(0, 9)}\n"
        )
        wf_entity = crate.add_file(str(wf_path), properties=wf_props)

    # Optional: SoftwareApplication tool used by the workflow
    if rng.random() < 0.6:
        tool_id = f"#tool-{_rand_str(6)}"
        crate.add(ContextEntity(crate, tool_id, properties={
            "@type": "SoftwareApplication",
            "name": f"AnalysisTool-{_rand_str(4).upper()}",
            "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}",
            "url": f"https://example.org/tool/{_rand_str(6)}",
            "softwareRequirements": f"Python >= 3.{random.randint(8, 12)}",
        }))
        wf_entity["softwareRequirements"] = {"@id": tool_id}

    # Mark as mainEntity of the crate
    crate.root_dataset["mainEntity"] = {"@id": wf_entity.id}
    return [wf_entity]


def _add_instrument(crate: ROCrate, rng: random.Random) -> list:
    inst_id = f"#instrument-{_rand_str(6)}"
    inst = crate.add(ContextEntity(crate, inst_id, properties={
        "@type": ["Thing", "IndividualProduct"],
        "name": rng.choice(INSTRUMENT_TYPES),
        "description": "Research instrument used for data acquisition.",
        "manufacturer": rng.choice(UNIVERSITIES),
        "serialNumber": f"SN-{random.randint(10000, 99999)}",
        "model": f"Model-{_rand_str(4).upper()}",
    }))
    return [inst]


def _add_geo(crate: ROCrate, rng: random.Random) -> None:
    place_id = f"#place-{_rand_str(6)}"
    lat = round(rng.uniform(-60, 70), 4)
    lon = round(rng.uniform(-180, 180), 4)
    geo_id = f"#geo-{_rand_str(6)}"
    crate.add(ContextEntity(crate, geo_id, properties={
        "@type": "GeoCoordinates",
        "latitude": str(lat),
        "longitude": str(lon),
    }))
    crate.add(ContextEntity(crate, place_id, properties={
        "@type": "Place",
        "name": rng.choice(PLACE_NAMES),
        "geo": {"@id": geo_id},
        "description": "Geographic location where data was collected.",
    }))
    crate.root_dataset["spatialCoverage"] = {"@id": place_id}


def _add_software(
    crate: ROCrate,
    rng: random.Random,
    staging_dir: Path,
    base_url: str = "",
) -> list:
    script_name = f"script_{_rand_str(5)}.py"
    props: dict[str, Any] = {
        "@type": ["File", "SoftwareSourceCode"],
        "name": script_name.replace("_", " ").replace(".py", ""),
        "programmingLanguage": "Python",
        "runtimePlatform": f"Python {random.randint(3, 3)}.{random.randint(9, 12)}",
        "description": "Analysis script.",
        "codeRepository": f"https://github.com/example/{_rand_str(8)}",
        "version": f"{random.randint(0, 2)}.{random.randint(1, 9)}.{random.randint(0, 5)}",
    }
    if base_url:
        url = f"{base_url.rstrip('/')}/{script_name}"
        sw = crate.add_file(url, fetch_remote=False, properties=props)
    else:
        script_path = staging_dir / script_name
        script_path.write_text(
            "#!/usr/bin/env python3\n"
            "# Auto-generated script\n"
            "import sys\n\n"
            "def main():\n"
            "    print('Hello, RO-Crate!')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        sw = crate.add_file(str(script_path), properties=props)
    return [sw]


def _add_event(crate: ROCrate, rng: random.Random) -> None:
    ev_id = f"#event-{_rand_str(6)}"
    start = _rand_date(2019, 2023)
    end_d = date.fromisoformat(start) + timedelta(days=rng.randint(1, 5))
    crate.add(ContextEntity(crate, ev_id, properties={
        "@type": "Event",
        "name": f"Workshop on {rng.choice(KEYWORDS).replace('-', ' ').title()}",
        "startDate": start,
        "endDate": end_d.isoformat(),
        "location": rng.choice(PLACE_NAMES),
        "description": "A scientific event at which this crate's data was produced.",
    }))
    crate.root_dataset["about"] = {"@id": ev_id}


def _add_funding(crate: ROCrate, rng: random.Random) -> None:
    funder_id = f"#funder-{_rand_str(6)}"
    grant_id = f"#grant-{_rand_str(6)}"
    funder_name = rng.choice(GRANT_FUNDERS)
    crate.add(ContextEntity(crate, funder_id, properties={
        "@type": "Organization",
        "name": funder_name,
        "url": f"https://example.org/funder/{_rand_str(5)}",
    }))
    crate.add(ContextEntity(crate, grant_id, properties={
        "@type": "Grant",
        "name": f"Grant {random.randint(100000, 999999)}",
        "identifier": f"{funder_name[:3].upper()}-{random.randint(10000, 99999)}",
        "funder": {"@id": funder_id},
        "description": "Research grant that funded this work.",
    }))
    crate.root_dataset["funding"] = {"@id": grant_id}
    crate.root_dataset["funder"] = {"@id": funder_id}


def _add_scholarly_article(
    crate: ROCrate,
    rng: random.Random,
    people: list,
) -> None:
    art_id = _rand_doi()
    props: dict[str, Any] = {
        "@type": "ScholarlyArticle",
        "name": f"Study of {rng.choice(KEYWORDS).replace('-', ' ').title()}",
        "datePublished": _rand_date(2018, 2024),
        "identifier": art_id,
        "url": art_id,
        "description": "A peer-reviewed article related to this dataset.",
    }
    if people:
        props["author"] = [{"@id": p.id} for p in rng.sample(
            people, k=min(len(people), rng.randint(1, 3))
        )]
    crate.add(ContextEntity(crate, art_id, properties=props))
    crate.root_dataset["citation"] = {"@id": art_id}


def _add_collection(
    crate: ROCrate,
    rng: random.Random,
    data_entities: list,
) -> None:
    if not data_entities:
        return
    col_id = f"#collection-{_rand_str(6)}"
    members = rng.sample(data_entities, k=min(len(data_entities), rng.randint(2, 4)))
    crate.add(ContextEntity(crate, col_id, properties={
        "@type": "Dataset",
        "name": "Curated collection",
        "description": "A logical grouping of selected data entities.",
        "hasPart": [{"@id": e.id} for e in members],
    }))


def _add_subcrate(
    crate: ROCrate,
    rng: random.Random,
    staging_dir: Path,
) -> None:
    sub_dest = f"subcrate_{_rand_str(5)}/"
    subcrate_entity = crate.add_subcrate(dest_path=sub_dest)
    subcrate_obj = subcrate_entity.get_crate()
    # Add a file to the subcrate
    sub_staging = staging_dir / sub_dest.rstrip("/")
    sub_staging.mkdir(parents=True, exist_ok=True)
    enc, ext = rng.choice(ENCODINGS)
    subf_path = sub_staging / f"sub_data{ext}"
    _make_dummy_file(subf_path, enc)
    subcrate_obj.add_file(str(subf_path), properties={
        "name": "Subcrate data file",
        "encodingFormat": enc,
    })
    subcrate_obj.root_dataset["name"] = "Nested sub-crate"
    subcrate_obj.root_dataset["description"] = "A nested RO-Crate inside the root crate."


def _add_testing_metadata(crate: ROCrate, rng: random.Random) -> None:
    """Adds workflow testing metadata."""
    suite_id = f"#test-suite-{_rand_str(5)}"
    instance_id = f"#test-instance-{_rand_str(5)}"
    service = rng.choice([get_service(crate, _) for _ in TEST_SERVICES])

    crate.add(service)
    crate.add(ContextEntity(crate, suite_id, properties={
        "@type": "TestSuite",
        "name": f"Test suite {_rand_str(4).upper()}",
        "instance": [{"@id": instance_id}],
    }))
    crate.add(ContextEntity(crate, instance_id, properties={
        "@type": "TestInstance",
        "name": "CI instance",
        "runsOn": service,
        "url": f"https://ci.example.org/jobs/{_rand_str(8)}",
        "resource": "jobs",
    }))
    crate.root_dataset["mentions"] = [{"@id": suite_id}]


# ---------------------------------------------------------------------------
# Core crate builder
# ---------------------------------------------------------------------------

def _choose_profiles(rng: random.Random, allowed: list[str]) -> list[str]:
    """Pick a random non-empty subset of profiles, always including 'minimal'."""
    chosen = ["minimal"]
    others = [p for p in allowed if p != "minimal"]
    k = rng.randint(1, min(len(others), 6))
    chosen += rng.sample(others, k=k)
    if "testing" in chosen and "workflow" not in chosen:
        chosen.append("workflow")
    return chosen


def _add_profile_conformance(crate: ROCrate, profiles: list[str]) -> None:
    """
    For each active feature-profile that maps to a known RO-Crate profile URI,
    add a conformsTo reference on the root data entity and a matching contextual
    entity (type CreativeWork + Profile) to the graph.
    """
    conforms_to = []
    for feature in profiles:
        if feature not in PROFILE_URIS:
            continue
        uri, name, version = PROFILE_URIS[feature]
        # Add (or reuse) the profile contextual entity
        existing = crate.dereference(uri)
        if existing is None:
            crate.add(ContextEntity(crate, uri, properties={
                "@type": ["CreativeWork", "Profile"],
                "name": name,
                "version": version,
            }))
        conforms_to.append({"@id": uri})

    if conforms_to:
        existing_ct = crate.root_dataset.get("conformsTo")
        if existing_ct is None:
            crate.root_dataset["conformsTo"] = (
                conforms_to[0] if len(conforms_to) == 1 else conforms_to
            )
        else:
            # Merge with any existing value
            if isinstance(existing_ct, list):
                crate.root_dataset["conformsTo"] = existing_ct + conforms_to
            else:
                crate.root_dataset["conformsTo"] = [existing_ct] + conforms_to


def _build_metadata_json(crate: ROCrate, profiles: list[str],
                         meta_id: str, root_id: str) -> dict:
    """
    Call crate.metadata.generate(), then patch the resulting document to:
      1. Fix the metadata descriptor's @id to *meta_id* (e.g. "prefix-ro-crate-metadata.json").
      2. Fix the root data entity's @id to *root_id* (e.g. an absolute URL).
      3. Expand @context to a list when extra profile contexts are needed.
    """
    doc = crate.metadata.generate()

    # --- 1 & 2: patch @ids in the @graph ---
    # The library always emits the root as "./" and the descriptor as
    # "ro-crate-metadata.json" (or "ro-crate-metadata.jsonld" for 1.0).
    lib_descriptor_id = crate.metadata.id        # e.g. "ro-crate-metadata.json"
    lib_root_id = crate.root_dataset.id          # e.g. "./"

    graph = doc.get("@graph", [])
    for entity in graph:
        eid = entity.get("@id", "")
        if eid == lib_descriptor_id:
            entity["@id"] = meta_id
            # Update "about" to point to the new root @id
            entity["about"] = {"@id": root_id}
        elif eid == lib_root_id:
            entity["@id"] = root_id
        else:
            # Also fix any property values that referenced the old root @id
            for key, val in entity.items():
                if key in ("@id", "@type"):
                    continue
                if isinstance(val, dict) and val.get("@id") == lib_root_id:
                    entity[key] = {"@id": root_id}
                elif isinstance(val, list):
                    entity[key] = [
                        ({"@id": root_id} if isinstance(v, dict)
                         and v.get("@id") == lib_root_id else v)
                        for v in val
                    ]

    return doc


def build_crate(
    crate_index: int,
    output_dir: Path,
    version: str,
    crate_type: str,  # "attached", "detached", "zip"
    profiles: list[str],
    rng: random.Random,
    verbose: bool = False,
) -> dict:
    """
    Build one RO-Crate and write it to disk.

    Returns a summary dict.
    """
    crate_id = f"crate_{crate_index:04d}_{_rand_str(6)}"
    staging_dir = output_dir / "_staging" / crate_id
    staging_dir.mkdir(parents=True, exist_ok=True)

    # For detached crates, all data entity @ids must be absolute URLs.
    # We use a synthetic base URL derived from the crate_id.
    is_detached = crate_type == "detached"
    base_url = f"http://example.org/crates/{crate_id}/" if is_detached else ""

    try:
        crate = ROCrate(version=version)

        # --- Root dataset metadata ---
        root_keywords = rng.sample(KEYWORDS, k=rng.randint(1, 4))
        root_date = _rand_date()
        root_license = rng.choice(LICENSES)

        crate.root_dataset["name"] = f"Example RO-Crate #{crate_index}"
        crate.root_dataset["description"] = (
            f"Auto-generated RO-Crate demonstrating: {', '.join(profiles)}."
        )
        crate.root_dataset["datePublished"] = root_date
        crate.root_dataset["license"] = {"@id": root_license}
        crate.root_dataset["keywords"] = ", ".join(root_keywords)
        crate.root_dataset["identifier"] = _rand_doi()

        # Track everything added
        people: list = []
        data_entities: list = []
        we = None

        # ---- Apply feature profiles ----
        if "people" in profiles or rng.random() < 0.7:
            n_people = rng.randint(1, 5)
            people = _add_people(crate, rng, n=n_people)
            if people:
                crate.root_dataset["author"] = [{"@id": p.id} for p in people]

        if "files" in profiles or "minimal" in profiles:
            n_files = rng.randint(2, 7)
            fe = _add_files(crate, rng, staging_dir, n=n_files, base_url=base_url)
            data_entities.extend(fe)

        if "dataset" in profiles:
            de = _add_dataset(crate, rng, staging_dir, base_url=base_url)
            data_entities.extend(de)

        if "remote" in profiles:
            re_ = _add_remote_entities(crate, rng, n=rng.randint(1, 3))
            data_entities.extend(re_)

        if "provenance" in profiles:
            _add_provenance(crate, rng, people, data_entities)

        if "workflow" in profiles:
            we = _add_workflow(crate, rng, staging_dir, people, base_url=base_url)
            data_entities.extend(we)

        if "instrument" in profiles:
            ie = _add_instrument(crate, rng)
            if ie and data_entities:
                data_entities[0]["instrument"] = {"@id": ie[0].id}

        if "geo" in profiles:
            _add_geo(crate, rng)

        if "software" in profiles:
            se = _add_software(crate, rng, staging_dir, base_url=base_url)
            data_entities.extend(se)

        if "event" in profiles:
            _add_event(crate, rng)

        if "funding" in profiles:
            _add_funding(crate, rng)

        if "scholarly" in profiles:
            _add_scholarly_article(crate, rng, people)

        if "collection" in profiles:
            _add_collection(crate, rng, data_entities)

        # subcrate is not meaningful for detached crates; skip silently
        if "subcrate" in profiles and not is_detached:
            _add_subcrate(crate, rng, staging_dir)

        if "testing" in profiles:
            _add_testing_metadata(crate, rng)

        if "license" in profiles:
            # Per-entity license overrides
            for ent in rng.sample(data_entities, k=min(len(data_entities), 3)):
                ent["license"] = {"@id": rng.choice(LICENSES)}

        # ---- Add conformsTo for any recognised RO-Crate profiles ----
        _add_profile_conformance(crate, profiles)

        # expand @context when needed
        for feature, ctx_url in PROFILE_EXTRA_CONTEXTS.items():
            if feature in profiles:
                crate.metadata.extra_contexts.append(ctx_url)

        # --- Write the crate ---
        if crate_type == "zip":
            zip_path = output_dir / f"{crate_id}.zip"
            crate.write_zip(str(zip_path))
            dest_str = str(zip_path)

        elif crate_type == "detached":
            # Detached: a single standalone metadata file.
            # Filename follows the <prefix>-ro-crate-metadata.json convention.
            # The root data entity @id is an absolute URL; the descriptor @id
            # is always "ro-crate-metadata.json" per the spec.
            root_url = base_url  # e.g. "http://example.org/crates/crate_0001_abc/"
            meta_file_id = "ro-crate-metadata.json"  # spec-mandated descriptor @id
            doc = _build_metadata_json(
                crate, profiles,
                meta_id=meta_file_id,
                root_id=root_url,
            )
            meta_filename = f"{crate_id}-ro-crate-metadata.json"
            meta_path = output_dir / meta_filename
            meta_path.write_text(json.dumps(doc, indent=2))
            dest_str = str(meta_path)

        else:
            # Attached: full directory with data files
            dest = output_dir / crate_id
            crate.write(str(dest))
            dest_str = str(dest)

        summary = {
            "index": crate_index,
            "id": crate_id,
            "version": version,
            "crate_type": crate_type,
            "profiles": profiles,
            "n_data_entities": len(data_entities),
            "n_people": len(people),
            "output": dest_str,
        }

        if verbose:
            print(f"  [{crate_index:04d}] {crate_id}")
            print(f"         version={version}  type={crate_type}")
            print(f"         profiles={profiles}")
            print(f"         entities={len(data_entities)}  people={len(people)}")
            print(f"         → {dest_str}")

        return summary

    finally:
        # Clean up staging directory
        shutil.rmtree(staging_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_ro_crates",
        description=textwrap.dedent("""\
            Generate multiple example RO-Crates exercising the various features
            of the RO-Crate specification (https://www.researchobject.org/ro-crate/).
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
            Available profiles:
            {chr(10).join(f'  {k:<12} {v}' for k, v in PROFILES.items())}

            Examples:
              %(prog)s --count 10 --output-dir ./crates
              %(prog)s --count 100 --versions 1.1 1.2 --crate-types attached zip
              %(prog)s --count 20 --seed 42 --profiles workflow provenance dataset
              %(prog)s --count 5  --verbose --report summary.json
        """),
    )

    parser.add_argument(
        "--count", "-n",
        type=int,
        default=10,
        metavar="N",
        help="Number of RO-Crates to generate (default: 10).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("ro_crates_output"),
        metavar="DIR",
        help="Directory where crates will be written (default: ro_crates_output/).",
    )
    parser.add_argument(
        "--versions",
        nargs="+",
        default=["1.2"],
        choices=["1.0", "1.1", "1.2"],
        metavar="VER",
        help="RO-Crate spec version(s) to use. Multiple values rotate randomly. "
             "Choices: 1.0, 1.1, 1.2 (default: 1.2).",
    )
    parser.add_argument(
        "--crate-types",
        nargs="+",
        default=["attached"],
        choices=["attached", "detached", "zip"],
        metavar="TYPE",
        help="Output format(s). Multiple values rotate randomly. "
             "attached=directory with files, detached=metadata-only directory, "
             "zip=zipped archive (default: attached).",
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=None,
        choices=ALL_PROFILE_NAMES,
        metavar="PROFILE",
        help="Restrict feature profiles to this list. "
             "If omitted, a random subset is chosen per crate. "
             f"Choices: {', '.join(ALL_PROFILE_NAMES)}.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="INT",
        help="Random seed for reproducibility (default: random).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        metavar="FILE",
        help="Write a JSON summary report to this file.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print details about each generated crate.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove output-dir before generating (CAUTION: deletes existing data).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Set up RNG
    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)
    print(f"RO-Crate Generator  |  seed={seed}  count={args.count}")

    # Prepare output directory
    out = args.output_dir.resolve()
    if args.clean and out.exists():
        print(f"Removing existing output directory: {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {out}")

    # Determine allowed profiles
    allowed_profiles = args.profiles if args.profiles else ALL_PROFILE_NAMES

    summaries = []
    errors = []

    print(f"\nGenerating {args.count} crate(s) …")
    if args.verbose:
        print()

    for i in range(1, args.count + 1):
        version = rng.choice(args.versions)
        crate_type = rng.choice(args.crate_types)
        profiles = _choose_profiles(rng, allowed_profiles)

        try:
            summary = build_crate(
                crate_index=i,
                output_dir=out,
                version=version,
                crate_type=crate_type,
                profiles=profiles,
                rng=rng,
                verbose=args.verbose,
            )
            summaries.append(summary)
        except Exception as exc:  # noqa: BLE001
            msg = f"  [FAILED] crate #{i}: {exc}"
            print(msg, file=sys.stderr)
            errors.append({"index": i, "error": str(exc)})

        # Simple non-verbose progress
        if not args.verbose and i % 10 == 0:
            print(f"  … {i}/{args.count} done")

    # Clean up any leftover staging directory
    staging = out / "_staging"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)

    # Summary
    print(f"\n{'='*60}")
    print(f"Done.  {len(summaries)} succeeded, {len(errors)} failed.")
    print(f"Versions used:    {sorted({s['version'] for s in summaries})}")
    print(f"Types used:       {sorted({s['crate_type'] for s in summaries})}")
    profile_counts: dict[str, int] = {}
    for s in summaries:
        for p in s["profiles"]:
            profile_counts[p] = profile_counts.get(p, 0) + 1
    print("Profile usage:")
    for prof, cnt in sorted(profile_counts.items(), key=lambda x: -x[1]):
        bar = "█" * (cnt * 20 // max(args.count, 1))
        print(f"  {prof:<12} {cnt:4d}  {bar}")

    # Optional report
    report = {
        "generated": iso_now(),
        "seed": seed,
        "count_requested": args.count,
        "count_succeeded": len(summaries),
        "count_failed": len(errors),
        "output_dir": str(out),
        "crates": summaries,
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print(f"\nReport written to: {args.report}")
    else:
        report_path = out / "generation_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        print(f"\nReport written to: {report_path}")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
