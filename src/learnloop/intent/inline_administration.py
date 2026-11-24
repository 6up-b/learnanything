"""Inline cold checks in the Reader (spec §12.6; mvp-0.69): the administration protocol of a due "Check once" where
the learner reads, beside Today's (decision D2: the Reader adds a place, not a rule).

The protocol (``docs/reviews/reader-rd7a.md`` §1.2) is a small state machine over ``check_administrations``:
``begin`` opens one (the item Today's check view would serve, its contract frozen by the serve itself, the protection
computed and its first veil set written) before the prompt leaves; ``protect_more`` appends a veil set for what came
into view; ``expose`` records what the learner opened and writes its reveal at once; ``submit`` records the attempt
through the one attempt service (the sidecar calls it between :func:`prepare_submit` and :func:`finish_submit`) and
then settles as any qualifying attempt does; ``abandon`` closes with no attempt. ``reopen`` is the restart read.

The owner's rulings (2026-11-23):

* **Opening a veil** writes a ``source_review`` reveal on each of the check's candidates, sized by the opened text's
  overlap with that candidate's answer key (``tutor_qa.span_answer_overlap``, as the Reader tutor debits a passage it
  shows). The answer counts as practice only when the reveal ledger then primes the item (the Check once decision).
* **Every note-bearing surface is veiled by default** when an inline check opens: every window but a source's text
  (pads of every kind, lessons, threads, the companion's history, panels) whole, margin notes on open sources, and the
  check's LO's covered passages in every source (structure). The learner can open any veil, which follows the rule
  above. There is no separate rule for what was on screen before the veils dropped. The Decider's judgment, once it
  exists, may only narrow the veiled set (:func:`narrow`); it never widens an evidence rule.
* **A later answer on the other surface** answers nothing (the first settling attempt won) and stays an ordinary
  attempt; the reply labels it practice.

Nothing here grades, scores or schedules: an inline answer reaches evidence only as an ordinary attempt, and exposure
only as reveal rows, both of which replay already reads. The administration table and its veil sets are workflow and
receipt rows that nothing derived reads.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from learnloop.algorithm_versions import inline_checks_on
from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.curriculum import commitments as C
from learnloop.db.stores import check_administrations as store
from learnloop.ids import new_ulid

#: The serving surface an inline administration records (``attempts.entry_surface``, ``check_administrations``).
SURFACE = "reader_inline"
#: How the protection was computed: the check's LO's covered passages by structure, every note-bearing surface by
#: default (the owner's ruling on uncertain protection).
METHOD = "structural+notes_by_default"
#: The same when coverage could not be read: every visible source passage is veiled instead of its covered ones.
METHOD_WHOLE_SOURCES = "whole_sources+notes_by_default"
#: Window kinds whose text structure can place (their passages are veiled by coverage); every other window is veiled
#: whole while a check is open.
PLACED_KINDS = frozenset({"source", "video"})
#: What a reveal from an opened veil is recorded as (``reveal_events.basis``).
OPENED_BASIS = "check_inline:opened_veil"

DUE_ONLY = "not_due"
BELOW_TAG = "below_tag"


class InlineCheckError(Exception):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class Opened:
    """A check's commitment and what begin found about it."""

    commitment_id: str
    practice_item_id: str
    cold: bool
    candidates: tuple[str, ...]
    learning_object_ids: tuple[str, ...]
    provenance: Mapping[str, Any]


def _now(clock: Clock | None) -> str:
    return utc_now_iso(clock)


def _require_tag(vault: Any) -> None:
    if not inline_checks_on(vault.config):
        raise InlineCheckError(BELOW_TAG, "Inline checks arrive with mvp-0.69; this vault is below it.")


# -- the protection set -------------------------------------------------------------------------------------------

def _ref_key(ref: Mapping[str, Any]) -> str:
    return json.dumps({key: ref[key] for key in sorted(ref) if key != "group"}, sort_keys=True)


