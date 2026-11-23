"""The import and extraction job types: ``import``, ``auto_study_map``, ``legacy_ingest`` and ``exam_ingest``, and
``extraction_repair``, with the acquisition and extraction defaults the runner's services fall back on.

The durable host that runs them is :mod:`learnloop.content.pipeline.jobs`; what each type is (its handler and its
flags) is its row in :mod:`learnloop.content.pipeline.job_types`.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.pipeline.job_contracts import FetchedBytes, IngestRunnerError
from learnloop.content.pipeline.reread import _pdf_page_count
from learnloop.db.repositories import Repository
from learnloop.goals.exam_seeding import exam_ingest_instructions
from learnloop.ids import new_ulid
from learnloop.ingest.source_kinds import source_kind
from learnloop.source_retrieval.jobs import queue_source_vectors

if TYPE_CHECKING:
    from learnloop.content.pipeline.runner import JobContext


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

    fetched = source_ingestion.fetch_source(
        ctx.vault_root,
        source,
        kind=source_kind(category).fetch_as,
        allow_auto_captions=True,
        raw_only=True,
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

    if source_kind(category).fetch_as != "youtube_video":
        return None, ()
    try:
        from learnloop.ingest.youtube import youtube_oembed_metadata, youtube_video_id

        video_title, author = youtube_oembed_metadata(youtube_video_id(source))
    except Exception:  # pragma: no cover - metadata is strictly best-effort
        return None, ()
    return video_title, (author,) if author else ()


def _pdf_payload_config(ctx: JobContext) -> dict[str, Any]:
    """The effective PDF extraction config for one import job.

    The job payload's ``pdf_config`` wins key-by-key (a per-ingest engine choice
    or a repair's page/OCR options); the vault's ``[ingest.pdf]`` engine fills in
    when the payload doesn't pin one, so a configured ``engine = "pypdf"`` (or
    "marker") finally governs the durable import path too. This is the config
    the extraction request hash covers; the GLM-OCR runtime settings travel
    beside it (:func:`_document_extractor`), since endpoints, timeouts and
    prices never change what is extracted (the backend is in the version)."""

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
    if _local_repair(ctx):
        # A repair the learner OK'd as local ("re-running local extraction",
        # no "external VLM") is read by a local extractor only (GLM-OCR third
        # review F10): never the native-PDF model, never hosted Marker, never
        # hosted GLM-OCR. The per-book "keep on this computer" that narrowed
        # every reading of a book is retired (reading hardening, part 3).
        if config.get("engine") == "native":
            config["engine"] = "auto"
        if _hosted_marker_selected(config, glm_selected=_glm_backend(ctx, config) is not None):
            config["engine"] = "pypdf"
    return config


def _local_repair(ctx: JobContext) -> bool:
    """Whether this reading must stay on this computer: an extraction repair
    whose consent is local (GLM-OCR third review F10, set by
    :func:`handle_extraction_repair`). Nothing else narrows a reading: the
    per-book "keep on this computer" is retired, and nothing here reads the
    choice a library may still store for a book."""

    return bool(ctx.job.get("_local_repair"))


def _repair_is_local(consent: Mapping[str, Any]) -> bool:
    """A repair consent that approved no external service: OutlineAndPlan's
    repair without "external VLM" and ``learnloop repair-extraction`` without
    ``--use-llm`` both send ``external: false`` and provider ``local``. A
    record that does not say ``external`` counts as local."""

    return not consent.get("external") or str(consent.get("provider") or "") == "local"


def _glm_settings(ctx: JobContext) -> dict[str, Any]:
    """The vault's ``[ingest.pdf.glm_ocr]`` settings (not hashed); loading
    the config also loads the machine's settings.env, where the key lives."""

    from learnloop.config.loader import load_config

    try:
        return load_config(Path(ctx.vault_root) / "learnloop.toml").ingest.pdf.glm_ocr.model_dump()
    except FileNotFoundError:
        return {}


def _glm_backend(ctx: JobContext, pdf_config: Mapping[str, Any]) -> str | None:
    if str(pdf_config.get("engine") or "auto") not in {"auto", "glm_ocr"}:
        return None
    from learnloop.ingest.extractors.glm_ocr import selected_backend

    return selected_backend(_glm_settings(ctx), local_only=_local_repair(ctx))


def _hosted_marker_selected(pdf_config: Mapping[str, Any], *, glm_selected: bool = False) -> bool:
    """The explicit Datalab debug runtime: Marker runs on Datalab's servers
    (only when GLM-OCR, which ``auto`` prefers, is not selected)."""

    import os

    engine = str(pdf_config.get("engine") or "auto")
    if engine in {"pypdf", "native", "glm_ocr"} or (engine == "auto" and glm_selected):
        return False
    return os.environ.get("LEARNLOOP_MARKER_PROVIDER", "local").strip().lower() == "datalab"


