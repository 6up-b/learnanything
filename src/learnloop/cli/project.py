"""`learnloop project`: delayed questions on agent-written code (project understanding M1).

Capture is automatic once a repo is enrolled (app start, plan build, `sweep`).
Paid work (probe generation, grading) runs under spend caps with `--dry-run`
estimates; on the Codex subscription its cost is an `estimated_only` figure.
No command renders a question before it is due.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.cli.embeddings import _cancellation
from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.config import LearnLoopConfig, load_config
from learnloop.ids import new_ulid
from learnloop.projects.ai_runtime import (
    PaidCalls,
    PlannedCall,
    caps_from_options,
    describe_routes,
    project_routes,
)
from learnloop.projects.capture import (
    AGENTS,
    capture_commit,
    capture_working_tree,
    enroll_repo,
    estimate_tokens,
    find_repo,
    sweep,
)
from learnloop.projects.experiment_store import ProjectStore
from learnloop.projects.git import GitError, repo_toplevel
from learnloop.projects.hooks import HookError, install_hook, uninstall_hook
from learnloop.projects.probes import (
    GRADING_ITEM_TOKENS_ESTIMATE,
    GRADING_OUTPUT_TOKENS_PER_ITEM,
    PROMPT_OVERHEAD_TOKENS,
    ProbeStateError,
    SealedProbeError,
    contest_grade,
    diffs_awaiting_generation,
    due_probes,
    generate_probes,
    grade_responses,
    open_probe,
    plan_generation,
    record_response,
    reveal,
)
from learnloop.projects.report import build_report, build_status, render_report
from learnloop.vault.paths import find_vault_root

project_app = typer.Typer(
    no_args_is_help=True,
    help="Delayed questions on agent-written code in your enrolled repos.",
)

VaultOption = Annotated[Path | None, typer.Option("--vault", help="Vault root (default: the vault containing the cwd).")]
JsonOption = Annotated[bool, typer.Option("--json", help="Emit JSON.")]
MaxCandidates = Annotated[int, typer.Option("--max-candidates", min=0, help="Cap on authored candidates.")]
MaxCalls = Annotated[int, typer.Option("--max-calls", min=0, help="Cap on model calls (every route).")]
MaxRetries = Annotated[int, typer.Option("--max-retries", min=0, help="Cap on hidden provider retries (metered routes).")]
MaxTokens = Annotated[int, typer.Option("--max-tokens", min=0, help="Token cap for metered routes; the Codex subscription is not token-capped.")]
MaxCost = Annotated[float, typer.Option("--max-cost-usd", min=0, help="Dollar cap for metered routes; the Codex subscription is estimate-only.")]
PriceOption = Annotated[float | None, typer.Option(
    "--price-per-million", min=0,
    help="USD per million tokens for a metered route with an unknown price (unknown prices fail closed); "
    "also overrides the subscription's reference rate for estimates.",
)]


def _clock() -> Clock:
    return SystemClock()


def _vault_root(vault: Path | None) -> Path:
    root = (vault or find_vault_root(Path.cwd())).expanduser().resolve()
    if not (root / "learnloop.toml").is_file():
        raise ValueError(f"{root} is not a vault (no learnloop.toml)")
    return root


def _config(root: Path) -> LearnLoopConfig:
    return load_config(root / "learnloop.toml")


def _store(root: Path) -> ProjectStore:
    store = ProjectStore.existing(root)
    if store is None:
        raise ValueError("No repo is enrolled in this vault yet: run `learnloop project enroll <repo>`.")
    return store


def _emit(payload: dict[str, Any], json_output: bool, text: str | None = None) -> None:
    if json_output or text is None:
        typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2, default=str))
    else:
        typer.echo(text)


def _fail(message: str, json_output: bool) -> None:
    _emit({"status": "invalid", "reason": message}, json_output, f"Error: {message}")
    raise typer.Exit(code=1)


def _generate(
    root: Path,
    config: LearnLoopConfig,
    store: ProjectStore,
    diffs: list[dict[str, Any]],
    *,
    caps,
    price_per_million: float | None,
    dry_run: bool,
    clock: Clock,
) -> dict[str, Any]:
    if not diffs:
        return {"status": "nothing_to_generate", "diffs": []}
    routes = describe_routes(config)
    with _cancellation() as stop:
        paid = PaidCalls(store, caps=caps, run_id=new_ulid(), price_per_million=price_per_million, cancelled=stop.is_set)
        planned = plan_generation(store, root, config, diffs)
        try:
            estimate = paid.plan(planned, routes)
        except SpendLimitExceeded as exc:
            return {"status": "over_budget", "reason": str(exc), "diffs": len(diffs), "routes": routes}
        if dry_run:
            return {"status": "dry_run", "diffs": len(diffs), "estimate": estimate, "routes": routes}
        with project_routes(root, config, ("authoring", "closed_book", "grading")) as resolved:
            report = generate_probes(store, root, config, paid, resolved, diffs, clock=clock)
    return {**report.as_dict(), "estimate": estimate}


def _grading_plan(store: ProjectStore, responses: list[dict[str, Any]]) -> list[PlannedCall]:
    planned = []
    for response in responses:
        probe = store.probe(response["probe_id"]) or {}
        text = (probe.get("question") or "") + (probe.get("reference_answer") or "") + (probe.get("citations_json") or "") + (response.get("answer") or "")
        planned.append(
            PlannedCall("grading", PROMPT_OVERHEAD_TOKENS + max(GRADING_ITEM_TOKENS_ESTIMATE, estimate_tokens(text)), GRADING_OUTPUT_TOKENS_PER_ITEM)
        )
    return planned


def _grade(
    root: Path,
    config: LearnLoopConfig,
    store: ProjectStore,
    response_ids: list[str] | None,
    *,
    caps,
    price_per_million: float | None,
    clock: Clock,
    dry_run: bool = False,
) -> dict[str, Any]:
    pending = [
        response for response in store.responses(grade_status="pending")
        if response_ids is None or response["id"] in response_ids
    ]
    if not pending:
        return {"status": "nothing_to_grade", "results": []}
    routes = describe_routes(config)
    with _cancellation() as stop:
        paid = PaidCalls(store, caps=caps, run_id=new_ulid(), price_per_million=price_per_million, cancelled=stop.is_set)
        try:
            estimate = paid.plan(_grading_plan(store, pending), routes)
        except SpendLimitExceeded as exc:
            return {"status": "over_budget", "reason": str(exc), "pending": len(pending)}
        if dry_run:
            return {"status": "dry_run", "pending": len(pending), "estimate": estimate, "routes": {"grading": routes["grading"]}}
        with project_routes(root, config, ("grading",)) as resolved:
            route = resolved["grading"]
            if not route.ready:
                return {"status": "provider_unavailable", "reason": route.message, "pending": len(pending)}
            try:
                results = grade_responses(store, paid, route, response_ids=[r["id"] for r in pending], clock=clock)
                status = "complete" if all(r["status"] == "graded" for r in results) else "partial"
            except SpendLimitExceeded as exc:
                return {"status": "over_budget", "reason": str(exc), "spend": paid.summary()}
    return {"status": status, "results": results, "spend": paid.summary()}


# --- enrollment -------------------------------------------------------------------


@project_app.command("enroll")
def project_enroll(
    repo: Annotated[Path, typer.Argument(help="A git work tree whose agent-written commits you want questions about.")],
    vault: VaultOption = None,
    since_days: Annotated[int | None, typer.Option("--since-days", min=0, help="Also capture agent commits from this many days back (default: project.enroll_backfill_days).")] = None,
    context_scope: Annotated[str, typer.Option("--context-scope", help="'diff' (default) or 'repo'; repo scope needs READ_ONLY_WORKSPACE, which is not built yet, so diff scope is used.")] = "diff",
    hook: Annotated[bool, typer.Option("--install-hook", help="Also install the append-only post-commit hook.")] = False,
    json_output: JsonOption = False,
) -> None:
    """Enroll a repo: from now on its agent-trailer commits are captured automatically."""

    clock = _clock()
    try:
        root = _vault_root(vault)
        config = _config(root)
        row, created = enroll_repo(root, config, repo, clock=clock, backfill_days=since_days, context_scope=context_scope)
        store = ProjectStore.for_vault(root)
        hook_result = install_hook(root, store, row) if hook else None
        swept = sweep(root, config, clock=clock, trigger="enroll", repo_ids={row["id"]})
    except (ValueError, GitError, HookError) as exc:
        _fail(str(exc), json_output)
        return
    payload = {
        "status": "enrolled" if created else "already_enrolled",
        "repo": {key: row[key] for key in ("id", "name", "path", "capture_since", "context_scope")},
        "hook": hook_result,
        "captured": swept.captured,
        "excluded": swept.excluded,
        "next": "learnloop project sweep --dry-run, then learnloop project sweep (generates questions)",
    }
    notes = []
    if context_scope == "repo":
        notes.append("Repo scope is recorded, but READ_ONLY_WORKSPACE is not available yet: diff scope is used.")
    payload["notes"] = notes
    text = (
        f"{'Enrolled' if created else 'Already enrolled'} {row['name']} ({row['path']}).\n"
        f"Captured {swept.captured} agent commit(s) since {row['capture_since']}"
        + (f"; {swept.excluded} too small or nothing to ask about" if swept.excluded else "")
        + ".\n"
        + (f"Hook: {hook_result['status']} at {hook_result['hook']}\n" if hook_result else "")
        + "".join(f"{note}\n" for note in notes)
        + "Questions are generated by `learnloop project sweep` (dry-run first) and become due "
        f"{config.project.probe_delay_days} days after capture."
    )
    _emit(payload, json_output, text)


@project_app.command("unenroll")
def project_unenroll(
    repo: Annotated[str, typer.Argument(help="Repo path or id.")],
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Stop capturing a repo. Captured diffs, probes and answers are kept."""

    try:
        root = _vault_root(vault)
        store = _store(root)
        row = find_repo(store, repo)
        if row is None:
            raise ValueError(f"{repo} is not enrolled")
        store.set_repo_enabled(row["id"], False)
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    _emit({"status": "unenrolled", "repo_id": row["id"]}, json_output, f"Stopped capturing {row['name']}; its history is kept.")