#: ``covered(learning_object_ids) -> {(extraction_id, section_id)} | None``: the sections that treat the check's LOs
#: (judged coverage about them), or None when coverage cannot be read. The sidecar supplies it (coverage lives in
#: ``source_retrieval``, which this package must not import).
Covered = Callable[[Sequence[str]], "set[tuple[str, str]] | None"]


def protection(vault: Any, repository: Any, opened: Opened, visible: Mapping[str, Any],
               covered: Covered) -> tuple[str, list[dict[str, Any]]]:
    """What is veiled of ``visible`` while this check is open, and how it was decided.

    ``visible`` (the client's view of what is on screen): ``windows`` (each ``window_id``, ``kind``, and for a source
    its ``extraction_id``, ``span_ids``, ``note_ids`` and ``figures`` ``[{figure_id, span_id}]``, for any other window
    the ids it shows), ``companion_open`` with ``companion_exchange_ids``, ``preview_window_ids`` and ``search_rows``.
    """

    from learnloop.intent.inline_checks import _Sections

    sections_covered = covered(opened.learning_object_ids)
    method = METHOD if sections_covered is not None else METHOD_WHOLE_SOURCES
    anchors = {(str(opened.provenance.get("extraction_id") or ""), str(span))
               for span in opened.provenance.get("anchor_span_ids") or ()}
    sections = _Sections(repository)
    veiled: list[dict[str, Any]] = []
    held_windows: set[str] = set()

    def protected_span(extraction_id: str, span_id: str) -> bool:
        if sections_covered is None or (extraction_id, span_id) in anchors:
            return True
        section_id = sections.section_of(extraction_id, span_id)
        return section_id is not None and (extraction_id, section_id) in sections_covered

    for window in visible.get("windows") or ():
        window_id = str(window.get("window_id") or "")
        kind = str(window.get("kind") or "")
        if kind in PLACED_KINDS:
            extraction_id = str(window.get("extraction_id") or "")
            for span_id in window.get("span_ids") or ():
                if protected_span(extraction_id, str(span_id)):
                    veiled.append({"group": "source passages", "kind": "span", "window_id": window_id,
                                   "extraction_id": extraction_id, "span_id": str(span_id)})
                    held_windows.add(window_id)
            for figure in window.get("figures") or ():
                if protected_span(extraction_id, str(figure.get("span_id") or "")):
                    veiled.append({"group": "figures", "kind": "figure", "window_id": window_id,
                                   "figure_id": str(figure.get("figure_id") or "")})
                    held_windows.add(window_id)
            for note_id in window.get("note_ids") or ():
                veiled.append({"group": "notes", "kind": "note", "window_id": window_id, "note_id": str(note_id)})
                held_windows.add(window_id)
            continue
        # Every other window (pads of every kind, lessons, threads, the history, panels) is veiled whole by default.
        items = {key: [str(value) for value in window.get(key) or ()]
                 for key in ("pad_block_ids", "exchange_ids", "note_ids") if window.get(key)}
        veiled.append({"group": _window_group(kind), "kind": "window", "window_id": window_id, "window_kind": kind,
                       **items})
        held_windows.add(window_id)
    if visible.get("companion_open"):
        veiled.append({"group": "the companion", "kind": "companion",
                       "exchange_ids": [str(value) for value in visible.get("companion_exchange_ids") or ()]})
    for window_id in visible.get("preview_window_ids") or ():
        if str(window_id) in held_windows:
            veiled.append({"group": "previews", "kind": "preview", "window_id": str(window_id)})
    for row in visible.get("search_rows") or ():
        kind = str(row.get("kind") or "")
        if kind == "span" and not protected_span(str(row.get("extraction_id") or ""), str(row.get("span_id") or "")):
            continue
        veiled.append({"group": "search results", "kind": "search_row", "row_kind": kind,
                       **{key: str(row[key]) for key in ("extraction_id", "span_id", "ref_id") if row.get(key)}})
    return method, narrow(veiled)


