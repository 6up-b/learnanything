from types import SimpleNamespace

from learnloop.db.repositories import Repository
from learnloop.ingest.source_library import register_source_revision
from learnloop.services.source_refs import (
    source_ref_display_dto,
    source_ref_presentation,
)
from learnloop.vault.models import SourceRef


def _vault():
    return SimpleNamespace(notes={})


def test_file_source_ref_uses_original_imported_filename(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    registered = register_source_revision(
        repository,
        acquisition_kind="pdf",
        canonical_uri="file:///library/opaque-location",
        original_uri="file:///home/learner/Linear%20Algebra%20Problems.pdf",
        raw_bytes=b"%PDF-source",
        display_title="PDF metadata title",
    )
    ref = SourceRef(
        ref_type="canonical_source",
        ref_id=registered.source_id,
        revision_id=registered.revision_id,
    )

    presentation = source_ref_presentation(_vault(), repository, ref)

    assert presentation.display_name == "Linear Algebra Problems.pdf"
    assert (
        source_ref_display_dto(_vault(), repository, ref)["ref_id"]
        == registered.source_id
    )


def test_youtube_source_ref_uses_title_captured_during_ingest(tmp_path):
    repository = Repository(tmp_path / "state.sqlite")
    registered = register_source_revision(
        repository,
        acquisition_kind="youtube",
        canonical_uri="https://www.youtube.com/watch?v=abc123",
        original_uri="https://www.youtube.com/watch?v=abc123",
        raw_bytes=b"captions",
        display_title="Eigenvectors, Clearly Explained — Math Channel",
    )
    ref = SourceRef(ref_type="canonical_source", ref_id=registered.source_id)

    presentation = source_ref_presentation(_vault(), repository, ref)

    assert presentation.display_name == "Eigenvectors, Clearly Explained — Math Channel"
    assert presentation.kind == "youtube_video"
