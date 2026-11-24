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
#: The submit reply's sub-reason when the answer is practice because a note's veil was opened (``notes_opened``).
PRIMED_BY_NOTE = "unmeasured_note"
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


#: ``covered(learning_object_ids) -> {lo_id: {(extraction_id, section_id)}} | None``: per LO, the sections that treat
#: it (judged coverage about it), or None when coverage cannot be read at all. An LO missing from the answer (or with
#: an empty set) has no current coverage judgment: its host sources are protected whole (fail closed). The sidecar
#: supplies it (coverage lives in ``source_retrieval``, which this package must not import).
Covered = Callable[[Sequence[str]], "dict[str, set[tuple[str, str]]] | None"]


def _host_places(repository: Any, learning_object_ids: Iterable[str]) -> tuple[set[tuple[str, str]], set[str]]:
    """Where each LO is taught as the desks place it: its primary passage's section and every goal path's section for
    it (the host a check's marker sits before). Returns those sections and the readings that hold them."""

    from learnloop.intent.inline_checks import _Sections, _primary_passage

    sections = _Sections(repository)
    places: set[tuple[str, str]] = set()
    with repository.connection() as connection:
        for lo_id in learning_object_ids:
            passage = _primary_passage(connection, lo_id)
            if passage is not None:
                section_id = sections.section_of(*passage)
                if section_id is not None:
                    places.add((passage[0], section_id))
            try:
                rows = connection.execute("SELECT extraction_id, section_id FROM deliverable_path_sections "
                                          "WHERE learning_object_id = ?", (lo_id,)).fetchall()
            except Exception:  # noqa: BLE001 - no path table: no path places
                rows = []
            places.update((str(row[0]), str(row[1])) for row in rows)
    return places, {extraction for extraction, _section in places}


def protection(vault: Any, repository: Any, opened: Opened, visible: Mapping[str, Any],
               covered: Covered) -> tuple[str, list[dict[str, Any]]]:
    """What is veiled of ``visible`` while this check is open, and how it was decided.

    ``visible`` (the client's view of what is on screen): ``windows`` (each ``window_id``, ``kind``, and for a source
    its ``extraction_id``, ``span_ids``, ``note_ids`` and ``figures`` ``[{figure_id, span_id}]``, for any other window
    the ids it shows), ``companion_open`` with ``companion_exchange_ids``, ``preview_window_ids`` and ``search_rows``.
    """

    from learnloop.intent.inline_checks import _Sections

    by_lo = covered(opened.learning_object_ids)
    hosts, _host_readings = _host_places(repository, opened.learning_object_ids)
    # An LO with no current coverage judgment: the readings that host it are protected whole; with no host either, every
    # source is (fail closed). Coverage unreadable: every source is.
    uncovered = [lo for lo in opened.learning_object_ids if by_lo is not None and not by_lo.get(lo)]
    uncovered_hosts = {lo: _host_places(repository, [lo]) for lo in uncovered}
    whole_everywhere = by_lo is None or any(not places for places, _readings in uncovered_hosts.values())
    whole_readings = {reading for _places, readings in uncovered_hosts.values() for reading in readings}
    sections_covered: set[tuple[str, str]] = set().union(*(by_lo or {}).values()) | hosts
    method = METHOD_WHOLE_SOURCES if whole_everywhere or whole_readings else METHOD
    anchors = {(str(opened.provenance.get("extraction_id") or ""), str(span))
               for span in opened.provenance.get("anchor_span_ids") or ()}
    sections = _Sections(repository)
    veiled: list[dict[str, Any]] = []
    held_windows: set[str] = set()

    def protected_span(extraction_id: str, span_id: str) -> bool:
        if whole_everywhere or extraction_id in whole_readings or (extraction_id, span_id) in anchors:
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
    """Today shows one of the check's items now: the current practice session's checkpoint names it (written when the
    item is shown, whether or not an answer is typed yet). Only the current session: an old session nobody ended is
    not one the learner is answering in."""

    wanted = set(candidates)
    current = repository.most_recent_open_session()
    if current is None:
        return False
    with repository.connection() as connection:
        row = connection.execute("SELECT current_practice_item_id FROM session_checkpoints WHERE session_id = ?",
                                 (str(current["id"]),)).fetchone()
    return bool(row and row[0] and str(row[0]) in wanted)


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


