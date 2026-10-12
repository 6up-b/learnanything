"""Router R1's one serving change: probe near-ties join the epsilon tie-break.

Before ``mvp-0.12`` the Today queue's seeded exploration never displaced a
PROBE-intent best and never explored to a PROBE-intent item, so probe
decisions always logged propensity 1 or 0 (spec_action_router_v1 §2). At
``mvp-0.12`` with ``router.probe_tie_admission`` they are ordinary near-ties
with a logged propensity. Below the successor, or with the switch off, serving
is exactly the predecessor's.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.scheduling import scheduler as scheduler_module
from learnloop.scheduling.scheduler import (
    ScheduledItem,
    SchedulerSession,
    _apply_seeded_exploration,
    _selection_propensities,
    build_due_queue,
    probe_ties_admitted,
)
from learnloop.scheduling.selection_rewards import SchedulerIntent
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    admit_probe_instrument_card,
    append_config_toml,
    create_basic_vault,
    create_placement_vault,
    set_algorithm_version,
)

PROBE = SchedulerIntent.PROBE.value


def _config(version: str, *, switch: bool = True, rate: float = 0.2, window: float = 1.0) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    config.router.probe_tie_admission = switch
    config.scheduler.selection_exploration_rate = rate
    config.scheduler.selection_exploration_reward_window = window
    return config


def _item(item_id: str, reward: float, *, intent: str = "practice") -> ScheduledItem:
    return ScheduledItem(
        practice_item_id=item_id, learning_object_id="lo", priority=reward,
        components={"selection_reward": reward}, readiness_factor=None,
        selected_mode="short_answer", plain_english=[], reward_debug={"intent": intent},
    )


def test_the_gate_needs_the_successor_and_the_switch():
    assert probe_ties_admitted(_config("mvp-0.12"))
    assert not probe_ties_admitted(_config("mvp-0.12", switch=False))
    for version in ("mvp-0.6", "mvp-0.9", "mvp-0.10", "mvp-0.11"):
        assert not probe_ties_admitted(_config(version))


@pytest.mark.parametrize("version,switch", [("mvp-0.11", True), ("mvp-0.12", False), ("mvp-0.10", True)])
def test_predecessor_and_kill_switch_keep_the_probe_exclusion_exactly(version, switch):
    session = SchedulerSession(session_id="s")
    config = _config(version, switch=switch)
    probe_best = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    assert _selection_propensities(probe_best, session, config) == {"p": 1.0, "a": 0.0}
    practice_best = [_item("a", 1.0), _item("p", 0.95, intent=PROBE), _item("b", 0.9)]
    assert _selection_propensities(practice_best, session, config) == {"a": 0.8, "p": 0.0, "b": 0.2}


def test_successor_admits_probe_near_ties_both_ways():
    session = SchedulerSession(session_id="s")
    config = _config("mvp-0.12")
    probe_best = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    assert _selection_propensities(probe_best, session, config) == {"p": 0.8, "a": pytest.approx(0.2)}
    practice_best = [_item("a", 1.0), _item("p", 0.95, intent=PROBE), _item("b", 0.9)]
    assert _selection_propensities(practice_best, session, config) == {
        "a": 0.8, "p": pytest.approx(0.1), "b": pytest.approx(0.1),
    }
    # The reward window still bounds the tie set.
    narrow = _config("mvp-0.12", window=0.01)
    assert _selection_propensities(probe_best, session, narrow) == {"p": 1.0, "a": 0.0}


def test_the_draw_can_displace_a_probe_only_at_the_successor(monkeypatch):
    from datetime import UTC, datetime

    queue = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    session = SchedulerSession(session_id="s")
    now = datetime(2026, 5, 19, 12, tzinfo=UTC)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))
    assert [i.practice_item_id for i in _apply_seeded_exploration(queue, session, _config("mvp-0.11"), now)] == ["p", "a"]
    explored = _apply_seeded_exploration(queue, session, _config("mvp-0.12"), now)
    assert [i.practice_item_id for i in explored] == ["a", "p"]
    assert explored[0].components["exploration_selected"] == 1.0


# ── end to end: a probe-led offer is logged with its true propensity ─────────


def _probe_vault(tmp_path, version: str, *, toml: str = ""):
    """Two never-seen items bound to an in-progress diagnostic episode: two
    PROBE-intent candidates and nothing due, so Today's head is whichever probe
    the queue puts first (the probe section is the only one)."""

    paths = create_basic_vault(tmp_path / version.replace(".", "_"))
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    add_followup_item(paths.root, "pi_svd_define_002")
    set_algorithm_version(paths, version)
    append_config_toml(
        paths.root,
        "[scheduler]\nselection_exploration_rate = 0.2\nselection_exploration_reward_window = 5.0\n" + toml,
    )
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip", "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip", "severity": 0.7, "is_misconception": True,
            "status": "active", "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    admit_probe_instrument_card(repository, items=("pi_svd_define_001", "pi_svd_define_002"))
    enter_episode(vault, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    return paths, load_vault(paths.root), repository


def _offer_row(paths, repository):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))
    with repository.connection() as connection:
        row = dict(connection.execute("SELECT * FROM router_decisions").fetchone())
    for column in ("candidates_json", "detail_json"):
        row[column] = json.loads(row[column])
    return row


def _probe_candidates(row) -> list[dict]:
    return [c for c in row["candidates_json"] if c["kind"] == "item" and c["planner"]["intent"] == PROBE]


def test_a_probe_near_tie_carries_a_true_propensity_only_at_the_successor(tmp_path):
    before_paths, _vault, before_repo = _probe_vault(tmp_path, "mvp-0.11")
    after_paths, _vault, after_repo = _probe_vault(tmp_path, "mvp-0.12")
    before = _offer_row(before_paths, before_repo)
    after = _offer_row(after_paths, after_repo)

    assert len(_probe_candidates(before)) == len(_probe_candidates(after)) == 2
    # mvp-0.11: the leading probe is never displaced, so the head is fixed and
    # its decision logs "deterministic".
    assert {c["exploration_propensity"] for c in _probe_candidates(before)} == {0.0, 1.0}
    assert before["detail_json"]["exploration"]["probe_ties_admitted"] is False
    assert len(before["detail_json"]["head_distribution"]) == 1
    assert (before["propensity_kind"], before["design"]) == ("deterministic", None)
    # mvp-0.12: the other probe joins the tie set; either may head the offer,
    # and the served one carries its true probability.
    assert after["detail_json"]["exploration"]["probe_ties_admitted"] is True
    assert sorted(c["exploration_propensity"] for c in _probe_candidates(after)) == [
        pytest.approx(0.2), pytest.approx(0.8),
    ]
    assert sorted(after["detail_json"]["head_distribution"].values()) == [pytest.approx(0.2), pytest.approx(0.8)]
    assert after["propensity_kind"] == "exact" and after["design"] == "epsilon_tiebreak"
    assert after["propensity"] == after["detail_json"]["head_distribution"][after["chosen_practice_item_id"]]


def test_kill_switch_serves_the_predecessors_probe_offer_exactly(tmp_path):
    base_paths, base_vault, base_repo = _probe_vault(tmp_path, "mvp-0.11")
    off_paths, off_vault, off_repo = _probe_vault(
        tmp_path, "mvp-0.12", toml="[router]\nprobe_tie_admission = false\n"
    )
    for session_id in ("s1", "s2", "s3", "s4", "s5", "s6"):
        base = build_due_queue(base_vault, base_repo, clock=FrozenClock(NOW),
                               session=SchedulerSession(session_id=session_id), persist_explanations=False)
        off = build_due_queue(off_vault, off_repo, clock=FrozenClock(NOW),
                              session=SchedulerSession(session_id=session_id), persist_explanations=False)
        assert [(i.practice_item_id, round(i.priority, 12), sorted(i.components.items())) for i in base] == [
            (i.practice_item_id, round(i.priority, 12), sorted(i.components.items())) for i in off
        ]


# ── a queue with no PROBE-intent candidate is unchanged by the successor ─────


def _serving_fingerprint(vault, repository, session_id: str):
    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW),
                            session=SchedulerSession(session_id=session_id), persist_explanations=False)
    return [
        (s.practice_item_id, s.learning_object_id, round(s.priority, 12),
         sorted((k, round(v, 12)) for k, v in s.components.items()))
        for s in queue
    ]


@pytest.mark.parametrize("toml", ["", "[router]\nprobe_tie_admission = false\n"])
def test_without_probe_candidates_the_successor_serves_exactly_as_mvp011(tmp_path, toml):
    base = create_placement_vault(tmp_path / "base", version="mvp-0.11")
    succ = create_placement_vault(tmp_path / "succ", version="mvp-0.12", placement_toml=toml or None)
    base_vault, succ_vault = load_vault(base.root), load_vault(succ.root)
    base_repo, succ_repo = Repository(base.sqlite_path), Repository(succ.sqlite_path)
    sync_vault_state(base_vault, base_repo, clock=FrozenClock(NOW))
    sync_vault_state(succ_vault, succ_repo, clock=FrozenClock(NOW))
    for session_id in ("a", "b", "c"):
        assert _serving_fingerprint(succ_vault, succ_repo, session_id) == _serving_fingerprint(
            base_vault, base_repo, session_id
        )
