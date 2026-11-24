"""Reader workbench v2 RPCs for checks where the learner reads (spec §3.4, §12.6; mvp-0.69).

* ``checks.due_for``: the due delayed checks by goal, learning object, reading or passage, each with its host passage.
  Read only; it shows nothing of the item.
* The inline administration protocol (``learnloop.intent.inline_administration``): ``check.begin_inline`` (the item
  Today's check view would serve, served through Today's own session serve so its contract is frozen the same way,
  and the protection with its first veil set, all before the prompt is returned), ``check.protect_more``,
  ``check.expose`` (persisted at once: an opened veil writes its reveal), ``check.submit_inline`` (the attempt through
  the one attempt service, then settlement as for any qualifying attempt; idempotent by ``submission_id``),
  ``check.abandon_inline`` and ``check.open_inline`` (the restart read).

Desktop only (pinned in tests/test_mobile_allowlist.py). No model call of their own (the attempt service grades as it
always does).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from learnloop.intent import inline_administration as IA
from learnloop.intent.inline_checks import due_checks
from learnloop_sidecar.handlers.practice import SelfGradeInputDto
from learnloop_sidecar.check_hold import drain_after_check
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, Verbatim, to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method
from learnloop_sidecar.request_origin import host_mutation

#: Every RPC this module registers (pinned desktop-only).
INLINE_CHECK_RPCS: tuple[str, ...] = ("checks.due_for", "check.begin_inline", "check.protect_more", "check.expose",
                                      "check.submit_inline", "check.abandon_inline", "check.open_inline")


class ChecksDueForInput(ParamsModel):
    goal_id: str | None = None
    learning_object_ids: list[str] | None = None
    extraction_id: str | None = None
    span_id: str | None = None


@method("checks.due_for", ChecksDueForInput)
def checks_due_for_handler(ctx: SidecarContext, params: ChecksDueForInput) -> dict[str, Any]:
    """``{checks: [{commitment_id, lo_id, due, host?, provenance, being_answered}]}``."""

    vault, repository = ctx.require_vault()
    return versioned({"checks": due_checks(
        vault, repository, goal_id=params.goal_id, learning_object_ids=params.learning_object_ids,
        extraction_id=params.extraction_id, span_id=params.span_id)})


class VisibleFigure(ParamsModel):
    figure_id: str
    span_id: str | None = None


class VisibleWindow(ParamsModel):
    window_id: str = Field(min_length=1)
    #: source | video | pad_stack | pad | ink | lesson | thread | history | panel | ...
    kind: str = Field(min_length=1)
    extraction_id: str | None = None
    span_ids: list[str] = Field(default_factory=list)
    note_ids: list[str] = Field(default_factory=list)
    figures: list[VisibleFigure] = Field(default_factory=list)
    pad_block_ids: list[str] = Field(default_factory=list)
    exchange_ids: list[str] = Field(default_factory=list)


class VisibleSearchRow(ParamsModel):
    #: span | pad | note | exchange | thread | ...
    kind: str
    extraction_id: str | None = None
    span_id: str | None = None
    ref_id: str | None = None


class Visible(ParamsModel):
    """What is on screen, on every desk: the windows (with what each shows), the companion, overview previews and
    search results."""

    windows: list[VisibleWindow] = Field(default_factory=list)
    companion_open: bool = False
    companion_exchange_ids: list[str] = Field(default_factory=list)
    preview_window_ids: list[str] = Field(default_factory=list)
    search_rows: list[VisibleSearchRow] = Field(default_factory=list)


class BeginInlineInput(ParamsModel):
    request_id: str = Field(min_length=1, max_length=128)
    commitment_id: str = Field(min_length=1)
    #: The desks' practice session: the attempt service records the answer on it, as every surface does. Absent (the
    #: app has none yet), the most recent open one, else a new one, as a workbench submit resolves it.
    session_id: str | None = None
    visible: Visible = Field(default_factory=Visible)


class TokenInput(ParamsModel):
    administration_token: str = Field(min_length=1, max_length=128)


class ProtectMoreInput(TokenInput):
    visible: Visible


class ExposeInput(TokenInput):
    #: What was opened or reached: a veiled ref as ``check.begin_inline`` / ``check.protect_more`` named it, or for
    #: ``left`` the surface reached (``{kind: "surface", surface}``).
    ref: dict[str, Any]
    kind: Literal["opened_veil", "left", "navigated", "help"]
    #: The client's id for this opening (stable across retries): a retry returns the first result, charging nothing.
    exposure_id: str | None = Field(default=None, min_length=1, max_length=128)


class SubmitInlineInput(TokenInput):
    submission_id: str = Field(min_length=1, max_length=128)
    answer_md: str
    #: The last veil revision the client applied: behind the server's, the submit is refused (``veils_stale``).
    veils_revision: int = Field(ge=0)
    latency_seconds: int | None = Field(default=None, ge=0)
    active_seconds: int | None = Field(default=None, ge=0)
    #: Grading unavailable: the learner's own grade, as ``submit_attempt`` takes it.
    self_grade: SelfGradeInputDto | None = None


def _covered(vault: Any, repository: Any) -> IA.Covered:
    """The sections that treat the check's LOs (judged coverage about them, as the goal lens reads it), or None when
    coverage cannot be read (every visible source passage is then veiled)."""

    from learnloop.source_retrieval import section_coverage as SC

    def covered(learning_object_ids: Any) -> dict[str, set[tuple[str, str]]] | None:
        try:
            library = SC.Library(vault, repository)
            out: dict[str, set[tuple[str, str]]] = {}
            for lo_id, entries in SC.standing(vault, repository, library, list(learning_object_ids)).items():
                for (extraction_id, section_id), entry in entries.items():
                    if entry.treatment is None or entry.treatment in SC.ABOUT:
                        out.setdefault(str(lo_id), set()).add((str(extraction_id), str(section_id)))
            return out
        except SC.CoverageError:
            return None

    return covered


def _error(exc: IA.InlineCheckError) -> SidecarError:
    return SidecarError(exc.code, exc.message, details=exc.details or None)


def _refs(repository: Any, refs: Any) -> list[Verbatim]:
    return [Verbatim(ref) for ref in IA.with_measured(repository, refs)]


def _card(vault: Any, repository: Any, admin: dict[str, Any], *, replayed: bool = False) -> dict[str, Any]:
    """The card: what begin froze (the cold presentation, never the item's detail), the veils with what each would
    show measured or not, the reserved submission and the serve-time eligibility."""

    veils = IA.veils(repository, admin["administration_token"])
    return {
        "administration_token": admin["administration_token"], "commitment_id": admin["commitment_id"],
        "item_ref": admin["practice_item_id"], "contract_hash": admin["contract_hash"], "cold": admin["cold"],
        "state": admin["state"], "submission_id": admin.get("submission_id"), "replayed": replayed,
        "eligibility": IA.eligibility_of(vault, repository, admin) if not admin["cold"] else None,
        "revision": veils["revision"],
        "protection": {"veil_set_id": veils["veil_set_id"], "method": veils["method"],
                       "veiled": _refs(repository, veils["veiled"]), "opened": _refs(repository, veils["opened"]),
                       "standing": _refs(repository, veils["standing"]), "groups": veils["groups"]},
        "prompt": Verbatim(admin.get("presentation") or {}),
    }


def _serve(ctx: SidecarContext, session_id: str):
    from learnloop_sidecar.handlers.practice import ServePracticeItemInput, get_practice_item

    def serve(practice_item_id: str) -> dict[str, Any]:
        # Today's own session serve of the item: the contract frozen as Today freezes it, the check's view as Today
        # shows it (no locators until feedback).
        return get_practice_item(ctx, ServePracticeItemInput(practice_item_id=practice_item_id, session_id=session_id))

    return serve


@method("check.begin_inline", BeginInlineInput)
@host_mutation
def check_begin_inline(ctx: SidecarContext, params: BeginInlineInput) -> dict[str, Any]:
    """Open an inline administration; the prompt is in the reply only once the veils are recorded."""

    from learnloop_sidecar.context import session_snapshot
    from learnloop_sidecar.handlers.workbench import _practice_session

    from learnloop_sidecar.handlers.sessions import require_owned_session

    vault, repository = ctx.require_vault()
    try:
        # Refused checks start no session: the lock and the due rule are read before one is resolved. A retried or
        # repeated begin adopts the open administration as it was frozen (nothing is served again).
        standing = IA.preflight(vault, repository, request_id=params.request_id, commitment_id=params.commitment_id)
        if standing is not None:
            return versioned({**_card(vault, repository, standing, replayed=True),
                              "practice_session": session_snapshot(repository, standing["session_id"])})
        session_id = _practice_session(ctx, repository, params.session_id)
        # The answer is written on this session: a session another device holds is refused before the question shows.
        require_owned_session(ctx, repository, session_id)
        opened = IA.begin(vault, repository, request_id=params.request_id, commitment_id=params.commitment_id,
                          session_id=session_id, visible=params.visible.model_dump(),
                          serve=_serve(ctx, session_id), covered=_covered(vault, repository))
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    admin = opened["administration"]
    # The session the answer is recorded on, for the app to adopt when it had none (as a workbench submit's).
    return versioned({**_card(vault, repository, admin, replayed=opened["replayed"]),
                      "practice_session": session_snapshot(repository, admin["session_id"])})


@method("check.protect_more", ProtectMoreInput)
def check_protect_more(ctx: SidecarContext, params: ProtectMoreInput) -> dict[str, Any]:
    """Veil what came into view during the administration: ``{veil_additions}``."""

    vault, repository = ctx.require_vault()
    try:
        result = IA.protect_more(vault, repository, token=params.administration_token,
                                 visible=params.visible.model_dump(), covered=_covered(vault, repository))
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    # The standing set and its revision: a client whose earlier reply was lost still gets every veil.
    return versioned({"veil_additions": _refs(repository, result["additions"]),
                      "standing": _refs(repository, result["standing"]), "revision": result["revision"]})


@method("check.expose", ExposeInput)
def check_expose(ctx: SidecarContext, params: ExposeInput) -> dict[str, Any]:
    """Record an exposure at once: ``{protection_status: {exposure, cold_now}}``."""

    vault, repository = ctx.require_vault()
    try:
        status = IA.expose(vault, repository, token=params.administration_token, ref=params.ref, kind=params.kind,
                           exposure_id=params.exposure_id)
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    return versioned({"protection_status": {"exposure": [Verbatim(event) for event in status["exposure"]],
                                            "cold_now": status["cold_now"], "measured": status["measured"],
                                            "eligibility": status["eligibility"]}})


@method("check.submit_inline", SubmitInlineInput)
@host_mutation
def check_submit_inline(ctx: SidecarContext, params: SubmitInlineInput) -> dict[str, Any]:
    """The attempt through the one attempt service for the frozen item and contract, then settlement: the attempt's
    own reply plus ``{cold, reason}``. Idempotent by ``submission_id`` (a duplicate returns the first result)."""

    from learnloop.attempts.stuck import stuck_attempt_type
    from learnloop_sidecar.handlers.practice import SubmitAttemptInput, submit_attempt_on

    vault, repository = ctx.require_vault()
    try:
        admin = IA.prepare_submit(vault, repository, token=params.administration_token,
                                  submission_id=params.submission_id, veils_revision=params.veils_revision)
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    item = vault.practice_items.get(admin["practice_item_id"])
    if item is None:
        raise SidecarError("not_found", f"Practice item {admin['practice_item_id']} was not found.")
    submission = SubmitAttemptInput(
        session_id=admin["session_id"], practice_item_id=admin["practice_item_id"], answer_md=params.answer_md,
        attempt_type=stuck_attempt_type(item.attempt_types_allowed, hints_used=0),
        assessment_contract_version_id=admin["contract_hash"], latency_seconds=params.latency_seconds,
        active_seconds=params.active_seconds, submission_id=IA.attempt_submission_key(params.submission_id),
        # A note's veil opened during the check: its words cannot be measured (C2), so the answer is declared primed.
        primed=IA.notes_opened(admin), self_grade=params.self_grade)
    # The one submit implementation; help shown on this item in this session is folded in by the server, exactly as
    # on the practice screen (taking help makes the answer assisted).
    reply = submit_attempt_on(ctx, submission, entry_surface=IA.SURFACE, hint_window_fold=True)
    attempt_id = reply.get("attempt_id") or reply.get("attemptId")
    if admin["replayed"] and admin.get("outcome") is not None:
        # The outcome the close promised, never one computed again.
        outcome = dict(admin["outcome"])
    else:
        outcome = IA.finish_submit(vault, repository, token=params.administration_token, attempt_id=str(attempt_id))
        drain_after_check(ctx, vault, repository)
    return {**reply, **to_camel({"cold": outcome["cold"], "reason": outcome["reason"],
                                 "eligibility": outcome.get("eligibility"),
                                 **({"primed_by": outcome["primed_by"]} if outcome.get("primed_by") else {}),
                                 "administration_token": params.administration_token})}


@method("check.abandon_inline", TokenInput)
def check_abandon_inline(ctx: SidecarContext, params: TokenInput) -> dict[str, Any]:
    """"Not now": closed with no attempt; the duty stays pending."""

    vault, repository = ctx.require_vault()
    try:
        IA.abandon(vault, repository, token=params.administration_token)
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    drain_after_check(ctx, vault, repository)
    return versioned({})


class OpenInlineInput(ParamsModel):
    pass


@method("check.open_inline", OpenInlineInput)
def check_open_inline(ctx: SidecarContext, params: OpenInlineInput) -> dict[str, Any]:
    """The restart read: the open administration with its veils and prompt, or ``administration: null``. One whose
    answer reached the attempt service before a crash is closed with it; one whose check was settled elsewhere is
    closed superseded."""

    vault, repository = ctx.require_vault()

    def attempt_for(session_id: str, key: str) -> str | None:
        row = repository.practice_attempt_by_submission_id(key)
        return str(row["id"]) if row is not None else None

    try:
        admin = IA.reopen(vault, repository, attempt_for=attempt_for)
    except IA.InlineCheckError as exc:
        raise _error(exc) from exc
    if admin is None:
        drain_after_check(ctx, vault, repository)
        return versioned({"administration": None})
    # The card as begin froze it: the item is not served again.
    return versioned({"administration": _card(vault, repository, admin)})


__all__ = ["INLINE_CHECK_RPCS"]