def _is_document(fetched: FetchedBytes, category: str) -> bool:
    """A PDF, PNG or JPG: read by the document extractors (GLM-OCR, Marker,
    pypdf), whatever page or link it came from."""

    content_type = (fetched.content_type or "").split(";")[0].strip().lower()
    return (
        source_kind(category).document
        or content_type in {"application/pdf", "image/png", "image/jpeg"}
        or fetched.raw_bytes[:5] == b"%PDF-"
    )


def _image_config(pdf_config: dict[str, Any], fetched: FetchedBytes) -> dict[str, Any]:
    from learnloop.ingest.extractors import document_pdf_config

    return document_pdf_config(pdf_config, fetched.raw_bytes)


def _document_extractor(ctx: JobContext, pdf_config: Mapping[str, Any], fetched: FetchedBytes) -> Any:
    """The extractor for a PDF/PNG/JPG import, its upload guarded.

    Hosted GLM-OCR sends the whole file to z.ai: it waits for the learner's
    one-time OK naming z.ai. Under ``auto``, an import with no OK card to
    show (``learnloop import``, the Ingest screen, an external repair) reads
    a PDF locally until the OK is given, flagged ``glm_ocr_needs_upload_ok``
    so the book offers text recognition (second review F2); a scan it can't
    read that way asks for the OK on its card (third review F2,
    :func:`default_extract`). A repair the learner OK'd as local never leaves
    this computer, whatever the engine (third review F10): ``auto`` passes
    over z.ai and a text recognition server on another computer. An image
    needs GLM-OCR: Marker and pypdf read PDFs only."""

    from learnloop.ingest.extractors import MarkerUnavailableError, pdf_extractor_for

    try:
        extractor, consent = pdf_extractor_for(
            {**pdf_config, "glm_ocr": _glm_settings(ctx)}, local_only=_local_repair(ctx),
            raw_bytes=fetched.raw_bytes, upload_allowed=lambda: _upload_allowed(ctx, "glm_ocr_upload"),
            require_upload_ok=bool(ctx.payload.get("require_upload_ok")),
        )
    except MarkerUnavailableError as exc:
        raise IngestRunnerError(str(exc), code="pdf_extractor_unavailable", retryable=True) from exc
    if consent is not None:
        if consent.code != "needs_upload_ok":
            raise IngestRunnerError(consent.plain_message, code=consent.code, retryable=consent.retryable,
                                    details={"flow": consent.flow})
        _guard_file_upload(ctx, consent.flow, plain_message=consent.plain_message,
                           details=glm_upload_estimate(ctx, fetched))
    return extractor


def glm_upload_estimate(ctx: JobContext, fetched: FetchedBytes) -> dict[str, Any]:
    """Pages and the estimated cost of reading this file with hosted GLM-OCR
    (``glm_ocr.estimate``), for the card's z.ai OK line (re-read safety item 5):
    the pages the import asks for, else every page of the file."""

    from learnloop.ingest.extractors.glm_ocr import estimate, is_image_document

    pages: int | None
    selection = _normalize_pages(ctx.payload.get("page_selection"))
    if selection:
        pages = len(selection)
    elif is_image_document(fetched.raw_bytes):
        pages = 1
    else:
        pages = _pdf_page_count(fetched.raw_bytes)
    priced = estimate(pages, _glm_settings(ctx), backend="api")
    return {"pages": priced["pages"], "estimated_usd": priced["estimated_usd"],
            "page_selection": selection or None}


def _extraction_interrupt(ctx: JobContext) -> Any:
    """Checked before each request GLM-OCR sends (every window, every retry;
    second review F4): a cancelled import stops there (never a fallback; the
    runner records the job as cancelled). A request already under way is not
    recalled."""

    from learnloop.ai.spend import SpendCancelled

    cancelled = getattr(ctx, "cancelled", None)

    def interrupt() -> None:
        if cancelled is not None and cancelled():
            raise SpendCancelled("The import was cancelled")

    return interrupt


def _upload_allowed(ctx: JobContext, flow: str) -> bool:
    from learnloop.content.pipeline.add_source import file_upload_allowed
    from learnloop.vault.loader import load_vault

    return file_upload_allowed(load_vault(ctx.vault_root).config, flow)


_UPLOAD_FLOW_MESSAGES = {
    "audio_transcription": (
        "Transcribing this recording sends it to an online service. Say OK once to allow that."
    ),
    "glm_ocr_upload": "Reading this document sends the whole file to z.ai (GLM-OCR). Say OK once to allow that.",
    "pdf_upload": "Reading this PDF sends the whole file to your AI. Say OK once to allow that.",
}
# A plain import (`learnloop import`, the Ingest screen) asks nothing where it
# starts: its words say where the OK is given, the book's card in the Library
# (third review F2: the card finds the import that waits).
_PLAIN_IMPORT_UPLOAD_MESSAGES = {
    "glm_ocr_upload": (
        "Reading this document with GLM-OCR sends the whole file to z.ai, which needs your OK first. "
        "Say OK on its card in the Library, or choose another PDF engine."
    ),
}
_PLAIN_IMPORT_SCAN_MESSAGE = (
    "This PDF has no text layer (it looks scanned), so only text recognition can read it. Reading it with "
    "GLM-OCR sends the whole file to z.ai, which needs your OK first. Say OK on its card in the Library."
)
# Why a PDF was read locally: the z.ai OK was missing where no card could ask.
GLM_NEEDS_UPLOAD_OK = "glm_ocr_needs_upload_ok"


