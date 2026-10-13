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
from durable rows. The build a planner queues has an id derived from the
planner (:func:`child_batch_id`) and carries the plan on its jobs, so it is
found even when the planner died before saving its result. Per book, migration
186 keeps the learner's "Keep this book on this computer" (read at every
outbound boundary) and the automatic-build state: the generation an Undo
advances and the reading position a running build could not act on yet.

Kill switches ``[ingest] auto_build`` (off: Add only makes the source readable,
and queued automatic work is cancelled before its next paid stage) and
``[ingest] auto_apply_passing_builds`` (off: automatic builds wait as
proposals), both read when the work runs, not when it was planned.
"""

from __future__ import annotations

import io
import re
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, FrozenClock, utc_now_iso
from learnloop.content.sources.front_matter import FRONT_MATTER
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
# The separate OK for sending a whole file out: a recording to a transcription
# service, a whole PDF to a model that reads PDFs (spec §6.6, review F1).
FILE_UPLOAD_CONSENT = "whole_files"
FILE_UPLOAD_DATA_FLOW = "whole_files"
KEPT_LOCAL_BUILD_MESSAGE = "This book is kept on this computer, so no questions are written for it."
# Automatic builds' batch ids: ``batch_auto_<planner job id>`` (review F3).
AUTO_BUILD_BATCH_PREFIX = "batch_auto_"
# The learner's Undo as an owner verdict in judgment_ledger (review F12).
UNDO_JUDGMENT_TASK = "auto_applied_content"
# How to get text recognition, plainly (usability round 2: the details pasted
# the extractor's raw "install marker-pdf for OCR support"). It comes with
# LearnLoop's optional PDF tools; the command is the install's own.
TEXT_RECOGNITION_HOW_TO = (
    "To add it, run uv sync --extra pdf in LearnLoop's folder, then restart LearnLoop."
)
TEXT_RECOGNITION_UNAVAILABLE_MESSAGE = (
    "Text recognition isn't installed on this computer, so this was added without it. "
    + TEXT_RECOGNITION_HOW_TO
)
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
_CHAPTER_NUMBER = re.compile(r"^\s*(?:chapter|ch\.?|part|lecture|unit)?\s*(\d+)\b", re.IGNORECASE)
_JUNK_PDF_TITLES = re.compile(r"^(?:untitled|microsoft word|document\d*|\s*)$|\.(?:docx?|tex|dvi|pdf)$", re.IGNORECASE)
# The AI the learner set up, named as they know it (usability round 2: a Codex
# user's one-time OK said "ChatGPT" while everything else said Codex).
_CONSENT_LABEL = {"codex": "Codex (your ChatGPT account)", "chatgpt": "ChatGPT", "openrouter": "OpenRouter"}


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


# A PDF is a paper when it opens with an abstract and is short (usability
# round 2: an 11-page paper was called a "book").
_ABSTRACT_LABEL = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?abstract\s*[.:]?\s*$", re.IGNORECASE)
_PAPER_MAX_PAGES = 60


def source_kind_noun(repo, source_id: str, category: str | None) -> str:
    """What the learner calls this source: ``kind_noun``, except that a short
    PDF whose text opens with an Abstract is a paper."""

    noun = kind_noun(category)
    if category != "pdf":
        return noun
    resolved = _completed_extraction(repo, source_id)
    if resolved is None:
        return noun
    extraction_id = resolved[1]
    with repo.connection() as connection:
        labels = [
            str(row["label"] or "")
            for row in connection.execute(
                "SELECT label FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal LIMIT 4",
                (extraction_id,),
            ).fetchall()
        ]
        pages = connection.execute(
            "SELECT MAX(COALESCE(page_end, page_start)) AS units_end FROM source_document_units WHERE extraction_id = ?",
            (extraction_id,),
        ).fetchone()["units_end"]
        if pages is None:
            pages = connection.execute(
                "SELECT MAX(page) AS last FROM source_document_blocks WHERE extraction_id = ?", (extraction_id,)
            ).fetchone()["last"]
    if any(_ABSTRACT_LABEL.match(label) for label in labels) and (pages is None or int(pages) + 1 <= _PAPER_MAX_PAGES):
        return "paper"
    return noun


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
        if options.keep_local and not artifact.get("keep_local"):
            # Asking for more privacy on a book already here always applies,
            # to the work already queued for it too.
            keep_on_this_computer(ingest_jobs, artifact["id"], clock=clock)
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
        if options.keep_local:
            # Persisted with the book before anything is queued (review F1):
            # every later build, retry and Reader request reads it.
            repo.set_source_keep_local(source_id, True, clock=clock)
        item.update(status="added", source_id=source_id, revision_id=revision_id, title=title, preparing=True)
    elif category in {"pdf", "textfile", "audio"} and not resolved.source.lower().startswith(("http://", "https://")):
        item.update(status="unsupported", message=MISSING_FILE_MESSAGE)
        return item
    else:
        item.update(status="queued", preparing=True)

    if options.text_recognition and not text_recognition_available(keep_local=options.keep_local):
        # Text recognition was asked for but nothing installed can do it
        # (review F9): add the book without it and say so, never pretend.
        options = replace(options, text_recognition=False)
        item["message"] = TEXT_RECOGNITION_UNAVAILABLE_MESSAGE
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
        title = pdf_metadata_title(raw_bytes)
        if title:
            return title
    return title_from_file_name(path.name)


def pdf_metadata_title(raw_bytes: bytes) -> str | None:
    """The PDF's own title when it has a real one (not "Untitled", not a file
    name), else ``None``. Add and the Ingest import both use it (usability
    round 2: a book imported through Ingest was titled by its file name)."""

    try:
        from pypdf import PdfReader

        metadata = PdfReader(io.BytesIO(raw_bytes)).metadata
        title = str((metadata.title if metadata else None) or "").strip()
    except Exception:  # noqa: BLE001 - a damaged PDF still gets a title
        return None
    if title and len(title) >= 3 and not _JUNK_PDF_TITLES.search(title):
        return title
    return None


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
        for job in repo.ingest_jobs_for_source(("import",), source_id)
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
                front_matter=bool(FRONT_MATTER.match(str(top.label or ""))),
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
    return chapter.front_matter or bool(FRONT_MATTER.match(chapter.label))


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


def file_upload_allowed(config) -> bool:
    """The learner's separate OK for sending a whole file out (a recording to
    be transcribed, a whole PDF to a model that reads PDFs). The connection's
    OK covers passages and answers only (spec §6.6)."""

    return FILE_UPLOAD_CONSENT in config.ai.consent


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


# -- Money (Q5; review F2) ----------------------------------------------------
#
# Two different things, kept apart:
# * a *confirmation threshold* (``threshold_usd``, ``daily_cap_fraction``): an
#   automatic build above it asks first ("would cost about $3.10 · Build them"),
#   and the learner's "Build them" passes it once;
# * *enforceable limits*: the build's authorization (what the learner allowed,
#   with headroom for the estimate) and ``daily_cap_usd``. "Build them" never
#   passes the daily cap. Every paid job of an automatic build is admitted
#   through ``learnloop.ai.spend.SpendBudget`` against what is left of both,
#   priced at the route resolved when the job runs (a runtime fallback is
#   priced as itself) and counted from the receipts of every attempt.
# Spending is counted from ``model_call_receipts`` (every model call LearnLoop
# makes, whatever started it), not from planner estimates. Subscription routes
# (Codex, the ChatGPT plan) are never paused or capped (Slice A §5 rule 6);
# their estimate is kept in tokens, ``cost_basis = estimated_only``.

AUTHORIZATION_HEADROOM = 1.25


def _price_per_million(config, provider_name: str | None) -> float:
    pause = config.ingest.cost_pause
    return float(pause.prices.get(provider_name or "", pause.default_price_per_million_tokens))


def is_subscription_route(config, provider_name: str | None) -> bool:
    from learnloop.ai.spend import is_subscription_transport
    from learnloop.config import CODEX_PROVIDER_NAMES

    profile = config.ai.providers.get(provider_name or "")
    if profile is not None:
        return is_subscription_transport(profile=profile)
    return (provider_name or "") in CODEX_PROVIDER_NAMES


def plan_tokens(totals: Mapping[str, Any]) -> int:
    return int(totals.get("input_tokens") or 0) + int(totals.get("max_output_tokens") or 0)


def estimate_usd(config, provider_name: str, totals: Mapping[str, Any]) -> float:
    """A metered route's price for a build plan: input plus maximum output."""

    return plan_tokens(totals) * _price_per_million(config, provider_name) / 1_000_000


def cost_pause_reason(config, usd: float, spent_today_usd: float) -> str | None:
    """``over_threshold`` / ``daily_cap`` when a build should ask first (Q5).

    A confirmation threshold only; :func:`decide_cost` enforces the limits."""

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


