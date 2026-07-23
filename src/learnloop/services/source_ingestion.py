from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Literal

from learnloop.ai.client import AIProviderClient
from learnloop.clock import Clock, utc_now_iso
from learnloop.config import PdfIngestConfig
from learnloop.codex.client import CanonicalIngestContext, CodexClient, ExtractionPlan, SourceChunk, SourceKind
from learnloop.codex.prompts import CANONICAL_INGEST_PROMPT_VERSION
from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.ids import kebab_case, new_ulid, snake_case
from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.resolution import ResolvedSource, resolve_source
from learnloop.services.pdf_extraction import PdfExtractionError, extract_pdf_markdown
from learnloop.services.proposals import _auto_apply_rows, _proposal_item_row
from learnloop.vault.loader import add_subject, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_markdown_with_frontmatter, write_yaml

KindOption = Literal["auto", "website_page", "youtube_video", "arxiv_html", "textbook_chapter"]
IngestProgress = Callable[[str, dict[str, Any]], None]


class SourceIngestionError(ValueError):
    pass


@dataclass(frozen=True)
class FetchResult:
    raw_bytes: bytes
    content_type: str | None
    original_uri: str
    retrieved_at: str
    fetch_uri: str | None = None
    # Original document bytes when raw_bytes holds a converted form (e.g. the
    # PDF a Markdown conversion came from); retained alongside the note so the
    # true source survives re-extraction with a better engine later.
    source_bytes: bytes | None = None


@dataclass(frozen=True)
class CaptionCue:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class NormalizedSource:
    kind: SourceKind
    title: str
    authors: list[str]
    canonical_uri: str
    original_uri: str
    markdown: str
    retrieved_at: str
    license_hint: str | None = None
    captions: list[CaptionCue] = field(default_factory=list)
    labels: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RegisteredSource:
    note_id: str
    path: str
    subject_id: str
    canonical_source: dict[str, Any]


@dataclass(frozen=True)
class IngestWindow:
    chunks: list[SourceChunk]
    ordinal: int


@dataclass(frozen=True)
class IngestResult:
    patch_id: str | None
    agent_run_id: str | None
    source_note_id: str
    source_kind: SourceKind
    subject_id: str
    content_hash: str
    reused_existing: bool
    codex_calls: int
    auto_applied_count: int
    review_required_count: int
    invalid_count: int
    source_event_count: int = 0
    goal_id: str | None = None
    goal_created: bool = False
    goal_updated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.patch_id,
            "agent_run_id": self.agent_run_id,
            "source_note_id": self.source_note_id,
            "source_kind": self.source_kind,
            "subject_id": self.subject_id,
            "content_hash": self.content_hash,
            "reused_existing": self.reused_existing,
            "codex_calls": self.codex_calls,
            "auto_applied_count": self.auto_applied_count,
            "review_required_count": self.review_required_count,
            "invalid_count": self.invalid_count,
            "source_event_count": self.source_event_count,
            "goal_id": self.goal_id,
            "goal_created": self.goal_created,
            "goal_updated": self.goal_updated,
        }


@dataclass(frozen=True)
class SourceChangeAnalysis:
    events: list[dict[str, Any]]
    summary: str | None = None


def ingest_canonical_source(
    root: Path,
    source: str,
    codex_client: CodexClient | AIProviderClient,
    *,
    kind: KindOption = "auto",
    subject_id: str | None = None,
    learning_object_ids: list[str] | None = None,
    goal_id: str | None = None,
    allow_auto_captions: bool | None = None,
    instructions: str | None = None,
    model: str | None = None,
    codex_revision: str | None = None,
    retry_client: CodexClient | AIProviderClient | None = None,
    retry_model: str | None = None,
    retry_provider_revision: str | None = None,
    purpose: str = "canonical_ingest",
    pdf_engine: str | None = None,
    pdf_use_llm: bool | None = None,
    ir_markdown: str | None = None,
    clock: Clock | None = None,
    progress: IngestProgress | None = None,
) -> IngestResult:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    target_learning_object_ids = list(learning_object_ids or [])
    resolved_source, resolved_kind = resolve_canonical_source(
        source,
        kind=kind,
        learning_object_ids=target_learning_object_ids,
    )
    if allow_auto_captions is None:
        allow_auto_captions = vault.config.ingest.allow_auto_captions
    pdf_config = _resolved_pdf_config(vault.config.ingest.pdf, engine=pdf_engine, use_llm=pdf_use_llm)
    if goal_id is not None:
        _validate_active_goal(vault, goal_id)

    if resolved_kind == "textbook_chapter":
        _validate_textbook_targets(vault, subject_id, target_learning_object_ids)

    _report_progress(progress, "fetching", source_kind=resolved_kind)
    fetch_result = fetch_source(
        vault.root,
        resolved_source.source,
        kind=resolved_kind,
        allow_auto_captions=allow_auto_captions,
        pdf_config=pdf_config,
        clock=clock,
        progress=progress,
    )
    _report_progress(progress, "extracting", source_kind=resolved_kind)
    normalized = normalize_source(fetch_result, resolved_kind)
    # M3.5 v2-lite (§2.3): when a durable ExtractionRun already produced a Document
    # IR for this source, synthesis builds its chunk context from the IR's
    # deterministic display rendering (respecting a persisted unit selection)
    # instead of the legacy extraction. Sources without an IR pass ``ir_markdown``
    # as None and keep the legacy markdown byte-for-byte. Caption-based sources
    # (YouTube) still chunk from their cues, so only the display body is swapped.
    if ir_markdown is not None:
        normalized = replace(normalized, markdown=ir_markdown)
    content_hash = source_content_hash(normalized.markdown)
    chunks = chunk_normalized_source(normalized)
    _validate_usable_source(chunks, vault.config.ingest.min_content_chars)

    _report_progress(progress, "staging", source_kind=resolved_kind)
    subject = _resolve_subject(vault.root, normalized, subject_id, resolved_kind, target_learning_object_ids, content_hash, clock=clock)
    change_analysis = analyze_source_change(
        load_vault(vault.root),
        normalized,
        chunks,
        content_hash,
        clock=clock,
    )
    registered = register_canonical_source(
        vault.root,
        subject,
        normalized,
        fetch_result.source_bytes or fetch_result.raw_bytes,
        content_hash,
        clock=clock,
    )
    vault = load_vault(vault.root)
    repository = Repository(paths.sqlite_path)
    context_hash = canonical_ingest_context_hash(
        normalized.canonical_uri,
        content_hash,
        resolved_kind,
        target_learning_object_ids,
    )
    completed = repository.completed_agent_run_by_context(purpose, context_hash)
    if completed is not None:
        batch = repository.proposal_batch_for_agent_run(completed["id"])
        return _result_from_existing_batch(
            completed,
            batch,
            registered,
            resolved_kind,
            content_hash,
        )

    windows = build_ingest_windows(chunks, window_char_cap=vault.config.ingest.window_char_cap)
    now = utc_now_iso(clock)
    provider_fields = _agent_provider_fields(codex_client, model=model, provider_revision=codex_revision)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": purpose,
            **provider_fields,
            "prompt_template": "canonical-ingestor",
            "prompt_version": CANONICAL_INGEST_PROMPT_VERSION,
            "input_context_hash": context_hash,
            "output_schema": "AuthoringProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        merged = _run_ingest_windows(
            codex_client,
            vault,
            registered,
            normalized,
            windows,
            target_learning_object_ids=target_learning_object_ids,
            instructions=instructions,
            progress=progress,
        )
        if change_analysis.summary:
            merged = _proposal_with_change_summary(merged, change_analysis.summary)
        proposal_payload = merged.model_dump(mode="json", exclude_none=False)
        vault_for_validation = load_vault(vault.root)
        rows = [
            _proposal_item_row(item, now, vault=vault_for_validation, proposal=merged, provider=provider_fields["provider"] or "codex")
            for item in merged.items
        ]
        _downgrade_unready_auto_apply(rows, vault_for_validation)
        if retry_client is not None and any(row["validation_status"] == "invalid" for row in rows):
            repository.complete_agent_run(
                agent_run_id,
                status="failed",
                error_message="canonical_ingest_validation_failed; retrying with stronger provider",
                clock=clock,
            )
            provider_fields = _agent_provider_fields(
                retry_client,
                model=retry_model,
                provider_revision=retry_provider_revision,
            )
            agent_run_id = repository.insert_agent_run(
                {
                    "id": new_ulid(),
                    "purpose": purpose,
                    **provider_fields,
                    "prompt_template": "canonical-ingestor",
                    "prompt_version": CANONICAL_INGEST_PROMPT_VERSION,
                    "input_context_hash": context_hash,
                    "output_schema": "AuthoringProposal",
                    "started_at": utc_now_iso(clock),
                    "status": "running",
                }
            )
            merged = _run_ingest_windows(
                retry_client,
                vault,
                registered,
                normalized,
                windows,
                target_learning_object_ids=target_learning_object_ids,
                instructions=instructions,
                progress=progress,
            )
            if change_analysis.summary:
                merged = _proposal_with_change_summary(merged, change_analysis.summary)
            proposal_payload = merged.model_dump(mode="json", exclude_none=False)
            vault_for_validation = load_vault(vault.root)
            rows = [
                _proposal_item_row(
                    item,
                    now,
                    vault=vault_for_validation,
                    proposal=merged,
                    provider=provider_fields["provider"] or "codex",
                )
                for item in merged.items
            ]
            _downgrade_unready_auto_apply(rows, vault_for_validation)
        patch_id = repository.persist_proposal_batch(
            {
                "id": new_ulid(),
                "agent_run_id": agent_run_id,
                "purpose": purpose,
                "source_refs": proposal_payload["source_refs"],
                "summary": merged.summary,
                "created_at": now,
                "updated_at": now,
            },
            rows,
        )
        _auto_apply_rows(vault.root, patch_id, rows)
        linkage = _establish_goal_linkage(
            vault.root,
            subject,
            normalized.title,
            merged,
            goal_id=goal_id,
            default_priority=vault.config.ingest.default_goal_priority,
            clock=clock,
        )
        repository.record_content_events(change_analysis.events)
        repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    except Exception as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise

    return IngestResult(
        patch_id=patch_id,
        agent_run_id=agent_run_id,
        source_note_id=registered.note_id,
        source_kind=resolved_kind,
        subject_id=subject,
        content_hash=content_hash,
        reused_existing=False,
        codex_calls=len(windows),
        auto_applied_count=sum(1 for row in rows if row.get("_auto_apply")),
        review_required_count=sum(
            1
            for row in rows
            if row["validation_status"] in {"valid", "warning"} and not row.get("_auto_apply")
        ),
        invalid_count=sum(1 for row in rows if row["validation_status"] == "invalid"),
        source_event_count=len(change_analysis.events),
        goal_id=linkage["goal_id"],
        goal_created=linkage["created"],
        goal_updated=linkage["updated"],
    )


