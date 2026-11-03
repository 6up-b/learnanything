"""Reader RW5c (G23h): "checked" is never evidence, mastery, certification or help weight (spec §11.2)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from learnloop.adaptive_difficulty import protected_tables as PT

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    # The check's own home, its table's store and the classifications that say nobody reads it.
    "src/learnloop/figures/source_check.py", "src/learnloop/figures/service.py", "src/learnloop/db/stores/figures.py",
    "src/learnloop/db/table_roles.py", "src/learnloop/adaptive_difficulty/protected_tables.py",
    "src/learnloop/adaptive_difficulty/column_classes.py",
    # Docstrings naming the table: the switch's predicate and the config section read no row.
    "src/learnloop/figure_admission.py", "src/learnloop/config/schema.py",
}


def _grep(*patterns: str) -> set[str]:
    found: set[str] = set()
    for pattern in patterns:
        result = subprocess.run(["git", "grep", "-l", "-e", pattern, "--", "src"], cwd=ROOT, capture_output=True, text=True,
                                check=False)
        found |= set(result.stdout.split())
    return found


def test_only_the_figure_package_reads_the_ledger_or_its_judgments():
    assert _grep("figure_source_checks", "figure_source_check\\b") <= ALLOWED


def test_nothing_outside_the_figure_package_imports_the_check():
    importers = _grep("figures.source_check", "figures import source_check", "figures.elements", "figures.book_math")
    outside = {path for path in importers if not path.startswith("src/learnloop/figures/")}
    # The sidecar's RPC and the CLI start it; neither is evidence, attempts, hints or scheduling.
    assert outside <= {"src/learnloop/cli/reader.py", "src/learnloop_sidecar/handlers/figures.py"}


def test_the_view_block_reaches_no_grader_hint_or_outcome_path():
    readers = _grep("source_check", "sourceCheck")
    for path in readers:
        assert not any(part in path for part in ("/hints/", "help_outcomes", "/grading/", "/scheduling/", "/attempts/",
                                                 "/evidence", "/projection", "/adaptive_difficulty/operations")), path


def test_the_table_is_protected_and_unread_by_ad():
    assert PT.role("figure_source_checks") == PT.PROTECTED
    assert "figure_source_checks" in PT.READING


def test_the_import_contract_covers_the_new_modules():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "evidence-never-reads-figures" in text or "learnloop.figures" in text
    for module in ("book_math", "source_check", "elements", "display_format"):
        assert (ROOT / "src" / "learnloop" / "figures" / f"{module}.py").is_file()
