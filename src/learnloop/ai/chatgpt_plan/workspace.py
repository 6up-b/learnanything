"""A read-only workspace that LearnLoop serves to a ``chatgpt_plan`` turn.

Codex reads a prepared directory with its own shell tools inside a sandbox, and
reports afterwards (best effort) what it ran. A Responses request on the
ChatGPT plan has no file access at all, so LearnLoop serves the directory
itself, one of two ways (the profile's ``workspace_mode``):

* ``tools`` (the default): Responses function calling. The plan route takes
  function tools grouped in a namespace (developers.openai.com/siwc,
  preview-limitations, re-read 2026-10-15), so the request declares one
  namespace, ``workspace``, with two functions: ``list_entries`` (a directory's
  names) and ``read_entry`` (a file's text, by line range). LearnLoop runs each
  call against an index of the directory taken when the turn starts, and
  records every file it serves AS THE CALL RUNS, before the next request
  carries it to the model. Nothing else is reachable: no shell, search, path
  outside the index, symlink or network.
* ``inline`` (deterministic "explicit context"): every file is sent in the
  request itself, and every file is recorded as served.

Either way the record of what the model was given is exact by construction:
:meth:`ServedWorkspace.activity` lists the served files' paths relative to the
workspace root, which is what a snapshot diagnosis records as its inputs
(``workspace_activity``; diagnosis input provenance maps each path to the
export entry it serves). A listing serves names only and is not an input; a
refused call (an unknown path, a bad argument, an exhausted budget) serves
nothing. A file is recorded as served when LearnLoop hands it out, even if the
request that would carry it then fails: over-reporting what the model may have
read is safe, under-reporting is not.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

#: The namespace the workspace functions are declared in (and called by).
NAMESPACE = "workspace"
LIST_ENTRIES = "list_entries"
READ_ENTRY = "read_entry"
FUNCTIONS = (LIST_ENTRIES, READ_ENTRY)
#: Names one listing returns at most; a longer directory says how many more.
LIST_LIMIT = 2_000

INSTRUCTIONS_TOOLS = (
    "A read-only workspace is attached to this request. Its files are served only through the "
    f"{NAMESPACE} functions: {NAMESPACE}.{LIST_ENTRIES} lists a directory and {NAMESPACE}.{READ_ENTRY} "
    "returns a file's text (by line range for a long file). Paths are relative to the workspace root, "
    "for example INDEX.md. Wherever the task speaks of your working directory, files, listing, searching "
    "or opening, use these functions: there is no shell, search or network. Call several functions in one "
    "turn when that helps. When you have read enough, answer with the final JSON only."
)
INSTRUCTIONS_INLINE = (
    "A read-only workspace is attached to this request: every one of its files is included below the task "
    "as a <workspace_file path=\"...\"> block, with paths relative to the workspace root. Wherever the task "
    "speaks of your working directory, files, listing, searching or opening, read those blocks: they are "
    "the whole workspace, and there is no shell, search or network."
)


class WorkspaceTooLarge(ValueError):
    """The workspace does not fit the inline budget (``max_workspace_chars``)."""


@dataclass(frozen=True)
class ServedEntry:
    """One file (or a line range of it) LearnLoop handed to the model."""

    path: str
    sha256: str
    start_line: int
    end_line: int
    total_lines: int
    chars: int
    call_id: str | None
    round: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CallRecord:
    """Every workspace call, served or refused, in order (for the receipt)."""

    round: int
    call_id: str | None
    name: str
    arguments: str
    outcome: str  # served | listed | refused
    path: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def _relative_files(root: Path) -> dict[str, Path]:
    """Every regular file under ``root`` (no symlink is followed or served), by POSIX path."""

    files: dict[str, Path] = {}
    for directory, subdirectories, names in os.walk(root, followlinks=False):
        here = Path(directory)
        subdirectories[:] = sorted(name for name in subdirectories if not (here / name).is_symlink())
        for name in sorted(names):
            path = here / name
            if path.is_symlink() or not path.is_file():
                continue
            files[path.relative_to(root).as_posix()] = path
    return dict(sorted(files.items()))


def normalize_path(value: Any) -> str | None:
    """A requested path as an index key, or None when it can name nothing in the workspace.

    The workspace is presented rooted at ``/``: a leading ``/`` or ``./`` is
    dropped. ``..`` is refused outright (it never reaches the index lookup).
    """

    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or "\x00" in text or "\\" in text:
        return None
    parts = [part for part in PurePosixPath(text).parts if part not in ("/", ".", "")]
    if any(part == ".." for part in parts):
        return None
    return "/".join(parts)


class ServedWorkspace:
    """The index of one prepared directory and the record of what was served from it."""

    def __init__(self, root: Path, *, max_entry_chars: int, max_workspace_chars: int) -> None:
        root = Path(root)
        if not root.is_dir():
            raise NotADirectoryError(f"Read-only workspace {root} is not a directory.")
        self.root = root.resolve()
        self.files = _relative_files(self.root)
        self.max_entry_chars = max(1, int(max_entry_chars))
        self.max_workspace_chars = max(1, int(max_workspace_chars))
        self.served: list[ServedEntry] = []
        self.calls: list[CallRecord] = []
        self.served_chars = 0
        #: Set when an inline turn's files exceeded the inline limit and this
        #: workspace serves them by function calls instead (plan-first T1).
        self.overflowed_inline = False
        self._texts: dict[str, str] = {}

    # -- the request side ---------------------------------------------------------

    @staticmethod
    def namespace_tool() -> dict[str, Any]:
        """The one tool the request declares: a namespace of two strict functions."""

        return {
            "type": "namespace",
            "name": NAMESPACE,
            "description": "Read-only files prepared for this request and served by LearnLoop.",
            "tools": [
                {
                    "type": "function",
                    "name": LIST_ENTRIES,
                    "description": (
                        "List one directory of the workspace: its files (with their sizes in bytes) and "
                        "its subdirectories (with how many files each holds). Use null or \"\" for the root."
                    ),
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": ["string", "null"],
                                "description": "A directory path relative to the workspace root, or null for the root.",
                            },
                        },
                        "required": ["directory"],
                        "additionalProperties": False,
                    },
                },
                {
                    "type": "function",
                    "name": READ_ENTRY,
                    "description": (
                        "Return the text of one workspace file. A long file is returned in parts: pass "
                        "start_line (1-based) to continue where a previous part stopped."
                    ),
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "A file path relative to the workspace root, for example INDEX.md.",
                            },
                            "start_line": {
                                "type": ["integer", "null"],
                                "description": "The first line to return (1-based); null for the start of the file.",
                            },
                            "max_lines": {
                                "type": ["integer", "null"],
                                "description": "How many lines to return at most; null for as many as fit.",
                            },
                        },
                        "required": ["path", "start_line", "max_lines"],
                        "additionalProperties": False,
                    },
                },
            ],
        }

    def inline_block(self) -> str:
        """Every file, for ``workspace_mode = "inline"``; each recorded as served.

        Refused (:class:`WorkspaceTooLarge`) when the files exceed
        ``max_workspace_chars``: the workspace is never cut short silently.
        """

        texts = {path: self._text(path) for path in self.files}
        total = sum(len(text) for text in texts.values())
        if total > self.max_workspace_chars:
            raise WorkspaceTooLarge(
                f"The workspace holds {total} characters in {len(texts)} files, over max_workspace_chars "
                f"({self.max_workspace_chars}); raise it or use workspace_mode = \"tools\"."
            )
        blocks = []
        for path, text in texts.items():
            lines = text.splitlines()
            self._record_served(path, text, 1, len(lines), len(lines), len(text), call_id=None, round_index=0)
            blocks.append(f'<workspace_file path="{path}">\n{text}\n</workspace_file>')
        return "\n\n".join(blocks)

    # -- the call side -------------------------------------------------------------

    def call(self, name: str, arguments: str, *, call_id: str | None, round_index: int) -> str:
        """Run one function call; returns its output text. Never raises on model input."""

        qualifier, _dot, function = (name if isinstance(name, str) else "").rpartition(".")
        if qualifier and qualifier != NAMESPACE:
            function = ""
        try:
            parsed = json.loads(arguments) if isinstance(arguments, str) and arguments.strip() else {}
        except ValueError:
            return self._refuse(round_index, call_id, function or str(name), arguments,
                                "the arguments are not valid JSON")
        if not isinstance(parsed, Mapping):
            return self._refuse(round_index, call_id, function, arguments, "the arguments must be a JSON object")
        if function == LIST_ENTRIES:
            return self._list(parsed, arguments, call_id=call_id, round_index=round_index)
        if function == READ_ENTRY:
            return self._read(parsed, arguments, call_id=call_id, round_index=round_index)
        return self._refuse(round_index, call_id, str(name), arguments,
                            f"there is no function {name!r}; use {NAMESPACE}.{LIST_ENTRIES} or {NAMESPACE}.{READ_ENTRY}")

    def refuse(self, name: str, arguments: str, *, call_id: str | None, round_index: int, reason: str) -> str:
        """Answer a call without running it (serves nothing); the refusal is recorded."""

        return self._refuse(round_index, call_id, name, arguments, reason)

    def refuse_exhausted(self, name: str, arguments: str, *, call_id: str | None, round_index: int) -> str:
        """The answer to a call made after the tool-round budget is spent (serves nothing)."""

        return self._refuse(round_index, call_id, name, arguments,
                            "the workspace budget for this request is spent; answer now with the final JSON "
                            "from what you have already read")

    def _list(self, arguments: Mapping[str, Any], raw: str, *, call_id: str | None, round_index: int) -> str:
        requested = arguments.get("directory")
        directory = "" if requested in (None, "") else normalize_path(requested)
        if directory is None:
            return self._refuse(round_index, call_id, LIST_ENTRIES, raw, f"{requested!r} is not a workspace path")
        prefix = f"{directory}/" if directory else ""
        if directory and directory in self.files:
            return self._refuse(round_index, call_id, LIST_ENTRIES, raw,
                                f"{directory} is a file; read it with {NAMESPACE}.{READ_ENTRY}")
        files: list[str] = []
        subdirectories: dict[str, int] = {}
        for path in self.files:
            if not path.startswith(prefix):
                continue
            rest = path[len(prefix):]
            head, separator, _tail = rest.partition("/")
            if separator:
                subdirectories[head] = subdirectories.get(head, 0) + 1
            else:
                files.append(path)
        if directory and not files and not subdirectories:
            return self._refuse(round_index, call_id, LIST_ENTRIES, raw, f"there is no directory {directory!r}")
        lines = [f"directory: {directory or '/'}"]
        names = [f"{prefix}{name}/ ({count} files)" for name, count in sorted(subdirectories.items())]
        names += [f"{path} ({self.files[path].stat().st_size} bytes)" for path in files]
        lines += names[:LIST_LIMIT]
        if len(names) > LIST_LIMIT:
            lines.append(f"... {len(names) - LIST_LIMIT} more; list a subdirectory to see them")
        self.calls.append(CallRecord(round_index, call_id, LIST_ENTRIES, raw, "listed", path=directory or "/"))
        return "\n".join(lines)

    def _read(self, arguments: Mapping[str, Any], raw: str, *, call_id: str | None, round_index: int) -> str:
        path = normalize_path(arguments.get("path"))
        if path is None or path not in self.files:
            hint = f"{arguments.get('path')!r} is not a workspace file"
            if path is not None and any(name.startswith(f"{path}/") for name in self.files):
                hint = f"{path} is a directory; list it with {NAMESPACE}.{LIST_ENTRIES}"
            return self._refuse(round_index, call_id, READ_ENTRY, raw, hint)
        start = arguments.get("start_line")
        limit = arguments.get("max_lines")
        if start is not None and (isinstance(start, bool) or not isinstance(start, int) or start < 1):
            return self._refuse(round_index, call_id, READ_ENTRY, raw, "start_line must be a positive integer or null")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
            return self._refuse(round_index, call_id, READ_ENTRY, raw, "max_lines must be a positive integer or null")
        text = self._text(path)
        lines = text.splitlines()
        first = int(start or 1)
        if lines and first > len(lines):
            return self._refuse(round_index, call_id, READ_ENTRY, raw,
                                f"{path} has {len(lines)} lines; start_line {first} is past its end")
        remaining = self.max_workspace_chars - self.served_chars
        if remaining <= 0:
            return self._refuse(round_index, call_id, READ_ENTRY, raw,
                                "the workspace read budget for this request is spent; answer from what you have read")
        allowance = min(self.max_entry_chars, remaining)
        chosen: list[str] = []
        size = 0
        for line in lines[first - 1:]:
            if limit is not None and len(chosen) >= limit:
                break
            if chosen and size + len(line) + 1 > allowance:
                break
            chosen.append(line if len(line) <= allowance else line[:allowance])
            size += len(chosen[-1]) + 1
        last = first + len(chosen) - 1 if chosen else first - 1
        body = "\n".join(chosen)
        # A line longer than the allowance is served cut, and says so.
        cut = bool(chosen) and len(lines[first - 1]) > len(chosen[0])
        self._record_served(path, text, first, last, len(lines), len(body), call_id=call_id, round_index=round_index)
        self.calls.append(CallRecord(round_index, call_id, READ_ENTRY, raw, "served", path=path,
                                     detail=f"lines {first}-{last} of {len(lines)}" + (" (cut)" if cut else "")))
        header = f"path: {path} (lines {first}-{last} of {len(lines)})"
        if cut:
            header += f"; line {first} is cut to its first {len(chosen[0])} characters"
        if last < len(lines):
            header += f"; more follows: call {NAMESPACE}.{READ_ENTRY} with start_line={last + 1}"
        return f"{header}\n{body}"

    def _refuse(self, round_index: int, call_id: str | None, name: str, raw: Any, reason: str) -> str:
        self.calls.append(CallRecord(round_index, call_id, name, raw if isinstance(raw, str) else json.dumps(raw),
                                     "refused", detail=reason))
        return f"error: {reason}"

    def _text(self, path: str) -> str:
        text = self._texts.get(path)
        if text is None:
            text = self.files[path].read_bytes().decode("utf-8", errors="replace")
            self._texts[path] = text
        return text

    def _record_served(self, path: str, text: str, first: int, last: int, total: int, chars: int, *,
                       call_id: str | None, round_index: int) -> None:
        self.served.append(ServedEntry(
            path=path, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), start_line=first,
            end_line=last, total_lines=total, chars=chars, call_id=call_id, round=round_index,
        ))
        self.served_chars += chars

    # -- the record ------------------------------------------------------------------

    def activity(self) -> list[str]:
        """Every served file's path, once each, in the order first served."""

        return list(dict.fromkeys(entry.path for entry in self.served))

    def summary(self) -> dict[str, Any]:
        return {
            "files": len(self.files),
            "served_files": len(self.activity()),
            "served_chars": self.served_chars,
            "calls": len(self.calls),
            "refused": sum(1 for call in self.calls if call.outcome == "refused"),
        }


__all__ = [
    "CallRecord",
    "FUNCTIONS",
    "INSTRUCTIONS_INLINE",
    "INSTRUCTIONS_TOOLS",
    "LIST_ENTRIES",
    "NAMESPACE",
    "READ_ENTRY",
    "ServedEntry",
    "ServedWorkspace",
    "WorkspaceTooLarge",
    "normalize_path",
]
