from __future__ import annotations

import importlib
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from learnloop.ingest.resolution import resolve_source
from learnloop.ingest.models import (
    FetchedSource,
    IngestDependencyMissing,
    SourceFetchError,
    UnsupportedSourceError,
)

SUPPORTED_KINDS = ("web", "arxiv", "pdf", "youtube", "textfile")

_USER_AGENT = "learnloop-ingest/0.1 (+https://github.com/learnloop)"
_HTTP_TIMEOUT = 30


# --------------------------------------------------------------------------- #
# Pure transforms (no network, no optional dependencies — always unit-tested).
# --------------------------------------------------------------------------- #

def _collapse_ws(text: str) -> str:
    return " ".join(text.split())


def clean_markdown(text: str) -> str:
    """Normalize extracted text: strip trailing spaces and collapse blank runs."""

    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    out: list[str] = []
    blanks = 0
    for line in lines:
        if line:
            blanks = 0
            out.append(line)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out).strip()


def first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
        if stripped:
            return None
    return None


def arxiv_id_from_source(source: str) -> str:
    """Extract a canonical arXiv id (keeping any version suffix) from a URL or id."""

    candidate = source.strip()
    if candidate.lower().startswith(("http://", "https://")):
        path = urlparse(candidate).path
        # Strip a leading /abs/, /pdf/, or ar5iv /html/ segment.
        match = re.search(r"/(?:abs|pdf|html)/(.+)$", path)
        token = match.group(1) if match else path.rsplit("/", 1)[-1]
    else:
        token = candidate
    token = re.sub(r"^arxiv:", "", token, flags=re.IGNORECASE)
    if token.lower().endswith(".pdf"):
        token = token[:-4]
    token = token.strip("/")
    if not token:
        raise UnsupportedSourceError(f"Could not extract an arXiv id from {source!r}")
    return token


def youtube_video_id(source: str) -> str:
    """Extract the 11-character video id from any common YouTube URL form."""

    candidate = source.strip()
    parsed = urlparse(candidate)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"youtu.be", "www.youtu.be"}:
        video = parsed.path.lstrip("/").split("/", 1)[0]
        if video:
            return video
    if "v" in parse_qs(parsed.query):
        return parse_qs(parsed.query)["v"][0]
    match = re.search(r"/(?:embed|shorts|live|v)/([^/?#]+)", parsed.path)
    if match:
        return match.group(1)
    raise UnsupportedSourceError(f"Could not extract a YouTube video id from {source!r}")


def transcript_to_markdown(segments: list[dict]) -> str:
    """Join caption segments into clean prose, dropping per-segment timing."""

    texts = []
    for segment in segments:
        value = segment.get("text", "") if isinstance(segment, dict) else getattr(segment, "text", "")
        value = (value or "").replace("\n", " ").strip()
        if value:
            texts.append(value)
    return _collapse_ws(" ".join(texts))


def _parse_arxiv_atom(xml_text: str) -> dict:
    import xml.etree.ElementTree as ET

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {"title": None, "authors": (), "abstract": None}
    title_el = entry.find("atom:title", ns)
    summary_el = entry.find("atom:summary", ns)
    authors = tuple(
        _collapse_ws(name.text or "")
        for author in entry.findall("atom:author", ns)
        for name in [author.find("atom:name", ns)]
        if name is not None and name.text
    )
    return {
        "title": _collapse_ws(title_el.text) if title_el is not None and title_el.text else None,
        "authors": authors,
        "abstract": _collapse_ws(summary_el.text) if summary_el is not None and summary_el.text else None,
    }


def _compose_arxiv_markdown(meta: dict, fulltext: str | None) -> str:
    parts: list[str] = []
    if meta.get("abstract"):
        parts.append("## Abstract\n\n" + meta["abstract"])
    if fulltext:
        parts.append(fulltext)
    return clean_markdown("\n\n".join(parts))


# --------------------------------------------------------------------------- #
# I/O helpers and import-guarded fetchers.
# --------------------------------------------------------------------------- #

def _import_optional(name: str):
    """Import an optional dependency. Indirection point so tests can simulate absence."""

    return importlib.import_module(name)


