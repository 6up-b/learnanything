"""What the screen reads and writes of a learner's marks (spec §7; spec_router_objective_v1 §4 row 6).

Marks follow §6.0: nothing while what the workflow holds is held, so a list never primes the probe's
answer. With no probe, or once it is answered, the list rides on the feedback bundle. ``Show anyway``
releases it and FG1 keeps the probe's answer labelled not independent.

The order is shuffled once, with a logged seed, over stable hypothesis identities (§11 of the router
objective spec), and each display of any list of an attempt's causes writes an exposure receipt from
the client's display event. A display event is what happened on screen, so it is recorded even while
feedback is held, and ``workflow.probe_answer_exposed`` reads it: causes on screen before a probe's
answer make that answer not independent, whichever surface showed them (R1 of the landing record).
A mark decides nothing: it is appended to a raw ledger and is not forwarded to
``record_unresolved_cause_self_report``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import logging
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import hypothesis_marks as store
from learnloop.followup_run.lanes import concrete_rivals
from learnloop.followup_run.serving import is_holding, source_of_probe_attempt
from learnloop.followup_serve import marks as M
from learnloop.followup_serve import workflow as wf
from learnloop.followup_serve.gates import hypothesis_marks_on

logger = logging.getLogger(__name__)

#: The marks panel on the attempt's own feedback, and on the probe's answer.
SURFACE_FEEDBACK = "marks_feedback"
SURFACE_PROBE_FEEDBACK = "marks_probe_feedback"
#: The inspector's read of an attempt or an error event (a click from the feedback screen, or a search),
#: which shows the raw causes. It has no client event: the sidecar's read is the display.
SURFACE_INSPECTOR = "inspector"
#: The other places the desktop lists an attempt's causes; each keeps its own order.
LIST_SURFACES: frozenset[str] = frozenset({"why", "unresolved_cause_card", "causal_feedback", SURFACE_INSPECTOR})
MARKS_SURFACES: frozenset[str] = frozenset({SURFACE_FEEDBACK, SURFACE_PROBE_FEEDBACK})
EXPOSURE_SURFACES: frozenset[str] = LIST_SURFACES | MARKS_SURFACES


class MarkRefused(ValueError):
    """A mark that names nothing on this attempt's list, or a list that is still held."""


@dataclass(frozen=True)
class MarkableList:
    """One attempt's list of possible causes, in the order it is displayed."""

    attempt_id: str
    learning_object_id: str
    factor_id: str | None
    diagnosis_id: str | None
    workflow: Mapping[str, Any] | None
    #: Each: ``hypothesis_version_id``, ``key`` (the stable identity) and ``statement``.
    hypotheses: tuple[Mapping[str, Any], ...]
    order_seed: str

    @property
    def order(self) -> list[str]:
        return [str(row["hypothesis_version_id"]) for row in self.hypotheses]


def _chosen_factor(repository: Repository, attempt_id: str, workflow: Mapping[str, Any] | None) -> tuple[str | None, tuple[str, ...]]:
    """The factor whose causes are listed, and those causes: the workflow's, whatever became of it
    (its probe tested those very versions), else the newest factor still open or resolved."""

    factors: list[Mapping[str, Any]] = []
    owned = (workflow or {}).get("factor_id")
    if owned:
        factor = repository.unresolved_cause_factor(str(owned))
        if factor is not None:
            factors.append(factor)
    for status in ("open", "resolved"):
        factors.extend(reversed(repository.unresolved_cause_factors_for_attempt(attempt_id, status=status)))
    for factor in factors:
        rivals = concrete_rivals(repository, dict(factor))
        if rivals:
            return str(factor["id"]), rivals
    return None, ()


