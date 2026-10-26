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
  Each successor's predecessor is recorded on the ask row's removal history
  (``relation_successors``), the only writer of relation successors, and
  :func:`relation_head` reads a relation's current head from it.

A comparison is kept at most once: the compare service reuses a stored
comparison for the same question and passages, so Keep (and adding a take)
first resolves the row that keeps it now (:func:`live_keep_of`), whichever ask
holds it, and that row's own caller chooses the availability check
(``guard``). The card's read (:func:`kept_comparisons_for_card`) asks the
held-out predicate too, failing closed.

Keep, adding a take and remove each run as one transaction
(``Repository.atomic()``, ``BEGIN IMMEDIATE``): the state read, the proposals,
the keep record and the event commit together or not at all, and a second
request waits for the first and then reads its result. A take's key is its
passages and its words (:func:`take_key`): replaying a take adds nothing.
Every mutation names the comparison it was shown under (``comparison_id``);
one the question no longer shows, and nothing keeps, is refused.

Held-out material (exam protection) is never kept and never shown again: the
one predicate (``exam_material.exam_withheld``, the call RW4b's statement
reader makes) is asked about **every passage that contributed to the
comparison** (its sources, counterparts, unverified sources and dropped pins,
the ask's anchor, the tutor question's passages:
``reader.source_objects.comparison_passages``). Keep, keep_tutor and adding a
take ask it inside the transaction before any write, and reopen at every
read; a hit, unresolvable provenance or an unreadable predicate refuses
(``comparison_withheld``). Every other read (the marks, "you compared these
on", the table's keep state, the card, ``reader.source_objects`` and the
proposal inbox) leaves such a comparison out whole: no object, line,
relation, statement or take derived from it is returned. Ledger rows stay.

