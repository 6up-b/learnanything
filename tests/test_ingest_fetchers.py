from __future__ import annotations

import pytest

from learnloop.ingest import fetchers
from learnloop.ingest.fetchers import (
    _compose_arxiv_markdown,
    _parse_arxiv_atom,
    arxiv_id_from_source,
    clean_markdown,
    fetch_source,
    fetch_textfile,
    first_heading,
    transcript_to_markdown,
    youtube_video_id,
)
from learnloop.ingest.models import IngestDependencyMissing, SourceFetchError, UnsupportedSourceError


def test_clean_markdown_collapses_blank_runs_and_trailing_space():
    raw = "# Title  \n\n\n\nBody line\t\n\n\n\nNext"
    assert clean_markdown(raw) == "# Title\n\nBody line\n\nNext"


def test_first_heading():
    assert first_heading("# Singular Value Decomposition\n\nText") == "Singular Value Decomposition"
    assert first_heading("Just prose, no heading") is None


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("2310.12345", "2310.12345"),
        ("arXiv:2310.12345v2", "2310.12345v2"),
        ("https://arxiv.org/abs/2310.12345", "2310.12345"),
        ("https://arxiv.org/pdf/2310.12345v3", "2310.12345v3"),
        ("https://arxiv.org/pdf/2310.12345.pdf", "2310.12345"),
        ("https://ar5iv.labs.arxiv.org/html/2310.12345", "2310.12345"),
        ("math.GT/0309136", "math.GT/0309136"),
    ],
)
def test_arxiv_id_from_source(source, expected):
    assert arxiv_id_from_source(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
    ],
)
def test_youtube_video_id(source):
    assert youtube_video_id(source) == "dQw4w9WgXcQ"


def test_youtube_video_id_rejects_bad_url():
    with pytest.raises(UnsupportedSourceError):
        youtube_video_id("https://www.youtube.com/feed/subscriptions")


def test_transcript_to_markdown_joins_and_normalizes():
    segments = [
        {"text": "Hello and", "start": 0.0, "duration": 1.0},
        {"text": "welcome\nback", "start": 1.0, "duration": 1.0},
        {"text": "   ", "start": 2.0, "duration": 1.0},
        {"text": "to the lecture.", "start": 3.0, "duration": 1.0},
    ]
    assert transcript_to_markdown(segments) == "Hello and welcome back to the lecture."


def test_parse_arxiv_atom_and_compose():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>A Study of\n      Matrix Factorization</title>
        <summary>We factorize matrices into orthogonal factors.</summary>
        <author><name>Ada Lovelace</name></author>
        <author><name>Alan Turing</name></author>
      </entry>
    </feed>"""
    meta = _parse_arxiv_atom(xml)
    assert meta["title"] == "A Study of Matrix Factorization"
    assert meta["authors"] == ("Ada Lovelace", "Alan Turing")
    assert "orthogonal factors" in meta["abstract"]

    body = _compose_arxiv_markdown(meta, fulltext="## Section 1\n\nDetails.")
    assert body.startswith("## Abstract")
    assert "## Section 1" in body


def test_fetch_textfile_uses_heading_as_title(tmp_path):
    path = tmp_path / "svd.md"
    path.write_text("# SVD Overview\n\nSVD factorizes a matrix.\n", encoding="utf-8")
    fetched = fetch_textfile(str(path))
    assert fetched.kind == "textfile"
    assert fetched.title == "SVD Overview"
    assert "factorizes" in fetched.text_md
    assert fetched.locator == str(path.resolve())


def test_fetch_textfile_missing_file_raises(tmp_path):
    with pytest.raises(SourceFetchError):
        fetch_textfile(str(tmp_path / "nope.md"))


def test_fetch_source_dispatches_to_textfile(tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text("plain text body", encoding="utf-8")
    fetched = fetch_source(str(path))
    assert fetched.kind == "textfile"
    assert fetched.text_md == "plain text body"


@pytest.mark.parametrize(
    ("fetcher", "arg", "package"),
    [
        (fetchers.fetch_web, "https://example.com", "trafilatura"),
        (fetchers.fetch_pdf, "https://example.com/x.pdf", "pypdf"),
        (fetchers.fetch_youtube, "https://youtu.be/dQw4w9WgXcQ", "youtube-transcript-api"),
    ],
)
def test_optional_dependency_missing_is_actionable(monkeypatch, fetcher, arg, package):
    def _raise(name):
        raise ImportError(name)

    monkeypatch.setattr(fetchers, "_import_optional", _raise)
    with pytest.raises(IngestDependencyMissing) as excinfo:
        fetcher(arg)
    assert package in str(excinfo.value)
    assert "pip install learnloop[ingest]" in str(excinfo.value)


def test_legacy_fetch_source_rejects_audio(tmp_path):
    from learnloop.ingest.fetchers import fetch_source
    from learnloop.ingest.models import UnsupportedSourceError

    with pytest.raises(UnsupportedSourceError, match="durable import pipeline"):
        fetch_source(str(tmp_path / "lecture.mp3"))
