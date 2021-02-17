import os
from pathlib import Path

import click
from .rocrate import ROCrate
from .model.preview import Preview
from .model.computerlanguage import LANG_MAP


LANG_CHOICES = list(LANG_MAP)


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
@click.option('-l', '--language', type=click.Choice(LANG_CHOICES))
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


if __name__ == '__main__':
    cli()
