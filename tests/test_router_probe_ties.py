"""Router R1's one serving change: probe near-ties join the epsilon tie-break.

Before ``mvp-0.15`` the Today queue's seeded exploration never displaced a
PROBE-intent best and never explored to a PROBE-intent item, so probe
decisions always logged propensity 1 or 0 (spec_action_router_v1 §2). At
``mvp-0.15`` with ``router.probe_tie_admission`` they are ordinary near-ties
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
    assert probe_ties_admitted(_config("mvp-0.15"))
    assert not probe_ties_admitted(_config("mvp-0.15", switch=False))
    for version in ("mvp-0.6", "mvp-0.9", "mvp-0.10", "mvp-0.11", "mvp-0.12", "mvp-0.13", "mvp-0.14"):
        assert not probe_ties_admitted(_config(version))


@pytest.mark.parametrize("version,switch", [("mvp-0.14", True), ("mvp-0.15", False), ("mvp-0.10", True)])
def test_predecessor_and_kill_switch_keep_the_probe_exclusion_exactly(version, switch):
    session = SchedulerSession(session_id="s")
    config = _config(version, switch=switch)
    probe_best = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    assert _selection_propensities(probe_best, session, config) == {"p": 1.0, "a": 0.0}
    practice_best = [_item("a", 1.0), _item("p", 0.95, intent=PROBE), _item("b", 0.9)]
    assert _selection_propensities(practice_best, session, config) == {"a": 0.8, "p": 0.0, "b": 0.2}


def test_successor_admits_probe_near_ties_both_ways():
    session = SchedulerSession(session_id="s")
    config = _config("mvp-0.15")
    probe_best = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    assert _selection_propensities(probe_best, session, config) == {"p": 0.8, "a": pytest.approx(0.2)}
    practice_best = [_item("a", 1.0), _item("p", 0.95, intent=PROBE), _item("b", 0.9)]
    assert _selection_propensities(practice_best, session, config) == {
        "a": 0.8, "p": pytest.approx(0.1), "b": pytest.approx(0.1),
    }
    # The reward window still bounds the tie set.
    narrow = _config("mvp-0.15", window=0.01)
    assert _selection_propensities(probe_best, session, narrow) == {"p": 1.0, "a": 0.0}


def test_the_draw_can_displace_a_probe_only_at_the_successor(monkeypatch):
    from datetime import UTC, datetime

    queue = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    session = SchedulerSession(session_id="s")
    now = datetime(2026, 5, 19, 12, tzinfo=UTC)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))
    assert [i.practice_item_id for i in _apply_seeded_exploration(queue, session, _config("mvp-0.14"), now)] == ["p", "a"]
    explored = _apply_seeded_exploration(queue, session, _config("mvp-0.15"), now)
    assert [i.practice_item_id for i in explored] == ["a", "p"]
    assert explored[0].components["exploration_selected"] == 1.0


# ── end to end: a probe-led offer is logged with its true propensity ─────────


def _probe_vault(tmp_path, version: str, *, toml: str = ""):
    """Two never-seen items bound to an in-progress diagnostic episode: two
    PROBE-intent candidates and nothing due, so Today's head is whichever probe
    the queue puts first (the probe section is the only one). The daily plan
    (mvp-0.14 and later) is switched off, so Today is the legacy queue whose
    head the offer serves."""

    paths = create_basic_vault(tmp_path / version.replace(".", "_"))
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    add_followup_item(paths.root, "pi_svd_define_002")
    set_algorithm_version(paths, version)
    append_config_toml(
        paths.root,
        "[scheduler]\nselection_exploration_rate = 0.2\nselection_exploration_reward_window = 5.0\n"
        "[plan]\nenabled = false\n" + toml,
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
    # A misconception re-probe, not an opening ("initial") episode: from
    # mvp-0.11 placement ignores unanswered opening episodes (owner decision
    # 2026-10-12), so only a re-probe's items are in-episode probes there.
    enter_episode(vault, repository, "lo_svd_definition", trigger="misconception", clock=FrozenClock(NOW))
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
    before_paths, _vault, before_repo = _probe_vault(tmp_path, "mvp-0.14")
    after_paths, _vault, after_repo = _probe_vault(tmp_path, "mvp-0.15")
    before = _offer_row(before_paths, before_repo)
    after = _offer_row(after_paths, after_repo)

    assert len(_probe_candidates(before)) == len(_probe_candidates(after)) == 2
    # mvp-0.14: the leading probe is never displaced, so the head is fixed and
    # its decision logs "deterministic".
    assert {c["exploration_propensity"] for c in _probe_candidates(before)} == {0.0, 1.0}
    assert before["detail_json"]["exploration"]["probe_ties_admitted"] is False
    assert len(before["detail_json"]["head_distribution"]) == 1
    assert (before["propensity_kind"], before["design"]) == ("deterministic", None)
    # mvp-0.15: the other probe joins the tie set; either may head the offer,
    # and the served one carries its true probability.
    assert after["detail_json"]["exploration"]["probe_ties_admitted"] is True
    assert sorted(c["exploration_propensity"] for c in _probe_candidates(after)) == [
        pytest.approx(0.2), pytest.approx(0.8),
    ]
    assert sorted(after["detail_json"]["head_distribution"].values()) == [pytest.approx(0.2), pytest.approx(0.8)]
    assert after["propensity_kind"] == "exact" and after["design"] == "scheduler_seeded_exploration"
    assert after["propensity"] == after["detail_json"]["head_distribution"][after["chosen_practice_item_id"]]


def test_kill_switch_serves_the_predecessors_probe_offer_exactly(tmp_path):
    base_paths, base_vault, base_repo = _probe_vault(tmp_path, "mvp-0.14")
    off_paths, off_vault, off_repo = _probe_vault(
        tmp_path, "mvp-0.15", toml="[router]\nprobe_tie_admission = false\n"
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
def test_without_probe_candidates_the_successor_serves_exactly_as_mvp014(tmp_path, toml):
    base = create_placement_vault(tmp_path / "base", version="mvp-0.14")
    succ = create_placement_vault(tmp_path / "succ", version="mvp-0.15", placement_toml=toml or None)
    base_vault, succ_vault = load_vault(base.root), load_vault(succ.root)
    base_repo, succ_repo = Repository(base.sqlite_path), Repository(succ.sqlite_path)
    sync_vault_state(base_vault, base_repo, clock=FrozenClock(NOW))
    sync_vault_state(succ_vault, succ_repo, clock=FrozenClock(NOW))
    for session_id in ("a", "b", "c"):
        assert _serving_fingerprint(succ_vault, succ_repo, session_id) == _serving_fingerprint(
            base_vault, base_repo, session_id
        )


# ── Codex review F4: an explored probe's presentation says it was drawn ──────


def test_an_explored_probe_presentation_is_marked_as_drawn_not_as_the_eig_choice(tmp_path, monkeypatch):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (1.0, 0.0))
    greedy = build_due_queue(vault, repository, clock=FrozenClock(NOW),
                             session=SchedulerSession(session_id=session_id), persist_explanations=False)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))

    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id=session_id))

    assert queue[0].practice_item_id != greedy[0].practice_item_id
    assert queue[0].components.get("exploration_selected") == 1.0
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and presentation.practice_item_id == queue[0].practice_item_id
    assert presentation.selection_components["scheduler_exploration"] == {
        "mechanism": "scheduler_seeded_exploration",
        "exploration_selected": True,
        "exploration_rate": pytest.approx(0.2),
        "exploration_propensity": pytest.approx(0.2),
        "greedy_item_id": greedy[0].practice_item_id,
    }


def test_a_greedy_probe_presentation_carries_no_exploration_mark(tmp_path, monkeypatch):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.14")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))
    build_due_queue(vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id=session_id))
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and "scheduler_exploration" not in presentation.selection_components


# ── owner decision D11 (2026-10-12): teach-back stays in the probe tie-break ──


_TEACH_BACK = {
    "id": "pi_svd_teach_back",
    "learning_object_id": "lo_svd_definition",
    "subjects": None,
    "practice_mode": "teach_back",
    "attempt_types_allowed": ["teach_back"],
    "evidence_facets": ["recall"],
    "evidence_weights": {"recall": 1.0},
    "criterion_facet_weights": {"core_definition": {"recall": 1.0}},
    "prompt": "Teach the singular value decomposition to a curious student.",
    "expected_answer": "U, Sigma and V transpose.",
    "grading_rubric": {
        "max_points": 1,
        "criteria": [{"id": "core_definition", "points": 1.0, "tier": "core", "description": "States U, Sigma, V."}],
        "fatal_errors": [],
    },
    "created_at": "2026-05-19T12:00:00Z",
    "updated_at": "2026-05-19T12:00:00Z",
}


@pytest.mark.parametrize(
    "version,toml,admitted",
    [
        ("mvp-0.15", "", True),
        ("mvp-0.15", "[router]\nprobe_tie_admission = false\n", False),
        ("mvp-0.14", "", False),
    ],
)
def test_teach_back_items_are_probe_near_ties_at_the_successor(tmp_path, version, toml, admitted):
    """D11: a teach-back dialogue is a high-value probe, so a teach-back item is
    a PROBE-intent near-tie the seeded exploration may draw (its cost belongs in
    the router's cost term, not in an exclusion). The predecessor and the kill
    switch keep the exclusion."""

    from learnloop.scheduling.scheduler import OfferTrace
    from learnloop.vault.writer import upsert_practice_item

    from tests.helpers import seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    upsert_practice_item(paths.root, _TEACH_BACK, clock=FrozenClock(NOW))
    set_algorithm_version(paths, version)
    append_config_toml(
        paths.root,
        "[scheduler]\nselection_exploration_rate = 0.2\nselection_exploration_reward_window = 5.0\n" + toml,
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    trace = OfferTrace()
    queue = build_due_queue(
        vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id="s"),
        persist_explanations=False, offer_trace=trace,
    )
    teach_back = next(item for item in trace.considered if item.practice_item_id == "pi_svd_teach_back")
    assert (teach_back.reward_debug or {}).get("intent") == PROBE
    assert trace.exploration["probe_ties_admitted"] is admitted
    assert (trace.base_propensity["pi_svd_teach_back"] > 0.0) is admitted
    assert queue
