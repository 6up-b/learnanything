"""What an AD operation reads of protected material equals what it reads with that material absent
(the AD23 redesign; since round 8, Option B).

Since round 8 a reading that holds any withheld block is ABSENT for AD's reading signals: its
structure and its reading events read as none (``MaterialView.reading_withheld``). The oracle is a
row deletion (``tests.ad_ingest_fakes.delete_reading``). The full property over production-built
readings is ``test_ad_protected_readings.py``; this file keeps:

* a mixed section (F48): no AD reading signal of that reading at all, as in the deleted copy; the
  vault's projection still drops an LO reference into the withheld block (items and LOs keep the
  block-level rule), and a locator-only one too (round 4);
* a whole extraction held out reads as no extraction;
* every protected table's rows as the operation's view reads them, on the contract's two copies (A:
  every class of protected material present and protected; B: the reading deleted), equal B's, but
  for the tables whose rows are scoped by the protection epoch instead (``test_ad_epoch.py``);
* the shared reference key function.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime, timedelta

import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, ad23_vault
from tests.ad_ingest_fakes import MARKER, Element, delete_reading, ingest_ir
from tests.helpers import write_yaml

EXT = "ext_f48"
HELD_LO = "lo_f48_held"
QUOTE = "Teaching text of the public passage"
T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
#: The production span ids of the mixed section's two blocks (ingest numbers them s1, s2).
P, H = "s1", "s2"


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _cite(paths, lo: str, refs) -> None:
    path = paths.learning_object_path("linear-algebra", lo)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["provenance"] = {"origin": "human", "source_refs": list(refs)}
    write_yaml(path, payload)


def _mixed_section(tmp_path, name: str = "protected"):
    """One extraction, built by Marker's production converter: public P and held-out H. ``LO``
    cites P, ``HELD_LO`` cites H (once by span id, once by its locator alone with a quote P's text
    holds). One Reader view of P."""

    from tests.test_source_inventory import _persist

    paths = ad23_vault(tmp_path / name, items=("pi_m1a",), learning_objects={HELD_LO: ("pi_f48",)})
    made = _iso(T0 - timedelta(days=7))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES ('src_f48', 'pdf', 'file:///f48.pdf', ?, ?)", (made, made))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) "
                           "VALUES ('rev_f48', 'src_f48', 'sha256:f48', ?)", (made,))
        connection.commit()
    ir = ingest_ir([Element("text", f"{QUOTE}."), Element("text", "The held-out exercise.")], style=MARKER)
    repository = Repository(paths.sqlite_path)
    _persist(repository, ir, revision_id="rev_f48", extraction_id=EXT)
    ref = {"ref_type": "canonical_source", "ref_id": "src_f48", "source_id": "src_f48"}
    _cite(paths, LO, [{**ref, "extraction_id": EXT, "span_ids": [P], "locator": f"span:{EXT}/{P}"}])
    _cite(paths, HELD_LO, [{**ref, "extraction_id": EXT, "span_ids": [H], "locator": f"span:{EXT}/{H}"},
                           {**ref, "locator": f"span:{EXT}/{H}", "quote": QUOTE}])
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


def test_a_mixed_reading_gives_no_reading_signal_as_if_deleted(tmp_path, monkeypatch):
    """F48 under Option B: the reading holds withheld H, so P's view records nothing and the
    reading's structure reads as none, exactly as in the copy with that reading deleted; the vault's
    projection still drops both of ``HELD_LO``'s references into H (the span id and the locator-only
    one, round 4), while ``LO``'s reference to visible P stands (items and LOs keep the block rule)."""

    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.reader.reader_progression import learning_objects_for_span

    _hold_h(monkeypatch)
    protected = _mixed_section(tmp_path)
    deleted = _mixed_section(tmp_path, "deleted")
    delete_reading(deleted.sqlite_path, EXT)
    for paths in (protected, deleted):
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        with ad_operation(vault, repository) as op:
            ir = op.repository.load_document_ir(EXT)
            assert ir is None or ir.blocks == []
            assert learning_objects_for_span(op.vault, op.repository, extraction_id=EXT, span_id=P) == []
            assert op.vault.learning_objects[HELD_LO].provenance.source_refs == []
            assert [ref.span_ids for ref in op.vault.learning_objects[LO].provenance.source_refs] == [[P]]
    assert _swept(protected) == _swept(deleted) == []


def test_a_whole_extraction_held_out_reads_as_no_extraction(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.content.sources import exam_material

    paths = _mixed_section(tmp_path)
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


def test_every_recorded_reference_shape_is_located_through_the_shared_key_function():
    """Round 4: the shapes AD reads references in (a provenance ref's extraction, span ids and
    locator; a recorded mapping's ``extraction_id``/``span_id``/``span_ids``/``locator``/``href``,
    a nested ``anchor`` under its parent's extraction, and ``ext:span`` keys) all resolve through
    ``exam_material.reference_keys``, which places a ref through ``source_ref_keys``."""

    from types import SimpleNamespace

    from learnloop.content.sources.exam_material import reference_keys, source_ref_keys

    ref = SimpleNamespace(extraction_id=None, span_ids=[], locator=f"span:{EXT}/{H}")
    assert source_ref_keys(ref)[0] == {(EXT, H)}
    assert reference_keys(ref)[0] == {(EXT, H)}
    context = {"extraction_id": "e1", "anchor": {"span_ids": ["a1"]},
               "citations": [{"locator": "span:e2/c1"}, {"href": "span:e3/h1"}],
               "grounded_keys": ["e4:g1"], "source_spans": [{"extraction_id": "e5", "span_id": "s5"}]}
    keys, whole = reference_keys(context)
    assert {("e1", "a1"), ("e2", "c1"), ("e3", "h1"), ("e4", "g1"), ("e5", "s5")} <= keys
    assert whole == set()
    assert reference_keys({"extraction_id": "e6"}) == (set(), {"e6"})


