from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from learnloop.db.stores.session_ownership import SessionOwnershipError
from learnloop.scheduling.session_minutes import (
    MINUTE_PRESETS,
    minute_choices,
    remembered_session_minutes,
)
from learnloop_sidecar.context import SidecarContext, session_snapshot
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class SessionStartInput(ParamsModel):
    # Daily-loop DL0 (§6.6): neither client sends energy or sleep any more; both
    # stay accepted for old clients, and the scheduler logs ``energy=None``.
    energy: str | None = None
    sleep_quality: float | None = None
    available_minutes: int | None = None
    notes_md_path: str | None = None


class SessionIdInput(ParamsModel):
    session_id: str


class SessionCheckpointInput(ParamsModel):
    session_id: str
    current_practice_item_id: str | None = None
    current_answer: str | None = None
    hints_used: int | None = None
    submission_id: str | None = None
    #: mvp-0.13: the draft is a stuck answer ("I'm stuck"); stored in the
    #: practice envelope beside the retry key (no schema change).
    declared_stuck: bool | None = None
    focus_block_state: dict[str, Any] | None = None
    pending_grading_proposal: dict[str, Any] | None = None
    readiness: dict[str, Any] | None = None


@method("start_session", SessionStartInput)
def start_session(ctx: SidecarContext, params: SessionStartInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    from learnloop.goals.forecast_ledger import issue_goal_forecasts, resolve_due_forecasts

    resolve_due_forecasts(repository)
    issue_goal_forecasts(vault, repository)
    # Mobile PR-4 (§6.5): the new session and the end of every other one are
    # one BEGIN IMMEDIATE transaction, so interleaved starts from two
    # processes leave exactly one open session. A session another device owns
    # is never ended silently: ``session_open_elsewhere`` carries its snapshot
    # (the desktop's adopt / start fresh prompt is M2's).
    with owned_session_errors():
        session_id = repository.start_session_exclusive(
            {
                "energy": params.energy,
                "sleep_quality": params.sleep_quality,
                "available_minutes": params.available_minutes,
                "notes_md_path": params.notes_md_path,
            },
            request_device_id(ctx),
            settle_checkpoint=lambda stale: settle_self_grade_disclosure(repository, stale),
        )
    snapshot = session_snapshot(repository, session_id)
    if snapshot is None:
        raise SidecarError("internal", "Session was created but could not be read.")
    return snapshot


@method("get_start_summary", EmptyParams)
def get_start_summary(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    """What Start shows before a session begins (daily-loop DL0).

    Minutes only (§6.6): the remembered budget (the last session's minutes, else
    25 on a fresh vault), the one-tap chips, and the streak (§8), read fresh so
    the badge's "today" state is never left over from before ``start_session``.
    Read-only: nothing here is served or persisted.
    """

    _vault, repository = ctx.require_vault()
    remembered = remembered_session_minutes(repository)
    return versioned(
        {
            "remembered_minutes": remembered.minutes,
            "minutes_source": remembered.source,
            "minutes_presets": list(MINUTE_PRESETS),
            "minute_choices": list(minute_choices(remembered.minutes)),
            "streak": repository.session_day_streak(),
        }
    )


@method("get_session", SessionIdInput)
def get_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    snapshot = session_snapshot(repository, params.session_id)
    if snapshot is None:
        raise SidecarError("not_found", f"Session {params.session_id} was not found.")
    return snapshot


@method("update_session_checkpoint", SessionCheckpointInput)
def update_session_checkpoint(ctx: SidecarContext, params: SessionCheckpointInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    patch_checkpoint(repository, params, device_id=request_device_id(ctx))
    return {"ok": True}


@method("clear_session_checkpoint", SessionIdInput)
def clear_session_checkpoint(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    with repository.atomic():
        require_owned_session(ctx, repository, params.session_id)
        return {"cleared": clear_checkpoint(repository, params.session_id)}


@method("end_session", SessionIdInput)
def end_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    # Mobile PR-4: the owner check, the end and the checkpoint clear are one
    # transaction; ending an ended session still returns it unchanged.
    with owned_session_errors():
        row = repository.end_session_owned(
            params.session_id,
            request_device_id(ctx),
            clear=lambda session_id: clear_checkpoint(repository, session_id),
        )
    counts = repository.session_attempt_counts(params.session_id) or {"attempts_recorded": 0, "items_reviewed": 0}
    from learnloop.learner.session_learning_diff import session_learning_diff

    learning_diff = dict(session_learning_diff(vault, repository, params.session_id))
    learning_diff.pop("demonstrated_facet_ids", None)
    demonstrated_attempt_ids = learning_diff.pop("demonstrated_attempt_ids", [])
    cold_checks = _session_cold_checks(repository, params.session_id)
    return versioned(
        {
            "session_id": row["id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "attempts_recorded": counts["attempts_recorded"],
            "items_reviewed": counts["items_reviewed"],
            "followups_queued": _session_followups_queued(repository, params.session_id),
            # Cold checks are the session's only unassisted repair evidence, and
            # they are counted SEPARATELY from what passed: "2 answered, 1 held"
            # is the honest shape, "1 repair confirmed" alone hides the other.
            "cold_checks_completed": cold_checks["completed"],
            "cold_checks_passed": cold_checks["passed"],
            "streak": repository.session_day_streak(),
            # UX Phase 4: the calm session finish names what was practised, in
            # the knowledge well's words (display only, never evidence).
            "topics": _session_topics(vault, repository, params.session_id, demonstrated_attempt_ids),
            **learning_diff,
        }
    )


#: Attempt types that are help by construction (a walkthrough, its
#: reconstruction, a hinted answer).
_ASSISTED_ATTEMPT_TYPES = frozenset({"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"})


def _session_topics(vault, repository, session_id: str, demonstrated_attempt_ids) -> list[dict[str, Any]]:
    """The topics the session practised, each with how it went, in the ○ ◌ ●
    vocabulary (``docs/specs/ux_learnloop_v1.md`` §7.5, session end):

    * ``on_your_own`` (●): one of the topic's OWN answers in the session
      earned certification credit (the session diff's ``demonstrated_attempt_ids``:
      the unassisted attempts whose points raised a facet the session
      demonstrated). A facet another topic's answer raised credits that topic
      only (Codex review F4), and a held answer earns nothing;
    * ``with_help`` (◌): otherwise, an answer that earned points with help
      (hints, a primed retry or a walkthrough) whose grade is not held.

    A topic only tried, missed, skipped or held is not named: the line says
    what moved, never a count of what did not. Display only.
    """

    from learnloop.held_grades import held_attempt_ids

    rows = repository.session_attempt_rows(session_id)
    if not rows:
        return []
    earned = {str(attempt_id) for attempt_id in demonstrated_attempt_ids or ()}
    held = held_attempt_ids(repository, (row["id"] for row in rows))
    order: list[str] = []
    evidence: dict[str, str | None] = {}
    for row in rows:
        learning_object_id = str(row.get("learning_object_id") or "")
        if not learning_object_id or row.get("attempt_type") == "skip":
            continue
        if learning_object_id not in evidence:
            order.append(learning_object_id)
            evidence[learning_object_id] = None
        if evidence[learning_object_id] == "on_your_own" or row["id"] in held:
            continue
        assisted = (
            int(row.get("hints_used") or 0) > 0
            or bool(row.get("primed"))
            or row.get("attempt_type") in _ASSISTED_ATTEMPT_TYPES
        )
        if row["id"] in earned and not assisted:
            evidence[learning_object_id] = "on_your_own"
        elif assisted and float(row.get("correctness") or 0.0) > 0.0:
            evidence[learning_object_id] = "with_help"
    topics: list[dict[str, Any]] = []
    for learning_object_id in order:
        if evidence[learning_object_id] is None:
            continue
        learning_object = vault.learning_objects.get(learning_object_id)
        topics.append(
            {
                "learning_object_id": learning_object_id,
                "title": learning_object.title if learning_object is not None else learning_object_id,
                "evidence": evidence[learning_object_id],
            }
        )
    return topics


#: ``patch_checkpoint``'s default for a field the caller does not touch.
_KEEP: Any = object()
#: Adaptive difficulty AD1: the practice draft RPC's "leave the marker as it is".
KEEP_MARKER: Any = _KEEP
KEEP_HINT_SEEN: Any = _KEEP
KEEP_EARLIER_OPENED: Any = _KEEP


def patch_checkpoint(
    repository,
    params: SessionCheckpointInput,
    *,
    device_id: str | None,
    plan_presentation_id: Any = _KEEP,
    self_grade_disclosure: Any = _KEEP,
    first_hint_progress: Any = _KEEP,
    hint_seen: Any = _KEEP,
    page_seen: Any = _KEEP,
    earlier_opened: Any = _KEEP,
) -> None:
    """Merge ``params`` into the session's checkpoint.

    ``plan_presentation_id`` (router R2a, review F5): the daily-plan
    presentation a practice draft answers, kept in the practice envelope with
    the draft's retry key, so a draft resumed after a restart still submits
    bound to it. Only the practice draft RPC passes it; every save replaces
    it (None clears it), so a later draft never inherits an earlier one's.

    ``self_grade_disclosure`` (UX Phase 4, Codex review F1): the trace a plain
    self-grade froze before it showed a full answer
    (:func:`with_self_grade_disclosure`). It stays with its draft while the
    draft keeps its item and retry key; a draft that replaces it settles its
    exposure in the reveal ledger first (:func:`settle_self_grade_disclosure`).

    Mobile PR-4 (§6.5): the read-merge-write is one ``BEGIN IMMEDIATE``
    transaction, so two writers never merge into the same stale checkpoint,
    and it starts with the ownership check: ``device_id`` (the request
    origin's, :func:`request_device_id`; None is the desktop) must own the
    session, or the patch fails with ``session_moved``. It has no default, so
    no caller checks against the desktop by omission (Codex review F3).
    """

    with repository.atomic():
        _require_owned(repository, params.session_id, device_id)
        _patch_checkpoint_locked(
            repository, params, plan_presentation_id=plan_presentation_id,
            self_grade_disclosure=self_grade_disclosure, first_hint_progress=first_hint_progress,
            hint_seen=hint_seen, page_seen=page_seen, earlier_opened=earlier_opened,
        )


def _patch_checkpoint_locked(
    repository,
    params: SessionCheckpointInput,
    *,
    plan_presentation_id: Any,
    self_grade_disclosure: Any,
    first_hint_progress: Any,
    hint_seen: Any,
    page_seen: Any,
    earlier_opened: Any,
) -> None:
    fields = params.model_fields_set
    existing = repository.fetch_session_checkpoint(params.session_id) or {}
    focus = _copy_mapping(existing.get("focus_block_state"))
    if "focus_block_state" in fields:
        focus = _copy_mapping(params.focus_block_state)

    if "hints_used" in fields:
        hints_used = 0 if params.hints_used is None else params.hints_used
        if hints_used < 0:
            raise SidecarError("validation_error", "hintsUsed must be non-negative.", details={"field": "hintsUsed"})
        focus = _with_hints_used(focus, hints_used)

    if "submission_id" in fields:
        focus = _with_submission_id(focus, params.submission_id)

    if "declared_stuck" in fields:
        focus = _with_declared_stuck(focus, bool(params.declared_stuck))

    if plan_presentation_id is not _KEEP:
        focus = _with_plan_presentation_id(focus, plan_presentation_id)

    if first_hint_progress is not _KEEP:
        focus = _with_first_hint_progress(focus, first_hint_progress)

    if hint_seen is not _KEEP:
        focus = _with_hint_seen(focus, hint_seen)

    if page_seen is not _KEEP:
        focus = _with_keyed_flag(focus, "pageSeen", page_seen)
    if earlier_opened is not _KEEP:
        focus = _with_earlier_opened(focus, earlier_opened)

    current_item = _merged_value(existing, params, fields, "current_practice_item_id")
    if self_grade_disclosure is not _KEEP:
        focus = with_self_grade_disclosure(focus, self_grade_disclosure)
    focus = _kept_disclosure(focus, current_item)
    before = draft_self_grade_disclosure(existing)
    after = draft_self_grade_disclosure({"current_practice_item_id": current_item, "focus_block_state": focus})
    if before is not None and before != after:
        settle_self_grade_disclosure(repository, existing)

    repository.update_session_checkpoint(
        params.session_id,
        current_practice_item_id=_merged_value(existing, params, fields, "current_practice_item_id"),
        current_answer=_merged_value(existing, params, fields, "current_answer"),
        focus_block_state=focus,
        pending_grading_proposal=_merged_value(existing, params, fields, "pending_grading_proposal"),
        readiness=_merged_value(existing, params, fields, "readiness"),
    )


def request_device_id(ctx: SidecarContext) -> str | None:
    """The device a session-scoped request comes from (mobile §6.8): None, the desktop.

    Mobile PR-5 puts the request origin on the context (the phone host sets
    it around each call); until then every sidecar request is the desktop's.
    Never a parameter: a client cannot claim to be another device.
    """

    del ctx
    return None


def ownership_error(error: SessionOwnershipError) -> SidecarError:
    """The sidecar's form of a refused session operation (mobile PR-4).

    ``not_found`` and an ended session keep the codes and messages the
    desktop has always received; ``session_moved``, ``session_open_elsewhere``
    and ``current_item_desktop_only`` are new, not retryable, and carry the
    owner snapshot as details.
    """

    if error.code == "session_ended":
        return SidecarError("validation_error", error.message)
    return SidecarError(error.code, error.message, retryable=False, details=dict(error.details))


@contextmanager
def owned_session_errors() -> Iterator[None]:
    try:
        yield
    except SessionOwnershipError as error:
        raise ownership_error(error) from None


def _require_owned(
    repository, session_id: str, device_id: str | None, *, expected_generation: int | None = None
) -> dict[str, Any]:
    with owned_session_errors():
        return repository.require_session_owner(session_id, device_id, expected_generation=expected_generation)


def require_owned_session(
    ctx: SidecarContext, repository, session_id: str, *, expected_generation: int | None = None
) -> dict[str, Any]:
    """The open session, if the request's device owns it (mobile PR-4, §6.5).

    Every session-scoped write calls it at its acceptance boundary:
    checkpoint updates and clears, draft saves, self-grade disclosures (both
    the freeze and a display of the key), skips, submit acceptance, hint
    requests, hint reveals and discriminating answers, teach-back turns,
    acknowledgements and the end. A write from a device that does not own the
    session fails with ``session_moved`` (not retryable), carrying the owner's
    label and generation. Reads never call it. A submit or a hint job
    accepted before a handoff completes, because ownership is checked at
    acceptance. ``expected_generation``: see
    ``SessionOwnershipStoreMixin.require_session_owner``.
    """

    return _require_owned(repository, session_id, request_device_id(ctx), expected_generation=expected_generation)


def _merged_value(existing: dict[str, Any], params: SessionCheckpointInput, fields: set[str], name: str):
    if name in fields:
        return getattr(params, name)
    return existing.get(name)


def _copy_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _with_hints_used(focus: dict[str, Any] | None, hints_used: int) -> dict[str, Any]:
    payload = dict(focus or {})
    practice = payload.get("practice")
    if not isinstance(practice, dict):
        practice = {}
    else:
        practice = dict(practice)
    practice["hintsUsed"] = hints_used
    payload["practice"] = practice
    return payload


def _with_declared_stuck(focus: dict[str, Any] | None, declared_stuck: bool) -> dict[str, Any]:
    """Store whether the draft is a stuck answer in the practice envelope.

    Only a stuck draft carries the key; anything else clears it, so a later
    item never inherits an earlier item's stuck mode.
    """

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    if declared_stuck:
        practice["declaredStuck"] = True
    else:
        practice.pop("declaredStuck", None)
    payload["practice"] = practice
    return payload


def _with_plan_presentation_id(focus: dict[str, Any] | None, presentation_id: str | None) -> dict[str, Any]:
    """Store the draft's daily-plan presentation in the practice envelope
    (router R2a; no schema change). A blank or absent id clears it."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    value = presentation_id.strip() if isinstance(presentation_id, str) else ""
    if value:
        practice["planPresentationId"] = value
    else:
        practice.pop("planPresentationId", None)
    payload["practice"] = practice
    return payload


def _with_first_hint_progress(focus: dict[str, Any] | None, marker: str | None) -> dict[str, Any]:
    """Adaptive difficulty AD1 (§11.2): keep the draft's first-hint progress
    marker in the practice envelope with the retry key it was set under (no
    schema change), so a restored draft keeps it and another draft never
    inherits it. None clears it."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    key = practice.get("submissionId") or practice.get("submission_id")
    if marker in ("no_draft", "draft_started") and isinstance(key, str) and key.strip():
        practice["firstHintProgress"] = {"submissionId": key.strip(), "value": marker}
    else:
        practice.pop("firstHintProgress", None)
    payload["practice"] = practice
    return payload


def _with_hint_seen(focus: dict[str, Any] | None, seen: Any) -> dict[str, Any]:
    """Adaptive difficulty AD1 fix round 5 (V4): keep "a hint was seen on this
    draft" in the practice envelope with the retry key it was set under (no
    schema change), so a draft restored without a first-hint marker knows
    the first hint's timing is unknown. Anything but True clears it."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    key = practice.get("submissionId") or practice.get("submission_id")
    if seen is True and isinstance(key, str) and key.strip():
        practice["hintSeen"] = {"submissionId": key.strip()}
    else:
        practice.pop("hintSeen", None)
    payload["practice"] = practice
    return payload


def _with_keyed_flag(focus: dict[str, Any] | None, name: str, value: Any) -> dict[str, Any]:
    """A flag kept in the practice envelope under the retry key it was set
    under (Reader CA1's ``pageSeen``, as ``hintSeen``); anything but True
    clears it."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    key = practice.get("submissionId") or practice.get("submission_id")
    if value is True and isinstance(key, str) and key.strip():
        practice[name] = {"submissionId": key.strip()}
    else:
        practice.pop(name, None)
    payload["practice"] = practice
    return payload


def _with_earlier_opened(focus: dict[str, Any] | None, opened: Any) -> dict[str, Any]:
    """Reader CA2 (K6, Q2; Codex review F1): *earlier on this question* was
    opened before Submit on this draft, kept in the practice envelope with
    the retry key it was opened under (no schema change), so the one
    hint-equivalent it costs survives a restart and a move into steps: the
    submit folds it from here (:func:`draft_earlier_opened`), never from the
    client's count. Only True sets it; nothing but a new draft clears it."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    key = practice.get("submissionId") or practice.get("submission_id")
    stored = practice.get("earlierOpened")
    if opened is True and isinstance(key, str) and key.strip() and not (
            isinstance(stored, dict) and stored.get("submissionId") == key.strip()):
        # A marker already kept for this key stays as it is (re-review F1:
        # one carried into steps keeps ``carriedTo``, so it counts once).
        practice["earlierOpened"] = {"submissionId": key.strip()}
    payload["practice"] = practice
    return payload


def draft_page_seen(practice: dict[str, Any] | None, submission_id: str | None) -> bool:
    """Reader CA1: whether a saved draft records the original page opened
    before Submit under ``submission_id``."""

    if not isinstance(practice, dict) or not submission_id:
        return False
    stored = practice.get("pageSeen")
    return isinstance(stored, dict) and stored.get("submissionId") == submission_id


def _draft_earlier_marker(checkpoint: dict[str, Any] | None, practice_item_id: str) -> dict[str, Any] | None:
    if not checkpoint or checkpoint.get("current_practice_item_id") != practice_item_id:
        return None
    focus = checkpoint.get("focus_block_state")
    practice = focus.get("practice") if isinstance(focus, dict) else None
    if not isinstance(practice, dict):
        return None
    key = practice.get("submissionId") or practice.get("submission_id")
    stored = practice.get("earlierOpened")
    if isinstance(stored, dict) and isinstance(key, str) and bool(key) and stored.get("submissionId") == key:
        return stored
    return None


def draft_earlier_opened(checkpoint: dict[str, Any] | None, *, practice_item_id: str) -> bool:
    """Whether the session's saved draft on ``practice_item_id`` opened an
    earlier attempt's help under its current retry key (Codex review F1).
    The panel reads it to say the opening is already counted."""

    return _draft_earlier_marker(checkpoint, practice_item_id) is not None


def draft_earlier_uncarried(checkpoint: dict[str, Any] | None, *, practice_item_id: str) -> bool:
    """Whether the draft's opening is not marked carried yet (opened, and
    :func:`carry_earlier_opened` has not recorded the first problem it moved
    onto). Counting no longer reads it (orchestrator fix F15/F1): the draft's
    marker and the problem's ``earlier_opened_at`` are ORed, one per attempt."""

    marker = _draft_earlier_marker(checkpoint, practice_item_id)
    return marker is not None and not marker.get("carriedTo")


def carry_earlier_opened(repository, session_id: str | None, *, practice_item_id: str,
                         workbench_session_id: str) -> bool:
    """Codex re-review F1: the practice screen hands its draft to the steps,
    so the opening's one hint moves onto the unfinished workbench, where it
    lives as a carried answer-box hint (``workbench_sessions.carried_hints``,
    durable whatever the session's later drafts or sessions). The draft's
    marker records where it went (``carriedTo``), so the checkpoint never
    counts it again and the panel still says it is counted. Returns whether
    it was carried now (the caller added it to the carried count)."""

    if not session_id:
        return False
    checkpoint = repository.fetch_session_checkpoint(session_id)
    if not draft_earlier_uncarried(checkpoint, practice_item_id=practice_item_id):
        return False
    focus = _copy_mapping(checkpoint.get("focus_block_state"))
    practice = dict(focus.get("practice") or {})
    practice["earlierOpened"] = {**practice["earlierOpened"], "carriedTo": workbench_session_id}
    focus["practice"] = practice
    repository.update_session_checkpoint(
        session_id,
        current_practice_item_id=checkpoint.get("current_practice_item_id"),
        current_answer=checkpoint.get("current_answer"),
        focus_block_state=focus,
        pending_grading_proposal=checkpoint.get("pending_grading_proposal"),
        readiness=checkpoint.get("readiness"),
    )
    return True


def draft_hint_seen(practice: dict[str, Any] | None, submission_id: str | None) -> bool:
    """Whether a saved draft records a hint seen under ``submission_id``."""

    if not isinstance(practice, dict) or not submission_id:
        return False
    stored = practice.get("hintSeen")
    return isinstance(stored, dict) and stored.get("submissionId") == submission_id


def draft_first_hint_progress(practice: dict[str, Any] | None, submission_id: str | None) -> str | None:
    """The marker a saved draft holds for ``submission_id``, else None."""

    if not isinstance(practice, dict) or not submission_id:
        return None
    stored = practice.get("firstHintProgress")
    if not isinstance(stored, dict) or stored.get("submissionId") != submission_id:
        return None
    value = stored.get("value")
    return value if value in ("no_draft", "draft_started") else None


def draft_plan_presentation(checkpoint: dict[str, Any] | None, *, practice_item_id: str,
                            submission_id: str | None) -> str | None:
    """The presentation a saved draft named, when ``submission_id`` is that
    draft's retry key on ``practice_item_id`` (router R2a, review F5), else None."""

    if not checkpoint or not submission_id or checkpoint.get("current_practice_item_id") != practice_item_id:
        return None
    focus = checkpoint.get("focus_block_state")
    practice = focus.get("practice") if isinstance(focus, dict) else None
    if not isinstance(practice, dict):
        return None
    key = practice.get("submissionId") or practice.get("submission_id")
    if not isinstance(key, str) or key.strip() != submission_id.strip():
        return None
    value = practice.get("planPresentationId")
    return value if isinstance(value, str) and value.strip() else None


def _with_submission_id(focus: dict[str, Any] | None, submission_id: str | None) -> dict[str, Any]:
    """Store the current attempt's stable retry key in the practice envelope.

    The checkpoint already has a JSON focus-block field, so this is additive
    and needs no schema migration.  Clearing or switching a legacy client must
    not leave a previous item's key behind.
    """

    payload = dict(focus or {})
    practice = payload.get("practice")
    if not isinstance(practice, dict):
        practice = {}
    else:
        practice = dict(practice)
    if submission_id is None:
        practice.pop("submissionId", None)
        practice.pop("submission_id", None)
    else:
        stable_id = submission_id.strip()
        if not stable_id:
            raise SidecarError(
                "validation_error",
                "submissionId must not be blank.",
                details={"field": "submissionId"},
            )
        practice["submissionId"] = stable_id
        practice.pop("submission_id", None)
    payload["practice"] = practice
    return payload


#: The practice envelope's key for the trace a plain self-grade froze before
#: showing a full answer (UX Phase 4, Codex review F1; no schema change).
_SELF_GRADE_DISCLOSURE_KEY = "selfGradeDisclosure"


def with_self_grade_disclosure(focus: dict[str, Any] | None, disclosure: dict[str, Any] | None) -> dict[str, Any]:
    """Store (or, with None, drop) the frozen self-grade trace in the practice envelope."""

    payload = dict(focus or {})
    practice = payload.get("practice")
    practice = dict(practice) if isinstance(practice, dict) else {}
    if disclosure:
        practice[_SELF_GRADE_DISCLOSURE_KEY] = dict(disclosure)
    else:
        practice.pop(_SELF_GRADE_DISCLOSURE_KEY, None)
    payload["practice"] = practice
    return payload


def _kept_disclosure(focus: dict[str, Any] | None, current_item: Any) -> dict[str, Any] | None:
    """The envelope without a disclosure that no longer belongs to its draft
    (another item, or another retry key on the same item)."""

    disclosure = draft_self_grade_disclosure({"current_practice_item_id": current_item, "focus_block_state": focus})
    practice = focus.get("practice") if isinstance(focus, dict) else None
    if disclosure is None and isinstance(practice, dict) and _SELF_GRADE_DISCLOSURE_KEY in practice:
        return with_self_grade_disclosure(focus, None)
    return focus


def draft_self_grade_disclosure(checkpoint: dict[str, Any] | None) -> dict[str, Any] | None:
    """The trace a plain self-grade froze for the checkpoint's draft, or None.

    Only while the draft is still the one it froze: the same item and the
    same retry key. ``{"practice_item_id", "learning_object_id",
    "submission_id", "answer_md", "explanation_md"}``.
    """

    if not checkpoint:
        return None
    focus = checkpoint.get("focus_block_state")
    practice = focus.get("practice") if isinstance(focus, dict) else None
    if not isinstance(practice, dict):
        return None
    stored = practice.get(_SELF_GRADE_DISCLOSURE_KEY)
    if not isinstance(stored, dict):
        return None
    item_id = stored.get("practiceItemId")
    submission_id = stored.get("submissionId")
    draft_key = practice.get("submissionId") or practice.get("submission_id")
    if (
        not isinstance(item_id, str)
        or not isinstance(submission_id, str)
        or item_id != checkpoint.get("current_practice_item_id")
        or submission_id != draft_key
        or not isinstance(stored.get("answerMd"), str)
    ):
        return None
    explanation = stored.get("explanationMd")
    return {
        "practice_item_id": item_id,
        "learning_object_id": stored.get("learningObjectId") if isinstance(stored.get("learningObjectId"), str) else None,
        "submission_id": submission_id,
        "answer_md": stored["answerMd"],
        "explanation_md": explanation if isinstance(explanation, str) and explanation.strip() else None,
    }


def settle_self_grade_disclosure(repository, checkpoint: dict[str, Any] | None) -> None:
    """The draft a plain self-grade showed a full answer for is done with:
    debit the reveal ledger (``reveal_ledger.record_self_grade_disclosure_reveal``).

    Committed under its retry key: linked to that attempt (it counts against
    the next attempt). Never committed: an unlinked row stamped now, so a
    later attempt on the item is primed. Best effort and idempotent.
    """

    disclosure = draft_self_grade_disclosure(checkpoint)
    if disclosure is None:
        return
    from learnloop.attempts.reveal_ledger import frozen_trace_hash, record_self_grade_disclosure_reveal

    try:
        attempt = repository.practice_attempt_by_submission_id(disclosure["submission_id"])
    except Exception:  # noqa: BLE001 - ledger bookkeeping never fails the action
        attempt = None
    committed = attempt is not None and attempt.get("practice_item_id") == disclosure["practice_item_id"]
    record_self_grade_disclosure_reveal(
        repository,
        practice_item_id=disclosure["practice_item_id"],
        learning_object_id=disclosure["learning_object_id"]
        or (str(attempt.get("learning_object_id") or "") or None if committed else None),
        submission_id=disclosure["submission_id"],
        frozen_hash=frozen_trace_hash(disclosure["answer_md"], disclosure["explanation_md"]),
        attempt_id=str(attempt["id"]) if committed else None,
    )


def clear_checkpoint(repository, session_id: str) -> bool:
    """Clear the session's checkpoint, settling a self-grade disclosure first."""

    settle_self_grade_disclosure(repository, repository.fetch_session_checkpoint(session_id))
    return repository.clear_session_checkpoint(session_id)


def _session_cold_checks(repository, session_id: str) -> dict[str, int]:
    """Repair cold checks this session spent, and how many of them passed.

    Same window convention as ``_session_followups_queued`` (attempt timestamps
    between the session's start and end). A cold task is joined to the attempt
    that CONSUMED it, so a check scheduled long ago counts for the session that
    actually answered it. ``passed`` reads the recorded outcome, not the grade:
    an outcome row is written by the cold verification lane, and its absence
    means the check produced no verdict rather than a failure.
    """

    session = repository.fetch_session(session_id)
    if session is None:
        return {"completed": 0, "passed": 0}
    started_at = session["started_at"]
    ended_at = session["ended_at"] or started_at
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT o.outcome AS outcome
            FROM followup_tasks t
            JOIN practice_attempts a ON a.id = t.consumed_attempt_id
            LEFT JOIN causal_cold_outcomes o ON o.followup_task_id = t.id
            WHERE t.kind = 'cold_retry'
              AND t.status = 'consumed'
              AND a.created_at >= ? AND a.created_at <= ?
            """,
            (started_at, ended_at),
        ).fetchall()
    return {
        "completed": len(rows),
        "passed": sum(1 for row in rows if row["outcome"] == "cold_success"),
    }


def _session_followups_queued(repository, session_id: str) -> int:
    session = repository.fetch_session(session_id)
    if session is None:
        return 0
    started_at = session["started_at"]
    ended_at = session["ended_at"] or started_at
    with repository.connection() as connection:
        rows = connection.execute(
            """
            SELECT s.triggered_actions_json
            FROM attempt_surprise s
            JOIN practice_attempts a ON a.id = s.attempt_id
            WHERE a.created_at >= ? AND a.created_at <= ?
              AND s.triggered_actions_json IS NOT NULL
            """,
            (started_at, ended_at),
        ).fetchall()
    count = 0
    for row in rows:
        try:
            actions = json.loads(row["triggered_actions_json"] or "[]")
        except json.JSONDecodeError:
            continue
        count += sum(
            1
            for action in actions
            if isinstance(action, str)
            and (
                action.startswith("intervention_followup:queued:")
                or action.startswith("negative_surprise_followup:")
            )
        )
    return count
