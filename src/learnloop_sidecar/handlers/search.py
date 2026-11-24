"""Reader workbench v2 RPCs: ``search.everything`` and ``search.job`` (spec §3.4, §9.3): search in
context, by words at once and by meaning through a job.

``search.everything`` ``{query, desk_id?, scopes?}`` answers at once with the groups found by the
learner's words (``learnloop.companion.search`` plus the library's passages and the vault's notes
through their own services) and the state of the search by meaning:

* ``meaning.status = "pending"`` with a ``job_id``: the groups that can be searched by meaning run on a
  thread the context owns (``search.job`` reads it at once). Today those are the passages (the
  library's stored passage vectors and one query embedding, ``reader.search_sources``' deep search)
  and the vault's notes (``notes.search``' meaning mode). Each group the job returns says whether it
  ran (``status`` ``ok``), could not (``unavailable``, with the retrieval's reason: the query not
  embedded, no note embedded yet) or failed (``failed``), never an empty "nothing found"; the job's
  poll also carries the groups that had no search by meaning at all (``unavailable``).
* ``meaning.status = "unavailable"``: nothing to search by meaning, each group with its reason
  (embeddings off, the library index missing, no OK to use AI yet, a group with no meaning index,
  searches already running).

Every search from a desk supersedes the desk's running search by meaning, whatever it returns: its
next model request is refused and its result is never delivered. Every group is bounded
(``companion.search.GROUP_ROWS`` rows; ``more`` is read from every match before the cap); a result
found by meaning that the words already found is left out, so the meaning rows merge in without
repeats. A note row opens its note: a Reader note or highlight at its passage in its book, a
capture-inbox note in the notes panel, with the note named in ``target``. Jobs belong to the vault
open when they started (``polled_jobs``). Nothing here writes, and none of it is evidence. Desktop only (pinned in
tests/test_mobile_allowlist.py).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from learnloop.companion import search as CS
from learnloop.ids import new_ulid
from learnloop_sidecar import polled_jobs as PJ
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method
from learnloop_sidecar.workbench_protection import PassageSelection, block_places, reading_places, refuse_protected

#: Every RPC this module registers (pinned desktop-only).
SEARCH_RPCS: tuple[str, ...] = ("search.everything", "search.job")
KIND = "search.meaning"
_REGISTRY = "search_jobs"
SCOPES = ("sources", "passages", "notes", "pads", "threads", "exchanges")
Scope = Literal["sources", "passages", "notes", "pads", "threads", "exchanges"]
#: Groups with no meaning index: they are searched by words only, and the reply says so.
NO_MEANING_INDEX = {
    "pads": "Pads are searched by word matches.",
    "threads": "Questions and replies are searched by word matches.",
    "exchanges": "Questions and replies are searched by word matches.",
}
_MEANING_LISTS = frozenset({"meaning", "rewrite_meaning"})


class SearchEverythingInput(ParamsModel):
    selection: PassageSelection | None = None
    block_ids: list[str] = Field(default_factory=list)
    query: str = Field(min_length=1, max_length=CS.MAX_QUERY_CHARS)
    desk_id: str | None = Field(default=None, min_length=1)
    #: The groups to search (all when omitted). "open on this desk" is the client's own group.
    scopes: list[Scope] | None = Field(default=None, max_length=len(SCOPES))


class SearchJobInput(ParamsModel):
    job_id: str = Field(min_length=1, max_length=128)


#: Searches by meaning running at once (a superseded one keeps its thread until its request returns).
MAX_RUNNING_SEARCHES = 4


def _jobs(ctx: SidecarContext) -> PJ.PolledJobs:
    # Search ids are the server's: only records of recent jobs are kept (a stale id reads expired).
    return PJ.registry(ctx, _REGISTRY, running=MAX_RUNNING_SEARCHES, remember_ids=False)


def _require_desk(repository: Any, desk_id: str) -> None:
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores import desks as desk_store

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        desk = desk_store.desk(connection, desk_id)
    if desk is None or desk.get("archived_at"):
        raise SidecarError("desk_not_found", "Couldn’t find the desk. Open a desk and search again.")


def _passages_state(vault: Any) -> tuple[bool, str | None]:
    """Whether the library's passages can be searched at all (the Reader and its retrieval on)."""

    from learnloop.reader import reader_dialogue as RD

    if not RD.reader_enabled(vault):
        return False, "the Reader is switched off (tutor_qa.reader_enabled = false)"
    return True, None


