"""AD23 redesign, step 4: what an operation reads of protected material equals what it reads with
that material physically absent, blocks included.

* F48 (Codex verify): a public span P and a held-out span H share one section; an LO cites only H.
  A view of P maps, in AD, to the LOs citing visible material only, exactly as when H was never
  extracted (failed before: the Reader's whole-section mapping resolved provenance against every
  block of the section, H included, and assigned P's exposure to H's LO);
* the projected document IR and vault: with H held out they equal the copy without H (blocks, units,
  the Reader's section mapping, the LO's provenance);
* every protected table's rows as the operation's view reads them, on the contract's two copies (A:
  every class of protected material present and protected; B: absent), equal B's, but for the
  tables whose rows are scoped by the protection epoch instead (``test_ad_epoch.py``).

The F48 case uses only production entry points (the sweep), so it runs on the pre-redesign tree.
Fakes only: no network, no model call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest
import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, ad23_vault
from tests.helpers import write_yaml

EXT = "ext_f48"
P, H = "p_span", "h_span"
HELD_LO = "lo_f48_held"
T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _cite(paths, lo: str, span: str) -> None:
    path = paths.learning_object_path("linear-algebra", lo)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "src_f48", "source_id": "src_f48", "extraction_id": EXT,
        "span_ids": [span], "locator": f"span:{EXT}/{span}"}]}
    write_yaml(path, payload)


def _mixed_section(tmp_path, *, absent: bool):
    """One extraction, one section holding P and (unless ``absent``) H. ``LO`` cites P, ``HELD_LO``
    cites H (in both copies: an LO is not protected material, its reference into H is). One reader
    view of P."""

    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

    from tests.test_source_inventory import _persist

    paths = ad23_vault(tmp_path / ("absent" if absent else "protected"), items=("pi_m1a",),
                       learning_objects={HELD_LO: ("pi_f48",)})
    made = _iso(T0 - timedelta(days=7))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES ('src_f48', 'pdf', 'file:///f48.pdf', ?, ?)", (made, made))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) "
                           "VALUES ('rev_f48', 'src_f48', 'sha256:f48', ?)", (made,))
        connection.commit()
    spans = [P] if absent else [P, H]
    blocks = [DocumentBlock.build(span_id=span, block_type="Text", text=f"Teaching text of {span}.", ordinal=index,
                                  page=1, section_path=["sec_mixed"]) for index, span in enumerate(spans)]
    units = [DocumentUnit(unit_id="sec_mixed", label="sec_mixed", ordinal=0, semantic_hash="sha256:sec_mixed",
                          page_start=1, page_end=1, span_ids=list(spans))]
    repository = Repository(paths.sqlite_path)
    _persist(repository, DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                                    health=ExtractionHealth()), revision_id="rev_f48", extraction_id=EXT)
    _cite(paths, LO, P)
    _cite(paths, HELD_LO, H)
    repository.insert_source_exposure_event(
        {"context": "reader", "extraction_id": EXT, "span_id": P, "revision_id": "rev_f48", "source_id": "src_f48",
         "entity_type": "reader", "entity_id": "visit_f48", "created_at": _iso(T0 - timedelta(hours=5))})
    return paths


def _hold_h(monkeypatch) -> None:
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset({(EXT, H)}))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _swept(paths) -> list[tuple[str, str, str, str]]:
    from learnloop.adaptive_difficulty.reading import sweep

    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    sweep(vault, repository, as_of=_iso(T0), sweep_kind="backfill")
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return sorted((str(kind), str(subkind), str(table), str(lo)) for kind, subkind, table, lo in connection.execute(
            "SELECT kind, subkind, source_table, learning_object_id FROM ad_reading_opportunities"))


def test_a_public_span_in_a_mixed_section_maps_only_to_visible_provenance(tmp_path, monkeypatch):
    """F48: the reader view of P records a reading opportunity for exactly the LOs it records when H
    was never extracted (failed before: also for ``HELD_LO``, whose only citation is H)."""

    _hold_h(monkeypatch)
    protected = _swept(_mixed_section(tmp_path, absent=False))
    absent = _swept(_mixed_section(tmp_path, absent=True))
    assert protected == absent
    assert ("reading", "passage_viewed", "source_exposure_events", LO) in absent
    assert all(row[3] != HELD_LO for row in protected)


def test_the_projected_ir_and_vault_equal_the_copy_without_the_held_out_block(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.reader.reader_progression import learning_objects_for_section, learning_objects_for_span

    _hold_h(monkeypatch)
    seen = {}
    for absent in (False, True):
        paths = _mixed_section(tmp_path, absent=absent)
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        with ad_operation(vault, repository) as op:
            ir = op.repository.load_document_ir(EXT)
            if not absent:
                # A's projection drops the LO's only reference (into H); B keeps it dangling.
                assert op.vault.learning_objects[HELD_LO].provenance.source_refs == []
            seen[absent] = {
                "blocks": [block.span_id for block in ir.blocks],
                "units": [unit.span_ids for unit in ir.units],
                "section": learning_objects_for_section(op.vault, op.repository, extraction_id=EXT,
                                                        section_id="sec_mixed"),
                "span": learning_objects_for_span(op.vault, op.repository, extraction_id=EXT, span_id=P),
            }
    assert seen[False] == seen[True]
    assert seen[True]["blocks"] == [P] and seen[True]["section"] == [LO]


def test_a_whole_extraction_held_out_reads_as_no_extraction(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.content.sources import exam_material

    paths = _mixed_section(tmp_path, absent=False)
    material = exam_material.Material(extractions=frozenset({EXT}))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)
    with ad_operation(load_vault(paths.root), Repository(paths.sqlite_path)) as op:
        assert op.repository.load_document_ir(EXT) is None
        assert op.vault.learning_objects[LO].provenance.source_refs == []


#: Rows scoped by the protection epoch, not withheld (E2: ``test_ad_epoch.py``): a run proposed
#: before the material was protected, and its judgments, stand in A, out of force at A's epoch.
EPOCH_SCOPED = {"ad_relatedness_runs": None, "judgment_ledger": "ad_relatedness"}


def test_every_protected_table_reads_as_in_the_absent_copy(tmp_path, monkeypatch):
    """For every protected table, the operation's view of copy A (protected material present and
    protected) equals its view of copy B (absent): ids normalized away, no table skipped but the
    epoch-scoped ones (named, with their reason)."""

    from learnloop.adaptive_difficulty import protected_tables as T
    from learnloop.adaptive_difficulty.operation import ad_operation

    from tests import test_ad23_contract as C

    copies = C.make_copies(tmp_path, coupled=True)
    C._hold_out(monkeypatch)
    seen: dict[str, dict[str, list[str]]] = {}
    for name, paths in zip(("protected", "absent"), copies):
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        out: dict[str, list[str]] = {}
        with ad_operation(vault, repository) as op, closing(connect(paths.sqlite_path, read_only=True)) as connection:
            for table in sorted(T.COLUMNS):
                rows = op.view.rows(connection, table)
                if table in EPOCH_SCOPED:
                    task = EPOCH_SCOPED[table]
                    rows = [row for row in rows if task is not None and row.get("task") != task]
                # The view reads only rows of its own epoch; each copy's epoch is its own (a digest
                # of what it withholds), so the stamp is named, not compared.
                rows = [{**row, "protection_epoch": "<the copy's epoch>"} if "protection_epoch" in row else row
                        for row in rows]
                out[table] = sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)
        seen[name] = out
    differing = sorted(table for table in T.COLUMNS if seen["protected"][table] != seen["absent"][table])
    assert differing == [], {table: (len(seen["protected"][table]), len(seen["absent"][table])) for table in differing}
    # The comparison is not vacuous: the protected copy holds rows the view withheld.
    with closing(connect(copies[0].sqlite_path, read_only=True)) as connection:
        raw = connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]
    assert raw > len(seen["protected"]["practice_attempts"]) > 0
