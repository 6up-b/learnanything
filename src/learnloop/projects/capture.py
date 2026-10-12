"""Automatic capture of agent-written diffs (spec §3, §4).

- **Sweep** (``sweep``/``auto_sweep``): every enrolled repo's local branches
  are listed since the repo's ``capture_since``; commits with an agent trailer
  (``Co-Authored-By: Claude …`` and friends) that are not yet captured are
  captured. The optional ``post-commit`` pending list feeds the same path;
  trailer-less commits from it are kept as *unattributed* for a one-tap
  self-report. Sweeps only run git: no model is ever called here.
- **Manual** (``capture_working_tree``/``capture_commit`` through
  ``learnloop project accept``): agent work without a trailer.

A capture stores a redacted *bundle*: per included file, its redacted diff and
redacted head-side excerpts (±``project.context_lines`` around each hunk,
extended to the enclosing function or class when the bundle stays within
``project.context_token_budget``), plus the redacted commit message. The bundle
lives in the originals store keyed by content hash, so probes and grades are
reproducible without git (P6). Secret, ignored, noise and binary files are
skipped by path before any content is read into the bundle.
"""

from __future__ import annotations

import json
import logging
import math
import re
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

from learnloop.clock import Clock, FrozenClock, SystemClock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.ids import new_ulid
from learnloop.ingest.hashing import asset_hash
from learnloop.ingest.originals import canonical_source_raw_path, store_original_bytes
from learnloop.projects.experiment_store import ProjectStore, pending_path, store_path
from learnloop.projects.git import (
    GitError,
    empty_tree_sha,
    git_text,
    head_sha,
    patch_id,
    repo_toplevel,
    run_git,
)
from learnloop.projects.redaction import (
    SECRET_PATTERN_VERSION,
    PathRules,
    RedactionCounter,
    load_path_rules,
    redact_diff,
    redact_lines,
    redact_text,
)

_LOG = logging.getLogger(__name__)

BUNDLE_FORMAT = "learnloop-project-diff-bundle-v1"
MAX_FILES_PER_CAPTURE = 200
MAX_UNTRACKED_FILE_BYTES = 512 * 1024
MAX_EXCERPT_FILE_BYTES = 2 * 1024 * 1024
MAX_SCOPE_LINES = 400
SWEEP_MAX_COMMITS = 5000
AGENT_TRAILER_KEYS = ("co-authored-by", "assisted-by", "generated-by")
_DIFF_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "--find-renames")
AGENTS = ("claude_code", "codex", "other", "unknown")

_AGENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("claude_code", re.compile(r"claude|anthropic", re.IGNORECASE)),
    ("codex", re.compile(r"\bcodex\b|openai|chatgpt", re.IGNORECASE)),
    (
        "other",
        re.compile(
            r"copilot|cursor|aider|devin|gemini|windsurf|codeium|\bjules\b|\bcline\b|\bamp\b",
            re.IGNORECASE,
        ),
    ),
)
_BODY_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("claude_code", re.compile(r"Generated with \[Claude Code\]")),
)
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_SCOPE_HEADER_RE = re.compile(
    r"^\s*(?:"
    r"(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:def|class|function|func|fn|impl|struct|enum|interface|trait|module|object)\b"
    r"|pub(?:\([^)]*\))?\s+(?:async\s+)?(?:fn|struct|enum|trait|impl|mod)\b"
    r"|(?:export\s+)?(?:const|let|var)\s+[\w$]+\s*=\s*(?:async\s*)?(?:function\b|\()"
    r"|(?:public|private|protected|internal|static|override)\s[^;=]*\("
    r")"
)


def estimate_tokens(text: str) -> int:
    """A conservative token estimate for budgets and spend (≈3 bytes/token)."""

    return math.ceil(len(text.encode("utf-8")) / 3)


# --- agent attribution ------------------------------------------------------


def parse_trailers(raw: str) -> list[tuple[str, str]]:
    trailers: list[tuple[str, str]] = []
    for line in raw.replace("\x1e", "\n").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        trailers.append((key.strip().lower(), value.strip()))
    return trailers


_TRAILER_LINE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9-]*)\s*:\s*(.*)$")


