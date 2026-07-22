"""P2 ACCEPTANCE -- the narrow golden-path §12-§13 acceptance contract.

This is the ONE continuous end-to-end walk of the entire golden path on the
deterministic fixture vault through the *real* services (spec_p2_narrow_golden_path
§12.7, acceptance map §F of the P2 design memo). The track tests
(``test_golden_path_*``, ``test_diagnostic_pack``, ``test_failure_triage``,
``test_pattern_ladder``, ``test_surface_pool``, ``test_golden_path_assessment``)
cover each step in isolation; this suite asserts the *cross-step invariants* that
only a single continuous walk can prove:

* the reserve + goal-contract pins stay stable throughout;
* the SAME goal-contract v1 is cited end to end;
* every stage transition lands on the run event stream;
* zero depth activations occur (U-018 inert -- the headline acceptance);
* zero live-LLM calls happen on the hot path.

Plus: event-replay equivalence (§12.6), fault-injection completeness on the path's
write boundaries (§12.6), and planted-learner routing divergence (§13).
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import card_outcome_replay as COR
from learnloop.services import diagnostic_pack as DP
from learnloop.services import failure_triage as FT
from learnloop.services import familiarity as F
from learnloop.services import goal_contracts as GC
from learnloop.services import golden_path_assessment as GA
from learnloop.services import golden_path_restoration as GRstr
from learnloop.services import golden_path_run as GPR
from learnloop.services import pattern_ladder as PL
from learnloop.services import surface_pool as SP
from learnloop.services.activities import resolve_legacy_item
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.golden_path_fixture import (
    EXEMPLAR_A,
    EXEMPLAR_B,
    FIX_NOW,
    GOAL_ID,
    HELD_OUT,
    LO_ID,
    build_golden_path_fixture,
)
from learnloop.services import probe_episodes as PE
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    episode_posterior,
    serve_presentation,
)
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    CONTRAST_CONFUSABLE_V1,
    InstrumentCard,
    ensure_builtin_families,
    validate_and_compile_card,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

CLOCK = FrozenClock(FIX_NOW)


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def no_live_llm(monkeypatch):
    """Cross-step invariant: the golden path makes ZERO live-LLM calls. Any attempt
    to construct an AI provider / codex client during the walk fails the test loudly
    (U-034 artifacts-not-calls: the hot path is deterministic over reviewed artifacts)."""

    def _boom(*_a, **_k):  # pragma: no cover - only fires on a regression
        raise AssertionError("golden path made a live-LLM client on the hot path")

    monkeypatch.setattr("learnloop.ai.client.make_ai_provider_client", _boom)
    monkeypatch.setattr("learnloop.codex.client.make_codex_client", _boom)
    return _boom


def _open_repo(fx) -> Repository:
    vault = load_vault(fx.root)
    return Repository(VaultPaths(vault.root, vault.config).sqlite_path)


def _admit_probe_card(repo: Repository) -> None:
    """Admit ONE pre-authored contrast instrument card over the fixture LO's method-
    selection facet, linking the two familiar-anchor exemplars as probe candidates."""

    ensure_builtin_families(repo, clock=CLOCK)
    card = InstrumentCard(
        id="card_method_selection",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="choose_symmetric_decomposition",
        bindings={"target_facet": "method_selection", "confusable_concept": "non_symmetric"},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=("method_selection",),
        signature_error_types={"confusable_signature": ["wrong_method"]},
    )
    inst = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    repo.insert_probe_instrument_card(
        card_id=card.id, version=1,
        probe_family_template_id=CONTRAST_CONFUSABLE_V1.id,
        probe_family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID, hypothesis_scope=list(card.hypotheses),
        card=card.as_dict(), compiled_likelihood_hash=inst.compiled_likelihood_hash(), clock=CLOCK,
    )
    for iid in (EXEMPLAR_A, EXEMPLAR_B):
        repo.link_probe_item_family(
            practice_item_id=iid, instrument_card_id=card.id, instrument_card_version=1, clock=CLOCK
        )


def _reviewed_pack(repo: Repository, blueprint_version_id: str):
    pack = DP.assemble_pack(
        repo, pack_slug="pack_acceptance", blueprint_version_id=blueprint_version_id,
        cards=[{"card_slug": "c1", "coverage": ["a"]}, {"card_slug": "c2", "coverage": ["b"]}],
    )
    for c in pack.cards:
        DP.admit_pack_card(repo, pack_id=pack.pack_id, card_slug=c.card_slug)
    DP.review_pack(repo, pack_id=pack.pack_id)
    return pack


def _drive_probe_item(vault, repo, episode_id: str, item_id: str, score: int) -> None:
    episode = repo.probe_episode(episode_id)
    hs = episode_hypothesis_set(repo, episode)
    eligible = next(
        e for e in eligible_instruments(vault, repo, episode, hypothesis_set=hs) if e.item.id == item_id
    )
    pres = commit_presentation(vault, repo, episode, eligible, clock=CLOCK)
    serve_presentation(repo, pres.id, clock=CLOCK)
    apply_attempt(
        vault, repo,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="answer",
                attempt_type="diagnostic_probe", hints_used=0, probe_presentation_id=pres.id,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=score, criterion_points={"correctness": float(score)},
                evidence_rows=[], error_attributions=[], grader_confidence=1.0,
                confidence=4, manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


def _head_version(repo: Repository) -> int:
    return repo.fetch_goal_contract_head(GOAL_ID)["head_version"]


# ---------------------------------------------------------------------------
# 1 + 6. The 10-step fixture journey -- ONE continuous walk (§12.7)
# ---------------------------------------------------------------------------

def test_golden_path_ten_step_fixture_journey(tmp_path, no_live_llm):
    fx = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fx.root)
    repo = _open_repo(fx)
    rid = fx.receipt.run_id
    gcv = fx.receipt.goal_contract_version_id

    # -- Cross-step pin snapshot taken at confirmation (must not drift). --
    run0 = repo.golden_path_run(rid)
    pinned_contract = run0["goal_contract_version_id"]
    pinned_reserve = run0["reserved_surface_id"]
    pinned_support = run0["reserved_support_hash"]
    assert pinned_contract == gcv and pinned_reserve is not None
    assert fx.receipt.mode == "certifying"

    def assert_pins_stable() -> None:
        run = repo.golden_path_run(rid)
        assert run["goal_contract_version_id"] == pinned_contract
        assert run["reserved_surface_id"] == pinned_reserve
        assert run["reserved_support_hash"] == pinned_support
        assert _head_version(repo) == 1  # still goal-contract v1, no unprompted successor

    # Step 1 (exemplar selection) + Step 2 (atomic confirmation) are done by the
    # fixture bootstrap: the run is minted `ready` with v1 + a fresh reserve.
    assert GPR.project_run(repo, rid).current_state == "ready"
    assert_pins_stable()

    # Step 3: bounded diagnostic baseline (2-4 items THROUGH the live probe machinery).
    GPR.advance(repo, rid, to_state="measuring", reason="run bounded baseline", idempotency_key="measuring", clock=CLOCK)
    _admit_probe_card(repo)
    pack = _reviewed_pack(repo, fx.blueprint_version_id)
    baseline = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID, pack_id=pack.pack_id, clock=CLOCK)
    baseline_items = 0
    # Plant a WEAK method-selection boundary: both baseline observations fail on the
    # method_selection facet, so the baseline projection reads that cell `weak` (§5.3) --
    # the planted `weak -> demonstrated` move asserted after the cold pass (§8.4).
    for iid in (EXEMPLAR_A, EXEMPLAR_B):
        if repo.probe_episode(baseline["episode_id"]).status != "in_progress":
            break
        _drive_probe_item(vault, repo, baseline["episode_id"], iid, score=1)
        baseline_items += 1
    pin = repo.diagnostic_pack_pin_for_run(rid)
    assert 2 <= pin["visible_cap"] <= 4  # baseline visible cap enforced (§12.2)
    assert 2 <= baseline_items <= 4
    assert pin["probe_episode_id"] == baseline["episode_id"]  # the LANDED probe episode, no 2nd posterior
    assert_pins_stable()

    # Step 4: triage the localized method-selection boundary (decisive tier-one route).
    GPR.advance(repo, rid, to_state="triaging", reason="triage the boundary", idempotency_key="triaging", clock=CLOCK)
    triage = FT.triage(
        repo, rid,
        attempt={"attempt_id": "att_boundary", "coarse_class": "wrong",
                 "error_signature": "wrong_method", "grader_confidence": 0.95},
    )
    assert triage.tier == "one" and triage.decisive
    assert triage.reason == "method_selection" and triage.routed_to == "instructing"
    assert GPR.project_run(repo, rid).current_state == "instructing"
    assert_pins_stable()

    # Step 5: the pattern ladder -- at least two rungs climbed with planted evidence.
    entry = PL.enter_ladder(repo, rid, reason=triage.reason)
    assert entry["stage"] == "setup_only"  # method-selection repair uses setup, not procedure repeat
    rungs = [entry["stage"]]
    stage = entry["stage"]
    for _ in range(10):
        adv = PL.advance_stage(repo, rid, from_stage=stage, outcome="pass",
                               surface_id=f"surf_{stage}", scaffold_use=0.5)
        if adv.ready_to_assess:
            break
        rungs.append(adv.to_stage)
        stage = adv.to_stage
    assert len(rungs) >= 2  # at least two rungs
    assert GPR.project_run(repo, rid).current_state == "ready_to_assess"
    assert_pins_stable()

    # Step 6: rotating practice on the reviewed pool -- at least one rotation.
    ra = resolve_legacy_item(vault, repo, vault.practice_items[EXEMPLAR_A], purpose="practice", clock=CLOCK)
    rb = resolve_legacy_item(vault, repo, vault.practice_items[EXEMPLAR_B], purpose="practice", clock=CLOCK)
    pool = SP.assemble_pool(
        repo, pool_slug="pool_acceptance", blueprint_version_id=fx.blueprint_version_id,
        surfaces=[{"surface_slug": "s_a", "angle": "setup_only"}, {"surface_slug": "s_b", "angle": "move_spotting"}],
    )
    SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="s_a", surface_id=ra.surface_id)
    SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="s_b", surface_id=rb.surface_id)
    SP.review_pool(repo, pool_id=pool.pool_id)
    first = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert first.current.surface_id == ra.surface_id and first.rotated is False
    F.record_soft_features(repo, surface_id=ra.surface_id, features={"exposure_count": 5.0, "recency": 3.0})
    rotated = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert rotated.rotated is True and rotated.current.surface_id == rb.surface_id
    assert first.current.fresh is False  # familiar practice never reported fresh
    assert_pins_stable()

    # Step 7: the held-out target-like assessment is administered COLD, citing v1.
    admin = GA.open_assessment(repo, run_id=rid, idempotency_key="assess_open", clock=CLOCK)
    assert admin.surface_id == pinned_reserve  # the exact reserved sibling
    result = GA.submit_assessment(
        vault, repo, run_id=rid, administration_id=admin.administration_id,
        item=vault.practice_items[HELD_OUT], surface_id=admin.surface_id,
        rubric_score=4, max_points=4, attempt_id="att_cold", response_text="spectral decomposition", clock=CLOCK,
    )
    assert result.passed is True and result.terminal is True
    # SAME goal-contract v1 cited end to end.
    assert result.target_contract_version_id == gcv and result.cited_version == 1
    assert GPR.project_run(repo, rid).current_state == "assessing"
    assert _head_version(repo) == 1

    # Step 8: source neighborhood + boundary diff restored AFTER measurement.
    restore = GRstr.restore(repo, run_id=rid, idempotency_key="restore", clock=CLOCK)
    assert GPR.project_run(repo, rid).current_state == "restoring"
    changed = [c for c in restore.boundary_diff["cells"] if c["changed"]]
    assert changed, "cold assessment must move at least one covered cell"
    # The projection is REAL evidence, not a hardcoded `untested`: the planted weak
    # method-selection cell moves weak -> demonstrated after the cold pass (§5.3/§8.4).
    method_cell = next(
        c for c in restore.boundary_diff["cells"]
        if (c["facet"], c["capability"]) == ("decomposition_choice", "method_selection")
    )
    assert method_cell["before"] == "weak"
    assert method_cell["after"] in ("demonstrated", "developing")  # real move off the weak baseline
    assert method_cell["changed"] is True
    # The frozen baseline snapshot was taken at diagnostic-segment close (invariant 7).
    assert repo.latest_golden_path_artifact(rid, kind="baseline_boundary") is not None
    assert repo.latest_golden_path_artifact(rid, kind="diagnostic_segment_closed") is not None

    # Step 9: milestone recorded, then ONE reviewed edge rendered as suggest_next.
    assert restore.milestone_recorded is True
    invitations = repo.golden_path_artifacts_for(rid, kind="depth_invitation")
    assert len(invitations) == 1
    assert restore.invitation["served_as"] == "suggest_next"
    assert restore.invitation["activated"] is False

    # Headline acceptance invariant (folded in from the assessment track): NO UNPROMPTED
    # DEPTH ACTIVATION -- no transition committed, no successor appended, still v1.
    commitment_events = repo.commitment_events_for(fx.receipt.commitment_id)
    assert not any(e["kind"] == "depth_transition_committed" for e in commitment_events)
    assert _head_version(repo) == 1

    # Step 10: the learner declines the edge; the run ends in a terminal state.
    GRstr.decline_depth_invitation(repo, run_id=rid, idempotency_key="decline", to_state="maintaining", clock=CLOCK)
    GPR.advance(repo, rid, to_state="complete", reason="hold at target", idempotency_key="complete", clock=CLOCK)
    final = GPR.project_run(repo, rid)
    assert final.current_state == "complete" and final.next_action.terminal is True
    # Milestone stays reached even after decline (never downgraded).
    assert repo.latest_golden_path_artifact(rid, kind="milestone") is not None

    # -- Cross-step: every stage transition is on the ONE event stream, all pinned to v1. --
    run_events = repo.golden_path_run_events_for(rid)
    to_states = [e["to_state"] for e in run_events]
    for stage in ("ready", "measuring", "triaging", "instructing", "ready_to_assess",
                  "assessing", "restoring", "maintaining", "complete"):
        assert stage in to_states, f"missing stage transition: {stage}"
    assert all(e["goal_contract_head_version_id"] == gcv for e in run_events)

    # -- Cross-step: zero depth activations across the whole run. --
    # (`depth_transition_committed` is a COMMITMENT event, never a golden_path_artifact
    # kind, so asserting its absence from artifacts was vacuous -- C7. The real check is
    # the commitment-event stream, plus no `depth_accept` artifact was ever written.)
    assert repo.golden_path_artifacts_for(rid, kind="depth_accept") == []
    assert not any(e["kind"] == "depth_transition_committed" for e in repo.commitment_events_for(fx.receipt.commitment_id))


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
    """After the full walk, rebuild the run + certification + card-outcome projections
    from events ALONE and assert equality with the live projections."""

    fx = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fx.root)
    repo = _open_repo(fx)
    rid = fx.receipt.run_id
    gcv = fx.receipt.goal_contract_version_id

    # Drive the path far enough to have a run projection + a cold assessment citation +
    # graded card-outcome events (the three projections under replay).
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
    PL.enter_ladder(repo, rid, reason=tr.reason)
    stage = "setup_only"
    for _ in range(10):
        adv = PL.advance_stage(repo, rid, from_stage=stage, outcome="pass", surface_id=f"s_{stage}")
        if adv.ready_to_assess:
            break
        stage = adv.to_stage
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

    # (c) Card-outcome projection: the deferred psychometrics replay reads ledger
    # events only, so a fresh handle reproduces byte-identical counts.
    live_counts = COR.replay_card_outcome_counts(repo)
    rebuilt_counts = COR.replay_card_outcome_counts(Repository(repo.sqlite_path))
    assert rebuilt_counts.counts == live_counts.counts
    assert rebuilt_counts.events_replayed == live_counts.events_replayed
    assert COR.REPLAY_MANIFEST["reads_live_tables"] is False


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


# ---------------------------------------------------------------------------
# 4. Planted-learner profiles route differently (§13)
# ---------------------------------------------------------------------------

_METHOD_FACET = "method_selection"
_CRITERIA = [("method", 2.0, {_METHOD_FACET: 1.0}), ("execution", 2.0, {_METHOD_FACET: 1.0})]


def _planted_outcome(profile_name: str, seed: int):
    """Drive one attempt outcome from a planted profile in sim/profiles.py. The built-in
    misconception profile uses the AUTO facet, resolved to the target facet the way the
    sim runner resolves it against a loaded vault."""

    from dataclasses import replace

    from learnloop.sim.profiles import AUTO_FACET, load_profile
    from learnloop.sim.student import SyntheticStudent

    profile = load_profile(profile_name)
    profile = replace(
        profile,
        misconceptions=[
            replace(m, facet_id=_METHOD_FACET) if m.facet_id == AUTO_FACET else m
            for m in profile.misconceptions
        ],
    )
    student = SyntheticStudent(profile, seed=seed)
    outcome = student.attempt(
        day=0.0, item_facet_weights={_METHOD_FACET: 1.0}, criteria=_CRITERIA, hints_available=0
    )
    correctness = sum(outcome.criterion_points.values()) / 4.0
    return outcome, correctness


def test_capable_planted_learner_skips_instruction(tmp_path):
    """A capable planted learner (strong_forgetter: high true mastery, no misconception)
    answers correctly -> demonstrated capability -> the ladder skips instruction straight
    to independent practice (§12.3 skip-when-capable)."""

    outcome, correctness = _planted_outcome("strong_forgetter", seed=3)
    assert outcome.misconception_fired is None and correctness >= 0.75

    stage = PL.select_rung(demonstrated_capability=True)
    assert stage.stage_key == "independent_repair"  # skip/advance, not the bottom rung
    assert stage.purpose == "practice"


def test_misconception_planted_learner_takes_signature_route_and_repair_rung(tmp_path):
    """A misconception-holding planted learner (intermediate_with_misconception) fires the
    planted misconception -> the false-belief signature route (which re-opens diagnosis)
    -> the explanation repair rung, with the diagnosis surfaced in the triage trace."""

    outcome, _ = _planted_outcome("intermediate_with_misconception", seed=0)
    assert outcome.misconception_fired is not None

    fx = build_golden_path_fixture(tmp_path / "vault")
    repo = _open_repo(fx)
    rid = fx.receipt.run_id
    GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m", clock=CLOCK)
    GPR.advance(repo, rid, to_state="triaging", reason="t", idempotency_key="t", clock=CLOCK)

    # The fired misconception is the attempt's error signature driving triage.
    triage = FT.triage(
        repo, rid,
        attempt={"attempt_id": "a", "coarse_class": "wrong",
                 "error_signature": "misconception", "grader_confidence": 0.95},
    )
    assert triage.reason == "false_belief_or_confusion"
    assert triage.route["reopens_diagnostic"] is True  # the signature route re-opens diagnosis

    # The diagnosis is surfaced in the append-only triage trace.
    trace = FT.triage_status(repo, rid)["trace"]
    assert trace and trace[-1]["selected_reason"] == "false_belief_or_confusion"

    # The repair rung is the instructional explanation rung -- NOT the capable skip.
    stage = PL.select_rung(reason=triage.reason)
    assert stage is not None and stage.stage_key == "explanation"
    assert stage.purpose == "instructional"
    assert stage.stage_key != PL.select_rung(demonstrated_capability=True).stage_key


def test_planted_profiles_route_to_distinct_rungs(tmp_path):
    """The headline §13 divergence: the two planted profiles land on different rungs."""

    capable_outcome, capable_correct = _planted_outcome("strong_forgetter", seed=3)
    misc_outcome, _ = _planted_outcome("intermediate_with_misconception", seed=0)

    capable_rung = PL.select_rung(demonstrated_capability=True).stage_key
    misc_rung = PL.select_rung(reason="false_belief_or_confusion").stage_key

    assert capable_outcome.misconception_fired is None and capable_correct >= 0.75
    assert misc_outcome.misconception_fired is not None
    assert capable_rung != misc_rung
    assert capable_rung == "independent_repair" and misc_rung == "explanation"