Nothing here writes a concept edge, facet merge, prerequisite, learning-object
change, attempt, evidence, mastery or plan; replay never reads these rows.
Reviewing a proposal is P3's existing path; nothing here promotes one. Kill
switch ``reader_compare.keep_enabled`` (and RW4a's ``reader_compare.enabled``
and the sources service's ``compare``).
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.content.sources import exam_material as EM
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
#: The availability check of the row a keep writes on, chosen by the caller
#: (the sidecar) from that row's persisted caller; it raises to refuse.
RowGuard = Callable[[Mapping[str, Any]], None]


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


def _withheld_rows(vault: LoadedVault, repository: Repository,
                   rows: Sequence[Mapping[str, Any]]) -> frozenset[str]:
    """The ids of ``rows`` whose comparison is withheld whole: any passage that
    contributed to it is held out now, or its provenance cannot be resolved
    (``reader.source_objects.withheld_comparisons``, failing closed)."""

    pairs = {str(row["id"]): (str((row.get("kept") or {}).get("comparison_id") or row.get("comparison_id") or ""),
                              str(row["id"])) for row in rows}
    held = SO.withheld_comparisons(vault, repository, list(pairs.values()))
    return frozenset(row_id for row_id, pair in pairs.items() if not pair[0] or pair in held)


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


def _comparison_withheld() -> LibraryAskError:
    return LibraryAskError(
        "comparison_withheld",
        "Part of this comparison is held out for an exam now (or its sources can't be checked), so it isn't "
        "kept or shown. Nothing was saved.")


def _refuse_comparison(vault: LoadedVault, repository: Repository, comparison_id: str | None, *,
                       ask_id: str | None = None, question_event_id: str | None = None,
                       keys: Sequence[tuple[str, str]] = (), ask_ids: Sequence[str] = (),
                       question_event_ids: Sequence[str] = ()) -> None:
    """Refuse (``comparison_withheld``) unless every passage that contributed
    to the comparison is readable now: its sources, counterparts, unverified
    sources and dropped pins, the ask's anchor and binding, the tutor
    question's passages (``reader.source_objects.comparison_passages``) and
    ``keys``. Unresolvable provenance or an unreadable predicate refuses too
    (fail closed). Asked before any write and at every read of a keep."""

    if not comparison_id:
        raise LibraryAskError("validation_error", "Compare the passages first; there is no comparison to keep.")
    try:
        passages = SO.comparison_passages(repository, str(comparison_id), ask_id=ask_id,
                                          question_event_id=question_event_id, ask_ids=ask_ids,
                                          question_event_ids=question_event_ids)
    except Exception as exc:  # noqa: BLE001 - unresolvable provenance is withheld (fail closed)
        raise _comparison_withheld() from exc
    wanted = sorted(passages | {key for key in keys if key[0] and key[1]})
    if held_out_now(vault, repository, wanted):
        raise _comparison_withheld()


def _stored(repository: Repository, comparison_id: str | None) -> dict[str, Any]:
    if not comparison_id:
        raise LibraryAskError("validation_error", "Compare the passages first; there is no comparison to keep.")
    with repository.connection() as connection:
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
    with repository.connection() as connection:
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


def _take_parts(take: Mapping[str, Any]) -> tuple[list[str], str]:
    text = " ".join(str(take.get("text") if "text" in take else take.get("learner_text") or "").split())
    return [str(key) for key in dict.fromkeys(take.get("keys") or ())], text


def take_key(keys: Sequence[str], text: str) -> str:
    """A take's idempotency key: its passages (in order) and its words, as kept.
    The same take sent again (a retry after a lost response) is the same take."""

    payload = json.dumps([[str(key) for key in dict.fromkeys(keys)], " ".join(str(text).split())])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _kept_take_key(take: Mapping[str, Any]) -> str:
    return str(take.get("take_key") or take_key(take.get("keys") or (), str(take.get("learner_text") or "")))


def _resolve_take(take: Mapping[str, Any], objects: Mapping[str, Mapping[str, Any]]) -> tuple[str, str | None, str]:
    keys, text = _take_parts(take)
    if not text:
        raise LibraryAskError("validation_error", "Your take is empty.")
    if len(text) > MAX_TAKE_CHARS:
        raise LibraryAskError("validation_error", f"Your take is longer than {MAX_TAKE_CHARS} characters.")
    if not 1 <= len(keys) <= 2 or any(key not in objects for key in keys):
        raise LibraryAskError("validation_error", "Your take names a passage that isn't kept in this comparison.")
    return str(objects[keys[0]]["id"]), (str(objects[keys[1]]["id"]) if len(keys) == 2 else None), text


def _check_takes(takes: Sequence[Mapping[str, Any]], keys: Sequence[str], *,
                 kept_takes: Sequence[Mapping[str, Any]] = ()) -> list[Mapping[str, Any]]:
    """Every take is valid against the claims that will be kept (before any
    write); returns the ones not kept yet (a replayed take is not new, so a
    replay at the limit succeeds), refusing when those would pass the limit."""

    placeholders = {key: {"id": key} for key in keys}
    for take in takes:
        _resolve_take(take, placeholders)
    seen = {_kept_take_key(take) for take in kept_takes}
    new: list[Mapping[str, Any]] = []
    for take in takes:
        key = take_key(*_take_parts(take))
        if key not in seen:
            seen.add(key)
            new.append(take)
    if len(kept_takes) + len(new) > MAX_TAKES:
        raise LibraryAskError("validation_error", f"A comparison keeps at most {MAX_TAKES} takes.")
    return new


def _add_takes(repository: Repository, kept: dict[str, Any], takes: Sequence[Mapping[str, Any]], *,
               clock: Clock | None) -> list[dict[str, Any]]:
    objects = {entry["key"]: entry for entry in kept["objects"]}
    new = _check_takes(takes, list(objects), kept_takes=kept.get("takes") or ())
    resolved = [(take, *_resolve_take(take, objects)) for take in new]
    added = []
    for take, left, right, text in resolved:
        link = SO.link_relation(repository, source_object_id=left, related_object_id=right,
                                relation_type=TAKE_RELATION, learner_text=text, authorship="learner", clock=clock)
        keys = _take_parts(take)[0]
        added.append({"id": link["relation_id"], "relation_type": TAKE_RELATION, "learner_text": text,
                      "keys": keys, "take_key": take_key(keys, text),
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


def _contributors(repository: Repository, kept: Mapping[str, Any], *, ask_id: str, acting_ask_id: str | None,
                  question_event_id: str | None) -> list[dict[str, Any]]:
    """The keep's recorded contributors with those of this moment added: the
    ask acting now (when another ask owns the keep), the tutor question acting
    now, and the question each contributing ask holds **now** (the owner's,
    the acting ask's, every recorded ask's). Recorded, they are provenance a
    later reuse, a replaced question or a deleted one cannot drop: a recorded
    question that no longer resolves withholds the comparison (fix rounds 5
    and 6, F1 and F3)."""

    recorded = [dict(entry) for entry in kept.get("contributors") or () if isinstance(entry, Mapping)]
    wanted: list[dict[str, Any]] = []
    if acting_ask_id and acting_ask_id != ask_id:
        wanted.append({"ask_id": acting_ask_id})
    asks = [ask_id, *([acting_ask_id] if acting_ask_id else []),
            *(str(entry["ask_id"]) for entry in recorded if entry.get("ask_id"))]
    for contributor in dict.fromkeys(asks):
        with repository.connection() as connection:
            row = ask_store.kept_row(connection, contributor)
        if row is not None and row.get("question_event_id"):
            wanted.append({"question_event_id": str(row["question_event_id"])})
    if question_event_id:
        wanted.append({"question_event_id": question_event_id})
    for entry in wanted:
        if entry not in recorded:
            recorded.append(entry)
    return recorded


def _keep(vault: LoadedVault, repository: Repository, ask: Mapping[str, Any], *, shown: Sequence[str] | None,
          takes: Sequence[Mapping[str, Any]], caller: str, clock: Clock | None,
          question_event_id: str | None = None, acting_ask_id: str | None = None) -> dict[str, Any]:
    # Every passage that contributed to the comparison, as the union across
    # its reuse (every ask and tutor question that has shown, kept or added a
    # take to it, the one acting now included) is readable now, before
    # anything is written.
    live = bool(ask.get("kept") and ask.get("kept_at"))
    _refuse_comparison(vault, repository, (ask.get("kept") or {}).get("comparison_id") if live
                       else ask.get("comparison_id"), ask_id=str(ask["id"]), question_event_id=question_event_id,
                       ask_ids=[acting_ask_id] if acting_ask_id else (),
                       keys=[tuple(key.split(":", 1)) for key in (ask.get("kept") or {}).get("keys") or ()
                             if ":" in key] if live else ())
    if live:
        # Kept already (a second press, or a take added after keeping): the
        # proposals stay as they are; only new takes are written.
        kept = dict(ask["kept"])
        added = _add_takes(repository, kept, takes, clock=clock) if takes else []
        if added:
            # Whoever added it (another ask, the tutor's question) is recorded
            # on the keep, so every later read checks its passages too.
            kept["contributors"] = _contributors(repository, kept, ask_id=str(ask["id"]),
                                                 acting_ask_id=acting_ask_id,
                                                 question_event_id=question_event_id)
            _save(repository, ask["id"], kept, kept_at=ask["kept_at"])
        return {"ask_id": ask["id"], "kept": {**(kept_state(kept, kept_at=ask["kept_at"]) or {}), "ask_id": ask["id"]},
                "added_takes": len(added), "already_kept": True}
    stored = _stored(repository, ask.get("comparison_id"))
    sources = _sources(stored, shown)
    plan = _plan(vault, repository, stored, sources)
    if len(plan["passages"]) < 1:
        raise LibraryAskError("validation_error", "Nothing in this comparison could be kept: no checked line is left.")
    takes = _check_takes(takes, [_key_str(claim["key"]) for claim in plan["passages"].values()])
    kept = _write(vault, repository, ask=ask, stored=stored, plan=plan, caller=caller, clock=clock,
                  learning_object_ids=_question_learning_objects(repository, ask))
    if (ask.get("kept") or {}).get("removed"):
        # Kept again after a remove: the earlier keep's history stays on the row.
        kept["removed"] = list(ask["kept"]["removed"])
    kept["contributors"] = _contributors(repository, ask.get("kept") or {}, ask_id=str(ask["id"]),
                                         acting_ask_id=acting_ask_id, question_event_id=question_event_id)
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
    with repository.connection() as connection:
        full = ask_store.ask_row(connection, ask["id"]) or {}
    anchor = (full.get("anchor") or {}).get("learning_object_ids") or []
    caller = (full.get("manifest") or {}).get("caller") or {}
    given = caller.get("learning_object_ids") or [] if isinstance(caller, Mapping) else []
    return [str(lo) for lo in dict.fromkeys([*anchor, *given])]


def _row(repository: Repository, ask_id: str) -> dict[str, Any]:
    # Through the repository's connection: inside ``atomic()`` that is the
    # transaction's own, so the read sees (and serializes with) its writes.
    with repository.connection() as connection:
        row = ask_store.kept_row(connection, ask_id)
    if row is None:
        raise LibraryAskError("not_found", f"Unknown library question {ask_id}.")
    return row


def kept_ask(repository: Repository, ask_id: str) -> dict[str, Any]:
    """An ask's caller, comparison and keep state (``not_found`` when unknown)."""

    return _row(repository, ask_id)


def _stale() -> LibraryAskError:
    return LibraryAskError(
        "stale_comparison",
        "This isn't the comparison this question shows any more, and it isn't kept. Compare again to keep it.")


def _fork_for(repository: Repository, row: Mapping[str, Any], comparison_id: str, *,
              clock: Clock | None) -> dict[str, Any]:
    """The row that keeps ``comparison_id`` for this question, forked when none does."""

    with repository.connection() as connection:
        others = [other for other in ask_store.asks_for_comparison(
            connection, comparison_id, caller=str(row.get("caller") or "learner")) if other != row["id"]]
    forked = next((found for other in others if (found := _row(repository, other)).get("kept_at")
                   and (found.get("kept") or {}).get("comparison_id") == comparison_id), None)
    if forked is not None:
        return forked
    new_id = "la_" + new_ulid()
    with repository.connection() as connection:
        ask_store.fork_ask(connection, row["id"], new_id=new_id, created_at=utc_now_iso(clock))
        ask_store.update_ask(connection, new_id, comparison_id=comparison_id,
                             requested_perspectives_json=json.dumps(row.get("requested_perspectives") or []))
        connection.commit()
    return _row(repository, new_id)


def live_keep_of(repository: Repository, comparison_id: str | None, *,
                 prefer: str | None = None) -> dict[str, Any] | None:
    """The row that keeps ``comparison_id`` now, whichever ask holds it: the
    ask named by ``prefer`` when it does, else the earliest live keep of that
    comparison (any caller). The compare service reuses a stored comparison for
    the same question and passages, so a second ask (or the tutor) can be shown
    a comparison another row keeps; a comparison already kept is never kept
    twice (Codex verify of fix round 1, F1). Through the repository's
    connection: inside ``atomic()`` the read serializes with the keep's writes."""

    if not comparison_id:
        return None
    if prefer:
        found = _row(repository, prefer)
        if found.get("kept_at") and (found.get("kept") or {}).get("comparison_id") == comparison_id:
            return found
    live = [row for row in _live(repository) if (row.get("kept") or {}).get("comparison_id") == comparison_id]
    live.sort(key=lambda row: (str(row.get("kept_at") or ""), str(row.get("created_at") or ""), row["id"]))
    return live[0] if live else None


def keep(vault: LoadedVault, repository: Repository, ask_id: str, *, comparison_id: str | None = None,
         takes: Sequence[Mapping[str, Any]] = (), clock: Clock | None = None,
         guard: RowGuard | None = None) -> dict[str, Any]:
    """Keep a library ask's comparison (the learner pressed *keep comparison*),
    or add a take to it once kept.

    ``comparison_id`` is the comparison the learner was shown (the table's, or
    a reopened keep's); without it, the ask's latest. A take on an older kept
    comparison stays on that keep; a comparison another row keeps already (the
    service reused it for a second ask) is modified on that row, never kept
    again; the ask's newer comparison is kept on its own row; a comparison the
    ask neither shows nor keeps is refused.

    ``guard`` is asked about the row that will be written, inside the
    transaction and before anything is written: an existing keep is checked
    by its own persisted caller (a tutor keep by the tutor's rules)."""

    with repository.atomic():
        row = _row(repository, ask_id)
        kept = row.get("kept") or {}
        target = comparison_id or row.get("comparison_id")
        if row.get("kept_at") and kept.get("comparison_id") == target:
            pass  # this row keeps it: a second press, or a take added to it
        elif target and target == row.get("comparison_id"):
            existing = live_keep_of(repository, str(target))
            if existing is not None:
                # Kept already on another row (the service reused this
                # comparison for this ask): that keep is the one modified.
                row = existing
            elif row.get("kept_at"):
                # This question's first comparison is kept and the learner
                # compared again (other pins or perspectives): the new
                # comparison is kept on its own row, so each kept comparison
                # keeps its own ids and history (a second press finds it).
                # The fork copies this row's caller, so its guard is this row's.
                if guard is not None:
                    guard(row)
                # Refused before the fork row is written (the fork's anchor is this row's).
                _refuse_comparison(vault, repository, str(target), ask_id=str(row["id"]), ask_ids=[ask_id])
                row = _fork_for(repository, row, str(target), clock=clock)
                guard = None
        elif target and (existing := live_keep_of(repository, str(target))) is not None:
            # The comparison shown is kept on another row (the learner's table
            # under this ask, after this ask compared again): the owner's keep
            # is modified, this ask recorded as its contributor (fix round 6, F1).
            row = existing
        else:
            raise _stale()
        if guard is not None:
            guard(row)
        return _keep(vault, repository, row, shown=None, takes=takes, caller=str(row.get("caller") or "learner"),
                     clock=clock, acting_ask_id=ask_id)


def compare_kept_state(vault: LoadedVault, repository: Repository, ask_id: str,
                       comparison_id: str | None) -> dict[str, Any] | None:
    """Whether the comparison just shown is the one this ask keeps (for the
    table). A keep withheld whole (:func:`_withheld_rows`) is not shown."""

    # The same resolution Keep makes (live_keep_of): the table shows the keep
    # that a press would modify.
    found = live_keep_of(repository, comparison_id, prefer=ask_id)
    if found is None or found["id"] in _withheld_rows(vault, repository, [found]):
        return None
    return {**(kept_state(found["kept"], kept_at=found["kept_at"]) or {}), "ask_id": found["id"]}


def tutor_comparison(repository: Repository, tool_call_id: str) -> dict[str, Any]:
    """The tutor's comparison request and its latest successful run (what was shown)."""

    with repository.connection() as connection:
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
               takes: Sequence[Mapping[str, Any]] = (), clock: Clock | None = None,
               guard: RowGuard | None = None) -> dict[str, Any]:
    """Keep the tutor's comparison (RW1c's *how do your books treat this?*,
    pressed and shown). Only the sources its run showed are kept; the keep is
    recorded on a ``library_asks`` row with ``caller = 'tutor'``. A comparison
    another row keeps already is modified there (never kept twice), checked
    by ``guard`` under that row's own caller."""

    with repository.atomic():
        found = tutor_comparison(repository, tool_call_id)
        if not found["request"].get("caller_ref"):
            # The tutor question it was asked under is part of its provenance:
            # without it nothing can be checked, so nothing is kept (fail closed).
            raise _comparison_withheld()
        with repository.connection() as connection:
            existing = ask_store.asks_for_comparison(connection, found["comparison_id"], caller="tutor")
        live = live_keep_of(repository, found["comparison_id"], prefer=existing[0] if existing else None)
        if live is not None or existing:
            row = live if live is not None else _row(repository, existing[0])
            if guard is not None:
                guard(row)
        else:
            # Nothing is written for a comparison that cannot be kept: any
            # contributing passage (the tutor question's included) held out.
            _refuse_comparison(vault, repository, found["comparison_id"],
                               question_event_id=found["request"].get("caller_ref"))
            stored = _stored(repository, found["comparison_id"])
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
        result = _keep(vault, repository, row, shown=found["shown"], takes=takes, caller="tutor", clock=clock,
                       question_event_id=found["request"].get("caller_ref"))
    return {**result, "tool_call_id": tool_call_id}


#: What a removal's history keeps of the keep it removed (for the card's ``as_of``).
_SNAPSHOT_FIELDS = ("comparison_id", "caller", "kept_at", "objects", "relations", "takes", "keys",
                    "learning_object_ids", "contributors")


def remove(vault: LoadedVault, repository: Repository, ask_id: str, *, comparison_id: str | None = None,
           clock: Clock | None = None) -> dict[str, Any]:
    """*Remove*: the keep's proposals are superseded (append-only), never deleted.

    One transaction: every claim's superseded version, every relation's
    superseded successor (with the relation it supersedes recorded), the
    cleared keep (its snapshot kept in the history) and the event. With
    ``comparison_id`` (the comparison shown), a row that keeps another is refused."""

    with repository.atomic():
        row = _row(repository, ask_id)
        kept = row.get("kept")
        if not kept or not row.get("kept_at"):
            return {"ask_id": ask_id, "kept": None, "removed": False}
        if comparison_id and kept.get("comparison_id") != comparison_id:
            raise _stale()
        superseded: list[str] = []
        for obj in kept.get("objects") or ():
            SO.review_source_object(repository, source_object_id=obj["id"], status="superseded", clock=clock)
            superseded.append(obj["id"])
        successors = []
        for relation in [*(kept.get("relations") or ()), *(kept.get("takes") or ())]:
            successor = SO.supersede_relation(repository, relation_id=relation["id"], clock=clock)
            successors.append({"relation_id": successor["relation_id"], "supersedes": successor["supersedes"]})
        history = list(kept.get("removed") or [])
        history.append({"removed_at": utc_now_iso(clock), "kept_at": row["kept_at"], "objects": superseded,
                        "relation_successors": successors,
                        "kept": {field: kept.get(field) for field in _SNAPSHOT_FIELDS} | {"kept_at": row["kept_at"]}})
        _save(repository, ask_id, {**kept, "removed": history}, kept_at=None)
        _event(repository, "comparison_removed", {"extraction_id": row.get("extraction_id"),
                                                  "claim_count": len(superseded), "relations": len(successors)},
               subject_id=row.get("extraction_id"), clock=clock)
    return {"ask_id": ask_id, "kept": None, "removed": True}


def _with_keeps(repository: Repository) -> list[dict[str, Any]]:
    """Every ask that has kept a comparison, live or removed since."""

    with repository.connection() as connection:
        return ask_store.asks_with_keeps(connection)


def relation_lineage(repository: Repository) -> dict[str, str]:
    """Each superseded successor relation id -> the relation id it supersedes
    (RW4d's removals are the only writer of relation successors)."""

    lineage: dict[str, str] = {}
    for row in _with_keeps(repository):
        for entry in (row.get("kept") or {}).get("removed") or ():
            for successor in entry.get("relation_successors") or ():
                if isinstance(successor, Mapping) and successor.get("relation_id") and successor.get("supersedes"):
                    lineage[str(successor["relation_id"])] = str(successor["supersedes"])
    return lineage


def relation_head(repository: Repository, relation_id: str) -> dict[str, Any] | None:
    """The current head of a relation's lineage (itself while nothing supersedes it)."""

    forward = {prior: successor for successor, prior in relation_lineage(repository).items()}
    head, seen = relation_id, {relation_id}
    while head in forward and forward[head] not in seen:
        head = forward[head]
        seen.add(head)
    return repository.source_object_relation(head)


def _live(repository: Repository) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return ask_store.kept_asks(connection)


def kept_marks(vault: LoadedVault, repository: Repository, extraction_id: str, *,
               available: Callable[[Mapping[str, Any]], bool] | None = None) -> dict[str, Any]:
    """The ``⇄`` marks for one reading: each span with a live kept comparison
    (the learner's own mark, outside the cue budget). A comparison with held-out
    material now is left out (its table could not be reopened), and so is one
    ``available`` refuses (its caller's switch is off: reopen would refuse it)."""

    marks: dict[str, dict[str, Any]] = {}
    rows = []
    for row in _live(repository):
        if available is not None and not available(row):
            continue
        kept = row["kept"] or {}
        keys = [tuple(key.split(":", 1)) for key in kept.get("keys") or ()]
        mine = [key for key in keys if key[0] == extraction_id]
        if mine:
            rows.append((row, kept, keys, mine))
    # One read of the predicate for every candidate comparison (fail closed:
    # an unreadable predicate shows no mark).
    try:
        withheld = EM.exam_withheld(vault, repository, [key for _row, _kept, keys, _mine in rows for key in keys]) \
            if rows else frozenset()
    except Exception:  # noqa: BLE001 - fail closed
        rows, withheld = [], frozenset()
    # A comparison withheld whole (any contributing passage held out now, or
    # provenance unresolved) has no mark.
    whole = _withheld_rows(vault, repository, [row for row, *_rest in rows]) if rows else frozenset()
    for row, kept, keys, mine in rows:
        if any(key in withheld for key in keys) or row["id"] in whole:
            continue
        query = row.get("query")
        others = sorted({obj.get("source_title") or "a source" for obj in kept.get("objects") or ()
                         if obj["extraction_id"] != extraction_id})
        for key in mine:
            mark = marks.setdefault(key[1], {"span_id": key[1], "ask_ids": [], "kept_at": row["kept_at"],
                                             "other_sources": others, "comparisons": []})
            if row["id"] in mark["ask_ids"]:
                continue
            mark["ask_ids"].append(row["id"])
            # Every comparison kept on this passage, newest first, told apart
            # by its question and its date (the mark lists them all).
            mark["comparisons"].append({"ask_id": row["id"], "kept_at": row["kept_at"], "query": query,
                                        "other_sources": others})
    return {"extraction_id": extraction_id, "marks": sorted(marks.values(), key=lambda mark: mark["span_id"]),
            "label": "a comparison you kept"}


def _relation_signature(rel: Mapping[str, Any], fine: Any) -> tuple[Any, ...]:
    return (rel.get("left_ref"), rel.get("right_ref"), fine, rel.get("statement"), rel.get("left_quote"),
            rel.get("right_quote"))


def reopen(vault: LoadedVault, repository: Repository, ask_id: str, *, open_source_id: str | None = None,
           clock: Clock | None = None) -> dict[str, Any]:
    """The table of a kept comparison, rebuilt from the stored row (no model
    call), showing only what was kept; refused while any of it is held out."""

    row = _row(repository, ask_id)
    kept = row.get("kept")
    if not kept or not row.get("kept_at"):
        raise LibraryAskError("not_found", "This comparison isn't kept any more.")
    keys = [tuple(key.split(":", 1)) for key in kept.get("keys") or () if ":" in key]
    # Withheld whole while any passage that contributed to it is held out now.
    _refuse_comparison(vault, repository, kept.get("comparison_id"), ask_id=str(row["id"]), keys=keys)
    stored = _stored(repository, kept.get("comparison_id"))
    shown = set(kept.get("keys") or ())
    # Only what was kept: its claims with their kept lines, its kept relations.
    quotes = {obj["key"]: set(obj.get("quotes") or ()) for obj in kept.get("objects") or ()}
    sources = []
    for entry in _sources(stored, sorted(shown)):
        lines = [line for line in entry.get("contributions") or ()
                 if line.get("quote") in quotes.get(_key_str(_key(entry)), set())]
        sources.append({**entry, "contributions": lines})
    # Each kept relation exactly (endpoints, label, statement and both quotes),
    # once each: a same-labelled relation on the same pair that failed Keep's
    # recheck is not shown again.
    wanted = Counter(_relation_signature(rel, rel.get("fine")) for rel in kept.get("relations") or ())
    relations = []
    for rel in _relations(stored, {entry.get("ref") for entry in sources}):
        signature = _relation_signature(rel, rel.get("relation"))
        if wanted[signature] > 0:
            wanted[signature] -= 1
            relations.append(rel)
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


def compared_on(vault: LoadedVault, repository: Repository, keys: Sequence[str]) -> list[dict[str, Any]]:
    """For a later library ask: the kept comparisons sharing its passages
    ("you compared these on 3 Oct"), newest first; none withheld whole."""

    wanted = set(keys)
    found = []
    rows = [row for row in _live(repository) if wanted & set((row["kept"] or {}).get("keys") or ())]
    whole = _withheld_rows(vault, repository, rows) if rows else frozenset()
    for row in rows:
        if row["id"] in whole:
            continue
        shared = sorted(wanted & set((row["kept"] or {}).get("keys") or ()))
        if shared:
            found.append({"ask_id": row["id"], "kept_at": row["kept_at"], "keys": shared})
    return found


def _episodes(row: Mapping[str, Any]) -> list[tuple[dict[str, Any], str, str | None]]:
    """Each keep of an ask: (the keep, kept_at, removed_at or None while live)."""

    kept = row.get("kept") or {}
    episodes = [(dict(entry["kept"]), str(entry.get("kept_at") or entry["kept"].get("kept_at")),
                 str(entry["removed_at"])) for entry in kept.get("removed") or ()
                if isinstance(entry.get("kept"), Mapping) and entry.get("removed_at")
                and (entry.get("kept_at") or entry["kept"].get("kept_at"))]
    if row.get("kept_at"):
        episodes.append((dict(kept), str(row["kept_at"]), None))
    return episodes


def _episode_keys(kept: Mapping[str, Any]) -> set[tuple[str, str]]:
    """Every passage a keep holds: its keys and each kept object's span."""

    named = [str(key) for key in kept.get("keys") or ()]
    for obj in kept.get("objects") or ():
        if isinstance(obj, Mapping):
            named.append(f"{obj.get('extraction_id') or ''}:{obj.get('span_id') or ''}")
            named.append(str(obj.get("key") or ""))
    keys: set[tuple[str, str]] = set()
    for key in named:
        extraction, _sep, span = key.partition(":")
        if extraction and span:
            keys.add((extraction, span))
    return keys


def kept_comparisons_for_card(vault: LoadedVault, repository: Repository, *, learning_object_ids: Sequence[str],
                              as_of: str | None = None) -> list[dict[str, Any]]:
    """Kept comparisons on these LOs (for RW6b's ``reader_activity_for_card``,
    spec §9.4): a pure, deterministic read of ``library_asks.kept_json``,
    typed, with no prose and no quotes. Nothing in it is evidence (W1).

    ``as_of`` reads the card as it was then: the keeps live at that time
    (kept by then, not removed by then, from the removal history's snapshots)
    and only the takes written by then. Without it, the keeps live now.

    Held out **now** (exam protection), at any ``as_of``: an episode holding
    any passage the one predicate (``exam_material.exam_withheld``) withholds
    today is left out, and so is one whose passages cannot be named. The
    predicate is asked once; if it cannot be read, no entry is returned (fail
    closed; Codex verify of fix round 1, F3)."""

    wanted = set(learning_object_ids)
    cutoff = parse_utc(as_of) if as_of else None

    def by_then(value: Any) -> bool:
        when = parse_utc(str(value)) if value else None
        return cutoff is None or (when is not None and when <= cutoff)

    candidates = []
    for row in _with_keeps(repository):
        for kept, kept_at, removed_at in _episodes(row):
            live = removed_at is None if cutoff is None else (
                by_then(kept_at) and (removed_at is None or not by_then(removed_at)))
            los = [lo for lo in kept.get("learning_object_ids") or () if lo in wanted]
            if los and live:
                candidates.append((row, kept, kept_at, los, _episode_keys(kept)))
    if not candidates:
        return []
    try:
        withheld = EM.exam_withheld(vault, repository, sorted({key for *_rest, keys in candidates for key in keys}))
    except Exception:  # noqa: BLE001 - an unreadable predicate shows nothing (fail closed)
        return []
    # Comparison-wide too: an episode whose comparison had any contributing
    # passage held out now is left out (as its shared fields are redacted).
    shared = SO.withheld_comparisons(vault, repository, [
        (str(kept.get("comparison_id") or ""), str(row["id"])) for row, kept, *_rest in candidates])
    entries = []
    for row, kept, kept_at, los, keys in candidates:
        if not keys or keys & set(withheld):
            continue
        if not kept.get("comparison_id") or (str(kept["comparison_id"]), str(row["id"])) in shared:
            continue
        entries.append({
            "kind": "kept_comparison", "ask_id": row["id"], "kept_at": kept_at,
            "caller": kept.get("caller") or row["caller"],
            "learning_object_ids": los,
            "sources": [{"source_id": obj.get("source_id"), "key": obj["key"], "object_type": obj["object_type"],
                         "source_object_id": obj["id"]} for obj in kept.get("objects") or ()],
            # Each relation's two ends (C0a Codex review F6: a comparison of
            # three sections relates pairs, never all of them at once).
            "relations": [{"relation_type": rel["relation_type"], "fine": rel["fine"], "relation_id": rel["id"],
                           "left_source_object_id": rel.get("left_object_id"),
                           "right_source_object_id": rel.get("right_object_id")}
                          for rel in kept.get("relations") or ()],
            "takes": sum(1 for take in kept.get("takes") or () if by_then(take.get("created_at"))),
            "status": "proposed",
        })
    entries.sort(key=lambda entry: (entry["kept_at"], entry["ask_id"]))
    return entries


__all__ = [
    "EVENTS",
    "MAX_PERSPECTIVES",
    "RELATION_MAP",
    "RowGuard",
    "TAKE_RELATION",
    "clean_perspectives",
    "coarse_relation",
    "compare_kept_state",
    "compared_on",
    "held_out_now",
    "keep",
    "keep_enabled",
    "keep_tutor",
    "kept_ask",
    "kept_comparisons_for_card",
    "live_keep_of",
    "kept_marks",
    "kept_state",
    "relation_head",
    "relation_lineage",
    "remove",
    "reopen",
    "take_key",
    "tutor_comparison",
    "tutor_keep_enabled",
]