def _passages_meaning(vault: Any, repository: Any) -> tuple[bool, str | None, str | None]:
    """(searchable by meaning, why not, coverage label): the library's stored passage vectors."""

    from learnloop.source_retrieval.corpus import library_scope
    from learnloop.source_retrieval.library import meaning_search_state

    if not vault.config.source_retrieval.enabled:
        return False, "Similar-passage search is off. Word search is available.", None
    state = meaning_search_state(vault, repository, library_scope(repository))
    if state["status"] not in ("ready", "partial"):
        return False, "Similar-passage search is unavailable. Word search is available.", None
    coverage = None if state["status"] == "ready" else (
        f"Similar-passage search covers {state['sources_covered']} of {state['sources']} sources.")
    return True, None, coverage


def _passage_rows(repository: Any, hits: list[dict[str, Any]], *, basis: str) -> list[dict[str, Any]]:
    starts = CS.cue_starts(repository, [(str(hit["extraction_id"]), str(hit["span_id"])) for hit in hits])
    return [CS.passage_row(hit, starts.get((str(hit["extraction_id"]), str(hit["span_id"]))), basis=basis)
            for hit in hits]


def _note_row(hit: dict[str, Any], source_ids: CS.SourceIds, *, basis: str) -> dict[str, Any]:
    """A vault note as a result row that opens it: a Reader note or highlight at its passage in its book
    (``ref`` the source, ``target`` the passage and the note), a capture-inbox note in the notes panel
    (``target`` the note)."""

    note_key = str(hit.get("note_key") or "")
    kind, _, note_id = note_key.partition(":")
    extraction_id, span_id = hit.get("extraction_id"), hit.get("span_id")
    source_id = source_ids(str(extraction_id)) if extraction_id else None
    if kind == "annotation" and source_id and extraction_id:
        ref: dict[str, Any] = CS.source_ref(source_id, str(extraction_id)) or {}
        target: dict[str, Any] = {"note_key": note_key, "annotation_id": note_id,
                                  **({"span_id": span_id} if span_id else {})}
    else:
        ref = {"kind": "panel", "panel": "notes"}
        target = {"note_key": note_key, **({"capture_id": note_id} if kind == "capture" else {})}
    return {"note_kind": "note", "note_key": note_key, "note_ref_kind": kind or None, "title": hit.get("title"),
            "heading": hit.get("heading"), "snippet": hit.get("snippet"), "captured_on": hit.get("captured_on"),
            "by_meaning": basis == "meaning", "ref": ref, "target": target}


def _word_groups(ctx: SidecarContext, vault: Any, repository: Any, words: str, desk_id: str | None,
                 scopes: list[str]) -> list[dict[str, Any]]:
    from learnloop.source_retrieval.library import search_library
    from learnloop_sidecar.handlers.notes import notes_search_state, search_vault_notes

    found = CS.word_groups(repository, words, desk_id=desk_id, scopes=scopes)
    source_ids = CS.SourceIds(repository)
    groups: list[dict[str, Any]] = []
    for name in scopes:
        if name == "passages":
            searchable, reason = _passages_state(vault)
            if not searchable:
                groups.append(CS.off_group(name, str(reason)))
                continue
            hits = list(search_library(vault, repository, query=words, limit=CS.GROUP_ROWS + 1, deep=False)["hits"])
            groups.append(CS.group(name, _passage_rows(repository, hits[:CS.GROUP_ROWS], basis="words"),
                                   more=len(hits) > CS.GROUP_ROWS))
        elif name == "notes":
            gaps, more_gaps = found["gaps"]
            state = notes_search_state(vault)
            notes = search_vault_notes(ctx, vault, repository, query=words, mode="words")["hits"] if state["on"] else []
            # Whether more exist is read from every match before the cap, never from the capped rows.
            rows = [*(_note_row(hit, source_ids, basis="words") for hit in notes), *gaps]
            entry = CS.group(name, rows[:CS.GROUP_ROWS], more=more_gaps or len(rows) > CS.GROUP_ROWS)
            if not state["on"]:
                # The learner's words LearnLoop read are still searched; the notes themselves are not.
                entry["reason"] = state["reason"]
            groups.append(entry)
        else:
            groups.append(found[name])
    return groups