def _receipt_usd(config, row: Mapping[str, Any]) -> float:
    """What one model call cost in money: the provider's reported cost, else
    its tokens at the route's price; nothing for a subscription call."""

    usage = str(row.get("usage_json") or "")
    if "estimated_only" in usage or is_subscription_route(config, row.get("provider")):
        return 0.0
    if row.get("cost") is not None:
        return float(row["cost"])
    tokens = int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)
    return tokens * _price_per_million(config, row.get("provider")) / 1_000_000


def metered_spend_usd(config, rows: Iterable[Mapping[str, Any]]) -> float:
    return sum(_receipt_usd(config, row) for row in rows)


def _day_start_iso(now: datetime) -> str:
    from datetime import UTC

    return now.astimezone(UTC).date().isoformat() + "T00:00:00"


def _active_auto_build_batches(repo) -> list[dict[str, Any]]:
    return [
        batch for batch in repo.ingest_batches_by_workflow(
            "bootstrap_synthesis", exclude_statuses=("completed", "failed", "cancelled", "blocked"),
        )
        if str(batch["id"]).startswith(AUTO_BUILD_BATCH_PREFIX)
    ]


def _batch_job_ids(repo, batch_id: str) -> list[str]:
    return [job["id"] for job in repo.ingest_jobs_for_batch(batch_id)]


def build_spend_usd(repo, config, batch_id: str) -> float:
    """What one automatic build has cost so far, every attempt included."""

    rows = repo.model_call_spend_rows(owner_kind="ingest_job", owner_ids=_batch_job_ids(repo, batch_id))
    return metered_spend_usd(config, rows)


def spent_today_usd(repo, config, now: datetime) -> float:
    """Money spent today on every model call LearnLoop made (receipts), plus
    what automatic builds still running are allowed to spend."""

    spent = metered_spend_usd(config, repo.model_call_spend_rows(started_since=_day_start_iso(now)))
    reserved = 0.0
    for batch in _active_auto_build_batches(repo):
        auto = _child_auto_info(repo, batch["id"]) or {}
        estimate = auto.get("estimate_usd")
        if estimate is None or auto.get("subscription"):
            continue
        reserved += max(float(estimate) - build_spend_usd(repo, config, batch["id"]), 0.0)
    return spent + reserved


@dataclass(frozen=True)
class CostDecision:
    """What an automatic build may spend, and whether it must ask first."""

    subscription: bool
    tokens: int
    estimate_usd: float | None
    pause: str | None = None
    authorized_usd: float | None = None
    daily_remaining_usd: float | None = None

    @property
    def cost_basis(self) -> str:
        return "estimated_only" if self.subscription else "metered"

    def as_dict(self) -> dict[str, Any]:
        return {
            "subscription": self.subscription,
            "cost_basis": self.cost_basis,
            "estimate_tokens": self.tokens,
            "estimate_usd": None if self.estimate_usd is None else round(self.estimate_usd, 4),
            "authorized_usd": None if self.authorized_usd is None else round(self.authorized_usd, 4),
            "daily_remaining_usd": None if self.daily_remaining_usd is None else round(self.daily_remaining_usd, 4),
            "pause": self.pause,
        }


def decide_cost(config, repo, provider_name: str, totals: Mapping[str, Any], *,
                approved: bool, now: datetime) -> CostDecision:
    """Price a build plan and decide: run silently, ask first (``over_threshold``
    / ``daily_cap``: "Build them" passes these), or stop (``budget_used``: the
    daily cap is spent; "Build them" does not pass it)."""

    tokens = plan_tokens(totals)
    pause_config = config.ingest.cost_pause
    if is_subscription_route(config, provider_name):
        # Billed to the subscription: no pause and no dollar cap, tokens kept.
        owner_price = pause_config.prices.get(provider_name)
        usd = tokens * float(owner_price) / 1_000_000 if owner_price is not None else None
        return CostDecision(subscription=True, tokens=tokens, estimate_usd=usd)
    usd = estimate_usd(config, provider_name, totals)
    spent = spent_today_usd(repo, config, now)
    remaining = None
    if pause_config.daily_cap_usd is not None:
        remaining = max(float(pause_config.daily_cap_usd) - spent, 0.0)
    if remaining is not None and usd > remaining:
        return CostDecision(subscription=False, tokens=tokens, estimate_usd=usd, pause="budget_used",
                            daily_remaining_usd=remaining)
    if not approved:
        reason = cost_pause_reason(config, usd, spent)
        if reason is not None:
            return CostDecision(subscription=False, tokens=tokens, estimate_usd=usd, pause=reason,
                                daily_remaining_usd=remaining)
    threshold = float(pause_config.threshold_usd)
    # A silent build may spend up to the standing "runs without asking" amount;
    # an approved one what the learner approved, with headroom for the estimate.
    authorized = max(usd * AUTHORIZATION_HEADROOM, threshold) if approved else max(threshold, usd)
    if remaining is not None:
        authorized = min(authorized, remaining)
    return CostDecision(subscription=False, tokens=tokens, estimate_usd=usd, authorized_usd=authorized,
                        daily_remaining_usd=remaining)


class AutoBuildPaused(Exception):
    """An automatic build's next paid job is not admitted."""


def admit_auto_build_job(ctx, *, planned_tokens: int | None = None) -> None:
    """Admit one paid job attempt of an automatic build, or stop it (F1-F5),
    and admit each of its model requests (re-review F2).

    Runs at the start of every attempt (a retry is admitted again):
    * the kill switch ``[ingest] auto_build`` and the book's Undo generation
      are read now, not when the build was planned: work they no longer allow
      is cancelled before any model call;
    * a book kept on this computer sends nothing;
    * money: the job's ceiling-priced estimate must fit what is left of the
      build's authorization and of today's cap (priced at the route resolved
      now), and then, for the rest of the attempt, EVERY physical request
      (transport retries, a provider's JSON repair, append reconciliation's
      follow-up call, parallel inventory workers) passes a
      :class:`~learnloop.ai.spend.MeteredRequestGate` over the same limit,
      settled with what each request reported. A refused request stops the
      job as ``spend_paused`` before it is sent;
    * once the build is cancelled (Undo, keeping the book on this computer)
      it starts no further request, on any route.
    No-op for jobs that are not part of an automatic build."""

    from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
    from learnloop.content.pipeline.runner import IngestRunnerError, JobCancelled
    from learnloop.vault.loader import load_vault

    auto = ctx.payload.get("auto_build")
    if not isinstance(auto, Mapping):
        return
    repo = ctx.repo
    source_id = str(auto.get("source_id") or "")
    config = load_vault(ctx.vault_root).config
    batch_id = str(ctx.job["batch_id"])
    if not config.ingest.auto_build:
        _cancel_rest_of_batch(ctx)
        raise JobCancelled("Automatic question building was turned off.")
    if int(repo.source_auto_build_state(source_id)["generation"]) != int(auto.get("generation") or 0):
        _cancel_rest_of_batch(ctx)
        raise JobCancelled("This book's questions were taken back out.")
    if repo.source_kept_local(source_id):
        raise IngestRunnerError(KEPT_LOCAL_BUILD_MESSAGE, code="kept_local", retryable=False)
    route = ctx.services.authoring_route(ctx)
    tokens = int(planned_tokens if planned_tokens is not None else auto.get("job_tokens") or 0)
    spent_build = build_spend_usd(repo, config, batch_id)
    authorized = auto.get("authorized_usd")
    limit = max(float(authorized) - spent_build, 0.0) if authorized is not None else None
    reason = "authorization"
    cap = config.ingest.cost_pause.daily_cap_usd
    if cap is not None:
        today = metered_spend_usd(config, repo.model_call_spend_rows(started_since=_day_start_iso(ctx.clock.now())))
        daily_left = max(float(cap) - today, 0.0)
        if limit is None or daily_left < limit:
            limit, reason = daily_left, "daily_cap"
    if limit is None:
        # Planned before this rule, or on the subscription (no authorization
        # recorded): the standing "runs without asking" amount.
        limit = float(config.ingest.cost_pause.threshold_usd)
    details = {"reason": reason, "provider": route.provider, "limit_usd": round(limit, 4),
               "spent_by_build_usd": round(spent_build, 4)}
    if not is_subscription_route(config, route.provider):
        usd = tokens * _price_per_million(config, route.provider) / 1_000_000
        budget = SpendBudget(
            SpendCaps(max_candidates=10**9, max_pairs=10**9, max_retries=10**9, max_calls=10**9,
                      max_total_tokens=10**15, max_estimated_usd=limit),
            cancelled=ctx.cancelled,
        )
        try:
            budget.check(SpendEstimate(calls=1, total_tokens=tokens, estimated_usd=usd))
        except SpendLimitExceeded as exc:
            raise _spend_paused(reason, {**details, "estimate_usd": round(usd, 4), "spend_check": str(exc)}) from exc
    # Every request of the rest of this attempt, whatever route it really
    # takes (a subscription route is never limited; a metered fallback is).
    gate = _request_gate(config, limit, _request_output_ceiling(config, str(ctx.job.get("job_type") or "")),
                         cancelled=ctx.cancelled)
    ctx.hold(_requests_admitted(gate, reason, details))


