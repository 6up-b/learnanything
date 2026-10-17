"""Regrade contracts (successor ``mvp-0.26``): writers, replay and their readers.

``tests/test_regrade_contract_replay.py`` holds the fail-first reproductions of
the three §8.4 cases. This module pins the successor itself:

* the version is the next link of the chain;
* every regrade (ordinary, deferred, method-explicit, a clarification's) cites
  the contract it graded against on every row, in its own transaction, under
  the attempt's next grading revision, and supersedes every live row; below
  the tag it writes as before;
* replay reads the CURRENT grading epoch under its own contract; a current
  epoch citing none (rows written before the tag) is held for review with the
  maximum recorded with it, unless it is the attempt's only, pre-contract
  grade (the compatibility reading, while its score fits); a regrade or an
  adjudication releases it;
* the readers of the grading epoch compose: feedback (``contract``), the
  forecasts' graded contract, held grades and their release, the provenance
  record of the grading, the grade contest, the adjudication revision;
* a property test over random grading histories: correctness stays in
  [0, 1], replay equals the live write for every epoch, and a rebuild is
  idempotent.

Fakes only; no network.
"""

from __future__ import annotations

import json
import random
from contextlib import contextmanager
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import (
    CANONICAL_STATE_VERSIONS,
    DIAGNOSIS_SPLIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    METHOD_EXPLICIT_VERSIONS,
    P0_PROJECTION_VERSIONS,
    PLACEMENT_VERSIONS,
    REGRADE_CONTRACT_ALGORITHM_VERSION,
    REGRADE_CONTRACT_VERSIONS,
    ROUTE_RULES_VERSIONS,
    ROUTER_MIXTURE_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
from learnloop.attempts.regrade import regrade_attempt, run_deferred_ai_regrades
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
from learnloop.grading_epochs import current_epoch, next_grading_revision, ordered_epochs
from learnloop.held_grades import attempt_grade_held
from learnloop.outcome_contract import GRADE_CONTRACT_UNRECORDED
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.shadow_rebuild import _learner_state_snapshot
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.serializers import feedback_bundle

from tests.split_live_helpers import ReadyRuntime, append_config, split_vault, submit
from tests.test_held_grade_evidence import T, _graded_apply
from tests.test_regrade_contract_replay import (
    ITEM,
    SIBLING_ITEM,
    PointsGrader,
    _grade,
    _regrade,
    _self_graded_apply,
    _set_result_points,
)
from tests.test_route_rules_in_grader import ALTERNATIVE, DivergentUnlocatedGrader

VERSION = REGRADE_CONTRACT_ALGORITHM_VERSION
PREDECESSOR = METHOD_EXPLICIT_ALGORITHM_VERSION
JOINT = "[diagnosis]\nsplit_enabled = false"


def _vault(tmp_path, *, version=VERSION, config=""):
    return split_vault(tmp_path, version=version, config=config)


def _rows(repository, attempt_id, *, superseded=False):
    return repository.fetch_grading_evidence(attempt_id, include_superseded=superseded)


def _contract(repository, version_id):
    stored = repository.fetch_assessment_contract_version(version_id)
    assert stored is not None
    return dict(stored["contract"])


def _flip(paths, version):
    from tests.helpers import set_algorithm_version

    set_algorithm_version(paths, version)
    return load_vault(paths.root)


def _rebuild(vault, repository, days=30):
    return rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=days)))


def _settle(vault, repository, days=30):
    """Rebuild to the fixed point. A rebuild reaches it in one pass after a
    regrade (which replays in its own transaction) and in two after a write
    that does not replay (an adjudication, a label move): replay reads the
    canonical projection as each attempt's prior, so the first pass reads the
    projection the change made stale (shown identical at mvp-0.25 in
    ``test_rebuild_converges_after_an_adjudication_as_it_did_before``)."""

    _rebuild(vault, repository, days)
    _rebuild(vault, repository, days)


def _unversioned(snapshot):
    """A learner snapshot without the version stamp each row carries."""

    return {
        family: {key: {k: v for k, v in row.items() if k != "algorithm_version"} for key, row in rows.items()}
        for family, rows in snapshot.items()
    }


def _state(repository):
    """Everything a rebuild derives that this module compares: the learner
    projections and each attempt's grade summary."""

    with repository.connection() as connection:
        attempts = [
            tuple(row)
            for row in connection.execute(
                "SELECT id, rubric_score, correctness, manual_review, manual_review_reason "
                "FROM practice_attempts ORDER BY id"
            )
        ]
    return {"learner": _learner_state_snapshot(repository), "attempts": attempts}


# -- the version -----------------------------------------------------------------------------


