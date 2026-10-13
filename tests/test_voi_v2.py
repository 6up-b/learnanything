"""voi-v2: the value-of-information successor's last review findings and the
multi-family EVSI study's robust changes (docs/reviews/voi-v2.md).

Fixes (Codex final verify, ``voi-final-verify``):

* F2: on the predictive objective the conditional valuation recomputes the
  predictive information on each expected posterior branch;
* F10: the plan admits project probes against the minutes left after the
  requested items and the lane constraints, on build and on every refresh;
* F12: migration 188 backfills the legacy ``decision_features`` follow-up
  receipts, which the reader then sees exactly once.

The study's ship list (``docs/reviews/evsi-multisim.md`` §6.1), each behind its
own switch:

* rank 1, ``voi_stopping.robust_gate_with_value`` (false): the robust
  completion gate does not end an episode while value decides;
* rank 2, ``voi_stopping.lookahead_max_checks`` (3): the best 2-3 checks valued
  jointly when no single check pays;
* rank 3, ``voi_stopping.robust_quantile`` (0.25) in the successor's value
  gate.

At their restore values (true, 1, 0.10) the successor's decisions are the
branch's before the study, exactly (``tests/voi_restore_golden.json``).
"""

from __future__ import annotations

import json
import math

import pytest

from learnloop.daily_plan.lanes import register_scheduled_check_provider, unregister_scheduled_check_provider, ScheduledCheck
from learnloop.db.repositories import Repository
from learnloop.diagnosis import voi_stopping as voi

from tests.daily_plan_fakes import make_env, scheduled
from tests.helpers import create_daily_plan_vault
from tests.test_voi_stopping import _admission, _classify, _ctx, _probe


# ── F2: the predictive objective, recomputed on each posterior branch ────────

#: Four equally likely hypotheses (X, Y).
_XY = {"x0y0": 0.25, "x0y1": 0.25, "x1y0": 0.25, "x1y1": 0.25}


def _reveal_x():
    return {label: {f"x{label[1]}": 1.0} for label in _XY}


def _reveal_xy():
    return {label: {label: 1.0} for label in _XY}


def _target_on_x(accuracy=1.0):
    """A held-out target whose answer depends only on X."""

    return {
        label: {"t1": accuracy if label[1] == "1" else 1.0 - accuracy,
                "t0": 1.0 - accuracy if label[1] == "1" else accuracy}
        for label in _XY
    }


def _predictive_channel(likelihood, *, targets=None, belief="episode_xy"):
    return {
        "belief_key": belief,
        "prior": dict(_XY),
        "likelihood": likelihood,
        "objective": "predictive_eig",
        "targets": [_target_on_x(), _target_on_x(0.8)] if targets is None else targets,
    }


def _predictive_terms(likelihood, *, term=1.0, lo="lo_xy"):
    """A check whose only information is its predictive term (the reward's
    normalized predictive EIG, ``term``)."""

    return voi.InformationTerms(
        learning_object_id=lo, hypothesis_nats=term, lo_prior_variance=1.0, lo_posterior_variance=1.0,
        discount=1.0, facets=(),
        hypothesis=voi.HypothesisChannel.from_mapping(_predictive_channel(likelihood), hypothesis_term=term),
    )


def test_after_a_check_reveals_x_one_revealing_x_and_y_adds_no_predictive_information():
    """F2 reopened (the reviewer's reproduction): targets depend only on X. A
    reveals X, B reveals (X, Y); each alone removes all the targets'
    predictive uncertainty (normalized term 1). After A, B adds none."""

    a, b = _predictive_terms(_reveal_x()), _predictive_terms(_reveal_xy())
    root = voi.InformationState()
    assert a.conditional_nats(root)["hypothesis"] == pytest.approx(1.0)
    assert b.conditional_nats(root)["hypothesis"] == pytest.approx(1.0)
    after_a = root.after(a)
    assert b.conditional_nats(after_a)["hypothesis"] == pytest.approx(0.0, abs=1e-12)
    assert a.conditional_nats(root.after(b))["hypothesis"] == pytest.approx(0.0, abs=1e-12)
    assert b.hypothesis_conditioning == "expected_posterior_branches:predictive_objective"
    # A check that reveals only Y tells nothing about the targets, alone or after A.
    reveal_y = {label: {f"y{label[3]}": 1.0} for label in _XY}
    channel = voi.HypothesisChannel.from_mapping(_predictive_channel(reveal_y), hypothesis_term=0.5)
    assert channel is None  # zero standalone predictive information: no hypothesis channel


def test_the_greedy_admission_does_not_admit_a_check_whose_targets_are_already_known():
    """Through the plan's own admission (as the reviewer ran it): A (1 minute)
    is admitted, B (2 minutes) is worth zero minutes given A, not 30."""

    def probe(item_id, likelihood):
        return _probe(item_id, "lo_xy", {}, lo_variance=1.0, hypothesis_eig=1.0, channel=_predictive_channel(likelihood))

    minutes = {"pi_x": 1.0, "pi_xy": 2.0}.__getitem__
    pool = {item.practice_item_id: item for item in _classify([probe("pi_x", _reveal_x()), probe("pi_xy", _reveal_xy())], minutes=minutes)}
    assert pool["pi_x"].lane == "maintain"
    assert pool["pi_xy"].lane is None and pool["pi_xy"].voi["decision"] == voi.STOP
    subject = pool["pi_xy"].voi["subject"]
    assert subject["evsi_robust_minutes"] == pytest.approx(0.0, abs=1e-9)
    assert subject["detail"]["hypothesis_conditioning"] == "expected_posterior_branches:predictive_objective"
    assert subject["detail"]["unconditioned_eig_nats"] * voi.VALUE_PER_NAT_MINUTES > 2.0  # alone it pays