#: The serve-time Check once reasons a card or an outcome names when the item is not answered cold (the learner's
#: words are the frontend's).
ELIGIBILITY_WORDS = {
    "check_once_answer_shown": "answer_shown", "cold_check_revealed_since_scheduled": "hold",
    "cold_check_routine_display": "hold",
}
#: What an unmeasurable opening is recorded as (``reveal_events.basis``): what it showed cannot be measured, so it is
#: charged as priming, on every candidate.
UNMEASURED_BASIS = "check_inline:unmeasured"
#: Pad block kinds whose stored words are what the block shows (measured); any other kind (ink, a sketch, a figure, a
#: notebook cell, a lifted or check cell) shows something its words do not.
MEASURED_BLOCK_KINDS = frozenset({"text", "note", "source_quote", "source_piece", "tutor_quote"})
#: The keys of a served item's detail that the learner may see while the check is open: the question and its
#: learner-facing blocks, the answer's form, and the check's own banner (never its key, hints, rubric, history,
#: source locators or way back).
PRESENTATION_KEYS = ("id", "practiceMode", "attemptTypesAllowed", "prompt", "presentation", "activeFollowupKind")
INTENT_CHECK_KEYS = ("kind", "commitmentId", "cold", "banner", "helpHeader", "locatorsHidden", "duty", "beingAnsweredIn")


def cold_presentation(served: Mapping[str, Any]) -> dict[str, Any]:
    """The learner-facing cold presentation of a served item (an allowlist): what the card shows, and nothing it could
    read the answer from."""

    out = {"practiceItemId" if key == "id" else key: served[key] for key in PRESENTATION_KEYS if key in served}
    check = served.get("intentCheck") or served.get("intent_check")
    if isinstance(check, Mapping):
        out["intentCheck"] = {key: check[key] for key in INTENT_CHECK_KEYS if key in check}
    return out


def _frozen_candidates(vault: Any, candidates: Iterable[str]) -> list[dict[str, Any]]:
    """Every item that can settle the check (the serving view's candidates, ``build_checks``'s one expansion), each
    with its LO and its answer key as they are now: what an opening is charged to and measured against."""

    out = []
    for item_id in candidates:
        item = vault.practice_items.get(item_id)
        if item is None:
            continue
        out.append({"practice_item_id": str(item_id), "learning_object_id": str(item.learning_object_id),
                    "key": str(item.expected_answer or "")})
    return out


def eligibility_of(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None = None) -> str | None:
    """The serve-time Check once reason the item is not cold now (``ELIGIBILITY_WORDS``), or None when it is."""

    from learnloop import serve_eligibility

    item = vault.practice_items.get(admin["practice_item_id"])
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    if item is None or check is None:
        return None
    decision = serve_eligibility.decide(serve_eligibility.gather(
        repository, practice_item_id=item.id, learning_object_id=str(item.learning_object_id), at=_now(clock),
        check_created_at=check.created_at), serve_eligibility.CHECK_ONCE)
    if decision.reason == serve_eligibility.ELIGIBLE:
        return None
    return ELIGIBILITY_WORDS.get(str(decision.reason), str(decision.reason))


def refuse_open_elsewhere(repository: Any, commitment_id: str) -> None:
    """Another commitment's administration is open: refused, naming it."""

    with repository.connection() as connection:
        current = store.open_administration(connection)
    if current is not None and current["commitment_id"] != commitment_id:
        raise InlineCheckError("administration_open", "Another check is open; answer it or say not now first.",
                               {"administration_token": current["administration_token"],
                                "commitment_id": current["commitment_id"]})


