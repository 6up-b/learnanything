"""Reader workbench v2 RPCs: scratchpads (spec §3.4, §10). ``pad.get``, ``pad.list`` and ``pad.apply`` (RD0); and
RD4's backend: ``pad.submit_block``, ``pad.proposals``, ``proposal.label``, ``pad.drain`` and the carried questions
(``carried.carry``, ``carried.list``, ``carried.mark``).

Desktop only (pinned in tests/test_mobile_allowlist.py). A pad is the learner's own writing, never evidence: its
two exits are explicit. ``pad.apply`` follows the write protocol (``learnloop.desks.protocol``), sharing one batch
numbering per client with ``desk.apply``; after a batch commits, its blocks' committed words are emitted as learner
text (``learnloop.pads.emission``, mvp-0.68) and given their proposals, neither of which can fail the batch. A block
becomes an attempt or a teach-back only through ``pad.submit_block``, which hands its frozen text to the existing
entry points. No model call here but the entry points' own.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import Field

from learnloop.desks.protocol import ProtocolError
from learnloop.pads import carried as carried_core
from learnloop.pads import emission
from learnloop.pads import proposals as proposal_core
from learnloop.pads import submission as submission_core
from learnloop.pads.blocks import PadNotFound, PadOp, apply_pad_ops, pad_list, pad_view
from learnloop.pads.drain import desk_drain
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, Verbatim, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.desks import protocol_error
from learnloop_sidecar.registry import method
from learnloop_sidecar.workbench_protection import block_places, check_placed_quote, payload_places, reading_places, refuse_protected

LOG = logging.getLogger(__name__)

#: Every RPC this module registered in RD0 (pinned desktop-only).
PAD_RPCS: tuple[str, ...] = ("pad.get", "pad.list", "pad.apply")
#: RD4's (pinned desktop-only).
PAD_RD4_RPCS: tuple[str, ...] = (
    "pad.submit_block", "pad.proposals", "proposal.label", "pad.drain", "carried.carry", "carried.list",
    "carried.mark",
)


class PadGetInput(ParamsModel):
    pad_id: str = Field(min_length=1)


class PadListInput(ParamsModel):
    desk_id: str | None = None
    query: str | None = None
    kept: bool | None = None
    cursor: str | None = None


class PadApplyInput(ParamsModel):
    client_id: str = Field(min_length=1)
    seq: int = Field(ge=1)
    pad_id: str = Field(min_length=1)
    ops: list[PadOp]


@method("pad.get", PadGetInput)
def pad_get_handler(ctx: SidecarContext, params: PadGetInput) -> dict[str, Any]:
    """One pad: its metadata, its standing blocks in order (each with its head version and its submissions) and
    their links."""

    _vault, repository = ctx.require_vault()
    try:
        view = pad_view(repository, params.pad_id)
    except PadNotFound as exc:
        raise SidecarError("pad_not_found", "Couldn’t find this pad. Open it again from the window list.") from exc
    # A block's payload and an anchor's JSON are the client's, returned with their keys as stored.
    for block in view["blocks"]:
        block["payload"] = Verbatim(block["payload"])
    for anchor in view["anchors"]:
        anchor["anchor"] = Verbatim(anchor["anchor"])
    return versioned(view)


@method("pad.list", PadListInput)
def pad_list_handler(ctx: SidecarContext, params: PadListInput) -> dict[str, Any]:
    """Pads, most recently changed first, a page at a time: for the library, search and the drain."""

    _vault, repository = ctx.require_vault()
    return versioned(pad_list(repository, desk_id=params.desk_id, query=params.query, kept=params.kept,
                              cursor=params.cursor))


def _after_batch(ctx: SidecarContext, vault: Any, repository: Any, block_ids: list[str]) -> None:
    """The committed blocks' words to learner text, and their proposals. Never fails the batch: the reconcile on
    the next open (and after each gap drain) settles whatever this could not."""

    if not block_ids:
        return
    from learnloop_sidecar.check_hold import open_check

    try:
        # While an inline check is open the pad's words wait for its close (they would reach learner-text gaps, a
        # model's input); the close reconciles every pad (``drain_after_check``), as a vault's open does.
        if open_check(repository) is None and emission.settle_blocks(vault, repository, block_ids).queued:
            ctx.post_attempt_worker.notify()
    except Exception:  # noqa: BLE001 - the learner's write already committed
        LOG.warning("could not emit the pad's committed words", exc_info=True)
    try:
        proposal_core.propose_for_blocks(repository, block_ids, vault=vault)
    except Exception:  # noqa: BLE001 - a suggestion never fails the learner's write
        LOG.warning("could not compute the pad's proposals", exc_info=True)


def _check_source_inserts(vault: Any, repository: Any, ops: list[PadOp]) -> None:
    # Check the batch before its first op. A refusal on a later link would leave the quote inserted.
    links: dict[str, list[tuple[str, str]]] = {}
    for op in ops:
        if op.op == "link_anchor":
            links.setdefault(op.block_id, []).append((op.extraction_id, op.span_id))
    places = []
    for op in ops:
        if op.op != "insert_block" or op.kind not in {"source_quote", "source_piece", "figure"}:
            continue
        origins = [*payload_places(op.payload), *links.get(op.block_id, [])]
        if op.kind == "figure":
            blocks = list(op.payload.get("source_block_ids") or [])
            if parent := op.payload.get("parent_block_id"):
                blocks.append(parent)
            origins.extend(block_places(vault, repository, blocks))
        else:
            check_placed_quote(vault, repository, origins, op.body_md)
        places.extend(origins)
    refuse_protected(vault, repository, places)


@method("pad.apply", PadApplyInput)
def pad_apply_handler(ctx: SidecarContext, params: PadApplyInput) -> dict[str, Any]:
    """One batch of ops on one pad: ``{applied_seq, results, heads, pads}``."""

    vault, repository = ctx.require_vault()
    try:
        reply = apply_pad_ops(repository, client_id=params.client_id, seq=params.seq, pad_id=params.pad_id,
                              ops=list(params.ops),
                              check_material=lambda: _check_source_inserts(vault, repository, params.ops))
    except ProtocolError as exc:
        raise protocol_error(exc) from exc
    _after_batch(ctx, vault, repository, [str(head["block_id"]) for head in reply.get("heads") or ()])
    return versioned(reply)


# -- submitting a block (spec §10.9) ------------------------------------------------------------------------------


class SubmitTarget(ParamsModel):
    """Where the block's text goes: the practice session and item the existing entry point records it on (the item
    a problem pad or check cell answers, or a teach-back item for the block's LO from ``request_teach_back``)."""

    session_id: str = Field(min_length=1)
    practice_item_id: str = Field(min_length=1)
    assessment_contract_version_id: str | None = None
    scheduler_candidate_id: str | None = None
    latency_seconds: int | None = Field(default=None, ge=0)
    active_seconds: int | None = Field(default=None, ge=0)


