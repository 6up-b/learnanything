"""``learnloop gaps report``: what the pipeline did, per kind and chooser (no call).

For each kind and each chooser (the context model, or the Decider when the
switch made it authoritative): read, matched, created, noted beliefs, undone.
For created prerequisites, the first-check pass rate (their light commitment's
delayed check, read from placement whatever the creation switch says now),
overall and per chooser. For beliefs, the learner's "not what I meant" taps
and the diagnosis card's "not the same mistake" taps on the answers this
pipeline read as beliefs. And the evidence on whether the Decider or the LLM
chooses better: their agreement on the kind (and, per disagreement, whether
the acted reading was later undone), and the two judges' agreement on the
same pairs. ``since`` windows everything: the readings, their reversals, the
pair verdicts, the commitments and the jobs (Codex review F11).

Counts carry Wilson 95% intervals; there are no thresholds and no
recommendation. Learner texts appear only in ``--out``'s batch-review section
(slip, wording and unmatched readings for an owner's batch review: error types
are never created automatically).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from contextlib import closing
import math
from pathlib import Path
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.decider_judgments import FAILURE_VERDICTS
from learnloop.diagnosis.text_gaps.contract import NEEDED_TASK, SAME_BELIEF_TASK, SAME_PREREQUISITE_TASK
from learnloop.vault.models import LoadedVault

REPORT_VERSION = "learner-text-gaps-report-v1"


def wilson(successes: int, trials: int, z: float = 1.96) -> list[float] | None:
    if trials <= 0:
        return None
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def _rate(successes: int, trials: int) -> dict[str, Any]:
    return {"n": trials, "k": successes, "rate": round(successes / trials, 4) if trials else None,
            "wilson95": wilson(successes, trials)}


def _pair_agreement(connection: Any, task: str, *, since: str | None = None) -> dict[str, Any]:
    """LLM vs Decider on the same pair (latest standing verdict of each).

    A Tier-1 Decider row that holds no answer (``FAILURE_VERDICTS``: the
    Decider was unavailable, refused or failing and the LLM decided) is not a
    verdict and is skipped.
    """

    failures = sorted(FAILURE_VERDICTS)
    latest: dict[tuple[str, str, str, str], dict[str, str]] = defaultdict(dict)
    for row in connection.execute(
        "SELECT left_kind, left_id, right_kind, right_id, judge, verdict FROM judgment_ledger j "
        "WHERE task = ? AND judge IN ('llm', 'decider') AND (? IS NULL OR created_at >= ?) "
        f"AND NOT (judge = 'decider' AND verdict IN ({', '.join('?' for _ in failures)})) "
        "AND NOT EXISTS (SELECT 1 FROM judgment_ledger s WHERE s.supersedes_id = j.id) "
        "ORDER BY created_at, rowid",
        (task, since, since, *failures),
    ):
        key = tuple(sorted([(str(row[0]), str(row[1])), (str(row[2]), str(row[3]))]))
        latest[key][str(row[4])] = str(row[5])  # type: ignore[index]
    both = [verdicts for verdicts in latest.values() if "llm" in verdicts and "decider" in verdicts]
    agree = sum(1 for verdicts in both if verdicts["llm"] == verdicts["decider"])
    matrix: Counter[str] = Counter(f"{verdicts['llm']}|{verdicts['decider']}" for verdicts in both)
    return {"pairs_judged_by_both": len(both), "agreement": _rate(agree, len(both)),
            "llm_by_decider": dict(sorted(matrix.items()))}


def _check_counts(rows: list[Any]) -> dict[str, Any]:
    passed = sum(1 for a in rows if a.status == "passed")
    failed = sum(1 for a in rows if a.status == "failed")
    return {"commitments": len(rows), "open": sum(1 for a in rows if a.is_open), "passed": passed,
            "failed": failed, "returned": sum(1 for a in rows if a.status == "returned"),
            "first_check_pass_rate": _rate(passed, passed + failed)}


def _first_checks(vault: LoadedVault, repository: Repository, gaps: list[dict[str, Any]]) -> dict[str, Any]:
    """The created prerequisites' light commitments and their delayed checks.

    Read whatever ``create_prerequisites_enabled`` says now (the outcome of a
    creation does not stop existing when creation is switched off), only for
    the readings in the report's window, overall and per chooser.
    """

    from learnloop.placement.state import (
        LEARNER_TEXT_GAP_SOURCE,
        diagnosis_can_arrive,
        load_placement_state_from_connection,
        placement_active,
    )

    with repository.connection() as connection:
        state = load_placement_state_from_connection(
            connection, active=placement_active(vault), diagnosis_live=diagnosis_can_arrive(vault),
            now_iso=utc_now_iso(), gap_commitments=True,
        )
    by_gap = {str(row["id"]): row for row in gaps}
    rows = [a for a in state.assumptions if a.source == LEARNER_TEXT_GAP_SOURCE and str(a.trigger_ref) in by_gap]
    per_chooser: dict[str, list[Any]] = defaultdict(list)
    for assumption in rows:
        gap = by_gap[str(assumption.trigger_ref)]
        per_chooser["decider" if gap["chooser"] == "decider" else str(gap["context_judge"])].append(assumption)
    return {**_check_counts(rows),
            "by_chooser": {key: _check_counts(value) for key, value in sorted(per_chooser.items())}}


def _card_taps(connection: Any, attempt_ids: set[str], *, since: str | None) -> int:
    """T1's diagnosis-card "not the same mistake" taps on these answers.

    A tap's ``left`` is the answer whose card was tapped, ``right`` the
    earlier answer the card cited: only a tap on one of these answers counts,
    never a tap on another answer that cites one (re-review F6).
    """

    if not attempt_ids:
        return 0
    taps = connection.execute(
        "SELECT left_id FROM judgment_ledger WHERE task = 'same_cause' AND judge = 'learner_card' "
        "AND left_kind = 'attempt' AND verdict = 'different' AND (? IS NULL OR created_at >= ?)",
        (since, since),
    ).fetchall()
    return sum(1 for (left,) in taps if str(left) in attempt_ids)


def build_report(vault: LoadedVault, repository: Repository, *, since: str | None = None) -> dict[str, Any]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.gaps(connection, since=since)
        reversal_rows = store.reversals(connection, [row["id"] for row in rows])
        agreement = {task: _pair_agreement(connection, task, since=since)
                     for task in (SAME_PREREQUISITE_TASK, SAME_BELIEF_TASK, NEEDED_TASK)}
        jobs = Counter(job["state"] for job in store.jobs(connection) if since is None or job["created_at"] >= since)
        belief_attempts = {
            str(row["attempt_id"]) for row in rows
            if row.get("attempt_id") and row["kind"] == "misconception"
            and row["action"] in ("belief_sighting", "belief_candidate", "belief_registry_path")
        }
        card_taps = _card_taps(connection, belief_attempts, since=since)
    reversed_by: dict[str, set[str]] = defaultdict(set)
    for reversal in reversal_rows:
        reversed_by[reversal["gap_id"]].add(reversal["reversal"])
    by_kind_chooser: dict[str, dict[str, Any]] = {}
    for row in rows:
        acting = "decider" if row["chooser"] == "decider" else str(row["context_judge"])
        key = f"{row['kind']}|{acting}"
        entry = by_kind_chooser.setdefault(key, Counter())
        entry["read"] += 1
        entry[row["action"]] += 1
        if row.get("edge_id"):
            entry["edges_added"] += 1
        undone = reversed_by.get(row["id"], set())
        if "undo_creation" in undone:
            entry["creations_undone"] += 1
        if "undo_edge" in undone:
            entry["edges_undone"] += 1
        if "not_this_belief" in undone:
            entry["not_this_belief_taps"] += 1
    beliefs = [row for row in rows if row["action"] in ("belief_sighting", "belief_candidate")]
    taps = sum(1 for row in beliefs if "not_this_belief" in reversed_by.get(row["id"], set()))
    created = [row for row in rows if row["action"] == "created_prerequisite"]
    undone_creations = sum(1 for row in created if "undo_creation" in reversed_by.get(row["id"], set()))
    both = [row for row in rows if row.get("context_kind") and row.get("decider_kind")]
    agree = sum(1 for row in both if row["context_kind"] == row["decider_kind"])
    kind_matrix: Counter[str] = Counter(f"{row['context_kind']}|{row['decider_kind']}" for row in both)
    disagreements = [row for row in both if row["context_kind"] != row["decider_kind"]]
    acted_undone = sum(1 for row in disagreements if reversed_by.get(row["id"]))
    return {
        "report_version": REPORT_VERSION,
        "since": since,
        "learner_texts": len(rows),
        "by_source": dict(Counter(row["source_kind"] for row in rows)),
        "by_kind_and_chooser": {key: dict(value) for key, value in sorted(by_kind_chooser.items())},
        "created_prerequisites": {
            "created": len(created), "undone": undone_creations,
            "undo_rate": _rate(undone_creations, len(created)),
            "seed_status": dict(Counter(str(row.get("seed_status")) for row in created)),
            **_first_checks(vault, repository, created),
        },
        "beliefs": {"noted": len(beliefs), "not_this_belief_taps": taps, "tap_rate": _rate(taps, len(beliefs)),
                    "new_candidates": sum(1 for row in beliefs if row["action"] == "belief_candidate"),
                    "card_not_same_mistake_taps": card_taps},
        "chooser": {
            "configured_now": vault.config.learner_text_gaps.chooser,
            "kind_agreement": _rate(agree, len(both)),
            "context_by_decider": dict(sorted(kind_matrix.items())),
            "disagreements": len(disagreements),
            "disagreements_later_reversed": acted_undone,
            "note": (
                "Only the authoritative chooser's reading is acted on, so outcomes measure that chooser. To "
                "compare outcomes, run each chooser for a period (learner_text_gaps.chooser) and compare the "
                "undo, first-check and tap rates per period; agreement is the cheap signal meanwhile."
            ),
        },
        "judges": agreement,
        "jobs": dict(jobs),
    }


def batch_review(repository: Repository, *, since: str | None = None) -> list[dict[str, Any]]:
    """Slip, wording and unmatched readings, with the learner's text (owner only)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.gaps(connection, since=since)
    return [
        {"gap_id": row["id"], "at": row["created_at"], "source": row["source_kind"], "kind": row["kind"],
         "action": row["action"], "named": row.get("named"), "learner_text": row["learner_text"],
         "reason": (row.get("detail") or {}).get("reason")}
        for row in rows
        if row["action"] in ("signal_only", "unmatched_prerequisite", "unnamed", "unplaced", "failed")
    ]


