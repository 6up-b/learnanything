from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.constructor import RoundTripConstructor
from ruamel.yaml.resolver import implicit_resolvers as _RUAMEL_IMPLICIT_RESOLVERS
from ruamel.yaml.util import timestamp_regexp as _RUAMEL_TIMESTAMP_REGEXP

try:
    import yaml as _pyyaml
except ImportError:  # pragma: no cover - PyYAML ships with the dependency set
    _pyyaml = None


def _yaml() -> YAML:
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def read_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping for editing.

    The round-trip loader keeps comments, key order and quoting so a later
    ``write_yaml`` of the same data leaves untouched parts of the file as the
    author wrote them. Read-only callers should use ``read_yaml_data``.
    """

    yaml = _yaml()
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping at {path}")
    return loaded


def read_yaml_data(path: Path) -> dict[str, Any]:
    """Load a YAML mapping as plain Python data, for callers that never write it back.

    Parses with libyaml when it is available (about 18x faster than the
    pure-Python round-trip loader) using the round-trip loader's YAML 1.2
    scalar rules, so the values are equal to ``read_yaml``'s. Anything the fast
    path does not reproduce exactly (explicit tags, directives, merge keys,
    duplicate keys, non-canonical numbers, parse errors) is loaded by
    ``read_yaml`` instead, which also keeps its error messages.
    """

    text = path.read_text(encoding="utf-8")
    fast = _fast_load(text)
    if fast is _NEEDS_ROUND_TRIP:
        return read_yaml(path)
    loaded = fast or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping at {path}")
    return loaded


#: The emitter's line width when the default one would not read back.
WIDE_EMITTER_WIDTH = 4096


def _dumped(data: dict[str, Any]) -> str:
    """The YAML text for ``data``, guaranteed to read back.

    ruamel folds a plain mapping key longer than the line width across lines,
    which is invalid YAML (a simple key must stay on one line): a trace
    contract keyed by long checkpoint sentences was written unreadable, and
    the loader then skipped the item. The default emitter's output is kept
    whenever it reads back, so every file that was valid stays byte-identical;
    otherwise the text is emitted again without folding.
    """

    yaml = _yaml()
    stream = StringIO()
    yaml.dump(data, stream)
    text = stream.getvalue()
    try:
        _yaml().load(text)
        return text
    except Exception:  # noqa: BLE001 - re-emit below; a second failure raises
        wide = _yaml()
        wide.width = WIDE_EMITTER_WIDTH
        stream = StringIO()
        wide.dump(data, stream)
        text = stream.getvalue()
        _yaml().load(text)
        return text


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _dumped(data)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def yaml_to_string(data: dict[str, Any]) -> str:
    return _dumped(data)


def read_markdown_with_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, rest = text.split("---\n", 1)
    frontmatter_text, body = rest.split("\n---\n", 1)
    yaml = _yaml()
    metadata = yaml.load(frontmatter_text) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected frontmatter mapping at {path}")
    return metadata, body


def read_markdown_frontmatter_data(path: Path) -> tuple[dict[str, Any], str]:
    """``read_markdown_with_frontmatter`` for read-only callers; see ``read_yaml_data``."""

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, rest = text.split("---\n", 1)
    if "\n---\n" not in rest:
        return read_markdown_with_frontmatter(path)
    frontmatter_text, body = rest.split("\n---\n", 1)
    fast = _fast_load(frontmatter_text)
    if fast is _NEEDS_ROUND_TRIP:
        return read_markdown_with_frontmatter(path)
    metadata = fast or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected frontmatter mapping at {path}")
    return metadata, body


def write_markdown_with_frontmatter(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = _yaml()
    stream = StringIO()
    yaml.dump(metadata, stream)
    frontmatter = stream.getvalue().strip()
    normalized_body = body if body.endswith("\n") else body + "\n"
    path.write_text(f"---\n{frontmatter}\n---\n\n{normalized_body}", encoding="utf-8")


# --- Fast read path -------------------------------------------------------
#
# PyYAML resolves plain scalars by YAML 1.1 rules (``yes``/``on`` are booleans,
# ``1e-4`` is a string, ``3:2`` is a base-60 integer, ``010`` is octal), while
# the round-trip loader follows YAML 1.2. The loader below swaps in ruamel's own
# YAML 1.2 resolver table and only constructs the scalar forms whose values are
# unambiguous; every other form sends the whole document to ``read_yaml``.

_NEEDS_ROUND_TRIP = object()

# An explicit tag (``!foo``, ``!!str``) changes what the round-trip loader
# builds, and a ``%YAML`` directive changes its resolver version. Both are rare
# enough in vault files that the whole document can take the slow path.
_TAG_OR_DIRECTIVE = re.compile(r"(?:^|[\s\[\]{},])!|^%", re.MULTILINE)
_CANONICAL_INT = re.compile(r"^[-+]?(?:0|[1-9][0-9]*)$")
_TAG_PREFIX = "tag:yaml.org,2002:"
_MERGE_OR_VALUE_KEY_TAGS = {_TAG_PREFIX + "merge", _TAG_PREFIX + "value"}


class _RoundTripOnly(Exception):
    """The document uses a form only the round-trip loader reproduces exactly."""


def _fast_load(text: str, loader: type | None = None) -> Any:
    """Parse ``text`` on the fast path, or return ``_NEEDS_ROUND_TRIP``."""

    loader = loader or _FastSafeLoader
    if loader is None or _TAG_OR_DIRECTIVE.search(text):
        return _NEEDS_ROUND_TRIP
    try:
        return _pyyaml.load(text, Loader=loader)
    except Exception:
        return _NEEDS_ROUND_TRIP


def _build_fast_loader(base: type) -> type:
    """Subclass a PyYAML safe loader (C or pure Python) with round-trip scalar rules."""

    class FastSafeLoader(base):  # type: ignore[misc, valid-type]
        yaml_implicit_resolvers: dict[Any, list[tuple[str, Any]]] = {}
        yaml_constructors: dict[Any, Any] = {}
        timestamp_regexp = _RUAMEL_TIMESTAMP_REGEXP

        def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
            if any(key_node.tag in _MERGE_OR_VALUE_KEY_TAGS for key_node, _ in node.value):
                raise _RoundTripOnly("merge or value key")
            mapping = _pyyaml.constructor.BaseConstructor.construct_mapping(self, node, deep=deep)
            if len(mapping) != len(node.value):
                # The round-trip loader rejects duplicate keys; PyYAML keeps the last.
                raise _RoundTripOnly("duplicate key")
            return mapping

        def construct_yaml_int(self, node: Any) -> int:
            value = self.construct_scalar(node)
            if not _CANONICAL_INT.match(value):
                raise _RoundTripOnly("non-decimal or underscored integer")
            return int(value)

        def construct_yaml_float(self, node: Any) -> float:
            value = self.construct_scalar(node)
            if "_" in value:
                raise _RoundTripOnly("underscored float")
            lowered = value.lower()
            sign = -1.0 if lowered.startswith("-") else 1.0
            unsigned = lowered.lstrip("+-")
            if unsigned == ".inf":
                return sign * float("inf")
            if unsigned == ".nan":
                return float("nan")
            return float(lowered)

        def construct_yaml_bool(self, node: Any) -> bool:
            value = self.construct_scalar(node).lower()
            if value not in {"true", "false"}:
                raise _RoundTripOnly("YAML 1.1 boolean")
            return value == "true"

        def construct_yaml_timestamp(self, node: Any) -> Any:
            # Same objects (date, or ruamel's TimeStamp carrying the written
            # offset) as the round-trip loader builds.
            return RoundTripConstructor.construct_yaml_timestamp(self, node)

        def construct_round_trip_only(self, node: Any) -> Any:
            raise _RoundTripOnly(f"tag {node.tag}")

    for versions, tag, regexp, first in _RUAMEL_IMPLICIT_RESOLVERS:
        if (1, 2) in versions:
            FastSafeLoader.add_implicit_resolver(tag, re.compile(regexp.pattern, regexp.flags), first)
    safe_constructor = _pyyaml.constructor.SafeConstructor
    for tag, method in (
        ("null", safe_constructor.construct_yaml_null),
        ("bool", FastSafeLoader.construct_yaml_bool),
        ("int", FastSafeLoader.construct_yaml_int),
        ("float", FastSafeLoader.construct_yaml_float),
        ("timestamp", FastSafeLoader.construct_yaml_timestamp),
        ("str", safe_constructor.construct_yaml_str),
        ("seq", safe_constructor.construct_yaml_seq),
        ("map", safe_constructor.construct_yaml_map),
    ):
        FastSafeLoader.add_constructor(_TAG_PREFIX + tag, method)
    FastSafeLoader.add_constructor(None, FastSafeLoader.construct_round_trip_only)
    return FastSafeLoader


_FastSafeLoader = (
    _build_fast_loader(getattr(_pyyaml, "CSafeLoader", _pyyaml.SafeLoader))
    if _pyyaml is not None
    else None
)
