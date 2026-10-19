"""Reader workbench RW1c: the Reader context's span provider (spec_reader_workbench_v1 §4.6).

Practice, feedback and library already ground the tutor in retrieved spans
(``tutor.TutorSpanProvider``); in the Reader it saw only the selection and its
neighbours. This module gives the Reader context its own provider:

* **Its own query.** The learner's question, the inquiry's ancestors and,
  when personalized, the open gaps on the passage's learning objects
  (:func:`reader_query`); T6's rewrite step (``search_spans``' query rewrite
  under ``source_retrieval.query_rewrite``) rewrites it inside
  ``find_sources``.
* **The sources spec's function, under the caller's policy.** The adapter
  injects ``find`` bound to the server-derived Reader caller (the sources
  service's ``propose_sources``, or the base ``find_sources_for_caller`` when
  the service is off, G53): the Reader context reads under ``reading``, a
  bound workbench session under ``assisted_practice`` for its item, and a
  cold administration retrieves nothing (W7). The policy is never an
  argument. ``verify=True``: only passages the verification keeps reach the
  tutor.
* **T6's rule 0.** When the verification route cannot run, nothing is
  retrieved or paid for and the tutor keeps today's delivery.
* **T6's exclusions.** Item-bound, every exercise and solution block and every
  passage linked to the item stay out (``find_sources``' ``assisted_practice``
  scope), a block whose own lead names an exercise or a solution never
  reaches the tutor, and nor does one that reproduces the item's answer;
  held-out material never does, whatever the policy.

The intents (§4.6): ``explain`` (an ordinary question), ``alternative``
("another way": every passage already shown in the inquiry excluded, so the
second explanation comes from another source or another role) and
``remediate`` ("that didn't help": the inquiry's named gaps as
``target_hypotheses``). Without the service, both fall back to ``explain``
with the shown passages excluded.

Retrieval is context (T6's ruling): nothing here writes evidence, mastery,
grading inputs or scheduling state; the manifest is the receipt.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.sources.exam_material import held_out_material
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.ingest.block_roles import lead_role
from learnloop.source_retrieval.corpus import block_roles
from learnloop.source_retrieval.tutor import ITEM_BOUND_LEAD_ROLES
from learnloop.source_retrieval.verify import verification_route
from learnloop.tutor.tutor_qa import span_leaks_expected
from learnloop.vault.models import LoadedVault, PracticeItem

#: The intents the Reader tutor retrieves with (the sources spec's names).
READER_INTENTS = ("explain", "alternative", "remediate")
#: How many of the inquiry's earlier questions join the query.
QUERY_ANCESTORS = 2
#: How many open-gap statements join a personalized query.
QUERY_GAPS = 3
QUERY_CHARS = 2000
#: Roles a cited block has when "Try the next step first" fits it (a
#: derivation or a worked example, RW1b's next-step question at that line).
NEXT_STEP_ROLES = frozenset({"proof", "worked_example"})
#: The labels "another way" carries (UX §4.2).
FROM_ANOTHER_BOOK = "from a different book"
WORKED_EXAMPLE_INSTEAD = "a worked example instead"
SAME_BOOK_OTHER_PASSAGE = "another passage from your books"
#: Statuses a find_sources verification ran under.
VERIFIED = ("verified", "cached")
#: How many of the learner's recent workbench steps the bridge sees.
WORK_STEPS = 4


def reader_query(question_md: str, *, ancestors: Sequence[Mapping[str, Any]] = (),
                 gaps: Sequence[Mapping[str, Any]] = ()) -> str:
    """The tutor's own query: the question, its latest ancestors' questions and
    (personalized) the open-gap statements, within ``QUERY_CHARS``."""

    parts = [" ".join(str(question_md or "").split())]
    for ancestor in list(ancestors)[-QUERY_ANCESTORS:][::-1]:
        text = " ".join(str(ancestor.get("question_md") or "").split())
        if text and text not in parts:
            parts.append(text)
    for gap in list(gaps)[:QUERY_GAPS]:
        text = " ".join(str(gap.get("statement") or "").split())
        if text:
            parts.append(text)
    return " ".join(part for part in parts if part)[:QUERY_CHARS]


def _span(hit: Mapping[str, Any]) -> dict[str, Any]:
    title = str(hit.get("source_title") or "")
    section = str(hit.get("section") or "")
    label = title if not section else f"{title} · {section}"
    return {
        "extraction_id": str(hit["extraction_id"]), "span_id": str(hit["span_id"]), "relation": "retrieved",
        "semantic_authority": False, "source_id": hit.get("source_id"), "label": label[:120],
        "text": str(hit.get("text") or ""), "page": hit.get("page"), "role": hit.get("role"),
    }


def another_way_label(hits: Sequence[Mapping[str, Any]], shown_sources: Sequence[str]) -> str | None:
    """How "another way"'s passages differ from what the inquiry showed."""

    if not hits:
        return None
    shown = set(shown_sources)
    if any(hit.get("source_id") and hit.get("source_id") not in shown for hit in hits):
        return FROM_ANOTHER_BOOK
    if any(hit.get("role") == "worked_example" for hit in hits):
        return WORKED_EXAMPLE_INSTEAD
    return SAME_BOOK_OTHER_PASSAGE