def test_the_successor_is_the_latest_and_keeps_every_predecessor():
    assert VERSION == "mvp-0.26"
    # The one eligibility decision (mvp-0.27) followed it and keeps it.
    assert SUCCESSOR_CHAIN[-2] == VERSION and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.27"
    assert SUCCESSOR_CHAIN[-3] == PREDECESSOR == "mvp-0.25"
    assert REGRADE_CONTRACT_VERSIONS == frozenset({VERSION, "mvp-0.27"})
    for versions in (CANONICAL_STATE_VERSIONS, P0_PROJECTION_VERSIONS, DIAGNOSIS_SPLIT_VERSIONS, PLACEMENT_VERSIONS,
                     ROUTE_RULES_VERSIONS, ROUTER_MIXTURE_VERSIONS, METHOD_EXPLICIT_VERSIONS):
        assert VERSION in versions
    assert PREDECESSOR not in REGRADE_CONTRACT_VERSIONS


def test_its_defaults_fingerprint_is_recorded():
    assert defaults_fingerprint_for_version(VERSION) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[VERSION]


# -- the epoch rule (pure) ---------------------------------------------------------------------


def _row(rid, criterion, *, revision=None, at="2026-11-01T12:00:00Z", contract=None, superseded=False):
    return {"id": rid, "criterion_id": criterion, "grading_revision": revision, "created_at": at,
            "assessment_contract_version_id": contract, "superseded_at": "x" if superseded else None}


def test_the_current_epoch_is_chosen_among_live_rows_never_by_a_first_seen_stamp():
    first = [_row("a1", "setup", revision=0, contract="A"), _row("a2", "result", revision=0, contract="A")]
    # A regrade written before the successor: no revision, same second, live beside the original.
    legacy = [_row("01Z", "setup"), _row("01Y", "result")]
    assert current_epoch(first + legacy).key == "legacy:2026-11-01T12:00:00Z"
    # A successor epoch supersedes every live row: it is the only live one.
    superseded = [{**row, "superseded_at": "x"} for row in first + legacy]
    successor = [_row("b1", "setup", revision=1, contract="C"), _row("b2", "result", revision=1, contract="C")]
    epoch = current_epoch(superseded + successor)
    assert (epoch.key, epoch.contract_version_id, epoch.revision) == ("revision:1", "C", 1)
    assert [e.key for e in ordered_epochs(superseded + successor)][-1] == "revision:1"
    assert next_grading_revision(superseded + successor) == 2
    assert next_grading_revision([]) == 0
    assert next_grading_revision(legacy) == 1
    # Rows citing different contracts, or not all citing one, record none.
    mixed = [_row("c1", "setup", revision=3, contract="A"), _row("c2", "result", revision=3)]
    assert current_epoch(mixed).contract_version_id is None


# -- the writer ------------------------------------------------------------------------------


def test_an_ordinary_regrade_cites_the_contract_it_read_and_supersedes_every_live_row(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_w", when=T)
    [original_contract] = {row.assessment_contract_version_id for row in _rows(repository, "att_w")}
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)

    _regrade(vault, repository, "att_w", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))

    live = _rows(repository, "att_w")
    assert {row.grader_tier for row in live} == {3} and len(live) == 2
    [cited] = {row.assessment_contract_version_id for row in live}
    assert cited != original_contract
    contract = _contract(repository, cited)
    assert contract["rubric_max_points"] == 8
    assert {c["id"]: c["max_points"] for c in contract["criteria"]} == {"setup": 2, "result": 6}
    assert {row.grading_revision for row in live} == {1}
    # The original's model rows are superseded by the regrade (decision: an
    # ordinary regrade of a model grade supersedes the model tier).
    old = [row for row in _rows(repository, "att_w", superseded=True) if row.superseded_at is not None]
    assert {row.grader_tier for row in old} == {3} and len(old) == 2
    assert {row.superseded_by_evidence_id for row in old} <= {row.id for row in live}

    # A second regrade of the unchanged item reuses the snapshot, one revision on.
    _regrade(vault, repository, "att_w", {"setup": 2.0, "result": 6.0}, when=T + timedelta(days=2))
    live = _rows(repository, "att_w")
    assert {row.assessment_contract_version_id for row in live} == {cited}
    assert {row.grading_revision for row in live} == {2}
    assert _grade(repository, "att_w") == (8, 1.0)


def test_the_regrade_snapshot_is_written_in_the_regrade_transaction(tmp_path, monkeypatch):
    """A regrade whose publication fails leaves no contract behind (and no rows)."""

    import learnloop.attempts.regrade as regrade_module

    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_tx", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        before = connection.execute("SELECT COUNT(*) FROM assessment_contract_versions").fetchone()[0]

    def fail(*args, **kwargs):
        raise RuntimeError("replay failed")

    monkeypatch.setattr(regrade_module, "replay_learning_object", fail)
    with pytest.raises(RuntimeError):
        _regrade(vault, repository, "att_tx", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))

    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM assessment_contract_versions").fetchone()[0] == before
    assert {row.grading_revision for row in _rows(repository, "att_tx", superseded=True)} == {0}


