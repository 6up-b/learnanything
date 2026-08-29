"""Concrete ingest jobs and the durable host shared by CLI and sidecar (§6.2).

Acquisition/provider defaults and domain handlers live here, separate from the
leased queue state machine in :mod:`learnloop.content.pipeline.runner`. The
durable host replaced the old in-memory/subprocess job manager. Its sidecar-facing
API (``start``/``get``/``list``/
``cancel``/``needs_reload``/``mark_reloaded``/``shutdown``) is unchanged, but the
job now lives in the durable queue (``ingest_batches``/``ingest_jobs``): a single
``legacy_ingest`` batch that survives restarts. A background drain thread hosts
the runner while the app is open; on next open, ``IngestRunner.recover_stale_leases``
resumes anything left unfinished.

Determinism: ``bind(..., background=False)`` disables the thread so tests drain
synchronously via ``drain_foreground()`` with stubbed :class:`RunnerServices`.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import queue
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.ai.transport import INTERRUPT, interrupt_callback
from learnloop.db.repositories import Repository
from learnloop.goals.exam_seeding import exam_ingest_instructions
from learnloop.ids import new_ulid
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader import reader_requests as RR
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.promotions import (
    PromotionError,
    PromotionNoItemError,
    promote_tutor_question,
)
from learnloop.content.pipeline.runner import (
    CHECKPOINT_LADDER,
    FetchedBytes,
    Handler,
    IngestRunner,
    IngestRunnerError,
    JobCancelled,
    JobContext,
    JobSpec,
    RunnerServices,
    WaitingForInput,
    derive_batch_status,
    effective_ingest_job_status,
)

# Handler execution defaults remain here with the concrete jobs they govern.
_MAX_INVENTORY_WORKERS = 2
INGEST_CODEX_TIMEOUT_SECONDS = 8 * 60

_LEGACY_PHASE_TO_LADDER = {
    "preparing": "acquired",
    "fetching": "acquired",
    "extracting": "extracted",
    "staging": "proposed",
    "authoring": "proposed",
}

_LEGACY_PHASE_MESSAGE = {
    "preparing": "Checking the authoring provider",
    "fetching": "Fetching source material",
    "extracting": "Extracting clean structure",
    "staging": "Staging the canonical-source note",
    "authoring": "Generating the authoring proposal",
}


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


# ---------------------------------------------------------------------------
# Injectable side effects — real defaults, stubbed in tests.
# ---------------------------------------------------------------------------


def default_fetch(source: str, category: str, ctx: JobContext) -> FetchedBytes:
    """Read raw bytes for one acquisition. Local files are read directly; URLs
    reuse the source-ingestion fetcher so import stays honest for the web path."""

    path = Path(source).expanduser()
    if path.exists() and path.is_file():
        return FetchedBytes(
            raw_bytes=path.read_bytes(),
            content_type=None,
            original_uri=path.resolve().as_uri(),
            retrieved_at=utc_now_iso(ctx.clock),
        )
    from learnloop.content.pipeline import source_ingestion

    kind = "youtube_video" if category == "youtube" else "website_page"
    fetched = source_ingestion.fetch_source(
        ctx.vault_root,
        source,
        kind=kind,
        allow_auto_captions=True,
        clock=ctx.clock,
    )
    title, authors = _fetch_metadata(source, category)
    return FetchedBytes(
        raw_bytes=fetched.source_bytes or fetched.raw_bytes,
        content_type=fetched.content_type,
        original_uri=fetched.original_uri,
        retrieved_at=fetched.retrieved_at,
        title=title,
        authors=authors,
    )


def _fetch_metadata(source: str, category: str) -> tuple[str | None, tuple[str, ...]]:
    """Best-effort human-readable (title, authors) for the fetched source.

    Only YouTube is resolvable cheaply today: its public oEmbed endpoint returns
    the video title + channel with no API key. This runs in the import's fetch
    phase — the same phase that already made a network request for the transcript,
    so it adds one small extra egress (oEmbed) and never a new phase. Any failure
    degrades to ``(None, ())`` so the import proceeds with a URL title."""

    if category != "youtube":
        return None, ()
    try:
        from learnloop.ingest.fetchers import youtube_oembed_metadata, youtube_video_id

        video_title, author = youtube_oembed_metadata(youtube_video_id(source))
    except Exception:  # pragma: no cover - metadata is strictly best-effort
        return None, ()
    return video_title, (author,) if author else ()


def _pdf_payload_config(ctx: JobContext) -> dict[str, Any]:
    """The effective PDF extraction config for one import job.

    The job payload's ``pdf_config`` wins key-by-key (a per-ingest engine choice
    or a repair's page/OCR options); the vault's ``[ingest.pdf]`` engine fills in
    when the payload doesn't pin one, so a configured ``engine = "pypdf"`` (or
    "marker") finally governs the durable import path too."""

    config = dict(ctx.payload.get("pdf_config") or {})
    if not config.get("engine"):
        from learnloop.vault.loader import load_vault

        try:
            engine = load_vault(ctx.vault_root).config.ingest.pdf.engine
        except FileNotFoundError:
            engine = "auto"
        # "auto" stays implicit: writing it into the config would change every
        # extraction request hash and needlessly re-extract unchanged sources.
        if engine != "auto":
            config["engine"] = engine
    return config


def default_extract(fetched: FetchedBytes, category: str, ctx: JobContext) -> Any:
    """Produce Document IR from fetched bytes using the M1 extractor providers.

    PDFs go through the engine the payload/vault config selects (marker, the
    pypdf fallback, or auto); audio is transcribed via the [ingest.audio]
    endpoint; everything else gets honest trivial IR from its decoded text
    (§2.3)."""

    from learnloop.ingest.extractors import MarkerUnavailableError, markdown_to_ir, pdf_extractor_for
    from learnloop.ingest.extractors.base import ExtractionContext

    if category == "audio":
        return _extract_audio(fetched, ctx)

    is_pdf = (
        category == "pdf"
        or (fetched.content_type or "").lower().startswith("application/pdf")
        or fetched.raw_bytes[:5] == b"%PDF-"
    )
    if is_pdf:
        pdf_config = _pdf_payload_config(ctx)
        if pdf_config.get("engine") == "native":
            return _extract_pdf_native(fetched, ctx)
        try:
            extractor = pdf_extractor_for(pdf_config)
        except MarkerUnavailableError as exc:
            raise IngestRunnerError(
                str(exc), code="pdf_extractor_unavailable", retryable=True
            ) from exc
        pages = _normalize_pages(ctx.payload.get("page_selection") or pdf_config.get("page_range")) or None
        context = ExtractionContext(
            revision_id=str(ctx.job.get("_revision_id") or "rev"),
            page_selection=tuple(pages) if pages is not None else None,
        )
        try:
            return extractor.extract(fetched.raw_bytes, context)
        except Exception as marker_exc:  # noqa: BLE001 — degrade explicitly (§2.9)
            # Marker can fail at runtime (model load, GPU state, malformed PDF
            # object streams) long after the availability check passed. Unless
            # marker was explicitly forced, degrade to native-text extraction
            # with a health flag instead of failing the whole import.
            if extractor.name != "marker" or pdf_config.get("engine") == "marker":
                raise
            from learnloop.ingest.extractors import PyPdfDocumentExtractor

            try:
                ir = PyPdfDocumentExtractor().extract(fetched.raw_bytes, context)
            except Exception as pypdf_exc:
                raise IngestRunnerError(
                    "PDF extraction failed: marker: "
                    f"{marker_exc}; pypdf fallback: {pypdf_exc}",
                    code="pdf_extraction_failed",
                    retryable=True,
                ) from pypdf_exc
            if "marker_failed_pypdf_fallback" not in ir.health.flags:
                ir.health.flags.append("marker_failed_pypdf_fallback")
            return ir

    text = fetched.raw_bytes.decode("utf-8", errors="replace")

    if category == "youtube":
        from learnloop.ingest.extractors import captions_to_ir

        cues = _caption_cues(text)
        if cues is not None:
            return captions_to_ir(cues, title=ctx.payload.get("title"))

    looks_like_html = (fetched.content_type or "").lower().startswith("text/html") or bool(
        re.match(r"\s*(?:<!doctype\s+html|<html)", text, re.IGNORECASE)
    )
    if category in ("web", "arxiv") or looks_like_html:
        markdown = _html_to_markdown(text)
        if markdown:
            return markdown_to_ir(markdown, title=ctx.payload.get("title"), extractor_name="html")

    # Transcript-aware path: a standalone caption file (WebVTT/SRT) keeps its
    # cue timing + speaker turns instead of flattening to prose paragraphs.
    from learnloop.ingest.transcripts import detect_transcript_format, parse_transcript

    fmt = detect_transcript_format(text[:4096])
    if fmt is not None:
        from learnloop.ingest.extractors import transcript_to_ir

        parsed = parse_transcript(text, fmt=fmt)
        if parsed:
            return transcript_to_ir(parsed, title=ctx.payload.get("title"))

    return markdown_to_ir(text, title=ctx.payload.get("title"), extractor_name="text")


def default_extraction_identity(
    fetched: FetchedBytes, category: str, ctx: JobContext
) -> Mapping[str, Any]:
    """Describe the chosen extractor before running it, making cache hits cheap."""

    from learnloop.ingest.extractors import MarkerUnavailableError, pdf_extractor_for

    if category == "audio":
        # Lock-step with _extract_audio: the same pure route decision picks
        # native vs routed-chat vs endpoint transcription, and the identity
        # carries the model + provider/endpoint so re-pointing either forces a
        # fresh transcription. Keys named api_key* are stripped by
        # hashing._sanitized_config.
        from learnloop.ai.multimodal import chat_audio_format

        route = _native_media_route(ctx, "audio")
        if route is not None and chat_audio_format(_audio_filename(fetched)) is not None:
            return {
                "extractor": "audio_native",
                "extractor_version": "1",
                "model_versions": {"chat_model": route.model or ""},
                "config": {"provider": route.provider_name},
            }
        audio_config = _audio_ingest_config(ctx)
        route = _transcription_media_route(ctx)
        if route is not None:
            if chat_audio_format(_audio_filename(fetched)) is None:
                raise IngestRunnerError(
                    _ROUTED_AUDIO_FORMAT_MESSAGE,
                    code="audio_format_unsupported",
                    retryable=True,
                )
            return {
                "extractor": "audio_native",
                "extractor_version": "1",
                "model_versions": {"chat_model": route.model or ""},
                "config": {"provider": route.provider_name},
            }
        return {
            "extractor": "audio_transcript",
            "extractor_version": "1",
            "model_versions": {"transcription_model": audio_config.transcription_model},
            "config": {"base_url": audio_config.transcription_base_url},
        }

    is_pdf = (
        category == "pdf"
        or (fetched.content_type or "").lower().startswith("application/pdf")
        or fetched.raw_bytes[:5] == b"%PDF-"
    )
    if is_pdf:
        config = _pdf_payload_config(ctx)
        if config.get("engine") == "native":
            route = _require_native_pdf_route(ctx)
            return {
                "extractor": "pdf_native",
                "extractor_version": "1",
                "model_versions": {"chat_model": route.model or ""},
                "config": {"provider": route.provider_name},
            }
        try:
            extractor = pdf_extractor_for(config)
        except MarkerUnavailableError as exc:
            raise IngestRunnerError(
                str(exc), code="pdf_extractor_unavailable", retryable=True
            ) from exc
        return {
            "extractor": extractor.name,
            "extractor_version": extractor.version(),
            "model_versions": extractor.model_versions(),
            "config": config,
        }
    if category == "youtube":
        # Captions normalizer (captions_to_ir) v2 stamps per-cue t= timing onto
        # extractor_block_id; must match captions_to_ir's default.
        return {"extractor": "youtube", "extractor_version": "2", "model_versions": {}, "config": {}}
    text = fetched.raw_bytes[:4096].decode("utf-8", errors="replace")
    looks_html = (fetched.content_type or "").lower().startswith("text/html") or bool(
        re.match(r"\s*(?:<!doctype\s+html|<html)", text, re.IGNORECASE)
    )
    if category in ("web", "arxiv") or looks_html:
        return {"extractor": "html", "extractor_version": "2", "model_versions": {}, "config": {}}
    # Head-based transcript sniff — same 4 KB window default_extract uses, so the
    # identity and the actual extraction always agree.
    from learnloop.ingest.transcripts import detect_transcript_format

    if detect_transcript_format(text) is not None:
        return {"extractor": "transcript", "extractor_version": "1", "model_versions": {}, "config": {}}
    # Markdown normalizer (markdown_to_ir) is at version "2" (level-2 unit fallback);
    # must match markdown_to_ir's default so preflight cache keys line up.
    return {"extractor": "text", "extractor_version": "2", "model_versions": {}, "config": {}}


def _audio_ingest_config(ctx: JobContext):
    """The vault's [ingest.audio] settings (defaults when the vault is gone)."""

    from learnloop.config import AudioIngestConfig
    from learnloop.vault.loader import load_vault

    try:
        return load_vault(ctx.vault_root).config.ingest.audio
    except FileNotFoundError:
        return AudioIngestConfig()


@dataclass(frozen=True)
class NativeMediaRoute:
    """A resolved native-multimodal route: which chat provider ingests media."""

    provider_name: str
    model: str | None
    max_audio_mb: int


def _native_media_route(ctx: JobContext, modality: str) -> NativeMediaRoute | None:
    """PURE config decision: is native multimodal active for this modality?

    Shared by default_extract and default_extraction_identity so the cache
    identity and the actual extraction can never disagree. Requires
    [ingest.native] enabled + the per-modality flag, a canonical_ingest route
    resolving to an OpenAI-compatible chat provider, and the modality declared
    in that profile's input_modalities."""

    from learnloop.ai.multimodal import supports_input_modality
    from learnloop.ai.routing import provider_for_task
    from learnloop.vault.loader import load_vault

    try:
        config = load_vault(ctx.vault_root).config
    except FileNotFoundError:
        return None
    native = config.ingest.native
    if not native.enabled or not bool(getattr(native, modality, False)):
        return None
    selection = provider_for_task(config, "canonical_ingest")
    profile = config.ai.providers.get(selection.provider_name)
    if profile is None or profile.type.lower() not in {"openai_chat", "openrouter"}:
        return None
    if not supports_input_modality(profile, modality):
        return None
    return NativeMediaRoute(
        provider_name=selection.provider_name,
        model=profile.model,
        max_audio_mb=native.max_audio_mb,
    )


