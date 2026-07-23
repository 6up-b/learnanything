"""Durable ingest runner (spec_source_ingestion_v2 §6.2).

A repository-backed, leased drain that replaces the old in-memory job manager.
Work survives restarts: batches/jobs/dependencies live in SQLite, exactly one
vault-writing worker drains at a time under a lease, and explicitly compatible
DB-only work may use a bounded parallel lane. Every stage is independently
resumable along the checkpoint ladder::

    acquired -> registered -> extracted -> inventoried -> synthesized -> proposed -> applied

Design invariants (mirrors §6.2 and §14):

- Eligibility = a ``queued`` job whose dependencies are all ``completed``.
- A dependency that ends ``failed``/``blocked``/``cancelled`` makes every
  downstream job ``blocked`` (never silently ``failed``).
- ``waiting_for_input`` holds NO lease, so a question to the user cannot block the
  drain of other eligible jobs.
- Lease = ``worker_id`` + ``heartbeat_at``; on startup an expired ``running`` lease
  is recovered to ``failed(interrupted)`` and its ``queued`` siblings resume.
- Retries are keyed by the stage idempotency hash (asset hash for import,
  extraction_request_hash for extract — reusing the M1 hash model), so a retry
  reuses a completed revision/extraction instead of duplicating it.
- ``usage_json`` accumulates as a deterministic sum over attempts, so retry usage
  stays visible rather than being overwritten.

The core drain is synchronous and clock-injectable: ``drain``/``run_next`` are
callable directly in tests with a :class:`FrozenClock` and a stub
:class:`RunnerServices`; no sleeps and no threads are required to exercise the
machinery. Worker hosts (the sidecar background loop and the foreground CLI) wrap
this same object.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid

# The checkpoint ladder (§6.2). Every phase is an independently resumable stage.
CHECKPOINT_LADDER: tuple[str, ...] = (
    "acquired",
    "registered",
    "extracted",
    "inventoried",
    "synthesized",
    "proposed",
    "applied",
)

TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})
_UNFINISHED_STATUSES = frozenset({"failed", "blocked", "cancelled"})

# Application-validated open vocabularies (§6.2 — deliberately not SQL CHECKs).
KNOWN_WORKFLOW_TYPES = frozenset(
    {"import", "import_inventory", "legacy_ingest", "create_study_map", "update_study_map"}
)
KNOWN_JOB_TYPES = frozenset(
    {
        "import",
        "extract",
        "inventory",
        "legacy_ingest",
        "exam_ingest",
        "bootstrap_synthesis",
        "append_synthesis",
        "extraction_repair",
    }
)


class IngestRunnerError(ValueError):
    """A typed, user-actionable job failure persisted for the Activity UI."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_job",
        details: Mapping[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})
        self.retryable = retryable


class JobCancelled(Exception):
    """Raised from ``report()`` when a cancellation was requested mid-stage."""


class WaitingForInput(Exception):
    """A handler pauses the job pending user input (unit choice, consent, budget).

    Carries the actionable payload the Batch-progress UI renders as a card. The
    job releases its lease so the rest of the queue keeps draining (§6.2)."""

    def __init__(self, payload: Mapping[str, Any], *, message: str = "Waiting for input") -> None:
        self.payload = dict(payload)
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class FetchedBytes:
    raw_bytes: bytes
    content_type: str | None
    original_uri: str
    retrieved_at: str
    # Human-readable metadata captured during the fetch phase, when the source
    # kind exposes it cheaply (e.g. a YouTube video's title + channel via oEmbed).
    # Absent (None/()) for sources with no knowable metadata — the import then
    # falls back to the URL title as before.
    title: str | None = None
    authors: tuple[str, ...] = ()