def test_a_deferred_regrade_of_a_self_grade_cites_its_contract(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _self_graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_d", when=T)

    result = run_deferred_ai_regrades(
        vault, repository, runtime=ReadyRuntime(), ai_client=PointsGrader({"setup": 2.0, "result": 2.0}),
        clock=FrozenClock(T + timedelta(days=1)),
    )

    assert result.regraded >= 1
    live = _rows(repository, "att_d")
    assert {row.grader_tier for row in live} == {3}
    [cited] = {row.assessment_contract_version_id for row in live}
    assert cited is not None and {row.grading_revision for row in live} == {1}
    assert _grade(repository, "att_d") == (4, 1.0)


def test_a_clarification_regrade_cites_its_contract(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_q", when=T)
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt("att_q"), runtime=ReadyRuntime(),
        client=PointsGrader({"setup": 2.0, "result": 1.0}), grading_source="ai",
        clock=FrozenClock(T + timedelta(days=1)),
        clarification_exchange={"question_md": "Which V?", "answer_md": "From A^T A.", "criterion_id": "setup",
                                "reason": "method_ambiguity"},
    )
    live = _rows(repository, "att_q")
    assert len({row.assessment_contract_version_id for row in live} - {None}) == 1
    assert {row.grading_revision for row in live} == {1}


def test_a_method_explicit_regrade_cites_its_frozen_contract_under_a_new_revision(tmp_path):
    from tests.test_required_method_grading import DivergentGrader, _edit_item, _method_vault

    paths, vault, repository = _method_vault(tmp_path, version=VERSION)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    [frozen] = {row.assessment_contract_version_id for row in _rows(repository, result.attempt_id)}
    _edit_item(paths, prompt="Write the SVD of A. Use row reduction in your answer.")
    vault = load_vault(paths.root)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentGrader(), grading_source="ai",
                    clock=FrozenClock(T + timedelta(days=1)))
    live = _rows(repository, result.attempt_id)
    assert {row.assessment_contract_version_id for row in live} == {frozen}
    assert {row.grading_revision for row in live} == {1}


def test_below_the_successor_a_regrade_writes_as_before(tmp_path):
    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_old", when=T)
    _regrade(vault, repository, "att_old", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))
    live = _rows(repository, "att_old")
    # The original's model rows stay live beside the regrade's, which cite nothing.
    assert len(live) == 4
    regrade_rows = [row for row in live if row.grading_revision is None]
    assert len(regrade_rows) == 2 and {row.assessment_contract_version_id for row in regrade_rows} == {None}


# -- replay and the unrecorded hold -------------------------------------------------------------


def _legacy_regraded(tmp_path, *, config="", self_graded=False):
    """An answer regraded at the predecessor within its original maximum (3
    of 8 under the raised rubric, uncited), rebuilt there: the §8.4 case-2
    shape, 0.75 as the predecessor replays it."""

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR, config=config)
    apply = _self_graded_apply if self_graded else _graded_apply
    apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_l", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_l", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))
    _rebuild(vault, repository)
    return paths, vault, repository


def test_below_the_successor_old_rows_replay_exactly_as_before(tmp_path):
    paths, vault, repository = _legacy_regraded(tmp_path)
    assert _grade(repository, "att_l") == (3, 0.75)  # the predecessor's reading, kept
    before = _state(repository)
    _rebuild(vault, repository)
    assert _state(repository) == before


def test_an_uncited_regrade_epoch_is_held_with_the_maximum_recorded_with_it(tmp_path):
    """The blind regrade recorded its maximum (8): at the successor the epoch
    is held for review, its correctness 3/8, never read against today's item
    nor against the original's contract."""

    paths, vault, repository = _legacy_regraded(tmp_path)
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)

    attempt = repository.fetch_practice_attempt("att_l")
    assert (attempt["rubric_score"], attempt["correctness"]) == (3, 0.375)
    assert attempt["manual_review_reason"] == GRADE_CONTRACT_UNRECORDED
    assert attempt_grade_held(repository, "att_l")
    assert feedback_bundle(vault, repository, "att_l")["heldForReview"] is True
    _rebuild(vault, repository)
    before = _state(repository)
    _rebuild(vault, repository)
    assert _state(repository) == before


def test_an_unrecorded_joint_regrade_keeps_the_correctness_it_carries_and_never_fails_a_rebuild(tmp_path):
    """A joint regrade recorded no maximum: held, with the correctness the
    attempt row carries; lowering the rubric after it never fails a rebuild."""

    paths, vault, repository = _legacy_regraded(tmp_path, config=JOINT, self_graded=True)
    assert repository.latest_blind_grade_record("att_l") is None
    stored = _grade(repository, "att_l")
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)
    assert _grade(repository, "att_l") == stored
    assert attempt_grade_held(repository, "att_l")

    _set_result_points(paths, 1)  # maximum 3, below the regrade's score
    vault = load_vault(paths.root)
    _rebuild(vault, repository)
    assert _grade(repository, "att_l") == stored