def _native_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any:
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.vault.loader import load_vault

    config = load_vault(ctx.vault_root).config
    resolved = ready_client_for_task(
        ctx.vault_root,
        config,
        "canonical_ingest",
        explicit=route.provider_name,
    )
    if resolved.client is None:
        raise IngestRunnerError(
            resolved.runtime.message
            or f"AI provider {route.provider_name!r} is {resolved.runtime.status}.",
            code="native_media_unavailable",
            retryable=True,
        )
    return resolved.client


def _transcription_media_route(ctx: JobContext) -> NativeMediaRoute | None:
    """Resolve an explicitly configured chat-transcription route without I/O."""

    from learnloop.ai.multimodal import supports_input_modality
    from learnloop.ai.routing import provider_for_task
    from learnloop.vault.loader import load_vault

    try:
        config = load_vault(ctx.vault_root).config
    except FileNotFoundError:
        return None
    if not str(config.ai.routing.transcription or "").strip():
        return None
    selection = provider_for_task(config, "transcription")
    profile = config.ai.providers.get(selection.provider_name)
    if profile is None:
        raise IngestRunnerError(
            f"Transcription provider {selection.provider_name!r} is not configured.",
            code="transcription_unavailable",
            retryable=True,
        )
    if profile.type.lower() not in {"openai_chat", "openrouter"}:
        raise IngestRunnerError(
            f"Transcription provider {selection.provider_name!r} does not support chat audio.",
            code="transcription_unavailable",
            retryable=True,
        )
    if not supports_input_modality(profile, "audio"):
        raise IngestRunnerError(
            f"Transcription provider {selection.provider_name!r} does not declare audio input.",
            code="transcription_unavailable",
            retryable=True,
        )
    return NativeMediaRoute(
        provider_name=selection.provider_name,
        model=profile.model,
        # Preserve the existing base64/chat upload cap. Endpoint transcription
        # continues to use [ingest.audio] max_file_mb below.
        max_audio_mb=config.ingest.native.max_audio_mb,
    )


def _transcription_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any:
    """Build the configured transcription client through the composition root."""

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.ai.transport import MEDIA_TRANSCRIPTION
    from learnloop.vault.loader import load_vault

    config = load_vault(ctx.vault_root).config
    # Media egress is consented for the provider named by the route. Mark that
    # selection explicit so the generic fallback chain cannot send bytes to a
    # different, unconsented provider.
    resolved = ready_client_for_task(
        ctx.vault_root,
        config,
        "transcription",
        explicit=route.provider_name,
    )
    if resolved.client is None:
        raise IngestRunnerError(
            resolved.runtime.message
            or f"AI provider {resolved.provider_name!r} is {resolved.runtime.status}.",
            code="transcription_unavailable",
            retryable=True,
        )
    if not resolved.client.supports(MEDIA_TRANSCRIPTION):
        raise IngestRunnerError(
            f"AI provider {resolved.provider_name!r} does not support audio transcription.",
            code="transcription_unavailable",
            retryable=True,
        )
    return resolved


def _audio_filename(fetched: FetchedBytes) -> str:
    from urllib.parse import urlparse

    raw = fetched.original_uri or ""
    if raw.lower().startswith(("http://", "https://")):
        raw = urlparse(raw).path
    name = Path(raw).name
    return name or "audio"


# Shared by identity and extraction so both raise the same actionable message.
_ROUTED_AUDIO_FORMAT_MESSAGE = (
    "Chat transcription sends audio as input_audio and supports "
    "mp3/wav only; convert the file or switch the transcription provider to "
    "an OpenAI-compatible endpoint."
)


def _extract_audio(fetched: FetchedBytes, ctx: JobContext) -> Any:
    """Audio → timestamped transcript → the same time_range IR captions use.

    Native-multimodal route first (when configured and the container is a chat
    input_audio format); then the optional ``transcription`` task route;
    otherwise the [ingest.audio] transcription endpoint. All failure modes are
    retryable typed errors: audio
    is always an external call, so the durable queue owns retry semantics — no
    partial IR ever persists, and a mid-run provider failure never silently
    switches routes (different cost/consent surface)."""

    from learnloop.ai.multimodal import chat_audio_format
    from learnloop.ingest.extractors import transcript_to_ir
    from learnloop.ingest.transcription import (
        TranscriptionFailed,
        TranscriptionUnavailable,
        transcribe_audio,
    )

    route = _native_media_route(ctx, "audio")
    chat_format = chat_audio_format(_audio_filename(fetched))
    if route is not None and chat_format is not None:
        return _extract_audio_native(fetched, ctx, route, chat_format)

    config = _audio_ingest_config(ctx)
    transcription_route = _transcription_media_route(ctx)
    if transcription_route is not None:
        return _extract_audio_routed(
            fetched,
            ctx,
            config,
            transcription_route,
            chat_format,
        )

    size_mb = len(fetched.raw_bytes) / (1024 * 1024)
    if size_mb > config.max_file_mb:
        raise IngestRunnerError(
            f"Audio file is {size_mb:.1f} MB; [ingest.audio] max_file_mb is {config.max_file_mb}.",
            code="audio_too_large",
            retryable=True,
        )
    try:
        result = transcribe_audio(
            fetched.raw_bytes, filename=_audio_filename(fetched), config=config
        )
    except TranscriptionUnavailable as exc:
        raise IngestRunnerError(str(exc), code="transcription_unavailable", retryable=True) from exc
    except TranscriptionFailed as exc:
        raise IngestRunnerError(str(exc), code="transcription_failed", retryable=True) from exc
    return transcript_to_ir(
        result.cues,
        title=ctx.payload.get("title"),
        extractor_name="audio_transcript",
        extractor_version="1",
    )


def _extract_audio_native(
    fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute, chat_format: str
) -> Any:
    from learnloop.ai.multimodal import MediaTranscriptionContext
    from learnloop.ai.errors import CodexUnavailable

    size_mb = len(fetched.raw_bytes) / (1024 * 1024)
    if size_mb > route.max_audio_mb:
        raise IngestRunnerError(
            f"Audio file is {size_mb:.1f} MB; [ingest.native] max_audio_mb is {route.max_audio_mb}.",
            code="audio_too_large",
            retryable=True,
        )
    client = _native_media_client(ctx, route)
    try:
        transcript = client.run_media_transcription(
            MediaTranscriptionContext(
                media_bytes=fetched.raw_bytes,
                media_format=chat_format,
                title=ctx.payload.get("title") or fetched.title,
            )
        )
    except CodexUnavailable as exc:
        raise IngestRunnerError(str(exc), code="native_audio_failed", retryable=True) from exc
    return _chat_transcript_to_ir(
        transcript, ctx, provider_label=route.provider_name, empty_code="native_audio_failed"
    )


def _extract_audio_routed(
    fetched: FetchedBytes,
    ctx: JobContext,
    config: Any,
    route: NativeMediaRoute,
    chat_format: str | None,
) -> Any:
    """Transcribe through the dedicated task route with no endpoint fallback."""

    from learnloop.ai.multimodal import MediaTranscriptionContext
    from learnloop.ai.errors import CodexUnavailable

    if chat_format is None:
        raise IngestRunnerError(
            _ROUTED_AUDIO_FORMAT_MESSAGE,
            code="audio_format_unsupported",
            retryable=True,
        )
    size_mb = len(fetched.raw_bytes) / (1024 * 1024)
    if size_mb > route.max_audio_mb:
        # Base64 inflates ~33% inside a chat body, so the chat-path cap
        # applies, not the endpoint's max_file_mb.
        raise IngestRunnerError(
            f"Audio file is {size_mb:.1f} MB; [ingest.native] max_audio_mb is {route.max_audio_mb}.",
            code="audio_too_large",
            retryable=True,
        )
    resolved = _transcription_media_client(ctx, route)
    try:
        transcript = resolved.client.run_media_transcription(
            MediaTranscriptionContext(
                media_bytes=fetched.raw_bytes,
                media_format=chat_format,
                title=ctx.payload.get("title") or fetched.title,
                language=config.language or None,
            )
        )
    except CodexUnavailable as exc:
        raise IngestRunnerError(
            f"Audio transcription failed: {exc}. Check that the model accepts audio input.",
            code="transcription_failed",
            retryable=True,
        ) from exc
    return _chat_transcript_to_ir(
        transcript,
        ctx,
        provider_label=resolved.provider_name,
        empty_code="transcription_failed",
    )


def _chat_transcript_to_ir(
    transcript: Any, ctx: JobContext, *, provider_label: str, empty_code: str
) -> Any:
    """Chat-model MediaTranscript segments → the same time_range IR the
    endpoint transcription path produces (shared native/routed-chat tail)."""

    from learnloop.ingest.extractors import transcript_to_ir
    from learnloop.ingest.transcripts import TranscriptCue

    cues = [
        TranscriptCue(
            start=segment.start_seconds,
            end=segment.end_seconds,
            text=segment.text.strip(),
            speaker=segment.speaker,
        )
        for segment in transcript.segments
        if segment.text.strip()
    ]
    if not cues:
        raise IngestRunnerError(
            f"{provider_label} returned no transcript segments",
            code=empty_code,
            retryable=True,
        )
    return transcript_to_ir(
        cues,
        title=ctx.payload.get("title"),
        extractor_name="audio_native",
        extractor_version="1",
    )


def _require_native_pdf_route(ctx: JobContext) -> NativeMediaRoute:
    route = _native_media_route(ctx, "pdf")
    if route is None:
        raise IngestRunnerError(
            'PDF engine "native" requires [ingest.native] enabled with pdf = true and a '
            'canonical_ingest route to an OpenAI-compatible provider declaring "pdf" in '
            "input_modalities.",
            code="native_pdf_unavailable",
            retryable=True,
        )
    return route


def _extract_pdf_native(fetched: FetchedBytes, ctx: JobContext) -> Any:
    """PDF → chat file part → Markdown → IR ([ingest.pdf] engine "native")."""

    from learnloop.ai.multimodal import PdfExtractionContextNative
    from learnloop.ai.errors import CodexUnavailable
    from learnloop.ingest.extractors import markdown_to_ir

    route = _require_native_pdf_route(ctx)
    if ctx.payload.get("page_selection"):
        raise IngestRunnerError(
            "Native PDF ingestion does not support page selection; use the marker or "
            "pypdf engine for page ranges.",
            code="native_pdf_unavailable",
        )
    filename = _audio_filename(fetched)
    if "." not in filename:
        filename = f"{filename}.pdf"
    client = _native_media_client(ctx, route)
    try:
        markdown = client.run_media_markdown(
            PdfExtractionContextNative(
                media_bytes=fetched.raw_bytes,
                filename=filename,
                title=ctx.payload.get("title") or fetched.title,
            )
        )
    except CodexUnavailable as exc:
        raise IngestRunnerError(str(exc), code="native_pdf_failed", retryable=True) from exc
    return markdown_to_ir(markdown, title=ctx.payload.get("title"), extractor_name="pdf_native")


def _caption_cues(text: str) -> list[dict[str, Any]] | None:
    """Decode fetched YouTube caption bytes ({"cues": [...]} or a bare list)."""

    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        return None
    cues = payload.get("cues") if isinstance(payload, dict) else payload
    if not isinstance(cues, list) or not cues:
        return None
    normalized: list[dict[str, Any]] = []
    for cue in cues:
        if not isinstance(cue, dict) or not str(cue.get("text") or "").strip():
            continue
        start = float(cue.get("start") or 0.0)
        end = cue.get("end")
        if end is None:
            end = start + float(cue.get("duration") or 0.0)
        normalized.append({"start": start, "end": float(end), "text": cue["text"]})
    return normalized or None


def _html_to_markdown(raw_html: str) -> str | None:
    """Readable-body markdown from raw HTML (same engine as the legacy path)."""

    try:
        import trafilatura
    except ImportError:  # pragma: no cover - trafilatura is a base dependency
        return None
    extracted = trafilatura.extract(
        raw_html, output_format="markdown", include_tables=True, include_comments=False
    )
    return extracted or None


def default_run_legacy_ingest(
    *,
    vault_root: Path,
    source: str,
    subject_id: str,
    mode: str,
    progress: Callable[[str, dict[str, Any]], None] | None,
    clock: Clock | None,
    ir_markdown: str | None = None,
    **_ignored: Any,
) -> Any:
    """Run the legacy one-shot pipeline in-process with a ready provider client.

    Mirrors the CLI's provider readiness (``learnloop ingest``) so the durable
    ``legacy_ingest`` job keeps the current UX. Tests inject a stub that calls
    ``ingest_canonical_source`` with a fake client (see test_source_ingestion)."""

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.content.pipeline.source_ingestion import ingest_canonical_source
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault_root)
    resolved = ready_client_for_task(vault_root, vault.config, "canonical_ingest")
    runtime, client = resolved.runtime, resolved.client
    if client is None:
        raise IngestRunnerError(runtime.message or f"Authoring provider is {runtime.status}.")

    purpose = "exam_ingest" if mode == "exam" else "canonical_ingest"
    instructions = exam_ingest_instructions(None) if mode == "exam" else None
    return ingest_canonical_source(
        vault_root,
        source,
        client,
        subject_id=subject_id,
        instructions=instructions,
        model=getattr(client, "model", None),
        codex_revision=getattr(runtime, "actual_revision", None),
        purpose=purpose,
        ir_markdown=ir_markdown,
        clock=clock,
        progress=progress,
    )


def inventory_client_identity(client: Any) -> tuple[str, str]:
    return (
        str(getattr(client, "provider_type", None) or "codex"),
        str(getattr(client, "model", None) or "unknown"),
    )


def default_inventory_identity(ctx: JobContext) -> tuple[str, str] | None:
    """Resolve the primary inventory cache key without a runtime probe.

    A miss still validates runtime readiness before executing. If that selects a
    fallback provider, ``handle_inventory`` rechecks the miss under the actual
    client's identity before making a model call.
    """

    from learnloop.ai.routing import provider_for_task
    from learnloop.vault.loader import load_vault

    config = load_vault(ctx.vault_root).config
    provider_name = provider_for_task(config, "canonical_ingest").provider_name
    profile = config.ai.providers.get(provider_name)
    if profile is None:
        return None
    provider_type = profile.type.strip().lower()
    if provider_type in {"http", "http_adapter"}:
        provider_type = "http_adapter"
    return provider_type, str(profile.model or "unknown")


def default_inventory_client(
    ctx: JobContext,
    *,
    codex_timeout_seconds: int | None = None,
) -> Any:
    """Resolve the unit-inventory/quick-check client through ai routing (§7).

    Routed via the ``canonical_ingest`` task (empty routing follows
    ai.active_provider), except codex-family routes are pinned to the
    LOW-effort codex profile: unit inventories deliberately stay cheap while
    synthesis follows the routed medium-effort profile
    (``default_synthesis_client``). The inventory/quick-check methods are
    getattr-discovered on the client, so a provider lacking them degrades to
    an explicit unavailable error rather than fabricating rows."""

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    resolved = ready_client_for_task(
        ctx.vault_root,
        vault.config,
        "canonical_ingest",
        timeout_seconds=codex_timeout_seconds,
    )
    if resolved.client is not None:
        return resolved.client
    raise IngestRunnerError(
        resolved.runtime.message
        or f"AI provider {resolved.provider_name!r} is {resolved.runtime.status}."
    )