def plan_report(repository: Repository, *, since: str | None = None) -> dict[str, Any]:
    """The dry run: population sizes only, nothing written."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.gaps(connection, since=since)
        reversal_count = len(store.reversals(connection, [row["id"] for row in rows]))
    return {"dry_run": True, "learner_texts": len(rows), "reversals": reversal_count,
            "by_action": dict(Counter(row["action"] for row in rows)), "calls": 0}


def render_markdown(report: Mapping[str, Any], review: list[dict[str, Any]]) -> str:
    lines = [
        "# Learner-text gaps report", "",
        f"Report `{report['report_version']}`; {report['learner_texts']} learner texts read"
        + (f" since {report['since']}" if report.get("since") else "") + ".", "",
        "## By kind and chooser", "",
        "| kind / chooser | read | matched | created | beliefs noted | edges added | undone |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, entry in report["by_kind_and_chooser"].items():
        undone = entry.get("creations_undone", 0) + entry.get("edges_undone", 0) + entry.get("not_this_belief_taps", 0)
        lines.append(
            f"| {key} | {entry.get('read', 0)} | {entry.get('matched_prerequisite', 0)} | "
            f"{entry.get('created_prerequisite', 0)} | "
            f"{entry.get('belief_sighting', 0) + entry.get('belief_candidate', 0)} | "
            f"{entry.get('edges_added', 0)} | {undone} |"
        )
    created = report["created_prerequisites"]
    beliefs = report["beliefs"]
    chooser = report["chooser"]
    lines += [
        "", "## Created prerequisites", "",
        f"{created['created']} created, {created['undone']} undone; first checks: {created['passed']} passed, "
        f"{created['failed']} failed, {created['open']} open "
        f"(pass rate {created['first_check_pass_rate']['rate']}, Wilson 95% {created['first_check_pass_rate']['wilson95']}).",
        *[
            f"- {chooser_key}: {entry['passed']} passed, {entry['failed']} failed, {entry['open']} open "
            f"(pass rate {entry['first_check_pass_rate']['rate']}, Wilson 95% {entry['first_check_pass_rate']['wilson95']})"
            for chooser_key, entry in created.get("by_chooser", {}).items()
        ],
        "", "## Beliefs", "",
        f"{beliefs['noted']} noted ({beliefs['new_candidates']} new holding-pen candidates); "
        f"\"not what I meant\": {beliefs['not_this_belief_taps']} (rate {beliefs['tap_rate']['rate']}, "
        f"Wilson 95% {beliefs['tap_rate']['wilson95']}); diagnosis-card \"not the same mistake\" taps on "
        f"those answers: {beliefs['card_not_same_mistake_taps']}.",
        "", "## Decider or LLM", "",
        f"Kind agreement (context model vs Decider): {chooser['kind_agreement']['k']}/{chooser['kind_agreement']['n']} "
        f"(Wilson 95% {chooser['kind_agreement']['wilson95']}); disagreements later reversed: "
        f"{chooser['disagreements_later_reversed']}/{chooser['disagreements']}.", "",
        chooser["note"], "",
    ]
    for task, entry in report["judges"].items():
        lines.append(
            f"- `{task}`: {entry['pairs_judged_by_both']} pairs judged by both; agreement "
            f"{entry['agreement']['rate']} (Wilson 95% {entry['agreement']['wilson95']})."
        )
    lines += ["", "## Batch review (slip, wording, unmatched)", ""]
    if not review:
        lines.append("None.")
    for row in review:
        lines.append(f"- {row['at']} {row['source']} `{row['kind']}` {row['action']}"
                     f"{' (' + str(row['reason']) + ')' if row.get('reason') else ''}: {row['learner_text'][:300]!r}")
    return "\n".join(lines) + "\n"


def write_report(vault: LoadedVault, repository: Repository, out: Path, *, since: str | None = None) -> dict[str, Any]:
    report = build_report(vault, repository, since=since)
    out.write_text(render_markdown(report, batch_review(repository, since=since)), encoding="utf-8")
    return report


__all__ = ["REPORT_VERSION", "batch_review", "build_report", "plan_report", "render_markdown", "wilson",
           "write_report"]