def test_a_held_unrecorded_grade_is_no_evidence(tmp_path):
    """Held: the learner's projections (mastery, facets, every item's
    schedule) are exactly those of the same history whose answer carries a
    route-rule hold instead, which every reader already reads as no evidence."""

    paths, vault, repository = _legacy_regraded(tmp_path / "regraded", config=JOINT, self_graded=True)
    vault = _flip(paths, VERSION)
    _settle(vault, repository)
    assert attempt_grade_held(repository, "att_l")
    held = _learner_state_snapshot(repository)

    from tests.test_held_grade_evidence import _held_apply

    other_paths, other_vault, other_repository = _vault(tmp_path / "control", version=VERSION, config=JOINT)
    _held_apply(other_vault, other_repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_l", when=T)
    _set_result_points(other_paths, 6)
    other_vault = load_vault(other_paths.root)
    _settle(other_vault, other_repository)
    assert attempt_grade_held(other_repository, "att_l")
    control = _learner_state_snapshot(other_repository)

    for family in ("mastery", "facet", "schedule"):
        assert held[family] == control[family], family


def test_a_successor_regrade_releases_an_unrecorded_hold(tmp_path):
    paths, vault, repository = _legacy_regraded(tmp_path)
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)
    assert attempt_grade_held(repository, "att_l")

    _regrade(vault, repository, "att_l", {"setup": 2.0, "result": 3.0}, when=T + timedelta(days=40))

    assert not attempt_grade_held(repository, "att_l")
    assert repository.fetch_practice_attempt("att_l")["manual_review_reason"] != GRADE_CONTRACT_UNRECORDED
    assert _grade(repository, "att_l") == (5, 0.625)
    _rebuild(vault, repository, days=41)
    assert _grade(repository, "att_l") == (5, 0.625)


def test_an_adjudication_releases_an_unrecorded_hold_under_the_contract_it_cites(tmp_path):
    paths, vault, repository = _legacy_regraded(tmp_path)
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)

    revision = append_adjudication_evidence_revision(
        repository, attempt_id="att_l", resolved_fraction=0.5, adjudication_id="adj_l",
        adjudicator_source="human_owner", rationale="half", vault=vault,
        clock=FrozenClock(T + timedelta(days=40)),
    )

    assert revision["status"] == "revised"
    live = _rows(repository, "att_l")
    [cited] = {row.assessment_contract_version_id for row in live}
    assert cited is not None and _contract(repository, cited)["rubric_max_points"] == 8
    # The legacy rows hold revision 0 (the original) and none (the regrade).
    assert {row.grading_revision for row in live} == {1}
    assert not attempt_grade_held(repository, "att_l")
    assert _grade(repository, "att_l") == (4, 0.5)
    _rebuild(vault, repository, days=41)
    assert _grade(repository, "att_l") == (4, 0.5)


def test_a_first_grade_made_before_contracts_keeps_its_compatibility_reading(tmp_path):
    """The seeded history (graded at mvp-0.6, no contract, one epoch each)
    replays at the successor exactly as at the predecessor, until an item's
    maximum falls below a score: then that grade is held, never above 1."""

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    _settle(vault, repository)
    before = _state(repository)
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)
    assert _state(repository)["attempts"] == before["attempts"]
    assert _unversioned(_state(repository)["learner"]) == _unversioned(before["learner"])

    # att_03_svd_pass scored 4 of 4 on pi_svd_compute_002; its maximum falls to 3.
    from learnloop.vault.writer import upsert_practice_item

    data = vault.practice_items[SIBLING_ITEM].model_dump(mode="json")
    data["grading_rubric"]["criteria"] = [{**c, "points": 1 if c["id"] == "result" else c["points"]}
                                          for c in data["grading_rubric"]["criteria"]]
    data["grading_rubric"]["max_points"] = 3
    upsert_practice_item(paths.root, data)
    vault = load_vault(paths.root)
    _rebuild(vault, repository)
    attempt = repository.fetch_practice_attempt("att_03_svd_pass")
    assert attempt["manual_review_reason"] == GRADE_CONTRACT_UNRECORDED
    assert 0.0 <= attempt["correctness"] <= 1.0


def _as_graded_before_contracts(repository, attempt_id):
    """Rewrite an attempt's rows as a pre-mvp-0.7 grade wrote them: no
    grading revision and no assessment contract (test construction only)."""

    with repository.connection() as connection:
        connection.execute(
            "UPDATE grading_evidence SET grading_revision = NULL, assessment_contract_version_id = NULL "
            "WHERE attempt_id = ?",
            (attempt_id,),
        )
        connection.commit()


