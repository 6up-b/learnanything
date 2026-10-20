"""Keep this comparison (reader workbench RW4d; spec_reader_workbench_v1 §7.8).

The sources spec's ``compare_sources`` (its §9.4) stores each comparison in
``source_comparisons`` and writes nothing else; keeping one as relation
proposals is the Reader's action (its §19). Pressing *keep comparison*, and
only that, turns the **stored** comparison (never what the client sends) into
proposals in P3 §7's source-object layer, through ``reader.source_objects``:

* each compared source with a line that passed the comparison's quote check
  becomes one ``source_objects`` row with one version (``object_type =
  'definition'`` when its block's effective role is a definition, else
  ``'claim'``; ``authorship = 'ai'``, ``status = 'proposed'``, its reading's
  ``revision_id``; one citation with the span, the block's content hash and the
  verified quote). The quote is checked again against the block as it is now:
  a line whose quote is no longer there (the book re-extracted) is not kept;
* each verified relation between two kept claims becomes a
  ``source_object_relations`` row (``authorship = 'ai'``, ``review_status =
  'proposed'``) typed by :data:`RELATION_MAP` (§3.4 item 15); the fine label,
  the relation's statement and its two quotes are kept on
  ``library_asks.kept_json`` (relations have no content column);
* *your take*: the learner's own line on a pair or a claim, a
  ``learner_connects`` relation with ``learner_text`` and ``authorship =
  'learner'`` (P3 invariant 8's connect-it semantics). It is the learner's
  note, in their voice: never read for gaps (UX §4.10) and never evidence;
* *remove* supersedes every proposal (a ``superseded`` status version for each
  claim, a superseded successor row for each relation); nothing is deleted.

Held-out material (exam protection) is never kept and never shown again: the
one predicate (``exam_material.exam_withheld``, the call RW4b's statement
reader makes) is asked about every compared span at the keep and at every
reopen, failing closed; a hit refuses before anything is written or quoted.

Nothing here writes a concept edge, facet merge, prerequisite, learning-object
change, attempt, evidence, mastery or plan; replay never reads these rows.
Reviewing a proposal is P3's existing path; nothing here promotes one. Kill
switch ``reader_compare.keep_enabled`` (and RW4a's ``reader_compare.enabled``
and the sources service's ``compare``).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import json
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.content.sources import exam_material as EM
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import library_asks as ask_store
from learnloop.db.stores.source_block_fts import block_content_hashes, blocks_by_key
from learnloop.db.stores.source_service import comparison_row, tool_call, tool_call_runs
from learnloop.ids import new_ulid
from learnloop.reader import source_objects as SO
from learnloop.source_retrieval.compare import COMPARE_PROMPT_VERSION, _quote_in
from learnloop.source_retrieval.corpus import block_roles
from learnloop.source_retrieval.library_ask import (
    LibraryAskError,
    anchor_learning_objects,
    compare_enabled,
    compare_table,
)
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.models import LoadedVault

#: The sources spec's comparison relations (and "complementary", which §3.4
#: item 15 maps too) onto the source-object layer's coarser types. The fine
#: label is kept in ``kept_json``; ``equivalent`` between two definitions is
#: an ``alternate_definition`` (see :func:`coarse_relation`).
RELATION_MAP: dict[str, str] = {
    "equivalent": "supports",
    "different_assumptions": "refines",
    "different_notation": "refines",
    "complementary": "refines",
    "disagreement": "contradicts",
    "unclear": "unresolved",
}
#: The learner's own take on a pair or a claim (P3's connect-it relation).
TAKE_RELATION = SO.CONNECT_IT_RELATION
#: Bounds on what the learner types (display sizes, not learning thresholds).
MAX_TAKE_CHARS = 1000
MAX_TAKES = 12
#: Requested perspectives the compare field accepts (prompt-size bounds).
MAX_PERSPECTIVES = 4
MAX_PERSPECTIVE_CHARS = 80
KEPT_VERSION = 1
#: Salience-only reader events RW4d's sidecar writes (never evidence).
EVENTS: tuple[str, ...] = ("comparison_kept", "comparison_removed", "comparison_reopened")


def keep_enabled(vault: LoadedVault) -> bool:
    """Keep is on: its own switch and everything RW4a's compare needs."""

    return compare_enabled(vault) and bool(vault.config.reader_compare.keep_enabled)