class PadSubmitBlockInput(ParamsModel):
    submission_id: str = Field(min_length=1)
    block_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    submitted_as: Literal["attempt", "teach_back"] = Field(alias="as")
    target: SubmitTarget


def _submission_reply(row: dict[str, Any], *, duplicate: bool, entry: dict[str, Any] | None,
                      attempt_id: str | None = None, teach_back: dict[str, Any] | None = None) -> dict[str, Any]:
    return versioned({
        "submission_id": row["submission_id"], "block_id": row["block_id"], "version_id": row["version_id"],
        "as": row["submitted_as"], "practice_item_id": row["practice_item_id"],
        "attempt_id": attempt_id or row["attempt_id"], "teach_back_id": row["teach_back_id"], "duplicate": duplicate,
        # The entry point's own reply (already in wire form), on the call that handed the text over.
        "entry": Verbatim(entry) if entry is not None else None,
        # A teach-back's conversation, found by its id: completed (attempt_id set), ongoing (its state, to resume
        # in the teach-back screen) or, on the call that opened it, as the entry point left it.
        "teach_back": teach_back,
    })


def _hand_to_attempt(ctx: SidecarContext, vault: Any, prepared: submission_core.Prepared,
                     target: SubmitTarget) -> dict[str, Any]:
    from learnloop.attempts.stuck import stuck_attempt_type
    from learnloop_sidecar.handlers.practice import SubmitAttemptInput, submit_attempt_on

    item = vault.practice_items.get(prepared.practice_item_id)
    if item is None:
        raise SidecarError("not_found", "Couldn’t find that question. Reopen it from Practice.")
    submission = SubmitAttemptInput(
        session_id=prepared.session_id,
        practice_item_id=prepared.practice_item_id,
        answer_md=prepared.text,
        # The type the answer box would record for this item; help shown on this work is the server's to count.
        attempt_type=stuck_attempt_type(item.attempt_types_allowed, hints_used=0),
        assessment_contract_version_id=target.assessment_contract_version_id,
        scheduler_candidate_id=target.scheduler_candidate_id,
        latency_seconds=target.latency_seconds,
        active_seconds=target.active_seconds,
        # The attempt path's own idempotency key: a retry after a lost reply finds the recorded attempt.
        submission_id=f"pad:{prepared.submission_id}",
    )
    # The one submit implementation, with the help shown on this item in this session folded in by the server
    # (worked help makes the answer assisted, exactly as on the practice screen).
    return submit_attempt_on(ctx, submission, entry_surface=submission_core.ENTRY_SURFACE, hint_window_fold=True)