def _window_group(kind: str) -> str:
    if kind in ("pad_stack", "pad", "ink"):
        return "pads"
    if kind in ("thread", "history", "companion"):
        return "threads"
    if kind == "lesson":
        return "lessons"
    return "windows"


def narrow(veiled: list[dict[str, Any]], judgment: Any | None = None) -> list[dict[str, Any]]:
    """The Decider's seam (spec §12.6.3): once the reveal adjudication judgment exists it may un-veil what it judges
    states nothing of the answer. It narrows the set only; it never widens what an opened veil means. Until then, the
    identity."""

    return veiled


# -- reads --------------------------------------------------------------------------------------------------------

def _check(vault: Any, repository: Any, commitment_id: str, *, clock: Clock | None) -> Any:
    from learnloop.scheduling.intent.serving import intent_serving

    serving = intent_serving(vault, repository, now=(clock or SystemClock()).now(), force=True)
    return None if serving is None else serving.checks.get(commitment_id)


def _learning_objects(vault: Any, repository: Any, commitment_id: str, candidates: Iterable[str]) -> tuple[str, ...]:
    from learnloop.scheduling.intent.resolution import load_snapshots

    los = {str(vault.practice_items[item].learning_object_id) for item in candidates if item in vault.practice_items}
    with repository.connection() as connection:
        for snapshot in load_snapshots(connection):
            if snapshot.id == commitment_id:
                los.update(str(lo) for lo in snapshot.learning_object_targets)
    return tuple(sorted(los))


def _open_in_today(repository: Any, candidates: Iterable[str]) -> bool:
    """A Today session shows one of the check's items with an answer being written: the check is being answered there."""

    wanted = set(candidates)
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT checkpoint.current_practice_item_id, checkpoint.current_answer FROM session_checkpoints checkpoint "
            "JOIN sessions ON sessions.id = checkpoint.session_id WHERE sessions.ended_at IS NULL").fetchall()
    return any(str(row[0]) in wanted and str(row[1] or "").strip() for row in rows if row[0])


def being_answered(repository: Any) -> frozenset[str]:
    """The commitments an open inline administration holds (the lock Today honours)."""

    with repository.connection() as connection:
        return store.open_commitments(connection)