@pytest.mark.parametrize("after", [timedelta(0), timedelta(seconds=1)], ids=["same_second", "a_second_later"])
def test_a_regrade_in_its_pre_contract_grades_second_is_held_not_read_as_its_only_grade(tmp_path, after):
    """Review F3: a pre-contract self-grade and the ordinary regrade that
    superseded it, both revision-less and stamped in the same second, share
    the legacy epoch key. The explicit supersession (and the regrade's own
    run) says they are two writes, so the regrade is no "only, pre-contract
    grade": it is held with the maximum its blind record kept (3/8), never
    read against today's item (3/6). A second later (the control) it was
    already held."""

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    _set_result_points(paths, 6)  # maximum 8
    vault = load_vault(paths.root)
    _self_graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_s2", when=T)
    _as_graded_before_contracts(repository, "att_s2")
    _regrade(vault, repository, "att_s2", {"setup": 1.0, "result": 2.0}, when=T + after)
    rows = _rows(repository, "att_s2", superseded=True)
    assert {row.grading_revision for row in rows} == {None}
    assert {row.assessment_contract_version_id for row in rows} == {None}
    assert len({row.created_at for row in rows}) == (1 if after == timedelta(0) else 2)
    assert any(row.superseded_at is not None for row in rows)
    assert _grade(repository, "att_s2") == (3, 0.375)

    _set_result_points(paths, 4)  # maximum 6: the regrade's 3 still fits today's item
    vault = _flip(paths, VERSION)
    _rebuild(vault, repository)

    attempt = repository.fetch_practice_attempt("att_s2")
    assert (attempt["rubric_score"], attempt["correctness"]) == (3, 0.375)
    assert attempt["manual_review_reason"] == GRADE_CONTRACT_UNRECORDED
    assert attempt_grade_held(repository, "att_s2")


def test_only_a_grade_no_later_write_replaced_is_an_attempts_only_grade():
    """Review F3, the rule as a pure function: one epoch key is not enough.
    A superseded row, or two grading runs under one legacy key, is evidence
    of a second write."""

    from learnloop.grading_epochs import only_grade

    at = "2026-11-01T12:00:00Z"
    self_grade = [_row("s1", "setup", at=at), _row("s2", "result", at=at)]
    assert only_grade(self_grade)
    # A same-second regrade that superseded the self-grade (tier 1).
    superseded = [{**row, "superseded_at": "x"} for row in self_grade]
    regrade = [{**_row("r1", "setup", at=at), "agent_run_id": "run_2"},
               {**_row("r2", "result", at=at), "agent_run_id": "run_2"}]
    assert not only_grade(superseded + regrade)
    # A same-second model regrade that left the model original live beside it
    # (before the successor, an ordinary regrade superseded tier 1 alone).
    model = [{**row, "agent_run_id": "run_1"} for row in self_grade]
    assert not only_grade(model + regrade)
    # One write with a self-graded and a model-graded tier (a joint grade): one run.
    assert only_grade(self_grade + regrade)
    assert not only_grade(self_grade + [_row("x1", "setup", at="2026-11-01T12:00:01Z")])
    assert not only_grade([])


@contextmanager
def _before_the_next_transaction(monkeypatch, repository, intruder):
    """Run ``intruder`` (another writer, on its own connection) once,
    immediately before ``repository`` next enters a transaction: review F2's
    interleaving of two writers that both read before either writes."""

    real = repository.atomic
    fired: list[bool] = []

    @contextmanager
    def atomic():
        if not fired:
            fired.append(True)
            intruder()
        with real():
            yield

    monkeypatch.setattr(repository, "atomic", atomic)
    try:
        yield fired
    finally:
        monkeypatch.undo()


