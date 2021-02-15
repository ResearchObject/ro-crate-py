import os

import click
from .rocrate import ROCrate


@click.group()
def cli():
    pass


@cli.command()
@click.argument('top_dir', nargs=-1)
def init(top_dir):
    print("top_dir", top_dir)
    if not top_dir:
        top_dir = (os.getcwd(),)
    for d in top_dir:
        crate = ROCrate(d, init=True, load_preview=True)
        crate.metadata.write(d)


@cli.command()
def add():
    click.echo('Not implemented yet')


if __name__ == '__main__':
    cli()
