"""Every effective default of a new vault, one readable line each, in ``tests/goldens/effective_defaults.toml``.

A default nobody meant to change fails here, and one that was meant to change shows up in review as its own line: the
file is the whole effective config (``learnloop config effective``, with unset keys kept), flattened to sorted dotted
keys. It replaces one sha256 per algorithm tag, which held one bit and moved on every default change.

Regenerate after a deliberate default change, and commit the file with the change:

    uv run python tests/test_effective_defaults_golden.py --write
"""

from __future__ import annotations

import difflib
import json
import math
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, SUCCESSOR_CHAIN
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import DEFAULT_CONFIG_TEXT, default_config_text

GOLDEN_PATH = Path(__file__).parent / "goldens" / "effective_defaults.toml"
REGENERATE = "uv run python tests/test_effective_defaults_golden.py --write"
HEADER = (
    "# Every effective default of a new vault (the decision-only template, loaded), one line per key, sorted.\n"
    "# Generated; do not edit by hand. After a deliberate default change: " + REGENERATE + "\n"
    "# TOML has no null, so an unset key is a comment: `# key = null`.\n"
)
_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def effective_defaults(config_text: str = DEFAULT_CONFIG_TEXT) -> dict[str, Any]:
    return LearnLoopConfig.model_validate(tomllib.loads(config_text)).model_dump(mode="json", exclude_none=False)


def _key(part: str) -> str:
    return part if _BARE_KEY.fullmatch(part) else json.dumps(part, ensure_ascii=False)


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # repr is the shortest exact form and valid TOML (1e-05, 40.0); TOML spells the specials inf and nan.
        return ("-inf" if value < 0 else "inf") if math.isinf(value) else "nan" if math.isnan(value) else repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{_key(k)} = {_value(v)}" for k, v in sorted(value.items())) + " }" if value else "{}"
    raise TypeError(f"no TOML form for {value!r} inside a value")


def _lines(payload: dict[str, Any], path: tuple[str, ...] = ()):
    for name in sorted(payload):
        value, here = payload[name], (*path, name)
        if isinstance(value, dict) and value:
            yield from _lines(value, here)
        elif value is None:
            yield here, f"# {'.'.join(map(_key, here))} = null"
        else:
            yield here, f"{'.'.join(map(_key, here))} = {_value(value)}"


def effective_defaults_toml(config_text: str = DEFAULT_CONFIG_TEXT) -> str:
    """The golden file's text: one line per effective key, sorted by its path."""

    body = "\n".join(line for _path, line in sorted(_lines(effective_defaults(config_text))))
    return HEADER + body + "\n"


def test_the_effective_defaults_match_the_golden_file() -> None:
    pinned, current = GOLDEN_PATH.read_text(encoding="utf-8"), effective_defaults_toml()
    if pinned != current:
        changed = [line for line in difflib.unified_diff(pinned.splitlines(), current.splitlines(), "golden", "now",
                                                         n=0, lineterm="") if line[:1] in "+-"]
        raise AssertionError("an effective default changed. If it was meant to, run `" + REGENERATE
                             + "` and commit the file with the change:\n" + "\n".join(changed))


def _without_nulls(payload: dict[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for name, value in payload.items():
        if isinstance(value, dict) and value:
            inner = _without_nulls(value)
            if inner:
                kept[name] = inner
        elif value is not None:
            kept[name] = value
    return kept


def test_the_golden_file_reads_back_as_the_effective_config() -> None:
    """Guards the rendering: the file parses as TOML into exactly the effective config, unset keys aside."""

    golden = GOLDEN_PATH.read_text(encoding="utf-8")
    assert tomllib.loads(golden) == _without_nulls(effective_defaults())
    nulls = [line for line in golden.splitlines() if line.endswith(" = null") and not line.startswith("# ")]
    assert nulls == [] and len(golden.splitlines()) > 1000
    assert f'algorithms.algorithm_version = "{LATEST_ALGORITHM_VERSION}"' in golden.splitlines()


def test_every_tag_has_the_latest_defaults_apart_from_its_label() -> None:
    """A new key reaches every tag's effective config and is inert below its own tag, so one file covers them all."""

    latest = effective_defaults()
    for version in SUCCESSOR_CHAIN:
        at_version = effective_defaults(default_config_text(version))
        assert at_version["algorithms"]["algorithm_version"] == version
        at_version["algorithms"]["algorithm_version"] = LATEST_ALGORITHM_VERSION
        assert at_version == latest, version


if __name__ == "__main__" and sys.argv[1:] == ["--write"]:
    GOLDEN_PATH.parent.mkdir(exist_ok=True)
    GOLDEN_PATH.write_text(effective_defaults_toml(), encoding="utf-8")