def _request_output_ceiling(config, job_type: str) -> int:
    """The output a request is reserved for when it names no ceiling of its
    own (append reconciliation, epigraphs): the configured per-operation
    output budget the pipeline holds its results to."""

    budgets = config.ingest.budgets
    if job_type == "inventory":
        return int(budgets.inventory_output_tokens)
    return max(int(budgets.synthesis_output_tokens), int(budgets.synthesis_shard_output_tokens),
               int(budgets.append_output_tokens))


def _request_gate(config, limit_usd: float, default_output_tokens: int, *, cancelled=None):
    from learnloop.ai.spend import MeteredRequestGate, is_subscription_transport

    return MeteredRequestGate(
        cancelled=cancelled,
        limit_usd=limit_usd,
        price_per_token=lambda provider: _price_per_million(config, provider) / 1_000_000,
        is_subscription=lambda client: (
            is_subscription_transport(client=client)
            or is_subscription_route(config, getattr(client, "provider_name", None))
        ),
        default_output_tokens=max(int(default_output_tokens), 0),
    )


def _spend_paused(reason: str, details: Mapping[str, Any]):
    from learnloop.content.pipeline.runner import IngestRunnerError

    return IngestRunnerError(
        "Paused: this would spend more than allowed." if reason == "authorization"
        else "Paused: today's AI budget is used.",
        code="spend_paused",
        retryable=True,
        details=dict(details),
    )


@contextmanager
def _requests_admitted(gate, reason: str, details: Mapping[str, Any]):
    """Hold ``gate`` over every model request of the attempt; a request it
    refused stops the job as ``spend_paused`` (whatever the pipeline made of
    the refusal on its way out)."""

    from learnloop.ai.execution import gate_model_requests
    from learnloop.content.pipeline.runner import IngestRunnerError, JobCancelled, WaitingForInput
    from learnloop.db.scopes import JobOwnershipLost

    try:
        with gate_model_requests(gate):
            yield gate
    except (JobCancelled, JobOwnershipLost, WaitingForInput):
        raise
    except Exception as exc:
        if gate.refusal is None or (isinstance(exc, IngestRunnerError) and exc.code == "spend_paused"):
            raise
        # What the job reported on its way out is kept (a preserved
        # candidate, for Retry's zero-model repair first).
        earlier = dict(exc.details) if isinstance(exc, IngestRunnerError) else {}
        raise _spend_paused(reason, {**earlier, **details, "request": dict(gate.refusal),
                                     "spent_by_job_usd": round(gate.spent_usd, 4)}) from exc


def _cancel_rest_of_batch(ctx) -> None:
    """Stop the automatic build this job belongs to: the batch is flagged and
    its jobs still waiting go straight to cancelled (as a batch cancel does);
    the runner finishes this job as cancelled."""

    repo = ctx.repo
    batch_id = str(ctx.job["batch_id"])
    repo.request_ingest_batch_cancel(batch_id)
    for job in repo.ingest_jobs_for_batch(batch_id):
        if job["id"] != ctx.job_id and job["status"] in {"queued", "blocked", "waiting_for_input"}:
            repo.transition_unleased_ingest_job(
                job["id"], status="cancelled", phase="cancelled", message="Batch cancelled",
                error={"code": "cancelled", "message": "The batch was cancelled."}, clock=ctx.clock,
            )


def auto_apply_allowed(ctx) -> bool:
    """Read immediately before an automatic build applies (F4, F5): the kill
    switches, the Undo generation and the book's privacy, as they are now. A
    ``False`` keeps the build's result as an unapplied record."""

    from learnloop.vault.loader import load_vault

    auto = ctx.payload.get("auto_build")
    if not isinstance(auto, Mapping):
        return True
    config = load_vault(ctx.vault_root).config
    source_id = str(auto.get("source_id") or "")
    return (
        bool(config.ingest.auto_build)
        and bool(config.ingest.auto_apply_passing_builds)
        and int(ctx.repo.source_auto_build_state(source_id)["generation"]) == int(auto.get("generation") or 0)
        and not ctx.repo.source_kept_local(source_id)
    )


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


def child_batch_id(planner_job_id: str) -> str:
    """The build batch a planning job queues: derived from the planner, so a
    planner that dies after queuing it finds it again (review F3) and status,
    coverage and Undo find it even when the planner never saved its result."""

    return f"{AUTO_BUILD_BATCH_PREFIX}{planner_job_id}"


def _job_source_id(job: Mapping[str, Any]) -> str | None:
    payload = job.get("payload") or {}
    result = job.get("result") or {}
    return payload.get("source_id") or result.get("source_id")


def auto_jobs(repo, source_id: str) -> list[dict[str, Any]]:
    """This source's planning jobs, newest first: the whole history, filtered
    by source in SQL before anything is limited (review F10)."""

    return repo.ingest_jobs_for_source((AUTO_STUDY_MAP_JOB,), source_id)


def import_jobs(repo, source_id: str) -> list[dict[str, Any]]:
    return repo.ingest_jobs_for_source(("import",), source_id)


def _child_auto_info(repo, batch_id: str) -> dict[str, Any] | None:
    """The plan an automatic build batch carries on its synthesis job."""

    for job in repo.ingest_jobs_for_batch(batch_id):
        auto = (job.get("payload") or {}).get("auto_build")
        if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"} and isinstance(auto, Mapping):
            return dict(auto)
    return None


def _outcome_from_child(repo, batch_id: str) -> dict[str, Any] | None:
    auto = _child_auto_info(repo, batch_id)
    if auto is None:
        return None
    outcome = {key: value for key, value in auto.items() if key not in {"job_tokens", "planner_job_id"}}
    outcome.update(outcome="building", build_batch_id=batch_id, recovered=True)
    return outcome


def planner_outcome(repo, job: Mapping[str, Any]) -> dict[str, Any] | None:
    """What a planning job decided: its saved result, or (when it died after
    queuing its build) the plan its build batch carries."""

    result = job.get("result") or {}
    if job.get("status") == "completed" and result:
        return dict(result)
    child = child_batch_id(str(job["id"]))
    if repo.get_ingest_batch(child) is not None:
        return _outcome_from_child(repo, child)
    return None


def latest_auto_outcome(repo, source_id: str) -> dict[str, Any] | None:
    for job in auto_jobs(repo, source_id):
        outcome = planner_outcome(repo, job)
        if outcome is not None:
            return outcome
    return None


def current_generation(repo, source_id: str) -> int:
    return int(repo.source_auto_build_state(source_id)["generation"])


def _build_state(repo, outcome: Mapping[str, Any], *, generation: int | None = None) -> dict[str, Any]:
    """What became of a ``building`` outcome's batch: its status, proposal,
    whether it applied, was taken back out, or left changes to look at."""

    batch_id = outcome.get("build_batch_id")
    batch = repo.get_ingest_batch(batch_id) if batch_id else None
    state: dict[str, Any] = {"batch": batch, "status": (batch or {}).get("status"), "proposal_id": None,
                             "applied": False, "undone": False, "pending": 0, "error": None,
                             "error_code": None, "error_details": {}}
    source_id = outcome.get("source_id")
    if generation is None and source_id:
        generation = current_generation(repo, str(source_id))
    if generation is not None and int(outcome.get("generation") or 0) < generation:
        # Planned before the learner's Undo: never applies, never counts.
        state["undone"] = True
    if batch is None:
        return state
    for job in repo.ingest_jobs_for_batch(batch_id):
        error = job.get("error") or {}
        if error and job["status"] in {"failed", "blocked", "cancelled"} and state["error"] is None:
            state["error"] = error.get("message")
            state["error_code"] = error.get("code")
            state["error_details"] = dict(error.get("details") or {})
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


@dataclass
class Coverage:
    """Which chapters of a book automatic builds cover (review F6).

    ``built``: a build finished (applied, or waiting for a look); ``reserved``:
    planned or building now; ``failed``: the last build for it failed or was
    stopped and nothing later covers it. Undone builds count for nothing."""

    built: set[str] = field(default_factory=set)
    reserved: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)

    @property
    def covered(self) -> set[str]:
        """What a new build must not plan again."""

        return self.built | self.reserved


def coverage(repo, source_id: str, *, exclude_job_id: str | None = None) -> Coverage:
    generation = current_generation(repo, source_id)
    result = Coverage()
    for job in auto_jobs(repo, source_id):
        if job["id"] == exclude_job_id:
            continue
        outcome = planner_outcome(repo, job)
        if outcome is None:
            if _active(job):
                # A planner still to run reserves the chapters it was asked for.
                result.reserved.update((job.get("payload") or {}).get("chapter_ids") or [])
            continue
        if outcome.get("outcome") != "building":
            continue
        state = _build_state(repo, outcome, generation=generation)
        if state["undone"]:
            continue
        chapters = set(outcome.get("chapter_ids") or [])
        if state["batch"] is None or state["status"] in {"failed", "blocked", "cancelled"}:
            result.failed.update(chapters)
        elif _active(state["batch"]):
            result.reserved.update(chapters)
        else:
            result.built.update(chapters)
    result.failed -= result.covered
    return result


