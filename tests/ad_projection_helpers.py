"""What other test files use from ``tests/test_ad_projection.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta

import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository

from tests.ad23_fakes import LO, ad23_vault
from tests.ad_ingest_fakes import MARKER, Element, ingest_ir
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

    from tests.source_inventory_helpers import _persist

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
