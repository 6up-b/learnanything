"""The one machinery behind promoted rows and pad proposals (spec §9.1, §10.6): passage links, correspondents and search
(with ``verify_spans``), each finding labelled checked or "found by search, not checked"; and the pad proposals RD4
deferred, now found by correspondents and search too. Every judge and search here is a fake: no model call."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.passage_union import elsewhere as E
from learnloop.pads.proposals import pad_proposals, propose_for_blocks
from learnloop.source_retrieval.search import SpanHit, SpanSearch
from learnloop.source_retrieval.verify import Verification
from tests.desk_helpers import seed_reading
from tests.reader_rd4_helpers import PAD, create_pad, insert, pad_vault, vault


def _hit(extraction_id, span_id, source_id="src_other", title="Another book"):
    return SpanHit(extraction_id=extraction_id, span_id=span_id, source_id=source_id, source_title=title, text="t",
                   block_type="Text", section_path=[], page=3, ordinal=1)


def test_search_findings_are_the_judges_picks_checked_or_every_hit_unchecked_without_a_judgment(tmp_path,
                                                                                                 monkeypatch):
    paths, repository, _batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_other", revision_id="rev_o", extraction_id="ext_other", spans=["o1", "o2"])
    seed_reading(repository, source_id="src_here", revision_id="rev_h", extraction_id="ext_here", spans=["h1"])
    seen = {}

    def search(_vault, _repository, words, scope, **kwargs):
        seen["scope"], seen["deep"] = sorted(scope.extractions), kwargs["deep"]
        return SpanSearch(query=words, hits=[_hit("ext_other", "o1"), _hit("ext_other", "o2")])

    monkeypatch.setattr(E, "search_spans", search)
    monkeypatch.setattr(E, "verify_spans", lambda *_a, pool, **_k: Verification("verified", picks=[pool[1]]))
    checked = E.by_search(vault(paths), repository, "a passage about kernels", exclude_sources=["src_here"],
                          exclude_places=[("ext_here", "h1")], deep=True, verify=True, pick_at_most=4)
    # The passage's own source is left out of the search; the judge kept o2 and dropped o1.
    assert seen == {"scope": ["ext_other"], "deep": True}
    assert [(f.span_id, f.checked, f.reason) for f in checked] == [("o2", True, "says this in other words")]
    unchecked = E.by_search(vault(paths), repository, "a passage about kernels", deep=False, verify=False,
                            pick_at_most=1)
    assert [(f.span_id, f.checked, f.reason) for f in unchecked] == [("o1", False, E.UNCHECKED)]


def test_correspondents_judged_first_and_the_keyword_fallback_only_without_them(tmp_path, monkeypatch):
    paths, repository, _batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_here", revision_id="rev_h", extraction_id="ext_here", spans=["h1"])
    section = {"extraction_id": "ext_b", "section_id": "u2", "source_id": "src_b", "source_title": "Book B",
               "jump": {"span_id": "b7"}}
    judged = {"learning_objects": [{"title": "kernels", "sources": [{"sections": [section]}]}], "search": None}
    fallback = {"learning_objects": [], "search": {"sources": [{"sections": [section]}]}}
    for view, checked, reason in ((judged, True, "Book B treats kernels here"), (fallback, False, E.UNCHECKED)):
        monkeypatch.setattr(E.SC, "correspondents", lambda *_a, view=view, **_k: view)
        [finding] = E.by_correspondents(vault(paths), repository, [("ext_here", "h1")], search_fallback=True)
        assert (finding.extraction_id, finding.span_id, finding.checked, finding.reason) == (
            "ext_b", "b7", checked, reason)


def test_a_pad_block_with_no_passage_link_gets_a_correspondent_then_a_search_proposal(tmp_path, monkeypatch):
    """RD4 deferred these two: a block linked to a passage whose section another book treats (a judged
    correspondent), and a block linked to nothing (its words found by keyword, unchecked)."""

    paths, repository, batches = pad_vault(tmp_path)
    seed_reading(repository, source_id="src_here", revision_id="rev_h", extraction_id="ext_here", spans=["h1"])
    finders = SimpleNamespace(correspondents=[], search=[])
    monkeypatch.setattr(E, "by_correspondents", lambda *_a, **_k: list(finders.correspondents))
    monkeypatch.setattr(E, "by_search", lambda *_a, **_k: list(finders.search))
    create_pad(batches)
    batches.pad(PAD, insert("q1", "The passage h1.", kind="source_quote", provenance="source"),
                {"op": "link_anchor", "block_id": "q1", "extraction_id": "ext_here", "span_id": "h1",
                 "expected_anchor_head": None},
                insert("n1", "so the kernel decides it", kind="note", version_id="v1", position="a1",
                       payload={"parent_block_id": "q1"}),
                insert("t1", "an unlinked thought about images", version_id="v2", position="a2"))
    finders.correspondents = [E.Finding("correspondent", "ext_b", "b7", "src_b", "Book B", True, 0,
                                        "Book B treats kernels here")]
    finders.search = [E.Finding("search", "ext_c", "c1", "src_c", "Book C", False, 0, E.UNCHECKED)]
    written = propose_for_blocks(repository, ["n1", "t1"], vault=vault(paths))
    assert {(row["block_id"], row["found_by"], row["reason_md"]) for row in written} == {
        ("n1", "correspondent", "Book B treats kernels here"), ("t1", "search", E.UNCHECKED)}
    shown = {row["block_id"]: row for row in pad_proposals(repository, PAD)["proposals"]}
    assert shown["t1"]["target"] == {"content": {"kind": "source", "source_id": "src_c", "extraction_id": "ext_c",
                                                 "view": "render"}, "target": {"span_id": "c1"}}
    # Without the vault (the call RD4 made) only passage links are looked at, as before.
    batches.pad(PAD, insert("t3", "another unlinked thought", version_id="v3", position="a3"))
    assert propose_for_blocks(repository, ["t3"]) == []