def built_unit_ids(repo, source_id: str) -> set[str]:
    """Chapters an automatic build covers or is building, and not undone.
    Failed and stopped builds do not count (review F6)."""

    return coverage(repo, source_id).covered


def _active(job_or_batch: Mapping[str, Any] | None) -> bool:
    return bool(job_or_batch) and job_or_batch.get("status") in {"queued", "running", "waiting_for_input"}


def _source_work_active(repo, source_id: str, *, ignore_batch_id: str | None = None) -> bool:
    for job in auto_jobs(repo, source_id):
        if job["batch_id"] != ignore_batch_id and _active(job):
            return True
        outcome = planner_outcome(repo, job)
        if outcome and outcome.get("outcome") == "building":
            batch_id = outcome.get("build_batch_id")
            if batch_id and batch_id != ignore_batch_id and _active(repo.get_ingest_batch(batch_id)):
                return True
    return False


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


@dataclass
class BuildPlanChoice:
    """What a build would cover, and its plan totals (no writes, no calls)."""

    extraction_id: str
    revision_id: str
    chapters: list[Chapter]
    whole: bool
    unit_ids: list[str]
    stages: dict[str, int]
    totals: dict[str, Any]
    outline: Any

    @property
    def info(self) -> dict[str, Any]:
        return {"chapters": [chapter.label for chapter in self.chapters],
                "chapter_ids": [chapter.unit_id for chapter in self.chapters],
                "whole_source": self.whole}


def _choose_scope(repo, config, vault, source_id: str, resolved: tuple[str, str], *,
                  chapter_ids: Sequence[str] | None, start_unit_id: str | None,
                  exclude_job_id: str | None) -> BuildPlanChoice | None:
    from learnloop.content.pipeline.build_plan import build_build_plan
    from learnloop.content.sources.source_outline import build_source_outline

    revision_id, extraction_id = resolved
    outline = build_source_outline(repo, extraction_id)
    chapters = outline_chapters(outline)
    covered = coverage(repo, source_id, exclude_job_id=exclude_job_id).covered
    whole = False
    if chapter_ids:
        wanted = set(chapter_ids)
        picked = [
            chapter for chapter in chapters
            if chapter.unit_id in wanted and chapter.unit_id not in covered and not _is_front_matter(chapter)
        ]
    else:
        cap = int(config.ingest.budgets.quick_add_scope_input_tokens)
        if not covered and outline.approx_tokens <= cap:
            picked, whole = list(chapters), True
        else:
            picked = reading_order_scope(
                chapters, built=covered, start_unit_id=start_unit_id,
                cap_tokens=cap, floor_tokens=min(FLOOR_TOKENS, max(cap // 4, 1)),
            )
    if not picked:
        return None
    unit_ids = [unit_id for chapter in picked for unit_id in chapter.unit_ids]
    plan = build_build_plan(
        repo, config, vault, subject_id=None,
        selections=[{"extraction_id": extraction_id, "selected_unit_ids": unit_ids}],
    ).as_dict()
    stages = {str(stage.get("stage")): int(stage.get("input_tokens") or 0) + int(stage.get("max_output_tokens") or 0)
              for stage in plan.get("stages") or []}
    return BuildPlanChoice(
        extraction_id=extraction_id, revision_id=revision_id, chapters=picked, whole=whole,
        unit_ids=unit_ids, stages=stages, totals=dict(plan["totals"]), outline=outline,
    )


def preview_auto_build(vault_root: Path, repo, source_id: str, *, whole_book: bool = False,
                       chapter_ids: Sequence[str] | None = None, approved: bool = False,
                       route: AuthoringRoute | None = None, now: datetime | None = None) -> dict[str, Any]:
    """The zero-call dry run of an automatic build (review F2): what it would
    cover, the route, tokens, money and whether it would ask first or stop.
    Writes nothing and calls no model."""

    from learnloop.clock import SystemClock
    from learnloop.vault.loader import load_vault

    vault = load_vault(vault_root)
    config = vault.config
    report: dict[str, Any] = {"source_id": source_id, "model_calls": 0, "writes": 0}
    artifact = repo.get_source_artifact(source_id)
    if artifact is None:
        return {**report, "status": "unknown_source"}
    if repo.source_kept_local(source_id):
        return {**report, "status": "kept_local"}
    if not config.ingest.auto_build:
        return {**report, "status": "auto_build_off"}
    resolved = _completed_extraction(repo, source_id)
    if resolved is None:
        return {**report, "status": "not_ready"}
    if whole_book and not chapter_ids:
        from learnloop.content.sources.source_outline import build_source_outline

        chapter_ids = [chapter.unit_id for chapter in outline_chapters(build_source_outline(repo, resolved[1]))]
    choice = _choose_scope(repo, config, vault, source_id, resolved, chapter_ids=chapter_ids,
                           start_unit_id=None, exclude_job_id=None)
    if choice is None:
        return {**report, "status": "nothing_to_build"}
    route = route or authoring_route_for(vault.root, config)
    cost = decide_cost(config, repo, route.provider, choice.totals, approved=approved,
                       now=now or SystemClock().now())
    status = "would_build"
    if not route.ready:
        status = "needs_ai"
    elif route.consent_key not in config.ai.consent:
        status = "needs_ok"
    elif cost.pause == "budget_used":
        status = "would_stop_budget_used"
    elif cost.pause is not None:
        status = "would_ask_first"
    return {
        **report,
        "status": status,
        "provider": route.provider,
        "route_ready": route.ready,
        **choice.info,
        "unit_count": len(choice.unit_ids),
        "stages": choice.stages,
        "totals": choice.totals,
        **cost.as_dict(),
        "threshold_usd": float(config.ingest.cost_pause.threshold_usd),
        "daily_cap_usd": config.ingest.cost_pause.daily_cap_usd,
        "applies": bool(config.ingest.auto_apply_passing_builds),
    }


def run_auto_study_map(ctx) -> dict[str, Any]:
    """Plan (and queue) the automatic question build for one source."""

    from learnloop.content.pipeline.quick_add import _default_brief
    from learnloop.content.pipeline.runner import IngestRunnerError, JobSpec
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set
    from learnloop.vault_lock import vault_mutation_lock

    payload = ctx.payload
    # An earlier attempt of this job may have queued its build and died before
    # saving its result (review F3): that build is the answer.
    recovered = _outcome_from_child(ctx.repo, child_batch_id(ctx.job_id))
    if recovered is not None:
        return recovered
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
    # The book's own privacy choice, persisted (review F1): every later build
    # reads it, not only the Add that set it. The Add's own request was
    # persisted before this planner could run (by Add for a file, by the
    # import for a link), so the book's current choice decides (re-review F13).
    if artifact.get("keep_local"):
        return {"outcome": "waiting", "reason": "kept_local", **base}
    resolved = _completed_extraction(ctx.repo, source_id)
    if resolved is None:
        raise IngestRunnerError("This source has no text yet.", code="not_extracted", retryable=True)
    revision_id, extraction_id = resolved
    generation = current_generation(ctx.repo, source_id)

    ctx.report("inventoried", message="Choosing what to build first")
    choice = _choose_scope(
        ctx.repo, config, vault, source_id, resolved,
        chapter_ids=payload.get("chapter_ids"), start_unit_id=payload.get("start_unit_id"),
        exclude_job_id=ctx.job_id,
    )
    if choice is None:
        return {"outcome": "skipped", "reason": "nothing_to_build", **base}
    plan_info = choice.info
    unit_ids = choice.unit_ids

    route = ctx.services.authoring_route(ctx)
    if not route.ready:
        return {"outcome": "waiting", "reason": "no_ai", "provider": route.provider,
                "message": route.message, **plan_info, **base}
    if route.consent_key not in config.ai.consent:
        return {"outcome": "waiting", "reason": "needs_consent", "provider": route.provider,
                "consent_key": route.consent_key, **plan_info, **base}

    cost = decide_cost(config, ctx.repo, route.provider, choice.totals,
                       approved=bool(payload.get("approved")), now=ctx.clock.now())
    if cost.pause is not None:
        return {"outcome": "paused", "reason": "cost", "cost_reason": cost.pause,
                "provider": route.provider, **cost.as_dict(), **plan_info, **base}

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
        order = {unit.unit_id: index for index, unit in enumerate(choice.outline.units)}
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
    outcome = {
        "outcome": "building",
        "subject_id": subject_id,
        "subject_created": created,
        "source_set_id": source_set_id,
        "unit_ids": unit_ids,
        "provider": route.provider,
        "applies": apply,
        "generation": generation,
        **cost.as_dict(),
        **plan_info,
        **base,
    }
    # The plan travels with the build (same enqueue transaction), so the build
    # is never orphaned from its book: status, coverage and Undo read it there.
    auto = {key: value for key, value in outcome.items() if key not in {"outcome", "applies"}}
    auto["planner_job_id"] = ctx.job_id
    synthesis_tokens = sum(tokens for stage, tokens in choice.stages.items() if stage != "inventory")
    build_batch_id = ctx.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"extraction_id": extraction_id,
                                  "units": [{"unit_id": unit_id, "role": role} for unit_id in unit_ids],
                                  "auto_build": {**auto, "job_tokens": choice.stages.get("inventory", 0)}}),
            JobSpec(
                "bootstrap_synthesis",
                {"source_set_id": source_set_id, "brief": brief, "mode": "auto", "apply": apply,
                 "auto_build_source_id": source_id,
                 "auto_build": {**auto, "job_tokens": synthesis_tokens}},
                depends_on=(0,),
            ),
        ],
        subject_id=subject_id,
        source_set_id=source_set_id,
        priority=BUILD_PRIORITY,
        batch_id=child_batch_id(ctx.job_id),
    )
    return {**outcome, "build_batch_id": build_batch_id}