def _guard_file_upload(ctx: JobContext, flow: str, *, plain_message: str | None = None,
                       details: Mapping[str, Any] | None = None) -> None:
    """Before a whole file leaves the computer (UX Phase 1 review F1): an Add
    (which asked the learner nothing per book) uploads only after the separate
    OK for whole files (spec §6.6: the connection's OK covers passages and
    answers only). z.ai's upload (GLM-OCR) always asks, for its own OK.
    ``plain_message`` replaces a plain import's words for this one file."""

    # Every upload goes to a model: it waits for the learner's one OK to use
    # AI first, whatever OK for the file itself it also needs.
    from learnloop.ai import model_use

    model_use.require(ctx.vault_root)
    # z.ai's upload always asks (not only an Add's), for its own OK naming
    # z.ai (second review F3). Under "auto" a plain import never gets here
    # without it (it reads locally); an explicit glm_ocr engine does.
    if ctx.payload.get("require_upload_ok") or flow == "glm_ocr_upload":
        if not _upload_allowed(ctx, flow):
            message = _UPLOAD_FLOW_MESSAGES[flow]
            if not ctx.payload.get("require_upload_ok"):
                message = plain_message or _PLAIN_IMPORT_UPLOAD_MESSAGES.get(flow, message)
            raise IngestRunnerError(message, code="needs_upload_ok", retryable=True,
                                    details={"flow": flow, **dict(details or {})})


def _extract_pdf_locally(
    fetched: FetchedBytes, extractor: Any, pdf_config: Mapping[str, Any], context: Any
) -> Any:
    """Run the extractor with the registry's fallback chain (§2.9): under
    ``auto``, GLM-OCR degrades to local Marker or pypdf and Marker to pypdf,
    each with a health flag; an explicitly chosen engine fails as itself."""

    from learnloop.ingest.extractors import ExtractionFallbackFailed, extract_with_fallback

    try:
        return extract_with_fallback(fetched.raw_bytes, extractor, dict(pdf_config), context)
    except ExtractionFallbackFailed as exc:
        raise IngestRunnerError(
            f"PDF extraction failed: {exc}", code="pdf_extraction_failed", retryable=True
        ) from exc


def _found_no_text(exc: BaseException) -> bool:
    """A local reading that found no text layer at all (a scanned PDF)."""

    lowered = str(exc).lower()
    return "no extractable text" in lowered or "likely scanned" in lowered


