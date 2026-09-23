"""Read-only model-usage report over the durable model-call receipts.

Receipts form chains through ``parent_call_id``. The root of a chain is the
feature operation (``source_set_synthesis``, ``tutor_qa``, ...); the leaves are
the physical provider requests or SDK turns, and only leaves carry reported
usage. An OpenAI-compatible request is always the leaf purpose
``chat_request``, so every request is attributed to its root's purpose, and
the leaf purpose is kept beside it.

NULL usage means the provider did not report it. It is counted as unknown and
never averaged in as zero, so every statistic states how many requests it
covers.
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
import math
from pathlib import Path
import sqlite3
import statistics
from typing import Any, Iterable, Mapping

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.db.connection import connect


REPORT_VERSION = 1

# The purposes a study-map synthesis run passes to its structured operations
# (content.synthesis.source_set_synthesis). Base and span-follow-up shard passes
# share the first; the cross-source graph-structuring pass is the second. Both
# are charged against the run's total input and output ceilings.
SYNTHESIS_PASS_PURPOSE = "source_set_synthesis"
GRAPH_STRUCTURING_PURPOSE = "concept_graph_structuring"
SYNTHESIS_RUN_PURPOSES = (SYNTHESIS_PASS_PURPOSE, GRAPH_STRUCTURING_PURPOSE)

SYNTHESIS_BUDGET_FIELDS = (
    "synthesis_shard_input_tokens",
    "synthesis_shard_output_tokens",
    "synthesis_total_input_ceiling",
    "synthesis_output_tokens",
)
TOKEN_FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens", "reasoning_tokens")
STATUSES = ("completed", "failed", "truncated", "interrupted", "started")

_RECEIPT_COLUMNS = (
    "id", "parent_call_id", "owner_kind", "owner_id", "purpose", "provider", "model", "status",
    "started_at", "finished_at", *TOKEN_FIELDS, "cost",
)


@dataclass(frozen=True)
class _Chains:
    """Each receipt's root and whether it is a leaf (a request with usage)."""

    by_id: dict[str, dict[str, Any]]
    root_of: dict[str, str]
    leaf_ids: set[str]
    leaves_by_root: dict[str, list[dict[str, Any]]]

    def leaves_of(self, root_id: str) -> list[dict[str, Any]]:
        return self.leaves_by_root.get(root_id, [])


