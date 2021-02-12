import click

from rocrate.rocrate import ROCrate


@click.group()
def cli():
    pass


@click.command()
@click.argument('top_dir')
def init(top_dir):
    crate = ROCrate(top_dir, init=True, load_preview=True)
    crate.metadata.write(top_dir)


@click.command()
def add():
    click.echo('Not implemented yet')


cli.add_command(init)
cli.add_command(add)


if __name__ == '__main__':
    cli()