def union(veil_sets: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Everything veiled by an administration's veil sets (deduplicated, in order) and what was opened by the last."""

    seen: dict[str, dict[str, Any]] = {}
    for veil in veil_sets:
        for ref in veil.get("veiled") or ():
            seen.setdefault(_ref_key(ref), dict(ref))
    opened = list(veil_sets[-1].get("opened") or ()) if veil_sets else []
    return list(seen.values()), opened


# -- the protocol ---------------------------------------------------------------------------------------------------

def find(repository: Any, token: str) -> dict[str, Any]:
    with repository.connection() as connection:
        admin = store.by_token(connection, token)
    if admin is None:
        raise InlineCheckError("administration_not_found", "That check isn't open (it was closed, or never opened).")
    return admin


def preflight(vault: Any, repository: Any, *, request_id: str, commitment_id: str) -> None:
    """The refusals ``begin`` gives before it reads the serving view (the tag, another open check, a duty no longer
    pending), for a caller that would otherwise do work first (start a practice session for a check that cannot open).
    ``begin`` checks them again."""

    _require_tag(vault)
    with repository.connection() as connection:
        known = store.by_request(connection, request_id)
        current = store.open_administration(connection)
    if known is not None:
        return
    if current is not None:
        raise InlineCheckError("administration_open", "Another check is open; answer it or say not now first.",
                               {"administration_token": current["administration_token"],
                                "commitment_id": current["commitment_id"]})
    if C.resolve_disposition(repository, commitment_id) != "one_check_pending":
        raise InlineCheckError(DUE_ONLY, "This check isn't pending any more.")


def begin(vault: Any, repository: Any, *, request_id: str, commitment_id: str, session_id: str,
          visible: Mapping[str, Any], serve: Callable[[str], Mapping[str, Any]], covered: Covered,
          clock: Clock | None = None) -> dict[str, Any]:
    """Open an inline administration: the item, the frozen contract (``serve``: Today's own session serve of the item,
    which freezes it), the protection and its first veil set, all before the prompt is returned. A retry with the same
    ``request_id`` returns the same administration."""

    _require_tag(vault)
    with repository.connection() as connection:
        known = store.by_request(connection, request_id)
        current = store.open_administration(connection)
    if known is not None:
        if known["commitment_id"] != commitment_id:
            raise InlineCheckError("request_reused", "That request id opened another check.")
        return {"administration": known, "served": serve(known["practice_item_id"]), "replayed": True}
    if current is not None:
        raise InlineCheckError("administration_open", "Another check is open; answer it or say not now first.",
                               {"administration_token": current["administration_token"],
                                "commitment_id": current["commitment_id"]})
    if C.resolve_disposition(repository, commitment_id) != "one_check_pending":
        raise InlineCheckError(DUE_ONLY, "This check isn't pending any more.")
    check = _check(vault, repository, commitment_id, clock=clock)
    if check is None or not check.pending:
        raise InlineCheckError(DUE_ONLY, "This check isn't due yet.")
    servable = check.servable
    if not servable:
        raise InlineCheckError("nothing_to_serve", "Nothing can be asked for this check right now; it comes back later.")
    if _open_in_today(repository, check.candidates):
        raise InlineCheckError("being_answered_in_today", "This check is being answered in Today.")
    item_id = servable[0]
    opened = Opened(commitment_id=commitment_id, practice_item_id=item_id, cold=check.cold(item_id),
                    candidates=tuple(check.candidates),
                    learning_object_ids=_learning_objects(vault, repository, commitment_id, check.candidates),
                    provenance=dict(check.provenance))
    served = serve(item_id)
    contract = served.get("assessment_contract_version_id") or served.get("assessmentContractVersionId")
    method, veiled = protection(vault, repository, opened, visible, covered)
    token = "cad_" + new_ulid()
    now = _now(clock)
    with repository.atomic():
        connection = repository.connection()
        store.insert_administration(connection, {
            "administration_token": token, "request_id": request_id, "commitment_id": commitment_id,
            "surface": SURFACE, "session_id": session_id, "practice_item_id": item_id, "contract_hash": contract,
            "cold": opened.cold, "protection_method": method, "opened_at": now})
        veil_set_id = "cvs_" + new_ulid()
        store.insert_veil_set(connection, veil_set_id=veil_set_id, token=token, commitment_id=commitment_id,
                              kind="begin", method=method, veiled=veiled, opened=[], now=now)
        admin = store.by_token(connection, token)
    return {"administration": admin, "served": served, "replayed": False}


def veils(repository: Any, token: str) -> dict[str, Any]:
    with repository.connection() as connection:
        sets = store.veil_sets(connection, token)
    veiled, opened = union(sets)
    return {"veil_set_id": sets[-1]["veil_set_id"] if sets else None, "method": sets[-1]["method"] if sets else None,
            "veiled": veiled, "opened": opened, "groups": sorted({str(ref.get("group")) for ref in veiled})}


def _require_open(admin: Mapping[str, Any]) -> None:
    if admin["state"] != "open":
        raise InlineCheckError("administration_closed", "This check was already closed.", {"state": admin["state"]})


def _opened_for(admin: Mapping[str, Any], repository: Any) -> Opened:
    from learnloop.scheduling.intent.resolution import load_snapshots

    provenance: dict[str, Any] = {}
    candidates: tuple[str, ...] = (admin["practice_item_id"],)
    los: set[str] = set()
    with repository.connection() as connection:
        for snapshot in load_snapshots(connection):
            if snapshot.id == admin["commitment_id"]:
                candidates = tuple(dict.fromkeys([admin["practice_item_id"], *snapshot.item_targets]))
                los.update(str(lo) for lo in snapshot.learning_object_targets)
    return Opened(commitment_id=admin["commitment_id"], practice_item_id=admin["practice_item_id"],
                  cold=bool(admin["cold"]), candidates=candidates, learning_object_ids=tuple(sorted(los)),
                  provenance=provenance)


def protect_more(vault: Any, repository: Any, *, token: str, visible: Mapping[str, Any], covered: Covered,
                 clock: Clock | None = None) -> list[dict[str, Any]]:
    """Veil what came into view (navigation, a new window, a search): a veil set of the additions only."""

    _require_tag(vault)
    admin = find(repository, token)
    _require_open(admin)
    opened = _opened_for(admin, repository)
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    if check is not None:
        opened = Opened(commitment_id=opened.commitment_id, practice_item_id=opened.practice_item_id, cold=opened.cold,
                        candidates=tuple(check.candidates),
                        learning_object_ids=_learning_objects(vault, repository, admin["commitment_id"], check.candidates),
                        provenance=dict(check.provenance))
    method, veiled = protection(vault, repository, opened, visible, covered)
    with repository.atomic():
        connection = repository.connection()
        known, already_opened = union(store.veil_sets(connection, token))
        keys = {_ref_key(ref) for ref in known}
        additions = [ref for ref in veiled if _ref_key(ref) not in keys]
        if additions:
            store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token,
                                  commitment_id=admin["commitment_id"], kind="more", method=method, veiled=additions,
                                  opened=already_opened, now=_now(clock))
    return additions