def test_the_predictive_information_matches_the_probe_episodes_own_objective(tmp_path):
    """The channel's standalone predictive information is the probe episode's
    own §7.4 predictive EIG (``instrument_predictive_information_gain``), for
    every eligible instrument of the real probe vault, and the scheduler hands
    a predictive-objective probe its held-out targets."""

    from learnloop.diagnosis.probe_episodes import eligible_instruments, episode_posterior
    from tests.test_voi_stopping import LO, _build, _long_probe_vault

    vault, repository = _long_probe_vault(tmp_path, "mvp-0.17")
    episode = repository.open_probe_episode(LO)
    posterior = episode_posterior(vault, repository, episode).posterior
    eligible = eligible_instruments(vault, repository, episode, posterior=posterior)
    assert eligible and any(entry.selection_objective == "predictive_eig" for entry in eligible)
    for entry in eligible:
        body = voi.hypothesis_channel_body(episode.id, entry, posterior, objective="predictive_eig")
        assert len(body["targets"]) == entry.predictive_target_count
        channel = voi.HypothesisChannel.from_mapping(body, hypothesis_term=1.0)
        if entry.predictive_eig > 0:
            assert channel is not None
            assert channel.standalone_nats == pytest.approx(entry.predictive_eig, rel=1e-9, abs=1e-12)
    probes = [item for item in _build(vault, repository) if item.components.get("probe_eig", 0.0) > 0.0]
    predictive = [item for item in probes if item.components.get("probe_predictive_primary") == 1.0]
    assert predictive
    for item in predictive:
        assert item.hypothesis_channel["objective"] == "predictive_eig" and item.hypothesis_channel["targets"]
        terms = voi.InformationTerms.from_reward_debug(
            item.learning_object_id, item.reward_debug,
            total_nats=item.components["probe_eig_total"], hypothesis_channel=item.hypothesis_channel,
        )
        assert terms is not None and terms.hypothesis_conditioning == "expected_posterior_branches:predictive_objective"


# ── F10: admission against the minutes the plan can actually use ────────────


def _overlapping_probes():
    return [
        _probe("pi_a", "lo_repo", {"facet_x": 2.0, "facet_y": 1.0}, mass=0.0),
        _probe("pi_b", "lo_repo", {"facet_x": 1.0}, mass=0.0),
    ]


def _requested_plan(tmp_path, *, version="mvp-0.17"):
    """Twenty minutes, a fifteen-minute requested item, and two overlapping
    project probes: A (twelve minutes) and B (five)."""

    from learnloop.daily_plan.engine import build_plan

    paths = create_daily_plan_vault(
        tmp_path / version.replace(".", "_"),
        learning_objects={"lo_repo": [("pi_req", 14.5), ("pi_a", 11.5), ("pi_b", 4.5)]},
        version=version,
    )

    def provider(_vault, _repository, item_ids):
        return {item_id: ScheduledCheck("project_probe") for item_id in item_ids if item_id in {"pi_a", "pi_b"}}

    register_scheduled_check_provider(provider)
    env = make_env(paths.root, [scheduled("pi_req", "lo_repo"), *_overlapping_probes()], requested=["pi_req"])
    record = build_plan(env, kind="normal", budget=20.0, remembered=20, minutes_source="chip")
    return env, record, provider


def _plan_decisions(env):
    with env.repository.connection() as connection:
        return [
            json.loads(row[0])
            for row in connection.execute("SELECT detail_json FROM router_decisions WHERE decision_kind = 'plan_block'")
        ]


def test_project_probes_are_admitted_against_the_minutes_left_after_requests(tmp_path):
    """F10 reopened (the reviewer's reproduction through the real admission,
    split and chooser): the request takes fifteen of twenty minutes, so A
    cannot be planned; B is valued without A and planned, not stop_for_today."""

    from tests.test_daily_plan_build import _run_to_end

    env, _record, provider = _requested_plan(tmp_path)
    try:
        record, _steps = _run_to_end(env)
    finally:
        unregister_scheduled_check_provider(provider)
    planned = {item.practice_item_id for item in record.items()}
    assert planned == {"pi_req", "pi_b"}
    decisions = [d for detail in _plan_decisions(env) for d in detail.get("voi_decisions", [])]
    first = [d for d in decisions if d.get("subject_ref") == "pi_b"][0]
    assert first["decision"] == voi.CONTINUE and first["context"]["minutes_budget"] == pytest.approx(5.0)
    assert first["subject"]["detail"]["conditioning"] == "none_chosen"
    a = [d for d in decisions if d.get("subject_ref") == "pi_a"][0]
    assert a["reason"] == voi.REASON_DOES_NOT_FIT


def test_a_refresh_admits_against_the_minutes_left_and_conditions_on_planned_probes(tmp_path):
    """The live refresh values the remaining probes against the plan's minutes
    left (not its budget) and conditions them on the probes it already
    planned, which it does not charge again."""

    from learnloop.daily_plan.engine import _live_context

    env, record, provider = _requested_plan(tmp_path)
    try:
        _context, built = _live_context(env, record)
    finally:
        unregister_scheduled_check_provider(provider)
    assert record.planned_ids() >= {"pi_req", "pi_b"}  # the first block: the request, then B
    probes = {item.practice_item_id: item for item in built.pool if item.check_kind == "project_probe"}
    assert probes["pi_b"].voi["reason"] == voi.REASON_ALREADY_PLANNED
    assert probes["pi_b"].voi["decision"] == voi.CONTINUE
    a = probes["pi_a"].voi
    assert a["context"]["minutes_budget"] == pytest.approx(record.minutes_left()) == pytest.approx(0.0)
    assert a["context"]["chosen_before"] == ["pi_b"]  # conditioned on the planned probe
    assert a["reason"] == voi.REASON_DOES_NOT_FIT