def _http_get_text(url: str, *, timeout: int = _HTTP_TIMEOUT) -> str:
    return _http_get_bytes(url, timeout=timeout).decode("utf-8", errors="replace")


def _http_get_bytes(url: str, *, timeout: int = _HTTP_TIMEOUT) -> bytes:
    import urllib.request

    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (trusted scheme checked upstream)
            return response.read()
    except OSError as exc:
        raise SourceFetchError(f"Failed to fetch {url}: {exc}") from exc


def fetch_textfile(source: str) -> FetchedSource:
    path = Path(source).expanduser()
    if not path.is_file():
        raise SourceFetchError(f"No such file: {source}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceFetchError(f"Failed to read {source}: {exc}") from exc
    body = clean_markdown(text)
    title = first_heading(body) or path.stem.replace("_", " ").replace("-", " ").strip() or path.name
    return FetchedSource(
        kind="textfile",
        title=title,
        text_md=body,
        canonical_url=None,
        locator=str(path.resolve()),
        authors=(),
        extra={"bytes": len(text)},
    )


def fetch_web(source: str) -> FetchedSource:
    try:
        trafilatura = _import_optional("trafilatura")
    except ImportError as exc:
        raise IngestDependencyMissing("web", "trafilatura") from exc

    downloaded = trafilatura.fetch_url(source)
    if not downloaded:
        raise SourceFetchError(f"Could not download {source}")
    extracted = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
    )
    if not extracted:
        raise SourceFetchError(f"Could not extract readable content from {source}")
    title = None
    try:
        meta = trafilatura.extract_metadata(downloaded)
        title = getattr(meta, "title", None) if meta else None
    except Exception:  # pragma: no cover - metadata extraction is best-effort
        title = None
    body = clean_markdown(extracted)
    return FetchedSource(
        kind="web",
        title=title or first_heading(body) or urlparse(source).netloc or source,
        text_md=body,
        canonical_url=source,
        locator=source,
        authors=(),
        extra={},
    )


def fetch_arxiv(source: str) -> FetchedSource:
    arxiv_id = arxiv_id_from_source(source)
    base_id = arxiv_id.split("v")[0] if re.match(r"^\d", arxiv_id) else arxiv_id
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        meta = _parse_arxiv_atom(_http_get_text(api_url))
    except SourceFetchError:
        raise
    except Exception as exc:  # malformed Atom, etc.
        raise SourceFetchError(f"Failed to read arXiv metadata for {arxiv_id}: {exc}") from exc

    fulltext = None
    fulltext_available = False
    try:
        trafilatura = _import_optional("trafilatura")
    except ImportError:
        trafilatura = None
    if trafilatura is not None:
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
        downloaded = trafilatura.fetch_url(ar5iv_url)
        if downloaded:
            fulltext = trafilatura.extract(downloaded, output_format="markdown", include_tables=True)
            fulltext_available = bool(fulltext)

    body = _compose_arxiv_markdown(meta, fulltext)
    if not body:
        raise SourceFetchError(f"arXiv {arxiv_id} returned no abstract or full text")
    return FetchedSource(
        kind="arxiv",
        title=meta.get("title") or f"arXiv:{arxiv_id}",
        text_md=body,
        canonical_url=f"https://arxiv.org/abs/{base_id}",
        locator=arxiv_id,
        authors=meta.get("authors") or (),
        extra={"arxiv_id": arxiv_id, "fulltext_available": fulltext_available},
    )


