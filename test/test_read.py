# Copyright 2019-2025 The University of Manchester, UK
# Copyright 2020-2025 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2025 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2025 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2025 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2025 Data Centre, SciLifeLab, SE
# Copyright 2024-2025 National Institute of Informatics (NII), JP
# Copyright 2025 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
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

import json
import pytest
import shutil
import uuid
import zipfile
from pathlib import Path

from rocrate import model
from rocrate.rocrate import ROCrate, Subcrate
from rocrate.model import DataEntity, ContextEntity, File, Dataset

_URL = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/master/'
        'test/test-data/sample_file.txt')


@pytest.mark.parametrize("gen_preview,from_zip", [(False, False), (True, False), (True, True)])
def test_crate_dir_loading(test_data_dir, tmpdir, helpers, gen_preview, from_zip):
    crate_dir = test_data_dir / 'read_crate'
    if from_zip:
        zip_source = shutil.make_archive(tmpdir / "read_crate.crate", "zip", crate_dir)
        crate = ROCrate(zip_source, gen_preview=gen_preview)
    else:
        crate = ROCrate(crate_dir, gen_preview=gen_preview)

    assert crate.version == "1.2"
    assert set(_["@id"] for _ in crate.default_entities) == {
        "./",
        "ro-crate-metadata.json",
        "ro-crate-preview.html"
    }
    assert set(_["@id"] for _ in crate.data_entities) == {
        "test_galaxy_wf.ga",
        "abstract_wf.cwl",
        "test_file_galaxy.txt",
        "https://raw.githubusercontent.com/ResearchObject/ro-crate-py/master/test/test-data/sample_file.txt",
        "examples/",
        "test/",
        "with%20space.txt",
        "a%20b/",
    }
    assert set(_["@id"] for _ in crate.contextual_entities) == {"#joe"}

    root = crate.dereference('./')
    assert crate.root_dataset is root
    root_prop = root.properties()
    assert root_prop['@id'] == root.id
    assert root_prop['@id'] == './'
    assert root_prop['@type'] == 'Dataset'

    metadata = crate.dereference(helpers.METADATA_FILE_NAME)
    assert crate.metadata is metadata
    md_prop = metadata.properties()
    assert md_prop['@id'] == metadata.id
    assert md_prop['@id'] == helpers.METADATA_FILE_NAME
    assert md_prop['@type'] == 'CreativeWork'
    assert md_prop['about'] == {'@id': './'}
    assert md_prop['conformsTo'] == {'@id': "https://w3id.org/ro/crate/1.2"}
    assert metadata.root is root

    preview = crate.dereference(helpers.PREVIEW_FILE_NAME)
    assert preview == crate.preview
    preview_prop = preview.properties()
    assert preview_prop['@id'] == helpers.PREVIEW_FILE_NAME
    assert preview_prop['@id'] == preview.id
    assert preview_prop['@type'] == 'CreativeWork'
    assert preview_prop['about'] == {'@id': './'}
    if not gen_preview:
        assert Path(preview.source).name == helpers.PREVIEW_FILE_NAME
    else:
        assert not preview.source

    main_wf = crate.dereference('test_galaxy_wf.ga')
    wf_prop = main_wf.properties()
    assert wf_prop['@id'] == 'test_galaxy_wf.ga'
    assert wf_prop['@id'] == main_wf.id
    assert set(wf_prop['@type']) == helpers.WORKFLOW_TYPES
    assert wf_prop['programmingLanguage'] == {'@id': 'https://galaxyproject.org'}
    assert wf_prop['subjectOf'] == {'@id': 'abstract_wf.cwl'}

    abs_wf = crate.dereference('abstract_wf.cwl')
    abs_wf_prop = abs_wf.properties()
    assert abs_wf_prop['@id'] == 'abstract_wf.cwl'
    assert abs_wf_prop['@id'] == abs_wf.id
    assert set(abs_wf_prop['@type']) == helpers.WORKFLOW_TYPES

    wf_author = crate.dereference('#joe')
    author_prop = wf_author.properties()
    assert author_prop['@id'] == '#joe'
    assert author_prop['@id'] == wf_author.id
    assert author_prop['@type'] == 'Person'
    assert author_prop['name'] == 'Joe Bloggs'

    test_file = crate.dereference('test_file_galaxy.txt')
    test_file_prop = test_file.properties()
    assert test_file_prop['@id'] == 'test_file_galaxy.txt'
    assert test_file_prop['@id'] == test_file.id

    remote_file = crate.dereference(_URL)
    remote_file_prop = remote_file.properties()
    assert remote_file_prop['@id'] == _URL
    assert remote_file_prop['@id'] == remote_file.id

    examples_dataset = crate.dereference('examples/')
    examples_dataset_prop = examples_dataset.properties()
    assert examples_dataset_prop['@id'] == 'examples/'
    assert examples_dataset_prop['@id'] == examples_dataset.id
    assert crate.examples_dir is examples_dataset

    test_dataset = crate.dereference('test/')
    test_dataset_prop = test_dataset.properties()
    assert test_dataset_prop['@id'] == 'test/'
    assert test_dataset_prop['@id'] == test_dataset.id
    assert crate.test_dir is test_dataset

    # write the crate in a different directory
    out_path = tmpdir / 'crate_read_out'
    out_path.mkdir()
    crate.write(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    legacy_metadata_path = out_path / helpers.LEGACY_METADATA_FILE_NAME
    # legacy metadata file should just be copied over as a regular file
    assert legacy_metadata_path.exists()
    with open(crate_dir / helpers.LEGACY_METADATA_FILE_NAME) as f1, open(legacy_metadata_path) as f2:
        assert f1.read() == f2.read()
    preview_path = out_path / helpers.PREVIEW_FILE_NAME
    assert preview_path.exists()
    if not gen_preview:
        with open(preview.source) as f1, open(preview_path) as f2:
            assert f1.read() == f2.read()

    json_entities = helpers.read_json_entities(out_path)
    data_entity_ids = [main_wf.id, abs_wf.id, test_file.id, remote_file.id]
    helpers.check_crate(json_entities, data_entity_ids=data_entity_ids)

    for e in main_wf, abs_wf, test_file:
        with open(e.source) as f1, open(out_path / e.id) as f2:
            assert f1.read() == f2.read()


# according to the 1.1 spec, the legacy .jsonld file is still supported for
# crates conforming to version <= 1.0.
def test_legacy_crate(test_data_dir, tmpdir, helpers):
    crate_dir = test_data_dir / 'read_crate'
    # Remove the metadata file, leaving only the legacy one
    (crate_dir / helpers.METADATA_FILE_NAME).unlink()
    crate = ROCrate(crate_dir)
    assert crate.version == "1.0"
    md_prop = crate.metadata.properties()

    assert crate.dereference(helpers.LEGACY_METADATA_FILE_NAME) is crate.metadata
    assert md_prop['conformsTo'] == {'@id': "https://w3id.org/ro/crate/1.0"}

    main_wf = crate.dereference('test_galaxy_wf.ga')
    wf_prop = main_wf.properties()
    assert set(wf_prop['@type']) == helpers.LEGACY_WORKFLOW_TYPES


def test_bad_crate(test_data_dir, tmpdir):
    # nonexistent dir
    crate_dir = test_data_dir / uuid.uuid4().hex
    with pytest.raises(FileNotFoundError):
        ROCrate(crate_dir)
    with pytest.raises(NotADirectoryError):
        ROCrate(crate_dir, init=True)
    # no metadata file
    crate_dir = tmpdir / uuid.uuid4().hex
    crate_dir.mkdir()
    with pytest.raises(ValueError):
        ROCrate(crate_dir)

def load_crate_with_subcrate(test_data_dir):
    return ROCrate(test_data_dir / "crate_with_subcrate", parse_subcrate=True)

def test_crate_with_subcrate(test_data_dir):
    
    main_crate = load_crate_with_subcrate(test_data_dir)
    
    subcrate = main_crate.get("subcrate")
    assert isinstance(subcrate, Subcrate)
    assert main_crate.subcrate_entities == [subcrate]

    # check that at this point, we have not yet loaded the subcrate
    assert subcrate._jsonld == subcrate._empty()
    assert "hasPart" not in subcrate
    
    # check lazy loading by accessing an entity from the subcrate
    assert isinstance(subcrate.get("subfile.txt"), model.file.File)

    # reload the crate to "reset" the state to unloaded
    main_crate = load_crate_with_subcrate(test_data_dir)
    subcrate = main_crate.get("subcrate")
    
    # as_jsonld should trigger loading of the subcrate
    assert subcrate.as_jsonld() != subcrate._empty()
    assert "hasPart" in subcrate
    assert len(subcrate["hasPart"]) == 1


@pytest.mark.parametrize("override", [False, True])
def test_init(test_data_dir, tmpdir, helpers, override):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    if not override:
        (crate_dir / helpers.METADATA_FILE_NAME).unlink()
    crate = ROCrate(crate_dir, init=True)
    assert crate.dereference("./") is not None
    assert crate.dereference(helpers.METADATA_FILE_NAME) is not None
    fpaths = [
        "LICENSE",
        "README.md",
        "sort-and-change-case.ga",
        "test/test1/input.bed",
        "test/test1/output_exp.bed",
        "test/test1/sort-and-change-case-test.yml"
    ]
    dpaths = [
        "test/",
        "test/test1/",
    ]
    for p in fpaths:
        assert isinstance(crate.dereference(p), File)
    for p in dpaths:
        assert isinstance(crate.dereference(p), Dataset)

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    assert (out_path / helpers.METADATA_FILE_NAME).exists()
    json_entities = helpers.read_json_entities(out_path)
    data_entity_ids = fpaths + dpaths
    helpers.check_crate(json_entities, data_entity_ids=data_entity_ids)
    for p in fpaths:
        with open(crate_dir / p) as f1, open(out_path / p) as f2:
            assert f1.read() == f2.read()


def test_exclude(test_data_dir, tmpdir, helpers):
    def check(out=False):
        for p in "LICENSE", "sort-and-change-case.ga":
            assert isinstance(crate.dereference(p), File)
        for p in exclude + ["test/"]:
            assert not crate.dereference(p)
            if out:
                assert not (crate.source / p).exists()
        for e in crate.data_entities:
            assert not e.id.startswith("test")
        if out:
            assert not (crate.source / "test").exists()
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    (crate_dir / helpers.METADATA_FILE_NAME).unlink()
    exclude = ["test", "README.md"]
    crate = ROCrate(crate_dir, init=True, exclude=exclude)
    check()
    out_path = tmpdir / 'ro_crate_out'
    crate.write(out_path)
    crate = ROCrate(out_path)
    check(out=True)


@pytest.mark.parametrize("gen_preview,preview_exists", [(False, False), (False, True), (True, False), (True, True)])
def test_init_preview(test_data_dir, tmpdir, helpers, gen_preview, preview_exists):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    dummy_prev_content = "foo\nbar\n"
    if preview_exists:
        with open(crate_dir / helpers.PREVIEW_FILE_NAME, "wt") as f:
            f.write(dummy_prev_content)
    crate = ROCrate(crate_dir, gen_preview=gen_preview, init=True)
    prev = crate.dereference(helpers.PREVIEW_FILE_NAME)
    if gen_preview or preview_exists:
        assert prev is not None

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    out_prev_path = out_path / helpers.PREVIEW_FILE_NAME
    if gen_preview or preview_exists:
        assert out_prev_path.is_file()
    else:
        assert not out_prev_path.exists()

    if not gen_preview and preview_exists:
        assert out_prev_path.open().read() == dummy_prev_content


def test_no_parts(tmpdir):
    crate = ROCrate()

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    crate = ROCrate(out_path)
    assert "hasPart" not in crate.root_dataset


@pytest.mark.parametrize("to_zip", [False, True])
def test_extra_data(test_data_dir, tmpdir, to_zip):
    crate_dir = test_data_dir / 'read_extra'
    crate = ROCrate(crate_dir)
    out_path = tmpdir / 'read_extra_out'
    if to_zip:
        zip_path = tmpdir / 'ro_crate_out.crate.zip'
        crate.write_zip(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_path)
    else:
        out_path.mkdir()
        crate.write(out_path)
    for rel in {
            "listed.txt",
            "listed/listed.txt",
            "listed/not_listed.txt",
            "not_listed.txt",
            "not_listed/not_listed.txt",
    }:
        assert (out_path / rel).is_file()
        with open(crate_dir / rel) as f1, open(out_path / rel) as f2:
            assert f1.read() == f2.read()


def test_missing_dir(test_data_dir, tmpdir):
    crate_dir = test_data_dir / 'read_crate'
    name = 'examples'
    shutil.rmtree(crate_dir / name)
    crate = ROCrate(crate_dir)

    examples_dataset = crate.dereference(name)
    assert examples_dataset.id == f'{name}/'

    out_path = tmpdir / 'crate_read_out'
    with pytest.raises(OSError):
        crate.write(out_path)

    # Two options to get a writable crate

    # 1. Set the source to None (will create an empty dir)
    examples_dataset.source = None
    crate.write(out_path)
    assert (out_path / name).is_dir()

    shutil.rmtree(out_path)

    # 2. Provide an existing source
    source = tmpdir / "source"
    source.mkdir()
    examples_dataset.source = source
    crate.write(out_path)
    assert (out_path / name).is_dir()


@pytest.mark.filterwarnings("ignore")
def test_missing_file(test_data_dir, tmpdir):
    crate_dir = test_data_dir / 'read_crate'
    name = 'test_file_galaxy.txt'
    test_path = crate_dir / name
    test_path.unlink()
    crate = ROCrate(crate_dir)

    test_file = crate.dereference(name)
    assert test_file.id == name

    out_path = tmpdir / 'crate_read_out'
    with pytest.raises(OSError):
        crate.write(out_path)

    # Two options to get a writable crate

    # 1. Set the source to None (file will still be missing in the copy)
    test_file.source = None
    crate.write(out_path)
    assert not (out_path / name).exists()

    shutil.rmtree(out_path)

    # 2. Provide an existing source
    source = tmpdir / "source.txt"
    text = "foo\nbar\n"
    source.write_text(text)
    test_file.source = source
    crate.write(out_path)
    assert (out_path / name).read_text() == text


@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_generic_data_entity(tmpdir, version):
    rc_id = "#collection"
    metadata = {
        "@context": [
            f"https://w3id.org/ro/crate/{version}/context",
            {"@vocab": "http://schema.org/"},
            {"@base": None}
        ],
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {
                    "@id": f"https://w3id.org/ro/crate/{version}"
                },
                "about": {
                    "@id": "./"
                },
                "identifier": "ro-crate-metadata.json"
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "hasPart": [{"@id": rc_id}],
                "name": "Test RepositoryCollection"
            },
            {
                "@id": rc_id,
                "@type": "RepositoryCollection",
                "name": "Test collection"
            }
        ]
    }
    crate_dir = tmpdir / "test_repository_collection"
    crate_dir.mkdir()
    with open(crate_dir / "ro-crate-metadata.json", "wt") as f:
        json.dump(metadata, f, indent=4)
    crate = ROCrate(crate_dir)

    def check_rc():
        rc = crate.dereference(rc_id)
        assert rc is not None
        if version == "1.2":
            assert isinstance(rc, ContextEntity)
        else:
            assert isinstance(rc, DataEntity)
        assert rc.id == rc_id
        assert rc.type == "RepositoryCollection"
        assert rc._jsonld["name"] == "Test collection"
        if version == "1.2":
            assert not crate.data_entities
            assert crate.contextual_entities == [rc]
        else:
            assert crate.data_entities == [rc]
            assert not crate.contextual_entities

    check_rc()

    out_crate_dir = tmpdir / "output_crate"
    crate.write(out_crate_dir)
    crate = ROCrate(out_crate_dir)

    check_rc()


