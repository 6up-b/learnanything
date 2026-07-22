"""P2 LEARNING track -- the nine-rung pattern ladder (7 ordinals) (spec_p2 §7.1,
§7.2, §12.3; design B.6)."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.services import failure_triage as FT
from learnloop.services import golden_path_run as GPR
from learnloop.services import pattern_ladder as PL
from learnloop.services.golden_path_fixture import build_golden_path_fixture
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repo, fx


def _advance_to(repo, run_id, *states):
    for i, state in enumerate(states):
        GPR.advance(repo, run_id, to_state=state, reason=f"setup:{state}", idempotency_key=f"setup:{state}:{i}")


# ---------------------------------------------------------------------------
# Reviewable policy DATA (migration 084) matches the in-code authority.
# ---------------------------------------------------------------------------

def test_ladder_policy_data_matches_code_authority(fixture):
    _vault, repo, _fx = fixture
    policy = PL.active_ladder(repo)
    assert policy["policy"]["policy_slug"] == "ladder_v1"
    db_stages = {s["stage_key"]: s for s in policy["stages"]}
    assert set(db_stages) == set(PL.STAGE_BY_KEY)
    # 9 rungs across 7 ordinals (0..6).
    assert len(PL.LADDER_STAGES) == 9
    assert {s.ordinal for s in PL.LADDER_STAGES} == set(range(7))
    for key, code in PL.STAGE_BY_KEY.items():
        row = db_stages[key]
        assert row["ordinal"] == code.ordinal
        assert row["purpose"] == code.purpose
        assert row["run_state"] == code.run_state
        # Widened drift guard (§7.2): EVERY seeded column matches the code authority.
        assert row["pattern_family"] == code.pattern_family
        assert bool(row["requires_cold"]) is code.requires_cold
        assert bool(row["records_scaffold"]) is code.records_scaffold
        # No rung mints certification (§7.2): instructional stages mint nothing.
        assert bool(row["mints_certification"]) is False is code.mints_certification
        # Entry/exit criteria are declared, observable prose (§7.2 stage contracts).
        assert row["entry_criteria"].strip()
        assert row["exit_criteria"].strip()


# ---------------------------------------------------------------------------
# §7.1 nearest-useful rung selection.
# ---------------------------------------------------------------------------

def test_capable_learner_skips_unnecessary_instruction():
    # §12.3: a capable planted learner skips straight to independent practice.
    stage = PL.select_rung(demonstrated_capability=True)
    assert stage.stage_key == "independent_repair"
    assert stage.purpose == "practice"


@pytest.mark.parametrize(
    "reason,expected",
    [
        ("memory_lapse", "explanation"),
        ("procedure_execution", "example_completion"),
        ("method_selection", "setup_only"),
        ("coordination_or_integration", "whole_task_integration"),
        ("schema_or_conceptual_hole", "example_comparison"),
    ],
)
def test_select_rung_maps_each_reason_to_nearest_useful_rung(reason, expected):
    assert PL.select_rung(reason=reason).stage_key == expected


def test_fault_and_ambiguous_reasons_open_no_rung():
    assert PL.select_rung(reason="surface_or_grading_fault") is None
    assert PL.select_rung(reason="unknown_or_ambiguous") is None


def test_method_selection_repair_uses_setup_not_procedure_repetition():
    # §12.3: method-selection repair uses setup/move-spotting, not blind procedure repeat.
    stage = PL.select_rung(reason="method_selection")
    assert stage.stage_key == "setup_only"
    assert stage.pattern_family in ("setup_only", "move_spotting")
    # It never routes into procedure_execution's completion rung.
    assert PL.select_rung(reason="method_selection").stage_key != "example_completion"


# ---------------------------------------------------------------------------
# Entry stage from the diagnostic route (consume failure_triage).
# ---------------------------------------------------------------------------

def test_entry_stage_is_set_by_the_triage_route(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging")
    # A decisive method-selection fault routes the run into `instructing` (route table).
    result = FT.triage(
        repo, run_id,
        attempt={"error_signature": "wrong_method", "grader_confidence": 0.95, "coarse_class": "wrong_method"},
    )
    assert result.decisive and result.routed_to == "instructing"
    entry = PL.enter_ladder(repo, run_id, reason=result.reason)
    assert entry["stage"] == "setup_only"
    # The rung is consistent with the route's run state (both instructing).
    assert PL.STAGE_BY_KEY["setup_only"].run_state == "instructing"
    status = PL.ladder_status(repo, run_id)
    assert status["current_stage"] == "setup_only"


# ---------------------------------------------------------------------------
# §7.2 evidence via the P1 administration adapters -- no unassisted certification.
# ---------------------------------------------------------------------------

def test_instructional_stages_mint_no_certification_and_no_lapse():
    for key in ("explanation", "example_study", "example_completion", "setup_only"):
        effects = PL.stage_evidence_effects(key, eligible=True, failed=True)
        assert effects.mints_unassisted_certification is False
        assert effects.opens_lapse_on_failure is False
        assert effects.applies_fsrs_review is False


def test_practice_rung_is_practice_weighted_but_still_not_certifying():
    effects = PL.stage_evidence_effects("independent_repair", eligible=True, failed=False)
    assert effects.updates_practice_schedule is True
    assert effects.mints_unassisted_certification is False


# ---------------------------------------------------------------------------
# Ladder walk -- climbs each rung with planted evidence, ends ready_to_assess.
# ---------------------------------------------------------------------------

def test_ladder_walks_each_stage_to_ready_to_assess(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "instructing")
    PL.enter_ladder(repo, run_id, reason="memory_lapse")  # entry: explanation

    walked = ["explanation"]
    stage = "explanation"
    for _ in range(10):
        adv = PL.advance_stage(repo, run_id, from_stage=stage, outcome="pass",
                               surface_id=f"surf_{stage}", scaffold_use=0.6)
        if adv.ready_to_assess:
            break
        assert adv.to_stage is not None
        walked.append(adv.to_stage)
        stage = adv.to_stage

    assert walked == [
        "explanation", "example_study", "example_completion", "setup_only",
        "independent_repair", "whole_task_integration", "delayed_independent_practice",
    ]
    assert GPR.project_run(repo, run_id).current_state == "ready_to_assess"


def test_completion_records_scaffold_use(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "completing")
    PL.enter_ladder(repo, run_id, reason="procedure_execution")  # entry: example_completion
    PL.advance_stage(repo, run_id, from_stage="example_completion", outcome="pass",
                     surface_id="surf_completion", scaffold_use=0.8)
    history = PL.ladder_status(repo, run_id)["history"]
    completion_events = [h for h in history if h["stage"] == "example_completion"]
    # The completion rung's exit carries scaffold use (recorded, not certified).
    events = repo.golden_path_run_events_for(run_id)
    import json
    scaffolds = [
        json.loads(e["selected_activity_json"])["scaffold_use"]
        for e in events
        if e["selected_activity_json"] and json.loads(e["selected_activity_json"]).get("stage") == "example_completion"
        and json.loads(e["selected_activity_json"]).get("outcome") == "pass"
    ]
    assert completion_events
    assert 0.8 in scaffolds


def test_completion_scaffold_threshold_and_stage_delay_are_wired(fixture):
    """L7 regression: the two previously-inert knobs are wired into the event stream --
    a scaffold-heavy completion exit is flagged via COMPLETION_SCAFFOLD_THRESHOLD, and the
    delayed independent practice rung carries a due_at computed from STAGE_DELAY_DAYS."""

    import json

    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "completing")
    PL.enter_ladder(repo, run_id, reason="procedure_execution")  # example_completion

    heavy = PL.advance_stage(repo, run_id, from_stage="example_completion", outcome="pass",
                             surface_id="s_heavy", scaffold_use=0.9)
    assert heavy.effects["scaffold_heavy"] is True  # >= COMPLETION_SCAFFOLD_THRESHOLD

    # Climb to the delayed independent practice rung and assert its due_at is stamped.
    stage = heavy.to_stage
    saw_delay = False
    for _ in range(10):
        adv = PL.advance_stage(repo, run_id, from_stage=stage, outcome="pass", surface_id=f"s_{stage}")
        if adv.ready_to_assess:
            break
        stage = adv.to_stage
    rungs = [
        json.loads(e["selected_activity_json"])
        for e in repo.golden_path_run_events_for(run_id)
        if e["selected_activity_json"]
    ]
    for payload in rungs:
        if payload.get("stage") == "delayed_independent_practice":
            assert payload.get("delayed_check_due_at")  # STAGE_DELAY_DAYS window stamped
            saw_delay = True
    assert saw_delay


# ---------------------------------------------------------------------------
# §7.2 repeated varied failures -> needs_review telemetry, not infinite practice.
# ---------------------------------------------------------------------------

def test_repeated_varied_failures_terminate_into_needs_review(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "instructing")
    PL.enter_ladder(repo, run_id, reason="method_selection")  # setup_only

    last = None
    for i in range(PL.REPEATED_FAILURE_REVIEW_N):
        last = PL.advance_stage(repo, run_id, from_stage="setup_only", outcome="fail",
                                surface_id=f"surf_varied_{i}")
    assert last.needs_review is True
    assert last.repeated_failures >= PL.REPEATED_FAILURE_REVIEW_N
    assert GPR.project_run(repo, run_id).current_state == "needs_review"


def test_one_fail_per_rung_while_climbing_never_triggers_review(fixture):
    """§7.2 per-rung counting (L1 regression): a single distinct-surface failure on
    each of several rungs while CLIMBING must never accumulate across rungs into a
    false ``needs_review`` -- only N distinct fails on the SAME rung do.

    Before the per-rung fix ``_failed_surfaces`` counted every failed surface across
    the whole run, so one fail apiece on N rungs tripped the review threshold."""

    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "instructing")
    PL.enter_ladder(repo, run_id, reason="memory_lapse")  # explanation (ordinal 0)

    stage = "explanation"
    climbed = 0
    # Climb through more rungs than the review threshold, failing ONCE (distinct
    # surface) on each rung before passing to the next.
    for i in range(PL.REPEATED_FAILURE_REVIEW_N + 2):
        failed = PL.advance_stage(
            repo, run_id, from_stage=stage, outcome="fail",
            surface_id=f"surf_{stage}_{i}", idempotency_key=f"fail:{stage}:{i}",
        )
        assert failed.needs_review is False, f"one fail on {stage} must not trip review"
        assert failed.repeated_failures == 1  # per-rung count, never the cross-rung sum
        adv = PL.advance_stage(
            repo, run_id, from_stage=stage, outcome="pass",
            surface_id=f"pass_{stage}_{i}", idempotency_key=f"pass:{stage}:{i}",
        )
        climbed += 1
        if adv.ready_to_assess:
            break
        stage = adv.to_stage
    assert climbed > PL.REPEATED_FAILURE_REVIEW_N  # genuinely crossed the naive threshold
    assert GPR.project_run(repo, run_id).current_state != "needs_review"


def test_repeated_failure_counts_distinct_surfaces_only(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "instructing")
    PL.enter_ladder(repo, run_id, reason="method_selection")
    # Failing the SAME surface many times is not "varied" -> no premature review.
    for i in range(PL.REPEATED_FAILURE_REVIEW_N + 2):
        adv = PL.advance_stage(repo, run_id, from_stage="setup_only", outcome="fail",
                               surface_id="surf_same", idempotency_key=f"same:{i}")
    assert adv.needs_review is False
    assert adv.repeated_failures == 1
    assert GPR.project_run(repo, run_id).current_state == "instructing"


# ---------------------------------------------------------------------------
# §12.6 resume -- ladder position rebuilds from events; advance is idempotent.
# ---------------------------------------------------------------------------

def test_kill_resume_mid_ladder_rebuilds_position_from_events(fixture):
    _vault, repo, fx = fixture
    run_id = fx.receipt.run_id
    _advance_to(repo, run_id, "measuring", "triaging", "instructing")
    PL.enter_ladder(repo, run_id, reason="memory_lapse")
    PL.advance_stage(repo, run_id, from_stage="explanation", outcome="pass",
                     surface_id="s1", idempotency_key="adv1")

    before = PL.ladder_status(repo, run_id)

    # A crash/retry with the SAME idempotency key repeats no side effect (§12.6).
    PL.advance_stage(repo, run_id, from_stage="explanation", outcome="pass",
                     surface_id="s1", idempotency_key="adv1")
    after = PL.ladder_status(repo, run_id)
    assert before["current_stage"] == after["current_stage"] == "example_study"
    assert len(before["history"]) == len(after["history"])

    # A fresh Repository (cache dropped) reprojects the identical ladder position.
    reopened = Repository(repo.sqlite_path)
    assert PL.ladder_status(reopened, run_id)["current_stage"] == "example_study"
