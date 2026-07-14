"""KM2 write-path + replay: canonical belief under mvp-0.7.

Builds a small hand-authored mvp-0.7 vault (two LOs sharing one canonical facet,
criterion targets, evidence fingerprints) and drives real attempts through
`complete_self_graded_attempt` so the canonical projection runs end to end.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    create_basic_vault,
    set_algorithm_version,
    write_facets,
)

SHARED = "facet_svd_factorization"
SELECT = "facet_svd_method_selection"


def _rubric(criterion_id, targets, *, points=4, correlation_group=None, depends_on=None):
    crit = {
        "id": criterion_id,
        "points": points,
        "description": f"{criterion_id} criterion.",
        "targets": targets,
    }
    if correlation_group is not None:
        crit["correlation_group"] = correlation_group
    if depends_on is not None:
        crit["depends_on"] = depends_on
    return {"max_points": points, "criteria": [crit], "fatal_errors": []}


def _item(item_id, lo_id, *, evidence_facets, rubric, fingerprint=None):
    payload = {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": lo_id,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": evidence_facets,
        "evidence_weights": {f: 1.0 for f in evidence_facets},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "An answer.",
        "difficulty": 0.5,
        "grading_rubric": rubric,
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if fingerprint is not None:
        payload["evidence_fingerprint"] = fingerprint
    return payload


def _lo(lo_id, title, summary):
    return {
        "schema_version": 1,
        "id": lo_id,
        "title": title,
        "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition",
        "knowledge_type": "definition",
        "status": "active",
        "contradicts": None,
        "summary": summary,
        "prerequisites": [],
        "confusables": [],
        "difficulty_prior": 0.55,
        "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def build_mvp07_vault(root: Path):
    """A minimal mvp-0.7 fixture: one shared canonical facet across two LOs."""

    paths = create_basic_vault(root)
    # No goal, so certified scope does not lock the facet during grace-window work.
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [
            {"id": SHARED, "kind": "definition", "claim": "SVD factorizes into U, Sigma, V^T."},
            {"id": SELECT, "kind": "applicability_condition", "claim": "When SVD applies."},
            {"id": "recall", "kind": "definition", "claim": "SVD recall."},
        ],
    )
    # LO 1 already exists (lo_svd_definition). Re-author its item to target the
    # shared canonical facet at retrieval capability.
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        _item(
            "pi_svd_define_001",
            "lo_svd_definition",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "correctness",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_definition",
            ),
            fingerprint={"source_family": "chapter3-definition"},
        ),
    )
    # LO 2: a second learning object on the same concept, whose item exercises
    # the SAME shared canonical facet -> one shared belief parent.
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_application"),
        _lo("lo_svd_application", "SVD application", "Applying SVD in practice."),
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_apply_001"),
        _item(
            "pi_svd_apply_001",
            "lo_svd_application",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "uses_factorization",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_application",
            ),
            fingerprint={"source_family": "chapter5-application"},
        ),
    )
    # A near-clone under LO 2 sharing LO 1's item's source-example family: it
    # must NOT mint a fresh independent surface group (§6).
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_clone_001"),
        _item(
            "pi_svd_clone_001",
            "lo_svd_application",
            evidence_facets=[SHARED],
            rubric=_rubric(
                "uses_factorization",
                [{"facet": SHARED, "capability": "retrieval", "role": "primary"}],
                correlation_group="svd_definition",
            ),
            fingerprint={"source_family": "chapter3-definition"},  # same as define item
        ),
    )
    # An item whose single whole-item criterion maps to several candidate facets
    # with no resolving attribution: a wrong answer is an unresolved cause set.
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_ambiguous_001"),
        _item(
            "pi_svd_ambiguous_001",
            "lo_svd_definition",
            evidence_facets=[SHARED, SELECT],
            rubric=_rubric(
                "whole_item",
                [
                    {"facet": SHARED, "capability": "retrieval", "role": "primary"},
                    {"facet": SELECT, "capability": "method_selection", "role": "primary"},
                ],
            ),
            fingerprint={"source_family": "chapter7-ambiguous"},
        ),
    )
    set_algorithm_version(paths, "mvp-0.7")
    return paths


def _attempt(vault, repository, item_id, points, clock, *, hints_used=0):
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
        ),
        SelfGradeInput(criterion_points=points, fatal_errors=[], confidence=4),
        clock=clock,
    )


@pytest.fixture
def mvp07(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_two_los_share_one_facet_parent(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    aggregates = [
        s
        for s in repository.canonical_facet_recall_states()
        if s.facet_id == SHARED and s.capability_key == "retrieval" and s.practice_item_id is None
    ]
    # Exactly ONE shared aggregate parent, moved by both LOs' attempts.
    assert len(aggregates) == 1
    parent = aggregates[0]
    # Two positive observations accrued onto the shared parent (alpha grew twice
    # past the 1.0 prior).
    assert parent.recall_alpha > 2.0
    assert parent.recall_mean > 0.6


def test_retrieval_evidence_cannot_certify_method_selection(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)

    retrieval = repository.facet_capability_evidence(SHARED, "retrieval")
    assert retrieval is not None
    assert retrieval.certification_credit > 0
    # No method_selection credit is minted from a retrieval observation.
    assert repository.facet_capability_evidence(SHARED, "method_selection") is None


def test_certification_credit_zero_when_assisted(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock, hints_used=1)
    retrieval = repository.facet_capability_evidence(SHARED, "retrieval")
    assert retrieval is not None
    # Hinted attempt: positive mass accrues but certification credit is zero.
    assert retrieval.direct_positive_mass > 0
    assert retrieval.certification_credit == pytest.approx(0.0)


def test_near_clones_globally_discounted(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    # Two attempts on items sharing one source-example family (define + clone).
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_clone_001", {"uses_factorization": 4}, clock)

    ledger = repository.facet_capability_evidence(SHARED, "retrieval")
    assert ledger is not None
    # The clone shares the source family -> a single independent surface group,
    # not two.
    assert ledger.independent_surface_groups == ["chapter3-definition"]

    parent = repository.canonical_facet_recall_state(SHARED, "retrieval", None)
    assert parent is not None
    # The clone contributes NO fresh independent mass (one independent surface).
    assert parent.independent_evidence_mass == pytest.approx(1.0)
    # But it still contributes a discounted inference update: alpha grew past the
    # single-observation value (2.0) yet stayed below two full observations (3.0).
    assert 2.0 < parent.recall_alpha < 3.0


def test_wrong_answer_no_work_creates_unresolved_cause_set(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, clock)

    # No marginal negative mass smeared across the candidate facets.
    assert repository.canonical_facet_recall_state(SHARED, "retrieval", None) is None
    assert repository.canonical_facet_recall_state(SELECT, "method_selection", None) is None
    # An unresolved joint-cause factor is recorded instead.
    assert repository.open_unresolved_cause_observation_ids()


def test_explicit_failure_attribution_penalizes_only_selected_target(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_ambiguous_001",
                learner_answer_md="I selected the wrong method.",
            ),
            attempt_id="att_explicit_method_failure",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"whole_item": 0.0},
                evidence_rows=[
                    {
                        "id": "ge_explicit_method_failure",
                        "criterion_id": "whole_item",
                        "points_awarded": 0.0,
                        "evidence": "Method-selection error was localized.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        "conceptual_slip",
                        0.8,
                        target_evidence_families=[SELECT],
                        target_criterion_ids=["whole_item"],
                    )
                ],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=clock,
    )

    selected = repository.canonical_facet_recall_state(
        SELECT, "method_selection", None
    )
    unselected = repository.canonical_facet_recall_state(SHARED, "retrieval", None)
    assert selected is not None and selected.recall_beta > 1.0
    assert unselected is None
    assert not repository.open_unresolved_cause_observation_ids()


def test_golden_replay_identity_mvp07(mvp07):
    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 3}, clock)

    def snapshot():
        recall = {
            (s.facet_id, s.capability_key, s.practice_item_id): (
                round(s.recall_alpha, 9),
                round(s.recall_beta, 9),
                round(s.independent_evidence_mass, 9),
                s.consecutive_failures,
            )
            for s in repository.canonical_facet_recall_states()
        }
        cap = {
            (c.facet_id, c.capability): (
                round(c.direct_positive_mass, 9),
                round(c.direct_negative_mass, 9),
                round(c.certification_credit, 9),
                tuple(c.independent_surface_groups),
            )
            for c in repository.facet_capability_evidence_all()
        }
        return recall, cap

    live = snapshot()
    rebuild_derived_state(vault, repository)
    replayed_once = snapshot()
    rebuild_derived_state(vault, repository)
    replayed_twice = snapshot()

    assert live == replayed_once
    assert replayed_once == replayed_twice


def test_rebuild_uses_presented_contract_after_live_target_change(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)

    def canonical_snapshot():
        return (
            [
                (
                    row.facet_id,
                    row.capability_key,
                    row.practice_item_id,
                    row.recall_alpha,
                    row.recall_beta,
                    row.independent_evidence_mass,
                )
                for row in repository.canonical_facet_recall_states()
            ],
            [
                (
                    row.facet_id,
                    row.capability,
                    row.direct_positive_mass,
                    row.direct_negative_mass,
                    row.certification_credit,
                    tuple(row.independent_surface_groups),
                )
                for row in repository.facet_capability_evidence_all()
            ],
        )

    live = canonical_snapshot()
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    changed = read_yaml(item_path)
    changed["evidence_facets"] = [SELECT]
    changed["evidence_weights"] = {SELECT: 1.0}
    changed["grading_rubric"] = _rubric(
        "new_live_criterion",
        [{"facet": SELECT, "capability": "method_selection", "role": "primary"}],
    )
    write_yaml(item_path, changed)

    mutated_vault = load_vault(paths.root)
    rebuild_derived_state(mutated_vault, repository)
    assert canonical_snapshot() == live