def test_a_minutes_change_values_probes_against_the_new_minutes_left(tmp_path, monkeypatch):
    """A chip tap re-plans the rest: the probes are valued against what the
    new budget leaves after the planned blocks, not the old budget."""

    from learnloop.daily_plan import engine

    env, record, provider = _requested_plan(tmp_path)
    seen = []
    original = engine._live_context

    def spy(env_, record_, **kwargs):
        context, built = original(env_, record_, **kwargs)
        seen.append({item.practice_item_id: item.voi for item in built.pool if item.check_kind == "project_probe"})
        return context, built

    monkeypatch.setattr(engine, "_live_context", spy)
    try:
        engine.set_minutes(env, 30)
    finally:
        unregister_scheduled_check_provider(provider)
    assert seen
    a = seen[0]["pi_a"]
    # 30 minutes less the 20 planned (neither the old budget, 20, nor the old
    # minutes left, 0).
    assert a["context"]["minutes_budget"] == pytest.approx(30.0 - record.minutes_planned()) == pytest.approx(10.0)
    assert a["context"]["chosen_before"] == ["pi_b"] and a["subject"]["detail"]["conditioning"] == "chosen_before"


def test_the_usable_minutes_are_what_the_requests_and_lanes_leave():
    """The minutes project probes are admitted against: the plan's minutes
    less the requested items reserved before the split (on a build), or the
    plan's minutes left (on a refresh, less requests a crash left unplaced),
    and none when the plan's lanes exclude maintain."""

    from learnloop.daily_plan.engine import _usable_probe_minutes

    assert _usable_probe_minutes(minutes=20.0, reserved=15.0, lanes_allowed=("repair", "maintain")) == 5.0
    assert _usable_probe_minutes(minutes=20.0, reserved=25.0, lanes_allowed=("maintain",)) == 0.0
    assert _usable_probe_minutes(minutes=20.0, reserved=0.0, lanes_allowed=("repair", "new")) == 0.0


# ── F12: legacy follow-up receipts after migration 188 ──────────────────────


def _db_before_188(tmp_path):
    from learnloop.db.migrate import apply_migrations, default_migrations_dir

    before = tmp_path / "before_188"
    before.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) < 188:
            (before / path.name).write_bytes(path.read_bytes())
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=before)
    return sqlite_path


def _legacy_body(attempt_id):
    return {
        "forecast_version": voi.FORECAST_VERSION, "site": voi.SITE_FOLLOWUP, "learning_object_id": "lo_legacy",
        "decision": voi.STOP, "reason": voi.REASON_EVSI_BELOW, "recommended_ref": None, "chosen_ref": None,
        "candidate_count": 2, "context": {"session_id": "sess_legacy"}, "best": {"ref": "pi_x"},
        "candidates": [], "former_cap": {"would_bind": True}, "parameters": [], "calibration_label": "heuristic",
    }


def test_migration_188_backfills_a_legacy_follow_up_receipt_once(tmp_path):
    """F12: a follow-up value decision recorded on its ``decision_features``
    row before migration 188 is read by ``followup_receipt`` afterwards, with
    a stable identity and its source-attempt link; it is counted once, and a
    later decision on the same attempt follows it."""

    from learnloop.db.migrate import apply_migrations

    sqlite_path = _db_before_188(tmp_path)
    legacy = Repository.attach(sqlite_path)
    legacy.record_decision_features(
        decision_id="att_legacy", decision_type="followup", ability_vector={},
        context={"decision_outcome": "suppressed_voi_value_below_minutes_cost", "need_id": None,
                 "manual_trigger": None, "voi_stopping": _legacy_body("att_legacy")},
        algorithm_version="mvp-0.17",
    )
    legacy.record_decision_features(
        decision_id="att_manual", decision_type="followup", ability_vector={},
        context={"decision_outcome": "queued_diagnostic", "need_id": None, "manual_trigger": {"gate": "queued"},
                 "voi_stopping": {**_legacy_body("att_manual"), "decision": voi.CONTINUE, "served_ref": "pi_y",
                                  "recommended_ref": "pi_y"}},
        algorithm_version="mvp-0.17",
    )
    # mvp-0.16 follow-up features (no value decision) are not receipts of one.
    legacy.record_decision_features(
        decision_id="att_old", decision_type="followup", ability_vector={},
        context={"decision_outcome": "queued_diagnostic"}, algorithm_version="mvp-0.16",
    )
    apply_migrations(sqlite_path)
    repository = Repository.attach(sqlite_path)
    receipts = voi.followup_receipts(repository, "att_legacy")
    assert len(receipts) == 1
    (row,) = receipts
    assert row["id"].startswith("legacy_decision_features:") and row["decision_ordinal"] == 1
    assert row["source_attempt_id"] == "att_legacy" and row["learning_object_id"] == "lo_legacy"
    assert row["decision_outcome"] == "suppressed_voi_value_below_minutes_cost" and row["verdict"] == voi.STOP
    assert row["session_id"] == "sess_legacy" and row["manual_override"] is False and row["candidate_count"] == 2
    assert row["algorithm_version"] == "mvp-0.17"
    receipt = voi.followup_receipt(repository, "att_legacy")
    assert receipt["reason"] == voi.REASON_EVSI_BELOW and receipt["backfilled_from"] == "decision_features.context_json.voi_stopping"
    manual = voi.followup_receipts(repository, "att_manual")
    assert len(manual) == 1 and manual[0]["manual_override"] is True and manual[0]["served_ref"] == "pi_y"
    assert voi.followup_receipts(repository, "att_old") == []
    # No double counting: a later decision on the same attempt is the second.
    voi.record_followup_decision(
        repository, attempt_id="att_legacy", learning_object_id="lo_legacy", session_id="sess_2",
        outcome="queued_diagnostic", decision={"decision": voi.CONTINUE, "forecast_version": voi.FORECAST_VERSION},
        manual_override=True, need_id=None, algorithm_version="mvp-0.17",
    )
    after = voi.followup_receipts(repository, "att_legacy")
    assert [r["decision_ordinal"] for r in after] == [1, 2] and after[0]["id"] == row["id"]
    with repository.connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM followup_value_decisions").fetchone()[0]
    assert total == 3


