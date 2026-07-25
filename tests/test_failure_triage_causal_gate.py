"""P2 causal-support normalization + the tier-one AND gate (contract §2, §2.1, §2.2).

These exercise ``failure_triage`` directly: the normalizer is the single place both the
decisive route and the provisional distribution read causal support from, so its
denominator, its aggregation, and its incompleteness flag are the whole gate.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import failure_triage as FT
from learnloop.services import golden_path_run as GPR
from learnloop.services.golden_path_fixture import build_golden_path_fixture
from learnloop.vault.paths import VaultPaths
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _row(
    hypothesis_id: str,
    reason: str | None,
    score: Any,
    *,
    trace: str = "consistent_with_claims",
    open_set: bool = False,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "hypothesis_id": hypothesis_id,
        "triage_reason": reason,
        "support_score": score,
        "trace_consistency": trace,
    }
    if open_set:
        row["open_set"] = True
    return row


def _support(*rows: dict[str, Any], authority: str = "validator_owned") -> dict[str, Any]:
    return {"support_authority": authority, "hypotheses": list(rows)}


# ---------------------------------------------------------------------------
# normalize_causal_support
# ---------------------------------------------------------------------------

def test_unmapped_and_open_set_mass_stays_in_the_denominator():
    norm = FT.normalize_causal_support(
        _support(
            _row("h_method", "method_selection", 0.6),
            _row("h_unmapped", None, 0.3),
            _row("H_OTHER", None, 0.1, open_set=True),
        )
    )
    assert norm.total_mass == pytest.approx(1.0)
    assert norm.by_reason["method_selection"] == pytest.approx(0.6)
    # 0.3 unmapped + 0.1 open set -- NOT dropped, so 0.6 is not dominant.
    assert norm.by_reason[FT.UNKNOWN_REASON] == pytest.approx(0.4)
    assert norm.dominant_reason == "method_selection"
    assert norm.dominant_share == pytest.approx(0.6)
    assert norm.dominant_share < FT.TRIAGE_DOMINANCE_SHARE
    assert not norm.incomplete


def test_two_hypotheses_on_one_reason_aggregate():
    """P2 routing is action-relative: two causes implying the same repair ADD."""

    norm = FT.normalize_causal_support(
        _support(
            _row("h_a", "method_selection", 0.45),
            _row("h_b", "method_selection", 0.35),
            _row("h_c", "procedure_execution", 0.2),
        )
    )
    assert norm.by_reason["method_selection"] == pytest.approx(0.8)
    assert norm.dominant_reason == "method_selection"
    assert norm.dominant_share == pytest.approx(0.8)


def test_open_set_row_never_credits_a_mapped_reason():
    norm = FT.normalize_causal_support(
        _support(_row("H_OTHER", "method_selection", 1.0, open_set=True))
    )
    assert norm.by_reason == {FT.UNKNOWN_REASON: pytest.approx(1.0)}
    assert norm.dominant_reason is None


def test_missing_score_on_a_concrete_hypothesis_is_incomplete():
    norm = FT.normalize_causal_support(
        _support(
            _row("h_method", "method_selection", 0.9),
            _row("h_execution", "procedure_execution", None),
        )
    )
    assert norm.incomplete
    # An open-set row legitimately carries no score and does not flag incompleteness.
    clean = FT.normalize_causal_support(
        _support(
            _row("h_method", "method_selection", 0.9),
            _row("H_OTHER", None, None, open_set=True),
        )
    )
    assert not clean.incomplete


def test_negative_score_is_clamped_and_flagged():
    norm = FT.normalize_causal_support(
        _support(
            _row("h_method", "method_selection", 1.0),
            _row("h_execution", "procedure_execution", -0.5),
        )
    )
    assert norm.incomplete
    assert norm.by_reason["method_selection"] == pytest.approx(1.0)
    assert norm.by_reason.get("procedure_execution", 0.0) == pytest.approx(0.0)


def test_all_none_scores_produce_zero_mass_and_no_dominance():
    norm = FT.normalize_causal_support(
        _support(
            _row("h_a", "method_selection", None),
            _row("h_b", "procedure_execution", None),
            authority="unavailable_single_attempt",
        )
    )
    assert norm.total_mass == 0.0
    assert norm.dominant_reason is None
    assert norm.incomplete
    assert not norm.authority_approved
    assert norm.by_reason == {FT.UNKNOWN_REASON: 0.0}


def test_ties_and_residual_maxima_name_no_dominant_reason():
    tied = FT.normalize_causal_support(
        _support(
            _row("h_a", "method_selection", 0.5),
            _row("h_b", "procedure_execution", 0.5),
        )
    )
    assert tied.dominant_reason is None
    residual = FT.normalize_causal_support(
        _support(
            _row("h_a", "method_selection", 0.2),
            _row("h_unmapped", None, 0.8),
        )
    )
    assert residual.dominant_reason is None


def test_authority_approval_reads_the_causal_attribution_vocabulary():
    assert FT.normalize_causal_support(
        _support(_row("h", "method_selection", 1.0), authority="validator_owned")
    ).authority_approved
    assert not FT.normalize_causal_support(
        _support(
            _row("h", "method_selection", 1.0),
            authority="unavailable_single_attempt",
        )
    ).authority_approved
    assert not FT.normalize_causal_support({"hypotheses": []}).authority_approved


# ---------------------------------------------------------------------------
# tier-one gate (§2.1)
# ---------------------------------------------------------------------------

_HIGH = {"error_signature": "wrong_method", "grader_confidence": 0.99}


def test_receipt_presence_alone_does_not_downgrade_the_legacy_route():
    """The regression guard: a receipt with no usable support must leave tier one
    reachable through the legacy arm."""

    reason, basis = FT._decisive_route(
        _HIGH,
        {},
        causal_support=_support(
            _row("h_method", "method_selection", None, trace="no_deterministic_claims"),
            authority="unavailable_single_attempt",
        ),
        causal_support_available=True,
    )
    assert (reason, basis) == ("method_selection", FT.TIER_ONE_BASIS_LEGACY)


def test_unapproved_authority_cannot_promote():
    reason, basis = FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.1},
        {},
        causal_support=_support(
            _row("h_method", "method_selection", 1.0),
            authority="unavailable_single_attempt",
        ),
        causal_support_available=True,
    )
    assert (reason, basis) == (None, None)
    # Same numbers under an approved authority DO promote.
    assert FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.1},
        {},
        causal_support=_support(
            _row("h_method", "method_selection", 1.0), authority="learner_confirmed"
        ),
        causal_support_available=True,
    ) == ("method_selection", FT.TIER_ONE_BASIS_CAUSAL)


def test_incomplete_support_blocks_promotion_but_not_the_legacy_arm():
    support = _support(
        _row("h_method", "method_selection", 1.0),
        _row("h_execution", "procedure_execution", None),
    )
    assert FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.1},
        {},
        causal_support=support,
        causal_support_available=True,
    ) == (None, None)
    assert FT._decisive_route(
        _HIGH, {}, causal_support=support, causal_support_available=True
    ) == ("method_selection", FT.TIER_ONE_BASIS_LEGACY)


def test_causal_veto_downgrades_an_otherwise_legacy_valid_route():
    # (a) the causal mass names a DIFFERENT reason.
    assert FT._decisive_route(
        _HIGH,
        {},
        causal_support=_support(
            _row("h_execution", "procedure_execution", 0.9),
            _row("h_method", "method_selection", 0.1),
        ),
        causal_support_available=True,
    ) == (None, None)
    # (b) the routed reason's own claim is contradicted.
    assert FT._decisive_route(
        _HIGH,
        {},
        causal_support=_support(
            _row("h_method", "method_selection", 1.0, trace="contradicted")
        ),
        causal_support_available=True,
    ) == (None, None)


def test_promotion_requires_positive_trace_evidence_not_mere_absence():
    for state in ("no_deterministic_claims", "unknown"):
        assert FT._decisive_route(
            {"error_signature": "wrong_method", "grader_confidence": 0.1},
            {},
            causal_support=_support(
                _row("h_method", "method_selection", 1.0, trace=state)
            ),
            causal_support_available=True,
        ) == (None, None)


def test_no_receipt_keeps_the_pure_legacy_behaviour():
    assert FT._decisive_route(_HIGH, {}, causal_support=None) == (
        "method_selection",
        FT.TIER_ONE_BASIS_LEGACY,
    )
    assert FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.3},
        {},
        causal_support=None,
    ) == (None, None)


def test_deterministic_triggers_report_their_own_basis():
    assert FT._decisive_route({"surface_validity": "quarantined"}, {}) == (
        "surface_or_grading_fault",
        FT.TIER_ONE_BASIS_DETERMINISTIC,
    )
    assert FT._decisive_route({"memory_trace": "expired"}, {}) == (
        "memory_lapse",
        FT.TIER_ONE_BASIS_DETERMINISTIC,
    )


# ---------------------------------------------------------------------------
# snapshot: merged signature map, open-set retention, trace states
# ---------------------------------------------------------------------------

class _StubRepository:
    """Only the reads ``_causal_support_snapshot`` performs."""

    def __init__(
        self,
        receipt: dict[str, Any],
        hypotheses: dict[str, dict[str, Any]],
        observations: list[dict[str, Any]] | None = None,
    ):
        self._receipt = receipt
        self._hypotheses = hypotheses
        self._observations = list(observations or [])

    def attempt_debug_payload(self, attempt_id: str) -> dict[str, Any]:
        return {"causal_attribution": {"diagnosis_receipt": self._receipt}}

    def causal_hypothesis(self, hypothesis_id: str) -> dict[str, Any] | None:
        return self._hypotheses.get(hypothesis_id)

    def causal_discriminating_observations(
        self, *, attempt_id=None, admitted_only=False, **_kwargs
    ) -> list[dict[str, Any]]:
        # Migration 130: the §7 observation receipt the snapshot overlays. Most
        # of these cases have none, which is the production shape today.
        return [
            row
            for row in self._observations
            if (attempt_id is None or row.get("attempt_id") == attempt_id)
            and (not admitted_only or row.get("admitted"))
        ]


def _stub() -> _StubRepository:
    receipt = {
        "schema_version": 3,
        "support_authority": "validator_owned",
        "support_scores": {"h_house": 0.9, "h_exec": 0.1},
        "trace_consistency": {
            "h_house": "consistent_with_claims",
            "h_exec": "no_deterministic_claims",
        },
        "trace_consistent": True,
        "hypotheses": [
            {"id": "h_house", "status": "candidate"},
            {"id": "h_exec", "status": "candidate"},
            {"id": "h_open", "status": "open_set"},
        ],
    }
    hypotheses = {
        # A vault-specific signature that only the blueprint override maps.
        "h_house": {
            "id": "h_house",
            "status": "candidate",
            "operation": "house_convention_slip",
            "repair_class_id": "repair:method",
            "evidence": {},
        },
        "h_exec": {
            "id": "h_exec",
            "status": "candidate",
            "operation": "execution_error",
            "repair_class_id": "repair:exec",
            "evidence": {},
        },
        "h_open": {"id": "h_open", "status": "open_set", "evidence": {}},
    }
    return _StubRepository(receipt, hypotheses)


def test_snapshot_uses_the_merged_signature_map_and_keeps_open_set_rows():
    repository = _stub()
    inputs = {"attempt_id": "att_1", "error_signature": "house_convention_slip"}

    # Without the vault override the house signature is unmapped -> residual mass.
    default_support, available = FT._causal_support_snapshot(repository, inputs)
    assert available
    default_norm = FT.normalize_causal_support(default_support)
    assert default_norm.by_reason[FT.UNKNOWN_REASON] == pytest.approx(0.9)
    assert FT._decisive_route(
        {**inputs, "grader_confidence": 0.99},
        {},
        causal_support=default_support,
        causal_support_available=True,
    ) == (None, None)

    # With it, the same receipt routes -- and the snapshot must honour the SAME merged
    # map the gate does, or the vault override mismatches silently.
    signature_map = {"house_convention_slip": "method_selection"}
    support, _ = FT._causal_support_snapshot(repository, inputs, signature_map)
    assert [row["hypothesis_id"] for row in support["hypotheses"]] == [
        "h_house",
        "h_exec",
        "h_open",
    ]
    open_row = support["hypotheses"][-1]
    assert open_row["open_set"] is True and open_row["triage_reason"] is None
    assert support["support_authority"] == "validator_owned"
    assert support["hypotheses"][0]["trace_consistency"] == "consistent_with_claims"

    reason, basis = FT._decisive_route(
        {**inputs, "grader_confidence": 0.1},
        signature_map,
        causal_support=support,
        causal_support_available=True,
    )
    assert (reason, basis) == ("method_selection", FT.TIER_ONE_BASIS_CAUSAL)


def test_a_discriminating_observation_overlays_scores_but_not_always_authority():
    """Migration 130's receipt reaching the gate -- asymmetrically (§2.1).

    The observation's per-hypothesis scores always land, so a discriminating
    observation may VETO a route.  Its ``support_authority`` lands only when the
    observation earned one: ``record_probe_classification`` grants
    ``validator_owned`` to a deterministic sensor and withholds it from a
    model-extracted one, and a snapshot that overlaid the authority regardless
    would launder a model-read feature vector into deterministic routing.
    """

    signature_map = {"house_convention_slip": "method_selection"}
    inputs = {"attempt_id": "att_1", "error_signature": "house_convention_slip"}

    # A model-extracted observation that names the OTHER cause: it moves the
    # mass (and therefore vetoes), but carries no authority of its own.
    repository = _stub()
    repository._receipt = {
        **repository._receipt,
        "support_authority": "unavailable_single_attempt",
        "support_scores": {"h_house": None, "h_exec": None},
    }
    repository._observations = [
        {
            "id": "cdo_1",
            "attempt_id": "att_1",
            "admitted": True,
            "support_authority": None,
            "support_scores": {"h_house": 0.0, "h_exec": 1.0},
        }
    ]
    vetoed, _ = FT._causal_support_snapshot(repository, inputs, signature_map)
    assert vetoed["support_authority"] == "unavailable_single_attempt"
    assert vetoed["discriminating_observation_id"] == "cdo_1"
    norm = FT.normalize_causal_support(vetoed)
    assert norm.authority_approved is False
    assert norm.dominant_reason == "procedure_execution"
    assert FT._decisive_route(
        {**inputs, "grader_confidence": 0.99},
        signature_map,
        causal_support=vetoed,
        causal_support_available=True,
    ) == (None, None)

    # ...and the same observation from a DETERMINISTIC sensor promotes.
    repository._observations = [
        {
            "id": "cdo_2",
            "attempt_id": "att_1",
            "admitted": True,
            "support_authority": "validator_owned",
            "support_scores": {"h_house": 1.0, "h_exec": 0.0},
        }
    ]
    promoted, _ = FT._causal_support_snapshot(repository, inputs, signature_map)
    assert promoted["support_authority"] == "validator_owned"
    assert FT._decisive_route(
        {**inputs, "grader_confidence": 0.1},
        signature_map,
        causal_support=promoted,
        causal_support_available=True,
    ) == ("method_selection", FT.TIER_ONE_BASIS_CAUSAL)

    # An INADMISSIBLE observation is not overlaid at all: the scores stay
    # ``None`` and the receipt keeps its own honest abstention.
    repository._observations = [
        {
            "id": "cdo_3",
            "attempt_id": "att_1",
            "admitted": False,
            "support_authority": None,
            "support_scores": {},
        }
    ]
    ignored, _ = FT._causal_support_snapshot(repository, inputs, signature_map)
    assert ignored["discriminating_observation_id"] is None
    assert {row["support_score"] for row in ignored["hypotheses"]} == {None}
    assert FT.normalize_causal_support(ignored).incomplete is True


def test_legacy_receipt_states_are_unknown_and_cannot_promote():
    """A schema-2 receipt's receipt-level bool cannot be attributed to a hypothesis, so
    every row reads ``unknown`` (the shared ``receipt_trace_consistency`` contract):
    no corroboration, and no reason-specific veto either."""

    repository = _stub()
    repository._receipt = {
        **repository._receipt,
        "schema_version": 2,
        "trace_consistency": None,
        "trace_consistent": False,
    }
    signature_map = {"house_convention_slip": "method_selection"}
    support, _ = FT._causal_support_snapshot(
        repository, {"attempt_id": "att_1"}, signature_map
    )
    assert {row["trace_consistency"] for row in support["hypotheses"]} == {"unknown"}
    assert support["trace_consistent"] is False
    # No positive trace evidence -> the causal arm cannot promote...
    assert FT._decisive_route(
        {"error_signature": "house_convention_slip", "grader_confidence": 0.1},
        signature_map,
        causal_support=support,
        causal_support_available=True,
    ) == (None, None)
    # ...but the dominant causal mass still agrees with the legacy route, so the
    # legacy arm is not vetoed.
    assert FT._decisive_route(
        {"error_signature": "house_convention_slip", "grader_confidence": 0.99},
        signature_map,
        causal_support=support,
        causal_support_available=True,
    ) == ("method_selection", FT.TIER_ONE_BASIS_LEGACY)


# ---------------------------------------------------------------------------
# provisional distribution + alternatives (§2.2)
# ---------------------------------------------------------------------------

def test_provisional_distribution_keeps_the_residual_bucket_visible():
    dist = FT._provisional_distribution(
        {"error_signature": "wrong_method"},
        {},
        causal_support=_support(
            _row("h_method", "method_selection", 0.6),
            _row("h_unmapped", None, 0.3),
            _row("H_OTHER", None, 0.1, open_set=True),
        ),
    )
    assert dist["method_selection"] == pytest.approx(0.6)
    assert dist[FT.UNKNOWN_REASON] == pytest.approx(0.4)
    assert sum(dist.values()) == pytest.approx(1.0)


def test_supplied_distribution_still_takes_precedence():
    dist = FT._provisional_distribution(
        {
            "error_signature": "wrong_method",
            "provisional_distribution": {"memory_lapse": 2.0, "method_selection": 2.0},
        },
        {},
        causal_support=_support(_row("h_method", "method_selection", 1.0)),
    )
    assert dist == {
        "memory_lapse": pytest.approx(0.5),
        "method_selection": pytest.approx(0.5),
    }


def test_zero_mass_causal_support_falls_through_to_the_signature_fallback():
    dist = FT._provisional_distribution(
        {"error_signature": "wrong_method"},
        {},
        causal_support=_support(
            _row("h_method", "method_selection", None),
            authority="unavailable_single_attempt",
        ),
    )
    assert dist == {"method_selection": 0.6, FT.UNKNOWN_REASON: 0.4}


def test_triage_records_tier_one_basis_on_the_result_and_the_event(tmp_path):
    import json

    root = tmp_path / "vault"
    fixture = build_golden_path_fixture(root)
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    run_id = fixture.receipt.run_id
    GPR.advance(
        repository, run_id, to_state="measuring", reason="baseline", idempotency_key="m"
    )
    GPR.advance(
        repository, run_id, to_state="triaging", reason="triage", idempotency_key="t"
    )

    result = FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": "a",
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.95,
        },
    )
    assert result.tier == "one"
    assert result.tier_one_basis == FT.TIER_ONE_BASIS_LEGACY
    event = repository.failure_triage_event(result.event_id)
    payload = json.loads(event["inputs_snapshot_json"])
    assert payload["triage_decision"]["tier_one_basis"] == FT.TIER_ONE_BASIS_LEGACY
    assert payload["triage_decision"]["causal_support_available"] is False
    # The raw §6.1 inputs stay in the snapshot alongside the decision trace.
    assert payload["error_signature"] == "wrong_method"


def test_real_receipt_from_apply_attempt_does_not_force_tier_two(tmp_path):
    """The defect this whole change exists to kill, on the INTEGRATION path.

    ``apply_attempt`` writes a single-attempt receipt whose ``support_scores`` are all
    ``None`` by design. That receipt must leave a decisive legacy signature route
    intact -- no hand-built dicts, no injected support numbers."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id="att_triage_gate",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": "ge_att_triage_gate",
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
                        error_type="wrong_method",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement=(
                            "The learner may be treating Q and Q transpose as identical."
                        ),
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="wrong_method",
                        model_reported_causal_confidence=0.65,
                        candidate_causes=[
                            {
                                "statement": (
                                    "The learner may be treating Q and Q transpose "
                                    "as identical."
                                ),
                                "cause_scope": "learner_state",
                                "target_ref": {
                                    "kind": "criterion",
                                    "criterion_id": "correctness",
                                },
                            }
                        ],
                        postdictive_claims=[],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
            ),
        ),
        clock=FrozenClock(NOW),
    )

    inputs = {
        "attempt_id": result.attempt_id,
        "coarse_class": "wrong",
        "error_signature": "wrong_method",
        "grader_confidence": 0.95,
    }
    support, available = FT._causal_support_snapshot(repository, inputs, {})
    assert available, "the attempt must carry a P2 diagnosis receipt"
    assert support["support_authority"] == "unavailable_single_attempt"
    assert support["hypotheses"], "receipt hypotheses must reach the snapshot"
    assert all(
        row["support_score"] is None for row in support["hypotheses"]
    ), "a single attempt owns no validator support -- that is not the thing to fix"

    norm = FT.normalize_causal_support(support)
    assert not norm.authority_approved and norm.dominant_reason is None

    reason, basis = FT._decisive_route(
        inputs, {}, causal_support=support, causal_support_available=available
    )
    assert (reason, basis) == ("method_selection", FT.TIER_ONE_BASIS_LEGACY)


class _Routeless:
    def failure_triage_route_for_reason(self, reason: str) -> None:
        return None


def test_alternatives_surface_the_residual_bucket_and_its_hypotheses():
    support = _support(
        _row("h_a", "method_selection", 0.3),
        _row("h_b", "procedure_execution", 0.25),
        _row("h_c", "memory_lapse", 0.25),
        _row("h_unmapped", None, 0.1),
        _row("H_OTHER", None, 0.1, open_set=True),
    )
    distribution = FT.normalize_causal_support(support).by_reason
    alternatives = FT._alternatives(_Routeless(), distribution, causal_support=support)
    residual = [a for a in alternatives if a["reason"] == FT.UNKNOWN_REASON]
    assert residual, "the unplaced causal mass must reach the decision aid"
    assert residual[0]["weight"] == pytest.approx(0.2)
    assert {row["hypothesis_id"] for row in residual[0]["causal_hypotheses"]} == {
        "h_unmapped",
        "H_OTHER",
    }
