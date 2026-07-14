"""KM4 — mechanism taxonomy remap, compositional misconceptions, promotion
discipline, and contrast-probe parameterization (knowledge-model §10, §16).

No LLM: all grader payloads are canned; deterministic.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.error_taxonomy_map import (
    MECHANISM_TAXONOMY,
    map_legacy_error_type,
)
from learnloop.services.misconceptions import normalize_attempt_misconceptions
from learnloop.services.probe_families import CONTRAST_CONFUSABLE_V1
from learnloop.services.probe_instance_generation import ensure_instrument_card
from learnloop.services.taxonomy_regrade import run_taxonomy_regrade_checks
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CONCEPT_ID = "singular_value_decomposition"


def _mvp06(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(tmp_path / "vault"), Repository(paths.sqlite_path)


def _mvp07(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    return load_vault(tmp_path / "vault"), Repository(paths.sqlite_path)


def _insert_attempt(repository, *, attempt_id, item_id=ITEM_ID, attempt_type="independent_attempt", grader_confidence=None):
    row = {
        "id": attempt_id,
        "practice_item_id": item_id,
        "learning_object_id": LO_ID,
        "practice_mode": "short_answer",
        "attempt_type": attempt_type,
        "rubric_score": 1,
        "correctness": 0.0,
        "error_type": None,
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if grader_confidence is not None:
        row["grader_confidence"] = grader_confidence
    repository.insert_practice_attempt(row)


def _insert_mc_event(repository, *, attempt_id, event_id, statement, error_type="conceptual_schema_error", facets=None, consistent=None):
    repository.insert_error_event(
        {
            "id": event_id,
            "attempt_id": attempt_id,
            "learning_object_id": LO_ID,
            "error_type": error_type,
            "severity": 0.7,
            "is_misconception": True,
            "misconception_statement": statement,
            "misconception_consistent_answer": consistent,
            "repair_plan": {"target_evidence_families": facets} if facets else None,
            "status": "active",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


# -- §16 Taxonomy row: legacy mapping ------------------------------------------


def test_legacy_error_types_map_per_spec():
    # §10.1 verbatim mapping.
    assert map_legacy_error_type("recall_failure") == "retrieval_failure"
    assert map_legacy_error_type("conceptual_error") == "conceptual_schema_error"
    assert map_legacy_error_type("procedure_error") == "procedure_execution_error"
    assert map_legacy_error_type("notation_error") == "representation_notation_error"
    assert map_legacy_error_type("assumption_error") == "condition_assumption_error"
    assert map_legacy_error_type("theorem_selection_error") == "selection_planning_error"
    assert map_legacy_error_type("transfer_failure") == "transfer_context_error"
    # Reviewed decisions.
    assert map_legacy_error_type("arithmetic_slip") == "local_slip"
    assert map_legacy_error_type("scaffold_failure") == "retrieval_failure"
    # mvp-0.6 grader-vocabulary synonyms.
    assert map_legacy_error_type("conceptual_slip") == "conceptual_schema_error"
    assert map_legacy_error_type("procedure_misapplication") == "procedure_execution_error"
    assert map_legacy_error_type("incomplete_answer") == "local_slip"
    # Nine-value taxonomy; identity on canonical values; pass-through for unknowns.
    assert len(MECHANISM_TAXONOMY) == 9
    for mechanism in MECHANISM_TAXONOMY:
        assert map_legacy_error_type(mechanism) == mechanism
    assert map_legacy_error_type("confuses_x_with_y") == "confuses_x_with_y"
    assert map_legacy_error_type(None) is None


def test_arithmetic_slip_and_scaffold_failure_mapping_decision():
    # arithmetic_slip is the canonical local execution error; scaffold_failure is
    # a retrieval lapse that failed despite support (severity, not mechanism).
    assert map_legacy_error_type("arithmetic_slip") == "local_slip"
    assert map_legacy_error_type("scaffold_failure") == "retrieval_failure"


def test_grader_prompt_version_bumped():
    assert GRADING_PROMPT_VERSION == "mvp-0.7-mechanism-taxonomy"
    assert GRADING_PROMPT_VERSION != "mvp-0.5-misconception-statements"


def test_mvp07_grader_taxonomy_emits_mechanism_vocabulary(tmp_path):
    from learnloop.services.grading import _grading_error_taxonomy

    vault06, _ = _mvp06(tmp_path / "a")
    vault07, _ = _mvp07(tmp_path / "b")
    ids06 = {e["id"] for e in _grading_error_taxonomy(vault06)["canonical_error_types"]}
    ids07 = {e["id"] for e in _grading_error_taxonomy(vault07)["canonical_error_types"]}
    assert ids07 == set(MECHANISM_TAXONOMY)
    assert "recall_failure" in ids06 and "recall_failure" not in ids07


def test_config_error_impacts_resolve_through_map(tmp_path):
    # A legacy [error_impacts] TOML stays consumable when the grader emits the
    # canonical mechanism vocabulary (retrieval_failure / local_slip).
    from learnloop.services.recall_coverage import _resolve_error_impact_config

    vault07, _ = _mvp07(tmp_path)
    config = vault07.config
    assert _resolve_error_impact_config(config, "recall_failure") is not None  # direct
    assert _resolve_error_impact_config(config, "retrieval_failure") is not None  # mapped
    assert _resolve_error_impact_config(config, "local_slip") is not None  # arithmetic_slip


# -- §16 regrade-check ---------------------------------------------------------


class _CannedGrader:
    """Returns a fixed attribution echoing the context's ids (no LLM)."""

    def __init__(self, error_type: str, *, is_misconception: bool = True):
        self._error_type = error_type
        self._is_misconception = is_misconception

    def run_grading_proposal(self, context):
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=1,
            criterion_evidence=[
                CriterionEvidence(criterion_id="correctness", points_awarded=1, evidence="Partial.")
            ],
            fatal_errors=[],
            error_attributions=[
                ErrorAttribution(
                    error_type=self._error_type,
                    severity=0.6,
                    evidence="Confuses the definition.",
                    is_misconception=self._is_misconception,
                    misconception_statement="believes X" if self._is_misconception else None,
                    target_evidence_families=[],
                    target_criterion_ids=[],
                )
            ],
            grader_confidence=0.9,
            repair_suggestions=[],
        )


