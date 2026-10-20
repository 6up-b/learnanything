"""Source-object layer + relations + canonical mapping proposals (spec §7, design
B step 7).

A source object is a PER-SOURCE reviewed/proposed semantic object, never a
cross-source truth claim (§7.1). Inventory / demand-paged-synthesis output begins
``proposed``; authoring, review, and linking are append-only. The reader cannot
create a transcript-shaped graph merely because content was visible or highlighted
(§7.3) -- new canonical objects flow only through the proposal/gate/review path, and
accepting a mapping never overwrites the source object nor deletes the annotation.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.content.sources import exam_material as EM
from learnloop.content.sources.span_aliases import CitationResolver
from learnloop.db.repositories import Repository
from learnloop.db.stores import library_asks as ask_store
from learnloop.db.stores.source_block_fts import source_extraction_ids
from learnloop.db.stores.source_service import comparison_row

OBJECT_TYPES = (
    "claim", "definition", "procedure", "worked_example",
    "problem", "proof_move", "motif_or_passage", "artifact",
)
RELATION_TYPES = (
    "supports", "contradicts", "refines", "alternate_definition",
    "unresolved", "learner_connects",
)
MAPPING_TARGET_KINDS = ("facet", "lo", "blueprint", "commitment", "new_object")

# §5.2/§A.3.6: connect_it's birth relation is learner_connects -- never a canonical
# edge; it stays a proposal unless reviewed into another relation (§7.2).
CONNECT_IT_RELATION = "learner_connects"


class SourceObjectError(ValueError):
    """Domain error for the source-object service."""


def author_source_object(
    repository: Repository,
    *,
    source_id: str,
    revision_id: str,
    object_type: str,
    exact_text: str = "",
    content: Mapping[str, Any] | None = None,
    citations: list[Mapping[str, Any]] | None = None,
    authorship: str = "ai",
    status: str = "proposed",
    authorial_role: str | None = None,
    salience_proposal: float | None = None,
    model_provenance: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author a new source object (version 1). Inventory/reader output begins
    ``proposed`` (§7.1); a source object is not a cross-source truth claim."""

    if object_type not in OBJECT_TYPES:
        raise SourceObjectError(f"unknown object_type: {object_type!r}")
    source_object_id = repository.create_source_object(source_id=source_id, clock=clock)
    written = repository.append_source_object_version(
        source_object_id=source_object_id,
        version={
            "revision_id": revision_id,
            "object_type": object_type,
            "authorial_role": authorial_role,
            "salience_proposal": salience_proposal,
            "exact_text": exact_text,
            "content": dict(content or {}),
            "authorship": authorship,
            "status": status,
            "model_provenance": dict(model_provenance) if model_provenance is not None else None,
        },
        citations=list(citations or []),
        clock=clock,
    )
    return {"source_object_id": source_object_id, "status": status, **written}


