# Copyright 2019-2022 The University of Manchester, UK
# Copyright 2020-2022 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2022 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2022 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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

import click
from click.testing import CliRunner
import pytest

from rocrate.cli import cli
from rocrate.model.file import File
from rocrate.model.metadata import TESTING_EXTRA_TERMS
from rocrate.rocrate import ROCrate


def get_command_paths(command):
    """Return a list of full command paths for all leaf commands that are part of the given root command.

    For example, for a root command that has two subcommands ``command_a`` and ``command_b`` where ``command_b`` in turn
    has two subcommands, the returned list will have the form::

        [
            ['command_a'],
            ['command_b', 'subcommand_a'],
            ['command_b', 'subcommand_b'],
        ]

    :param command: The root command.
    :return: A list of lists, where each element is the full command path to a leaf command.
    """

    def resolve_commands(command, command_path, commands):
        if isinstance(command, click.MultiCommand):
            for subcommand in command.commands.values():
                command_subpath = command_path + [subcommand.name]
                resolve_commands(subcommand, command_subpath, commands)
        else:
            commands.append(command_path)

    commands = []
    resolve_commands(command, [], commands)

    return commands


@pytest.mark.parametrize('command_path', get_command_paths(cli))
def test_cli_help(command_path):
    """Test that invoking any CLI command with ``--help`` prints the help string and exits normally.

    This is a regression test for: https://github.com/ResearchObject/ro-crate-py/issues/97

    Note that we cannot simply invoke the actual leaf :class:`click.Command` that we are testing, because the test
    runner follows a different path then when actually invoking the command from the command line. This means that any
    code that is in the groups that the command is part of, won't be executed. This in turn means that a command could
    actually be broken when invoked from the command line but would not be detected by the test. The workaround is to
    invoke the full command path. For example when testing ``add workflow --help``, we cannot simply invoke ``workflow``
    with ``['--help']`` as argument but we need to invoke the base command with ``['add', 'workflow', '--help']``.
    """
    runner = CliRunner()
    result = runner.invoke(cli, command_path + ['--help'])
    assert result.exit_code == 0, result.output
    assert 'Usage:' in result.output


@pytest.mark.parametrize("gen_preview,cwd", [(False, False), (False, True), (True, False), (True, True)])
def test_cli_init(test_data_dir, helpers, monkeypatch, cwd, gen_preview):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    metadata_path = crate_dir / helpers.METADATA_FILE_NAME
    preview_path = crate_dir / helpers.PREVIEW_FILE_NAME
    metadata_path.unlink()

    runner = CliRunner()
    args = ["init"]
    if cwd:
        monkeypatch.chdir(str(crate_dir))
    else:
        args.extend(["-c", str(crate_dir)])
    if gen_preview:
        args.append("--gen-preview")
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    assert metadata_path.is_file()
    if gen_preview:
        assert preview_path.is_file()
    else:
        assert not preview_path.exists()

    json_entities = helpers.read_json_entities(crate_dir)
    assert "sort-and-change-case.ga" in json_entities
    assert json_entities["sort-and-change-case.ga"]["@type"] == "File"