def _claim_checked_ids(vault: Any, repository: Repository, attempt_id: str) -> tuple[str, ...]:
    """With no factor, exactly the causes the feedback's own overlay would show (it fails closed on
    a receipt that doesn't permit learner feedback)."""

    from learnloop.diagnosis.causal_attribution import claim_checked_feedback

    try:
        feedback = claim_checked_feedback(vault, repository, attempt_id)
    except ValueError:
        logger.warning("marks: the causes of attempt %s could not be read", attempt_id, exc_info=True)
        return ()
    return tuple(str(row["hypothesis_id"]) for row in (feedback or {}).get("causal_hypotheses") or [])


def claim_checked_ids_of(causal_feedback: Mapping[str, Any] | None) -> tuple[str, ...]:
    """The cause ids of a feedback bundle's ``causalFeedback`` (the camel-cased
    ``claim_checked_feedback`` the bundle already computed), as ``_claim_checked_ids`` reads them."""

    return tuple(str(row["hypothesisId"]) for row in (causal_feedback or {}).get("causalHypotheses") or [])


def markable_list(vault: Any, repository: Repository, attempt_id: str, *,
                  claim_checked_ids: Sequence[str] | None = None) -> MarkableList | None:
    """The attempt's list, or None with no concrete cause to mark. Holding is the caller's check.

    ``claim_checked_ids``: the attempt's claim-checked causes when the caller already has them (the
    desktop's feedback bundle computed them a moment ago, FG1d); None reads them here."""

    from learnloop.diagnosis.split.jobs import diagnosis_status

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    workflow = wf.attempt_workflow(repository, attempt_id)
    factor_id, ids = _chosen_factor(repository, attempt_id, workflow)
    if not ids:
        ids = (tuple(claim_checked_ids) if claim_checked_ids is not None
               else _claim_checked_ids(vault, repository, attempt_id))
    rows = [row for row in (repository.causal_hypothesis(value) for value in ids) if row is not None]
    if not rows:
        return None
    by_key = {str(row["episode_key"]): row for row in reversed(rows)}
    seed, order = M.display_order(attempt_id, list(by_key))
    return MarkableList(
        attempt_id=attempt_id,
        learning_object_id=str(attempt.get("learning_object_id") or ""),
        factor_id=factor_id,
        diagnosis_id=diagnosis_status(repository, attempt_id).get("diagnosis_id"),
        workflow=workflow,
        hypotheses=tuple({"hypothesis_version_id": str(by_key[key]["id"]), "key": key,
                          "statement": str(by_key[key]["statement"])} for key in order),
        order_seed=seed,
    )


def _state(repository: Repository, listed: MarkableList) -> dict[str, Any]:
    with repository.connection() as connection:
        return M.probe_state(connection, factor_id=listed.factor_id, workflow=listed.workflow)


def view(vault: Any, repository: Repository, attempt_id: str, *, surface: str = SURFACE_FEEDBACK,
         claim_checked_ids: Sequence[str] | None = None) -> dict[str, Any] | None:
    """What the panel shows for one attempt, or None: the switch is off, the list is held, or there
    is nothing to mark. Replaces the diagnosis card's tap only on the probe lane (§7)."""

    if not hypothesis_marks_on(vault.config):
        return None
    with repository.connection() as connection:
        if not store.present(connection):
            return None
    if is_holding(wf.attempt_workflow(repository, attempt_id)):
        return None
    listed = markable_list(vault, repository, attempt_id, claim_checked_ids=claim_checked_ids)
    if listed is None:
        return None
    with repository.connection() as connection:
        rows = store.marks_for_attempt(connection, attempt_id)
    latest = M.latest_marks(rows)
    none_row = latest.get(None)
    return {
        "attempt_id": attempt_id,
        "surface": surface,
        "order_seed": listed.order_seed,
        "probe_answered": _state(repository, listed)["answered"],
        "replaces_card_tap": (listed.workflow or {}).get("lane") == wf.LANE_PROBE,
        "hypotheses": [
            {"hypothesis_version_id": row["hypothesis_version_id"], "statement": row["statement"],
             "mark": (latest.get(str(row["key"])) or {}).get("mark")}
            for row in listed.hypotheses
        ],
        "none_of_these": none_row is not None,
        "none_of_these_text": (none_row or {}).get("free_text"),
    }