def tutor_keep_enabled(vault: LoadedVault) -> bool:
    """Keep on the tutor's comparison (RW1c's offer): the keep switch, the
    Reader's compare switch and the service's comparison, without requiring
    the library answer (the tutor's offer does not go through it)."""

    config = vault.config
    return bool(config.reader_compare.keep_enabled and config.reader_compare.enabled
                and config.source_service.enabled and config.source_service.compare
                and config.reader_inquiry.enabled and config.tutor_qa.reader_enabled)


def coarse_relation(fine: str, left_type: str, right_type: str) -> str | None:
    """§3.4 item 15's mapping; None for a label it does not know (not kept)."""

    if fine == "equivalent" and left_type == right_type == "definition":
        return "alternate_definition"
    return RELATION_MAP.get(fine)


def clean_perspectives(values: Sequence[str] | None) -> list[str]:
    """The requested perspectives as typed: trimmed, distinct, bounded."""

    kept: list[str] = []
    for value in values or ():
        text = " ".join(str(value or "").split())[:MAX_PERSPECTIVE_CHARS]
        if text and text.casefold() not in {k.casefold() for k in kept}:
            kept.append(text)
    return kept[:MAX_PERSPECTIVES]


def _key(entry: Mapping[str, Any]) -> tuple[str, str]:
    return (str(entry.get("extraction_id") or ""), str(entry.get("span_id") or ""))


def _key_str(key: tuple[str, str]) -> str:
    return f"{key[0]}:{key[1]}"


def _event(repository: Repository, event: str, payload: Mapping[str, Any], *, subject_id: str | None,
           clock: Clock | None = None) -> None:
    log_interaction_event(
        repository, kind="reader_action_invoked", origin="learner", subject_type="reader_extraction",
        subject_id=subject_id, payload=salience_payload({"event": event, **payload}), clock=clock,
    )


def held_out_now(vault: LoadedVault, repository: Repository, keys: Sequence[tuple[str, str]]) -> bool:
    """Whether any of ``keys`` is exam or held-out material now. The one
    predicate (``exam_material.exam_withheld``), asked as RW4b's statement
    reader asks it; it fails closed (an unreadable predicate counts as held)."""

    wanted = [key for key in keys if key[0] and key[1]]
    if not wanted:
        return False
    try:
        return bool(EM.exam_withheld(vault, repository, wanted))
    except Exception:  # noqa: BLE001 - an unreadable predicate never keeps or shows material (fail closed)
        return True


def _refuse_held_out(vault: LoadedVault, repository: Repository, keys: Sequence[tuple[str, str]]) -> None:
    if held_out_now(vault, repository, keys):
        raise LibraryAskError(
            "exam_material",
            "Part of this comparison is held out for an exam now, so it isn't kept or shown. Nothing was saved.")


def _stored(repository: Repository, comparison_id: str | None) -> dict[str, Any]:
    if not comparison_id:
        raise LibraryAskError("validation_error", "Compare the passages first; there is no comparison to keep.")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stored = comparison_row(connection, comparison_id)
    if stored is None:
        raise LibraryAskError("not_found", f"Unknown comparison {comparison_id}.")
    return stored