def _teach_back_status(repository: Any, prepared: submission_core.Prepared,
                       conversation_id: str | None) -> tuple[str, dict[str, Any] | None, str | None]:
    """Where the conversation ``conversation_id`` stands, found by its id alone (never by its words, which another
    submission may share): ``completed`` (its attempt, whose evidence carries the id as its agent run), ``ongoing``
    (the session's checkpointed state), or ``not_started``. Refuses when another teach-back of the item is under way
    in the session: its next turn would take the block as an answer."""

    from learnloop.tutor.teach_back import TeachBackState
    from learnloop_sidecar.context import teach_back_envelope

    if conversation_id is not None:
        attempt_id = repository.find_attempt_id_by_evidence_agent_run(
            practice_item_id=prepared.practice_item_id, agent_run_id=conversation_id, attempt_type="teach_back")
        if attempt_id is not None:
            return "completed", None, attempt_id
    checkpoint = repository.fetch_session_checkpoint(prepared.session_id) or {}
    envelope = teach_back_envelope(checkpoint.get("current_answer"))
    if envelope is not None:
        state = TeachBackState.from_dict(envelope["state"])
        if state.practice_item_id == prepared.practice_item_id and state.turns:
            if conversation_id is not None and state.conversation_id == conversation_id:
                return "ongoing", state.to_dict(), None
            raise SidecarError("teach_back_in_progress",
                               "Return to Practice to finish the explanation you started.")
    return "not_started", None, None


def _hand_to_teach_back(ctx: SidecarContext, prepared: submission_core.Prepared, target: SubmitTarget,
                        conversation_id: str) -> tuple[dict[str, Any], str | None]:
    """The block's words as the opening of the conversation ``conversation_id`` (reserved before this call)."""

    from learnloop_sidecar.handlers.teach_back import SubmitTeachBackTurnInput, submit_teach_back_turn_on

    entry = submit_teach_back_turn_on(ctx, SubmitTeachBackTurnInput(
        session_id=prepared.session_id, practice_item_id=prepared.practice_item_id,
        scheduler_candidate_id=target.scheduler_candidate_id, answer_md=prepared.text,
        latency_seconds=target.latency_seconds, active_seconds=target.active_seconds),
        conversation_id=conversation_id)
    # Done at once (the student could not ask): graded now, the attempt's evidence carrying the conversation's id.
    return entry, (entry.get("attemptId") if entry.get("done") else None)


def _submit_teach_back(ctx: SidecarContext, repository: Any, prepared: submission_core.Prepared,
                       target: SubmitTarget) -> dict[str, Any]:
    """A teach-back submission, reserved before its hand-off so a crash anywhere after it is recoverable.

    The submission's row is written first, naming a conversation id minted here; the conversation is then opened
    under that id. A retry of the same submission finds the row and asks where its conversation stands, by that id:
    completed (its attempt), ongoing (its state, to resume), or never started (a crash before the hand-off, or the
    entry point refused: the words are handed over again under the same id)."""

    from learnloop.ids import new_ulid

    row = prepared.existing
    conversation_id = str(row["teach_back_id"]) if row is not None else new_ulid()
    status, state, attempt_id = _teach_back_status(repository, prepared, conversation_id)
    if row is None:
        row = submission_core.record(repository, prepared, attempt_id=None, teach_back_id=conversation_id)
        conversation_id = str(row["teach_back_id"])  # a concurrent first call's reservation wins
    duplicate = prepared.existing is not None
    entry = None
    if status == "not_started":
        entry, attempt_id = _hand_to_teach_back(ctx, prepared, target, conversation_id)
        status = "completed" if attempt_id else "ongoing"
        state = None if attempt_id else (entry.get("state") or None)
    return _submission_reply(row, duplicate=duplicate, entry=entry, attempt_id=attempt_id or row.get("attempt_id"),
                             teach_back={"status": status, "conversation_id": conversation_id,
                                         "state": Verbatim(state) if state is not None else None})


