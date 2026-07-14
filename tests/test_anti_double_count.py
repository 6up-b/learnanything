"""Anti-double-count invariants (knowledge-model §9.4, all six as literal tests).

These are the read-time integrity guarantees of the projection layer: evidence
originates only from attempts/grading/claims, each observation attaches once,
projections are deterministic/idempotent, certification is bounded and prior/
projection signals earn zero credit, direct evidence is never reintroduced via
graph priors or the LO residual, and replay reproduces identical derived state.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.blueprint_projection import project_lo_readiness
from learnloop.services.calibration_sessions import graph_propagated_prior
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO
from tests.test_km3_projections import (
    COMP_A,
    COMP_B,
    INTEG,
    LO_ID,
    build_blueprint_vault,
)


def _attempt(vault, repository, item_id, points, *, hints_used=0):
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW),
    )


def _fixture(tmp_path):
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _recall_snapshot(repository):
    return sorted(
        (r.facet_id, r.capability_key, r.practice_item_id or "", round(r.recall_alpha, 9), round(r.recall_beta, 9))
        for r in repository.canonical_facet_recall_states()
    )


def _ledger_snapshot(repository):
    return sorted(
        (
            c.facet_id,
            c.capability,
            round(c.direct_positive_mass, 9),
            round(c.direct_negative_mass, 9),
            round(c.certification_credit, 9),
            tuple(c.independent_surface_groups),
        )
        for c in repository.facet_capability_evidence_all()
    )


# 1. Evidence originates only from attempts/grading/claims; claims never earn mass.


def test_anti_double_count_claim_seeds_prior_but_earns_no_mass(tmp_path):
    vault, repository = _fixture(tmp_path)
    repository.insert_learner_claim(
        {
            "id": "claim_high",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": LO_ID,
            "evidence_family": "recall",
            "claimed_level": 0.95,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )
    project_canonical_facet_state(vault, repository)
    # A claim is a prior, not evidence: it creates no belief rows and no
    # certification credit (§9.4.1).
    assert repository.canonical_facet_recall_states() == []
    assert repository.facet_capability_evidence_all() == []


# 2. Each observation id is attached exactly once (bounded, idempotent lineage).


def test_anti_double_count_observation_attaches_once(tmp_path):
    vault, repository = _fixture(tmp_path)
    _attempt(vault, repository, "pi_comp_a", 4)
    # The single criterion's pseudo-mass is bounded by the attempt evidence mass:
    # one observation, counted once, not once per derived path (§9.4.2).
    cell = repository.facet_capability_evidence(COMP_A, "procedure_execution")
    assert cell is not None
    assert cell.direct_positive_mass <= 1.0 + 1e-9
    # Re-running the projection does not duplicate the observation's contribution.
    before = _ledger_snapshot(repository)
    project_canonical_facet_state(vault, repository)
    assert _ledger_snapshot(repository) == before


# 3. Projections are deterministic and idempotent.


def test_anti_double_count_projection_deterministic_and_idempotent(tmp_path):
    vault, repository = _fixture(tmp_path)
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 3)

    recall_before = _recall_snapshot(repository)
    ledger_before = _ledger_snapshot(repository)
    for _ in range(3):
        project_canonical_facet_state(vault, repository)
    assert _recall_snapshot(repository) == recall_before
    assert _ledger_snapshot(repository) == ledger_before

    # A derived LO readiness projection is a pure function of facet recall, never
    # an input to another projection: recomputing it twice is identical and does
    # not touch persisted state.
    lo = vault.learning_objects[LO_ID]
    a = project_lo_readiness(lo, lambda f, c: 0.7, slip=0.05)
    b = project_lo_readiness(lo, lambda f, c: 0.7, slip=0.05)
    assert a.as_dict() == b.as_dict()
    assert _recall_snapshot(repository) == recall_before


# 4. Certification bounded per group; projection/prior signals earn zero credit.


def test_anti_double_count_projection_signal_earns_zero_certification(tmp_path):
    vault, repository = _fixture(tmp_path)
    # A confident claim lifts predicted readiness (a prior), but grants no
    # certification credit — only direct evidence certifies (§9.4.4).
    repository.insert_learner_claim(
        {
            "id": "claim_high",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": LO_ID,
            "evidence_family": "recall",
            "claimed_level": 0.95,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )
    project_canonical_facet_state(vault, repository)
    assert repository.facet_capability_evidence(COMP_A, "procedure_execution") is None
    # The integration facet, never directly attempted, earns no credit even after
    # both components are demonstrated.
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 4)
    assert repository.facet_capability_evidence(INTEG, "coordination") is None


# 5. Direct evidence is never reintroduced through the graph prior/LO residual.


def test_anti_double_count_direct_evidence_not_refed_via_graph_prior(tmp_path):
    vault, repository = _fixture(tmp_path)
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 4)
    # The composite LO has strong direct facet evidence but no prerequisite edges;
    # its own evidence is NOT recycled as a graph-propagated prior (§9.4.5). The
    # graph prior draws only from prerequisite neighbours' mastery.
    assert graph_propagated_prior(vault, repository, LO_ID) is None


# 6. Replay reproduces identical marginals, ledgers, and projections.


def test_anti_double_count_replay_reproduces_identical_state(tmp_path):
    vault, repository = _fixture(tmp_path)
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 2)
    # An ambiguous/failed attempt path too, for the unresolved-cause ledger.
    _attempt(vault, repository, "pi_integrated", 0)

    recall_before = _recall_snapshot(repository)
    ledger_before = _ledger_snapshot(repository)
    causes_before = sorted(repository.open_unresolved_cause_observation_ids())

    rebuild_derived_state(vault, repository, clock=FrozenClock(NOW))

    assert _recall_snapshot(repository) == recall_before
    assert _ledger_snapshot(repository) == ledger_before
    assert sorted(repository.open_unresolved_cause_observation_ids()) == causes_before
