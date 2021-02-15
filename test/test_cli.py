# Copyright 2019-2020 The University of Manchester, UK
# Copyright 2020 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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

import pytest
from click.testing import CliRunner

from rocrate.cli import cli


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_init(test_data_dir, helpers, monkeypatch, cwd):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    metadata_path = crate_dir / helpers.METADATA_FILE_NAME
    metadata_path.unlink()

    runner = CliRunner()
    args = ["init"]
    if cwd:
        monkeypatch.chdir(str(crate_dir))
    else:
        args.append(str(crate_dir))
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    assert metadata_path.is_file()

    json_entities = helpers.read_json_entities(crate_dir)
    assert "sort-and-change-case.ga" in json_entities
    assert json_entities["sort-and-change-case.ga"]["@type"] == "File"