def default_extract(fetched: FetchedBytes, category: str, ctx: JobContext) -> Any:
    """Produce Document IR from fetched bytes using the M1 extractor providers.

    PDFs go through the engine the payload/vault config selects (marker, the
    pypdf fallback, or auto); audio is transcribed via the [ingest.audio]
    endpoint; everything else gets honest trivial IR from its decoded text
    (§2.3)."""

    from learnloop.ingest.extractors import markdown_to_ir
    from learnloop.ingest.extractors.base import ExtractionContext

    reader = source_kind(category).reader
    if reader == "audio":
        _guard_file_upload(ctx, "audio_transcription")
        return _extract_audio(fetched, ctx)

    is_pdf = _is_document(fetched, category)
    if is_pdf:
        pdf_config = _image_config(_pdf_payload_config(ctx), fetched)
        native_fallback: str | None = None
        if _hosted_marker_selected(pdf_config, glm_selected=_glm_backend(ctx, pdf_config) is not None):
            _guard_file_upload(ctx, "pdf_upload")
        if pdf_config.get("engine") == "native":
            decision = _decide_native(ctx, "pdf", requested=True, unavailable_code="native_pdf_unavailable")
            if decision is not None and decision.route is not None:
                _guard_file_upload(ctx, "pdf_upload")
                return _extract_pdf_native(fetched, ctx, decision.route)
            native_fallback = decision.fallback_reason if decision else "unavailable"
            pdf_config = {**pdf_config, "engine": "auto"}
        extractor = _document_extractor(ctx, pdf_config, fetched)
        pages = _normalize_pages(ctx.payload.get("page_selection") or pdf_config.get("page_range")) or None
        context = ExtractionContext(
            revision_id=str(ctx.job.get("_revision_id") or "rev"),
            config={"whole_file_upload_allowed": getattr(extractor, "backend", None) == "api"},
            page_selection=tuple(pages) if pages is not None else None,
            interrupt=_extraction_interrupt(ctx),
            # A hosted reader's paid window answers are kept in the import's
            # model_work_checkpoints, so a retry or a re-read pays only for
            # what is unanswered.
            checkpoints=getattr(ctx, "repo", None),
        )
        try:
            ir = _extract_pdf_locally(fetched, extractor, pdf_config, context)
        except Exception as exc:
            if (
                getattr(extractor, "selection_reason", None) == GLM_NEEDS_UPLOAD_OK
                and _found_no_text(exc)
                and ctx.job.get("job_type") != "extraction_repair"
            ):
                # Read locally only because the z.ai OK was missing, and a
                # scan has no text to read that way: the OK is what helps
                # (third review F2), asked on the book's card. A repair has
                # no card that asks, so it fails as the local reading did.
                raise IngestRunnerError(
                    _PLAIN_IMPORT_SCAN_MESSAGE, code="needs_upload_ok", retryable=True,
                    details={"flow": "glm_ocr_upload", **glm_upload_estimate(ctx, fetched)},
                ) from exc
            raise
        if native_fallback:
            _add_health_flag(ir, "native_pdf_fallback_local")
        return ir

    text = fetched.raw_bytes.decode("utf-8", errors="replace")

    if reader == "captions":
        from learnloop.ingest.extractors import captions_to_ir

        cues = _caption_cues(text)
        if cues is not None:
            return captions_to_ir(cues, title=ctx.payload.get("title"))

    looks_like_html = (fetched.content_type or "").lower().startswith("text/html") or bool(
        re.match(r"\s*(?:<!doctype\s+html|<html)", text, re.IGNORECASE)
    )
    if reader == "html" or looks_like_html:
        from learnloop.ingest.extractors.web_page import WEB_PAGE_EXTRACTOR_VERSION, page_markdown

        markdown = page_markdown(text)
        if markdown:
            return markdown_to_ir(markdown, title=ctx.payload.get("title"), extractor_name="html",
                                  extractor_version=WEB_PAGE_EXTRACTOR_VERSION, section_titles=True)

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

    reader = source_kind(category).reader
    if reader == "audio":
        _guard_file_upload(ctx, "audio_transcription")
        # Lock-step with _extract_audio: the same pure route decision picks
        # native vs routed-chat vs endpoint transcription, and the identity
        # carries the model + provider/endpoint so re-pointing either forces a
        # fresh transcription. Keys named api_key* are stripped by
        # hashing._sanitized_config.
        from learnloop.ai.multimodal import chat_audio_format

        chat_format = chat_audio_format(_audio_filename(fetched))
        fallback_config: dict[str, Any] = {}
        # Containers the chat API cannot take (m4a, flac, ...) never go native,
        # so their route's readiness is irrelevant: the documented data-dependent
        # fallback to transcription, with no marker in the identity.
        decision = (
            _decide_native(ctx, "audio", unavailable_code="native_audio_unavailable")
            if chat_format is not None
            else None
        )
        if decision is not None:
            if decision.route is not None:
                return {
                    "extractor": "audio_native",
                    "extractor_version": "1",
                    "model_versions": {"chat_model": decision.route.model or ""},
                    "config": {"provider": decision.route.provider_name},
                }
            # A configuration fallback is recorded in the identity.
            if decision.fallback_reason:
                fallback_config = {"native_fallback": decision.fallback_reason}
        audio_config = _audio_ingest_config(ctx)
        route = _transcription_media_route(ctx)
        if route is not None:
            if chat_format is None:
                raise IngestRunnerError(
                    _ROUTED_AUDIO_FORMAT_MESSAGE,
                    code="audio_format_unsupported",
                    retryable=True,
                )
            return {
                "extractor": "audio_native",
                "extractor_version": "1",
                "model_versions": {"chat_model": route.model or ""},
                "config": {"provider": route.provider_name, **fallback_config},
            }
        return {
            "extractor": "audio_transcript",
            "extractor_version": "1",
            "model_versions": {"transcription_model": audio_config.transcription_model},
            "config": {"base_url": audio_config.transcription_base_url, **fallback_config},
        }

    is_pdf = _is_document(fetched, category)
    if is_pdf:
        config = _image_config(_pdf_payload_config(ctx), fetched)
        native_fallback: str | None = None
        if _hosted_marker_selected(config, glm_selected=_glm_backend(ctx, config) is not None):
            _guard_file_upload(ctx, "pdf_upload")
        if config.get("engine") == "native":
            decision = _decide_native(ctx, "pdf", requested=True, unavailable_code="native_pdf_unavailable")
            if decision is not None and decision.route is not None:
                _guard_file_upload(ctx, "pdf_upload")
                return {
                    "extractor": "pdf_native",
                    "extractor_version": "1",
                    "model_versions": {"chat_model": decision.route.model or ""},
                    "config": {"provider": decision.route.provider_name},
                }
            # Native cannot run and fallback is opted in: the local road, and
            # the identity says why so the cache never confuses the two.
            native_fallback = decision.fallback_reason if decision else "unavailable"
            config = {**config, "engine": "auto"}
        extractor = _document_extractor(ctx, config, fetched)
        return {
            "extractor": extractor.name,
            "extractor_version": extractor.version(),
            "model_versions": extractor.model_versions(),
            "config": {**config, "native_fallback": native_fallback} if native_fallback else config,
        }
    if reader == "captions":
        # Captions normalizer (captions_to_ir) v2 stamps per-cue t= timing onto
        # extractor_block_id; must match captions_to_ir's default.
        return {"extractor": "youtube", "extractor_version": "2", "model_versions": {}, "config": {}}
    text = fetched.raw_bytes[:4096].decode("utf-8", errors="replace")
    looks_html = (fetched.content_type or "").lower().startswith("text/html") or bool(
        re.match(r"\s*(?:<!doctype\s+html|<html)", text, re.IGNORECASE)
    )
    if reader == "html" or looks_html:
        # The version is in the request hash: a page read with an earlier one
        # is never served this reading from cache, and keeps its own until it
        # is imported again (the card's "Read it again").
        from learnloop.ingest.extractors.web_page import WEB_PAGE_EXTRACTOR_VERSION

        return {"extractor": "html", "extractor_version": WEB_PAGE_EXTRACTOR_VERSION, "model_versions": {},
                "config": {}}
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
    #: Upload cap for the modality (base64 inflates ~33% inside a chat body).
    max_mb: int


