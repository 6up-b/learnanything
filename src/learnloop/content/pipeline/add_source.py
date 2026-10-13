"""One Add for any source (UX Phase 1, docs/specs/ux_learnloop_v1.md §6).

A learner drops a book, paper, web page or video in and is reading it at once.
Everything else happens in the durable queue, without a question on the way:

1. **Add** (:func:`add_source`). A local file is registered and its original
   stored synchronously, so the Reader can show the original PDF before any text
   is extracted. A link is fetched by the queue. One ``add_source`` batch holds
   the import and an :data:`AUTO_STUDY_MAP_JOB` that depends on it.
2. **Plan the first build** (:func:`run_auto_study_map`, the job handler). Once
   the text is ready: file the book under an automatic subject (Q7), pick the
   chapter the learner starts in plus the next one (reading order, Q6; a small
   source is built whole), check that an AI can write questions and that the
   learner said OK to it once (Q4), and pause only when the estimate is unusual
   (Q5). Then queue the ordinary inventory -> synthesis build, applied when every
   gate passes (Q3, kill switch ``[ingest] auto_apply_passing_builds``).
3. **Keep one chapter ahead** (:func:`advance_reading_build`), called when the
   Reader marks a section reached: the chapter being read and the next one.
4. **Say it in one line** (:func:`source_status_line`): the book card's only
   status line, in the learner's words (§6.3, §6.7, glossary §9).
5. **Undo** (:func:`undo_source_questions`): revert the book's applied maps.

The job ledger is the record: every planning decision is an ``auto_study_map``
job whose result says what happened (``building``, ``waiting``, ``paused``,
``skipped``), so the status line, the progressive build and undo all derive
from durable rows. No migration: job types are open strings.

Kill switch ``[ingest] auto_build``: off, Add only makes the source readable.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import kebab_case
from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.resolution import resolve_source

AUTO_STUDY_MAP_JOB = "auto_study_map"
ADD_SOURCE_WORKFLOW = "add_source"
AUTO_BUILD_WORKFLOW = "auto_study_map"
# Add's import drains ahead of question builds (Quick add's priority is 100):
# the learner is waiting to read.
ADD_SOURCE_PRIORITY = 110
BUILD_PRIORITY = 100

UNSUPPORTED_MESSAGE = (
    "LearnLoop can't open this yet — it reads PDFs, web pages, arXiv, YouTube, Markdown, text and subtitles."
)
MISSING_FILE_MESSAGE = "LearnLoop couldn't find that file. It may have moved."
EXISTING_MESSAGE = "Already in your library — opened where you left off."
DATA_FLOW = "passages_and_answers"
# A first build accumulates tiny units (page-per-unit extractions) up to this
# much text, so it is never one page; never past the scope cap.
FLOOR_TOKENS = 4000

_KIND_NOUN = {
    "pdf": "book",
    "arxiv": "paper",
    "web": "article",
    "youtube": "video",
    "audio": "recording",
    "textfile": "book",
}
_ROLE_BY_CATEGORY = {
    "pdf": "primary_textbook",
    "youtube": "lecture",
    "arxiv": "paper",
    "web": "reference",
    "textfile": "reference",
}
_FRONT_MATTER = re.compile(
    r"^\s*(?:(?:table of )?contents|preface|foreword|acknowledge?ments?|copyright|dedication|"
    r"about the authors?|index|bibliography|references|title page|half[- ]title|"
    r"list of (?:figures|tables|symbols)|notation|front matter|cover)\s*$",
    re.IGNORECASE,
)
_CHAPTER_NUMBER = re.compile(r"^\s*(?:chapter|ch\.?|part|lecture|unit)?\s*(\d+)\b", re.IGNORECASE)
_JUNK_PDF_TITLES = re.compile(r"^(?:untitled|microsoft word|document\d*|\s*)$|\.(?:docx?|tex|dvi|pdf)$", re.IGNORECASE)
_CONSENT_LABEL = {"codex": "ChatGPT", "chatgpt": "ChatGPT", "openrouter": "OpenRouter"}


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AddSourceOptions:
    """Add → More options (spec §8.2). Every field defaults to "no decision"."""

    page_selection: tuple[int, ...] | None = None
    problem_set: bool = False
    keep_local: bool = False
    text_recognition: bool = False


def kind_noun(category: str | None) -> str:
    return _KIND_NOUN.get(category or "", "book")


def add_source(vault, ingest_jobs, source: str, options: AddSourceOptions | None = None, *,
               clock: Clock | None = None) -> dict[str, Any]:
    """Add one source and return the item the Library and Reader open.

    ``status`` is ``added`` (a local file, registered now, its original
    stored), ``queued`` (a link the queue fetches first), ``existing`` (already
    in the library: nothing is duplicated) or ``unsupported`` (one plain
    line). Never raises for a bad input: an Add of many files reports each."""

    options = options or AddSourceOptions()
    raw = (source or "").strip()
    item: dict[str, Any] = {
        "source": raw,
        # The library's own spelling of the source (its card's canonical_uri),
        # so the shell can open a fetched link once it is ready.
        "canonical": None,
        "kind": None,
        "kind_noun": None,
        "status": "unsupported",
        "source_id": None,
        "revision_id": None,
        "title": raw,
        "batch_id": None,
        "preparing": False,
        "message": UNSUPPORTED_MESSAGE,
    }
    try:
        resolved = resolve_source(raw)
    except UnsupportedSourceError:
        return item
    repo = ingest_jobs.repository
    category = resolved.category
    item.update(canonical=resolved.source, kind=category, kind_noun=kind_noun(category), message=None)

    artifact = repo.source_artifact_by_uri(category, resolved.source)
    if artifact is not None and _has_text_or_add_in_flight(repo, artifact["id"]):
        revision_id = artifact.get("current_revision_id")
        item.update(
            status="existing",
            source_id=artifact["id"],
            revision_id=revision_id,
            title=_display_title(artifact, repo.get_source_revision(revision_id) if revision_id else None),
            preparing=_completed_extraction(repo, artifact["id"]) is None,
            message=EXISTING_MESSAGE,
        )
        return item

    local = _local_file(resolved.source)
    source_id = revision_id = None
    if local is not None:
        from learnloop.content.sources.source_library import register_source_revision

        raw_bytes = local.read_bytes()
        title = local_display_title(local, raw_bytes, category)
        registered = register_source_revision(
            repo,
            acquisition_kind=category,
            canonical_uri=resolved.source,
            raw_bytes=raw_bytes,
            original_uri=local.resolve().as_uri(),
            retrieved_at=utc_now_iso(clock),
            display_title=title,
            reader_enabled=False if options.problem_set else None,
            vault_root=vault.root,
            clock=clock,
        )
        source_id, revision_id = registered.source_id, registered.revision_id
        item.update(status="added", source_id=source_id, revision_id=revision_id, title=title, preparing=True)
    elif category in {"pdf", "textfile", "audio"} and not resolved.source.lower().startswith(("http://", "https://")):
        item.update(status="unsupported", message=MISSING_FILE_MESSAGE)
        return item
    else:
        item.update(status="queued", preparing=True)

    item["batch_id"] = ingest_jobs.enqueue_add_source(resolved.source, source_id=source_id, options=options)
    return item


def _local_file(source: str) -> Path | None:
    if source.lower().startswith(("http://", "https://")):
        return None
    path = Path(source).expanduser()
    return path if path.is_file() else None


def local_display_title(path: Path, raw_bytes: bytes, category: str | None) -> str:
    """A readable title for a local file: the PDF's own title when it has a
    real one, else the file name in words (never a ``file://`` URI)."""

    if category == "pdf":
        try:
            from pypdf import PdfReader

            metadata = PdfReader(io.BytesIO(raw_bytes)).metadata
            title = str((metadata.title if metadata else None) or "").strip()
        except Exception:  # noqa: BLE001 - a damaged PDF still gets a title
            title = ""
        if title and len(title) >= 3 and not _JUNK_PDF_TITLES.search(title):
            return title
    return title_from_file_name(path.name)


def title_from_file_name(name: str) -> str:
    stem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", name)
    words = re.sub(r"[_\-.]+", " ", stem).split()
    if not words:
        return name
    if all(word == word.lower() for word in words):
        return " ".join(word.capitalize() for word in words)
    return " ".join(words)


def _display_title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str:
    title = artifact.get("display_title")
    if isinstance(title, str) and title.strip():
        return title
    uri = str((revision or {}).get("original_uri") or artifact.get("canonical_uri") or artifact.get("id") or "")
    if uri.startswith("file://") or (uri and not uri.startswith(("http://", "https://"))):
        return title_from_file_name(Path(uri.removeprefix("file://")).name) or uri
    return uri


def learner_title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str:
    """The card and Reader title: display title, else a file name in words."""

    return _display_title(artifact, revision)


def _completed_extraction(repo, source_id: str) -> tuple[str, str] | None:
    from learnloop.content.pipeline.quick_add import _resolve_extraction

    return _resolve_extraction(repo, source_id)


def _has_text_or_add_in_flight(repo, source_id: str) -> bool:
    if _completed_extraction(repo, source_id) is not None:
        return True
    return any(
        job["status"] in {"queued", "running", "waiting_for_input"}
        for job in _jobs_for_source(repo.ingest_jobs_by_types(("import",), limit=500), source_id)
    )


# ---------------------------------------------------------------------------
# Chapters and reading order (Q6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Chapter:
    """A top-level unit of the outline with every unit nested under it."""

    unit_id: str
    label: str
    unit_ids: tuple[str, ...]
    tokens: int
    front_matter: bool = False


def outline_chapters(outline) -> list[Chapter]:
    units = list(outline.units)
    known = {unit.unit_id for unit in units}
    children: dict[str, list[Any]] = {}
    tops: list[Any] = []
    for unit in units:
        parent = unit.parent_unit_id
        if parent and parent in known:
            children.setdefault(parent, []).append(unit)
        else:
            tops.append(unit)

    def collect(unit) -> list[Any]:
        out = [unit]
        for child in children.get(unit.unit_id, []):
            out.extend(collect(child))
        return out

    chapters: list[Chapter] = []
    for top in tops:
        members = collect(top)
        chapters.append(
            Chapter(
                unit_id=top.unit_id,
                label=readable_label(str(top.label or top.unit_id)),
                unit_ids=tuple(member.unit_id for member in members),
                tokens=sum(int(member.approx_tokens or 0) for member in members),
                front_matter=bool(_FRONT_MATTER.match(str(top.label or ""))),
            )
        )
    return chapters


def readable_label(label: str) -> str:
    """A heading slug (``1-probability-and-counting``, how the Markdown
    extractor keys sections) back into words; real titles pass unchanged."""

    if " " in label or "-" not in label or label != label.lower():
        return label
    words = [word for word in label.split("-") if word]
    for index, word in enumerate(words):
        if word[:1].isalpha():
            words[index] = word.capitalize()
            break
    return " ".join(words)


def _is_front_matter(chapter: Chapter) -> bool:
    return chapter.front_matter or bool(_FRONT_MATTER.match(chapter.label))


def reading_order_scope(
    chapters: Sequence[Chapter],
    *,
    built: Iterable[str] = (),
    start_unit_id: str | None = None,
    cap_tokens: int,
    floor_tokens: int = FLOOR_TOKENS,
    ahead: int = 1,
) -> list[Chapter]:
    """The first build: the chapter the learner starts in, plus ``ahead`` more.

    Front matter is skipped. Tiny chapters (one page per unit) keep
    accumulating until ``floor_tokens``. Never more than ``cap_tokens``, except
    that the first chapter is always built, alone if it is over the cap."""

    built_ids = set(built)
    index = 0
    if start_unit_id is not None:
        index = next(
            (i for i, chapter in enumerate(chapters) if start_unit_id in chapter.unit_ids), 0
        )
    candidates = [
        chapter for chapter in chapters[index:]
        if not _is_front_matter(chapter) and chapter.unit_id not in built_ids
    ]
    picked: list[Chapter] = []
    tokens = 0
    for chapter in candidates:
        if picked and tokens + chapter.tokens > cap_tokens:
            break
        picked.append(chapter)
        tokens += chapter.tokens
        if len(picked) >= 1 + ahead and tokens >= floor_tokens:
            break
    return picked


def chapters_to_keep_ahead(chapters: Sequence[Chapter], section_unit_id: str, built: Iterable[str]) -> list[Chapter]:
    """While reading: the chapter holding ``section_unit_id`` and the next one,
    minus what is already built (or nothing, outside every chapter)."""

    built_ids = set(built)
    index = next((i for i, chapter in enumerate(chapters) if section_unit_id in chapter.unit_ids), None)
    if index is None:
        return []
    wanted = [chapter for chapter in chapters[index:index + 2] if not _is_front_matter(chapter)]
    return [chapter for chapter in wanted if chapter.unit_id not in built_ids]


def chapter_phrase(labels: Sequence[str], *, whole: bool = False, noun: str = "book") -> str:
    """``Ch. 1–2``, ``Ch. 3``, ``this article`` or a short chapter title."""

    if whole or not labels:
        return f"this {noun}"
    numbers: list[int] = []
    for label in labels:
        match = _CHAPTER_NUMBER.match(label)
        if match is None:
            numbers = []
            break
        numbers.append(int(match.group(1)))
    if numbers:
        if len(numbers) == 1:
            return f"Ch. {numbers[0]}"
        if numbers == list(range(numbers[0], numbers[0] + len(numbers))):
            return f"Ch. {numbers[0]}–{numbers[-1]}"
        return "Ch. " + ", ".join(str(number) for number in numbers)
    if len(labels) == 1:
        label = labels[0].strip()
        return label if len(label) <= 40 else label[:39].rstrip() + "…"
    return f"{len(labels)} chapters"


# ---------------------------------------------------------------------------
# Who writes the questions, the learner's OK, and money (Q4, Q5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthoringRoute:
    provider: str
    ready: bool
    message: str | None = None
    subscription: bool = True
    consent_key: str = "codex"


def consent_key(config, provider_name: str) -> str:
    """The consent identity for a provider: one OK covers its whole family."""

    from learnloop.config import CODEX_PROVIDER_NAMES

    profile = config.ai.providers.get(provider_name)
    provider_type = str(getattr(profile, "type", "") or "")
    if provider_name in CODEX_PROVIDER_NAMES or provider_type in {"codex_sdk", "http", "http_adapter"}:
        return "codex"
    if provider_type == "chatgpt_plan":
        return "chatgpt"
    if provider_type == "openrouter" or provider_name.startswith("openrouter"):
        return "openrouter"
    return provider_name


def consent_label(key: str) -> str:
    return _CONSENT_LABEL.get(key, key)


def what_leaves(label: str) -> str:
    return (
        f"LearnLoop sends passages of the books you add, and your answers, to {label} "
        "to write questions and give feedback."
    )


def authoring_route_for(vault_root: Path, config) -> AuthoringRoute:
    """The route that would write questions for a build, and whether it is
    ready, the way the build resolves it (routed provider, else the fallback)."""

    from learnloop.ai.routing import provider_for_task, runtime_for_provider
    from learnloop.ai.spend import is_subscription_transport

    name = provider_for_task(config, "canonical_ingest").provider_name
    report = runtime_for_provider(vault_root, config, name, task="canonical_ingest")
    chosen, ready, message = name, report.ready, report.message
    fallback = (config.ai.fallback_provider or "").strip()
    if not ready and fallback and fallback != name:
        backup = runtime_for_provider(vault_root, config, fallback, task="canonical_ingest")
        if backup.ready:
            chosen, ready, message = fallback, True, None
    profile = config.ai.providers.get(chosen)
    return AuthoringRoute(
        provider=chosen,
        ready=ready,
        message=None if ready else message,
        subscription=is_subscription_transport(profile=profile),
        consent_key=consent_key(config, chosen),
    )


def default_authoring_route(ctx) -> AuthoringRoute:
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    return authoring_route_for(vault.root, vault.config)


def estimate_usd(config, provider_name: str, totals: Mapping[str, Any]) -> float:
    pause = config.ingest.cost_pause
    tokens = int(totals.get("input_tokens") or 0) + int(totals.get("max_output_tokens") or 0)
    price = float(pause.prices.get(provider_name, pause.default_price_per_million_tokens))
    return tokens * price / 1_000_000


def cost_pause_reason(config, usd: float, spent_today_usd: float) -> str | None:
    """``over_threshold`` / ``daily_cap`` when a build should ask first (Q5)."""

    pause = config.ingest.cost_pause
    if usd <= 0:
        return None
    if usd > pause.threshold_usd:
        return "over_threshold"
    if pause.daily_cap_usd is not None:
        remaining = max(float(pause.daily_cap_usd) - spent_today_usd, 0.0)
        if usd > remaining * pause.daily_cap_fraction:
            return "daily_cap"
    return None


def spent_today_usd(repo, now: datetime) -> float:
    """What automatic builds started today were estimated to cost."""

    day = now.date().isoformat()
    total = 0.0
    for job in repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,), limit=500):
        result = job.get("result") or {}
        if result.get("outcome") == "building" and str(job.get("finished_at") or "")[:10] == day:
            total += float(result.get("estimate_usd") or 0.0)
    return total


