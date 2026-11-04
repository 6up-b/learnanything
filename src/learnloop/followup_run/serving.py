"""What the learner's screen and Next read from a workflow (spec §6).

§6.0's hold, §6.1's wait, §6.2's failure line, §6.3's visible wait and §6.4's decision
line are all one read here, so what is on screen is what the workflow says.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.followup_run import decision_view as dv
from learnloop.followup_run import lanes
from learnloop.followup_serve import identity, workflow as wf

PREPARING = "Preparing a question on this…"
FAILED_LINE = "Couldn't prepare a question on this. It's noted for later."
NO_PLAN_LINE = "This question comes first."
READY_LINE = "Your next question is ready."

#: Exactly what §6.0 holds in the feedback bundle: the worked answer, the diagnosis
#: summary and possible causes, repairs, the prerequisite explanation and escalation.
#: The verdict and the criteria stay.
HELD_KEYS: Mapping[str, Any] = {
    "answeredExpectedAnswer": None,
    "feedbackMd": None,
    "repairSuggestions": [],
    "errorAttributions": [],
    "matchedMisconception": None,
    "causalFeedback": None,
    "unresolvedCauses": [],
    "commonRepair": None,
    "guidedRedoAvailable": False,
    "interventionNeed": None,
    "fatalErrors": [],
}


@dataclass(frozen=True)
class NextAction:
    action: str
    line: str | None = None
    practice_item_id: str | None = None
    presentation_id: str | None = None


def is_holding(row: Mapping[str, Any] | None) -> bool:
    return bool(row and row.get("feedback_held") and not row.get("feedback_released_at"))


def held_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """The bundle with what is held taken out, on the server, so nothing can show it."""

    return {**bundle, **{key: value for key, value in HELD_KEYS.items() if key in bundle}}


def _line(vault: Any, row: Mapping[str, Any]) -> str | None:
    state = row["state"]
    if state == wf.PENDING:
        return PREPARING
    if state == wf.WAITING:
        learning_object = vault.learning_objects.get(str(row["learning_object_id"]))
        topic = learning_object.title if learning_object is not None else "this"
        return f"A question on {topic} is coming in your next block."
    if state == wf.FAILED:
        return FAILED_LINE
    if state == wf.READY:
        return NO_PLAN_LINE if not row.get("decision_id") else READY_LINE
    return None


def view(vault: Any, repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    """The screen's read of the attempt's workflow, or None (the bundle stays as it was)."""

    row = wf.attempt_workflow(repository, attempt_id)
    if row is None:
        return None
    holding = is_holding(row)
    out: dict[str, Any] = {
        "workflow_id": row["id"],
        "state": row["state"],
        "lane": row.get("lane"),
        "held": holding,
        "line": _line(vault, row),
        "chosen_ref": row.get("chosen_ref"),
        # Next never strands the learner: both exits stay open while anything is held.
        "can_show_anyway": holding,
        "can_continue_without": row["state"] in {wf.PENDING, wf.READY} and not _served(repository, row),
        "shown_anyway": bool(row.get("shown_anyway_at")),
    }
    if dv.show_router_decisions(vault):
        out["router_decision"] = dv.decision_view(repository, row.get("decision_id"))
    return out


def _served(repository: Repository, row: Mapping[str, Any]) -> bool:
    item_id = row.get("practice_item_id")
    return bool(item_id) and str(item_id) in identity.closed_probe_ids(repository)


def source_of_probe_attempt(repository: Repository, attempt_id: str) -> str | None:
    """The miss whose held feedback this probe answer released, or None."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    row = wf.workflow_of_item(repository, str(attempt.get("practice_item_id") or ""))
    if row is None or not row.get("feedback_released_at"):
        return None
    return str(row["source_attempt_id"])


def router_wait() -> str:
    from learnloop.followup_run.router import WAIT

    return WAIT


def plan_will_place(vault: Any, repository: Repository, attempt_id: str, *, clock: Clock | None = None) -> bool:
    """R12, R13: a plan serves a workflow's probe only if the miss came from the plan, which the
    attempt's own validated ``plan_presentation_id`` records, and placement itself says this probe
    has a live placement or gets one at the next step. Otherwise Next opens it: nothing else would,
    and the answer would stay held."""

    from learnloop.daily_plan.engine import FOLLOWUP_GONE, PlanEnv, followup_placement, latest_today, plan_active

    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    if not attempt.get("plan_presentation_id") or not plan_active(vault):
        return False
    row = wf.attempt_workflow(repository, attempt_id) or {}
    record = latest_today(PlanEnv(vault=vault, repository=repository, clock=clock))
    return followup_placement(record, str(row.get("practice_item_id") or "")) != FOLLOWUP_GONE