def test_taxonomy_regrade_check_no_attribution_regressions(tmp_path):
    # A graded attempt attributed the legacy `conceptual_slip`; the bumped grader
    # now emits the mechanism `conceptual_schema_error`. Both resolve to the same
    # mechanism, so there is NO attribution regression.
    vault, repository = _mvp06(tmp_path)
    _insert_attempt(repository, attempt_id="att1")
    _insert_mc_event(
        repository,
        attempt_id="att1",
        event_id="ev1",
        statement="believes SVD equals eigendecomposition",
        error_type="conceptual_slip",
    )
    report = run_taxonomy_regrade_checks(
        vault, repository, _CannedGrader("conceptual_schema_error"), limit=10
    )
    assert report["checked"] == 1
    assert report["no_regressions"] is True
    assert report["regression_count"] == 0

    # Negative control: a regrade that drops the mechanism IS flagged.
    regression_report = run_taxonomy_regrade_checks(
        vault, repository, _CannedGrader("retrieval_failure"), limit=10
    )
    assert regression_report["no_regressions"] is False
    assert regression_report["regressions"][0]["dropped_mechanisms"] == ["conceptual_schema_error"]


# -- §10.2 compositional record parameterizes contrast probe -------------------


def test_compositional_record_parameterizes_contrast_probe(tmp_path):
    vault, repository = _mvp07(tmp_path)
    target = "facet_matrix_symmetry_definition"
    confused = "facet_orthogonal_matrix_definition"
    repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="believes A^T = A implies A^T A = I",
        concept_id=CONCEPT_ID,
        status="active",
        mechanism="conceptual_schema_error",
        operation="property_substitution",
        target_facet=target,
        confused_with_facet=confused,
        clock=FrozenClock(NOW),
    )
    result = ensure_instrument_card(
        vault, repository, LO_ID, CONTRAST_CONFUSABLE_V1, clock=FrozenClock(NOW)
    )
    assert result is not None
    card, _template = result
    assert card.bindings["target_facet"] == target
    assert card.bindings["confused_with_facet"] == confused
    # The instrument targets exactly the two bound facets of the §10.2 record.
    assert set(card.target_facets) == {target, confused}