def review_source_object(
    repository: Repository, *, source_object_id: str, status: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Append a review status successor (``reviewed`` / ``rejected`` / ``superseded``).
    Accepting/reviewing never overwrites prior versions -- they remain for audit."""

    if status not in ("proposed", "reviewed", "rejected", "superseded"):
        raise SourceObjectError(f"unknown status: {status!r}")
    try:
        return repository.set_source_object_status(
            source_object_id=source_object_id, status=status, clock=clock
        )
    except ValueError as exc:
        raise SourceObjectError(str(exc)) from exc


def link_relation(
    repository: Repository,
    *,
    source_object_id: str,
    related_object_id: str | None = None,
    relation_type: str = CONNECT_IT_RELATION,
    learner_text: str | None = None,
    authorship: str = "learner",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Create a versioned relation between source objects. ``learner_connects``
    preserves the learner's wording and remains ``proposed`` until reviewed (§7.2)."""

    if relation_type not in RELATION_TYPES:
        raise SourceObjectError(f"unknown relation_type: {relation_type!r}")
    relation_id = repository.create_source_object_relation(
        source_object_id=source_object_id, related_object_id=related_object_id,
        relation_type=relation_type, learner_text=learner_text, authorship=authorship,
        review_status="proposed", clock=clock,
    )
    return {"relation_id": relation_id, "relation_type": relation_type, "review_status": "proposed"}


def supersede_relation(repository: Repository, *, relation_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """Mark a relation ``superseded`` by appending its successor version (the
    same endpoints, type, wording and authorship; ``version_ordinal + 1``):
    relations are versioned and append-only, so nothing is updated or deleted
    (Reader RW4d's *remove*, spec_reader_workbench_v1 §7.8)."""

    prior = repository.source_object_relation(relation_id)
    if prior is None:
        raise SourceObjectError(f"unknown relation: {relation_id!r}")
    successor = repository.create_source_object_relation(
        source_object_id=prior["source_object_id"], related_object_id=prior["related_object_id"],
        relation_type=prior["relation_type"], learner_text=prior["learner_text"], authorship=prior["authorship"],
        review_status="superseded", version_ordinal=int(prior["version_ordinal"]) + 1, clock=clock,
    )
    return {"relation_id": successor, "supersedes": relation_id, "review_status": "superseded"}


def propose_mapping(
    repository: Repository,
    *,
    target_kind: str,
    source_object_id: str | None = None,
    annotation_id: str | None = None,
    target_ref: str | None = None,
    confidence: float | None = None,
    rationale: str | None = None,
    provenance: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append a canonical mapping proposal (§7.3). Append-only; accepting does not
    overwrite the source object and rejecting does not delete the annotation."""

    if target_kind not in MAPPING_TARGET_KINDS:
        raise SourceObjectError(f"unknown target_kind: {target_kind!r}")
    proposal_id = repository.create_mapping_proposal(
        source_object_id=source_object_id, annotation_id=annotation_id,
        target_kind=target_kind, target_ref=target_ref, confidence=confidence,
        rationale=rationale, provenance=provenance, clock=clock,
    )
    return {"proposal_id": proposal_id, "status": "proposed"}


def accept_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None = None) -> dict[str, Any]:
    row = repository.decide_mapping_proposal(proposal_id=proposal_id, status="accepted", clock=clock)
    if row is None:
        raise SourceObjectError(f"unknown mapping proposal: {proposal_id!r}")
    return row


def reject_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """Rejecting a mapping never deletes the annotation or suppresses alternatives (§7.3)."""

    row = repository.decide_mapping_proposal(proposal_id=proposal_id, status="rejected", clock=clock)
    if row is None:
        raise SourceObjectError(f"unknown mapping proposal: {proposal_id!r}")
    return row


def withheld_source_objects(vault: Any, repository: Repository,
                            heads: Sequence[Mapping[str, Any]]) -> frozenset[str]:
    """The ids among ``heads`` whose material is exam or held out **now** (exam
    protection's one predicate, ``exam_material``), read from each object's own
    provenance: every citation's span on the reading it was made on, on its
    book's current reading and on every reading of its revision, and the spans
    its selection named. Fail closed: when the predicate cannot be read every
    object is withheld, and an object with no span to place is withheld while
    its book has any exam or held-out material. The rows stay in the ledger;
    only what is returned is filtered (Codex verify of RW4d fix round 1, F2:
    a kept comparison's quotes, held out after the keep)."""

    ids = [str(head["object"]["id"]) for head in heads if head and head.get("object")]
    if not ids:
        return frozenset()
    try:
        material = EM.exam_material(vault, repository)
        resolver = CitationResolver(repository)
        withheld: set[str] = set()
        with repository.connection() as connection:
            readings: dict[str, list[str]] = {}

            def of_revision(revision_id: Any) -> list[str]:
                key = str(revision_id or "")
                if key and key not in readings:
                    readings[key] = source_extraction_ids(connection, revision_id=key)
                return readings.get(key, [])

            for head in heads:
                if not head or not head.get("object"):
                    continue
                obj, version = head["object"], head.get("version") or {}
                keys: set[tuple[str, str]] = set()
                for citation in head.get("citations") or ():
                    span = str(citation.get("span_id") or "")
                    resolution = resolver.resolve(citation)
                    if resolution is not None:
                        keys.add((str(resolution.from_extraction_id), str(resolution.from_span_id)))
                        if resolution.key is not None:
                            keys.add((str(resolution.key[0]), str(resolution.key[1])))
                    for reading in of_revision(citation.get("revision_id") or version.get("revision_id")):
                        keys.add((reading, span))
                content = json.loads(version.get("content_json") or "{}") if version else {}
                for span in (content.get("selected_span_ids") or []) if isinstance(content, Mapping) else []:
                    for reading in of_revision(version.get("revision_id")):
                        keys.add((reading, str(span)))
                keys = {key for key in keys if key[0] and key[1]}
                if keys:
                    if any(material.covers(*key) for key in keys):
                        withheld.add(str(obj["id"]))
                    continue
                book = set(source_extraction_ids(connection, source_id=str(obj.get("source_id") or ""))) | set(
                    of_revision(version.get("revision_id")))
                if not book or book & material.material.touched:
                    withheld.add(str(obj["id"]))
        return frozenset(withheld)
    except Exception:  # noqa: BLE001 - an unreadable predicate returns no material (fail closed)
        return frozenset(ids)


def _span_key(value: Any) -> tuple[str, str] | None:
    if isinstance(value, Mapping):
        pair = (value.get("extraction_id") or value.get("extractionId"), value.get("span_id") or value.get("spanId"))
    elif isinstance(value, str):
        pair = tuple(value.split(":", 1)) if ":" in value else (None, None)  # type: ignore[assignment]
    elif isinstance(value, Sequence) and len(value) == 2:
        pair = (value[0], value[1])
    else:
        return None
    return (str(pair[0]), str(pair[1])) if pair[0] and pair[1] else None


def _question_passages(repository: Repository, question_event_id: str) -> list[Any]:
    """The passages a tutor question was asked from: its passage and the spans
    it was given. A question with no source context names none; one naming a
    reading without a passage (or the reverse) is malformed."""

    event = repository.question_event(str(question_event_id))
    if event is None:
        raise LookupError(f"unknown question event {question_event_id!r}")
    context = event.get("source_context") or {}
    if not isinstance(context, Mapping):
        raise LookupError(f"question event {question_event_id!r} has a malformed source context")
    found: list[Any] = []
    if context.get("extraction_id") or context.get("span_id"):
        found.append((context.get("extraction_id"), context.get("span_id")))
    found.extend(context.get("source_spans") or ())
    delivery = context.get("delivery") or {}
    if isinstance(delivery, Mapping):
        found.extend(delivery.get("source_spans") or ())
    return found


def comparison_passages(repository: Repository, comparison_id: str, *, ask_id: str | None = None,
                        question_event_id: str | None = None, ask_ids: Sequence[str] = (),
                        question_event_ids: Sequence[str] = ()) -> set[tuple[str, str]]:
    """Every passage that contributed to a stored comparison, as the **union
    across its reuse** (Codex verify of RW4d fix round 4, F1):

    * the stored comparison: its compared sources, counterparts, unverified
      sources and dropped pins, and its own ``caller_ref`` (a tutor question;
      for the Reader, the reading it was asked in);
    * every ask that refers to it (showing it now, keeping it, a removal's
      snapshot, or a contributor its keep recorded), with each ask's anchor,
      binding and question, and ``ask_id`` / ``ask_ids`` (an ask acting now);
    * every tutor question whose request ran it (``source_tool_calls``), the
      contributors' questions, and ``question_event_id`` / ``question_event_ids``.

    Every named contributor is resolved (Codex verify of fix round 4, F3):
    each passage must exist as a block of its reading, each ask, question and
    reading must exist. Anything malformed or unresolvable raises
    ``LookupError``; callers withhold the whole comparison (fail closed)."""

    from learnloop.db.stores.source_block_fts import existing_spans
    from learnloop.db.stores.source_service import tool_requests_for_result

    if not comparison_id:
        raise LookupError("no comparison named")
    found: list[Any] = []
    asks: list[str] = [str(value) for value in (ask_id, *ask_ids) if value]
    events: list[str] = [str(value) for value in (question_event_id, *question_event_ids) if value]
    readings: list[str] = []
    with repository.connection() as connection:
        stored = comparison_row(connection, str(comparison_id))
        if stored is None:
            raise LookupError(f"unknown comparison {comparison_id!r}")
        found.extend([*((stored.get("comparison") or {}).get("sources") or ()),
                      *(stored.get("counterpart_keys") or ()), *(stored.get("unverified_sources") or ()),
                      *(stored.get("dropped_pins") or ())])
        caller_ref = stored.get("caller_ref")
        if caller_ref:
            if str(stored.get("caller") or "") == "tutor":
                events.append(str(caller_ref))
            else:
                readings.append(str(caller_ref))
        asks.extend(ask_store.asks_referencing_comparison(connection, str(comparison_id)))
        for request in tool_requests_for_result(connection, str(comparison_id)):
            if not request.get("caller_ref"):
                raise LookupError(f"a run of comparison {comparison_id!r} names no question")
            events.append(str(request["caller_ref"]))
        seen: set[str] = set()
        while asks:
            current = asks.pop(0)
            if current in seen:
                continue
            seen.add(current)
            ask = ask_store.ask_row(connection, current)
            kept_row = ask_store.kept_row(connection, current)
            if ask is None or kept_row is None:
                raise LookupError(f"unknown library question {current!r}")
            extraction = ask.get("extraction_id")
            spans = list((ask.get("anchor") or {}).get("span_ids") or ())
            if spans and not extraction:
                raise LookupError(f"library question {current!r} names an anchor without its reading")
            found.extend((extraction, span) for span in spans)
            if extraction:
                readings.append(str(extraction))
            caller = (ask.get("manifest") or {}).get("caller")
            if isinstance(caller, Mapping):
                reading = caller.get("extraction_id") or extraction
                named = [caller.get("span_id"), *(caller.get("span_ids") or ()),
                         *(caller.get("selection_span_ids") or ())]
                found.extend((reading, span) for span in named if span)
            if ask.get("question_event_id"):
                events.append(str(ask["question_event_id"]))
            kept = kept_row.get("kept") or {}
            recorded = [*(kept.get("contributors") or ()),
                        *(contributor for entry in kept.get("removed") or () if isinstance(entry, Mapping)
                          for contributor in ((entry.get("kept") or {}).get("contributors") or ()))]
            for contributor in recorded:
                if not isinstance(contributor, Mapping):
                    raise LookupError(f"library question {current!r} records a malformed contributor")
                if contributor.get("ask_id"):
                    asks.append(str(contributor["ask_id"]))
                if contributor.get("question_event_id"):
                    events.append(str(contributor["question_event_id"]))
        for reading in dict.fromkeys(readings):
            if connection.execute("SELECT 1 FROM source_extraction_runs WHERE id = ?", (reading,)).fetchone() is None:
                raise LookupError(f"unknown reading {reading!r}")
    for event_id in dict.fromkeys(events):
        found.extend(_question_passages(repository, event_id))
    keys: set[tuple[str, str]] = set()
    for value in found:
        key = _span_key(value)
        if key is None:
            raise LookupError(f"comparison {comparison_id!r} names a malformed passage: {value!r}")
        keys.add(key)
    if not keys:
        raise LookupError(f"comparison {comparison_id!r} names no passage")
    with repository.connection() as connection:
        present = existing_spans(connection, keys)
    missing = keys - present
    if missing:
        raise LookupError(f"comparison {comparison_id!r} names passages that do not resolve: {sorted(missing)!r}")
    return keys


def withheld_comparisons(vault: Any, repository: Repository,
                         comparisons: Sequence[tuple[str, str | None]]) -> frozenset[tuple[str, str | None]]:
    """The ``(comparison id, ask id)`` pairs with **any** contributing passage
    (:func:`comparison_passages`) that is exam or held out now. Such a
    comparison is withheld whole on every read path: every object, version,
    citation, relation and take derived from it. Fail closed: a comparison
    whose provenance cannot be read, or a predicate that cannot be, counts as
    withheld (Codex verify of RW4d fix round 3; the orchestrator's ruling)."""

    wanted = list(dict.fromkeys((str(cid or ""), None if ask is None else str(ask)) for cid, ask in comparisons))
    if not wanted:
        return frozenset()
    passages: dict[tuple[str, str | None], set[tuple[str, str]]] = {}
    unknown: set[tuple[str, str | None]] = set()
    for pair in wanted:
        try:
            if not pair[0]:
                raise LookupError("no comparison named")
            passages[pair] = comparison_passages(repository, pair[0], ask_id=pair[1])
        except Exception:  # noqa: BLE001 - unresolvable provenance is withheld (fail closed)
            unknown.add(pair)
    try:
        held = EM.exam_material(vault, repository).withheld(sorted({key for keys in passages.values() for key in keys}))
    except Exception:  # noqa: BLE001 - an unreadable predicate withholds every comparison (fail closed)
        return frozenset(wanted)
    return frozenset(unknown | {pair for pair, keys in passages.items() if keys & set(held)})


def _comparison_of(head: Mapping[str, Any]) -> tuple[str, str | None] | None:
    """The comparison an object was kept from, ``("", None)`` when it claims
    one it does not name (unresolvable), None for any other object."""

    try:
        content = json.loads((head.get("version") or {}).get("content_json") or "{}")
    except (TypeError, ValueError):
        return ("", None)
    if not isinstance(content, Mapping):
        return ("", None)
    if content.get("comparison_id") or content.get("kept_from") == "source_comparison":
        return (str(content.get("comparison_id") or ""), str(content["ask_id"]) if content.get("ask_id") else None)
    return None


def hidden_source_objects(vault: Any, repository: Repository,
                          heads: Sequence[Mapping[str, Any]]) -> frozenset[str]:
    """The ids among ``heads`` no reader returns: an object whose own material
    is withheld (:func:`withheld_source_objects`), and every object kept from a
    comparison that is withheld whole (:func:`withheld_comparisons`)."""

    hidden = set(withheld_source_objects(vault, repository, heads))
    kept_from = {str(head["object"]["id"]): pair for head in heads
                 if head and head.get("object") and (pair := _comparison_of(head)) is not None}
    withheld = withheld_comparisons(vault, repository, list(kept_from.values()))
    hidden.update(object_id for object_id, pair in kept_from.items() if pair in withheld)
    return frozenset(hidden)


def source_objects_for_source(vault: Any, repository: Repository, *, source_id: str) -> list[dict[str, Any]]:
    """A book's source objects (each head version with its citations), without
    any whose material is exam or held out now, or that was kept from a
    comparison withheld whole (:func:`hidden_source_objects`): their exact
    text, content, lines, quotes and citations are never returned. The rows
    stay in the ledger."""

    heads = [head for head in repository.source_objects_for_source(source_id) if head]
    hidden = hidden_source_objects(vault, repository, heads)
    return [head for head in heads if str(head["object"]["id"]) not in hidden]


def proposal_inbox(
    vault: Any, repository: Repository, *, status: str = "proposed", source_object_id: str | None = None
) -> dict[str, Any]:
    """Non-modal review inbox (§6.4): accumulated proposals reviewed without losing
    reading position. Nothing here is auto-applied. A proposal about a source
    object no reader returns (:func:`hidden_source_objects`) is left out."""

    proposals = repository.mapping_proposals(status=status, source_object_id=source_object_id)
    ids = sorted({str(p["source_object_id"]) for p in proposals if p.get("source_object_id")})
    heads = [head for object_id in ids if (head := repository.source_object_head(object_id))]
    missing = set(ids) - {str(head["object"]["id"]) for head in heads}
    hidden = hidden_source_objects(vault, repository, heads) | missing
    return {"proposals": [p for p in proposals if str(p.get("source_object_id") or "") not in hidden]}