def test_cli_init_exclude(test_data_dir, helpers):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    (crate_dir / helpers.METADATA_FILE_NAME).unlink()
    exclude = "test,README.md"
    runner = CliRunner()
    args = ["init", "-c", str(crate_dir), "-e", exclude]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    crate = ROCrate(crate_dir)
    for p in "LICENSE", "sort-and-change-case.ga":
        assert isinstance(crate.dereference(p), File)
    for p in exclude.split(",") + ["test/"]:
        assert not crate.dereference(p)
    for e in crate.data_entities:
        assert not(e.id.startswith("test"))


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_add_workflow(test_data_dir, helpers, monkeypatch, cwd):
    # init
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    runner = CliRunner()
    assert runner.invoke(cli, ["init", "-c", str(crate_dir)]).exit_code == 0
    json_entities = helpers.read_json_entities(crate_dir)
    assert "sort-and-change-case.ga" in json_entities
    assert json_entities["sort-and-change-case.ga"]["@type"] == "File"
    # add
    wf_path = crate_dir / "sort-and-change-case.ga"
    args = ["add", "workflow"]
    if cwd:
        monkeypatch.chdir(str(crate_dir))
        wf_path = wf_path.relative_to(crate_dir)
    else:
        args.extend(["-c", str(crate_dir)])
    for lang in "cwl", "galaxy":
        extra_args = ["-l", lang, str(wf_path)]
        result = runner.invoke(cli, args + extra_args)
        assert result.exit_code == 0
        json_entities = helpers.read_json_entities(crate_dir)
        helpers.check_wf_crate(json_entities, wf_path.name)
        assert "sort-and-change-case.ga" in json_entities
        lang_id = f"https://w3id.org/workflowhub/workflow-ro-crate#{lang}"
        assert lang_id in json_entities
        assert json_entities["sort-and-change-case.ga"]["programmingLanguage"]["@id"] == lang_id


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_add_test_metadata(test_data_dir, helpers, monkeypatch, cwd):
    # init
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    runner = CliRunner()
    assert runner.invoke(cli, ["init", "-c", str(crate_dir)]).exit_code == 0
    json_entities = helpers.read_json_entities(crate_dir)
    def_id = "test/test1/sort-and-change-case-test.yml"
    assert def_id in json_entities
    assert json_entities[def_id]["@type"] == "File"
    # add workflow
    wf_path = crate_dir / "sort-and-change-case.ga"
    assert runner.invoke(cli, ["add", "workflow", "-c", str(crate_dir), "-l", "galaxy", str(wf_path)]).exit_code == 0
    # add test suite
    result = runner.invoke(cli, ["add", "test-suite", "-c", str(crate_dir)])
    assert result.exit_code == 0
    suite_id = result.output.strip()
    json_entities = helpers.read_json_entities(crate_dir)
    assert suite_id in json_entities
    # add test instance
    result = runner.invoke(cli, ["add", "test-instance", "-c", str(crate_dir), suite_id, "http://example.com", "-r", "jobs"])
    assert result.exit_code == 0
    instance_id = result.output.strip()
    json_entities = helpers.read_json_entities(crate_dir)
    assert instance_id in json_entities
    # add test definition
    def_path = crate_dir / def_id
    args = ["add", "test-definition"]
    if cwd:
        monkeypatch.chdir(str(crate_dir))
        def_path = def_path.relative_to(crate_dir)
    else:
        args.extend(["-c", str(crate_dir)])
    extra_args = ["-e", "planemo", "-v", ">=0.70", suite_id, str(def_path)]
    result = runner.invoke(cli, args + extra_args)
    assert result.exit_code == 0
    json_entities = helpers.read_json_entities(crate_dir)
    assert def_id in json_entities
    assert set(json_entities[def_id]["@type"]) == {"File", "TestDefinition"}
    # check extra terms
    metadata_path = crate_dir / helpers.METADATA_FILE_NAME
    with open(metadata_path, "rt") as f:
        json_data = json.load(f)
    assert "@context" in json_data
    context = json_data["@context"]
    assert isinstance(context, list)
    assert len(context) > 1
    extra_terms = context[1]
    assert set(TESTING_EXTRA_TERMS.items()).issubset(extra_terms.items())


@pytest.mark.parametrize("hash_", [False, True])
def test_cli_add_test_metadata_explicit_ids(test_data_dir, helpers, monkeypatch, hash_):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    runner = CliRunner()
    assert runner.invoke(cli, ["init", "-c", str(crate_dir)]).exit_code == 0
    wf_path = crate_dir / "sort-and-change-case.ga"
    assert runner.invoke(cli, ["add", "workflow", "-c", str(crate_dir), "-l", "galaxy", str(wf_path)]).exit_code == 0
    suite_id = "#foo"
    cli_suite_id = suite_id if hash_ else suite_id[1:]
    result = runner.invoke(cli, ["add", "test-suite", "-c", str(crate_dir), "-i", cli_suite_id])
    assert result.exit_code == 0
    assert result.output.strip() == suite_id
    json_entities = helpers.read_json_entities(crate_dir)
    assert suite_id in json_entities
    instance_id = "#bar"
    cli_instance_id = instance_id if hash_ else instance_id[1:]
    args = [
        "add", "test-instance", cli_suite_id, "http://example.com", "-c", str(crate_dir), "-r", "jobs", "-i", cli_instance_id
    ]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    assert result.output.strip() == instance_id
    json_entities = helpers.read_json_entities(crate_dir)
    assert instance_id in json_entities


@pytest.mark.parametrize("cwd", [False, True])
def test_cli_write_zip(test_data_dir, monkeypatch, cwd):
    crate_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    runner = CliRunner()
    assert runner.invoke(cli, ["init", "-c", str(crate_dir)]).exit_code == 0
    wf_path = crate_dir / "sort-and-change-case.ga"
    args = ["add", "workflow", str(wf_path), "-c", str(crate_dir)]
    assert runner.invoke(cli, args).exit_code == 0

    output_zip_path = test_data_dir / "test-zip-archive.zip"
    args = ["write-zip"]
    if cwd:
        monkeypatch.chdir(str(crate_dir))
    else:
        args.extend(["-c", str(crate_dir)])
    args.append(str(output_zip_path))

    result = runner.invoke(cli, args)
    assert result.exit_code == 0
    assert output_zip_path.is_file()

    crate = ROCrate(output_zip_path)
    assert crate.mainEntity is not None
