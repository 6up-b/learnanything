"""Delayed probes: generation, filters, selection, sealing, answers, grades (spec §5.2).

Generation runs per captured diff in stages, each persisted before the next
paid call, so an interrupted or failed run resumes without paying twice:

1. **Author** (``project_probe_authoring``): ~6 answer-first candidates, each a
   reference answer with ``file:line``/commit/diff citations, then the question.
2. **Validity** (local, a ``verifier`` verdict): file citations must resolve to
   stored head-side lines, quotes must match verbatim, and a ``why`` needs a
   citation that states the reason (P4). Invalid candidates are dropped.
3. **Closed-book** (``project_closed_book_check``): a model with only the
   question answers each survivor; the probe grader grades that answer against
   the reference, and a ``correct`` answer rejects the candidate as generic.
4. **Select**: two survivors at random with the diff's stored seed; fewer than
   two leaves the diff ``under_probed`` with what it has.

Probes are sealed until ``captured_at + project.probe_delay_days``: nothing
renders a question before then (G5). Answers are unassisted unless the owner
taps "I looked" or "I used AI". The grader (``grading`` route) is blind: it sees
the question, the reference with its quoted evidence and the answer, nothing
about who answered or how the code was produced (G3). Probe answers are
practice only, never cold certification (D6).
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable, AITurnTimeout
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.clock import Clock, FrozenClock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.ids import new_ulid
from learnloop.projects.ai_contracts import (
    CLOSED_BOOK_PROMPT_VERSION,
    CLOSED_BOOK_PURPOSE,
    PROBE_AUTHORING_PROMPT_VERSION,
    PROBE_AUTHORING_PURPOSE,
    PROBE_GRADING_PROMPT_VERSION,
    PROBE_GRADING_PURPOSE,
    PROBE_KINDS,
    ClosedBookAnswers,
    ClosedBookContext,
    ProbeAuthoringContext,
    ProbeCandidate,
    ProbeCandidates,
    ProbeGrades,
    ProbeGradingContext,
    closed_book_prompt,
    probe_authoring_prompt,
    probe_grading_prompt,
)
from learnloop.projects.ai_runtime import PaidCalls, PlannedCall, ProjectRoute
from learnloop.projects.capture import BundleIntegrityError, estimate_tokens, load_bundle, parse_hunks
from learnloop.projects.experiment_store import ProjectStore, store_path

AUTHORING_OUTPUT_TOKENS = 6_000
CLOSED_BOOK_OUTPUT_TOKENS_PER_QUESTION = 250
GRADING_OUTPUT_TOKENS_PER_ITEM = 250
# Every call's output budget also covers reasoning: on metered routes the budget
# is the request's enforced generation limit, and a reasoning model spends its
# thinking from the same limit.
REASONING_HEADROOM_TOKENS = 4_000
GRADING_ITEM_TOKENS_ESTIMATE = 500
CLOSED_BOOK_QUESTION_TOKENS_ESTIMATE = 120
PROMPT_OVERHEAD_TOKENS = 900
MAX_GENERATION_ATTEMPTS = 3
MAX_GRADE_ATTEMPTS = 3
GENERIC_VERDICTS = frozenset({"correct"})
RESPONSE_KINDS = ("answer", "dont_know", "unfair", "skip")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
DECLARATIONS = ("unassisted", "looked", "used_ai")


def authoring_output_tokens() -> int:
    return AUTHORING_OUTPUT_TOKENS + REASONING_HEADROOM_TOKENS


def closed_book_output_tokens(questions: int) -> int:
    return CLOSED_BOOK_OUTPUT_TOKENS_PER_QUESTION * questions + REASONING_HEADROOM_TOKENS


def grading_output_tokens(items: int) -> int:
    return GRADING_OUTPUT_TOKENS_PER_ITEM * items + REASONING_HEADROOM_TOKENS


class SealedProbeError(ValueError):
    """A probe is not due yet, not selected, or does not exist."""


class ProbeStateError(ValueError):
    """The requested action does not apply to this probe or response."""


class GenerationError(ValueError):
    """A generation stage failed for a reason whose message is safe to show."""


def safe_error(exc: BaseException) -> str:
    """An error string that can never quote model output.

    Invalid-output and validation messages can echo a candidate question,
    which must not render before it is due (G5); the full output stays in the
    store's call receipts.
    """

    name = type(exc).__name__
    if isinstance(exc, (GenerationError, BundleIntegrityError, SpendLimitExceeded, AITurnTimeout)):
        return f"{name}: {exc}"[:300]
    if isinstance(exc, AIProviderUnavailable) and not isinstance(exc, AIInvalidOutput):
        return f"{name}: {exc}"[:300]
    return f"{name} (details are in the call receipts)"


@contextmanager
def _exclusive(vault_root: Path, name: str) -> Iterator[bool]:
    """A non-blocking cross-process lock, so two commands never pay twice."""

    try:
        import fcntl
    except ImportError:  # pragma: no cover - POSIX hosts only
        yield True
        return
    path = store_path(vault_root).parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _input_hash(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


def _now(clock: Clock | None) -> str:
    return utc_now_iso(clock)


def _sealed_until(diff: dict[str, Any], config: LearnLoopConfig) -> str:
    captured = parse_utc(diff["captured_at"])
    assert captured is not None
    return utc_now_iso(FrozenClock(captured + timedelta(days=config.project.probe_delay_days)))


# --- model-facing material -------------------------------------------------------


def authoring_context(bundle: dict[str, Any], *, repo_name: str, config: LearnLoopConfig) -> ProbeAuthoringContext:
    files = []
    for entry in bundle["files"]:
        if entry.get("omitted"):
            continue
        excerpts = []
        for excerpt in entry["excerpts"]:
            start = int(excerpt["start_line"])
            lines = excerpt["lines"]
            excerpts.append(
                {
                    "start_line": start,
                    "end_line": start + len(lines) - 1,
                    "text": "\n".join(f"{number}| {line}" for number, line in enumerate(lines, start)),
                }
            )
        files.append(
            {
                "path": entry["path"],
                "old_path": entry.get("old_path"),
                "status": entry["status"],
                "diff": entry["diff"],
                "excerpts": excerpts,
            }
        )
    return ProbeAuthoringContext(
        repo_name=repo_name,
        commit_message=bundle["commit_message"],
        files=files,
        candidate_count=config.project.candidates_per_diff,
        kinds=list(PROBE_KINDS),
    )


def _disclosure_for_bundle(bundle: dict[str, Any], diff: dict[str, Any], repo: dict[str, Any], prompt: str) -> dict[str, Any]:
    files = [entry for entry in bundle["files"] if not entry.get("omitted")]
    return {
        "stage": "authoring",
        "files_sent": [entry["path"] for entry in files],
        "hunk_count": sum(len(parse_hunks(entry["diff"])) for entry in files),
        "bytes_sent": len(prompt.encode("utf-8")),
        "redaction_count": int(diff["redaction_count"]),
        "context_scope": "diff",
        "requested_context_scope": repo["context_scope"],
        "commit_message_sent": bool(bundle["commit_message"]),
    }


def _evidence(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source": citation["source"],
            "path": citation.get("path", ""),
            "line_start": citation.get("line_start", 0),
            "line_end": citation.get("line_end", 0),
            "quote": citation.get("quote", ""),
        }
        for citation in citations
    ]


# --- validity -----------------------------------------------------------------------


def added_lines(diff_text: str) -> set[int]:
    """New-side line numbers this diff added."""

    added: set[int] = set()
    current: int | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current = None
            continue
        match = _HUNK_HEADER.match(line)
        if match is not None:
            current = int(match.group(1))
            continue
        if current is None or line.startswith("\\"):
            continue
        if line.startswith("+"):
            added.add(current)
            current += 1
        elif line.startswith(" "):
            current += 1
    return added


@dataclass(frozen=True)
class Validity:
    status: str
    detail: str | None = None
    rationale_label: str | None = None


def _clean_quote(quote: str) -> str:
    return quote.replace("\r\n", "\n").strip()


def validate_candidate(
    candidate: ProbeCandidate,
    bundle: dict[str, Any],
    *,
    agent_committed: bool,
) -> Validity:
    """Deterministic checks: citations resolve and quotes are verbatim (§5.2)."""

    if candidate.kind not in PROBE_KINDS:
        return Validity("invalid_kind", candidate.kind)
    if not candidate.question.strip() or not candidate.reference_answer.strip():
        return Validity("empty")
    if not candidate.citations:
        return Validity("no_citation")
    files = {entry["path"]: entry for entry in bundle["files"] if not entry.get("omitted")}
    rationale_sources: list[str] = []
    for citation in candidate.citations:
        quote = _clean_quote(citation.quote)
        if not quote:
            return Validity("quote_mismatch", "empty quote")
        if "[REDACTED" in quote:
            return Validity("quote_mismatch", "quotes a redacted line")
        if citation.source == "commit_message":
            if quote not in bundle["commit_message"]:
                return Validity("quote_mismatch", "commit message quote not found")
            source = "agent_stated" if agent_committed else "cited"
        elif citation.source == "diff":
            entry = files.get(citation.path)
            if entry is None:
                return Validity("citation_unresolved", f"unknown file {citation.path!r}")
            if quote not in entry["diff"]:
                return Validity("quote_mismatch", f"diff quote not found in {citation.path}")
            source = "agent_stated"
        else:
            entry = files.get(citation.path)
            if entry is None:
                return Validity("citation_unresolved", f"unknown file {citation.path!r}")
            start, end = int(citation.line_start), int(citation.line_end)
            if start < 1 or end < start:
                return Validity("citation_unresolved", f"bad line range {start}-{end}")
            excerpt = next(
                (
                    item for item in entry["excerpts"]
                    if item["start_line"] <= start and end <= item["start_line"] + len(item["lines"]) - 1
                ),
                None,
            )
            if excerpt is None:
                return Validity("citation_unresolved", f"{citation.path}:{start}-{end} is not in the stored snapshot")
            cited = "\n".join(excerpt["lines"][start - excerpt["start_line"] : end - excerpt["start_line"] + 1])
            if quote not in cited and quote not in "\n".join(line.strip() for line in cited.splitlines()):
                return Validity("quote_mismatch", f"quote does not match {citation.path}:{start}-{end}")
            changed = added_lines(entry["diff"])
            source = "agent_stated" if any(line in changed for line in range(start, end + 1)) else "cited"
        if citation.rationale:
            rationale_sources.append(source)
    if candidate.kind == "why":
        if not rationale_sources:
            return Validity("why_uncited", "no citation states the reason")
        label = "agent_stated" if "agent_stated" in rationale_sources else "cited"
        return Validity("valid", rationale_label=label)
    return Validity("valid")


# --- grading (shared by the closed-book filter and owner answers) -------------------


def grade_items(
    paid: PaidCalls,
    route: ProjectRoute,
    items: list[dict[str, Any]],
    *,
    diff_id: str | None,
    stage: str,
) -> dict[str, Any]:
    """Blind-grade ``items`` ({key, question, reference_answer, citations, answer})."""

    context = ProbeGradingContext(
        items=[
            {
                "id": item["key"],
                "question": item["question"],
                "reference_answer": item["reference_answer"],
                "evidence": _evidence(item["citations"]),
                "answer": item["answer"],
            }
            for item in items
        ]
    )
    prompt = probe_grading_prompt(context)
    result: ProbeGrades = paid.call(
        route,
        purpose=PROBE_GRADING_PURPOSE,
        prompt=prompt,
        result_model=ProbeGrades,
        output_tokens=grading_output_tokens(len(items)),
        diff_id=diff_id,
        disclosure={
            "files_sent": sorted({c.get("path") for item in items for c in item["citations"] if c.get("path")}),
            "hunk_count": 0,
            "bytes_sent": len(prompt.encode("utf-8")),
            "redaction_count": 0,
            "context_scope": "quoted_evidence",
            "stage": stage,
        },
    )
    grades = {grade.id: grade for grade in result.grades}
    missing = [item["key"] for item in items if item["key"] not in grades]
    if missing:
        raise GenerationError(f"grader returned no grade for {', '.join(missing)}")
    return grades


def _clamp(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


# --- generation ------------------------------------------------------------------------


@dataclass
class GenerationReport:
    status: str = "complete"
    dry_run: bool = False
    diffs: list[dict[str, Any]] = field(default_factory=list)
    estimate: dict[str, Any] | None = None
    spend: dict[str, Any] | None = None
    routes: dict[str, Any] | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dry_run": self.dry_run,
            "diffs": self.diffs,
            "estimate": self.estimate,
            "spend": self.spend,
            "routes": self.routes,
            "reason": self.reason,
        }


def diffs_awaiting_generation(store: ProjectStore, *, due_by: str | None = None, config: LearnLoopConfig | None = None) -> list[dict[str, Any]]:
    """Diffs whose probes are not generated yet, optionally only those due by ``due_by``."""

    pending = store.diffs(probe_status="pending")
    if due_by is None or config is None:
        return pending
    return [diff for diff in pending if _sealed_until(diff, config) <= due_by]


def plan_generation(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    diffs: list[dict[str, Any]],
) -> list[PlannedCall]:
    """The calls generation would make, from the stored bundles (no model calls)."""

    planned: list[PlannedCall] = []
    count = config.project.candidates_per_diff
    for diff in diffs:
        existing = store.probes_for_diff(diff["id"])
        if not existing:
            repo = store.repo(diff["repo_id"]) or {"name": ""}
            try:
                bundle = load_bundle(vault_root, diff["bundle_hash"])
                prompt = probe_authoring_prompt(authoring_context(bundle, repo_name=repo["name"], config=config))
                input_tokens = estimate_tokens(prompt)
            except BundleIntegrityError:
                input_tokens = int(diff["token_estimate"]) + PROMPT_OVERHEAD_TOKENS
            planned.append(PlannedCall("authoring", input_tokens, authoring_output_tokens(), candidates=count))
            closed_book, grading = count, count
        else:
            closed_book = sum(probe["status"] == "pending_closed_book" for probe in existing)
            grading = closed_book + sum(probe["status"] == "pending_closed_book_grade" for probe in existing)
        if closed_book:
            planned.append(
                PlannedCall(
                    "closed_book",
                    PROMPT_OVERHEAD_TOKENS + CLOSED_BOOK_QUESTION_TOKENS_ESTIMATE * closed_book,
                    closed_book_output_tokens(closed_book),
                )
            )
        if grading:
            planned.append(
                PlannedCall(
                    "grading",
                    PROMPT_OVERHEAD_TOKENS + GRADING_ITEM_TOKENS_ESTIMATE * grading,
                    grading_output_tokens(grading),
                )
            )
    return planned


def _author(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    paid: PaidCalls,
    route: ProjectRoute,
    diff: dict[str, Any],
    repo: dict[str, Any],
    clock: Clock | None,
) -> None:
    bundle = load_bundle(vault_root, diff["bundle_hash"])
    context = authoring_context(bundle, repo_name=repo["name"], config=config)
    prompt = probe_authoring_prompt(context)
    result: ProbeCandidates = paid.call(
        route,
        purpose=PROBE_AUTHORING_PURPOSE,
        prompt=prompt,
        result_model=ProbeCandidates,
        output_tokens=authoring_output_tokens(),
        candidates=config.project.candidates_per_diff,
        diff_id=diff["id"],
        disclosure=_disclosure_for_bundle(bundle, diff, repo, prompt),
    )
    candidates = result.candidates[: config.project.candidates_per_diff]
    now = _now(clock)
    sealed_until = _sealed_until(diff, config)
    rows = []
    for index, candidate in enumerate(candidates):
        validity = validate_candidate(candidate, bundle, agent_committed=diff["agent_source"] == "trailer")
        rows.append(
            {
                "id": new_ulid(),
                "diff_id": diff["id"],
                "candidate_index": index,
                "kind": candidate.kind,
                "question": candidate.question.strip(),
                "reference_answer": candidate.reference_answer.strip(),
                "citations_json": json.dumps([c.model_dump() for c in candidate.citations], sort_keys=True),
                "rationale_label": validity.rationale_label,
                "validity": validity.status,
                "validity_detail": validity.detail,
                "status": "pending_closed_book" if validity.status == "valid" else "invalid",
                "sealed_until": sealed_until,
                "generator_provider": route.provider_name,
                "generator_model": route.model or route.provider_name,
                "generator_prompt_version": PROBE_AUTHORING_PROMPT_VERSION,
                "created_at": now,
            }
        )
    store.insert_probe_candidates(rows)
    for row in rows:
        store.append_judgment(
            task="project_probe_validity",
            left_kind="project_probe",
            left_id=row["id"],
            judge="verifier",
            input_hash=_input_hash({"citations": row["citations_json"], "bundle": diff["bundle_hash"]}),
            verdict=row["validity"],
            rationale=json.dumps({"detail": row["validity_detail"], "rationale_label": row["rationale_label"]}),
            created_at=now,
        )


def _closed_book(
    store: ProjectStore,
    paid: PaidCalls,
    route: ProjectRoute,
    diff: dict[str, Any],
    probes: list[dict[str, Any]],
) -> None:
    keys = {f"q{probe['candidate_index']}": probe for probe in probes}
    context = ClosedBookContext(questions=[{"id": key, "question": probe["question"]} for key, probe in keys.items()])
    prompt = closed_book_prompt(context)
    result: ClosedBookAnswers = paid.call(
        route,
        purpose=CLOSED_BOOK_PURPOSE,
        prompt=prompt,
        result_model=ClosedBookAnswers,
        output_tokens=closed_book_output_tokens(len(keys)),
        diff_id=diff["id"],
        disclosure={
            "files_sent": [],
            "hunk_count": 0,
            "bytes_sent": len(prompt.encode("utf-8")),
            "redaction_count": 0,
            "context_scope": "questions_only",
            "stage": "closed_book",
        },
    )
    answers = {answer.id: answer.answer for answer in result.answers}
    store.record_closed_book_answers(
        {probe["id"]: answers.get(key, "") for key, probe in keys.items()},
        model=route.model or route.provider_name,
    )


def _closed_book_grades(
    store: ProjectStore,
    paid: PaidCalls,
    route: ProjectRoute,
    diff: dict[str, Any],
    probes: list[dict[str, Any]],
    clock: Clock | None,
) -> None:
    items = [
        {
            "key": f"q{probe['candidate_index']}",
            "question": probe["question"],
            "reference_answer": probe["reference_answer"],
            "citations": json.loads(probe["citations_json"]),
            "answer": probe["closed_book_answer"] or "",
        }
        for probe in probes
    ]
    grades = grade_items(paid, route, items, diff_id=diff["id"], stage="closed_book_grading")
    now = _now(clock)
    for item, probe in zip(items, probes):
        grade = grades[item["key"]]
        generic = grade.verdict in GENERIC_VERDICTS
        store.record_closed_book_grade(probe["id"], verdict=grade.verdict, score=_clamp(grade.score), generic=generic)
        store.append_judgment(
            task="project_closed_book",
            left_kind="project_probe",
            left_id=probe["id"],
            judge="llm",
            judge_model=route.model or route.provider_name,
            prompt_version=PROBE_GRADING_PROMPT_VERSION,
            input_hash=_input_hash(item),
            verdict="generic" if generic else "specific",
            score=_clamp(grade.score),
            rationale=json.dumps(
                {"grade_verdict": grade.verdict, "feedback": grade.feedback,
                 "closed_book_prompt_version": CLOSED_BOOK_PROMPT_VERSION}
            ),
            created_at=now,
        )


def _select(store: ProjectStore, config: LearnLoopConfig, diff: dict[str, Any], clock: Clock | None) -> str:
    survivors = [probe for probe in store.probes_for_diff(diff["id"]) if probe["status"] == "survivor"]
    wanted = config.project.probes_per_diff
    rng = random.Random(int(diff["selection_seed"]))
    chosen = rng.sample(survivors, min(wanted, len(survivors)))
    store.select_probes([probe["id"] for probe in chosen])
    status = "generated" if len(chosen) >= wanted else "under_probed"
    store.finish_generation(diff["id"], status=status, generated_at=_now(clock))
    return status


def generate_for_diff(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    paid: PaidCalls,
    routes: dict[str, ProjectRoute],
    diff: dict[str, Any],
    *,
    clock: Clock | None = None,
) -> str:
    """Run the remaining stages for one diff; returns its new probe status."""

    repo = store.repo(diff["repo_id"]) or {"name": "", "context_scope": "diff"}
    if not store.probes_for_diff(diff["id"]):
        _author(store, vault_root, config, paid, routes["authoring"], diff, repo, clock)
    pending = [probe for probe in store.probes_for_diff(diff["id"]) if probe["status"] == "pending_closed_book"]
    if pending:
        _closed_book(store, paid, routes["closed_book"], diff, pending)
    to_grade = [probe for probe in store.probes_for_diff(diff["id"]) if probe["status"] == "pending_closed_book_grade"]
    if to_grade:
        _closed_book_grades(store, paid, routes["grading"], diff, to_grade, clock)
    return _select(store, config, diff, clock)


def generate_probes(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    paid: PaidCalls,
    routes: dict[str, ProjectRoute],
    diffs: list[dict[str, Any]],
    *,
    clock: Clock | None = None,
) -> GenerationReport:
    report = GenerationReport(routes={role: route.describe() for role, route in routes.items()})
    unready = [route for route in routes.values() if not route.ready]
    if unready and diffs:
        report.status = "provider_unavailable"
        report.reason = "; ".join(f"{route.role}: {route.message or 'not ready'}" for route in unready)
        report.spend = paid.summary()
        return report
    with _exclusive(vault_root, "generate.lock") as acquired:
        if not acquired:
            report.status, report.reason = "busy", "another command is generating questions; rerun when it finishes"
            report.spend = paid.summary()
            return report
        _generate_all(store, vault_root, config, paid, routes, diffs, report, clock)
    report.spend = paid.summary()
    return report


def _generate_all(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    paid: PaidCalls,
    routes: dict[str, ProjectRoute],
    diffs: list[dict[str, Any]],
    report: GenerationReport,
    clock: Clock | None,
) -> None:
    for diff in diffs:
        current = store.diff(diff["id"])
        if current is None or current["probe_status"] != "pending":
            continue  # finished by another run in the meantime
        entry = {"diff_id": diff["id"], "status": None, "error": None}
        report.diffs.append(entry)
        try:
            entry["status"] = generate_for_diff(store, vault_root, config, paid, routes, current, clock=clock)
        except SpendLimitExceeded as exc:
            entry["status"], entry["error"] = "pending", str(exc)
            report.status, report.reason = "over_budget", str(exc)
            break
        except (AIInterrupted, KeyboardInterrupt) as exc:
            entry["status"], entry["error"] = "pending", type(exc).__name__
            report.status, report.reason = "cancelled", "interrupted; rerun to resume"
            break
        except BundleIntegrityError as exc:
            store.record_generation_failure(diff["id"], error=safe_error(exc), max_attempts=1)
            entry["status"], entry["error"] = "failed", safe_error(exc)
        except Exception as exc:  # noqa: BLE001 - provider and output failures are per-diff
            message = safe_error(exc)
            store.record_generation_failure(diff["id"], error=message, max_attempts=MAX_GENERATION_ATTEMPTS)
            entry["status"], entry["error"] = (store.diff(diff["id"]) or {}).get("probe_status"), message
            report.status = "partial"


# --- serving and answering ---------------------------------------------------------------


def probe_header(store: ProjectStore, probe: dict[str, Any]) -> dict[str, Any]:
    """What the owner sees with a due question: where it is from, never the answer.

    The commit message is left out: it often states the very rationale a
    ``why`` probe asks for.
    """

    diff = store.diff(probe["diff_id"]) or {}
    repo = store.repo(diff.get("repo_id", "")) or {}
    files = [entry["path"] for entry in json.loads(diff.get("files_json") or "[]") if not entry.get("omitted")]
    return {
        "probe_id": probe["id"],
        "repo": repo.get("name"),
        "files": files,
        "committed_at": diff.get("committed_at"),
        "captured_at": diff.get("captured_at"),
        "kind": probe["kind"],
    }


def due_probes(store: ProjectStore, *, clock: Clock | None = None, repo_id: str | None = None) -> list[dict[str, Any]]:
    return store.due_probes(_now(clock), repo_id=repo_id)


def _require_due(store: ProjectStore, probe_id: str, clock: Clock | None) -> dict[str, Any]:
    probe = store.probe(probe_id)
    if probe is None or not probe["selected"] or probe["sealed_until"] > _now(clock):
        # One message for all three: whether a sealed probe exists is itself
        # not revealed before it is due.
        raise SealedProbeError(f"No due probe {probe_id!r}.")
    return probe


def open_probe(store: ProjectStore, probe_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """The question text of a due probe (the only way a question is rendered)."""

    probe = _require_due(store, probe_id, clock)
    return {**probe_header(store, probe), "question": probe["question"]}


def record_response(
    store: ProjectStore,
    probe_id: str,
    *,
    kind: str,
    answer: str | None = None,
    declaration: str = "unassisted",
    served_at: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if kind not in RESPONSE_KINDS:
        raise ProbeStateError(f"response kind must be one of {', '.join(RESPONSE_KINDS)}")
    if declaration not in DECLARATIONS:
        raise ProbeStateError(f"declaration must be one of {', '.join(DECLARATIONS)}")
    probe = _require_due(store, probe_id, clock)
    if kind == "answer" and not (answer or "").strip():
        raise ProbeStateError("an answer needs text; use don't know or skip otherwise")
    now = _now(clock)
    due = parse_utc(probe["sealed_until"])
    answered = parse_utc(now)
    response_id = new_ulid()
    inserted = store.insert_response(
        {
            "id": response_id,
            "probe_id": probe_id,
            "response_kind": kind,
            "answer": answer.strip() if kind == "answer" and answer else None,
            "declaration": declaration,
            "served_at": served_at or now,
            "answered_at": now,
            "due_at": probe["sealed_until"],
            "lateness_seconds": max(0, int((answered - due).total_seconds())) if due and answered else 0,
            "grade_status": "pending" if kind == "answer" else "not_applicable",
        }
    )
    if not inserted:
        raise ProbeStateError(f"probe {probe_id} was already answered")
    if kind == "unfair":
        store.append_judgment(
            task="project_probe_unfair",
            left_kind="project_probe",
            left_id=probe_id,
            judge="owner",
            input_hash=_input_hash({"probe": probe_id, "question": probe["question"]}),
            verdict="unfair_or_ambiguous",
            rationale="owner tapped 'question is unfair/ambiguous'",
            created_at=now,
        )
    return store.response(response_id) or {}


def grade_responses(
    store: ProjectStore,
    paid: PaidCalls,
    route: ProjectRoute,
    *,
    response_ids: list[str] | None = None,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Blind-grade pending answers one at a time; failures stay pending to retry."""

    results = []
    pending = [
        response for response in store.responses(grade_status="pending")
        if response_ids is None or response["id"] in response_ids
    ]
    for response in pending:
        probe = store.probe(response["probe_id"])
        if probe is None:
            continue
        item = {
            "key": "a1",
            "question": probe["question"],
            "reference_answer": probe["reference_answer"],
            "citations": json.loads(probe["citations_json"]),
            "answer": response["answer"] or "",
        }
        try:
            grade = grade_items(paid, route, [item], diff_id=probe["diff_id"], stage="answer_grading")["a1"]
        except (SpendLimitExceeded, AIInterrupted, KeyboardInterrupt):
            raise
        except Exception as exc:  # noqa: BLE001 - one failed grade must not lose the answer
            store.record_grade_failure(response["id"], max_attempts=MAX_GRADE_ATTEMPTS)
            results.append({"response_id": response["id"], "status": "grade_failed", "error": safe_error(exc)})
            continue
        now = _now(clock)
        score = _clamp(grade.score)
        model = route.model or route.provider_name
        store.record_grade(
            response["id"], score=score, verdict=grade.verdict, feedback=grade.feedback,
            provider=route.provider_name, model=model, prompt_version=PROBE_GRADING_PROMPT_VERSION,
            graded_at=now,
        )
        store.append_judgment(
            task="project_probe_grade",
            left_kind="probe_response",
            left_id=response["id"],
            judge="llm",
            judge_model=model,
            prompt_version=PROBE_GRADING_PROMPT_VERSION,
            input_hash=_input_hash(item),
            verdict=grade.verdict,
            score=score,
            rationale=grade.feedback or grade.verdict,
            created_at=now,
        )
        results.append({"response_id": response["id"], "status": "graded", "score": score, "verdict": grade.verdict})
    return results