def _run_ingest_windows(
    client: CodexClient | AIProviderClient,
    vault,
    registered: RegisteredSource,
    normalized: NormalizedSource,
    windows: list[IngestWindow],
    *,
    target_learning_object_ids: list[str],
    instructions: str | None,
    progress: IngestProgress | None = None,
) -> AuthoringProposal:
    proposals: list[AuthoringProposal] = []
    for index, window in enumerate(windows, 1):
        _report_progress(
            progress,
            "authoring",
            current_window=index,
            total_windows=len(windows),
        )
        context = _canonical_context(
            vault,
            registered,
            normalized,
            window,
            target_learning_object_ids=target_learning_object_ids,
            instructions=instructions,
        )
        proposal = client.run_canonical_ingest(context)
        proposals.append(_proposal_with_locator_validation(proposal, registered, window))
    return merge_window_proposals(proposals)


def _report_progress(progress: IngestProgress | None, phase: str, **details: Any) -> None:
    if progress is not None:
        progress(phase, details)


def _proposal_with_change_summary(proposal: AuthoringProposal, summary: str) -> AuthoringProposal:
    return AuthoringProposal.model_validate(
        {
            "summary": f"{proposal.summary}\n\n{summary}",
            "source_refs": [ref.model_dump(mode="json", exclude_none=True) for ref in proposal.source_refs],
            "items": [item.model_dump(mode="json", exclude_none=True) for item in proposal.items],
        }
    )


def _agent_provider_fields(
    client: CodexClient | AIProviderClient,
    *,
    model: str | None,
    provider_revision: str | None,
) -> dict[str, str | None]:
    provider = getattr(client, "provider_name", None) or "codex"
    provider_type = getattr(client, "provider_type", None)
    resolved_model = model or getattr(client, "model", None)
    fields = {
        "model": resolved_model,
        "provider": provider,
        "provider_type": provider_type,
        "provider_revision": provider_revision,
    }
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = provider_revision
    return fields


def _downgrade_unready_auto_apply(rows: list[dict[str, Any]], vault) -> None:
    """Keep auto-apply from accepting dependents before their prerequisites exist.

    General proposal validation can look across a full proposal, but the current
    patch applier accepts one item at a time. Concepts are not auto-applied by
    policy, so a new LO that depends on a proposed concept must remain pending;
    likewise a PI must wait if its LO is not already live or auto-applied in
    this same ingest batch.
    """

    auto_learning_object_ids: set[str] = set(vault.learning_objects)
    for row in rows:
        if not row.get("_auto_apply") or row["item_type"] != "learning_object":
            continue
        concept_id = row["payload"].get("concept") or row["payload"].get("concept_id")
        if concept_id not in vault.concepts:
            row["_auto_apply"] = False
            continue
        learning_object_id = row["payload"].get("id") or row.get("target_entity_id")
        if learning_object_id:
            auto_learning_object_ids.add(str(learning_object_id))
    for row in rows:
        if not row.get("_auto_apply") or row["item_type"] != "practice_item":
            continue
        if row["payload"].get("learning_object_id") not in auto_learning_object_ids:
            row["_auto_apply"] = False
    for row in rows:
        if not row.get("_auto_apply") or row["item_type"] != "concept_edge":
            continue
        source = row["payload"].get("source") or row["payload"].get("source_concept_id")
        target = row["payload"].get("target") or row["payload"].get("target_concept_id")
        if source not in vault.concepts or target not in vault.concepts:
            row["_auto_apply"] = False


def _resolved_pdf_config(
    base: PdfIngestConfig,
    *,
    engine: str | None,
    use_llm: bool | None,
) -> PdfIngestConfig:
    if engine is None and use_llm is None:
        return base
    updates = base.model_dump()
    if engine is not None:
        updates["engine"] = engine
    if use_llm is not None:
        updates["use_llm"] = use_llm
    try:
        return PdfIngestConfig.model_validate(updates)
    except ValueError as exc:
        raise SourceIngestionError(f"invalid PDF extraction settings: {exc}") from exc


def detect_source_kind(
    source: str,
    *,
    kind: KindOption = "auto",
    learning_object_ids: list[str] | None = None,
) -> SourceKind:
    return resolve_canonical_source(source, kind=kind, learning_object_ids=learning_object_ids)[1]