# ── the switches: defaults, ranges, restore values ──────────────────────────


def test_the_study_switches_default_to_the_recommendation():
    from learnloop.config.schema import LearnLoopConfig, VoiStoppingConfig
    from learnloop.diagnosis.robust_composition import ROBUST_QUANTILE

    section = LearnLoopConfig().voi_stopping
    assert section.robust_gate_with_value is False
    assert section.lookahead_max_checks == 3
    assert section.robust_quantile == 0.25
    # The mvp-0.8 paths keep their own quantile.
    assert ROBUST_QUANTILE == 0.10
    for bad in ({"lookahead_max_checks": 0}, {"robust_quantile": 0.0}, {"robust_quantile": 0.6}):
        with pytest.raises(ValueError):
            VoiStoppingConfig(**bad)
    settings = voi.VoiSettings.from_config(LearnLoopConfig())
    assert (settings.robust_gate_with_value, settings.lookahead_max_checks, settings.robust_quantile) == (False, 3, 0.25)


def _restore_config(**overrides):
    from learnloop.config.schema import LearnLoopConfig

    config = LearnLoopConfig()
    config.voi_stopping.robust_gate_with_value = True
    config.voi_stopping.lookahead_max_checks = 1
    config.voi_stopping.robust_quantile = 0.10
    for name, value in overrides.items():
        setattr(config.voi_stopping, name, value)
    return config


_RESTORE_TOML = "[voi_stopping]\nrobust_gate_with_value = true\nlookahead_max_checks = 1\nrobust_quantile = 0.10\n"


def test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly(tmp_path, monkeypatch):
    """robust_gate_with_value = true, lookahead_max_checks = 1 and
    robust_quantile = 0.10 give the decisions the branch took before the
    study (pinned at 1b094b73): every pure scenario and the real probe vault's
    builds, episodes and completions, the robust gate's included."""

    from tests import voi_restore_scenarios as S

    golden = S.load_golden()
    assert S.pure_decisions(_restore_config()) == golden["pure"]
    assert S.integration_decisions(tmp_path, monkeypatch, toml=_RESTORE_TOML) == golden["integration"]


@pytest.mark.parametrize(
    "switch,default,method_prefix",
    [("lookahead_max_checks", 3, "robust_evsi_lookahead_"), ("robust_quantile", 0.25, None)],
)
def test_each_switch_alone_moves_only_its_own_decisions(switch, default, method_prefix):
    """With one switch at its default and the others at their restore values,
    the scenarios that change are exactly that switch's: the lookahead changes
    only decisions it takes (method robust_evsi_lookahead_<k>), never one a
    single check already decided; the quantile never adds a lookahead."""

    from tests import voi_restore_scenarios as S

    golden = S.load_golden()["pure"]
    moved = S.pure_decisions(_restore_config(**{switch: default}))
    changed = [name for name in golden if moved[name] != golden[name]]
    assert changed, "the switch must matter somewhere in the grid"
    for name in changed:
        methods = {candidate["method"] for candidate in moved[name]["candidates"]}
        if method_prefix is not None:
            assert golden[name]["decision"] == voi.STOP and moved[name]["decision"] == voi.CONTINUE
            assert any(method.startswith(method_prefix) for method in methods), name
        else:
            assert not any(method.startswith("robust_evsi_lookahead_") for method in methods)


# ── rank 1: the robust completion gate does not end an episode while value decides


def _gate_abstains(monkeypatch):
    from learnloop.diagnosis import probe_episodes as pe

    calls = []

    def gate(*_args, **_kwargs):
        calls.append(1)
        return "couldnt_reliably_distinguish"

    monkeypatch.setattr(pe, "_robust_completion_override", gate)
    return calls


def _gate_vault(tmp_path, version="mvp-0.17", toml=""):
    from tests.test_voi_stopping import _long_probe_vault

    return _long_probe_vault(tmp_path, version, toml)


def test_the_robust_gate_does_not_end_an_episode_while_value_decides(tmp_path, monkeypatch):
    from tests.test_voi_stopping import _answer_probe, _minutes

    vault, repository = _gate_vault(tmp_path)
    _gate_abstains(monkeypatch)
    _minutes(monkeypatch, 0.0001)  # the next observation pays
    episode = _answer_probe(vault, repository, score=0)
    assert episode.status == "in_progress" and episode.completion_reason is None


