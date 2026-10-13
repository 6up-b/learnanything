"""`learnloop sources`: Slice 2 T6 source retrieval from the command line.

``report`` reads the tutor questions' receipts back: each retrieval step's p50
and p90 wall time and how often it went over the soft deadline (the owner
logs the tutor's retrieval time rather than cancelling it, 2026-10-12), plus
the LLM answers cut off by their output budget. ``search`` is the library search the reader runs (keyword while typing; with
``--deep`` also meaning and, for a conceptual question, the LLM rewrite: paid
calls under one budget, ``--max-calls`` / ``--max-tokens`` / ``--max-cost-usd``,
planned without any call by ``--dry-run``). ``suggest-lo`` shows a span's provenance-linked learning
objects or, when it has none, the labelled nearest-LO suggestions. Neither
writes anything except receipts, cached query vectors and checkpoints of the
calls a deep search makes.

Canonical sources (spec_source_practice_and_probes_v1) adds owner-run batch
work over textbook exercises (``exercises harvest``, ``exercises verify``), the
typed tools for external agents (``tools``, ``tool``) and the intervention
report (``outcomes``). Every paid command has ``--dry-run`` (no client is
built, nothing is sent or written) and a money cap.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from learnloop.cli.runtime import _repository, _root
from learnloop.vault.loader import load_vault

sources_app = typer.Typer(no_args_is_help=True, help="Slice 2 T6 source retrieval: search and span -> LO suggestions.")
exercises_app = typer.Typer(no_args_is_help=True,
                            help="Textbook exercises as practice: harvest thin facets, verify answer keys.")
sources_app.add_typer(exercises_app, name="exercises")


def _open(vault: Path, *, migrate: bool = True):
    from learnloop.practice_index.paid import planning_repository
    from learnloop.vault.paths import VaultPaths

    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    try:
        # A dry run attaches read-only and never migrates.
        return loaded, planning_repository(sqlite_path, dry_run=not migrate)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@sources_app.command("search")
def sources_search(
    query: Annotated[str, typer.Argument(help="What to find in the source library.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for experiments.")],
    deep: Annotated[bool, typer.Option("--deep", help="Also search by meaning (stored source-block vectors; one cached, capped query embedding) and rewrite a conceptual question (route source_query_rewrite). Paid: dry-run first.")] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=200)] = 20,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the planned paid calls and their estimated cost; call and write nothing.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0, help="Cap on the deep search's paid requests (rewrite, its retry, query embedding).")] = 3,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Cap on the deep search's estimated tokens (a rewrite reserves its full output budget, a truncation retry twice that).")] = 120_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0.0, help="Cap on the deep search's estimated metered cost (USD).")] = 0.25,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search every reader-enabled source, as the reader's library search does."""

    from learnloop.ai.spend import SpendBudget
    from learnloop.source_retrieval.library import deep_search_caps, plan_library_search, search_library

    loaded, repository = _open(vault, migrate=not dry_run)
    caps = deep_search_caps(max_calls=max_calls, max_tokens=max_tokens, max_cost_usd=max_cost_usd)
    if dry_run:
        plan = plan_library_search(loaded, repository, query=query, deep=deep, caps=caps)
        if json_output:
            typer.echo(json.dumps(plan, sort_keys=True, default=str))
            return
        typer.echo(f"dry run: {plan['status']}; {plan['calls']} paid call(s) at most; "
                   f"estimated ${plan['estimated_usd']}" if plan.get("estimated_usd") is not None
                   else f"dry run: {plan['status']}; {plan['calls']} paid call(s) at most; cost unknown")
        for step in ("rewrite", "query_embedding"):
            if step in plan:
                entry = plan[step]
                typer.echo(f"  {step}: {entry.get('status')} ({entry.get('calls', 0)} call(s))"
                           + (f": {entry['reason']}" if entry.get("reason") else ""))
        meaning = plan.get("meaning_search") or {}
        if meaning:
            typer.echo(f"  meaning search: {meaning.get('status')}"
                       + (f" ({meaning['reason']})" if meaning.get("reason") else ""))
        return
    report = search_library(loaded, repository, query=query, limit=limit, deep=deep,
                            budget=SpendBudget(caps) if deep else None)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True, default=str))
        return
    typer.echo(f"{len(report['hits'])} hits across {report['searched_sources']} sources; "
               f"basis: {report.get('basis', 'substring')}")
    for note in (report.get("retrieval") or {}).get("notes", []):
        typer.echo(f"  note: {note}")
    for rank, hit in enumerate(report["hits"], start=1):
        where = " · ".join(str(part) for part in (hit.get("section"), f"p.{hit['page']}" if hit.get("page") is not None else None) if part)
        typer.echo(f"{rank:>3}. {hit['source_title']}{(' · ' + where) if where else ''}  "
                   f"[{hit['extraction_id']}/{hit['span_id']}] {','.join(hit.get('matched_by', []))}")
        typer.echo(f"     {hit['snippet']}")


