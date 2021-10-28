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

import io
import pytest
import uuid
import zipfile
from itertools import product
from urllib.error import URLError

from rocrate.model.dataset import Dataset
from rocrate.model.person import Person
from rocrate.rocrate import ROCrate


@pytest.mark.parametrize("gen_preview,to_zip", [(False, False), (False, True), (True, False), (True, True)])
def test_file_writing(test_data_dir, tmpdir, helpers, gen_preview, to_zip):
    crate = ROCrate(gen_preview=gen_preview)
    crate_name = 'Test crate'
    crate.name = crate_name
    creator_id = '001'
    creator_name = 'Lee Ritenour'
    new_person = Person(crate, creator_id, {'name': creator_name})
    crate.add(new_person)
    crate.creator = new_person

    sample_file_id = 'sample_file.txt'
    sample_file2_id = 'a/b/sample_file2.csv'
    test_dir_id = 'test_add_dir/'
    data_entity_ids = [sample_file_id, sample_file2_id, test_dir_id]
    file_subdir_id = 'sample_file_subdir.txt'

    sample_file = test_data_dir / sample_file_id
    file_returned = crate.add_file(sample_file)
    assert file_returned.id == sample_file_id
    file_returned_subdir = crate.add_file(sample_file, sample_file2_id)
    assert file_returned_subdir.id == sample_file2_id
    test_dir_path = test_data_dir / test_dir_id
    test_dir_entity = crate.add_directory(test_dir_path, test_dir_id)
    assert isinstance(test_dir_entity, Dataset)

    out_path = tmpdir / 'ro_crate_out'
    if to_zip:
        zip_path = tmpdir / 'ro_crate_out.crate.zip'
        crate.write_zip(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_path)
    else:
        out_path.mkdir()
        crate.write(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    preview_path = out_path / helpers.PREVIEW_FILE_NAME
    if gen_preview:
        assert preview_path.exists()
    else:
        assert not preview_path.exists()
    file1 = out_path / sample_file_id
    file2 = out_path / sample_file2_id
    file_subdir = out_path / test_dir_id / file_subdir_id
    assert file1.exists()
    with open(sample_file) as f1, open(file1) as f2:
        sample_file_content = f1.read()
        assert sample_file_content == f2.read()
    assert file2.exists()
    with open(file2) as f:
        assert sample_file_content == f.read()
    assert file_subdir.exists()
    with open(test_dir_path / file_subdir_id) as f1, open(file_subdir) as f2:
        assert f1.read() == f2.read()

    json_entities = helpers.read_json_entities(out_path)
    helpers.check_crate(json_entities, data_entity_ids=data_entity_ids)
    root = json_entities["./"]
    assert root["name"] == crate_name
    assert "datePublished" in root
    formatted_creator_id = f"#{creator_id}"
    assert root["creator"] == {"@id": formatted_creator_id}
    assert formatted_creator_id in json_entities
    assert json_entities[formatted_creator_id]["name"] == creator_name
    if gen_preview:
        assert helpers.PREVIEW_FILE_NAME in json_entities


@pytest.mark.parametrize("stream_cls", [io.BytesIO, io.StringIO])
def test_in_mem_stream(stream_cls, tmpdir, helpers):
    crate = ROCrate()

    test_file_id = 'a/b/test_file.txt'
    file_content = b'\x00\x01' if stream_cls is io.BytesIO else 'foo\n'
    file_returned = crate.add_file(stream_cls(file_content), test_file_id)
    assert file_returned.id == test_file_id

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    file1 = out_path / test_file_id
    assert file1.exists()
    mode = 'r' + ('b' if stream_cls is io.BytesIO else 't')
    with open(file1, mode) as f:
        assert f.read() == file_content


@pytest.mark.parametrize(
    "fetch_remote,validate_url,to_zip",
    list(product((False, True), repeat=3))
)
def test_remote_uri(tmpdir, helpers, fetch_remote, validate_url, to_zip):
    crate = ROCrate()
    url = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/'
           'master/test/test-data/sample_file.txt')
    relpath = "a/b/sample_file.txt"
    kw = {"fetch_remote": fetch_remote, "validate_url": validate_url}
    if fetch_remote:
        file_ = crate.add_file(url, relpath, **kw)
        assert file_.id == relpath
    else:
        file_ = crate.add_file(url, **kw)
        assert file_.id == url

    out_path = tmpdir / 'ro_crate_out'
    if to_zip:
        zip_path = f"{out_path}.zip"
        crate.write_zip(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_path)
    else:
        crate.write(out_path)

    out_crate = ROCrate(out_path)
    if fetch_remote:
        out_file = out_crate.dereference(file_.id)
        assert (out_path / relpath).is_file()
    else:
        out_file = out_crate.dereference(url)
        assert not (out_path / relpath).exists()
    if validate_url:
        props = out_file.properties()
        assert {"contentSize", "encodingFormat"}.issubset(props)
        if not fetch_remote:
            assert "sdDatePublished" in props