def _terminal(admin: Mapping[str, Any]) -> InlineCheckError:
    return InlineCheckError("administration_closed", "This check was already closed.",
                            {"state": admin["state"], "outcome": admin.get("outcome")})


def preflight(vault: Any, repository: Any, *, request_id: str, commitment_id: str) -> dict[str, Any] | None:
    """The answers ``begin`` gives before it reads the serving view, for a caller that would otherwise do work first
    (start a practice session for a check that cannot open). Returns the standing administration a retried or repeated
    begin adopts (the same request, or the same commitment's open one), else None after the refusals: the tag,
    another commitment's open check, a closed request, a duty no longer pending."""

    _require_tag(vault)
    with repository.connection() as connection:
        known = store.by_request(connection, request_id)
        current = store.open_administration(connection)
    if known is not None:
        if known["commitment_id"] != commitment_id:
            raise InlineCheckError("request_reused", "That request id opened another check.")
        if known["state"] != "open":
            raise _terminal(known)
        return known
    if current is not None:
        if current["commitment_id"] == commitment_id:
            # A lost begin reply, or another click: the open administration of this check is adopted, not refused.
            return current
        refuse_open_elsewhere(repository, commitment_id)
    if C.resolve_disposition(repository, commitment_id) != "one_check_pending":
        raise InlineCheckError(DUE_ONLY, "This check isn't pending any more.")
    return None


def begin(vault: Any, repository: Any, *, request_id: str, commitment_id: str, session_id: str,
          visible: Mapping[str, Any], serve: Callable[[str], Mapping[str, Any]], covered: Covered,
          clock: Clock | None = None) -> dict[str, Any]:
    """Open an inline administration: the item, the frozen contract (``serve``: Today's own session serve of the item,
    which freezes it), every candidate with its key, the cold presentation, the protection and its first veil set, all
    before the prompt is returned. A retry with the same ``request_id``, or a begin for the commitment already open,
    returns that administration as it was frozen (nothing is served again); a closed request is refused."""

    standing = preflight(vault, repository, request_id=request_id, commitment_id=commitment_id)
    if standing is not None:
        return {"administration": standing, "replayed": True}
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
            "cold": opened.cold, "protection_method": method, "opened_at": now,
            "candidates": _frozen_candidates(vault, opened.candidates), "presentation": cold_presentation(served)})
        store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token, commitment_id=commitment_id,
                              kind="begin", method=method, veiled=veiled, opened=[], now=now)
        admin = store.by_token(connection, token)
    return {"administration": admin, "replayed": False}


def veils(repository: Any, token: str) -> dict[str, Any]:
    """The administration's veils: everything veiled, what was opened, the standing set (veiled and not opened) and the
    revision (the last veil set's sequence number)."""

    with repository.connection() as connection:
        sets = store.veil_sets(connection, token)
    veiled, opened = union(sets)
    opened_keys = {_ref_key(ref) for ref in opened}
    return {"veil_set_id": sets[-1]["veil_set_id"] if sets else None, "method": sets[-1]["method"] if sets else None,
            "veiled": veiled, "opened": opened, "groups": sorted({str(ref.get("group")) for ref in veiled}),
            "standing": [ref for ref in veiled if _ref_key(ref) not in opened_keys],
            "revision": sets[-1]["seq"] if sets else 0}


def _require_open(admin: Mapping[str, Any]) -> None:
    if admin["state"] != "open":
        raise _terminal(admin)


def _require_unreserved(admin: Mapping[str, Any]) -> None:
    if admin.get("submission_id"):
        raise InlineCheckError("submission_in_flight", "Your answer to this check is being recorded.")


