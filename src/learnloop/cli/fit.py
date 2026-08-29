from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

fit_app = typer.Typer(no_args_is_help=True, help="Fit algorithm parameters from logged attempts.")

@fit_app.command("fsrs")
def fit_fsrs_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Fit and report without persisting.")] = False,
) -> None:
    """Fit FSRS weights to this learner's own review log (pure Python)."""

    from learnloop.params.fitted_params import FSRS_WEIGHTS_SCOPE
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
    from learnloop.scheduling.fsrs_fitting import FIT_INDICES, FsrsFittingError, fit_fsrs_weights
    from learnloop.scheduling.review_log import reconstruct_review_log

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    review_log = reconstruct_review_log(loaded, repository)
    try:
        result = fit_fsrs_weights(review_log, config=loaded.config.fitting.fsrs)
    except FsrsFittingError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "insufficient_reviews", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    persisted_id: str | None = None
    if result.improved and not dry_run:
        persisted_id = repository.insert_fitted_parameters(
            scope=FSRS_WEIGHTS_SCOPE,
            params={
                "weights": list(result.weights),
                "fitted_indices": list(result.fitted_indices),
                "pinned_from": "fsrs6_defaults",
            },
            algorithm_version=loaded.config.algorithms.algorithm_version,
            training_rows_count=result.predicted_count,
            training_data_through=result.data_through,
            metrics={
                "log_loss_default": result.log_loss_default,
                "log_loss_fitted": result.log_loss_fitted,
                "relative_improvement": result.relative_improvement,
                "iterations": result.iterations,
                "converged": result.converged,
                "fitter": "fsrs_fitting.v1",
            },
        )

    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "fit": result,
                    "persisted_id": persisted_id,
                    "activated": persisted_id is not None,
                }
            )
        )
        return
    typer.echo(
        f"Reviews: {result.review_count} total, {result.predicted_count} usable "
        f"(skipped {review_log.skipped_attempts} attempts missing from vault)."
    )
    typer.echo(
        f"Log-loss: default {result.log_loss_default:.4f} -> fitted {result.log_loss_fitted:.4f} "
        f"({result.relative_improvement:+.1%}, {result.iterations} iterations, converged={result.converged})"
    )
    for index in FIT_INDICES:
        typer.echo(f"  w{index}: {FSRS6_DEFAULT_WEIGHTS[index]:.4f} -> {result.weights[index]:.4f}")
    if persisted_id is not None:
        typer.echo(f"Activated fitted set {persisted_id}.")
    elif result.improved and dry_run:
        typer.echo("Dry run: improved fit not persisted.")
    else:
        typer.echo(
            "Fitted weights do not beat defaults by the configured margin; nothing persisted "
            f"(need >= {loaded.config.fitting.fsrs.min_relative_improvement:.1%} improvement)."
        )

@fit_app.command("gate")
def fit_gate_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Fit and report without persisting.")] = False,
    min_labels: Annotated[int, typer.Option("--min-labels", help="Minimum strong labels (overrides + ratings).")] = 20,
    l2: Annotated[float, typer.Option("--l2")] = 0.1,
    epochs: Annotated[int, typer.Option("--epochs")] = 500,
    learning_rate: Annotated[float, typer.Option("--lr")] = 0.5,
) -> None:
    """Fit follow-up gate weights from manual-override + usefulness labels."""

    from learnloop.params.fitted_params import FOLLOWUP_GATE_SCOPE
    from learnloop.diagnosis.gate_fit import GateFitError, assemble_gate_training_set, fit_gate_weights
    from learnloop.diagnosis.gate_score import GATE_FEATURE_VERSION

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    examples = assemble_gate_training_set(repository, loaded.config)
    strong = sum(1 for example in examples if example.label_source != "silent_gate")
    if strong < min_labels:
        message = (
            f"Only {strong} strong gate labels (manual overrides + ratings); "
            f"need at least {min_labels} to fit. Keep using ⇧D and the usefulness rating."
        )
        if json_output:
            typer.echo(_dump({"version": 1, "error": "insufficient_labels", "message": message}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = fit_gate_weights(examples, l2=l2, epochs=epochs, learning_rate=learning_rate)
    except GateFitError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "unfittable", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    persisted_id: str | None = None
    if not dry_run:
        persisted_id = repository.insert_fitted_parameters(
            scope=FOLLOWUP_GATE_SCOPE,
            params={
                "weights": result.weights,
                "bias": result.bias,
                "feature_version": GATE_FEATURE_VERSION,
            },
            algorithm_version=loaded.config.algorithms.algorithm_version,
            training_rows_count=result.n_examples,
            metrics={
                "auc": result.auc,
                "accuracy": result.accuracy,
                "log_loss": result.log_loss,
                "n_positive": result.n_positive,
                "n_negative": result.n_negative,
                "label_source_counts": result.label_source_counts,
                "fitter": "gate_fit.v2",
                "feature_version": GATE_FEATURE_VERSION,
            },
        )
    if json_output:
        typer.echo(_dump({"version": 1, "fit": result, "persisted_id": persisted_id}))
        return
    typer.echo(
        f"Labels: {result.n_examples} total ({result.n_positive} positive / {result.n_negative} negative), "
        f"{result.n_strong_labels} strong; sources {result.label_source_counts}"
    )
    typer.echo(f"AUC {result.auc:.3f}  accuracy {result.accuracy:.3f}  log-loss {result.log_loss:.4f}")
    for name, weight in sorted(result.weights.items()):
        typer.echo(f"  {name}: {weight:+.3f}")
    typer.echo(f"  bias: {result.bias:+.3f}")
    if persisted_id is not None:
        typer.echo(f"Activated fitted gate weights {persisted_id} (gate_mode=score uses them immediately).")
    else:
        typer.echo("Dry run: not persisted.")

@fit_app.command("show")
def fit_show_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    scope: Annotated[str | None, typer.Option("--scope", help="Filter by scope.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List fitted parameter sets (newest first)."""

    root = _root(vault)
    _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    rows = repository.list_fitted_parameters(scope)
    if json_output:
        typer.echo(_dump({"version": 1, "fitted_parameters": rows}))
        return
    if not rows:
        typer.echo("No fitted parameter sets.")
        return
    for row in rows:
        marker = "*" if row["active"] else " "
        metrics = row.get("metrics") or {}
        detail = ", ".join(
            f"{key}={value}" for key, value in sorted(metrics.items()) if isinstance(value, (int, float))
        )
        typer.echo(
            f"{marker} {row['id']}  {row['scope']}  fitted_at={row['fitted_at']}  "
            f"rows={row['training_rows_count']}  {detail}"
        )

@fit_app.command("deactivate")
def fit_deactivate_command(
    scope: Annotated[str, typer.Argument(help="Fitted-parameter scope (e.g. fsrs_weights).")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    fitted_id: Annotated[str | None, typer.Option("--id", help="Deactivate only this set id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Deactivate the active fitted set for a scope; defaults apply afterwards."""

    root = _root(vault)
    _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    count = repository.deactivate_fitted_parameters(scope, fitted_id=fitted_id)
    if json_output:
        typer.echo(_dump({"version": 1, "deactivated": count, "scope": scope}))
        return
    typer.echo(f"Deactivated {count} fitted set(s) for scope {scope}; defaults now apply.")

__all__ = [name for name in globals() if not name.startswith("__")]