@project_app.command("install-hook")
def project_install_hook(
    repo: Annotated[str, typer.Argument(help="Enrolled repo path or id.")],
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Install the append-only post-commit hook (it never blocks a commit)."""

    try:
        root = _vault_root(vault)
        store = _store(root)
        row = find_repo(store, repo)
        if row is None:
            raise ValueError(f"{repo} is not enrolled")
        result = install_hook(root, store, row)
    except (ValueError, GitError, HookError) as exc:
        _fail(str(exc), json_output)
        return
    _emit(result, json_output, f"Hook {result['status']}: {result['hook']}")


@project_app.command("uninstall-hook")
def project_uninstall_hook(
    repo: Annotated[str, typer.Argument(help="Enrolled repo path or id.")],
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Remove LearnLoop's block from the repo's post-commit hook."""

    try:
        root = _vault_root(vault)
        store = _store(root)
        row = find_repo(store, repo)
        if row is None:
            raise ValueError(f"{repo} is not enrolled")
        result = uninstall_hook(store, row)
    except (ValueError, GitError, HookError) as exc:
        _fail(str(exc), json_output)
        return
    _emit(result, json_output, f"Hook {result['status']}: {result['hook']}")


# --- capture ------------------------------------------------------------------------


@project_app.command("sweep")
def project_sweep(
    vault: VaultOption = None,
    repo: Annotated[str | None, typer.Option("--repo", help="Only this enrolled repo (path or id).")] = None,
    capture_only: Annotated[bool, typer.Option("--capture-only", help="Capture without generating questions (no model calls).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate generation for captured diffs; no capture, model calls or writes.")] = False,
    max_diffs: Annotated[int, typer.Option("--max-diffs", min=0, help="Generate for at most this many diffs, oldest first.")] = 30,
    max_candidates: MaxCandidates = 300,
    max_calls: MaxCalls = 200,
    max_retries: MaxRetries = 4,
    max_tokens: MaxTokens = 2_000_000,
    max_cost_usd: MaxCost = 2.0,
    price_per_million: PriceOption = None,
    json_output: JsonOption = False,
) -> None:
    """Capture new agent-trailer commits, then generate their questions.

    Always exits 0 (a sweep never fails its caller); problems are reported.
    """

    clock = _clock()
    try:
        root = _vault_root(vault)
        config = _config(root)
        store = ProjectStore.existing(root)
        if store is None:
            _emit({"status": "not_enrolled"}, json_output, "No repo is enrolled in this vault yet: run `learnloop project enroll <repo>`.")
            return
        repo_ids = None
        if repo is not None:
            row = find_repo(store, repo)
            if row is None:
                raise ValueError(f"{repo} is not enrolled")
            repo_ids = {row["id"]}
        caps = caps_from_options(
            max_candidates=max_candidates, max_calls=max_calls, max_retries=max_retries,
            max_tokens=max_tokens, max_cost_usd=max_cost_usd,
        )
        swept = None if dry_run else sweep(root, config, clock=clock, trigger="manual", repo_ids=repo_ids)
        awaiting = [
            diff for diff in diffs_awaiting_generation(store)
            if repo_ids is None or diff["repo_id"] in repo_ids
        ][:max_diffs]
        generation = None if capture_only else _generate(
            root, config, store, awaiting, caps=caps, price_per_million=price_per_million, dry_run=dry_run, clock=clock,
        )
        payload = {
            "status": "dry_run" if dry_run else (swept.status if swept else "ok"),
            "sweep": swept.as_dict() if swept else None,
            "generation": generation,
        }
    except Exception as exc:  # noqa: BLE001 - G1: a sweep reports, it never fails
        payload = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    _emit(payload, json_output)


@project_app.command("accept")
def project_accept(
    repo: Annotated[Path, typer.Option("--repo", help="Enrolled repo (default: the cwd's repo).")] = Path("."),
    commit: Annotated[list[str] | None, typer.Option("--commit", help="Capture this commit (repeatable) instead of the working tree.")] = None,
    agent: Annotated[str | None, typer.Option("--agent", help="claude_code, codex, other or unknown.")] = None,
    include_untracked: Annotated[bool, typer.Option("--include-untracked", help="Include untracked files (.gitignore respected).")] = False,
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Mark agent work that has no trailer: the working tree, or `--commit <sha>`."""

    clock = _clock()
    try:
        if agent is not None and agent not in AGENTS:
            raise ValueError(f"--agent must be one of {', '.join(AGENTS)}")
        root = _vault_root(vault)
        config = _config(root)
        store = _store(root)
        row = find_repo(store, repo)
        if row is None:
            raise ValueError(f"{repo_toplevel(repo)} is not enrolled: run `learnloop project enroll` first")
        if commit:
            results = [
                capture_commit(
                    store, root, config, row, sha, capture_source="accept", trigger="manual",
                    clock=clock, agent=agent, agent_source="flag" if agent else "self_report",
                ).as_dict()
                for sha in commit
            ]
        else:
            results = [
                capture_working_tree(
                    store, root, config, row, clock=clock, agent=agent, include_untracked=include_untracked,
                ).as_dict()
            ]
    except (ValueError, GitError) as exc:
        _fail(str(exc), json_output)
        return
    payload = {"status": "ok", "results": results}
    text = "\n".join(
        f"{result['status']}: {result['diff_id'] or '-'}" + (f" ({result['detail']})" if result["detail"] else "")
        for result in results
    )
    _emit(payload, json_output, text)


@project_app.command("provenance")
def project_provenance(
    diff_id: Annotated[str, typer.Argument(help="A captured diff id (see `status --diffs`).")],
    accept_style: Annotated[str | None, typer.Option("--accept-style", help="per_hunk, all_at_once or unknown.")] = None,
    usage: Annotated[str | None, typer.Option("--usage", help="i_designed_it_typed, we_iterated or it_designed.")] = None,
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Optional self-report of how the code was produced. It never changes a grade."""

    clock = _clock()
    try:
        if accept_style is None and usage is None:
            raise ValueError("give --accept-style and/or --usage")
        if accept_style is not None and accept_style not in {"per_hunk", "all_at_once", "unknown"}:
            raise ValueError("--accept-style must be per_hunk, all_at_once or unknown")
        if usage is not None and usage not in {"i_designed_it_typed", "we_iterated", "it_designed"}:
            raise ValueError("--usage must be i_designed_it_typed, we_iterated or it_designed")
        root = _vault_root(vault)
        store = _store(root)
        if store.diff(diff_id) is None:
            raise ValueError(f"no captured diff {diff_id!r}")
        store.add_provenance(
            {"id": new_ulid(), "diff_id": diff_id, "accept_style": accept_style, "usage_tap": usage, "created_at": utc_now_iso(clock)}
        )
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    _emit({"status": "recorded", "diff_id": diff_id}, json_output, "Recorded.")


# --- status and report --------------------------------------------------------------------


@project_app.command("status")
def project_status(
    vault: VaultOption = None,
    disclosure: Annotated[bool, typer.Option("--disclosure", help="What was sent to models, per repo.")] = False,
    diffs: Annotated[bool, typer.Option("--diffs", help="List captured diffs (no question text).")] = False,
    json_output: JsonOption = False,
) -> None:
    """Captured and pending counts. Never shows a question."""

    try:
        root = _vault_root(vault)
        store = ProjectStore.existing(root)
        if store is None:
            _emit({"status": "not_enrolled", "repos": []}, json_output, "No repo is enrolled in this vault yet.")
            return
        status = build_status(store, clock=_clock(), disclosure=disclosure, include_diffs=diffs)
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    lines = []
    for repo in status["repos"]:
        lines.append(
            f"{repo['name']}{'' if repo['enabled'] else ' (unenrolled)'}: captured {repo['captured']}, "
            f"awaiting questions {repo['awaiting_generation']}, sealed questions {repo['probes_sealed']}"
            + (f" (next due {repo['next_due_at']})" if repo["next_due_at"] else "")
            + f", due now {repo['probes_due']}, answered {repo['probes_answered']}"
            + (f", excluded {repo['excluded']}" if repo["excluded"] else "")
            + (f", under-probed {repo['under_probed']}" if repo["under_probed"] else "")
            + (f", generation failed {repo['generation_failed']}" if repo["generation_failed"] else "")
            + (f" — last sweep error: {repo['last_sweep_error']}" if repo["last_sweep_error"] else "")
        )
    if status["pending_grades"]:
        lines.append(f"{status['pending_grades']} answer(s) await grading: `learnloop project grade`.")
    if status["unattributed_commits"]:
        lines.append("Commits without an agent trailer (mark AI-written ones with `learnloop project accept --commit <sha>`):")
        lines += [f"  {row['sha'][:12]} {row['subject']}" for row in status["unattributed_commits"][:20]]
    for diff in status.get("diffs", []):
        lines.append(
            f"  {diff['diff_id']} {diff['repo']} {(diff['head_sha'] or '')[:10]} {diff['agent']} "
            f"{diff['probe_status']}{' (' + diff['excluded_reason'] + ')' if diff['excluded_reason'] else ''} "
            f"{', '.join(diff['files'][:4])}"
        )
    for entry in status.get("disclosure", []):
        lines.append(
            f"Disclosure {entry['name']}: {entry['model_calls']} model call(s), {entry['distinct_files_sent']} file(s), "
            f"{entry['hunks_sent']} hunk(s), {entry['bytes_sent']} bytes sent; {entry['redacted_lines_in_captures']} line(s) redacted; "
            f"never sent: {json.dumps(entry['files_never_sent'], sort_keys=True)}; scopes {json.dumps(entry['context_scopes'], sort_keys=True)}"
        )
    _emit(status, json_output, "\n".join(lines) or "No repos.")


@project_app.command("report")
def project_report(
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """The M1 probe report: validity, value, capture coverage, accuracy by provenance."""

    try:
        root = _vault_root(vault)
        config = _config(root)
        store = _store(root)
        report = build_report(store, config, clock=_clock())
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    _emit(report, json_output, render_report(report))


# --- answering ---------------------------------------------------------------------------


_HELP_LINE = (
    "Answer from memory; finish with an empty line. Commands: /dk (don't know), /unfair "
    "(question is unfair or ambiguous), /skip, /quit. Add /looked or /ai if you looked at the "
    "code or used AI."
)


def _read_answer() -> tuple[str | None, str, str]:
    """(answer text, kind or 'quit', declaration) from stdin."""

    lines: list[str] = []
    while True:
        line = sys.stdin.readline()
        if line == "":
            if not lines:
                return None, "quit", "unassisted"
            break
        line = line.rstrip("\n")
        if not line.strip():
            if lines:
                break
            continue
        lines.append(line)
    text = "\n".join(lines)
    declaration = "unassisted"
    if "/looked" in text:
        declaration = "looked"
        text = text.replace("/looked", "")
    if "/ai" in text:
        declaration = "used_ai"
        text = text.replace("/ai", "")
    command = text.strip().lower()
    for token, kind in (("/dk", "dont_know"), ("/unfair", "unfair"), ("/skip", "skip"), ("/quit", "quit")):
        if command == token:
            return None, kind, declaration
    return text.strip(), "answer", declaration


def _render_reveal(info: dict[str, Any]) -> str:
    lines = []
    if info["grade_status"] == "graded":
        lines.append(f"Grade: {info['verdict']} ({info['score']:.2f})" + (f" — {info['feedback']}" if info["feedback"] else ""))
    elif info["grade_status"] == "pending":
        lines.append("Saved; grading will retry with `learnloop project grade`.")
    lines.append(f"Reference: {info['reference_answer']}")
    for citation in info["citations"]:
        where = citation["path"] + (f":{citation['line_start']}-{citation['line_end']}" if citation["line_start"] else "")
        source = {"file": where, "diff": f"{citation['path']} (diff)", "commit_message": "commit message"}[citation["source"]]
        lines.append(f"  {source}: {citation['quote']}")
    if info["rationale_label"] == "agent_stated":
        lines.append("  (This reason is the coding agent's stated rationale, not necessarily yours.)")
    return "\n".join(lines)


@project_app.command("probes")
def project_probes(
    vault: VaultOption = None,
    repo: Annotated[str | None, typer.Option("--repo", help="Only questions about this repo.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Questions this session.")] = 10,
    list_only: Annotated[bool, typer.Option("--list", help="Print due questions and their ids; answer with `project answer`.")] = False,
    no_generate: Annotated[bool, typer.Option("--no-generate", help="Do not generate questions for due diffs that have none.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate generation and grading; serve nothing.")] = False,
    max_candidates: MaxCandidates = 300,
    max_calls: MaxCalls = 200,
    max_retries: MaxRetries = 4,
    max_tokens: MaxTokens = 2_000_000,
    max_cost_usd: MaxCost = 2.0,
    price_per_million: PriceOption = None,
    json_output: JsonOption = False,
) -> None:
    """Answer due questions (unassisted unless you say otherwise)."""

    clock = _clock()
    try:
        root = _vault_root(vault)
        config = _config(root)
        store = _store(root)
        repo_id = None
        if repo is not None:
            row = find_repo(store, repo)
            if row is None:
                raise ValueError(f"{repo} is not enrolled")
            repo_id = row["id"]
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    caps = caps_from_options(
        max_candidates=max_candidates, max_calls=max_calls, max_retries=max_retries,
        max_tokens=max_tokens, max_cost_usd=max_cost_usd,
    )
    generation = None
    if config.project.generate_before_serving and not no_generate:
        awaiting = [
            diff for diff in diffs_awaiting_generation(store, due_by=utc_now_iso(clock), config=config)
            if repo_id is None or diff["repo_id"] == repo_id
        ]
        if awaiting and not dry_run and not json_output and not list_only:
            typer.echo(f"Preparing questions for {len(awaiting)} captured change(s)...")
        generation = _generate(
            root, config, store, awaiting, caps=caps, price_per_million=price_per_million, dry_run=dry_run, clock=clock,
        ) if awaiting else None
    due = due_probes(store, clock=clock, repo_id=repo_id)
    if dry_run:
        grading = PaidCalls(store, caps=caps, run_id="dry-run", price_per_million=price_per_million)
        planned = [PlannedCall("grading", PROMPT_OVERHEAD_TOKENS + GRADING_ITEM_TOKENS_ESTIMATE, GRADING_OUTPUT_TOKENS_PER_ITEM)] * min(limit, len(due))
        try:
            grading_estimate = grading.plan(planned, describe_routes(config))
        except SpendLimitExceeded as exc:
            grading_estimate = {"status": "over_budget", "reason": str(exc)}
        _emit({"status": "dry_run", "due": len(due), "generation": generation, "grading_estimate": grading_estimate}, json_output)
        return
    if list_only:
        questions = [open_probe(store, probe["id"], clock=clock) for probe in due[:limit]]
        text = "\n\n".join(
            f"{q['probe_id']}  [{q['repo']} · {', '.join(q['files'][:3])}]\n{q['question']}" for q in questions
        ) or "No questions are due."
        _emit({"status": "ok", "due": questions, "generation": generation}, json_output, text)
        return
    if not due:
        status = build_status(store, clock=clock)
        upcoming = [repo_row["next_due_at"] for repo_row in status["repos"] if repo_row["next_due_at"]]
        typer.echo("No questions are due." + (f" Next due {min(upcoming)}." if upcoming else ""))
        if generation and generation.get("status") not in {"complete", "nothing_to_generate"}:
            typer.echo(f"Question generation: {generation.get('status')} {generation.get('reason') or ''}".rstrip())
        return
    with _cancellation() as stop:
        paid = PaidCalls(store, caps=caps, run_id=new_ulid(), price_per_million=price_per_million, cancelled=stop.is_set)
        with project_routes(root, config, ("grading",)) as routes:
            grader = routes["grading"]
            for index, probe in enumerate(due[:limit], start=1):
                opened = open_probe(store, probe["id"], clock=clock)
                served_at = utc_now_iso(clock)
                typer.echo(
                    f"\n[{index}/{min(limit, len(due))}] {opened['repo']} · {', '.join(opened['files'][:4])}"
                    + (f" · committed {opened['committed_at'][:10]}" if opened.get("committed_at") else "")
                )
                typer.echo(opened["question"])
                typer.echo(_HELP_LINE)
                answer, kind, declaration = _read_answer()
                if kind == "quit":
                    typer.echo("Stopped; unanswered questions stay due.")
                    break
                response = record_response(
                    store, probe["id"], kind=kind, answer=answer, declaration=declaration,
                    served_at=served_at, clock=clock,
                )
                if kind == "answer" and grader.ready:
                    try:
                        grade_responses(store, paid, grader, response_ids=[response["id"]], clock=clock)
                    except SpendLimitExceeded as exc:
                        typer.echo(f"Grading deferred: {exc}")
                elif kind == "answer":
                    typer.echo(f"Grading provider unavailable: {grader.message}")
                typer.echo(_render_reveal(reveal(store, store.response(response["id"]) or response)))


@project_app.command("answer")
def project_answer(
    probe_id: Annotated[str, typer.Argument(help="A due probe id (see `probes --list`).")],
    text: Annotated[str | None, typer.Option("--text", help="Your answer, from memory.")] = None,
    dont_know: Annotated[bool, typer.Option("--dont-know")] = False,
    unfair: Annotated[bool, typer.Option("--unfair", help="The question is unfair or ambiguous.")] = False,
    skip: Annotated[bool, typer.Option("--skip")] = False,
    looked: Annotated[bool, typer.Option("--looked", help="You looked at the code.")] = False,
    used_ai: Annotated[bool, typer.Option("--used-ai", help="You used AI.")] = False,
    no_grade: Annotated[bool, typer.Option("--no-grade", help="Save now; grade later with `project grade`.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate grading; record nothing.")] = False,
    max_calls: MaxCalls = 5,
    max_retries: MaxRetries = 2,
    max_tokens: MaxTokens = 50_000,
    max_cost_usd: MaxCost = 0.25,
    price_per_million: PriceOption = None,
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Answer one due question non-interactively."""

    clock = _clock()
    chosen = [kind for kind, flag in (("answer", text is not None), ("dont_know", dont_know), ("unfair", unfair), ("skip", skip)) if flag]
    try:
        if len(chosen) != 1:
            raise ValueError("give exactly one of --text, --dont-know, --unfair or --skip")
        if looked and used_ai:
            raise ValueError("give at most one of --looked and --used-ai")
        root = _vault_root(vault)
        config = _config(root)
        store = _store(root)
        caps = caps_from_options(max_candidates=0, max_calls=max_calls, max_retries=max_retries, max_tokens=max_tokens, max_cost_usd=max_cost_usd)
        if dry_run:
            open_probe(store, probe_id, clock=clock)  # refuses sealed probes without rendering them
            paid = PaidCalls(store, caps=caps, run_id="dry-run", price_per_million=price_per_million)
            estimate = paid.plan(
                [PlannedCall("grading", PROMPT_OVERHEAD_TOKENS + GRADING_ITEM_TOKENS_ESTIMATE, GRADING_OUTPUT_TOKENS_PER_ITEM)]
                if chosen[0] == "answer" else [],
                describe_routes(config),
            )
            _emit({"status": "dry_run", "estimate": estimate}, json_output)
            return
        declaration = "looked" if looked else ("used_ai" if used_ai else "unassisted")
        response = record_response(store, probe_id, kind=chosen[0], answer=text, declaration=declaration, clock=clock)
        grading = None
        if chosen[0] == "answer" and not no_grade:
            grading = _grade(root, config, store, [response["id"]], caps=caps, price_per_million=price_per_million, clock=clock)
    except (ValueError, SealedProbeError, ProbeStateError, SpendLimitExceeded) as exc:
        _fail(str(exc), json_output)
        return
    info = reveal(store, store.response(response["id"]) or response)
    _emit({"status": "recorded", "response": info, "grading": grading}, json_output, _render_reveal(info))


@project_app.command("grade")
def project_grade(
    vault: VaultOption = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate; make no calls.")] = False,
    max_calls: MaxCalls = 50,
    max_retries: MaxRetries = 4,
    max_tokens: MaxTokens = 500_000,
    max_cost_usd: MaxCost = 1.0,
    price_per_million: PriceOption = None,
    json_output: JsonOption = False,
) -> None:
    """Grade saved answers whose grading is still pending (blind grader)."""

    clock = _clock()
    try:
        root = _vault_root(vault)
        config = _config(root)
        store = _store(root)
        caps = caps_from_options(max_candidates=0, max_calls=max_calls, max_retries=max_retries, max_tokens=max_tokens, max_cost_usd=max_cost_usd)
        result = _grade(root, config, store, None, caps=caps, price_per_million=price_per_million, clock=clock, dry_run=dry_run)
    except ValueError as exc:
        _fail(str(exc), json_output)
        return
    _emit(result, json_output)


@project_app.command("contest")
def project_contest(
    response_id: Annotated[str, typer.Argument(help="The graded response id.")],
    score: Annotated[float, typer.Option("--score", min=0.0, max=1.0, help="Your adjudicated score (0-1).")],
    note: Annotated[str, typer.Option("--note", help="Why the grade was wrong.")] = "",
    vault: VaultOption = None,
    json_output: JsonOption = False,
) -> None:
    """Contest a grade: your adjudication becomes the outcome of record; the grade is kept."""

    try:
        root = _vault_root(vault)
        store = _store(root)
        response = contest_grade(store, response_id, score=score, note=note, clock=_clock())
    except (ValueError, ProbeStateError) as exc:
        _fail(str(exc), json_output)
        return
    _emit(
        {"status": "adjudicated", "response_id": response_id, "grade": response.get("score"), "adjudicated_score": response.get("adjudicated_score")},
        json_output,
        f"Recorded {score:.2f} as the outcome of record (the grader gave {response.get('score')}).",
    )


__all__ = ["project_app"]
