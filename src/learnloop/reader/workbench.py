"""Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1 §5.1, §5.4, §5.7).

A problem is worked in steps, beside the source in the Reader or full width on
the practice screen. This module is the workbench's state and its one rule
about evidence; the sidecar handler (``learnloop_sidecar.handlers.workbench``)
is the adapter around it, and it submits through the ordinary attempt path.

Functional core, imperative shell:

* the pure part decides the default book visibility for an entry
  (:func:`default_book_visible`, UX S7 / D9), folds the append-only step rows
  into the work as it stands (:func:`live_steps`), composes the answer a submit
  sends (:func:`compose_answer`), and states what the attempt will record
  (:func:`record_line`);
* the shell writes sessions and steps in one transaction each, with a
  salience-only ``reader_action_invoked`` event (payload ``event``) for every
  lifecycle change, so no new event kind and no new reveal kind exist.

**What a session records** (§5.4; confirmed against
``resolve_attempt_activity_policy``). The only evidence a session produces is
its submitted attempt. In the Reader the book counts as one hint-equivalent
from the first step written with it shown, or from its first showing after a
step (``source_shown_at``); flipping it before the first step is free. Every
showing records an exposure of the problem's anchored spans
(``source_exposure_events``, context ``reader``), as opening the source does.
Hints the learner revealed on the practice screen's answer box before working
in steps (``carried_hints``) count too, and both survive a move to another
surface. A book counted in a session the learner left for the answer box
goes with them (the answer box counts it) and comes back into steps as a
counted book (``carried_book``), so neither direction drops it. The submit
therefore sends ``hints_used`` = the book's one plus the
carried hints and nothing else new: any of them makes the attempt assisted
(FSRS-fed, certifying nothing); none leaves it the learner's own. The server
holds this, not the client: every submit for the item, the answer box's
included, records at least what its open problems hold (:func:`held_hints`,
the larger of that and what the client sent, never their sum), and an
independent attempt type becomes the assisted one (review F2). It is graded
against the assessment contract the session showed
(``assessment_contract_version_id``), and answers the serve it was opened
from (``scheduler_candidate_id``, ``plan_presentation_id``), kept across a
resume. Stuck steps stay learner work and are
left out of the answer; with no ordinary step the stuck text (or an empty box)
is the existing "I'm stuck" answer. Abandoned sessions write no attempt.
Replay and rebuild never read the workbench tables (an import-linter contract
keeps evidence code from importing this module).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.stores import help_assists as assists_store
from learnloop.db.stores import workbench as store
from learnloop.db.stores.help_assists import WorkbenchFold
from learnloop.ids import new_ulid
from learnloop.substrate.activities import log_interaction_event

WORKBENCH_VERSION = "rw2a-scratchpad-v1"

ORIGINS: tuple[str, ...] = ("reader", "practice", "plan")
#: How a session was opened (spec §5.7): it sets the default book visibility.
ENTRIES: tuple[str, ...] = (
    "work_through", "resume", "check_me", "practice_this", "path_exercise",
    "discriminating_problem", "practice_screen", "plan",
)
STATUSES: tuple[str, ...] = ("open", "submitted", "abandoned")
IMPORT_STATUSES: tuple[str, ...] = ("none", "pending", "bound", "failed")
STEP_KINDS: tuple[str, ...] = ("step", "stuck")
HELP_STYLES: tuple[str, ...] = ("let_me_struggle", "balanced", "guide_me")
STEP_OPS: tuple[str, ...] = ("add", "edit", "delete", "restore")

#: Entries that open WITH the book: working through the book's own problem,
#: resuming, and the Guide's exercise. The entries that exist to test ("check
#: me", "practice this question", "a short problem instead", plan items) open
#: without it (UX S7, D9). Off the Reader there is no source pane at all.
BOOK_OPEN_ENTRIES: frozenset[str] = frozenset({"work_through", "resume", "path_exercise"})

#: ``practice_attempts.entry_surface`` for a workbench submit.
ENTRY_SURFACE_READER = "desktop_reader_workbench"
ENTRY_SURFACE_PRACTICE = "desktop_practice_workbench"

#: Every payload ``event`` the workbench writes on ``reader_action_invoked``.
SERVER_WORKBENCH_EVENTS: tuple[str, ...] = (
    "workbench_opened", "workbench_resumed", "workbench_left", "workbench_closed",
    "workbench_reopened", "workbench_bound", "book_visibility_changed",
)
#: RW2b's payload ``event`` values on ``reader_action_invoked``: the rung the
#: ladder suggested when Help opened (the Reader's fallback progression reads
#: it) and the header's help style. Salience only, like RW2a's.
HELP_WORKBENCH_EVENTS: tuple[str, ...] = ("workbench_help_offered", "help_style_changed")
SUBJECT_TYPE = "workbench_session"

#: The submit line before an empty "stuck" answer (spec §5.1, UX §5.10).
STUCK_NOTE = "Submitting now records 'stuck' — that's fine"
OWN_ATTEMPT_LINE = "your own attempt"

MAX_STEM_CHARS = 20_000
MAX_STEP_CHARS = 20_000


class WorkbenchError(ValueError):
    """A refused workbench request (nothing was written)."""

    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def workbench_enabled(vault: Any) -> bool:
    """RW2a's kill switch (``workbench.enabled``, default on)."""

    section = getattr(vault.config, "workbench", None)
    return bool(getattr(section, "enabled", True))


def open_session_days(vault: Any) -> int:
    section = getattr(vault.config, "workbench", None)
    return int(getattr(section, "open_session_days", 30) or 30)


# ---------------------------------------------------------------------------
# The pure core
# ---------------------------------------------------------------------------

def default_book_visible(entry: str, origin: str) -> bool:
    """Whether a new session starts with the book shown (UX S7, D9)."""

    return origin == "reader" and entry in BOOK_OPEN_ENTRIES


@dataclass(frozen=True)
class ComposedAnswer:
    """What a submit sends: the ordinary steps in order, or "I'm stuck"."""

    answer_md: str
    declared_stuck: bool

    @property
    def empty_stuck(self) -> bool:
        return self.declared_stuck and not self.answer_md