# ---------------------------------------------------------------------------
# Automatic subjects (Q7)
# ---------------------------------------------------------------------------


def subject_title_from(title: str) -> str:
    """A subject name from a book title: drop the author part, editions and
    subtitles, keep at most eight words."""

    name = re.split(r"\s+[—–]\s+|\s+-\s+|:\s+", title or "", maxsplit=1)[0]
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    name = re.sub(r"\b\d+(?:st|nd|rd|th)\s+edition\b", "", name, flags=re.IGNORECASE)
    words = name.split()[:8]
    return " ".join(words).strip() or "My library"


def ensure_subject(vault_root: Path, vault, source_id: str, title: str, *, clock: Clock | None = None) -> tuple[str, bool]:
    """The subject this source is filed under, creating a provisional one
    named from the book when nothing fits. ``(subject_id, created)``."""

    from learnloop.vault.loader import add_subject

    for source_set in vault.source_sets:
        if any(member.source_id == source_id for member in source_set.members):
            return source_set.subject_id, False
    name = subject_title_from(title)
    wanted = kebab_case(name) or "my-library"
    if wanted in vault.subjects:
        return wanted, False
    for subject_id, subject in vault.subjects.items():
        metadata = getattr(subject, "metadata", None)
        if kebab_case(str(getattr(metadata, "title", "") or "")) == wanted:
            return subject_id, False
    add_subject(vault_root, wanted, name, clock=clock)
    return kebab_case(wanted), True


