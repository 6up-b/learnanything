"""What other test files use from ``tests/test_figure_label_wording.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES_TS = ROOT / "apps/learnloop-tauri/src/screens/reader/figures"


def _frame(name: str, frame: str) -> dict[str, str]:
    source = (FIGURES_TS / name).read_text(encoding="utf-8")
    body = source[source.index(f"export const {frame} = {{"):]
    body = body[:body.index("} as const;")]
    return dict(re.findall(r'^\s+(\w+): "((?:[^"\\]|\\.)*)",?$', body, flags=re.MULTILINE))