@pytest.mark.parametrize(
    "version,toml",
    [
        ("mvp-0.17", "[voi_stopping]\nrobust_gate_with_value = true\n"),  # the switch restores the gate
        ("mvp-0.17", "[voi_stopping]\nprobe_episodes = false\n"),  # value off: today's gate
        ("mvp-0.17", "[voi_stopping]\nenabled = false\n"),
        ("mvp-0.16", ""),
    ],
)
def test_the_gate_still_ends_an_episode_where_value_does_not_decide_or_the_switch_is_on(tmp_path, monkeypatch, version, toml):
    from tests.test_voi_stopping import _answer_probe, _minutes

    vault, repository = _gate_vault(tmp_path, version, toml)
    _gate_abstains(monkeypatch)
    _minutes(monkeypatch, 0.0001)
    episode = _answer_probe(vault, repository, score=0)
    assert episode.status == "complete" and episode.completion_reason == "couldnt_reliably_distinguish"


def test_a_calibration_session_keeps_the_robust_gate(tmp_path, monkeypatch):
    from learnloop.diagnosis import calibration_sessions
    from tests.test_voi_stopping import _answer_probe, _minutes

    vault, repository = _gate_vault(tmp_path)
    _gate_abstains(monkeypatch)
    _minutes(monkeypatch, 0.0001)
    monkeypatch.setattr(calibration_sessions, "calibration_cap_lifted", lambda _repository, _session_id: True)
    episode = _answer_probe(vault, repository, score=0)
    assert episode.completion_reason == "couldnt_reliably_distinguish"


def test_a_value_stop_records_the_gates_verdict_as_a_counterfactual(tmp_path, monkeypatch):
    from tests.test_voi_stopping import _answer_probe, _minutes

    vault, repository = _gate_vault(tmp_path)
    _gate_abstains(monkeypatch)
    _minutes(monkeypatch, 10_000.0)  # nothing pays
    episode = _answer_probe(vault, repository, score=0)
    assert episode.completion_reason == "value_of_information_stop"
    with repository.connection() as connection:
        detail = json.loads(
            connection.execute("SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (episode.id,)).fetchone()[0]
        )
    gate = detail["former_cap"]["robust_completion_gate"]
    assert gate == {
        "name": voi.ROBUST_GATE, "switch": "voi_stopping.robust_gate_with_value",
        "verdict": "couldnt_reliably_distinguish", "would_bind": True,
    }
    assert detail["former_cap"]["would_bind"] is True and detail["cap_comparison"] == "agree"


def test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt(tmp_path, monkeypatch):
    """The other side of rank 1, for calibration: where value outranks a
    gate abstention and the episode continues, the next committed
    observation's receipt says what the gate would have said ("later")."""

    from learnloop.diagnosis import probe_episodes as pe
    from learnloop.scheduling import scheduler as S
    from tests.test_voi_stopping import CLOCK, _answer_probe, _minutes

    vault, repository = _gate_vault(tmp_path)
    _gate_abstains(monkeypatch)
    monkeypatch.setattr(pe, "_robust_gate_verdict", lambda *_a, **_k: "couldnt_reliably_distinguish")
    _minutes(monkeypatch, 0.0001)
    episode = _answer_probe(vault, repository, score=0)
    assert episode.status == "in_progress"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    S.build_due_queue(vault, repository, clock=CLOCK, session=S.SchedulerSession(session_id=session_id), persist_explanations=True)
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None
    body = presentation.selection_components["voi_stopping"]
    assert body["decision"] == voi.CONTINUE
    assert body["former_cap"]["robust_completion_gate"]["verdict"] == "couldnt_reliably_distinguish"
    assert body["cap_comparison"] == "later"
    # Where the gate decides (the switch on), no counterfactual: it ran.
    restored, restored_repository = _gate_vault(tmp_path / "restored", toml="[voi_stopping]\nrobust_gate_with_value = true\n")
    first = restored_repository.open_probe_episode("lo_svd_definition")
    rows = restored_repository.probe_observations_for_episode(first.id)
    assert pe.robust_gate_counterfactual(restored, restored_repository, first, {"a": 0.5, "b": 0.5}) == (False, None)
    assert rows == []


def test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode(tmp_path, monkeypatch):
    """The pinned golden: with the gate restored the third episode ends
    couldnt_reliably_distinguish after two answers while value still pays;
    at the default it keeps asking (no monkeypatch: the real robust gate)."""

    from tests import voi_restore_scenarios as S

    golden = S.load_golden()["integration"]["episode_gate_m0.02"]
    assert golden[-1]["completion_reason"] == "couldnt_reliably_distinguish"
    toml = "[voi_stopping]\nlookahead_max_checks = 1\nrobust_quantile = 0.10\n"  # only the gate moves
    now = S.integration_decisions(tmp_path, monkeypatch, toml=toml)["episode_gate_m0.02"]
    assert now[: len(golden) - 1] == golden[:-1]
    assert now[len(golden) - 1]["status"] == "in_progress"


# ── rank 2: the best 2-3 checks valued jointly when no single check pays ───


_PAIR_PRIOR = {"unfamiliar": 0.75, "robust_initial_grasp": 0.25}


def _weak(ref, accuracy=0.7, minutes=0.1):
    row = {"unfamiliar": {"w": accuracy, "r": 1.0 - accuracy}, "robust_initial_grasp": {"w": 1.0 - accuracy, "r": accuracy}}
    return voi.Candidate(ref=ref, minutes=voi.MinutesEstimate(minutes, "authored_prior"), members=(row,))


def _decide(candidates, prior=_PAIR_PRIOR, config=None):
    from tests import voi_restore_scenarios as S

    return voi.value_candidates(
        S.context(config), voi.SITE_PROBE_EPISODE, candidates, prior=prior, learning_object_id="lo",
        former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=1),
    )


