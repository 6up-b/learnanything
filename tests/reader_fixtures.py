"""Reader source fixtures for RW1a's parity cases (spec §4.1, G51).

One interaction model on every source kind the Reader opens: a book (Marker
blocks, ``pdf``), a video transcript (caption cues, ``youtube``) and the
learner's own text notes (``textfile``). Each helper registers a source and
persists one completed extraction, ready for ``reader.ask``.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import captions_to_ir
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from tests.helpers import NOW
from tests.test_source_inventory import _persist

_CLOCK = FrozenClock(NOW)


def register_source(repo: Repository, *, source_id: str, revision_id: str, kind: str, uri: str) -> None:
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) VALUES (?,?,?,?,?)",
            (source_id, kind, uri, now, now),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            (revision_id, source_id, f"sha256:{revision_id}", now),
        )
        connection.commit()


def transcript_source(repo: Repository, *, extraction_id: str = "ext_video") -> dict[str, str]:
    """A YouTube transcript: one caption block per cue, one unit."""

    register_source(repo, source_id="src_video", revision_id="rev_video", kind="youtube",
                    uri="https://www.youtube.com/watch?v=hvjkcmzfix8")
    ir = captions_to_ir(
        [
            {"start": 0.0, "end": 4.0, "text": "A mixture picks a component, then samples from it."},
            {"start": 4.0, "end": 9.0, "text": "So the density is weighted by the chance of each component."},
            {"start": 9.0, "end": 14.0, "text": "Conditioning on the coin flip gives the CDF directly."},
        ],
        title="Mixtures, explained",
    )
    _persist(repo, ir, revision_id="rev_video", extraction_id=extraction_id)
    return {"source_id": "src_video", "extraction_id": extraction_id, "span_id": "s2", "parent_span": "s2"}


def notes_source(repo: Repository, *, extraction_id: str = "ext_notes") -> dict[str, str]:
    """The learner's own text notes, ingested as a ``textfile`` source."""

    register_source(repo, source_id="src_notes", revision_id="rev_notes", kind="textfile",
                    uri="file:///notes/mixtures.md")
    blocks = [
        DocumentBlock.build(span_id="n0", block_type="SectionHeader", text="My mixture notes",
                            ordinal=0, section_path=["notes"]),
        DocumentBlock.build(span_id="n1", block_type="Text",
                            text="F_X(x) = p F_Y(x) + (1 - p) F_Z(x): condition on the component.",
                            ordinal=1, section_path=["notes"]),
    ]
    unit = DocumentUnit(unit_id="u1", label="My mixture notes", ordinal=0, semantic_hash="sha256:notes",
                        span_ids=["n0", "n1"])
    ir = DocumentIR(extractor="markdown", extractor_version="1", units=[unit], blocks=blocks,
                    assets=[], health=ExtractionHealth())
    _persist(repo, ir, revision_id="rev_notes", extraction_id=extraction_id)
    return {"source_id": "src_notes", "extraction_id": extraction_id, "span_id": "n1"}
