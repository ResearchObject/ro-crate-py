import os

import click
from .rocrate import ROCrate


class State:
    pass


@click.group()
@click.option('-c', '--crate-dir')
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


if __name__ == '__main__':
    cli()