@sources_app.command("suggest-lo")
def sources_suggest_lo(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    extraction_id: Annotated[str, typer.Option("--extraction", help="Extraction id of the span.")],
    span_id: Annotated[str, typer.Option("--span", help="Span id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Provenance-linked LOs for a span, else labelled nearest-LO suggestions (no calls)."""

    from learnloop.source_retrieval.suggest import suggest_learning_objects

    loaded, repository = _open(vault)
    report = suggest_learning_objects(loaded, repository, extraction_id=extraction_id, span_id=span_id)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
        return
    typer.echo(f"status: {report['status']}")
    for lo_id in report["provenance"]:
        typer.echo(f"  provenance: {lo_id}")
    for entry in report["suggestions"]:
        typer.echo(f"  suggestion (not a provenance link): {entry['learning_object_id']} "
                   f"{entry['title']} [{', '.join(entry['basis'])}]")


@sources_app.command("report")
def sources_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    since: Annotated[str | None, typer.Option("--since", help="Only questions asked at or after this ISO time.")] = None,
    spend_days: Annotated[int, typer.Option("--spend-days", min=0, max=366,
                                            help="Days of the source service's actual spend to show (0: none).")] = 7,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Tutor-span retrieval timing per step (p50/p90, over the soft deadline) and truncated answers,
    and the source service's actual spend per day (receipt cost, reserved vs settled, largest operations)."""

    from learnloop.source_retrieval.service_spend import spend_report
    from learnloop.source_retrieval.timing import tutor_timing_report

    loaded, repository = _open(vault, migrate=False)
    config = loaded.config.source_retrieval
    report = tutor_timing_report(repository, soft_deadline_seconds=config.retrieval_timeout_seconds,
                                 cancels_at_deadline=config.tutor_deadline_cancels, since=since)
    spend = spend_report(loaded, repository, days=spend_days) if spend_days else None
    if spend is not None:
        report["service_spend"] = spend
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
        return
    deadline = report["soft_deadline_seconds"]
    typer.echo(f"{report['questions']} tutor question(s) with timed retrieval; soft deadline {deadline:g} s "
               f"({'cancels' if report['cancels_at_deadline'] else 'logged, never cancelled'})")
    typer.echo(f"{'step':<16}{'n':>5}{'p50 ms':>10}{'p90 ms':>10}{'max ms':>10}{'> deadline':>12}")
    for step, entry in report["steps"].items():
        def cell(value):
            return "-" if value is None else f"{value:.0f}"
        typer.echo(f"{step:<16}{entry['n']:>5}{cell(entry['p50_ms']):>10}{cell(entry['p90_ms']):>10}"
                   f"{cell(entry['max_ms']):>10}{entry['over_soft_deadline']:>12}")
    for step, count in report["over_soft_deadline"].items():
        typer.echo(f"  note: {step} exceeded the {deadline:g} s soft deadline on {count} question(s)")
    if report["basis"]:
        typer.echo("basis: " + ", ".join(f"{name} {count}" for name, count in report["basis"].items()))
    if report["pool"]:
        typer.echo("pool: " + ", ".join(f"{name} {count}" for name, count in report["pool"].items()))
    truncated = report["truncated_answers"]
    if truncated:
        typer.echo("truncated LLM answers (each retried once at double the budget):")
        for entry in truncated:
            typer.echo(f"  {entry['purpose']} {entry['model'] or '?'}: {entry['truncated']}")
    else:
        typer.echo("truncated LLM answers: none")
    if spend is not None:
        _echo_spend(spend)


def _echo_spend(spend: dict[str, Any]) -> None:
    guard = spend["daily_guard"]
    caps = spend["operation_caps"]

    def cap(value: Any) -> str:
        return "none" if value is None else f"${float(value):.2f}"

    typer.echo(f"source service spend (metered, from receipts; subscription is estimated only): daily guard "
               f"${guard['counted_usd']:.4f} of ${guard['cap_usd']:.2f} today; per-import cap "
               f"{cap(caps['import_max_cost_usd'])}, per-comparison cap {cap(caps['compare_max_cost_usd'])}")
    typer.echo(f"{'day':<12}{'requests':>9}{'actual $':>11}{'unpriced':>9}{'reserved $':>12}{'settled $':>11}"
               f"{'est. only':>11}")
    for day in spend["days"]:
        receipts, rows = day["receipts"], day["reservations"]
        reserved = sum(entry["reserved_usd"] for entry in rows.values())
        settled = rows["settled"]["charged_usd"] + rows["legacy"]["charged_usd"]
        typer.echo(f"{day['day']:<12}{receipts['metered_requests']:>9}{receipts['metered_usd']:>11.4f}"
                   f"{receipts['unpriced']:>9}{reserved:>12.4f}{settled:>11.4f}"
                   f"{receipts['estimated_only']['requests']:>11}")
    if spend["largest_operations"]:
        typer.echo("largest operations:")
        for op in spend["largest_operations"]:
            typer.echo(f"  ${op['usd']:.4f} {op['owner_kind']} {op['owner_id']} ({op['requests']} request(s), "
                       f"from {op['first_started_at']})")


def _emit(report: dict[str, Any], json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, default=str) if json_output
               else json.dumps(report, indent=2, sort_keys=True, default=str))


def _exit_for(report: dict[str, Any], ok: set[str]) -> None:
    if report.get("status") not in ok:
        raise typer.Exit(code=1)


@exercises_app.command("harvest")
def exercises_harvest(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    learning_object: Annotated[list[str] | None, typer.Option("--lo", help="Only facets of these LOs.")] = None,
    facet: Annotated[list[str] | None, typer.Option("--facet", help="Only these facets.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: no client, nothing written.")] = False,
    max_cost_usd: Annotated[float | None, typer.Option("--max-cost-usd", min=0.0,
                                                       help="Stop once metered spend reaches this.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Import judged textbook exercises for thin facets, each key checked before writing."""
    from learnloop.instructional.harvest import harvest

    root = _root(vault)
    try:
        report = harvest(load_vault(root), _repository(root), dry_run=dry_run, max_cost_usd=max_cost_usd,
                         learning_object_ids=tuple(learning_object or ()), facet_ids=tuple(facet or ()),
                         on_progress=None if json_output else typer.echo)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete", "over_budget"})


@exercises_app.command("verify")
def exercises_verify(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    item: Annotated[list[str] | None, typer.Option("--item", help="Only these practice items.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: no client, nothing written.")] = False,
    max_cost_usd: Annotated[float | None, typer.Option("--max-cost-usd", min=0.0,
                                                       help="Stop once metered spend reaches this.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Check imported exercises' answer keys whose current content is not verified."""
    from learnloop.instructional.harvest import verify

    root = _root(vault)
    try:
        report = verify(load_vault(root), _repository(root), dry_run=dry_run, max_cost_usd=max_cost_usd,
                        item_ids=tuple(item or ()))
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete", "over_budget"})


@sources_app.command("outcomes")
def sources_outcomes(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """What retrieval showed or served, and what followed (associations, not causes; no model call)."""
    from learnloop.instructional.interventions import outcomes_report

    root = _root(vault)
    report = outcomes_report(load_vault(root), _repository(root))
    if json_output:
        _emit(report, True)
        return
    typer.echo(report["label"])
    typer.echo(f"interventions: {report['interventions']} (recording {report['recording']})")
    overall = report["overall"]
    typer.echo(f"R_next: {overall['R_next']['successes']}/{overall['R_next']['n']} "
               f"interval {overall['R_next']['interval_95']}")
    typer.echo(f"R_cold: {overall['R_cold']['successes']}/{overall['R_cold']['n']} "
               f"interval {overall['R_cold']['interval_95']}; states {overall['R_cold']['states']}")
    for name, groups in report["by"].items():
        for value, rates in groups.items():
            typer.echo(f"  {name}={value}: n={rates['n']} R_next={rates['R_next']['successes']}/"
                       f"{rates['R_next']['n']} R_cold={rates['R_cold']['successes']}/{rates['R_cold']['n']}")
    typer.echo(f"key labels: {report['key_labels']}")
    typer.echo(f"certification gate: {report['certification_gate']['unverified_attempts']} unverified attempt(s)")
    typer.echo(f"exposure exclusions: {report['exposure_exclusions']}")
    typer.echo(f"valuation: {report['valuation']['by_group_and_regime']} ({report['valuation']['scale']})")


@sources_app.command("tools")
def sources_tools(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Every source tool's declaration (name, description, JSON schema, model call)."""
    from learnloop.instructional.tools import tool_schemas

    _emit({"version": 1, "tools": tool_schemas()}, json_output)


def _agent_injections(vault: Any, repository: Any) -> dict[str, Any]:
    from learnloop.daily_plan.estimates import Estimator, load_duration_evidence
    from learnloop.instructional.wiring import find_practice_injections

    evidence = load_duration_evidence(repository, latency_cap_minutes=vault.config.plan.latency_cap_minutes)
    estimator = Estimator(evidence, read_words_per_minute=vault.config.plan.read_words_per_minute).estimate
    return find_practice_injections(vault, estimator=estimator)


@sources_app.command("tool")
def sources_tool(
    name: Annotated[str, typer.Argument(help="find_practice, find_sources, compare_sources, find_facets or "
                                             "practice_availability.")],
    args: Annotated[str, typer.Option("--args", help="The tool's arguments as a JSON object.")] = "{}",
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and show the policy; run nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run one tool as an external agent (caller kind ``agent``, policy ``reading``)."""
    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.tools import ToolArgumentsInvalid, drop_unknown_ids, run_tool, validate_arguments
    from learnloop.practice_index.retrieval import IntentUnavailable
    from learnloop.source_retrieval.policy import PolicyRefused, derive_policy

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(root)
    try:
        arguments = json.loads(args)
        if not isinstance(arguments, dict):
            raise ValueError("--args must be a JSON object")
    except ValueError as exc:
        _emit({"version": 1, "status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1)
    caller = caller_for(repository, "agent", "cli")
    policy, derived_from = derive_policy(caller)
    try:
        if dry_run:
            parsed, dropped = drop_unknown_ids(loaded, repository, validate_arguments(name, arguments))
            report = {"version": 1, "status": "dry_run", "tool": name, "policy": policy,
                      "policy_derived_from": derived_from, "arguments": parsed.model_dump(), "dropped": dropped,
                      "note": "Nothing was run or recorded."}
        else:
            report = {"version": 1, "status": "ran", **run_tool(loaded, repository, name, arguments, caller=caller,
                                                                injections=_agent_injections(loaded, repository))}
    except ToolArgumentsInvalid as exc:
        report = {"version": 1, "status": "invalid", "code": exc.code, "reason": str(exc), "details": exc.details}
    except (PolicyRefused, IntentUnavailable) as exc:
        report = {"version": 1, "status": "refused", "code": exc.code, "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "ran"})


@sources_app.command("build-preview")
def sources_build_preview(
    source_id: Annotated[str, typer.Argument(help="The book's source id (src_...).")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for experiments.")],
    whole_book: Annotated[bool, typer.Option("--whole-book", help="Preview 'Build questions for the whole book'.")] = False,
    approved: Annotated[bool, typer.Option("--approved", help="Preview as if the learner pressed 'Build them'.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Dry run of an automatic question build for one book (UX Phase 1): what it
    would cover, the route, tokens, money and whether it would ask first or
    stop. Zero model calls; reads only (the database opens read-only)."""

    from learnloop.content.pipeline.add_source import preview_auto_build

    loaded, repository = _open(vault, migrate=False)
    report = preview_auto_build(loaded.root, repository, source_id, whole_book=whole_book, approved=approved)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True, default=str))
        return
    typer.echo(f"dry run: {report['status']}; 0 model calls")
    if "chapters" in report:
        typer.echo(f"  chapters: {', '.join(report['chapters'])}")
        typer.echo(f"  route: {report['provider']} ({report['cost_basis']}); tokens about {report['estimate_tokens']:,}")
        usd = report.get("estimate_usd")
        typer.echo(f"  money: {'unknown' if usd is None else f'about ${usd:,.2f}'}"
                   + (f"; allowed up to ${report['authorized_usd']:,.2f}" if report.get("authorized_usd") is not None else ""))