def strip_agent_trailers(message: str) -> str:
    """Remove agent attribution (trailers, "Generated with" lines) from a message.

    The model-facing bundle must not tell the generator who wrote the code
    (P3: no provenance labels); the full redacted message stays in the store.
    """

    kept: list[str] = []
    for line in message.splitlines():
        match = _TRAILER_LINE_RE.match(line)
        if match is not None and match.group(1).lower() in AGENT_TRAILER_KEYS:
            continue
        if any(rule.search(line) for _agent, rule in _BODY_MARKERS):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def detect_agent(trailers: Iterable[tuple[str, str]], message: str = "") -> str | None:
    """The coding agent named by a commit's trailers, or ``None`` if none is."""

    for key, value in trailers:
        if key not in AGENT_TRAILER_KEYS:
            continue
        for agent, rule in _AGENT_RULES:
            if rule.search(value):
                return agent
    for agent, rule in _BODY_MARKERS:
        if rule.search(message):
            return agent
    return None


# --- change listing -----------------------------------------------------------


@dataclass(frozen=True)
class FileChange:
    path: str
    old_path: str | None
    status: str
    added: int | None
    removed: int | None

    @property
    def binary(self) -> bool:
        return self.added is None or self.removed is None


def _range_args(base: str, head: str | None) -> list[str]:
    return [base] if head is None else [base, head]


def list_changes(repo: Path, base: str, head: str | None) -> list[FileChange]:
    """Changed tracked files between ``base`` and ``head`` (``None``: working tree)."""

    statuses = run_git(repo, ["diff", "--name-status", "-z", *_DIFF_FLAGS, *_range_args(base, head)])
    numstat = run_git(repo, ["diff", "--numstat", "-z", *_DIFF_FLAGS, *_range_args(base, head)])
    counts: dict[str, tuple[int | None, int | None]] = {}
    parts = numstat.decode("utf-8", "surrogateescape").split("\0")
    index = 0
    while index < len(parts):
        entry = parts[index]
        index += 1
        if not entry:
            continue
        added, removed, path = entry.split("\t", 2)
        if path == "":  # rename/copy: the two paths follow as their own fields
            path = parts[index + 1]
            index += 2
        counts[path] = (
            None if added == "-" else int(added),
            None if removed == "-" else int(removed),
        )
    changes: list[FileChange] = []
    fields = statuses.decode("utf-8", "surrogateescape").split("\0")
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if not status:
            continue
        letter = status[0]
        if letter in {"R", "C"}:
            old_path, path = fields[index], fields[index + 1]
            index += 2
        else:
            old_path, path = None, fields[index]
            index += 1
        added, removed = counts.get(path, (None, None))
        changes.append(FileChange(path=path, old_path=old_path, status=letter, added=added, removed=removed))
    return changes


def _literal(path: str) -> str:
    return f":(literal){path}"


def _file_diff(repo: Path, base: str, head: str | None, change: FileChange) -> str:
    paths = [change.path] if change.old_path is None else [change.old_path, change.path]
    output = run_git(
        repo,
        ["diff", *_DIFF_FLAGS, *_range_args(base, head), "--", *(_literal(path) for path in paths)],
    )
    return output.decode("utf-8", "replace")


def _untracked_diff(repo: Path, path: str) -> str:
    output = run_git(
        repo,
        ["diff", "--no-index", "--no-color", "--no-ext-diff", "--no-textconv", "--", "/dev/null", path],
        ok_codes=(0, 1),
    )
    return output.decode("utf-8", "replace")


def _head_lines(repo: Path, head: str | None, path: str) -> list[str] | None:
    """Head-side text lines of ``path``; ``None`` when unavailable or not text."""

    try:
        if head is None:
            candidate = (repo / path)
            if candidate.is_symlink() or not candidate.is_file():
                return None
            resolved = candidate.resolve()
            if repo not in resolved.parents:
                return None
            if resolved.stat().st_size > MAX_EXCERPT_FILE_BYTES:
                return None
            raw = resolved.read_bytes()
        else:
            raw = run_git(repo, ["cat-file", "blob", f"{head}:{path}"])
            if len(raw) > MAX_EXCERPT_FILE_BYTES:
                return None
    except (GitError, OSError):
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", "replace").splitlines()


def parse_hunks(diff_text: str) -> list[tuple[int, int]]:
    """New-side ``(start, end)`` line ranges (1-based, inclusive) of each hunk."""

    ranges: list[tuple[int, int]] = []
    for line in diff_text.splitlines():
        match = _HUNK_RE.match(line)
        if match is None:
            continue
        start = int(match.group(1))
        length = 1 if match.group(2) is None else int(match.group(2))
        if length == 0:
            ranges.append((max(start, 1), max(start, 1)))
        else:
            ranges.append((start, start + length - 1))
    return ranges


