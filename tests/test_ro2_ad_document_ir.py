"""RO2 landing, second pass (ruling R6): AD reads a reading's structure only through its chokepoint.

The landing smoke found every serve on the owner's copies rolled back: H2's span mapping
(``VaultReadingMap.los_for_span`` -> ``section_map.section_id_for_span`` -> ``repository.load_document_ir``)
read ``source_document_units`` raw inside AD's operation, AD's guard refused it, and the serve's
savepoint dropped every AD write of the serve (AD1's receipts, the frozen inputs, the reading sweep's
rows, RO2's draw). A Reader question anchored to a block span was enough.

The reproduction: a span-anchored Reader question on the textbook fake, at FG1's tag and RO1's
successor. The card builds with the inquiry on it, the reading map answers inside the operation what
the incumbent's mapping answers outside it, and the serve records its AD rows. The structural guard
(R7) is ``tests/test_ro2_ad_raw_document_reads.py``. Fakes only; no model call.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import rows

SERVED = "2026-10-12T09:00:00Z"
VERSIONS = pytest.mark.parametrize("version", ["mvp-0.45", "mvp-0.46"], ids=["fg1_tag", "ro1_successor"])


def _textbook_with_span_question(tmp_path, version: str):
    """The textbook fake, one LO citing a span of ``ext_text`` in its provenance, and a Reader question
    anchored to that span (``span:ext_text/<span>``, as the Reader writes it)."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.helpers import set_algorithm_version
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    unit, span_ids = next(iter(spans.items()))
    span = span_ids[-1]
    lo_path = paths.learning_object_path("linear-algebra", "lo_matrices")
    lo = read_yaml(lo_path)
    provenance = dict(lo.get("provenance") or {})
    provenance["source_refs"] = [*(provenance.get("source_refs") or []), {
        "ref_type": "canonical_source", "ref_id": "src_text", "source_id": "src_text", "extraction_id": "ext_text",
        "locator": f"span:ext_text/{span}", "span_ids": [span]}]
    lo["provenance"] = provenance
    write_yaml(lo_path, lo)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO question_events(id, context, note_id, question_md, answer_status, answered_at, resolution, "
            "created_at) VALUES ('qe_span', 'reader', ?, 'Why does this hold?', 'answered', ?, 'open', ?)",
            (f"span:ext_text/{span}", "2026-10-11T09:05:00Z", "2026-10-11T09:00:00Z"))
    return paths, repository, "ext_text", span, unit


@VERSIONS
def test_a_span_anchored_reader_question_does_not_poison_the_card_build(tmp_path, version):
    """The reproduction (fails before the fix: AD guard denied read of source_document_units by
    learnloop.section_map, and the operation was poisoned)."""

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.operation import ad_operation

    paths, repository, _extraction, _span, _unit = _textbook_with_span_question(tmp_path, version)
    vault = load_vault(paths.root)
    with ad_operation(vault, repository, read_only=True) as op:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            built = HC.build_sections(op.vault, connection, op.view.item("pi_eigen_1"), served_at=SERVED, view=op.view)
    assert [entry["evidence_id"] for entry in built["sections"]["inquiries"]] == ["question:qe_span"]


@VERSIONS
def test_the_reading_map_answers_inside_the_operation_what_the_incumbent_answers_outside(tmp_path, version):
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.reading import VaultReadingMap
    from learnloop.reader.reader_progression import learning_objects_for_section, learning_objects_for_span

    paths, repository, extraction, span, unit = _textbook_with_span_question(tmp_path, version)
    vault = load_vault(paths.root)
    outside_span = learning_objects_for_span(vault, Repository(paths.sqlite_path), extraction_id=extraction, span_id=span)
    outside_section = learning_objects_for_section(vault, Repository(paths.sqlite_path), extraction_id=extraction,
                                                   section_id=unit)
    assert outside_span == ["lo_matrices"] and outside_section == ["lo_matrices"]
    with ad_operation(vault, repository, read_only=True) as op:
        mapping = VaultReadingMap(op.vault, repository, op.view)
        inside_span = mapping.los_for_span(extraction, span)
        inside_section = mapping.los_for_section(extraction, unit)
    assert (inside_span, inside_section) == (outside_span, outside_section)


@VERSIONS
def test_the_serve_records_its_ad_rows_with_a_span_anchored_question(tmp_path, version):
    """The serve's AD record (AD1's receipts, the frozen inputs, RO2's draw) is written, not rolled back,
    and H3's frozen card carries the inquiry."""

    from learnloop.adaptive_difficulty.serve import record_plan_serve

    paths, repository, *_ = _textbook_with_span_question(tmp_path, version)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk', 'practice', 10, 'hash', ?)", (SERVED,))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_1', 'blk', 'pi_eigen_2', 'chooser', ?)", (SERVED,))
    vault = load_vault(paths.root)
    with repository.atomic():
        record = record_plan_serve(vault, repository, presentation_id="pp_1", practice_item_id="pi_eigen_2",
                                   served_at=SERVED)
    assert record.skipped is None, record.skipped
    assert record.history_draw and record.frozen_inputs and record.receipt_ids
    assert rows(paths.sqlite_path, "SELECT * FROM ad_history_forecast_draws")
    frozen = rows(paths.sqlite_path, "SELECT content_json FROM item_forecast_payloads WHERE owner_key LIKE "
                                     "'ad_llm_history_state:%' AND owner_key LIKE '%:H3'")
    assert '"question:qe_span"' in frozen[0]["content_json"]
