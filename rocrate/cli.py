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

import os
from pathlib import Path

import click
from .rocrate import ROCrate
from .model.computerlanguage import LANG_MAP
from .model.testservice import SERVICE_MAP
from .model.softwareapplication import APP_MAP


LANG_CHOICES = list(LANG_MAP)
SERVICE_CHOICES = list(SERVICE_MAP)
ENGINE_CHOICES = list(APP_MAP)


class State:
    pass


@click.group()
@click.option('-c', '--crate-dir', type=click.Path())
@click.pass_context
def cli(ctx, crate_dir):
    ctx.obj = state = State()
    state.crate_dir = os.getcwd() if not crate_dir else os.path.abspath(crate_dir)


@cli.command()
@click.option('--gen-preview', is_flag=True)
@click.pass_obj
def init(state, gen_preview):
    crate = ROCrate(state.crate_dir, init=True, gen_preview=gen_preview)
    crate.metadata.write(state.crate_dir)
    if crate.preview:
        crate.preview.write(state.crate_dir)


@cli.group()
@click.pass_obj
def add(state):
    state.crate = ROCrate(state.crate_dir, init=False, gen_preview=False)


@add.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-l', '--language', type=click.Choice(LANG_CHOICES), default="cwl")
@click.pass_obj
def workflow(state, path, language):
    source = Path(path).resolve(strict=True)
    try:
        dest_path = source.relative_to(state.crate_dir)
    except ValueError:
        # For now, only support marking an existing file as a workflow
        raise ValueError(f"{source} is not in the crate dir {state.crate_dir}")
    # TODO: add command options for main and gen_cwl
    state.crate.add_workflow(source, dest_path, main=True, lang=language, gen_cwl=False)
    state.crate.metadata.write(state.crate_dir)


@add.command(name="test-suite")
@click.option('-i', '--identifier')
@click.option('-n', '--name')
@click.option('-m', '--main-entity')
@click.pass_obj
def suite(state, identifier, name, main_entity):
    suite_ = state.crate.add_test_suite(identifier=identifier, name=name, main_entity=main_entity)
    state.crate.metadata.write(state.crate_dir)
    print(suite_.id)


@add.command(name="test-instance")
@click.argument('suite')
@click.argument('url')
@click.option('-r', '--resource', default="")
@click.option('-s', '--service', type=click.Choice(SERVICE_CHOICES), default="jenkins")
@click.option('-i', '--identifier')
@click.option('-n', '--name')
@click.pass_obj
def instance(state, suite, url, resource, service, identifier, name):
    instance_ = state.crate.add_test_instance(suite, url, resource=resource, service=service, identifier=identifier, name=name)
    state.crate.metadata.write(state.crate_dir)
    print(instance_.id)


@add.command(name="test-definition")
@click.argument('suite')
@click.argument('path', type=click.Path(exists=True))
@click.option('-e', '--engine', type=click.Choice(ENGINE_CHOICES), default="planemo")
@click.option('-v', '--engine-version')
@click.pass_obj
def definition(state, suite, path, engine, engine_version):
    source = Path(path).resolve(strict=True)
    try:
        dest_path = source.relative_to(state.crate_dir)
    except ValueError:
        # For now, only support marking an existing file as a test definition
        raise ValueError(f"{source} is not in the crate dir {state.crate_dir}")
    state.crate.add_test_definition(suite, source=source, dest_path=dest_path, engine=engine, engine_version=engine_version)
    state.crate.metadata.write(state.crate_dir)


@cli.command()
@click.argument('dst', type=click.Path(writable=True))
@click.pass_obj
def write_zip(state, dst):
    crate = ROCrate(state.crate_dir, init=True, gen_preview=False)
    crate.write_zip(dst)


if __name__ == '__main__':
    cli()