def contest_grade(
    store: ProjectStore,
    response_id: str,
    *,
    score: float,
    note: str = "",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The owner's adjudication becomes the outcome of record; the grade is kept."""

    if not 0.0 <= score <= 1.0:
        raise ProbeStateError("score must be between 0 and 1")
    response = store.response(response_id)
    if response is None:
        raise ProbeStateError(f"no response {response_id!r}")
    if response["grade_status"] != "graded":
        raise ProbeStateError("only a graded answer can be contested")
    now = _now(clock)
    prior = [row for row in store.judgments(task="project_probe_grade", left_id=response_id)]
    store.record_adjudication(response_id, score=score, note=note, adjudicated_at=now)
    store.append_judgment(
        task="project_probe_grade",
        left_kind="probe_response",
        left_id=response_id,
        judge="owner",
        input_hash=_input_hash({"response": response_id, "score": score}),
        verdict="adjudicated",
        score=score,
        rationale=note or "owner adjudication",
        created_at=now,
        supersedes_id=prior[-1]["id"] if prior else None,
    )
    return store.response(response_id) or {}


def reveal(store: ProjectStore, response: dict[str, Any]) -> dict[str, Any]:
    """After answering: the reference, its citations, and honest rationale labels."""

    probe = store.probe(response["probe_id"]) or {}
    citations = json.loads(probe.get("citations_json") or "[]")
    return {
        "probe_id": probe.get("id"),
        "response_id": response["id"],
        "grade_status": response["grade_status"],
        "score": response.get("adjudicated_score") if response.get("adjudicated_score") is not None else response.get("score"),
        "verdict": response.get("verdict"),
        "feedback": response.get("feedback"),
        "reference_answer": probe.get("reference_answer"),
        "citations": _evidence(citations),
        "rationale_label": probe.get("rationale_label"),
    }


__all__ = [
    "DECLARATIONS",
    "GenerationReport",
    "ProbeStateError",
    "RESPONSE_KINDS",
    "SealedProbeError",
    "Validity",
    "added_lines",
    "authoring_context",
    "authoring_output_tokens",
    "closed_book_output_tokens",
    "grading_output_tokens",
    "contest_grade",
    "diffs_awaiting_generation",
    "due_probes",
    "generate_for_diff",
    "generate_probes",
    "grade_items",
    "grade_responses",
    "open_probe",
    "plan_generation",
    "probe_header",
    "record_response",
    "reveal",
    "validate_candidate",
]
