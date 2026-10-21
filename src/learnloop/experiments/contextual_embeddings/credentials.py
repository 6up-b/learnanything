"""Hosted API keys: the process environment only, never printed (spec D13).

Adapters read a configurable environment variable name
(``PERPLEXITY_API_KEY``, ``VOYAGE_API_KEY`` by default). ``--env-file
<path>`` loads only the NAMED variables from a dotenv file into this
process's environment, without printing, logging or persisting them; a value
already set in the shell takes precedence (the app loader's rule). Every
report says only whether a name is present or absent: never a value, a
prefix, a length or a hash of one.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping
import os
from pathlib import Path
import re

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EnvFileError(ValueError):
    """The env file could not be read; the message never contains file contents."""


def _value(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    # An unquoted value ends at an inline comment.
    hash_at = raw.find(" #")
    return (raw[:hash_at] if hash_at >= 0 else raw).strip()


def load_env_file(path: Path | str, names: Iterable[str], *,
                  environ: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Load the named variables from ``path`` into ``environ`` (default
    ``os.environ``) without overriding values already set. Returns each
    name's availability (``present`` / ``absent``) after loading, nothing else.

    Lines that are not ``NAME=value`` assignments are ignored silently (their
    text is never echoed); unnamed variables are never loaded.
    """

    environ = os.environ if environ is None else environ
    wanted = [str(name) for name in names]
    for name in wanted:
        if not _NAME.match(name):
            raise EnvFileError("environment variable names must be identifiers")
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # The path is the owner's own argument; the file's content is never quoted.
        raise EnvFileError(f"cannot read the env file ({type(exc).__name__})") from None
    found: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _LINE.match(line)
        if match is None or match.group(1) not in wanted:
            continue
        value = _value(match.group(2))
        if value:
            found[match.group(1)] = value
    for name, value in found.items():
        if not environ.get(name):
            environ[name] = value
    del found
    return availability(wanted, environ=environ)


def availability(names: Iterable[str], *, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """``{name: "present" | "absent"}``; the redacted check every report uses."""

    environ = os.environ if environ is None else environ
    return {str(name): ("present" if environ.get(str(name)) else "absent") for name in names}


def read_key(name: str, *, environ: Mapping[str, str] | None = None) -> str | None:
    """The key's value for an adapter's request header (never logged)."""

    environ = os.environ if environ is None else environ
    value = environ.get(name)
    return value or None