def default_synthesis_client(ctx: JobContext) -> Any:
    """Resolve the canonical-ingest route for judgment-heavy synthesis.

    Unit inventories deliberately keep the low-effort legacy Codex client;
    synthesis follows the routed medium-effort profile and its fallback. Codex
    SDK turns get an eight-minute deadline because source-set bootstrap and
    append synthesis routinely exceed the interactive default.
    """

    return _routed_task_client(
        ctx,
        "canonical_ingest",
        codex_timeout_seconds=INGEST_CODEX_TIMEOUT_SECONDS,
    )


def default_animation_client(ctx: JobContext) -> Any:
    """Resolve the animation route (default: the medium-effort profile) — any
    configured provider works; run_concept_animation is getattr-discovered."""

    return _routed_task_client(ctx, "animation")


def default_rung_variant_client(ctx: JobContext) -> Any:
    """Resolve the rung_variant route (default: the fast low-effort profile).

    A learner-requested variant is a small, instruction-constrained authoring
    task whose output the deterministic rung gate checks — it does not need the
    judgment-heavy synthesis profile, and the learner is actively waiting."""

    return _routed_task_client(ctx, "rung_variant")


def default_promotion_analysis_client(ctx: JobContext) -> Any:
    """Fast classification/dedup pass for a durable promotion request."""

    try:
        return _routed_task_client(ctx, "tutor_qa")
    except IngestRunnerError as exc:
        raise IngestRunnerError(
            str(exc),
            code="provider_unavailable",
            details={"task": "tutor_qa"},
            retryable=True,
        ) from exc


def default_promotion_authoring_client(ctx: JobContext) -> Any:
    """Judgment-heavy practice generation follows the configured authoring route."""

    try:
        return _routed_task_client(ctx, "authoring")
    except IngestRunnerError as exc:
        raise IngestRunnerError(
            str(exc),
            code="provider_unavailable",
            details={"task": "authoring"},
            retryable=True,
        ) from exc


def _routed_task_client(
    ctx: JobContext,
    task: str,
    *,
    codex_timeout_seconds: int | None = None,
) -> Any:
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    resolved = ready_client_for_task(
        ctx.vault_root,
        vault.config,
        task,
        timeout_seconds=codex_timeout_seconds,
    )
    if resolved.client is None:
        raise IngestRunnerError(
            resolved.runtime.message
            or f"Synthesis provider is {resolved.runtime.status}."
        )
    return resolved.client


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


class _InventoryInterruptGroup:
    """One job-scoped interrupt hook covering its active inventory clients."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: dict[int, tuple[Any, int]] = {}

    def add(self, client: Any) -> None:
        with self._lock:
            existing = self._clients.get(id(client))
            self._clients[id(client)] = (
                client,
                1 if existing is None else existing[1] + 1,
            )

    def discard(self, client: Any) -> None:
        with self._lock:
            existing = self._clients.get(id(client))
            if existing is None:
                return
            if existing[1] <= 1:
                self._clients.pop(id(client), None)
            else:
                self._clients[id(client)] = (existing[0], existing[1] - 1)

    def interrupt(self) -> None:
        with self._lock:
            clients = [entry[0] for entry in self._clients.values()]
        for client in clients:
            interrupt = interrupt_callback(client)
            if interrupt is None:
                continue
            try:
                interrupt()
            except Exception:
                # Cancellation is best-effort per provider; continue through
                # the group so one broken hook cannot strand another call.
                pass

    def supports(self, capability: str) -> bool:
        return capability == INTERRUPT


def handle_inventory(ctx: JobContext) -> dict[str, Any]:
    """inventory: role-aware per-unit inventories for the selected units (§7).

    Depends on extraction (the runner enforces this via job dependencies).
    Payload: ``extraction_id`` and ``units`` = [{unit_id, role, profile?}]. Each
    unit is inventoried through the cache: a cache hit records ZERO tokens
    (``run_unit_inventory`` returns ``cache_hit``), and only semantic-hash-changed
    units are ever re-inventoried across collections/revisions (§3.2)."""

    from learnloop.content.synthesis.source_unit_inventory import (
        InventoryExecution,
        InventoryResult,
        PreparedInventory,
        execute_prepared_inventory,
        persist_prepared_inventory,
        prepare_unit_inventory,
    )

    payload = ctx.payload
    extraction_id, units = _inventory_inputs(ctx, payload)
    if not extraction_id:
        raise IngestRunnerError("inventory job requires an 'extraction_id'.")
    if not units:
        raise IngestRunnerError("inventory job requires at least one unit.")
    units = _effective_inventory_inputs(ctx.repo, extraction_id, units)
    budgets = _ingest_budgets(ctx)
    budget = _optional_int(payload.get("input_budget_tokens")) or budgets.inventory_input_tokens
    unlimited_token_budget = bool(payload.get("unlimited_token_budget", False))
    output_budget = (
        None
        if unlimited_token_budget
        else _optional_int(payload.get("output_budget_tokens")) or budgets.inventory_output_tokens
    )

    specs: list[dict[str, Any]] = []
    for spec in units:
        unit_id = str(spec.get("unit_id") or "").strip()
        if not unit_id:
            raise IngestRunnerError("every inventory unit needs a 'unit_id'.")
        specs.append(
            {
                **dict(spec),
                "unit_id": unit_id,
                "unit_ids": [
                    str(value) for value in spec.get("unit_ids") or [unit_id]
                ],
            }
        )

    ctx.report("extracted", message="Checking unit inventory cache")
    warm_client: Any = None
    identity = ctx.services.inventory_identity(ctx)
    if identity is None:
        # Custom factories may not expose a cheap identity resolver on their
        # first job. Retain this client for the first execution lane.
        warm_client = ctx.services.inventory_client(
            ctx, bind_interruptible=False
        )
        identity = inventory_client_identity(warm_client)

    results_by_index: dict[int, InventoryResult] = {}
    work_by_index: dict[int, PreparedInventory] = {}

    def prepare(index: int, provider_identity: tuple[str, str]) -> None:
        spec = specs[index]
        resolved = prepare_unit_inventory(
            ctx.repo,
            extraction_id,
            spec["unit_id"],
            unit_ids=spec["unit_ids"],
            role=str(spec.get("role") or "reference"),
            profile=spec.get("profile"),
            provider=provider_identity[0],
            model=provider_identity[1],
            input_budget_tokens=budget,
            output_budget_tokens=output_budget,
            clock=ctx.clock,
        )
        if isinstance(resolved, InventoryResult):
            results_by_index[index] = resolved
            work_by_index.pop(index, None)
        else:
            work_by_index[index] = resolved
            results_by_index.pop(index, None)

    for index in range(len(specs)):
        prepare(index, identity)

    if work_by_index:
        if warm_client is None:
            warm_client = ctx.services.inventory_client(
                ctx, bind_interruptible=False
            )
        actual_identity = inventory_client_identity(warm_client)
        if actual_identity != identity:
            # Runtime routing may have selected the configured fallback. Recheck
            # those misses under the identity that will actually produce them.
            for index in list(work_by_index):
                prepare(index, actual_identity)
            identity = actual_identity

    if work_by_index:
        worker_count = min(_MAX_INVENTORY_WORKERS, len(work_by_index))
        clients = [warm_client]
        for _ in range(1, worker_count):
            client = ctx.services.inventory_client(
                ctx, bind_interruptible=False
            )
            if inventory_client_identity(client) != identity:
                raise IngestRunnerError(
                    "Inventory provider routing changed while preparing parallel workers."
                )
            clients.append(client)

        lanes: list[list[tuple[int, PreparedInventory]]] = [
            [] for _ in range(worker_count)
        ]
        for ordinal, item in enumerate(sorted(work_by_index.items())):
            lanes[ordinal % worker_count].append(item)

        interrupt_group = _InventoryInterruptGroup()
        ctx.bind_interruptible(interrupt_group)
        progress_events: queue.SimpleQueue[tuple[str, int, int]] = queue.SimpleQueue()
        total_model_windows = sum(
            len(prepared.windows) for prepared in work_by_index.values()
        )
        completed_model_windows = 0
        ctx.report(
            "inventoried",
            message=(
                f"Inventorying {len(work_by_index)} uncached unit"
                f"{'' if len(work_by_index) == 1 else 's'} "
                f"across {total_model_windows} model window"
                f"{'' if total_model_windows == 1 else 's'}"
            ),
            current_window=0,
            total_windows=total_model_windows,
        )

        def run_lane(
            client: Any,
            lane: list[tuple[int, PreparedInventory]],
        ) -> list[tuple[int, PreparedInventory, InventoryExecution]]:
            completed: list[
                tuple[int, PreparedInventory, InventoryExecution]
            ] = []
            interrupt_group.add(client)
            try:
                for index, prepared in lane:
                    def report_window(
                        current: int,
                        total: int,
                        unit: str = prepared.unit_id,
                    ) -> None:
                        progress_events.put((unit, current, total))

                    execution = execute_prepared_inventory(
                        prepared,
                        client,
                        progress=report_window,
                    )
                    completed.append((index, prepared, execution))
                return completed
            finally:
                interrupt_group.discard(client)

        executions: dict[int, tuple[PreparedInventory, InventoryExecution]] = {}
        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=worker_count,
                thread_name_prefix="learnloop-inventory",
            ) as executor:
                pending = {
                    executor.submit(run_lane, client, lane)
                    for client, lane in zip(clients, lanes)
                    if lane
                }
                while pending:
                    done, pending = concurrent.futures.wait(
                        pending,
                        timeout=0.25,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    while not progress_events.empty():
                        unit_id, unit_window, unit_total = progress_events.get_nowait()
                        completed_model_windows += 1
                        ctx.report(
                            "inventoried",
                            message=(
                                f"Inventoried {unit_id} window "
                                f"{unit_window} of {unit_total}"
                            ),
                            current_window=completed_model_windows,
                            total_windows=total_model_windows,
                        )
                    if ctx.cancelled():
                        interrupt_group.interrupt()
                        for future in pending:
                            future.cancel()
                        raise JobCancelled()
                    for future in done:
                        for index, prepared, execution in future.result():
                            executions[index] = (prepared, execution)
        except Exception:
            interrupt_group.interrupt()
            raise

        # Provider workers never touch SQLite. Persist their validated output in
        # payload order on the runner thread.
        for index in sorted(executions):
            prepared, execution = executions[index]
            result = persist_prepared_inventory(
                ctx.repo, prepared, execution, clock=ctx.clock
            )
            ctx.record_usage(dict(result.usage or {}))
            results_by_index[index] = result

    results: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        result = results_by_index[index]
        results.append(
            {
                "unit_id": result.inventory.unit_id,
                "unit_ids": spec["unit_ids"],
                "inventory_id": result.inventory_id,
                "profile": result.profile,
                "cache_hit": result.cache_hit,
                "reused_profile": result.reused_profile,
            }
        )

    cache_hits = sum(1 for row in results if row["cache_hit"])
    ctx.report(
        "inventoried",
        message=(
            "Unit inventories ready"
            if cache_hits == 0
            else f"Unit inventories ready · reused {cache_hits} cached"
        ),
    )
    return {
        "extraction_id": extraction_id,
        "units": results,
        "cache_hits": cache_hits,
    }


def _ingest_budgets(ctx: JobContext):
    """Load vault budgets, retaining service defaults for isolated workers/tests."""

    from learnloop.config import IngestBudgetsConfig
    from learnloop.vault.loader import load_vault

    try:
        return load_vault(ctx.vault_root).config.ingest.budgets
    except FileNotFoundError:
        return IngestBudgetsConfig()


def _inventory_inputs(
    ctx: JobContext, payload: Mapping[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    """Resolve public import→inventory shorthand from the completed dependency."""

    extraction_id = str(payload.get("extraction_id") or "").strip()
    units = [dict(unit) for unit in payload.get("units") or [] if isinstance(unit, Mapping)]
    if not extraction_id:
        for dep_id in ctx.repo.ingest_job_dependency_ids(ctx.job_id):
            dependency = ctx.repo.get_ingest_job(dep_id)
            if dependency is None or dependency.get("job_type") != "import":
                continue
            result = dependency.get("result") or {}
            extraction_id = str(result.get("extraction_id") or "").strip()
            if extraction_id:
                break
    if extraction_id and not units:
        ir = ctx.repo.load_document_ir(extraction_id)
        role = str(payload.get("role") or "reference")
        units = [{"unit_id": unit.unit_id, "role": role} for unit in (ir.units if ir else [])]
    return extraction_id, units


def _effective_inventory_inputs(
    repo: Repository,
    extraction_id: str,
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fold explicit same-role ``merge_with_next`` groups into one model input.

    Boundary overrides describe the learner-confirmed semantic unit shape, not a
    presentation-only grouping.  A merge is honored only when every source member
    is selected with the same effective role/profile.  Exam units remain separate
    because held-out and paper-level accounting is member-scoped.
    """

    selection = repo.get_unit_selection(extraction_id)
    ir = repo.load_document_ir(extraction_id)
    if ir is None or not selection or not selection.get("boundary_overrides"):
        return units

    from learnloop.content.sources.role_authority import default_inventory_profile
    from learnloop.content.synthesis.source_unit_inventory import normalize_profile
    from learnloop.content.synthesis.source_unit_selection import effective_scope_groups

    requested: dict[str, dict[str, Any]] = {}
    input_order: list[str] = []
    for spec in units:
        source_id = str(spec.get("unit_id") or "").strip()
        if not source_id or source_id in requested:
            continue
        requested[source_id] = dict(spec)
        input_order.append(source_id)

    effective_specs: list[dict[str, Any]] = []
    role_by_unit = {
        source_id: str(spec.get("role") or "reference")
        for source_id, spec in requested.items()
    }
    groups = effective_scope_groups(
        ir,
        selection.get("boundary_overrides") or [],
        input_order,
        role_by_unit=role_by_unit,
    )
    for group in groups:
        source_ids = [str(value) for value in group["unit_ids"]]
        member_specs = [requested[source_id] for source_id in source_ids]
        if group["merged"]:
            profiles = {
                normalize_profile(
                    spec.get("profile")
                    or default_inventory_profile(
                        str(spec.get("role") or "reference")
                    )
                )
                for spec in member_specs
            }
        else:
            profiles = set()
        if group["merged"] and len(profiles) == 1:
            role = str(group["role"])
            profile = next(iter(profiles))
            effective_specs.append(
                {
                    "unit_id": str(group["unit_id"]),
                    "unit_ids": source_ids,
                    "role": role,
                    "profile": profile,
                }
            )
            continue
        for source_id in source_ids:
            effective_specs.append(requested[source_id])
    return effective_specs


def handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]:
    """bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).

    Depends on all selected unit-inventory jobs (the runner enforces this via
    job dependencies). Payload: ``source_set_id`` plus optional ``brief``,
    ``mode``, ``apply``, ``create_goal``. Emits the dependency-closed proposal
    through the existing pipeline; the manifest hash is the agent-run cache seam
    so an identical manifest re-drains at zero tokens."""

    from learnloop.content.synthesis.source_set_synthesis import (
        StudyMapError,
        create_study_map,
        revalidate_synthesis_candidate,
    )

    payload = ctx.payload
    source_set_id = str(payload.get("source_set_id") or "").strip()
    if not source_set_id:
        raise IngestRunnerError("bootstrap_synthesis job requires a 'source_set_id'.")

    # `auto` is a product journey, not an alias for bootstrap: once this subject
    # has a live map, new sources reconcile into it through the bounded append
    # vocabulary instead of tripping the identity-lock refusal.
    if str(payload.get("mode") or "auto") == "auto" and not payload.get("reuse_candidate"):
        from learnloop.content.synthesis.source_append import subject_has_applied_study_map
        from learnloop.vault.loader import load_vault

        vault = load_vault(ctx.vault_root)
        source_set = next((item for item in vault.source_sets if item.id == source_set_id), None)
        if source_set is not None and subject_has_applied_study_map(vault, source_set.subject_id):
            return handle_append_synthesis(ctx)

    ctx.report("inventoried", message="Preparing study-map synthesis")
    try:
        if payload.get("reuse_candidate") and payload.get("synthesis_run_id"):
            # Recovery path: finish the pipeline from the preserved candidate —
            # no provider client and ZERO model calls.
            ctx.report("synthesized", message="Revalidating the preserved synthesis candidate")
            result = revalidate_synthesis_candidate(
                ctx.vault_root,
                str(payload["synthesis_run_id"]),
                apply=bool(payload.get("apply", False)),
                create_goal=bool(payload.get("create_goal", False)),
                repair=bool(payload.get("repair_candidate", False)),
                repair_ops=[dict(op) for op in payload.get("repair_ops") or []],
                repository=ctx.repo,
                clock=ctx.clock,
                progress=_synthesis_progress(ctx),
            )
        else:
            client = ctx.services.synthesis_client(ctx)
            result = create_study_map(
                ctx.vault_root,
                source_set_id,
                client=client,
                brief=payload.get("brief") or {},
                mode=str(payload.get("mode") or "auto"),
                apply=bool(payload.get("apply", False)),
                create_goal=bool(payload.get("create_goal", False)),
                repository=ctx.repo,
                clock=ctx.clock,
                budget_overrides=dict(payload.get("synthesis_budgets") or {}),
                unlimited_token_budget=bool(payload.get("unlimited_token_budget", False)),
                progress=_synthesis_progress(ctx),
            )
    except StudyMapError as exc:
        raise IngestRunnerError(
            str(exc),
            code=exc.code,
            details={
                "diagnostics": exc.diagnostics,
                "lock_reasons": exc.lock_reasons,
                "stage": "synthesis",
                "completed_dependencies_preserved": True,
                "candidate_preserved": exc.candidate_preserved,
                "synthesis_run_id": exc.synthesis_run_id,
            },
            retryable=exc.code not in {"subject_identity_locked"},
        ) from exc

    run = ctx.repo.synthesis_run(result.synthesis_run_id) if result.synthesis_run_id else None
    ctx.record_usage(
        (run or {}).get("actual_usage")
        or {"calls": 0 if result.reused else ((result.item_counts and 1) or 0)}
    )
    ctx.report("synthesized", message="Study map synthesized")
    if result.applied:
        ctx.report("applied", message="Study map applied")
    else:
        ctx.report("proposed", message="Study-map proposal ready for review")
    return result.as_dict()


# Synthesis-service progress stages -> checkpoint-ladder phases. Shard work
# happens between "inventoried" and "synthesized"; gates run after the model
# output exists; persistence/apply match their ladder rungs.
_SYNTH_STAGE_PHASE = {
    "synthesis": "inventoried",
    "validation": "synthesized",
    "persistence": "proposed",
    "apply": "applied",
}


def _synthesis_progress(ctx: JobContext):
    """A ProgressFn bridging create_study_map to the durable job heartbeat.

    Every callback refreshes the lease and re-checks cancellation, so a long
    multi-shard synthesis can be cancelled at the next shard boundary instead
    of only before/after the whole model stage."""

    def progress(stage: str, message: str, current: int | None = None, total: int | None = None) -> None:
        ctx.report(
            _SYNTH_STAGE_PHASE.get(stage, "inventoried"),
            message=message,
            current_window=current,
            total_windows=total,
        )

    return progress


def handle_append_synthesis(ctx: JobContext) -> dict[str, Any]:
    """append_synthesis: bounded reconciliation against an existing study map."""

    from learnloop.content.synthesis.source_append import append_source
    from learnloop.content.synthesis.source_set_synthesis import StudyMapError

    payload = ctx.payload
    source_set_id = str(payload.get("source_set_id") or payload.get("set_id") or "").strip()
    if not source_set_id:
        raise IngestRunnerError("append_synthesis job requires a 'source_set_id'.")
    ctx.report("inventoried", message="Preparing bounded source reconciliation")
    client = ctx.services.synthesis_client(ctx)
    try:
        result = append_source(
            ctx.vault_root,
            source_set_id,
            client=client,
            new_revision_ids=[str(value) for value in payload.get("new_revision_ids") or []] or None,
            change_kind=str(payload.get("change_kind") or "source_added"),
            revision_diff=dict(payload.get("revision_diff") or {}),
            brief=dict(payload.get("brief") or {}),
            auto_apply=bool(payload.get("apply", payload.get("auto_apply", True))),
            repository=ctx.repo,
            clock=ctx.clock,
            budget_overrides=dict(payload.get("synthesis_budgets") or {}),
            unlimited_token_budget=bool(payload.get("unlimited_token_budget", False)),
        )
    except StudyMapError as exc:
        raise IngestRunnerError(f"{exc.code}: {exc}") from exc
    ctx.record_usage({"calls": 0 if result.reused else 1})
    ctx.report("synthesized", message="Source reconciliation synthesized")
    if result.auto_applied_item_ids:
        ctx.report("applied", message="Safe source additions applied")
    else:
        ctx.report("proposed", message="Source reconciliation ready for review")
    return result.as_dict()


def handle_import(ctx: JobContext) -> dict[str, Any]:
    """import: fetch -> register artifact/revision -> extract to IR -> persist -> health.

    Retries reuse a completed revision (keyed by asset hash) and a completed
    extraction run (keyed by extraction_request_hash), so re-running never
    duplicates identity rows (§2.1/§2.2)."""

    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION
    from learnloop.ingest.resolution import resolve_source
    from learnloop.content.sources.source_library import register_source_revision

    payload = ctx.payload
    source = str(payload.get("source") or "").strip()
    if not source:
        raise IngestRunnerError("import job requires a 'source'.")
    resolved = resolve_source(source)
    category = resolved.category
    requested_pages = _normalize_pages(payload.get("page_selection")) or None

    ctx.report("acquired", message="Fetching source material")
    fetched = ctx.services.fetch_bytes(resolved.source, category, ctx)
    is_pdf = (
        category == "pdf"
        or (fetched.content_type or "").lower().startswith("application/pdf")
        or fetched.raw_bytes[:5] == b"%PDF-"
    )
    page_selection = requested_pages if is_pdf else None
    if page_selection:
        _validate_page_selection(fetched.raw_bytes, page_selection)

    display_title = _compose_display_title(fetched.title, fetched.authors)
    reader_enabled = payload.get("reader_enabled")
    registered = register_source_revision(
        ctx.repo,
        acquisition_kind=category,
        canonical_uri=resolved.source,
        raw_bytes=fetched.raw_bytes,
        original_uri=fetched.original_uri,
        retrieved_at=fetched.retrieved_at,
        display_title=display_title,
        reader_enabled=None if reader_enabled is None else bool(reader_enabled),
        vault_root=ctx.vault_root,
        clock=ctx.clock,
    )
    ctx.job["_revision_id"] = registered.revision_id
    # Label the extracted transcript unit by the real video title (not the
    # "<title> — <author>" display form) when the fetch captured one.
    if fetched.title and not ctx.payload.get("title"):
        ctx.job["payload"] = {**ctx.payload, "title": fetched.title}
    ctx.report("registered", message="Registered source revision")

    identity = dict(ctx.services.extraction_identity(fetched, category, ctx))
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id,
        extractor=str(identity.get("extractor") or "unknown"),
        extractor_version=str(identity.get("extractor_version") or "unknown"),
        model_versions=identity.get("model_versions") or {},
        config=identity.get("config") or {},
        page_selection=page_selection,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    existing = ctx.repo.extraction_run_by_request_hash(registered.revision_id, request_hash)
    if existing is not None and existing.get("status") == "completed":
        extraction_id = existing["id"]
        reused_extraction = True
        ir = ctx.repo.load_document_ir(extraction_id)
        if ir is None:
            raise IngestRunnerError(f"cached extraction '{extraction_id}' has no persisted IR")
    else:
        ir = ctx.services.extract_ir(fetched, category, ctx)
        # Injected/custom providers may refine the preflight identity. Persist
        # under the actual identity and let subsequent retries hit that key.
        actual_hash = extraction_request_hash(
            revision_id=registered.revision_id,
            extractor=ir.extractor,
            extractor_version=ir.extractor_version,
            model_versions=identity.get("model_versions") or {},
            config=identity.get("config") or {},
            page_selection=page_selection,
            ir_schema_version=IR_SCHEMA_VERSION,
        )
        if actual_hash != request_hash:
            request_hash = actual_hash
            existing = ctx.repo.extraction_run_by_request_hash(registered.revision_id, request_hash)
            if existing is not None and existing.get("status") == "completed":
                extraction_id = existing["id"]
                loaded = ctx.repo.load_document_ir(extraction_id)
                if loaded is None:
                    raise IngestRunnerError(f"cached extraction '{extraction_id}' has no persisted IR")
                ir = loaded
                reused_extraction = True
        if existing is not None and existing.get("status") == "completed":
            extraction_id = existing["id"]
            reused_extraction = True
        else:
            reused_extraction = False
        extraction_id = existing["id"] if existing is not None else f"ext_{new_ulid()}"
        if not reused_extraction and existing is None:
            ctx.repo.insert_extraction_run(
                id=extraction_id,
                revision_id=registered.revision_id,
                extractor=ir.extractor,
                extractor_version=ir.extractor_version,
                extraction_request_hash=request_hash,
                ir_schema_version=IR_SCHEMA_VERSION,
                model_versions=identity.get("model_versions") or {},
                config=identity.get("config") or {},
                page_selection=page_selection,
                status="running",
                clock=ctx.clock,
            )
        if not reused_extraction:
            ctx.repo.persist_document_ir(extraction_id, ir)
            ctx.repo.complete_extraction_run(
                extraction_id,
                extraction_result_hash=extraction_result_hash(request_hash, ir),
                health=ir.health.model_dump(mode="json"),
                clock=ctx.clock,
            )

    ctx.report("extracted", message="Extracted document structure")
    return {
        "source_id": registered.source_id,
        "revision_id": registered.revision_id,
        "title": display_title,
        "asset_hash": registered.asset_hash,
        "reused_revision": registered.reused_revision,
        "extraction_id": extraction_id,
        "reused_extraction": reused_extraction,
        "unit_count": len(ir.units),
        "block_count": len(ir.blocks),
        "page_selection": page_selection,
        "health": {
            "flags": list(ir.health.flags),
            "flagged_pages": ir.health.flagged_pages(),
        },
    }


def _compose_display_title(title: str | None, authors: Sequence[str]) -> str | None:
    """Assemble the artifact's stored label: "<title> — <author>" when both are
    known, the title alone when there is no author, and ``None`` (→ URL fallback)
    when the fetch captured no title at all."""

    clean_title = (title or "").strip()
    author = next((a.strip() for a in authors if a and a.strip()), "")
    if clean_title and author:
        return f"{clean_title} — {author}"
    return clean_title or None


def handle_legacy_ingest(ctx: JobContext) -> dict[str, Any]:
    """legacy_ingest: wrap the existing one-shot pipeline as one durable job so
    the current single-source UX keeps working (Quick add compatibility, §6.1)."""

    payload = ctx.payload
    source = str(payload.get("source") or "").strip()
    subject_id = str(payload.get("subject_id") or "").strip()
    mode = str(payload.get("mode") or "canonical")
    if not source:
        raise IngestRunnerError("legacy_ingest job requires a 'source'.")

    ctx.report("acquired", message="Preparing ingestion")

    # M3.5 v2-lite: when this legacy_ingest depends on a completed import job, the
    # source was already extracted once into a Document IR. Feed synthesis the IR's
    # display rendering (selected units only, if a selection was persisted) rather
    # than re-fetching/re-extracting. No import dependency (legacy call path) →
    # ir_markdown is None and the pipeline keeps its byte-identical legacy behavior.
    ir_markdown = _legacy_ir_markdown(ctx)

    def _progress(phase: str, details: dict[str, Any]) -> None:
        ladder = _LEGACY_PHASE_TO_LADDER.get(phase, "acquired")
        ctx.report(
            ladder,
            message=_LEGACY_PHASE_MESSAGE.get(phase, phase.replace("_", " ").capitalize()),
            current_window=_optional_int(details.get("current_window")),
            total_windows=_optional_int(details.get("total_windows")),
        )

    result = ctx.services.legacy_ingest(
        vault_root=ctx.vault_root,
        source=source,
        subject_id=subject_id,
        mode=mode,
        ir_markdown=ir_markdown,
        progress=_progress,
        clock=ctx.clock,
    )
    ctx.record_usage({"calls": int(getattr(result, "codex_calls", 0) or 0)})
    ctx.report("applied", message="Ingest complete")
    return result.as_dict() if hasattr(result, "as_dict") else dict(result)