def after_auto_build(ctx) -> None:
    """An automatic build's synthesis finished: act on reading progress that
    arrived while it ran (review F7). Best effort."""

    auto = ctx.payload.get("auto_build")
    if not isinstance(auto, Mapping) or not auto.get("source_id"):
        return
    try:
        from learnloop.content.pipeline.runner import JobSpec

        source_id = str(auto["source_id"])
        request = ctx.repo.pending_reading_request(source_id)
        if request is None:
            return
        wanted = _wanted_chapters(ctx.repo, ctx.vault_root, source_id, request)
        if wanted:
            ctx.enqueue_batch(
                AUTO_BUILD_WORKFLOW,
                [JobSpec(AUTO_STUDY_MAP_JOB, {"source_id": source_id, "chapter_ids": wanted})],
                priority=BUILD_PRIORITY,
            )
        # Exactly the request acted on (F9): a newer one recorded meanwhile stays.
        ctx.repo.settle_reading_request(source_id, request["revision"])
    except Exception:  # noqa: BLE001 - a follow-up must never fail the build that applied
        import logging

        logging.getLogger(__name__).warning("could not act on reading progress after a build", exc_info=True)


# ---------------------------------------------------------------------------
# Follow-ups the shell and the Reader ask for
# ---------------------------------------------------------------------------


def request_auto_build(ingest_jobs, source_id: str, *, approved: bool = False,
                       chapter_ids: Sequence[str] | None = None, start_unit_id: str | None = None) -> str:
    """Plan another automatic build for ``source_id`` (connect, build now,
    keep ahead). ``approved`` is the learner's explicit "Build them": it passes
    the confirmation threshold once, for the chapters the pause named (never
    the daily cap)."""

    if approved and chapter_ids is None:
        repo = ingest_jobs.repository
        outcome = latest_auto_outcome(repo, source_id) or {}
        if outcome.get("outcome") == "paused":
            chapter_ids = outcome.get("chapter_ids")
        elif outcome.get("outcome") == "building":
            state = _build_state(repo, outcome)
            if state["error_code"] == "spend_paused":
                chapter_ids = outcome.get("chapter_ids")
    return ingest_jobs.enqueue_auto_build(
        source_id, approved=approved, chapter_ids=chapter_ids, start_unit_id=start_unit_id,
    )


def release_waiting_builds(ingest_jobs) -> list[str]:
    """After an AI is connected: plan again for every book waiting on it, and
    act on reading progress that waited (complete history, review F10)."""

    repo = ingest_jobs.repository
    released: list[str] = []
    for job in repo.latest_ingest_job_per_source(AUTO_STUDY_MAP_JOB):
        source_id = _job_source_id(job)
        if not source_id or _active(job):
            continue
        result = job.get("result") or {}
        if job["status"] == "completed" and result.get("outcome") == "waiting" and result.get("reason") in {"no_ai", "needs_consent"}:
            request_auto_build(ingest_jobs, source_id)
            released.append(source_id)
    reconcile_reading_builds(ingest_jobs, skip=set(released))
    return released


def _keep_ahead_ready(repo, vault_root: Path, source_id: str) -> bool:
    """Whether a book's questions may grow with reading now: it has an
    automatic build that was not undone, auto-build is on and nothing for it
    is running."""

    from learnloop.config.loader import load_config

    if repo.source_kept_local(source_id):
        return False
    # The config alone (review F1): this runs on the Reader's progress path,
    # and parsing the whole vault there stalled the serial sidecar.
    if not load_config(Path(vault_root) / "learnloop.toml").ingest.auto_build:
        return False
    generation = current_generation(repo, source_id)
    for job in auto_jobs(repo, source_id):
        outcome = planner_outcome(repo, job)
        if outcome and outcome.get("outcome") == "building":
            return not _build_state(repo, outcome, generation=generation)["undone"]
    return False


def _wanted_chapters(repo, vault_root: Path, source_id: str, state: Mapping[str, Any]) -> list[str]:
    """The chapters a pending reading request asks for (none: nothing to do)."""

    if not _keep_ahead_ready(repo, vault_root, source_id):
        return []
    extraction_id = str(state.get("extraction_id") or "")
    section_id = str(state.get("section_id") or "")
    if not extraction_id or not section_id or repo.get_extraction_run(extraction_id) is None:
        return []
    chapters = outline_chapters(_unit_tree(repo, extraction_id))
    cover = coverage(repo, source_id)
    # Failed chapters wait for the card's Retry instead of looping here.
    return [chapter.unit_id for chapter in chapters_to_keep_ahead(chapters, section_id, cover.covered | cover.failed)]


def reconcile_reading_builds(ingest_jobs, *, skip: Iterable[str] = ()) -> list[str]:
    """Act on every book's pending reading request: at startup, on reconnection
    (review F7). A request that fails here is not only logged (finishing pass,
    F8): it is marked failed with a fresh set of worker retries, so the worker
    retries it and the Reader's next report asks again. Returns the books whose
    build was queued."""

    repo = ingest_jobs.repository
    skipped = set(skip)
    started: list[str] = []
    for state in repo.sources_with_wanted_reading():
        source_id = str(state["source_id"])
        if source_id in skipped:
            continue  # a build was just asked for; the worker acts after it
        try:
            outcome = act_on_reading_request(ingest_jobs, source_id, rearm=True)
        except Exception:  # noqa: BLE001 - one book's failure is kept for its retries
            import logging

            logging.getLogger(__name__).warning("could not act on a book's pending reading position", exc_info=True)
            continue
        if outcome and outcome.get("batch_id"):
            started.append(source_id)
    return started


def plan_reading_advance(ingest_jobs, source_id: str, extraction_id: str, section_id: str) -> dict[str, Any] | None:
    """Keep one chapter ahead of ``section_id`` (Q6), or say why not now.

    ``None``: nothing to do (not a book whose questions grow with reading, or
    the next chapter is already covered). ``{"deferred": True}``: the book's
    work is running; the request waits for it. Otherwise the build is queued.
    It keeps no state of its own: the caller settles the request it acted on.

    It runs on the Reader's progress RPC, so it stays cheap (round-2 review
    F1): the chapter list comes from the unit tree, never the full outline
    (which loads the book's text once per unit), the switch from the config,
    never the whole vault, and the build itself is only queued; its planning
    runs on the ingest worker."""

    repo = ingest_jobs.repository
    if not _keep_ahead_ready(repo, ingest_jobs.vault_root, source_id):
        return None
    if _source_work_active(repo, source_id):
        return {"deferred": True, "source_id": source_id, "section_id": section_id}
    if repo.get_extraction_run(extraction_id) is None:
        return None
    chapters = outline_chapters(_unit_tree(repo, extraction_id))
    cover = coverage(repo, source_id)
    wanted = chapters_to_keep_ahead(chapters, section_id, cover.covered | cover.failed)
    if not wanted:
        return None
    batch_id = request_auto_build(ingest_jobs, source_id, chapter_ids=[chapter.unit_id for chapter in wanted])
    return {"batch_id": batch_id, "source_id": source_id, "chapters": [chapter.label for chapter in wanted]}


def act_on_reading_request(ingest_jobs, source_id: str, *, rearm: bool = False) -> dict[str, Any] | None:
    """Act on the book's pending reading request, exactly its current revision
    (finishing pass, F8 and F9). Raises when acting fails, after recording it.

    One lock serialises the acting (the Reader's RPC, the worker's retries and
    the start), so a request is never acted on twice at once. Recording a newer
    request does not wait for the lock: it advances the revision, so settling
    the older one cannot erase it, and the newer one is acted on next.

    * queued, or nothing to do: the request is settled;
    * deferred (the book's work is running): it stays, due, for the worker to
      act on once that work ends;
    * failed: its attempts are counted and the worker's next retry is set
      (``rearm`` starts a fresh set, as the start does); the Reader's next
      report asks again meanwhile."""

    repo = ingest_jobs.repository
    with ingest_jobs.reading_lock:
        request = repo.pending_reading_request(source_id)
        if request is None:
            return None
        try:
            outcome = plan_reading_advance(ingest_jobs, source_id, request["extraction_id"], request["section_id"])
        except Exception:
            attempts = 1 if rearm else request["attempts"] + 1
            _note_reading_failure(ingest_jobs, source_id, request["revision"], attempts)
            raise
        if not (outcome or {}).get("deferred"):
            repo.settle_reading_request(source_id, request["revision"])
        return outcome


