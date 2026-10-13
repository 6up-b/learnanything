"""Usage signals on find_practice proposals, logged now for later evaluation.

Two sources, both appended to ``judgment_ledger`` (task ``practice_usage``):

* **learner taps** (judge ``learner_card``): a consumer that shows proposals
  records ``practised``, ``skipped``, ``too_easy`` or ``not_what_i_asked``;
* **the attempt join** (judge ``exact_key``): a proposed item attempted within
  ``practice_index.usage_window_hours`` of the proposal is ``practised``.

Usage signals evaluate retrieval; they are never evidence about the learner
and never change what the scheduler serves.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from datetime import timedelta
import json
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.practice_index import (
    attempts_after,
    judgments_by_ids,
    judgments_for_task,
    proposal,
    proposals,
)


USAGE_TASK = "practice_usage"
LEARNER_SIGNALS = ("practised", "skipped", "too_easy", "not_what_i_asked")
JOIN_PROMPT_VERSION = "practice_usage_join.v1"


#: Characters of the learner's own words kept on a tap's rationale.
LEARNER_TEXT_CHARS = 2000


def record_practice_usage(repository: Repository, *, proposal_id: str, practice_item_id: str,
                          signal: str, clock: Clock | None = None,
                          text: str | None = None) -> dict[str, Any]:
    """Append one learner tap on a proposed item. Repeating a tap is a no-op.

    ``text`` is the learner's optional words with the tap ("not what I asked:
    I wanted proofs, not computations"); learner text over skip buttons. It is
    kept on the verdict's rationale for a later learner-text adapter."""
    if signal not in LEARNER_SIGNALS:
        raise ValueError(f"signal must be one of {', '.join(LEARNER_SIGNALS)}")
    with repository.connection() as connection:
        found = proposal(connection, proposal_id)
        if found is None:
            raise ValueError("Unknown proposal")
        proposed = {entry["practice_item_id"] for entry in found["proposed"]}
        if practice_item_id not in proposed:
            raise ValueError("That item was not proposed by this proposal")
        judgment_id = "pus_" + content_key([proposal_id, practice_item_id, signal])[:40]
        if not judgments_by_ids(connection, [judgment_id]):
            append_judgment(
                connection, id=judgment_id, task=USAGE_TASK,
                left_kind="practice_proposal", left_id=proposal_id,
                right_kind="practice_item", right_id=practice_item_id,
                judge="learner_card", input_hash=content_key([proposal_id, practice_item_id]),
                verdict=signal, rationale=_tap_rationale(text),
                created_at=utc_now_iso(clock),
            )
    return {"judgment_id": judgment_id, "proposal_id": proposal_id,
            "practice_item_id": practice_item_id, "signal": signal}


def _tap_rationale(text: str | None) -> str:
    words = " ".join((text or "").split())[:LEARNER_TEXT_CHARS]
    if not words:
        return "learner tap on a find_practice proposal"
    return json.dumps({"text": "learner tap on a find_practice proposal", "learner_text": words},
                      ensure_ascii=False, sort_keys=True)


def sweep_practice_usage(repository: Repository, *, window_hours: int,
                         clock: Clock | None = None) -> dict[str, Any]:
    """Append ``practised`` for proposed items attempted within the window. Idempotent."""
    now = (clock or SystemClock()).now()
    added = 0
    with repository.connection() as connection:
        for row in proposals(connection):
            created = parse_utc(row["created_at"])
            if created is None:
                continue
            until = min(now, created + timedelta(hours=window_hours))
            items = [entry["practice_item_id"] for entry in row["proposed"]]
            attempts = attempts_after(
                connection, practice_item_ids=items, since=row["created_at"],
                until=until.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            )
            first: dict[str, dict[str, Any]] = {}
            for attempt in attempts:
                first.setdefault(attempt["practice_item_id"], attempt)
            for item_id, attempt in sorted(first.items()):
                judgment_id = "puj_" + content_key([row["id"], item_id])[:40]
                if judgments_by_ids(connection, [judgment_id]):
                    continue
                append_judgment(
                    connection, id=judgment_id, task=USAGE_TASK,
                    left_kind="practice_proposal", left_id=row["id"],
                    right_kind="practice_item", right_id=item_id, judge="exact_key",
                    prompt_version=JOIN_PROMPT_VERSION,
                    input_hash=content_key([row["id"], item_id, attempt["id"]]),
                    verdict="practised",
                    rationale=f"attempt {attempt['id']} within {window_hours}h of the proposal",
                    created_at=utc_now_iso(clock),
                )
                added += 1
    return {"added": added, "window_hours": window_hours}


def usage_summary(repository: Repository) -> dict[str, Any]:
    """Aggregate counts by retrieval path, signal and judge; no learner text."""
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = proposals(connection)
        signals = judgments_for_task(connection, USAGE_TASK)
    path_of = {row["id"]: row["path"] for row in rows}
    proposed_by_path: Counter[str] = Counter()
    for row in rows:
        proposed_by_path[row["path"]] += len(row["proposed"])
    by_path: dict[str, Counter[str]] = defaultdict(Counter)
    for signal in signals:
        path = path_of.get(signal["left_id"], "unknown")
        by_path[path][f"{signal['judge']}:{signal['verdict']}"] += 1
    return {
        "proposals": len(rows),
        "proposals_by_path": dict(Counter(row["path"] for row in rows)),
        "proposed_items_by_path": dict(proposed_by_path),
        "reranked": sum(1 for row in rows if row["reranked"]),
        "signals_by_path": {path: dict(counts) for path, counts in sorted(by_path.items())},
    }


__all__ = [
    "LEARNER_SIGNALS",
    "USAGE_TASK",
    "record_practice_usage",
    "sweep_practice_usage",
    "usage_summary",
]