def _legacy_ir_markdown(ctx: JobContext) -> str | None:
    """Render the IR from this job's completed ``import`` dependency, if any (§2.3).

    Returns the display markdown for the extraction the import stage produced,
    filtered to a persisted unit selection when one exists. Returns ``None`` when
    there is no import dependency or no persisted IR — the legacy path then runs
    unchanged (extract-once-reuse-everywhere without deep coupling; §15 M3.5)."""

    from learnloop.ingest.ir import render_ir_markdown

    extraction_id: str | None = None
    for dep_id in ctx.repo.ingest_job_dependency_ids(ctx.job_id):
        dep = ctx.repo.get_ingest_job(dep_id)
        if dep is None or dep.get("job_type") != "import" or dep.get("status") != "completed":
            continue
        result = dep.get("result")
        if isinstance(result, Mapping):
            candidate = result.get("extraction_id")
            if candidate:
                extraction_id = str(candidate)
                break
    if extraction_id is None:
        return None

    ir = ctx.repo.load_document_ir(extraction_id)
    if ir is None or not ir.blocks:
        return None
    selection = ctx.repo.get_unit_selection(extraction_id)
    selected = (selection or {}).get("selected_unit_ids") or None
    return render_ir_markdown(ir, selected_unit_ids=selected)


def handle_extraction_repair(ctx: JobContext) -> dict[str, Any]:
    """extraction_repair: a consent-gated, page-range re-extraction (§2.5).

    Payload carries the revision, target pages, repair options (force-OCR /
    inline-math / table-processing / an approved external LLM service per
    ``[ingest.pdf]``), and an explicit consent record (provider, purpose, pages,
    cached?). The run re-extracts only the requested pages with
    ``parent_extraction_id`` set, then composes with the parent so unaffected units
    keep their semantic hashes while repaired units get fresh ones (§2.3). Declining
    repair is simply not enqueuing this job — the flagged parent stays usable."""

    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION, compose_extraction_runs
    from learnloop.ingest.resolution import resolve_source

    payload = ctx.payload
    revision_id = str(payload.get("revision_id") or "").strip()
    if not revision_id:
        raise IngestRunnerError("extraction_repair requires a 'revision_id'.")
    pages = _normalize_pages(payload.get("pages") or payload.get("page_ranges"))
    if not pages:
        raise IngestRunnerError("extraction_repair requires at least one page.")
    consent = payload.get("consent")
    if not isinstance(consent, Mapping) or not consent.get("provider") or not consent.get("purpose"):
        raise IngestRunnerError(
            "extraction_repair requires an explicit consent record (provider + purpose)."
        )

    revision = ctx.repo.get_source_revision(revision_id)
    if revision is None:
        raise IngestRunnerError(f"revision '{revision_id}' does not exist.")
    artifact = ctx.repo.get_source_artifact(revision["source_id"])
    acquisition_kind = artifact.get("acquisition_kind") if artifact else "pdf"

    parent_id = payload.get("parent_extraction_id") or _latest_completed_extraction(ctx.repo, revision_id)
    if not parent_id:
        raise IngestRunnerError(f"revision '{revision_id}' has no completed extraction to repair.")
    parent_ir = ctx.repo.load_document_ir(parent_id)
    if parent_ir is None:
        raise IngestRunnerError(f"parent extraction '{parent_id}' has no persisted IR.")

    source = revision.get("original_uri") or (artifact.get("canonical_uri") if artifact else None)
    if not source:
        raise IngestRunnerError(f"revision '{revision_id}' has no fetchable URI for re-extraction.")
    resolved_category = resolve_source(str(source)).category

    ctx.report("acquired", message=f"Re-acquiring {len(pages)} page(s) for repair")
    fetched = ctx.services.fetch_bytes(str(source), resolved_category, ctx)

    options = dict(payload.get("repair_options") or {})
    repair_config = _repair_pdf_config(options, pages)
    ctx.job["payload"] = {**payload, "pdf_config": repair_config}
    ctx.job["_revision_id"] = revision_id

    ctx.report("registered", message="Registered repair extraction")
    repair_ir = ctx.services.extract_ir(fetched, resolved_category, ctx)

    request_hash = extraction_request_hash(
        revision_id=revision_id,
        extractor=repair_ir.extractor,
        extractor_version=repair_ir.extractor_version,
        config=repair_config,
        page_selection=pages,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    existing = ctx.repo.extraction_run_by_request_hash(revision_id, request_hash)
    if existing is not None and existing.get("status") == "completed":
        repair_extraction_id = existing["id"]
    else:
        repair_extraction_id = existing["id"] if existing is not None else f"ext_{new_ulid()}"
        if existing is None:
            ctx.repo.insert_extraction_run(
                id=repair_extraction_id,
                revision_id=revision_id,
                extractor=repair_ir.extractor,
                extractor_version=repair_ir.extractor_version,
                extraction_request_hash=request_hash,
                ir_schema_version=IR_SCHEMA_VERSION,
                config=repair_config,
                page_selection=pages,
                parent_extraction_id=parent_id,
                status="running",
                clock=ctx.clock,
            )
        ctx.repo.persist_document_ir(repair_extraction_id, repair_ir)
        ctx.repo.complete_extraction_run(
            repair_extraction_id,
            extraction_result_hash=extraction_result_hash(request_hash, repair_ir),
            health=repair_ir.health.model_dump(mode="json"),
            clock=ctx.clock,
        )

    ctx.report("extracted", message="Composed repaired pages with the parent extraction")
    composed = compose_extraction_runs(parent_ir, repair_ir)
    repaired_pages = sorted({block.page for block in repair_ir.blocks if block.page is not None})
    affected = {unit.unit_id for unit in _units_touching(composed, repaired_pages)}

    return {
        "revision_id": revision_id,
        "parent_extraction_id": parent_id,
        "repair_extraction_id": repair_extraction_id,
        "repaired_pages": repaired_pages,
        "requested_pages": pages,
        "affected_unit_hashes": {
            unit.unit_id: unit.semantic_hash for unit in composed.units if unit.unit_id in affected
        },
        "unaffected_unit_hashes": {
            unit.unit_id: unit.semantic_hash for unit in composed.units if unit.unit_id not in affected
        },
        "consent": dict(consent),
    }


def _repair_pdf_config(options: Mapping[str, Any], pages: list[int]) -> dict[str, Any]:
    config: dict[str, Any] = {"page_range": ",".join(str(page) for page in pages)}
    if options.get("force_ocr"):
        config["force_ocr"] = True
    if options.get("inline_math"):
        config["inline_math"] = True
    if options.get("table_processing"):
        config["table_processing"] = True
    if options.get("use_llm"):
        config["use_llm"] = True
        if options.get("llm_service"):
            config["llm_service"] = options["llm_service"]
    return config


def _validate_page_selection(raw_bytes: bytes, pages: list[int]) -> None:
    """Refuse out-of-range page selections BEFORE any expensive extraction.

    Marker/pypdf failures on a bad range surface as deep, engine-specific
    exceptions (or worse, silently empty extractions); a typed refusal with the
    document's real page count is actionable in the UI. Best-effort: when the
    page count cannot be read (odd/encrypted PDF), extraction proceeds and any
    real problem surfaces through the normal extraction error path."""

    page_count = _pdf_page_count(raw_bytes)
    if page_count is None or not pages:
        return
    beyond = [page for page in pages if page >= page_count]
    if beyond:
        raise IngestRunnerError(
            f"Requested PDF pages up to {max(beyond) + 1}, but the document has "
            f"only {page_count} page(s).",
            code="invalid_page_range",
            details={"page_count": page_count, "requested_max": max(beyond) + 1},
            retryable=False,
        )


def _pdf_page_count(raw_bytes: bytes) -> int | None:
    try:
        import io

        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return None
        return len(reader.pages)
    except Exception:  # noqa: BLE001 — validation is strictly best-effort
        return None


def _normalize_pages(raw: Any) -> list[int]:
    pages: set[int] = set()
    if raw is None:
        return []
    for entry in raw if isinstance(raw, (list, tuple)) else [raw]:
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            start, end = int(entry[0]), int(entry[1])
            pages.update(range(min(start, end), max(start, end) + 1))
        elif isinstance(entry, int) and not isinstance(entry, bool):
            pages.add(entry)
        elif isinstance(entry, str) and entry.strip():
            text = entry.strip()
            if "-" in text:
                start_s, _, end_s = text.partition("-")
                pages.update(range(int(start_s), int(end_s) + 1))
            else:
                pages.add(int(text))
    return sorted(pages)


def _latest_completed_extraction(repo: Repository, revision_id: str) -> str | None:
    runs = [
        run
        for run in repo.extraction_runs_for_revision(revision_id)
        if run.get("status") == "completed" and run.get("parent_extraction_id") is None
    ]
    return runs[-1]["id"] if runs else None


def _units_touching(ir: Any, pages: list[int]) -> list[Any]:
    page_set = set(pages)
    touching: list[Any] = []
    for unit in ir.units:
        if unit.page_start is None:
            continue
        end = unit.page_end if unit.page_end is not None else unit.page_start
        if any(unit.page_start <= page <= end for page in page_set):
            touching.append(unit)
    return touching


def _not_implemented_handler(job_type: str) -> Handler:
    def handler(_ctx: JobContext) -> dict[str, Any]:
        raise NotImplementedError(
            f"job_type '{job_type}' is a validated seam reserved for a later milestone (M3/M4/M6)."
        )

    return handler


def handle_reader_quick_check(ctx: JobContext) -> dict[str, Any]:
    """Author one section-boundary quick check (reader producer slice).

    Interactive-priority, one section per job. Idempotent through the service:
    an existing row for the section (any status) is reused without a model
    call, so a duplicate enqueue or a retry never double-authors."""

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    section_id = str(payload.get("section_id") or "")
    if not extraction_id or not section_id:
        raise IngestRunnerError("reader_quick_check needs extraction_id and section_id.")
    existing = ctx.repo.latest_reader_authored_question(
        extraction_id=extraction_id, section_id=section_id
    )
    if existing is not None:
        return {"question_id": existing["id"], "deduplicated": True}
    ctx.report("authoring", message="Authoring a quick check for this section")
    client = ctx.services.quick_check_client(ctx)
    row = RQC.author_quick_check(
        ctx.repo, client, extraction_id=extraction_id, section_id=section_id, clock=ctx.clock
    )
    return {"question_id": row["id"], "deduplicated": False}


def handle_reader_exercise_import(ctx: JobContext) -> dict[str, Any]:
    """reader_exercise_import: author the learner's selected textbook
    exercise(s) into complete, schedulable PracticeItems.

    Interactive-priority but on the MAIN single-writer lane — unlike
    reader_quick_check this job writes vault YAML, so it must never run
    concurrently with another vault-writing job. Idempotent through the
    service's prompt-level dedupe: a retry after a crash mid-batch skips
    already-written exercises as duplicates instead of double-authoring."""

    from learnloop.content.authoring import exercise_authoring as EX

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    raw_selection = payload.get("raw_selection") or {}
    if not extraction_id or not raw_selection.get("nodes"):
        raise IngestRunnerError("reader_exercise_import needs extraction_id and raw_selection nodes.")
    ctx.report("authoring", message="Authoring the selected exercise(s) into practice items")
    client = ctx.services.exercise_import_client(ctx)
    try:
        return EX.import_exercises(
            ctx.vault_root,
            ctx.repo,
            client,
            extraction_id=extraction_id,
            raw_selection=raw_selection,
            render_view_id=str(payload.get("render_view_id") or "") or None,
            source_id=str(payload.get("source_id") or "") or None,
            revision_id=str(payload.get("revision_id") or "") or None,
            learning_object_hint=str(payload.get("learning_object_hint") or "") or None,
            clock=ctx.clock,
        )
    except EX.ExerciseAuthoringError as exc:
        raise IngestRunnerError(str(exc)) from exc


def handle_practice_expansion(ctx: JobContext) -> dict[str, Any]:
    """practice_expansion: per-LO item generation (reader-first seeding).

    Payload: ``learning_object_ids`` (explicit, from the section→LO provenance
    mapping) + ``reason``. The completed-probe gate is waived — the trigger is
    the learner having READ the material; rung selection and difficulty
    calibration come from the learner claim / mastery through the standard
    generation path. "Nothing needed" is success, not an error."""

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        generate_post_probe_practice_proposal,
    )

    payload = ctx.payload
    lo_ids = [str(lo) for lo in (payload.get("learning_object_ids") or []) if str(lo).strip()]
    source_refs = [ref for ref in (payload.get("source_refs") or []) if isinstance(ref, dict)]
    if not lo_ids:
        raise IngestRunnerError("practice_expansion job requires 'learning_object_ids'.")
    ctx.report("generation", message=f"Generating practice for {len(lo_ids)} learning object(s)")
    client = ctx.services.synthesis_client(ctx)
    try:
        result = generate_post_probe_practice_proposal(
            ctx.vault_root,
            client,
            learning_object_ids=lo_ids,
            require_completed_probe=False,
            target_items_per_lo=3,
            max_new_per_lo=3,
            source_refs=source_refs,
            extra_instructions=(
                "These items seed practice for material the learner just finished reading "
                f"({payload.get('reason') or 'reader_section_completed'}). Ground every item in the "
                "cited source spans. For each item, copy the exact proposal-local ref_id values from "
                "context.source_refs whose learning_object_ids contain that item's learning_object_id "
                "into item.source_ref_ids; do not cite bundles assigned to another Learning Object."
            ),
        )
    except PracticeExpansionError as exc:
        # All targeted LOs already supplied — a legitimate no-op for a trigger.
        return {"generated": 0, "skipped_reason": str(exc)}
    return {
        "patch_id": result.patch_id,
        "generated": result.plan.requested_new_items,
        "rung_violations": result.rung_violations,
    }