@pytest.mark.parametrize("intruder", ["adjudication", "regrade"])
def test_an_adjudication_allocates_its_revision_inside_its_own_transaction(tmp_path, monkeypatch, intruder):
    """Review F2: another writer that commits between an adjudication's entry
    and its transaction never shares its revision. The adjudication reads the
    current epoch, its contract and the next revision inside the one
    ``BEGIN IMMEDIATE`` that publishes it, so the history keeps every epoch
    and the revision cites the contract of the grade it actually revises."""

    from learnloop.db.repositories import Repository

    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_r", when=T)
    _set_result_points(paths, 6)  # maximum 8: what the intruding regrade grades under
    vault = load_vault(paths.root)
    other = Repository(repository.sqlite_path)

    def intrude():
        if intruder == "adjudication":
            append_adjudication_evidence_revision(
                other, attempt_id="att_r", resolved_fraction=0.5, adjudication_id="adj_other",
                adjudicator_source="human_owner", rationale=None, vault=vault,
                clock=FrozenClock(T + timedelta(days=1)),
            )
        else:
            _regrade(vault, other, "att_r", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))

    with _before_the_next_transaction(monkeypatch, repository, intrude) as fired:
        revision = append_adjudication_evidence_revision(
            repository, attempt_id="att_r", resolved_fraction=0.25, adjudication_id="adj_mine",
            adjudicator_source="human_owner", rationale=None, vault=vault,
            clock=FrozenClock(T + timedelta(days=2)),
        )
    assert fired and revision["status"] == "revised"

    every_row = _rows(repository, "att_r", superseded=True)
    epochs = ordered_epochs(every_row)
    assert [epoch.key for epoch in epochs] == ["revision:0", "revision:1", "revision:2"]
    assert [epoch.live for epoch in epochs] == [False, False, True]
    live = _rows(repository, "att_r")
    intruded = epochs[1].contract_version_id
    assert intruded is not None
    # The adjudication revised the grade the intruder left: it cites that contract.
    assert {row.assessment_contract_version_id for row in live} == {intruded}
    maximum = _contract(repository, intruded)["rubric_max_points"]
    assert maximum == (8 if intruder == "regrade" else 4)
    assert _grade(repository, "att_r") == (round(0.25 * maximum), round(0.25 * maximum) / maximum)
    _rebuild(vault, repository)
    assert _grade(repository, "att_r") == (round(0.25 * maximum), round(0.25 * maximum) / maximum)


# -- the readers ------------------------------------------------------------------------------


def test_feedback_reads_a_reopened_regrade_from_the_contract_it_cites(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_f", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_f", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))
    _set_result_points(paths, 2)  # the item changes again, with no regrade
    vault = load_vault(paths.root)

    bundle = feedback_bundle(vault, repository, "att_f")

    assert bundle["answeredSource"] == "contract"
    assert bundle["answeredMaxPoints"] == 8
    assert {row["criterionId"]: row["pointsPossible"] for row in bundle["answeredCriteria"]} == {
        "setup": 2.0, "result": 6.0,
    }
    assert (bundle["regrade"]["oldMaxPoints"], bundle["regrade"]["newMaxPoints"]) == (4, 8)


@pytest.mark.parametrize("version", [PREDECESSOR, VERSION])
def test_a_regraded_observation_resolves_its_graded_contract_in_the_forecast_reader(tmp_path, version):
    from learnloop.evsi_calibration.forecast_report import _Ledgers

    paths, vault, repository = _vault(tmp_path, version=version)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_fc", when=T)
    _regrade(vault, repository, "att_fc", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1))
    facet = vault.practice_items[ITEM].evidence_facets[0]

    with repository.connection() as connection:
        outcome, why, _contract = _Ledgers(connection, vault).facet_outcome("att_fc", facet)

    if version == VERSION:
        assert why != "graded_contract_unknown"
    else:
        assert (outcome, why) == (None, "graded_contract_unknown")