def model_usage_report(
    sqlite_path: Path,
    *,
    budgets: Mapping[str, int | None],
    since: datetime | None = None,
    purpose_prefix: str | None = None,
) -> dict[str, Any]:
    """Read every receipt in one read-only transaction and summarize it."""

    receipts: list[dict[str, Any]] = []
    if Path(sqlite_path).exists():
        with closing(connect(sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            receipts = read_receipts(connection)
    return build_usage_report(receipts, budgets=budgets, since=since, purpose_prefix=purpose_prefix)


def read_receipts(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """All receipts, with columns an older schema lacks read as NULL."""

    table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='model_call_receipts'").fetchone()
    if table is None:
        return []
    present = {row[1] for row in connection.execute("PRAGMA table_info(model_call_receipts)")}
    selected = ",".join(column if column in present else f"NULL AS {column}" for column in _RECEIPT_COLUMNS)
    return [dict(row) for row in connection.execute(f"SELECT {selected} FROM model_call_receipts ORDER BY started_at, id")]


def build_usage_report(
    receipts: Iterable[Mapping[str, Any]],
    *,
    budgets: Mapping[str, int | None],
    since: datetime | None = None,
    purpose_prefix: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Summarize receipts by root purpose, by synthesis run, and by coverage.

    Filters apply to whole chains through their root: a request is in scope
    when its root operation started at or after ``since`` and the root's
    purpose starts with ``purpose_prefix``.
    """

    chains = _link_chains(receipts)
    in_scope_roots = {
        root_id for root_id in set(chains.root_of.values())
        if _root_in_scope(chains.by_id[root_id], since=since, purpose_prefix=purpose_prefix)
    }
    requests = [
        chains.by_id[leaf_id] for leaf_id in sorted(chains.leaf_ids)
        if chains.root_of[leaf_id] in in_scope_roots
    ]
    scoped_receipts = sum(1 for receipt_id in chains.root_of if chains.root_of[receipt_id] in in_scope_roots)
    return {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at or utc_now_iso(),
        "filters": {"since": since.isoformat() if since else None, "purpose_prefix": purpose_prefix},
        "totals": {"receipts": scoped_receipts, "operations": len(in_scope_roots), "requests": len(requests)},
        "by_purpose": _by_purpose(requests, chains),
        "synthesis_runs": _synthesis_runs(in_scope_roots, chains, budgets),
        "coverage": _coverage(requests, chains),
        "scope": {
            "unit": "A request is a receipt with no child receipts: one provider request or SDK turn. Requests are attributed to the purpose of the root operation that made them.",
            "unknown_usage": "NULL usage is unknown, never zero. Each statistic reports how many requests it covers as 'known'.",
            "percentiles": "Median is the middle value; p95 is the nearest-rank 95th percentile.",
            "synthesis_runs": "A run is the synthesis and graph-structuring operations that share one receipt owner (an ingest job or a sidecar request). Token totals sum the known usage of their requests.",
            "budget_ratios": "Ratios divide measured tokens by the vault's current effective [ingest.budgets]. A run may have been given other budgets for that one request.",
        },
    }


def _link_chains(receipts: Iterable[Mapping[str, Any]]) -> _Chains:
    by_id = {str(receipt["id"]): dict(receipt) for receipt in receipts}
    parent_ids = {receipt["parent_call_id"] for receipt in by_id.values() if receipt.get("parent_call_id")}
    root_of: dict[str, str] = {}
    for receipt_id in by_id:
        current = receipt_id
        visited = {current}
        # A parent missing from the table ends the walk at the last receipt found.
        while (parent := by_id[current].get("parent_call_id")) in by_id and parent not in visited:
            visited.add(parent)
            current = parent
        root_of[receipt_id] = current
    leaf_ids = {receipt_id for receipt_id in by_id if receipt_id not in parent_ids}
    leaves_by_root: dict[str, list[dict[str, Any]]] = {}
    for leaf_id in sorted(leaf_ids):
        leaves_by_root.setdefault(root_of[leaf_id], []).append(by_id[leaf_id])
    return _Chains(by_id=by_id, root_of=root_of, leaf_ids=leaf_ids, leaves_by_root=leaves_by_root)


def _root_in_scope(root: Mapping[str, Any], *, since: datetime | None, purpose_prefix: str | None) -> bool:
    if purpose_prefix and not str(root["purpose"]).startswith(purpose_prefix):
        return False
    if since is not None:
        started = parse_utc(root.get("started_at"))
        if started is None or started < since:
            return False
    return True


def _usage_unknown(request: Mapping[str, Any]) -> bool:
    return request.get("input_tokens") is None and request.get("output_tokens") is None


def distribution(values: Iterable[int | float | None]) -> dict[str, Any]:
    """Mean, median, nearest-rank p95 and max over the known values only."""

    known = sorted(value for value in values if value is not None)
    if not known:
        return {"known": 0, "total": None, "mean": None, "median": None, "p95": None, "max": None}
    p95_rank = math.ceil(0.95 * len(known))
    return {
        "known": len(known),
        "total": sum(known),
        "mean": round(sum(known) / len(known), 1),
        "median": statistics.median(known),
        "p95": known[p95_rank - 1],
        "max": known[-1],
    }


def _provider_and_model(request: Mapping[str, Any], root: Mapping[str, Any]) -> tuple[str | None, str | None]:
    return request.get("provider") or root.get("provider"), request.get("model") or root.get("model")


def _by_purpose(requests: list[dict[str, Any]], chains: _Chains) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str | None, str | None], list[dict[str, Any]]] = {}
    for request in requests:
        root = chains.by_id[chains.root_of[request["id"]]]
        provider, model = _provider_and_model(request, root)
        groups.setdefault((root["purpose"], provider, model), []).append(request)
    rows = []
    for (purpose, provider, model), members in sorted(groups.items(), key=lambda entry: _sort_key(entry[0])):
        statuses = Counter(member["status"] for member in members)
        costs = [member["cost"] for member in members if member.get("cost") is not None]
        rows.append({
            "purpose": purpose,
            "provider": provider,
            "model": model,
            "requests": len(members),
            "operations": len({chains.root_of[member["id"]] for member in members}),
            "request_purposes": dict(sorted(Counter(member["purpose"] for member in members).items())),
            "statuses": {status: statuses.get(status, 0) for status in STATUSES},
            "usage_unknown": sum(_usage_unknown(member) for member in members),
            "tokens": {field: distribution(member.get(field) for member in members) for field in TOKEN_FIELDS},
            "cost": {"known": len(costs), "total": round(sum(costs), 6) if costs else None},
        })
    return rows


def _synthesis_runs(in_scope_roots: set[str], chains: _Chains, budgets: Mapping[str, int | None]) -> dict[str, Any]:
    runs: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for root_id in sorted(in_scope_roots):
        root = chains.by_id[root_id]
        if root["purpose"] in SYNTHESIS_RUN_PURPOSES:
            runs.setdefault((str(root["owner_kind"]), str(root["owner_id"])), []).append(root)
    summaries = [_synthesis_run(owner, roots, chains, budgets) for owner, roots in runs.items()]
    summaries.sort(key=lambda run: (run["started_at"] or "", run["owner_kind"], run["owner_id"]))
    return {"budgets": {field: budgets.get(field) for field in SYNTHESIS_BUDGET_FIELDS}, "runs": summaries}


def _synthesis_run(owner: tuple[str, str], roots: list[dict[str, Any]], chains: _Chains, budgets: Mapping[str, int | None]) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    shard_pass_inputs: list[int | None] = []
    shard_pass_outputs: list[int | None] = []
    for root in roots:
        pass_requests = chains.leaves_of(root["id"])
        requests.extend(pass_requests)
        if root["purpose"] == SYNTHESIS_PASS_PURPOSE:
            shard_pass_inputs.append(_known_sum(pass_requests, "input_tokens"))
            shard_pass_outputs.append(_known_sum(pass_requests, "output_tokens"))
    input_tokens = _known_sum(requests, "input_tokens")
    output_tokens = _known_sum(requests, "output_tokens")
    largest_pass_input = max((value for value in shard_pass_inputs if value is not None), default=None)
    largest_pass_output = max((value for value in shard_pass_outputs if value is not None), default=None)
    models = sorted({_provider_and_model(request, chains.by_id[chains.root_of[request["id"]]]) for request in requests}, key=_sort_key)
    return {
        "owner_kind": owner[0],
        "owner_id": owner[1],
        "started_at": min((root["started_at"] for root in roots if root.get("started_at")), default=None),
        "models": [{"provider": provider, "model": model} for provider, model in models],
        "passes": {purpose: sum(root["purpose"] == purpose for root in roots) for purpose in SYNTHESIS_RUN_PURPOSES},
        "pass_statuses": {status: sum(root["status"] == status for root in roots) for status in STATUSES},
        "requests": len(requests),
        "requests_without_usage": sum(_usage_unknown(request) for request in requests),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "largest_pass_input_tokens": largest_pass_input,
        "largest_pass_output_tokens": largest_pass_output,
        "budget_ratios": {
            "input_to_total_input_ceiling": _ratio(input_tokens, budgets.get("synthesis_total_input_ceiling")),
            "output_to_output_ceiling": _ratio(output_tokens, budgets.get("synthesis_output_tokens")),
            "largest_pass_input_to_shard_input": _ratio(largest_pass_input, budgets.get("synthesis_shard_input_tokens")),
            "largest_pass_output_to_shard_output": _ratio(largest_pass_output, budgets.get("synthesis_shard_output_tokens")),
        },
    }


def _coverage(requests: list[dict[str, Any]], chains: _Chains) -> list[dict[str, Any]]:
    """Where usage goes unreported, by root purpose, request purpose and provider.

    Failed or unfinished requests often carry no usage. A completed request
    without usage points at a provider path that does not report it.
    """

    groups: dict[tuple[str, str, str | None], list[dict[str, Any]]] = {}
    for request in requests:
        root = chains.by_id[chains.root_of[request["id"]]]
        provider, _ = _provider_and_model(request, root)
        groups.setdefault((root["purpose"], request["purpose"], provider), []).append(request)
    rows = []
    for (purpose, request_purpose, provider), members in sorted(groups.items(), key=lambda entry: _sort_key(entry[0])):
        completed = [member for member in members if member["status"] == "completed"]
        completed_without_usage = sum(_usage_unknown(member) for member in completed)
        if not completed:
            completed_coverage = "no_completed_requests"
        elif completed_without_usage == 0:
            completed_coverage = "full"
        elif completed_without_usage == len(completed):
            completed_coverage = "none"
        else:
            completed_coverage = "partial"
        rows.append({
            "purpose": purpose,
            "request_purpose": request_purpose,
            "provider": provider,
            "requests": len(members),
            "requests_with_usage": sum(not _usage_unknown(member) for member in members),
            "completed_requests": len(completed),
            "completed_without_usage": completed_without_usage,
            "completed_usage_coverage": completed_coverage,
        })
    return rows


def _known_sum(requests: Iterable[Mapping[str, Any]], field: str) -> int | None:
    """The sum of the reported values, or None when no request reported one."""

    known = [request[field] for request in requests if request.get(field) is not None]
    return sum(known) if known else None


def _ratio(value: int | None, budget: int | None) -> float | None:
    if value is None or not budget:
        return None
    return round(value / budget, 3)


def _sort_key(values: tuple[Any, ...]) -> tuple[str, ...]:
    return tuple("" if value is None else str(value) for value in values)
