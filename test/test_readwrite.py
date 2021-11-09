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
import shutil
import zipfile
from itertools import product
from urllib.error import URLError
from pathlib import Path

from rocrate.model.dataset import Dataset
from rocrate.model.person import Person
from rocrate.rocrate import ROCrate


@pytest.mark.parametrize("gen_preview,to_zip,from_zip", [(False, False, False), (False, True, True), (True, False, False), (True, True, True)])
def test_file_rewriting(test_data_dir, tmpdir, helpers, gen_preview, to_zip, from_zip):
    # load crate
    crate_dir = test_data_dir / 'read_crate'
    if from_zip:
        zip_source = shutil.make_archive(tmpdir / "read_crate.crate", "zip", crate_dir)
        crate = ROCrate(zip_source, gen_preview=gen_preview)
    else:
        crate = ROCrate(crate_dir, gen_preview=gen_preview)

    creator_id = '003'
    creator_name = 'Chet Baker'
    new_person = Person(crate, creator_id, {'name': creator_name})
    crate.add(new_person)
    crate.creator = new_person

    out_path = tmpdir / 'read_write_crate'
    if to_zip:
        zip_path = tmpdir / 'read_write_crate.crate.zip'
        crate.write_zip(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_path)
    else:
        out_path.mkdir()
        crate.write(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    preview_path = out_path / helpers.PREVIEW_FILE_NAME

    preview = crate.dereference(helpers.PREVIEW_FILE_NAME)
    assert preview == crate.preview

    if not gen_preview:
        assert Path(preview.source).name == helpers.PREVIEW_FILE_NAME
    else:
        assert not preview.source

    sample_file_id = "test_file_galaxy.txt"
    sample_file2_id = "test_galaxy_wf.ga"
    file1 = out_path / sample_file_id
    file2 = out_path / sample_file2_id
    assert file1.exists()
    assert file2.exists()
    