def resolve_canonical_source(
    source: str,
    *,
    kind: KindOption = "auto",
    learning_object_ids: list[str] | None = None,
) -> tuple[ResolvedSource, SourceKind]:
    try:
        resolved = resolve_source(source)
    except UnsupportedSourceError as exc:
        raise SourceIngestionError(str(exc)) from exc
    if resolved.category == "audio":
        raise SourceIngestionError(
            "Audio sources are only supported by the durable import pipeline "
            "(canonical mode); exam seeding and the legacy one-shot path cannot read audio."
        )
    if kind != "auto":
        _validate_explicit_kind(kind)
        return resolved, kind
    if learning_object_ids:
        return resolved, "textbook_chapter"
    mapping: dict[str, SourceKind] = {
        "youtube": "youtube_video",
        "arxiv": "arxiv_html",
        "web": "website_page",
        "pdf": "website_page",
        "textfile": "website_page",
    }
    return resolved, mapping[resolved.category]


def fetch_source(
    root: Path,
    source: str,
    *,
    kind: SourceKind,
    allow_auto_captions: bool,
    pdf_config: PdfIngestConfig | None = None,
    clock: Clock | None = None,
    progress: IngestProgress | None = None,
) -> FetchResult:
    parsed = urllib.parse.urlparse(source)
    if kind == "youtube_video":
        return _fetch_youtube_transcript(source, allow_auto_captions=allow_auto_captions, clock=clock)
    if parsed.scheme in {"http", "https"}:
        fetch_uri = _canonical_fetch_uri(source, kind)
        fetched = _fetch_url(root, fetch_uri, original_uri=source, clock=clock)
        if _is_pdf_fetch(fetched):
            _report_progress(progress, "extracting", source_kind=kind)
            return _pdf_fetch_result(root, fetched.raw_bytes, fetched, pdf_config)
        return fetched
    path = Path(source).expanduser()
    if not path.exists() or not path.is_file():
        raise SourceIngestionError("unsupported or inaccessible source")
    if path.suffix.lower() == ".pdf":
        _report_progress(progress, "extracting", source_kind=kind)
        uri = path.resolve().as_uri()
        placeholder = FetchResult(
            raw_bytes=b"",
            content_type="application/pdf",
            original_uri=uri,
            fetch_uri=uri,
            retrieved_at=utc_now_iso(clock),
        )
        return _pdf_fetch_result(root, path.read_bytes(), placeholder, pdf_config)
    raw = path.read_bytes()
    text_suffixes = {".html", ".htm", ".md", ".markdown", ".mdown", ".txt", ".text", ".rst"}
    if path.suffix.lower() not in text_suffixes and b"\x00" in raw[:4096]:
        raise SourceIngestionError("unsupported or inaccessible source")
    content_type = _content_type_for_path(path)
    return FetchResult(
        raw_bytes=raw,
        content_type=content_type,
        original_uri=path.resolve().as_uri(),
        fetch_uri=path.resolve().as_uri(),
        retrieved_at=utc_now_iso(clock),
    )


def normalize_source(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource:
    if kind == "youtube_video":
        return _normalize_youtube(fetch_result, kind)
    if kind == "arxiv_html":
        return _normalize_arxiv_html(fetch_result, kind)
    return _normalize_website_like(fetch_result, kind)


def source_content_hash(markdown: str) -> str:
    normalized = markdown if markdown.endswith("\n") else markdown + "\n"
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def analyze_source_change(
    vault,
    source: NormalizedSource,
    new_chunks: list[SourceChunk],
    content_hash: str,
    *,
    clock: Clock | None = None,
) -> SourceChangeAnalysis:
    previous = _previous_registered_sources(vault, source.kind, source.canonical_uri, content_hash)
    if not previous:
        return SourceChangeAnalysis(events=[])
    new_locator_hashes = _locator_hashes(new_chunks)
    previous_chunks = {
        note.id: _chunks_for_note_body(source.kind, note.body)
        for note in previous
    }
    previous_maps = {
        note_id: _locator_hashes(chunks)
        for note_id, chunks in previous_chunks.items()
    }
    latest = max(previous, key=lambda note: note.updated_at or note.created_at or note.id)
    latest_hashes = previous_maps.get(latest.id, {})
    added = set(new_locator_hashes) - set(latest_hashes)
    removed = set(latest_hashes) - set(new_locator_hashes)
    changed = {
        locator
        for locator in set(new_locator_hashes) & set(latest_hashes)
        if new_locator_hashes[locator] != latest_hashes[locator]
    }
    summary = (
        "Source diff: "
        f"added {len(added)} locator(s), "
        f"removed {len(removed)} locator(s), "
        f"changed {len(changed)} locator(s)."
    )
    previous_by_id = {note.id: note for note in previous}
    previous_by_path = {note.path: note for note in previous if note.path}
    events: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    now = utc_now_iso(clock)
    for entity_type, entity_id, subject, source_refs in _grounded_entity_refs(vault):
        for ref in source_refs:
            if ref.ref_type != "canonical_source" or ref.locator is None:
                continue
            note = previous_by_id.get(ref.ref_id) or previous_by_path.get(ref.path)
            if note is None:
                continue
            old_chunks = previous_chunks.get(note.id, [])
            event_type: str | None = None
            new_ref_hash = _locator_hash_for_ref(new_chunks, ref.locator)
            old_ref_hash = _locator_hash_for_ref(old_chunks, ref.locator)
            if new_ref_hash is None:
                event_type = "source_span_removed"
            elif old_ref_hash is not None and old_ref_hash != new_ref_hash:
                event_type = "source_span_changed"
            if event_type is None:
                continue
            key = (entity_type, entity_id, ref.locator, event_type)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                {
                    "id": new_ulid(),
                    "event_type": event_type,
                    "subject": subject,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "origin": "codex",
                    "review_status": None,
                    "summary": (
                        f"{source.canonical_uri} locator {ref.locator} "
                        f"{'changed' if event_type == 'source_span_changed' else 'was removed'} in re-ingested source."
                    ),
                    "created_at": now,
                }
            )
    return SourceChangeAnalysis(events=events, summary=summary)


def chunk_normalized_source(source: NormalizedSource) -> list[SourceChunk]:
    if source.kind == "youtube_video" and source.captions:
        chunks = []
        for ordinal, cue in enumerate(source.captions, start=1):
            locator = f"t={cue.start:.1f}-{cue.end:.1f}"
            chunks.append(
                SourceChunk(
                    locator=locator,
                    text=cue.text,
                    chunk_kind="caption",
                    heading_path=[source.title],
                    ordinal=ordinal,
                )
            )
        return chunks
    chunks = chunk_markdown(source.markdown)
    if source.kind == "arxiv_html":
        chunks = _apply_arxiv_native_locator_overrides(chunks, source.labels)
    return chunks


def chunk_markdown(markdown: str) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    path: list[str] = ["root"]
    path_by_level: dict[int, str] = {1: "root"}
    heading_counts: dict[tuple[str, ...], int] = {}
    block_counts: dict[tuple[str, ...], dict[str, int]] = {}
    current: list[str] = []
    in_fence = False
    fence_kind = "code"

    def flush() -> None:
        nonlocal current, fence_kind
        text = "\n".join(current).strip()
        if not text:
            current = []
            return
        path_key = tuple(path)
        counters = block_counts.setdefault(path_key, {"prose": 0, "block": 0})
        kind = fence_kind if text.startswith("```") else ("math" if text.startswith("$$") else "prose")
        counter_name = "block" if kind in {"code", "math"} else "prose"
        counters[counter_name] += 1
        suffix = f"block{counters[counter_name]}" if counter_name == "block" else f"p{counters[counter_name]}"
        chunks.append(
            SourceChunk(
                locator="/".join([*path, suffix]),
                text=text,
                chunk_kind=kind,
                heading_path=list(path),
                ordinal=len(chunks) + 1,
            )
        )
        current = []
        fence_kind = "code"

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading and not in_fence:
            flush()
            level = len(heading.group(1))
            slug = kebab_case(_strip_markdown(heading.group(2))) or "section"
            parent = tuple(path_by_level[i] for i in sorted(path_by_level) if i < level)
            occurrence_key = (*parent, slug)
            occurrence = heading_counts.get(occurrence_key, 0) + 1
            heading_counts[occurrence_key] = occurrence
            slug = slug if occurrence == 1 else f"{slug}-{occurrence}"
            for existing_level in list(path_by_level):
                if existing_level >= level:
                    del path_by_level[existing_level]
            path_by_level[level] = slug
            path = [path_by_level[i] for i in sorted(path_by_level)]
            continue
        if line.startswith("```") or line.startswith("$$"):
            current.append(line)
            if not in_fence:
                in_fence = True
                fence_kind = "math" if line.startswith("$$") else "code"
            else:
                in_fence = False
            continue
        if not line.strip() and not in_fence:
            flush()
            continue
        current.append(line)
    flush()
    return chunks


