"""Reader workbench RW6b part 1: cold follow-ups (spec_reader_workbench_v1 §9.3;
UX §4.8-§4.9, S15).

Four desktop RPCs over ``learnloop.instructional.reader_followups``:

* ``reader.followups`` -- "Coming up": the scheduled checks as a dated
  timeline (next three, then later), with purpose, why and undo, and the
  retirements as good news (a pure read);
* ``reader.followup_undo`` -- undo one check, with an optional reason (a
  ``learner_card`` verdict, calibration data);
* ``reader.followup_undo_all`` -- undo every pending check from one session;
* ``reader.followup_restore`` -- undo a retirement or an undo.

:func:`prepare_followups` is what every Today build does first: the daily
re-valuation (no model call) and, when an ended session waits or a kept
check's exposure needs the judge, the planning job on the context's
background registry (its relevance and exposure calls are paid and never on
the request path). Kill switch ``followups.enabled``: off, the
writes refuse, nothing is planned or re-valued, and "Coming up" still lists
the learner's existing checks so they can be undone.
Desktop only (pinned in tests/test_mobile_allowlist.py; spec D20).
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.instructional import reader_digest as RN
from learnloop.instructional import reader_followups as RF
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

READER_RW6B_RPCS = (
    "reader.followups",
    "reader.followup_undo",
    "reader.followup_undo_all",
    "reader.followup_restore",
)
JOB_NAME = "reader-followups"
_PLANNING = threading.Lock()


def _now() -> datetime:
    return datetime.now(UTC)


def _search(vault: Any, repository: Any) -> Any:
    from learnloop.instructional.wiring import find_practice_injections
    from learnloop_sidecar.handlers.practice_index import plan_minutes_estimator

    return RF.default_search(vault, repository, injections=find_practice_injections(
        vault, estimator=plan_minutes_estimator(vault, repository)))


def _valuer(vault: Any, repository: Any) -> Any:
    from learnloop_sidecar.handlers.practice_index import plan_minutes_estimator

    return RF.default_valuer(vault, repository, estimator=plan_minutes_estimator(vault, repository))


def prepare_followups(ctx: SidecarContext, vault: Any, repository: Any) -> None:
    """Before the day's plan: re-value the pending follow-ups (once a local
    day, no model call) and start planning any ended session in the
    background. RW6b part 2: the same job then writes the narrative of each
    ended session that has none yet (``digest.narrative_enabled``; off, this
    is part 1's work exactly). Never raises into the queue build."""

    live = RF.followups_enabled(vault)
    narrate = RN.narrative_enabled(vault)
    if not (live or narrate):
        return
    now = _now()
    waiting: list[Any] = []
    refresh = False
    if live:
        try:
            RF.revalue_pending(vault, repository, now=now, valuer=_valuer(vault, repository))
        except Exception:  # noqa: BLE001 - re-valuation never blocks the plan
            logging.getLogger(__name__).warning("reader follow-up re-valuation failed", exc_info=True)
        try:
            waiting = RF.sessions_to_plan(vault, repository, now=now)
            refresh = RF.exposure_refresh_waiting(repository)
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).warning("reader follow-up session scan failed", exc_info=True)
            return
    client = getattr(ctx, "reader_digest_client", None)
    narrations = False
    if narrate:
        try:
            # A session waiting for its narrative starts the job; sessions
            # planned in this job (or, with follow-ups not live, summarized
            # for their narrative: Codex review F2) are narrated right after
            # (only when a narration could run now: no idle job otherwise).
            narrations = bool(RN.digests_waiting(vault, repository, now=now, client=client)) or (
                bool(waiting or RN.sessions_to_summarize(vault, repository, now=now))
                and RN.admission_problem(vault, repository, client=client) is None)
        except Exception:  # noqa: BLE001 - a narrative never blocks the plan
            logging.getLogger(__name__).warning("reader narrative scan failed", exc_info=True)
            narrations = False
    # The lock only keeps this process from starting two jobs; two sidecars
    # are safe because each publication re-reads the digest in its own
    # transaction (Codex review F3), and a narrative is written only once.
    if not (waiting or refresh or narrations) or not _PLANNING.acquire(blocking=False):
        return

    def run() -> None:
        try:
            if refresh:
                # Codex review F5: the paid exposure refresh, in the background,
                # under both envelopes and the source switches.
                RF.refresh_exposure(vault, repository, now=_now())
            if waiting:
                RF.plan_ended_sessions(vault, repository, search=_search(vault, repository), now=_now())
        except Exception:  # noqa: BLE001 - a failed plan is retried at the next build
            logging.getLogger(__name__).warning("reader follow-up planning failed", exc_info=True)
        try:
            if narrations:
                if not live:
                    # Follow-ups off (or below their successor): the session's
                    # summary is persisted for its narrative alone (F2).
                    RN.summarize_ended_sessions(vault, repository, now=_now())
                RN.narrate_waiting(vault, repository, now=_now(), client=client)
        except Exception:  # noqa: BLE001 - a failed narrative is retried at the next build
            logging.getLogger(__name__).warning("reader narrative failed", exc_info=True)
        finally:
            _PLANNING.release()

    try:
        background_jobs(ctx).spawn(run, name=JOB_NAME)
    except Exception:  # noqa: BLE001
        _PLANNING.release()
        raise


