"""E0 delivery arms D0-D3 (spec §5.3): D0/D1 reproduce the production tutor."""
from __future__ import annotations

import pytest

from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import delivery as D
from learnloop.experiments.contextual_embeddings import pins
from learnloop.tutor.context_delivery import BlockSource
from learnloop.tutor.tutor_qa import _reader_source_spans
from tests.e0_fakes import build_e0_vault
from tests.test_tutor_delivery_fixes import THEOREM, _span_of, _vault


def _shape(spans):
    return [(str(span["span_id"]), span["relation"], span["text"]) for span in spans]


@pytest.mark.parametrize("quote", [None, "hence t is real"])
def test_d0_and_d1_reproduce_the_production_reader_delivery(tmp_path, quote):
    extra = {"ch_thm": ("Chapter 3 Spectral theorem", [(THEOREM, 1)])}
    paths, repository = _vault(tmp_path, extra_units=extra)
    step = _span_of(repository, "Paragraph six")
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    source = BlockSource(paths.sqlite_path)
    selection = D.Selection("ext_text", step, (), quote)
    production_d0 = _reader_source_spans(repository, "ext_text", step, selection_quote_md=quote,
                                         expanded=False, resolve_references=False, budget_tokens=D.D0_BUDGET_TOKENS)
    production_d1 = _reader_source_spans(repository, "ext_text", step, selection_quote_md=quote,
                                         budget_tokens=pins.D1_EVIDENCE_TOKENS)
    assert _shape(D.reader_d0(source, snapshot, selection).spans) == _shape(production_d0)
    assert _shape(D.reader_d1(source, snapshot, selection).spans) == _shape(production_d1)
    d0 = D.reader_d0(source, snapshot, selection)
    if quote:
        # The observed defect: a quoted one-block selection gets i-3 and i-2 only.
        around = [span["span_id"] for span in d0.spans if span["relation"] == "surrounding"]
        assert _span_of(repository, "Paragraph five") not in around
    d1 = D.reader_d1(source, snapshot, selection)
    assert any(span["relation"] == "referenced" for span in d1.spans)


def test_d0_cuts_cover_only_their_canonical_prefix():
    canonical = "alpha   beta\ngamma delta epsilon"
    assert D.canonical_prefix_end(canonical, "alpha   beta") == len("alpha   beta")
    assert D.canonical_prefix_end(canonical, "alpha beta gamma") == canonical.index("gamma") + len("gamma")


def test_d2_is_the_whole_permitted_section_and_d3_the_whole_permitted_source(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    source = BlockSource(paths.sqlite_path)
    exercise_block = next(block for block in snapshot.blocks["ext_book"] if block.text.startswith("Exercise 2.1"))
    selection = D.Selection("ext_book", exercise_block.span_id)
    d2 = D.whole_section(source, snapshot, selection)
    d3 = D.whole_source(source, snapshot, selection)
    assert d2.arm == "D2" and d3.arm == "D3"
    for delivered in (d2, d3):
        texts = " ".join(span["text"] for span in delivered.spans)
        assert "Solution: apply linearity" not in texts  # full-source policy filtering
        assert delivered.receipt["omitted"]["withheld"] >= 1
        assert not any(span.get("trimmed") for span in delivered.spans)
    assert "Definition 1.1" in " ".join(span["text"] for span in d3.spans)
    assert "Definition 1.1" not in " ".join(span["text"] for span in d2.spans)
    # Complete blocks: nothing shortened.
    for span in d3.spans:
        block = next(block for block in snapshot.blocks["ext_book"] if block.span_id == span["span_id"])
        assert span["text"] == block.text


def test_a_source_that_does_not_fit_runs_the_named_fallback_never_a_truncation(tmp_path, monkeypatch):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    source = BlockSource(paths.sqlite_path)
    block = next(block for block in snapshot.blocks["ext_book"] if block.text.startswith("Theorem 1.2"))
    selection = D.Selection("ext_book", block.span_id)
    monkeypatch.setattr(pins, "GENERATOR_CONTEXT_TOKENS", sum(pins.GENERATOR_RESERVES.values()) + 300)
    d3 = D.whole_source(source, snapshot, selection)
    assert d3.arm.startswith("D3_fallback_")
    assert d3.receipt["does_not_fit"]["arm"] == "D3"
    d2 = D.whole_section(source, snapshot, selection)
    assert d2.arm == "D2_fallback_d1" and d2.receipt["does_not_fit"]["arm"] == "D2"


def test_retrieved_d0_and_d1_deliver_the_same_initial_evidence(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    source = BlockSource(paths.sqlite_path)
    ranked = [unit.unit_id for unit in snapshot.units if unit.extraction_id == "ext_book"][:3]
    d0 = D.retrieved_d0(snapshot, ranked)
    d1 = D.retrieved_d1(source, snapshot, ranked)
    assert [span["span_id"] for span in d0.spans][:2] == [span["span_id"] for span in d1.spans][:2]
    assert all(len(span["text"]) <= 600 for span in d0.spans)
    blocks = {(block.extraction_id, block.span_id): block for block in snapshot.blocks["ext_book"]}
    coverage = d0.coverage(blocks)
    assert all(end - start <= 600 for _e, _s, start, end in coverage)
