"""Tests for learner self-attributed misconceptions — probe-coverage extension.

Covers the spec_irt_difficulty.md §12.8 (v1) test plan: the trust-weighted label
mixture (monotonicity + w=0/w=1 boundaries + soft `mastered` downweight), the
density-modulated `c_eff` blend, the score-consistency gate, the locked-set split,
durable-probe promotion, replay idempotence, and the candidate-ranking picker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.probes import (
    Hypothesis,
    HypothesisSet,
    _apply_observation,
    _concept_closeness,
    _observation_likelihoods,
    _resolve_self_tag_weight,
    enter_probe,
    probe_posterior,
    rank_error_type_candidates,
    self_tag_weight,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import (
    Concept,
    ConceptEdge,
    ErrorType,
    LearningObject,
    LoadedVault,
    PracticeItem,
    Rubric,
    RubricFatalError,
)
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


# --- Concept-graph closeness (§12.3) ---------------------------------------


def test_concept_closeness_direct_one_hop_two_hop_and_disconnected():
    adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
    assert _concept_closeness(adjacency, "a", ["a"], 0.5) == 1.0  # source is itself a target
    assert _concept_closeness(adjacency, "a", ["b"], 0.5) == 0.5  # one hop
    assert _concept_closeness(adjacency, "a", ["c"], 0.5) == 0.25  # two hops
    assert _concept_closeness(adjacency, "a", ["zzz"], 0.5) == 0.0  # disconnected
    assert _concept_closeness(adjacency, "a", [], 0.5) == 0.0  # no related concepts
    assert _concept_closeness(adjacency, None, ["a"], 0.5) == 0.0  # missing source


# --- self_tag_weight: density-modulated c_eff + consistency gate (§12.3) ----


def _graph_vault(
    *,
    edges: list[tuple[str, str]],
    extra_concepts: list[str],
    related: list[str],
    item_concept: str = "c_item",
) -> tuple[LoadedVault, PracticeItem]:
    vault = LoadedVault(root=Path("."), config=LearnLoopConfig())
    for concept_id in {*extra_concepts, item_concept}:
        vault.concepts[concept_id] = Concept(id=concept_id, title=concept_id, created_at=NOW_ISO, updated_at=NOW_ISO)
    vault.edges = [
        ConceptEdge(
            id=f"edge_{index}",
            relation_type="related",
            source=source,
            target=target,
            created_at=NOW_ISO,
            updated_at=NOW_ISO,
        )
        for index, (source, target) in enumerate(edges)
    ]
    vault.error_types["misc_e"] = ErrorType(
        id="misc_e",
        title="Misc E",
        related_concepts=related,
        is_misconception=True,
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    vault.learning_objects["lo1"] = LearningObject(
        id="lo1",
        title="LO",
        subjects=["s"],
        concept=item_concept,
        knowledge_type="definition",
        summary="x",
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    item = PracticeItem(
        id="pi1",
        learning_object_id="lo1",
        practice_mode="short_answer",
        prompt="p",
        expected_answer="x",
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    vault.practice_items["pi1"] = item
    return vault, item


_K4 = [("c_item", "c_a"), ("c_item", "c_b"), ("c_item", "c_c"), ("c_a", "c_b"), ("c_a", "c_c"), ("c_b", "c_c")]


def test_self_tag_weight_sparse_graph_falls_back_to_w_base():
    # No edges -> rho_global = 0 -> c_eff = 1 (semantics off) -> w = w_base.
    vault, item = _graph_vault(edges=[], extra_concepts=[], related=["c_item"])
    assert self_tag_weight(vault, item, "misc_e", "low") == pytest.approx(0.5)


def test_self_tag_weight_dense_graph_genuine_mismatch_drops_to_zero():
    # Dense graph, both endpoints linkable, but the related concept is disconnected
    # from the item concept -> c_raw = 0 -> w -> 0.
    vault, item = _graph_vault(edges=_K4, extra_concepts=["c_a", "c_b", "c_c", "c_far"], related=["c_far"])
    assert self_tag_weight(vault, item, "misc_e", "low") == pytest.approx(0.0)


def test_self_tag_weight_dense_graph_close_neighbor_uses_closeness():
    # Dense graph, related concept is one hop away -> c_raw = hop_decay = 0.5 ->
    # w = w_base * 0.5 = 0.25 (semantics now bite).
    vault, item = _graph_vault(edges=_K4, extra_concepts=["c_a", "c_b", "c_c"], related=["c_a"])
    assert self_tag_weight(vault, item, "misc_e", "low") == pytest.approx(0.25)


def test_self_tag_weight_unlinked_endpoint_is_neutral():
    # No related concepts on the error -> rho_local = 0 -> c_eff = 1 even in a dense
    # graph (a missing link is not trusted when an endpoint cannot be linked).
    vault, item = _graph_vault(edges=_K4, extra_concepts=["c_a", "c_b", "c_c"], related=[])
    assert self_tag_weight(vault, item, "misc_e", "low") == pytest.approx(0.5)


def test_self_tag_weight_consistency_gate_zeroes_high_bucket():
    vault, item = _graph_vault(edges=[], extra_concepts=[], related=["c_item"])
    assert self_tag_weight(vault, item, "misc_e", "high") == 0.0


def test_resolve_self_tag_weight_only_fires_for_in_set_non_fatal_label():
    vault, item = _graph_vault(edges=[], extra_concepts=[], related=["c_item"])
    set_with = HypothesisSet(
        "lo1",
        [Hypothesis("mastered"), Hypothesis("misconception:misc_e", error_type="misc_e")],
        {"mastered": 0.5, "misconception:misc_e": 0.5},
    )
    set_without = HypothesisSet("lo1", [Hypothesis("mastered"), Hypothesis("unfamiliar")], {"mastered": 0.5, "unfamiliar": 0.5})
    fatal_rubric = Rubric(max_points=4, criteria=[], fatal_errors=[RubricFatalError(id="misc_e", description="d", max_grade=1)])

    assert _resolve_self_tag_weight(vault, item, None, set_with, "misc_e", "low") == pytest.approx(0.5)
    assert _resolve_self_tag_weight(vault, item, None, set_without, "misc_e", "low") is None  # not a hypothesis
    assert _resolve_self_tag_weight(vault, item, fatal_rubric, set_with, "misc_e", "low") is None  # rubric-fatal
    assert _resolve_self_tag_weight(vault, item, None, set_with, None, "low") is None  # no label


# --- Trust-weighted label mixture (§12.2) ----------------------------------


def _set() -> HypothesisSet:
    return HypothesisSet(
        learning_object_id="lo",
        hypotheses=[
            Hypothesis("mastered"),
            Hypothesis("unfamiliar"),
            Hypothesis("misconception:E", error_type="E"),
        ],
        prior={"mastered": 1 / 3, "unfamiliar": 1 / 3, "misconception:E": 1 / 3},
    )


def _item(*, fatal_e: bool) -> PracticeItem:
    fatal_errors = [RubricFatalError(id="E", description="d", max_grade=1)] if fatal_e else []
    return PracticeItem(
        id="pi",
        learning_object_id="lo",
        practice_mode="short_answer",
        prompt="p",
        expected_answer="x",
        grading_rubric=Rubric(max_points=4, criteria=[], fatal_errors=fatal_errors),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )


def test_mixture_w0_reproduces_no_label_update_bit_for_bit():
    hypothesis_set = _set()
    item = _item(fatal_e=False)
    mixture = _observation_likelihoods(hypothesis_set, item, item.grading_rubric, "low", "E", self_tag_weight=0.0)
    no_label = _observation_likelihoods(hypothesis_set, item, item.grading_rubric, "low", None)
    assert mixture == pytest.approx(no_label)


def test_mixture_w1_equals_rubric_fatal_path():
    hypothesis_set = _set()
    self_tag_item = _item(fatal_e=False)
    fatal_item = _item(fatal_e=True)
    mixture = _observation_likelihoods(hypothesis_set, self_tag_item, self_tag_item.grading_rubric, "low", "E", self_tag_weight=1.0)
    rubric_fatal = _observation_likelihoods(hypothesis_set, fatal_item, fatal_item.grading_rubric, "low", "E")
    assert mixture == pytest.approx(rubric_fatal)


def test_mixture_posterior_misconception_is_monotone_in_w():
    hypothesis_set = _set()
    item = _item(fatal_e=False)
    posteriors = [
        _apply_observation(hypothesis_set, item, item.grading_rubric, "low", "E", dict(hypothesis_set.prior), self_tag_weight=w)[
            "misconception:E"
        ]
        for w in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]
    assert all(later > earlier for earlier, later in zip(posteriors, posteriors[1:]))


def test_mixture_softly_downweights_mastered_without_eliminating_it():
    hypothesis_set = _set()
    item = _item(fatal_e=False)
    posterior = _apply_observation(hypothesis_set, item, item.grading_rubric, "low", "E", dict(hypothesis_set.prior), self_tag_weight=0.5)
    assert 0.0 < posterior["mastered"] < hypothesis_set.prior["mastered"]


# --- Integration: probe replay with a self-tagged misconception -------------


def _vault_with_self_tag_item(root: Path):
    """Basic vault + a second item on the same LO whose rubric does *not* probe the
    misconception, plus a second (non-misconception) error type for picker tests."""

    paths = create_basic_vault(root)
    write_yaml(
        paths.error_types_path,
        {
            "schema_version": 1,
            "error_types": [
                {
                    "id": "conceptual_slip",
                    "title": "Conceptual slip",
                    "description": "The answer confuses the core definition.",
                    "related_concepts": ["singular_value_decomposition"],
                    "severity_default": 0.7,
                    "is_misconception": True,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                {
                    "id": "arithmetic_slip",
                    "title": "Arithmetic slip",
                    "description": "A careless arithmetic mistake.",
                    "related_concepts": [],
                    "severity_default": 0.3,
                    "is_misconception": False,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
            ],
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_002"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_002",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Apply SVD.",
            "expected_answer": "An application.",
            "difficulty": 0.5,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            # No fatal_errors: this item does NOT rubric-probe conceptual_slip.
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct application."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    return paths


def _insert_active_misconception(repository: Repository) -> None:
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def _self_tag_attempt(repository, loaded):
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_002", learner_answer_md="answer"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )


def test_self_tag_on_non_probing_item_credits_misconception(tmp_path):
    paths = _vault_with_self_tag_item(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _insert_active_misconception(repository)  # so misconception:E is in the locked set
    loaded = load_vault(tmp_path / "vault")
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))

    _self_tag_attempt(repository, loaded)

    posterior = probe_posterior(loaded, repository, "lo_svd_definition")
    assert posterior is not None
    # The mixture credits the self-tagged misconception even though the item's rubric
    # does not probe it (the §11.3 coverage gap) — previously this read as unfamiliar.
    assert posterior.posterior["misconception:conceptual_slip"] > posterior.prior["misconception:conceptual_slip"]
    assert posterior.posterior["mastered"] < posterior.prior["mastered"]
    assert sum(posterior.posterior.values()) == pytest.approx(1.0)


def test_self_tag_replay_is_idempotent(tmp_path):
    paths = _vault_with_self_tag_item(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _insert_active_misconception(repository)
    loaded = load_vault(tmp_path / "vault")
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    _self_tag_attempt(repository, loaded)

    first = probe_posterior(loaded, repository, "lo_svd_definition")
    second = probe_posterior(loaded, repository, "lo_svd_definition")
    assert first.posterior == second.posterior
    assert first.attempts == second.attempts


def test_brand_new_self_tag_does_not_touch_current_posterior_but_seeds_next_set(tmp_path):
    paths = _vault_with_self_tag_item(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(tmp_path / "vault")
    # No active misconception yet, so the locked set is {mastered, unfamiliar} only.
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    locked = repository.fetch_hypothesis_set(repository.probe_state("lo_svd_definition").hypothesis_set_id)
    assert "misconception:conceptual_slip" not in {h["label"] for h in locked["hypotheses"]}

    _self_tag_attempt(repository, loaded)  # attaches a label not in the locked set

    posterior = probe_posterior(loaded, repository, "lo_svd_definition")
    # Effect 2 only: the score bucket carries this attempt (a low score reads as
    # unfamiliarity); the label seeds the *next* hypothesis set via the error event.
    assert posterior.posterior["unfamiliar"] > posterior.prior["unfamiliar"]
    next_set = enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    assert "misconception:conceptual_slip" in {h.label for h in next_set.hypotheses}


# --- Durable-probe promotion (§12.4) ---------------------------------------


def test_repeated_self_tag_promotes_to_one_reviewed_fatal_error_proposal(tmp_path):
    paths = _vault_with_self_tag_item(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(tmp_path / "vault")

    for _ in range(3):  # promotion_threshold default = 3
        _self_tag_attempt(repository, loaded)

    promotions = [batch for batch in repository.proposal_batches() if batch["purpose"] == "self_tag_promotion"]
    assert len(promotions) == 1
    items = repository.proposal_items(promotions[0]["id"])
    assert len(items) == 1
    assert items[0]["item_type"] == "rubric"
    assert items[0]["operation"] == "update"
    assert items[0]["decision"] == "pending"  # never auto-applies
    fatal_ids = {fatal_error["id"] for fatal_error in items[0]["payload"]["fatal_errors"]}
    assert "conceptual_slip" in fatal_ids

    # A fourth self-tag does not queue a second proposal (fires exactly once).
    _self_tag_attempt(repository, loaded)
    promotions_after = [batch for batch in repository.proposal_batches() if batch["purpose"] == "self_tag_promotion"]
    assert len(promotions_after) == 1


def test_no_promotion_below_threshold(tmp_path):
    paths = _vault_with_self_tag_item(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(tmp_path / "vault")

    _self_tag_attempt(repository, loaded)
    _self_tag_attempt(repository, loaded)

    assert [batch for batch in repository.proposal_batches() if batch["purpose"] == "self_tag_promotion"] == []


def test_no_promotion_when_label_already_rubric_fatal(tmp_path):
    # pi_svd_define_001's rubric already lists conceptual_slip as a fatal error, so
    # self-tagging it there is the rubric-asserted path and must not re-propose it.
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(tmp_path / "vault")
    for _ in range(3):
        complete_self_graded_attempt(
            loaded,
            repository,
            AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="answer"),
            SelfGradeInput(criterion_points={"correctness": 0}, confidence=4, fatal_errors=["conceptual_slip"]),
            clock=FrozenClock(NOW),
        )
    assert [batch for batch in repository.proposal_batches() if batch["purpose"] == "self_tag_promotion"] == []


# --- Candidate-ranking picker (§12.5) --------------------------------------


def test_candidate_ranking_prefers_concept_relevant_misconception(tmp_path):
    _vault_with_self_tag_item(tmp_path / "vault")
    loaded = load_vault(tmp_path / "vault")
    item = loaded.practice_items["pi_svd_define_002"]

    candidates = rank_error_type_candidates(loaded, item=item)

    assert candidates[0].error_type == "conceptual_slip"
    assert candidates[0].is_misconception


def test_candidate_ranking_fuzzy_query_surfaces_match(tmp_path):
    _vault_with_self_tag_item(tmp_path / "vault")
    loaded = load_vault(tmp_path / "vault")
    item = loaded.practice_items["pi_svd_define_002"]

    candidates = rank_error_type_candidates(loaded, item=item, query="arith")

    assert candidates[0].error_type == "arithmetic_slip"
