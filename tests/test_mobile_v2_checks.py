"""Mobile v2 §2.2, J6: the day's randomized check (RO5 §9 item 2) under a phone's step.

The check is drawn before any device is known. A phone's step that can't show it leaves it for the
desktop: its trace says ``item_device_deferred`` once, nothing re-draws it for the phone, its logged
probability is the draw's, and at the day's end an unanswered one resolves ``not_answered:device_deferred``.
The desktop's next Next serves it. Engine-level, with RO5's own fakes; no model is asked.
"""

from __future__ import annotations

from datetime import date, timedelta
import json

from learnloop.daily_plan import engine
from learnloop.daily_plan.engine import advance
from learnloop.router_objective import assignments as A
from learnloop.router_objective import checks as C
from learnloop.scheduling.device_eligibility import DESKTOP_ONLY_MODE, PlanStepFilter

from tests.daily_plan_fakes import record_attempt
from tests.router_mixture_helpers import run
from tests.test_ro5_checks import _env


class _HoldsTheChecks(PlanStepFilter):
    """A phone that can't show any administered check (as a check whose prompt embeds a page would be)."""

    def __init__(self, env) -> None:
        super().__init__(device_filter=None)
        self._env = env

    def holds(self, item):
        with self._env.repository.connection() as connection:
            checks = {str(entry.get("practice_item_id")) for entry in C.administered(connection).values()}
        return DESKTOP_ONLY_MODE if item.id in checks else None


def _draws(env):
    with env.repository.connection() as connection:
        return [(row["unit_id"], row["variant"], row["propensity"], row["draw"], row["detail"].get("item_id"))
                for row in A.rows(connection, A.CHECK)]


def _phone_run(env, *, steps: int = 30):
    served = []
    for _ in range(steps):
        record, step = advance(env, serve=True)
        if step is None or step["kind"] != "item":
            return served, step
        served.append(step["practice_item_id"])
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    return served, None


def _deferrals(env):
    with env.repository.connection() as connection:
        return [json.loads(row["detail_json"]) for row in connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE kind = ?", (engine.ITEM_DEVICE_DEFERRED,))]


def test_j6_the_check_waits_for_the_desktop_is_recorded_once_and_never_redrawn(tmp_path):
    desktop = _env(tmp_path / "desktop")
    run(desktop)
    phone = _env(tmp_path / "phone")
    phone.device = _HoldsTheChecks(phone)
    served, last = _phone_run(phone)
    with phone.repository.connection() as connection:
        administered = {str(entry["practice_item_id"]) for entry in C.administered(connection).values()}
    assert administered, "the day's check was administered"
    # The phone never served it, and nothing re-drew it for the phone. It comes first on every device, so
    # the phone crosses no boundary past it: no later draw (a stop) can leave it unanswered.
    assert not administered & set(served)
    assert last["kind"] == engine.DEVICE_HELD_STEP and last["first_held_item_id"] in administered
    assert served == []
    assert _draws(phone) == _draws(desktop)
    deferrals = _deferrals(phone)
    assert {entry["practice_item_id"] for entry in deferrals} == administered
    assert len(deferrals) == len(administered)  # once each, however many steps passed it
    assert all(entry["origin"] == C.ORIGIN and entry["surface"] == "phone_plan" for entry in deferrals)
    # The desktop's next Next serves it.
    phone.device = None
    record, step = advance(phone, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] in administered


def test_j6_an_unanswered_deferred_check_resolves_device_deferred_at_the_days_end(tmp_path):
    phone = _env(tmp_path)
    phone.device = _HoldsTheChecks(phone)
    _phone_run(phone)
    day = phone.today()
    tomorrow = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    with phone.repository.connection() as connection:
        today = C.resolve(connection, through=day)
        closed = C.resolve(connection, through=tomorrow)
        rate = C.completion(connection, through=tomorrow)
    assert {entry.status for entry in today} == {C.OPEN}
    assert {entry.status for entry in closed} == {C.DEVICE_DEFERRED}
    # Not completed, as not_answered is: the rate is unchanged, its label says why.
    assert rate["completed"] == 0 and rate["by_status"] == {C.DEVICE_DEFERRED: len(closed)}


def test_j6_the_learner_may_skip_it_from_the_phone_as_from_the_desktops_skip_link(tmp_path):
    phone = _env(tmp_path)
    phone.device = _HoldsTheChecks(phone)
    _served, last = _phone_run(phone)
    held = last["first_held_item_id"]
    _record, step = advance(phone, serve=True, skip_practice_item_id=held)
    assert step["kind"] in ("item", "done", engine.DEVICE_HELD_STEP)
    tomorrow = (date.fromisoformat(phone.today()) + timedelta(days=1)).isoformat()
    with phone.repository.connection() as connection:
        statuses = {entry.item_id: entry.status for entry in C.resolve(connection, through=tomorrow)}
    assert statuses[held] == C.SKIPPED


def test_j6_the_engine_and_the_resolver_name_one_event():
    assert engine.ITEM_DEVICE_DEFERRED == C.DEVICE_DEFERRED_EVENT


def test_j6_a_check_the_phone_can_show_is_served_on_the_phone_as_an_ordinary_item(tmp_path):
    desktop = _env(tmp_path / "desktop")
    run(desktop)
    phone = _env(tmp_path / "phone")
    phone.device = PlanStepFilter(device_filter=None)
    served, _last = _phone_run(phone)
    with phone.repository.connection() as connection:
        administered = {str(entry["practice_item_id"]) for entry in C.administered(connection).values()}
    assert administered <= set(served)
    assert _deferrals(phone) == []
    assert _draws(phone) == _draws(desktop)
