"""`learnloop diagnose`: the Slice 1 M1 offline review of blind grading and diagnosis.

Every command reads the vault and writes only to a run directory's scratch
copy, except two that the spec asks for: the optional spot-check's verdicts on
the stored joint diagnosis go to the vault's ``diagnosis_adjudications``, and
``import-links`` appends pattern-link verdicts to its ``judgment_ledger``.
"""

from __future__ import annotations

import json
import signal
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Iterator

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.receipts import bind_command_repository, bind_command_vault
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

diagnose_app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Slice 1: the M1 offline review (scratch copy only) and the M2 live split's "
        "diagnosis queue, status and reports."
    ),
)


@contextmanager
def _cancellation() -> Iterator[threading.Event]:
    stop = threading.Event()
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda *_: stop.set())
    try:
        yield stop
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _load(vault: Path):
    """Load the vault; validation issues are reported, not fatal.

    The review only reads the vault: an item that fails to load is simply not
    sampled (its attempts are skipped), so one broken file must not block it.
    """

    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    # Model calls not wrapped in an owner of their own (e.g. embed-on-write)
    # are receipted by the command; they go to this vault, not the cwd's.
    bind_command_vault(loaded.root)
    if loaded.issues:
        typer.echo(
            f"warning: the vault has {len(loaded.issues)} validation issue(s); attempts on items "
            "that fail to load are skipped. Run `learnloop doctor` to see them.",
            err=True,
        )
    return loaded


def _echo(payload: object, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True, default=str))
    else:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))


