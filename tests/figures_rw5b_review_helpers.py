"""What other test files use from ``tests/test_figures_rw5b_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import re

from tests.figure_fixtures import set_config


def _panels(paths, on: bool) -> None:
    """Flip ``figures.advanced_panels_enabled`` (set_config appends, and a
    TOML key may be set only once)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "advanced_panels_enabled = " in text:
        config.write_text(re.sub(r"advanced_panels_enabled = (true|false)",
                                 f"advanced_panels_enabled = {'true' if on else 'false'}", text), encoding="utf-8")
    else:
        set_config(paths, "figures", advanced_panels_enabled=on)
