from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

sim_app = typer.Typer(
    no_args_is_help=True,
    help="Synthetic-student simulation harness and config sensitivity sweeps.",
)

@sim_app.command("probe-validation")
def sim_probe_validation_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (copied per run, never written).")] = None,
    seeds: Annotated[int, typer.Option("--seeds", min=1, help="Runs per planted type.")] = 5,
    planted: Annotated[str | None, typer.Option("--planted", help="Comma-separated planted types (default: all).")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Target Learning Object (default: first with an open episode).")] = None,
    label_threshold: Annotated[float, typer.Option("--label-threshold", help="Per-type classification accuracy gate.")] = 0.6,
    action_threshold: Annotated[float, typer.Option("--action-threshold", help="Per-type instructional-action accuracy gate.")] = 0.6,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Checkpoint-3 episode validation against planted latent hypothesis types.

    Drives the real selection/presentation/observation/completion loop against
    planted `surface_only`, `confuses_with`, `schema_without_transfer`,
    `unfamiliar`, and `robust_initial_grasp` students, and gates on per-type
    classification and instructional-action accuracy (the Checkpoint-4 entry
    gate of spec_probe_eig_redesign.md).
    """

    import tempfile

    from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation

    source_root = _root(vault)
    planted_types = (
        tuple(part.strip() for part in planted.split(",") if part.strip())
        if planted
        else PLANTED_TYPES
    )
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-probe-validation-"))
    report = run_probe_validation(
        source_root,
        workdir,
        planted_types=planted_types,
        seeds=tuple(range(11, 11 + seeds)),
        learning_object_id=learning_object_id,
        config_overrides=_parse_sim_sets(sets),
    )
    payload = report.as_dict()
    payload["passes"] = report.passes(
        label_accuracy_threshold=label_threshold, action_accuracy_threshold=action_threshold
    )
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Run dir: {workdir}")
    for planted_type, summary in payload["by_planted"].items():
        typer.echo(
            f"{planted_type}: label {summary['label_accuracy']:.2f}, "
            f"action {summary['action_accuracy']:.2f}, "
            f"mean observations {summary['mean_observations']:.1f} ({summary['runs']} runs)"
        )
    typer.echo(
        f"Overall: label {payload['overall_label_accuracy']:.2f}, "
        f"action {payload['overall_action_accuracy']:.2f} — "
        f"{'PASS' if payload['passes'] else 'FAIL'} at label>={label_threshold} action>={action_threshold}"
    )
    if not payload["passes"]:
        raise typer.Exit(code=1)

@sim_app.command("probe-pilot")
def sim_probe_pilot_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Fixture vault root (copied per run, never written).")] = None,
    seeds: Annotated[int, typer.Option("--seeds", min=1, help="Runs per planted type.")] = 3,
    planted: Annotated[str | None, typer.Option("--planted", help="Comma-separated planted types (default: all).")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Target Learning Object.")] = None,
    label_threshold: Annotated[float, typer.Option("--label-threshold", help="Checkpoint 4 entry gate: per-type classification accuracy.")] = 0.6,
    action_threshold: Annotated[float, typer.Option("--action-threshold", help="Checkpoint 4 entry gate: per-type action accuracy.")] = 0.6,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Checkpoint-4 fixture-vault pilot: enforce the Checkpoint-3 sim entry
    gate, drive the full episode accounting against planted students, then run
    the §13 audit (predicted-vs-realized EIG, negative information, time
    calibration, cross-surface replication, shadow policies) and the replay
    determinism check on every run vault."""

    import tempfile

    from learnloop.diagnosis.probe_audit import pilot_report
    from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation

    source_root = _root(vault)
    planted_types = (
        tuple(part.strip() for part in planted.split(",") if part.strip())
        if planted
        else PLANTED_TYPES
    )
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-probe-pilot-"))
    validation = run_probe_validation(
        source_root,
        workdir,
        planted_types=planted_types,
        seeds=tuple(range(11, 11 + seeds)),
        learning_object_id=learning_object_id,
        config_overrides=_parse_sim_sets(sets),
    )
    entry_gate_passes = validation.passes(
        label_accuracy_threshold=label_threshold, action_accuracy_threshold=action_threshold
    )

    # Audit every run vault the validation produced; aggregate determinism.
    audits: list[dict] = []
    deterministic = True
    for run_root in sorted(workdir.glob("run_*")):
        try:
            run_vault = load_vault(run_root)
        except Exception:
            continue
        run_repository = _repository(run_vault.root)
        audit = pilot_report(run_vault, run_repository)
        audit["run"] = run_root.name
        deterministic = deterministic and audit["replay_determinism"]["deterministic"]
        audits.append(audit)

    payload = {
        "version": 1,
        "entry_gate": {
            "passes": entry_gate_passes,
            "label_threshold": label_threshold,
            "action_threshold": action_threshold,
            **validation.as_dict(),
        },
        "replay_deterministic": deterministic,
        "audits": audits,
    }
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Run dir: {workdir}")
    typer.echo(
        f"Entry gate (Checkpoint 3 sim validation): {'PASS' if entry_gate_passes else 'FAIL'} "
        f"at label>={label_threshold} action>={action_threshold}"
    )
    total_observations = sum(a["eig_calibration"]["observations"] for a in audits)
    negative = sum(a["eig_calibration"]["negative_information_count"] for a in audits)
    typer.echo(
        f"Audited {len(audits)} run vaults: {total_observations} qualifying observations, "
        f"{negative} with negative realized information."
    )
    typer.echo(f"Replay determinism: {'OK' if deterministic else 'FAILED'}")
    if not entry_gate_passes or not deterministic:
        raise typer.Exit(code=1)

@sim_app.command("benchmark-forgetting")
def sim_benchmark_forgetting_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (read-only).")] = None,
    train_fraction: Annotated[float, typer.Option("--train-fraction", min=0.1, max=0.9, help="Temporal split point.")] = 0.7,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Offline DAS3H-style forgetting benchmark (probe redesign Checkpoint 5.6).

    Fits a time-window logistic model on the vault's attempt history and
    compares held-out next-attempt prediction against frequency baselines.
    Report-only: never replaces durable state or facet mappings."""

    from learnloop.sim.offline_benchmarks import run_forgetting_benchmark

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    report = run_forgetting_benchmark(repository, train_fraction=train_fraction)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    if report["status"] != "ok":
        typer.echo(f"{report['status']}: {report.get('examples', 0)} examples "
                   f"(need {report.get('minimum_examples')})")
        return
    typer.echo(f"Train {report['train_examples']} / test {report['test_examples']} attempts.")
    for name, metrics in report["results"].items():
        typer.echo(f"- {name}: log loss {metrics['log_loss']}, Brier {metrics['brier']}")
    typer.echo(f"Best by log loss: {report['best_by_log_loss']} (report-only; nothing auto-adopted)")

@sim_app.command("run")
def sim_run_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (never written by default).")] = None,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or profile YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", help="Simulated days.")] = 60,
    items_per_day: Annotated[int, typer.Option("--items-per-day", help="Attempts per simulated day.")] = 6,
    seed: Annotated[int, typer.Option("--seed", help="Student RNG seed.")] = 42,
    fresh_copy: Annotated[bool, typer.Option("--fresh-copy/--in-place", help="Copy the vault to a tmp run dir (default) or simulate in place.")] = True,
    reset_state: Annotated[bool, typer.Option("--reset-state/--keep-state", help="Drop derived SQLite state in the run copy (default: reset).")] = True,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    primed_retries: Annotated[bool, typer.Option("--primed-retries/--no-primed-retries", help="After each failed attempt, re-read the source and retry a sibling item as a primed attempt.")] = False,
    goal_due_day: Annotated[int | None, typer.Option("--goal-due-day", help="Set every active goal's due date N sim-days in (exercises the projection horizon and ramping goal quota).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Simulate a synthetic student through the real scheduling/belief pipeline."""

    from learnloop.sim.profiles import ProfileError, load_profile
    from learnloop.sim.runner import SimulationError, run_simulation

    source_root = _root(vault)
    try:
        student_profile = load_profile(profile)
        run_root = _sim_run_root(source_root, fresh_copy=fresh_copy, reset_state=reset_state)
        report = run_simulation(
            run_root,
            student_profile,
            days=days,
            items_per_day=items_per_day,
            seed=seed,
            config_overrides=_parse_sim_sets(sets),
            primed_retries=primed_retries,
            goal_due_day=goal_due_day,
        )
    except (ProfileError, SimulationError, ConfigLoadError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "sim_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    payload = report.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    metrics = report.metrics
    belief = metrics.get("belief_vs_truth", {})
    calibration = metrics.get("calibration", {})
    counts = metrics.get("counts", {})
    typer.echo(f"Run dir: {run_root}")
    typer.echo(
        f"Simulated {days} days x {items_per_day} items as {student_profile.name} (seed {seed}): "
        f"{counts.get('attempts', 0)} attempts."
    )
    typer.echo(
        f"Belief vs truth: MAE={belief.get('mae')} "
        f"(day1 {belief.get('daily_mae_first')} -> final {belief.get('daily_mae_last')}), "
        f"sign agreement {belief.get('sign_agreement_rate')}"
    )
    typer.echo(
        f"Calibration: brier={calibration.get('brier')} log_loss={calibration.get('log_loss')} "
        f"n={calibration.get('n')}"
    )
    typer.echo(
        f"Counts: followups={counts.get('followups_triggered')} "
        f"dont_know={counts.get('dont_know_attempts')} "
        f"error_events={counts.get('error_events_created')} "
        f"resolved={counts.get('error_events_resolved')}"
    )
    for planted in metrics.get("misconceptions", {}).get("planted", []):
        verdict = "DETECTED" if planted.get("detected") else "NOT DETECTED"
        typer.echo(
            f"Misconception {planted['error_type']} on {planted['facet_id']}: {verdict} "
            f"(first error event day {planted.get('first_error_event_day')}, "
            f"known_gap day {planted.get('first_known_gap_day')}, "
            f"{planted.get('error_events')} events, "
            f"{planted.get('error_events_resolved')} resolved)"
        )
    false_positives = metrics.get("misconceptions", {}).get("false_positive_misconception_types", [])
    if false_positives:
        typer.echo(f"False-positive misconception types: {', '.join(false_positives)}")
    for goal_entry in metrics.get("goals", {}).get("per_goal", []):
        typer.echo(
            f"Goal {goal_entry['goal_id']} (due day {goal_entry['due_day']}): "
            f"truth at target {goal_entry['truth_at_target_fraction_at_due']} at due, "
            f"{goal_entry['truth_at_target_fraction_due_plus_30']} at due+30d; "
            f"belief on-track {goal_entry['belief_on_track_fraction_at_due']}; "
            f"frontier empty day {goal_entry['frontier_empty_day']}"
        )

@sim_app.command("sweep")
def sim_sweep_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (never written; each run uses a fresh copy).")] = None,
    spec: Annotated[Path | None, typer.Option("--spec", help="Sweep spec YAML (defaults to the packaged default_sweep.yaml).")] = None,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or profile YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", help="Simulated days per run.")] = 30,
    items_per_day: Annotated[int, typer.Option("--items-per-day", help="Attempts per simulated day.")] = 6,
    seed: Annotated[int, typer.Option("--seed", help="Student RNG seed (shared by all runs).")] = 42,
    reset_state: Annotated[bool, typer.Option("--reset-state/--keep-state", help="Drop derived SQLite state in each run copy (default: reset).")] = True,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Baseline config override param.path=value (repeatable).")] = None,
    primed_retries: Annotated[bool, typer.Option("--primed-retries/--no-primed-retries", help="Enable primed source-review retries in every run (needed for the priming_b_offset sweep).")] = False,
    goal_due_day: Annotated[int | None, typer.Option("--goal-due-day", help="Set every active goal's due date N sim-days in for all runs (needed for the goal quota sweeps).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Sweep config parameters and report which ones change scheduling decisions."""

    import tempfile

    from learnloop.sim.profiles import ProfileError, load_profile
    from learnloop.sim.runner import SimulationError
    from learnloop.sim.sweep import SweepSpecError, load_sweep_spec, run_sweep

    source_root = _root(vault)
    try:
        student_profile = load_profile(profile)
        entries = load_sweep_spec(spec)
        work_dir = Path(tempfile.mkdtemp(prefix="learnloop-sweep-"))
        report = run_sweep(
            source_root,
            student_profile,
            sweep_spec=entries,
            days=days,
            items_per_day=items_per_day,
            seed=seed,
            work_dir=work_dir,
            reset_state=reset_state,
            base_overrides=_parse_sim_sets(sets),
            primed_retries=primed_retries,
            goal_due_day=goal_due_day,
        )
    except (ProfileError, SimulationError, SweepSpecError, ConfigLoadError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "sweep_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    payload = report.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Sweep work dir: {work_dir}")
    typer.echo(
        f"Baseline: {student_profile.name}, {days} days x {items_per_day} items, seed {seed}."
    )
    header = f"{'param=value':<62} {'topK':>6} {'tau':>6} {'dFllw':>6} {'dErr':>6} {'dMAE':>9}  verdict"
    typer.echo(header)
    typer.echo("-" * len(header))
    for result in report.results:
        if result.get("verdict") == "error":
            typer.echo(f"{result['param_path']}={result['value']}: ERROR {result['error']}")
            continue
        label = f"{result['param_path']}={result['value']}"
        counts = result["count_deltas"]
        metric_deltas = result["metric_deltas"]
        topk = result.get("mean_topk_overlap")
        tau = result.get("mean_kendall_tau")
        mae = metric_deltas.get("belief_mae")
        typer.echo(
            f"{label:<62} "
            f"{topk if topk is not None else '-':>6} "
            f"{tau if tau is not None else '-':>6} "
            f"{counts.get('followups_triggered', 0):>6} "
            f"{counts.get('error_events_created', 0):>6} "
            f"{mae if mae is not None else '-':>9}  "
            f"{result['verdict']}"
        )

__all__ = [name for name in globals() if not name.startswith("__")]