def test_robust_batch_evsi_is_the_robust_quantile_of_the_joint_evsi_per_member():
    from learnloop.scheduling import evsi as EV
    from tests import voi_restore_scenarios as S

    ctx = S.context()
    table = ctx.loss_table(ctx.label_actions(_PAIR_PRIOR))
    members = [
        {"unfamiliar": {"w": a, "r": 1 - a}, "robust_initial_grasp": {"w": 1 - a, "r": a}} for a in (0.7, 0.6, 0.8, 0.65)
    ]
    candidates = [
        EV.DiagnosticCandidate(ref=ref, members=tuple(members), prior=_PAIR_PRIOR, expected_minutes=0.1)
        for ref in ("a", "b", "c")
    ]
    batch = EV.robust_batch_evsi(candidates, table, k=2, quantile=0.25)
    joint = [
        EV.evsi_for_conditionals(
            {h: {(e1, e2): m[h][e1] * m[h][e2] for e1 in m[h] for e2 in m[h]} for h in m}, _PAIR_PRIOR, table
        ).evsi
        for m in members
    ]
    assert batch.refs == ("a", "b") and batch.member_count == 4
    assert batch.point == pytest.approx(joint[0])
    assert batch.lcb == pytest.approx(sorted(joint)[0])  # ceil(0.25 * 4) - 1 = 0
    assert batch.stop_threshold == pytest.approx(0.2)
    # Conditionally independent given H: a check that repeats a perfectly
    # revealing one adds nothing, so the pair is worth the revealing one alone.
    reveal = {"unfamiliar": {"w": 1.0}, "robust_initial_grasp": {"r": 1.0}}
    sure = EV.DiagnosticCandidate(ref="sure", members=(reveal,), prior=_PAIR_PRIOR, expected_minutes=0.1)
    weak = EV.DiagnosticCandidate(ref="weak", members=(members[0],), prior=_PAIR_PRIOR, expected_minutes=0.1)
    alone = EV.robust_evsi(sure.members, _PAIR_PRIOR, table).point
    assert EV.robust_batch_evsi([sure, weak], table, k=2).point == pytest.approx(alone)


def test_the_batch_value_equals_the_product_tables_evsi_on_the_real_credible_sets(tmp_path, monkeypatch):
    """The vectorized joint EVSI is evsi_for_conditionals on the product
    table, member by member, on the probe vault's 129-member ensembles (and
    the receipt's P(action change) is member 0's)."""

    from learnloop.diagnosis.probe_episodes import eligible_instruments, episode_posterior
    from learnloop.diagnosis.probe_robust import instrument_ensemble, load_pinned_channel
    from learnloop.diagnosis.robust_composition import robust_quantile
    from learnloop.scheduling import evsi as EV
    from tests.test_voi_stopping import LO, _long_probe_vault
    from tests.voi_restore_scenarios import seed_ids

    seed_ids(monkeypatch)
    vault, repository = _long_probe_vault(tmp_path, "mvp-0.17")
    episode = repository.open_probe_episode(LO)
    labels = list(episode_posterior(vault, repository, episode).posterior)
    posterior = {label: 0.85 if label == "unfamiliar" else 0.05 for label in labels}
    eligible = eligible_instruments(vault, repository, episode, posterior=posterior)[:3]
    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    ctx = voi.VoiContext(vault, repository)
    table = ctx.loss_table(ctx.label_actions(posterior))
    candidates = []
    for entry in eligible:
        ensemble, _ = instrument_ensemble(channel, entry.instrument, entry.slot_map, posterior, episode_id=episode.id)
        members = tuple(voi._keyed(member) for member in ensemble.members)
        candidates.append(EV.DiagnosticCandidate(ref=entry.item.id, members=members, prior=posterior, expected_minutes=0.5))
    for k in (2, 3):
        batch = EV.robust_batch_evsi(candidates, table, k=k, quantile=0.25)
        slow = [
            EV.evsi_for_conditionals(
                EV.joint_conditionals([c.members[index] for c in candidates[:k]], list(posterior)), posterior, table
            )
            for index in range(batch.member_count)
        ]
        assert batch.member_count == 129
        assert batch.point == pytest.approx(slow[0].evsi, abs=1e-12)
        assert batch.lcb == pytest.approx(robust_quantile([r.evsi for r in slow], 0.25), abs=1e-12)
        joint0 = EV.joint_conditionals([c.members[0] for c in candidates[:k]], list(posterior))
        moved = sum(
            sum(posterior[h] * joint0[h].get(e, 0.0) for h in posterior)
            for e, action in slow[0].argmin_by_emission.items() if action != slow[0].current_action
        )
        assert batch.p_action_change == pytest.approx(moved, abs=1e-12)
        assert batch.current_action == slow[0].current_action


def test_when_no_single_check_pays_a_paying_pair_continues_with_its_forecast():
    """Two weak checks: alone neither can change the repair (EVSI 0), together
    they can (0.33 minutes against 0.2): the episode continues."""

    decision = _decide([_weak("weak_a"), _weak("weak_b")])
    assert decision.decision == voi.CONTINUE
    chosen = decision.chosen
    assert chosen.method == "robust_evsi_lookahead_2" and chosen.reason == voi.REASON_EVSI_BATCH_CLEARS
    assert chosen.value_robust_minutes == pytest.approx(0.33) and chosen.cost_minutes == pytest.approx(0.2)
    assert chosen.detail["single_check"]["evsi_robust_minutes"] == pytest.approx(0.0)
    body = decision.as_dict()
    json.dumps(body)
    lookahead = body["lookahead"]
    assert lookahead["paid"] is True and lookahead["k"] == 2 and set(lookahead["batch"]) == {"weak_a", "weak_b"}
    assert lookahead["chosen_ref"] == chosen.ref and lookahead["evsi_robust_minutes"] == pytest.approx(0.33)
    assert 0.0 < lookahead["p_action_change"] <= 1.0
    assert [t["k"] for t in lookahead["tried"]] == [2]
    names = {p["name"]: p for p in body["parameters"]}
    assert names["lookahead_max_checks"]["value"] == 3 and names["lookahead_max_checks"]["provenance"] == "evsi_multisim"
    # Only the chosen check continues: the site serves one observation.
    assert [value.ref for value in decision.candidates if value.continues] == [chosen.ref]


