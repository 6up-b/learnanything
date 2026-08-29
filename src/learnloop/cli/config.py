from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

config_app = typer.Typer(no_args_is_help=True, help="Inspect effective vault configuration.")

@config_app.command("effective")
def config_effective(
    vault: Annotated[
        Path | None,
        typer.Option("--vault", help="Vault root."),
    ] = None,
    only_overrides: Annotated[
        bool,
        typer.Option(
            "--only-overrides",
            help="Show only keys explicitly present in learnloop.toml.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON instead of TOML."),
    ] = False,
) -> None:
    """Print the modeled configuration that LearnLoop actually uses."""

    import tomllib
    import tomlkit

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    if only_overrides:
        with (vault_root / "learnloop.toml").open("rb") as handle:
            payload: dict[str, Any] = tomllib.load(handle)
    else:
        payload = loaded.config.model_dump(mode="json", exclude_none=True)
    if json_output:
        typer.echo(jsonlib.dumps(payload, sort_keys=True, indent=2))
    else:
        typer.echo(tomlkit.dumps(payload).rstrip())

__all__ = [name for name in globals() if not name.startswith("__")]