# ---------------------------------------------------------------------------
# The job ledger
# ---------------------------------------------------------------------------


def _job_source_id(job: Mapping[str, Any]) -> str | None:
    payload = job.get("payload") or {}
    result = job.get("result") or {}
    return payload.get("source_id") or result.get("source_id")


def _jobs_for_source(jobs: Iterable[Mapping[str, Any]], source_id: str) -> list[dict[str, Any]]:
    return [dict(job) for job in jobs if _job_source_id(job) == source_id]


def auto_jobs(repo, source_id: str) -> list[dict[str, Any]]:
    """This source's planning jobs, newest first."""

    return _jobs_for_source(repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,), limit=500), source_id)


def latest_auto_outcome(repo, source_id: str) -> dict[str, Any] | None:
    for job in auto_jobs(repo, source_id):
        if job["status"] == "completed" and job.get("result"):
            return dict(job["result"])
    return None


def _build_state(repo, outcome: Mapping[str, Any]) -> dict[str, Any]:
    """What became of a ``building`` outcome's batch: its status, proposal,
    whether it applied, was taken back out, or left changes to look at."""

    batch_id = outcome.get("build_batch_id")
    batch = repo.get_ingest_batch(batch_id) if batch_id else None
    state: dict[str, Any] = {"batch": batch, "status": (batch or {}).get("status"), "proposal_id": None,
                             "applied": False, "undone": False, "pending": 0, "error": None}
    if batch is None:
        return state
    for job in repo.ingest_jobs_for_batch(batch_id):
        if job.get("error") and state["error"] is None:
            state["error"] = (job.get("error") or {}).get("message")
        if job["job_type"] not in {"bootstrap_synthesis", "append_synthesis"}:
            continue
        result = job.get("result") or {}
        state["proposal_id"] = result.get("proposal_id")
        state["applied"] = bool(result.get("applied") or result.get("auto_applied_item_ids"))
    if state["proposal_id"]:
        items = repo.proposal_items(state["proposal_id"])
        revertable = [item for item in items if _revertable(item)]
        if revertable and all(item.get("decision") == "rejected" for item in revertable):
            state["undone"] = True
        state["pending"] = sum(1 for item in items if item.get("decision") == "pending")
    return state