# -- §10.3 promotion discipline ------------------------------------------------


def test_unresolved_cause_set_does_not_mint_misconception(tmp_path):
    vault, repository = _mvp07(tmp_path)
    _insert_attempt(repository, attempt_id="att1")
    repository.insert_unresolved_cause_factor(
        attempt_id="att1",
        candidate_causes=[{"facet": "recall", "capability": "shared"}],
        algorithm_version="mvp-0.7",
        observation_id="att1:0",
        clock=FrozenClock(NOW),
    )
    _insert_mc_event(
        repository,
        attempt_id="att1",
        event_id="ev1",
        statement="believes SVD equals eigendecomposition",
    )
    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert touched == []
    assert repository.misconceptions_for_learning_object(LO_ID, statuses=("active", "resolving", "resolved")) == []


def test_promotion_requires_independent_surface_or_probe_reproduction(tmp_path):
    vault, repository = _mvp07(tmp_path)
    statement = "believes SVD equals eigendecomposition"

    # A single ordinary attempt stays a candidate — no durable misconception.
    _insert_attempt(repository, attempt_id="att1", item_id=ITEM_ID)
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement=statement)
    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert touched == []
    assert repository.misconceptions_for_learning_object(LO_ID) == []
    candidates = repository.misconception_candidates_for_learning_object(LO_ID)
    assert len(candidates) == 1 and candidates[0]["status"] == "candidate"

    # A targeted diagnostic probe reproducing the belief promotes it (§10.3).
    _insert_attempt(repository, attempt_id="att2", item_id=ITEM_ID, attempt_type="diagnostic_probe")
    _insert_mc_event(repository, attempt_id="att2", event_id="ev2", statement=statement)
    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att2", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert len(touched) == 1
    durable = repository.misconceptions_for_learning_object(LO_ID)
    assert len(durable) == 1
    assert durable[0].promotion_reason == "probe_reproduction"
    assert durable[0].mechanism == "conceptual_schema_error"


def test_promotion_on_independent_surface(tmp_path):
    from tests.helpers import add_followup_item

    paths = create_basic_vault(tmp_path / "vault")
    add_followup_item(tmp_path / "vault", item_id="pi_svd_define_002")
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    statement = "believes SVD equals eigendecomposition"

    _insert_attempt(repository, attempt_id="att1", item_id=ITEM_ID)
    _insert_mc_event(repository, attempt_id="att1", event_id="ev1", statement=statement)
    assert normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    ) == []

    # A repeat on a second, independent item (surface) promotes to durable.
    _insert_attempt(repository, attempt_id="att2", item_id="pi_svd_define_002")
    _insert_mc_event(repository, attempt_id="att2", event_id="ev2", statement=statement)
    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att2", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert len(touched) == 1
    durable = repository.misconceptions_for_learning_object(LO_ID)
    assert len(durable) == 1
    assert durable[0].promotion_reason == "independent_surface"


def test_legacy_vault_still_mints_immediately(tmp_path):
    # mvp-0.6 promotion discipline is unchanged: one statement mints one row.
    vault, repository = _mvp06(tmp_path)
    _insert_attempt(repository, attempt_id="att1")
    _insert_mc_event(
        repository, attempt_id="att1", event_id="ev1", statement="believes X", error_type="conceptual_slip"
    )
    touched = normalize_attempt_misconceptions(
        vault, repository, attempt_id="att1", learning_object_id=LO_ID, clock=FrozenClock(NOW)
    )
    assert len(touched) == 1
    assert len(repository.misconceptions_for_learning_object(LO_ID)) == 1