def build_ingest_windows(chunks: list[SourceChunk], *, window_char_cap: int) -> list[IngestWindow]:
    if not chunks:
        return []
    total = sum(len(chunk.text) for chunk in chunks)
    if total <= window_char_cap:
        return [IngestWindow(chunks=chunks, ordinal=1)]

    sections: list[list[SourceChunk]] = []
    current_section: list[SourceChunk] = []
    current_key: str | None = None
    for chunk in chunks:
        key = chunk.heading_path[0] if chunk.heading_path else "root"
        if current_section and key != current_key:
            sections.append(current_section)
            current_section = []
        current_section.append(chunk)
        current_key = key
    if current_section:
        sections.append(current_section)

    windows: list[IngestWindow] = []
    current: list[SourceChunk] = []
    current_size = 0
    for section in sections:
        section_size = sum(len(chunk.text) for chunk in section)
        if current and current_size + section_size > window_char_cap:
            windows.append(IngestWindow(chunks=current, ordinal=len(windows) + 1))
            current = []
            current_size = 0
        current.extend(section)
        current_size += section_size
    if current:
        windows.append(IngestWindow(chunks=current, ordinal=len(windows) + 1))
    return windows


def canonical_ingest_context_hash(
    canonical_uri: str,
    content_hash: str,
    source_kind: SourceKind,
    target_learning_object_ids: list[str],
) -> str:
    payload = {
        "canonical_uri": canonical_uri,
        "content_hash": content_hash,
        "source_kind": source_kind,
        "target_learning_object_ids": sorted(target_learning_object_ids),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def register_canonical_source(
    root: Path,
    subject_id: str,
    source: NormalizedSource,
    raw_bytes: bytes,
    content_hash: str,
    *,
    clock: Clock | None = None,
) -> RegisteredSource:
    vault = load_vault(root)
    existing = _existing_registered_source(vault, source.kind, source.canonical_uri, content_hash)
    if existing is not None:
        _retain_raw_bytes(root, existing.note_id, content_hash, raw_bytes)
        return existing

    now = utc_now_iso(clock)
    note_id = _unique_note_id(vault, source.title, content_hash)
    paths = VaultPaths(vault.root, vault.config)
    note_path = paths.note_path(subject_id, note_id)
    canonical_source = {
        "kind": source.kind,
        "original_uri": source.original_uri,
        "canonical_uri": source.canonical_uri,
        "title": source.title,
        "authors": source.authors,
        "retrieved_at": source.retrieved_at,
        "content_hash": content_hash,
        "license_hint": source.license_hint,
    }
    if source.labels:
        canonical_source["labels"] = source.labels
    write_markdown_with_frontmatter(
        note_path,
        {
            "schema_version": 1,
            "id": note_id,
            "subjects": [subject_id],
            "related_los": [],
            "related_concepts": [],
            "source_type": "canonical_source",
            "canonical_source": canonical_source,
            "created_at": now,
            "updated_at": now,
        },
        source.markdown,
    )
    _retain_raw_bytes(root, note_id, content_hash, raw_bytes)
    return RegisteredSource(
        note_id=note_id,
        path=note_path.relative_to(root).as_posix(),
        subject_id=subject_id,
        canonical_source=canonical_source,
    )


def merge_window_proposals(proposals: list[AuthoringProposal]) -> AuthoringProposal:
    summaries: list[str] = []
    source_refs: list[dict[str, Any]] = []
    source_ref_keys: set[str] = set()
    items: list[dict[str, Any]] = []
    item_keys: set[str] = set()
    for proposal in proposals:
        if proposal.summary:
            summaries.append(proposal.summary)
        for ref in proposal.source_refs:
            dumped = ref.model_dump(mode="json", exclude_none=True)
            key = json.dumps(dumped, sort_keys=True, separators=(",", ":"))
            if key in source_ref_keys:
                continue
            source_ref_keys.add(key)
            source_refs.append(dumped)
        for item in proposal.items:
            key = item.proposed_entity_id or f"{item.item_type}:{item.operation}:{item.client_item_id}"
            if key in item_keys:
                continue
            item_keys.add(key)
            items.append(item.model_dump(mode="json", exclude_none=True))
    return AuthoringProposal.model_validate(
        {
            "summary": "\n\n".join(summaries) if summaries else "Canonical ingest proposal",
            "source_refs": source_refs,
            "items": items,
        }
    )


def _validate_explicit_kind(kind: str) -> None:
    if kind not in {"website_page", "youtube_video", "arxiv_html", "textbook_chapter"}:
        raise SourceIngestionError(f"unsupported source kind {kind}")


def _validate_textbook_targets(vault, subject_id: str | None, learning_object_ids: list[str]) -> None:
    if subject_id is None:
        raise SourceIngestionError("textbook_chapter ingestion requires --subject")
    if subject_id not in vault.subjects:
        raise SourceIngestionError(f"subject '{subject_id}' does not exist")
    if not learning_object_ids:
        raise SourceIngestionError("textbook_chapter ingestion requires --learning-object")
    missing = [learning_object_id for learning_object_id in learning_object_ids if learning_object_id not in vault.learning_objects]
    if missing:
        raise SourceIngestionError(f"unknown learning object anchor(s): {', '.join(missing)}")
    out_of_subject = [
        learning_object_id
        for learning_object_id in learning_object_ids
        if subject_id not in vault.learning_objects[learning_object_id].subjects
    ]
    if out_of_subject:
        raise SourceIngestionError(
            f"learning object anchor(s) not in subject '{subject_id}': {', '.join(out_of_subject)}"
        )


def _validate_active_goal(vault, goal_id: str) -> None:
    for goal in vault.goals:
        if goal.id == goal_id:
            if goal.status != "active":
                raise SourceIngestionError(f"goal '{goal_id}' is not active")
            return
    raise SourceIngestionError(f"goal '{goal_id}' is not active")


def _validate_usable_source(chunks: list[SourceChunk], min_content_chars: int) -> None:
    prose = sum(len(chunk.text.strip()) for chunk in chunks if chunk.chunk_kind in {"prose", "caption"})
    if not chunks or prose < min_content_chars:
        raise SourceIngestionError("source produced no usable content")


def _canonical_fetch_uri(source: str, kind: SourceKind) -> str:
    if kind != "arxiv_html":
        return source
    parsed = urllib.parse.urlparse(source)
    if parsed.netloc.lower().endswith("arxiv.org") and parsed.path.startswith(("/abs/", "/pdf/")):
        arxiv_id = parsed.path.split("/", 2)[-1].strip("/")
        if arxiv_id.lower().endswith(".pdf"):
            arxiv_id = arxiv_id[:-4]
        return urllib.parse.urlunparse(parsed._replace(path=f"/html/{arxiv_id}", query="", fragment=""))
    return source


def _fetch_url(root: Path, fetch_uri: str, *, original_uri: str, clock: Clock | None) -> FetchResult:
    cache_dir = root / ".learnloop" / "source-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(fetch_uri.encode("utf-8")).hexdigest()
    body_path = cache_dir / f"{key}.body"
    meta_path = cache_dir / f"{key}.json"
    request = urllib.request.Request(fetch_uri, headers={"User-Agent": "learnloop/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            content_type = response.headers.get_content_type()
    except urllib.error.URLError as exc:
        if body_path.exists() and meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            return FetchResult(
                raw_bytes=body_path.read_bytes(),
                content_type=metadata.get("content_type"),
                original_uri=metadata.get("original_uri", original_uri),
                retrieved_at=metadata["retrieved_at"],
                fetch_uri=metadata.get("fetch_uri", fetch_uri),
            )
        raise SourceIngestionError(f"unsupported or inaccessible source: {exc.reason}") from exc
    retrieved_at = utc_now_iso(clock)
    body_path.write_bytes(raw)
    meta_path.write_text(
        json.dumps(
            {
                "content_type": content_type,
                "original_uri": original_uri,
                "fetch_uri": fetch_uri,
                "retrieved_at": retrieved_at,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return FetchResult(raw_bytes=raw, content_type=content_type, original_uri=original_uri, retrieved_at=retrieved_at, fetch_uri=fetch_uri)


def _fetch_youtube_transcript(source: str, *, allow_auto_captions: bool, clock: Clock | None) -> FetchResult:
    video_id = _youtube_video_id(source)
    if video_id is None:
        raise SourceIngestionError("unsupported or inaccessible source")
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    except ImportError as exc:
        raise SourceIngestionError("youtube-transcript-api is required for youtube_video ingestion") from exc
    try:
        api = YouTubeTranscriptApi()
        transcripts = api.list(video_id) if hasattr(api, "list") else YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcripts.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            if not allow_auto_captions:
                raise SourceIngestionError("no human captions available; pass --allow-auto-captions to use auto captions")
            transcript = transcripts.find_generated_transcript(["en"])
        cues = _transcript_cues_to_raw_data(transcript.fetch())
    except (NoTranscriptFound, TranscriptsDisabled) as exc:
        raise SourceIngestionError("no usable captions available") from exc
    raw = json.dumps({"video_id": video_id, "cues": cues}, sort_keys=True).encode("utf-8")
    return FetchResult(
        raw_bytes=raw,
        content_type="application/json",
        original_uri=source,
        retrieved_at=utc_now_iso(clock),
        fetch_uri=f"https://www.youtube.com/watch?v={video_id}",
    )


def _transcript_cues_to_raw_data(fetched: Any) -> list[dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        raw = fetched.to_raw_data()
    else:
        raw = fetched
    cues: list[dict[str, Any]] = []
    for cue in raw:
        if isinstance(cue, dict):
            cues.append(
                {
                    "text": cue.get("text", ""),
                    "start": cue.get("start", 0.0),
                    "duration": cue.get("duration", 0.0),
                }
            )
        else:
            cues.append(
                {
                    "text": getattr(cue, "text", ""),
                    "start": getattr(cue, "start", 0.0),
                    "duration": getattr(cue, "duration", 0.0),
                }
            )
    return cues


def _normalize_website_like(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource:
    raw_text = _decode_bytes(fetch_result.raw_bytes)
    if _looks_like_markdown(fetch_result):
        markdown = _normalize_markdown(raw_text)
        title = _first_markdown_heading(markdown) or _title_from_uri(fetch_result.original_uri)
        canonical_uri = fetch_result.original_uri
        authors: list[str] = []
        license_hint = None
    else:
        extracted = _extract_html_markdown(raw_text)
        markdown = _normalize_markdown(extracted["markdown"])
        title = extracted.get("title") or _first_markdown_heading(markdown) or _title_from_uri(fetch_result.original_uri)
        canonical_uri = extracted.get("canonical_uri") or fetch_result.original_uri
        authors = extracted.get("authors") or []
        license_hint = extracted.get("license_hint")
    return NormalizedSource(
        kind=kind,
        title=title,
        authors=authors,
        canonical_uri=canonical_uri,
        original_uri=fetch_result.original_uri,
        markdown=markdown,
        retrieved_at=fetch_result.retrieved_at,
        license_hint=license_hint,
    )


def _normalize_arxiv_html(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource:
    source = _normalize_website_like(fetch_result, kind)
    canonical_uri = fetch_result.fetch_uri or source.canonical_uri
    parsed = urllib.parse.urlparse(canonical_uri)
    labels: dict[str, Any] = {}
    if parsed.netloc.lower().endswith("arxiv.org"):
        match = re.search(r"/(?:abs|html)/([^/?#]+)", parsed.path)
        if match:
            arxiv_id = match.group(1)
            labels["arxiv_id"] = arxiv_id
            version = re.search(r"v(\d+)$", arxiv_id)
            if version:
                labels["version"] = int(version.group(1))
    native_overrides = _arxiv_native_locator_overrides(_decode_bytes(fetch_result.raw_bytes))
    if native_overrides:
        labels["native_locator_overrides"] = native_overrides
    return NormalizedSource(
        kind=kind,
        title=source.title,
        authors=source.authors,
        canonical_uri=canonical_uri,
        original_uri=source.original_uri,
        markdown=source.markdown,
        retrieved_at=source.retrieved_at,
        license_hint=source.license_hint,
        labels=labels,
    )


def _normalize_youtube(fetch_result: FetchResult, kind: SourceKind) -> NormalizedSource:
    payload = json.loads(fetch_result.raw_bytes.decode("utf-8"))
    video_id = payload["video_id"]
    cues = [
        CaptionCue(
            start=float(cue["start"]),
            end=float(cue["start"]) + float(cue.get("duration", 0.0)),
            text=_collapse_ws(str(cue.get("text", ""))),
        )
        for cue in payload.get("cues", [])
        if str(cue.get("text", "")).strip()
    ]
    title = f"YouTube video {video_id}"
    lines = [f"# {title}", ""]
    for cue in cues:
        lines.append(f"[t={cue.start:.1f}-{cue.end:.1f}] {cue.text}")
        lines.append("")
    markdown = _normalize_markdown("\n".join(lines))
    return NormalizedSource(
        kind=kind,
        title=title,
        authors=[],
        canonical_uri=f"https://www.youtube.com/watch?v={video_id}",
        original_uri=fetch_result.original_uri,
        markdown=markdown,
        retrieved_at=fetch_result.retrieved_at,
        captions=cues,
    )


def _extract_html_markdown(raw_html: str) -> dict[str, Any]:
    parser = _HTMLMarkdownParser()
    parser.feed(raw_html)
    markdown = parser.markdown()
    try:
        import trafilatura
    except ImportError:
        extracted = None
    else:
        extracted = trafilatura.extract(raw_html, output_format="markdown", include_tables=True, include_comments=False)
    if extracted and (_first_markdown_heading(extracted) or not _first_markdown_heading(markdown)):
        markdown = extracted
    return {
        "markdown": markdown,
        "title": parser.title,
        "canonical_uri": parser.canonical_uri,
        "authors": parser.authors,
        "license_hint": parser.license_hint,
    }


def _arxiv_native_locator_overrides(raw_html: str) -> list[dict[str, str]]:
    overrides: list[dict[str, str]] = []
    BeautifulSoup = None
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None
    if BeautifulSoup is not None:
        parsed = BeautifulSoup(raw_html, "lxml")
        for element in parsed.find_all(id=True):
            text = _collapse_ws(element.get_text(" ", strip=True))
            label = _native_arxiv_label(str(element.get("id") or ""), text)
            if label and text:
                overrides.append({"label": label, "text": text})
        return _dedupe_native_overrides(overrides)

    pattern = re.compile(
        r"<(?P<tag>div|p|section|article|span)\b(?P<attrs>[^>]*)\bid=[\"'](?P<id>[^\"']+)[\"'][^>]*>(?P<body>.*?)</(?P=tag)>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(raw_html):
        text = _collapse_ws(re.sub(r"<[^>]+>", " ", match.group("body")))
        label = _native_arxiv_label(match.group("id"), text)
        if label and text:
            overrides.append({"label": label, "text": text})
    return _dedupe_native_overrides(overrides)


def _native_arxiv_label(element_id: str, text: str) -> str | None:
    lowered = element_id.lower()
    explicit = re.search(r"\b((?:thm|theorem|eq|equation)[:.\-_]?\d+(?:\.\d+)*)\b", element_id, re.IGNORECASE)
    if explicit:
        raw = explicit.group(1).lower().replace("theorem", "thm").replace("equation", "eq")
        return raw.replace("_", ":").replace("-", ":").replace(".", ":", 1) if ":" not in raw else raw
    theorem = re.search(r"\btheorem\s+(\d+(?:\.\d+)*)", text, re.IGNORECASE)
    if theorem and ("theorem" in lowered or "thm" in lowered or "ltx_theorem" in lowered):
        return f"thm:{theorem.group(1)}"
    equation = re.search(r"\((\d+(?:\.\d+)*)\)", text)
    if equation and ("equation" in lowered or "eq" in lowered or "ltx_equation" in lowered):
        return f"eq:{equation.group(1)}"
    return None


def _dedupe_native_overrides(overrides: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for override in overrides:
        label = override["label"]
        if label in seen:
            continue
        seen.add(label)
        deduped.append(override)
    return deduped


def _apply_arxiv_native_locator_overrides(
    chunks: list[SourceChunk],
    labels: dict[str, Any],
) -> list[SourceChunk]:
    overrides = labels.get("native_locator_overrides")
    if not isinstance(overrides, list):
        return chunks
    updated: list[SourceChunk] = []
    used_labels: set[str] = set()
    for chunk in chunks:
        replacement = None
        for override in overrides:
            if not isinstance(override, dict):
                continue
            label = str(override.get("label") or "")
            text = str(override.get("text") or "")
            if not label or label in used_labels or not text:
                continue
            if text in _collapse_ws(chunk.text):
                replacement = SourceChunk(
                    locator=label,
                    text=chunk.text,
                    chunk_kind=chunk.chunk_kind,
                    heading_path=chunk.heading_path,
                    label=label,
                    ordinal=chunk.ordinal,
                )
                used_labels.add(label)
                break
        updated.append(replacement or chunk)
    return updated


class _HTMLMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.canonical_uri: str | None = None
        self.authors: list[str] = []
        self.license_hint: str | None = None
        self._blocks: list[str] = []
        self._current: list[str] = []
        self._heading_level: int | None = None
        self._in_title = False
        self._title_parts: list[str] = []
        self._skip_depth = 0
        self._pre_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag in {"script", "style", "nav", "footer", "noscript"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "link" and attrs_dict.get("rel") == "canonical" and attrs_dict.get("href"):
            self.canonical_uri = attrs_dict["href"]
        if tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            content = attrs_dict.get("content", "")
            if name in {"author", "citation_author"} and content:
                self.authors.append(content)
            if name in {"license", "dc.rights"} and content:
                self.license_hint = content
        if self._skip_depth:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self._heading_level = int(tag[1])
        elif tag in {"p", "div", "section", "article", "li"}:
            self._flush()
            if tag == "li":
                self._current.append("- ")
        elif tag in {"br"}:
            self._current.append("\n")
        elif tag in {"pre", "code"}:
            if tag == "pre":
                self._flush()
                self._pre_depth += 1
                self._current.append("```")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
            title = _collapse_ws(" ".join(self._title_parts))
            if title:
                self.title = title
        if self._skip_depth:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self._heading_level = None
        elif tag in {"p", "div", "section", "article", "li"}:
            self._flush()
        elif tag == "pre" and self._pre_depth:
            self._current.append("```")
            self._pre_depth -= 1
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
            return
        if self._skip_depth:
            return
        if not data.strip():
            return
        if self._heading_level is not None and not self._current:
            self._current.append("#" * self._heading_level + " ")
        self._current.append(data if self._pre_depth else _collapse_ws(data))

    def markdown(self) -> str:
        self._flush()
        return "\n\n".join(block for block in self._blocks if block.strip())

    def _flush(self) -> None:
        text = _collapse_block("".join(self._current))
        if text:
            self._blocks.append(text)
        self._current = []


def _canonical_context(
    vault,
    registered: RegisteredSource,
    source: NormalizedSource,
    window: IngestWindow,
    *,
    target_learning_object_ids: list[str],
    instructions: str | None,
) -> CanonicalIngestContext:
    learning_objects = [
        {
            "id": lo.id,
            "title": lo.title,
            "concept": lo.concept,
            "subjects": lo.subjects,
        }
        for lo in sorted(vault.learning_objects.values(), key=lambda item: item.id)
        if not target_learning_object_ids or lo.id in target_learning_object_ids or registered.subject_id in lo.subjects
    ]
    concepts = [
        {"id": concept_id, "title": concept.title}
        for concept_id, concept in sorted(vault.concepts.items())
    ]
    plan = ExtractionPlan(learning_object_required=source.kind != "textbook_chapter")
    return CanonicalIngestContext(
        vault_root=str(vault.root),
        source_kind=source.kind,
        canonical_source={
            "id": registered.note_id,
            "path": registered.path,
            **registered.canonical_source,
        },
        chunks=window.chunks,
        target_subject=registered.subject_id,
        target_learning_object_ids=target_learning_object_ids,
        concepts=concepts,
        learning_objects=learning_objects,
        extraction_plan=plan,
        instructions=instructions,
    )


def _proposal_with_locator_validation(
    proposal: AuthoringProposal,
    registered: RegisteredSource,
    window: IngestWindow,
) -> AuthoringProposal:
    known_ref_ids = {ref.ref_id for ref in proposal.source_refs}
    rewritten_refs: list[dict[str, Any]] = []
    for ref in proposal.source_refs:
        if ref.ref_type != "canonical_source":
            rewritten_refs.append(ref.model_dump(mode="json", exclude_none=True))
            continue
        path = ref.path or registered.path
        locator = ref.locator or _time_locator_from_ref_id(ref.ref_id)
        if locator is not None and not _locator_resolves(window.chunks, locator):
            path = f"{registered.path}#unresolved-locator:{locator}"
        rewritten_refs.append(
            ref.model_copy(update={"path": path, "locator": locator}).model_dump(mode="json", exclude_none=True)
        )
    for ref_id in _missing_source_ref_ids(proposal, known_ref_ids):
        ref = _canonical_source_ref_from_id(ref_id, registered, window)
        rewritten_refs.append(ref)
    return AuthoringProposal.model_validate(
        {
            "summary": proposal.summary,
            "source_refs": rewritten_refs,
            "items": [item.model_dump(mode="json", exclude_none=True) for item in proposal.items],
        }
    )


def _missing_source_ref_ids(proposal: AuthoringProposal, known_ref_ids: set[str]) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for item in proposal.items:
        for ref_id in item.source_ref_ids:
            if ref_id in known_ref_ids or ref_id in seen:
                continue
            seen.add(ref_id)
            missing.append(ref_id)
    return missing


def _canonical_source_ref_from_id(
    ref_id: str,
    registered: RegisteredSource,
    window: IngestWindow,
) -> dict[str, Any]:
    locator = _time_locator_from_ref_id(ref_id) or _chunk_locator_from_ref_id(ref_id, registered, window)
    path = registered.path
    if locator is None:
        path = f"{registered.path}#unresolved-source-ref:{ref_id}"
    elif not _locator_resolves(window.chunks, locator):
        path = f"{registered.path}#unresolved-locator:{locator}"
    return {
        "ref_type": "canonical_source",
        "ref_id": ref_id,
        "path": path,
        "locator": locator,
    }


def _chunk_locator_from_ref_id(
    ref_id: str,
    registered: RegisteredSource,
    window: IngestWindow,
) -> str | None:
    """Recover a chunk locator from a source-ref id that embeds one.

    Ingestor models frequently key every ``source_ref`` for one source by the note
    id alone (so the ids are not unique) and then reference a specific span from an
    item as ``<note_id>:<locator>`` (or reference the bare chunk locator directly).
    Recover the locator - stripping the note-id prefix when present - and keep it
    only when it resolves to a real chunk, so those items stay grounded instead of
    being marked ``unresolved_source_ref``.
    """

    if _locator_resolves(window.chunks, ref_id):
        return ref_id
    for separator in (":", "#"):
        prefix = f"{registered.note_id}{separator}"
        if ref_id.startswith(prefix):
            candidate = ref_id[len(prefix):].strip()
            if candidate and _locator_resolves(window.chunks, candidate):
                return candidate
    return None


def _time_locator_from_ref_id(ref_id: str) -> str | None:
    match = re.search(r"(?:^|[:#?&])t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$", ref_id)
    if match:
        start = float(match.group(1))
        end = float(match.group(2))
        if end <= start:
            return None
        return f"t={start:.1f}-{end:.1f}"
    match = re.search(r"_(\d+(?:p\d+)?)_(\d+(?:p\d+)?)$", ref_id)
    if not match:
        return None
    start = float(match.group(1).replace("p", "."))
    end = float(match.group(2).replace("p", "."))
    if end <= start:
        return None
    return f"t={start:.1f}-{end:.1f}"


def _existing_registered_source(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> RegisteredSource | None:
    for note in vault.notes.values():
        if note.source_type != "canonical_source":
            continue
        metadata = getattr(note, "model_extra", {}) or {}
        canonical_source = metadata.get("canonical_source")
        if not isinstance(canonical_source, dict):
            continue
        if (
            canonical_source.get("kind") == kind
            and canonical_source.get("canonical_uri") == canonical_uri
            and canonical_source.get("content_hash") == content_hash
        ):
            subject_id = note.subjects[0] if note.subjects else ""
            return RegisteredSource(
                note_id=note.id,
                path=note.path or "",
                subject_id=subject_id,
                canonical_source=dict(canonical_source),
            )
    return None


def _previous_registered_sources(vault, kind: SourceKind, canonical_uri: str, content_hash: str) -> list[Any]:
    previous: list[Any] = []
    for note in vault.notes.values():
        if note.source_type != "canonical_source":
            continue
        metadata = getattr(note, "model_extra", {}) or {}
        canonical_source = metadata.get("canonical_source")
        if not isinstance(canonical_source, dict):
            continue
        if (
            canonical_source.get("kind") == kind
            and canonical_source.get("canonical_uri") == canonical_uri
            and canonical_source.get("content_hash") != content_hash
        ):
            previous.append(note)
    return previous


def _chunks_for_note_body(kind: SourceKind, body: str) -> list[SourceChunk]:
    if kind == "youtube_video":
        chunks: list[SourceChunk] = []
        for ordinal, line in enumerate(body.splitlines(), start=1):
            match = re.match(r"^\[t=([0-9.]+)-([0-9.]+)\]\s+(.+)$", line.strip())
            if not match:
                continue
            locator = f"t={float(match.group(1)):.1f}-{float(match.group(2)):.1f}"
            chunks.append(
                SourceChunk(
                    locator=locator,
                    text=match.group(3).strip(),
                    chunk_kind="caption",
                    heading_path=["transcript"],
                    ordinal=ordinal,
                )
            )
        return chunks
    return chunk_markdown(body)


def _locator_hashes(chunks: list[SourceChunk]) -> dict[str, str]:
    return {
        chunk.locator: hashlib.sha256(chunk.text.strip().encode("utf-8")).hexdigest()
        for chunk in chunks
    }


def _locator_resolves(chunks: list[SourceChunk], locator: str) -> bool:
    if locator in {chunk.locator for chunk in chunks}:
        return True
    if _child_chunks_for_locator(chunks, locator):
        return True
    return bool(_caption_chunks_for_time_range(chunks, locator))


def _locator_hash_for_ref(chunks: list[SourceChunk], locator: str | None) -> str | None:
    if locator is None:
        return None
    for chunk in chunks:
        if chunk.locator == locator:
            return hashlib.sha256(chunk.text.strip().encode("utf-8")).hexdigest()
    child_chunks = _child_chunks_for_locator(chunks, locator)
    if child_chunks:
        text = "\n".join(chunk.text.strip() for chunk in child_chunks)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    caption_chunks = _caption_chunks_for_time_range(chunks, locator)
    if not caption_chunks:
        return None
    text = "\n".join(chunk.text.strip() for chunk in caption_chunks)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _child_chunks_for_locator(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]:
    prefix = locator.strip().rstrip("/")
    if not prefix:
        return []
    child_prefix = f"{prefix}/"
    return [chunk for chunk in chunks if chunk.locator.startswith(child_prefix)]


def _caption_chunks_for_time_range(chunks: list[SourceChunk], locator: str) -> list[SourceChunk]:
    target = _parse_time_locator(locator)
    if target is None:
        return []
    start, end = target
    timed_chunks: list[tuple[float, float, SourceChunk]] = []
    for chunk in chunks:
        if chunk.chunk_kind != "caption":
            continue
        chunk_range = _parse_time_locator(chunk.locator)
        if chunk_range is None:
            continue
        timed_chunks.append((chunk_range[0], chunk_range[1], chunk))
    if not timed_chunks:
        return []

    epsilon = 0.05
    min_start = min(item[0] for item in timed_chunks)
    max_end = max(item[1] for item in timed_chunks)
    if start < min_start - epsilon or end > max_end + epsilon:
        return []
    selected = [
        chunk
        for chunk_start, chunk_end, chunk in timed_chunks
        if chunk_end > start + epsilon and chunk_start < end - epsilon
    ]
    selected.sort(key=lambda chunk: chunk.ordinal)
    return selected


def _parse_time_locator(locator: str) -> tuple[float, float] | None:
    match = re.match(r"^t=([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)$", locator.strip())
    if not match:
        return None
    start = float(match.group(1))
    end = float(match.group(2))
    if end <= start:
        return None
    return start, end


def _grounded_entity_refs(vault) -> list[tuple[str, str, str | None, list[Any]]]:
    rows: list[tuple[str, str, str | None, list[Any]]] = []
    for learning_object in vault.learning_objects.values():
        rows.append(
            (
                "learning_object",
                learning_object.id,
                learning_object.subjects[0] if learning_object.subjects else None,
                learning_object.provenance.source_refs,
            )
        )
    for practice_item in vault.practice_items.values():
        subjects = vault.subjects_for_item(practice_item)
        rows.append(
            (
                "practice_item",
                practice_item.id,
                subjects[0] if subjects else None,
                practice_item.provenance.source_refs,
            )
        )
    return rows


def _resolve_subject(
    root: Path,
    source: NormalizedSource,
    subject_id: str | None,
    kind: SourceKind,
    learning_object_ids: list[str],
    content_hash: str,
    *,
    clock: Clock | None,
) -> str:
    vault = load_vault(root)
    if kind == "textbook_chapter":
        if subject_id is None:
            raise SourceIngestionError("textbook_chapter ingestion requires --subject")
        return subject_id
    if subject_id is not None:
        normalized_subject = kebab_case(subject_id)
        if normalized_subject not in vault.subjects:
            add_subject(root, normalized_subject, _title_from_slug(normalized_subject), clock=clock)
        return normalized_subject
    derived = kebab_case(source.title) or "source"
    if derived in vault.subjects:
        existing = _existing_registered_source(vault, source.kind, source.canonical_uri, content_hash)
        if existing is not None:
            return existing.subject_id
        raise SourceIngestionError(f"subject '{derived}' already exists; pass --subject to target it explicitly")
    add_subject(root, derived, source.title, clock=clock)
    return derived


def _establish_goal_linkage(
    root: Path,
    subject_id: str,
    title: str,
    proposal: AuthoringProposal,
    *,
    goal_id: str | None,
    default_priority: float,
    clock: Clock | None,
) -> dict[str, Any]:
    vault = load_vault(root)
    concepts = _proposal_learning_object_concepts(proposal) & set(vault.concepts)
    if not concepts:
        return {"goal_id": goal_id, "created": False, "updated": False}
    paths = VaultPaths(vault.root, vault.config)
    goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals = goals_data.setdefault("goals", [])
    now = utc_now_iso(clock)
    created = False
    updated = False

    target: dict[str, Any] | None = None
    if goal_id is not None:
        for goal in goals:
            if isinstance(goal, dict) and goal.get("id") == goal_id:
                target = goal
                break
        if target is None or target.get("status") != "active":
            raise SourceIngestionError(f"goal '{goal_id}' is not active")
    else:
        for goal in goals:
            if not isinstance(goal, dict) or goal.get("status") != "active":
                continue
            if concepts <= _goal_scope_concepts(goal):
                target = goal
                break
        if target is None:
            target = {
                "id": _unique_goal_id(goals, subject_id),
                "title": title,
                "status": "active",
                "priority": default_priority,
                "target_recall": 0.8,
                "facet_scope": {"concepts": [], "facets": []},
                "due_at": None,
                "created_at": now,
                "updated_at": now,
            }
            goals.append(target)
            created = True

    # Normalize legacy v1 goals (concept_anchors) to v2 facet_scope on write.
    scope = target.get("facet_scope")
    if not isinstance(scope, dict):
        scope = {"concepts": list(target.pop("concept_anchors", None) or []), "facets": []}
        target["facet_scope"] = scope
        updated = True
    scope_concepts = list(scope.get("concepts") or [])
    for concept_id in sorted(concepts):
        if concept_id not in scope_concepts:
            scope_concepts.append(concept_id)
            updated = True
    scope["concepts"] = scope_concepts
    if created or updated:
        target["updated_at"] = now
        write_yaml(paths.goals_path, goals_data)
    return {"goal_id": target.get("id"), "created": created, "updated": updated}


def _proposal_learning_object_concepts(proposal: AuthoringProposal) -> set[str]:
    concepts: set[str] = set()
    for item in proposal.items:
        if item.item_type != "learning_object":
            continue
        payload = item.payload.model_dump(mode="json", exclude_none=True)
        concept = payload.get("concept_id") or payload.get("concept")
        if concept:
            concepts.add(str(concept))
    return concepts


def _goal_scope_concepts(goal: dict[str, Any]) -> set[str]:
    """Concept scope of a raw goals.yaml entry, tolerating legacy v1 form."""

    scope = goal.get("facet_scope")
    if isinstance(scope, dict):
        return set(scope.get("concepts") or [])
    return set(goal.get("concept_anchors") or [])


def _result_from_existing_batch(
    agent_run: dict[str, Any],
    batch: dict[str, Any] | None,
    registered: RegisteredSource,
    source_kind: SourceKind,
    content_hash: str,
) -> IngestResult:
    return IngestResult(
        patch_id=batch["id"] if batch else None,
        agent_run_id=agent_run["id"],
        source_note_id=registered.note_id,
        source_kind=source_kind,
        subject_id=registered.subject_id,
        content_hash=content_hash,
        reused_existing=True,
        codex_calls=0,
        auto_applied_count=0,
        review_required_count=0,
        invalid_count=0,
    )


def _retain_raw_bytes(root: Path, note_id: str, content_hash: str, raw_bytes: bytes) -> Path:
    raw_dir = root / "canonical-sources" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    digest = content_hash.split(":", 1)[-1]
    path = raw_dir / f"{note_id}-{digest[:16]}.bin"
    if not path.exists():
        path.write_bytes(raw_bytes)
    return path


def _unique_note_id(vault, title: str, content_hash: str) -> str:
    base = "note_source_" + snake_case(title)[:48].strip("_")
    if base == "note_source_":
        base = "note_source"
    candidate = f"{base}_{content_hash.split(':', 1)[-1][:8]}"
    if candidate not in vault.notes:
        return candidate
    suffix = 2
    while f"{candidate}_{suffix}" in vault.notes:
        suffix += 1
    return f"{candidate}_{suffix}"


def _unique_goal_id(goals: list[Any], subject_id: str) -> str:
    existing = {str(goal.get("id")) for goal in goals if isinstance(goal, dict)}
    base = "goal_" + snake_case(subject_id)
    if base not in existing:
        return base
    suffix = 2
    while f"{base}_{suffix}" in existing:
        suffix += 1
    return f"{base}_{suffix}"


def _youtube_video_id(source: str) -> str | None:
    parsed = urllib.parse.urlparse(source)
    if parsed.netloc.lower() == "youtu.be":
        return parsed.path.strip("/") or None
    query = urllib.parse.parse_qs(parsed.query)
    if "v" in query and query["v"]:
        return query["v"][0]
    match = re.search(r"/(?:embed|shorts)/([^/?#]+)", parsed.path)
    return match.group(1) if match else None


def _is_pdf_fetch(fetched: FetchResult) -> bool:
    if (fetched.content_type or "").lower() == "application/pdf":
        return True
    parsed = urllib.parse.urlparse(fetched.fetch_uri or fetched.original_uri)
    if Path(parsed.path).suffix.lower() == ".pdf":
        return True
    return fetched.raw_bytes[:5] == b"%PDF-"


def _pdf_fetch_result(
    root: Path,
    pdf_bytes: bytes,
    fetched: FetchResult,
    pdf_config: PdfIngestConfig | None,
) -> FetchResult:
    markdown = _pdf_markdown(root, pdf_bytes, pdf_config)
    return FetchResult(
        raw_bytes=markdown.encode("utf-8"),
        content_type="text/markdown",
        original_uri=fetched.original_uri,
        fetch_uri=fetched.fetch_uri,
        retrieved_at=fetched.retrieved_at,
        source_bytes=pdf_bytes,
    )


def _pdf_markdown(root: Path, pdf_bytes: bytes, pdf_config: PdfIngestConfig | None) -> str:
    cache_dir = root / ".learnloop" / "source-cache" / "pdf"
    try:
        extraction = extract_pdf_markdown(pdf_bytes, config=pdf_config, cache_dir=cache_dir)
    except PdfExtractionError as exc:
        raise SourceIngestionError(str(exc)) from exc
    return _normalize_markdown(extraction.markdown)


def _content_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "text/html"
    if suffix == ".md":
        return "text/markdown"
    return "text/plain"


def _looks_like_markdown(fetch_result: FetchResult) -> bool:
    parsed = urllib.parse.urlparse(fetch_result.original_uri)
    suffix = Path(parsed.path).suffix.lower()
    return suffix in {".md", ".txt"} or (fetch_result.content_type or "").startswith(("text/plain", "text/markdown"))


def _decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _normalize_markdown(markdown: str) -> str:
    lines = [line.rstrip() for line in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    collapsed: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                collapsed.append("")
            blank = True
            continue
        collapsed.append(line)
        blank = False
    text = "\n".join(collapsed).strip()
    return text + "\n"


def _first_markdown_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+)$", line)
        if match:
            return _strip_markdown(match.group(1)).strip()
    return None


def _strip_markdown(text: str) -> str:
    return re.sub(r"[*_`#\[\]()>]", "", text).strip()


def _title_from_uri(uri: str) -> str:
    parsed = urllib.parse.urlparse(uri)
    name = Path(parsed.path).stem or parsed.netloc or "Source"
    return _title_from_slug(kebab_case(name) or "Source")


def _title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-") if part) or "Source"


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _collapse_block(text: str) -> str:
    lines = [_collapse_ws(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
