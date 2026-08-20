from __future__ import annotations

from tests.structured_ai import StructuredClientFake

import json
import sys
import types

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
from learnloop.config import PdfIngestConfig
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.sources.pdf_extraction import PdfExtractionError, extract_pdf_markdown
from learnloop.content.pipeline.source_ingestion import (
    FetchResult,
    SourceIngestionError,
    chunk_normalized_source,
    detect_source_kind,
    fetch_source,
    ingest_canonical_source,
    normalize_source,
    resolve_canonical_source,
    _fetch_youtube_transcript,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


def test_source_kind_detection_handles_special_cases(tmp_path):
    html = tmp_path / "chapter.html"
    html.write_text("<html><body>Chapter</body></html>", encoding="utf-8")

    assert detect_source_kind("https://youtu.be/abc123") == "youtube_video"
    assert detect_source_kind("https://www.youtube.com/watch?v=abc123") == "youtube_video"
    assert detect_source_kind("https://arxiv.org/abs/2401.12345") == "arxiv_html"
    assert detect_source_kind("https://example.edu/page") == "website_page"
    assert detect_source_kind(str(html), learning_object_ids=["lo_svd_definition"]) == "textbook_chapter"
    # A text-based PDF is ingested like a web page (normalized to Markdown).
    assert detect_source_kind(str(tmp_path / "paper.pdf")) == "website_page"

    markdown = tmp_path / "notes.md"
    markdown.write_text("# Notes\n\nA sufficiently useful local source.", encoding="utf-8")
    assert detect_source_kind(str(markdown)) == "website_page"
    assert detect_source_kind(str(tmp_path / "notes.txt")) == "website_page"
    assert detect_source_kind("2401.12345") == "arxiv_html"
    assert detect_source_kind("arxiv:2401.12345v2") == "arxiv_html"

    resolved, kind = resolve_canonical_source("arxiv:2401.12345v2")
    assert kind == "arxiv_html"
    assert resolved.source == "https://arxiv.org/abs/2401.12345v2"


def _make_pdf_bytes(lines: list[str]) -> bytes:
    """Build a minimal single-page PDF whose text layer holds ``lines``."""

    text = ""
    y = 700
    for line in lines:
        text += f"BT /F1 12 Tf 72 {y} Td ({line}) Tj ET\n"
        y -= 20
    stream = text.encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets: list[int] = []
    for index, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % index + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref_pos)
    return out


def test_pdf_source_is_normalized_to_markdown(tmp_path):
    pdf_path = tmp_path / "glossary.pdf"
    pdf_path.write_bytes(
        _make_pdf_bytes(
            [
                "1. A: Which nerve tension test is positive for hand pain overhead?",
                "A. Ulnar B. Median C. Radial D. Musculocutaneous",
            ]
        )
    )

    assert detect_source_kind(str(pdf_path)) == "website_page"
    # Pin pypdf so unit tests stay hermetic when marker (real model inference)
    # is installed in the environment.
    fetched = fetch_source(
        tmp_path,
        str(pdf_path),
        kind="website_page",
        allow_auto_captions=False,
        pdf_config=PdfIngestConfig(engine="pypdf"),
    )
    assert fetched.original_uri.endswith("glossary.pdf")
    assert fetched.source_bytes == pdf_path.read_bytes()

    normalized = normalize_source(fetched, "website_page")
    assert "Ulnar" in normalized.markdown
    assert "nerve tension test" in normalized.markdown

    chunks = chunk_normalized_source(normalized)
    assert any(chunk.chunk_kind == "prose" and chunk.text.strip() for chunk in chunks)


def test_pdf_without_text_layer_raises(tmp_path):
    with pytest.raises(PdfExtractionError):
        extract_pdf_markdown(b"%PDF-1.4 not-really-a-pdf")

    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not-really-a-pdf")
    with pytest.raises(SourceIngestionError):
        fetch_source(
            tmp_path,
            str(broken),
            kind="website_page",
            allow_auto_captions=False,
            pdf_config=PdfIngestConfig(engine="pypdf"),
        )


def test_arxiv_html_normalizer_captures_descriptor_fields():
    html = b"""
    <html>
      <head>
        <title>Attention Is All You Need</title>
        <meta name="citation_author" content="A. Researcher" />
      </head>
      <body>
        <h1>Abstract</h1>
        <p>Transformers replace recurrence with attention.</p>
        <h1>Results</h1>
        <p id="thm-main">Theorem 2.1. Every attention layer is differentiable.</p>
      </body>
    </html>
    """

    source = normalize_source(
        FetchResult(
            raw_bytes=html,
            content_type="text/html",
            original_uri="https://arxiv.org/html/1706.03762v7",
            fetch_uri="https://arxiv.org/html/1706.03762v7",
            retrieved_at="2026-05-19T12:00:00Z",
        ),
        "arxiv_html",
    )

    assert source.title == "Attention Is All You Need"
    assert source.authors == ["A. Researcher"]
    assert source.canonical_uri == "https://arxiv.org/html/1706.03762v7"
    assert source.labels["arxiv_id"] == "1706.03762v7"
    assert source.labels["version"] == 7
    chunks = chunk_normalized_source(source)
    assert chunks[0].locator == "abstract/p1"
    assert any(chunk.locator == "thm:2.1" and chunk.label == "thm:2.1" for chunk in chunks)


