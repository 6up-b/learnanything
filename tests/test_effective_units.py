"""Effective-unit shape from boundary overrides (spec_source_ingestion_v2 §5.3).

Deterministic, zero-LLM preview of how the learner's merge/split intents reshape
an extraction's units — covering merge chains, split with intro blocks, split
no-ops, and plain passthrough.
"""

from __future__ import annotations

from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit
from learnloop.services.source_unit_selection import compute_effective_units


def _block(span_id, text, *, ordinal, section_path=None):
    return DocumentBlock.build(
        span_id=span_id,
        block_type="Text",
        text=text,
        ordinal=ordinal,
        section_path=section_path or [],
    )


def _unit(unit_id, label, ordinal, span_ids):
    return DocumentUnit(
        unit_id=unit_id,
        label=label,
        ordinal=ordinal,
        semantic_hash=f"sha256:{unit_id}",
        span_ids=list(span_ids),
    )


def _ir(blocks, units):
    return DocumentIR(extractor="test", extractor_version="1", blocks=blocks, units=units)


def test_passthrough_no_overrides():
    ir = _ir(
        [_block("s1", "aaaa" * 5, ordinal=1), _block("s2", "bbbb" * 5, ordinal=2)],
        [_unit("u1", "One", 1, ["s1"]), _unit("u2", "Two", 2, ["s2"])],
    )
    effective = compute_effective_units(ir, [])
    assert [e["effective_id"] for e in effective] == ["u1", "u2"]
    assert all(e["kind"] == "unchanged" for e in effective)
    assert effective[0]["approx_tokens"] == len("aaaa" * 5) // 4
    assert effective[0]["source_unit_ids"] == ["u1"]


def test_merge_chain_fuses_three_units():
    ir = _ir(
        [
            _block("s1", "a" * 8, ordinal=1),
            _block("s2", "b" * 8, ordinal=2),
            _block("s3", "c" * 8, ordinal=3),
            _block("s4", "d" * 8, ordinal=4),
        ],
        [
            _unit("u1", "A", 1, ["s1"]),
            _unit("u2", "B", 2, ["s2"]),
            _unit("u3", "C", 3, ["s3"]),
            _unit("u4", "D", 4, ["s4"]),
        ],
    )
    overrides = [
        {"op": "merge_with_next", "unitId": "u1"},
        {"op": "merge_with_next", "unitId": "u2"},
    ]
    effective = compute_effective_units(ir, overrides)
    # u1+u2+u3 fold into one merged unit; u4 passes through unchanged.
    assert len(effective) == 2
    merged = effective[0]
    assert merged["kind"] == "merged"
    assert merged["label"] == "A + B + C"
    assert merged["source_unit_ids"] == ["u1", "u2", "u3"]
    assert merged["block_count"] == 3
    assert merged["approx_tokens"] == (8 * 3) // 4
    assert effective[1]["effective_id"] == "u4"
    assert effective[1]["kind"] == "unchanged"


def test_split_with_intro_blocks():
    ir = _ir(
        [
            _block("s1", "intro" * 4, ordinal=1, section_path=["chap"]),
            _block("s2", "one" * 4, ordinal=2, section_path=["chap", "alpha"]),
            _block("s3", "two" * 4, ordinal=3, section_path=["chap", "beta"]),
            _block("s4", "more" * 4, ordinal=4, section_path=["chap", "alpha"]),
        ],
        [_unit("u1", "Chapter", 1, ["s1", "s2", "s3", "s4"])],
    )
    effective = compute_effective_units(ir, [{"op": "split_at_heading", "unitId": "u1"}])
    labels = [e["label"] for e in effective]
    assert labels == ["Chapter › (intro)", "Chapter › alpha", "Chapter › beta"]
    assert all(e["kind"] == "split" for e in effective)
    assert all(e["source_unit_ids"] == ["u1"] for e in effective)
    # "alpha" gathers both s2 and s4 despite the interleaved "beta" block.
    alpha = next(e for e in effective if e["label"].endswith("alpha"))
    assert alpha["block_count"] == 2
    assert not any(e.get("split_noop") for e in effective)


def test_split_no_op_without_level2_headings():
    ir = _ir(
        [
            _block("s1", "x" * 8, ordinal=1, section_path=["chap"]),
            _block("s2", "y" * 8, ordinal=2, section_path=["chap"]),
        ],
        [_unit("u1", "Flat", 1, ["s1", "s2"])],
    )
    effective = compute_effective_units(ir, [{"op": "split_at_heading", "unitId": "u1"}])
    assert len(effective) == 1
    assert effective[0]["split_noop"] is True
    assert effective[0]["effective_id"] == "u1"
    assert effective[0]["block_count"] == 2