# What "take this book's questions back out" reverts: the topics (made
# dormant), the questions (made inactive) and the links between ideas. Ideas,
# skills and question recipes stay as inert records, so no evidence the
# learner earned is deleted (the proposal revert path cannot remove them).
_REVERTABLE_ITEM_TYPES = frozenset({"learning_object", "practice_item", "concept_edge"})


def _revertable(item: Mapping[str, Any]) -> bool:
    return item.get("item_type") in _REVERTABLE_ITEM_TYPES and item.get("operation") == "create"


def built_unit_ids(repo, source_id: str) -> set[str]:
    """Chapters an automatic build covers and the learner has not undone."""

    built: set[str] = set()
    for job in auto_jobs(repo, source_id):
        result = job.get("result") or {}
        if job["status"] != "completed" or result.get("outcome") != "building":
            continue
        if _build_state(repo, result)["undone"]:
            continue
        built.update(result.get("chapter_ids") or [])
    return built


def _active(job_or_batch: Mapping[str, Any] | None) -> bool:
    return bool(job_or_batch) and job_or_batch.get("status") in {"queued", "running", "waiting_for_input"}


# ---------------------------------------------------------------------------
# The planning job (handler for AUTO_STUDY_MAP_JOB)
# ---------------------------------------------------------------------------