@dataclass
class ReaderLookup:
    """One Reader question's retrieval, bound by the adapter (``ReaderTutorRequest.retrieve``)."""

    vault: LoadedVault
    repository: Repository
    #: ``find(query, **kwargs) -> SourceHits`` under the server-derived caller.
    find: Callable[..., Any]
    #: The caller's derived policy (the manifest's, and ``cold_attempt`` retrieves nothing).
    policy: str
    query: str
    intent: str = "explain"
    learning_object_ids: Sequence[str] = ()
    exclude_span_keys: Sequence[str] = ()
    target_hypotheses: Sequence[Mapping[str, Any]] = ()
    shown_source_ids: Sequence[str] = ()
    personalized: bool = True
    item: PracticeItem | None = None
    rerank_client: Any | None = None
    #: The sources service is on (its intents); off, the base explain (G53).
    service: bool = True
    notes: list[str] = field(default_factory=list)

    def __call__(self) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
        vault, repository = self.vault, self.repository
        intent = self.intent if self.service else "explain"
        manifest: dict[str, Any] = {"basis": "reader_lookup", "policy": self.policy, "intent": intent,
                                    "requested_intent": self.intent, "service": self.service,
                                    "excluded_span_keys": list(self.exclude_span_keys),
                                    "target_hypotheses": [dict(ref) for ref in self.target_hypotheses],
                                    "personalized": self.personalized}
        if self.policy == "cold_attempt":
            return None, {**manifest, "status": "cold_attempt", "books_cover": None,
                          "reason": "nothing is retrieved during a cold administration"}
        config = vault.config.source_retrieval
        if not config.enabled:
            return None, {**manifest, "status": "disabled", "books_cover": None,
                          "reason": "source_retrieval.enabled is false"}
        ready = verification_route(vault, self.rerank_client)
        if not ready.ready:
            # T6's rule 0: nothing is retrieved (or paid for) when verification cannot run.
            return None, {**manifest, "status": f"skipped: verification {ready.skip}", "books_cover": None,
                          "reason": ready.reason}
        hits = self.find(
            self.query, intent=intent, scope="library", learning_object_ids=list(self.learning_object_ids),
            exclude_span_keys=list(self.exclude_span_keys),
            target_hypotheses=[dict(ref) for ref in self.target_hypotheses] if intent == "remediate" else [],
            personalized=self.personalized, verify=True, limit=config.tutor_spans, rerank_client=ready.client,
        )
        found = hits.as_dict() if hasattr(hits, "as_dict") else dict(hits)
        found_manifest = dict(found.get("manifest") or {})
        verification = dict(found_manifest.get("verification") or {})
        status = str(verification.get("status") or found.get("status") or "")
        kept, withheld = self._admitted(list(found.get("hits") or []))
        manifest.update({"find_sources": found_manifest, "status": status,
                         "candidates_judged": verification.get("judged"), "withheld": withheld})
        if status in VERIFIED:
            books_cover: bool | None = bool(kept)
        elif status == "not_requested" and not found.get("hits"):
            # Nothing in the learner's library was even a candidate.
            books_cover = False
        else:
            return None, {**manifest, "books_cover": None, "reason": verification.get("reason")}
        spans = [_span(hit) for hit in kept]
        label = another_way_label(kept, self.shown_source_ids) if intent == "alternative" else None
        if intent == "remediate" and kept:
            label = "chosen for what's still unclear"
        manifest.update({"books_cover": books_cover, "passages": len(spans), "label": label,
                         "span_keys": [f"{span['extraction_id']}:{span['span_id']}" for span in spans]})
        return spans, manifest

    def _admitted(self, hits: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """The hits that may reach the tutor: never held-out material; item-bound,
        never an exercise or solution lead nor a passage reproducing the item's answer
        (``find_sources`` already applied the policy's scope; this is the second guard)."""

        held = held_out_material(self.vault, self.repository)
        item = self.item if self.policy == "assisted_practice" else None
        kept: list[dict[str, Any]] = []
        counts = {"held_out": 0, "exercise_or_solution": 0, "answer_overlap": 0}
        for hit in hits:
            text = str(hit.get("text") or "")
            if held.covers(str(hit["extraction_id"]), str(hit["span_id"])):
                counts["held_out"] += 1
            elif item is not None and (lead_role(text) in ITEM_BOUND_LEAD_ROLES
                                       or hit.get("role") in ITEM_BOUND_LEAD_ROLES):
                counts["exercise_or_solution"] += 1
            elif item is not None and span_leaks_expected(text, item.expected_answer):
                counts["answer_overlap"] += 1
            else:
                kept.append(hit)
        return kept, {key: value for key, value in counts.items() if value}


# ---------------------------------------------------------------------------
# The inquiry: what it has shown, the gaps it named
# ---------------------------------------------------------------------------

def inquiry_exchanges(exchanges: Sequence[Mapping[str, Any]], exchange_id: str | None) -> list[dict[str, Any]]:
    """Every exchange of the inquiry ``exchange_id`` belongs to (its root's tree), oldest first."""

    if not exchange_id:
        return []
    by_id = {str(e["event_id"]): dict(e) for e in exchanges}
    root = exchange_id
    seen: set[str] = set()
    while root in by_id and by_id[root].get("parent_exchange_id") and root not in seen:
        seen.add(root)
        root = str(by_id[root]["parent_exchange_id"])
    if root not in by_id:
        return []
    members = {root}
    changed = True
    while changed:
        changed = False
        for e in by_id.values():
            if str(e["event_id"]) not in members and str(e.get("parent_exchange_id") or "") in members:
                members.add(str(e["event_id"]))
                changed = True
    return sorted((by_id[key] for key in members), key=lambda e: (str(e.get("created_at") or ""), str(e["event_id"])))


def shown_span_keys(exchanges: Sequence[Mapping[str, Any]]) -> list[str]:
    """Every passage an inquiry has shown: each exchange's selection, citations,
    excerpt and the passages its tutor retrieved."""

    keys: list[str] = []

    def add(extraction_id: Any, span_id: Any) -> None:
        if extraction_id and span_id:
            key = f"{extraction_id}:{span_id}"
            if key not in keys:
                keys.append(key)

    for exchange in exchanges:
        extraction_id = exchange.get("extraction_id")
        for span_id in [exchange.get("span_id"), *(exchange.get("selection_span_ids") or [])]:
            add(extraction_id, span_id)
        for citation in exchange.get("citations") or []:
            add(citation.get("extraction_id"), citation.get("span_id"))
        tutor = exchange.get("tutor") or {}
        excerpt = tutor.get("excerpt") or {}
        add(excerpt.get("extraction_id"), excerpt.get("span_id"))
        for key in (tutor.get("retrieval") or {}).get("span_keys") or []:
            extraction, _, span = str(key).partition(":")
            add(extraction, span)
    return keys


def shown_source_ids(repository: Repository, keys: Sequence[str]) -> list[str]:
    """The sources the shown passages belong to (for "from a different book")."""

    out: list[str] = []
    for extraction_id in dict.fromkeys(str(key).partition(":")[0] for key in keys):
        run = repository.get_extraction_run(extraction_id) or {}
        revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
        source_id = revision.get("source_id")
        if source_id and source_id not in out:
            out.append(str(source_id))
    return out


def named_gap_hypotheses(repository: Repository, exchanges: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """The gaps learner-text gaps named from the inquiry's questions, as
    ``target_hypotheses`` (``named_gap`` refs the sources service resolves)."""

    from learnloop.reader.reader_observations import named_gaps

    question_ids = [str(e["question_event_id"]) for e in exchanges if e.get("question_event_id")]
    found = named_gaps(repository, question_ids)
    refs: list[dict[str, str]] = []
    for question_id in question_ids:
        for gap in found.get(question_id, []):
            ref = {"kind": "named_gap", "id": str(gap["gap_id"])}
            if ref not in refs:
                refs.append(ref)
    return refs


# ---------------------------------------------------------------------------
# The bridge's context: the learner's work on the passage's LOs
# ---------------------------------------------------------------------------

def passage_learning_objects(vault: LoadedVault, repository: Repository, *, extraction_id: str,
                             span_ids: Sequence[str]) -> list[str]:
    """The passage's learning objects: its section's provenance-linked LOs
    (RW4a's anchor), else the LOs whose current source links name one of its
    blocks (``entity_source_links``, ``primary`` or ``support``)."""

    from learnloop.ingest.locators import format_block_span
    from learnloop.source_retrieval.library_ask import anchor_learning_objects

    found = anchor_learning_objects(vault, repository, extraction_id=extraction_id, span_ids=span_ids)
    if found:
        return found
    locators = [format_block_span(extraction_id, span_id) for span_id in dict.fromkeys(span_ids) if span_id]
    if not locators:
        return []
    marks = ", ".join("?" for _ in locators)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT DISTINCT entity_id FROM entity_source_links WHERE entity_type = 'learning_object' "
            f"AND status = 'current' AND relation IN ('primary', 'support') AND locator IN ({marks}) "
            "ORDER BY entity_id", tuple(locators)).fetchall()
    return [str(row[0]) for row in rows if str(row[0]) in vault.learning_objects]


def learner_work(vault: LoadedVault, repository: Repository, learning_object_ids: Sequence[str]) -> list[dict[str, Any]]:
    """The learner's open questions (statements, labelled LearnLoop's reading)
    and most recent workbench steps (their own words) on these LOs: the same
    class of data the hint writer already sends (spec §5.8)."""

    from learnloop.source_retrieval.library_ask import open_questions

    lo_ids = [lo for lo in dict.fromkeys(learning_object_ids) if lo in vault.learning_objects]
    if not lo_ids:
        return []
    work: list[dict[str, Any]] = [
        {"kind": "open_question", "statement": entry["statement"], "author": "LearnLoop's reading",
         "learning_object_id": entry.get("learning_object_id")}
        for entry in open_questions(vault, repository, lo_ids)[:QUERY_GAPS]
    ]
    items = [item_id for item_id, item in vault.practice_items.items() if item.learning_object_id in lo_ids]
    if items:
        session = _latest_session(repository, items)
        if session is not None:
            work.append(session)
    return work


def _latest_session(repository: Repository, item_ids: Sequence[str]) -> dict[str, Any] | None:
    from learnloop.reader.workbench import live_steps

    marks = ", ".join("?" for _ in item_ids)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='workbench_steps'").fetchone() is None:
            return None
        session = connection.execute(
            f"SELECT id, practice_item_id, stem_md FROM workbench_sessions WHERE practice_item_id IN ({marks}) "
            "ORDER BY updated_at DESC, id DESC LIMIT 1", tuple(item_ids)).fetchone()
        if session is None:
            return None
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM workbench_steps WHERE session_id = ? ORDER BY created_at, id", (session["id"],))]
    steps = [step for step in live_steps(rows) if step["kind"] == "step" and str(step["body_md"]).strip()]
    if not steps:
        return None
    return {"kind": "workbench_steps", "author": "the learner", "problem": " ".join(str(session["stem_md"]).split())[:300],
            "steps": [str(step["body_md"])[:300] for step in steps[-WORK_STEPS:]]}


# ---------------------------------------------------------------------------
# The Reader's own buttons
# ---------------------------------------------------------------------------

def next_step_buttons(repository: Repository, *, extraction_id: str,
                      cited: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """"Try the next step first" on each cited block of the open source that is
    a derivation or a worked example (RW1b's next-step question at that line)."""

    keys = [(str(c.get("extraction_id")), str(c.get("span_id"))) for c in cited
            if str(c.get("extraction_id")) == extraction_id and c.get("span_id")]
    if not keys:
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        roles = block_roles(connection, keys)
    buttons: list[dict[str, Any]] = []
    for key in dict.fromkeys(keys):
        if roles.get(key) in NEXT_STEP_ROLES:
            buttons.append({"kind": "try_next_step", "extraction_id": key[0], "span_id": key[1],
                            "label": "try the next step first", "role": roles[key]})
    return buttons


def citation_dicts(raw: Any) -> list[dict[str, Any]]:
    """Citations as plain dicts whatever their stored shape."""

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return []
    return [dict(c) for c in raw or [] if isinstance(c, Mapping)]


__all__ = [
    "FROM_ANOTHER_BOOK",
    "NEXT_STEP_ROLES",
    "READER_INTENTS",
    "ReaderLookup",
    "SAME_BOOK_OTHER_PASSAGE",
    "WORKED_EXAMPLE_INSTEAD",
    "another_way_label",
    "citation_dicts",
    "inquiry_exchanges",
    "learner_work",
    "named_gap_hypotheses",
    "next_step_buttons",
    "passage_learning_objects",
    "reader_query",
    "shown_source_ids",
    "shown_span_keys",
]