def test_the_lookahead_tries_three_checks_when_two_do_not_pay():
    prior = {"unfamiliar": 0.8, "robust_initial_grasp": 0.2}
    candidates = [_weak(ref, accuracy=0.65, minutes=0.03) for ref in ("a", "b", "c")]
    decision = _decide(candidates, prior=prior)
    assert decision.decision == voi.CONTINUE and decision.chosen.method == "robust_evsi_lookahead_3"
    assert [t["k"] for t in decision.as_dict()["lookahead"]["tried"]] == [2, 3]
    capped = _decide(candidates, prior=prior, config=_restore_config(lookahead_max_checks=2, robust_quantile=0.25))
    assert capped.decision == voi.STOP and capped.as_dict()["lookahead"]["paid"] is False
    off = _decide(candidates, prior=prior, config=_restore_config(robust_quantile=0.25))
    assert off.decision == voi.STOP and "lookahead" not in off.as_dict()


def test_the_lookahead_does_not_run_when_a_single_check_pays_or_rank_abstains():
    strong = voi.Candidate(
        ref="strong", minutes=voi.MinutesEstimate(0.05, "authored_prior"),
        members=({"unfamiliar": {"w": 0.95, "r": 0.05}, "robust_initial_grasp": {"w": 0.05, "r": 0.95}},),
    )
    decision = _decide([strong, _weak("weak_a"), _weak("weak_b")], prior={"unfamiliar": 0.5, "robust_initial_grasp": 0.5})
    assert decision.decision == voi.CONTINUE and decision.chosen.method == voi.METHOD_ROBUST_EVSI
    assert "lookahead" not in decision.as_dict()
    # Nothing at stake (no routes): the EIG rule decides, never the lookahead.
    from tests import voi_restore_scenarios as S

    unrouted = voi.value_candidates(
        S.context(routes=()), voi.SITE_PROBE_EPISODE, [_weak("weak_a"), _weak("weak_b")], prior=_PAIR_PRIOR,
        learning_object_id="lo", former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=1),
    )
    assert "lookahead" not in unrouted.as_dict()
    assert all(not value.method.startswith("robust_evsi_lookahead_") for value in unrouted.candidates)


def test_the_batch_serves_the_sites_own_choice_when_it_is_in_the_batch():
    """The successor's serving rule among a paying batch: the site's own first
    choice (the first candidate in its order; on a predictive-objective
    episode the highest predictive information rate) when it is in the batch,
    else the batch's top-ranked check."""

    # The site lists the weakest check first; it is not among the top two.
    candidates = [_weak("site_pick", accuracy=0.62), _weak("weak_a", accuracy=0.7), _weak("weak_b", accuracy=0.71)]
    decision = _decide(candidates)
    lookahead = decision.as_dict()["lookahead"]
    assert lookahead["paid"] and "site_pick" not in lookahead["batch"]
    assert decision.chosen.ref == lookahead["batch"][0] and lookahead["chosen_rule"] == "batch_top_ranked"
    # Listed first and inside the batch: the site's own pick is served.
    reordered = [_weak("weak_a", accuracy=0.7), _weak("weak_b", accuracy=0.71)]
    inside = _decide(reordered)
    assert inside.chosen.ref == "weak_a" and inside.as_dict()["lookahead"]["chosen_rule"] == "site_choice_in_batch"


def test_the_lookahead_on_a_predictive_objective_episode_serves_the_incumbents_pick(tmp_path, monkeypatch):
    """Composes with the predictive objective: on the real probe vault (a
    pinned channel, 129 members) the candidates arrive in the episode's own
    order (the highest predictive information rate first); with a belief one
    answer cannot move off its repair and cheap checks, a pair pays and the
    episode's own pick is served when the pair holds it, else the pair's
    top-ranked check."""

    from learnloop.diagnosis.probe_episodes import eligible_instruments, episode_posterior
    from tests.test_voi_stopping import LO, _long_probe_vault
    from tests.voi_restore_scenarios import seed_ids

    seed_ids(monkeypatch)  # the credible sets are seeded by ids
    vault, repository = _long_probe_vault(tmp_path, "mvp-0.17")
    episode = repository.open_probe_episode(LO)
    labels = list(episode_posterior(vault, repository, episode).posterior)
    _minutes_patch(monkeypatch, 0.02)
    rules = set()
    for top in labels:
        posterior = {label: 0.9 if label == top else 0.1 / (len(labels) - 1) for label in labels}
        eligible = eligible_instruments(vault, repository, episode, posterior=posterior)
        assert eligible[0].selection_objective == "predictive_eig"
        decision = voi.probe_episode_decision(voi.VoiContext(vault, repository), episode, eligible, posterior, session_id=None)
        lookahead = decision.as_dict()["lookahead"]
        assert lookahead["paid"] and lookahead["member_count"] == 129 and lookahead["quantile"] == 0.25
        assert all(value.value_robust_minutes <= value.cost_minutes for value in decision.candidates if not value.continues)
        own = eligible[0].item.id
        expected = own if own in lookahead["batch"] else lookahead["batch"][0]
        assert decision.chosen.ref == expected and lookahead["site_choice_ref"] == own
        assert [value.ref for value in decision.candidates if value.continues] == [expected]
        rules.add(lookahead["chosen_rule"])
    assert rules == {"site_choice_in_batch", "batch_top_ranked"}


