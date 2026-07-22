"""Local-first capture spine + outbox drain (spec §5.3, §13.3, §15.2; design B step 4).

``capture`` is THE one local transaction: it resolves the selection into a
sub-block anchor, appends the annotation/version/anchor rows, appends the typed
interaction event, and writes ONE durable ``reader_capture_outbox`` row -- all in a
single SQLite transaction (``repository.capture_local_transaction``). The model/job
call happens strictly AFTER commit. A client idempotency key dedupes retries to
exactly one annotation version, one interaction event, and one outbox row (§15.2).

A crash between capture-commit and drain leaves the outbox row ``pending`` and the
annotation already safe and editable (§13.3 last row: never acknowledge a capture
that can vanish). ``drain_outbox`` converts pending rows into their target work
idempotently; it is safe to re-run after a crash and never duplicates.

Reading/telemetry interaction events are salience-only (§8.2): they can never enter
the evidence pipeline. The reader is fully usable with the drain worker down (§1.1.1).
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping, NamedTuple

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import annotations as ann
from learnloop.services import commitment_arcs as ca
from learnloop.services import commitments as cmt
from learnloop.services import reader_requests as rr
from learnloop.services.salience_firewall import salience_payload

# action -> (annotation_type, capture_kind). Slice 1 captures are annotation /
# flashcard-intent / question-intent; slice 2 adds the nine-preset palette below.
_ACTION_MAP: dict[str, tuple[str, str]] = {
    "annotate": ("highlight", "annotation"),
    "highlight": ("highlight", "annotation"),
    "question": ("question", "annotation"),
    "confusion": ("confusion", "annotation"),
    "interpretation": ("interpretation", "annotation"),
    "disposition": ("disposition", "annotation"),
    "flashcard_intent": ("interpretation", "flashcard_intent"),
    "question_intent": ("question", "question_intent"),
    # P3 slice 2 nine-preset palette actions (§5.2):
    "ask": ("question", "question_intent"),
    "worked_example": ("interpretation", "flashcard_intent"),
    "alt_explanation": ("interpretation", "annotation"),
    "why_matters": ("interpretation", "annotation"),
    "test_me_later": ("interpretation", "flashcard_intent"),
    "help_me_remember": ("interpretation", "flashcard_intent"),
    "connect_it": ("interpretation", "annotation"),
    "mark_confusing": ("confusion", "annotation"),
    "not_worth_remembering": ("disposition", "annotation"),
}


class _Preset(NamedTuple):
    """A palette preset (§5.2): the local-capture action + its commit/synthesis wiring.

    ``commit_action`` is a P1 commit-class action (§5.5) or None; Ask and Mark NEVER
    create commitments (§15.2). ``enqueue_synth`` gates whether the outbox drain
    enqueues a demand-paged synthesis request (§6). ``suppress`` marks
    not_worth_remembering, which suppresses proposals and creates no commitment (§5.6).
    """

    annotation_action: str
    commit_action: str | None
    depth_preset: str | None
    enqueue_synth: bool
    suppress: bool = False


# The three visible primitives / nine presets (§5.2). Ask=1-4, Practice/Commit=5-7,
# Mark/Disposition=8-9. Only the three commit presets are P1 commit-class.
PRESETS: dict[str, _Preset] = {
    # Ask (1-4): never a commitment (§15.2); semantic work is demand-paged.
    "ask": _Preset("ask", None, None, enqueue_synth=True),
    "worked_example": _Preset("worked_example", None, None, enqueue_synth=True),
    "alt_explanation": _Preset("alt_explanation", None, None, enqueue_synth=True),
    "why_matters": _Preset("why_matters", None, None, enqueue_synth=True),
    # Practice/Commit (5-7): the three commit-class presets, each distinct.
    "test_me_later": _Preset("test_me_later", "test_me_later", "keep_in_touch", enqueue_synth=True),
    "help_me_remember": _Preset("help_me_remember", "help_me_remember", "remember_key_ideas", enqueue_synth=True),
    "connect_it": _Preset("connect_it", "help_me_remember", "remember_key_ideas", enqueue_synth=True),
    # Mark/Disposition (8-9): never a commitment (§15.2).
    "mark_confusing": _Preset("mark_confusing", None, None, enqueue_synth=True),
    "not_worth_remembering": _Preset("not_worth_remembering", None, None, enqueue_synth=False, suppress=True),
}


class CaptureError(ValueError):
    """Domain error for the capture spine."""


def _anchor_from_translation(
    *, source_id: str, revision_id: str, extraction_id: str, render_view_id: str | None,
    translation: Mapping[str, Any],
) -> dict[str, Any]:
    status = translation["status"]
    return {
        "source_id": source_id,
        "revision_id": revision_id,
        "extraction_id": extraction_id,
        "render_view_id": render_view_id,
        "status": status,
        "algo_version": ann.ALGO_VERSION,
        "confidence": translation.get("confidence"),
        "raw_selection": translation.get("raw_selection") if status == "needs_reanchor" else None,
        "segments": translation.get("segments", []),
    }


def capture(
    repository: Repository,
    *,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    action: str,
    client_idempotency_key: str,
    raw_selection: Mapping[str, Any] | None = None,
    render_view_id: str | None = None,
    learner_text: str = "",
    what_i_think_is_going_on: str | None = None,
    privacy_locality: str = "local_private",
    session_id: str | None = None,
    commitment_id: str | None = None,
    enqueue_synth: bool = False,
    preset: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """One local-first capture. Returns a receipt with the annotation id, anchor
    status, and outbox id. Idempotent on ``client_idempotency_key``."""

    if action not in _ACTION_MAP:
        raise CaptureError(f"unknown capture action: {action!r}")
    annotation_type, capture_kind = _ACTION_MAP[action]

    # Fast idempotent short-circuit (also enforced atomically in the repo txn).
    existing = repository.capture_by_client_key(client_idempotency_key)
    if existing is not None:
        head = repository.annotation_head(existing["annotation_id"]) if existing["annotation_id"] else None
        return {
            "annotation_id": existing["annotation_id"],
            "outbox_id": existing["id"],
            "interaction_event_id": existing["interaction_event_id"],
            "anchor_status": (head["anchor"] or {}).get("status") if head else None,
            "capture_kind": existing["capture_kind"],
            "deduplicated": True,
            "receipt": "acknowledged",
        }

    translation = ann.translate_selection(
        repository, extraction_id=extraction_id, raw_selection=raw_selection or {}, render_view_id=render_view_id,
    )
    anchor = _anchor_from_translation(
        source_id=source_id, revision_id=revision_id, extraction_id=extraction_id,
        render_view_id=render_view_id, translation=translation,
    )
    version = {
        "annotation_type": annotation_type,
        "learner_text": learner_text,
        "what_i_think_is_going_on": what_i_think_is_going_on,
        "privacy_locality": privacy_locality,
        "authorship": "learner",
        "client_idempotency_key": client_idempotency_key,
    }
    interaction_event = {
        "kind": "reader_capture_acknowledged",
        "origin": "learner",
        "subject_type": "reader_span",
        "subject_id": (translation.get("segments") or [{}])[0].get("span_id"),
        "payload": salience_payload({"action": action, "capture_kind": capture_kind}),
        "revision_id": revision_id,
        "render_view_id": render_view_id,
        "session_id": session_id,
        "privacy_locality": privacy_locality,
    }
    outbox = {
        "capture_kind": capture_kind,
        "payload": {
            "action": action,
            "preset": preset or action,
            "learner_text_present": bool(learner_text),
            "enqueue_synth": bool(enqueue_synth),
            "extraction_id": extraction_id,
            "span_id": (translation.get("segments") or [{}])[0].get("span_id"),
        },
        "revision_id": revision_id,
        "render_view_id": render_view_id,
        "commitment_id": commitment_id,
    }
    result = repository.capture_local_transaction(
        source_id=source_id,
        client_idempotency_key=client_idempotency_key,
        annotation=version,
        anchor=anchor,
        interaction_event=interaction_event,
        outbox=outbox,
        clock=clock,
    )
    return {
        "annotation_id": result["annotation_id"],
        "outbox_id": result["outbox_id"],
        "interaction_event_id": result["interaction_event_id"],
        "anchor_status": anchor["status"],
        "capture_kind": capture_kind,
        "commitment_id": commitment_id,
        "deduplicated": result["deduplicated"],
        "receipt": "acknowledged",
        "provisional_arc": ca.preview_for_capture(action=action, depth_preset=None),
    }


def invoke_preset(
    repository: Repository,
    *,
    preset: str,
    source_id: str,
    revision_id: str,
    extraction_id: str,
    client_idempotency_key: str,
    raw_selection: Mapping[str, Any] | None = None,
    render_view_id: str | None = None,
    learner_text: str = "",
    what_i_think_is_going_on: str | None = None,
    session_id: str | None = None,
    subject_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The three-action / nine-preset palette (§5.2). Runs the local-first capture
    transaction, creates a P1 commitment ONLY for a commit preset (§5.5), and marks
    the outbox row for demand-paged synthesis where semantic work is needed. Ask and
    Mark never create commitments (§15.2). Idempotent on ``client_idempotency_key``."""

    spec = PRESETS.get(preset)
    if spec is None:
        raise CaptureError(f"unknown preset: {preset!r}")

    # A short-circuit on retry returns the existing receipt (also enforced in-txn).
    existing = repository.capture_by_client_key(client_idempotency_key)
    if existing is not None:
        head = repository.annotation_head(existing["annotation_id"]) if existing["annotation_id"] else None
        existing_arcs = repository.arcs_for_commitment(existing["commitment_id"]) if existing["commitment_id"] else []
        return {
            "preset": preset,
            "annotation_id": existing["annotation_id"],
            "outbox_id": existing["id"],
            "commitment_id": existing["commitment_id"],
            "arc_id": existing_arcs[0] if existing_arcs else None,
            "arc": ca.project_arc(repository, arc_id=existing_arcs[0]) if existing_arcs else None,
            "anchor_status": (head["anchor"] or {}).get("status") if head else None,
            "capture_kind": existing["capture_kind"],
            "deduplicated": True,
            "receipt": "acknowledged",
        }

    # Step 4 of the capture (§5.3): create/extend a commitment ONLY for a commit
    # preset -- BEFORE the local capture, idempotent on the same client key so a crash
    # leaves at most one commitment and one annotation, both resumable (§15.2).
    commitment_id: str | None = None
    arc: dict[str, Any] | None = None
    if spec.commit_action is not None:
        subject = subject_id or (raw_selection or {}).get("nodes", [{}])[0].get("spanId") \
            or (raw_selection or {}).get("nodes", [{}])[0].get("span_id")
        target = {
            "target_kind": "source_locator",
            "target_ref": subject or extraction_id,
            "role": "required",
        }
        commitment = cmt.create_commitment(
            repository,
            action=spec.commit_action,
            intent_text=f"reader preset {preset}",
            targets=[target],
            depth_preset=spec.depth_preset or "remember_key_ideas",
            interpretation_text=learner_text or None,
            client_idempotency_key=client_idempotency_key,
            reason=f"reader_preset_{preset}",
            clock=clock,
        )
        commitment_id = commitment.id
        # §10.2 / Journey 2 step 3: a commit produces a durable, immediately visible
        # arc bound to the commitment. Idempotent: a retry that returns the existing
        # commitment reuses its already-created arc rather than minting a second.
        existing_arcs = repository.arcs_for_commitment(commitment_id)
        if not existing_arcs:
            created = ca.create_arc(
                repository, commitment_id=commitment_id, source_id=source_id, clock=clock
            )
            existing_arcs = [created["arc_id"]]
        arc = ca.project_arc(repository, arc_id=existing_arcs[0])

    receipt = capture(
        repository,
        source_id=source_id,
        revision_id=revision_id,
        extraction_id=extraction_id,
        action=spec.annotation_action,
        client_idempotency_key=client_idempotency_key,
        raw_selection=raw_selection,
        render_view_id=render_view_id,
        learner_text=learner_text,
        what_i_think_is_going_on=what_i_think_is_going_on,
        session_id=session_id,
        commitment_id=commitment_id,
        enqueue_synth=spec.enqueue_synth,
        preset=preset,
        clock=clock,
    )
    receipt["preset"] = preset
    receipt["commitment_id"] = commitment_id
    receipt["suppresses_proposals"] = spec.suppress
    if arc is not None:
        receipt["arc_id"] = arc.get("arc_id")
        receipt["arc"] = arc
        receipt["provisional_arc"] = ca.preview_for_capture(
            action=spec.annotation_action, depth_preset=spec.depth_preset
        )
    return receipt