@dataclass
class RunnerServices:
    """The side-effecting seams the M2 handlers need. Real by default; tests
    inject deterministic stubs so no network/LLM/marker runs."""

    fetch: Callable[[str, str, "JobContext"], FetchedBytes] | None = None
    extract: Callable[[FetchedBytes, str, "JobContext"], Any] | None = None
    describe_extraction: Callable[[FetchedBytes, str, "JobContext"], Mapping[str, Any]] | None = None
    run_legacy_ingest: Callable[..., Any] | None = None
    inventory_client_factory: Callable[["JobContext"], Any] | None = None
    synthesis_client_factory: Callable[["JobContext"], Any] | None = None
    quick_check_client_factory: Callable[["JobContext"], Any] | None = None
    rung_variant_client_factory: Callable[["JobContext"], Any] | None = None
    exercise_import_client_factory: Callable[["JobContext"], Any] | None = None

    def fetch_bytes(self, source: str, category: str, ctx: "JobContext") -> FetchedBytes:
        return (self.fetch or default_fetch)(source, category, ctx)

    def extract_ir(self, fetched: FetchedBytes, category: str, ctx: "JobContext") -> Any:
        return (self.extract or default_extract)(fetched, category, ctx)

    def extraction_identity(
        self, fetched: FetchedBytes, category: str, ctx: "JobContext"
    ) -> Mapping[str, Any]:
        return (self.describe_extraction or default_extraction_identity)(fetched, category, ctx)

    def legacy_ingest(self, **kwargs: Any) -> Any:
        return (self.run_legacy_ingest or default_run_legacy_ingest)(**kwargs)

    def inventory_client(self, ctx: "JobContext") -> Any:
        client = (self.inventory_client_factory or default_inventory_client)(ctx)
        ctx.bind_interruptible(client)
        return client

    def synthesis_client(self, ctx: "JobContext") -> Any:
        client = (self.synthesis_client_factory or default_synthesis_client)(ctx)
        ctx.bind_interruptible(client)
        return client

    def quick_check_client(self, ctx: "JobContext") -> Any:
        # Reader quick checks ride the inventory resolver (low-effort on codex
        # vaults, routed elsewhere): the task method is getattr-discovered on
        # the client, exactly like unit inventory.
        return (self.quick_check_client_factory or default_inventory_client)(ctx)

    def rung_variant_client(self, ctx: "JobContext") -> Any:
        client = (self.rung_variant_client_factory or default_rung_variant_client)(ctx)
        ctx.bind_interruptible(client)
        return client

    def exercise_import_client(self, ctx: "JobContext") -> Any:
        # Reader exercise imports ride the codex-only resolver: the task method
        # is getattr-discovered on the SDK client, like reader quick checks.
        client = (self.exercise_import_client_factory or default_inventory_client)(ctx)
        ctx.bind_interruptible(client)
        return client


@dataclass
class JobContext:
    """What a handler is handed: repository, vault root, payload, and the
    checkpoint/usage/cancellation primitives the runner threads through."""

    repo: Repository
    vault_root: Path
    job: dict[str, Any]
    clock: Clock
    worker_id: str
    services: RunnerServices = field(default_factory=RunnerServices)
    _usage: dict[str, Any] = field(default_factory=dict)
    _phase: str | None = None
    _bind_interruptible: Callable[[Any], None] | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return dict(self.job.get("payload") or {})

    @property
    def job_id(self) -> str:
        return self.job["id"]

    def report(
        self,
        phase: str,
        *,
        message: str | None = None,
        current_window: int | None = None,
        total_windows: int | None = None,
    ) -> None:
        """Advance the checkpoint ladder and refresh the lease heartbeat.

        Raises :class:`JobCancelled` when cancellation was requested, so long
        handlers abort cleanly at their next checkpoint (§6.2 — cancellation is
        honored between stages)."""

        if self._cancel_requested():
            raise JobCancelled()
        self._phase = phase
        self.repo.heartbeat_ingest_job(
            self.job_id,
            worker_id=self.worker_id,
            phase=phase,
            message=message or _phase_message(phase),
            current_window=current_window,
            total_windows=total_windows,
        )

    def record_usage(self, usage: Mapping[str, Any]) -> None:
        """Add one call's usage to the running per-attempt sum (§6.2)."""

        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._usage[key] = _as_number(self._usage.get(key, 0)) + value
            else:
                self._usage[key] = value

    def cancelled(self) -> bool:
        return self._cancel_requested()

    def bind_interruptible(self, client: Any) -> None:
        """Expose a job-scoped provider's interrupt hook to the worker host."""

        if self._bind_interruptible is not None:
            self._bind_interruptible(client)

    def _cancel_requested(self) -> bool:
        fresh = self.repo.get_ingest_job(self.job_id)
        if fresh is not None and fresh.get("cancel_requested"):
            return True
        batch = self.repo.get_ingest_batch(self.job["batch_id"])
        return bool(batch and batch.get("cancel_requested"))