def _minutes_patch(monkeypatch, minutes):
    monkeypatch.setattr(
        voi.VoiContext, "item_minutes",
        lambda self, item, authored_minutes=None: voi.MinutesEstimate(float(minutes), "authored_prior"),
    )


def test_greedy_admission_never_runs_the_lookahead():
    """Teach-backs and project probes have no decision at stake: their greedy
    conditional admission (the F2 path) is the EIG rule, never a batch."""

    entries = [
        voi.InformationEntry(
            ref=f"pi_{index}", learning_object_id="lo_xy", eig_nats=1.0, minutes=voi.MinutesEstimate(1.0, "authored_prior"),
            terms=_predictive_terms(likelihood),
        )
        for index, likelihood in enumerate((_reveal_x(), _reveal_xy()))
    ]
    admission = voi.greedy_information_admission(_ctx(), voi.SITE_PROJECT_PROBE, entries, cap_value=4)
    assert all("lookahead" not in step.as_dict() for step in admission.steps)


# ── rank 3: the robust quantile of the successor's value gate ──────────────


def _ensemble(ref, accuracies, minutes):
    members = tuple(
        {"unfamiliar": {"w": a, "r": 1 - a}, "robust_initial_grasp": {"w": 1 - a, "r": a}} for a in accuracies
    )
    return voi.Candidate(ref=ref, minutes=voi.MinutesEstimate(minutes, "authored_prior"), members=members)


_SPREAD = (0.7, 0.58, 0.62, 0.65, 0.68, 0.72, 0.75, 0.78, 0.82)


def test_the_value_gate_reads_the_configured_robust_quantile():
    from learnloop.diagnosis.robust_composition import expected_information_gain, robust_quantile
    from tests import voi_restore_scenarios as S

    prior = {"unfamiliar": 0.5, "robust_initial_grasp": 0.5}
    candidate = _ensemble("q", _SPREAD, 1.5)
    eigs = [expected_information_gain(member, prior) for member in candidate.members]

    def decide(config):
        return voi.value_candidates(
            S.context(config, routes=()), voi.SITE_PROBE_EPISODE, [candidate], prior=prior, learning_object_id="lo",
            former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=1),
        )

    default, restored = decide(None), decide(_restore_config())
    assert default.best.eig_robust_nats == pytest.approx(robust_quantile(eigs, 0.25))
    assert restored.best.eig_robust_nats == pytest.approx(robust_quantile(eigs, 0.10))
    assert default.decision == voi.CONTINUE and restored.decision == voi.STOP  # 2.75 vs 0.78 minutes against 1.5
    names = {p["name"]: p for p in default.as_dict()["parameters"]}
    assert names["robust_quantile"] == {
        "name": "robust_quantile", "value": 0.25, "provenance": "evsi_multisim",
        "source": "voi_stopping.robust_quantile",
        "note": "docs/reviews/evsi-multisim.md §6.1 rank 3 (0.10 restores robust_composition.ROBUST_QUANTILE)",
    }
    restored_names = {p["name"]: p for p in restored.as_dict()["parameters"]}
    assert restored_names["robust_quantile"]["value"] == 0.10 and restored_names["robust_quantile"]["provenance"] == "heuristic"


def test_rank_feasible_values_the_episode_at_the_configured_quantile():
    """The robust EVSI rank_feasible decides with is the credible set's 25th
    percentile at the default (0.90 minutes here), its 10th at the restore
    value (0.48): with a 0.6-minute check the default measures, 0.10 stops."""

    from learnloop.diagnosis.robust_composition import robust_quantile
    from learnloop.scheduling import evsi as EV
    from tests import voi_restore_scenarios as S

    prior = {"unfamiliar": 0.5, "robust_initial_grasp": 0.5}
    candidate = _ensemble("q", _SPREAD, 0.6)
    ctx = S.context()
    table = ctx.loss_table(ctx.label_actions(prior))
    evsis = [EV.evsi_for_conditionals(member, prior, table).evsi for member in candidate.members]
    default = _decide([candidate], prior=prior)
    restored = _decide([candidate], prior=prior, config=_restore_config())
    assert default.best.method == restored.best.method == voi.METHOD_ROBUST_EVSI
    assert default.best.value_robust_minutes == pytest.approx(robust_quantile(evsis, 0.25)) == pytest.approx(0.9)
    assert restored.best.value_robust_minutes == pytest.approx(robust_quantile(evsis, 0.10)) == pytest.approx(0.48)
    assert default.decision == voi.CONTINUE and restored.decision == voi.STOP


# ── no count cap reappears ──────────────────────────────────────────────────


def test_no_count_cap_reappears(tmp_path, monkeypatch):
    """At the defaults one episode keeps asking past the former maximum (4),
    the session cap (4) and the lookahead's depth (3) while value pays; none
    of the study's switches is a count of observations."""

    from tests.test_voi_stopping import _answer_probe, _long_probe_vault, _minutes, _qualifying

    vault, repository = _long_probe_vault(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 0.0001)
    episode_id = repository.open_probe_episode(LO_ID).id
    for index in range(6):
        episode = _answer_probe(vault, repository, score=4 if index % 2 else 0)
        assert episode.id == episode_id and episode.status == "in_progress", episode.completion_reason
    assert _qualifying(repository, episode_id) == 6
    section = vault.config.voi_stopping
    assert section.lookahead_max_checks == 3 and _qualifying(repository, episode_id) > section.lookahead_max_checks
    for name, value in section.model_dump().items():
        assert "cap" not in name and "max_observations" not in name, name


LO_ID = "lo_svd_definition"