@method("pad.submit_block", PadSubmitBlockInput)
def pad_submit_block_handler(ctx: SidecarContext, params: PadSubmitBlockInput) -> dict[str, Any]:
    """Submit one block version as an attempt or a teach-back (an explicit act): ``{submission_id, block_id,
    version_id, as, attempt_id?, teach_back_id?, duplicate, entry?, teach_back?}``. Idempotent by
    ``submission_id``."""

    vault, repository = ctx.require_vault()
    try:
        # The submission's own refusals (not_learners_words, stale_version, …) first, then protection's: prepare
        # only reads and freezes, nothing is written before both pass.
        prepared = submission_core.prepare(
            repository, submission_id=params.submission_id, block_id=params.block_id, version_id=params.version_id,
            submitted_as=params.submitted_as, practice_item_id=params.target.practice_item_id,
            session_id=params.target.session_id)
        refuse_protected(vault, repository, block_places(vault, repository, [params.block_id]))
    except submission_core.SubmissionRefused as exc:
        raise SidecarError(exc.code, exc.message, details=exc.details) from exc
    if params.submitted_as == submission_core.TEACH_BACK:
        return _submit_teach_back(ctx, repository, prepared, params.target)
    if prepared.existing is not None:
        return _submission_reply(prepared.existing, duplicate=True, entry=None)
    entry: dict[str, Any] | None = _hand_to_attempt(ctx, vault, prepared, params.target)
    attempt_id = (entry or {}).get("attemptId")
    if not attempt_id:
        raise SidecarError("internal", "Couldn’t record this answer. Open the question in Practice and try again.")
    row = submission_core.record(repository, prepared, attempt_id=attempt_id, teach_back_id=None)
    return _submission_reply(row, duplicate=False, entry=entry)


# -- proposals and their labels (spec §10.6) ----------------------------------------------------------------------


class PadProposalsInput(ParamsModel):
    pad_id: str = Field(min_length=1)


@method("pad.proposals", PadProposalsInput)
def pad_proposals_handler(ctx: SidecarContext, params: PadProposalsInput) -> dict[str, Any]:
    """The pad's gutter proposals: one per standing block's current words at most, with its labels."""

    vault, repository = ctx.require_vault()
    try:
        out = proposal_core.pad_proposals(repository, params.pad_id, vault=vault)
    except proposal_core.ProposalRefused as exc:
        raise SidecarError(exc.code, exc.message) from exc
    for row in out["proposals"]:
        row["target"] = Verbatim(row["target"])
    return versioned(out)


class ProposalLabelInput(ParamsModel):
    label_id: str = Field(min_length=1)
    proposal_kind: Literal["pad_proposal", "promoted_row"] = "pad_proposal"
    proposal_id: str = Field(min_length=1)
    label: Literal["opened", "not_this", "dismiss", "ignored"]


@method("proposal.label", ProposalLabelInput)
def proposal_label_handler(ctx: SidecarContext, params: ProposalLabelInput) -> dict[str, Any]:
    """What the learner did with a proposal ("not this" means wrong, "dismiss" means not now), once per id."""

    _vault, repository = ctx.require_vault()
    try:
        out = proposal_core.label(repository, label_id=params.label_id, proposal_kind=params.proposal_kind,
                                  proposal_id=params.proposal_id, label_value=params.label)
    except proposal_core.ProposalRefused as exc:
        raise SidecarError(exc.code, exc.message) from exc
    return versioned(out)


# -- the desk drain and carried questions (spec §10.12) -----------------------------------------------------------


class PadDrainInput(ParamsModel):
    desk_id: str = Field(min_length=1)
    #: The learner's local calendar day (YYYY-MM-DD); today when absent.
    day: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


@method("pad.drain", PadDrainInput)
def pad_drain_handler(ctx: SidecarContext, params: PadDrainInput) -> dict[str, Any]:
    """Closing a desk: the pads it worked on that day, what each holds, and a carry offer when the last line asks."""

    _vault, repository = ctx.require_vault()
    return versioned(desk_drain(repository, params.desk_id, day=params.day))


