"""P2 §1: the trace-consistency veto is per hypothesis, not per receipt.

Every case here goes through ``apply_attempt`` so the receipt under test is the
one production writes, not a hand-built dict.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import EVIDENCE_READING_FIX_ALGORITHM_VERSION, GRADE_CHANNEL_FIX_ALGORITHM_VERSION
from learnloop.cli import app
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
    APPROVED_SUPPORT_AUTHORITIES,
    CAUSAL_DECISION_POLICY_VERSION,
    DIAGNOSIS_RECEIPT_SCHEMA_VERSION,
    SUPPORT_AUTHORITIES,
    causal_episode_for_attempt,
    claim_checked_feedback,
    receipt_probe_need,
    receipt_trace_consistency,
)
from learnloop.vault.loader import load_vault

from tests.diagnosis_split_helpers import build_diagnosis_vault
from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version

_STATEMENT = "The learner may be treating Q and Q transpose as identical."


def _apply(
    vault,
    repository,
    attempt_id: str,
    *,
    points_awarded: float = 0.0,
    candidate_causes: list[dict] | None = None,
    postdictive_claims: list[dict] | None = None,
):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=points_awarded,
                criterion_points={"correctness": points_awarded},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": float(points_awarded),
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
                        misconception_statement=_STATEMENT,
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        model_reported_causal_confidence=0.65,
                        candidate_causes=candidate_causes
                        or [
                            {
                                "statement": _STATEMENT,
                                "cause_scope": "learner_state",
                                "target_ref": {
                                    "kind": "facet_capability",
                                    "facet_id": "recall",
                                    "capability": "retrieval",
                                },
                            }
                        ],
                        postdictive_claims=(
                            postdictive_claims
                            if postdictive_claims is not None
                            else [
                                {
                                    "criterion_id": "correctness",
                                    "must": "not_full_credit",
                                }
                            ]
                        ),
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "insert_transpose",
                        "rationale": "Repair only the transpose.",
                        "target_refs": [
                            {
                                "kind": "facet_capability",
                                "facet_id": "recall",
                                "capability": "retrieval",
                            }
                        ],
                        "expected_minutes": 2.0,
                        "answer_reveal_budget": 0.5,
                        "repaired_trace": {
                            "learner_work_prefix": "U Sigma ",
                            "minimal_edit": "replace Q with Q^T",
                            "regenerated_work": "",
                            "repaired_answer_md": "U Sigma Q^T",
                            "changed_latent_claims": ["the factor is transposed"],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            ),
        ),
        clock=FrozenClock(NOW),
    )


def _receipt(tmp_path, name: str, **kwargs):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _apply(vault, repository, name, **kwargs)
    episode = causal_episode_for_attempt(repository, result.attempt_id)
    assert episode is not None
    return vault, repository, episode, episode["receipt"]


def test_receipt_stamps_schema_three_and_the_decision_policy(tmp_path):
    _, _, episode, receipt = _receipt(tmp_path, "att_policy")

    assert receipt["schema_version"] == DIAGNOSIS_RECEIPT_SCHEMA_VERSION == 3
    assert receipt["decision_policy_version"] == CAUSAL_DECISION_POLICY_VERSION
    assert episode["decision_policy_version"] == CAUSAL_DECISION_POLICY_VERSION
    # A single attempt earns no approved authority, and the honest support value
    # is None rather than a fabricated score.
    assert receipt["support_authority"] in SUPPORT_AUTHORITIES
    assert receipt["support_authority"] not in APPROVED_SUPPORT_AUTHORITIES
    assert set(receipt["support_scores"].values()) == {None}


def test_attributed_claim_that_holds_is_the_only_positive_state(tmp_path):
    _, _, _, receipt = _receipt(tmp_path, "att_holds")

    states = receipt["trace_consistency"]
    assert set(states.values()) == {"consistent_with_claims"}
    assert receipt["trace_consistent"] is True
    detail = receipt["trace_consistency_detail"]
    assert detail["unattributed_postdictive_claims"] == []
    assert all(
        row["claims_checked"] == 1 for row in detail["by_hypothesis"].values()
    )


def test_full_credit_criterion_contradicts_the_claiming_hypothesis(tmp_path):
    _, _, _, receipt = _receipt(tmp_path, "att_contradicted", points_awarded=4.0)

    states = receipt["trace_consistency"]
    assert set(states.values()) == {"contradicted"}
    assert receipt["trace_consistent"] is False
    detail = receipt["trace_consistency_detail"]
    assert all(
        row["contradicted_criterion_ids"] == ["correctness"]
        for row in detail["by_hypothesis"].values()
    )


def test_claimless_hypothesis_is_absence_of_evidence_not_corroboration(tmp_path):
    _, _, _, receipt = _receipt(
        tmp_path, "att_claimless", postdictive_claims=[]
    )

    states = receipt["trace_consistency"]
    assert set(states.values()) == {"no_deterministic_claims"}
    # The legacy alias still reads True — that is exactly why it must never be
    # read as support. Nobody made a falsifiable claim.
    assert receipt["trace_consistent"] is True
    assert "consistent_with_claims" not in states.values()


def test_plan_level_claim_is_not_credited_to_every_rival_candidate(tmp_path):
    _, _, _, receipt = _receipt(
        tmp_path,
        "att_ambiguous",
        candidate_causes=[
            {
                "statement": _STATEMENT,
                "cause_scope": "learner_state",
                "target_ref": {
                    "kind": "facet_capability",
                    "facet_id": "recall",
                    "capability": "retrieval",
                },
            },
            {
                "statement": "The learner may have misread the prompt.",
                "cause_scope": "interaction_context",
                "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
            },
            {"statement": "Something else.", "hypothesis_id": "H_OTHER"},
        ],
    )

    states = receipt["trace_consistency"]
    concrete = [
        str(ref["id"])
        for ref in receipt["hypotheses"]
        if ref.get("status") != "open_set"
    ]
    assert len(concrete) == 2
    assert {states[value] for value in concrete} == {"no_deterministic_claims"}
    # The open-set arm is never dropped (spec §5.1) and gets its own state.
    open_set = [
        str(ref["id"])
        for ref in receipt["hypotheses"]
        if ref.get("status") == "open_set"
    ]
    assert len(open_set) == 1
    assert states[open_set[0]] == "no_deterministic_claims"
    unattributed = receipt["trace_consistency_detail"][
        "unattributed_postdictive_claims"
    ]
    assert len(unattributed) == 1
    assert unattributed[0]["reason"] == "ambiguous_between_candidates"
    assert unattributed[0]["claim"]["criterion_id"] == "correctness"


def test_claim_naming_its_candidate_is_attributed_to_that_hypothesis(tmp_path):
    _, _, _, receipt = _receipt(
        tmp_path,
        "att_named",
        candidate_causes=[
            {
                "hypothesis_id": "H1",
                "statement": _STATEMENT,
                "cause_scope": "learner_state",
                "target_ref": {
                    "kind": "facet_capability",
                    "facet_id": "recall",
                    "capability": "retrieval",
                },
            },
            {
                "hypothesis_id": "H2",
                "statement": "The learner may have misread the prompt.",
                "cause_scope": "interaction_context",
                "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
            },
        ],
        postdictive_claims=[
            {
                "criterion_id": "correctness",
                "must": "not_full_credit",
                "hypothesis_id": "H1",
            }
        ],
    )

    states = receipt["trace_consistency"]
    detail = receipt["trace_consistency_detail"]["by_hypothesis"]
    claiming = [
        value for value, row in detail.items() if row["claims_attributed"] == 1
    ]
    assert len(claiming) == 1
    assert states[claiming[0]] == "consistent_with_claims"
    assert {
        states[value] for value in states if value != claiming[0]
    } == {"no_deterministic_claims"}
    assert receipt["trace_consistency_detail"][
        "unattributed_postdictive_claims"
    ] == []


def test_probe_need_replaces_the_decision_verbs(tmp_path):
    _, _, episode, receipt = _receipt(tmp_path, "att_probe_need")

    need = receipt["probe_need"]
    assert set(need) == {
        "divergent",
        "repair_class_ids",
        "common_repair_cover",
        "incomplete_repair_mapping",
        "reason",
    }
    assert need["repair_class_ids"] == sorted(need["repair_class_ids"])
    assert isinstance(need["divergent"], bool)
    assert isinstance(need["incomplete_repair_mapping"], bool)
    assert episode["probe_need"] == need
    # Deprecated alias keeps old readers alive without reintroducing a verb.
    assert receipt["probe_decision"]["decision"] == "see probe_need"
    assert {
        key: value
        for key, value in receipt["probe_decision"].items()
        if key != "decision"
    } == need


def test_legacy_schema_two_receipts_are_readable(tmp_path):
    legacy = {
        "schema_version": 2,
        "hypotheses": [{"id": "h_one"}, {"id": "h_two"}],
        "trace_consistent": True,
        "probe_decision": {
            "decision": "consider_probe",
            "reason": "plausible causes map to different repair classes",
        },
    }

    # A receipt-level True cannot be attributed after the fact, so no hypothesis
    # inherits corroboration it never earned.
    assert receipt_trace_consistency(legacy) == {
        "h_one": "unknown",
        "h_two": "unknown",
    }
    need = receipt_probe_need(legacy)
    assert need["divergent"] is True
    assert need["common_repair_cover"] is False
    assert need["legacy_schema"] is True


def test_cli_renders_probe_need_and_per_hypothesis_state(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = _apply(vault, repository, "att_cli")

    shown = CliRunner().invoke(
        app,
        ["show", result.attempt_id, "--causal", "--vault", str(paths.root)],
    )

    assert shown.exit_code == 0, shown.output
    assert "probe need" in shown.output
    assert "trace=consistent_with_claims" in shown.output
    assert "decision policy" in shown.output
    assert "probe decision" not in shown.output


def test_overlay_carries_per_hypothesis_state(tmp_path):
    vault, repository, episode, receipt = _receipt(tmp_path, "att_overlay")

    overlay = claim_checked_feedback(vault, repository, episode["attempt_id"])
    assert overlay is not None
    assert overlay["trace_consistency"] == receipt["trace_consistency"]
    assert overlay["probe_need"] == receipt["probe_need"]
    assert overlay["decision_policy_version"] == CAUSAL_DECISION_POLICY_VERSION
    for row in overlay["causal_hypotheses"]:
        assert row["trace_consistency"] == "consistent_with_claims"
        assert row["support_score"] is None
        assert row["support_authority"] == receipt["support_authority"]


# -- a criterion the own-route rule left unassessed (adversarial review of arc E, finding 2)


def _route_rule_receipt(tmp_path, *, marked: bool, tag: str | None = None):
    """``result`` at 0/2 beside ``setup`` at 2/2, with a hypothesis whose only
    claim is that ``result`` fell short. ``marked``: the rule left ``result``
    unassessed (its row carries the marker, as since mvp-0.17); otherwise it
    is a genuinely assessed zero. ``tag``: the vault's tag (the head when None)."""

    paths = build_diagnosis_vault(tmp_path / "vault")
    if tag is not None:
        set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rows = [
        {
            "id": f"ge_{criterion}",
            "criterion_id": criterion,
            "points_awarded": points,
            "evidence": "graded",
            "notes": None,
            "local_grader_id": "test",
            "grader_tier": 1,
            "created_at": NOW_ISO,
        }
        for criterion, points in (("setup", 2.0), ("result", 0.0))
    ]
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id="pi_svd_compute_001", learner_answer_md="U Sigma V"),
            attempt_id="att_marked" if marked else "att_assessed",
            grade=ResolvedGrade(
                rubric_score=4 if marked else 2,
                criterion_points={"setup": 2.0, "result": 0.0},
                evidence_rows=rows,
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement=_STATEMENT,
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        model_reported_causal_confidence=0.65,
                        candidate_causes=[{
                            "statement": _STATEMENT,
                            "cause_scope": "learner_state",
                            "target_ref": {"kind": "criterion", "criterion_id": "result"},
                        }],
                        postdictive_claims=[{"criterion_id": "result", "must": "not_full_credit"}],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[],
            ),
            unverified_criterion_ids=("result",) if marked else (),
        ),
        clock=FrozenClock(NOW),
    )
    episode = causal_episode_for_attempt(repository, result.attempt_id)
    assert episode is not None
    receipt = episode["receipt"]
    claiming = [
        value for value, row in receipt["trace_consistency_detail"]["by_hypothesis"].items()
        if row["claims_attributed"] == 1
    ]
    assert len(claiming) == 1
    outcomes = {row["criterion_id"]: row for row in receipt["criterion_outcomes"]}
    return receipt, claiming[0], outcomes["result"]