def _source_from_dependency(ctx) -> str | None:
    for dep_id in ctx.repo.ingest_job_dependency_ids(ctx.job_id):
        dependency = ctx.repo.get_ingest_job(dep_id)
        if dependency and dependency.get("job_type") == "import":
            source_id = (dependency.get("result") or {}).get("source_id")
            if source_id:
                return str(source_id)
    return None


def run_auto_study_map(ctx) -> dict[str, Any]:
    """Plan (and queue) the automatic question build for one source."""

    from learnloop.content.pipeline.build_plan import build_build_plan
    from learnloop.content.pipeline.quick_add import _default_brief
    from learnloop.content.pipeline.runner import IngestRunnerError, JobSpec
    from learnloop.content.sources.source_outline import build_source_outline
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set
    from learnloop.vault_lock import vault_mutation_lock

    payload = ctx.payload
    source_id = payload.get("source_id") or _source_from_dependency(ctx)
    if not source_id:
        raise IngestRunnerError("The automatic build has no source to plan for.", code="source_missing")
    base = {"source_id": source_id}
    vault = load_vault(ctx.vault_root)
    config = vault.config
    if not config.ingest.auto_build:
        return {"outcome": "skipped", "reason": "auto_build_off", **base}
    artifact = ctx.repo.get_source_artifact(source_id)
    if artifact is None:
        raise IngestRunnerError(f"Source {source_id!r} is not in the library.", code="source_missing")
    if payload.get("problem_set") or not artifact.get("reader_enabled", 1):
        return {"outcome": "skipped", "reason": "problem_set", **base}
    if payload.get("keep_local"):
        return {"outcome": "waiting", "reason": "kept_local", **base}
    resolved = _completed_extraction(ctx.repo, source_id)
    if resolved is None:
        raise IngestRunnerError("This source has no text yet.", code="not_extracted", retryable=True)
    revision_id, extraction_id = resolved

    ctx.report("inventoried", message="Choosing what to build first")
    outline = build_source_outline(ctx.repo, extraction_id)
    chapters = outline_chapters(outline)
    built = built_unit_ids(ctx.repo, source_id)
    approved_chapters = payload.get("chapter_ids")
    whole = False
    if approved_chapters:
        wanted = set(approved_chapters)
        picked = [chapter for chapter in chapters if chapter.unit_id in wanted and chapter.unit_id not in built]
    else:
        cap = int(config.ingest.budgets.quick_add_scope_input_tokens)
        if not built and outline.approx_tokens <= cap:
            picked, whole = list(chapters), True
        else:
            picked = reading_order_scope(
                chapters, built=built, start_unit_id=payload.get("start_unit_id"),
                cap_tokens=cap, floor_tokens=min(FLOOR_TOKENS, max(cap // 4, 1)),
            )
    if not picked:
        return {"outcome": "skipped", "reason": "nothing_to_build", **base}
    labels = [chapter.label for chapter in picked]
    chapter_ids = [chapter.unit_id for chapter in picked]
    unit_ids = [unit_id for chapter in picked for unit_id in chapter.unit_ids]
    plan_info = {"chapters": labels, "chapter_ids": chapter_ids, "whole_source": whole}

    route = ctx.services.authoring_route(ctx)
    if not route.ready:
        return {"outcome": "waiting", "reason": "no_ai", "provider": route.provider,
                "message": route.message, **plan_info, **base}
    if route.consent_key not in config.ai.consent:
        return {"outcome": "waiting", "reason": "needs_consent", "provider": route.provider,
                "consent_key": route.consent_key, **plan_info, **base}

    totals = build_build_plan(
        ctx.repo, config, vault, subject_id=None,
        selections=[{"extraction_id": extraction_id, "selected_unit_ids": unit_ids}],
    ).as_dict()["totals"]
    usd = 0.0 if route.subscription else estimate_usd(config, route.provider, totals)
    if not payload.get("approved"):
        reason = cost_pause_reason(config, usd, spent_today_usd(ctx.repo, ctx.clock.now()))
        if reason is not None:
            return {"outcome": "paused", "reason": "cost", "cost_reason": reason,
                    "estimate_usd": round(usd, 2), "provider": route.provider, **plan_info, **base}

    revision = ctx.repo.get_source_revision(revision_id)
    title = learner_title(artifact, revision)
    category = artifact.get("acquisition_kind")
    role = _ROLE_BY_CATEGORY.get(str(category or ""), "reference")
    source_set_id = f"sset_quickadd_{source_id}"
    with vault_mutation_lock(ctx.vault_root, purpose="auto_study_map"):
        subject_id, created = ensure_subject(ctx.vault_root, vault, source_id, title, clock=ctx.clock)
        vault = load_vault(ctx.vault_root)
        existing = next((s for s in vault.source_sets if s.id == source_set_id), None)
        previous = [
            entry.unit_id
            for member in (existing.members if existing else [])
            if member.source_id == source_id
            for entry in member.scope
        ]
        order = {unit.unit_id: index for index, unit in enumerate(outline.units)}
        scope = sorted(set(previous) | set(unit_ids), key=lambda unit_id: order.get(unit_id, len(order)))
        upsert_source_set(
            ctx.vault_root,
            {
                "id": source_set_id,
                "subject_id": existing.subject_id if existing else subject_id,
                "title": title or source_set_id,
                "members": [{
                    "source_id": source_id,
                    "revision_id": revision_id,
                    "default_role": role,
                    "scope": [{"unit_id": unit_id} for unit_id in scope],
                    "priority": 1,
                }],
            },
            clock=ctx.clock,
        )
    brief = _default_brief({"practice_items": "as_you_read"}, title, subject_id, vault=vault)
    apply = bool(config.ingest.auto_apply_passing_builds)
    build_batch_id = ctx.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"extraction_id": extraction_id,
                                  "units": [{"unit_id": unit_id, "role": role} for unit_id in unit_ids]}),
            JobSpec(
                "bootstrap_synthesis",
                {"source_set_id": source_set_id, "brief": brief, "mode": "auto", "apply": apply,
                 "auto_build_source_id": source_id},
                depends_on=(0,),
            ),
        ],
        subject_id=subject_id,
        source_set_id=source_set_id,
        priority=BUILD_PRIORITY,
    )
    return {
        "outcome": "building",
        "subject_id": subject_id,
        "subject_created": created,
        "source_set_id": source_set_id,
        "build_batch_id": build_batch_id,
        "unit_ids": unit_ids,
        "estimate_usd": round(usd, 4),
        "provider": route.provider,
        "applies": apply,
        **plan_info,
        **base,
    }


