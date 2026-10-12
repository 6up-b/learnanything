"""The M3 signals report (Slice 2 §3.7), after ~2-4 weeks at ``mvp-0.11``.

Reads only ledgers, receipts and the recurrence projection: no model and no
embedding call. Every rate carries a Wilson interval and its n (no
thresholds: the owner reads them at the M3 review).

| Signal | Reevaluate if |
|---|---|
| escalation usefulness taps | escalated repairs are mostly "didn't help" |
| group precision: an audit sample of merged groups + "not the same mistake" taps on cited answers | merges are often wrong |
| repeated diagnostic episodes (unresolved-cause factors) per recurring cause, before vs after the switch | no reduction |
| next attempt on the LO after an escalated vs a non-escalated diagnosed failure (directional) | consistently worse |
| refused-union log volume | high: the judges disagree with each other |

The audit sample shows the merged groups' statements (learner-derived text):
the report is a local file for the owner, never sent anywhere.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

from learnloop.algorithm_versions import RECURRENCE_GROUP_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.report import wilson
from learnloop.recurrence import key_for_statement
from learnloop.vault.models import LoadedVault

REPORT_VERSION = "slice2-t1-m3-report-v1"


def _rows(repository: Repository, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, params)]


def _switch_time(repository: Repository) -> str | None:
    rows = _rows(
        repository,
        "SELECT MIN(created_at) AS at FROM derived_state_rebuilds WHERE algorithm_version = ?",
        (RECURRENCE_GROUP_ALGORITHM_VERSION,),
    )
    return rows[0]["at"] if rows and rows[0]["at"] else None


def _escalation_taps(repository: Repository) -> dict[str, Any]:
    escalations = repository.recurrence_escalations()
    taps: Counter = Counter()
    rated = 0
    for escalation in escalations:
        responses = [
            row["response"] for row in repository.diagnosis_feedback_rows(escalation["diagnosis_id"])
            if str(row["response"]).startswith("escalation:")
        ]
        if responses:
            rated += 1
            taps[responses[-1].split(":", 1)[1]] += 1
    return {
        "escalations": len(escalations),
        "different_approach": sum(1 for row in escalations if row["different_approach"]),
        "rated": rated,
        "taps": dict(taps),
        "didnt_help_share": wilson(taps.get("didnt_help", 0), rated),
        "helped_share": wilson(taps.get("helped", 0), rated),
    }


def _sample(groups: Mapping[str, list[dict[str, Any]]], size: int) -> list[str]:
    ranked = sorted(groups, key=lambda key: hashlib.sha256(key.encode()).hexdigest())
    return ranked[:size]


def _group_precision(repository: Repository, *, audit_sample: int) -> dict[str, Any]:
    members = repository.recurrence_groups()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in members:
        groups[str(row["group_key"])].append(row)
    joins = Counter(str(row["judge"] or row["joined_by"]) for row in members if row["joined_by"] in ("citation", "judgment"))
    sample = []
    for key in _sample(groups, audit_sample):
        rows = groups[key]
        statements = []
        for row in rows:
            if row["joined_by"] == "exact_key":
                continue
            head = repository.latest_causal_hypothesis_for_episode(str(row["episode_key"])) or {}
            statements.append(
                {
                    "statement": head.get("statement"),
                    "joined_by": row["joined_by"],
                    "judge": row["judge"],
                    "source": row["joined_by_ref"],
                }
            )
        sample.append({"group_key": key, "classes": rows[0]["class_count"], "members": len(rows), "statements": statements})
    citations_shown = 0
    for receipt in _rows(repository, "SELECT validated_citations_json FROM diagnosis_context_receipts"):
        try:
            citations_shown += len({str(row.get("attempt_id")) for row in json.loads(receipt["validated_citations_json"] or "[]")})
        except (TypeError, ValueError):
            continue
    not_same = _rows(repository, "SELECT COUNT(*) AS n FROM diagnosis_feedback WHERE response = 'not_same_mistake'")[0]["n"]
    return {
        "merged_groups": len(groups),
        "merged_classes": sum(rows[0]["class_count"] for rows in groups.values()),
        "class_joins_by_judge": dict(joins),
        "not_same_mistake_taps": int(not_same or 0),
        "not_same_mistake_share_of_citations_shown": wilson(int(not_same or 0), citations_shown),
        "audit_sample": sample,
    }


def _repeated_episodes(repository: Repository, switch_at: str | None) -> dict[str, Any]:
    """Unresolved-cause factors (diagnostic episodes) per recurring cause."""

    groups = repository.recurrence_group_map()
    attempts = {row["id"]: row for row in _rows(repository, "SELECT id, created_at FROM practice_attempts")}
    factors = _rows(repository, "SELECT attempt_id, created_at, resolution_kind FROM unresolved_cause_factors")
    attempt_keys: dict[str, set[str]] = defaultdict(set)
    for row in _rows(
        repository,
        "SELECT attempt_id, statement_normalized FROM causal_hypotheses WHERE status != 'open_set' "
        "AND cause_scope = 'learner_state'",
    ):
        attempt_keys[str(row["attempt_id"])].add(key_for_statement(row["statement_normalized"], groups))
    attempts_per_key: dict[str, set[str]] = defaultdict(set)
    for attempt_id, keys in attempt_keys.items():
        for key in keys:
            attempts_per_key[key].add(attempt_id)
    recurring = {key for key, ids in attempts_per_key.items() if len(ids) >= 2}

    def window(created: str | None) -> str:
        if switch_at is None:
            return "before"
        return "after" if str(created or "") >= switch_at else "before"

    counts: dict[str, Counter] = {"before": Counter(), "after": Counter()}
    for key in recurring:
        for attempt_id in attempts_per_key[key]:
            counts[window(attempts.get(attempt_id, {}).get("created_at"))]["attempts"] += 1
    for factor in factors:
        keys = attempt_keys.get(str(factor.get("attempt_id") or ""), set()) & recurring
        if not keys:
            continue
        side = window(factor.get("created_at"))
        counts[side]["factors"] += 1
        if factor.get("resolution_kind") == "escalated_unrepaired":
            counts[side]["escalated_unrepaired"] += 1
    return {
        "switch_at": switch_at,
        "recurring_causes": len(recurring),
        **{
            side: {
                **dict(values),
                "factors_per_recurring_attempt": round(values["factors"] / values["attempts"], 4) if values["attempts"] else None,
            }
            for side, values in counts.items()
        },
        "note": "a diagnostic episode is an unresolved-cause factor opened on a recurring cause's attempt",
    }


def _next_outcomes(repository: Repository) -> dict[str, Any]:
    """The next attempt on the same LO after a diagnosed failure (directional)."""

    escalated = {row["attempt_id"] for row in repository.recurrence_escalations()}
    diagnosed = {
        row["attempt_id"]
        for row in _rows(repository, "SELECT attempt_id FROM attempt_diagnoses WHERE mode = 'live' AND status = 'completed'")
    }
    attempts = _rows(
        repository,
        "SELECT id, learning_object_id, created_at, correctness FROM practice_attempts ORDER BY created_at, id",
    )
    by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempts:
        by_lo[str(row["learning_object_id"])].append(row)
    outcome: dict[str, list[int]] = {"escalated": [0, 0], "not_escalated": [0, 0]}
    for rows in by_lo.values():
        for position, row in enumerate(rows):
            if row["id"] not in diagnosed or position + 1 >= len(rows):
                continue
            nxt = rows[position + 1]
            bucket = "escalated" if row["id"] in escalated else "not_escalated"
            outcome[bucket][1] += 1
            if float(nxt.get("correctness") or 0.0) >= 1.0:
                outcome[bucket][0] += 1
    return {
        bucket: {"next_attempt_correct": wilson(hits, n)} for bucket, (hits, n) in outcome.items()
    } | {"note": "directional only: slow, confounded by item difficulty and time"}


def _review_volume(repository: Repository) -> dict[str, Any]:
    cases = Counter(row["case_kind"] for row in repository.recurrence_review())
    judged = _rows(
        repository,
        "SELECT judge, verdict, COUNT(*) AS n FROM judgment_ledger WHERE task = 'same_cause' "
        "AND COALESCE(left_kind, '') != 'planted_hypothesis' GROUP BY judge, verdict",
    )
    by_judge: dict[str, dict[str, int]] = defaultdict(dict)
    for row in judged:
        by_judge[str(row["judge"])][str(row["verdict"])] = int(row["n"])
    return {"review_cases": dict(cases), "same_cause_verdicts_by_judge": dict(by_judge)}


def m3_report(vault: LoadedVault, repository: Repository, *, audit_sample: int = 10) -> dict[str, Any]:
    switch_at = _switch_time(repository)
    return {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "recurrence_enabled": bool(vault.config.recurrence.enabled),
        "state": repository.recurrence_state(),
        "escalation_usefulness": _escalation_taps(repository),
        "group_precision": _group_precision(repository, audit_sample=audit_sample),
        "repeated_diagnostic_episodes": _repeated_episodes(repository, switch_at),
        "next_attempt_after_repair": _next_outcomes(repository),
        "review_volume": _review_volume(repository),
    }


def _fmt(value: Any) -> str:
    if isinstance(value, Mapping) and "rate" in value:
        rate = value.get("rate")
        low, high = value.get("low"), value.get("high")
        return f"{rate} [{low}, {high}] (n={value.get('n')})" if rate is not None else f"n={value.get('n')}"
    return json.dumps(value, sort_keys=True, default=str)


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Slice 2 T1: M3 signals",
        "",
        f"Generated {report['generated_at']} at {report['algorithm_version']} "
        f"(recurrence.enabled = {report['recurrence_enabled']}). No model or embedding call was made.",
        "",
        "## Escalation usefulness",
    ]
    taps = report["escalation_usefulness"]
    lines += [
        f"- escalations shown: {taps['escalations']} ({taps['different_approach']} with a different approach)",
        f"- rated: {taps['rated']}; taps {json.dumps(taps['taps'], sort_keys=True)}",
        f"- didn't help: {_fmt(taps['didnt_help_share'])}; helped: {_fmt(taps['helped_share'])}",
        "",
        "## Group precision",
    ]
    precision = report["group_precision"]
    lines += [
        f"- merged groups: {precision['merged_groups']} over {precision['merged_classes']} statement classes",
        f"- class joins by judge: {json.dumps(precision['class_joins_by_judge'], sort_keys=True)}",
        f"- \"not the same mistake\" taps: {precision['not_same_mistake_taps']}; share of citations shown "
        f"{_fmt(precision['not_same_mistake_share_of_citations_shown'])}",
        "",
        "Audit sample (read each group: is it one cause?):",
        "",
    ]
    for group in precision["audit_sample"]:
        lines.append(f"- `{group['group_key']}` ({group['classes']} classes, {group['members']} hypotheses)")
        for statement in group["statements"]:
            lines.append(f"  - [{statement['joined_by']}/{statement['judge'] or '-'}] {statement['statement']}")
    episodes = report["repeated_diagnostic_episodes"]
    lines += [
        "",
        "## Repeated diagnostic episodes per recurring cause",
        f"- switch at: {episodes['switch_at'] or 'not switched (all history counts as before)'}; recurring causes: {episodes['recurring_causes']}",
        f"- before: {json.dumps(episodes['before'], sort_keys=True)}",
        f"- after: {json.dumps(episodes['after'], sort_keys=True)}",
        "",
        "## Next attempt after an escalated vs a non-escalated diagnosed failure (directional)",
    ]
    outcomes = report["next_attempt_after_repair"]
    lines += [
        f"- escalated: {_fmt(outcomes['escalated']['next_attempt_correct'])}",
        f"- not escalated: {_fmt(outcomes['not_escalated']['next_attempt_correct'])}",
        "",
        "## Review volume",
        f"- review cases: {json.dumps(report['review_volume']['review_cases'], sort_keys=True)}",
        f"- same_cause verdicts by judge: {json.dumps(report['review_volume']['same_cause_verdicts_by_judge'], sort_keys=True)}",
        "",
    ]
    return "\n".join(lines)


__all__ = ["REPORT_VERSION", "m3_report", "render_markdown"]
