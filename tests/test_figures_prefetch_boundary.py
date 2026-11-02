"""Reader RW5d P5 (spec_reader_show_me_figures_v1 §10b): ``figures/prefetch.py`` is a composition layer.

Nothing imports it back but the desktop sidecar's prefetch runtime (and the tests): not the figure
service, the plan, the teacher, the evidence side or any host. The import-linter's frozen-cycles
contract ignores its two function-local reads (the stored day plan, a lesson's stored plan) on this
promise. The evidence-never-reads-figures contract covers the decision tables' readers too: they live
under ``learnloop.figures``.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
PATTERN = re.compile(r"learnloop\.figures\.prefetch(?![_\w])|from learnloop\.figures import [^\n]*\bprefetch\b(?!_)")
ALLOWED = {"learnloop_sidecar/prefetch_runtime.py", "learnloop/figures/prefetch.py"}


def test_nothing_imports_the_prefetch_service_back():
    found = sorted(str(path.relative_to(ROOT)) for path in ROOT.rglob("*.py")
                   if PATTERN.search(path.read_text(encoding="utf-8")))
    assert set(found) <= ALLOWED, found
    assert "learnloop_sidecar/prefetch_runtime.py" in found


def test_the_decision_ledger_is_never_read_by_evidence_scheduling_or_serving():
    """The evidence-never-reads-figures packages (and the plan, the hints) never name the P5 tables;
    AD's table and column classes name them only to deny and classify them."""

    packages = ("substrate", "learner", "attempts", "scheduling", "goals", "diagnosis", "placement", "field",
                "router", "adaptive_difficulty", "daily_plan", "hints")
    readers = sorted(str(path.relative_to(ROOT)) for package in packages for path in (ROOT / "learnloop" / package).rglob("*.py")
                     if "figure_prefetch_decisions" in (text := path.read_text(encoding="utf-8"))
                     or "plan_usage_pauses" in text)
    assert readers == ["learnloop/adaptive_difficulty/column_classes.py",
                       "learnloop/adaptive_difficulty/protected_tables.py"], readers