def _opened_for(admin: Mapping[str, Any], repository: Any) -> Opened:
    """The administration as begin froze it: its candidates are the ones begin resolved, never rebuilt later."""

    from learnloop.scheduling.intent.resolution import load_snapshots

    candidates = tuple(str(entry["practice_item_id"]) for entry in admin.get("candidates") or ()) \
        or (str(admin["practice_item_id"]),)
    los = {str(entry["learning_object_id"]) for entry in admin.get("candidates") or ()}
    provenance: dict[str, Any] = {}
    with repository.connection() as connection:
        for snapshot in load_snapshots(connection):
            if snapshot.id == admin["commitment_id"]:
                los.update(str(lo) for lo in snapshot.learning_object_targets)
                provenance = dict(snapshot.provenance)
    return Opened(commitment_id=admin["commitment_id"], practice_item_id=admin["practice_item_id"],
                  cold=bool(admin["cold"]), candidates=candidates, learning_object_ids=tuple(sorted(los)),
                  provenance=provenance)


def protect_more(vault: Any, repository: Any, *, token: str, visible: Mapping[str, Any], covered: Covered,
                 clock: Clock | None = None) -> dict[str, Any]:
    """Veil what came into view (navigation, a new window, a search): a veil set of the additions only. Returns the
    additions, the standing set and the revision, so a client whose earlier reply was lost still has every veil."""

    _require_tag(vault)
    admin = find(repository, token)
    _require_open(admin)
    opened = _opened_for(admin, repository)
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
    current = veils(repository, token)
    return {"additions": additions, "standing": current["standing"], "revision": current["revision"]}


def measured(repository: Any, ref: Mapping[str, Any]) -> bool:
    """Whether what opening this ref shows can be measured against the answer keys: a source passage's text, text pad
    blocks, tutor exchanges and search rows naming one of those. A note, a figure, a lesson, an ink or notebook block, a
    window with nothing listed, a preview or the companion with no exchange named cannot (``UNMEASURED_BASIS``)."""

    from learnloop.db.stores import pad_reads

    kind = ref.get("kind")
    if kind == "span":
        return bool(ref.get("extraction_id") and ref.get("span_id"))
    if kind == "search_row":
        return bool(ref.get("ref_id") or ref.get("span_id")) and ref.get("row_kind") in ("span", "pad", "exchange", "thread")
    if kind == "companion":
        return bool(ref.get("exchange_ids"))
    if kind != "window" or ref.get("note_ids"):
        return False
    blocks = [str(value) for value in ref.get("pad_block_ids") or ()]
    exchanges = [str(value) for value in ref.get("exchange_ids") or ()]
    if not blocks and not exchanges:
        return False
    with repository.connection() as connection:
        for block_id in blocks:
            head = pad_reads.head(connection, block_id)
            if head is not None and not head.get("tombstone") and str(head.get("kind") or "") not in MEASURED_BLOCK_KINDS:
                return False
    return True


def with_measured(repository: Any, refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{**dict(ref), "measured": measured(repository, ref)} for ref in refs]


def _text_of(repository: Any, ref: Mapping[str, Any]) -> list[str]:
    """What an opened (measured) veil shows, as the texts measured against the answer keys. A note's words are never
    read here: a note is never evidence (curriculum C2), so an opened note is unmeasured."""

    from learnloop.db.stores import pad_reads

    kind = ref.get("kind")
    texts: list[str] = []
    span = ref.get("span_id")
    if kind == "span" or (kind == "search_row" and ref.get("row_kind") == "span" and span):
        blocks = repository.document_blocks(str(ref.get("extraction_id") or ""), [str(span or "")])
        texts.extend(str(getattr(block, "text", "") or getattr(block, "markdown", "") or "") for block in blocks)
        return texts
    block_ids = [str(value) for value in ref.get("pad_block_ids") or ()]
    exchange_ids = [str(value) for value in ref.get("exchange_ids") or ()]
    if kind == "search_row" and ref.get("ref_id"):
        if ref.get("row_kind") == "pad":
            block_ids.append(str(ref["ref_id"]))
        elif ref.get("row_kind") in ("exchange", "thread"):
            exchange_ids.append(str(ref["ref_id"]))
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
    return texts


