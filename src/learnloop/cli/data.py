"""Local collection inspection and reproducible dataset artifacts."""
from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Annotated, Any
import json
import typer

from learnloop.cli.app import app
from learnloop.cli.runtime import _dump, _load_vault_or_exit, _root
from learnloop.clock import parse_utc
from learnloop.substrate.data_quality import data_quality_report
from learnloop.substrate.dataset import export_dataset
from learnloop.substrate.model_usage import SYNTHESIS_BUDGET_FIELDS, model_usage_report
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.vault_lock import VaultLockError


def _loaded_vault(vault: Path | None) -> LoadedVault:
    return _load_vault_or_exit(_root(vault), json_output=True)


def _sqlite_path(loaded: LoadedVault) -> Path:
    return VaultPaths(loaded.root, loaded.config).sqlite_path


def _fail(exc: BaseException) -> typer.Exit:
    typer.echo(str(exc), err=True)
    return typer.Exit(1)


@app.command("data-quality")
def data_quality(
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Read-only JSON coverage report, with current-version denominators."""
    typer.echo(_dump(data_quality_report(_sqlite_path(_loaded_vault(vault)))))


@app.command("usage")
def usage(
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the stable JSON report.")] = False,
    since: Annotated[str | None, typer.Option("--since", help="Only operations started at or after this ISO date or time (UTC when no offset).")] = None,
    purpose: Annotated[str | None, typer.Option("--purpose", help="Only operations whose root purpose starts with this prefix.")] = None,
) -> None:
    """Read-only token and cost report from model-call receipts, with synthesis budget ratios."""
    try:
        since_at = parse_utc(since) if since else None
    except ValueError as exc:
        raise typer.BadParameter(f"--since must be an ISO date or time: {exc}") from exc
    loaded = _loaded_vault(vault)
    budgets_config = loaded.config.ingest.budgets
    budgets = {field: getattr(budgets_config, field, None) for field in SYNTHESIS_BUDGET_FIELDS}
    report = model_usage_report(_sqlite_path(loaded), budgets=budgets, since=since_at, purpose_prefix=purpose)
    typer.echo(_dump(report) if json_output else render_usage_report(report))


_TOKEN_LABELS = (
    ("input_tokens", "input"),
    ("output_tokens", "output"),
    ("cached_input_tokens", "cached input"),
    ("cache_write_tokens", "cache write"),
    ("reasoning_tokens", "reasoning"),
)


def render_usage_report(report: dict[str, Any]) -> str:
    """A terminal-width summary of the JSON report, section by section."""
    lines = [_usage_heading(report), ""]
    lines += _render_purposes(report["by_purpose"])
    lines += _render_synthesis_runs(report["synthesis_runs"])
    lines += _render_coverage(report["coverage"])
    return "\n".join(lines).rstrip()


def _usage_heading(report: dict[str, Any]) -> str:
    totals = report["totals"]
    filters = [f"{name} {value}" for name, value in (("since", report["filters"]["since"]), ("purpose", report["filters"]["purpose_prefix"])) if value]
    scope = f" ({', '.join(filters)})" if filters else ""
    return f"Model usage{scope}: {totals['requests']} requests in {totals['operations']} operations"


def _number(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(value):,}"


def _render_purposes(groups: list[dict[str, Any]]) -> list[str]:
    lines = ["By purpose (tokens per request)"]
    if not groups:
        return [*lines, "  No model-call receipts.", ""]
    for group in groups:
        statuses = group["statuses"]
        cost = group["cost"]
        cost_text = f"cost {cost['total']:.4f} ({cost['known']} known)" if cost["known"] else "cost unknown"
        lines += [
            f"  {group['purpose']}  {group['provider'] or '?'} / {group['model'] or '?'}",
            f"    {group['requests']} requests in {group['operations']} operations; "
            f"usage unknown for {group['usage_unknown']}; {cost_text}",
            f"    status: {statuses['completed']} completed, {statuses['failed']} failed, {statuses['truncated']} truncated, "
            f"{statuses['interrupted']} interrupted, {statuses['started']} unfinished",
            f"    {'tokens':<14}{'known':>7}{'mean':>11}{'median':>11}{'p95':>11}{'max':>11}",
        ]
        for field, label in _TOKEN_LABELS:
            stats = group["tokens"][field]
            if field == "cache_write_tokens" and not stats["known"]:
                continue
            lines.append(f"    {label:<14}{stats['known']:>7}" + "".join(f"{_number(stats[key]):>11}" for key in ("mean", "median", "p95", "max")))
        lines.append("")
    return lines


def _ratio_text(value: int | None, ratio: float | None, budget: int | None, name: str) -> str:
    if budget is None:
        return f"{_number(value)} (no {name})"
    if value is None:
        return f"- ({name} {_number(budget)})"
    share = f"{ratio:.2f}" if ratio is not None else "-"
    return f"{_number(value)} = {share} of {name} {_number(budget)}"


def _render_synthesis_runs(section: dict[str, Any]) -> list[str]:
    lines = ["Synthesis runs (measured tokens against the budgets each run ran under)"]
    runs = section["runs"]
    if not runs:
        return [*lines, "  No synthesis runs.", ""]
    for run in runs:
        passes = run["passes"]
        ratios = run["budget_ratios"]
        budgets = run["budgets"]
        budget_note = "unlimited, " if budgets.get("unlimited") else ""
        budget_note += "budgets from its receipts" if run["budget_source"] == "receipt" else "budgets from the current config"
        lines += [
            f"  {run['owner_kind']} {run['owner_id']}",
            f"    started {run['started_at'] or '?'}; {budget_note}",
            f"    {passes['source_set_synthesis']} synthesis + {passes['concept_graph_structuring']} structuring passes, "
            f"{run['requests']} requests ({run['requests_without_usage']} without usage)",
            f"    input   {_ratio_text(run['input_tokens'], ratios['input_to_total_input_ceiling'], budgets['synthesis_total_input_ceiling'], 'total ceiling')}",
            f"            largest pass {_ratio_text(run['largest_pass_input_tokens'], ratios['largest_pass_input_to_shard_input'], budgets['synthesis_shard_input_tokens'], 'shard')}",
            f"    output  {_ratio_text(run['output_tokens'], ratios['output_to_output_ceiling'], budgets['synthesis_output_tokens'], 'total ceiling')}",
            f"            largest pass {_ratio_text(run['largest_pass_output_tokens'], ratios['largest_pass_output_to_shard_output'], budgets['synthesis_shard_output_tokens'], 'shard')}",
        ]
    lines.append("")
    return lines


def _render_coverage(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["Usage coverage of completed requests"]
    gaps = [row for row in rows if row["completed_usage_coverage"] in {"none", "partial"}]
    if not rows:
        return [*lines, "  No requests."]
    if not gaps:
        return [*lines, "  Every completed request reported usage."]
    for row in gaps:
        lines += [
            f"  {row['purpose']} / {row['request_purpose']} / {row['provider'] or '?'}",
            f"    {row['completed_without_usage']} of {row['completed_requests']} completed requests reported no usage",
        ]
    return lines


@app.command("dataset-export")
def dataset_export(
    output: Annotated[Path, typer.Argument(help="New local output directory.")],
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Back up an active database and export evidence, labels and split metadata."""
    sqlite_path = _sqlite_path(_loaded_vault(vault))
    try:
        manifest = export_dataset(sqlite_path, output)
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise _fail(exc) from exc
    typer.echo(_dump({"output": str(output.resolve()), "snapshot_sha256": manifest["snapshot_sha256"], "artifacts": len(manifest["artifacts"])}))


@app.command("adjudicate-remediation")
def adjudicate_remediation(
    attempt_id: Annotated[str, typer.Argument()],
    false_remediation: Annotated[bool, typer.Option("--false-remediation/--appropriate-remediation")],
    evidence: Annotated[Path, typer.Option("--evidence", help="JSON list of retained {table, id} evidence references; id is the table's primary-key value.")],
    verifier_version: Annotated[str, typer.Option("--verifier-version")],
    author_kind: Annotated[str, typer.Option("--author-kind", help="human or machine")] = "human",
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Append an evidence-backed label; corrections append another adjudication."""
    try:
        refs = json.loads(evidence.read_text(encoding="utf-8"))
        if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
            raise ValueError("Evidence must be a JSON list of {table, id} objects.")
        loaded = _loaded_vault(vault)
        repository = open_vault_repository(loaded.root, _sqlite_path(loaded))
        identity = repository.record_false_remediation(attempt_id=attempt_id, value=false_remediation, evidence_refs=refs, author_kind=author_kind, verifier_version=verifier_version)
    except (OSError, ValueError, sqlite3.Error, VaultLockError) as exc:
        raise _fail(exc) from exc
    typer.echo(_dump({"adjudication_id": identity}))