def _indent(line: str) -> int:
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip(" "))


def scope_range(lines: list[str], start: int, end: int) -> tuple[int, int] | None:
    """The enclosing function/class around a hunk, by header and indentation.

    A heuristic for indentation-structured code (Python, and brace languages
    that indent their bodies). ``None`` when no header is found or the scope is
    longer than ``MAX_SCOPE_LINES``.
    """

    count = len(lines)
    if count == 0:
        return None
    start = max(1, min(start, count))
    end = max(start, min(end, count))
    anchor = next((index for index in range(start, end + 1) if lines[index - 1].strip()), start)
    target = _indent(lines[anchor - 1])
    header = None
    for index in range(anchor, max(0, anchor - MAX_SCOPE_LINES), -1):
        line = lines[index - 1]
        if not line.strip() or not _SCOPE_HEADER_RE.match(line):
            continue
        if _indent(line) < target or index == anchor:
            header = index
            break
    if header is None:
        return None
    header_indent = _indent(lines[header - 1])
    last = max(end, header)
    index = last + 1
    while index <= count:
        line = lines[index - 1]
        if line.strip() and _indent(line) <= header_indent:
            if line.strip().startswith(("}", "end", ")", "]")):
                last = index
            break
        last = index
        index += 1
    while last > header and not lines[last - 1].strip():
        last -= 1
    if last - header + 1 > MAX_SCOPE_LINES:
        return None
    return header, last