def _unmeasured(ref: Mapping[str, Any]) -> list[str]:
    """The notes an opened veil showed (their ids only; C2: a note is never evidence)."""

    ids = [str(value) for value in ref.get("note_ids") or ()]
    if ref.get("kind") == "note" and ref.get("note_id"):
        ids.append(str(ref["note_id"]))
    if ref.get("kind") == "search_row" and ref.get("ref_id") and ref.get("row_kind") not in ("pad", "exchange", "thread", "span"):
        ids.append(str(ref["ref_id"]))
    return ids


def _exposure_result(vault: Any, repository: Any, admin: Mapping[str, Any], event: Mapping[str, Any] | None, *,
                     clock: Clock | None) -> dict[str, Any]:
    return {"exposure": list(admin["exposure"]), "cold_now": cold_now(vault, repository, admin, clock=clock),
            "measured": bool(event.get("measured", True)) if event is not None else True,
            "eligibility": eligibility_of(vault, repository, admin, clock=clock)}


def expose(vault: Any, repository: Any, *, token: str, ref: Mapping[str, Any], kind: str,
           exposure_id: str | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Record what the learner did that is exposure, at once, with its reveals, in one transaction (all of it or none:
    a refusal or failure records nothing, and the veil must stay).

    * ``opened_veil``, measured: a ``source_review`` reveal on each frozen candidate, sized by the opened text's
      overlap with that candidate's frozen key (the owner's overlap rule).
    * ``opened_veil``, unmeasured (a note, a figure, a lesson, ink, …), and ``left`` (the learner reached a surface the
      veils do not cover): a ``source_review`` reveal at the priming threshold on every frozen candidate. What was shown
      cannot be measured, so the answer counts as practice (confirmed by the owner for notes, 2026-11-23); the reveals
      outlive the administration (not now, a crash, a supersede), so the next attempt on the check's material, on any
      surface, is not cold either. No note is read.
    * ``navigated`` and ``help``: recorded only (help is the hint path's, which the attempt service already counts).

    ``exposure_id``: the client's id for this opening; a retry with it returns the first result and charges nothing
    again."""

    from learnloop.attempts.reveal_ledger import reveal_episode_id
    from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD
    from learnloop.tutor.tutor_qa import span_answer_overlap

    _require_tag(vault)
    if kind not in ("opened_veil", "left", "navigated", "help"):
        raise InlineCheckError("validation_error", f"Unknown exposure {kind!r}.")
    admin = find(repository, token)
    if exposure_id is not None and exposure_id in (admin.get("exposure_ids") or ()):
        recorded = next((event for event in admin["exposure"] if event.get("exposure_id") == exposure_id), None)
        return _exposure_result(vault, repository, admin, recorded, clock=clock)
    _require_open(admin)
    _require_unreserved(admin)
    opened = _opened_for(admin, repository)
    charging = kind in ("opened_veil", "left")
    is_measured = kind == "opened_veil" and measured(repository, ref)
    amounts: dict[str, float] = {}
    if charging:
        texts = _text_of(repository, ref) if is_measured else []
        for entry in admin.get("candidates") or ({"practice_item_id": item, "learning_object_id": None, "key": None}
                                                for item in opened.candidates):
            item_id = str(entry["practice_item_id"])
            key = entry.get("key")
            if key is None:
                item = vault.practice_items.get(item_id)
                key = str(item.expected_answer or "") if item is not None else ""
            amounts[item_id] = (max((span_answer_overlap(text, key) for text in texts if text), default=0.0)
                                if is_measured else float(AUTO_PRIME_REVEAL_THRESHOLD))
    now = _now(clock)
    event: dict[str, Any] = {"kind": kind, "ref": dict(ref), "at": now, "amounts": amounts, "measured": is_measured}
    if exposure_id is not None:
        event["exposure_id"] = exposure_id
    notes = _unmeasured(ref) if kind == "opened_veil" else []
    if notes:
        event["unmeasured_notes"] = notes
    los = {str(entry["practice_item_id"]): entry.get("learning_object_id") for entry in admin.get("candidates") or ()}
    episodes = {item_id: reveal_episode_id(repository, item_id, strict=True) for item_id, amount in amounts.items()
                if amount > 0}
    with repository.atomic():
        connection = repository.connection()
        current = store.by_token(connection, token)
        _require_open(current)
        _require_unreserved(current)
        if exposure_id is not None and exposure_id in (current.get("exposure_ids") or ()):
            recorded = next((item for item in current["exposure"] if item.get("exposure_id") == exposure_id), None)
            return _exposure_result(vault, repository, current, recorded, clock=clock)
        for index, (item_id, amount) in enumerate(sorted(amounts.items())):
            if amount <= 0:
                continue
            # The strict writer's insert, in this transaction, with an id derived from the opening: a retry cannot
            # write a second row.
            repository.insert_reveal_event({
                "id": f"rvl_{token}_{exposure_id or new_ulid()}_{index}", "practice_item_id": item_id,
                "learning_object_id": los.get(item_id), "remediation_episode_id": episodes.get(item_id),
                "source_kind": "source_review", "amount": amount,
                "basis": OPENED_BASIS if is_measured else UNMEASURED_BASIS}, clock=clock)
        exposure = [*current["exposure"], event]
        ids = [*(current.get("exposure_ids") or ()), *([exposure_id] if exposure_id is not None else [])]
        if not store.set_exposure(connection, token, exposure, ids):
            raise InlineCheckError("submission_in_flight", "Your answer to this check is being recorded.")
        if kind == "opened_veil":
            _veiled, opened_refs = union(store.veil_sets(connection, token))
            store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token,
                                  commitment_id=admin["commitment_id"], kind="more", method=admin["protection_method"],
                                  veiled=[], opened=[*opened_refs, dict(ref)], now=now)
        after = store.by_token(connection, token)
    return _exposure_result(vault, repository, after, event, clock=clock)


def cold_now(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None = None) -> bool:
    """Whether the check's item could still be answered cold now: the Check once decision over the reveal ledger,
    where every opening (measured, or unmeasured at the priming threshold) is."""

    if notes_opened(admin) or any(event.get("kind") == "left" for event in admin.get("exposure") or ()):
        return False
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    return bool(check is not None and check.cold(admin["practice_item_id"]))


def prepare_submit(vault: Any, repository: Any, *, token: str, submission_id: str,
                   veils_revision: int | None = None) -> dict[str, Any]:
    """Before the attempt: reserve the submission on the administration (a crash after the attempt is found by it),
    with whether the check was pending then. A retry of the same submission passes (its first outcome is returned
    once it has one); another submission, or a client whose veils are behind the server's revision, is refused."""

    _require_tag(vault)
    admin = find(repository, token)
    if admin["state"] == "submitted":
        if admin["submission_id"] != submission_id:
            raise InlineCheckError("already_submitted", "This check was already answered.")
        return {**admin, "replayed": True}
    _require_open(admin)
    if admin["submission_id"] not in (None, submission_id):
        raise InlineCheckError("already_submitted", "An answer to this check is already on its way.")
    if veils_revision is not None and admin["submission_id"] is None:
        current = veils(repository, token)["revision"]
        if veils_revision < current:
            raise InlineCheckError("veils_stale", "Some of what is on screen isn't covered yet; it is now. Send again.",
                                   {"revision": current})
    pending = admin["pending_before"] if admin["submission_id"] is not None else \
        C.resolve_disposition(repository, admin["commitment_id"]) == "one_check_pending"
    with repository.atomic():
        if not store.set_submission(repository.connection(), token, submission_id, pending_before=bool(pending)):
            raise InlineCheckError("already_submitted", "An answer to this check is already on its way.")
    return {**find(repository, token), "replayed": False}


def notes_opened(admin: Mapping[str, Any]) -> bool:
    """Whether the learner opened a note's veil during this administration (an exposure event with unmeasured notes).
    Its reveals already make the answer practice; the flag names why (``primed_by``) and declares the attempt primed.
    Confirmed by the owner (2026-11-23): opening one of your own notes during a cold check counts as practice."""

    return any(event.get("kind") == "opened_veil" and event.get("unmeasured_notes") for event in admin.get("exposure") or ())


def attempt_submission_key(submission_id: str) -> str:
    """The attempt service's own idempotency key for an inline submission."""

    return f"inline:{submission_id}"


def finish_submit(vault: Any, repository: Any, *, token: str, attempt_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """After the attempt: settle as for any qualifying attempt (the check is answered only if this attempt is its first
    on-your-own, cold one), then close the administration with the attempt and the outcome it promises, in one
    transaction. Settlement is idempotent, so a crash before the close is finished by the next read (``reopen``)
    and a retry returns the saved outcome."""

    from learnloop.intent.checks import settle_answered_checks

    admin = find(repository, token)
    if admin["state"] == "submitted" and admin.get("outcome") is not None:
        return dict(admin["outcome"])
    settle_answered_checks(vault, repository, clock=clock)
    result = outcome(vault, repository, admin={**admin, "attempt_id": attempt_id}, clock=clock)
    now = _now(clock)
    with repository.atomic():
        connection = repository.connection()
        if store.close(connection, token, state="submitted", now=now, attempt_id=attempt_id, outcome=result):
            _close_veils(connection, token, now)
        else:
            closed = store.by_token(connection, token)
            if closed is not None and closed.get("outcome") is not None:
                return dict(closed["outcome"])
    return result


def outcome(vault: Any, repository: Any, *, admin: Mapping[str, Any], clock: Clock | None = None) -> dict[str, Any]:
    """Whether the administration's attempt answered its check, and why not when it did not: the reason, and the
    Check once decision's own reason at the attempt (``eligibility``: a hold, the answer shown)."""

    from learnloop import serve_eligibility

    attempt_id = admin["attempt_id"]
    with repository.connection() as connection:
        settled = connection.execute(
            "SELECT 1 FROM commitment_events WHERE commitment_id = ? AND kind = 'disposition_changed' "
            "AND json_extract(detail_json, '$.disposition') = 'satisfied' "
            "AND json_extract(detail_json, '$.administration_id') = ?", (admin["commitment_id"], attempt_id)).fetchone()
        row = connection.execute("SELECT primed, hints_used, created_at FROM practice_attempts WHERE id = ?",
                                 (attempt_id,)).fetchone()
    if settled:
        return {"cold": True, "reason": "on_your_own", "eligibility": None}
    eligibility = None
    item = vault.practice_items.get(admin["practice_item_id"])
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    if row is not None and item is not None and check is not None:
        decision = serve_eligibility.check_once_at_attempt(
            repository, practice_item_id=item.id, learning_object_id=str(item.learning_object_id),
            attempt_id=str(attempt_id), attempt_at=str(row[2]), check_created_at=check.created_at)
        if decision.reason != serve_eligibility.ELIGIBLE:
            eligibility = ELIGIBILITY_WORDS.get(str(decision.reason), str(decision.reason))
    if admin.get("pending_before") is False:
        return {"cold": False, "reason": "already_answered", "eligibility": eligibility}
    if row is not None and int(row[1] or 0):
        return {"cold": False, "reason": "with_help", "eligibility": eligibility}
    if row is not None and int(row[0] or 0) or eligibility == "answer_shown":
        # The sub-reason lets the card say why honestly: a note was opened, and nothing could measure it.
        return {"cold": False, "reason": "primed", "eligibility": eligibility,
                **({"primed_by": PRIMED_BY_NOTE} if notes_opened(admin) else {})}
    if eligibility == "hold":
        return {"cold": False, "reason": "hold", "eligibility": eligibility}
    if not admin["cold"]:
        return {"cold": False, "reason": "seen_before", "eligibility": eligibility}
    return {"cold": False, "reason": "practice", "eligibility": eligibility}


def _close_veils(connection: Any, token: str, now: str) -> None:
    admin = store.by_token(connection, token)
    veiled, opened = union(store.veil_sets(connection, token))
    store.insert_veil_set(connection, veil_set_id="cvs_" + new_ulid(), token=token, commitment_id=admin["commitment_id"],
                          kind="close", method=admin["protection_method"], veiled=[], opened=opened, now=now)


def abandon(vault: Any, repository: Any, *, token: str, clock: Clock | None = None) -> None:
    """"Not now": closed with no attempt; the duty stays pending and what was opened stays in the reveal ledger. While
    a submission is reserved it is refused (the answer decides)."""

    _require_tag(vault)
    admin = find(repository, token)
    if admin["state"] == "abandoned":
        return
    _require_open(admin)
    _require_unreserved(admin)
    now = _now(clock)
    with repository.atomic():
        connection = repository.connection()
        if not store.close(connection, token, state="abandoned", now=now, unreserved=True):
            current = store.by_token(connection, token)
            if current is not None and current["state"] == "abandoned":
                return
            raise InlineCheckError("submission_in_flight", "Your answer to this check is being recorded.")
        _close_veils(connection, token, now)


def _attempted_elsewhere(repository: Any, admin: Mapping[str, Any]) -> bool:
    """An attempt on one of the check's candidates since the administration opened, made on another surface (an
    assisted Today answer moves the check's date; any answer there changes what this card would decide)."""

    items = [str(entry["practice_item_id"]) for entry in admin.get("candidates") or ()] or [str(admin["practice_item_id"])]
    marks = ",".join("?" for _ in items)
    with repository.connection() as connection:
        row = connection.execute(
            f"SELECT 1 FROM practice_attempts WHERE practice_item_id IN ({marks}) AND created_at >= ? "
            "AND entry_surface != ? LIMIT 1", (*items, admin["opened_at"], SURFACE)).fetchone()
    return row is not None


def reopen(vault: Any, repository: Any, *, attempt_for: Callable[[str, str], str | None],
           clock: Clock | None = None) -> dict[str, Any] | None:
    """The restart read: the open administration, or None. One whose submission reached the attempt service before a
    crash is finished with that attempt (settled, closed with its outcome); one whose check was settled elsewhere,
    stopped, moved by an answer on another surface, or no longer holds its item, is closed superseded."""

    _require_tag(vault)
    with repository.connection() as connection:
        admin = store.open_administration(connection)
    if admin is None:
        return None
    token = admin["administration_token"]
    if admin["submission_id"]:
        attempt_id = attempt_for(admin["session_id"], attempt_submission_key(admin["submission_id"]))
        if attempt_id is not None:
            finish_submit(vault, repository, token=token, attempt_id=attempt_id, clock=clock)
            return None
        return admin
    check = _check(vault, repository, admin["commitment_id"], clock=clock)
    still = (C.resolve_disposition(repository, admin["commitment_id"]) == "one_check_pending" and check is not None
             and check.pending and admin["practice_item_id"] in check.candidates
             and not _attempted_elsewhere(repository, admin))
    if not still:
        now = _now(clock)
        with repository.atomic():
            connection = repository.connection()
            if store.close(connection, token, state="superseded", now=now, unreserved=True):
                _close_veils(connection, token, now)
        return None
    return admin


__all__ = [
    "BELOW_TAG", "Covered", "InlineCheckError", "METHOD", "METHOD_WHOLE_SOURCES", "OPENED_BASIS", "Opened", "PLACED_KINDS",
    "SURFACE", "UNMEASURED_BASIS", "abandon", "attempt_submission_key", "begin", "being_answered", "cold_now",
    "cold_presentation", "eligibility_of", "expose", "find", "finish_submit", "measured", "narrow", "outcome",
    "preflight", "prepare_submit", "protect_more", "protection", "reopen", "union", "veils", "with_measured",
]