def test_an_assessed_zero_holds_a_shortfall_claim(tmp_path):
    receipt, hypothesis, result = _route_rule_receipt(tmp_path, marked=False)
    assert receipt["trace_consistency"][hypothesis] == "consistent_with_claims"
    assert result["assessable"] is True and result["passed"] is False


@pytest.mark.parametrize("tag", [GRADE_CHANNEL_FIX_ALGORITHM_VERSION, EVIDENCE_READING_FIX_ALGORITHM_VERSION])
def test_a_criterion_left_unassessed_neither_holds_nor_fails_a_claim(tmp_path, tag):
    """ER-2 (the evidence reading fixes, mvp-0.61): a row the route rule left unassessed is no assessed zero to
    either diagnosis reader. It was a strict xfail until the tag: replay rematerializes the receipt from the stored
    rows, so the fix moves rebuilt receipts. Below the tag (mvp-0.60) the receipt is today's."""

    receipt, hypothesis, result = _route_rule_receipt(tmp_path, marked=True, tag=tag)
    detail = receipt["trace_consistency_detail"]["by_hypothesis"][hypothesis]
    if tag == EVIDENCE_READING_FIX_ALGORITHM_VERSION:
        assert (receipt["trace_consistency"][hypothesis], detail["reason"]) == (
            "unknown", "claim_criteria_were_not_assessed",
        )
        assert (result["assessable"], result["passed"], result["full_credit"]) == (False, False, False)
    else:
        assert (receipt["trace_consistency"][hypothesis], detail["reason"]) == (
            "consistent_with_claims", "every_attributed_claim_held",
        )
        assert result["assessable"] is True and result["passed"] is False


@pytest.mark.parametrize("tag", [GRADE_CHANNEL_FIX_ALGORITHM_VERSION, EVIDENCE_READING_FIX_ALGORITHM_VERSION])
def test_an_assessed_zero_reads_the_same_at_both_tags(tmp_path, tag):
    receipt, hypothesis, result = _route_rule_receipt(tmp_path, marked=False, tag=tag)
    assert receipt["trace_consistency"][hypothesis] == "consistent_with_claims"
    assert result["assessable"] is True and result["passed"] is False