def _note_reading_failure(ingest_jobs, source_id: str, revision: int, attempts: int) -> None:
    """Best effort: count a failed attempt and wake the worker for its retry
    (timed from now, by the wall clock). If even that write fails, the request
    stays due and the worker acts on it."""

    from datetime import timedelta

    delays = ingest_jobs.READING_RETRY_DELAYS
    retry_at = None
    if attempts <= len(delays):
        moment = datetime.now(UTC)
        retry_at = utc_now_iso(FrozenClock(moment + timedelta(seconds=delays[attempts - 1])))
    try:
        ingest_jobs.repository.fail_reading_request(source_id, revision, attempts=attempts, retry_at=retry_at)
    except Exception:  # noqa: BLE001 - the request itself is durable already
        import logging

        logging.getLogger(__name__).warning("could not record a failed reading request", exc_info=True)
    ingest_jobs.wake_reading_retries()


def _extraction_source(repo, extraction_id: str) -> str | None:
    run = repo.get_extraction_run(extraction_id)
    revision = repo.get_source_revision(run["revision_id"]) if run else None
    source_id = (revision or {}).get("source_id")
    return str(source_id) if source_id else None


def advance_reading_build(ingest_jobs, extraction_id: str, section_id: str) -> dict[str, Any] | None:
    """The Reader reached ``section_id``: keep one chapter ahead (Q6).

    Only for sources added through Add whose questions were built and not
    undone. The position becomes the book's reading request (the newest wins)
    and is acted on now; while a build for the book is running it waits for
    that work to finish (review F7). Raises when acting fails; the request is
    kept and retried (see :func:`act_on_reading_request`)."""

    repo = ingest_jobs.repository
    source_id = _extraction_source(repo, extraction_id)
    if not source_id:
        return None
    repo.record_reading_request(source_id, extraction_id, section_id)
    return act_on_reading_request(ingest_jobs, source_id)


def keep_ahead_for_reader(ingest_jobs, extraction_id: str, section_id: str) -> dict[str, Any] | None:
    """The Reader's progress RPC asks to keep one chapter ahead. Never raises.

    ``reader.mark_section_progress`` recorded ``section_id`` as the book's
    reading request in the same transaction as the progress itself, so a
    saved report never loses its ask. This acts on that request now. A failure
    is kept (finishing pass, F8): the request is marked failed, the ingest
    worker retries it off the RPC path, the next start asks again, and until it
    settles the Reader's next report asks again instead of being coalesced."""

    try:
        source_id = _extraction_source(ingest_jobs.repository, extraction_id)
        if not source_id:
            return None
        return act_on_reading_request(ingest_jobs, source_id)
    except Exception:  # noqa: BLE001 - planning never fails the Reader
        import logging

        logging.getLogger(__name__).warning(
            "failed to keep questions a chapter ahead of %s; retrying", section_id, exc_info=True
        )
        try:
            ingest_jobs.wake_reading_retries()
        except Exception:  # noqa: BLE001
            pass
        return None


def _record_undo_judgment(repo, source_id: str, proposal_id: str, item_ids: Sequence[str],
                          generation: int, *, clock: Clock | None = None) -> str | None:
    """The learner's Undo is an owner verdict on automatically applied content
    (review F12): one ``judgment_ledger`` row per proposal, idempotent."""

    import json
    import sqlite3
    import uuid

    from learnloop.db.stores.judgments import append_judgment
    from learnloop.ai.execution import content_key

    items = sorted(str(item_id) for item_id in item_ids)
    input_hash = content_key({"proposal_id": proposal_id, "item_ids": items, "source_id": source_id})
    judgment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"learnloop:auto_apply_undo:{input_hash}"))
    try:
        with repo.connection() as connection:
            if connection.execute("SELECT 1 FROM judgment_ledger WHERE id = ?", (judgment_id,)).fetchone():
                return judgment_id
            append_judgment(
                connection, id=judgment_id, task=UNDO_JUDGMENT_TASK,
                left_kind="proposal", left_id=proposal_id,
                right_kind="source", right_id=source_id,
                judge="owner", input_hash=input_hash, verdict="rejected",
                rationale=json.dumps({"action": "undo_questions", "source_id": source_id,
                                      "proposal_id": proposal_id, "item_ids": items,
                                      "generation": generation}, sort_keys=True),
                created_at=utc_now_iso(clock),
            )
            connection.commit()
    except sqlite3.Error:
        import logging

        logging.getLogger(__name__).warning("could not record the undo verdict", exc_info=True)
        return None
    return judgment_id


def undo_source_questions(ingest_jobs, source_id: str, *, clock: Clock | None = None) -> int:
    """Take a book's automatic questions back out (one-tap undo, Q3).

    First a new generation is recorded (review F5): a build already running
    can no longer apply, queued work for the book is cancelled, and reading
    stops growing the book's questions until the learner builds them again.
    Then every applied proposal of the book is reverted, and the verdict is
    recorded in ``judgment_ledger`` (review F12)."""

    from learnloop.content.proposals.proposals import reject_items

    repo = ingest_jobs.repository
    generation = repo.advance_source_auto_build_generation(source_id, clock=clock)
    for job in auto_jobs(repo, source_id):
        if _active(job):
            planner_batch = repo.get_ingest_batch(job["batch_id"]) or {}
            if planner_batch.get("workflow_type") == AUTO_BUILD_WORKFLOW:
                ingest_jobs.cancel_batch(job["batch_id"])
            else:
                # The planner only: an Add's batch also holds the book's import.
                repo.set_ingest_job_cancel_requested(job["id"])
        outcome = planner_outcome(repo, job)
        batch_id = (outcome or {}).get("build_batch_id")
        if batch_id and _active(repo.get_ingest_batch(batch_id)):
            # Waiting jobs are cancelled now; a running one stops at its next
            # checkpoint and, either way, can no longer apply (generation).
            ingest_jobs.cancel_batch(batch_id)
    reverted = 0
    for job in auto_jobs(repo, source_id):
        outcome = planner_outcome(repo, job)
        if not outcome or outcome.get("outcome") != "building":
            continue
        state = _build_state(repo, outcome, generation=-1)
        if not state["proposal_id"]:
            continue
        item_ids = [
            item["id"] for item in repo.proposal_items(state["proposal_id"])
            if _revertable(item) and item.get("decision") in {"accepted", "pending"}
        ]
        if item_ids:
            reverted += reject_items(ingest_jobs.vault_root, state["proposal_id"], item_ids)
            _record_undo_judgment(repo, source_id, state["proposal_id"], item_ids, generation, clock=clock)
    return reverted


def keep_on_this_computer(ingest_jobs, source_id: str, *, clock: Clock | None = None) -> None:
    """Keep a book on this computer from now on (book details, or an Add of a
    book already here with the option).

    The choice is persisted first, and every outbound boundary reads it when
    its work runs (re-review F1). Work already queued to send the book out is
    stopped now too: its queued Reader requests are cancelled (a running one
    is flagged), and its automatic builds are cancelled (the card then says
    the book is kept on this computer). A planner still to run costs nothing
    and records "kept on this computer" itself. A request or model call
    already under way is not recalled; nothing new starts."""

    repo = ingest_jobs.repository
    repo.set_source_keep_local(source_id, True, clock=clock)
    for request in repo.reader_requests_for_source(source_id):
        if request["status"] in {"queued", "running"}:
            repo.cancel_reader_request(request["id"], clock=clock)
    for job in auto_jobs(repo, source_id):
        batch_id = (planner_outcome(repo, job) or {}).get("build_batch_id")
        if batch_id and _active(repo.get_ingest_batch(batch_id)):
            ingest_jobs.cancel_batch(batch_id)


def share_with_ai(ingest_jobs, source_id: str, *, clock: Clock | None = None) -> str | None:
    """"Let LearnLoop write questions for it" (book details): the book is no
    longer kept on this computer, and the persisted choice decides from now on.

    A readable book plans a build. A book that never became readable (a
    recording kept local stops before transcription, re-review F13) has its
    Add brought up to date: the stale ``keep_local`` is removed from the
    Add's jobs, the import asks for the separate whole-file OK before any
    upload (§6.6), and the Add is resumed. Returns the batch started or
    resumed, if any."""

    repo = ingest_jobs.repository
    repo.set_source_keep_local(source_id, False, clock=clock)
    if _completed_extraction(repo, source_id) is not None:
        return request_auto_build(ingest_jobs, source_id)
    batch_id = latest_add_batch(repo, source_id)
    if batch_id is None:
        return None
    for job in repo.ingest_jobs_for_batch(batch_id):
        payload = dict(job.get("payload") or {})
        if not (payload.get("keep_local") or payload.get("keep_local_applied")):
            continue
        payload.pop("keep_local", None)
        payload.pop("keep_local_applied", None)
        if job["job_type"] == "import":
            payload["require_upload_ok"] = True
        repo.update_ingest_job_payload(job["id"], payload)
    ingest_jobs.resume_batch(batch_id)
    return batch_id


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