def _text_of(repository: Any, ref: Mapping[str, Any]) -> list[str]:
    """What an opened veil shows, as the texts measured against the answer keys."""

    from learnloop.db.stores import pad_reads

    kind = ref.get("kind")
    texts: list[str] = []
    if kind == "span":
        blocks = repository.document_blocks(str(ref.get("extraction_id") or ""), [str(ref.get("span_id") or "")])
        texts.extend(str(getattr(block, "text", "") or getattr(block, "markdown", "") or "") for block in blocks)
        return texts
    block_ids = [str(value) for value in ref.get("pad_block_ids") or ()]
    exchange_ids = [str(value) for value in ref.get("exchange_ids") or ()]
    note_ids = [str(value) for value in ref.get("note_ids") or ()]
    if kind == "note" and ref.get("note_id"):
        note_ids.append(str(ref["note_id"]))
    if kind == "search_row" and ref.get("ref_id"):
        row_kind = ref.get("row_kind")
        (block_ids if row_kind == "pad" else exchange_ids if row_kind in ("exchange", "thread") else note_ids).append(
            str(ref["ref_id"]))
    with repository.connection() as connection:
        for block_id in block_ids:
            head = pad_reads.head(connection, block_id)
            if head and not head.get("tombstone"):
                texts.append(str(head.get("body_md") or ""))
        for event_id in exchange_ids:
            row = connection.execute("SELECT question_md, answer_md FROM question_events WHERE id = ?",
                                     (event_id,)).fetchone()
            if row:
                texts.append(f"{row[0] or ''}\n{row[1] or ''}")
        for note_id in note_ids:
            row = connection.execute("SELECT text_md FROM learner_notes WHERE id = ?", (note_id,)).fetchone()
            if row:
                texts.append(str(row[0] or ""))
                continue
            # A margin note on an open source is a source annotation (the desks name it by its annotation id): its
            # current words are what opening its veil shows.
            row = connection.execute(
                "SELECT learner_text, what_i_think_is_going_on FROM source_annotation_versions WHERE annotation_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1", (note_id,)).fetchone()
            if row:
                texts.append(f"{row[0] or ''}\n{row[1] or ''}")
    return texts