# ---------------------------------------------------------------------------
# Follow-ups the shell and the Reader ask for
# ---------------------------------------------------------------------------


def request_auto_build(ingest_jobs, source_id: str, *, approved: bool = False,
                       chapter_ids: Sequence[str] | None = None, start_unit_id: str | None = None) -> str:
    """Plan another automatic build for ``source_id`` (connect, build now,
    keep ahead). ``approved`` is the learner's explicit "Build them": it passes
    the cost pause once, for the chapters the pause named."""

    if approved and chapter_ids is None:
        outcome = latest_auto_outcome(ingest_jobs.repository, source_id) or {}
        if outcome.get("outcome") == "paused":
            chapter_ids = outcome.get("chapter_ids")
    return ingest_jobs.enqueue_auto_build(
        source_id, approved=approved, chapter_ids=chapter_ids, start_unit_id=start_unit_id,
    )


def release_waiting_builds(ingest_jobs) -> list[str]:
    """After an AI is connected: plan again for every book waiting on it."""

    repo = ingest_jobs.repository
    seen: set[str] = set()
    released: list[str] = []
    for job in repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,), limit=500):
        source_id = _job_source_id(job)
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        if _active(job):
            continue
        result = job.get("result") or {}
        if job["status"] == "completed" and result.get("outcome") == "waiting" and result.get("reason") in {"no_ai", "needs_consent"}:
            request_auto_build(ingest_jobs, source_id)
            released.append(source_id)
    return released


