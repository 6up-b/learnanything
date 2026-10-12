"""Daily-loop audit 2026-10-11: a dormant or resolved Learning Object is still served.

A learner who sets an LO's lifecycle ``status`` to ``dormant`` (parked) or
``resolved`` (done) has said "stop bringing this up". Before the fix the
scheduler's item loop (``scheduling/scheduler.py``) checked the item's own status
and derived state but never the owning LO's, and neither did the follow-up lanes,
the probe pool or the sidecar's by-id serving doors. Each test below fails on
the pre-fix code at the door it names.

This is a pure serving-eligibility rule: nothing is persisted, so reactivating
the LO makes its items servable again at once (asserted below).
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import (
    eligible_instruments,
    enter_episode,
    enter_stale_uncertainty_reprobes,
    episode_hypothesis_set,
    next_probe_item,
)
from learnloop.scheduling.scheduler import _insert_pending_followups, build_due_queue
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.errors import SidecarError

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)
INACTIVE = ("dormant", "resolved")


def _set_lo_status(root, status: str) -> None:
    lo_path = VaultPaths(root, load_vault(root).config).learning_object_path("linear-algebra", LO_ID)
    payload = read_yaml(lo_path)
    payload["status"] = status
    write_yaml(lo_path, payload)


def _queue_ids(root, repository) -> list[str]:
    return [entry.practice_item_id for entry in build_due_queue(load_vault(root), repository, clock=CLOCK)]


@pytest.mark.parametrize("status", INACTIVE)
def test_due_queue_stops_serving_items_of_an_inactive_lo(tmp_path, status):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    assert ITEM_ID in _queue_ids(paths.root, repository), "sanity: the due item is served"

    _set_lo_status(paths.root, status)
    assert ITEM_ID not in _queue_ids(paths.root, repository)

    # Reversible and stateless: reactivating the LO serves the item again.
    _set_lo_status(paths.root, "active")
    assert ITEM_ID in _queue_ids(paths.root, repository)


@pytest.mark.parametrize("status", INACTIVE)
def test_follow_up_lanes_do_not_resurrect_items_of_an_inactive_lo(tmp_path, status):
    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)
    repository.create_followup_task(
        kind="cold_retry",
        case_kind="misconception",
        case_ref="mc_cold",
        not_before=NOW_ISO,
        selected_item_id=ITEM_ID,
        expires_at="2026-06-19T12:00:00Z",
        context={"kind": "causal_cold_verification", "source_attempt_id": "att_src"},
        clock=CLOCK,
    )
    _set_lo_status(paths.root, status)
    vault = load_vault(paths.root)

    # The by-id follow-up door, which rebuilds a ScheduledItem from the vault
    # and pushes it above every ordinary pick.
    assert _insert_pending_followups(vault, [], [{"practice_item_id": ITEM_ID}], None) == []
    assert ITEM_ID not in _queue_ids(paths.root, repository)


def _probe_env(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID,))
    return paths, repository


@pytest.mark.parametrize("status", INACTIVE)
def test_probe_pool_is_empty_for_an_inactive_lo(tmp_path, status):
    paths, repository = _probe_env(tmp_path)
    vault = load_vault(paths.root)
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    before = eligible_instruments(vault, repository, episode, hypothesis_set=hypothesis_set)
    assert ITEM_ID in {entry.item.id for entry in before}, "sanity: a probe candidate"

    _set_lo_status(paths.root, status)
    vault = load_vault(paths.root)
    assert eligible_instruments(vault, repository, episode, hypothesis_set=hypothesis_set) == []
    assert next_probe_item(vault, repository, LO_ID) is None


def test_stale_uncertainty_reprobe_does_not_reopen_an_inactive_lo(tmp_path, monkeypatch):
    """The periodic re-probe producer must not open a fresh episode on a parked LO."""

    from types import SimpleNamespace

    from learnloop.diagnosis import probe_episodes as PE

    paths = create_basic_vault(tmp_path / "vault")
    repository = seed_due_item(paths)  # mastery logit_variance 1.0: above the re-probe bar
    _set_lo_status(paths.root, "dormant")
    vault = load_vault(paths.root)
    finished = SimpleNamespace(
        learning_object_id=LO_ID, status="complete", completed_at="2026-01-01T00:00:00Z"
    )
    monkeypatch.setattr(repository, "list_probe_episodes", lambda: [finished])
    opened: list[str] = []
    monkeypatch.setattr(PE, "enter_episode", lambda vault, repository, lo_id, **kw: opened.append(lo_id))

    enter_stale_uncertainty_reprobes(vault, repository, clock=CLOCK)
    assert opened == []

    _set_lo_status(paths.root, "active")  # sanity: the same LO re-probes once active
    enter_stale_uncertainty_reprobes(load_vault(paths.root), repository, clock=CLOCK)
    assert opened == [LO_ID]


def test_probe_dialogue_block_refuses_an_inactive_lo(tmp_path):
    from learnloop.diagnosis.probe_dialogue import DialogueBlockError, begin_dialogue_block

    paths, repository = _probe_env(tmp_path)
    episode = enter_episode(load_vault(paths.root), repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress", "sanity: an episode the dialogue could probe"

    _set_lo_status(paths.root, "dormant")
    with pytest.raises(DialogueBlockError, match="not active"):
        begin_dialogue_block(load_vault(paths.root), repository, LO_ID, clock=CLOCK)


def test_exam_start_does_not_administer_items_of_an_lo_put_away_after_reservation(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from learnloop.goals.exam_session import ExamSessionError, start_exam
    from learnloop.substrate.state_sync import sync_vault_state

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    goal = vault.goals[0]
    reserved = reserve_exam_pool(vault, repository, goal, clock=CLOCK).reserved_item_ids
    assert reserved, "sanity: the basic vault reserves a held-out pool"

    # Every reserved item belongs to the one LO, now put away: nothing to administer.
    _set_lo_status(paths.root, "resolved")
    with pytest.raises(ExamSessionError, match="dormant or resolved"):
        start_exam(load_vault(paths.root), repository, goal.id, clock=CLOCK)


# --- Sidecar by-id serving doors ------------------------------------------------


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    _set_lo_status(paths.root, "dormant")
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_sidecar_today_queue_omits_items_of_a_dormant_lo(ctx):
    queue = _call(ctx, "get_today_queue", {})
    served = [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
    assert ITEM_ID not in served


def test_sidecar_serve_doors_refuse_items_of_a_dormant_lo(ctx):
    session = _call(ctx, "start_session", {"availableMinutes": 20})
    with pytest.raises(SidecarError) as opened:
        _call(ctx, "open_queue_item", {"practiceItemId": ITEM_ID})
    assert opened.value.code == "learning_object_inactive"
    with pytest.raises(SidecarError) as served:
        _call(ctx, "get_practice_item", {"practiceItemId": ITEM_ID, "sessionId": session["sessionId"]})
    assert served.value.code == "learning_object_inactive"
    with pytest.raises(SidecarError) as probed:
        _call(ctx, "start_overconfidence_probe", {"learningObjectId": LO_ID})
    assert probed.value.code == "learning_object_inactive"
