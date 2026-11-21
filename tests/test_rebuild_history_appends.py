"""A rebuild replays history; it must not grow it (refactor bug ledger D-36, D-52, D-53).

Replay re-applies every recorded practice attempt. Before the grade channel
fixes (mvp-0.60; no kill switch) each application re-minted the
attempt's grade channel: one more ``activity_observations`` row,
``raw_grade_events`` row and ``grade_interpretations`` row and four
``measurement_events`` per graded answer, at every rebuild. Those four tables
are history (``RAW_LEDGER``): a vault rebuilt N times held N+1 copies of each
answer's chain. The projection reads only each attempt's newest observation,
so belief was equal after every rebuild, but two readers were not:

- the review queue (``Repository.pending_grade_reviews``) listed every flagged
  head of every copy, one row per rebuild;
- an owner adjudication sits on the observation it was made on, and the next
  rebuild's fresh observation (unadjudicated) became the one the projection
  read, so the adjudication's evidence was gone after one rebuild.

With the fixes replay keeps the observation and appends only what changed (a
regrade's grade, a re-reading under another calibration or projection version),
never over a head a review wrote unless the grade changed. Below the tag (the
floor mvp-0.58 and mvp-0.59), a rebuild re-mints the chain exactly as before; the readers
read each attempt's newest observation either way, so a vault already rebuilt
that way lists a flagged grade once.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
)
from learnloop.attempts import grade_resolution
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.grade_resolution import append_adjudication, flag_observation_for_review
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.stores.observation_ledger import load_authoritative_observation_ledger
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.held_grade_evidence_helpers import T, _graded_apply
from tests.helpers import NOW
from tests.rebuild_equivalence_helpers import _answer, _vault
from tests.regrade_contract_replay_helpers import _regrade
from tests.route_rules_in_grader_helpers import ITEM
from tests.split_live_helpers import split_vault

CLOCK = FrozenClock(NOW + timedelta(days=30))
#: The tag just below the fixes: a vault there rebuilds as the predecessor does.
BELOW = FACET_BELIEF_FIX_ALGORITHM_VERSION
GRADE_CHANNEL = ("activity_observations", "raw_grade_events", "grade_interpretations", "measurement_events")
REVIEWED_CHANNEL = (*GRADE_CHANNEL, "grade_adjudications")
#: A short head-written history: graded answers on several items.
HISTORY = (
    ("pi_svd_define_001", 4.0), ("pi_svd_define_001", 1.0), ("pi_diag_easy", 3.0),
    ("pi_diag_mid", 0.0), ("pi_eig_easy", 2.0),
)
#: One rebuild's re-minted chains for HISTORY: an observation, a raw event and an
#: interpretation per answer, and four measurement events each.
ONE_CHAIN_PER_ANSWER = {
    "activity_observations": 5, "grade_interpretations": 5, "measurement_events": 20, "raw_grade_events": 5,
}


def _history(tmp_path, *, version: str = LATEST_ALGORITHM_VERSION):
    _paths, vault, repository = _vault(tmp_path, version=version)
    for index, (item, points) in enumerate(HISTORY):
        _answer(vault, repository, item, minutes=10 + 60 * index, points=points)
    return vault, repository


def _raw_ledgers(repository, tables=None) -> dict[str, Counter]:
    """Every history table (or those named) as a multiset of rows, surrogate ids
    and stamps left out (a repeat of a row is a second element, not the same one).

    A vault's first rebuild also backfills the activity cards and surfaces of
    the items nobody has answered yet: a test that starts from live writes
    names the grade channel's tables."""

    out: dict[str, Counter] = {}
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table in sorted(tables or tables_for_role(TableRole.RAW_LEDGER)):
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            if not columns:
                continue
            kept = [c for c in columns if c != "id" and not c.endswith("_id") and c not in {"created_at", "updated_at"}]
            if not kept:
                kept = columns
            selected = ", ".join(f'"{c}"' for c in kept)
            out[table] = Counter(tuple(row) for row in connection.execute(f'SELECT {selected} FROM "{table}"'))
    return out