def test_the_grading_provenance_record_pins_the_contract_the_regrade_read(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_p", when=T)
    _regrade(vault, repository, "att_p", {"setup": 2.0, "result": 1.0}, when=T + timedelta(days=1))
    [cited] = {row.assessment_contract_version_id for row in _rows(repository, "att_p")}
    with repository.connection() as connection:
        (inputs,) = connection.execute(
            "SELECT inputs_json FROM text_write_provenance WHERE kind = 'grading' AND record_id = ? "
            "AND writer = 'regrade' ORDER BY created_at DESC, id DESC LIMIT 1",
            ("att_p",),
        ).fetchone()
    assert json.loads(inputs)["answers"]["att_p"] == [cited]


def test_an_adjudication_of_a_regrade_revises_its_epoch_under_its_contract(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_a", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_a", {"setup": 2.0, "result": 4.0}, when=T + timedelta(days=1))
    [cited] = {row.assessment_contract_version_id for row in _rows(repository, "att_a")}

    append_adjudication_evidence_revision(
        repository, attempt_id="att_a", resolved_fraction=0.3, adjudication_id="adj_a",
        adjudicator_source="human_owner", rationale="partly", vault=vault,
        clock=FrozenClock(T + timedelta(days=2)),
    )

    live = _rows(repository, "att_a")
    assert {row.assessment_contract_version_id for row in live} == {cited}
    assert {row.grading_revision for row in live} == {2} and {row.grader_tier for row in live} == {4}
    # round(0.3 * 8) = 2: the correctness replay computes, written live.
    assert _grade(repository, "att_a") == (2, 0.25)
    _rebuild(vault, repository)
    assert _grade(repository, "att_a") == (2, 0.25)


def test_a_route_rule_hold_is_released_by_a_successor_regrade_under_its_contract(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=T)
    assert attempt_grade_held(repository, held.attempt_id)

    _regrade(vault, repository, held.attempt_id, {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1))

    assert not attempt_grade_held(repository, held.attempt_id)
    live = _rows(repository, held.attempt_id)
    assert len({row.assessment_contract_version_id for row in live} - {None}) == 1
    assert _grade(repository, held.attempt_id) == (4, 1.0)


# -- the property ----------------------------------------------------------------------------


class _History:
    """A random grading history on two answers of one learning object."""

    ATTEMPTS = ("att_p1", "att_p2")
    ITEMS = {"att_p1": ITEM, "att_p2": SIBLING_ITEM}

    def __init__(self, tmp_path, seed: int):
        self.rng = random.Random(seed)
        self.paths, self.vault, self.repository = _vault(tmp_path)
        self.day = 0
        self.graded: list[str] = []
        #: attempt -> (rubric_score, correctness) as its last live write left it.
        self.live: dict[str, tuple[int, float]] = {}

    def when(self):
        self.day += 1
        return T + timedelta(days=self.day)

    def _maxima(self, attempt_id):
        item = self.vault.practice_items[self.ITEMS[attempt_id]]
        return {criterion.id: float(criterion.points) for criterion in item.grading_rubric.criteria}

    def _points(self, attempt_id):
        return {cid: float(self.rng.randint(0, int(points))) for cid, points in self._maxima(attempt_id).items()}

    def _record(self, attempt_id):
        self.live[attempt_id] = _grade(self.repository, attempt_id)

    def grade(self):
        remaining = [a for a in self.ATTEMPTS if a not in self.graded]
        if not remaining:
            return self.regrade()
        attempt_id = remaining[0]
        apply = self.rng.choice((_graded_apply, _self_graded_apply))
        apply(self.vault, self.repository, self.ITEMS[attempt_id], self._points(attempt_id),
              attempt_id=attempt_id, when=self.when())
        self.graded.append(attempt_id)
        self._record(attempt_id)
        return f"grade {attempt_id}"

    def regrade(self):
        if not self.graded:
            return self.grade()
        attempt_id = self.rng.choice(self.graded)
        _regrade(self.vault, self.repository, attempt_id, self._points(attempt_id), when=self.when())
        self._record(attempt_id)
        return f"regrade {attempt_id}"

    def hold_then_release(self):
        if not self.graded:
            return self.grade()
        attempt_id = self.rng.choice(self.graded)
        regrade_attempt(self.vault, self.repository, self.repository.fetch_practice_attempt(attempt_id),
                        runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
                        clock=FrozenClock(self.when()))
        self._record(attempt_id)
        if self.rng.random() < 0.5:
            _regrade(self.vault, self.repository, attempt_id, self._points(attempt_id), when=self.when())
            self._record(attempt_id)
            return f"hold+release {attempt_id}"
        return f"hold {attempt_id}"

    def edit_rubric(self):
        points = self.rng.choice((1, 2, 4, 6))
        _set_result_points(self.paths, points)
        self.vault = load_vault(self.paths.root)
        return f"result -> {points}"

    def adjudicate(self):
        if not self.graded:
            return self.grade()
        attempt_id = self.rng.choice(self.graded)
        fraction = self.rng.choice((0.0, 0.3, 0.5, 0.8, 1.0))
        append_adjudication_evidence_revision(
            self.repository, attempt_id=attempt_id, resolved_fraction=fraction,
            adjudication_id=f"adj_{self.day}", adjudicator_source="human_owner", rationale=None,
            vault=self.vault, clock=FrozenClock(self.when()),
        )
        self._record(attempt_id)
        return f"adjudicate {attempt_id} {fraction}"

    def rebuild(self):
        _rebuild(self.vault, self.repository, days=self.day + 1)
        return "rebuild"


@pytest.mark.parametrize("seed", range(10))
def test_random_grading_histories_stay_in_range_replay_equal_to_live_and_rebuild_idempotent(tmp_path, seed):
    history = _History(tmp_path, seed)
    steps = [history.grade(), history.grade()]
    operations = (history.regrade, history.hold_then_release, history.edit_rubric, history.adjudicate,
                  history.rebuild)
    for _ in range(9):
        steps.append(history.rng.choice(operations)())
        with history.repository.connection() as connection:
            bad = connection.execute(
                "SELECT id, correctness FROM practice_attempts WHERE correctness < 0 OR correctness > 1"
            ).fetchall()
        assert not bad, steps
        if steps[-1] == "rebuild":
            for attempt_id, live in history.live.items():
                assert _grade(history.repository, attempt_id) == live, (attempt_id, steps)
    # Replay equals the live write of every attempt's current epoch, whatever
    # the item says now; once settled, a rebuild changes nothing.
    history.rebuild()
    for attempt_id, live in history.live.items():
        assert _grade(history.repository, attempt_id) == live, (attempt_id, steps)
        epoch = current_epoch(_rows(history.repository, attempt_id))
        assert epoch is not None and epoch.contract_version_id is not None, (attempt_id, steps)
    history.rebuild()
    first = _state(history.repository)
    history.rebuild()
    assert _state(history.repository) == first, steps


@pytest.mark.parametrize("version", [PREDECESSOR, VERSION])
def test_rebuild_converges_after_an_adjudication_as_it_did_before(tmp_path, version):
    """The fixed point is reached in two passes after a write that does not
    replay (an adjudication), at the successor exactly as at mvp-0.25: replay
    reads the canonical projection as each attempt's prior (pre-existing; see
    the review's open questions). After a regrade, which replays in its own
    transaction, one pass is already the fixed point."""

    paths, vault, repository = _vault(tmp_path, version=version)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_c", when=T)
    _rebuild(vault, repository)
    _regrade(vault, repository, "att_c", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1))
    _rebuild(vault, repository)
    after_regrade = _state(repository)
    _rebuild(vault, repository)
    assert _state(repository) == after_regrade
    append_adjudication_evidence_revision(
        repository, attempt_id="att_c", resolved_fraction=0.5, adjudication_id="adj_c",
        adjudicator_source="human_owner", rationale=None, vault=vault, clock=FrozenClock(T + timedelta(days=2)),
    )
    _settle(vault, repository)
    settled = _state(repository)
    _rebuild(vault, repository)
    assert _state(repository) == settled