def bundle_view(vault: Any, repository: Repository, attempt_id: str, *,
                claim_checked_ids: Sequence[str] | None = None) -> dict[str, Any] | None:
    """§3 step 8: an answer to a generated probe shows the earlier miss's list, since that is what
    its answer was about. Any other attempt shows its own.

    ``claim_checked_ids`` are ``attempt_id``'s own claim-checked causes, from the bundle the panel
    rides on (FG1d: recomputing them cost every feedback open tens of milliseconds). A probe answer's
    list is the earlier miss's, whose causes that bundle doesn't carry, so they are read there."""

    if not hypothesis_marks_on(vault.config):
        return None
    source = source_of_probe_attempt(repository, attempt_id)
    if source is not None:
        return view(vault, repository, source, surface=SURFACE_PROBE_FEEDBACK)
    return view(vault, repository, attempt_id, claim_checked_ids=claim_checked_ids)


def record_exposure(
    vault: Any,
    repository: Repository,
    *,
    attempt_id: str,
    surface: str,
    hypothesis_version_ids: Sequence[str],
    shown_at: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    """One display, from the client's display event, in the order as displayed. The id, or None. A
    refused receipt rolls back alone with a warning: it never blocks a screen or an answer. A display
    event while feedback is held is recorded, not discarded: the screen says the causes were on it,
    and the probe's answer has to know. A time that can't be read is the server's own."""

    if not hypothesis_marks_on(vault.config):
        return None
    try:
        with repository.atomic(), repository.connection() as connection:
            if not store.present(connection):
                return None
            refusal = _exposure_refusal(repository, attempt_id, surface, hypothesis_version_ids)
            if refusal is not None:
                logger.warning("hypothesis exposure of attempt %s refused: %s", attempt_id, refusal)
                return None
            listed = markable_list(vault, repository, attempt_id)
            workflow = wf.attempt_workflow(repository, attempt_id)
            factor_id = listed.factor_id if listed is not None else None
            state = M.probe_state(connection, factor_id=factor_id, workflow=workflow)
            shuffled = surface in MARKS_SURFACES and listed is not None
            now = utc_now_iso(clock)
            return store.insert_exposure(connection, {
                "attempt_id": attempt_id,
                "factor_id": factor_id,
                "diagnosis_id": listed.diagnosis_id if listed is not None else None,
                "workflow_id": (workflow or {}).get("id"),
                "surface": surface,
                "hypothesis_version_ids_json": json.dumps(list(hypothesis_version_ids)),
                "order_seed": listed.order_seed if shuffled else None,
                "order_version": M.ORDER_VERSION if shuffled else None,
                "probe_answered": 1 if state["answered"] else 0,
                "probe_attempt_id": state["attempt_id"],
                "shown_at": shown_at if _readable_time(shown_at) else now,
                "created_at": now,
            })
    except Exception:  # noqa: BLE001 - a receipt never blocks a screen or an answer
        logger.warning("hypothesis exposure of attempt %s refused", attempt_id, exc_info=True)
        return None


def record_inspector_exposure(vault: Any, repository: Repository, attempt_id: str) -> str | None:
    """The inspector shows every cause of the attempt, held or not. Never in the way of the read."""

    try:
        ids = list(dict.fromkeys(str(row["id"]) for row in repository.causal_hypotheses_for_attempt(attempt_id)))
    except Exception:  # noqa: BLE001 - a receipt never blocks a screen
        logger.warning("the causes of attempt %s could not be read", attempt_id, exc_info=True)
        return None
    if not ids:
        return None
    return record_exposure(vault, repository, attempt_id=attempt_id, surface=SURFACE_INSPECTOR, hypothesis_version_ids=ids)


def _readable_time(value: str | None) -> bool:
    try:
        return bool(value) and parse_utc(value) is not None
    except ValueError:
        return False


def _exposure_refusal(repository: Repository, attempt_id: str, surface: str, ids: Sequence[str]) -> str | None:
    if surface not in EXPOSURE_SURFACES:
        return f"unknown surface {surface!r}"
    if not ids or len(set(ids)) != len(ids):
        return "no list, or a repeated cause"
    for value in ids:
        hypothesis = repository.causal_hypothesis(str(value))
        if hypothesis is None or str(hypothesis.get("attempt_id")) != attempt_id:
            return f"{value!r} is not a cause of this attempt"
    return None


def record_mark(
    vault: Any,
    repository: Repository,
    *,
    attempt_id: str,
    mark: str,
    hypothesis_version_id: str | None = None,
    free_text: str | None = None,
    surface: str = SURFACE_FEEDBACK,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Append one mark and return the panel's new read; None with the switch off.

    :class:`MarkRefused` names a mark that fits nothing on the list. Nothing else is written:
    no self-report, no belief, no factor move, no probability."""

    if not hypothesis_marks_on(vault.config):
        return None
    if mark not in M.MARKS:
        raise MarkRefused(f"unknown mark {mark!r}")
    if surface not in MARKS_SURFACES:
        raise MarkRefused(f"unknown surface {surface!r}")
    if is_holding(wf.attempt_workflow(repository, attempt_id)):
        raise MarkRefused("the possible causes are held until the question is answered")
    listed = markable_list(vault, repository, attempt_id)
    if listed is None:
        raise MarkRefused("this attempt has no possible causes to mark")
    text = (free_text or "").strip() or None
    if text is not None and mark != M.NONE_OF_THESE:
        raise MarkRefused("only None of these takes free text")
    position, key = None, None
    if hypothesis_version_id is not None:
        if mark == M.NONE_OF_THESE:
            raise MarkRefused("None of these names no cause")
        found = next((index for index, row in enumerate(listed.hypotheses)
                      if row["hypothesis_version_id"] == hypothesis_version_id), None)
        if found is None:
            raise MarkRefused("that cause is not on this attempt's list")
        position, key = found + 1, str(listed.hypotheses[found]["key"])
    elif mark in M.HYPOTHESIS_MARKS:
        raise MarkRefused(f"{mark} names a cause")
    with repository.atomic(), repository.connection() as connection:
        state = M.probe_state(connection, factor_id=listed.factor_id, workflow=listed.workflow)
        written = store.insert_mark(connection, {
            "attempt_id": attempt_id,
            "learning_object_id": listed.learning_object_id,
            "diagnosis_id": listed.diagnosis_id,
            "factor_id": listed.factor_id,
            "workflow_id": (listed.workflow or {}).get("id"),
            "hypothesis_version_id": hypothesis_version_id,
            "hypothesis_key": key,
            "mark": mark,
            "free_text": text,
            "display_position": position,
            "display_order_json": json.dumps(listed.order),
            "order_seed": listed.order_seed,
            "order_version": M.ORDER_VERSION,
            "surface": surface,
            "probe_answered": 1 if state["answered"] else 0,
            "probe_attempt_id": state["attempt_id"],
            "probe_outcome_json": json.dumps(state["outcome"], sort_keys=True) if state["outcome"] else None,
            "created_at": utc_now_iso(clock),
        })
    if written is None:
        raise MarkRefused("the mark could not be recorded")
    return view(vault, repository, attempt_id, surface=surface)


__all__ = [
    "EXPOSURE_SURFACES", "LIST_SURFACES", "MARKS_SURFACES", "MarkRefused", "MarkableList", "SURFACE_FEEDBACK",
    "SURFACE_INSPECTOR", "SURFACE_PROBE_FEEDBACK", "bundle_view", "markable_list", "record_exposure", "record_inspector_exposure", "record_mark", "view",
]
