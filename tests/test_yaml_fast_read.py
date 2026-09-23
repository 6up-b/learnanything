"""The libyaml read path must produce exactly what the round-trip loader produces.

``read_yaml_data`` feeds ``load_vault`` and doctor; ``read_yaml`` stays the
editing loader. These tests compare the two value-for-value (with ruamel's
scalar subclasses mapped to their base types) over every YAML file and Markdown
frontmatter block in ``fixtures/``, which are only read.
"""

from __future__ import annotations

import datetime
import math
from pathlib import Path
from typing import Any

import pytest
import yaml

from learnloop.vault import yaml_io
from learnloop.vault.yaml_io import (
    read_markdown_frontmatter_data,
    read_markdown_with_frontmatter,
    read_yaml,
    read_yaml_data,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE_YAML = sorted(FIXTURES.rglob("*.yaml"))
FIXTURE_MARKDOWN = sorted(
    path for path in FIXTURES.rglob("*.md") if path.read_text(encoding="utf-8").startswith("---\n")
)
PURE_PYTHON_LOADER = yaml_io._build_fast_loader(yaml.SafeLoader)


def _canonical(value: Any) -> Any:
    """Type-tagged structure that treats ruamel's scalar subclasses as their base type."""

    if isinstance(value, dict):
        return ("map", [(_canonical(key), _canonical(item)) for key, item in value.items()])
    if isinstance(value, list):
        return ("seq", [_canonical(item) for item in value])
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", int(value))
    if isinstance(value, float):
        return ("float", "nan" if math.isnan(value) else float(value))
    if isinstance(value, str):
        return ("str", str(value))
    if isinstance(value, datetime.datetime):
        return ("datetime", type(value).__name__, value.isoformat(), value.tzname(), getattr(value, "_yaml", None))
    if isinstance(value, datetime.date):
        return ("date", value.isoformat())
    if value is None:
        return ("null", None)
    raise AssertionError(f"unexpected YAML value type {type(value)!r}")


def _read_or_error(read, path: Path) -> Any:
    try:
        return ("ok", _canonical(read(path)))
    except Exception as exc:  # noqa: BLE001 - the error itself is what is compared
        return ("error", type(exc).__name__, str(exc))


def test_fixture_corpus_is_not_empty() -> None:
    assert len(FIXTURE_YAML) > 100
    assert FIXTURE_MARKDOWN


@pytest.mark.parametrize("path", FIXTURE_YAML, ids=lambda path: str(path.relative_to(FIXTURES)))
def test_fast_read_matches_round_trip_read_for_fixture_yaml(path: Path) -> None:
    assert _read_or_error(read_yaml_data, path) == _read_or_error(read_yaml, path)


@pytest.mark.parametrize("path", FIXTURE_YAML, ids=lambda path: str(path.relative_to(FIXTURES)))
def test_libyaml_and_pure_python_safe_loaders_agree_on_fixture_yaml(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    c_loaded = yaml_io._fast_load(text)
    pure_loaded = yaml_io._fast_load(text, PURE_PYTHON_LOADER)
    if c_loaded is yaml_io._NEEDS_ROUND_TRIP or pure_loaded is yaml_io._NEEDS_ROUND_TRIP:
        assert c_loaded is pure_loaded
        return
    assert _canonical(c_loaded) == _canonical(pure_loaded)


@pytest.mark.parametrize("path", FIXTURE_MARKDOWN, ids=lambda path: str(path.relative_to(FIXTURES)))
def test_fast_frontmatter_read_matches_round_trip_read(path: Path) -> None:
    assert _read_or_error(read_markdown_frontmatter_data, path) == _read_or_error(
        read_markdown_with_frontmatter, path
    )


SCALAR_CASES = {
    "yaml11_bools": "a: yes\nb: on\nc: No\nd: OFF\ne: y\n",
    "yaml12_bools": "a: true\nb: False\nc: TRUE\n",
    "exponent_without_dot": "a: 1e-4\nb: 1e3\nc: -.5\nd: 1.\ne: 1.5E+3\nf: .inf\ng: -.Inf\nh: .NaN\n",
    "base_sixty": "ratio: 3:2\nclock: 12:30:00\n",
    "leading_zero_and_prefixes": "a: 010\nb: 0o10\nc: 0x1F\nd: 0b101\ne: 1_000\nf: -0\ng: +7\n",
    "timestamps": (
        "a: 2026-07-01\nb: 2026-07-01T10:00:00Z\nc: 2026-07-01 10:00:00+02:00\n"
        "d: 2026-07-01T10:00:00.123456\ne: 2026-7-1\n"
    ),
    "nulls": "a: ~\nb: null\nc: NULL\nd:\n",
    "quoted_and_block_strings": "a: '010'\nb: \"yes\"\nc: |\n  line one\n  line two\nd: >\n  folded\n  text\n",
    "explicit_tags": "a: !!str 5\nb: !custom value\nc: !!float 1\n",
    "merge_key": "base: &base\n  x: 1\nderived:\n  <<: *base\n  y: 2\n",
    "anchors": "a: &shared [1, 2]\nb: *shared\n",
    "duplicate_key": "a: 1\na: 2\n",
    "directive": "%YAML 1.1\n---\na: yes\n",
    "not_a_mapping": "- 1\n- 2\n",
    "empty": "",
    "syntax_error": "a: [1, 2\nb: 3\n",
}


@pytest.mark.parametrize("name", sorted(SCALAR_CASES))
def test_fast_read_matches_round_trip_read_for_edge_cases(tmp_path: Path, name: str) -> None:
    path = tmp_path / f"{name}.yaml"
    path.write_text(SCALAR_CASES[name], encoding="utf-8")

    assert _read_or_error(read_yaml_data, path) == _read_or_error(read_yaml, path)


def test_fast_read_returns_plain_python_containers(tmp_path: Path) -> None:
    path = tmp_path / "plain.yaml"
    path.write_text("a:\n  b: [1, 'x']\n", encoding="utf-8")

    loaded = read_yaml_data(path)

    assert type(loaded) is dict
    assert type(loaded["a"]) is dict
    assert type(loaded["a"]["b"]) is list
    assert type(loaded["a"]["b"][1]) is str