def handle_goal_population(ctx: JobContext) -> dict[str, Any]:
    """Generate and apply the missing practicable supply for one active goal."""

    from learnloop.content.proposals.patches import PatchApplicationError
    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_goal_practice_plan,
        generate_goal_practice_proposal,
    )
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.vault.loader import load_vault

    goal_id = str(ctx.payload.get("goal_id") or "")
    if not goal_id:
        raise IngestRunnerError(
            "goal_population job requires a 'goal_id'."
        )
    vault = load_vault(ctx.vault_root)
    sync_vault_state(vault, ctx.repo)
    goal = next(
        (
            candidate
            for candidate in vault.goals
            if candidate.id == goal_id and candidate.status == "active"
        ),
        None,
    )
    if goal is None:
        raise IngestRunnerError(
            f"Goal {goal_id} does not exist or is not active.",
            code="invalid_goal",
        )
    try:
        plan, at_risk_facets = build_goal_practice_plan(
            vault,
            ctx.repo,
            goal,
            target_items_per_lo=5,
            max_new_per_lo=3,
        )
    except PracticeExpansionError as exc:
        raise IngestRunnerError(
            str(exc), code="invalid_generation_request"
        ) from exc
    if not plan.targets:
        return {
            "goal_id": goal_id,
            "generated": 0,
            "applied_count": 0,
            "skipped_reason": "Goal already has enough practicable items.",
        }
    ctx.report(
        "generation",
        message=f"Generating practice for {goal.title}",
    )
    client = ctx.services.synthesis_client(ctx)
    try:
        result = generate_goal_practice_proposal(
            ctx.vault_root,
            client,
            goal_id=goal_id,
            target_items_per_lo=5,
            max_new_per_lo=3,
        )
    except PracticeExpansionError as exc:
        raise IngestRunnerError(
            str(exc), code="goal_population_failed"
        ) from exc
    ctx.report(
        "applying",
        message=f"Adding generated practice to {goal.title}",
    )
    try:
        applied = accept_items(
            ctx.vault_root,
            result.patch_id,
            clock=ctx.clock,
        )
    except PatchApplicationError as exc:
        raise IngestRunnerError(
            str(exc), code="goal_population_apply_failed"
        ) from exc
    return {
        "goal_id": goal_id,
        "proposal_id": result.patch_id,
        "generated": result.plan.requested_new_items,
        "applied_count": applied.applied_count,
        "at_risk_facets": at_risk_facets,
    }


def handle_question_promotion(ctx: JobContext) -> dict[str, Any]:
    """Run one persisted Open-question → practice request.

    Analysis and authoring use separate routed clients. Every terminal failure
    is copied onto the domain request before the generic ingest runner records
    its own job error, so the Open questions UI can explain and retry it.
    """

    from learnloop.ai.errors import CodexTurnTimeout, CodexUnavailable
    event_id = str(ctx.payload.get("event_id") or "")
    if not event_id:
        raise IngestRunnerError("question_promotion job requires an 'event_id'.")
    request = ctx.repo.question_promotion_request(event_id)
    if request is None:
        raise IngestRunnerError(
            f"question promotion request {event_id!r} does not exist."
        )

    def stage(name: str) -> None:
        ctx.repo.update_question_promotion_request(
            event_id, status="running", stage=name, clock=ctx.clock
        )
        ctx.report(name, message=f"Question promotion: {name}")

    def fail(code: str, exc: BaseException, *, retryable: bool) -> IngestRunnerError:
        message = str(exc) or exc.__class__.__name__
        ctx.repo.update_question_promotion_request(
            event_id,
            status="failed",
            stage="failed",
            error_code=code,
            error_message=message,
            retryable=retryable,
            clock=ctx.clock,
        )
        ctx.repo.bump_queue_revision(clock=ctx.clock)
        return IngestRunnerError(
            message,
            code=code,
            details={
                "event_id": event_id,
                "exception_type": exc.__class__.__name__,
            },
            retryable=retryable,
        )

    stage("analysis")
    try:
        analysis_client = ctx.services.promotion_analysis_client(ctx)
        result = promote_tutor_question(
            ctx.vault_root,
            analysis_client,
            event_id=event_id,
            intent=str(request["intent"]),
            subject_id=request.get("subject_id"),
            learning_object_id=request.get("learning_object_id"),
            authoring_client_factory=lambda: ctx.services.promotion_authoring_client(ctx),
            progress=stage,
            clock=ctx.clock,
        )
    except PromotionNoItemError as exc:
        raise fail("no_practice_item", exc, retryable=True) from exc
    except PromotionError as exc:
        raise fail("validation_error", exc, retryable=False) from exc
    except CodexTurnTimeout as exc:
        raise fail("provider_timeout", exc, retryable=True) from exc
    except TimeoutError as exc:
        raise fail("provider_timeout", exc, retryable=True) from exc
    except CodexUnavailable as exc:
        raise fail("provider_unavailable", exc, retryable=True) from exc
    except IngestRunnerError as exc:
        raise fail(exc.code, exc, retryable=exc.retryable) from exc
    except ValueError as exc:
        raise fail("invalid_structured_output", exc, retryable=True) from exc
    except Exception as exc:  # noqa: BLE001 - domain request must not stay "running"
        raise fail("promotion_failed", exc, retryable=True) from exc

    route = str(result.get("route") or "")
    stage_name = "review" if route == "review_required" else "ready"
    ctx.repo.update_question_promotion_request(
        event_id,
        status="completed",
        stage=stage_name,
        promotion_route=route,
        error_code=None,
        error_message=None,
        retryable=False,
        clock=ctx.clock,
    )
    # The promotion service bumps on the actual queue mutation; bump once more
    # for request-state consumers (review/ready chips) even on diagnostic routes.
    ctx.repo.bump_queue_revision(clock=ctx.clock)
    return {
        "question_event_id": event_id,
        "route": route,
        "promotion": result,
    }


def handle_rung_variant(ctx: JobContext) -> dict[str, Any]:
    """rung_variant: author one learner-requested easier/harder sibling item.

    The evidence package was written synchronously at request time; this job is
    only the generation half. Payload: ``request_id``. The service owns the
    request-row status transitions (applied / review_required / failed)."""

    from learnloop.content.authoring.rung_variants import RungVariantError, generate_rung_variant

    request_id = str(ctx.payload.get("request_id") or "")
    if not request_id:
        raise IngestRunnerError("rung_variant job requires a 'request_id'.")
    ctx.report("generation", message="Authoring the requested variant")
    client = ctx.services.rung_variant_client(ctx)
    try:
        result = generate_rung_variant(
            ctx.vault_root, client, request_id=request_id, clock=ctx.clock
        )
    except RungVariantError as exc:
        raise IngestRunnerError(str(exc)) from exc
    if result.get("status") == "failed":
        request = ctx.repo.rung_variant_request(request_id) or {}
        reason = str(request.get("failure_reason") or "Rung variant generation failed.")
        raise IngestRunnerError(
            reason,
            code="rung_variant_failed",
            details={"request_id": request_id, "result": result},
            retryable=True,
        )
    return result


def handle_concept_animation(ctx: JobContext) -> dict[str, Any]:
    """concept_animation: author + validate + render one explainer scene.

    Payload: ``animation_id``. The service owns the row's status machine
    (completed / failed with stage + stderr); consent was checked at request
    time before the row existed."""

    from learnloop.content.authoring.concept_animation import (
        ConceptAnimationError,
        generate_concept_animation,
    )

    animation_id = str(ctx.payload.get("animation_id") or "")
    if not animation_id:
        raise IngestRunnerError("concept_animation job requires an 'animation_id'.")
    ctx.report("generation", message="Authoring the explainer scene")
    client = ctx.services.animation_client(ctx)
    try:
        row = generate_concept_animation(
            ctx.vault_root,
            client,
            animation_id=animation_id,
            renderer=ctx.services.animation_renderer,
            clock=ctx.clock,
        )
    except ConceptAnimationError as exc:
        raise IngestRunnerError(str(exc), code=exc.code) from exc
    # Compact job result: the status RPC serves the full row (code, stderr).
    return {
        "animation_id": row["id"],
        "concept_id": row["concept_id"],
        "status": row["status"],
        "video_file_name": row.get("video_file_name"),
        "failure_stage": row.get("failure_stage"),
    }


DEFAULT_HANDLERS: dict[str, Handler] = {
    "import": handle_import,
    "legacy_ingest": handle_legacy_ingest,
    "exam_ingest": handle_legacy_ingest,
    "inventory": handle_inventory,
    "bootstrap_synthesis": handle_bootstrap_synthesis,
    "append_synthesis": handle_append_synthesis,
    "extraction_repair": handle_extraction_repair,
    "reader_quick_check": handle_reader_quick_check,
    "reader_exercise_import": handle_reader_exercise_import,
    "practice_expansion": handle_practice_expansion,
    "goal_population": handle_goal_population,
    "question_promotion": handle_question_promotion,
    "rung_variant": handle_rung_variant,
    "concept_animation": handle_concept_animation,
}



_LEGACY_JOB_TYPES = ("legacy_ingest", "exam_ingest")
# Job types whose completion can change vault content (an applied study map or
# canonical note). The sidecar must reload its in-memory vault after one of
# these finishes in the background drain, or screens that read the loaded vault
# (Today, knowledge map) keep serving the pre-apply snapshot.
APPLYING_JOB_TYPES = (
    "legacy_ingest",
    "exam_ingest",
    "bootstrap_synthesis",
    "append_synthesis",
    # Reader-driven progressive generation auto-applies grounded items.
    "practice_expansion",
    # Learner-requested easier/harder variants auto-apply when grounded.
    "rung_variant",
    # Open-question promotions may materialize a note and auto-apply practice.
    "question_promotion",
    # Reader-selected textbook exercises become vault practice items directly.
    "reader_exercise_import",
    # Goal-wizard population applies generated practice directly.
    "goal_population",
)
_ACTIVE_STATUSES = {"queued", "running", "waiting_for_input"}
_RECENT_LIMIT = 30

# Quick-add build batches drain ahead of bulk import/inventory batches (§1). The
# drain orders by batch priority DESC first, so anything above the default 0
# jumps the queue between checkpoints. Bulk batches stay at 0.
QUICK_ADD_PRIORITY = 100
_PARALLEL_JOB_TYPES = ("reader_quick_check",)
_QUICK_CHECK_WORKERS = 3


class ActiveIngestJobError(RuntimeError):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Ingest job {job_id} is already running.")


