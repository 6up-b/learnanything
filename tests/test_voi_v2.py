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