_SCAN_DETAILS = (
    "Reading the words of a scan needs text recognition, which isn't installed on this computer. "
    + TEXT_RECOGNITION_HOW_TO
    + " The pages still show in the Reader meanwhile."
)


def _is_scan_failure(lowered: str) -> bool:
    """An import that found no text layer at all: a scanned PDF."""

    return "no extractable text" in lowered or "likely scanned" in lowered


def _import_failure_line(job: Mapping[str, Any], category: str | None, *, keep_local: bool = False) -> dict[str, Any]:
    error = job.get("error") or {}
    message = str(error.get("message") or "")
    code = str(error.get("code") or "")
    flow = str((error.get("details") or {}).get("flow") or "")
    lowered = f"{code} {message}".lower()
    retry = ("retry", "Try again")
    if code == "needs_upload_ok":
        if flow == "audio_transcription" or category == "audio":
            return _line("Transcribing this recording sends it to an online service", "quiet",
                         ("allow_upload", "OK"), message or None)
        return _line("Reading this PDF sends the whole file to your AI", "quiet",
                     ("allow_upload", "OK"), message or None)
    if code == "kept_local":
        return _line(f"Kept on this computer — this {kind_noun(category)} can't be read here", "quiet",
                     None, message or None)
    if code == "pdf_extractor_unavailable":
        return _line("Text recognition isn't set up", "problem", ("open_settings", "Set it up"), message or None)
    if category == "youtube" and ("caption" in lowered or "transcript" in lowered):
        return _line("This video has no captions", "problem", retry, message or None)
    if _is_scan_failure(lowered):
        # A scan reads the same way on every try (usability round 1, U7): the
        # one action that can help, or one plain line when nothing can.
        if text_recognition_available(keep_local=keep_local):
            return _line("This PDF is a scan", "quiet", ("text_recognition", "Read it with text recognition"),
                         message or None)
        # The extractor's own words ("install marker-pdf for OCR support") are
        # not for the learner: the details say how to get it (usability round 2).
        return _line("This PDF is a scan — LearnLoop can show its pages but can't read them yet", "quiet",
                     None, _SCAN_DETAILS)
    if category in {"web", "arxiv", "youtube"} or any(
        marker in lowered for marker in ("http", "fetch", "connection", "timed out", "timeout", "network", "unreachable")
    ):
        return _line("Couldn't reach the page", "problem", retry, message or None)
    if category == "pdf":
        return _line("Couldn't read this PDF", "problem", retry, message or None)
    return _line(f"Couldn't get this {kind_noun(category)} ready", "problem", retry, message or None)


def text_recognition_available(*, keep_local: bool = False) -> bool:
    """Whether an extractor that really recognises text is installed (review
    F9): local Marker, or (not for a book kept on this computer) the hosted
    Marker runtime the owner configured."""

    import os

    from learnloop.ingest.extractors import datalab_api_key, marker_available

    if marker_available():
        return True
    if keep_local:
        return False
    return os.environ.get("LEARNLOOP_MARKER_PROVIDER", "").strip().lower() == "datalab" and bool(datalab_api_key())


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
        if text_recognition_available(keep_local=repo.source_kept_local(source_id)):
            return _line("Some pages look scanned", "quiet", ("text_recognition", "Read them with text recognition"))
        # Settings can't install it (usability round 1, U7): say so, no dead end.
        return _line("Some pages look scanned — their words can't be read here yet", "quiet", None, _SCAN_DETAILS)
    if "marker_failed_pypdf_fallback" in flags:
        return _line("Maths may look rough in the text view", "quiet", ("open_settings", "Fix it"),
                     "marker_failed_pypdf_fallback")
    return None


def _scope_size(outcome: Mapping[str, Any]) -> int:
    """How many sections a build covers (its units, else its chapters)."""

    return len(outcome.get("unit_ids") or outcome.get("chapter_ids") or outcome.get("chapters") or [])


def build_minutes_phrase(repo, *, section_count: int, sample: int = 5) -> str | None:
    """How long questions for ``section_count`` sections take, from this
    library's own finished automatic builds ("in about 4 min", "in under a
    minute"), or ``None`` when it has none to go on (usability round 2: "in
    about 13 min" was a made-up formula for a build that took seconds).

    The rate is per section in a build's scope, not per chapter: chapters
    differ in size (a paper's ten short sections took 48 s where two
    textbook chapters of ten sections each took about 20 s apiece)."""

    from datetime import datetime

    per_section: list[float] = []
    # Planning jobs, newest first: each names the build it queued and its scope.
    for job in repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,), limit=sample * 4):
        if len(per_section) >= sample:
            break
        if job.get("status") != "completed":
            continue
        outcome = planner_outcome(repo, job) or {}
        build_id = outcome.get("build_batch_id")
        build = repo.get_ingest_batch(str(build_id)) if build_id else None
        if not build or build.get("status") != "completed" or not build.get("started_at") or not build.get("finished_at"):
            continue
        try:
            seconds = (datetime.fromisoformat(str(build["finished_at"]).replace("Z", "+00:00"))
                       - datetime.fromisoformat(str(build["started_at"]).replace("Z", "+00:00"))).total_seconds()
        except ValueError:
            continue
        per_section.append(max(0.0, seconds) / max(1, _scope_size(outcome)))
    if not per_section:
        return None
    ordered = sorted(per_section)
    middle = ordered[len(ordered) // 2]
    minutes = middle * max(1, section_count) / 60.0
    if minutes < 1:
        return "in under a minute"
    return f"in about {round(minutes)} min"


def _budget_used_line(details: str | None = None) -> dict[str, Any]:
    return _line("Paused — today's AI budget is used", "quiet", ("open_settings", "Raise it"),
                 details or "Or wait until tomorrow.")


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
    noun = source_kind_noun(repo, source_id, category)
    has_text = _completed_extraction(repo, source_id) is not None
    if not has_text:
        imports = import_jobs(repo, source_id)
        latest_import = imports[0] if imports else None
        if latest_import is None:
            return None
        if latest_import["status"] in {"failed", "blocked", "cancelled"}:
            return _import_failure_line(latest_import, category, keep_local=bool(artifact.get("keep_local")))
        return _line(f"Getting this {noun} ready", "working")

    latest, outcome = latest_planner(repo, source_id)
    if latest is None:
        health = _health_line(repo, source_id)
        if health is not None or vault is None:
            return health
        # A book added another way (the Ingest screen) whose questions were
        # never applied: one line and the one action, never silence
        # (usability round 2: its card had no line at all). Filing it in a
        # collection builds nothing (round-2 review F6).
        if not artifact.get("reader_enabled", 1) or artifact.get("keep_local"):
            return None
        built = _study_map_questions(repo, source_id)
        if built == "applied":
            return None
        if built == "pending":
            return _line(f"Questions for this {noun} need a look", "quiet", ("open_changes", "Review"))
        return _line(f"No questions for this {noun} yet", "quiet", ("retry", "Build them"))
    if outcome is None and _active(latest):
        # The text is ready; LearnLoop is choosing what to build (§6.3 states).
        return _line("Chapters found", "working")
    if outcome is None:
        # Retry plans again; it is not the learner's "Build them" (no approval).
        error = latest.get("error") or {}
        return _line(f"Questions for this {noun} need another try", "problem", ("retry", "Retry"),
                     error.get("message"))
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
        if outcome.get("cost_reason") == "budget_used":
            return _budget_used_line()
        usd = float(outcome.get("estimate_usd") or 0.0)
        return _line(f"Building questions for {phrase} would cost about ${usd:,.2f}", "quiet",
                     ("build_now", "Build them"))
    if kind != "building":
        return None
    state = _build_state(repo, outcome)
    if state["undone"]:
        return _line(f"Questions for this {noun} were taken back out", "quiet", ("build_now", "Build them again"))
    if _active(state["batch"]):
        estimate = build_minutes_phrase(repo, section_count=_scope_size(outcome))
        if estimate is None:
            return _line(f"Writing questions for {phrase}", "working")
        return _line(f"Questions for {phrase} {estimate}", "working")
    if state["batch"] is None or state["status"] in {"failed", "blocked", "cancelled"}:
        if artifact.get("keep_local"):
            return _line("Kept on this computer — no questions are written for it", "quiet")
        if state["error_code"] == "spend_paused":
            if state["error_details"].get("reason") == "daily_cap":
                return _budget_used_line(state["error"])
            return _line(f"Questions for {phrase} would cost more than expected", "quiet",
                         ("build_now", "Build them"), state["error"])
        if state["status"] == "cancelled" and not vault.config.ingest.auto_build:
            # The owner turned automatic building off while it was queued.
            return _health_line(repo, source_id)
        return _line(f"Questions for {phrase} need another try", "problem", ("retry", "Retry"), state["error"])
    if not state["applied"]:
        return _line(f"Questions for {phrase} need a look", "quiet", ("open_changes", "Review"))
    if state["pending"]:
        count = state["pending"]
        return _line(f"{count} change{'s' if count != 1 else ''} need a look", "quiet", ("open_changes", "Review"))
    health = _health_line(repo, source_id)
    if health is not None:
        return health
    # Questions come as the learner reads (a check at each section break, then
    # practice once a section is done), so the line says where they come from;
    # Undo lives in details (usability round 1, U8: "Questions ready · Undo"
    # sent learners looking for questions and wondering what Undo would undo).
    built = _built_phrase(repo, source_id, outcome, noun) or phrase
    line = _line(f"Questions for {built} come up as you read", "quiet")
    # The shelf shows this instead while no AI can write them (usability round
    # 2: with no AI the card still promised questions as you read).
    line["without_ai"] = _line(f"Questions for {built} come up as you read once an AI is connected", "quiet",
                               ("connect_ai", "Connect"))
    return line


def _study_map_questions(repo, source_id: str) -> str | None:
    """What study-map builds that read this book left (round-2 review F6):
    ``"applied"`` when a finished build's questions were applied and are still
    in, ``"pending"`` when a finished build's questions still wait for a look,
    else ``None``. The applied proposal items are the receipt; collection
    membership and a build that failed or was turned down count for nothing."""

    extraction_ids = [
        run["id"]
        for revision in repo.source_revisions_for(source_id)
        for run in repo.extraction_runs_for_revision(revision["id"])
    ]
    if not extraction_ids:
        return None
    pending = False
    with repo.connection() as connection:
        for extraction_id in extraction_ids:
            rows = connection.execute(
                "SELECT i.decision AS decision, i.applied_change_batch_id AS applied "
                "FROM synthesis_manifests m "
                "JOIN synthesis_runs r ON r.manifest_id = m.id AND r.status = 'completed' "
                "JOIN proposed_patch_items i ON i.proposed_patch_id = r.proposal_id "
                "WHERE m.extraction_ids_json LIKE ?",
                (f'%"{extraction_id}"%',),
            ).fetchall()
            for row in rows:
                if row["decision"] == "accepted" and row["applied"]:
                    return "applied"
                pending = pending or row["decision"] == "pending"
    return "pending" if pending else None


def _built_phrase(repo, source_id: str, outcome: Mapping[str, Any], noun: str) -> str | None:
    """Every chapter the book's questions cover so far (``Ch. 1–3``), not
    only the newest build's (usability round 1)."""

    if outcome.get("whole_source"):
        return None
    resolved = _completed_extraction(repo, source_id)
    if resolved is None:
        return None
    built = coverage(repo, source_id).built
    if not built:
        return None
    labels = [chapter.label for chapter in outline_chapters(_unit_tree(repo, resolved[1])) if chapter.unit_id in built]
    return chapter_phrase(labels, noun=noun) if labels else None


def _unit_tree(repo, extraction_id: str) -> Any:
    """Just the extraction's units (id, parent, label), enough for
    ``outline_chapters``' chapter list and labels: the card's line is read on
    every library poll and keeping a chapter ahead on every reading-progress
    report, and the full outline loads the book's text once per unit
    (usability round 2: 6-8 s per read for a 630-page book; review F1)."""

    from types import SimpleNamespace

    with repo.connection() as connection:
        rows = connection.execute(
            "SELECT unit_id, parent_unit_id, label FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal",
            (extraction_id,),
        ).fetchall()
    return SimpleNamespace(units=[
        SimpleNamespace(unit_id=row["unit_id"], parent_unit_id=row["parent_unit_id"], label=row["label"], approx_tokens=0)
        for row in rows
    ])


def _category_of(source: Any) -> str | None:
    try:
        return resolve_source(str(source or "")).category
    except UnsupportedSourceError:
        return None


def pending_adds(repo, *, limit: int = 30) -> list[dict[str, Any]]:
    """Adds whose link is still being fetched (no library card yet): every
    unfinished Add, not a window over the queue (review F10)."""

    entries: list[dict[str, Any]] = []
    for batch in repo.ingest_batches_by_workflow(ADD_SOURCE_WORKFLOW, exclude_statuses=("completed", "cancelled")):
        if batch.get("cancel_requested"):
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
            "title": pending_title(source, category),
            "status_line": source_status_line(repo, None, None, batch_id=batch["id"]),
        })
        if len(entries) >= limit:
            break
    return entries