def advance_reading_build(ingest_jobs, extraction_id: str, section_id: str) -> dict[str, Any] | None:
    """The Reader reached ``section_id``: keep one chapter ahead (Q6).

    Only for sources added through Add whose questions were built and not
    undone; nothing while a build for the book is still running."""

    repo = ingest_jobs.repository
    run = repo.get_extraction_run(extraction_id)
    revision = repo.get_source_revision(run["revision_id"]) if run else None
    source_id = (revision or {}).get("source_id")
    if not source_id:
        return None
    jobs = auto_jobs(repo, source_id)
    if not jobs or any(_active(job) for job in jobs):
        return None
    building = [job.get("result") or {} for job in jobs if (job.get("result") or {}).get("outcome") == "building"]
    if not building:
        return None
    latest_state = _build_state(repo, building[0])
    if latest_state["undone"] or _active(latest_state["batch"]):
        return None

    from learnloop.content.sources.source_outline import build_source_outline
    from learnloop.vault.loader import load_vault

    if not load_vault(ingest_jobs.vault_root).config.ingest.auto_build:
        return None
    chapters = outline_chapters(build_source_outline(repo, extraction_id))
    wanted = chapters_to_keep_ahead(chapters, section_id, built_unit_ids(repo, source_id))
    if not wanted:
        return None
    batch_id = request_auto_build(ingest_jobs, source_id, chapter_ids=[chapter.unit_id for chapter in wanted])
    return {"batch_id": batch_id, "source_id": source_id, "chapters": [chapter.label for chapter in wanted]}


def undo_source_questions(ingest_jobs, source_id: str, *, clock: Clock | None = None) -> int:
    """Take a book's automatic questions back out (one-tap undo, Q3)."""

    from learnloop.content.proposals.proposals import reject_items

    repo = ingest_jobs.repository
    reverted = 0
    for job in auto_jobs(repo, source_id):
        result = job.get("result") or {}
        if result.get("outcome") != "building":
            continue
        state = _build_state(repo, result)
        if not state["proposal_id"] or state["undone"]:
            continue
        item_ids = [
            item["id"] for item in repo.proposal_items(state["proposal_id"])
            if _revertable(item) and item.get("decision") in {"accepted", "pending"}
        ]
        if item_ids:
            reverted += reject_items(ingest_jobs.vault_root, state["proposal_id"], item_ids)
    return reverted


# ---------------------------------------------------------------------------
# The book card's one status line (§6.3, §6.7)
# ---------------------------------------------------------------------------


def _line(text: str, tone: str = "quiet", action: tuple[str, str] | None = None,
          details: str | None = None) -> dict[str, Any]:
    return {
        "text": text,
        "tone": tone,
        "action": {"kind": action[0], "label": action[1]} if action else None,
        "details": details,
    }


def _import_failure_line(job: Mapping[str, Any], category: str | None) -> dict[str, Any]:
    error = job.get("error") or {}
    message = str(error.get("message") or "")
    code = str(error.get("code") or "")
    lowered = f"{code} {message}".lower()
    retry = ("retry", "Try again")
    if category == "youtube" and ("caption" in lowered or "transcript" in lowered):
        return _line("This video has no captions", "problem", retry, message or None)
    if category in {"web", "arxiv", "youtube"} or any(
        marker in lowered for marker in ("http", "fetch", "connection", "timed out", "timeout", "network", "unreachable")
    ):
        return _line("Couldn't reach the page", "problem", retry, message or None)
    if category == "pdf":
        return _line("Couldn't read this PDF", "problem", retry, message or None)
    return _line(f"Couldn't get this {kind_noun(category)} ready", "problem", retry, message or None)


def _health_line(repo, source_id: str) -> dict[str, Any] | None:
    resolved = _completed_extraction(repo, source_id)
    if resolved is None:
        return None
    run = repo.get_extraction_run(resolved[1]) or {}
    health = run.get("health") or {}
    flags = set(health.get("flags") or [])
    scanned = any(
        "image_only_page" in (page.get("flags") or []) for page in health.get("pages") or [] if isinstance(page, Mapping)
    )
    if scanned:
        return _line("Some pages look scanned", "quiet", ("text_recognition", "Read them with text recognition"))
    if "marker_failed_pypdf_fallback" in flags:
        return _line("Maths may look rough in the text view", "quiet", ("open_settings", "Fix it"),
                     "marker_failed_pypdf_fallback")
    return None


def _minutes(chapter_count: int) -> int:
    return 3 + max(chapter_count, 1)


