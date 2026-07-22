"""P1 step 4 -- edit classification, card-lineage state, rebuild (§3.7, §3.8, §9.2, §9.5)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import card_lineage as CL
from learnloop.services.fsrs import Rating

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
SCHED = "fsrs6"


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _card_version(repo, *, family_title="fam", contract=None, purpose="practice"):
    from learnloop.services import activities as A

    family_id = repo.ensure_activity_family(purpose=purpose, legacy_kind=None, title=family_title, clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = contract or {"target": "svd", "capability": "retrieval"}
    version_id = repo.ensure_activity_card_version(
        card_id=card_id,
        version=1,
        card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract),
        schema_version=1,
        clock=CLOCK,
    )
    return family_id, card_id, version_id


# --- §3.7 classification ------------------------------------------------------

def test_wording_only_edit_is_surface_preserving():
    prev = {"target": "svd", "capability": "retrieval", "prompt": "What is the SVD?"}
    new = {"target": "svd", "capability": "retrieval", "prompt": "Define the SVD."}
    result = CL.classify_edit(prev, new)
    assert result.verdict == "surface_preserving"


@pytest.mark.parametrize(
    "key,value",
    [
        ("target", "eigendecomposition"),
        ("capability", "procedure_execution"),
        ("response_contract", "long_constructed"),
        ("rubric_semantics", "stricter"),
        ("task_feature_bounds", {"complexity": 4}),
        ("tools", "open_book"),
        ("span", "whole_task"),
        ("feedback_eligibility", "changed"),
        ("evidence_eligibility", "changed"),
        ("difficulty", 4),
    ],
)
def test_semantic_change_forks(key, value):
    prev = {"target": "svd", "capability": "retrieval"}
    new = dict(prev)
    new[key] = value
    result = CL.classify_edit(prev, new)
    assert result.verdict == "fork_required"
    assert key in result.changed_semantic


def test_unknown_changed_component_is_parked_for_review():
    prev = {"target": "svd", "capability": "retrieval", "mystery_field": 1}
    new = {"target": "svd", "capability": "retrieval", "mystery_field": 2}
    result = CL.classify_edit(prev, new)
    assert result.verdict == "review_required"
    assert "mystery_field" in result.changed_unknown


def test_no_change_is_surface_preserving():
    contract = {"target": "svd", "capability": "retrieval"}
    assert CL.classify_edit(contract, dict(contract)).verdict == "surface_preserving"


@pytest.mark.parametrize("key", ["answer_key", "solution"])
def test_answer_key_or_solution_change_forks(key):
    # B8 regression. Pre-fix answer_key/solution were unknown keys -> parked for review;
    # they are material contract components (what counts as correct) -> fork_required.
    prev = {"target": "svd", "capability": "retrieval"}
    new = dict(prev)
    new[key] = "changed"
    result = CL.classify_edit(prev, new)
    assert result.verdict == "fork_required"
    assert key in result.changed_semantic


def test_rubric_clarification_with_semantics_delta_is_parked():
    # B8 regression. A cosmetic "clarification" cannot ride along with a real
    # rubric_semantics delta; pre-fix rubric_semantics alone forked and the clarification
    # was ignored, masking the ambiguity. The combination now parks for review.
    prev = {"target": "svd", "capability": "retrieval",
            "rubric_semantics": "lenient", "rubric_clarification": "v1"}
    new = {"target": "svd", "capability": "retrieval",
           "rubric_semantics": "strict", "rubric_clarification": "v2"}
    result = CL.classify_edit(prev, new)
    assert result.verdict == "review_required"


def test_rubric_clarification_alone_is_surface_preserving():
    # A clarification WITHOUT a rubric_semantics delta stays cosmetic.
    prev = {"target": "svd", "capability": "retrieval", "rubric_clarification": "v1"}
    new = {"target": "svd", "capability": "retrieval", "rubric_clarification": "v2"}
    assert CL.classify_edit(prev, new).verdict == "surface_preserving"


# --- lineage edges + scheduling state ----------------------------------------

def test_minor_successor_retains_lineage_and_state(repo):
    family_id, card_id, v1 = _card_version(repo)
    lineage_id = CL.start_lineage(repo, genesis_card_version_id=v1, family_id=family_id, card_id=card_id, clock=CLOCK)
    # Seed state on the lineage.
    CL.rebuild_card_state(
        repo, card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED,
        review_events=[{"rating": Rating.GOOD, "elapsed_days": 0.0}], clock=CLOCK,
    )
    before = repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED)
    # A minor successor version appends inside the lineage; state unchanged.
    v2 = repo.ensure_activity_card_version(
        card_id=card_id, version=2, card_contract_hash="h2", contract_json="{}",
        schema_version=1, predecessor_card_version_id=v1, lineage_kind="minor_successor", clock=CLOCK,
    )
    CL.append_minor_successor(repo, lineage_id=lineage_id, from_card_version_id=v1, to_card_version_id=v2, clock=CLOCK)
    assert repo.lineage_for_card_version(v2) == lineage_id
    after = repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED)
    assert after["stability"] == before["stability"]
    assert after["id"] == before["id"]


def test_fork_starts_new_lineage_and_state_without_inherited_stability(repo):
    family_id, card_id, v1 = _card_version(repo)
    lineage_id = CL.start_lineage(repo, genesis_card_version_id=v1, family_id=family_id, card_id=card_id, clock=CLOCK)
    CL.rebuild_card_state(
        repo, card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED,
        review_events=[{"rating": Rating.GOOD, "elapsed_days": 0.0}, {"rating": Rating.GOOD, "elapsed_days": 3.0}],
        clock=CLOCK,
    )
    prior = repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED)
    assert prior["stability"] is not None

    forked_version = repo.ensure_activity_card_version(
        card_id=card_id, version=2, card_contract_hash="fork-h", contract_json="{}",
        schema_version=1, predecessor_card_version_id=v1, lineage_kind="fork", clock=CLOCK,
    )
    result = CL.fork_card(
        repo, predecessor_card_version_id=v1, forked_card_version_id=forked_version,
        scheduler_algorithm_version=SCHED, family_id=family_id, card_id=card_id,
        informed_difficulty_prior=prior["difficulty"], predecessor_lineage_id=lineage_id, clock=CLOCK,
    )
    assert result["lineage_id"] != lineage_id
    fork_state = repo.activity_card_state(card_lineage_id=result["lineage_id"], scheduler_algorithm_version=SCHED)
    # Informed difficulty prior allowed; stability NEVER inherited.
    assert fork_state["stability"] is None
    assert fork_state["retrievability"] is None
    # Predecessor state untouched.
    assert repo.activity_card_state(card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED)["stability"] == prior["stability"]
    # The fork edge is recorded.
    edges = repo.card_lineage_edges(result["lineage_id"])
    assert any(e["edge_kind"] == "semantic_fork" for e in edges)


# --- §9.5 rebuild is independent of the legacy cache -------------------------

def test_rebuild_is_deterministic_and_independent_of_practice_item_cache(repo):
    family_id, card_id, v1 = _card_version(repo)
    lineage_id = CL.start_lineage(repo, genesis_card_version_id=v1, family_id=family_id, card_id=card_id, clock=CLOCK)
    events = [
        {"rating": Rating.GOOD, "elapsed_days": 0.0},
        {"rating": Rating.HARD, "elapsed_days": 2.0},
        {"rating": Rating.GOOD, "elapsed_days": 5.0},
    ]
    rebuilt = CL.rebuild_card_state(
        repo, card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED, review_events=events, clock=CLOCK,
    )
    # A corrupted legacy practice_item_state cache is irrelevant: the authoritative
    # card-state rebuild replays from its own event stream (§9.5).
    repo.upsert_practice_item_state("pi-1", difficulty=999.0, stability=999.0, retrievability=0.0, clock=CLOCK)
    # A rebuild from the authoritative event stream is unaffected by the corruption.
    rebuilt_again = CL.rebuild_card_state(
        repo, card_lineage_id=lineage_id, scheduler_algorithm_version=SCHED, clock=CLOCK,
    )
    assert rebuilt_again["stability"] == rebuilt["stability"]
    assert rebuilt_again["difficulty"] == rebuilt["difficulty"]
    assert rebuilt_again["stability"] != 999.0
