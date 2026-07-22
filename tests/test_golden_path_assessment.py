"""P2 ASSESSMENT + RESTORATION + MILESTONE track
(spec_p2_narrow_golden_path §8, §7.5; §12.5, §12.3.1; design B.8-B.10).

Headline acceptance under test: NO UNPROMPTED DEPTH ACTIVATION.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import depth_transition as DT
from learnloop.services import golden_path_assessment as GA
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import golden_path_restoration as GRstr
from learnloop.services import golden_path_run as GPR
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault

CLOCK = FrozenClock(NOW)

EXEMPLAR = "pi_svd_define_001"
HELD_OUT = "pi_svd_define_002"


def _build_run(tmp_path, *, with_assessment=True):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    add_followup_item(root, HELD_OUT)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)

    spec = {
        "source_rev": "rev-1", "unit_id": "unit-a", "family_key": "method-selection",
        "exemplars": [{"exemplar_ref": EXEMPLAR, "unit_id": "unit-a", "family_key": "method-selection"}],
        "solution_recipes": [
            {"all_of": [
                {"facet": "decomposition_choice", "capability": "method_selection"},
                {"facet": "spectral_execution", "capability": "procedure_execution"},
            ]}
        ],
        "source_neighborhoods": {"method": ["span_intro"], "execution": ["span_worked"]},
        # The blueprint declares the reviewed depth edge the contract pins (C5): the
        # contract's reviewed_edges must be edges the blueprint version actually reviews.
        "depth_milestones": [{
            "edge_id": "edge_transfer_1", "reviewed": True, "direction": "transfer",
            "milestone_slug": "m_transfer", "task_feature_delta": {"span": 1},
            "successor_activity_path": {"pattern": "whole_task_integration"},
        }],
    }
    bv = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=spec, clock=CLOCK)
    bv = TB.review_blueprint_version(repo, blueprint_version_id=bv.id, clock=CLOCK)

    surface_id = None
    if with_assessment:
        held = resolve_legacy_item(vault, repo, vault.practice_items[HELD_OUT], purpose="assessment", clock=CLOCK)
        surface_id = held.surface_id

    body = {
        "purpose": "method selection",
        "facet_scope": {"concepts": ["unit-a"], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection", "procedure_execution"],
        "baseline_milestone": "m_method_selection_boundary",
        "depth_envelope": {
            "envelope_version": "denv_v1",
            "bounds": {"target_additions": []},
            "reviewed_edges": [{
                "edge_id": "edge_transfer_1", "reviewed": True, "direction": "transfer",
                "milestone_slug": "m_transfer", "task_feature_delta": {"span": 1},
                "successor_activity_path": {"pattern": "whole_task_integration"},
            }],
        },
        "exemplars": [{"id": EXEMPLAR, "surface_ref": EXEMPLAR, "weight": 1.0}],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo, goal_id="g1", blueprint_version_id=bv.id, contract_body=body,
        depth_preset="master_tasks_like_these", source_rev="rev-1", unit_id="unit-a",
        assessment_surface_id=surface_id, clock=CLOCK,
    )
    return vault, repo, receipt


def _to_ready_to_assess(repo, run_id):
    GPR.advance(repo, run_id, to_state="ready_to_assess", reason="ready", idempotency_key="rta", clock=CLOCK)


# ---------------------------------------------------------------------------
# §12.5 -- cold assessment happy path certifies the pinned target version
# ---------------------------------------------------------------------------

def test_cold_assessment_success_certifies_the_pinned_version(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _to_ready_to_assess(repo, receipt.run_id)

    admin = GA.open_assessment(repo, run_id=receipt.run_id, idempotency_key="open1", clock=CLOCK)
    result = GA.submit_assessment(
        vault, repo, run_id=receipt.run_id, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=4, max_points=4, attempt_id="att1", response_text="correct method",
        clock=CLOCK,
    )
    assert result.passed is True
    assert result.terminal is True
    # Cites the EXACT pinned target version (goal-contract v1), never the head rewrite.
    assert result.target_contract_version_id == receipt.goal_contract_version_id
    assert result.cited_version == 1
    # Reliability-aware P0 read-DTO fields present.
    assert result.claim_language in ("provisional", "calibrated")
    assert "low" in result.interval and "high" in result.interval
    assert result.projection_algorithm_version
    assert result.calibration_status


def test_practice_only_run_mints_no_certification(tmp_path):
    vault, repo, receipt = _build_run(tmp_path, with_assessment=False)
    assert receipt.mode == "practice_only"
    GPR.advance(repo, receipt.run_id, to_state="ready_to_assess", reason="rta", idempotency_key="k", clock=CLOCK)
    # A practice_only run never opens a terminal assessment (§1.1).
    with pytest.raises(GA.PracticeOnlyNoAssessment):
        GA.open_assessment(repo, run_id=receipt.run_id, idempotency_key="open1", clock=CLOCK)
    assert GA.assessment_result(repo, run_id=receipt.run_id) is None


def test_feedback_before_response_yields_zero_terminal_credit(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _to_ready_to_assess(repo, receipt.run_id)
    admin = GA.open_assessment(
        repo, run_id=receipt.run_id, idempotency_key="open1",
        feedback_condition="before_response", clock=CLOCK,
    )
    result = GA.submit_assessment(
        vault, repo, run_id=receipt.run_id, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=4, max_points=4, attempt_id="att1", response_text="x",
        feedback_condition="before_response", clock=CLOCK,
    )
    # Feedback revealed before the response => not terminal, no terminal credit.
    assert result.terminal is False
    assert result.passed is False
    assert result.eligibility_reason == "feedback_before_response"


def test_burned_surface_refuses_and_run_degrades(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _to_ready_to_assess(repo, receipt.run_id)
    # Burn the reserved assessment surface via a practice render on the SAME item
    # (exact surface_hash collision in the shared exposure ledger).
    from learnloop.services.activities import open_administration
    practice = resolve_legacy_item(vault, repo, vault.practice_items[HELD_OUT], purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=practice, clock=CLOCK)

    with pytest.raises(GA.ReserveInvalid):
        GA.open_assessment(repo, run_id=receipt.run_id, idempotency_key="open1", clock=CLOCK)
    # The run degrades gracefully (needs_review), never burns the colliding surface.
    state = GPR.project_run(repo, receipt.run_id)
    assert state.current_state == "needs_review"
    assert GA.assessment_result(repo, run_id=receipt.run_id) is None


def test_failed_assessment_seeds_only_a_practice_successor(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _to_ready_to_assess(repo, receipt.run_id)
    admin = GA.open_assessment(repo, run_id=receipt.run_id, idempotency_key="open1", clock=CLOCK)
    result = GA.submit_assessment(
        vault, repo, run_id=receipt.run_id, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=0, max_points=4, attempt_id="att1", response_text="wrong",
        clock=CLOCK,
    )
    assert result.passed is False
    assert result.terminal is True  # a terminal failure was recorded
    assert result.practice_successor_event_id is not None
    # A practice_successor_minted lifecycle event exists; the surface is not re-reserved.
    kinds = [e["kind"] for e in repo.surface_lifecycle_history(admin.surface_id)]
    assert "practice_successor_minted" in kinds


# ---------------------------------------------------------------------------
# §8.4 -- restoration + boundary diff (after measurement, cannot change it)
# ---------------------------------------------------------------------------

def _assess_and_pass(vault, repo, run_id):
    _to_ready_to_assess(repo, run_id)
    admin = GA.open_assessment(repo, run_id=run_id, idempotency_key="open1", clock=CLOCK)
    GA.submit_assessment(
        vault, repo, run_id=run_id, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=4, max_points=4, attempt_id="att1", response_text="correct", clock=CLOCK,
    )
    return admin


def test_boundary_diff_is_deterministic_and_reliability_aware(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    admin = _assess_and_pass(vault, repo, receipt.run_id)
    r1 = GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)

    # A second restore is idempotent (no duplicate artifact) and byte-identical diff.
    r2 = GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    assert r1.boundary_diff == r2.boundary_diff
    assert len(repo.golden_path_artifacts_for(receipt.run_id, kind="boundary_diff")) == 1

    covered = [c for c in r1.boundary_diff["cells"] if c["changed"]]
    assert covered, "the cold assessment must move at least one covered cell"
    for cell in covered:
        assert cell["before"] == "untested"
        assert cell["after"] in ("demonstrated", "developing")
        # Reliability-aware per-cell fields (P0 read-DTO rule).
        assert cell["claim_language"] in ("provisional", "calibrated")
        assert "calibration_status" in cell


def test_restoration_after_measurement_cannot_change_the_observation(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    admin = _assess_and_pass(vault, repo, receipt.run_id)
    before = repo.observations_for_administration(admin.administration_id)
    GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    after = repo.observations_for_administration(admin.administration_id)
    assert before == after  # restoration is an instructional event, appends no observation
    state = GPR.project_run(repo, receipt.run_id)
    assert state.current_state == "restoring"


# ---------------------------------------------------------------------------
# §7.5 / §12.3.1 -- milestone event only + ONE suggest_next, NEVER activation
# ---------------------------------------------------------------------------

def test_milestone_event_only_and_one_suggest_next_never_activates(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _assess_and_pass(vault, repo, receipt.run_id)
    receipt_restore = GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)

    # Milestone recorded as an EVENT only -- no commitment version bump (A.3).
    events = repo.commitment_events_for(receipt.commitment_id)
    milestones = [e for e in events if e["kind"] == "depth_milestone_reached"]
    assert len(milestones) == 1
    assert all(e.get("commitment_version_id") is None for e in milestones)

    # Exactly ONE depth invitation, served as suggest_next, NOT activated.
    invitations = repo.golden_path_artifacts_for(receipt.run_id, kind="depth_invitation")
    assert len(invitations) == 1
    assert receipt_restore.invitation["served_as"] == "suggest_next"
    assert receipt_restore.invitation["activated"] is False

    # No depth transition was committed, no contract successor appended, and the run
    # never auto-advanced into `deepening`.
    assert not any(e["kind"] == "depth_transition_committed" for e in events)
    head = repo.fetch_goal_contract_head("g1")
    assert head["head_version"] == 1  # still v1 -- no unprompted authorized_depth_step
    assert GPR.project_run(repo, receipt.run_id).current_state == "restoring"


def test_accept_records_draft_intent_without_successor(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _assess_and_pass(vault, repo, receipt.run_id)
    GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)

    payload = GRstr.accept_depth_invitation(repo, run_id=receipt.run_id, idempotency_key="acc1", clock=CLOCK)
    # Accept records intent as a non-pinnable draft; U-018 off => NO activation.
    assert payload["intent_recorded"] is True
    assert payload["activated"] is False
    assert payload["draft"] is not None
    # No successor appended, no transition committed, run still not deepening.
    assert repo.fetch_goal_contract_head("g1")["head_version"] == 1
    events = repo.commitment_events_for(receipt.commitment_id)
    assert not any(e["kind"] == "depth_transition_committed" for e in events)
    assert GPR.project_run(repo, receipt.run_id).current_state == "restoring"


def test_decline_logs_decision_and_holds_milestone(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    _assess_and_pass(vault, repo, receipt.run_id)
    GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    GRstr.decline_depth_invitation(
        repo, run_id=receipt.run_id, idempotency_key="dec1", to_state="maintaining", clock=CLOCK
    )
    declines = repo.golden_path_artifacts_for(receipt.run_id, kind="depth_decline")
    assert len(declines) == 1
    # Milestone stays reached; the completed result is never downgraded.
    assert repo.latest_golden_path_artifact(receipt.run_id, kind="milestone") is not None
    assert GPR.project_run(repo, receipt.run_id).current_state == "maintaining"


# ---------------------------------------------------------------------------
# §12.3.1 -- harness activation: ONE explicit confirmation activates exactly one edge
# ---------------------------------------------------------------------------

def test_harness_activation_activates_exactly_one_edge(tmp_path, monkeypatch):
    vault, repo, receipt = _build_run(tmp_path)
    # Give the commitment an auto_within_envelope policy so the (harness-gated)
    # activation path is reachable; and flip the U-018 structural gate ON.
    from learnloop.services import commitments as C
    C.change_depth_policy(
        repo, commitment_id=receipt.commitment_id, policy="auto_within_envelope", clock=CLOCK,
    )
    monkeypatch.setattr(DT, "LIVE_ACTIVATION_ENABLED", True)

    _assess_and_pass(vault, repo, receipt.run_id)
    # The invitation itself NEVER activates, even under the flipped gate.
    r = GRstr.restore(repo, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    assert r.invitation["activated"] is False
    payload = GRstr.accept_depth_invitation(
        repo, run_id=receipt.run_id, idempotency_key="acc1", live_activation_enabled=True, clock=CLOCK,
    )
    assert payload["activated"] is True
    events = repo.commitment_events_for(receipt.commitment_id)
    committed = [e for e in events if e["kind"] == "depth_transition_committed"]
    assert len(committed) == 1  # EXACTLY one edge
    assert GPR.project_run(repo, receipt.run_id).current_state == "deepening"


# ---------------------------------------------------------------------------
# §12.6 -- kill/resume across the assessment boundary
# ---------------------------------------------------------------------------

def test_kill_resume_across_assessment_boundary(tmp_path):
    vault, repo, receipt = _build_run(tmp_path)
    admin = _assess_and_pass(vault, repo, receipt.run_id)

    # Simulate a crash: corrupt the cached run state, then resume from events alone.
    with repo.connection() as c:
        c.execute("UPDATE golden_path_runs SET current_state = 'draft' WHERE id = ?", (receipt.run_id,))
        c.commit()
    fresh = Repository(repo.sqlite_path)
    state = GPR.project_run(fresh, receipt.run_id)
    assert state.current_state == "assessing"

    # Retried restore after resume yields exactly one restoration + one boundary diff.
    GRstr.restore(fresh, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    GRstr.restore(fresh, run_id=receipt.run_id, idempotency_key="restore1", clock=CLOCK)
    assert len(fresh.golden_path_artifacts_for(receipt.run_id, kind="restoration")) == 1
    assert len(fresh.golden_path_artifacts_for(receipt.run_id, kind="boundary_diff")) == 1
    # Idempotent grade: the single assessment observation was never re-created.
    assert len(fresh.observations_for_administration(admin.administration_id)) == 1