def _seen_keys(groups: list[dict[str, Any]]) -> dict[str, set[str]]:
    """What the words found, by group, so a meaning result repeats none of it."""

    seen: dict[str, set[str]] = {"passages": set(), "notes": set()}
    for entry in groups:
        for row in entry["rows"]:
            if entry["group"] == "passages":
                seen["passages"].add(f"{row['extraction_id']}:{row['span_id']}")
            elif entry["group"] == "notes" and row.get("note_key"):
                seen["notes"].add(str(row["note_key"]))
    return seen


def _meaning_group(name: str, rows: list[dict[str, Any]], *, more: bool, status: str = "ok",
                   reason: str | None = None) -> dict[str, Any]:
    """A group found by meaning; ``status`` ``unavailable`` or ``failed`` says why it holds nothing, so an
    unrun search is never shown as "nothing found"."""

    entry = CS.group(name, rows, more=more, basis="meaning")
    entry["status"] = status
    if reason:
        entry["reason"] = reason
    return entry


def _passages_by_meaning(vault: Any, repository: Any, words: str, seen: set[str],
                         coverage: str | None) -> dict[str, Any]:
    from learnloop.source_retrieval.library import search_library

    found = search_library(vault, repository, query=words, limit=CS.GROUP_ROWS + 1, deep=True)
    if "meaning" not in str(found.get("basis") or ""):
        # The deep pass ranked nothing by meaning: the query was not embedded, or the index could not be
        # read.
        entry = _meaning_group("passages", [], more=False, status="unavailable",
                               reason="Couldn’t search for similar passages. Try word matches.")
    else:
        hits = [hit for hit in found["hits"] if _MEANING_LISTS & set(hit.get("matched_by") or ())
                and f"{hit['extraction_id']}:{hit['span_id']}" not in seen]
        entry = _meaning_group("passages", _passage_rows(repository, hits[:CS.GROUP_ROWS], basis="meaning"),
                               more=len(hits) > CS.GROUP_ROWS)
    entry["retrieval_basis"] = found.get("basis")
    if coverage:
        entry["coverage"] = coverage
    return entry


def _notes_by_meaning(ctx: SidecarContext, vault: Any, repository: Any, words: str, seen: set[str]) -> dict[str, Any]:
    from learnloop_sidecar.handlers.notes import search_vault_notes

    found = search_vault_notes(ctx, vault, repository, query=words, mode="meaning")
    meaning = found.get("meaning") or {}
    status = str(meaning.get("status") or "")
    if status in ("unavailable", "empty"):
        return _meaning_group("notes", [], more=False, status="unavailable",
                              reason="Couldn’t search for similar notes. Try word matches.")
    source_ids = CS.SourceIds(repository)
    hits = [hit for hit in found["hits"] if str(hit.get("note_key")) not in seen]
    entry = _meaning_group("notes", [_note_row(hit, source_ids, basis="meaning") for hit in hits[:CS.GROUP_ROWS]],
                           more=len(hits) > CS.GROUP_ROWS)
    if status == "partial":
        entry["coverage"] = (f"by meaning over {meaning.get('covered')} of {meaning.get('total')} notes "
                             "(the rest are searched by words)")
    return entry