def _default_convert(repository: Repository, row: Mapping[str, Any]) -> str | None:
    """Idempotent outbox conversion (§5.3 step 6 seam). The durable target (the
    annotation/commitment) already exists from the capture transaction. For a preset
    that needs semantic work, enqueue a demand-paged synthesis request (§6) -- the
    ONLY place the reading path touches a model, and off the hot path. Idempotent on
    the canonical request key: a re-drain after a crash never double-enqueues (§15.2)."""

    payload = _loads(row.get("payload_json"))
    if payload.get("enqueue_synth") and row.get("source_id") and row.get("revision_id") \
            and payload.get("extraction_id") and payload.get("span_id"):
        result = rr.enqueue_request(
            repository,
            source_id=row["source_id"],
            revision_id=row["revision_id"],
            extraction_id=payload["extraction_id"],
            span_id=payload["span_id"],
            preset=payload.get("preset", ""),
            annotation_id=row.get("annotation_id"),
            commitment_id=row.get("commitment_id"),
            client_idempotency_key=row.get("client_idempotency_key"),
        )
        return result["request_id"]
    return row.get("annotation_id")


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except ValueError:
            return {}
    return {}


def drain_outbox(
    repository: Repository,
    *,
    limit: int = 100,
    convert: Callable[[Repository, Mapping[str, Any]], str | None] = _default_convert,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Drain pending outbox rows idempotently. Safe to re-run after a crash: a row
    already ``done`` is never reprocessed, and ``draining`` -> ``done`` transitions
    are keyed by the durable row so nothing is lost or duplicated (§15.2)."""

    drained: list[str] = []
    failed: list[str] = []
    for row in repository.recoverable_capture_outbox(limit=limit):
        outbox_id = row["id"]
        repository.mark_capture_outbox(outbox_id, state="draining", bump_attempts=True, clock=clock)
        try:
            target_ref = convert(repository, row)
            repository.mark_capture_outbox(outbox_id, state="done", target_ref=target_ref, clock=clock)
            drained.append(outbox_id)
        except Exception as exc:  # noqa: BLE001 - retained capture; row stays recoverable
            repository.mark_capture_outbox(outbox_id, state="failed", last_error=str(exc), clock=clock)
            failed.append(outbox_id)
    return {"drained": drained, "failed": failed}


def outbox_status(repository: Repository, *, client_idempotency_key: str) -> dict[str, Any] | None:
    row = repository.capture_by_client_key(client_idempotency_key)
    return dict(row) if row is not None else None


def retry_outbox(repository: Repository, *, outbox_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """Reset a failed row to pending for the next drain (capture already durable)."""

    row = repository.get_capture_outbox(outbox_id)
    if row is None:
        raise CaptureError(f"unknown outbox row: {outbox_id!r}")
    if row["state"] == "failed":
        repository.mark_capture_outbox(outbox_id, state="pending", clock=clock)
    return repository.get_capture_outbox(outbox_id) or {}