class CarriedAnchor(ParamsModel):
    span_ids: list[str] = Field(default_factory=list)
    extraction_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    anchor: dict[str, Any] = Field(default_factory=dict)


class CarryInput(ParamsModel):
    block_ids: list[str] = Field(default_factory=list)
    carried_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=4000)
    origin_kind: Literal["block", "selection", "note", "drain", "typed"]
    origin_ref: str | None = None
    anchor: CarriedAnchor | None = None
    desk_id: str | None = None


def _carried_wire(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("anchor") is not None:
        row = {**row, "anchor": Verbatim(row["anchor"])}
    return row


@method("carried.carry", CarryInput)
def carried_carry_handler(ctx: SidecarContext, params: CarryInput) -> dict[str, Any]:
    """Carry a question (idempotent by ``carried_id``): ``{carried: {...}, created}``."""

    _vault, repository = ctx.require_vault()
    anchor = params.anchor.model_dump() if params.anchor is not None else None
    places = []
    if params.anchor:
        places = reading_places(params.anchor.extraction_id, [params.anchor.span_id, *params.anchor.span_ids])
        if not params.anchor.span_ids:
            anchor.pop("span_ids")  # Existing single-passage receipts compare the full anchor on retry.
    if params.origin_kind in {"selection", "note"} and not params.anchor:
        raise SidecarError("validation_error", "A question saved from a selection needs its passage.")
    block_ids = list(params.block_ids)
    if params.origin_kind == "block":
        if not params.origin_ref:
            raise SidecarError("validation_error", "A question saved from a pad line needs its line.")
        block_ids.append(params.origin_ref)
    try:
        carried_core.check_question(params.text, anchor)  # its own refusals keep their codes, before protection's
        with repository.atomic():
            block_origins = block_places(_vault, repository, block_ids)
            places.extend(block_origins)
            if block_origins and anchor is not None and params.block_ids:
                anchor["source_places"] = [list(place) for place in sorted(set(block_origins))]
            refuse_protected(_vault, repository, places)
            row = carried_core.carry(repository, carried_id=params.carried_id, text=params.text,
                                     origin_kind=params.origin_kind, origin_ref=params.origin_ref, anchor=anchor,
                                     desk_id=params.desk_id)
    except carried_core.CarriedRefused as exc:
        raise SidecarError(exc.code, exc.message, details=exc.details) from exc
    created = row.pop("created")
    return versioned({"carried": _carried_wire(row), "created": created})


class CarriedListInput(ParamsModel):
    which: Literal["open", "closed", "all"] = "open"
    desk_id: str | None = None
    cursor: str | None = None


@method("carried.list", CarriedListInput)
def carried_list_handler(ctx: SidecarContext, params: CarriedListInput) -> dict[str, Any]:
    """Carried questions, longest carried first, a page at a time, with the shelf's display limit."""

    _vault, repository = ctx.require_vault()
    out = carried_core.listing(repository, which=params.which, desk_id=params.desk_id, cursor=params.cursor)
    out["carried"] = [_carried_wire(row) for row in out["carried"]]
    return versioned(out)


class CarriedMarkInput(ParamsModel):
    event_id: str = Field(min_length=1)
    carried_id: str = Field(min_length=1)
    event: Literal["fruitful", "not_now", "let_go", "surfaced", "ignored"]
    #: Required for a label (fruitful, not now, let it go): the version the client last saw.
    expected_version: int | None = Field(default=None, ge=1)
    #: What the event happened beside (a passage, a window, a desk), for surfaced and ignored.
    ref: str | None = None


@method("carried.mark", CarriedMarkInput)
def carried_mark_handler(ctx: SidecarContext, params: CarriedMarkInput) -> dict[str, Any]:
    """A label or a notice on a carried question (idempotent by ``event_id``): ``{carried, applied, conflict}``."""

    _vault, repository = ctx.require_vault()
    try:
        row = carried_core.mark(repository, event_id=params.event_id, carried_id=params.carried_id, event=params.event,
                                expected_version=params.expected_version, ref=params.ref)
    except carried_core.CarriedRefused as exc:
        raise SidecarError(exc.code, exc.message, details=exc.details) from exc
    applied, conflict = row.pop("applied"), row.pop("conflict")
    return versioned({"carried": _carried_wire(row), "applied": applied, "conflict": conflict})