def _native_readiness(
    ctx: JobContext, modality: str, *, requested: bool | None = None
) -> tuple[Any, bool] | None:
    """The shared readiness judgement (learnloop.ai.native_media) for this vault
    plus the ``fallback_when_unavailable`` opt-in, read from ONE config load so
    the two can never come from different versions of learnloop.toml. None when
    the vault has no config file yet."""

    from learnloop.ai.native_media import native_modality_readiness
    from learnloop.vault.loader import load_vault

    try:
        config = load_vault(ctx.vault_root).config
    except FileNotFoundError:
        return None
    readiness = native_modality_readiness(config, modality, requested=requested)
    return readiness, bool(config.ingest.native.fallback_when_unavailable)


def _route_from_readiness(readiness: Any) -> NativeMediaRoute:
    return NativeMediaRoute(
        provider_name=readiness.provider_name or "",
        model=readiness.model,
        max_mb=readiness.max_mb,
    )


@dataclass(frozen=True)
class _NativeDecision:
    """What happens to media whose modality is routed natively.

    ``route`` is set when the native path runs. ``fallback_reason`` is set when
    native was selected but cannot run for a configuration reason and
    ``[ingest.native] fallback_when_unavailable`` sends the file down the
    non-native path instead; identity and extraction both record it."""

    route: NativeMediaRoute | None
    fallback_reason: str | None


def _decide_native(
    ctx: JobContext, modality: str, *, requested: bool | None = None, unavailable_code: str
) -> _NativeDecision | None:
    """PURE config decision shared by identity and extraction.

    Returns None when native is not selected for ``modality``. Raises a typed,
    NON-retryable error when native is selected, unavailable for a
    configuration reason, and fallback is not opted in — the durable queue
    must not retry a misconfiguration forever."""

    loaded = _native_readiness(ctx, modality, requested=requested)
    if loaded is None:
        if requested:
            raise IngestRunnerError(
                f"native {modality} ingestion was requested but the vault has no configuration",
                code=unavailable_code,
                retryable=False,
            )
        return None
    readiness, fallback_allowed = loaded
    if not readiness.requested:
        return None
    if readiness.ready:
        return _NativeDecision(route=_route_from_readiness(readiness), fallback_reason=None)
    if fallback_allowed:
        return _NativeDecision(route=None, fallback_reason=readiness.reason or "unavailable")
    raise IngestRunnerError(
        readiness.message,
        code=unavailable_code,
        retryable=False,
        details={"reason": readiness.reason, "modality": modality},
    )