def expose(vault: Any, repository: Any, *, token: str, ref: Mapping[str, Any], kind: str,
           clock: Clock | None = None) -> dict[str, Any]:
    """Record what the learner did that is exposure, at once. ``opened_veil``: a ``source_review`` reveal on each of the
    check's candidates, sized by the opened text's overlap with its answer key (the owner's ruling: the existing
    rule; the answer is practice only if that primes the item). ``navigated`` and ``help`` are recorded only (help is
    the hint path's, which the attempt service already counts)."""

    from learnloop.attempts.reveal_ledger import record_reveal
    from learnloop.tutor.tutor_qa import span_answer_overlap

    _require_tag(vault)
    if kind not in ("opened_veil", "navigated", "help"):
        raise InlineCheckError("validation_error", f"Unknown exposure {kind!r}.")
    admin = find(repository, token)
    _require_open(admin)
    opened = _opened_for(admin, repository)
    amounts: dict[str, float] = {}
    if kind == "opened_veil":
        texts = _text_of(repository, ref)
        for item_id in opened.candidates:
            item = vault.practice_items.get(item_id)
            if item is None:
                continue
            amount = max((span_answer_overlap(text, item.expected_answer) for text in texts if text), default=0.0)
            amounts[item_id] = amount
            record_reveal(repository, practice_item_id=item_id, source_kind="source_review", amount=amount,
                          learning_object_id=item.learning_object_id, basis=OPENED_BASIS, clock=clock)
    now = _now(clock)
    event = {"kind": kind, "ref": dict(ref), "at": now, "amounts": amounts}
    with repository.atomic():
        connection = repository.connection()
        current = store.by_token(connection, token)
        _require_open(current)
        exposure = [*current["exposure"], event]
        store.set_exposure(connection, token, exposure)
        if kind == "opened_veil":
            veiled, opened_refs = union(store.veil_sets(connection, token))
            store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token,
                                  commitment_id=admin["commitment_id"], kind="more", method=admin["protection_method"],
                                  veiled=[], opened=[*opened_refs, dict(ref)], now=now)
    return {"exposure": exposure, "cold_now": cold_now(vault, repository, admin, clock=clock)}


def cold_now(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None = None) -> bool:
    """Whether the check's item could still be answered cold now (the Check once decision over the reveal ledger)."""

    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    return bool(check is not None and check.cold(admin["practice_item_id"]))


def prepare_submit(vault: Any, repository: Any, *, token: str, submission_id: str) -> dict[str, Any]:
    """Before the attempt: name the submission on the administration (a crash after the attempt is found by it). A
    retry of the same submission passes; another submission on a closed administration is refused."""

    _require_tag(vault)
    admin = find(repository, token)
    if admin["state"] == "submitted":
        if admin["submission_id"] != submission_id:
            raise InlineCheckError("already_submitted", "This check was already answered.")
        return {**admin, "pending_before": False, "replayed": True}
    _require_open(admin)
    if admin["submission_id"] not in (None, submission_id):
        raise InlineCheckError("already_submitted", "An answer to this check is already on its way.")
    pending = C.resolve_disposition(repository, admin["commitment_id"]) == "one_check_pending"
    with repository.atomic():
        store.set_submission(repository.connection(), token, submission_id)
    return {**admin, "submission_id": submission_id, "pending_before": pending, "replayed": False}


def attempt_submission_key(submission_id: str) -> str:
    """The attempt service's own idempotency key for an inline submission."""

    return f"inline:{submission_id}"


def finish_submit(vault: Any, repository: Any, *, token: str, attempt_id: str, pending_before: bool,
                  clock: Clock | None = None) -> dict[str, Any]:
    """After the attempt: close the administration with it, then settle as for any qualifying attempt (the check is
    answered only if this attempt is its first on-your-own, cold one). Returns ``{cold, reason}``."""

    from learnloop.intent.checks import settle_answered_checks

    now = _now(clock)
    with repository.atomic():
        connection = repository.connection()
        store.close(connection, token, state="submitted", now=now, attempt_id=attempt_id)
        _close_veils(connection, token, now)
    settle_answered_checks(vault, repository, clock=clock)
    return outcome(vault, repository, token=token, pending_before=pending_before)