def fetch_pdf(source: str) -> FetchedSource:
    try:
        pypdf = _import_optional("pypdf")
    except ImportError as exc:
        raise IngestDependencyMissing("pdf", "pypdf") from exc

    import io

    is_url = source.lower().startswith(("http://", "https://"))
    if is_url:
        stream = io.BytesIO(_http_get_bytes(source))
        display_name = urlparse(source).path.rsplit("/", 1)[-1] or source
    else:
        path = Path(source).expanduser()
        if not path.is_file():
            raise SourceFetchError(f"No such file: {source}")
        stream = path.open("rb")
        display_name = path.name

    try:
        reader = pypdf.PdfReader(stream)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())
        meta_title = None
        try:
            meta_title = getattr(reader.metadata, "title", None) if reader.metadata else None
        except Exception:  # pragma: no cover - some PDFs have unreadable metadata
            meta_title = None
    except Exception as exc:
        raise SourceFetchError(f"Failed to read PDF {source}: {exc}") from exc
    finally:
        if not is_url:
            stream.close()

    body = clean_markdown("\n\n".join(pages))
    if not body:
        raise SourceFetchError(f"PDF {source} contained no extractable text (likely scanned images)")
    stem = display_name[:-4] if display_name.lower().endswith(".pdf") else display_name
    return FetchedSource(
        kind="pdf",
        title=(meta_title or "").strip() or stem.replace("_", " ").replace("-", " ").strip() or display_name,
        text_md=body,
        canonical_url=source if is_url else None,
        locator=source if is_url else str(Path(source).expanduser().resolve()),
        authors=(),
        extra={"pages": len(pages)},
    )


def compose_youtube_title(
    video_title: str | None, author: str | None, video_id: str
) -> str:
    """Assemble the display label for a YouTube source.

    "<title> — <author>" when both are known; the title alone when the author is
    missing; and the ``youtube · <id>``-shaped last-resort fallback (as a bare
    ``YouTube video <id>``) only when no metadata is available at all.
    """

    title = (video_title or "").strip()
    who = (author or "").strip()
    if title and who:
        return f"{title} — {who}"
    if title:
        return title
    return f"YouTube video {video_id}"


def youtube_oembed_metadata(video_id: str) -> tuple[str | None, str | None]:
    """Best-effort (title, author) from YouTube's public oEmbed endpoint.

    No API key: ``https://www.youtube.com/oembed`` returns the video title and
    the uploading channel as ``author_name``. Any failure (offline, private
    video, malformed JSON) returns ``(None, None)`` so callers degrade to a URL
    title rather than failing the import.
    """

    url = (
        "https://www.youtube.com/oembed?format=json&url="
        f"https://www.youtube.com/watch?v={video_id}"
    )
    try:
        import json

        data = json.loads(_http_get_text(url, timeout=10))
        title = (data.get("title") or "").strip() or None
        author = (data.get("author_name") or "").strip() or None
        return title, author
    except Exception:  # pragma: no cover - metadata is best-effort
        return None, None


def fetch_youtube(source: str) -> FetchedSource:
    try:
        module = _import_optional("youtube_transcript_api")
    except ImportError as exc:
        raise IngestDependencyMissing("youtube", "youtube-transcript-api") from exc

    video_id = youtube_video_id(source)
    try:
        api = module.YouTubeTranscriptApi
        segments = api.get_transcript(video_id)
    except Exception as exc:
        raise SourceFetchError(f"Could not fetch a transcript for YouTube video {video_id}: {exc}") from exc

    body = transcript_to_markdown(list(segments))
    if not body:
        raise SourceFetchError(f"YouTube video {video_id} returned an empty transcript")
    video_title, author = youtube_oembed_metadata(video_id)
    title = compose_youtube_title(video_title, author, video_id)
    return FetchedSource(
        kind="youtube",
        title=title,
        text_md=body,
        canonical_url=f"https://www.youtube.com/watch?v={video_id}",
        locator=video_id,
        authors=(author,) if author else (),
        extra={"video_id": video_id, "video_title": video_title},
    )


_FETCHERS = {
    "web": fetch_web,
    "arxiv": fetch_arxiv,
    "pdf": fetch_pdf,
    "youtube": fetch_youtube,
    "textfile": fetch_textfile,
}


def fetch_source(source: str) -> FetchedSource:
    """Detect the source kind and fetch it. Raises an :class:`IngestError` subclass on failure."""

    resolved = resolve_source(source)
    if resolved.category == "audio":
        raise UnsupportedSourceError(
            "Audio sources are only supported by the durable import pipeline "
            "(canonical mode); the legacy fetch path cannot transcribe audio."
        )
    return _FETCHERS[resolved.category](resolved.source)