def pending_title(source: str, category: str | None) -> str:
    """A readable name for a link still being fetched (usability round 1: the
    video's card was titled with its raw URL)."""

    from urllib.parse import urlparse

    if category == "youtube":
        return "YouTube video"
    arxiv = re.search(r"(\d{4}\.\d{4,5})(?:v\d+)?", source) if category == "arxiv" else None
    if arxiv:
        return f"arXiv {arxiv.group(1)}"
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        host = parsed.netloc.removeprefix("www.")
        return f"{host}{parsed.path}".rstrip("/") or host
    return source


def latest_add_batch(repo, source_id: str) -> str | None:
    imports = import_jobs(repo, source_id)
    return imports[0]["batch_id"] if imports else None


def latest_planner(repo, source_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The planning job the card's line speaks for, and its outcome (a planner
    an Undo or a cancel stopped before it ran is skipped)."""

    for job in auto_jobs(repo, source_id):
        outcome = planner_outcome(repo, job)
        if outcome is None and job["status"] == "cancelled":
            continue
        return job, outcome
    return None, None


def latest_build_batch(repo, source_id: str) -> str | None:
    for job in auto_jobs(repo, source_id):
        batch_id = (planner_outcome(repo, job) or {}).get("build_batch_id")
        if batch_id:
            return str(batch_id)
    return None


def retry_build(ingest_jobs, source_id: str) -> str:
    """The card's Retry for a failed automatic build (§6.7, review F11): the
    zero-model repair and revalidation of a preserved candidate first; a fresh
    model run only when there is none, or repairing it already failed, and
    then under a new admission (a new attempt of each paid job)."""

    repo = ingest_jobs.repository
    batch_id = latest_build_batch(repo, source_id)
    if batch_id is None:
        return request_auto_build(ingest_jobs, source_id)
    jobs = repo.ingest_jobs_for_batch(batch_id)
    synthesis = next((job for job in jobs if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}), None)
    inventories_done = all(job["status"] == "completed" for job in jobs if job["job_type"] == "inventory")
    if synthesis is not None and inventories_done and synthesis["status"] in {"failed", "blocked", "cancelled"}:
        details = (synthesis.get("error") or {}).get("details") or {}
        payload = synthesis.get("payload") or {}
        repaired_before = bool(payload.get("reuse_candidate") and payload.get("repair_candidate"))
        if details.get("candidate_preserved") and details.get("synthesis_run_id") and not repaired_before:
            try:
                ingest_jobs.retry_synthesis(batch_id, reuse_candidate=True, repair_candidate=True)
                return batch_id
            except ValueError:
                pass  # the candidate is gone: regenerate below
        ingest_jobs.retry_synthesis(batch_id)
        return batch_id
    ingest_jobs.resume_batch(batch_id)
    return batch_id


__all__ = [
    "ADD_SOURCE_PRIORITY",
    "ADD_SOURCE_WORKFLOW",
    "AUTO_BUILD_WORKFLOW",
    "AUTO_STUDY_MAP_JOB",
    "AddSourceOptions",
    "AuthoringRoute",
    "Chapter",
    "CostDecision",
    "Coverage",
    "act_on_reading_request",
    "add_source",
    "admit_auto_build_job",
    "advance_reading_build",
    "after_auto_build",
    "authoring_route_for",
    "auto_apply_allowed",
    "built_unit_ids",
    "chapter_phrase",
    "child_batch_id",
    "consent_key",
    "consent_label",
    "cost_pause_reason",
    "coverage",
    "decide_cost",
    "default_authoring_route",
    "ensure_subject",
    "estimate_usd",
    "file_upload_allowed",
    "keep_ahead_for_reader",
    "keep_on_this_computer",
    "kind_noun",
    "source_kind_noun",
    "build_minutes_phrase",
    "pdf_metadata_title",
    "TEXT_RECOGNITION_HOW_TO",
    "latest_auto_outcome",
    "latest_planner",
    "learner_title",
    "outline_chapters",
    "pending_adds",
    "pending_title",
    "plan_reading_advance",
    "planner_outcome",
    "preview_auto_build",
    "reading_order_scope",
    "reconcile_reading_builds",
    "release_waiting_builds",
    "request_auto_build",
    "retry_build",
    "run_auto_study_map",
    "share_with_ai",
    "source_status_line",
    "spent_today_usd",
    "text_recognition_available",
    "undo_source_questions",
    "what_leaves",
]