def outcome(vault: Any, repository: Any, *, token: str, pending_before: bool | None = None) -> dict[str, Any]:
    """Whether the administration's attempt answered its check, and why not when it did not."""

    admin = find(repository, token)
    attempt_id = admin["attempt_id"]
    with repository.connection() as connection:
        settled = connection.execute(
            "SELECT 1 FROM commitment_events WHERE commitment_id = ? AND kind = 'disposition_changed' "
            "AND json_extract(detail_json, '$.disposition') = 'satisfied' "
            "AND json_extract(detail_json, '$.administration_id') = ?", (admin["commitment_id"], attempt_id)).fetchone()
        primed = connection.execute("SELECT primed, hints_used FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone()
    if settled:
        return {"cold": True, "reason": "on_your_own"}
    if pending_before is False:
        return {"cold": False, "reason": "already_answered"}
    if primed and int(primed[0] or 0):
        return {"cold": False, "reason": "primed"}
    if primed and int(primed[1] or 0):
        return {"cold": False, "reason": "with_help"}
    if not admin["cold"]:
        return {"cold": False, "reason": "seen_before"}
    return {"cold": False, "reason": "practice"}


def _close_veils(connection: Any, token: str, now: str) -> None:
    admin = store.by_token(connection, token)
    veiled, opened = union(store.veil_sets(connection, token))
    store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token, commitment_id=admin["commitment_id"],
                          kind="close", method=admin["protection_method"], veiled=[], opened=opened, now=now)


def abandon(vault: Any, repository: Any, *, token: str, clock: Clock | None = None) -> None:
    """"Not now": closed with no attempt; the duty stays pending and what was opened stays in the reveal ledger."""

    _require_tag(vault)
    admin = find(repository, token)
    if admin["state"] == "abandoned":
        return
    _require_open(admin)
    now = _now(clock)
    with repository.atomic():
        connection = repository.connection()
        store.close(connection, token, state="abandoned", now=now)
        _close_veils(connection, token, now)


def reopen(vault: Any, repository: Any, *, attempt_for: Callable[[str, str], str | None],
           clock: Clock | None = None) -> dict[str, Any] | None:
    """The restart read: the open administration, or None. One whose submission reached the attempt service before a
    crash is closed with that attempt (``attempt_for(session_id, submission_key)``); one whose check was settled
    elsewhere or stopped meanwhile is closed superseded."""

    _require_tag(vault)
    with repository.connection() as connection:
        admin = store.open_administration(connection)
    if admin is None:
        return None
    token = admin["administration_token"]
    if admin["submission_id"]:
        attempt_id = attempt_for(admin["session_id"], attempt_submission_key(admin["submission_id"]))
        if attempt_id is not None:
            pending = C.resolve_disposition(repository, admin["commitment_id"]) == "one_check_pending"
            finish_submit(vault, repository, token=token, attempt_id=attempt_id, pending_before=pending, clock=clock)
            return None
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    still = (C.resolve_disposition(repository, admin["commitment_id"]) == "one_check_pending" and check is not None
             and admin["practice_item_id"] in check.candidates)
    if not still:
        now = _now(clock)
        with repository.atomic():
            connection = repository.connection()
            store.close(connection, token, state="superseded", now=now)
            _close_veils(connection, token, now)
        return None
    return admin


__all__ = [
    "BELOW_TAG", "InlineCheckError", "METHOD", "METHOD_WHOLE_SOURCES", "OPENED_BASIS", "Opened", "PLACED_KINDS",
    "Covered", "SURFACE", "abandon", "attempt_submission_key", "begin", "being_answered", "cold_now", "expose", "find",
    "finish_submit", "narrow", "outcome", "prepare_submit", "protect_more", "protection", "reopen", "union", "veils",
]