@pytest.mark.parametrize(
    "fetch_remote,validate_url",
    list(product((False, True), repeat=2))
)
def test_remote_dir(tmpdir, helpers, fetch_remote, validate_url):
    crate = ROCrate()
    url = "https://ftp.mozilla.org/pub/misc/errorpages/"
    relpath = "pub/misc/errorpages/"
    properties = {
        "hasPart": [
            {"@id": "404.html"},
            {"@id": "500.html"},
        ],
    }
    kw = {
        "fetch_remote": fetch_remote,
        "validate_url": validate_url,
        "properties": properties,
    }
    if fetch_remote:
        dataset = crate.add_dataset(url, relpath, **kw)
        assert dataset.id == relpath
    else:
        dataset = crate.add_dataset(url, **kw)
        assert dataset.id == url

    out_path = tmpdir / 'ro_crate_out'
    crate.write(out_path)

    out_crate = ROCrate(out_path)
    if fetch_remote:
        out_dataset = out_crate.dereference(relpath)
        assert (out_path / relpath).is_dir()
        for entry in properties["hasPart"]:
            assert (out_path / relpath / entry["@id"]).is_file()
    else:
        out_dataset = out_crate.dereference(url)
        assert not (out_path / relpath).exists()
    if validate_url and not fetch_remote:
        assert "sdDatePublished" in out_dataset.properties()


def test_remote_uri_exceptions(tmpdir):
    crate = ROCrate()
    url = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/'
           f'master/test/test-data/{uuid.uuid4().hex}.foo')
    crate.add_file(source=url, fetch_remote=True)
    out_path = tmpdir / 'ro_crate_out_1'
    out_path.mkdir()
    with pytest.raises(URLError):
        crate.write(out_path)

    crate = ROCrate()
    url = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/'
           'master/test/test-data/sample_file.txt')
    crate.add_file(source=url, dest_path="a/sample_file.txt", fetch_remote=True)
    out_path = tmpdir / 'ro_crate_out_2'
    out_path.mkdir()
    (out_path / "a").mkdir(mode=0o444)
    try:
        crate.write(out_path)
    except PermissionError:
        pass
    # no error on Windows, or on Linux as root, so we don't use pytest.raises


@pytest.mark.parametrize("fetch_remote,validate_url", [(False, False), (False, True), (True, False), (True, True)])
def test_missing_source(test_data_dir, tmpdir, fetch_remote, validate_url):
    path = test_data_dir / uuid.uuid4().hex
    args = {"fetch_remote": fetch_remote, "validate_url": validate_url}

    crate = ROCrate()
    file_ = crate.add_file(path, **args)
    assert file_ is crate.dereference(path.name)
    out_path = tmpdir / 'ro_crate_out_1'
    crate.write(out_path)
    assert not (out_path / path.name).exists()

    crate = ROCrate()
    file_ = crate.add_file(path, path.name, **args)
    assert file_ is crate.dereference(path.name)
    out_path = tmpdir / 'ro_crate_out_2'
    assert not (out_path / path.name).exists()


@pytest.mark.parametrize("fetch_remote,validate_url", [(False, False), (False, True), (True, False), (True, True)])
def test_stringio_no_dest(test_data_dir, fetch_remote, validate_url):
    crate = ROCrate()
    with pytest.raises(ValueError):
        crate.add_file(io.StringIO("foo"))


@pytest.mark.parametrize("fetch_remote,validate_url", [(False, False), (False, True), (True, False), (True, True)])
def test_no_source_no_dest(test_data_dir, fetch_remote, validate_url):
    crate = ROCrate()
    with pytest.raises(ValueError):
        crate.add_file()


def test_dataset(test_data_dir, tmpdir):
    crate = ROCrate()
    path = test_data_dir / "a" / "b"
    d1 = crate.add_dataset(path)
    assert crate.dereference("b") is d1
    d2 = crate.add_dataset(path, "a/b")
    assert crate.dereference("a/b") is d2

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    assert (out_path / "b").is_dir()
    assert (out_path / "a" / "b").is_dir()


def test_no_parts(tmpdir, helpers):
    crate = ROCrate()

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write(out_path)

    json_entities = helpers.read_json_entities(out_path)
    helpers.check_crate(json_entities)
    assert "hasPart" not in json_entities["./"]


def test_no_zip_in_zip(test_data_dir, tmpdir):
    crate_dir = test_data_dir / 'ro-crate-galaxy-sortchangecase'
    crate = ROCrate(crate_dir)

    zip_name = 'ro_crate_out.crate.zip'
    zip_path = crate_dir / zip_name  # within the crate dir
    crate.write_zip(zip_path)
    out_path = tmpdir / 'ro_crate_out'
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_path)

    assert not (out_path / zip_name).exists()
