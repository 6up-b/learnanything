"""Secret filtering before anything is stored or sent (spec §4, gate G2).

Two layers:

- **Paths.** Files matching the secret patterns, the repo's ``.learnloopignore``
  or the noise list (lockfiles, minified bundles) are left out entirely: their
  names stay in the local skip list, their contents never enter a diff,
  excerpt, store row or prompt.
- **Lines.** Every remaining diff line, context line and commit-message line is
  scanned for known key prefixes, PEM blocks, credential assignments and long
  high-entropy tokens. A matching line is replaced whole by
  ``[REDACTED:<kind>]``. Storage and model calls only ever read the redacted
  text, so the two cannot disagree.

The scanner is deliberately conservative: a false positive costs a line of
context, a false negative leaks a credential.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SECRET_PATTERN_VERSION = "project-secrets-v1"

SECRET_PATH_PATTERNS: tuple[str, ...] = (
    ".env*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "*.p12",
    "*credential*",
    "*secret*",
)
# Not secrets, but never worth model context.
NOISE_PATH_PATTERNS: tuple[str, ...] = (
    "*.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "*.min.js",
    "*.min.css",
    "*.map",
)
IGNORE_FILE_NAME = ".learnloopignore"

REDACTED = "[REDACTED:{kind}]"

_PREFIX_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("pem_block", re.compile(r"-----BEGIN")),
    ("api_key_sk", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{16,}")),
    ("aws_access_key", re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}(?![A-Z0-9])")),
    ("github_token", re.compile(r"(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("slack_token", re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("google_api_key", re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{35}")),
)
_CREDENTIAL_NAME = r"(?:pass(?:word|wd)?|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|auth[_-]?token)"
_ASSIGNMENT_RULES: tuple[re.Pattern[str], ...] = (
    # A quoted literal assigned to a credential-named key, in any language.
    re.compile(
        rf"(?i){_CREDENTIAL_NAME}[A-Za-z0-9_\-]*[\"']?\s*(?::|=|:=|=>)\s*[bru]?[\"'][^\"'\s]{{8,}}[\"']"
    ),
    # Env-file style: UPPER_SNAKE names, unquoted values.
    re.compile(
        r"^\s*(?:export\s+)?[A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|APIKEY|ACCESS_KEY|PRIVATE_KEY)[A-Z0-9_]*\s*[=:]\s*\S{8,}"
    ),
)
_TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_\-]{32,}")
_HEX_RE = re.compile(r"[0-9a-fA-F]+")
_PEM_END = re.compile(r"-----END")


@dataclass
class RedactionCounter:
    """Per-kind counts of replaced lines for one capture."""

    counts: Counter = field(default_factory=Counter)

    def add(self, kind: str) -> None:
        self.counts[kind] += 1

    @property
    def total(self) -> int:
        return int(sum(self.counts.values()))

    def as_dict(self) -> dict[str, int]:
        return {kind: int(count) for kind, count in sorted(self.counts.items())}


def _entropy(token: str) -> float:
    counts = Counter(token)
    size = len(token)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def _high_entropy(token: str) -> bool:
    if _HEX_RE.fullmatch(token):
        # Commit ids and content digests are everywhere in code; hex keys are
        # caught by the assignment rules instead.
        return False
    digits = sum(character.isdigit() for character in token)
    if digits < 3:
        return False
    classes = (
        any(character.islower() for character in token)
        + any(character.isupper() for character in token)
        + (digits > 0)
        + any(character in "+/" for character in token)
    )
    return classes >= 3 and _entropy(token) >= 4.3


def scan_line(text: str) -> str | None:
    """The redaction kind for one line of text, or ``None`` when it is clean."""

    for kind, rule in _PREFIX_RULES:
        if rule.search(text):
            return kind
    for rule in _ASSIGNMENT_RULES:
        if rule.search(text):
            return "credential_assignment"
    for match in _TOKEN_RE.finditer(text):
        if _high_entropy(match.group(0)):
            return "high_entropy"
    return None


class _LineRedactor:
    """Stateful so every line of a PEM block is redacted, not only BEGIN."""

    def __init__(self, counter: RedactionCounter) -> None:
        self.counter = counter
        self.in_pem = False

    def redact(self, content: str) -> str | None:
        """Return the replacement for ``content`` or ``None`` to keep it."""

        if self.in_pem:
            if _PEM_END.search(content):
                self.in_pem = False
            self.counter.add("pem_block")
            return REDACTED.format(kind="pem_block")
        kind = scan_line(content)
        if kind is None:
            return None
        if kind == "pem_block" and not _PEM_END.search(content.split("-----BEGIN", 1)[1]):
            self.in_pem = True
        self.counter.add(kind)
        return REDACTED.format(kind=kind)


def redact_text(text: str, counter: RedactionCounter) -> str:
    """Redact free text (a commit message, a file excerpt) line by line."""

    redactor = _LineRedactor(counter)
    lines = text.split("\n")
    return "\n".join(
        replacement if (replacement := redactor.redact(line)) is not None else line
        for line in lines
    )


def redact_lines(lines: list[str], counter: RedactionCounter) -> list[str]:
    redactor = _LineRedactor(counter)
    return [
        replacement if (replacement := redactor.redact(line)) is not None else line
        for line in lines
    ]


def redact_diff(diff_text: str, counter: RedactionCounter) -> str:
    """Redact the content lines of a unified diff, keeping its +/-/space markers.

    Header lines (``diff --git``, ``index``, ``---``/``+++``, ``@@``) carry no
    file content and are kept so hunks still parse.
    """

    output: list[str] = []
    in_hunk = False
    redactor = _LineRedactor(counter)
    for line in diff_text.split("\n"):
        if line.startswith("diff --git ") or line.startswith("diff --cc "):
            in_hunk = False
            redactor = _LineRedactor(counter)
            output.append(line)
            continue
        if line.startswith("@@"):
            in_hunk = True
            output.append(line)
            continue
        if in_hunk and line[:1] in {"+", "-", " "}:
            replacement = redactor.redact(line[1:])
            output.append(line if replacement is None else line[:1] + replacement)
            continue
        output.append(line)
    return "\n".join(output)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """gitignore-style glob: ``**`` spans directories, ``*``/``?`` do not."""

    regex = ""
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if pattern.startswith("**/", index):
            regex += "(?:.*/)?"
            index += 3
            continue
        if pattern.startswith("**", index):
            regex += ".*"
            index += 2
            continue
        if character == "*":
            regex += "[^/]*"
        elif character == "?":
            regex += "[^/]"
        elif character == "[":
            end = pattern.find("]", index + 1)
            if end == -1:
                regex += re.escape(character)
            else:
                regex += pattern[index : end + 1]
                index = end
        else:
            regex += re.escape(character)
        index += 1
    return re.compile(regex + r"\Z", re.IGNORECASE)


@dataclass(frozen=True)
class _Rule:
    regex: re.Pattern[str]
    anchored: bool
    directory_only: bool


def _compile(pattern: str) -> _Rule | None:
    pattern = pattern.strip()
    if not pattern or pattern.startswith("#") or pattern.startswith("!"):
        # Negation is not supported: re-including a file could only widen what
        # is sent, so an unsupported "!" line is ignored rather than guessed.
        return None
    directory_only = pattern.endswith("/")
    pattern = pattern.rstrip("/")
    anchored = "/" in pattern
    pattern = pattern.lstrip("/")
    if not pattern:
        return None
    return _Rule(_glob_to_regex(pattern), anchored, directory_only)


def _matches(rule: _Rule, path: str) -> bool:
    parts = [part for part in path.split("/") if part]
    if not parts:
        return False
    if rule.anchored:
        # The pattern names a path from the repo root; it also covers anything
        # below a matching directory.
        for depth in range(1, len(parts) + 1):
            prefix = "/".join(parts[:depth])
            if rule.directory_only and depth == len(parts):
                continue
            if rule.regex.match(prefix):
                return True
        return False
    candidates = parts[:-1] if rule.directory_only else parts
    return any(rule.regex.match(part) for part in candidates)


@dataclass(frozen=True)
class PathRules:
    """The secret, ignore and noise rules for one repo."""

    ignore_patterns: tuple[str, ...] = ()
    ignore_hash: str | None = None

    def exclusion(self, path: str) -> str | None:
        """Why ``path`` is never sent: a reason string, or ``None`` to allow it."""

        for pattern in SECRET_PATH_PATTERNS:
            rule = _compile(pattern)
            if rule is not None and _matches(rule, path):
                return "secret_pattern"
        for pattern in self.ignore_patterns:
            rule = _compile(pattern)
            if rule is not None and _matches(rule, path):
                return "learnloopignore"
        for pattern in NOISE_PATH_PATTERNS:
            rule = _compile(pattern)
            if rule is not None and _matches(rule, path):
                return "noise"
        return None


def load_path_rules(repo: Path) -> PathRules:
    """Read the repo's current ``.learnloopignore`` (the owner's latest intent)."""

    path = Path(repo) / IGNORE_FILE_NAME
    try:
        raw = path.read_bytes() if path.is_file() and not path.is_symlink() else b""
    except OSError:
        raw = b""
    if not raw:
        return PathRules()
    text = raw.decode("utf-8", "replace")
    patterns = tuple(line for line in text.splitlines() if _compile(line) is not None)
    return PathRules(
        ignore_patterns=patterns,
        ignore_hash="sha256:" + hashlib.sha256(raw).hexdigest(),
    )


__all__ = [
    "IGNORE_FILE_NAME",
    "NOISE_PATH_PATTERNS",
    "PathRules",
    "RedactionCounter",
    "SECRET_PATH_PATTERNS",
    "SECRET_PATTERN_VERSION",
    "load_path_rules",
    "redact_diff",
    "redact_lines",
    "redact_text",
    "scan_line",
]
