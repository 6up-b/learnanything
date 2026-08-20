"""KM5 §11.2 intent-first session composition — SHADOW ONLY.

The shadow intent planner selects an intent and ranks within it, logged alongside
live behavior, but the live queue composition is UNCHANGED. Promotion requires
held-out gains (not this milestone).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.scheduling.intent_planner import (
    SessionIntent,
    classify_intent,
    shadow_intent_plan,
)
from learnloop.diagnosis.probe_audit import shadow_intent_report
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import NOW, create_basic_vault


@dataclass
class _FakeItem:
    practice_item_id: str
    components: dict = field(default_factory=dict)


class _FakeVault:
    def __init__(self):
        self.practice_items = {}


def test_classify_intent_maps_signals():
    vault = _FakeVault()
    assert classify_intent(vault, _FakeItem("a", {"probe_eig": 0.5})) is SessionIntent.DIAGNOSE_UNCERTAINTY
    assert classify_intent(vault, _FakeItem("b", {"forgetting_risk": 0.9})) is SessionIntent.RESTORE_RETRIEVABILITY
    assert classify_intent(vault, _FakeItem("c", {})) is SessionIntent.BUILD_MISSING_KNOWLEDGE


def test_shadow_intent_plan_does_not_reorder_queue():
    vault = _FakeVault()
    queue = [
        _FakeItem("build_1", {}),
        _FakeItem("probe_1", {"probe_eig": 0.7}),
        _FakeItem("review_1", {"forgetting_risk": 0.8}),
    ]
    before = [i.practice_item_id for i in queue]
    plan = shadow_intent_plan(vault, queue)
    after = [i.practice_item_id for i in queue]
    assert before == after  # shadow never mutates the live queue
    # Highest-priority present intent is diagnose_uncertainty (probe_1).
    assert plan["selected_intent"] == "diagnose_uncertainty"
    assert plan["shadow_first_item"] == "probe_1"
    assert plan["live_first_item"] == "build_1"
    assert plan["agrees_with_live"] is False


def _drive_session(vault_root, *, shadow_enabled: bool, session_id: str):
    loaded = load_vault(vault_root)
    loaded.config.probe.shadow.enabled = shadow_enabled
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository, clock=FrozenClock(NOW))
    queue = build_due_queue(
        loaded,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id=session_id),
    )
    return loaded, repository, [i.practice_item_id for i in queue]


def test_intent_planner_is_shadow_only(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")

    _, repo_on, order_on = _drive_session(paths.root, shadow_enabled=True, session_id="s_on")
    _, repo_off, order_off = _drive_session(paths.root, shadow_enabled=False, session_id="s_off")

    # Live queue composition is identical with the shadow planner on or off.
    assert order_on == order_off

    # With shadow on, the plan was logged into that session's slate context...
    on_slate = repo_on.latest_scheduler_slate_by_session("s_on")
    assert (on_slate["session_context"] or {}).get("shadow_intent")
    # ...and read back by the shadow-intent report.
    report = shadow_intent_report(repo_on)
    assert report["slates_with_shadow_intent"] >= 1

    # With shadow off, that session's slate logs no intent plan (decision-inert).
    off_slate = repo_off.latest_scheduler_slate_by_session("s_off")
    assert "shadow_intent" not in (off_slate["session_context"] or {})
