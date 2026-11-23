"""Where else the library says something about a passage or a learner's words (spec §9.1, §10.6): the one
machinery behind the menus' promoted rows and the scratchpads' proposals.

Three finders, each with how far its finding is checked:

* **passage links** (``db.stores.passage_link_reads``): another passage the cue judge tied to the same learner problem
  (checked: a judge picked it for this learner, with its rank);
* **correspondents** (``source_retrieval.section_coverage.correspondents``): another book's section the coverage judge
  says treats the same learning objects (checked), or, with none, its keyword search hits (``found by search, not
  checked``); no model call;
* **search** (``source_retrieval.search.search_spans``): passages found for the words, keyword only (no model) or by
  meaning (a paid query embedding), then confirmed by ``source_retrieval.verify.verify_spans`` (a paid judge) where
  the caller asks; unconfirmed hits are ``found by search, not checked``.

Every finding names a content reference (the source, the reading, a target passage) so the menu and the gutter open it
the same way. Read only but for the judges' own receipts (``judgment_ledger``).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from learnloop.content.sources.span_aliases import reading_source
from learnloop.section_map import section_id_in_ir
from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval.corpus import Scope, library_scope
from learnloop.source_retrieval.search import search_spans
from learnloop.source_retrieval.verify import verify_spans

UNCHECKED = SC.UNCHECKED_LABEL
#: What each passage-link relation says, in the learner's words (the scratchpads' proposals use the same).
RELATION_REASONS = {
    "clarifies_distinction": "this passage draws the distinction you are working on",
    "new_application": "this passage takes it to a new application",
    "prerequisite_for": "this passage is what it builds on",
    "try_first": "try this passage first",
}


@dataclass(frozen=True)
class Finding:
    """One place elsewhere: its content reference and target, what found it, whether that was checked, and its rank
    within its finder (lower first)."""

    found_by: str  # passage_link | correspondent | search
    extraction_id: str
    span_id: str
    source_id: str
    source_title: str
    checked: bool
    rank: int
    reason: str
    quote: str = ""
    judgment_ref: str | None = None

    def target(self) -> dict[str, Any]:
        return {"content": {"kind": "source", "source_id": self.source_id, "extraction_id": self.extraction_id,
                            "view": "render"},
                "target": {"span_id": self.span_id}}


def by_passage_links(repository: Any, connection: Any, places: Iterable[tuple[str, str]]) -> list[Finding]:
    from learnloop.db.stores.passage_link_reads import links_elsewhere

    out = []
    for rank, link in enumerate(links_elsewhere(connection, places)):
        source_id = reading_source(repository, str(link["extraction_id"]))
        if source_id is None:
            continue
        out.append(Finding("passage_link", str(link["extraction_id"]), str(link["span_id"]), source_id, "",
                           True, rank, RELATION_REASONS.get(str(link["relation"]), "this passage is tied to it"),
                           str(link["quote"] or ""), str(link["ledger_id"])))
    return out


def by_correspondents(vault: Any, repository: Any, places: Iterable[tuple[str, str]], *, search_fallback: bool,
                      embedder: Any | None = None, cache: Any | None = None) -> list[Finding]:
    """Each passage's section's correspondents in the other books, judged first; the search fallback's hits
    (keyword, no model) only when asked and when no judged one exists."""

    out: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for extraction_id, span_id in places:
        ir = repository.load_document_ir(extraction_id)
        section_id = section_id_in_ir(ir, span_id) if ir is not None else None
        if section_id is None or (extraction_id, section_id) in seen:
            continue
        seen.add((extraction_id, section_id))
        try:
            view = SC.correspondents(vault, repository, extraction_id, section_id, search_fallback=search_fallback,
                                     embedder=embedder, cache=cache)
        except SC.CoverageError:
            continue
        judged = [(group, source) for group in view.get("learning_objects") or ()
                  for source in group.get("sources") or ()]
        for group, source in judged:
            for section in source.get("sections") or ():
                out.append(Finding("correspondent", str(section["extraction_id"]), str(section["jump"]["span_id"]),
                                   str(section["source_id"]), str(section.get("source_title") or ""), True,
                                   len(out), f"{section.get('source_title') or 'another source'} treats "
                                   f"{group.get('title') or 'the same topic'} here"))
        for source in ((view.get("search") or {}).get("sources") or ()) if not judged else ():
            for section in source.get("sections") or ():
                out.append(Finding("correspondent", str(section["extraction_id"]), str(section["jump"]["span_id"]),
                                   str(section["source_id"]), str(section.get("source_title") or ""), False,
                                   len(out), UNCHECKED))
    return out


def by_search(vault: Any, repository: Any, text: str, *, exclude_sources: Iterable[str] = (),
              exclude_places: Iterable[tuple[str, str]] = (), deep: bool, verify: bool,
              embedder: Any | None = None, verify_client: Any | None = None, owner_id: str = "",
              pick_at_most: int) -> list[Finding]:
    """Passages found for ``text`` in the other sources; with ``verify``, the judge's picks are checked and the rest
    dropped (a judge that looked at a hit and did not pick it said it does not say this); without a judgment,
    every hit is unchecked."""

    words = " ".join(str(text or "").split())
    if len(words) < 2:
        return []
    excluded_sources = set(exclude_sources)
    excluded = {(str(extraction_id), str(span_id)) for extraction_id, span_id in exclude_places}
    library = library_scope(repository)
    scope = Scope("elsewhere", {key: value for key, value in library.extractions.items()
                                if value.source_id not in excluded_sources}, frozenset(excluded))
    if not scope.extractions:
        return []
    search = search_spans(vault, repository, words, scope, deep=deep, embedder=embedder, owner_id=owner_id,
                          consumer="elsewhere")
    hits = [hit for hit in search.hits if hit.key not in excluded]
    if not hits:
        return []
    checked: dict[tuple[str, str], bool] = {}
    if verify:
        verdict = verify_spans(vault, repository, question=words, pool=hits, pick_at_most=pick_at_most,
                               client=verify_client, owner_id=owner_id)
        if verdict.status in ("verified", "cached"):
            picked = [hit.key for hit in verdict.picks]
            hits = [hit for key in picked for hit in hits if hit.key == key]
            checked = {key: True for key in picked}
    return [Finding("search", hit.extraction_id, hit.span_id, hit.source_id, hit.source_title,
                    checked.get(hit.key, False), rank,
                    "says this in other words" if checked.get(hit.key) else UNCHECKED)
            for rank, hit in enumerate(hits[:pick_at_most])]


def as_proposal(finding: Finding) -> Mapping[str, Any]:
    """A finding as a ``pad_proposals`` row's content (the caller adds the ids and the time)."""

    return {"found_by": finding.found_by, "target_spec": finding.target(), "reason_md": finding.reason,
            "quote": finding.quote, "judgment_ref": finding.judgment_ref}


__all__ = ["Finding", "RELATION_REASONS", "UNCHECKED", "as_proposal", "by_correspondents", "by_passage_links",
           "by_search"]