def _grown(before: dict[str, Counter], after: dict[str, Counter]) -> dict[str, int]:
    return {
        table: sum(after[table].values()) - sum(before[table].values())
        for table in after
        if after[table] != before.get(table, Counter())
    }


def _channel_counts(repository, attempt_id: str) -> dict[str, int]:
    """The attempt's grade-channel rows (measurement events through its observations)."""

    with connect(repository.sqlite_path, read_only=True) as connection:
        counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE attempt_id = ?", (attempt_id,)).fetchone()[0])
            for table in ("activity_observations", "raw_grade_events")
        }
        for table in ("grade_interpretations", "measurement_events"):
            counts[table] = int(connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE observation_id IN "
                "(SELECT id FROM activity_observations WHERE attempt_id = ?)",
                (attempt_id,),
            ).fetchone()[0])
    return counts


def test_a_second_rebuild_appends_no_history_row(tmp_path):
    vault, repository = _history(tmp_path)
    learning_object_id = next(iter(vault.learning_objects))
    locked_set = repository.insert_hypothesis_set(
        learning_object_id=learning_object_id, probe_phase_id=None, hypotheses=[{"id": "h1"}],
        prior={"h1": 1.0}, algorithm_version=vault.config.algorithms.algorithm_version, clock=CLOCK,
    )
    saved = repository.fetch_hypothesis_set(locked_set)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.fetch_hypothesis_set(locked_set) == saved
    once = _raw_ledgers(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _grown(once, _raw_ledgers(repository)) == {}


def test_the_first_rebuild_of_a_vault_written_at_the_head_appends_no_grade_channel_row(tmp_path):
    vault, repository = _history(tmp_path)
    live = _raw_ledgers(repository, GRADE_CHANNEL)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _grown(live, _raw_ledgers(repository, GRADE_CHANNEL)) == {}


@pytest.mark.parametrize("version", [FIGURE_WAIT_ALGORITHM_VERSION, BELOW])
def test_below_the_tag_every_rebuild_re_mints_each_answers_chain(tmp_path, version):
    # The floor and mvp-0.59: the vaults that exist below the tag.
    vault, repository = _history(tmp_path, version=version)
    live = _raw_ledgers(repository, GRADE_CHANNEL)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    once = _raw_ledgers(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _grown(live, {table: once[table] for table in GRADE_CHANNEL}) == ONE_CHAIN_PER_ANSWER
    assert _grown(once, _raw_ledgers(repository)) == ONE_CHAIN_PER_ANSWER


def _flag_a_low_confidence_self_grade(vault, repository) -> str:
    # A self-grade at confidence 1 is flagged for review (grader confidence below 0.4).
    draft = AttemptDraft(practice_item_id="pi_diag_hard", learner_answer_md="Not sure.", attempt_type="independent_attempt")
    result = complete_self_graded_attempt(
        vault, repository, draft, SelfGradeInput(criterion_points={"correctness": 2.0}, confidence=1),
        clock=FrozenClock(NOW + timedelta(days=1)),
    )
    return str(result.attempt_id)


@pytest.mark.parametrize("version", [LATEST_ALGORITHM_VERSION, BELOW])
def test_the_review_queue_lists_a_flagged_grade_once_after_rebuilds(tmp_path, version):
    # Below the tag, every rebuild re-mints the flagged chain on a fresh
    # observation, as vaults rebuilt before the fixes hold it: the queue still
    # lists the grade once, on the copy the projection reads.
    grade_channel_fixes = version == LATEST_ALGORITHM_VERSION
    vault, repository = _history(tmp_path, version=version)
    attempt_id = _flag_a_low_confidence_self_grade(vault, repository)
    assert len(repository.pending_grade_reviews()) == 1
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _observation_count(repository, attempt_id) == (1 if grade_channel_fixes else 3)
    listed = repository.pending_grade_reviews()
    assert [row["observation_id_join"] for row in listed] == [
        _ledger_entry(repository, attempt_id)["active_interpretation"]["observation_id"]
    ]


def test_the_observation_of_an_attempt_is_the_newest_whatever_the_query_plan(tmp_path):
    # The contest flow, the grading receipt and the calibration streams flag or
    # read the observation this returns; the projection reads the newest. The
    # index that happens to return the newest first is dropped here.
    vault, repository = _history(tmp_path, version=BELOW)
    attempt_id = _flag_a_low_confidence_self_grade(vault, repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    newest = _ledger_entry(repository, attempt_id)["active_interpretation"]["observation_id"]
    with connect(repository.sqlite_path) as connection:
        connection.execute("DROP INDEX idx_activity_observations_attempt")
        connection.commit()
    assert repository.observation_by_attempt(attempt_id)["id"] == newest


def _observation_count(repository, attempt_id: str) -> int:
    return _channel_counts(repository, attempt_id)["activity_observations"]


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


def test_a_regrade_appends_its_grade_once_and_rebuilds_add_nothing(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_regraded", when=T)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(hours=1)))
    before = _raw_ledgers(repository)
    graded = _channel_counts(repository, "att_regraded")
    observation = repository.observation_by_attempt("att_regraded")

    _regrade(vault, repository, "att_regraded", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1))
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))
    after_one = _raw_ledgers(repository)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=3)))

    # The regrade's own replay appended the new grade to the answer's
    # observation (a raw event, its interpretation, three measurement events);
    # no other answer and no rebuild appended anything.
    assert _grown(after_one, _raw_ledgers(repository)) == {}
    assert _channel_counts(repository, "att_regraded") == {
        "activity_observations": graded["activity_observations"],
        "raw_grade_events": graded["raw_grade_events"] + 1,
        "grade_interpretations": graded["grade_interpretations"] + 1,
        "measurement_events": graded["measurement_events"] + 3,
    }
    assert sum(_grown({t: before[t] for t in GRADE_CHANNEL}, {t: after_one[t] for t in GRADE_CHANNEL}).values()) == 5
    assert repository.observation_by_attempt("att_regraded")["id"] == observation["id"]
    head = _ledger_entry(repository, "att_regraded")["active_interpretation"]
    raw = repository.raw_grade_event(str(head["raw_grade_event_id"]))
    assert json.loads(raw["raw_output_json"])["rubric_score"] == 4


