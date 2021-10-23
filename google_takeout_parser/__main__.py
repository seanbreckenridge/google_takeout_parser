import shutil
from pathlib import Path
from typing import List

import click

from .cache import takeout_cache_path
from .path_dispatch import TakeoutParser, Results, Event, Res


@click.group()
def main() -> None:
    """
    Parse a google takeout!
    """
    pass


@main.group(
    name="cache_dir", invoke_without_command=True, short_help="interact with cache dir"
)
@click.pass_context
def cache_dir(ctx: click.Context) -> None:
    """
    Print location of cache dir
    """
    if ctx.invoked_subcommand is None:
        click.echo(str(takeout_cache_path.absolute()))


@cache_dir.command(name="clear")
def cache_dir_remove() -> None:
    """
    Remove the cache directory
    """
    click.echo(str(takeout_cache_path))
    click.echo("Contents:")
    for f in takeout_cache_path.rglob("*"):
        print(f"\t{str(f)}")
    if click.confirm("Really remove this directory?"):
        shutil.rmtree(str(takeout_cache_path))


@main.command(short_help="parse a takeout directory")
@click.option("--cache/--no-cache", default=True)
@click.argument("TAKEOUT_DIR")
def parse(cache: bool, takeout_dir: str) -> None:
    """
    Parse a google takeout and interact with it in the REPL
    """
    import IPython  # type: ignore[import]

    p = Path(str(takeout_dir)).absolute()
    ires: Results
    tp = TakeoutParser(p, drop_exceptions=True)
    if cache:
        ires = tp.cached_parse()
    else:
        ires = tp.parse()
    click.echo("Parsing...")
    # note: actually no exceptions since since they're dropped
    res: List[Res[Event]] = list(ires)

    click.echo(f"Interact with the export using {click.style('res', 'green')}")

    IPython.embed()


if __name__ == "__main__":
    main(prog_name="google_takeout_parser")