@method("search.everything", SearchEverythingInput)
def search_everything(ctx: SidecarContext, params: SearchEverythingInput) -> dict[str, Any]:
    """``{query, groups, meaning}``: the groups by words now, and the search by meaning's job or why none."""

    from learnloop.ai import model_use
    from learnloop_sidecar.handlers.notes import notes_search_state

    vault, repository = ctx.require_vault()

    def check_origin() -> None:
        places = set(block_places(vault, repository, params.block_ids))
        if params.selection:
            places.update(reading_places(params.selection.extraction_id, params.selection.span_ids))
        refuse_protected(vault, repository, places)

    check_origin()
    if params.desk_id is not None:
        _require_desk(repository, params.desk_id)
    jobs = _jobs(ctx)
    supersede_key = f"desk:{params.desk_id or ''}"
    # Every search from the desk replaces the one before, whether or not it searches by meaning itself.
    jobs.supersede(PJ.vault_key(ctx), supersede_key)
    words = CS.words_of(params.query)
    scopes = [name for name in SCOPES if params.scopes is None or name in params.scopes]
    if len(words) < CS.MIN_QUERY_CHARS:
        return versioned({"query": words, "groups": [], "meaning": {
            "status": "unavailable", "job_id": None,
            "unavailable": [{"group": name, "reason": "type at least two characters"} for name in scopes]}})
    groups = _word_groups(ctx, vault, repository, words, params.desk_id, scopes)

    meaning: list[str] = []
    unavailable: list[dict[str, Any]] = []
    coverage: str | None = None
    if "passages" in scopes:
        searchable, reason = _passages_state(vault)
        if searchable:
            searchable, reason, coverage = _passages_meaning(vault, repository)
        if searchable:
            meaning.append("passages")
        else:
            unavailable.append({"group": "passages", "reason": reason})
    if "notes" in scopes:
        state = notes_search_state(vault)
        if state["meaning"]:
            meaning.append("notes")
        else:
            unavailable.append({"group": "notes", "reason": "Similar-note search is unavailable. Try word matches."})
    unavailable.extend({"group": name, "reason": NO_MEANING_INDEX[name]} for name in scopes if name in NO_MEANING_INDEX)
    if meaning and model_use.waiting(vault.root):
        # Nothing is sent before the learner's OK to use AI; the words still answer.
        unavailable.extend({"group": name, "reason": "waiting for your OK to use AI"} for name in meaning)
        meaning = []
    if not meaning:
        return versioned({"query": words, "groups": groups,
                          "meaning": {"status": "unavailable", "job_id": None, "unavailable": unavailable}})

    seen = _seen_keys(groups)

    def work(_job: PJ.PolledJob) -> dict[str, Any]:
        check_origin()
        out: list[dict[str, Any]] = []
        for name in meaning:
            try:
                out.append(_passages_by_meaning(vault, repository, words, seen["passages"], coverage)
                           if name == "passages" else _notes_by_meaning(ctx, vault, repository, words, seen["notes"]))
            except Exception as exc:  # noqa: BLE001 - word matches and other groups can still be shown
                error = PJ.as_job_error(exc, cancelled=_job.cancelled)
                reason = ("Give LearnLoop permission to use AI, then search again." if error.code == "waiting_for_ok"
                          else "Couldn’t finish this search. Edit your query to try again.")
                out.append(_meaning_group(name, [], more=False, status="failed", reason=reason))
        return {"groups": out, "unavailable": unavailable}

    try:
        job = jobs.start(ctx, kind=KIND, job_id=f"srch_{new_ulid()}", work=work, supersede_key=supersede_key)
    except SidecarError as busy:
        if busy.code != "jobs_busy":
            raise
        unavailable.extend({"group": name, "reason": "Similar-passage search is busy. Try word matches or search again."}
                           for name in meaning)
        return versioned({"query": words, "groups": groups,
                          "meaning": {"status": "unavailable", "job_id": None, "unavailable": unavailable}})
    return versioned({"query": words, "groups": groups, "meaning": {
        "status": "pending", "job_id": job.job_id, "groups": meaning, "unavailable": unavailable}})


def _job_payload(job: PJ.PolledJob) -> dict[str, Any]:
    from learnloop.ai import plan_fallback

    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    status = state["status"]
    error = state["error"] if status == PJ.FAILED else None
    result = state["result"] or {}
    return versioned({
        "job_id": job.job_id,
        "status": status,
        "done": bool(state["finished"]),
        # A superseded or cancelled search delivers nothing, even when its work finished.
        "groups": result.get("groups", []) if status == PJ.DONE else [],
        # The groups that could not be searched by meaning, carried on every poll (not only the start's reply).
        "unavailable": result.get("unavailable", []) if status == PJ.DONE else [],
        "error": None if error is None else {"code": error.code, "message": error.message,
                                             "retryable": error.retryable},
    })


@method("search.job", SearchJobInput)
def search_job(ctx: SidecarContext, params: SearchJobInput) -> dict[str, Any]:
    """The search by meaning's state, at once (never a wait on the request path)."""

    ctx.require_vault()
    jobs = _jobs(ctx)
    vault = PJ.vault_key(ctx)
    job = jobs.get(vault, params.job_id)
    if job is None:
        receipt = jobs.receipt(vault, params.job_id)
        if receipt is None:
            raise SidecarError("job_not_found", "This search expired. Change your query to try again.",
                               details={"job_id": params.job_id})
        status = PJ.CANCELLED if receipt.status == PJ.CANCELLED else PJ.EXPIRED
        return versioned({"job_id": params.job_id, "status": status, "done": True, "groups": [],
                          "unavailable": [], "error": None})
    return _job_payload(job)


__all__ = ["SCOPES", "SEARCH_RPCS", "SearchEverythingInput"]
