"""A scheduled certification question stays fresh until its follow-up administers it."""

from dataclasses import asdict
from datetime import timedelta
import hashlib
import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import PlanEnv
from learnloop.goals.certification_cold_probe import schedule_certification_cold_probes
from learnloop.scheduling.scheduler import build_due_queue, exclusion_now, read_due_queue
from learnloop.scheduling.serving_exclusions import routine_serving_exclusions
from tests.certification_cold_probe_helpers import HELD_OUT_ITEM, _attempt, _certify, _tasks
from tests.helpers import NOW


@pytest.fixture
def reserved(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.clock.SystemClock.now", lambda self: NOW)
    paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    task = _tasks(repository)[0]
    assert task["selected_item_id"] == HELD_OUT_ITEM
    assert task["status"] == "pending"
    return paths, vault, repository, task


def test_read_queue_withholds_the_reserved_question_and_names_why(reserved):
    _paths, vault, repository, _task = reserved
    assert HELD_OUT_ITEM not in {item.practice_item_id for item in read_due_queue(vault, repository)}
    assert exclusion_now(vault, repository, HELD_OUT_ITEM) == "cold_check_reserved"
    assert HELD_OUT_ITEM in routine_serving_exclusions(vault, repository).item_ids


def test_plan_candidates_do_not_include_the_reserved_question(reserved):
    _paths, vault, repository, _task = reserved
    env = PlanEnv(vault=vault, repository=repository, clock=FrozenClock(NOW))
    assert HELD_OUT_ITEM not in {item.practice_item_id for item in env.build_eligible(25)}


def test_a_full_list_pick_cannot_choose_the_reserved_question_because_it_is_not_listed(reserved):
    import learnloop_sidecar.handlers  # noqa: F401 -- register RPC handlers
    from learnloop_sidecar.context import SidecarContext
    from tests.mobile_v2_plan_helpers import _call

    paths, _vault, _repository, _task = reserved
    ctx = SidecarContext()
    try:
        ctx.load(paths.root, maintenance=False)
        reply = _call(ctx, "get_today_queue", {})
        ids = {item["practiceItemId"] for section in reply["sections"] for item in section["items"]}
        assert HELD_OUT_ITEM not in ids
    finally:
        ctx.close()


def test_the_phone_list_withholds_the_reserved_question(reserved):
    import learnloop_sidecar.handlers  # noqa: F401 -- register RPC handlers
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.request_origin import RequestOrigin
    from tests.mobile_v2_plan_helpers import _call

    paths, _vault, _repository, _task = reserved
    ctx = SidecarContext()
    try:
        ctx.load(paths.root, maintenance=False)
        with ctx.acting_as(RequestOrigin(device_id="reserved-question-phone")):
            reply = _call(ctx, "get_today_queue", {})
        ids = {item["practiceItemId"] for section in reply["sections"] for item in section["items"]}
        assert HELD_OUT_ITEM not in ids
    finally:
        ctx.close()


def test_the_reserved_question_is_administered_by_its_check_on_its_day(reserved):
    _paths, vault, repository, task = reserved
    assert HELD_OUT_ITEM not in {item.practice_item_id for item in read_due_queue(vault, repository)}
    due = FrozenClock(NOW + timedelta(days=14))
    queue = build_due_queue(vault, repository, clock=due)
    selected = [item for item in queue if item.practice_item_id == HELD_OUT_ITEM]
    assert len(selected) == 1
    assert selected[0].followup_kind == "certification_cold_probe"
    result = _attempt(vault, repository, HELD_OUT_ITEM, clock=due)
    outcome = repository.certification_cold_probe_outcomes()[0]
    assert outcome["followup_task_id"] == task["id"]
    assert outcome["probe_attempt_id"] == result.attempt_id
    assert repository.followup_task(task["id"])["status"] == "consumed"


def test_no_reservation_keeps_the_existing_certified_vault_queue_byte_identical(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.clock.SystemClock.now", lambda self: NOW)
    _paths, vault, repository, _certificate = _certify(tmp_path)
    assert not _tasks(repository)
    rows = [asdict(item) for item in read_due_queue(vault, repository, clock=FrozenClock(NOW))]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == "e25f79090b29aa2d0feeefe18eef007d09db6b4cf96e9ed085fa22bb9f395c30"


@pytest.mark.parametrize("served", [False, True])
def test_an_open_reservation_releases_when_the_task_expires(reserved, served):
    _paths, vault, repository, task = reserved
    if served:
        with repository.connection() as connection:
            connection.execute("UPDATE followup_tasks SET status = 'served' WHERE id = ?", (task["id"],))
            connection.commit()
    assert HELD_OUT_ITEM not in {item.practice_item_id for item in read_due_queue(vault, repository)}
    repository.expire_followup_task(task["id"])
    assert HELD_OUT_ITEM in {item.practice_item_id for item in read_due_queue(vault, repository)}
