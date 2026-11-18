"""Router R1's one serving change: probe near-ties join the epsilon tie-break.

Before ``mvp-0.15`` the Today queue's seeded exploration never displaced a
PROBE-intent best and never explored to a PROBE-intent item, so probe
decisions always logged propensity 1 or 0 (spec_action_router_v1 §2). From
``mvp-0.15`` they are ordinary near-ties with a logged propensity (the
switch went once every vault was past the tag).
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.scheduling import scheduler as scheduler_module
from learnloop.scheduling.scheduler import (
    ScheduledItem,
    SchedulerSession,
    _apply_seeded_exploration,
    _selection_propensities,
    build_due_queue,
    read_due_queue,
)
from learnloop.scheduling.selection_rewards import SchedulerIntent
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import (
    NOW,
    append_config_toml,
    create_basic_vault,
)
from tests.router_probe_ties_helpers import _probe_vault

PROBE = SchedulerIntent.PROBE.value


def _config(version: str, *, rate: float = 0.2, window: float = 1.0) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    config.scheduler.selection_exploration_rate = rate
    config.scheduler.selection_exploration_reward_window = window
    return config


def _item(item_id: str, reward: float, *, intent: str = "practice") -> ScheduledItem:
    return ScheduledItem(
        practice_item_id=item_id, learning_object_id="lo", priority=reward,
        components={"selection_reward": reward}, readiness_factor=None,
        selected_mode="short_answer", plain_english=[], reward_debug={"intent": intent},
    )


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


def test_the_draw_can_displace_a_probe(monkeypatch):
    from datetime import UTC, datetime

    queue = [_item("p", 1.0, intent=PROBE), _item("a", 0.95)]
    session = SchedulerSession(session_id="s")
    now = datetime(2026, 5, 19, 12, tzinfo=UTC)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (0.0, 0.0))
    explored = _apply_seeded_exploration(queue, session, _config("mvp-0.15"), now)
    assert [i.practice_item_id for i in explored] == ["a", "p"]
    assert explored[0].components["exploration_selected"] == 1.0


# ── end to end: a probe-led offer is logged with its true propensity ─────────


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


def test_a_probe_near_tie_carries_a_true_propensity(tmp_path):
    after_paths, _vault, after_repo = _probe_vault(tmp_path, "mvp-0.15")
    after = _offer_row(after_paths, after_repo)

    assert len(_probe_candidates(after)) == 2
    # The other probe joins the tie set; either may head the offer, and the
    # served one carries its true probability.
    assert after["detail_json"]["exploration"]["probe_ties_admitted"] is True
    assert sorted(c["exploration_propensity"] for c in _probe_candidates(after)) == [
        pytest.approx(0.2), pytest.approx(0.8),
    ]
    assert sorted(after["detail_json"]["head_distribution"].values()) == [pytest.approx(0.2), pytest.approx(0.8)]
    assert after["propensity_kind"] == "exact" and after["design"] == "scheduler_seeded_exploration"
    assert after["propensity"] == after["detail_json"]["head_distribution"][after["chosen_practice_item_id"]]


# ── Codex review F4: an explored probe's presentation says it was drawn ──────


def test_an_explored_probe_presentation_is_marked_as_drawn_not_as_the_eig_choice(tmp_path, monkeypatch):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (1.0, 0.0))
    greedy = read_due_queue(vault, repository, clock=FrozenClock(NOW),
                             session=SchedulerSession(session_id=session_id))
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
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.15")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    # A roll above the rate: the build stays greedy and the probe heads it as the EIG choice.
    monkeypatch.setattr(scheduler_module, "_exploration_draws", lambda *_a, **_k: (1.0, 0.0))
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


def test_teach_back_items_are_probe_near_ties(tmp_path):
    """D11: a teach-back dialogue is a high-value probe, so a teach-back item is
    a PROBE-intent near-tie the seeded exploration may draw (its cost belongs in
    the router's cost term, not in an exclusion)."""

    from learnloop.scheduling.scheduler import OfferTrace
    from learnloop.vault.writer import upsert_practice_item

    from tests.helpers import seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    upsert_practice_item(paths.root, _TEACH_BACK, clock=FrozenClock(NOW))
    append_config_toml(
        paths.root,
        "[scheduler]\nselection_exploration_rate = 0.2\nselection_exploration_reward_window = 5.0\n",
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    trace = OfferTrace()
    queue = read_due_queue(
        vault, repository, clock=FrozenClock(NOW), session=SchedulerSession(session_id="s"), offer_trace=trace,
    )
    teach_back = next(item for item in trace.considered if item.practice_item_id == "pi_svd_teach_back")
    assert (teach_back.reward_debug or {}).get("intent") == PROBE
    assert trace.exploration["probe_ties_admitted"] is True
    assert trace.base_propensity["pi_svd_teach_back"] > 0.0
    assert queue
