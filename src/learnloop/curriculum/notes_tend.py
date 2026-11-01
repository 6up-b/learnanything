"""Deliverable curriculum C2: the one adapter to the learner's notes, the owner's ``tend``
(spec_deliverable_curriculum_v1 §10.1, §10.4).

LearnLoop never parses Org or Obsidian Markdown and never builds a note index: ``tend``
already chunks notes by heading, keys each chunk by path, heading path and content
hash, and searches them by words and meaning. This module calls it as a subprocess,
with a timeout, and nothing else:

* ``tend search -k K --json --local --notes-only [--words] -- QUERY`` (``--local``:
  carson's own index, never another machine's; ``--notes-only``: tend leaves out docs
  in project repositories). The JSON is ``{"results": [{path, title, heading, line,
  snippet, score, via, hash, source, mtime, ...}], "warning": ...}`` (tend's
  ``cli._print_hits``; ``search.Hit``). ``notes.tend.lexical_only`` adds ``--words``:
  words only, so no query leaves the machine (tend's meaning search embeds the query
  through Voyage, its documented choice; LearnLoop's queries are LO and section
  titles, never a passage or a note).
* ``tend serve``'s ``read`` op (``{"op": "read", "path": P, "id": N}`` per stdin line
  answers ``{"text": <the whole file>, "title": ..., "id": N}``, or ``{"error": ...}``;
  tend's ``cli.serve`` / ``remote.read_indexed``: only files its index knows, never a
  folder tend marks private). LearnLoop keeps the hit's heading section: from the hit's
  line up to the next heading of any level (tend's own chunk boundary). When tend
  answers a read with an error (a private note, a file it no longer indexes) the note
  is dropped. Only when ``tend serve`` cannot answer at all (it would not start, timed
  out, or does not know the op) is the section read from the file itself, and only
  inside the allowlist.

**The allowlist** (``notes.tend.paths``): the folders of tend's corpus LearnLoop may
use (default: grove notes, Quicknote, the Obsidian vault and ``~/org``; project
repositories are excluded). A hit outside it is dropped here, before anything is
returned, stored or sent. **tend absent** (no executable: a contributor's machine)
means the notes features are hidden: :func:`executable` is None.

``LEARNLOOP_NOTES_TEND`` overrides the executable: ``off`` means absent (the test
suite sets it, so no test can reach the owner's real ``tend``), a path names one (the
tests' fake).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ENV_BINARY = "LEARNLOOP_NOTES_TEND"

#: The origins a snapshot may carry (``phone_photo`` comes with image transcription, §13).
ORIGINS: tuple[str, ...] = ("tend", "pocket_notes")
#: ``keep`` (a prompt bound, never a model parameter): one note's text at most, as stored
#: and as the judge reads it. Tend's own sections are cut near 6000 characters; this keeps
#: a candidate list inside one prompt.
NOTE_CHARS = 3000
#: ``keep`` (a guardrail): the most one file read through the fallback may hold.
FALLBACK_MAX_BYTES = 2_000_000

_ORG_HEADING = re.compile(r"^\*+\s")
_MD_HEADING = re.compile(r"^#{1,6}\s")
_MD_FENCE = re.compile(r"^\s*(```|~~~)")
_ORG_BLOCK = re.compile(r"^\s*#\+(begin|end)_\w+", re.I)


class TendUnavailable(Exception):
    """tend could not answer (absent, timed out, unreadable output); ``reason`` names it."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class TendSettings:
    binary: str
    roots: tuple[Path, ...]
    pocket_roots: tuple[Path, ...]
    lexical_only: bool
    timeout: float
    k: int


@dataclass(frozen=True)
class NoteHit:
    """One heading section tend found, inside the allowlist."""

    path: str
    heading_path: str
    title: str
    line: int
    snippet: str
    content_hash: str
    mtime: float
    via: str
    origin: str

    @property
    def heading(self) -> str:
        return self.heading_path.split(" > ")[-1] if self.heading_path else ""

    @property
    def note_key(self) -> str:
        return note_key(self.path, self.heading_path)

    @property
    def captured_on(self) -> str | None:
        """The note's date as tend reports it (the file's last change), a local date."""

        if not self.mtime or self.mtime <= 0:
            return None
        try:
            return datetime.fromtimestamp(float(self.mtime)).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return None

    def view(self) -> dict[str, Any]:
        return {"note_key": self.note_key, "path": self.path, "title": self.title, "heading": self.heading,
                "heading_path": self.heading_path, "line": self.line, "snippet": self.snippet,
                "captured_on": self.captured_on, "origin": self.origin}