Handler = Callable[[JobContext], dict[str, Any] | None]


@dataclass(frozen=True)
class JobSpec:
    """One job in an enqueued batch. ``depends_on`` is a tuple of indices into
    the batch's job list (topologically before this job)."""

    job_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    depends_on: tuple[int, ...] = ()


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
    from learnloop.services import source_ingestion

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
    pypdf fallback, or auto); everything else gets honest trivial IR from its
    decoded text (§2.3)."""

    from learnloop.ingest.extractors import MarkerUnavailableError, markdown_to_ir, pdf_extractor_for
    from learnloop.ingest.extractors.base import ExtractionContext

    is_pdf = (
        category == "pdf"
        or (fetched.content_type or "").lower().startswith("application/pdf")
        or fetched.raw_bytes[:5] == b"%PDF-"
    )
    if is_pdf:
        pdf_config = _pdf_payload_config(ctx)
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

    is_pdf = (
        category == "pdf"
        or (fetched.content_type or "").lower().startswith("application/pdf")
        or fetched.raw_bytes[:5] == b"%PDF-"
    )
    config = _pdf_payload_config(ctx)
    if is_pdf:
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

    from learnloop.ai.client import make_ai_provider_client
    from learnloop.ai.routing import fallback_provider_for, provider_for_task
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.codex.client import make_codex_client
    from learnloop.codex.runtime import check_codex_runtime
    from learnloop.services.exam_seeding import exam_ingest_instructions
    from learnloop.services.source_ingestion import ingest_canonical_source
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault_root)
    config = vault.config

    def _runtime(name: str):
        if name == "codex":
            return check_codex_runtime(vault_root, config.codex)
        return check_ai_runtime(vault_root, config, provider_name=name)

    def _client(name: str):
        if name == "codex":
            return make_codex_client(config.codex, vault_root)
        return make_ai_provider_client(config, vault_root, provider_name=name)

    selection = provider_for_task(config, "canonical_ingest")
    provider_name = selection.provider_name
    runtime = _runtime(provider_name)
    client = _client(provider_name) if runtime.ready else None
    if client is None:
        fallback = fallback_provider_for(config, selection)
        if fallback:
            fallback_runtime = _runtime(fallback)
            if fallback_runtime.ready:
                provider_name, runtime, client = fallback, fallback_runtime, _client(fallback)
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


def default_inventory_client(ctx: JobContext) -> Any:
    """Resolve the unit-inventory/quick-check client through ai routing (§7).

    Routed via the ``canonical_ingest`` task (empty routing follows
    ai.active_provider), except codex-family routes are pinned to the
    LOW-effort codex profile: unit inventories deliberately stay cheap while
    synthesis follows the routed medium-effort profile
    (``default_synthesis_client``). The inventory/quick-check methods are
    getattr-discovered on the client, so a provider lacking them degrades to
    an explicit unavailable error rather than fabricating rows."""

    from learnloop.ai.client import make_ai_provider_client
    from learnloop.ai.routing import fallback_provider_for, provider_for_task
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.codex.client import make_codex_client
    from learnloop.codex.runtime import check_codex_runtime
    from learnloop.config import CODEX_LOW_PROVIDER, CODEX_PROVIDER_NAMES
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    config = vault.config

    def _runtime(name: str):
        if name == "codex":
            return check_codex_runtime(ctx.vault_root, config.codex)
        return check_ai_runtime(ctx.vault_root, config, provider_name=name)

    def _client(name: str):
        if name == "codex":
            return make_codex_client(config.codex, ctx.vault_root)
        return make_ai_provider_client(config, ctx.vault_root, provider_name=name)

    selection = provider_for_task(config, "canonical_ingest")
    provider_name = selection.provider_name
    if provider_name in CODEX_PROVIDER_NAMES:
        provider_name = CODEX_LOW_PROVIDER
    runtime = _runtime(provider_name)
    if runtime.ready:
        return _client(provider_name)
    fallback = fallback_provider_for(config, selection)
    if fallback:
        fallback_runtime = _runtime(fallback)
        if fallback_runtime.ready:
            return _client(fallback)
    raise IngestRunnerError(
        runtime.message or f"AI provider {provider_name!r} is {runtime.status}."
    )


def default_synthesis_client(ctx: JobContext) -> Any:
    """Resolve the canonical-ingest route for judgment-heavy synthesis.

    Unit inventories deliberately keep the low-effort legacy Codex client;
    synthesis follows the routed medium-effort profile and its fallback.
    """

    return _routed_task_client(ctx, "canonical_ingest")


def default_rung_variant_client(ctx: JobContext) -> Any:
    """Resolve the rung_variant route (default: the fast low-effort profile).

    A learner-requested variant is a small, instruction-constrained authoring
    task whose output the deterministic rung gate checks — it does not need the
    judgment-heavy synthesis profile, and the learner is actively waiting."""

    return _routed_task_client(ctx, "rung_variant")


def _routed_task_client(ctx: JobContext, task: str) -> Any:
    from learnloop.ai.client import make_ai_provider_client
    from learnloop.ai.routing import fallback_provider_for, provider_for_task
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.codex.client import make_codex_client
    from learnloop.codex.runtime import check_codex_runtime
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    selection = provider_for_task(vault.config, task)

    def ready_client(provider_name: str):
        if provider_name == "codex":
            runtime = check_codex_runtime(ctx.vault_root, vault.config.codex)
            client = (
                make_codex_client(vault.config.codex, ctx.vault_root)
                if runtime.ready
                else None
            )
        else:
            runtime = check_ai_runtime(ctx.vault_root, vault.config, provider_name=provider_name)
            client = (
                make_ai_provider_client(
                    vault.config,
                    ctx.vault_root,
                    provider_name=provider_name,
                )
                if runtime.ready
                else None
            )
        return runtime, client

    runtime, client = ready_client(selection.provider_name)
    if client is None:
        fallback = fallback_provider_for(vault.config, selection)
        if fallback:
            runtime, client = ready_client(fallback)
    if client is None:
        raise IngestRunnerError(runtime.message or f"Synthesis provider is {runtime.status}.")
    return client


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_inventory(ctx: JobContext) -> dict[str, Any]:
    """inventory: role-aware per-unit inventories for the selected units (§7).

    Depends on extraction (the runner enforces this via job dependencies).
    Payload: ``extraction_id`` and ``units`` = [{unit_id, role, profile?}]. Each
    unit is inventoried through the cache: a cache hit records ZERO tokens
    (``run_unit_inventory`` returns ``cache_hit``), and only semantic-hash-changed
    units are ever re-inventoried across collections/revisions (§3.2)."""

    from learnloop.services.source_unit_inventory import run_unit_inventory

    payload = ctx.payload
    extraction_id, units = _inventory_inputs(ctx, payload)
    if not extraction_id:
        raise IngestRunnerError("inventory job requires an 'extraction_id'.")
    if not units:
        raise IngestRunnerError("inventory job requires at least one unit.")
    budgets = _ingest_budgets(ctx)
    budget = _optional_int(payload.get("input_budget_tokens")) or budgets.inventory_input_tokens
    unlimited_token_budget = bool(payload.get("unlimited_token_budget", False))
    output_budget = (
        None
        if unlimited_token_budget
        else _optional_int(payload.get("output_budget_tokens")) or budgets.inventory_output_tokens
    )

    ctx.report("extracted", message="Preparing unit inventories")
    client = ctx.services.inventory_client(ctx)

    results: list[dict[str, Any]] = []
    total = len(units)
    for index, spec in enumerate(units):
        unit_id = str(spec.get("unit_id") or "").strip()
        if not unit_id:
            raise IngestRunnerError("every inventory unit needs a 'unit_id'.")
        ctx.report(
            "inventoried",
            message=f"Inventorying unit {index + 1} of {total}",
            current_window=index + 1,
            total_windows=total,
        )
        result = run_unit_inventory(
            ctx.repo,
            extraction_id,
            unit_id,
            role=str(spec.get("role") or "reference"),
            profile=spec.get("profile"),
            client=client,
            input_budget_tokens=budget,
            output_budget_tokens=output_budget,
            clock=ctx.clock,
        )
        ctx.record_usage(dict(result.usage or {}))
        results.append(
            {
                "unit_id": unit_id,
                "inventory_id": result.inventory_id,
                "profile": result.profile,
                "cache_hit": result.cache_hit,
                "reused_profile": result.reused_profile,
            }
        )

    ctx.report("inventoried", message="Unit inventories ready")
    return {
        "extraction_id": extraction_id,
        "units": results,
        "cache_hits": sum(1 for row in results if row["cache_hit"]),
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


def handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]:
    """bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).

    Depends on all selected unit-inventory jobs (the runner enforces this via
    job dependencies). Payload: ``source_set_id`` plus optional ``brief``,
    ``mode``, ``apply``, ``create_goal``. Emits the dependency-closed proposal
    through the existing pipeline; the manifest hash is the agent-run cache seam
    so an identical manifest re-drains at zero tokens."""

    from learnloop.services.source_set_synthesis import (
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
        from learnloop.services.source_append import subject_has_applied_study_map
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

    from learnloop.services.source_append import append_source
    from learnloop.services.source_set_synthesis import StudyMapError

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
    from learnloop.ingest.source_library import register_source_revision

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

    from learnloop.services import reader_quick_check as RQC

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

    from learnloop.services import exercise_authoring as EX

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

    from learnloop.services.practice_generation import (
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


def handle_rung_variant(ctx: JobContext) -> dict[str, Any]:
    """rung_variant: author one learner-requested easier/harder sibling item.

    The evidence package was written synchronously at request time; this job is
    only the generation half. Payload: ``request_id``. The service owns the
    request-row status transitions (applied / review_required / failed)."""

    from learnloop.services.rung_variants import RungVariantError, generate_rung_variant

    request_id = str(ctx.payload.get("request_id") or "")
    if not request_id:
        raise IngestRunnerError("rung_variant job requires a 'request_id'.")
    ctx.report("generation", message="Authoring the requested variant")
    client = ctx.services.rung_variant_client(ctx)
    try:
        return generate_rung_variant(ctx.vault_root, client, request_id=request_id, clock=ctx.clock)
    except RungVariantError as exc:
        raise IngestRunnerError(str(exc)) from exc


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
    "rung_variant": handle_rung_variant,
}


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------


class IngestRunner:
    def __init__(
        self,
        repo: Repository,
        *,
        vault_root: Path,
        worker_id: str,
        clock: Clock | None = None,
        handlers: Mapping[str, Handler] | None = None,
        services: RunnerServices | None = None,
        lease_ttl_seconds: int = 120,
        heartbeat_interval_seconds: float = 15,
    ) -> None:
        self.repo = repo
        self.vault_root = Path(vault_root)
        self.worker_id = worker_id
        self.clock = clock or SystemClock()
        self.handlers: dict[str, Handler] = {**DEFAULT_HANDLERS, **dict(handlers or {})}
        self.services = services or RunnerServices()
        self.lease_ttl_seconds = lease_ttl_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self._interrupt_lock = threading.RLock()
        self._active_interrupts: dict[str, Callable[[], Any]] = {}

    def active_interruptible_jobs(self) -> list[dict[str, Any]]:
        """Return running jobs that currently own an interruptible AI client."""

        with self._interrupt_lock:
            job_ids = list(self._active_interrupts)
        jobs: list[dict[str, Any]] = []
        for job_id in job_ids:
            job = self.repo.get_ingest_job(job_id)
            if job is not None and job.get("status") == "running":
                jobs.append(job)
        return jobs

    def interrupt_job(self, job_id: str) -> bool:
        """Cancel a batch and interrupt the selected job's active provider call."""

        with self._interrupt_lock:
            interrupt = self._active_interrupts.get(job_id)
        if interrupt is None:
            return False
        job = self.repo.get_ingest_job(job_id)
        if job is None or job.get("status") != "running":
            return False
        # Cancel queued siblings too, matching the existing batch-cancel contract
        # and preventing dependants of the interrupted job from remaining queued.
        self.cancel_batch(job["batch_id"])
        interrupt()
        return True

    def _bind_job_interruptible(self, job_id: str, client: Any) -> None:
        interrupt = getattr(client, "interrupt", None)
        if not callable(interrupt):
            return
        with self._interrupt_lock:
            self._active_interrupts[job_id] = interrupt

    def _clear_job_interruptible(self, job_id: str) -> None:
        with self._interrupt_lock:
            self._active_interrupts.pop(job_id, None)

    # -- enqueue -----------------------------------------------------------

    def enqueue_batch(
        self,
        workflow_type: str,
        jobs: Sequence[JobSpec],
        *,
        subject_id: str | None = None,
        source_set_id: str | None = None,
        priority: int = 0,
    ) -> str:
        if not jobs:
            raise IngestRunnerError("a batch needs at least one job.")
        for spec in jobs:
            if not spec.job_type:
                raise IngestRunnerError("every job needs a job_type.")
        batch_id = f"batch_{new_ulid()}"
        self.repo.insert_ingest_batch(
            id=batch_id,
            workflow_type=workflow_type,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
            clock=self.clock,
        )
        job_ids: list[str] = []
        for ordinal, spec in enumerate(jobs):
            job_id = f"ijob_{new_ulid()}"
            self.repo.insert_ingest_job(
                id=job_id,
                batch_id=batch_id,
                ordinal=ordinal,
                job_type=spec.job_type,
                payload=dict(spec.payload),
                clock=self.clock,
            )
            job_ids.append(job_id)
        for ordinal, spec in enumerate(jobs):
            for dep_index in spec.depends_on:
                if dep_index < 0 or dep_index >= len(jobs) or dep_index == ordinal:
                    raise IngestRunnerError(f"invalid dependency index {dep_index}.")
                self.repo.add_ingest_job_dependency(job_ids[ordinal], job_ids[dep_index])
        self._refresh_batch(batch_id)
        return batch_id

    # -- recovery / drive --------------------------------------------------

    def recover_stale_leases(self) -> list[str]:
        """Startup recovery (§6.2): expired ``running`` leases -> ``failed(interrupted)``;
        their queued siblings simply resume. Returns the recovered job ids."""

        cutoff = self._lease_cutoff_iso()
        recovered: list[str] = []
        for job in self.repo.expired_running_ingest_jobs(cutoff):
            self.repo.finish_ingest_job(
                job["id"],
                status="failed",
                phase="failed",
                message="Interrupted before completion",
                error={"code": "interrupted", "message": "Worker lease expired before the job finished."},
                clock=self.clock,
            )
            recovered.append(job["id"])
            self._propagate_blocks(job["batch_id"])
            self._refresh_batch(job["batch_id"])
        # Startup hygiene: historical error paths left synthesis_runs rows in
        # 'created'/'running' forever. Finalize abandoned rows — but never while
        # any synthesis job still holds a live lease (its run row is legitimately
        # non-terminal mid-flight).
        live_synthesis = any(
            job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
            and job["status"] == "running"
            and (job.get("heartbeat_at") or "") >= cutoff
            for job in self.repo.ingest_jobs_by_types(("bootstrap_synthesis", "append_synthesis"))
        )
        if not live_synthesis:
            self.repo.finalize_stale_synthesis_runs(before_iso=cutoff, clock=self.clock)
        return recovered

    def run_next(
        self,
        *,
        eligible_job_types: Sequence[str] | None = None,
        compatible_running_job_types: Sequence[str] = (),
        allow_parallel: bool = False,
        max_parallel: int | None = None,
    ) -> bool:
        """Claim and run one eligible job. Returns False when nothing was run
        (no eligible job, or another worker holds the drain lease)."""

        job = self.repo.claim_next_ingest_job(
            worker_id=self.worker_id,
            now_iso=utc_now_iso(self.clock),
            lease_cutoff_iso=self._lease_cutoff_iso(),
            eligible_job_types=eligible_job_types,
            compatible_running_job_types=compatible_running_job_types,
            allow_parallel=allow_parallel,
            max_parallel=max_parallel,
        )
        if job is None:
            return False
        self._run_claimed(job)
        return True

    def drain(
        self,
        *,
        max_jobs: int | None = None,
        eligible_job_types: Sequence[str] | None = None,
        compatible_running_job_types: Sequence[str] = (),
        allow_parallel: bool = False,
        max_parallel: int | None = None,
    ) -> int:
        """Drain matching jobs until none remain (or ``max_jobs``)."""

        ran = 0
        while max_jobs is None or ran < max_jobs:
            if not self.run_next(
                eligible_job_types=eligible_job_types,
                compatible_running_job_types=compatible_running_job_types,
                allow_parallel=allow_parallel,
                max_parallel=max_parallel,
            ):
                break
            ran += 1
        return ran

    # -- batch lifecycle ---------------------------------------------------

    def cancel_batch(self, batch_id: str) -> None:
        """Request cancellation. Completed artifacts are preserved; not-yet-run
        jobs go straight to ``cancelled`` and a running job is flagged so its
        handler stops at the next checkpoint (§6.2)."""

        self.repo.request_ingest_batch_cancel(batch_id)
        for job in self.repo.ingest_jobs_for_batch(batch_id):
            if job["status"] in {"queued", "blocked", "waiting_for_input"}:
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Batch cancelled",
                    error={"code": "cancelled", "message": "The batch was cancelled."},
                    clock=self.clock,
                )
        self._refresh_batch(batch_id)

    def resume_batch(self, batch_id: str) -> None:
        """Resume a partially-complete or cancelled batch: only unfinished jobs
        (failed/blocked/cancelled) are re-queued; completed jobs are preserved,
        so a resume creates new attempts only for what did not finish (§6.2)."""

        batch = self.repo.get_ingest_batch(batch_id)
        if batch is None:
            raise IngestRunnerError(f"batch '{batch_id}' does not exist.")
        with self.repo.connection() as connection:
            connection.execute(
                "UPDATE ingest_batches SET cancel_requested = 0 WHERE id = ?", (batch_id,)
            )
            connection.commit()
        for job in self.repo.ingest_jobs_for_batch(batch_id):
            if job["status"] in _UNFINISHED_STATUSES:
                self.repo.requeue_ingest_job(job["id"], clock=self.clock)
        self._refresh_batch(batch_id)

    # -- internals ---------------------------------------------------------

    def _run_claimed(self, job: dict[str, Any]) -> None:
        batch_id = job["batch_id"]
        self.repo.update_ingest_batch_status(batch_id, "running", mark_started=True, clock=self.clock)
        ctx = JobContext(
            repo=self.repo,
            vault_root=self.vault_root,
            job=dict(job),
            clock=self.clock,
            worker_id=self.worker_id,
            services=self.services,
            _usage=dict(job.get("usage") or {}),
            _bind_interruptible=lambda client: self._bind_job_interruptible(job["id"], client),
        )
        if ctx.cancelled():
            self.repo.finish_ingest_job(
                job["id"],
                status="cancelled",
                phase="cancelled",
                message="Batch cancelled",
                error={"code": "cancelled", "message": "The batch was cancelled."},
                usage=ctx._usage or None,
                clock=self.clock,
            )
            self._refresh_batch(batch_id)
            return
        handler = self.handlers.get(job["job_type"])
        try:
            if handler is None:
                raise IngestRunnerError(f"unknown job_type '{job['job_type']}'.")
            heartbeat_stop = threading.Event()
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_while_running,
                args=(job["id"], heartbeat_stop),
                name=f"ingest-heartbeat-{job['id']}",
                daemon=True,
            )
            heartbeat_thread.start()
            try:
                result = handler(ctx)
            finally:
                heartbeat_stop.set()
                heartbeat_thread.join(timeout=1)
        except JobCancelled:
            self.repo.finish_ingest_job(
                job["id"],
                status="cancelled",
                phase="cancelled",
                message="Cancelled",
                error={"code": "cancelled", "message": "The job was cancelled."},
                usage=ctx._usage or None,
                clock=self.clock,
            )
        except WaitingForInput as waiting:
            self.repo.finish_ingest_job(
                job["id"],
                status="waiting_for_input",
                phase="waiting_for_input",
                message=waiting.message,
                result={"waiting_for_input": waiting.payload},
                usage=ctx._usage or None,
                release_lease=True,
                clear_finished=True,
                clock=self.clock,
            )
        except NotImplementedError as exc:
            self.repo.finish_ingest_job(
                job["id"],
                status="failed",
                phase="failed",
                message=str(exc),
                error={"code": "not_implemented", "message": str(exc)},
                usage=ctx._usage or None,
                clock=self.clock,
            )
            self._propagate_blocks(batch_id)
        except Exception as exc:  # noqa: BLE001 — a failed job must never crash the drain
            if ctx.cancelled():
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Codex call interrupted",
                    error={"code": "cancelled", "message": "The Codex call was interrupted."},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
            else:
                error = {"code": _error_code(exc), "message": str(exc) or exc.__class__.__name__}
                if isinstance(exc, IngestRunnerError):
                    error["details"] = exc.details
                    error["retryable"] = exc.retryable
                self.repo.finish_ingest_job(
                    job["id"],
                    status="failed",
                    phase="failed",
                    message=str(exc) or exc.__class__.__name__,
                    error=error,
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
                self._propagate_blocks(batch_id)
        else:
            if ctx.cancelled():
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Codex call interrupted",
                    error={"code": "cancelled", "message": "The Codex call was interrupted."},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
            else:
                self.repo.finish_ingest_job(
                    job["id"],
                    status="completed",
                    phase=ctx._phase or "applied",
                    message="Completed",
                    result=result if result is not None else {},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
        self._clear_job_interruptible(job["id"])
        self._refresh_batch(batch_id)

    def _heartbeat_while_running(self, job_id: str, stop: threading.Event) -> None:
        """Keep a blocking extractor/LLM stage's lease alive until it returns."""

        interval = max(0.01, self.heartbeat_interval_seconds)
        while not stop.wait(interval):
            self.repo.heartbeat_ingest_job(
                job_id,
                worker_id=self.worker_id,
                clock=self.clock,
            )

    def _propagate_blocks(self, batch_id: str) -> None:
        """Mark every downstream queued job blocked when a dependency failed,
        blocked, or was cancelled — to a fixpoint (§6.2)."""

        changed = True
        while changed:
            changed = False
            jobs = {job["id"]: job for job in self.repo.ingest_jobs_for_batch(batch_id)}
            for job in jobs.values():
                if job["status"] != "queued":
                    continue
                for dep_id in self.repo.ingest_job_dependency_ids(job["id"]):
                    dep = jobs.get(dep_id)
                    if dep is not None and dep["status"] in _UNFINISHED_STATUSES:
                        self.repo.finish_ingest_job(
                            job["id"],
                            status="blocked",
                            phase="blocked",
                            message="Blocked by a failed dependency",
                            error={
                                "code": "dependency_failed",
                                "message": f"Dependency {dep_id} did not complete.",
                            },
                            clock=self.clock,
                        )
                        changed = True
                        break

    def _refresh_batch(self, batch_id: str) -> None:
        jobs = self.repo.ingest_jobs_for_batch(batch_id)
        status = derive_batch_status(jobs, self.repo.get_ingest_batch(batch_id))
        terminal = status in {"completed", "failed", "cancelled"}
        # A resumed/retried batch must not keep reporting the prior failure's
        # finished_at while it is running again.
        self.repo.update_ingest_batch_status(
            batch_id, status, mark_finished=terminal, clear_finished=not terminal, clock=self.clock
        )

    def _lease_cutoff_iso(self) -> str:
        cutoff = self.clock.now() - timedelta(seconds=self.lease_ttl_seconds)
        return utc_now_iso(_FixedClock(cutoff))


@dataclass(frozen=True)
class _FixedClock:
    instant: Any

    def now(self):
        return self.instant


def derive_batch_status(jobs: Sequence[Mapping[str, Any]], batch: Mapping[str, Any] | None) -> str:
    """Batch status is derived from its member jobs and can represent partial
    completion (§6.2)."""

    statuses = [job["status"] for job in jobs]
    if not statuses:
        return "queued"
    if all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "running" for status in statuses):
        return "running"
    if any(status == "queued" for status in statuses):
        return "queued" if all(s == "queued" for s in statuses) else "running"
    if any(status == "waiting_for_input" for status in statuses):
        return "waiting_for_input"
    # No active jobs remain: everything is terminal or blocked.
    if all(status == "cancelled" for status in statuses):
        return "cancelled"
    if batch is not None and batch.get("cancel_requested") and "cancelled" in statuses and "failed" not in statuses:
        return "cancelled"
    if any(status in {"failed", "blocked"} for status in statuses):
        return "failed"
    return "completed"


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

_PHASE_MESSAGES = {
    "acquired": "Fetching source material",
    "registered": "Registered source revision",
    "extracted": "Extracted document structure",
    "inventoried": "Building unit inventories",
    "synthesized": "Synthesizing the study map",
    "proposed": "Preparing the authoring proposal",
    "applied": "Applied",
}


def _phase_message(phase: str) -> str:
    return _PHASE_MESSAGES.get(phase, phase.replace("_", " ").capitalize())


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _as_number(value: Any) -> float | int:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return 0


def _error_code(exc: Exception) -> str:
    if isinstance(exc, IngestRunnerError):
        return exc.code
    if isinstance(exc, TimeoutError):
        return "timeout"
    return exc.__class__.__name__