def _add_health_flag(ir: Any, flag: str) -> Any:
    if flag not in ir.health.flags:
        ir.health.flags.append(flag)
    return ir


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
        status = resolved.runtime.status
        raise IngestRunnerError(
            resolved.runtime.message or f"AI provider {route.provider_name!r} is {status}.",
            code="native_media_unavailable",
            # A missing key or profile needs the owner, not a retry.
            retryable=status not in {"provider_auth_required", "provider_missing_config"},
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
        max_mb=config.ingest.native.max_audio_mb,
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

    chat_format = chat_audio_format(_audio_filename(fetched))
    native_fallback: str | None = None
    # Lock-step with default_extraction_identity: only chat-accepted containers
    # consult the native route.
    decision = (
        _decide_native(ctx, "audio", unavailable_code="native_audio_unavailable")
        if chat_format is not None
        else None
    )
    if decision is not None:
        if decision.route is not None:
            return _extract_audio_native(fetched, ctx, decision.route, chat_format)
        native_fallback = decision.fallback_reason

    ir = _extract_audio_transcription(fetched, ctx, chat_format)
    if native_fallback:
        _add_health_flag(ir, "native_audio_fallback_transcription")
    return ir


def _extract_audio_transcription(fetched: FetchedBytes, ctx: JobContext, chat_format: str | None) -> Any:
    """The non-native audio path: the dedicated transcription route, else the endpoint."""

    from learnloop.ingest.extractors import transcript_to_ir
    from learnloop.ingest.transcription import (
        TranscriptionFailed,
        TranscriptionUnavailable,
        transcribe_audio,
    )

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
    if size_mb > route.max_mb:
        raise IngestRunnerError(
            f"Audio file is {size_mb:.1f} MB; [ingest.native] max_audio_mb is {route.max_mb}.",
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
    if size_mb > route.max_mb:
        # Base64 inflates ~33% inside a chat body, so the chat-path cap
        # applies, not the endpoint's max_file_mb.
        raise IngestRunnerError(
            f"Audio file is {size_mb:.1f} MB; [ingest.native] max_audio_mb is {route.max_mb}.",
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


def _extract_pdf_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute) -> Any:
    """PDF → chat file part → Markdown → IR ([ingest.pdf] engine "native")."""

    from learnloop.ai.multimodal import PdfExtractionContextNative
    from learnloop.ai.errors import CodexUnavailable
    from learnloop.ingest.extractors import markdown_to_ir

    # Pages arrive as the import's ``page_selection`` or as a repair's
    # ``pdf_config.page_range``; either would be silently ignored by a
    # whole-document upload, so both are refused.
    if ctx.payload.get("page_selection") or (ctx.payload.get("pdf_config") or {}).get("page_range"):
        raise IngestRunnerError(
            "Native PDF ingestion sends the whole document and does not support page "
            "selection; clear the page range or choose the marker or pypdf engine.",
            code="native_pdf_unavailable",
            retryable=False,
        )
    size_mb = len(fetched.raw_bytes) / (1024 * 1024)
    if size_mb > route.max_mb:
        raise IngestRunnerError(
            f"PDF is {size_mb:.1f} MB; [ingest.native] max_pdf_mb is {route.max_mb}.",
            code="pdf_too_large",
            retryable=False,
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


def default_run_legacy_ingest(
    *,
    vault_root: Path,
    source: str,
    subject_id: str,
    mode: str,
    progress: Callable[[str, dict[str, Any]], None] | None,
    clock: Clock | None,
    ir_markdown: str | None = None,
    resume_extraction_id: str | None = None,
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
        resume_extraction_id=resume_extraction_id,
        clock=clock,
        progress=progress,
    )


def _record_import_source(ctx: JobContext, source_id: str, revision_id: str) -> None:
    """Name the book on its import once the book exists (GLM-OCR third
    review F2): a link Add's or a plain import's job learns its book only
    here, and a failed one has no result, so without it the book's card never
    finds the import that waits for an OK. An Add's own ``source_id`` (a
    book that already existed) is left as it is. The revision it registered
    is named too, so a retry reads that revision's own bytes (re-read safety),
    not the book's current one."""

    if ctx.payload.get("source_id"):
        return
    stored = dict((ctx.repo.get_ingest_job(ctx.job_id) or {}).get("payload") or {})
    if stored.get("source_id"):
        return
    ctx.repo.update_ingest_job_payload(ctx.job_id, {**stored, "source_id": source_id, "revision_id": revision_id})


def _note_carry_owed(ctx: JobContext, revision_id: str, extraction_id: str) -> None:
    """Before a reading of a revision that already has one completes (or a
    cached one is carried again): the job's payload names the carry-over it
    owes (re-read safety, Codex review F7; ``reread.carry_owed``)."""

    from learnloop.content.pipeline.reread import CARRY_DONE_KEY, CARRY_OWED_KEY, owes_carry

    if not owes_carry(ctx.repo, revision_id, extraction_id):
        return
    stored = dict((ctx.repo.get_ingest_job(ctx.job_id) or {}).get("payload") or {})
    if stored.get(CARRY_OWED_KEY) == extraction_id and stored.get(CARRY_DONE_KEY) != extraction_id:
        return
    stored.pop(CARRY_DONE_KEY, None)
    ctx.repo.update_ingest_job_payload(ctx.job_id, {**stored, CARRY_OWED_KEY: extraction_id})


def _carry_noted(ctx: JobContext, extraction_id: str) -> bool:
    from learnloop.content.pipeline.reread import CARRY_OWED_KEY

    stored = (ctx.repo.get_ingest_job(ctx.job_id) or {}).get("payload") or {}
    return stored.get(CARRY_OWED_KEY) == extraction_id


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
    # Re-read safety E1: an import that names an existing book (the card's
    # "Read it again", an Add of a book already here, a retry) keeps the
    # book's own kind and identity and is handed its current revision's BYTES
    # from the originals store, verified by its hash: never whatever sits at
    # its path now (a git-LFS pointer, an edited file), and its path is never
    # classified again (a store file has no extension, so ``resolve_source``
    # refuses it: GLM-OCR live run, 2026-10-14).
    known = ctx.repo.get_source_artifact(str(payload["source_id"])) if payload.get("source_id") else None
    if known is not None and known.get("acquisition_kind"):
        category = str(known["acquisition_kind"])
        canonical_uri = str(known.get("canonical_uri") or source)
    else:
        resolved = resolve_source(source)
        category, canonical_uri = resolved.category, resolved.source
    requested_pages = _normalize_pages(payload.get("page_selection")) or None

    ctx.report("acquired", message="Fetching source material")
    fetched = None
    if known is not None:
        from learnloop.content.pipeline.reread import original_bytes, revision_bytes

        fetch_url = lambda uri: ctx.services.fetch_bytes(uri, category, ctx)  # noqa: E731
        named = ctx.repo.get_source_revision(str(payload["revision_id"])) if payload.get("revision_id") else None
        if named is not None and named.get("source_id") == payload["source_id"]:
            # A retry of an import that registered this revision itself.
            fetched = revision_bytes(Path(ctx.vault_root), named, ctx.repo.get_source_artifact(named["source_id"]),
                                     fetch_url=fetch_url, clock=ctx.clock)
        else:
            fetched = original_bytes(ctx.repo, Path(ctx.vault_root), str(payload["source_id"]),
                                     fetch_url=fetch_url, clock=ctx.clock)
    if fetched is None:
        fetched = ctx.services.fetch_bytes(canonical_uri, category, ctx)
    is_pdf = _is_document(fetched, category)
    page_selection = requested_pages if is_pdf else None
    if page_selection:
        _validate_page_selection(fetched.raw_bytes, page_selection)

    display_title = _compose_display_title(fetched.title, fetched.authors)
    if display_title is None and fetched.raw_bytes.startswith(b"%PDF-"):
        # A PDF's own title, as Add uses (UX Phase 1 usability round 2: a book
        # imported through the Ingest screen was titled by its file name).
        from learnloop.content.pipeline.add_source import pdf_metadata_title

        display_title = pdf_metadata_title(fetched.raw_bytes)
    reader_enabled = payload.get("reader_enabled")
    registered = register_source_revision(
        ctx.repo,
        acquisition_kind=category,
        canonical_uri=canonical_uri,
        raw_bytes=fetched.raw_bytes,
        original_uri=fetched.original_uri,
        retrieved_at=fetched.retrieved_at,
        display_title=display_title,
        reader_enabled=None if reader_enabled is None else bool(reader_enabled),
        vault_root=ctx.vault_root,
        clock=ctx.clock,
    )
    ctx.job["_revision_id"] = registered.revision_id
    _record_import_source(ctx, registered.source_id, registered.revision_id)
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
        _note_carry_owed(ctx, registered.revision_id, extraction_id)
    else:
        ir = ctx.services.extract_ir(fetched, category, ctx)
        # Injected/custom providers may refine the preflight identity. Persist
        # under the actual identity and let subsequent retries hit that key.
        model_versions = _actual_model_versions(identity, ir)
        actual_hash = extraction_request_hash(
            revision_id=registered.revision_id,
            extractor=ir.extractor,
            extractor_version=ir.extractor_version,
            model_versions=model_versions,
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
                model_versions=model_versions,
                config=identity.get("config") or {},
                page_selection=page_selection,
                status="running",
                clock=ctx.clock,
            )
        _note_carry_owed(ctx, registered.revision_id, extraction_id)
        if not reused_extraction:
            ctx.repo.persist_document_ir(extraction_id, ir)
            ctx.repo.complete_extraction_run(
                extraction_id,
                extraction_result_hash=extraction_result_hash(request_hash, ir),
                health=ir.health.model_dump(mode="json"),
                clock=ctx.clock,
            )
    # Re-read safety: the revision becomes current only now that it has a
    # completed reading, and a second reading of a revision carries what the
    # learner had on the first (aliases, progress, selection, annotations).
    # The job's payload names the carry-over this reading owes before the
    # reading completes (``_note_carry_owed``) and records it done after: one
    # that fails here (a busy database) or is interrupted stays owed, on the
    # book's card ("Finish moving them") and in doctor, never silently lost
    # (Codex review F7). The reading itself stands either way.
    from learnloop.content.pipeline.reread import adopt_revision, carry_over, mark_carried

    adopt_revision(ctx.repo, registered.source_id, registered.revision_id, clock=ctx.clock)
    try:
        carried = carry_over(ctx.repo, extraction_id, clock=ctx.clock)
    except Exception as exc:  # noqa: BLE001 - the reading stands; the carry-over stays owed
        logging.getLogger(__name__).exception("carrying the old reading over to %s failed", extraction_id)
        carried = {"error": f"{type(exc).__name__}: {exc}", "owed": True}
    else:
        if _carry_noted(ctx, extraction_id):
            mark_carried(ctx.repo, ctx.job_id, extraction_id)

    # Fresh or reused alike (Codex review F3): a retry after a worker died
    # between completion and this call still queues what the source is owed.
    queue_source_vectors(ctx, extraction_id, title=display_title)

    ctx.report("extracted", message="Extracted document structure")
    return {
        "carried_over": carried,
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


def _actual_model_versions(identity: Mapping[str, Any], ir: Any) -> dict[str, Any]:
    """The model versions of the extractor that really read the document.

    Under ``auto`` a failing extractor's local stand-in (§2.9) reads it
    instead; its run records the stand-in's versions and what it stood in
    for, never the chosen extractor's models (second review F7). That holds
    through a second fallback (GLM-OCR → Marker → pypdf, third review F7).
    The ``fallback_from`` entry also keeps a stand-in's run apart from the
    same extractor chosen directly."""

    chosen = str(identity.get("extractor") or "")
    if ir.extractor != chosen and any(
        flag.startswith(f"{chosen}_failed_") and flag.endswith("_fallback") for flag in ir.health.flags
    ):
        from learnloop.ingest.extractors import fallback_model_versions

        return {**fallback_model_versions(ir.extractor), "fallback_from": chosen}
    return dict(identity.get("model_versions") or {})


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
    # than re-extracting. No import dependency (legacy call path) → ir_markdown
    # is None and the pipeline keeps its byte-identical legacy behavior.
    extraction_id = _legacy_ir_extraction_id(ctx)
    ir_markdown = _legacy_ir_markdown(ctx, extraction_id)
    # The first attempt fetches the source again: the fetch carries caption
    # cues, arXiv native locators, authors, license and labels that the IR
    # does not. A retry synthesizes from the import's retained bytes and IR
    # instead, so it still works when the source moved or went offline.
    is_retry = int(ctx.job.get("attempt_count") or 1) > 1
    resume_extraction_id = extraction_id if is_retry and ir_markdown is not None else None

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
        **({"resume_extraction_id": resume_extraction_id} if resume_extraction_id else {}),
        progress=_progress,
        clock=ctx.clock,
    )
    ctx.record_usage({"calls": int(getattr(result, "codex_calls", 0) or 0)})
    ctx.report("applied", message="Ingest complete")
    return result.as_dict() if hasattr(result, "as_dict") else dict(result)


def _legacy_ir_extraction_id(ctx: JobContext) -> str | None:
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
    return extraction_id


def _legacy_ir_markdown(ctx: JobContext, extraction_id: str | None) -> str | None:
    """Render the IR from this job's completed ``import`` dependency, if any (§2.3).

    Returns the display markdown for the extraction the import stage produced,
    filtered to a persisted unit selection when one exists. Returns ``None`` when
    there is no import dependency or no persisted IR — the legacy path then runs
    unchanged (extract-once-reuse-everywhere without deep coupling; §15 M3.5)."""

    from learnloop.ingest.ir import render_ir_markdown

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
    parent_id = payload.get("parent_extraction_id") or _latest_completed_extraction(ctx.repo, revision_id)
    if not parent_id:
        raise IngestRunnerError(f"revision '{revision_id}' has no completed extraction to repair.")
    parent_ir = ctx.repo.load_document_ir(parent_id)
    if parent_ir is None:
        raise IngestRunnerError(f"parent extraction '{parent_id}' has no persisted IR.")

    source = revision.get("original_uri") or (artifact.get("canonical_uri") if artifact else None)
    if not source:
        raise IngestRunnerError(f"revision '{revision_id}' has no fetchable URI for re-extraction.")
    # The book's own kind: its path is never classified again (a store file
    # has no extension; re-read safety, GLM-OCR live run).
    resolved_category = str((artifact or {}).get("acquisition_kind") or "") or resolve_source(str(source)).category

    ctx.report("acquired", message=f"Re-acquiring {len(pages)} page(s) for repair")
    # The revision's own bytes (re-read safety E1): never what sits at its
    # path now.
    from learnloop.content.pipeline.reread import revision_bytes

    fetched = revision_bytes(
        Path(ctx.vault_root), revision, artifact,
        fetch_url=lambda uri: ctx.services.fetch_bytes(uri, resolved_category, ctx), clock=ctx.clock,
    )

    options = dict(payload.get("repair_options") or {})
    repair_config = _repair_pdf_config(options, pages)
    ctx.job["payload"] = {**payload, "pdf_config": repair_config}
    ctx.job["_revision_id"] = revision_id
    # GLM-OCR third review F10: a repair whose consent is local ("re-running
    # local extraction", no "external VLM") never leaves this computer,
    # whatever the engine.
    ctx.job["_local_repair"] = _repair_is_local(consent)

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
    # Fresh or reused alike (Codex review F3; see handle_import).
    queue_source_vectors(ctx, repair_extraction_id)

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


def handle_auto_study_map(ctx: JobContext) -> dict[str, Any]:
    """auto_study_map: plan the automatic question build after an Add (UX Phase 1).

    Runs after the source's import (or alone, when the learner connects an AI,
    says "Build them", or reads into the next chapter). Its result is the
    ledger entry the book card's status line reads; see
    ``learnloop.content.pipeline.add_source``."""

    from learnloop import provenance
    from learnloop.content.pipeline.add_source import run_auto_study_map

    # The planner's job id is its build's trace (``_build_trace_id``): the scope it chose joins the run it caused.
    with provenance.trace_scope(ctx.job_id):
        return run_auto_study_map(ctx)
