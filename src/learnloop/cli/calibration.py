from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

calibration_app = typer.Typer(
    no_args_is_help=True, help="Grader-calibration streams and adjudication bootstrap."
)

@calibration_app.command("import-bundle")
def calibration_import_bundle(
    bundle_path: Annotated[Path, typer.Argument(help="Path to a calibration bundle YAML/JSON file.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Import shipped grader-calibration priors so this vault does not relearn a
    known grader from scratch. Models import as simulation_validated; promotion
    to live_calibrated still requires this vault's own adjudicated anchors."""

    import json as _json_module

    from learnloop.attempts.grader_calibration import import_calibration_bundle
    from learnloop.vault.yaml_io import read_yaml

    if bundle_path.suffix.lower() in (".yaml", ".yml"):
        bundle = read_yaml(bundle_path)
    else:
        bundle = _json_module.loads(bundle_path.read_text())
    repository = _repository(_root(vault))
    imported = import_calibration_bundle(repository, bundle)
    if json_output:
        typer.echo(_dump({"version": 1, "imported_model_ids": imported}))
        return
    if imported:
        typer.echo(f"Imported {len(imported)} calibration model(s): {', '.join(imported)}")
    else:
        typer.echo("Bundle already imported (content-hash match); nothing to do.")

@calibration_app.command("bootstrap-sample")
def calibration_bootstrap_sample(
    frame_id: Annotated[str | None, typer.Option("--frame-id", help="Reuse an existing sampling-frame id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON frame manifest.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Draw a stratified retrospective calibration sample over attempt history (§4.7).

    Read-only over history, append-only over calibration_stream_samples: writes one
    stream='calibration' row per selected attempt with a shared sampling frame id and
    logged inclusion probability, so this bootstrap batch composes with the ongoing
    stream. The actual owner adjudication session happens later (those become
    adjudicated-anchor samples and the first denominator-bearing counts)."""

    from learnloop.attempts.calibration_streams import build_bootstrap_frame

    repository = _repository(_root(vault))
    frame = build_bootstrap_frame(repository, frame_id=frame_id)
    payload = frame.as_dict()
    if json_output:
        typer.echo(_dump({"version": 1, "frame": payload}))
        return
    typer.echo(
        f"Sampling frame {frame.frame_id}: selected {frame.selected}/{frame.total_attempts} "
        f"attempts across {len(frame.stratum_counts)} strata."
    )
    for sample in frame.samples:
        typer.echo(
            f"- {sample['attempt_id']}: p={sample['inclusion_probability']:.3f} "
            f"stratum={sample['stratum']}"
        )

__all__ = [name for name in globals() if not name.startswith("__")]