def test_youtube_normalizer_uses_timestamp_locators():
    raw = json.dumps(
        {
            "video_id": "abc123",
            "cues": [
                {"start": 90.0, "duration": 35.0, "text": "Define singular value decomposition."},
                {"start": 125.0, "duration": 20.0, "text": "It factors a matrix."},
            ],
        }
    ).encode("utf-8")

    source = normalize_source(
        FetchResult(
            raw_bytes=raw,
            content_type="application/json",
            original_uri="https://www.youtube.com/watch?v=abc123",
            retrieved_at="2026-05-19T12:00:00Z",
        ),
        "youtube_video",
    )
    chunks = chunk_normalized_source(source)

    assert source.canonical_uri == "https://www.youtube.com/watch?v=abc123"
    assert [chunk.locator for chunk in chunks] == ["t=90.0-125.0", "t=125.0-145.0"]
    assert all(chunk.chunk_kind == "caption" for chunk in chunks)


def test_youtube_fetcher_supports_current_transcript_api(monkeypatch):
    calls: list[str] = []

    class NoTranscriptFound(Exception):
        pass

    class TranscriptsDisabled(Exception):
        pass

    class FetchedTranscript:
        def to_raw_data(self):
            return [{"start": 10.0, "duration": 5.0, "text": "SVD has singular values."}]

    class Transcript:
        def fetch(self):
            return FetchedTranscript()

    class TranscriptList:
        def find_manually_created_transcript(self, languages):
            assert languages == ["en"]
            return Transcript()

    class YouTubeTranscriptApi:
        def list(self, video_id):
            calls.append(video_id)
            return TranscriptList()

    module = types.ModuleType("youtube_transcript_api")
    module.YouTubeTranscriptApi = YouTubeTranscriptApi
    errors_module = types.ModuleType("youtube_transcript_api._errors")
    errors_module.NoTranscriptFound = NoTranscriptFound
    errors_module.TranscriptsDisabled = TranscriptsDisabled
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", module)
    monkeypatch.setitem(sys.modules, "youtube_transcript_api._errors", errors_module)

    result = _fetch_youtube_transcript(
        "https://www.youtube.com/watch?v=abc123",
        allow_auto_captions=False,
        clock=FrozenClock(NOW),
    )
    payload = json.loads(result.raw_bytes.decode("utf-8"))

    assert calls == ["abc123"]
    assert payload["cues"] == [{"duration": 5.0, "start": 10.0, "text": "SVD has singular values."}]


def test_textbook_ingest_requires_existing_anchor_and_passes_constraints(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    chapter = tmp_path / "chapter.html"
    chapter.write_text(
        """
        <html>
          <head><title>SVD chapter</title></head>
          <body>
            <h1>Worked examples</h1>
            <p>Singular value decomposition practice problem text. """ + ("This is useful. " * 40) + """</p>
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    client = _TextbookClient()

    result = ingest_canonical_source(
        vault_root,
        str(chapter),
        client,
        kind="auto",
        subject_id="linear-algebra",
        learning_object_ids=["lo_svd_definition"],
        clock=FrozenClock(NOW),
    )

    assert result.source_kind == "textbook_chapter"
    assert client.calls[0].source_kind == "textbook_chapter"
    assert client.calls[0].target_learning_object_ids == ["lo_svd_definition"]
    assert client.calls[0].extraction_plan.learning_object_required is False
    loaded = load_vault(vault_root)
    assert "pi_textbook_svd_001" in loaded.practice_items


class _TextbookClient(StructuredClientFake):
    def __init__(self):
        self.calls: list[CanonicalIngestContext] = []

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        self.calls.append(context)
        source_ref_id = context.canonical_source["id"]
        return AuthoringProposal.model_validate(
            {
                "summary": "Textbook practice extraction.",
                "source_refs": [
                    {
                        "ref_type": "canonical_source",
                        "ref_id": source_ref_id,
                        "path": context.canonical_source["path"],
                        "locator": context.chunks[0].locator,
                    }
                ],
                "items": [
                    {
                        "client_item_id": "pi_textbook_svd",
                        "item_type": "practice_item",
                        "operation": "create",
                        "proposed_entity_id": "pi_textbook_svd_001",
                        "source_ref_ids": [source_ref_id],
                        "rationale": "Extract a textbook practice problem for an existing LO.",
                        "review_route": "auto_apply",
                        "payload": {
                            "learning_object_id": "lo_svd_definition",
                            "subjects": None,
                            "practice_mode": "short_answer",
                            "attempt_types_allowed": ["independent_attempt"],
                            "prompt": "State the key factors in an SVD.",
                            "expected_answer": "Orthogonal factors and singular values.",
                            "evidence_facets": ["recall"],
                            "evidence_weights": {"recall": 1.0},
                            "grading_rubric": {
                                "max_points": 4,
                                "criteria": [{"id": "correctness", "points": 4, "description": "Names the factors."}],
                                "fatal_errors": [],
                            },
                        },
                    }
                ],
            }
        )

    def run_authoring_proposal(self, context):  # pragma: no cover - unused
        raise NotImplementedError

    def run_grading_proposal(self, context):  # pragma: no cover - unused
        raise NotImplementedError
