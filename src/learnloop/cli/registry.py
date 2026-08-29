from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

registry_app = typer.Typer(
    no_args_is_help=True, help="Calibration-status parameter registry: audit, list, trace."
)

@registry_app.command("audit")
def registry_audit(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON audit report.")] = False,
) -> None:
    """Decision-parameter audit (§6/§9.6): every LearnLoopConfig numeric leaf and
    named module constant must classify decision/structural; every decision entry
    needs status/provenance. Exit non-zero on any failure (CI-usable)."""

    from learnloop.params import parameter_registry as pr

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    report = pr.audit(loaded, repository)
    if json_output:
        typer.echo(_dump(report.as_dict()))
    else:
        typer.echo("Registry audit: " + ("CLEAN" if report.clean else "FAILURES"))
        for name in report.failures:
            typer.echo(f"  {name}: {getattr(report, name)}")
        # active_pending_certificate is enumerated debt, not a failure: report it as a
        # warning section (the strict `release-check` gate is what blocks on it).
        pending = report.active_pending_certificate
        if pending:
            typer.echo(
                f"  warning active_pending_certificate ({len(pending)}): "
                f"{pending} (blocks `registry release-check`)"
            )
    if not report.clean:
        raise typer.Exit(code=1)

@registry_app.command("list")
def registry_list(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    status: Annotated[str | None, typer.Option("--status")] = None,
    lifecycle: Annotated[str | None, typer.Option("--lifecycle")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List registry entries with optional status/lifecycle/kind filters."""

    from learnloop.params import parameter_registry as pr

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    rows = repository.parameter_registry_entries()
    if status:
        rows = [r for r in rows if r["status"] == status]
    if lifecycle:
        rows = [r for r in rows if r["lifecycle"] == lifecycle]
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    if json_output:
        typer.echo(_dump({"version": 1, "entries": rows}))
        return
    for r in rows:
        typer.echo(f"{r['path']}\t{r['kind']}\t{r['status']}\t{r['lifecycle']}\t{r['source']}")

@registry_app.command("show")
def registry_show(
    path: Annotated[str, typer.Argument(help="Registered parameter path.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Trace one parameter to its registry entry (§9.7 item 5): effective value,
    source, status, lifecycle, evidence refs, last review."""

    from learnloop.params import parameter_registry as pr

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    entry = repository.parameter_registry_entry(path)
    if entry is None:
        typer.echo(f"No registry entry for {path!r}.")
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump(entry))
        return
    for key in ("path", "kind", "param_class", "effective_value_json", "source",
                "status", "lifecycle", "rationale", "sensitivity_certificate_id",
                "last_review_at"):
        typer.echo(f"{key}: {entry.get(key)}")

@registry_app.command("certify")
def registry_certify(
    path: Annotated[str, typer.Argument(help="Config parameter path to certify (sweepable).")],
    low: Annotated[float, typer.Option("--low", help="Low end of the plausible range.")],
    high: Annotated[float, typer.Option("--high", help="High end of the plausible range.")],
    steps: Annotated[int, typer.Option("--steps", min=2, help="Grid points across [low, high].")] = 3,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", min=1, help="Sim days per grid point.")] = 8,
    items_per_day: Annotated[int, typer.Option("--items-per-day", min=1)] = 4,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run the real seeded decision-relevance sweep across ``[low, high]`` on the
    current vault, produce a COVERAGE certificate for the parameter's current
    effective value, and store + link it (U-022 v2). Coverage is descriptive: it
    documents where in the range decisions flip and satisfies the audit's coverage
    obligation for an ``active`` decision parameter -- it never changes status. Use
    ``registry promote`` to advance status beyond heuristic."""

    import tempfile

    from learnloop.params import parameter_registry as pr
    from learnloop.params import sensitivity_certificates as sc
    from learnloop.sim.profiles import ProfileError, load_profile

    if ":" in path:
        typer.echo("Only config parameters can be certified via the sweep (module constants are code-fixed).")
        raise typer.Exit(code=1)

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    entry = repository.parameter_registry_entry(path)
    if entry is None:
        typer.echo(f"No registry entry for {path!r}.")
        raise typer.Exit(code=1)
    try:
        student_profile = load_profile(profile)
    except ProfileError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    covered_value = pr._resolve_config_value(path, loaded.config)
    work_dir = Path(tempfile.mkdtemp(prefix="learnloop-certify-"))
    certificate = sc.certify(
        path=path,
        covered_value=covered_value,
        low=low,
        high=high,
        vault_root=root,
        profile=student_profile,
        work_dir=work_dir,
        grid_points=steps,
        days=days,
        items_per_day=items_per_day,
        seed=seed,
    )
    sc.store_certificate(repository, certificate)
    outcome = sc.link_coverage_certificate(repository, certificate)
    resolved = repository.parameter_registry_entry(path)
    payload = {
        "path": path,
        "certificate_id": certificate.id,
        "covered_value": covered_value,
        "plausible_range": certificate.plausible_range,
        "decision_stable": certificate.decision_stable,
        "flip_points": certificate.flip_points,
        "coverage_linked": outcome.linked,
        "link_reason": outcome.reason,
        "status": resolved["status"] if resolved else None,
    }
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(
        f"Certified {path}: coverage_linked={outcome.linked} "
        f"decision_stable={certificate.decision_stable} status={payload['status']}"
    )
    if outcome.reason:
        typer.echo(f"  note: {outcome.reason}")

@registry_app.command("promote")
def registry_promote(
    path: Annotated[str, typer.Argument(help="Config parameter path to promote (sweepable).")],
    low: Annotated[float, typer.Option("--low", help="Low end of the plausible range.")],
    high: Annotated[float, typer.Option("--high", help="High end of the plausible range.")],
    steps: Annotated[int, typer.Option("--steps", min=2, help="Grid points across [low, high].")] = 3,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", min=1, help="Sim days per grid point.")] = 8,
    items_per_day: Annotated[int, typer.Option("--items-per-day", min=1)] = 4,
    seed: Annotated[int, typer.Option("--seed")] = 42,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Consume sim PROMOTION EVIDENCE to advance status ``heuristic ->
    simulation_validated`` (U-022 v2, the normative gate). Runs the real seeded sweep
    across ``[low, high]``; a decision that stays stable across the range promotes,
    while a flip inside the range refuses promotion (the covered value is not certified
    robust). Sim source only for now; ``live_calibrated`` still needs the activated
    real-outcome evidence manifest (§6)."""

    import tempfile

    from learnloop.params import parameter_registry as pr
    from learnloop.params import sensitivity_certificates as sc
    from learnloop.sim.profiles import ProfileError, load_profile

    if ":" in path:
        typer.echo("Only config parameters can be promoted via the sweep (module constants are code-fixed).")
        raise typer.Exit(code=1)

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    entry = repository.parameter_registry_entry(path)
    if entry is None:
        typer.echo(f"No registry entry for {path!r}.")
        raise typer.Exit(code=1)
    try:
        student_profile = load_profile(profile)
    except ProfileError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    covered_value = pr._resolve_config_value(path, loaded.config)
    work_dir = Path(tempfile.mkdtemp(prefix="learnloop-promote-"))
    certificate = sc.certify(
        path=path,
        covered_value=covered_value,
        low=low,
        high=high,
        vault_root=root,
        profile=student_profile,
        work_dir=work_dir,
        grid_points=steps,
        days=days,
        items_per_day=items_per_day,
        seed=seed,
    )
    evidence = sc.promotion_evidence_from_certificate(certificate)
    outcome = sc.promote(repository, evidence)
    resolved = repository.parameter_registry_entry(path)
    payload = {
        "path": path,
        "promotion_evidence_id": evidence.id,
        "covered_value": covered_value,
        "plausible_range": evidence.plausible_range,
        "decision_stable": evidence.decision_stable,
        "flip_points": evidence.flip_points,
        "promoted": outcome.promoted,
        "refusal_reason": outcome.refusal_reason,
        "status": resolved["status"] if resolved else None,
    }
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(f"Promote {path}: promoted={outcome.promoted} status={payload['status']}")
    if outcome.refusal_reason:
        typer.echo(f"  refusal: {outcome.refusal_reason}")

@registry_app.command("release-check")
def registry_release_check(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Strict §9.6 release gate: fails on any audit failure AND on any outstanding
    coverage debt (``active_pending_certificate`` count > 0), with the pending list
    attached. Stricter than the ordinary ``registry audit``, which reports pending
    coverage as a non-blocking warning."""

    from learnloop.params import parameter_registry as pr

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    pr.refresh(loaded, repository)
    report = pr.audit(loaded, repository)
    if json_output:
        typer.echo(_dump(report.as_dict()))
    else:
        typer.echo("Registry release-check: " + ("CLEAN" if report.release_clean else "BLOCKED"))
        for name in report.failures:
            typer.echo(f"  failure {name}: {getattr(report, name)}")
        pending = report.active_pending_certificate
        if pending:
            typer.echo(f"  failure active_pending_certificate ({len(pending)}): {pending}")
    if not report.release_clean:
        raise typer.Exit(code=1)

__all__ = [name for name in globals() if not name.startswith("__")]