def _merge(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


# --- bundles -----------------------------------------------------------------


@dataclass
class _BundleFile:
    change: FileChange
    diff: str
    hunks: list[tuple[int, int]]
    lines: list[str] | None
    ranges: list[tuple[int, int]] = field(default_factory=list)
    omitted: bool = False

    def excerpts(self) -> list[dict[str, Any]]:
        if self.lines is None or self.omitted:
            return []
        return [
            {"start_line": start, "lines": self.lines[start - 1 : end]}
            for start, end in self.ranges
            if start <= len(self.lines)
        ]

    def tokens(self) -> int:
        if self.omitted:
            return 0
        excerpt_text = "\n".join("\n".join(excerpt["lines"]) for excerpt in self.excerpts())
        return estimate_tokens(self.diff) + estimate_tokens(excerpt_text) + 16


@dataclass(frozen=True)
class Bundle:
    payload: dict[str, Any]
    message_redacted: str
    raw: bytes
    digest: str
    files: list[dict[str, Any]]
    skipped: list[dict[str, str]]
    redactions: RedactionCounter
    lines_added: int
    lines_removed: int
    token_estimate: int
    truncated: bool


def _context_ranges(item: _BundleFile, context: int) -> list[tuple[int, int]]:
    if item.lines is None:
        return []
    count = len(item.lines)
    return _merge(
        (max(1, start - context), min(count, end + context))
        for start, end in item.hunks
        if count
    )


def _fit_budget(items: list[_BundleFile], message_tokens: int, budget: int, context: int) -> bool:
    """Apply ±context, extend to scopes within budget, else shrink. True if truncated."""

    for item in items:
        item.ranges = _context_ranges(item, context)
    sizes = [item.tokens() for item in items]

    def total() -> int:
        return message_tokens + sum(sizes)

    truncated = False
    if items and total() > budget:
        for index, item in enumerate(items):
            item.ranges = _context_ranges(item, 0)
            sizes[index] = item.tokens()
        truncated = True
    while total() > budget and sum(not item.omitted for item in items) > 1:
        last = max(index for index, item in enumerate(items) if not item.omitted)
        items[last].omitted = True
        sizes[last] = 0
    if items and total() > budget:
        index = next(index for index, item in enumerate(items) if not item.omitted)
        survivor = items[index]
        survivor.ranges = []
        allowance = max(0, (budget - message_tokens - 16) * 3)
        encoded = survivor.diff.encode("utf-8")
        if len(encoded) > allowance:
            cut = encoded[:allowance].decode("utf-8", "ignore")
            cut = cut[: cut.rfind("\n") + 1] if "\n" in cut else ""
            survivor.diff = cut + "[TRUNCATED: diff exceeds project.context_token_budget]\n"
        sizes[index] = survivor.tokens()
    if not truncated:
        # Extend each hunk to its enclosing scope while the bundle still fits.
        for index, item in enumerate(items):
            if item.lines is None:
                continue
            for start, end in item.hunks:
                scope = scope_range(item.lines, start, end)
                if scope is None:
                    continue
                previous, previous_size = item.ranges, sizes[index]
                item.ranges = _merge([*item.ranges, scope])
                sizes[index] = item.tokens()
                if total() > budget:
                    item.ranges, sizes[index] = previous, previous_size
    return truncated


def build_bundle(
    repo: Path,
    *,
    base: str,
    head: str | None,
    snapshot_kind: str,
    base_sha: str | None,
    head_sha_value: str | None,
    changes: list[FileChange],
    untracked: list[str],
    commit_message: str,
    rules: PathRules,
    config: LearnLoopConfig,
) -> Bundle:
    counter = RedactionCounter()
    skipped: list[dict[str, str]] = []
    items: list[_BundleFile] = []
    for change in changes:
        reason = rules.exclusion(change.path) or (
            rules.exclusion(change.old_path) if change.old_path else None
        )
        if reason is None and change.binary:
            reason = "binary"
        if reason is None and len(items) >= MAX_FILES_PER_CAPTURE:
            reason = "file_limit"
        if reason is not None:
            skipped.append({"path": change.path, "reason": reason})
            continue
        diff = redact_diff(_file_diff(repo, base, head, change), counter)
        lines = None if change.status == "D" else _head_lines(repo, head, change.path)
        if lines is not None:
            lines = redact_lines(lines, counter)
        items.append(_BundleFile(change=change, diff=diff, hunks=parse_hunks(diff), lines=lines))
    for path in untracked:
        reason = rules.exclusion(path)
        candidate = repo / path
        if reason is None:
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    reason = "not_regular_file"
                elif candidate.stat().st_size > MAX_UNTRACKED_FILE_BYTES:
                    reason = "too_large"
            except OSError:
                reason = "unreadable"
        if reason is None and len(items) >= MAX_FILES_PER_CAPTURE:
            reason = "file_limit"
        if reason is None:
            lines = _head_lines(repo, None, path)
            if lines is None:
                reason = "binary"
        if reason is not None:
            skipped.append({"path": path, "reason": reason})
            continue
        diff = redact_diff(_untracked_diff(repo, path), counter)
        change = FileChange(path=path, old_path=None, status="A", added=len(lines or []), removed=0)
        items.append(
            _BundleFile(change=change, diff=diff, hunks=parse_hunks(diff), lines=redact_lines(lines or [], counter))
        )

    message = redact_text(commit_message.strip(), counter)
    budget = config.project.context_token_budget
    truncated = _fit_budget(items, estimate_tokens(message), budget, config.project.context_lines)
    files = []
    for item in items:
        files.append(
            {
                "path": item.change.path,
                "old_path": item.change.old_path,
                "status": item.change.status,
                "added": item.change.added,
                "removed": item.change.removed,
                "omitted": item.omitted,
                "diff": "" if item.omitted else item.diff,
                "excerpts": item.excerpts(),
            }
        )
    payload = {
        "format": BUNDLE_FORMAT,
        "snapshot": {"kind": snapshot_kind, "base_sha": base_sha, "head_sha": head_sha_value},
        "commit_message": strip_agent_trailers(message),
        "context_lines": config.project.context_lines,
        "truncated": truncated,
        "files": files,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    included = [item for item in items if not item.omitted]
    return Bundle(
        payload=payload,
        message_redacted=message,
        raw=raw,
        digest=asset_hash(raw),
        files=[
            {key: entry[key] for key in ("path", "old_path", "status", "added", "removed", "omitted")}
            for entry in files
        ],
        skipped=skipped,
        redactions=counter,
        lines_added=sum(item.change.added or 0 for item in included),
        lines_removed=sum(item.change.removed or 0 for item in included),
        token_estimate=estimate_tokens(message) + sum(item.tokens() for item in items),
        truncated=truncated,
    )


class BundleIntegrityError(RuntimeError):
    """A stored bundle is missing or no longer matches its content hash."""


def load_bundle(vault_root: Path, digest: str) -> dict[str, Any]:
    path = canonical_source_raw_path(Path(vault_root), digest)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BundleIntegrityError(f"stored diff bundle {digest} is missing") from exc
    if asset_hash(raw) != digest:
        raise BundleIntegrityError(f"stored diff bundle {digest} does not match its hash")
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("format") != BUNDLE_FORMAT:
        raise BundleIntegrityError(f"stored diff bundle {digest} has an unknown format")
    return payload


# --- enrollment ----------------------------------------------------------------


def _strip_credentials(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme and parts.hostname:
        # Drop any user:token@ userinfo, query and fragment.
        netloc = parts.hostname + (f":{parts.port}" if parts.port else "")
        return urlunsplit((parts.scheme, netloc, parts.path, "", ""))
    # scp-like ssh remotes (git@host:path) carry no secret beyond the user name.
    return url


def _remote_url(repo: Path) -> str | None:
    try:
        return _strip_credentials(git_text(repo, ["remote", "get-url", "origin"]).strip())
    except GitError:
        return None


def enroll_repo(
    vault_root: Path,
    config: LearnLoopConfig,
    repo_path: Path,
    *,
    clock: Clock | None = None,
    backfill_days: int | None = None,
    context_scope: str = "diff",
) -> tuple[dict[str, Any], bool]:
    if context_scope not in {"diff", "repo"}:
        raise ValueError("context scope must be 'diff' or 'repo'")
    top = repo_toplevel(Path(repo_path).expanduser())
    now = (clock or SystemClock()).now()
    days = config.project.enroll_backfill_days if backfill_days is None else backfill_days
    if days < 0:
        raise ValueError("--since-days must be zero or more")
    rules = load_path_rules(top)
    store = ProjectStore.for_vault(vault_root)
    return store.enroll_repo(
        {
            "id": new_ulid(),
            "path": str(top),
            "name": top.name,
            "remote_url": _remote_url(top),
            "enrolled_at": utc_now_iso(clock),
            "capture_since": utc_now_iso(FrozenClock(now - timedelta(days=days))),
            "context_scope": context_scope,
            "secret_pattern_version": SECRET_PATTERN_VERSION,
            "ignore_hash": rules.ignore_hash,
        }
    )


def find_repo(store: ProjectStore, repo: str | Path) -> dict[str, Any] | None:
    """An enrolled repo by id, path, or any path inside its work tree."""

    text = str(repo)
    by_id = store.repo(text)
    if by_id is not None:
        return by_id
    try:
        top = repo_toplevel(Path(text).expanduser())
    except GitError:
        top = Path(text).expanduser().resolve()
    return store.repo_by_path(str(top))


# --- capture -------------------------------------------------------------------


@dataclass(frozen=True)
class CaptureResult:
    status: str  # captured | duplicate | excluded | nothing_to_capture | refused | error
    diff_id: str | None = None
    detail: str | None = None
    probe_status: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "diff_id": self.diff_id,
            "detail": self.detail,
            "probe_status": self.probe_status,
        }


def _commit_info(repo: Path, sha: str) -> dict[str, Any]:
    fmt = "%H%x1f%P%x1f%cI%x1f%(trailers:only,unfold,separator=%x1e)%x1f%B"
    raw = git_text(repo, ["log", "-1", f"--format=format:{fmt}", sha, "--"])
    return _parse_commit_record(raw)


def _parse_commit_record(record: str) -> dict[str, Any]:
    sha, parents, committed_at, trailers, message = (record.split("\x1f", 4) + ["", "", "", ""])[:5]
    return {
        "sha": sha.strip(),
        "parents": parents.split(),
        "committed_at": committed_at.strip() or None,
        "trailers": parse_trailers(trailers),
        "message": message,
    }


def _store_capture(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    repo_row: dict[str, Any],
    bundle: Bundle,
    *,
    snapshot_kind: str,
    base_sha: str | None,
    head: str | None,
    patch: str | None,
    agent: str,
    agent_source: str,
    capture_timing: str,
    capture_source: str,
    trigger: str,
    committed_at: str | None,
    clock: Clock | None,
    rules: PathRules,
) -> CaptureResult:
    changed = bundle.lines_added + bundle.lines_removed
    included = [entry for entry in bundle.files if not entry["omitted"]]
    excluded_reason = None
    if not included:
        excluded_reason = "no_probeable_content"
    elif changed < config.project.min_diff_lines:
        excluded_reason = "trivial"
    store_original_bytes(Path(vault_root), bundle.digest, bundle.raw)
    row, created = store.insert_diff(
        {
            "id": new_ulid(),
            "repo_id": repo_row["id"],
            "snapshot_kind": snapshot_kind,
            "base_sha": base_sha,
            "head_sha": head,
            "patch_id": patch,
            "bundle_hash": bundle.digest,
            "files_json": json.dumps(bundle.files, sort_keys=True),
            "files_touched": len(bundle.files),
            "lines_added": bundle.lines_added,
            "lines_removed": bundle.lines_removed,
            "skipped_files_json": json.dumps(bundle.skipped, sort_keys=True),
            "agent": agent,
            "agent_source": agent_source,
            "capture_timing": capture_timing,
            "capture_source": capture_source,
            "capture_trigger": trigger,
            "commit_message": bundle.message_redacted,
            "committed_at": committed_at,
            "captured_at": utc_now_iso(clock),
            "redaction_count": bundle.redactions.total,
            "redactions_json": json.dumps(bundle.redactions.as_dict(), sort_keys=True),
            "token_estimate": bundle.token_estimate,
            "truncated": int(bundle.truncated),
            "excluded_reason": excluded_reason,
            "selection_seed": secrets.randbits(62),
            "probe_status": "excluded" if excluded_reason else "pending",
            "secret_pattern_version": SECRET_PATTERN_VERSION,
            "ignore_hash": rules.ignore_hash,
        }
    )
    if not created:
        return CaptureResult("duplicate", row["id"], "already captured", row["probe_status"])
    return CaptureResult(
        "excluded" if excluded_reason else "captured", row["id"], excluded_reason, row["probe_status"]
    )


def capture_commit(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    repo_row: dict[str, Any],
    sha: str,
    *,
    capture_source: str,
    trigger: str,
    clock: Clock | None = None,
    agent: str | None = None,
    agent_source: str | None = None,
    info: dict[str, Any] | None = None,
) -> CaptureResult:
    repo = Path(repo_row["path"])
    resolved = git_text(repo, ["rev-parse", "--verify", f"{sha}^{{commit}}"]).strip()
    existing = store.diff_for_commit(repo_row["id"], resolved)
    if existing is not None:
        return CaptureResult("duplicate", existing["id"], "already captured", existing["probe_status"])
    info = info if info is not None and info.get("sha") == resolved else _commit_info(repo, resolved)
    if len(info["parents"]) > 1:
        return CaptureResult("refused", None, "merge commits are not captured")
    trailer_agent = detect_agent(info["trailers"], info["message"])
    if agent is None:
        if trailer_agent is not None:
            agent, agent_source = trailer_agent, "trailer"
        else:
            agent, agent_source = "unknown", agent_source or "self_report"
    elif agent_source is None:
        agent_source = "flag"
    base = info["parents"][0] if info["parents"] else empty_tree_sha(repo)
    full_diff = run_git(repo, ["diff", *_DIFF_FLAGS, base, resolved])
    patch = patch_id(repo, full_diff)
    if patch is not None:
        twin = store.diff_with_patch_id(repo_row["id"], patch)
        if twin is not None:
            return CaptureResult("duplicate", twin["id"], "same patch already captured", twin["probe_status"])
    rules = load_path_rules(repo)
    bundle = build_bundle(
        repo,
        base=base,
        head=resolved,
        snapshot_kind="commit",
        base_sha=info["parents"][0] if info["parents"] else None,
        head_sha_value=resolved,
        changes=list_changes(repo, base, resolved),
        untracked=[],
        commit_message=info["message"],
        rules=rules,
        config=config,
    )
    result = _store_capture(
        store, vault_root, config, repo_row, bundle,
        snapshot_kind="commit",
        base_sha=info["parents"][0] if info["parents"] else None,
        head=resolved,
        patch=patch,
        agent=agent,
        agent_source=agent_source,
        capture_timing="post_commit",
        capture_source=capture_source,
        trigger=trigger,
        committed_at=info["committed_at"],
        clock=clock,
        rules=rules,
    )
    if result.diff_id is not None:
        store.resolve_unattributed(repo_row["id"], resolved, result.diff_id)
    return result


def capture_working_tree(
    store: ProjectStore,
    vault_root: Path,
    config: LearnLoopConfig,
    repo_row: dict[str, Any],
    *,
    clock: Clock | None = None,
    agent: str | None = None,
    include_untracked: bool = False,
    message: str = "",
) -> CaptureResult:
    """Capture uncommitted changes (staged and unstaged) against HEAD."""

    repo = Path(repo_row["path"])
    head = head_sha(repo)
    base = head or empty_tree_sha(repo)
    changes = list_changes(repo, base, None)
    untracked: list[str] = []
    if include_untracked:
        listed = run_git(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
        untracked = [path for path in listed.decode("utf-8", "surrogateescape").split("\0") if path]
    if not changes and not untracked:
        return CaptureResult("nothing_to_capture", None, "the working tree has no changes against HEAD")
    full_diff = run_git(repo, ["diff", *_DIFF_FLAGS, base])
    patch = patch_id(repo, full_diff) if not untracked else None
    rules = load_path_rules(repo)
    bundle = build_bundle(
        repo,
        base=base,
        head=None,
        snapshot_kind="working_tree",
        base_sha=head,
        head_sha_value=None,
        changes=changes,
        untracked=untracked,
        commit_message=message,
        rules=rules,
        config=config,
    )
    existing = store.diff_for_worktree_bundle(repo_row["id"], bundle.digest)
    if existing is not None:
        return CaptureResult("duplicate", existing["id"], "identical working tree already captured", existing["probe_status"])
    return _store_capture(
        store, vault_root, config, repo_row, bundle,
        snapshot_kind="working_tree",
        base_sha=head,
        head=head,
        patch=patch,
        agent=agent or "unknown",
        agent_source="flag" if agent else "self_report",
        capture_timing="pre_commit",
        capture_source="accept",
        trigger="manual",
        committed_at=None,
        clock=clock,
        rules=rules,
    )


# --- sweep ---------------------------------------------------------------------


def _agent_commits(repo: Path, since_iso: str) -> list[dict[str, Any]]:
    if head_sha(repo) is None:
        return []
    fmt = "%H%x1f%P%x1f%cI%x1f%(trailers:only,unfold,separator=%x1e)%x1f%B"
    raw = git_text(
        repo,
        [
            "log", "--branches", "HEAD", "--no-merges", f"--since={since_iso}",
            f"--max-count={SWEEP_MAX_COMMITS}", "-z", f"--format=format:{fmt}", "--",
        ],
    )
    commits = [_parse_commit_record(record) for record in raw.split("\0") if record.strip()]
    commits.reverse()  # oldest first
    return [commit for commit in commits if detect_agent(commit["trailers"], commit["message"])]


@dataclass
class SweepReport:
    trigger: str
    status: str = "ok"
    swept_at: str | None = None
    repos: list[dict[str, Any]] = field(default_factory=list)
    captured: int = 0
    duplicates: int = 0
    excluded: int = 0
    unattributed: int = 0
    pending_lines: int = 0
    pending_malformed: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "status": self.status,
            "swept_at": self.swept_at,
            "repos": self.repos,
            "captured": self.captured,
            "duplicates": self.duplicates,
            "excluded": self.excluded,
            "unattributed": self.unattributed,
            "pending_lines": self.pending_lines,
            "pending_malformed": self.pending_malformed,
            "errors": self.errors,
        }


def _tally(report: SweepReport, result: CaptureResult) -> None:
    if result.status == "captured":
        report.captured += 1
    elif result.status == "duplicate":
        report.duplicates += 1
    elif result.status == "excluded":
        report.excluded += 1


def _read_pending(vault_root: Path, store: ProjectStore) -> tuple[list[dict[str, Any]], int, int]:
    """New pending-list entries since the stored byte offset, and the new offset."""

    path = pending_path(vault_root)
    if not path.is_file():
        return [], 0, 0
    offset = int(store.meta("pending_offset") or 0)
    size = path.stat().st_size
    if size < offset:  # truncated or rotated by the owner
        offset = 0
    with path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read()
    complete = data[: data.rfind(b"\n") + 1] if b"\n" in data else b""
    entries: list[dict[str, Any]] = []
    malformed = 0
    for line in complete.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line.decode("utf-8"))
            if not isinstance(entry, dict) or not isinstance(entry.get("repo_id"), str) or not isinstance(entry.get("sha"), str):
                raise ValueError
            entries.append(entry)
        except ValueError:
            malformed += 1
    return entries, offset + len(complete), malformed


def sweep(
    vault_root: Path,
    config: LearnLoopConfig,
    *,
    clock: Clock | None = None,
    trigger: str = "manual",
    repo_ids: set[str] | None = None,
    busy_timeout_ms: int | None = None,
) -> SweepReport:
    """Capture every new agent-trailer commit in enrolled repos (git only)."""

    report = SweepReport(trigger=trigger, swept_at=utc_now_iso(clock))
    store = ProjectStore.for_vault(vault_root, busy_timeout_ms=busy_timeout_ms)
    repos = [repo for repo in store.repos(enabled_only=True) if repo_ids is None or repo["id"] in repo_ids]
    entries, new_offset, malformed = _read_pending(vault_root, store)
    report.pending_lines, report.pending_malformed = len(entries), malformed
    pending_by_repo: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        pending_by_repo.setdefault(entry["repo_id"], []).append(entry)
    for repo_row in repos:
        summary = {"repo_id": repo_row["id"], "name": repo_row["name"], "captured": 0, "error": None}
        repo = Path(repo_row["path"])
        try:
            if repo_toplevel(repo) != repo:
                raise GitError(f"{repo} is no longer the root of a git work tree")
            known = store.known_commit_shas(repo_row["id"])
            for commit in _agent_commits(repo, repo_row["capture_since"]):
                if commit["sha"] in known:
                    continue
                result = capture_commit(
                    store, vault_root, config, repo_row, commit["sha"],
                    capture_source="sweep", trigger=trigger, clock=clock, info=commit,
                )
                _tally(report, result)
                summary["captured"] += result.status in {"captured", "excluded"}
                known.add(commit["sha"])
            for entry in pending_by_repo.get(repo_row["id"], []):
                sha = entry["sha"]
                if sha in known:
                    continue
                try:
                    info = _commit_info(repo, sha)
                except GitError:
                    continue  # the commit was rewritten away; nothing to capture
                if detect_agent(info["trailers"], info["message"]) is None:
                    if len(info["parents"]) <= 1:
                        subject = redact_text((info["message"].splitlines() or [""])[0], RedactionCounter())
                        store.note_unattributed(
                            {
                                "repo_id": repo_row["id"],
                                "sha": info["sha"],
                                "subject": subject[:200],
                                "committed_at": info["committed_at"],
                                "seen_at": utc_now_iso(clock),
                            }
                        )
                        report.unattributed += 1
                    continue
                result = capture_commit(
                    store, vault_root, config, repo_row, info["sha"],
                    capture_source="pending_list", trigger=trigger, clock=clock, info=info,
                )
                _tally(report, result)
                summary["captured"] += result.status in {"captured", "excluded"}
                known.add(info["sha"])
            store.record_repo_sweep(repo_row["id"], swept_at=report.swept_at, error=None)
        except (GitError, OSError, ValueError) as exc:
            summary["error"] = str(exc)
            report.errors.append(f"{repo_row['name']}: {exc}")
            store.record_repo_sweep(repo_row["id"], swept_at=report.swept_at, error=str(exc)[:500])
        report.repos.append(summary)
    store.set_meta("pending_offset", str(new_offset))
    if report.errors:
        report.status = "partial"
    return report


def auto_sweep(
    vault_root: Path,
    config: LearnLoopConfig | None,
    *,
    clock: Clock | None = None,
    trigger: str = "app_start",
    min_interval_minutes: int | None = None,
    busy_timeout_ms: int = 1000,
) -> dict[str, Any]:
    """The automatic sweep at app start and plan build. Never raises (G1).

    Returns at once, creating nothing, when the kill switch is off or no repo
    was ever enrolled in this vault.
    """

    try:
        if config is not None and not config.project.auto_sweep:
            return {"trigger": trigger, "status": "disabled"}
        if not store_path(vault_root).is_file():
            return {"trigger": trigger, "status": "not_enrolled"}
        if config is None:
            from learnloop.config import load_config

            config = load_config(Path(vault_root) / "learnloop.toml")
        store = ProjectStore.for_vault(vault_root, busy_timeout_ms=busy_timeout_ms)
        if min_interval_minutes:
            last = parse_utc(store.meta("last_auto_sweep_at"))
            now = (clock or SystemClock()).now()
            if last is not None and now - last < timedelta(minutes=min_interval_minutes):
                return {"trigger": trigger, "status": "throttled"}
        report = sweep(vault_root, config, clock=clock, trigger=trigger, busy_timeout_ms=busy_timeout_ms)
        store.set_meta("last_auto_sweep_at", report.swept_at or utc_now_iso(clock))
        return report.as_dict()
    except Exception as exc:  # noqa: BLE001 - a sweep must never break its caller
        _LOG.warning("Project sweep (%s) failed: %s", trigger, exc)
        return {"trigger": trigger, "status": "error", "error": f"{type(exc).__name__}: {exc}"}


__all__ = [
    "AGENTS",
    "BUNDLE_FORMAT",
    "Bundle",
    "BundleIntegrityError",
    "CaptureResult",
    "FileChange",
    "SweepReport",
    "auto_sweep",
    "build_bundle",
    "capture_commit",
    "capture_working_tree",
    "detect_agent",
    "enroll_repo",
    "estimate_tokens",
    "find_repo",
    "list_changes",
    "load_bundle",
    "parse_hunks",
    "parse_trailers",
    "scope_range",
    "strip_agent_trailers",
    "sweep",
]
