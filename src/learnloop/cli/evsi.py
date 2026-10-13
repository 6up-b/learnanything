"""`learnloop evsi simulate` and `learnloop evsi calibration` (EVSI calibration).

``simulate`` is the offline Part A study: no vault, no network, no paid call.
It fits the response model to the Eedi NeurIPS 2020 answers, builds
simulated learners from the Eedi 2024 misconception labels and runs the real
EIG and EVSI selectors against baselines.

``multisim`` (stage ``evsi-multisim``) fits several structurally different
simulator families to the same Eedi answers and reruns the study in each, so a
conclusion counts only when every family agrees (RankCert). Offline, no paid
call.

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

    from learnloop.evsi_calibration.artifacts import write_text_atomic
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
            write_text_atomic(output / "response_fit.json", json.dumps(fit.as_dict(), sort_keys=True, indent=1))
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
        write_text_atomic(report_path, json.dumps(report, sort_keys=True, indent=1, default=str))
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


@evsi_app.command("multisim")
def evsi_multisim_command(
    eedi_2024: Annotated[Path | None, typer.Option("--eedi-2024", help="Directory with the Eedi 2024 Kaggle train.csv and misconception_mapping.csv. Needed unless --reanalyze is given.")] = None,
    eedi_2020: Annotated[Path | None, typer.Option("--eedi-2020", help="Directory with the extracted Eedi NeurIPS 2020 archive. Needed unless --fits is given.")] = None,
    fit_path: Annotated[Path | None, typer.Option("--fit", help="The single-family study's response_fit.json: reuse its misconception triples (else they are searched again).")] = None,
    fits_path: Annotated[Path | None, typer.Option("--fits", help="A family_fits.json from an earlier multisim run (skips every family fit).")] = None,
    output: Annotated[Path, typer.Option("--output", help="Directory for family_fits.json and multisim_report.json.")] = Path("fixtures-local/evsi-multisim"),
    task: Annotated[str, typer.Option("--task", help="Eedi 2020 task to fit on: 1_2 (15.9M answers) or 3_4 (1.4M).")] = "1_2",
    cache_dir: Annotated[Path | None, typer.Option("--cache-dir", help="Where the parsed Eedi 2020 answers are cached (default: <output>/cache).")] = None,
    learners: Annotated[int, typer.Option("--learners", min=10, help="Flagged learners per arm.")] = 400,
    sensitivity_learners: Annotated[int, typer.Option("--sensitivity-learners", min=10, help="Learners per sensitivity arm.")] = 300,
    workers: Annotated[int, typer.Option("--workers", min=1, help="Worker processes.")] = 4,
    seed: Annotated[int, typer.Option("--seed")] = 20261012,
    quick: Annotated[bool, typer.Option("--quick", help="A small smoke run (few learners, two regimes, short sweeps).")] = False,
    reanalyze: Annotated[Path | None, typer.Option("--reanalyze", help="A multisim_report.json to re-score: recompute its analysis from the stored per-learner episodes (no fit, no simulation) and write it back.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Fit several simulator families to Eedi and rerun the EVSI study in each (RankCert)."""

    from learnloop.evsi_calibration.artifacts import write_text_atomic
    from learnloop.evsi_calibration.eedi import load_eedi_2024, load_neurips_2020
    from learnloop.evsi_calibration.experiments import SWEEPS
    from learnloop.evsi_calibration.family_data import build_subject_data, build_triple_data
    from learnloop.evsi_calibration.family_fit import FamilyFits, FamilyFitSettings, fit_families
    from learnloop.evsi_calibration.multifamily import MultiFamilySettings, analyze, run_multifamily
    from learnloop.evsi_calibration.response_fit import FitSettings, ResponseFit, fit_response_model

    def say(message: str) -> None:
        if not json_output:
            typer.echo(f"[evsi multisim] {message}", err=True)

    def headline(report: dict, report_path: Path) -> dict:
        analysis = report["analysis"]
        return {
            "status": "ok",
            "report": str(report_path),
            "families": analysis["families"],
            "stress_families": analysis["stress_families"],
            "excluded_families": analysis.get("excluded_families", []),
            "adequacy": {
                name: block.get("adequate")
                for name, block in (report["fits"]["validation"].get("families") or {}).items()
                if name != "marginal"
            },
            "claims": {claim["id"]: claim["verdict"] for claim in analysis["claims"]},
            "most_robust_policy": (analysis.get("policy_regret") or [{}])[0].get("policy"),
            "elapsed_seconds": report["elapsed_seconds"],
        }

    try:
        if reanalyze is not None:
            report = json.loads(reanalyze.read_text(encoding="utf-8"))
            report["analysis"] = analyze(report)
            # Atomic: the stored episodes are the expensive part (review F5).
            write_text_atomic(reanalyze, json.dumps(report, sort_keys=True, default=str))
            say(f"analysis recomputed from the stored episodes in {reanalyze}")
            _emit(headline(report, reanalyze), json_output)
            return
        if eedi_2024 is None:
            raise ValueError("--eedi-2024 is required unless --reanalyze names an earlier multisim_report.json")
        bank = load_eedi_2024(eedi_2024)
        output.mkdir(parents=True, exist_ok=True)
        if fits_path is not None:
            fits = FamilyFits.from_dict(json.loads(fits_path.read_text(encoding="utf-8")))
            say(f"family fits loaded from {fits_path}")
        else:
            if eedi_2020 is None:
                raise ValueError("--eedi-2020 is required unless --fits names an earlier family_fits.json")
            say(f"loading Eedi 2020 task {task}")
            responses = load_neurips_2020(eedi_2020, task=task, cache_dir=cache_dir or output / "cache", with_dates=True)
            if fit_path is not None:
                triples = ResponseFit.from_dict(json.loads(fit_path.read_text(encoding="utf-8"))).triples
                say(f"{len(triples)} triples from {fit_path}")
            else:
                say("searching misconception triples")
                triples = fit_response_model(responses, settings=FitSettings(seed=seed)).triples
            triple_data = build_triple_data(responses, triples)
            subject_data = build_subject_data(responses, [t.split(held_out=False) for t in triple_data])
            fit_settings = FamilyFitSettings(workers=workers)
            if quick:
                fit_settings = FamilyFitSettings(workers=workers, lca_iterations=200, cdm_iterations=100,
                                                 nrm_iterations=40, lta_iterations=60, bootstrap=50)
            fits = fit_families(
                triple_data, subject_data, fit_settings, progress=say,
                source={"dataset": "Eedi NeurIPS 2020 Education Challenge (public archive)", "task": task,
                        "source_hash": responses.source_hash, "triples_from": str(fit_path) if fit_path else "search"},
            )
            write_text_atomic(output / "family_fits.json", json.dumps(fits.as_dict(), sort_keys=True))
        settings = MultiFamilySettings(
            learners=learners, sensitivity_learners=min(sensitivity_learners, learners), seed=seed, workers=workers,
        )
        if quick:
            settings = MultiFamilySettings(
                learners=min(learners, 40), sensitivity_learners=min(sensitivity_learners, 30), seed=seed,
                workers=workers, strengths=(None, 0.9), repairs=(3.0, 30.0), rotation_regimes=((0.9, 30.0),),
                sweeps=tuple(list(SWEEPS)[:2]), unresolved_encounters=(12.0,), pseudo_counts=(2.0, 8.0),
                pseudo_count_regimes=((None, 3.0),), pseudo_count_block=20, draw_count=8, bootstrap=50,
            )
        report = run_multifamily(bank, fits, settings, progress=say)
        report_path = output / "multisim_report.json"
        write_text_atomic(report_path, json.dumps(report, sort_keys=True, default=str))
        _emit(headline(report, report_path), json_output)
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