def source_status_line(repo, vault, source_id: str | None, *, batch_id: str | None = None) -> dict[str, Any] | None:
    """The one quiet line a book card shows, or ``None`` when there is
    nothing to say. ``batch_id`` names an Add whose link is still being
    fetched (no source yet)."""

    if source_id is None:
        if not batch_id:
            return None
        jobs = repo.ingest_jobs_for_batch(batch_id)
        import_job = next((job for job in jobs if job["job_type"] == "import"), None)
        if import_job is None:
            return None
        category = _category_of((import_job.get("payload") or {}).get("source"))
        if import_job["status"] in {"failed", "blocked", "cancelled"}:
            return _import_failure_line(import_job, category)
        return _line(f"Getting this {kind_noun(category)} ready", "working")

    artifact = repo.get_source_artifact(source_id)
    if artifact is None:
        return None
    category = artifact.get("acquisition_kind")
    noun = kind_noun(category)
    imports = _jobs_for_source(repo.ingest_jobs_by_types(("import",), limit=500), source_id)
    has_text = _completed_extraction(repo, source_id) is not None
    if not has_text:
        latest_import = imports[0] if imports else None
        if latest_import is None:
            return None
        if latest_import["status"] in {"failed", "blocked", "cancelled"}:
            return _import_failure_line(latest_import, category)
        return _line(f"Getting this {noun} ready", "working")

    jobs = auto_jobs(repo, source_id)
    latest = jobs[0] if jobs else None
    if latest is None:
        return _health_line(repo, source_id)
    if _active(latest):
        # The text is ready; LearnLoop is choosing what to build (§6.3 states).
        return _line("Chapters found", "working")
    if latest["status"] in {"failed", "blocked"}:
        error = latest.get("error") or {}
        return _line(f"Questions for this {noun} need another try", "problem", ("build_now", "Retry"),
                     error.get("message"))
    outcome = latest.get("result") or {}
    kind = outcome.get("outcome")
    phrase = chapter_phrase(outcome.get("chapters") or [], whole=bool(outcome.get("whole_source")), noun=noun)
    if kind == "skipped":
        return _health_line(repo, source_id)
    if kind == "waiting":
        reason = outcome.get("reason")
        if reason == "no_ai":
            return _line("Questions need an AI connection", "quiet", ("connect_ai", "Connect"), outcome.get("message"))
        if reason == "needs_consent":
            # The provider is named on the connect sheet, not on the surface
            # (glossary §9: provider names live in Settings and details).
            return _line("Questions wait for your OK", "quiet", ("connect_ai", "Review"),
                         consent_label(str(outcome.get("consent_key") or "")))
        if reason == "kept_local":
            return _line("Kept on this computer — no questions are written for it", "quiet")
        return None
    if kind == "paused":
        usd = float(outcome.get("estimate_usd") or 0.0)
        return _line(f"Building questions for {phrase} would cost about ${usd:,.2f}", "quiet",
                     ("build_now", "Build them"))
    if kind != "building":
        return None
    state = _build_state(repo, outcome)
    if state["undone"]:
        return _line(f"Questions for this {noun} were taken back out", "quiet", ("build_now", "Build them again"))
    if state["status"] in {"queued", "running", "waiting_for_input"}:
        return _line(f"Questions for {phrase} in about {_minutes(len(outcome.get('chapters') or []))} min",
                     "working")
    if state["status"] in {"failed", "blocked", "cancelled"}:
        return _line(f"Questions for {phrase} need another try", "problem", ("retry", "Retry"), state["error"])
    if not state["applied"]:
        return _line(f"Questions for {phrase} need a look", "quiet", ("open_changes", "Review"))
    if state["pending"]:
        count = state["pending"]
        return _line(f"{count} change{'s' if count != 1 else ''} need a look", "quiet", ("open_changes", "Review"))
    health = _health_line(repo, source_id)
    if health is not None:
        return health
    return _line(f"Questions ready for {phrase}", "quiet", ("undo_questions", "Undo"))


def _category_of(source: Any) -> str | None:
    try:
        return resolve_source(str(source or "")).category
    except UnsupportedSourceError:
        return None


def pending_adds(repo, *, limit: int = 30) -> list[dict[str, Any]]:
    """Adds whose link is still being fetched (no library card yet)."""

    entries: list[dict[str, Any]] = []
    for batch in repo.list_ingest_batches(limit=200):
        if (
            batch.get("workflow_type") != ADD_SOURCE_WORKFLOW
            or batch.get("status") in {"completed", "cancelled"}
            or batch.get("cancel_requested")
        ):
            continue
        jobs = repo.ingest_jobs_for_batch(batch["id"])
        import_job = next((job for job in jobs if job["job_type"] == "import"), None)
        if import_job is None or _job_source_id(import_job) or import_job["status"] == "cancelled":
            continue
        source = str((import_job.get("payload") or {}).get("source") or "")
        category = _category_of(source)
        entries.append({
            "batch_id": batch["id"],
            "source": source,
            "kind": category,
            "kind_noun": kind_noun(category),
            "title": source,
            "status_line": source_status_line(repo, None, None, batch_id=batch["id"]),
        })
        if len(entries) >= limit:
            break
    return entries


def latest_add_batch(repo, source_id: str) -> str | None:
    imports = _jobs_for_source(repo.ingest_jobs_by_types(("import",), limit=500), source_id)
    return imports[0]["batch_id"] if imports else None


def latest_build_batch(repo, source_id: str) -> str | None:
    for job in auto_jobs(repo, source_id):
        batch_id = (job.get("result") or {}).get("build_batch_id")
        if batch_id:
            return str(batch_id)
    return None


__all__ = [
    "ADD_SOURCE_PRIORITY",
    "ADD_SOURCE_WORKFLOW",
    "AUTO_BUILD_WORKFLOW",
    "AUTO_STUDY_MAP_JOB",
    "AddSourceOptions",
    "AuthoringRoute",
    "Chapter",
    "add_source",
    "advance_reading_build",
    "authoring_route_for",
    "built_unit_ids",
    "chapter_phrase",
    "consent_key",
    "consent_label",
    "cost_pause_reason",
    "default_authoring_route",
    "ensure_subject",
    "estimate_usd",
    "kind_noun",
    "latest_auto_outcome",
    "learner_title",
    "outline_chapters",
    "pending_adds",
    "reading_order_scope",
    "release_waiting_builds",
    "request_auto_build",
    "run_auto_study_map",
    "source_status_line",
    "undo_source_questions",
    "what_leaves",
]
