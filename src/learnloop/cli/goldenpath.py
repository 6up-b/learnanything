from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

goldenpath_app = typer.Typer(
    no_args_is_help=True, help="P2 golden-path fixture bootstrap (spec_p2 §C)."
)

@goldenpath_app.command("init-fixture")
def goldenpath_init_fixture(
    path: Annotated[Path, typer.Argument(help="Target dir for the fresh mvp-0.8 fixture vault.")],
) -> None:
    """Deterministically build the P2 golden-path fixture vault (symmetric-matrices,
    method-selection family) and confirm the run. Idempotent per §12.8: two builds
    into empty roots produce identical content hashes."""

    from learnloop.curriculum.golden_path_fixture import build_golden_path_fixture

    if path.exists() and any(path.iterdir()):
        typer.echo(_dump({"version": 1, "error": "target_not_empty", "path": str(path)}))
        raise typer.Exit(code=1)
    fixture = build_golden_path_fixture(path)
    typer.echo(_dump({"version": 1, "fixture": fixture.as_dict()}))

__all__ = [name for name in globals() if not name.startswith("__")]
