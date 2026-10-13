"""`learnloop evsi simulate` and `learnloop evsi calibration` (EVSI calibration).

``simulate`` is the offline Part A study: no vault, no network, no paid call.
It fits the response model to the Eedi NeurIPS 2020 answers, builds
simulated learners from the Eedi 2024 misconception labels and runs the real
EIG and EVSI selectors against baselines.

``calibration`` is the live Part B report: read-only over a vault's
``voi_forecasts`` receipts, joined to realized outcomes and later truth.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

evsi_app = typer.Typer(no_args_is_help=True, help="Value-of-information calibration (EVSI/EIG).")


def _emit(payload: dict, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2, default=str))


@evsi_app.command("simulate")
def evsi_simulate_command(
    eedi_2024: Annotated[Path, typer.Option("--eedi-2024", help="Directory with the Eedi 2024 Kaggle train.csv and misconception_mapping.csv.")],
    eedi_2020: Annotated[Path | None, typer.Option("--eedi-2020", help="Directory with the extracted Eedi NeurIPS 2020 archive (data/...). Needed unless --fit is given.")] = None,
    fit_path: Annotated[Path | None, typer.Option("--fit", help="A response_fit.json from an earlier run (skips the fit).")] = None,
    output: Annotated[Path, typer.Option("--output", help="Directory for response_fit.json and simulation_report.json.")] = Path("fixtures-local/evsi-calibration"),
    task: Annotated[str, typer.Option("--task", help="Eedi 2020 task to fit on: 1_2 (15.9M answers) or 3_4 (1.4M).")] = "1_2",
    learners: Annotated[int, typer.Option("--learners", min=10, help="Flagged learners per arm.")] = 400,
    sensitivity_learners: Annotated[int, typer.Option("--sensitivity-learners", min=10, help="Learners per sensitivity arm.")] = 300,
    workers: Annotated[int, typer.Option("--workers", min=1, help="Worker processes.")] = 4,
    seed: Annotated[int, typer.Option("--seed")] = 20261012,
    quick: Annotated[bool, typer.Option("--quick", help="A small smoke run (few learners, one regime row, short sweeps).")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Fit the response model to Eedi, simulate, and score EIG/EVSI against baselines."""

    from learnloop.evsi_calibration.eedi import load_eedi_2024, load_neurips_2020
    from learnloop.evsi_calibration.experiments import SWEEPS, ExperimentSettings, run_experiments
    from learnloop.evsi_calibration.response_fit import FitSettings, ResponseFit, fit_response_model

    def say(message: str) -> None:
        if not json_output:
            typer.echo(f"[evsi simulate] {message}", err=True)

    try:
        bank = load_eedi_2024(eedi_2024)
        output.mkdir(parents=True, exist_ok=True)
        if fit_path is not None:
            fit = ResponseFit.from_dict(json.loads(fit_path.read_text(encoding="utf-8")))
            say(f"fit loaded from {fit_path}")
        else:
            if eedi_2020 is None:
                raise ValueError("--eedi-2020 is required unless --fit names an earlier response_fit.json")
            say(f"loading Eedi 2020 task {task}")
            responses = load_neurips_2020(eedi_2020, task=task, cache_dir=output / "cache", with_dates=True)
            say(f"fitting the response model on {responses.rows} answers")
            fit = fit_response_model(responses, settings=FitSettings(seed=seed))
            (output / "response_fit.json").write_text(json.dumps(fit.as_dict(), sort_keys=True, indent=1), encoding="utf-8")
        settings = ExperimentSettings(
            learners=learners, sensitivity_learners=min(sensitivity_learners, learners), seed=seed, workers=workers
        )
        if quick:
            settings = ExperimentSettings(
                learners=min(learners, 60), sensitivity_learners=min(sensitivity_learners, 40), seed=seed,
                workers=workers, regime_consistencies=(None,), regime_repairs=(3.0,), unresolved_encounters=(6.0,),
                bootstrap=50, sweeps=tuple(list(SWEEPS)[:2]), draw_count=8,
            )
        report = run_experiments(bank, fit, settings, progress=say)
        report["sweeps"] = {name: {"field": f, "current": c, "grid": list(g)} for name, (f, c, g) in SWEEPS.items()}
        report_path = output / "simulation_report.json"
        report_path.write_text(json.dumps(report, sort_keys=True, indent=1, default=str), encoding="utf-8")
        headline = {
            "status": "ok",
            "report": str(report_path),
            "fit": {k: v["median"] for k, v in report["fit"]["pooled"].items()},
            "flagged_learners": report["bank"]["flagged_learners"],
            "main": {
                model: {
                    policy: {
                        "mean_total_minutes": blocks["episodes"]["mean_total_minutes"],
                        "mean_checks": blocks["episodes"]["mean_checks"],
                        "log_loss": blocks["outcome_calibration"].get("log_loss"),
                    }
                    for policy, blocks in rows.items()
                }
                for model, rows in report["main"].items()
            },
            "elapsed_seconds": report["elapsed_seconds"],
        }
        _emit(headline, json_output)
    except (ValueError, OSError, KeyError) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@evsi_app.command("calibration")
def evsi_calibration_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    since: Annotated[str | None, typer.Option("--since", help="Only forecasts at or after this ISO time (UTC).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Live calibration of value-of-information forecasts (read-only)."""

    from learnloop.evsi_calibration.live_report import calibration_report
    from learnloop.vault.loader import load_vault

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        _emit(calibration_report(loaded, since=since), json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
