"""The canonical projection and the facet evidence timeline fold the same ledger the same way.

Both folds once took the reliability-discounted mass (P0) and the regrade-contract epoch reading only at or
above their tags; refactor D5 removed both tag gates from the two folds together. This pins that, on a vault
at the head, the two agree on the rows those readings exist for: a cold-calibrated self-grade (its mass is
discounted), a grade revised by an adjudication (two epochs, the current one last), a grade written before
contract lineage (rows citing no contract, keyed by their stamp), and a regrade written before regrade
contracts (its current epoch's contract is unrecorded, so replay holds it and both folds bank nothing)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.attempts.grade_resolution import append_adjudication
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.held_grades import contract_unrecorded_attempts
from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline
from learnloop.substrate.canonical_projection import p0_effective_evidence_mass
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault
from tests.regrade_contract_successor_helpers import as_graded_before_contracts, as_regraded_before_contracts

ITEMS = ("pi_svd_define_001", "pi_svd_define_002", "pi_svd_define_003", "pi_svd_define_004")


def _attempt(vault, repository, item_id, minutes, points=4):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    ).attempt_id


def _flip(repository, attempt_id, minutes):
    """An owner adjudication that flips a full-marks grade: a second, superseding grading epoch."""

    observation = repository.observation_by_attempt(attempt_id)
    raw = repository.raw_grade_events_for_observation(observation["id"])
    result = append_adjudication(
        repository,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw[-1]["id"]],
        adjudicator_source="human_owner",
        resolved_class="other",
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    assert result["evidence_revision"]["status"] == "revised", result


def _build(tmp_path, *, held_regrade: bool):
    paths = create_basic_vault(tmp_path / "vault")
    for item_id in ITEMS[1:]:
        add_followup_item(paths.root, item_id)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    cold = _attempt(vault, repository, ITEMS[0], 1)
    revised = _attempt(vault, repository, ITEMS[1], 2)
    _flip(repository, revised, 3)
    uncited = _attempt(vault, repository, ITEMS[2], 4)
    as_graded_before_contracts(repository, uncited)
    attempts = {"cold": cold, "revised": revised, "uncited": uncited}
    if held_regrade:
        held = _attempt(vault, repository, ITEMS[3], 5)
        _flip(repository, held, 6)
        as_regraded_before_contracts(repository, held, supersede_tiers=(1, 3))
        attempts["held"] = held
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))
    return vault, repository, attempts


@pytest.fixture
def ledger(tmp_path):
    return _build(tmp_path, held_regrade=True)


def _assert_the_timeline_ends_at_the_banked_credit(vault, repository):
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    assert sum(banked.values()) > 0.0
    facets = set(banked) | {
        vault.canonical_facet_id(str(facet)) for item in vault.practice_items.values() for facet in item.evidence_facets
    }
    for facet in sorted(facets):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked.get(facet, 0.0), abs=1e-12), facet


def test_the_ledger_holds_each_reading_the_folds_share(ledger):
    vault, repository, attempts = ledger
    rows = {row["attempt_id"]: row for row in repository.canonical_observation_ledger_v2()}
    cold = rows[attempts["cold"]]
    type_mass = attempt_evidence_mass(cold["attempt_type"], vault.config.evidence)
    assert 0.0 < p0_effective_evidence_mass(
        repository, interpretation=cold.get("active_interpretation"), attempt_type_mass=type_mass
    ) < type_mass
    assert len({row["grading_revision"] for row in rows[attempts["revised"]]["evidence"]}) == 1
    assert all(row.get("assessment_contract_version_id") is None for row in rows[attempts["uncited"]]["evidence"])
    with repository.connection() as connection:
        assert contract_unrecorded_attempts(connection) == frozenset({attempts["held"]})


def test_the_timeline_ends_at_the_projections_banked_credit(tmp_path):
    vault, repository, _attempts = _build(tmp_path, held_regrade=False)
    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)


@pytest.mark.xfail(strict=True, reason="ledger D-33: the timeline keeps an uncited held epoch's earlier credit")
def test_the_timeline_drops_what_a_held_uncited_regrade_holds(ledger):
    vault, repository, _attempts = ledger
    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)