@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_root_conformsto(tmpdir, version):
    # actually not a valid workflow ro-crate, but here it does not matter
    profiles = [
        f"https://w3id.org/ro/crate/{version}",
        "https://w3id.org/workflowhub/workflow-ro-crate/1.0",
    ]
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": [{"@id": _} for _ in profiles]
            },
            {
                "@id": "./",
                "@type": "Dataset",
            },
        ]
    }
    crate_dir = tmpdir / "test_root_conformsto_crate"
    crate_dir.mkdir()
    with open(crate_dir / "ro-crate-metadata.json", "wt") as f:
        json.dump(metadata, f, indent=4)
    crate = ROCrate(crate_dir)
    assert crate.metadata["conformsTo"] == profiles


@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_multi_type_context_entity(tmpdir, version):
    id_, type_ = "#xyz", ["Project", "Organization"]
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
            },
            {
                "@id": id_,
                "@type": type_,
            }
        ]
    }
    crate_dir = tmpdir / "test_multi_type_context_entity_crate"
    crate_dir.mkdir()
    with open(crate_dir / "ro-crate-metadata.json", "wt") as f:
        json.dump(metadata, f, indent=4)
    crate = ROCrate(crate_dir)
    entity = crate.dereference(id_)
    assert entity in crate.contextual_entities
    assert set(entity.type) == set(type_)


