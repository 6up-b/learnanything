"""A1: minimal-repair selection becomes structural.

``spec_diagnostic_augmentation_v1.md`` §2 A1 plus standing constraint 4 --
deterministic quantities outrank model-reported ones wherever both exist.

Before v2 the rank was ``(contradiction, invalid_rule, protected_violation,
latent_cost, checkpoint_cost, burden, repair_class_id)``: after the three
firewall booleans every key was a ``len()`` of a model-supplied list or the
model's own ``expected_minutes``. Backtracking depth and trace edit cost were
both computed and both written only into the receipt. These tests pin the new
order and the two failure modes it makes visible.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.causal_attribution import (
    LATENT_COST_RESOLUTION_FLOOR,
    REPAIR_POLICY_VERSION,
    REPAIR_SELECTION_BASES,
    select_minimal_repair,
    validate_repair_candidate,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import TraceContract, TraceRecipe
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault

# A three-step chain: c1 -> c2 -> c3. Depth(c1)=0, depth(c2)=1, depth(c3)=2, so
# max depth is 2 and BACKTRACKING depth is 2 - depth(changed): repairing the
# final step backtracks 0, repairing the first backtracks 2.
CHAIN = TraceContract(
    status="available",
    recipes=[
        TraceRecipe(
            id="r1",
            checkpoints=["c1", "c2", "c3"],
            dependencies={"c2": ["c1"], "c3": ["c2"]},
        )
    ],
)
NO_DECOMPOSITION = TraceContract(status="no_reliable_decomposition", recipes=[])


def _candidate(operator, *, checkpoints, latent, minutes, answer="fixed answer"):
    return {
        "practice_mode": "repair",
        "operator": operator,
        "target_refs": [{"kind": "criterion", "criterion_id": "failed"}],
        "expected_minutes": minutes,
        "repaired_trace": {
            "learner_work_prefix": "learner work",
            "minimal_edit": f"apply {operator}",
            "repaired_answer_md": answer,
            "changed_latent_claims": [f"claim_{i}" for i in range(latent)],
            "changed_checkpoint_ids": list(checkpoints),
        },
    }


def _operator_of(selection):
    return selection["selected"]["repair_class"]["operator"]


# --- validation: a hallucinated checkpoint is rejected, not silently None ---


def test_checkpoint_outside_every_recipe_is_a_typed_rejection(tmp_path):
    """A checkpoint id that names no authored step used to make every recipe
    fail the subset test, so the depth quietly became ``None`` and the ONE
    deterministic ordering term degraded invisibly."""

    hallucinated = _candidate(
        "invent_a_step", checkpoints=["c9_does_not_exist"], latent=0, minutes=1
    )
    validation = validate_repair_candidate(hallucinated, trace_contract=CHAIN)
    assert "unverifiable_checkpoint_claim" in validation.reasons
    # A false claim, not a missing one.
    assert validation.status == "invalid"
    assert validation.structural_checks["checkpoint_claims_verified"] is False

    # ...and the selector refuses it outright rather than ranking it first on
    # its (attractive) zero latent cost and one-minute burden.
    honest = _candidate("repair_last_step", checkpoints=["c3"], latent=4, minutes=30)
    selection = select_minimal_repair(
        [hallucinated, honest], trace_contract=CHAIN
    )
    assert _operator_of(selection) == "repair_last_step"
    rejected = {
        entry["repair_class_id"]: entry["reasons"] for entry in selection["rejected"]
    }
    assert any(
        "unverifiable_checkpoint_claim" in reasons for reasons in rejected.values()
    )


def test_claiming_checkpoints_on_an_undecomposable_item_is_unverifiable():
    """The item states it has no reliable step structure, so no id can be
    checked against one. Claiming NONE stays fine."""

    claiming = _candidate("touch_a_step", checkpoints=["c1"], latent=0, minutes=1)
    assert (
        "unverifiable_checkpoint_claim"
        in validate_repair_candidate(
            claiming, trace_contract=NO_DECOMPOSITION
        ).reasons
    )
    quiet = _candidate("edit_the_span", checkpoints=[], latent=1, minutes=2)
    assert (
        "unverifiable_checkpoint_claim"
        not in validate_repair_candidate(
            quiet, trace_contract=NO_DECOMPOSITION
        ).reasons
    )


def test_no_trace_contract_cannot_verify_and_does_not_pretend_to():
    """"The claim is false" and "the question could not be asked" are different
    facts. Without a contract the validator asserts neither."""

    claiming = _candidate("touch_a_step", checkpoints=["c1"], latent=0, minutes=1)
    validation = validate_repair_candidate(claiming)
    assert "unverifiable_checkpoint_claim" not in validation.reasons
    assert "checkpoint_claims_verified" not in validation.structural_checks


# --- ordering: computed keys outrank self-reported ones -------------------


def test_depth_outranks_a_one_claim_latent_difference():
    """Spec §10: two candidates whose latent-claim counts differ by 1 and whose
    backtracking depths differ are ordered by depth.

    Under v1 the shallow-but-chattier repair lost on ``latent_cost`` -- a model
    self-report overruling a quantity computed from the authored recipe.
    """

    shallow = _candidate("repair_last_step", checkpoints=["c3"], latent=2, minutes=9)
    deep = _candidate("rebuild_from_start", checkpoints=["c1"], latent=1, minutes=1)

    selection = select_minimal_repair([deep, shallow], trace_contract=CHAIN)
    assert _operator_of(selection) == "repair_last_step"
    assert selection["selection_basis"] == "structural"
    assert selection["selected"]["minimality"]["backtracking_depth"] == 0

    # Order the inputs the other way: selection is a property of the candidates,
    # not of their authoring order.
    assert (
        _operator_of(select_minimal_repair([shallow, deep], trace_contract=CHAIN))
        == "repair_last_step"
    )

    # And without the contract the deterministic keys are unavailable for both,
    # so the self-reports legitimately decide -- the OLD answer, now labelled.
    fallback = select_minimal_repair([deep, shallow])
    assert fallback["selection_basis"] == "model_reported"
    assert _operator_of(fallback) == "rebuild_from_start"


def test_a_one_claim_latent_difference_is_below_the_resolution_floor():
    """Among candidates tied on every deterministic key, a latent count within
    the floor of the best is not a real difference and must not decide; burden
    breaks the tie instead."""

    assert LATENT_COST_RESOLUTION_FLOOR == 1
    chatty_but_quick = _candidate(
        "quick_fix", checkpoints=["c3"], latent=2, minutes=2
    )
    terse_but_slow = _candidate("slow_fix", checkpoints=["c3"], latent=1, minutes=40)

    selection = select_minimal_repair(
        [terse_but_slow, chatty_but_quick], trace_contract=CHAIN
    )
    assert _operator_of(selection) == "quick_fix"

    # Two claims past the floor is a real difference again.
    much_chattier = _candidate(
        "verbose_fix", checkpoints=["c3"], latent=5, minutes=2
    )
    selection = select_minimal_repair(
        [terse_but_slow, much_chattier], trace_contract=CHAIN
    )
    assert _operator_of(selection) == "slow_fix"


def test_trace_edit_cost_breaks_a_depth_and_checkpoint_tie():
    """Two repairs at the same depth touching the same number of steps are
    ordered by the character-level diff -- computed here, not reported."""

    small = _candidate(
        "small_edit",
        checkpoints=["c3"],
        latent=3,
        minutes=30,
        answer="learner work plus one term",
    )
    large = _candidate(
        "rewrite",
        checkpoints=["c3"],
        latent=3,
        minutes=1,
        answer="a completely different answer from top to bottom, rewritten",
    )
    selection = select_minimal_repair(
        [large, small], trace_contract=CHAIN, learner_answer_md="learner work"
    )
    assert _operator_of(selection) == "small_edit"
    minimality = selection["selected"]["minimality"]
    assert minimality["trace_edit_cost"] is not None
    # The diff is measured against the LEARNER's real work, so the receipt and
    # the ranking report the same number.
    assert minimality["text_diff"]["before"] == "learner work"


def test_no_reliable_decomposition_still_selects_and_declares_the_regime():
    """Spec §10: an item with ``no_reliable_decomposition`` selects successfully
    and records ``selection_basis: model_reported``."""

    quick = _candidate("quick", checkpoints=[], latent=1, minutes=2)
    slow = _candidate("slow", checkpoints=[], latent=1, minutes=20)
    selection = select_minimal_repair(
        [slow, quick], trace_contract=NO_DECOMPOSITION
    )
    assert selection["selected"] is not None
    assert _operator_of(selection) == "quick"
    assert selection["selection_basis"] == "model_reported"
    assert selection["selection_basis"] in REPAIR_SELECTION_BASES
    assert selection["selected"]["minimality"]["selection_basis"] == "model_reported"
    assert selection["selected"]["minimality"]["backtracking_depth"] is None


def test_repair_policy_version_no_longer_overclaims():
    assert REPAIR_POLICY_VERSION == "structural_lexicographic_v2"


# --- end to end: the populated repair_class_id is the structural winner ----


def _vault_with_trace_contract(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    from learnloop.vault.yaml_io import read_yaml

    payload = read_yaml(item_path)
    payload["trace_contract"] = {
        "status": "available",
        "recipes": [
            {
                "id": "r1",
                "checkpoints": ["c1", "c2", "c3"],
                "dependencies": {"c2": ["c1"], "c3": ["c2"]},
            }
        ],
    }
    write_yaml(item_path, payload)
    return paths


def test_the_persisted_repair_class_is_the_structurally_selected_one(tmp_path):
    """The whole point of A1 for P2: ``repair_class_id`` is what the divergence
    gate, the common-repair cover, and the orchestrator's decision to spend
    learner effort all key on. If the class each hypothesis maps to were chosen
    by a noisy self-report ranking, the deterministic gate above it would be
    built on sand."""

    paths = _vault_with_trace_contract(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    target = {
        "kind": "facet_capability",
        "facet_id": "recall",
        "capability": "retrieval",
    }
    shallow = {
        "practice_mode": "repair",
        "operator": "repair_last_step",
        "rationale": "Fix only the final step.",
        "target_refs": [target],
        "expected_minutes": 9.0,
        "repaired_trace": {
            "learner_work_prefix": "U Sigma ",
            "minimal_edit": "transpose the final factor",
            "repaired_answer_md": "U Sigma Q^T",
            "changed_latent_claims": ["a", "b"],
            "changed_checkpoint_ids": ["c3"],
        },
    }
    deep = {
        "practice_mode": "repair",
        "operator": "rebuild_from_start",
        "rationale": "Redo the whole factorization.",
        "target_refs": [target],
        "expected_minutes": 1.0,
        "repaired_trace": {
            "learner_work_prefix": "",
            "minimal_edit": "start again",
            "repaired_answer_md": "U Sigma V^T",
            "changed_latent_claims": ["a"],
            "changed_checkpoint_ids": ["c1"],
        },
    }

    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id="att_structural",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": "ge_structural",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Q was used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement=(
                            "The learner may treat Q and Q transpose as identical."
                        ),
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        model_reported_causal_confidence=0.65,
                        candidate_causes=[
                            {
                                "statement": (
                                    "The learner may treat Q and Q transpose as "
                                    "identical."
                                ),
                                "cause_scope": "learner_state",
                                "target_ref": target,
                            }
                        ],
                        postdictive_claims=[
                            {"criterion_id": "correctness", "must": "not_full_credit"}
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose.",
                # Deliberately authored so the MODEL-reported keys favour the
                # deep repair (fewer latent claims, one minute) and the COMPUTED
                # keys favour the shallow one.
                repair_suggestions=[deep, shallow],
            ),
        ),
        clock=FrozenClock(NOW),
    )

    debug = repository.attempt_debug_payload(result.attempt_id) or {}
    receipt = (debug.get("causal_attribution") or {}).get("diagnosis_receipt") or {}
    selection = receipt["repair_selection"]
    assert receipt["repair_selection_basis"] == "structural"
    assert receipt["repair_policy_version"] == REPAIR_POLICY_VERSION
    assert selection["selected"]["repair_class"]["operator"] == "repair_last_step"
    assert selection["selected"]["minimality"]["backtracking_depth"] == 0

    # ...and the class persisted on the hypothesis is that structural winner,
    # not the self-report winner.
    winner = selection["selected"]["repair_class"]["id"]
    concrete = [
        row
        for row in repository.causal_hypotheses_for_attempt(result.attempt_id)
        if row["status"] != "open_set"
    ]
    assert concrete
    assert {row["repair_class_id"] for row in concrete} == {winner}
    assert receipt["common_repair_cover"]["repair_class_id"] == winner
