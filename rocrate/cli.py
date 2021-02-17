import os
from pathlib import Path

import click
from .rocrate import ROCrate
from .model.preview import Preview
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
    state.crate_dir = crate_dir


@cli.command()
@click.pass_obj
def init(state):
    crate_dir = state.crate_dir or os.getcwd()
    crate = ROCrate(crate_dir, init=True, load_preview=True)
    crate.metadata.write(crate_dir)


@cli.group()
@click.pass_obj
def add(state):
    crate_dir = state.crate_dir or os.getcwd()
    state.crate = ROCrate(crate_dir, init=False, load_preview=True)


@add.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-l', '--language', type=click.Choice(LANG_CHOICES), default="cwl")
@click.pass_obj
def workflow(state, path, language):
    crate_dir = state.crate_dir or os.getcwd()
    source = Path(path).resolve(strict=True)
    try:
        dest_path = source.relative_to(crate_dir)
    except ValueError:
        # For now, only support marking an existing file as a workflow
        raise ValueError(f"{source} is not in the crate dir")
    # TODO: add command options for main and gen_cwl
    state.crate.add_workflow(source, dest_path, main=True, lang=language, gen_cwl=False)
    state.crate.metadata.write(crate_dir)
    # FIXME: change preview generation to be optional when reading a crate
    if not (Path(crate_dir) / Preview.BASENAME).is_file():
        state.crate.preview.write(crate_dir)


@add.command()
@click.option('-i', '--identifier')
@click.option('-n', '--name')
@click.option('-m', '--main-entity')
@click.pass_obj
def suite(state, identifier, name, main_entity):
    crate_dir = state.crate_dir or os.getcwd()
    suite_ = state.crate.add_test_suite(identifier=identifier, name=name, main_entity=main_entity)
    state.crate.metadata.write(crate_dir)
    print(suite_.id)


@add.command()
@click.argument('suite')
@click.argument('url')
@click.option('-r', '--resource', default="")
@click.option('-s', '--service', type=click.Choice(SERVICE_CHOICES), default="jenkins")
@click.option('-i', '--identifier')
@click.option('-n', '--name')
@click.pass_obj
def instance(state, suite, url, resource, service, identifier, name):
    crate_dir = state.crate_dir or os.getcwd()
    instance_ = state.crate.add_test_instance(suite, url, resource=resource, service=service, identifier=identifier, name=name)
    state.crate.metadata.write(crate_dir)
    print(instance_.id)


@add.command()
@click.argument('suite')
@click.argument('path', type=click.Path(exists=True))
@click.option('-e', '--engine', type=click.Choice(ENGINE_CHOICES), default="planemo")
@click.option('-v', '--engine-version')
@click.pass_obj
def definition(state, suite, path, engine, engine_version):
    crate_dir = state.crate_dir or os.getcwd()
    source = Path(path).resolve(strict=True)
    try:
        dest_path = source.relative_to(crate_dir)
    except ValueError:
        # For now, only support marking an existing file as a test definition
        raise ValueError(f"{source} is not in the crate dir")
    state.crate.add_test_definition(suite, source=source, dest_path=dest_path, engine=engine, engine_version=engine_version)
    state.crate.metadata.write(crate_dir)


if __name__ == '__main__':
    cli()
