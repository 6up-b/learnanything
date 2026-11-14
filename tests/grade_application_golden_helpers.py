"""One graded history that reaches every kind of grade application, for ``tests/test_grade_application_golden.py``.

A split vault at the head (``tests/split_live_helpers.py``: SVD items with a seeded history), then, a day apart, on
``pi_svd_compute_001`` (``setup`` 2 + ``result`` 2) unless named: a self-graded independent answer; a model grade with
an error attribution aimed at the passed criterion (the firewall strips it) and one aimed at the failed one; a hinted
answer; a primed one; "I don't know"; a stuck answer; a model grade with one criterion unverified (unassessed); a
model grade held for review; a repeat on the same item and one on its sibling (same surface group, so familiarity
discounts them); an answer through the real blind-grading door with the deterministic fake; a regrade of the model
grade; and an adjudication's correction of the first answer. Everything is synthetic.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import math
import re
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
    calculate_rubric_score,
)
from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
from learnloop.attempts.grading import resolved_rubric
from learnloop.clock import FrozenClock

from tests.diagnosis_fakes import ReviewFakeClient
from tests.regrade_contract_replay_helpers import PointsGrader, _regrade
from tests.split_live_helpers import split_vault, submit

T = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
ITEM = "pi_svd_compute_001"
SIBLING = "pi_svd_compute_002"

_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_HEAD_TAG = re.compile(re.escape(LATEST_ALGORITHM_VERSION) + r"(?![0-9.])")
#: FTS shadow tables hold binary segments no attempt reads.
_SKIPPED_TABLE = re.compile(r"_(data|idx|content|docsize|config)$")


def _day(n: float) -> datetime:
    return T + timedelta(days=n)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _apply(vault, repository, points, *, attempt_id, when, item=ITEM, source="self", draft=None, grade=None,
           apply=None):
    rubric = resolved_rubric(vault, vault.practice_items[item])
    grade_fields = {
        "rubric_score": calculate_rubric_score(rubric, dict(points), []),
        "criterion_points": dict(points),
        "evidence_rows": [
            {
                "id": f"ge_{attempt_id}_{cid}", "criterion_id": cid, "points_awarded": float(value),
                "evidence": source, "notes": None, "local_grader_id": "test",
                "grader_tier": 1 if source == "self" else 3, "created_at": _iso(when),
            }
            for cid, value in points.items()
        ],
        "error_attributions": [],
        "grader_confidence": 1.0 if source == "self" else 0.85,
        "confidence": 3,
        "manual_review_reason": None,
        "feedback_md": "graded",
        **(grade or {}),
    }
    draft_fields = {"practice_item_id": item, "learner_answer_md": "U Sigma V^T from A^T A",
                    "attempt_type": "independent_attempt", **(draft or {})}
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(**draft_fields), attempt_id=attempt_id, grade=ResolvedGrade(**grade_fields),
            grading_source=source, **(apply or {}),
        ),
        clock=FrozenClock(when),
    )


def _attribution(error_type: str, **fields) -> GradeAttribution:
    return GradeAttribution(error_type=error_type, severity=0.6, evidence="Sigma V without the transpose", **fields)


def build_graded_vault(root: Path):
    """``(paths, vault, repository)`` after the setup, before the history this golden pins."""

    return split_vault(root, version=LATEST_ALGORITHM_VERSION)


def play_history(vault, repository) -> dict[str, str]:
    """The graded history, live. Returns each answer's attempt id by label."""

    error_type = "conceptual_slip" if "conceptual_slip" in vault.error_types else sorted(vault.error_types)[0]
    allowed = vault.practice_items[ITEM].attempt_types_allowed
    hinted_type = "hinted_attempt" if not allowed or "hinted_attempt" in allowed else "independent_attempt"
    ids = {}
    _apply(vault, repository, {"setup": 2, "result": 1}, attempt_id="att_i1_self", when=_day(1))
    ids["self"] = "att_i1_self"
    _apply(
        vault, repository, {"setup": 2, "result": 0}, attempt_id="att_i1_model", when=_day(2), source="ai",
        grade={"error_attributions": [
            _attribution(error_type, target_criterion_ids=["setup"], resolution_status="resolved"),
            _attribution(error_type, target_criterion_ids=["result"], resolution_status="resolved",
                         is_misconception=True, misconception_statement="V is not transposed"),
        ]},
        apply={"grader_identity": ("blind-test", "BlindGradingProposal")},
    )
    ids["model"] = "att_i1_model"
    _apply(vault, repository, {"setup": 1, "result": 1}, attempt_id="att_i1_hinted", when=_day(3),
           draft={"attempt_type": hinted_type, "hints_used": 1})
    ids["hinted"] = "att_i1_hinted"
    _apply(vault, repository, {"setup": 2, "result": 2}, attempt_id="att_i1_primed", when=_day(4),
           draft={"primed": True})
    ids["primed"] = "att_i1_primed"
    _apply(vault, repository, {"setup": 0, "result": 0}, attempt_id="att_i1_dont_know", when=_day(5),
           draft={"attempt_type": "dont_know", "learner_answer_md": ""},
           grade={"error_attributions": [_attribution("retrieval_failure")]})
    ids["dont_know"] = "att_i1_dont_know"
    _apply(vault, repository, {"setup": 1, "result": 0}, attempt_id="att_i1_stuck", when=_day(6),
           draft={"declared_stuck": True, "learner_answer_md": "I wrote A^T A and stopped."})
    ids["stuck"] = "att_i1_stuck"
    _apply(vault, repository, {"setup": 2, "result": 0}, attempt_id="att_i1_unassessed", when=_day(7), source="ai",
           apply={"unverified_criterion_ids": ("result",)})
    ids["unassessed"] = "att_i1_unassessed"
    _apply(vault, repository, {"setup": 0, "result": 0}, attempt_id="att_i1_held", when=_day(8), source="ai",
           grade={"error_attributions": [_attribution(error_type, target_criterion_ids=["result"])]},
           apply={"grade_held_for_review": True, "unverified_criterion_ids": ("setup", "result")})
    ids["held"] = "att_i1_held"
    _apply(vault, repository, {"setup": 2, "result": 2}, attempt_id="att_i1_repeat", when=_day(9))
    ids["repeat"] = "att_i1_repeat"
    _apply(vault, repository, {"setup": 2, "result": 1}, attempt_id="att_i1_sibling", when=_day(9.5), item=SIBLING)
    ids["sibling"] = "att_i1_sibling"
    ids["door"] = submit(vault, repository, ReviewFakeClient(), answer="A = U Sigma V wrong", when=_day(10)).attempt_id
    _regrade(vault, repository, "att_i1_model", {"setup": 2, "result": 1}, when=_day(11))
    revision = append_adjudication_evidence_revision(
        repository, attempt_id="att_i1_self", resolved_fraction=0.5, adjudication_id="adj_i1",
        adjudicator_source="human_owner", rationale="half", vault=vault, clock=FrozenClock(_day(12)),
    )
    assert revision["status"] == "revised", revision
    return ids


