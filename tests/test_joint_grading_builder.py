"""The joint-grading builders (``tests/joint_grading_helpers.py``) keep writing what the joint doors wrote.

While the diagnosis split's kill switch existed, each builder was compared with
the door it stands for, on the same answers in two vaults built alike (every
table, row by row in insertion order, ids, timestamps and digests tokenized):
equal. The doors are gone; this golden of the builders' grading-record rows
keeps the builders from drifting.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from learnloop.attempts.ai_contracts import GradingProposal, StuckGradingProposal
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository

from tests.diagnosis_split_helpers import at
from tests.joint_grading_helpers import write_joint_graded_attempt, write_joint_regrade
from tests.split_live_helpers import split_vault

GOLDEN = Path(__file__).parent / "goldens" / "joint_grading_builder.json"

_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
_STAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
_DIGEST = re.compile(r"(?<![0-9a-f])[0-9a-f]{20,64}(?![0-9a-f])")


def _wrong(context) -> GradingProposal:
    criteria = context.rubric["criteria"]
    return GradingProposal.model_validate(
        {
            "diagnosis_md": "The right factor is missing.",
            "attempt_id": context.attempt_id,
            "practice_item_id": context.practice_item_id,
            "criterion_evidence": [
                {"criterion_id": c["id"], "points_awarded": 0.0, "evidence": "absent"} for c in criteria
            ],
            "rubric_score": 0,
            "fatal_errors": [],
            "error_attributions": [
                {
                    "error_type": "conceptual_slip",
                    "severity": 0.7,
                    "evidence": "V is not transposed.",
                    "is_misconception": True,
                    "misconception_statement": "The learner thinks V needs no transpose.",
                    "target_criterion_ids": [criteria[-1]["id"]],
                    "resolution_status": "unresolved",
                    "cause_scope": "learner_state",
                    "first_divergence": {"anchor_kind": "whole_answer", "criterion_id": criteria[-1]["id"]},
                    "candidate_causes": [
                        {"statement": "The learner thinks V needs no transpose.", "cause_scope": "learner_state"}
                    ],
                }
            ],
            "grader_confidence": 0.8,
        }
    )


def _right(context) -> GradingProposal:
    criteria = context.rubric["criteria"]
    return GradingProposal.model_validate(
        {
            "diagnosis_md": "Correct.",
            "attempt_id": context.attempt_id,
            "practice_item_id": context.practice_item_id,
            "criterion_evidence": [
                {"criterion_id": c["id"], "points_awarded": float(c["points"]), "evidence": "present"}
                for c in criteria
            ],
            "rubric_score": int(sum(c["points"] for c in criteria)),
            "grader_confidence": 0.9,
        }
    )


def _stuck(context) -> StuckGradingProposal:
    return StuckGradingProposal.model_validate(
        {
            **_wrong(context).model_dump(mode="json"),
            "stuck_reading": {
                "attempts_answer": False,
                "describes_confusion": True,
                "confusion_quote": "where Sigma comes from",
            },
        }
    )


#: (item, answer, declared stuck, proposal), graded in order in one vault.
ANSWERS = (
    ("pi_svd_compute_001", "A = U Sigma V wrong", False, _wrong),
    ("pi_svd_compute_002", "B = U Sigma V nope", False, _wrong),
    ("pi_svd_compute_001", "I can't see where Sigma comes from", True, _stuck),
    ("pi_transpose_001", "M^T", False, _right),
)


def _draft(item_id, answer, stuck, minute):
    return AttemptDraft(
        practice_item_id=item_id, learner_answer_md=answer, attempt_type="independent_attempt",
        declared_stuck=stuck, session_id="s1", submission_id=f"sub-{minute}",
    )


def _history(tmp_path, write, *, pipeline=True):
    """Grade ANSWERS jointly, then regrade jointly a self-graded answer, the
    first joint one and the stuck one; ``write`` is the builders."""

    _paths, vault, repository = split_vault(tmp_path)
    attempt_ids = []
    for minute, (item_id, answer, stuck, proposal) in enumerate(ANSWERS):
        clock = FrozenClock(at(20 + minute))
        result = write["grade"](vault, repository, _draft(item_id, answer, stuck, minute), proposal, clock)
        if pipeline:
            run_post_attempt_pipeline(vault, repository, result=result, session_id="s1", clock=clock)
        attempt_ids.append(result.attempt_id)
    selfgraded = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_compute_002", learner_answer_md="B = U Sigma V^T", session_id="s1"),
        SelfGradeInput(criterion_points={"setup": 1, "result": 0}, confidence=3),
        fallback_reason="provider_timeout", clock=FrozenClock(at(30)),
    )
    write["regrade"](vault, repository, selfgraded.attempt_id, _right, FrozenClock(at(31)))
    write["regrade"](vault, repository, attempt_ids[0], _right, FrozenClock(at(32)))
    write["regrade"](vault, repository, attempt_ids[2], _stuck, FrozenClock(at(33)))
    return repository


BUILDERS = {
    "grade": lambda vault, repository, draft, proposal, clock: write_joint_graded_attempt(
        vault, repository, draft, proposal, clock=clock,
    ),
    "regrade": lambda vault, repository, attempt_id, proposal, clock: write_joint_regrade(
        vault, repository, attempt_id, proposal, clock=clock,
    ),
}


def _tables(repository: Repository) -> dict[str, list[list]]:
    """Every table's rows in insertion order, tokenized (see the module docstring)."""

    tokens: dict[str, str] = {}
    counts: dict[str, int] = {}

    def token(kind: str, match: re.Match) -> str:
        if match.group(0) not in tokens:
            counts[kind] = counts.get(kind, 0) + 1
            tokens[match.group(0)] = f"<{kind}{counts[kind]}>"
        return tokens[match.group(0)]

    def norm(value):
        if isinstance(value, bytes):
            value = value.hex()
        if not isinstance(value, str):
            return value
        value = _ULID.sub(lambda m: token("id", m), value)
        value = _UUID.sub(lambda m: token("id", m), value)
        value = _STAMP.sub(lambda m: token("at", m), value)
        return _DIGEST.sub(lambda m: token("hex", m), value)

    out: dict[str, list[list]] = {}
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        names = [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for name in names:
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{name}")')]
            order = "rowid" if connection.execute(
                "SELECT sql FROM sqlite_master WHERE name = ?", (name,)
            ).fetchone()[0].upper().find("WITHOUT ROWID") < 0 else ", ".join(f'"{c}"' for c in columns)
            rows = connection.execute(f'SELECT * FROM "{name}" ORDER BY {order}').fetchall()
            if rows:
                out[name] = [[norm(value) for value in row] for row in rows]
    return out


#: What the golden pins: the grading record the builders write (the attempt's
#: application and everything the pipeline derives are the code under test's).
GOLDEN_TABLES = (
    "agent_runs", "practice_attempts", "grading_evidence", "raw_grade_events", "attempt_feedback_metadata",
    "diagnostic_augmentation_receipts", "judgment_ledger", "text_write_provenance", "content_events",
)


def _builder_rows(tmp_path) -> dict[str, list[list]]:
    """The grading-record rows the builders add (the seeded history's aside)."""

    _paths, _vault, repository = split_vault(tmp_path / "seed")
    before = _tables(repository)
    built = _tables(_history(tmp_path / "built", BUILDERS, pipeline=False))
    return {name: built.get(name, [])[len(before.get(name, [])):] for name in GOLDEN_TABLES}


def test_the_builders_rows_match_their_golden(tmp_path):
    """``LEARNLOOP_WRITE_GOLDEN=1`` rewrites it (a deliberate change to what a builder writes)."""

    rows = json.loads(json.dumps(_builder_rows(tmp_path)))
    if os.environ.get("LEARNLOOP_WRITE_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(rows, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    assert rows == json.loads(GOLDEN.read_text(encoding="utf-8"))
