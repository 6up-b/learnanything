"""Explicit owner-side artifact checks, with optional dependencies loaded on use."""
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

notebook_app = typer.Typer(help='Inspect owner-authored notebooks without executing them.')


class Scope(str, Enum):
    structure = 'structure'


@notebook_app.command('check')
def check(
    path: Annotated[Path, typer.Argument(help='Marimo Python notebook to inspect.')],
    scope: Annotated[Scope, typer.Option('--scope', help='Checks to perform; structure does not imply acceptance.')],
    out: Annotated[Path, typer.Option('--out', help='Explicit report directory outside the checkout; no symlinks.')],
) -> None:
    """Write structure.json and structure.txt; exit 1 for structural findings, 2 for refusal."""
    from learnloop.notebook_authoring.check import OutputPathError, check_structure

    try:
        report, summary = check_structure(path, out)
    except OutputPathError as exc:
        typer.echo(f'Output refused: {exc}', err=True)
        raise typer.Exit(2) from exc
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(summary, nl=False)
    raise typer.Exit(1 if report['findings'] else 0)
