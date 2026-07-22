"""P2 DIAGNOSTIC track -- two-tier failure-reason triage (spec_p2 §6, U-027, §12.2)."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.services import failure_triage as FT
from learnloop.services import golden_path_run as GPR
from learnloop.services.golden_path_fixture import build_golden_path_fixture
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@pytest.fixture
def triaging(tmp_path):
    """A run advanced to the ``triaging`` gate, ready for a triage decision."""

    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    rid = fx.receipt.run_id
    GPR.advance(repo, rid, to_state="measuring", reason="baseline", idempotency_key="m")
    GPR.advance(repo, rid, to_state="triaging", reason="triage", idempotency_key="t")
    return repo, rid


# ---------------------------------------------------------------------------
# Route table is data (§6.2)
# ---------------------------------------------------------------------------

def test_route_table_is_seeded_data_over_ten_reasons(triaging):
    repo, _rid = triaging
    routes = repo.failure_triage_routes()
    assert {r["reason"] for r in routes} == set(FT.TRIAGE_REASONS)
    assert len(routes) == 10


def test_only_false_belief_and_unknown_reopen_a_diagnostic_episode(triaging):
    repo, _rid = triaging
    reopen = {r["reason"] for r in repo.failure_triage_routes() if r["reopens_diagnostic"]}
    assert reopen == {"false_belief_or_confusion", "unknown_or_ambiguous"}


# ---------------------------------------------------------------------------
# Tier one -- decisive routes (§6.1)
# ---------------------------------------------------------------------------

def test_dont_know_on_never_exposed_routes_unfamiliar_decisively(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "dont_know",
                                      "exposure_history": "never_exposed"})
    assert r.tier == "one" and r.decisive
    assert r.reason == "unfamiliar_or_missing_knowledge"
    assert r.routed and r.routed_to == "instructing"
    assert GPR.project_run(repo, rid).current_state == "instructing"


def test_expired_memory_trace_routes_lapse_decisively(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "memory_trace": "expired"})
    assert r.tier == "one" and r.reason == "memory_lapse" and r.routed


def test_quarantined_surface_routes_fault_never_a_deficit(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "surface_validity": "quarantined"})
    # A misgraded/quarantined response is a surface fault, never a learner deficit.
    assert r.reason == "surface_or_grading_fault"
    assert r.route["reopens_diagnostic"] is False
    assert r.routed_to == "needs_review"


@pytest.mark.parametrize(
    "signature,expected,stage",
    [
        ("wrong_method", "method_selection", "instructing"),
        ("execution_error", "procedure_execution", "completing"),
        ("schema_gap", "schema_or_conceptual_hole", "instructing"),
        ("misconception", "false_belief_or_confusion", "instructing"),
        ("integration_gap", "coordination_or_integration", "integrating"),
        ("task_misread", "task_interpretation", "instructing"),
    ],
)
def test_high_confidence_signature_takes_intended_route(tmp_path, signature, expected, stage):
    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    rid = fx.receipt.run_id
    GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m")
    GPR.advance(repo, rid, to_state="triaging", reason="t", idempotency_key="t")
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "error_signature": signature, "grader_confidence": 0.95})
    assert r.tier == "one" and r.decisive
    assert r.reason == expected
    assert r.routed_to == stage


# ---------------------------------------------------------------------------
# C3 -- the high-confidence signature route needs a DOMINANT distribution to stay
# tier-one (owner-flagged default). Both directions. Regression: before C3 a diffuse
# distribution still auto-committed tier-one.
# ---------------------------------------------------------------------------

def test_concentrated_signature_distribution_stays_tier_one(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={
        "attempt_id": "a", "coarse_class": "wrong", "error_signature": "wrong_method",
        "grader_confidence": 0.95,
        "provisional_distribution": {"method_selection": 0.9, "procedure_execution": 0.1},
    })
    # One dominant signature (0.9 >= TRIAGE_DOMINANCE_SHARE) -> decisive tier-one route.
    assert r.tier == "one" and r.decisive
    assert r.reason == "method_selection" and r.routed_to == "instructing"
    assert GPR.project_run(repo, rid).current_state == "instructing"


def test_diffuse_signature_distribution_downgrades_to_tier_two(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={
        "attempt_id": "a", "coarse_class": "wrong", "error_signature": "wrong_method",
        "grader_confidence": 0.95,
        "provisional_distribution": {"method_selection": 0.5, "procedure_execution": 0.5},
    })
    # No single dominant signature (0.5 < TRIAGE_DOMINANCE_SHARE) -> tier-two decision
    # aid, NEVER auto-committed; the run stays at the triaging gate.
    assert r.tier == "two" and not r.decisive
    assert r.routed is False and r.auto_committed is False
    assert r.alternatives
    assert GPR.project_run(repo, rid).current_state == "triaging"


def test_bare_high_confidence_signature_still_routes_tier_one(triaging):
    # No SUPPLIED distribution: an unambiguous high-confidence signature is itself a
    # concentrated signal and stays tier-one (C3 is cheap to reverse).
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={
        "attempt_id": "a", "coarse_class": "wrong", "error_signature": "wrong_method",
        "grader_confidence": 0.95,
    })
    assert r.tier == "one" and r.decisive and r.routed_to == "instructing"


# ---------------------------------------------------------------------------
# Tier two -- provisional distribution is a DECISION AID (§6.1)
# ---------------------------------------------------------------------------

def test_low_confidence_yields_decision_aid_that_never_auto_commits(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "error_signature": "wrong_method", "grader_confidence": 0.3})
    assert r.tier == "two" and not r.decisive
    assert r.distribution is not None
    assert r.alternatives  # named alternatives presented
    # NEVER silently applied to a consequential transition -- the run stays at the gate.
    assert r.routed is False and r.auto_committed is False
    assert GPR.project_run(repo, rid).current_state == "triaging"


def test_ambiguous_cause_defaults_to_unknown_distribution(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong"})
    assert r.tier == "two"
    assert r.reason == "unknown_or_ambiguous"


def test_supplied_p0_distribution_is_used_and_normalized(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={
        "attempt_id": "a", "coarse_class": "wrong", "grader_confidence": 0.4,
        "provisional_distribution": {"method_selection": 3, "procedure_execution": 1},
    })
    assert r.tier == "two"
    assert abs(sum(r.distribution.values()) - 1.0) < 1e-9
    assert r.reason == "method_selection"


def test_decide_commits_the_aid_and_routes_the_run(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "error_signature": "wrong_method", "grader_confidence": 0.3})
    d = FT.decide(repo, rid, triage_event_id=r.event_id, chosen_reason=r.reason)
    assert d.routed and d.routed_to == "instructing"
    assert GPR.project_run(repo, rid).current_state == "instructing"
    assert d.anchor_sample_id is None  # picking the recommendation is not an override


def test_decide_diverging_from_recommendation_logs_an_anchor(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "error_signature": "wrong_method", "grader_confidence": 0.3})
    d = FT.decide(repo, rid, triage_event_id=r.event_id, chosen_reason="procedure_execution")
    assert d.anchor_sample_id is not None  # divergence -> adjudication anchor
    assert d.reason == "procedure_execution"


# ---------------------------------------------------------------------------
# Overrides -> adjudication anchors (§6.1) + append-only trace
# ---------------------------------------------------------------------------

def test_override_logs_adjudication_anchor(triaging):
    repo, rid = triaging
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "dont_know",
                                      "exposure_history": "never_exposed"})
    o = FT.override(repo, rid, triage_event_id=r.event_id,
                    chosen_reason="schema_or_conceptual_hole", actor="owner")
    assert o.kind == "overridden"
    assert o.anchor_sample_id is not None
    ev = repo.failure_triage_event(o.event_id)
    assert ev["override_actor"] == "owner"
    assert ev["anchor_sample_id"] == o.anchor_sample_id


def test_triage_trace_is_append_only_and_logs_goal_contract_head(triaging):
    repo, rid = triaging
    head = repo.fetch_goal_contract_head("goal_symmetric_method_selection")["head_version_id"]
    r = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                      "error_signature": "wrong_method", "grader_confidence": 0.3})
    FT.override(repo, rid, triage_event_id=r.event_id, chosen_reason="method_selection")
    status = FT.triage_status(repo, rid)
    kinds = [t["kind"] for t in status["trace"]]
    assert kinds == ["triaged", "overridden"]  # append-only, ordered
    assert all(t["goal_contract_head_version_id"] == head for t in status["trace"])
    seqs = [t["seq"] for t in status["trace"]]
    assert seqs == sorted(seqs)


def test_retried_triage_is_idempotent_on_the_ledger(triaging):
    """C7: a retried triage() for the same attempt does not append a duplicate ledger
    event -- the idempotency key returns the existing event (§12.6 exactly-once)."""

    repo, rid = triaging
    attempt = {"attempt_id": "att_retry", "coarse_class": "wrong",
               "error_signature": "wrong_method", "grader_confidence": 0.95}
    first = FT.triage(repo, rid, attempt=attempt)
    before = len(repo.failure_triage_events_for(rid))
    second = FT.triage(repo, rid, attempt=attempt)
    after = repo.failure_triage_events_for(rid)
    # Exactly one `triaged` event for the attempt survives the retry.
    triaged = [e for e in after if e["kind"] == "triaged" and e["attempt_id"] == "att_retry"]
    assert len(triaged) == 1
    assert second.event_id == first.event_id
    assert len(after) == before  # no new triaged row appended on retry