REBUILD_CLOCK = FrozenClock(_day(13))


# -- what a record holds ---------------------------------------------------------------------------


def plain(value: Any) -> Any:
    """A JSON value holding every field of ``value``; floats keep every bit (JSON writes ``repr``)."""

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {"__type__": type(value).__name__,
                **{f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}}
    if hasattr(value, "model_dump") and not isinstance(value, type):
        return {"__type__": type(value).__name__, **plain(value.model_dump(mode="python"))}
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((plain(item) for item in value), key=repr)
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return f"{type(value).__name__}.{value.name}"
    if isinstance(value, bytes):
        return value.hex()
    return repr(value)


def table_rows(sqlite_path: Path) -> dict[str, list[str]]:
    """Every table's rows as canonical JSON lines, sorted (a multiset per table)."""

    connection = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        tables = [
            name for (name,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if not _SKIPPED_TABLE.search(name)
        ]
        out: dict[str, list[str]] = {}
        for table in tables:
            cursor = connection.execute(f'SELECT * FROM "{table}"')
            columns = [column[0] for column in cursor.description]
            out[table] = sorted(
                json.dumps(dict(zip(columns, (plain(cell) for cell in row), strict=True)), sort_keys=True)
                for row in cursor
            )
        return out
    finally:
        connection.close()


def row_delta(before: dict[str, list[str]], after: dict[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    """Rows added and removed, table by table (a changed row is one of each)."""

    delta: dict[str, dict[str, list[str]]] = {}
    for table in sorted(set(before) | set(after)):
        old, new = before.get(table, []), after.get(table, [])
        old_counts: dict[str, int] = {}
        for row in old:
            old_counts[row] = old_counts.get(row, 0) + 1
        added = []
        for row in new:
            if old_counts.get(row, 0):
                old_counts[row] -= 1
            else:
                added.append(row)
        removed = [row for row, count in old_counts.items() for _ in range(count)]
        if added or removed:
            delta[table] = {"added": sorted(added), "removed": sorted(removed)}
    return delta


class Normalizer:
    """ULIDs to ``<ulid:n>`` and random UUIDs to ``<uuid:n>`` in order of first appearance, wall-clock stamps to
    ``<wall>``, the head tag to ``<head tag>``. The history's own stamps (May and June 2026) stay."""

    def __init__(self) -> None:
        self.seen: dict[str, str] = {}

    @staticmethod
    def _stamp(text: str) -> str:
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
        except ValueError:
            return text
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return "<wall>" if abs((moment - datetime.now(UTC)).total_seconds()) < 3 * 86400 else text

    def __call__(self, text: str) -> str:
        def one(match: re.Match[str]) -> str:
            return self.seen.setdefault(match.group(0), f"<ulid:{len(self.seen)}>")

        def random_id(match: re.Match[str]) -> str:
            return self.seen.setdefault(match.group(0), f"<uuid:{len(self.seen)}>")

        text = _HEAD_TAG.sub("<head tag>", _STAMP.sub(lambda match: self._stamp(match.group(0)), text))
        return _UUID.sub(random_id, _ULID.sub(one, text))


__all__ = [
    "ITEM", "REBUILD_CLOCK", "SIBLING", "Normalizer", "PointsGrader", "build_graded_vault", "plain",
    "play_history", "row_delta", "table_rows",
]