def test_a_projection_version_change_reinterprets_once(tmp_path, monkeypatch):
    vault, repository = _history(tmp_path)
    attempt = next(a for a in repository.list_all_attempts() if a["practice_item_id"] == "pi_diag_easy")
    before = _channel_counts(repository, str(attempt["id"]))
    monkeypatch.setattr(grade_resolution, "PROJECTION_ALGORITHM_VERSION", "grade_interpretation_v2")

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    once = _raw_ledgers(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    # One new interpretation of the same raw grade per answer, with its one
    # measurement event, at the first rebuild; nothing at the second.
    assert _grown(once, _raw_ledgers(repository)) == {}
    assert _channel_counts(repository, str(attempt["id"])) == {
        **before,
        "grade_interpretations": before["grade_interpretations"] + 1,
        "measurement_events": before["measurement_events"] + 1,
    }
    head = _ledger_entry(repository, str(attempt["id"]))["active_interpretation"]
    assert head["projection_algorithm_version"] == "grade_interpretation_v2"


def test_a_contest_flag_survives_rebuilds(tmp_path):
    vault, repository = _history(tmp_path)
    attempt = next(a for a in repository.list_all_attempts() if a["practice_item_id"] == "pi_diag_easy")
    observation = repository.observation_by_attempt(str(attempt["id"]))
    flagged = flag_observation_for_review(
        repository, observation_id=str(observation["id"]), reason="learner_contest", clock=CLOCK
    )
    assert [row["id"] for row in repository.pending_grade_reviews()] == [flagged]
    history = _raw_ledgers(repository, REVIEWED_CHANNEL)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert _grown(history, _raw_ledgers(repository, REVIEWED_CHANNEL)) == {}
    assert _ledger_entry(repository, str(attempt["id"]))["active_interpretation"]["id"] == flagged
    assert [row["id"] for row in repository.pending_grade_reviews()] == [flagged]


def _adjudicate(vault, repository, attempt_id: str, resolved_class: str) -> dict:
    observation = repository.observation_by_attempt(attempt_id)
    head = repository.active_interpretation_for_observation(str(observation["id"]))
    return append_adjudication(
        repository,
        observation_id=str(observation["id"]),
        administration_id=str(observation["administration_id"]),
        reviewed_raw_event_ids=[str(head["raw_grade_event_id"])],
        adjudicator_source="human_owner",
        resolved_class=resolved_class,
        vault=vault,
        clock=CLOCK,
    )


@pytest.mark.parametrize("version", [LATEST_ALGORITHM_VERSION, BELOW])
def test_an_adjudication_survives_rebuilds(tmp_path, version):
    grade_channel_fixes = version == LATEST_ALGORITHM_VERSION
    vault, repository = _history(tmp_path, version=version)
    attempt_id = str(next(a for a in repository.list_all_attempts() if a["practice_item_id"] == "pi_diag_easy")["id"])
    with repository.atomic():
        project_canonical_facet_state(vault, repository, clock=CLOCK)
    unadjudicated = _facet_values(repository)
    # The owner confirms the grader's leading class: no direction flip, so no
    # grading_evidence revision; only the interpretation's authority changes.
    outcome = _adjudicate(vault, repository, attempt_id, "partial_success")
    assert outcome["evidence_revision"]["status"] == "skipped_direction_unchanged"
    with repository.atomic():
        project_canonical_facet_state(vault, repository, clock=CLOCK)
    adjudicated = _facet_values(repository)
    assert adjudicated != unadjudicated
    assert _ledger_entry(repository, attempt_id)["active_adjudication"] is not None
    history = _raw_ledgers(repository, REVIEWED_CHANNEL)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    if grade_channel_fixes:
        assert _ledger_entry(repository, attempt_id)["active_adjudication"]["id"] == outcome["adjudication_id"]
        assert _facet_values(repository) == adjudicated
        assert _grown(history, _raw_ledgers(repository, REVIEWED_CHANNEL)) == {}
    else:
        # The predecessor, kept exactly: the re-minted observation carries no
        # adjudication, and the facet row is the unadjudicated one again.
        assert _ledger_entry(repository, attempt_id)["active_adjudication"] is None
        assert _facet_values(repository) == unadjudicated


def test_an_adjudication_that_flips_the_grade_is_not_taken_for_a_regrade(tmp_path):
    vault, repository = _history(tmp_path)
    attempt_id = str(next(a for a in repository.list_all_attempts() if a["practice_item_id"] == "pi_diag_mid")["id"])
    # A zero-point answer the owner rules a success: the adjudication also
    # writes the grade it decided (a grading_evidence revision), which replay
    # then re-applies; that is the adjudication's grade, not a new one.
    outcome = _adjudicate(vault, repository, attempt_id, "success")
    assert outcome["evidence_revision"]["status"] == "revised"
    with repository.atomic():
        project_canonical_facet_state(vault, repository, clock=CLOCK)
    adjudicated = _facet_values(repository)
    history = _raw_ledgers(repository, REVIEWED_CHANNEL)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert _grown(history, _raw_ledgers(repository, REVIEWED_CHANNEL)) == {}
    assert _ledger_entry(repository, attempt_id)["active_interpretation"]["id"] == outcome["interpretation_id"]
    assert _facet_values(repository) == adjudicated