@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_indirect_data_entity(tmpdir, version):
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "hasPart": {"@id": "d1"}
            },
            {
                "@id": "d1",
                "@type": "Dataset",
                "hasPart": {"@id": "d1/d2"}
            },
            {
                "@id": "d1/d2",
                "@type": "Dataset",
                "hasPart": {"@id": "d1/d2/f1"}
            },
            {
                "@id": "d1/d2/f1",
                "@type": "File"
            }
        ]
    }
    crate_dir = tmpdir / "test_indirect_data_entity"
    crate_dir.mkdir()
    with open(crate_dir / "ro-crate-metadata.json", "wt") as f:
        json.dump(metadata, f, indent=4)
    d1 = crate_dir / "d1"
    d1.mkdir()
    d2 = d1 / "d2"
    d2.mkdir()
    f1 = d2 / "f1"
    f1.touch()
    crate = ROCrate(crate_dir)
    d1_e = crate.dereference("d1")
    assert d1_e
    assert d1_e in crate.data_entities
    d2_e = crate.dereference("d1/d2")
    assert d2_e
    assert d2_e in crate.data_entities
    f1_e = crate.dereference("d1/d2/f1")
    assert f1_e
    assert f1_e in crate.data_entities


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_from_dict(tmpdir, version):
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "creator": {"@id": "#josiah"},
                "hasPart": {"@id": "d1"}
            },
            {
                "@id": "d1",
                "@type": "Dataset",
                "hasPart": {"@id": "d1/d2"}
            },
            {
                "@id": "d1/d2",
                "@type": "Dataset",
                "hasPart": {"@id": "d1/d2/f1"}
            },
            {
                "@id": "d1/d2/f1",
                "@type": "File"
            },
            {
                "@id": "#josiah",
                "@type": "Person",
                'name': 'Josiah Carberry'
            },
        ]
    }
    crate = ROCrate(metadata)
    d1 = crate.dereference("d1")
    assert d1
    d2 = crate.dereference("d1/d2")
    assert d2
    f1 = crate.dereference("d1/d2/f1")
    assert f1
    p = crate.dereference("#josiah")
    assert p
    assert set(crate.data_entities) == {d1, d2, f1}
    assert set(crate.contextual_entities) == {p}
    out_path = tmpdir / 'out_crate'
    with pytest.raises(OSError):
        crate.write(out_path)
    # make it writable
    for entity in d1, d2, f1:
        entity.source = None
    crate.write(out_path)
    with pytest.raises(ValueError):
        ROCrate(metadata, init=True)


