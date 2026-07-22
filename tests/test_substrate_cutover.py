"""P1 step 9 -- dual-write cutover, narrowed by the 2026-07-19 owner decision
(spec_p1_shared_substrate §7.4, §7.5, §9.5, §9.7).

Covers: the mvp-0.8 gate flip (purpose adapters LIVE for mvp-0.8, legacy path for
older vaults); the complete new-substrate lineage write as one fail-safe unit with a
fault-injection test after every write boundary (silent-corruption concern); the six
ordered cutover gates as a hard sequential barrier in their narrowed form; idempotent
dual-write retry.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import administration_adapters as AA
from learnloop.services import card_lineage as CL
from learnloop.services import substrate_cutover as SC
from learnloop.services.fsrs import Rating

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
SCHED = SC.P1_SCHEDULER_ALGORITHM_VERSION
MVP08 = SC.P0_ALGORITHM_VERSION
MVP07 = SC.KM_ALGORITHM_VERSION


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _card(repo, *, purpose="practice", tag="a"):
    family_id = repo.ensure_activity_family(purpose=purpose, legacy_kind=None, title=f"fam-{tag}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval", "tag": tag}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    surface = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{tag}", fingerprint=None, surface_json="{}", clock=CLOCK,
    )
    lineage_id = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=family_id, card_id=card_id, clock=CLOCK)
    return dict(family_id=family_id, card_id=card_id, cv=cv, surface=repo.fetch_surface(surface), lineage_id=lineage_id)


# --- the gate flip: mvp-0.8 live, legacy byte-identical ----------------------

def test_purpose_adapters_live_only_for_mvp08():
    assert SC.purpose_adapters_live(MVP08) is True
    assert SC.purpose_adapters_live(MVP07) is False
    assert SC.purpose_adapters_live("mvp-0.6") is False
    assert SC.purpose_adapters_live(None) is False


def test_hot_path_review_is_byte_identical_for_eligible_practice_on_both_paths():
    # The only kind that reaches apply_attempt is an eligible practice attempt, so the
    # flip is behaviour-preserving there (both paths apply the review).
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", algorithm_version=MVP08) is True
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", algorithm_version=MVP07) is True
    # On a LIVE vault an ineligible (quarantined/out-of-band) observation now correctly
    # leaves card state unchanged; a legacy vault keeps the unconditional write.
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", eligible=False, algorithm_version=MVP08) is False
    assert AA.hot_path_applies_practice_review(attempt_type="independent_attempt", eligible=False, algorithm_version=MVP07) is True


def test_module_override_forces_live_regardless_of_version(monkeypatch):
    monkeypatch.setattr(AA, "P1_PURPOSE_ADAPTERS_ENABLED", True)
    assert SC.purpose_adapters_live(MVP07) is True


def test_purpose_adapters_live_from_registry_entry_is_bound_to_code(monkeypatch):
    # A4: the registered structural param substrate_cutover:PURPOSE_ADAPTERS_LIVE_FROM
    # names a REAL module constant that purpose_adapters_live actually reads -- not a
    # dangling registry entry. Repointing the constant repoints the live decision.
    assert SC.PURPOSE_ADAPTERS_LIVE_FROM == MVP08
    monkeypatch.setattr(SC, "PURPOSE_ADAPTERS_LIVE_FROM", MVP07)
    assert SC.purpose_adapters_live(MVP07) is True
    assert SC.purpose_adapters_live(MVP08) is False


# --- the complete new-substrate lineage write (happy path) -------------------

def test_submit_writes_full_lineage_in_one_unit(repo):
    card = _card(repo)
    receipt = SC.submit_administration_response(
        repo, surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False,
        attempt_id="att-1", admin_context={"cold": True, "open_book": False}, clock=CLOCK,
    )
    assert receipt.complete
    assert set(receipt.boundaries_completed) == set(SC.WRITE_BOUNDARIES)
    # Administration + rendered/submitted exposure + observation + card_state all present.
    admin = repo.activity_administration(receipt.administration_id)
    assert admin["purpose"] == "practice"
    kinds = {e["kind"] for e in repo.exposures_for_surface(card["surface"]["id"])}
    assert {"rendered", "submitted"} <= kinds
    assert repo.observations_for_administration(receipt.administration_id)
    assert receipt.card_state is not None and receipt.card_state["stability"] is not None


def test_diagnostic_and_assessment_write_no_practice_schedule(repo):
    for purpose in ("diagnostic", "instructional", "assessment"):
        card = _card(repo, purpose=purpose, tag=purpose)
        receipt = SC.submit_administration_response(
            repo, surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
            purpose=purpose, card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
            review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False, clock=CLOCK,
        )
        assert receipt.complete and receipt.card_state is None
        assert repo.activity_card_state(card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED) is None


# --- fault injection after every write boundary (silent-corruption concern) ---

def _no_fault_state(repo, tag):
    """The final card state a clean (no-fault) submit produces -- the recovery target."""
    card = _card(repo, tag=f"nofault-{tag}")
    receipt = SC.submit_administration_response(
        repo, surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False,
        attempt_id="att-nofault", clock=CLOCK,
    )
    assert receipt.complete
    return receipt.card_state


@pytest.mark.parametrize("boundary", SC.WRITE_BOUNDARIES)
def test_fault_after_each_boundary_recovers_to_the_no_fault_state(repo, boundary):
    target = _no_fault_state(repo, boundary)
    card = _card(repo, tag=f"fault-{boundary}")
    submit_kwargs = dict(
        surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False,
        attempt_id="att-fault", clock=CLOCK,
    )
    receipt = SC.submit_administration_response(repo, fault_after=[boundary], **submit_kwargs)
    # The service never raised into the caller (fail-safe posture); every fault defers.
    assert receipt.deferred

    if boundary in ("administration", "exposure"):
        # Fault INSIDE the atomic raw-event transaction -> the WHOLE unit rolled back:
        # clean nothing-happened state (no administration, no card state, nothing to
        # rebuild). Recovery = re-run submit; it completes to the no-fault state.
        assert receipt.administration_id is None and receipt.rebuild_id is None
        assert repo.observations_for_administration(receipt.administration_id or "none") == []
        recovered = SC.submit_administration_response(repo, **submit_kwargs)
        assert recovered.complete
    else:
        # Post-commit fault (observation / projection): the raw events are DURABLE and a
        # rebuild is enqueued. Recovery = re-derive the projection FROM THE LEDGER.
        assert receipt.administration_id is not None and receipt.rebuild_id is not None
        assert repo.observations_for_administration(receipt.administration_id)
        if boundary == "observation":
            # Projection never ran -> no half-updated card state before recovery.
            assert repo.activity_card_state(
                card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED
            ) is None
        recovered_state = SC.rebuild_deferred_projection(
            repo, administration_id=receipt.administration_id, card_lineage_id=card["lineage_id"], clock=CLOCK,
        )
        assert recovered_state is not None

    # Either recovery path lands the same final card-state stability as the no-fault run.
    final = repo.activity_card_state(card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED)
    assert final is not None and final["stability"] == target["stability"]


def test_rebuild_refuses_when_no_observation_exists(repo):
    # §7.5: a projection may never be written without an observation to derive it from.
    card = _card(repo, tag="no-obs")
    with pytest.raises(SC.NoObservationToRebuild):
        SC.rebuild_deferred_projection(
            repo, administration_id="does-not-exist", card_lineage_id=card["lineage_id"], clock=CLOCK,
        )


def test_projection_failure_defers_without_half_update(repo, monkeypatch):
    card = _card(repo, tag="projfail")

    def _boom(*_a, **_k):
        raise RuntimeError("adapter scheduling exploded")

    monkeypatch.setattr(AA.PracticeAdapter, "apply_scheduling", _boom)
    receipt = SC.submit_administration_response(
        repo, surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False, clock=CLOCK,
    )
    assert receipt.deferred and receipt.error is not None and receipt.rebuild_id is not None
    # No half-updated card state; the raw ledger (administration + observation) survived.
    assert repo.activity_card_state(card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED) is None
    assert repo.observations_for_administration(receipt.administration_id)


def test_deferred_projection_rebuild_is_deterministic_and_idempotent(repo, monkeypatch):
    card = _card(repo, tag="rebuild")
    boom = {"active": True}
    real = AA.PracticeAdapter.apply_scheduling

    def _maybe_boom(self, *a, **k):
        if boom["active"]:
            raise RuntimeError("boom")
        return real(self, *a, **k)

    monkeypatch.setattr(AA.PracticeAdapter, "apply_scheduling", _maybe_boom)
    receipt = SC.submit_administration_response(
        repo, surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False, clock=CLOCK,
    )
    assert receipt.deferred
    boom["active"] = False
    # Recovery re-derives eligibility + review from the LEDGER (no caller-supplied evidence).
    first = SC.rebuild_deferred_projection(
        repo, administration_id=receipt.administration_id, card_lineage_id=card["lineage_id"], clock=CLOCK,
    )
    second = SC.rebuild_deferred_projection(
        repo, administration_id=receipt.administration_id, card_lineage_id=card["lineage_id"], clock=CLOCK,
    )
    assert first is not None and first["stability"] == second["stability"]  # deterministic + idempotent


def test_dual_write_retry_does_not_duplicate_events(repo):
    card = _card(repo, tag="retry")
    kwargs = dict(
        surface=card["surface"], card_version_id=card["cv"], family_id=card["family_id"],
        purpose="practice", card_lineage_id=card["lineage_id"], algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD, "elapsed_days": 0.0}, eligible=True, failed=False,
        attempt_id="att-retry", clock=CLOCK,
    )
    r1 = SC.submit_administration_response(repo, **kwargs)
    r2 = SC.submit_administration_response(repo, **kwargs)
    # Render-once + idempotent guards: the second submit reuses the same administration,
    # submitted exposure, and observation (§9.5 dual-write retry idempotent).
    assert r1.administration_id == r2.administration_id
    submitted = [e for e in repo.exposures_for_surface(card["surface"]["id"]) if e["kind"] == "submitted"]
    assert len(submitted) == 1
    assert len(repo.observations_for_administration(r1.administration_id)) == 1


# --- the six ordered cutover gates (narrowed) --------------------------------

def test_six_gates_barrier_all_cleared_on_mvp08(repo):
    report = SC.run_cutover_gates(repo, algorithm_version=MVP08, clock=CLOCK)
    assert report.barrier_ok and report.all_cleared
    names = [g.name for g in report.gates]
    assert names == [
        "identity_mapping_coverage_100pct",
        "historical_replay_equivalence",
        "new_scheduling_projection_correct",
        "purpose_side_effects",
        "legacy_scheduler_reads_compat_state",
        "legacy_writes_rejected_for_new_admin",
    ]
    by_name = {g.name: g for g in report.gates}
    # Narrowed: legacy-row equivalence / legacy-read gates are N/A by owner decision.
    assert by_name["identity_mapping_coverage_100pct"].status == "na_owner_decision"
    assert by_name["historical_replay_equivalence"].status == "na_owner_decision"
    assert by_name["legacy_scheduler_reads_compat_state"].status == "na_owner_decision"
    # New-substrate write-path integrity gates stay LIVE and must pass.
    assert by_name["new_scheduling_projection_correct"].status == "pass"
    assert by_name["purpose_side_effects"].status == "pass"
    assert by_name["legacy_writes_rejected_for_new_admin"].status == "pass"


def test_gates_are_ordinal_and_ordered(repo):
    report = SC.run_cutover_gates(repo, algorithm_version=MVP08, clock=CLOCK)
    assert [g.ordinal for g in report.gates] == [1, 2, 3, 4, 5, 6]


def test_gate6_legacy_write_rejected_only_on_live_vault(repo):
    # Live mvp-0.8: a direct legacy scheduling write for a new administration is rejected.
    with pytest.raises(SC.LegacyWriteRejected):
        SC.reject_legacy_scheduling_write(MVP08, administration_id="admin-x")
    # Legacy vault: the legacy write path is retained (no rejection).
    SC.reject_legacy_scheduling_write(MVP07, administration_id="admin-x")
    report = SC.run_cutover_gates(repo, algorithm_version=MVP07, clock=CLOCK)
    assert report.gates[5].status == "na_owner_decision"


def test_gate6_chokepoint_actually_blocks_the_write(repo):
    # A3 gate 6: the guarded chokepoint prevents the row on a live vault (not just a flag).
    card = _card(repo, tag="gate6")
    before = repo.activity_card_state(card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED)
    with pytest.raises(SC.LegacyWriteRejected):
        SC.guarded_legacy_scheduling_write(
            repo, algorithm_version=MVP08, administration_id="admin-x",
            card_lineage_id=card["lineage_id"], stability=999.0, clock=CLOCK,
        )
    after = repo.activity_card_state(card_lineage_id=card["lineage_id"], scheduler_algorithm_version=SCHED)
    assert after == before  # nothing was written
    # On a legacy vault the same write proceeds through the chokepoint.
    state = SC.guarded_legacy_scheduling_write(
        repo, algorithm_version=MVP07, administration_id="admin-x",
        card_lineage_id=card["lineage_id"], stability=42.0, clock=CLOCK,
    )
    assert state is not None and state["stability"] == 42.0


def test_gate3_drives_adapter_and_matches_independent_fsrs(repo):
    # A3 gate 3: the LIVE report persists a card state via the real adapter and matches
    # an independent FSRS fold -- so a broken adapter projection would fail the gate.
    report = SC.run_cutover_gates(repo, algorithm_version=MVP08, clock=CLOCK)
    gate3 = report.gates[2]
    assert gate3.name == "new_scheduling_projection_correct" and gate3.status == "pass"


def test_barrier_blocks_every_later_gate_when_an_early_gate_fails(repo, monkeypatch):
    # A3: force gate 3 to fail; assert the barrier stops and every LATER gate is blocked
    # and unexecuted (its own probe never runs).
    executed: list[str] = []
    real_side_effects = SC._gate_purpose_side_effects

    def _tracking_side_effects():
        executed.append("purpose_side_effects")
        return real_side_effects()

    monkeypatch.setattr(SC, "_gate_purpose_side_effects", _tracking_side_effects)
    monkeypatch.setattr(
        SC, "_gate_new_scheduling_projection", lambda *_a, **_k: ("fail", "forced gate-3 failure")
    )
    report = SC.run_cutover_gates(repo, algorithm_version=MVP08, clock=CLOCK)
    assert report.barrier_ok is False
    by_ordinal = {g.ordinal: g for g in report.gates}
    assert by_ordinal[3].status == "fail"
    # Gates 4/5/6 are blocked and never executed their own logic.
    for ordinal in (4, 5, 6):
        assert by_ordinal[ordinal].status == "fail"
        assert "blocked" in by_ordinal[ordinal].detail
    assert executed == []  # gate 4's real side-effect probe never ran
