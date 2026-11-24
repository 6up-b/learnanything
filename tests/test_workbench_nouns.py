"""The workbench's nouns in the sidecar's learner messages (the owner's naming decision, 2026-11-23: "companion,
pad, saved question, cold check").

The messages the desks' handlers raise reach the learner as they are written, so they say pad (never scratchpad),
saved question and save for later (never carried question or carry), the companion for the ask surface, and cold
check for a check on your own. The code keeps its own names (``carried_*``, ``CarriedRefused``, the ``carry`` codes);
only the message text is read. The desks' frontend has the same scan (``screens/desks/workbenchNouns.test.ts``).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    *sorted((ROOT / "src/learnloop/pads").glob("*.py")),
    ROOT / "src/learnloop/intent/inline_checks.py",
    *(ROOT / "src/learnloop_sidecar/handlers" / f"{name}.py" for name in (
        "pads", "companion", "companion_ask", "desks", "inline_checks", "lesson", "passage_union", "search", "ink",
    )),
]
# Not scanned: handlers/figures.py, whose refusals name the check on your own as Practice and Today still name it (the
# naming pass covers the workbench and the lesson view; those screens keep their words until their own pass).

RETIRED = [
    (re.compile(r"scratch ?pads?", re.I), "pad / pads"),
    (re.compile(r"\bcarr(?:y|ies|ied|ying)\b", re.I), "save for later / saved question"),
    (re.compile(r"\b(?:checks?|questions?) on your own\b", re.I), "cold check"),
    (re.compile(r"\b(?:in|to|ask) the tutor\b|\bthe tutor waits\b", re.I), "the companion"),
]


def _raised_messages(path: Path) -> list[tuple[int, str]]:
    """Every string a ``raise`` passes to the exception it builds (its messages, by line)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
            continue
        for arg in [*node.exc.args, *(keyword.value for keyword in node.exc.keywords)]:
            for part in ast.walk(arg):
                if isinstance(part, ast.Constant) and isinstance(part.value, str) and " " in part.value:
                    out.append((part.lineno, part.value))
    return out


def test_the_scan_covers_the_desks_handlers_and_reads_their_messages() -> None:
    assert all(path.exists() for path in FILES)
    messages = [text for path in FILES for _, text in _raised_messages(path)]
    assert any("saved question" in text for text in messages)


def test_no_learner_message_of_the_desks_uses_a_retired_word() -> None:
    found = [
        f"{path.relative_to(ROOT)}:{line}: {text!r} (say {instead})"
        for path in FILES
        for line, text in _raised_messages(path)
        for pattern, instead in RETIRED
        if pattern.search(text)
    ]
    assert found == []
