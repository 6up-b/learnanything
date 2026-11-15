"""A rebuild replays history; it must not grow it (refactor bug ledger D-36).

Replay re-applies every recorded practice attempt, and each application
re-mints the attempt's grade channel (``attempts._dual_write_grade_channel``):
one more ``activity_observations`` row, ``raw_grade_events`` row and
``grade_interpretations`` row and four ``measurement_events`` per graded
answer, at every rebuild. Those four tables are history (``RAW_LEDGER``): a
vault rebuilt N times holds N+1 copies of each answer's chain. The projection
reads only each attempt's newest observation, so belief is equal after every
rebuild, but two readers are not:

- the review queue (``Repository.pending_grade_reviews``) lists every flagged
  head of every copy, one row per rebuild;
- an owner adjudication sits on the observation it was made on, and the next
  rebuild's fresh observation (unadjudicated) becomes the one the projection
  reads, so the adjudication's evidence is gone after one rebuild.

Each test is a strict xfail until the fix handed back with D-36 lands.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.grade_resolution import append_adjudication
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.stores.observation_ledger import load_authoritative_observation_ledger
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.helpers import NOW
from tests.rebuild_equivalence_helpers import _answer, _vault

D36 = pytest.mark.xfail(
    strict=True,
    reason="D-36: replay re-mints each practice answer's grade channel at every rebuild (fix handed back)",
)
CLOCK = FrozenClock(NOW + timedelta(days=30))
#: A short head-written history: graded answers on several items.
HISTORY = (
    ("pi_svd_define_001", 4.0), ("pi_svd_define_001", 1.0), ("pi_diag_easy", 3.0),
    ("pi_diag_mid", 0.0), ("pi_eig_easy", 2.0),
)


def _history(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    for index, (item, points) in enumerate(HISTORY):
        _answer(vault, repository, item, minutes=10 + 60 * index, points=points)
    return vault, repository


def _raw_ledgers(repository) -> dict[str, Counter]:
    """Every history table as a multiset of rows, surrogate ids and stamps left out
    (a repeat of a row is a second element, not the same one)."""

    out: dict[str, Counter] = {}
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table in sorted(tables_for_role(TableRole.RAW_LEDGER)):
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            if not columns:
                continue
            kept = [c for c in columns if c != "id" and not c.endswith("_id") and c not in {"created_at", "updated_at"}]
            if not kept:
                kept = columns
            selected = ", ".join(f'"{c}"' for c in kept)
            out[table] = Counter(tuple(row) for row in connection.execute(f'SELECT {selected} FROM "{table}"'))
    return out


@D36
def test_a_second_rebuild_appends_no_history_row(tmp_path):
    vault, repository = _history(tmp_path)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    once = _raw_ledgers(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    twice = _raw_ledgers(repository)
    grown = {table: sum(twice[table].values()) - sum(once[table].values()) for table in once if twice[table] != once[table]}
    assert grown == {}


@D36
def test_the_review_queue_lists_a_flagged_grade_once_after_rebuilds(tmp_path):
    vault, repository = _history(tmp_path)
    # A self-grade at confidence 1 is flagged for review (grader confidence below 0.4).
    draft = AttemptDraft(practice_item_id="pi_diag_hard", learner_answer_md="Not sure.", attempt_type="independent_attempt")
    complete_self_graded_attempt(
        vault, repository, draft, SelfGradeInput(criterion_points={"correctness": 2.0}, confidence=1),
        clock=FrozenClock(NOW + timedelta(days=1)),
    )
    assert len(repository.pending_grade_reviews()) == 1
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert len(repository.pending_grade_reviews()) == 1


def _ledger_entry(repository, attempt_id: str) -> dict:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return next(e for e in load_authoritative_observation_ledger(connection) if e["attempt_id"] == attempt_id)


def _facet_values(repository) -> list[str]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        connection.row_factory = None
        columns = [row[1] for row in connection.execute("PRAGMA table_info(facet_capability_evidence)")]
        kept = [c for c in columns if c not in {"created_at", "updated_at"}]
        rows = connection.execute(f"SELECT {', '.join(kept)} FROM facet_capability_evidence").fetchall()
    return sorted(json.dumps(dict(zip(kept, row, strict=True)), sort_keys=True, default=str) for row in rows)


@D36
def test_an_adjudication_survives_a_rebuild(tmp_path):
    vault, repository = _history(tmp_path)
    attempt = next(a for a in repository.list_all_attempts() if a["practice_item_id"] == "pi_diag_easy")
    observation = repository.observation_by_attempt(str(attempt["id"]))
    head = repository.active_interpretation_for_observation(str(observation["id"]))
    with repository.atomic():
        project_canonical_facet_state(vault, repository, clock=CLOCK)
    unadjudicated = _facet_values(repository)
    # The owner confirms the grader's leading class: no direction flip, so no
    # grading_evidence revision; only the interpretation's authority changes.
    append_adjudication(
        repository,
        observation_id=str(observation["id"]),
        administration_id=str(observation["administration_id"]),
        reviewed_raw_event_ids=[str(head["raw_grade_event_id"])],
        adjudicator_source="human_owner",
        resolved_class="partial_success",
        vault=vault,
        clock=CLOCK,
    )
    with repository.atomic():
        project_canonical_facet_state(vault, repository, clock=CLOCK)
    adjudicated = _facet_values(repository)
    assert adjudicated != unadjudicated
    assert _ledger_entry(repository, str(attempt["id"]))["active_adjudication"] is not None

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _ledger_entry(repository, str(attempt["id"]))["active_adjudication"] is not None
    assert _facet_values(repository) == adjudicated

