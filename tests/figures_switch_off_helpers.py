"""What other test files use from ``tests/test_figures_switch_off.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path


def _switch(root: Path, section: str, enabled: bool) -> None:
    import re

    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    found = re.search(rf"(?ms)^\[{section}\]\n(.*?)(?=^\[|\Z)", text)
    if found is None:
        text = text.rstrip("\n") + f"\n\n[{section}]\nenabled = {value}\n"
    elif re.search(r"(?m)^enabled = ", found.group(1)):
        body = re.sub(r"(?m)^enabled = \w+", f"enabled = {value}", found.group(1), count=1)
        text = text[:found.start(1)] + body + text[found.end(1):]
    else:
        text = text[:found.start(1)] + f"enabled = {value}\n" + text[found.start(1):]
    config.write_text(text, encoding="utf-8")