def _require_on(vault: Any) -> None:
    if not RF.followups_enabled(vault):
        raise SidecarError("followups_disabled", "Follow-ups are switched off (followups.enabled = false).")


class ReaderFollowupsInput(ParamsModel):
    # A source's checks (the card); omitted, every source's (Wrap up at the destination).
    extraction_id: str | None = None
    # Retirements after this moment read as good news (the card's previous session end).
    retired_after: str | None = None


@method("reader.followups", ReaderFollowupsInput)
def reader_followups(ctx: SidecarContext, params: ReaderFollowupsInput) -> dict[str, Any]:
    """"Coming up": a dated timeline, never a count. Writes nothing."""

    vault, repository = ctx.require_vault()
    extraction_id = None
    if params.extraction_id:
        extraction_id = resolve_extraction_id(repository, params.extraction_id)
        if extraction_id is None:
            raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    return versioned(RF.coming_up(vault, repository, extraction_id=extraction_id, now=_now(),
                                  retired_after=params.retired_after))


class FollowupUndoInput(ParamsModel):
    commitment_id: str
    reason: str | None = None


@method("reader.followup_undo", FollowupUndoInput)
def reader_followup_undo(ctx: SidecarContext, params: FollowupUndoInput) -> dict[str, Any]:
    """Undo one scheduled check; ``reason`` is the optional "why?"."""

    _vault, repository = ctx.require_vault()
    try:
        return versioned(RF.undo_followup(repository, commitment_id=params.commitment_id, reason=params.reason))
    except RF.FollowupError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class FollowupUndoAllInput(ParamsModel):
    digest_id: str
    reason: str | None = None


@method("reader.followup_undo_all", FollowupUndoAllInput)
def reader_followup_undo_all(ctx: SidecarContext, params: FollowupUndoAllInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    try:
        return versioned(RF.undo_all(repository, digest_id=params.digest_id, reason=params.reason))
    except RF.FollowupError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class FollowupRestoreInput(ParamsModel):
    commitment_id: str


@method("reader.followup_restore", FollowupRestoreInput)
def reader_followup_restore(ctx: SidecarContext, params: FollowupRestoreInput) -> dict[str, Any]:
    """Undo a retirement (or an undo): the check is pending again."""

    vault, repository = ctx.require_vault()
    _require_on(vault)
    try:
        return versioned(RF.restore_followup(repository, commitment_id=params.commitment_id))
    except RF.FollowupError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


__all__ = ["JOB_NAME", "READER_RW6B_RPCS", "prepare_followups"]