# -- the facet evidence timeline banks what the projection banks ---------------------------------


def _timeline_matches_the_ledger(vault, repository):
    from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline

    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    facets = set(banked)
    for item in vault.practice_items.values():
        facets.update(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets)
    for facet in sorted(facets):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked.get(facet, 0.0), abs=1e-12), facet
    return banked


def test_the_timeline_banks_exactly_what_the_projection_banks_at_the_successor(tmp_path):
    """The receipt-exactness invariant at mvp-0.26: a successor regrade under
    a changed rubric (its epoch alone, under its own contract) and a held
    unrecorded epoch (nothing) fold to the projection's banked credit."""

    paths, vault, repository = _legacy_regraded(tmp_path)
    vault = _flip(paths, VERSION)
    _settle(vault, repository)
    assert attempt_grade_held(repository, "att_l")
    _graded_apply(vault, repository, SIBLING_ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_t",
                  when=T + timedelta(days=50))
    _regrade(vault, repository, "att_t", {"setup": 2.0, "result": 1.0}, when=T + timedelta(days=51))
    _settle(vault, repository, days=52)
    banked = _timeline_matches_the_ledger(vault, repository)
    assert sum(banked.values()) > 0.0


# -- the screen's regrade and the grade channel ---------------------------------------------------


def _sidecar(paths, client):
    import learnloop_sidecar.handlers  # noqa: F401
    import learnloop_sidecar.handlers.ai_providers as providers
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    patch = pytest.MonkeyPatch()
    patch.setattr(providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client))
    patch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
    return ctx, patch


def _call(ctx, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_a_regrade_from_the_screen_is_read_from_its_contract_then_and_later(tmp_path):
    """The feedback screen's regrade at the successor: its own response and
    every later load read the contract it cites (``contract``), so the
    ``unrecorded`` label no longer follows a regrade."""

    paths, vault, repository = _vault(tmp_path)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_s", when=T)
    _set_result_points(paths, 6)
    ctx, patch = _sidecar(paths, PointsGrader({"setup": 2.0, "result": 4.0}))
    try:
        live = _call(ctx, "trigger_regrade", {"attemptId": "att_s"})
        _set_result_points(paths, 2)
        ctx.load(paths.root)
        later = _call(ctx, "get_feedback", {"attemptId": "att_s"})
    finally:
        patch.undo()
    for bundle in (live, later):
        assert bundle["answeredSource"] == "contract"
        assert bundle["answeredMaxPoints"] == 8
        assert (bundle["rubricScore"], bundle["correctness"]) == (6, 0.75)


def _channel_max_points(repository, attempt_id):
    with repository.connection() as connection:
        (raw,) = connection.execute(
            "SELECT raw_output_json FROM raw_grade_events WHERE attempt_id = ? ORDER BY id DESC LIMIT 1",
            (attempt_id,),
        ).fetchone()
    return json.loads(raw)["max_points"]


@pytest.mark.parametrize("version", [PREDECESSOR, VERSION])
def test_the_grade_channel_classifies_a_grade_out_of_the_maximum_it_was_computed_against(tmp_path, version):
    """The dual-written grade channel reads the same maximum as the attempt
    row at the successor (the cited contract's), never today's item; below it
    the channel keeps reading the item."""

    paths, vault, repository = _vault(tmp_path, version=version)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_g", when=T)
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_g", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))
    _set_result_points(paths, 4)  # maximum 6, the regrade's score still fits
    vault = load_vault(paths.root)
    _rebuild(vault, repository)
    assert _channel_max_points(repository, "att_g") == (8 if version == VERSION else 6)