def _chains(rows: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]:
    """Each step's versions, oldest first (rows are append-only, linear chains)."""

    by_id = {row["id"]: row for row in rows}
    superseded = {row["supersedes_id"] for row in rows if row.get("supersedes_id")}
    chains: list[list[Mapping[str, Any]]] = []
    for head in rows:
        if head["id"] in superseded:
            continue
        chain = [head]
        seen = {head["id"]}
        while chain[-1].get("supersedes_id") in by_id and chain[-1]["supersedes_id"] not in seen:
            seen.add(chain[-1]["supersedes_id"])
            chain.append(by_id[chain[-1]["supersedes_id"]])
        chains.append(list(reversed(chain)))
    return chains


def _step_payload(chain: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    head = chain[-1]
    root = chain[0]
    earlier: list[dict[str, Any]] = []
    seen_bodies = {head["body_md"]}
    for row in reversed(chain[:-1]):
        if row["deleted"] or row["body_md"] in seen_bodies:
            continue
        seen_bodies.add(row["body_md"])
        earlier.append({"step_id": row["id"], "body_md": row["body_md"], "created_at": row["created_at"]})
    return {
        "step_id": head["id"],
        "chain_id": root["id"],
        "ordinal": float(root["ordinal"]),
        "kind": head["kind"],
        "body_md": head["body_md"],
        "deleted": bool(head["deleted"]),
        "created_at": root["created_at"],
        "edited_at": head["created_at"],
        "versions": earlier,
    }


def live_steps(rows: Sequence[Mapping[str, Any]], *, include_deleted: bool = False) -> list[dict[str, Any]]:
    """The work as it stands: each step's newest version, in list order."""

    steps = [_step_payload(chain) for chain in _chains(rows)]
    if not include_deleted:
        steps = [step for step in steps if not step["deleted"]]
    return sorted(steps, key=lambda step: (step["ordinal"], step["created_at"], step["chain_id"]))


def compose_answer(steps: Iterable[Mapping[str, Any]]) -> ComposedAnswer:
    """The answer a submit sends (spec §5.1): the live ``step`` bodies in
    order, stuck steps and tombstones left out. With no ordinary step, the
    stuck text is the existing written "I'm stuck" answer, and nothing at all
    is the existing empty one (scored 0 with no model call)."""

    live = [step for step in steps if not step.get("deleted")]
    work = [str(step["body_md"]).strip() for step in live if step["kind"] == "step" and str(step["body_md"]).strip()]
    if work:
        return ComposedAnswer(answer_md="\n\n".join(work), declared_stuck=False)
    stuck = [str(step["body_md"]).strip() for step in live if step["kind"] == "stuck" and str(step["body_md"]).strip()]
    return ComposedAnswer(answer_md="\n\n".join(stuck), declared_stuck=True)


def book_counted(session: Mapping[str, Any]) -> bool:
    """Whether the book counts as one hint-equivalent on the submitted attempt.

    Once counted (``source_shown_at``) it stays counted, on any surface the
    session moves to; a book shown now counts only in the Reader, where there
    is one."""

    if session.get("source_shown_at"):
        return True
    return session.get("origin") == "reader" and bool(session.get("source_visible"))


def book_hints(session: Mapping[str, Any]) -> int:
    return 1 if book_counted(session) else 0


def carried_hints(session: Mapping[str, Any]) -> int:
    """The answer box's hints the learner saw before working in steps."""

    return max(0, int(session.get("carried_hints") or 0))


def session_hints(session: Mapping[str, Any]) -> int:
    """Every hint-equivalent the session itself holds (the submit's ``hints_used``)."""

    return book_hints(session) + carried_hints(session)


def _help_parts(fold: WorkbenchFold) -> list[str]:
    """The workbench's own assists in plain words (UX §5.5, §5.9; G62)."""

    parts: list[str] = []
    if fold.checks:
        parts.append("a check" if fold.checks == 1 else f"{fold.checks} checks")
    for level, count in zip((1, 2, 3), fold.by_level):
        if count:
            noun = {1: "question", 2: "pointer", 3: "hint"}[level]
            parts.append(f"a level-{level} {noun}" if count == 1 else f"{count} level-{level} {noun}s")
    if fold.worked:
        parts.append("worked help ◌" if fold.worked == 1 else f"{fold.worked} worked pieces ◌")
    return parts


def record_line(
    *, counted: bool, visible: bool, question_hints: int, composed: ComposedAnswer, carried: int = 0,
    help_fold: WorkbenchFold | None = None,
) -> dict[str, Any]:
    """What the attempt will record, stated before Submit (spec §5.1, G62).

    Every assist the submit counts is named here: in RW2a the book, the
    answer box's hints shown before steps, and the tutor questions the
    existing fold adds; from RW2b each shown check and hint of the problem
    (``help_fold``, the very count the submit reads), and worked help as
    *practice with help ◌* through ``primed``. It never promises a later
    check. With no workbench help the line and its keys are RW2a's.
    """

    question_hints = max(0, int(question_hints or 0))
    carried = max(0, int(carried or 0))
    fold = help_fold if help_fold is not None and not help_fold.empty else None
    helped = fold.hints if fold is not None else 0
    hints = (1 if counted else 0) + carried + question_hints + helped
    parts = (
        (["the book"] if counted else [])
        + ([f"{carried} shown on the answer box"] if carried else [])
        + ([f"{question_hints} tutor question{'s' if question_hints != 1 else ''}"] if question_hints else [])
        + ([part for part in _help_parts(fold) if "◌" not in part] if fold is not None else [])
    )
    worked = fold is not None and fold.primed
    if hints == 0 and not worked:
        line = OWN_ATTEMPT_LINE
    else:
        noun = f"{hints} hint{'s' if hints != 1 else ''}"
        what = f" ({', '.join(parts)})" if len(parts) > 1 or not counted else ""
        lead = "book open · " if counted else ""
        if worked:
            noun = f"{noun} and worked help" if hints else "worked help"
            what = f" ({', '.join(parts)})" if parts and (len(parts) > 1 or not counted) else ""
        line = f"{lead}{noun}{what} → practice with help ◌ (not yet checked on your own)"
    used = ([f"{carried} hint{'s' if carried != 1 else ''}"] if carried else []) + (
        _help_parts(fold) if fold is not None else [])
    help_used = ", ".join(used) if used else "none"
    footer = ("book open = 1 hint" if counted else "book hidden" if not visible else "book open") + f" · help used: {help_used}"
    if fold is not None:
        return {
            "book_counted": counted, "book_visible": visible, "hints": hints, "question_hints": question_hints,
            "carried_hints": carried, "own_attempt": False, "line": line, "footer": footer,
            "stuck_note": STUCK_NOTE if composed.empty_stuck else None,
            # RW2b: the problem's own assists (only when it has any).
            "help": {"checks": fold.checks, "by_level": list(fold.by_level), "worked": fold.worked,
                     "primed": fold.primed},
        }
    return {
        "book_counted": counted,
        "book_visible": visible,
        "hints": hints,
        "question_hints": question_hints,
        "carried_hints": carried,
        "own_attempt": hints == 0,
        "line": line,
        "footer": footer,
        "stuck_note": STUCK_NOTE if composed.empty_stuck else None,
    }


# ---------------------------------------------------------------------------
# The shell: sessions and steps
# ---------------------------------------------------------------------------

def _spans(session: Mapping[str, Any]) -> list[str]:
    try:
        value = json.loads(session.get("span_ids_json") or "[]")
    except (TypeError, ValueError):
        return []
    return [str(span) for span in value] if isinstance(value, list) else []


def _log(repository: Any, session: Mapping[str, Any], event: str, clock: Clock | None = None, **extra: Any) -> str:
    spans = _spans(session)
    return log_interaction_event(
        repository,
        kind="reader_action_invoked",
        origin="learner",
        subject_type=SUBJECT_TYPE,
        subject_id=str(session["id"]),
        payload=salience_payload({
            "event": event,
            "workbench_session_id": session["id"],
            "workbench_version": WORKBENCH_VERSION,
            "origin": session.get("origin"),
            "entry": session.get("entry"),
            "practice_item_id": session.get("practice_item_id"),
            "extraction_id": session.get("extraction_id"),
            "span_id": spans[0] if spans else None,
            **extra,
        }),
        clock=clock,
    )


def _require(connection: Any, session_id: str) -> dict[str, Any]:
    session = store.fetch_session(connection, session_id)
    if session is None:
        raise WorkbenchError("not_found", f"No workbench session {session_id!r}.")
    return session


def _require_open(session: Mapping[str, Any]) -> None:
    if session["status"] == "submitted":
        raise WorkbenchError(
            "already_submitted", "This problem was submitted.", {"attempt_id": session.get("attempt_id")}
        )
    if session["status"] != "open":
        raise WorkbenchError("not_open", "This problem is set aside. Reopen it to keep working.")


def session_row(repository: Any, session_id: str) -> dict[str, Any]:
    with repository.connection() as connection:
        return _require(connection, session_id)


def resumable_session(
    repository: Any,
    *,
    practice_item_id: str | None = None,
    extraction_id: str | None = None,
    span_ids: Sequence[str] = (),
    stem_md: str | None = None,
) -> dict[str, Any] | None:
    """The open session an "open" would resume: the item's, else the same
    selection's (so a second "work through this" never starts a second one)."""

    with repository.connection() as connection:
        if practice_item_id:
            return store.open_session_for_item(connection, practice_item_id)
        if extraction_id and stem_md:
            return store.open_session_for_selection(
                connection, extraction_id=extraction_id, span_ids_json=json.dumps(list(span_ids)),
                stem_md=stem_md.strip(),
            )
    return None


def _record_book_exposure(repository: Any, session: Mapping[str, Any], clock: Clock | None = None) -> list[str]:
    """The book shown beside the problem exposes its anchored spans (spec §5.4,
    G10): one ``source_exposure_events`` row per span, context ``reader``, as
    opening the source records today. Nothing without a Reader anchor."""

    extraction_id = session.get("extraction_id")
    spans = _spans(session)
    if session.get("origin") != "reader" or not extraction_id or not spans:
        return []
    from learnloop.ingest.locators import format_block_span

    revision_id = source_id = None
    ir = None
    try:
        run = repository.get_extraction_run(extraction_id)
        revision_id = run.get("revision_id") if run else None
        revision = repository.get_source_revision(revision_id) if revision_id else None
        source_id = revision.get("source_id") if revision else None
        ir = repository.load_document_ir(extraction_id) if run else None
    except Exception:  # noqa: BLE001 - an unreadable extraction still records the span it showed
        ir = None
    item = session.get("practice_item_id")
    ids = []
    for span in spans:
        block = ir.block_by_span(span) if ir is not None else None
        ids.append(repository.insert_source_exposure_event({
            "context": "reader",
            "extraction_id": extraction_id,
            "span_id": span,
            "revision_id": revision_id,
            "source_id": source_id,
            "entity_type": "practice_item" if item else SUBJECT_TYPE,
            "entity_id": item or session["id"],
            "page": getattr(block, "page", None),
            "locator": format_block_span(extraction_id, span),
            "section_path": list(getattr(block, "section_path", None) or []),
        }, clock=clock))
    return ids


SERVE_COLUMNS: tuple[str, ...] = ("scheduler_candidate_id", "plan_presentation_id")


def _serve_changes(serve: Mapping[str, str | None] | None) -> dict[str, Any]:
    """The serve a request names, to store on the session (review F13, F15).

    A serve is one pair: a request names none (``None``: the rail, the ``✎``
    mark, a resume that knows nothing of the serve), which keeps the pair the
    session holds, or it names a replacement, which replaces both identifiers
    together, an explicit null included. Never one of each: a new candidate
    beside the previous plan presentation would credit that plan with an
    answer to a serve it did not make."""

    if serve is None:
        return {}
    return {column: (str(serve[column]) if serve.get(column) else None) for column in SERVE_COLUMNS}


def held_parts_on(connection: Any, practice_item_id: str) -> tuple[tuple[tuple[int, int, tuple[str, ...]], ...], bool]:
    """The help each of the item's open problems holds, read on
    ``connection`` (a submit's own write transaction may pass its connection:
    RW2b fix round 1, F1), kept in its parts (fix round 5, items 4-5):
    ``(book, carried, assist_ids)``, where ``book`` is 1 when the problem
    counted the book, ``carried`` the answer-box hints carried into its steps
    (authored reveals a client may send too) and ``assist_ids`` the ids of
    its shown checks and level 1-3 hints (no client holds them); and whether
    any problem showed worked help (a level 4-5 hint). The submit joins them
    with the client's counts by ``learnloop.attempts.hint_fold.combine_held``."""

    sessions = store.sessions_where(
        connection, column="practice_item_id", value=practice_item_id, statuses=("open",),
    )
    # RW2b: the problem's shown checks and hints count too, so a submit
    # from the answer box records the help the open problem holds.
    folds = {session["id"]: assists_store.workbench_fold(connection, workbench_session_id=session["id"],
                                                         practice_item_id=practice_item_id)
             for session in sessions}
    parts = tuple((book_hints(session), carried_hints(session),
                   assists_store.workbench_assist_ids(connection, workbench_session_id=session["id"],
                                                      practice_item_id=practice_item_id))
                  for session in sessions)
    return parts, any(fold.primed for fold in folds.values())


def held_on(connection: Any, practice_item_id: str) -> tuple[int, bool]:
    """The help the item's open problems hold (:func:`held_parts_on`): the
    largest hint-equivalents one problem holds (its book, carried hints,
    shown checks and level 1-3 hints) and whether any showed worked help."""

    parts, primed = held_parts_on(connection, practice_item_id)
    return max((book + carried + len(ids) for book, carried, ids in parts), default=0), primed


def held_hints(repository: Any, practice_item_id: str) -> int:
    """The hint-equivalents the item's open problems hold (review F2): the
    book one counted and the answer-box hints it carried. Every submit for the
    item folds this in (the larger of it and what the client sent), so the
    record never depends on a client having restored it first, and nothing
    clamps it to the hints the item shows today."""

    with repository.connection() as connection:
        return held_on(connection, practice_item_id)[0]


def held_primed(repository: Any, practice_item_id: str) -> bool:
    """Whether an open problem of the item showed worked help (a level 4-5
    hint): every submit for the item is then primed (RW2b, §5.4)."""

    with repository.connection() as connection:
        return held_on(connection, practice_item_id)[1]


def _resume_existing(
    repository: Any,
    connection: Any,
    existing: Mapping[str, Any],
    *,
    origin: str,
    entry: str,
    extraction_id: str | None,
    span_ids: Sequence[str],
    source_visible: bool | None,
    carried: int,
    now: str,
    clock: Clock | None,
    carried_book: bool = False,
    serve: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    """Resume an existing session on the surface asking for it.

    A move between the Reader and the practice screen (or plan) is explicit:
    the session takes the new ``origin`` (so the submit records the surface it
    is sent from); into the Reader it gains the Reader's anchors when it had
    none and opens with the book only if no step was written yet (the
    entry's default, UX S7), so work written without the book stays the
    learner's own until they choose to show it; out of the Reader there is no
    book. The book once counted, and the carried hints, stay counted.
    "Check me" always opens with the book hidden, on any surface it comes
    from (UX S7), keeping whatever the book already counted. A serve the
    resume names (its scheduler offer, its plan presentation) replaces the
    pair kept, both identifiers together; a resume that names none keeps it.
    """

    changes: dict[str, Any] = {"updated_at": now}
    if carried > carried_hints(existing):
        changes["carried_hints"] = carried
    if carried_book and not existing.get("source_shown_at"):
        changes["source_shown_at"] = now
    changes.update(_serve_changes(serve))
    moved_from = None
    becomes_visible = False
    if (existing["origin"] == "reader") != (origin == "reader"):
        moved_from = existing["origin"]
        changes["origin"] = origin
        if origin == "reader":
            if not existing.get("extraction_id") and extraction_id:
                changes["extraction_id"] = extraction_id
                changes["span_ids_json"] = json.dumps([str(span) for span in span_ids])
            has_work = bool(store.steps_for_session(connection, existing["id"]))
            wanted = default_book_visible(entry, origin) if source_visible is None else bool(source_visible)
            becomes_visible = wanted and not has_work
            changes["source_visible"] = 1 if becomes_visible else 0
        else:
            changes["source_visible"] = 0
    elif origin != existing["origin"]:
        # Practice screen and plan: the same surface, no book.
        changes["origin"] = origin
    if entry == "check_me" and (changes.get("source_visible", existing["source_visible"])):
        # A check is the learner's own retrieval: the book starts hidden even
        # on a problem left with it open (review F14).
        changes["source_visible"] = 0
        changes["source_hidden_at"] = now
        becomes_visible = False
    store.update_session(connection, existing["id"], changes)
    row = _require(connection, existing["id"])
    _log(repository, row, "workbench_resumed", clock, via=entry,
         **({"moved_from": moved_from, "book_visible": bool(row["source_visible"])} if moved_from else {}))
    if becomes_visible:
        _record_book_exposure(repository, row, clock)
    return row


def open_session(
    repository: Any,
    *,
    origin: str,
    entry: str,
    stem_md: str,
    practice_item_id: str | None = None,
    extraction_id: str | None = None,
    span_ids: Sequence[str] = (),
    parent_session_id: str | None = None,
    source_visible: bool | None = None,
    client_idempotency_key: str | None = None,
    import_status: str = "none",
    import_batch_id: str | None = None,
    import_request: Mapping[str, Any] | None = None,
    import_error: str | None = None,
    carried: int = 0,
    carried_book: bool = False,
    serve: Mapping[str, str | None] | None = None,
    clock: Clock | None = None,
) -> tuple[dict[str, Any], bool]:
    """Open a session (or resume the open one for the same item or selection).

    Returns ``(session row, resumed)``. A retried request with the same key
    answers the session it made. A resumed session on another surface moves
    to it (:func:`_resume_existing`); ``carried`` is the answer box's hints
    shown before steps, kept at the highest count seen; ``carried_book`` a
    book a session the learner left for the answer box counted, which this
    session counts too. ``serve`` names the scheduler offer and the plan
    presentation the problem answers.
    """

    if origin not in ORIGINS:
        raise WorkbenchError("validation_error", f"unknown workbench origin {origin!r}")
    if entry not in ENTRIES:
        raise WorkbenchError("validation_error", f"unknown workbench entry {entry!r}")
    if import_status not in IMPORT_STATUSES or import_status == "bound":
        raise WorkbenchError("validation_error", f"a session cannot open with import status {import_status!r}")
    stem = (stem_md or "").strip()
    if not stem:
        raise WorkbenchError("validation_error", "A workbench problem needs its stem.")
    if len(stem) > MAX_STEM_CHARS:
        raise WorkbenchError("validation_error", "The problem's text is too long for the workbench.")
    if not practice_item_id and import_status == "none":
        raise WorkbenchError("validation_error", "A problem that is not an item yet needs its import.")
    now = utc_now_iso(clock)
    spans = [str(span) for span in span_ids]
    with repository.atomic():
        connection = repository.connection()
        if client_idempotency_key:
            existing = store.session_by_key(connection, client_idempotency_key)
            if existing is not None:
                return existing, False
        if practice_item_id:
            existing = store.open_session_for_item(connection, practice_item_id)
        elif extraction_id:
            existing = store.open_session_for_selection(
                connection, extraction_id=extraction_id, span_ids_json=json.dumps(spans), stem_md=stem,
            )
        else:
            existing = None
        if existing is not None:
            row = _resume_existing(
                repository, connection, existing, origin=origin, entry=entry, extraction_id=extraction_id,
                span_ids=spans, source_visible=source_visible, carried=carried, now=now, clock=clock,
                carried_book=carried_book, serve=serve,
            )
            return row, True
        if parent_session_id is not None:
            _require(connection, parent_session_id)
        visible = default_book_visible(entry, origin) if source_visible is None else bool(source_visible)
        session = {
            "id": new_ulid(),
            "practice_item_id": practice_item_id,
            "stem_md": stem,
            "import_status": import_status,
            "import_batch_id": import_batch_id,
            "import_request_json": json.dumps(dict(import_request), sort_keys=True) if import_request else None,
            "import_error": import_error,
            "origin": origin,
            "entry": entry,
            "parent_session_id": parent_session_id,
            "extraction_id": extraction_id,
            "span_ids_json": json.dumps(spans),
            "source_visible": 1 if visible and origin == "reader" else 0,
            "carried_hints": max(0, int(carried or 0)),
            "source_shown_at": now if carried_book else None,
            **_serve_changes(serve),
            "status": "open",
            "client_idempotency_key": client_idempotency_key,
            "created_at": now,
            "updated_at": now,
        }
        store.insert_session(connection, session)
        row = _require(connection, session["id"])
        _log(repository, row, "workbench_opened", clock, book_visible=bool(row["source_visible"]),
             import_status=import_status)
        if row["source_visible"]:
            _record_book_exposure(repository, row, clock)
    return row, False


def resume_session(
    repository: Any,
    session_id: str,
    *,
    origin: str,
    entry: str = "resume",
    extraction_id: str | None = None,
    span_ids: Sequence[str] = (),
    carried: int = 0,
    carried_book: bool = False,
    serve: Mapping[str, str | None] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Resume a named session on the surface asking ("resume your steps", the
    ``✎`` mark, the rail): an abandoned one is reopened, and a move to another
    surface is the same explicit transition :func:`open_session` makes."""

    if origin not in ORIGINS:
        raise WorkbenchError("validation_error", f"unknown workbench origin {origin!r}")
    if entry not in ENTRIES:
        raise WorkbenchError("validation_error", f"unknown workbench entry {entry!r}")
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "submitted":
            raise WorkbenchError(
                "already_submitted", "This problem was submitted.", {"attempt_id": session.get("attempt_id")}
            )
        if session["status"] == "abandoned":
            store.update_session(connection, session_id, {"status": "open", "closed_at": None, "updated_at": now})
            session = _require(connection, session_id)
            _log(repository, session, "workbench_reopened", clock)
        return _resume_existing(
            repository, connection, session, origin=origin, entry=entry, extraction_id=extraction_id,
            span_ids=[str(span) for span in span_ids], source_visible=None, carried=carried, now=now, clock=clock,
            carried_book=carried_book, serve=serve,
        )


def _ordinal_after(live: Sequence[Mapping[str, Any]], after: Mapping[str, Any] | None) -> float:
    ordinals = sorted(float(step["ordinal"]) for step in live)
    if after is None:
        return (ordinals[-1] + 1.0) if ordinals else 1.0
    anchor = float(after["ordinal"])
    later = [value for value in ordinals if value > anchor]
    return (anchor + later[0]) / 2.0 if later else anchor + 1.0


def save_step(
    repository: Any,
    session_id: str,
    *,
    op: str,
    client_idempotency_key: str,
    step_id: str | None = None,
    after_step_id: str | None = None,
    kind: str = "step",
    body_md: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Save one change to the work, as typed (spec §5.1).

    ``add`` writes a new step after ``after_step_id`` (or at the end); ``edit``
    a new version superseding the newest version of the step's chain;
    ``delete`` a tombstone; ``restore`` undoes it. A retried write with the
    same key writes nothing and answers the row it wrote. Returns the step's
    newest version.
    """

    if op not in STEP_OPS:
        raise WorkbenchError("validation_error", f"unknown step operation {op!r}")
    key = (client_idempotency_key or "").strip()
    if not key:
        raise WorkbenchError("validation_error", "A step write needs its idempotency key.")
    if body_md is not None and len(body_md) > MAX_STEP_CHARS:
        raise WorkbenchError("validation_error", "This step is too long to save.")
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        _require_open(session)
        prior = store.step_by_key(connection, session_id, key)
        rows = store.steps_for_session(connection, session_id)
        if prior is not None:
            chain = next(chain for chain in _chains(rows) if any(row["id"] == prior["id"] for row in chain))
            return _step_payload(chain)
        chains = _chains(rows)
        chain_of = {row["id"]: chain for chain in chains for row in chain}
        live = live_steps(rows)
        values: dict[str, Any] | None
        if op == "add":
            if kind not in STEP_KINDS:
                raise WorkbenchError("validation_error", f"unknown step kind {kind!r}")
            after = chain_of[after_step_id][0] if after_step_id in chain_of else None
            if after_step_id and after is None:
                raise WorkbenchError("not_found", f"No step {after_step_id!r} in this problem.")
            values = {"ordinal": _ordinal_after(live, after), "kind": kind, "body_md": body_md or "",
                      "supersedes_id": None, "deleted": 0}
        else:
            chain = chain_of.get(step_id or "")
            if chain is None:
                raise WorkbenchError("not_found", f"No step {step_id!r} in this problem.")
            head = chain[-1]
            if op == "edit":
                if head["deleted"]:
                    raise WorkbenchError("not_found", "This step was deleted; undo the delete to edit it.")
                body = body_md if body_md is not None else head["body_md"]
                values = None if body == head["body_md"] else {"body_md": body, "deleted": 0}
            elif op == "delete":
                values = None if head["deleted"] else {"body_md": head["body_md"], "deleted": 1}
            else:
                values = None if not head["deleted"] else {"body_md": head["body_md"], "deleted": 0}
            if values is None:
                return _step_payload(chain)
            values.update(ordinal=head["ordinal"], kind=head["kind"], supersedes_id=head["id"])
        step = {"id": new_ulid(), "session_id": session_id, "client_idempotency_key": key, "created_at": now, **values}
        store.insert_step(connection, step)
        changes: dict[str, Any] = {"updated_at": now}
        if session["origin"] == "reader" and session["source_visible"] and not session["source_shown_at"]:
            # The first step written with the book shown: it counts from now.
            changes["source_shown_at"] = now
        store.update_session(connection, session_id, changes)
        rows = store.steps_for_session(connection, session_id)
        chain = next(chain for chain in _chains(rows) if chain[-1]["id"] == step["id"])
    return _step_payload(chain)


def set_book(repository: Any, session_id: str, visible: bool, *, clock: Clock | None = None) -> dict[str, Any]:
    """Show or hide the book (``Ctrl+Shift+B``). Before the first step this is
    free; after it, a showing counts the book from then on (spec §5.4)."""

    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        _require_open(session)
        if session["origin"] != "reader":
            raise WorkbenchError("no_book", "Off the Reader there is no book beside the problem.")
        if bool(session["source_visible"]) == bool(visible):
            return session
        has_work = bool(store.steps_for_session(connection, session_id))
        changes: dict[str, Any] = {"source_visible": 1 if visible else 0, "updated_at": now}
        if visible and has_work and not session["source_shown_at"]:
            changes["source_shown_at"] = now
        if not visible:
            changes["source_hidden_at"] = now
        store.update_session(connection, session_id, changes)
        session = _require(connection, session_id)
        _log(repository, session, "book_visibility_changed", clock, visible=bool(visible),
             counts=book_counted(session), after_first_step=has_work)
        if visible:
            _record_book_exposure(repository, session, clock)
    return session


def leave(repository: Any, session_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """"Leave for now" (``Esc`` twice, navigating away, a restart): the session stays open."""

    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "open":
            _log(repository, session, "workbench_left", clock)
    return session


def abandon(repository: Any, session_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """Close the problem at once, steps kept; reversible by :func:`reopen` (UX S13)."""

    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "abandoned":
            return session
        _require_open(session)
        store.update_session(connection, session_id, {"status": "abandoned", "closed_at": now, "updated_at": now})
        session = _require(connection, session_id)
        _log(repository, session, "workbench_closed", clock, reason="abandoned")
    return session


def reopen(repository: Any, session_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """An abandoned session back to ``open`` (it never wrote an attempt)."""

    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "submitted":
            raise WorkbenchError(
                "already_submitted", "This problem was submitted.", {"attempt_id": session.get("attempt_id")}
            )
        if session["status"] == "open":
            return session
        store.update_session(connection, session_id, {"status": "open", "closed_at": None, "updated_at": now})
        session = _require(connection, session_id)
        _log(repository, session, "workbench_reopened", clock)
    return session


def import_request(session: Mapping[str, Any]) -> dict[str, Any] | None:
    raw = session.get("import_request_json")
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


# -- Reader RW4b: a textbook exercise the learner picked ("use this one") ------------------------------

#: The record a problem opened from a textbook exercise the learner picked in
#: the Reader keeps inside its stored import request (Reader RW4b, spec §7.4;
#: Codex review F2): the proposal it came from (None for the fallback's), the
#: exercise's region, the exposure the server read when it was chosen and when
#: it was admitted, and ``admitted_at``, set only once the learner pick of the
#: item the import wrote was delivered. Durable, so a restart or a resume
#: elsewhere still owes (and never repeats) that pick; no new column.
EXERCISE_PICK_KEY = "reader_exercise"
#: The payload ``event`` RW4b adds on ``reader_action_invoked`` (salience only).
EXERCISE_WORKBENCH_EVENTS: tuple[str, ...] = ("workbench_exercise_admitted",)


def exercise_pick(session: Mapping[str, Any]) -> dict[str, Any] | None:
    """The picked exercise's record, or None for every other problem."""

    value = (import_request(session) or {}).get(EXERCISE_PICK_KEY)
    return dict(value) if isinstance(value, dict) else None


def exercise_pick_due(session: Mapping[str, Any]) -> bool:
    """The import bound the problem to the item it wrote and the learner pick
    of that item was not delivered yet: the shell owes it, once."""

    pick = exercise_pick(session)
    return bool(
        pick is not None and not pick.get("admitted_at") and session.get("import_status") == "bound"
        and session.get("practice_item_id") and session.get("status") == "open"
    )


def admit_exercise_pick(
    repository: Any,
    session_id: str,
    *,
    practice_item_id: str,
    exposure: Mapping[str, Any] | None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record that the learner pick of the exercise's item was delivered, with
    the exposure read again at that moment. Idempotent: a problem admitted
    already, one bound to another item, or one that is no exercise is left
    as it is."""

    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        request = import_request(session) or {}
        pick = request.get(EXERCISE_PICK_KEY)
        if (not isinstance(pick, dict) or pick.get("admitted_at") or session.get("import_status") != "bound"
                or session.get("practice_item_id") != practice_item_id):
            return session
        updated = {**pick, "admitted_at": now}
        if exposure is not None:
            updated.update(exposure=dict(exposure), exposure_checked="admission")
        request[EXERCISE_PICK_KEY] = updated
        store.update_session(connection, session_id, {"import_request_json": json.dumps(request, sort_keys=True)})
        session = _require(connection, session_id)
        _log(repository, session, "workbench_exercise_admitted", clock,
             exposed=bool((exposure or {}).get("exposed")))
    return session


def mark_import(
    repository: Any,
    session_id: str,
    *,
    status: str,
    batch_id: str | None = None,
    error: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the import's progress: ``pending`` on a batch, or ``failed``."""

    if status not in ("pending", "failed"):
        raise WorkbenchError("validation_error", f"an import is marked pending or failed, not {status!r}")
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        # A bound import keeps its binding, and a problem opened on an item
        # ("none") never becomes an import: its item binding is fixed for
        # good, which the hints report relies on (adaptive hints H0, review
        # round 5).
        if session["import_status"] in ("bound", "none"):
            return session
        changes: dict[str, Any] = {"import_status": status, "updated_at": now,
                                   "import_error": error if status == "failed" else None}
        if batch_id is not None:
            changes["import_batch_id"] = batch_id
        store.update_session(connection, session_id, changes)
        return _require(connection, session_id)


def ensure_contract(repository: Any, session_id: str, version_id: str | None) -> dict[str, Any]:
    """Record the assessment contract the session shows, once: a resumed
    problem keeps the contract it was opened (or bound) with."""

    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if version_id and not session.get("assessment_contract_version_id") and session.get("practice_item_id"):
            store.update_session(connection, session_id, {"assessment_contract_version_id": version_id})
            session = _require(connection, session_id)
        return session


def bind(repository: Any, session_id: str, practice_item_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """Bind the session to the item its import made (UX S2)."""

    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "submitted":
            raise WorkbenchError("already_submitted", "This problem was submitted.")
        if session["practice_item_id"] == practice_item_id and session["import_status"] in ("bound", "none"):
            return session
        if session["import_status"] == "none":
            raise WorkbenchError("validation_error", "This problem is already an item.")
        store.update_session(connection, session_id, {
            "practice_item_id": practice_item_id, "import_status": "bound", "import_error": None, "updated_at": now,
            # A contract snapshotted for another item never governs this one.
            "assessment_contract_version_id": None,
        })
        session = _require(connection, session_id)
        _log(repository, session, "workbench_bound", clock)
    return session


@dataclass(frozen=True)
class SubmissionPlan:
    """What a workbench submit sends through the ordinary attempt path."""

    session_id: str
    practice_item_id: str
    origin: str
    entry_surface: str
    composed: ComposedAnswer
    book_hints: int
    carried_hints: int = 0
    assessment_contract_version_id: str | None = None
    #: The serve the session was opened from (review F13).
    scheduler_candidate_id: str | None = None
    plan_presentation_id: str | None = None
    #: RW2b: the problem's shown checks and hints (``help_assists``), the
    #: same count the record line names (G62).
    help: WorkbenchFold = WorkbenchFold()

    @property
    def hints_used(self) -> int:
        """The session's hint-equivalents: the book's, the carried hints, and
        each shown check and level 1-3 hint (§5.4)."""

        return self.book_hints + self.carried_hints + self.help.hints

    @property
    def client_hints(self) -> int:
        """What the submit sends as the client's count: the session's RW2a
        counts only (the book's, the carried hints). Its shown checks and
        hints are the server's, added by the held fold exactly once (RW2b fix
        round 4, item 4: ``learnloop.attempts.hint_fold.combine_held``)."""

        return self.book_hints + self.carried_hints

    @property
    def primed(self) -> bool:
        """Worked help (a shown level 4-5 hint) primes the attempt (§5.4)."""

        return self.help.primed

    @property
    def submission_id(self) -> str:
        return submission_id_for(self.session_id)


def submission_id_for(session_id: str) -> str:
    """One submit per session, so the session names its retry key: a
    response lost after the commit is answered from the receipt."""

    return f"workbench:{session_id}"


def submission_plan(repository: Any, session_id: str) -> SubmissionPlan:
    with repository.connection() as connection:
        session = _require(connection, session_id)
        _require_open(session)
        if not session["practice_item_id"]:
            raise WorkbenchError(
                "not_bound", "Submit is available once setup finishes.", {"import_status": session["import_status"]}
            )
        rows = store.steps_for_session(connection, session_id)
        fold = assists_store.workbench_fold(connection, workbench_session_id=session_id,
                                            practice_item_id=session["practice_item_id"])
    return SubmissionPlan(
        session_id=session_id,
        practice_item_id=session["practice_item_id"],
        origin=session["origin"],
        entry_surface=ENTRY_SURFACE_READER if session["origin"] == "reader" else ENTRY_SURFACE_PRACTICE,
        composed=compose_answer(live_steps(rows)),
        book_hints=book_hints(session),
        carried_hints=carried_hints(session),
        assessment_contract_version_id=session.get("assessment_contract_version_id"),
        scheduler_candidate_id=session.get("scheduler_candidate_id"),
        plan_presentation_id=session.get("plan_presentation_id"),
        help=fold,
    )


def help_fold(repository: Any, session_id: str) -> WorkbenchFold:
    """The problem's shown checks and hints (the record line's count)."""

    with repository.connection() as connection:
        session = _require(connection, session_id)
        return assists_store.workbench_fold(connection, workbench_session_id=session_id,
                                            practice_item_id=session.get("practice_item_id"))


def set_help_style(repository: Any, session_id: str, help_style: str | None, *,
                   clock: Clock | None = None) -> dict[str, Any]:
    """The workbench header's help style for this problem (D31): one of the
    three styles, or None to follow the stored preference again. A stated
    preference the chooser weighs, never a block."""

    if help_style is not None and help_style not in HELP_STYLES:
        raise WorkbenchError("validation_error", f"unknown help style {help_style!r}")
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        _require_open(session)
        if session.get("help_style") == help_style:
            return session
        store.update_session(connection, session_id, {"help_style": help_style, "updated_at": now})
        session = _require(connection, session_id)
        _log(repository, session, "help_style_changed", clock, help_style=help_style)
    return session


def log_help_offered(repository: Any, session_id: str, *, about_step_id: str | None, offered_level: int,
                     kind: str, chooser: str, suggestion_id: str | None, clock: Clock | None = None) -> str:
    """The rung the ladder suggested when Help opened (§5.5): the Reader's
    fallback progression reads it ("one rung above the last offered")."""

    with repository.connection() as connection:
        session = _require(connection, session_id)
    return _log(repository, session, "workbench_help_offered", clock, about_step_id=about_step_id,
                offered_level=int(offered_level), kind=kind, chooser=chooser, suggestion_id=suggestion_id)


def mark_submitted(
    repository: Any,
    session_id: str,
    *,
    attempt_id: str,
    practice_session_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        session = _require(connection, session_id)
        if session["status"] == "submitted":
            return session
        store.update_session(connection, session_id, {
            "status": "submitted", "attempt_id": attempt_id, "practice_session_id": practice_session_id,
            "closed_at": now, "updated_at": now,
        })
        session = _require(connection, session_id)
        _log(repository, session, "workbench_closed", clock, reason="submitted", attempt_id=attempt_id)
    return session


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def session_view(
    repository: Any,
    session_id: str,
    *,
    question_hints: int = 0,
    server_hints: int = 0,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything the workbench shows for one session (snake_case; the
    adapter camel-cases it). ``server_hints``: the answer box's hints the
    hint service showed that the problem's submit will fold (H2b fix round
    3, ruling R1: its practice session and item, since the item's last
    attempt there), named in the record line with the client's; ``carried_hints`` stays the client's
    own count, which the answer box restores on the way back (the answer
    box folds the service's rows itself, so neither is counted twice)."""

    with repository.connection() as connection:
        session = _require(connection, session_id)
        rows = store.steps_for_session(connection, session_id)
        fold = assists_store.workbench_fold(connection, workbench_session_id=session_id,
                                            practice_item_id=session.get("practice_item_id")) \
            if session["status"] == "open" else None
    steps = live_steps(rows)
    composed = compose_answer(steps)
    last = max(steps, key=lambda step: (step["edited_at"], step["step_id"])) if steps else None
    return {
        "session_id": session["id"],
        "practice_item_id": session["practice_item_id"],
        "stem_md": session["stem_md"],
        "import_status": session["import_status"],
        "import_error": session["import_error"],
        "origin": session["origin"],
        "entry": session["entry"],
        "parent_session_id": session["parent_session_id"],
        "extraction_id": session["extraction_id"],
        "span_ids": _spans(session),
        "source_visible": bool(session["source_visible"]),
        "source_hidden_at": session["source_hidden_at"],
        "source_shown_at": session["source_shown_at"],
        "practice_session_id": session["practice_session_id"],
        "assessment_contract_version_id": session["assessment_contract_version_id"],
        "carried_hints": carried_hints(session),
        "scheduler_candidate_id": session["scheduler_candidate_id"],
        "plan_presentation_id": session["plan_presentation_id"],
        "help_style": session["help_style"],
        "status": session["status"],
        "attempt_id": session["attempt_id"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "closed_at": session["closed_at"],
        "steps": steps,
        "last_edited_step_id": last["step_id"] if last else None,
        "record": record_line(
            counted=book_counted(session), visible=bool(session["source_visible"]),
            question_hints=question_hints, composed=composed,
            carried=carried_hints(session) + max(0, int(server_hints or 0)),
            help_fold=fold,
        ),
        "parts": None,
        **dict(extra or {}),
    }


def _summary(session: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], *, now: datetime | None,
             open_days: int) -> dict[str, Any]:
    unfinished = False
    if now is not None and session["status"] == "open":
        updated = parse_utc(session["updated_at"])
        unfinished = updated is not None and now - updated > timedelta(days=open_days)
    return {
        "session_id": session["id"],
        "status": session["status"],
        "practice_item_id": session["practice_item_id"],
        "stem_md": session["stem_md"],
        "origin": session["origin"],
        "entry": session["entry"],
        "extraction_id": session["extraction_id"],
        "span_ids": _spans(session),
        "import_status": session["import_status"],
        "source_visible": bool(session["source_visible"]),
        # The book this problem counted: the answer box counts it too (review F2).
        "book_counted": book_counted(session),
        "step_count": len(live_steps(rows)),
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "unfinished": unfinished,
    }


def session_for_attempt(repository: Any, attempt_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return store.session_for_attempt(connection, attempt_id)


def _listed(repository: Any, *, column: str, value: str, now: datetime | None, open_days: int) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        sessions = store.sessions_where(connection, column=column, value=value, statuses=("open", "abandoned"))
        steps = store.steps_for_sessions(connection, [session["id"] for session in sessions])
    return [_summary(session, steps.get(session["id"], []), now=now, open_days=open_days) for session in sessions]


def sessions_for_item(repository: Any, practice_item_id: str, *, now: datetime | None = None,
                      open_days: int = 30) -> list[dict[str, Any]]:
    """The item's practice card: "resume your steps" (open) or "reopen" (abandoned)."""

    return _listed(repository, column="practice_item_id", value=practice_item_id, now=now, open_days=open_days)


def sessions_for_source(repository: Any, extraction_id: str, *, now: datetime | None = None,
                        open_days: int = 30) -> list[dict[str, Any]]:
    """The problems worked on a source and not submitted: the ``✎`` marks, the
    rail, and RW6a's recap (open sessions past ``open_days`` are
    ``unfinished``, shown without alarm and never closed)."""

    return _listed(repository, column="extraction_id", value=extraction_id, now=now, open_days=open_days)


__all__ = [
    "BOOK_OPEN_ENTRIES",
    "ComposedAnswer",
    "ENTRIES",
    "ENTRY_SURFACE_PRACTICE",
    "ENTRY_SURFACE_READER",
    "EXERCISE_PICK_KEY",
    "EXERCISE_WORKBENCH_EVENTS",
    "HELP_STYLES",
    "HELP_WORKBENCH_EVENTS",
    "IMPORT_STATUSES",
    "ORIGINS",
    "SERVER_WORKBENCH_EVENTS",
    "STATUSES",
    "STEP_KINDS",
    "STEP_OPS",
    "STUCK_NOTE",
    "SubmissionPlan",
    "WorkbenchError",
    "abandon",
    "admit_exercise_pick",
    "bind",
    "book_counted",
    "book_hints",
    "carried_hints",
    "compose_answer",
    "default_book_visible",
    "ensure_contract",
    "exercise_pick",
    "exercise_pick_due",
    "held_hints",
    "held_on",
    "held_parts_on",
    "held_primed",
    "help_fold",
    "import_request",
    "log_help_offered",
    "leave",
    "live_steps",
    "mark_import",
    "mark_submitted",
    "open_session",
    "open_session_days",
    "record_line",
    "reopen",
    "resumable_session",
    "resume_session",
    "save_step",
    "session_for_attempt",
    "session_hints",
    "session_row",
    "session_view",
    "sessions_for_item",
    "sessions_for_source",
    "set_book",
    "set_help_style",
    "submission_id_for",
    "submission_plan",
    "workbench_enabled",
]