@pytest.mark.parametrize("version", ["1.1", "1.2"])
def test_no_data_entity_link_from_file(version):
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "hasPart": [
                    {"@id": "d1"},
                    {"@id": "packed.cwl"}
                ]
            },
            {
                "@id": "d1",
                "@type": "Dataset"
            },
            {
                "@id": "packed.cwl",
                "@type": [
                    "File",
                    "SoftwareSourceCode",
                    "ComputationalWorkflow"
                ],
                "hasPart": [
                    {"@id": "packed.cwl#do_this.cwl"},
                    {"@id": "packed.cwl#do_that.cwl"}
                ]
            },
            {
                "@id": "packed.cwl#do_this.cwl",
                "@type": "SoftwareApplication",
            },
            {
                "@id": "packed.cwl#do_that.cwl",
                "@type": "SoftwareApplication",
            }
        ]
    }
    crate = ROCrate(metadata)
    d1 = crate.dereference("d1")
    assert d1
    assert d1 in crate.data_entities
    assert d1 not in crate.contextual_entities
    wf = crate.dereference("packed.cwl")
    assert wf
    assert wf in crate.data_entities
    assert wf not in crate.contextual_entities
    t1 = crate.dereference("packed.cwl#do_this.cwl")
    assert t1
    assert t1 not in crate.data_entities
    assert t1 in crate.contextual_entities