def _sources(stored: Mapping[str, Any], shown: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """The stored comparison's compared sources (only those shown, when named)."""

    sources = [dict(entry) for entry in (stored.get("comparison") or {}).get("sources") or ()]
    if shown is not None:
        allowed = set(shown)
        sources = [entry for entry in sources if _key_str(_key(entry)) in allowed]
    return sources


def _relations(stored: Mapping[str, Any], refs: set[str]) -> list[dict[str, Any]]:
    return [dict(relation) for relation in (stored.get("comparison") or {}).get("relations") or ()
            if relation.get("left_ref") in refs and relation.get("right_ref") in refs]


def _plan(vault: LoadedVault, repository: Repository, stored: Mapping[str, Any],
          sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """What a keep would write, checked against the books as they are now (no writes)."""

    keys = [_key(entry) for entry in sources]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = blocks_by_key(connection, keys)
        roles = block_roles(connection, keys)
        hashes = {key: (block_content_hashes(connection, key[0], [key[1]]) or [None])[0] for key in keys}
    claims: dict[str, dict[str, Any]] = {}
    not_kept: list[dict[str, Any]] = []
    for entry in sources:
        key = _key(entry)
        ref = str(entry.get("ref") or "")
        block = blocks.get(key)
        run = repository.get_extraction_run(key[0]) if block is not None else None
        if block is None or run is None or not run.get("revision_id"):
            not_kept.append({"key": _key_str(key), "reason": "the passage is no longer in this reading"})
            continue
        lines = []
        for line in entry.get("contributions") or ():
            if _quote_in(str(line.get("quote") or ""), block.text):
                lines.append({"kind": "contribution", "text": str(line.get("contribution") or ""),
                              "perspective": line.get("perspective"), "quote": str(line.get("quote")),
                              "authorship": "ai", "label": "LearnLoop's reading (AI-written), quoting the source"})
            else:
                not_kept.append({"key": _key_str(key), "reason": "a line's quote is no longer in the passage"})
        claims[ref] = {"ref": ref, "key": key, "entry": dict(entry), "block": block, "lines": lines,
                       "revision_id": str(run["revision_id"]), "content_hash": hashes.get(key),
                       "object_type": "definition" if roles.get(key) == "definition" else "claim"}
    relations: list[dict[str, Any]] = []
    for relation in _relations(stored, set(claims)):
        left, right = claims[relation["left_ref"]], claims[relation["right_ref"]]
        fine = str(relation.get("relation") or "")
        coarse = coarse_relation(fine, left["object_type"], right["object_type"])
        ok = (coarse is not None and left["ref"] != right["ref"]
              and _quote_in(str(relation.get("left_quote") or ""), left["block"].text)
              and _quote_in(str(relation.get("right_quote") or ""), right["block"].text))
        if not ok:
            not_kept.append({"keys": [_key_str(left["key"]), _key_str(right["key"])],
                             "reason": "a relation's quote is no longer in its passage" if coarse
                             else f"unknown relation {fine!r}"})
            continue
        relations.append({**relation, "relation_type": coarse, "fine": fine})
    # A claim is kept when it has a verified line of its own or a kept relation.
    in_relation = {ref for relation in relations for ref in (relation["left_ref"], relation["right_ref"])}
    kept_claims = {ref: claim for ref, claim in claims.items() if claim["lines"] or ref in in_relation}
    for ref, claim in claims.items():
        if ref not in kept_claims:
            not_kept.append({"key": _key_str(claim["key"]), "reason": "no checked line for this passage"})
    return {"passages": kept_claims, "relations": relations, "not_kept": not_kept}


def _quote_of(claim: Mapping[str, Any], relations: Sequence[Mapping[str, Any]]) -> str:
    if claim["lines"]:
        return str(claim["lines"][0]["quote"])
    for relation in relations:
        if relation["left_ref"] == claim["ref"]:
            return str(relation["left_quote"])
        if relation["right_ref"] == claim["ref"]:
            return str(relation["right_quote"])
    return ""


def _resolve_take(take: Mapping[str, Any], objects: Mapping[str, Mapping[str, Any]]) -> tuple[str, str | None, str]:
    text = " ".join(str(take.get("text") or "").split())
    if not text:
        raise LibraryAskError("validation_error", "Your take is empty.")
    if len(text) > MAX_TAKE_CHARS:
        raise LibraryAskError("validation_error", f"Your take is longer than {MAX_TAKE_CHARS} characters.")
    keys = [str(key) for key in dict.fromkeys(take.get("keys") or ())]
    if not 1 <= len(keys) <= 2 or any(key not in objects for key in keys):
        raise LibraryAskError("validation_error", "Your take names a passage that isn't kept in this comparison.")
    return str(objects[keys[0]]["id"]), (str(objects[keys[1]]["id"]) if len(keys) == 2 else None), text


def _check_takes(takes: Sequence[Mapping[str, Any]], keys: Sequence[str], *, already: int = 0) -> None:
    """Every take is valid against the claims that will be kept (before any write)."""

    if already + len(takes) > MAX_TAKES:
        raise LibraryAskError("validation_error", f"A comparison keeps at most {MAX_TAKES} takes.")
    placeholders = {key: {"id": key} for key in keys}
    for take in takes:
        _resolve_take(take, placeholders)


def _add_takes(repository: Repository, kept: dict[str, Any], takes: Sequence[Mapping[str, Any]], *,
               clock: Clock | None) -> list[dict[str, Any]]:
    objects = {entry["key"]: entry for entry in kept["objects"]}
    _check_takes(takes, list(objects), already=len(kept.get("takes") or ()))
    resolved = [(take, *_resolve_take(take, objects)) for take in takes]
    added = []
    for take, left, right, text in resolved:
        link = SO.link_relation(repository, source_object_id=left, related_object_id=right,
                                relation_type=TAKE_RELATION, learner_text=text, authorship="learner", clock=clock)
        added.append({"id": link["relation_id"], "relation_type": TAKE_RELATION, "learner_text": text,
                      "keys": [str(key) for key in dict.fromkeys(take.get("keys") or ())],
                      "authorship": "learner", "created_at": utc_now_iso(clock)})
    kept["takes"] = [*(kept.get("takes") or []), *added]
    return added


def _write(vault: LoadedVault, repository: Repository, *, ask: Mapping[str, Any], stored: Mapping[str, Any],
           plan: Mapping[str, Any], caller: str, clock: Clock | None,
           learning_object_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Write the proposals (through reader.source_objects) and return kept_json."""

    provenance = {"comparison_id": stored["id"], "model": stored.get("model"),
                  "prompt_version": stored.get("prompt_version") or COMPARE_PROMPT_VERSION,
                  "ledger_ids": list(stored.get("ledger_ids") or []), "kept_by": "learner", "caller": caller}
    objects: list[dict[str, Any]] = []
    object_ids: dict[str, str] = {}
    relations = list(plan["relations"])
    for ref, claim in plan["passages"].items():
        entry = claim["entry"]
        quote = _quote_of(claim, relations)
        written = SO.author_source_object(
            repository, source_id=str(entry.get("source_id")), revision_id=claim["revision_id"],
            object_type=claim["object_type"], exact_text=quote,
            content={"kept_from": "source_comparison", "comparison_id": stored["id"], "ask_id": ask["id"],
                     "query": stored.get("query_md"), "lines": claim["lines"],
                     "source_label": "source-authored", "source_title": entry.get("source_title")},
            citations=[{"revision_id": claim["revision_id"], "span_id": claim["key"][1],
                        "block_content_hash": claim["content_hash"], "exact_quote": quote}],
            authorship="ai", status="proposed", model_provenance=provenance, clock=clock,
        )
        object_ids[ref] = written["source_object_id"]
        objects.append({"id": written["source_object_id"], "version_id": written["version_id"], "ref": ref,
                        "key": _key_str(claim["key"]), "extraction_id": claim["key"][0], "span_id": claim["key"][1],
                        "source_id": entry.get("source_id"), "source_title": entry.get("source_title"),
                        "page": entry.get("page"), "object_type": claim["object_type"],
                        "revision_id": claim["revision_id"], "quotes": [line["quote"] for line in claim["lines"]]})
    kept_relations: list[dict[str, Any]] = []
    for relation in relations:
        link = SO.link_relation(repository, source_object_id=object_ids[relation["left_ref"]],
                                related_object_id=object_ids[relation["right_ref"]],
                                relation_type=relation["relation_type"], authorship="ai", clock=clock)
        kept_relations.append({
            "id": link["relation_id"], "relation_type": relation["relation_type"], "fine": relation["fine"],
            "left_ref": relation["left_ref"], "right_ref": relation["right_ref"],
            "left_object_id": object_ids[relation["left_ref"]], "right_object_id": object_ids[relation["right_ref"]],
            "statement": relation.get("statement"), "left_quote": relation.get("left_quote"),
            "right_quote": relation.get("right_quote"), "authorship": "ai",
            "label": "LearnLoop's inferred relation (AI-written)"})
    keys = [obj["key"] for obj in objects]
    # The LOs the card reads it under: the question's own (its anchor, or the
    # tutor request's), then each kept passage's provenance-linked LOs.
    learning_objects: list[str] = [lo for lo in dict.fromkeys(learning_object_ids) if lo in vault.learning_objects]
    for obj in objects:
        for lo_id in anchor_learning_objects(vault, repository, extraction_id=obj["extraction_id"],
                                             span_ids=[obj["span_id"]]):
            if lo_id not in learning_objects:
                learning_objects.append(lo_id)
    return {"version": KEPT_VERSION, "comparison_id": stored["id"], "caller": caller, "kept_at": utc_now_iso(clock),
            "objects": objects, "relations": kept_relations, "takes": [], "not_kept": list(plan["not_kept"]),
            "keys": keys, "learning_object_ids": learning_objects,
            "requested_perspectives": list(stored.get("requested_perspectives") or [])}


def _save(repository: Repository, ask_id: str, kept: Mapping[str, Any] | None, *, kept_at: str | None) -> None:
    with repository.connection() as connection:
        ask_store.update_ask(connection, ask_id, kept_json=None if kept is None else json.dumps(kept, sort_keys=True),
                             kept_at=kept_at)
        connection.commit()


def kept_state(kept: Mapping[str, Any] | None, *, kept_at: str | None) -> dict[str, Any] | None:
    """What the Reader shows of a keep: ids, types and fine labels, the takes (no quotes)."""

    if not kept or kept_at is None:
        return None
    return {
        "kept_at": kept_at,
        "objects": [{"id": obj["id"], "key": obj["key"], "object_type": obj["object_type"],
                     "source_title": obj.get("source_title")} for obj in kept.get("objects") or ()],
        "relations": [{"id": rel["id"], "relation_type": rel["relation_type"], "fine": rel["fine"]}
                      for rel in kept.get("relations") or ()],
        "takes": [{"id": take["id"], "keys": take["keys"], "learner_text": take["learner_text"]}
                  for take in kept.get("takes") or ()],
        "not_kept": len(kept.get("not_kept") or ()),
        "status": "proposed",
        "label": "kept as proposals · nothing changes your map until you review them",
    }


def _keep(vault: LoadedVault, repository: Repository, ask: Mapping[str, Any], *, shown: Sequence[str] | None,
          takes: Sequence[Mapping[str, Any]], caller: str, clock: Clock | None) -> dict[str, Any]:
    if ask.get("kept") and ask.get("kept_at"):
        # Kept already (a second press, or a take added after keeping): the
        # proposals stay as they are; only new takes are written.
        kept = dict(ask["kept"])
        _refuse_held_out(vault, repository, [tuple(key.split(":", 1)) for key in kept.get("keys") or ()])
        added = _add_takes(repository, kept, takes, clock=clock) if takes else []
        if added:
            _save(repository, ask["id"], kept, kept_at=ask["kept_at"])
        return {"ask_id": ask["id"], "kept": {**(kept_state(kept, kept_at=ask["kept_at"]) or {}), "ask_id": ask["id"]},
                "added_takes": len(added), "already_kept": True}
    stored = _stored(repository, ask.get("comparison_id"))
    sources = _sources(stored, shown)
    # Held out now (or at any time since the comparison was made): refused
    # before anything is written, for every source the comparison holds.
    _refuse_held_out(vault, repository, [_key(entry) for entry in _sources(stored)])
    plan = _plan(vault, repository, stored, sources)
    if len(plan["passages"]) < 1:
        raise LibraryAskError("validation_error", "Nothing in this comparison could be kept: no checked line is left.")
    _check_takes(takes, [_key_str(claim["key"]) for claim in plan["passages"].values()])
    kept = _write(vault, repository, ask=ask, stored=stored, plan=plan, caller=caller, clock=clock,
                  learning_object_ids=_question_learning_objects(repository, ask))
    if (ask.get("kept") or {}).get("removed"):
        # Kept again after a remove: the earlier keep's history stays on the row.
        kept["removed"] = list(ask["kept"]["removed"])
    if takes:
        _add_takes(repository, kept, takes, clock=clock)
    _save(repository, ask["id"], kept, kept_at=kept["kept_at"])
    _event(repository, "comparison_kept", {
        "extraction_id": ask.get("extraction_id"), "claim_count": len(kept["objects"]),
        "relations": len(kept["relations"]), "takes": len(kept["takes"]), "caller": caller,
    }, subject_id=ask.get("extraction_id"), clock=clock)
    return {"ask_id": ask["id"], "kept": {**(kept_state(kept, kept_at=kept["kept_at"]) or {}), "ask_id": ask["id"]},
            "added_takes": len(kept["takes"]), "already_kept": False}


def _question_learning_objects(repository: Repository, ask: Mapping[str, Any]) -> list[str]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        full = ask_store.ask_row(connection, ask["id"]) or {}
    anchor = (full.get("anchor") or {}).get("learning_object_ids") or []
    caller = (full.get("manifest") or {}).get("caller") or {}
    given = caller.get("learning_object_ids") or [] if isinstance(caller, Mapping) else []
    return [str(lo) for lo in dict.fromkeys([*anchor, *given])]


def _row(repository: Repository, ask_id: str) -> dict[str, Any]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = ask_store.kept_row(connection, ask_id)
    if row is None:
        raise LibraryAskError("not_found", f"Unknown library question {ask_id}.")
    return row


def keep(vault: LoadedVault, repository: Repository, ask_id: str, *,
         takes: Sequence[Mapping[str, Any]] = (), clock: Clock | None = None) -> dict[str, Any]:
    """Keep a library ask's comparison (the learner pressed *keep comparison*)."""

    row = _row(repository, ask_id)
    kept = row.get("kept") or {}
    if row.get("kept_at") and row.get("comparison_id") and kept.get("comparison_id") != row["comparison_id"]:
        # This question's first comparison is kept and the learner compared
        # again (other pins or perspectives): the new comparison is kept on its
        # own row, so each kept comparison keeps its own ids and history (a
        # second press finds that row rather than forking again).
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            others = [other for other in ask_store.asks_for_comparison(
                connection, row["comparison_id"], caller=str(row.get("caller") or "learner")) if other != ask_id]
        forked = next((found for other in others if (found := _row(repository, other)).get("kept_at")
                       and (found.get("kept") or {}).get("comparison_id") == row["comparison_id"]), None)
        if forked is None:
            new_id = "la_" + new_ulid()
            with repository.connection() as connection:
                ask_store.fork_ask(connection, ask_id, new_id=new_id, created_at=utc_now_iso(clock))
                ask_store.update_ask(connection, new_id, comparison_id=row["comparison_id"],
                                     requested_perspectives_json=json.dumps(row.get("requested_perspectives") or []))
                connection.commit()
            forked = _row(repository, new_id)
        row = forked
    return _keep(vault, repository, row, shown=None, takes=takes, caller=str(row.get("caller") or "learner"),
                 clock=clock)


def compare_kept_state(repository: Repository, ask_id: str, comparison_id: str | None) -> dict[str, Any] | None:
    """Whether the comparison just shown is the one this ask keeps (for the table)."""

    if not comparison_id:
        return None
    row = _row(repository, ask_id)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        candidates = [ask_id, *ask_store.asks_for_comparison(connection, comparison_id,
                                                             caller=str(row.get("caller") or "learner"))]
    for candidate in dict.fromkeys(candidates):
        found = _row(repository, candidate)
        kept = found.get("kept") or {}
        if found.get("kept_at") and kept.get("comparison_id") == comparison_id:
            return {**(kept_state(kept, kept_at=found["kept_at"]) or {}), "ask_id": candidate}
    return None


def tutor_comparison(repository: Repository, tool_call_id: str) -> dict[str, Any]:
    """The tutor's comparison request and its latest successful run (what was shown)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        request = tool_call(connection, tool_call_id)
        runs = tool_call_runs(connection, tool_call_id) if request is not None else []
    if request is None or request.get("row_kind") != "request" or request.get("tool") != "compare_sources":
        raise LibraryAskError("not_found", f"No comparison request {tool_call_id}.")
    ran = [run for run in runs if run.get("status") == "ran" and run.get("result_ref")]
    if not ran:
        raise LibraryAskError("validation_error", "This comparison hasn't run; press it first.")
    run = ran[-1]
    return {"request": request, "run": run, "comparison_id": str(run["result_ref"]),
            "shown": [str(key) for key in run.get("result_keys") or ()]}


def keep_tutor(vault: LoadedVault, repository: Repository, tool_call_id: str, *, extraction_id: str | None = None,
               takes: Sequence[Mapping[str, Any]] = (), clock: Clock | None = None) -> dict[str, Any]:
    """Keep the tutor's comparison (RW1c's *how do your books treat this?*,
    pressed and shown). Only the sources its run showed are kept; the keep is
    recorded on a ``library_asks`` row with ``caller = 'tutor'``."""

    found = tutor_comparison(repository, tool_call_id)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        existing = ask_store.asks_for_comparison(connection, found["comparison_id"], caller="tutor")
    if existing:
        row = _row(repository, existing[0])
    else:
        stored = _stored(repository, found["comparison_id"])
        # Nothing is written for a comparison that cannot be kept (held out).
        _refuse_held_out(vault, repository, [_key(entry) for entry in _sources(stored)])
        ask_id = "la_" + new_ulid()
        with repository.connection() as connection:
            ask_store.insert_ask(connection, {
                "id": ask_id, "caller": "tutor", "entry": "reader", "query_md": str(stored.get("query_md") or ""),
                "query_hash": str(stored.get("query_hash") or ""), "extraction_id": extraction_id,
                "anchor": {}, "personalized": False,
                "requested_perspectives": list(stored.get("requested_perspectives") or []),
                "manifest": {"caller": dict(found["request"].get("context") or {}), "tool_call_id": tool_call_id,
                             "run_id": found["run"]["id"], "shown_keys": found["shown"]},
                "organizer": {"status": "not_run"}, "prompt_version": stored.get("prompt_version"),
                "created_at": utc_now_iso(clock),
            })
            ask_store.update_ask(connection, ask_id, comparison_id=found["comparison_id"],
                                 question_event_id=found["request"].get("caller_ref"))
            connection.commit()
        row = _row(repository, ask_id)
    result = _keep(vault, repository, row, shown=found["shown"], takes=takes, caller="tutor", clock=clock)
    return {**result, "tool_call_id": tool_call_id}


def remove(vault: LoadedVault, repository: Repository, ask_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """*Remove*: the keep's proposals are superseded (append-only), never deleted."""

    row = _row(repository, ask_id)
    kept = row.get("kept")
    if not kept or not row.get("kept_at"):
        return {"ask_id": ask_id, "kept": None, "removed": False}
    superseded: list[str] = []
    for obj in kept.get("objects") or ():
        SO.review_source_object(repository, source_object_id=obj["id"], status="superseded", clock=clock)
        superseded.append(obj["id"])
    successors = []
    for relation in [*(kept.get("relations") or ()), *(kept.get("takes") or ())]:
        successors.append(SO.supersede_relation(repository, relation_id=relation["id"], clock=clock)["relation_id"])
    history = list(kept.get("removed") or [])
    history.append({"removed_at": utc_now_iso(clock), "objects": superseded, "relation_successors": successors})
    _save(repository, ask_id, {**kept, "removed": history}, kept_at=None)
    _event(repository, "comparison_removed", {"extraction_id": row.get("extraction_id"),
                                              "claim_count": len(superseded), "relations": len(successors)},
           subject_id=row.get("extraction_id"), clock=clock)
    return {"ask_id": ask_id, "kept": None, "removed": True}


def _live(repository: Repository) -> list[dict[str, Any]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return ask_store.kept_asks(connection)


def kept_marks(vault: LoadedVault, repository: Repository, extraction_id: str) -> dict[str, Any]:
    """The ``⇄`` marks for one reading: each span with a live kept comparison
    (the learner's own mark, outside the cue budget). A comparison with held-out
    material now is left out (its table could not be reopened)."""

    marks: dict[str, dict[str, Any]] = {}
    for row in _live(repository):
        kept = row["kept"] or {}
        keys = [tuple(key.split(":", 1)) for key in kept.get("keys") or ()]
        mine = [key for key in keys if key[0] == extraction_id]
        if not mine or held_out_now(vault, repository, keys):
            continue
        others = sorted({obj.get("source_title") or "a source" for obj in kept.get("objects") or ()
                         if obj["extraction_id"] != extraction_id})
        for key in mine:
            marks.setdefault(key[1], {"span_id": key[1], "ask_ids": [], "kept_at": row["kept_at"],
                                      "other_sources": others})
            marks[key[1]]["ask_ids"].append(row["id"])
    return {"extraction_id": extraction_id, "marks": sorted(marks.values(), key=lambda mark: mark["span_id"]),
            "label": "a comparison you kept"}


def reopen(vault: LoadedVault, repository: Repository, ask_id: str, *, open_source_id: str | None = None,
           clock: Clock | None = None) -> dict[str, Any]:
    """The table of a kept comparison, rebuilt from the stored row (no model
    call), showing only what was kept; refused while any of it is held out."""

    row = _row(repository, ask_id)
    kept = row.get("kept")
    if not kept or not row.get("kept_at"):
        raise LibraryAskError("not_found", "This comparison isn't kept any more.")
    keys = [tuple(key.split(":", 1)) for key in kept.get("keys") or ()]
    _refuse_held_out(vault, repository, keys)
    stored = _stored(repository, kept.get("comparison_id"))
    shown = set(kept.get("keys") or ())
    # Only what was kept: its claims with their kept lines, its kept relations.
    quotes = {obj["key"]: set(obj.get("quotes") or ()) for obj in kept.get("objects") or ()}
    sources = []
    for entry in _sources(stored, sorted(shown)):
        lines = [line for line in entry.get("contributions") or ()
                 if line.get("quote") in quotes.get(_key_str(_key(entry)), set())]
        sources.append({**entry, "contributions": lines})
    pairs = {(rel.get("left_ref"), rel.get("right_ref"), rel.get("fine")) for rel in kept.get("relations") or ()}
    relations = [rel for rel in _relations(stored, {entry.get("ref") for entry in sources})
                 if (rel.get("left_ref"), rel.get("right_ref"), rel.get("relation")) in pairs]
    payload = {"status": "ok", "comparison_id": stored["id"], "sources": sources, "relations": relations,
               "manifest": {}, "also_discussed_in": [], "unverified_sources": [], "dropped_pins": [],
               "dropped_lines": []}
    table = compare_table(payload, first_source_id=open_source_id)
    perspectives = list(stored.get("requested_perspectives") or [])
    if perspectives:
        table["requested_perspectives"] = perspectives
        table["missing_perspectives"] = list((stored.get("comparison") or {}).get("missing_perspectives") or [])
    _event(repository, "comparison_reopened", {"extraction_id": row.get("extraction_id"), "claim_count": len(shown)},
           subject_id=row.get("extraction_id"), clock=clock)
    return {"ask_id": ask_id, **table, "kept": {**(kept_state(kept, kept_at=row["kept_at"]) or {}), "ask_id": ask_id},
            "query": row.get("query"), "kept_relations": [
                {"fine": rel["fine"], "relation_type": rel["relation_type"], "statement": rel.get("statement")}
                for rel in kept.get("relations") or ()]}


def compared_on(repository: Repository, keys: Sequence[str]) -> list[dict[str, Any]]:
    """For a later library ask: the kept comparisons sharing its passages
    ("you compared these on 3 Oct"), newest first."""

    wanted = set(keys)
    found = []
    for row in _live(repository):
        shared = sorted(wanted & set((row["kept"] or {}).get("keys") or ()))
        if shared:
            found.append({"ask_id": row["id"], "kept_at": row["kept_at"], "keys": shared})
    return found


def kept_comparisons_for_card(repository: Repository, *, learning_object_ids: Sequence[str],
                              as_of: str | None = None) -> list[dict[str, Any]]:
    """Kept comparisons on these LOs (for RW6b's ``reader_activity_for_card``,
    spec §9.4): a pure, deterministic read of ``library_asks.kept_json``,
    typed, with no prose and no quotes. Nothing in it is evidence (W1)."""

    wanted = set(learning_object_ids)
    cutoff = parse_utc(as_of) if as_of else None
    entries = []
    for row in _live(repository):
        kept = row["kept"] or {}
        los = [lo for lo in kept.get("learning_object_ids") or () if lo in wanted]
        kept_at = parse_utc(row["kept_at"])
        if not los or (cutoff is not None and kept_at is not None and kept_at > cutoff):
            continue
        entries.append({
            "kind": "kept_comparison", "ask_id": row["id"], "kept_at": row["kept_at"], "caller": row["caller"],
            "learning_object_ids": los,
            "sources": [{"source_id": obj.get("source_id"), "key": obj["key"], "object_type": obj["object_type"],
                         "source_object_id": obj["id"]} for obj in kept.get("objects") or ()],
            "relations": [{"relation_type": rel["relation_type"], "fine": rel["fine"], "relation_id": rel["id"]}
                          for rel in kept.get("relations") or ()],
            "takes": len(kept.get("takes") or ()),
            "status": "proposed",
        })
    entries.sort(key=lambda entry: (entry["kept_at"], entry["ask_id"]))
    return entries


__all__ = [
    "EVENTS",
    "MAX_PERSPECTIVES",
    "RELATION_MAP",
    "TAKE_RELATION",
    "clean_perspectives",
    "coarse_relation",
    "compare_kept_state",
    "compared_on",
    "held_out_now",
    "keep",
    "keep_enabled",
    "keep_tutor",
    "kept_comparisons_for_card",
    "kept_marks",
    "kept_state",
    "remove",
    "reopen",
    "tutor_comparison",
    "tutor_keep_enabled",
]
