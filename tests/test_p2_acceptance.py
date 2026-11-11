"""P2 ACCEPTANCE -- what the narrow golden path's §12 acceptance contract still proves
about the services the Golden Path removal kept (the run machine, the diagnostic pack,
triage, the cold assessment and the probe episodes).

The ten-step walk and the planted-learner rung routing went with the pattern ladder
and the practice pool. What stays: instruction closes the diagnostic segment and a
re-entry is fresh (P0 invariant 7), event-replay equivalence of the run and
certification projections (§12.6), and the diagnostic-baseline write boundary's
fault injection (§12.6).
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.diagnosis import diagnostic_pack as DP
from learnloop.diagnosis import failure_triage as FT
from learnloop.goals import goal_contracts as GC
from learnloop.curriculum import golden_path_assessment as GA
from learnloop.curriculum import golden_path_run as GPR
from learnloop.curriculum.golden_path_fixture import (
    EXEMPLAR_A,
    EXEMPLAR_B,
    GOAL_ID,
    HELD_OUT,
    LO_ID,
    build_golden_path_fixture,
)
from learnloop.diagnosis import probe_episodes as PE
from learnloop.diagnosis.probe_episodes import (
    episode_posterior,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.p2_acceptance_helpers import CLOCK, _admit_probe_card, _drive_probe_item, _reviewed_pack

# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------

def _open_repo(fx) -> Repository:
    vault = load_vault(fx.root)
    return Repository(VaultPaths(vault.root, vault.config).sqlite_path)


# ---------------------------------------------------------------------------
# C1 -- instruction closes the diagnostic segment; re-entry mints a FRESH episode
# (P0 invariant 7 / §12.2). Regression: fails before the close hook existed.
# ---------------------------------------------------------------------------

def test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh(tmp_path):
    fx = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fx.root)
    repo = _open_repo(fx)
    rid = fx.receipt.run_id

    GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m", clock=CLOCK)
    _admit_probe_card(repo)
    pack = _reviewed_pack(repo, fx.blueprint_version_id)
    baseline = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID, pack_id=pack.pack_id, clock=CLOCK)
    episode_a = baseline["episode_id"]
    # One failing baseline observation moves episode A's posterior off its prior.
    _drive_probe_item(vault, repo, episode_a, EXEMPLAR_A, score=1)
    ep_a_rec = repo.probe_episode(episode_a)
    post_a = episode_posterior(vault, repo, ep_a_rec)
    assert post_a.total_observations == 1 and post_a.posterior != post_a.prior  # A moved off its prior
    assert repo.probe_episode(episode_a).status == "in_progress"

    # The FIRST transition into an instruction state closes the diagnostic segment.
    GPR.advance(repo, rid, to_state="instructing", reason="teach", idempotency_key="i", clock=CLOCK)
    assert repo.probe_episode(episode_a).status == "converted_to_tutoring"  # segment closed
    assert repo.latest_golden_path_artifact(rid, kind="diagnostic_segment_closed") is not None

    # A later re-entry to measuring mints a FRESH episode with a fresh (prior) posterior
    # -- the closed segment never re-opens, so the posterior does not continue.
    assert repo.open_probe_episode(LO_ID) is None
    episode_b = PE.enter_episode(vault, repo, LO_ID, trigger="initial", goal_id=GOAL_ID, clock=CLOCK)
    assert episode_b.id != episode_a  # a genuinely new episode
    fresh = episode_posterior(vault, repo, episode_b)
    # Fresh posterior: it equals episode B's OWN prior and replays ZERO observations --
    # episode A's evidence does not continue into the re-minted segment.
    assert fresh.total_observations == 0
    assert fresh.posterior == fresh.prior


# ---------------------------------------------------------------------------
# 2. Event-replay equivalence (§12.6) -- rebuild projections from events alone
# ---------------------------------------------------------------------------

def test_event_replay_equivalence_after_full_walk(tmp_path):
    """After the full walk, rebuild the run and certification projections from events
    ALONE and assert equality with the live projections."""

    fx = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fx.root)
    repo = _open_repo(fx)
    rid = fx.receipt.run_id
    gcv = fx.receipt.goal_contract_version_id

    # Drive the path far enough to have a run projection and a cold assessment
    # citation (the two projections under replay).
    GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m", clock=CLOCK)
    _admit_probe_card(repo)
    pack = _reviewed_pack(repo, fx.blueprint_version_id)
    baseline = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID, pack_id=pack.pack_id, clock=CLOCK)
    for iid in (EXEMPLAR_A, EXEMPLAR_B):
        if repo.probe_episode(baseline["episode_id"]).status != "in_progress":
            break
        _drive_probe_item(vault, repo, baseline["episode_id"], iid, score=4)
    GPR.advance(repo, rid, to_state="triaging", reason="t", idempotency_key="t", clock=CLOCK)
    tr = FT.triage(repo, rid, attempt={"attempt_id": "a", "coarse_class": "wrong",
                                       "error_signature": "wrong_method", "grader_confidence": 0.95})
    assert GPR.project_run(repo, rid).current_state == tr.routed_to == "instructing"
    # The removed pattern ladder climbed its rungs here; the run's own legal step stands in.
    GPR.advance(repo, rid, to_state="ready_to_assess", reason="repair done", idempotency_key="rta", clock=CLOCK)
    admin = GA.open_assessment(repo, run_id=rid, idempotency_key="ao", clock=CLOCK)
    result = GA.submit_assessment(
        vault, repo, run_id=rid, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=4, max_points=4, attempt_id="cold", response_text="ok", clock=CLOCK,
    )

    # (a) Run projection: corrupt every cached current_state, then rebuild from events.
    live_run = GPR.project_run(repo, rid)
    with repo.connection() as c:
        c.execute("UPDATE golden_path_runs SET current_state = 'draft'")
        c.commit()
    rebuilt_run = GPR.project_run(Repository(repo.sqlite_path), rid)
    assert rebuilt_run == live_run  # RunState is a pure fold of the event log

    # (b) Certification: the canonical citation is a pure projection over the
    # administration + observation events -- re-derive it from a fresh handle.
    rebuilt_citation = GC.certify_from_administration(
        Repository(repo.sqlite_path), administration_id=admin.administration_id
    )
    assert rebuilt_citation.cited_version_id == result.target_contract_version_id == gcv
    assert rebuilt_citation.cited_version == result.cited_version == 1
    assert rebuilt_citation.terminal is True


# ---------------------------------------------------------------------------
# 3. Fault-injection completeness on the golden path's write boundaries (§12.6)
# ---------------------------------------------------------------------------

def test_fault_injection_diagnostic_baseline_boundary_yields_exactly_one(tmp_path):
    """Write-boundary enumeration (see module docstring / report). The confirmation,
    run-transition, administration/grade/observation, assessment-burn, restoration, and
    milestone/invitation boundaries each have a dedicated idempotency/fault test in the
    track suites. The diagnostic-baseline boundary is exercised here: a crash/retry
    reuses the open episode + the single pack pin -- exactly one of each side effect."""

    fx = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fx.root)
    repo = _open_repo(fx)
    rid = fx.receipt.run_id
    GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m", clock=CLOCK)
    _admit_probe_card(repo)
    pack = _reviewed_pack(repo, fx.blueprint_version_id)

    first = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID, pack_id=pack.pack_id, clock=CLOCK)
    # Simulate a crash right after the write, then retry the SAME boundary.
    again = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID, pack_id=pack.pack_id, clock=CLOCK)
    assert again["episode_id"] == first["episode_id"]  # the open episode is reused, not re-minted

    # Exactly one episode for the LO, exactly one pack pin for the run.
    with repo.connection() as c:
        episodes = c.execute(
            "SELECT COUNT(*) FROM probe_episodes WHERE learning_object_id = ?", (LO_ID,)
        ).fetchone()[0]
    assert episodes == 1
    pins = [p for p in [repo.diagnostic_pack_pin_for_run(rid)] if p is not None]
    assert len(pins) == 1 and pins[0]["probe_episode_id"] == first["episode_id"]

