"""RW4d (syntopic reading, kept) composed with RW3b (discovered cues), the landing's interaction test.

The two Reader layers meet on the same passages: a discovered margin cue
(RW3b) and a ``⇄`` mark of a kept comparison (RW4d) can sit beside one
passage, and both answer to exam protection. What this pins:

* **Independent marks.** Keeping a comparison changes no cue (the ``⇄`` mark
  is the learner's own, outside the cue budget), and discovery changes no
  kept mark.
* **One protection, never looser in the cues.** RW4d asks
  ``exam_material`` (exam and held-out material); RW3b's cue guard
  (``passage_cues.protection``) is ``teaching_exclusions`` (which contains the
  same exam material) plus ``held_out_material``. So every passage RW4d's
  predicate withholds is also one the cues never surface: checked key by key
  over both books.
* **Whole-comparison withholding is RW4d's alone.** When the *other* book's
  passage is held out, the comparison is withheld whole (no mark, no reopen,
  no kept object), while the still-open passage keeps its own discovered cue;
  the cue carries only that passage's own words and its target, nothing of
  the comparison.

Fakes only (the cue judge and the comparison service are deterministic fakes).
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.source_retrieval import passage_cues as PC
from learnloop.source_retrieval.corpus import exam_withheld
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import call, context
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config, snake
from tests.test_compare_sources_keep import PINS, QUESTION, _block_text, _fake_service

#: ext_book's chapter 3 holds the pinned ext_book:s6 (header s6, then s7-s9).
BOOK_UNITS = ["ch_eigen", "ch_det", "ch_orth"]
TEXT_UNITS = ["ch5", "worked", "exercises", "solutions"]


def _vault(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake()
    return paths, ctx, repository, spans


def _discover(ctx) -> None:
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert job["state"] == "done"


def _cues(ctx) -> dict:
    return call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"})["cues"]


def _cue_spans(ctx) -> set[str]:
    return {mark["spanId"] for mark in _cues(ctx)["marks"]}


def _kept_spans(ctx, extraction: str) -> set[str]:
    return {mark["spanId"] for mark in call(ctx, "reader.kept_comparisons", {"extractionId": extraction})["marks"]}


def _compare_and_keep(ctx, monkeypatch) -> tuple[dict, dict]:
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    _fake_service(monkeypatch)
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": PINS})
    assert table["status"] == "ok" and table["comparisonId"]
    kept = call(ctx, "reader.library_compare_keep", {"askId": asked["askId"]})
    assert kept["kept"]["objects"]
    return asked, table


def _kept_object_count(ctx) -> int:
    # RW4e: the cue judge's role proposals on passages still open are not
    # kept-comparison objects (they are counted apart, never withheld here).
    return sum(1 for source in ("src_text", "src_book")
               for head in call(ctx, "reader.source_objects", {"sourceId": source})["sourceObjects"]
               if "instructional_role" not in json.dumps(head))


def test_a_cue_and_a_kept_mark_on_one_passage_are_independent_and_both_withheld(tmp_path, monkeypatch):
    _paths, ctx, repository, spans = _vault(tmp_path)
    _discover(ctx)
    cues_before = _cues(ctx)
    assert "t3" in {mark["spanId"] for mark in cues_before["marks"]}, "the row-swap passage carries a discovered cue"

    asked, _table = _compare_and_keep(ctx, monkeypatch)
    # The same passage now carries both: the cue, unchanged by the keep, and the ⇄ mark.
    assert _cues(ctx)["marks"] == cues_before["marks"]
    assert _cues(ctx)["withheld"] == cues_before["withheld"], "the ⇄ mark is outside the cue budget"
    assert "t3" in _kept_spans(ctx, "ext_text")
    marks_before = call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"})
    # Discovery again (a second open) changes no kept mark.
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_2"}))
    assert job["state"] == "done"
    assert call(ctx, "reader.kept_comparisons", {"extractionId": "ext_text"}) == marks_before

    # The passage held out: neither layer shows anything on it.
    save_unit_selection(repository, "ext_text", TEXT_UNITS, exam_use_modes={"ch5": "held_out_evaluation"})
    assert not _cue_spans(ctx) & set(spans["ch5"])
    assert _kept_spans(ctx, "ext_text") == set() and _kept_spans(ctx, "ext_book") == set()
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert caught.value.code == "comparison_withheld"
    assert _kept_object_count(ctx) == 0
    held_text = _block_text(repository, "ext_text:t3")
    assert held_text not in json.dumps(_cues(ctx))


def test_discovery_on_a_source_whose_kept_comparison_is_withheld_shows_only_its_own_passage(tmp_path, monkeypatch):
    _paths, ctx, repository, _spans = _vault(tmp_path)
    asked, table = _compare_and_keep(ctx, monkeypatch)
    assert "t3" in _kept_spans(ctx, "ext_text")
    book_text = _block_text(repository, "ext_book:s6")

    # The other book's pinned passage held out: the comparison is withheld whole.
    save_unit_selection(repository, "ext_book", BOOK_UNITS, exam_use_modes={"ch_det": "held_out_evaluation"})
    assert _kept_spans(ctx, "ext_text") == set() and _kept_spans(ctx, "ext_book") == set()
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare_reopen", {"askId": asked["askId"]})
    assert caught.value.code == "comparison_withheld"
    assert _kept_object_count(ctx) == 0

    # Discovery on the open book still finds its own (unprotected) passage.
    _discover(ctx)
    cues = _cues(ctx)
    assert "t3" in {mark["spanId"] for mark in cues["marks"]}
    payload = json.dumps(cues)
    for withheld in (table["comparisonId"], asked["askId"], book_text, "ext_book", "src_book"):
        assert withheld not in payload, withheld
    # Its judge read only the open source.
    assert all(book_text not in prompt for prompt in ctx.cue_judge_client.prompts)


def test_every_passage_rw4ds_predicate_withholds_is_one_the_cues_never_surface(tmp_path):
    paths, _ctx, repository, _spans = _vault(tmp_path)
    save_unit_selection(repository, "ext_text", TEXT_UNITS, exam_use_modes={"ch5": "held_out_evaluation"})
    save_unit_selection(repository, "ext_book", BOOK_UNITS, exam_use_modes={"ch_det": "held_out_evaluation"})
    vault = loaded(paths)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        keys = [(str(extraction), str(span)) for extraction, span in connection.execute(
            "SELECT extraction_id, span_id FROM source_document_blocks WHERE extraction_id IN ('ext_text', 'ext_book')")]
    assert keys
    withheld = exam_withheld(vault, repository, keys)
    assert {key[0] for key in withheld} == {"ext_text", "ext_book"}, "both chapters are held out"
    for extraction in ("ext_text", "ext_book"):
        guard = PC.protection(vault, repository, extraction)
        leaked = [key for key in withheld if key[0] == extraction and guard.allows(key)]
        assert leaked == [], f"cues could surface a passage RW4d withholds: {leaked}"