@dataclass(frozen=True)
class NoteText:
    hit: NoteHit
    text: str
    truncated: bool
    #: tend (its read op) | file (the fallback, inside the allowlist)
    read_via: str


def note_key(path: str, heading_path: str) -> str:
    return f"{path}#{heading_path}"


def _expand(value: str) -> Path:
    return Path(os.path.realpath(os.path.expanduser(str(value))))


def executable(config: Any) -> str | None:
    """The tend executable LearnLoop may run, or None (absent: the notes features hide)."""

    override = os.environ.get(ENV_BINARY)
    if override is not None:
        value = override.strip()
        if not value or value.lower() == "off":
            return None
        return value if os.path.isfile(value) and os.access(value, os.X_OK) else None
    name = str(config.notes.tend.binary or "").strip()
    if not name:
        return None
    if os.sep in name:
        path = os.path.expanduser(name)
        return path if os.path.isfile(path) and os.access(path, os.X_OK) else None
    return shutil.which(name)


def settings(config: Any) -> TendSettings | None:
    """The adapter's settings, or None when tend is absent."""

    binary = executable(config)
    if binary is None:
        return None
    tend = config.notes.tend
    return TendSettings(binary=binary, roots=tuple(_expand(p) for p in tend.paths),
                        pocket_roots=tuple(_expand(p) for p in tend.pocket_notes_paths),
                        lexical_only=bool(tend.lexical_only), timeout=float(tend.timeout_seconds), k=int(tend.k))


def _under(path: Path, roots: Iterable[Path]) -> bool:
    return any(path == root or path.is_relative_to(root) for root in roots)


def allowed(path: str, roots: Sequence[Path]) -> bool:
    """Is ``path`` (a local, absolute path) inside the allowlist? Anything else (a
    remote machine's prefixed path, a relative path, a folder not listed) is not."""

    if not path or not os.path.isabs(path):
        return False
    try:
        resolved = Path(os.path.realpath(path))
    except (OSError, ValueError):
        return False
    return _under(resolved, roots)


def origin_of(path: str, pocket_roots: Sequence[Path]) -> str:
    try:
        resolved = Path(os.path.realpath(path))
    except (OSError, ValueError):
        return "tend"
    return "pocket_notes" if _under(resolved, pocket_roots) else "tend"


def _hit(row: Mapping[str, Any], config: TendSettings) -> NoteHit | None:
    """One result row as a hit, or None (malformed, another machine's, or outside the allowlist)."""

    try:
        path = str(row.get("path") or "")
        source = str(row.get("source") or "local")
        line = int(row.get("line") or 0)
    except (TypeError, ValueError):
        return None
    if source != "local" or line < 1 or not allowed(path, config.roots):
        return None
    resolved = os.path.realpath(path)
    try:
        mtime = float(row.get("mtime") or 0.0)
    except (TypeError, ValueError):
        mtime = 0.0
    return NoteHit(path=resolved, heading_path=" ".join(str(row.get("heading") or "").split()),
                   title=" ".join(str(row.get("title") or Path(resolved).stem).split()), line=line,
                   snippet=" ".join(str(row.get("snippet") or "").split())[:400],
                   content_hash=str(row.get("hash") or ""), mtime=mtime, via=str(row.get("via") or ""),
                   origin=origin_of(resolved, config.pocket_roots))


def search(config: TendSettings, query: str, *, k: int | None = None) -> list[NoteHit]:
    """``tend search`` for ``query``: the hits inside the allowlist, in tend's order,
    one per heading section. Raises :class:`TendUnavailable` when tend cannot answer."""

    words = " ".join(str(query or "").split())
    if not words:
        return []
    command = [config.binary, "search", "-k", str(int(k or config.k)), "--json", "--local", "--notes-only"]
    if config.lexical_only:
        command.append("--words")
    command += ["--", words]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=config.timeout,
                              stdin=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired as exc:
        raise TendUnavailable("timeout", "Your notes didn't answer in time.") from exc
    except OSError as exc:
        raise TendUnavailable("absent", "LearnLoop couldn't run tend to search your notes.") from exc
    if done.returncode != 0:
        raise TendUnavailable("failed", "tend couldn't search your notes just now.")
    try:
        payload = json.loads(done.stdout or "{}")
        rows = payload.get("results") or []
    except (ValueError, AttributeError) as exc:
        raise TendUnavailable("unreadable", "tend's answer couldn't be read.") from exc
    out: list[NoteHit] = []
    seen: set[str] = set()
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        hit = _hit(row, config)
        if hit is None or hit.note_key in seen:
            continue
        seen.add(hit.note_key)
        out.append(hit)
    return out