@diagnose_app.command("data-check")
def diagnose_data_check(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Graded wrong answers available for the review (M1 needs about 40 across topics)."""

    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.offline_review.runner import data_check

    loaded = _load(vault)
    repository = Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)
    _echo(data_check(loaded, repository), json_output)


#: CLI experiment options -> the ``ReviewOptions`` fields they set. On a
#: resume only these, when given explicitly, are checked against the run's.
_EXPERIMENT_PARAMETERS: dict[str, tuple[str, ...]] = {
    "sample_size": ("sample_size",),
    "seed": ("seed",),
    "arms": ("arms",),
    "attempt": ("attempt_ids",),
    "since": ("since",),
    "repeat_subset": ("repeat_subset",),
    "planted_per_shape": ("planted_per_shape",),
    "planted_manifest": ("planted_manifest", "generate_planted"),
    "no_planted": ("planted_per_shape", "planted_manifest", "generate_planted"),
    "no_sweep": ("sweep",),
    "sweep_budget": ("sweep_budgets",),
    "no_probes": ("probes",),
    "probe_items": ("probe_items",),
    "no_joint_repeat": ("joint_repeat",),
    "no_judge": ("judge",),
    "full_budget": ("settings.full_history_token_budget",),
    "history_error_limit": ("settings.history_error_limit",),
    "history_success_limit": ("settings.history_success_limit",),
}


def _explicit_options(ctx: typer.Context) -> tuple[str, ...]:
    """The ReviewOptions fields the command line set on purpose (not defaults)."""

    # Compared by name: typer may ship its own click, whose enum is distinct.
    defaults = {"DEFAULT", "DEFAULT_MAP"}
    fields: dict[str, None] = {}
    for parameter, names in _EXPERIMENT_PARAMETERS.items():
        source = ctx.get_parameter_source(parameter)
        if source is not None and getattr(source, "name", str(source)) not in defaults:
            fields.update(dict.fromkeys(names))
    return tuple(fields)


@diagnose_app.command("run")
def diagnose_run(
    ctx: typer.Context,
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; its database is copied, never modified.")],
    run_dir: Annotated[Path | None, typer.Option("--run-dir", help="Run directory (default: <vault>/.learnloop/diagnose-runs/<id>). An existing one resumes.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the plan and cost estimate; no copy, no client, no calls.")] = False,
    sample_size: Annotated[int, typer.Option("--sample-size", min=0)] = 40,
    seed: Annotated[int, typer.Option("--seed")] = 20261012,
    arms: Annotated[str, typer.Option("--arms", help="Comma-separated subset of a,b,c,d,e.")] = "a,b,c,d,e",
    attempt: Annotated[list[str] | None, typer.Option("--attempt", help="Diagnose these attempts instead of a sample (repeatable).")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Only attempts at or after this ISO timestamp.")] = None,
    repeat_subset: Annotated[int, typer.Option("--repeat-subset", min=0, help="Targets repeated under (b) for the noise floor.")] = 10,
    planted_per_shape: Annotated[int, typer.Option("--planted-per-shape", min=0)] = 2,
    planted_manifest: Annotated[Path | None, typer.Option("--planted-manifest", help="Authored planted cases (JSON) instead of generated ones.")] = None,
    no_planted: Annotated[bool, typer.Option("--no-planted")] = False,
    no_sweep: Annotated[bool, typer.Option("--no-sweep", help="Skip the (d) context-length sweep on planted cases.")] = False,
    sweep_budget: Annotated[list[int] | None, typer.Option("--sweep-budget", help="Sweep budgets in tokens (repeatable; default 25000, 50000, 100000).")] = None,
    no_probes: Annotated[bool, typer.Option("--no-probes", help="Skip the E1 grader probes.")] = False,
    probe_items: Annotated[int, typer.Option("--probe-items", min=0)] = 40,
    no_joint_repeat: Annotated[bool, typer.Option("--no-joint-repeat", help="Skip re-running the joint grader (E1 noise floor).")] = False,
    no_judge: Annotated[bool, typer.Option("--no-judge")] = False,
    full_budget: Annotated[int, typer.Option("--full-history-token-budget", min=1000)] = 100_000,
    history_error_limit: Annotated[int, typer.Option("--history-error-limit", min=0)] = 6,
    history_success_limit: Annotated[int, typer.Option("--history-success-limit", min=0)] = 4,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 2500,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 500,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0)] = 0,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Metered routes: every transport retry and JSON repair is one (Codex physical requests are not bounded).")] = 50,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Metered routes only; not enforced on the Codex subscription.")] = 5_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Metered routes only; Codex cost is estimated_only.")] = 5.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Owner USD/million-token bound for metered chat routes with an unknown price.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Blind-grade a stratified sample, diagnose it under arms (a)-(e), judge, probe.

    Everything lands in the run directory's scratch copy; the vault database
    is only read. Run with --dry-run first: it prints the planned calls,
    tokens and cost per route. SIGINT/SIGTERM stops before the next request;
    rerunning with the same --run-dir resumes without paying twice, under the
    run's own options (an explicit different option, vault, model or prompt
    version is refused).
    """

    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.offline_review.runner import (
        ReviewClients,
        ReviewOptions,
        estimate_spend,
        plan_review,
        resolve_review_clients,
        route_profiles,
        run_review,
        unavailable_arms,
    )
    from learnloop.diagnosis.offline_review.spend import ReviewSpend
    from learnloop.diagnosis.split.settings import DiagnosisSettings
    from learnloop.ids import new_ulid

    try:
        loaded = _load(vault)
        manifest = None
        if planted_manifest is not None:
            manifest = json.loads(planted_manifest.read_text(encoding="utf-8"))
        options = ReviewOptions(
            sample_size=sample_size,
            seed=seed,
            arms=tuple(value.strip() for value in arms.split(",") if value.strip()),
            repeat_subset=repeat_subset,
            planted_per_shape=0 if no_planted else planted_per_shape,
            planted_manifest=None if no_planted else manifest,
            generate_planted=not no_planted and manifest is None,
            sweep=not no_sweep,
            sweep_budgets=tuple(sweep_budget) if sweep_budget else (25_000, 50_000, 100_000),
            probes=not no_probes,
            probe_items=probe_items,
            joint_repeat=not no_joint_repeat,
            judge=not no_judge,
            attempt_ids=tuple(attempt or ()),
            since=since,
            settings=DiagnosisSettings(
                full_history_token_budget=full_budget,
                history_error_limit=history_error_limit,
                history_success_limit=history_success_limit,
            ),
        )
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=max_pairs, max_retries=max_retries,
            max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
    except (ValueError, typer.BadParameter) as exc:
        _echo({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if dry_run:
        spend = ReviewSpend(caps, price_per_million=price_per_million, config=loaded.config)
        profiles = route_profiles(loaded)
        for route, profile in profiles.items():
            if profile["enabled"]:
                spend.register_profile(
                    route, provider=profile["provider"], model=profile["model"],
                    subscription=profile["subscription"], max_tokens=profile.get("max_tokens"),
                )
        skip = unavailable_arms(
            embedding_ready=profiles["embedding"]["enabled"],
            workspace_ready=profiles["diagnosis"]["profile_type"] == "codex_sdk",
        )
        plan = plan_review(loaded, Repository.attach(sqlite_path, read_only=True), options, skip_arms=skip)
        estimate = estimate_spend(plan, spend)
        _echo(
            {
                "status": "dry_run",
                "data_check": plan["data_check"],
                "targets": plan["targets"],
                "sample": len(plan["sample"]),
                "missing_attempt_ids": plan["missing_attempt_ids"],
                "planted_cases": plan["planted_cases"],
                "arms": plan["arms"],
                "skipped_arms": plan["skipped_arms"],
                "calls": plan["calls"],
                "estimated_tokens": plan["estimated_tokens"],
                "routes": profiles,
                "estimate": estimate,
                "note": "Codex routes run on the ChatGPT subscription: their token/dollar caps are not enforced and their cost is estimated_only.",
            },
            json_output,
        )
        return
    clients: ReviewClients = resolve_review_clients(loaded)
    directory = run_dir or (loaded.root / ".learnloop" / "diagnose-runs" / new_ulid())

    def progress(message: str) -> None:
        if not json_output:
            typer.echo(message, err=True)

    with _cancellation() as stop:
        result = run_review(
            loaded,
            source_sqlite=sqlite_path,
            run_dir=directory,
            options=options,
            clients=clients,
            caps=caps,
            price_per_million=price_per_million,
            cancelled=stop.is_set,
            progress=progress,
            explicit_options=_explicit_options(ctx),
        )
    _echo(result, json_output)
    if result["status"] == "cancelled":
        raise typer.Exit(code=130)
    if result["status"] != "complete":
        raise typer.Exit(code=1)


@diagnose_app.command("report")
def diagnose_report(
    run: Annotated[Path, typer.Option("--run", help="Run directory from `diagnose run`.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (enables criterion-level grader agreement).")] = None,
    out: Annotated[Path | None, typer.Option("--out", help="Markdown path (default <run>/report.md); e.g. docs/reviews/slice-1-m1-report.md.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Write the M1 report (aggregates only) plus report.json and the verdict export."""

    from learnloop.diagnosis.offline_review.report import offline_review_report, render_markdown
    from learnloop.diagnosis.offline_review.spot_check import export_judgments

    loaded = _load(vault) if vault is not None else None
    report = offline_review_report(run, vault=loaded)
    markdown_path = out or (run / "report.md")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    (run / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (run / "review_judgments.json").write_text(json.dumps(export_judgments(run), indent=2, sort_keys=True, default=str), encoding="utf-8")
    if json_output:
        _echo(report, True)
    else:
        typer.echo(f"Wrote {markdown_path}, {run / 'report.json'} and {run / 'review_judgments.json'}.")


_DIAGNOSIS_KEYS = {"r": "right", "p": "partly", "w": "wrong", "n": "not_sure"}
_LINK_KEYS = {"s": "same", "d": "different", "n": "not_sure"}


@diagnose_app.command("review")
def diagnose_review(
    run: Annotated[Path, typer.Option("--run", help="Run directory from `diagnose run`.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (arm (a) verdicts are recorded there).")],
    new_session: Annotated[bool, typer.Option("--new-session", help="Start over instead of resuming.")] = False,
    seed: Annotated[int, typer.Option("--seed")] = 20261012,
    max_items: Annotated[int, typer.Option("--max-items", min=1, max=20)] = 10,
) -> None:
    """The optional owner spot-check: ~10 items, under 15 minutes, every screen skippable.

    Labels are hidden and shuffled. Type the letter for each tap; Enter skips;
    q saves your place and quits (rerun to resume).
    """

    from learnloop.diagnosis.offline_review.spot_check import (
        advance_session,
        record_diagnosis_screen,
        record_grade_screen,
        record_links_screen,
        render_screen,
        start_or_resume_session,
    )

    loaded = _load(vault)
    # Arm (a) verdicts are real vault writes: open the vault the way every
    # application entry point does (migrated under the vault lock).
    vault_repository = open_vault_repository(loaded.root, VaultPaths(loaded.root, loaded.config).sqlite_path)
    session_id, plan, position = start_or_resume_session(run, loaded, seed=seed, new=new_session, max_items=max_items)
    if not plan:
        typer.echo("Nothing to review in this run.")
        return

    def ask(text: str) -> str:
        return str(typer.prompt(text, default="", show_default=False)).strip().lower()

    for index in range(position, len(plan)):
        screen = plan[index]
        typer.echo(f"\n=== Screen {index + 1} of {len(plan)} ===\n")
        typer.echo(render_screen(screen))
        typer.echo("")
        if screen["kind"] == "diagnoses":
            ratings: dict[str, str] = {}
            repairs: dict[str, str] = {}
            for option in screen["options"]:
                key = ask(f"{option['label']}: [r]ight [p]artly [w]rong [n]ot sure, Enter skips, q quits")
                if key == "q":
                    advance_session(run, session_id, index)
                    typer.echo("Saved. Rerun to resume.")
                    return
                if key in _DIAGNOSIS_KEYS:
                    ratings[option["label"]] = _DIAGNOSIS_KEYS[key]
                    if key == "w":
                        repair = ask("Optional: what was actually wrong, or the repair you needed (Enter skips)")
                        if repair:
                            repairs[option["label"]] = repair
            letters = {option["label"].split()[-1].lower(): option["label"] for option in screen["options"]}
            best_key = ask(f"Best explanation? letter ({'/'.join(sorted(letters))}), 'none', Enter skips")
            best = "none" if best_key == "none" else letters.get(best_key)
            record_diagnosis_screen(run, session_id=session_id, screen=screen, ratings=ratings, best=best, vault_repository=vault_repository, wrong_repairs=repairs)
        elif screen["kind"] == "links":
            verdicts = []
            for number, _link in enumerate(screen["links"], start=1):
                key = ask(f"Earlier answer {number}: [s]ame mistake [d]ifferent [n]ot sure, Enter skips, q quits")
                if key == "q":
                    advance_session(run, session_id, index)
                    typer.echo("Saved. Rerun to resume.")
                    return
                verdicts.append(_LINK_KEYS.get(key))
            record_links_screen(run, session_id=session_id, screen=screen, verdicts=verdicts)
        elif screen["kind"] == "grade":
            key = ask("Which grade is right? 1, 2, [n]ot sure, Enter skips, q quits")
            if key == "q":
                advance_session(run, session_id, index)
                typer.echo("Saved. Rerun to resume.")
                return
            choice = {"1": "Grade 1", "2": "Grade 2", "n": "not_sure"}.get(key)
            record_grade_screen(run, session_id=session_id, screen=screen, choice=choice)
        advance_session(run, session_id, index + 1)
    advance_session(run, session_id, len(plan), finished=True)
    typer.echo("Spot-check complete. Run `learnloop diagnose report` to include it.")


@diagnose_app.command("import-links")
def diagnose_import_links(
    run: Annotated[Path, typer.Option("--run", help="Run directory from `diagnose run`.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root whose judgment_ledger receives the rows.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Count what would be imported; write nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Append the run's pattern-link verdicts (real attempts only) to judgment_ledger as same_cause rows."""

    from learnloop.diagnosis.offline_review.links import import_pattern_links

    from learnloop.db.repositories import Repository

    loaded = _load(vault)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    # A dry run only reads; a real import opens the vault the way every
    # application entry point does (migrated under the vault lock).
    repository = (
        Repository.attach(sqlite_path, read_only=True)
        if dry_run
        else open_vault_repository(loaded.root, sqlite_path)
    )
    _echo(import_pattern_links(run, repository, dry_run=dry_run), json_output)


__all__ = ["diagnose_app"]


# -- Slice 1 M2: the live split's queue, status and reports -------------------------


def _live_repository(vault: Path):
    """The vault and its migration-applied repository (M2 commands write)."""

    loaded = _load(vault)
    repository = open_vault_repository(loaded.root, VaultPaths(loaded.root, loaded.config).sqlite_path)
    bind_command_repository(repository)
    return loaded, repository


def _drain_caps(max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float) -> SpendCaps:
    return SpendCaps(
        max_candidates=max(max_calls, 1),
        max_pairs=0,
        max_retries=max_retries,
        max_calls=max_calls,
        max_total_tokens=max_tokens,
        max_estimated_usd=max_cost_usd,
    )


def _plan_repository(vault: Path, dry_run: bool):
    """A dry run only reads; a real run opens the vault for writing."""

    if not dry_run:
        return _live_repository(vault)
    from learnloop.db.repositories import Repository

    loaded = _load(vault)
    return loaded, Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)


def _outcome_rows(outcomes) -> list[dict]:
    return [
        {
            "job_id": outcome.job_id,
            "attempt_id": outcome.attempt_id,
            "kind": outcome.kind,
            "state": outcome.state,
            "diagnosis_id": outcome.diagnosis_id,
            "status": outcome.status,
            "error": outcome.error,
        }
        for outcome in outcomes
    ]


_MAX_CALLS_HELP = (
    "Calls this command may admit: one per logical diagnosis call, one per retrieval embedding request and, "
    "at mvp-0.12, one per same-cause judge call, hypothesis embedding request and escalated-repair request "
    "(metered retries also count as calls)."
)
_MAX_RETRIES_HELP = "Metered routes: physical retries and JSON repairs this command may admit."
_MAX_TOKENS_HELP = (
    "Metered routes (retrieval embeddings, a metered diagnoser): total tokens this command may admit "
    "(subscription routes are not token-capped)."
)
_MAX_COST_HELP = "Metered routes (retrieval embeddings, a metered diagnoser): estimated USD this command may admit."
_PRICE_HELP = "USD per million tokens for a metered route whose price is unknown (an unknown price fails closed)."


@diagnose_app.command("drain")
def diagnose_drain(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    attempt: Annotated[str | None, typer.Option("--attempt", help="Only this attempt's diagnosis (still in attempt order).")] = None,
    kind: Annotated[list[str] | None, typer.Option("--kind", help="diagnose and/or embed; repeatable. Default: both.")] = None,
    max_jobs: Annotated[int, typer.Option("--max-jobs", min=1)] = 1_000,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan and estimate only: no client, no call, no write.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0, help=_MAX_CALLS_HELP)] = 500,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help=_MAX_RETRIES_HELP)] = 50,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help=_MAX_TOKENS_HELP)] = 5_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help=_MAX_COST_HELP)] = 5.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help=_PRICE_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run queued post-attempt jobs (diagnoses in attempt order, then embeddings).

    The CLI has no daemon: this is how queued diagnoses run outside the app.
    Uses ``ai.routing.diagnosis`` (unset: the grading route) and, for
    embeddings, ``ai.routing.embedding`` when ``embedding.enabled``. Run
    ``--dry-run`` first: it plans the jobs and estimates their spend against
    the caps. Every diagnosis request, and every retrieval embedding request
    a diagnosis makes, is admitted against the caps before it is sent;
    retrieval only while the queued diagnoses still fit (otherwise that
    diagnosis uses the exact set). Embed jobs keep their own per-job caps
    (the plan's ``embed`` block). Ctrl-C stops before the next job (an
    interrupted one is released unspent).
    """

    from learnloop.diagnosis.split.jobs import (
        DIAGNOSE_KIND,
        EMBED_KIND,
        command_spend,
        drain,
        plan_diagnosis_jobs,
        plan_embed_jobs,
    )

    kinds = tuple(kind or (DIAGNOSE_KIND, EMBED_KIND))
    unknown = sorted(set(kinds) - {DIAGNOSE_KIND, EMBED_KIND})
    if unknown:
        raise typer.BadParameter(f"unknown job kind(s): {', '.join(unknown)}")
    caps = _drain_caps(max_calls, max_retries, max_tokens, max_cost_usd)
    loaded, repository = _plan_repository(vault, dry_run)
    with _cancellation() as stop:
        spend = command_spend(loaded, caps, price_per_million=price_per_million, cancelled=stop.is_set)
        plan = {
            "caps": caps.as_dict(),
            "diagnose": plan_diagnosis_jobs(loaded, repository, spend=spend, attempt_id=attempt, max_jobs=max_jobs)
            if DIAGNOSE_KIND in kinds
            else None,
            "embed": plan_embed_jobs(loaded, repository, attempt_id=attempt) if EMBED_KIND in kinds else None,
        }
        admissible = plan["diagnose"] is None or bool(plan["diagnose"]["admissible"])
        if dry_run:
            _echo({"status": "dry_run", **plan}, json_output)
            if not admissible:
                raise typer.Exit(code=1)
            return
        if not admissible:
            _echo({"status": "over_budget", **plan}, json_output)
            raise typer.Exit(code=1)
        outcomes = drain(
            loaded, repository, owner="cli", kinds=kinds, attempt_id=attempt, max_jobs=max_jobs,
            spend=spend, cancelled=stop.is_set,
        )
        cancelled = stop.is_set()
    payload = {
        "status": "cancelled" if cancelled else "done",
        "jobs": _outcome_rows(outcomes),
        "remaining": repository.post_attempt_job_counts(),
        "spend": spend.summary(),
    }
    _echo(payload, json_output)


@diagnose_app.command("retry")
def diagnose_retry(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    attempt: Annotated[str, typer.Option("--attempt", help="Attempt whose diagnosis runs again.")],
    run_now: Annotated[bool, typer.Option("--run/--queue-only", help="Run it now (default) or only queue it.")] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan and estimate only: nothing is queued or called.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0, help=_MAX_CALLS_HELP)] = 5,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help=_MAX_RETRIES_HELP)] = 4,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help=_MAX_TOKENS_HELP)] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help=_MAX_COST_HELP)] = 2.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help=_PRICE_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Retry a failed or skipped diagnosis, or re-diagnose (appends, supersedes).

    ``--dry-run`` estimates the one diagnosis call (and its retrieval
    embedding requests) against the caps and changes nothing.
    """

    from learnloop.diagnosis.split.jobs import (
        DIAGNOSE_KIND,
        command_spend,
        diagnosis_status,
        drain,
        enqueue_diagnosis,
        plan_diagnosis_jobs,
        plan_unqueued_diagnosis,
    )
    from learnloop.diagnosis.split.live import needs_diagnosis

    caps = _drain_caps(max_calls, max_retries, max_tokens, max_cost_usd)
    loaded, repository = _plan_repository(vault, dry_run)
    jobs = repository.post_attempt_jobs(attempt_id=attempt, kind=DIAGNOSE_KIND)
    retried = next((job for job in reversed(jobs) if job["state"] in ("failed", "skipped")), None)
    with _cancellation() as stop:
        spend = command_spend(loaded, caps, price_per_million=price_per_million, cancelled=stop.is_set)
        if dry_run:
            record = repository.latest_blind_grade_record(attempt)
            applies = retried is not None or (record is not None and needs_diagnosis(record.get("record") or {}))
            plan = plan_diagnosis_jobs(loaded, repository, spend=spend, attempt_id=attempt)
            if applies and not any(row["attempt_id"] == attempt for row in plan["jobs"]):
                # Not queued yet: estimate the call the retry would queue.
                plan = plan_unqueued_diagnosis(loaded, repository, attempt_id=attempt, spend=spend)
            _echo({"status": "dry_run", "attempt_id": attempt, "applies": applies, "caps": caps.as_dict(), "diagnose": plan}, json_output)
            if not plan["admissible"]:
                raise typer.Exit(code=1)
            return
        if run_now:
            # Admission first: an over-budget retry changes nothing.
            plan = plan_unqueued_diagnosis(loaded, repository, attempt_id=attempt, spend=spend)
            if not plan["admissible"]:
                _echo({"attempt_id": attempt, "queued": False, "status": "over_budget", "diagnose": plan}, json_output)
                raise typer.Exit(code=1)
        if retried is not None:
            repository.requeue_post_attempt_job(str(retried["id"]))
            queued = str(retried["id"])
        else:
            queued = enqueue_diagnosis(loaded, repository, attempt_id=attempt, rediagnose=bool(jobs))
        if queued is None:
            _echo({"attempt_id": attempt, "queued": False, "reason": "no diagnosis applies (not blind-graded or nothing failed)"}, json_output)
            raise typer.Exit(code=1)
        outcomes = []
        if run_now:
            outcomes = drain(
                loaded, repository, owner="cli", kinds=(DIAGNOSE_KIND,), attempt_id=attempt,
                spend=spend, cancelled=stop.is_set,
            )
    _echo(
        {
            "attempt_id": attempt,
            "queued": queued,
            "ran": [outcome.state for outcome in outcomes],
            "status": diagnosis_status(repository, attempt),
            "spend": spend.summary(),
        },
        json_output,
    )


@diagnose_app.command("status")
def diagnose_status(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    attempt: Annotated[str | None, typer.Option("--attempt", help="One attempt (default: queue counts).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """An attempt's diagnosis status, or the queue's job counts."""

    from learnloop.diagnosis.split.jobs import diagnosis_status

    _loaded, repository = _live_repository(vault)
    if attempt is None:
        _echo({"jobs": repository.post_attempt_job_counts()}, json_output)
        return
    _echo({"attempt_id": attempt, **diagnosis_status(repository, attempt)}, json_output)


@diagnose_app.command("m2-report")
def diagnose_m2_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read only).")],
    out: Annotated[Path | None, typer.Option("--out", help="Markdown path, e.g. docs/reviews/slice-1-m2-report.md.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """End-of-M2 report: E5 (shadow recurrence), E7 (operations), card signals.

    Reads receipts and ledgers only; no model or embedding call.
    """

    from learnloop.diagnosis.split.reports import m2_report, render_markdown

    loaded, repository = _live_repository(vault)
    report = m2_report(loaded, repository)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report), encoding="utf-8")
    if json_output or out is None:
        _echo(report, json_output)
    else:
        typer.echo(f"Wrote {out}.")


@diagnose_app.command("pfc-report")
def diagnose_pfc_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for trials.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan and estimate only: no client, no call, no write.")] = False,
    max_items: Annotated[int, typer.Option("--max-items", min=0)] = 40,
    max_real: Annotated[int, typer.Option("--max-real", min=0)] = 40,
    seed: Annotated[int, typer.Option("--seed")] = 0,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 400,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 4,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 2_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 5.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="USD per million tokens for an unknown metered price.")] = None,
    no_ledger: Annotated[bool, typer.Option("--no-ledger", help="Do not append verdicts to judgment_ledger.")] = False,
    out: Annotated[Path | None, typer.Option("--out", help="Markdown path for the report.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """PF-c before/after (E1-style): mvp-2.0 vs mvp-2.1 blind grading prompt.

    Measures valid-alternative false rejection and anchor accuracy on
    owner-adjudicated answers.

    Routes: ``ai.routing.diagnosis_generator`` writes the alternatives,
    ``ai.routing.grading`` grades them. Caps are checked before any request.
    """

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.diagnosis.offline_review.runner import route_profiles
    from learnloop.diagnosis.offline_review.spend import ReviewSpend
    from learnloop.diagnosis.split.pfc_report import (
        estimate_pfc,
        plan_pfc,
        render_pfc_markdown,
        run_pfc,
    )

    caps = SpendCaps(
        max_candidates=max(max_items, 1) * 2,
        max_pairs=0,
        max_retries=max_retries,
        max_calls=max_calls,
        max_total_tokens=max_tokens,
        max_estimated_usd=max_cost_usd,
    )
    loaded = _load(vault)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    from learnloop.db.repositories import Repository

    repository = Repository.attach(sqlite_path, read_only=dry_run) if dry_run else open_vault_repository(loaded.root, sqlite_path)
    plan = plan_pfc(loaded, repository, max_items=max_items, max_real=max_real, seed=seed)
    spend = ReviewSpend(caps, price_per_million=price_per_million, config=loaded.config)
    profiles = route_profiles(loaded)
    for route in ("diagnosis_generator", "grading"):
        profile = profiles[route]
        spend.register_profile(
            route,
            provider=profile["provider"],
            model=profile["model"],
            subscription=bool(profile["subscription"]),
            max_tokens=profile["max_tokens"],
        )
    estimate = estimate_pfc(loaded, repository, plan, spend)
    from learnloop.ai.spend import SpendEstimate, SpendLimitExceeded

    try:
        spend.check(
            SpendEstimate(
                candidates=estimate["items"],
                calls=sum(estimate["calls"].values()),
                total_tokens=estimate["metered_tokens"],
                estimated_usd=estimate["estimated_usd"],
            )
        )
        admissible, reason = True, None
    except SpendLimitExceeded as exc:
        admissible, reason = False, str(exc)
    if dry_run:
        _echo({"status": "dry_run", "admissible": admissible, "reason": reason, "estimate": estimate, "caps": caps.as_dict()}, json_output)
        if not admissible:
            raise typer.Exit(code=1)
        return
    if not admissible:
        _echo({"status": "over_budget", "reason": reason, "estimate": estimate}, json_output)
        raise typer.Exit(code=1)
    generator = ready_client_for_task(loaded.root, loaded.config, "diagnosis_generator")
    grading = ready_client_for_task(loaded.root, loaded.config, "grading")
    if not generator.ready or not grading.ready:
        _echo({"status": "unavailable", "generator": generator.runtime.message, "grading": grading.runtime.message}, json_output)
        raise typer.Exit(code=1)
    with _cancellation() as stop:
        report = run_pfc(
            loaded,
            repository,
            plan=plan,
            generator_client=generator.client,
            grading_client=grading.client,
            caps=caps,
            price_per_million=price_per_million,
            cancelled=stop.is_set,
            record_judgments=not no_ledger,
        )
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_pfc_markdown(report), encoding="utf-8")
    _echo(report, json_output)