def next_action(
    vault: Any, repository: Repository, attempt_id: str, *, plan_serves: bool, clock: Clock | None = None
) -> NextAction:
    """§6.1: what Next does. It waits only while a question may still come, and it says so."""

    row = wf.attempt_workflow(repository, attempt_id)
    if row is None or row["state"] not in {wf.PENDING, wf.READY}:
        return NextAction("continue")
    if row["state"] == wf.READY and not _served(repository, row) and not wf.waiting_still_valid(repository, row):
        # §4.2: retired while unused, if its hypotheses closed first.
        wf.retire_waiting(repository, row, reason="hypotheses_closed", clock=clock)
        return NextAction("continue")
    if row["state"] == wf.READY and _administration_over(repository, row):
        # Served, and its presentation has since ended: the door would refuse it, so Next doesn't offer it.
        wf.retire_waiting(repository, row, reason="presentation_ended", clock=clock)
        return NextAction("continue")
    if row["state"] == wf.PENDING and row.get("chosen_ref") == router_wait() and not is_holding(row):
        # §6.0: the router let it wait, and what was held is released, so nothing here waits for the
        # question being written. Whatever its job comes to, Next goes on.
        return NextAction("continue")
    if row["state"] == wf.PENDING:
        from learnloop.followup_run.jobs import recover_workflow

        # §6.1: Next never strands the learner on a handoff a crash lost.
        recover_workflow(vault, repository, row, clock=clock)
        row = wf.get(repository, str(row["id"])) or row
        if row["state"] != wf.PENDING:
            return next_action(vault, repository, attempt_id, plan_serves=plan_serves, clock=clock)
        now = utc_now_iso(clock)
        if not row.get("next_requested_at"):
            wf.set_fields(repository, str(row["id"]), next_requested_at=now, clock=clock)
            row = {**row, "next_requested_at": now}
        if _diagnosis_timed_out(vault, repository, row, now):
            # §6.2: the timeout reuses diagnosis.next_item_wait_seconds; one fallback.
            lanes.settle_practice_lane(vault, repository, row, reason="diagnosis_timeout",
                                       release=wf.RELEASE_FALLBACK, clock=clock)
            return NextAction("continue")
        return NextAction("wait", line=PREPARING)
    # Ready: the plan's own next step places and serves it; with no plan it comes first.
    if plan_serves and row.get("session_id"):
        return NextAction("continue")
    return NextAction("open", practice_item_id=str(row["practice_item_id"]),
                      presentation_id=str(row.get("presentation_id") or "") or None)


def _administration_over(repository: Repository, row: Mapping[str, Any]) -> bool:
    presentation = repository.probe_presentation(str(row.get("presentation_id") or ""))
    return _served(repository, row) and (presentation is None or presentation.status == "ended")


def _diagnosis_timed_out(vault: Any, repository: Repository, row: Mapping[str, Any], now: str) -> bool:
    """Only while the diagnosis itself is what's outstanding; generation has *Continue without it*."""

    from learnloop.diagnosis.split.jobs import PENDING, diagnosis_status

    attempt_id = str(row["source_attempt_id"])
    if repository.latest_blind_grade_record(attempt_id) is None:
        return False
    if diagnosis_status(repository, attempt_id)["status"] != PENDING:
        return False
    started = parse_utc(str(row.get("next_requested_at") or now))
    current = parse_utc(now)
    wait = float(getattr(getattr(vault.config, "diagnosis", None), "next_item_wait_seconds", 10.0))
    return current is not None and started is not None and current - started >= timedelta(seconds=wait)


def continue_without(repository: Repository, attempt_id: str, *, clock: Clock | None = None) -> bool:
    """§6.1: logged, it retires the probe, and §5.1 records today's *Teach me now* authorisation."""

    from learnloop.diagnosis.causal_orchestrator import record_learner_preference
    from learnloop.followup_run import router

    row = wf.attempt_workflow(repository, attempt_id)
    if row is None or row["state"] not in {wf.PENDING, wf.READY}:
        return False
    with repository.atomic():
        if not wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="continue_without_it",
                         release=wf.RELEASE_CONTINUE_WITHOUT, from_states=(wf.PENDING, wf.READY), clock=clock):
            return False
        if row.get("factor_id"):
            record_learner_preference(
                repository, preference="teach_now", factor_id=str(row["factor_id"]), session_id=row.get("session_id"),
                source="continue_without_it", detail={"workflow_id": row["id"]}, clock=clock,
            )
        if row.get("decision_id"):
            router.append_outcome(repository, str(row["decision_id"]), str(row["id"]), outcome="skipped", clock=clock)
    return True


def show_anyway(repository: Repository, attempt_id: str, *, clock: Clock | None = None) -> bool:
    """§6.0: releases what's held and marks the probe's answer not independent. No cancel."""

    row = wf.attempt_workflow(repository, attempt_id)
    if row is None or not is_holding(row):
        return False
    now = utc_now_iso(clock)
    wf.set_fields(repository, str(row["id"]), shown_anyway_at=now, feedback_released_at=now,
                  release_reason=wf.RELEASE_SHOW_ANYWAY, clock=clock)
    return True


def bind_plan_step(repository: Repository, step: Mapping[str, Any] | None, *, clock: Clock | None = None) -> None:
    """The plan served it: the decision's second presentation joins its binding."""

    from learnloop.followup_run import router

    if not step or step.get("kind") != "item" or not step.get("presentation_id"):
        return
    row = wf.workflow_of_item(repository, str(step.get("practice_item_id") or ""))
    if row is not None:
        router.bind_plan_presentation(repository, row, plan_presentation_id=str(step["presentation_id"]), clock=clock)


def abandon(repository: Repository, practice_item_id: str, *, clock: Clock | None = None) -> bool:
    """A generated probe skipped: abandonment closes it, for every generated probe, with or
    without a workflow, and what its workflow held is released."""

    from learnloop.followup_run import router

    row = wf.workflow_of_item(repository, practice_item_id)
    if row is None or row["state"] not in wf.OPEN_STATES:
        if not identity.is_generated_probe(repository, practice_item_id):
            return False
        return identity.withdraw(repository, practice_item_id, reason="abandoned", clock=clock)
    with repository.atomic():
        if not wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="abandoned",
                         release=wf.RELEASE_CONTINUE_WITHOUT, clock=clock):
            return False
        if row.get("decision_id"):
            router.append_outcome(repository, str(row["decision_id"]), str(row["id"]), outcome="abandoned", clock=clock)
    return True


__all__ = [
    "FAILED_LINE", "HELD_KEYS", "NO_PLAN_LINE", "NextAction", "PREPARING", "abandon", "bind_plan_step",
    "continue_without", "held_bundle", "is_holding", "next_action", "show_anyway", "source_of_probe_attempt", "view",
]