def test_init_percent_escape(tmpdir, helpers):
    in_crate = tmpdir / "in_crate"
    in_file = in_crate / "in file.txt"
    in_dir = in_crate / "in dir"
    deep_file = in_crate / "in dir" / "deep file.txt"
    out_crate = tmpdir / "out_crate"
    in_crate.mkdir()
    in_file.write_text("IN FILE\n")
    in_dir.mkdir()
    deep_file.write_text("DEEP FILE\n")
    crate = ROCrate(in_crate, init=True)
    crate.write(out_crate)
    json_entities = helpers.read_json_entities(out_crate)
    assert "in%20file.txt" in json_entities
    assert "in%20dir/" in json_entities
    assert "in%20dir/deep%20file.txt" in json_entities
    assert (out_crate / "in file.txt").is_file()
    assert (out_crate / "in dir").is_dir()
    assert (out_crate / "in dir" / "deep file.txt").is_file()


def test_read_version(test_data_dir):
    crate = ROCrate(test_data_dir / "crate-1.0")
    assert crate.version == "1.0"
    crate = ROCrate(test_data_dir / "crate-1.1")
    assert crate.version == "1.1"


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("version", ["1.0", "1.1", "1.2"])
def test_data_entity_not_linked(version):
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "hasPart": [
                    {"@id": "d1"}
                ]
            },
            {
                "@id": "d1",
                "@type": "Dataset"
            },
            {
                "@id": "f1.txt",
                "@type": "File"
            }
        ]
    }
    if version == "1.2":
        with pytest.raises(ValueError, match="hasPart"):
            ROCrate(metadata)
    else:
        crate = ROCrate(metadata)
        f1 = crate.get("f1.txt")
        assert f1 in crate.contextual_entities


@pytest.mark.parametrize("version", ["1.0", "1.1", "1.2"])
def test_not_data_entity_linked(version):
    metadata = {
        "@context": f"https://w3id.org/ro/crate/{version}/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": f"https://w3id.org/ro/crate/{version}"}
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "hasPart": [
                    {"@id": "d1"},
                    {"@id": "#f1.txt"}
                ]
            },
            {
                "@id": "d1",
                "@type": "Dataset"
            },
            {
                "@id": "#f1.txt",
                "@type": "File"
            }
        ]
    }
    crate = ROCrate(metadata)
    d1 = crate.get("d1")
    assert d1 in crate.data_entities
    f1 = crate.get("#f1.txt")
    if version == "1.2":
        assert f1 in crate.contextual_entities
    else:
        assert f1 in crate.data_entities