def slice_section(text: str, line: int, *, org: bool) -> str:
    """The heading section starting at ``line`` (1-based): up to the next heading of any
    level, headings inside code blocks ignored (tend's own chunk boundary)."""

    lines = text.splitlines()
    start = max(0, int(line) - 1)
    if start >= len(lines):
        return ""
    out = [lines[start]]
    in_block = False
    for current in lines[start + 1:]:
        if org:
            if _ORG_BLOCK.match(current):
                in_block = current.lstrip()[2:7].lower() == "begin"
            elif not in_block and _ORG_HEADING.match(current):
                break
        else:
            if _MD_FENCE.match(current):
                in_block = not in_block
            elif not in_block and _MD_HEADING.match(current):
                break
        out.append(current)
    return "\n".join(out).strip()


def _bounded(text: str) -> tuple[str, bool]:
    value = text.strip()
    if len(value) <= NOTE_CHARS:
        return value, False
    return value[: NOTE_CHARS - 1].rstrip() + "…", True


def _serve_reads(config: TendSettings, paths: Sequence[str]) -> dict[str, dict[str, Any]] | None:
    """``tend serve``'s read op for each path: the answers by path, or None when tend
    could not answer at all (the fallback's only trigger)."""

    requests = "".join(json.dumps({"op": "read", "path": path, "id": index}) + "\n"
                       for index, path in enumerate(paths))
    try:
        done = subprocess.run([config.binary, "serve"], input=requests, capture_output=True, text=True,
                              timeout=config.timeout, check=False)
    except (subprocess.TimeoutExpired, OSError):
        return None
    answers: dict[str, dict[str, Any]] = {}
    for raw in (done.stdout or "").splitlines():
        try:
            answer = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(answer, dict) or not isinstance(answer.get("id"), int):
            continue
        index = answer["id"]
        if 0 <= index < len(paths):
            answers[paths[index]] = answer
    if not answers:
        return None
    if all(str(answer.get("error") or "").startswith("unknown op") for answer in answers.values()):
        return None  # this tend has no read op
    return answers


def _read_file(path: str, roots: Sequence[Path]) -> str | None:
    if not allowed(path, roots):
        return None
    try:
        file = Path(os.path.realpath(path))
        if not file.is_file() or file.stat().st_size > FALLBACK_MAX_BYTES:
            return None
        return file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def read_sections(config: TendSettings, hits: Sequence[NoteHit]) -> dict[str, NoteText]:
    """The text of each hit's heading section, by note key, bounded per note
    (:data:`NOTE_CHARS`). A note tend refuses to read is dropped; the file itself is read
    only when ``tend serve`` cannot answer at all, and only inside the allowlist."""

    wanted = [hit for hit in hits if allowed(hit.path, config.roots)]
    paths = list(dict.fromkeys(hit.path for hit in wanted))
    if not paths:
        return {}
    answers = _serve_reads(config, paths)
    texts: dict[str, tuple[str, str]] = {}
    for path in paths:
        if answers is not None:
            answer = answers.get(path)
            if answer is None or "error" in answer or not isinstance(answer.get("text"), str):
                continue  # tend refused (a private note, an unindexed file) or said nothing: dropped
            texts[path] = (str(answer["text"]), "tend")
        else:
            body = _read_file(path, config.roots)
            if body is not None:
                texts[path] = (body, "file")
    out: dict[str, NoteText] = {}
    for hit in wanted:
        found = texts.get(hit.path)
        if found is None or hit.note_key in out:
            continue
        section = slice_section(found[0], hit.line, org=hit.path.endswith(".org"))
        if not section:
            continue
        text, truncated = _bounded(section)
        out[hit.note_key] = NoteText(hit=hit, text=text, truncated=truncated, read_via=found[1])
    return out


__all__ = [
    "ENV_BINARY",
    "NOTE_CHARS",
    "ORIGINS",
    "NoteHit",
    "NoteText",
    "TendSettings",
    "TendUnavailable",
    "allowed",
    "executable",
    "note_key",
    "origin_of",
    "read_sections",
    "search",
    "settings",
    "slice_section",
]