class DurableIngestJobs:
    """Enqueues single-source ingests into the durable queue and reads their state."""

    def __init__(self) -> None:
        self._runner: IngestRunner | None = None
        self._lock = threading.RLock()
        self._reloaded: set[str] = set()
        self._background = True
        self._poll_interval = 1.0
        self._worker_thread: threading.Thread | None = None
        self._quick_check_threads: list[threading.Thread] = []
        self._stop = threading.Event()
        self._work_available = threading.Event()
        self._quick_check_work_available = threading.Event()
        # Demand-paged reader synthesis: the same worker thread drains queued
        # reader_background_requests with a real model client (spec §6.4 — the
        # drain was previously never invoked, so requests sat queued forever).
        self._reader_synth_client_factory: Any = None
        self._reader_client: Any = None
        self._reader_client_checked = False

    # -- wiring ------------------------------------------------------------

    def bind(
        self,
        repository: Repository,
        vault_root: Path,
        *,
        clock: Clock | None = None,
        services: RunnerServices | None = None,
        lease_ttl_seconds: int = 120,
        heartbeat_interval_seconds: float = 15,
        poll_interval_seconds: float = 1.0,
        background: bool | None = None,
        reader_synth_client_factory: Any = None,
    ) -> None:
        """Attach the wrapper to a loaded vault. Called from SidecarContext.load."""

        with self._lock:
            self._reader_synth_client_factory = reader_synth_client_factory
            self._reader_client = None
            self._reader_client_checked = False
            same_vault = self._runner is not None and self._runner.vault_root.resolve() == Path(
                vault_root
            ).resolve()
            if same_vault:
                # SidecarContext.reload() refreshes the loaded vault after an
                # applying job completes. The drain thread may already be inside
                # the next Codex call, so replacing its runner here would orphan
                # that call's in-memory interrupt handle from `kill-codex`.
                # The existing Repository remains valid for the same SQLite file.
                runner = self._runner
                assert runner is not None
                if clock is not None:
                    runner.clock = clock
                if services is not None:
                    runner.services = services
                runner.lease_ttl_seconds = lease_ttl_seconds
                runner.heartbeat_interval_seconds = heartbeat_interval_seconds
            else:
                runner = IngestRunner(
                    repository,
                    vault_root=vault_root,
                    worker_id=f"sidecar-{os.getpid()}",
                    clock=clock,
                    services=services,
                    lease_ttl_seconds=lease_ttl_seconds,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )
                self._runner = runner
            # A same-vault SidecarContext.reload() must not silently replace an
            # explicitly foreground-bound test/CLI host with a background
            # thread. Omitted means "preserve" on rebind and "background" on
            # first bind.
            if not same_vault or background is not None:
                self._background = True if background is None else background
            self._poll_interval = poll_interval_seconds
        # Recover anything a prior process left mid-flight before draining.
        if not same_vault:
            runner.recover_stale_leases()
        # Jobs that finished before this bind are already reflected in the vault
        # load that accompanies it; only jobs completing AFTER this point should
        # trigger a reload from the batch-polling handlers.
        for job in runner.repo.ingest_jobs_by_types(APPLYING_JOB_TYPES):
            if job["status"] == "completed":
                self._reloaded.add(job["id"])

    def _require_runner(self) -> IngestRunner:
        if self._runner is None:
            raise RuntimeError("Ingest jobs are not bound to a vault yet.")
        return self._runner

    # -- sidecar-facing API ------------------------------------------------

    def start(
        self,
        vault_root: Path,
        source: str,
        subject_id: str,
        mode: Literal["canonical", "exam"],
        pdf_engine: str | None = None,
    ) -> dict[str, Any]:
        runner = self._require_runner()
        with self._lock:
            active = self._active_job_locked(runner)
            if active is not None:
                raise ActiveIngestJobError(active["id"])
            job_type = "exam_ingest" if mode == "exam" else "legacy_ingest"
            # v2-lite journey (§6.1 / §15 M3.5): extract once into a Document IR
            # (import), then run legacy synthesis over the IR's display rendering.
            # The legacy job depends on the import job, so synthesis reuses the
            # extraction instead of re-fetching, and the IngestScreen form now
            # feeds better extraction + unit selection into proposals.
            # Exam papers are assessment material, not reading material — they
            # default OUT of the reader loop (per-source flag, owner-overridable).
            import_payload: dict[str, Any] = {"source": source, "subject_id": subject_id}
            if mode == "exam":
                import_payload["reader_enabled"] = False
            if pdf_engine in ("marker", "pypdf"):
                # An explicit engine choice is part of the extraction identity;
                # "auto" stays implicit so unchanged sources keep their cache.
                import_payload["pdf_config"] = {"engine": pdf_engine}
            batch_id = runner.enqueue_batch(
                "legacy_ingest",
                [
                    JobSpec("import", import_payload),
                    JobSpec(
                        job_type,
                        {"source": source, "subject_id": subject_id, "mode": mode},
                        depends_on=(0,),
                    ),
                ],
                subject_id=subject_id,
            )
            job = self._legacy_job_for_batch(runner, batch_id)
        self._ensure_worker()
        return _compat(job)

    def get(self, job_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        return _compat(job) if job is not None else None

    def list(self) -> list[dict[str, Any]]:
        runner = self._require_runner()
        jobs = runner.repo.ingest_jobs_by_types(_LEGACY_JOB_TYPES, limit=_RECENT_LIMIT)
        return [_compat(job) for job in jobs]

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        if job is None:
            return None
        if _compat_status(job["status"]) in {"queued", "running"}:
            runner.cancel_batch(job["batch_id"])
            job = runner.repo.get_ingest_job(job_id)
        return _compat(job) if job is not None else None

    def needs_reload(self, job_id: str) -> bool:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        return bool(
            job
            and effective_ingest_job_status(job) == "completed"
            and job_id not in self._reloaded
        )

    def mark_reloaded(self, job_id: str) -> None:
        self._reloaded.add(job_id)

    def shutdown(self) -> None:
        self._stop.set()
        # Wake idle workers so shutdown never waits for the poll timeout.
        self._work_available.set()
        self._quick_check_work_available.set()
        thread = self._worker_thread
        if thread is not None:
            thread.join(timeout=2)
        for quick_thread in self._quick_check_threads:
            quick_thread.join(timeout=2)

    # -- durable batch API (Source library / Batch progress screens) -------

    def enqueue_import(
        self,
        sources: list[str],
        *,
        subject_id: str | None = None,
        inventory: bool = False,
        estimate: dict[str, Any] | None = None,
        page_selection: list[int] | None = None,
        page_selections: dict[str, list[int]] | None = None,
        reader_disabled_sources: set[str] | frozenset[str] | None = None,
        pdf_engine: str | None = None,
        priority: int = 0,
    ) -> str:
        """Enqueue an Import (or Import & inventory) batch (§6.1). One import job
        per source; when ``inventory`` is set, a dependent inventory job is queued
        per source. The handler derives extraction + units from the completed
        import dependency, so the public shorthand is directly executable.

        A build-plan ``estimate`` (when a batch is started from a plan) is
        snapshotted onto each import job's payload (§8.6.2)."""

        runner = self._require_runner()
        specs: list[JobSpec] = []
        for source in sources:
            import_index = len(specs)
            payload: dict[str, Any] = {"source": source}
            source_pages = (page_selections or {}).get(source, page_selection)
            if source_pages is not None:
                payload["page_selection"] = source_pages
            if reader_disabled_sources and source in reader_disabled_sources:
                payload["reader_enabled"] = False
            if pdf_engine in ("marker", "pypdf"):
                # See start(): explicit engines join the extraction identity.
                payload["pdf_config"] = {"engine": pdf_engine}
            if estimate is not None:
                payload["estimate"] = estimate
            specs.append(JobSpec("import", payload))
            if inventory:
                specs.append(JobSpec("inventory", {"source": source}, depends_on=(import_index,)))
        workflow = "import_inventory" if inventory else "import"
        batch_id = runner.enqueue_batch(workflow, specs, subject_id=subject_id, priority=priority)
        self._ensure_worker()
        return batch_id

    def enqueue_extraction_repair(
        self,
        *,
        revision_id: str,
        pages: list,
        repair_options: dict[str, Any] | None,
        consent: dict[str, Any],
        parent_extraction_id: str | None = None,
        subject_id: str | None = None,
    ) -> str:
        """Enqueue a consent-gated extraction-repair batch (§2.5)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "extraction_repair",
            [
                JobSpec(
                    "extraction_repair",
                    {
                        "revision_id": revision_id,
                        "pages": pages,
                        "repair_options": repair_options or {},
                        "consent": consent,
                        "parent_extraction_id": parent_extraction_id,
                    },
                )
            ],
            subject_id=subject_id,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str) -> str:
        """Enqueue one section's quick-check authoring (reader producer slice).

        Interactive priority (quick-add band) so a reader-initiated question
        drains ahead of bulk batches; the handler is idempotent per section so
        duplicate enqueues while one is queued/running resolve without a second
        model call."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "reader_quick_check",
            [JobSpec("reader_quick_check", {"extraction_id": extraction_id, "section_id": section_id})],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_exercise_import(
        self,
        *,
        extraction_id: str,
        raw_selection: dict[str, Any],
        render_view_id: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        learning_object_hint: str | None = None,
    ) -> str:
        """Enqueue authoring of the learner's selected textbook exercise(s).

        Interactive priority (the learner is waiting on it), but on the main
        single-writer lane — the handler writes vault YAML, so it must not
        join the parallel read-only quick-check lane."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "reader_exercise_import",
            [
                JobSpec(
                    "reader_exercise_import",
                    {
                        "extraction_id": extraction_id,
                        "raw_selection": dict(raw_selection),
                        "render_view_id": render_view_id,
                        "source_id": source_id,
                        "revision_id": revision_id,
                        "learning_object_hint": learning_object_hint,
                    },
                )
            ],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_practice_expansion(
        self,
        *,
        learning_object_ids: list[str],
        subject_id: str | None = None,
        reason: str | None = None,
        source_refs: list[dict[str, Any]] | None = None,
    ) -> str:
        """Enqueue per-LO practice generation (reader-first progressive seeding).

        Background priority (default band): generation after a section completes
        must never starve reader quick-checks or interactive quick-add builds."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "practice_expansion",
            [
                JobSpec(
                    "practice_expansion",
                    {
                        "learning_object_ids": list(learning_object_ids),
                        "reason": reason or "reader_section_completed",
                        "source_refs": list(source_refs or []),
                    },
                )
            ],
            subject_id=subject_id,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_goal_population(self, *, goal_id: str) -> str:
        """Enqueue durable goal-scoped practice authoring from the wizard."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "goal_population",
            [JobSpec("goal_population", {"goal_id": goal_id})],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_rung_variant(self, *, request_id: str, subject_id: str | None = None) -> str:
        """Enqueue one learner-requested variant authoring (interactive band —
        the learner is waiting on it, like a quick-add build)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "rung_variant",
            [JobSpec("rung_variant", {"request_id": request_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_question_promotion(
        self,
        *,
        event_id: str,
        subject_id: str | None = None,
    ) -> str:
        """Enqueue a durable Open-question analysis/authoring request."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "question_promotion",
            [JobSpec("question_promotion", {"event_id": event_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_concept_animation(self, *, animation_id: str, subject_id: str | None = None) -> str:
        """Enqueue one explainer-animation generation (interactive band — the
        learner clicked generate and is watching the status)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "concept_animation",
            [JobSpec("concept_animation", {"animation_id": animation_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_inventory(
        self,
        *,
        extraction_id: str,
        units: list[dict[str, Any]],
        subject_id: str | None = None,
        source_set_id: str | None = None,
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        unlimited_token_budget: bool = False,
        priority: int = 0,
    ) -> str:
        """Enqueue a role-aware unit-inventory batch (§7). Cached units cost zero
        tokens; only semantic-hash-changed units re-inventory."""

        runner = self._require_runner()
        payload: dict[str, Any] = {"extraction_id": extraction_id, "units": units}
        if input_budget_tokens is not None:
            payload["input_budget_tokens"] = input_budget_tokens
        if output_budget_tokens is not None:
            payload["output_budget_tokens"] = output_budget_tokens
        if unlimited_token_budget:
            payload["unlimited_token_budget"] = True
        batch_id = runner.enqueue_batch(
            "import_inventory",
            [JobSpec("inventory", payload)],
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_quick_add_build(
        self,
        *,
        extraction_id: str,
        units: list[dict[str, Any]],
        source_set_id: str,
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        mode: str = "auto",
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        unlimited_token_budget: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue the Quick-add build batch (§1): inventory(selected units) then
        bootstrap_synthesis over the freshly-created source set, as one batch that
        drains ahead of bulk work. The synthesis job depends on the inventory job,
        so gates only run once the selected units carry inventories."""

        runner = self._require_runner()
        inventory_payload: dict[str, Any] = {"extraction_id": extraction_id, "units": units}
        if input_budget_tokens is not None:
            inventory_payload["input_budget_tokens"] = input_budget_tokens
        if output_budget_tokens is not None:
            inventory_payload["output_budget_tokens"] = output_budget_tokens
        if unlimited_token_budget:
            inventory_payload["unlimited_token_budget"] = True
        synthesis_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "mode": mode,
            # Quick Add's promise is a usable study map after its one explicit
            # confirmation, not a second hidden proposal-acceptance step.
            "apply": True,
        }
        if unlimited_token_budget:
            synthesis_payload["unlimited_token_budget"] = True
        batch_id = runner.enqueue_batch(
            "bootstrap_synthesis",
            [
                JobSpec("inventory", inventory_payload),
                JobSpec("bootstrap_synthesis", synthesis_payload, depends_on=(0,)),
            ],
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_source_set_build(
        self,
        *,
        members: list[dict[str, Any]],
        source_set_id: str,
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        mode: str = "auto",
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        synthesis_budgets: dict[str, int] | None = None,
        unlimited_token_budget: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue a study-map build batch for an EXISTING source set (§1/§8): one
        inventory job per member (over its scoped units) followed by a
        bootstrap_synthesis job that depends on all of them, so gates only run once
        every member's units carry inventories. This is the multi-member, in-app
        counterpart to :meth:`enqueue_quick_add_build` (single-source Quick add) —
        it lets a collection assembled in the app synthesize a study map without the
        CLI, surfacing as one durable Activity batch.

        Each ``members`` entry is ``{"extraction_id": str, "units": [...]}`` where
        units are ``[{unit_id, role, profile?}]`` (the inventory job's shape)."""

        runner = self._require_runner()
        if not members:
            raise ValueError("a study-map build needs at least one member.")
        specs: list[JobSpec] = []
        for member in members:
            inventory_payload: dict[str, Any] = {
                "extraction_id": member["extraction_id"],
                "units": member["units"],
            }
            if input_budget_tokens is not None:
                inventory_payload["input_budget_tokens"] = input_budget_tokens
            if output_budget_tokens is not None:
                inventory_payload["output_budget_tokens"] = output_budget_tokens
            if unlimited_token_budget:
                inventory_payload["unlimited_token_budget"] = True
            specs.append(JobSpec("inventory", inventory_payload))
        synthesis_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "mode": mode,
            # Synthesizing a collection is itself the learner's explicit confirmation
            # (the "synthesize →" click), so apply so it yields a usable study map —
            # mirroring Quick add rather than leaving a second review step.
            "apply": True,
        }
        if synthesis_budgets:
            synthesis_payload["synthesis_budgets"] = dict(synthesis_budgets)
        if unlimited_token_budget:
            synthesis_payload["unlimited_token_budget"] = True
        specs.append(
            JobSpec("bootstrap_synthesis", synthesis_payload, depends_on=tuple(range(len(members))))
        )
        batch_id = runner.enqueue_batch(
            "bootstrap_synthesis",
            specs,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_source_set_append(
        self,
        *,
        members: list[dict[str, Any]],
        source_set_id: str,
        new_revision_ids: list[str] | None = None,
        change_kind: str = "source_added",
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        synthesis_budgets: dict[str, int] | None = None,
        unlimited_token_budget: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue a bounded-neighborhood APPEND batch for a collection whose subject
        already carries a study map (§10). One inventory job per NEW (not-yet-synthesized)
        member — same scoping/roles shape as the bootstrap build — followed by a single
        ``append_synthesis`` job that depends on all of them and reconciles ONLY the new
        material against the existing map through the bounded affected neighborhood. The
        map is never resent or rebuilt; ``new_revision_ids`` pins the append scope.

        The append counterpart to :meth:`enqueue_source_set_build`. ``members`` may be
        empty (nothing new to inventory), in which case the append job runs alone and
        reconciles the set's current membership (cache-reused when unchanged)."""

        runner = self._require_runner()
        specs: list[JobSpec] = []
        for member in members:
            inventory_payload: dict[str, Any] = {
                "extraction_id": member["extraction_id"],
                "units": member["units"],
            }
            if input_budget_tokens is not None:
                inventory_payload["input_budget_tokens"] = input_budget_tokens
            if output_budget_tokens is not None:
                inventory_payload["output_budget_tokens"] = output_budget_tokens
            if unlimited_token_budget:
                inventory_payload["unlimited_token_budget"] = True
            specs.append(JobSpec("inventory", inventory_payload))
        append_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "change_kind": change_kind,
            "new_revision_ids": list(new_revision_ids or []),
            # The "synthesize →" click is the learner's explicit confirmation, so
            # routine span/assessment attachments auto-apply (§10.3); everything else
            # stays a pending review proposal.
            "apply": True,
        }
        if synthesis_budgets:
            append_payload["synthesis_budgets"] = dict(synthesis_budgets)
        if unlimited_token_budget:
            append_payload["unlimited_token_budget"] = True
        specs.append(
            JobSpec("append_synthesis", append_payload, depends_on=tuple(range(len(members))))
        )
        batch_id = runner.enqueue_batch(
            "append_synthesis",
            specs,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def retry_synthesis(
        self,
        batch_id: str,
        *,
        synthesis_budgets: dict[str, int] | None = None,
        reuse_candidate: bool = False,
        repair_candidate: bool = False,
        repair_ops: list[dict[str, Any]] | None = None,
        unlimited_token_budget: bool = False,
    ) -> dict[str, Any]:
        """Retry only a failed synthesis stage with revised execution ceilings.

        Inventory dependencies must already be complete. Their durable outputs
        remain in place and are neither requeued nor regenerated.

        ``reuse_candidate`` finishes the pipeline from the failed attempt's
        preserved merged candidate — normalization/gates/persistence re-run with
        ZERO model calls. Requires the failed job to have recorded a preserved
        candidate's synthesis run id in its error details.

        ``repair_candidate`` additionally derives mechanically-safe repair ops
        over that candidate before the gates rerun (dangling criterion-id
        dependencies and similar); ``repair_ops`` applies explicit user- or
        agent-authored ops. Both require ``reuse_candidate``.
        """

        runner = self._require_runner()
        jobs = runner.repo.ingest_jobs_for_batch(batch_id)
        synthesis_jobs = [
            job for job in jobs
            if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
            and job["status"] in {"failed", "blocked", "cancelled"}
        ]
        if len(synthesis_jobs) != 1:
            raise ValueError("batch must contain exactly one unfinished synthesis job")
        if any(job["job_type"] == "inventory" and job["status"] != "completed" for job in jobs):
            raise ValueError("all inventory jobs must be completed before retrying synthesis")

        synthesis_job = synthesis_jobs[0]
        payload = dict(synthesis_job.get("payload") or {})
        payload.pop("reuse_candidate", None)
        payload.pop("synthesis_run_id", None)
        payload.pop("repair_candidate", None)
        payload.pop("repair_ops", None)
        payload["unlimited_token_budget"] = unlimited_token_budget
        if (repair_candidate or repair_ops) and not reuse_candidate:
            raise ValueError("candidate repair requires reuse_candidate")
        if reuse_candidate:
            details = ((synthesis_job.get("error") or {}).get("details")) or {}
            synthesis_run_id = str(details.get("synthesis_run_id") or "")
            if not details.get("candidate_preserved") or not synthesis_run_id:
                raise ValueError(
                    "the failed synthesis attempt preserved no candidate; retry synthesis instead"
                )
            run = runner.repo.synthesis_run(synthesis_run_id)
            if run is None or not run.get("candidate_output"):
                raise ValueError(
                    "the preserved candidate is no longer available; retry synthesis instead"
                )
            payload["reuse_candidate"] = True
            payload["synthesis_run_id"] = synthesis_run_id
            if repair_candidate:
                payload["repair_candidate"] = True
            if repair_ops:
                payload["repair_ops"] = [dict(op) for op in repair_ops]
        if synthesis_budgets:
            payload["synthesis_budgets"] = {
                **dict(payload.get("synthesis_budgets") or {}),
                **synthesis_budgets,
            }
        runner.repo.update_ingest_job_payload(synthesis_job["id"], payload)
        runner.resume_batch(batch_id)
        self._ensure_worker()
        return self.get_batch(batch_id) or {}

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        batch = runner.repo.get_ingest_batch(batch_id)
        if batch is None:
            return None
        return _batch_view(batch, runner.repo.ingest_jobs_for_batch(batch_id), runner.repo)

    def list_batches(self, limit: int = _RECENT_LIMIT) -> list[dict[str, Any]]:
        runner = self._require_runner()
        batches = runner.repo.list_ingest_batches(limit=limit)
        jobs_by_batch = runner.repo.ingest_jobs_for_batches(
            batch["id"] for batch in batches
        )
        dependencies_by_job = runner.repo.ingest_job_dependencies_for_jobs(
            job["id"]
            for jobs in jobs_by_batch.values()
            for job in jobs
        )
        rung_requests_by_id = runner.repo.rung_variant_requests(
            request_id
            for jobs in jobs_by_batch.values()
            for job in jobs
            if (request_id := _failed_rung_request_id(job)) is not None
        )
        return [
            _batch_view(
                batch,
                jobs_by_batch.get(batch["id"], []),
                runner.repo,
                dependencies_by_job=dependencies_by_job,
                rung_requests_by_id=rung_requests_by_id,
            )
            for batch in batches
        ]

    def cancel_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        if runner.repo.get_ingest_batch(batch_id) is None:
            return None
        runner.cancel_batch(batch_id)
        return self.get_batch(batch_id)

    def interrupt_codex(self, job_id: str | None = None) -> dict[str, Any]:
        """Interrupt one live Codex call while keeping the sidecar process alive."""

        runner = self._require_runner()
        active = runner.active_interruptible_jobs()
        if job_id is None:
            if not active:
                raise ValueError("No interruptible Codex ingest call is running.")
            if len(active) > 1:
                ids = ", ".join(job["id"] for job in active)
                raise ValueError(f"More than one Codex call is running; pass a job id: {ids}")
            selected = active[0]
        else:
            selected = next((job for job in active if job["id"] == job_id), None)
            if selected is None:
                job = runner.repo.get_ingest_job(job_id)
                if job is None:
                    raise ValueError(f"Ingest job '{job_id}' was not found.")
                if job.get("status") != "running":
                    raise ValueError(f"Ingest job '{job_id}' is {job.get('status')}, not running.")
                raise ValueError(f"Ingest job '{job_id}' has no interruptible Codex call attached.")
        if not runner.interrupt_job(selected["id"]):
            raise ValueError(f"Codex call for ingest job '{selected['id']}' already finished.")
        return {
            "job_id": selected["id"],
            "batch_id": selected["batch_id"],
            "job_type": selected["job_type"],
            "interrupted": True,
        }

    def resume_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        if runner.repo.get_ingest_batch(batch_id) is None:
            return None
        runner.resume_batch(batch_id)
        self._ensure_worker()
        return self.get_batch(batch_id)

    # -- worker host -------------------------------------------------------

    def drain_foreground(self) -> int:
        """Drain the queue synchronously (tests + CLI-less contexts)."""

        return self._require_runner().drain()

    def _ensure_worker(self) -> None:
        if not self._background:
            self.drain_foreground()
            return
        with self._lock:
            self._stop.clear()
            # An existing worker may be waiting between drain attempts. Signal
            # before checking thread liveness so enqueue-to-claim has no polling
            # delay; newly started workers simply consume the harmless signal.
            self._work_available.set()
            self._quick_check_work_available.set()
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(
                    target=self._worker_loop, name="learnloop-ingest-drain", daemon=True
                )
                self._worker_thread.start()
            self._quick_check_threads = [
                thread for thread in self._quick_check_threads if thread.is_alive()
            ]
            for index in range(len(self._quick_check_threads), _QUICK_CHECK_WORKERS):
                quick_thread = threading.Thread(
                    target=self._quick_check_worker_loop,
                    name=f"learnloop-quick-check-{index + 1}",
                    daemon=True,
                )
                self._quick_check_threads.append(quick_thread)
                quick_thread.start()

    def _worker_loop(self) -> None:
        runner = self._runner
        if runner is None:
            return
        idle_rounds = 0
        while not self._stop.is_set():
            self._work_available.clear()
            try:
                ran = runner.drain(
                    eligible_job_types=tuple(
                        job_type
                        for job_type in runner.handlers
                        if job_type not in _PARALLEL_JOB_TYPES
                    ),
                    compatible_running_job_types=_PARALLEL_JOB_TYPES,
                )
            except Exception:  # noqa: BLE001 — the drain thread must never die silently on one bad job
                ran = 0
            try:
                ran += self._drain_reader_requests(runner)
            except Exception:  # noqa: BLE001 — reader synthesis must never kill the ingest drain
                pass
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            if idle_rounds >= 3 and self._active_job_locked(runner) is None:
                break
            if ran == 0:
                self._work_available.wait(timeout=self._poll_interval)

    def _quick_check_worker_loop(self) -> None:
        """Drain independent quick checks beside the serialized vault writer.

        Each job resolves its own provider client, so up to three Codex calls can
        progress independently. Quick checks only write durable SQLite rows and
        never mutate vault YAML, which keeps the single-writer invariant intact.
        """

        runner = self._runner
        if runner is None:
            return
        idle_rounds = 0
        while not self._stop.is_set():
            self._quick_check_work_available.clear()
            try:
                ran = runner.drain(
                    max_jobs=1,
                    eligible_job_types=_PARALLEL_JOB_TYPES,
                    allow_parallel=True,
                    max_parallel=_QUICK_CHECK_WORKERS,
                )
            except Exception:  # noqa: BLE001 — one worker must not kill the lane
                ran = 0
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            active = runner.repo.ingest_jobs_by_types(_PARALLEL_JOB_TYPES)
            if idle_rounds >= 3 and not any(
                job["status"] in _ACTIVE_STATUSES for job in active
            ):
                break
            if ran == 0:
                self._quick_check_work_available.wait(timeout=self._poll_interval)

    # -- demand-paged reader synthesis drain (spec §6.4) --------------------

    def kick_reader_drain(self) -> None:
        """Ensure queued demand-paged reader requests get drained.

        Background mode starts (or keeps) the worker thread; foreground mode
        (tests, CLI-less contexts) drains once synchronously. Called by the
        reader handlers whenever a request may have been enqueued — a nudge,
        so it never raises into the RPC whose capture already succeeded."""

        runner = self._runner
        if runner is None:
            return
        if not self._background:
            try:
                self._drain_reader_requests(runner)
            except Exception:  # noqa: BLE001 — the nudge must not fail the capture RPC
                pass
            return
        # Re-probe provider readiness for each drain burst: the provider may
        # have come up since the last (failed) resolution.
        with self._lock:
            self._reader_client_checked = False
        self._ensure_worker()

    def _drain_reader_requests(self, runner: IngestRunner) -> int:
        """Drain queued reader requests with a real synthesize client.

        Provider unavailable → requests stay ``queued`` (never failed by the
        infrastructure); the next kick re-probes. Bounded per cycle so a large
        backlog cannot starve ingest jobs between polls."""

        if not runner.repo.has_queued_reader_requests():
            return 0
        client = self._resolve_reader_client(runner)
        if client is None:
            return 0
        result = RR.drain_requests(
            runner.repo,
            worker_id=f"sidecar-{os.getpid()}",
            synthesize=RR.model_synthesis(client),
            limit=3,
        )
        return len(result["completed"]) + len(result["failed"]) + len(result["partial"])

    def _resolve_reader_client(self, runner: IngestRunner) -> Any:
        with self._lock:
            if self._reader_client_checked:
                return self._reader_client
            factory = self._reader_synth_client_factory
        if factory is not None:
            client = factory()
        else:
            try:
                from learnloop.ai.routing import ready_client_for_task
                from learnloop.vault.loader import load_vault

                vault = load_vault(runner.vault_root)
                # Same canonical_ingest route the runner's inventory/synthesis
                # factories resolve, so non-codex vaults (e.g. openrouter) can
                # drain reader preset requests too.
                client = ready_client_for_task(
                    runner.vault_root,
                    vault.config,
                    "canonical_ingest",
                ).client
            except Exception:  # noqa: BLE001 — an unresolvable provider leaves requests queued
                client = None
        with self._lock:
            self._reader_client = client
            self._reader_client_checked = True
        return client

    @staticmethod
    def _legacy_job_for_batch(runner: IngestRunner, batch_id: str) -> dict[str, Any]:
        """The synthesis job the frontend polls (the batch also holds an import job)."""

        jobs = runner.repo.ingest_jobs_for_batch(batch_id)
        for job in jobs:
            if job["job_type"] in _LEGACY_JOB_TYPES:
                return job
        return jobs[-1]

    def _active_job_locked(self, runner: IngestRunner) -> dict[str, Any] | None:
        for job in runner.repo.ingest_jobs_by_types(_LEGACY_JOB_TYPES, limit=_RECENT_LIMIT):
            if job["status"] in _ACTIVE_STATUSES:
                return job
        return None


# The rungs each job type can actually reach. Reporting the full ladder for every
# job made an import-only batch advertise `inventoried`/`synthesized`/`applied`
# rungs no import handler ever reports, so the card read as a whole study-map
# build that had merely stalled. Anything not listed keeps the full ladder.
_LADDER_BY_JOB_TYPE: dict[str, tuple[str, ...]] = {
    "import": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("extracted") + 1],
    "extraction_repair": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("extracted") + 1],
    "inventory": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("inventoried") + 1],
}


def _job_view(
    job: dict[str, Any],
    repo: Repository,
    *,
    depends_on: list[str] | None = None,
    rung_requests_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One job as the Batch-progress screen needs it: the checkpoint ladder, live
    phase/window counts, actual usage, and any waiting_for_input payload (§5.7)."""

    result = job.get("result") or {}
    waiting_payload = result.get("waiting_for_input") if isinstance(result, dict) else None
    payload = job.get("payload") or {}
    status = effective_ingest_job_status(job)
    phase = job.get("phase")
    message = job.get("message")
    error = job.get("error")
    if status == "failed" and job.get("status") == "completed":
        request_id = str(payload.get("request_id") or "")
        request = (rung_requests_by_id or {}).get(request_id)
        reason = str(
            (request or {}).get("failure_reason")
            or "Rung variant generation failed before producing a proposal."
        )
        phase = "failed"
        message = reason
        error = {
            "code": "rung_variant_failed",
            "message": reason,
            "retryable": True,
            "details": {"request_id": request_id, "result": result},
        }
    return {
        "id": job["id"],
        "batch_id": job["batch_id"],
        "ordinal": job["ordinal"],
        "job_type": job["job_type"],
        "status": status,
        "phase": phase,
        "message": message,
        "current_window": job.get("current_window"),
        "total_windows": job.get("total_windows"),
        "attempt_count": job.get("attempt_count", 0),
        "checkpoint_ladder": list(
            _LADDER_BY_JOB_TYPE.get(job["job_type"], CHECKPOINT_LADDER)
        ),
        "usage": job.get("usage") or {},
        "estimate": payload.get("estimate") or {},
        "source": payload.get("source"),
        "result": None if waiting_payload is not None else (result or None),
        "error": error,
        "waiting_for_input": waiting_payload,
        "depends_on": (
            depends_on
            if depends_on is not None
            else repo.ingest_job_dependency_ids(job["id"])
        ),
    }


def _batch_view(
    batch: dict[str, Any],
    jobs: list[dict[str, Any]],
    repo: Repository,
    *,
    dependencies_by_job: dict[str, list[str]] | None = None,
    rung_requests_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if dependencies_by_job is None:
        dependencies_by_job = repo.ingest_job_dependencies_for_jobs(
            job["id"] for job in jobs
        )
    if rung_requests_by_id is None:
        rung_requests_by_id = repo.rung_variant_requests(
            request_id
            for job in jobs
            if (request_id := _failed_rung_request_id(job)) is not None
        )
    return {
        "id": batch["id"],
        "workflow_type": batch["workflow_type"],
        "subject_id": batch.get("subject_id"),
        "source_set_id": batch.get("source_set_id"),
        "status": derive_batch_status(jobs, batch),
        "cancel_requested": bool(batch.get("cancel_requested")),
        "created_at": batch.get("created_at"),
        "started_at": batch.get("started_at"),
        "finished_at": batch.get("finished_at"),
        "jobs": [
            _job_view(
                job,
                repo,
                depends_on=dependencies_by_job.get(job["id"], []),
                rung_requests_by_id=rung_requests_by_id,
            )
            for job in jobs
        ],
    }


def _failed_rung_request_id(job: dict[str, Any]) -> str | None:
    if effective_ingest_job_status(job) != "failed" or job.get("status") != "completed":
        return None
    request_id = str((job.get("payload") or {}).get("request_id") or "")
    return request_id or None


# Back-compat alias: SidecarContext + handlers import IngestJobManager.
IngestJobManager = DurableIngestJobs


def _compat_status(status: str) -> str:
    """Map the durable status vocabulary onto the legacy job vocabulary the
    existing frontend/handlers expect (queued|running|completed|failed|cancelled)."""

    return {"waiting_for_input": "running", "blocked": "failed"}.get(status, status)


def _compat(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    return {
        "id": job["id"],
        "batch_id": job.get("batch_id"),
        "source": payload.get("source"),
        "subject_id": payload.get("subject_id"),
        "mode": payload.get("mode", "canonical"),
        "status": _compat_status(job["status"]),
        "phase": job.get("phase") or job["status"],
        "message": job.get("message") or "",
        "current_window": job.get("current_window"),
        "total_windows": job.get("total_windows"),
        "created_at": job.get("created_at"),
        "updated_at": (
            job.get("finished_at")
            or job.get("heartbeat_at")
            or job.get("started_at")
            or job.get("created_at")
        ),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "result": job.get("result"),
        "error": job.get("error"),
    }
