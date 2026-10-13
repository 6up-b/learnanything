"""G17: the instructional service is a composition layer (spec_source_practice_and_probes_v1 SC12).

import-linter enforces the contract for every regular package; ``learnloop.content``
is an implicit namespace package grimp does not traverse, and function-local
imports are easy to miss, so this scans the source text of every package that
must reach the service only through injected callables.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "learnloop"
FORBIDDEN_IMPORTERS = (
    "attempts", "learner", "scheduling", "goals", "diagnosis", "curriculum", "substrate", "content",
    "reader", "tutor", "ops", "params", "sim", "projects", "practice_index", "source_retrieval",
    "daily_plan", "db", "vault", "ai", "config",
)


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
    return found


def test_no_domain_or_lower_package_imports_the_service():
    violations = []
    for package in FORBIDDEN_IMPORTERS:
        for path in sorted((ROOT / package).rglob("*.py")):
            for line, module in _imports(path):
                if module == "learnloop.instructional" or module.startswith("learnloop.instructional."):
                    violations.append(f"{path.relative_to(ROOT)}:{line}: {module}")
    assert not violations, "\n".join(violations)


def test_the_service_never_imports_the_daily_plan():
    violations = []
    for path in sorted((ROOT / "instructional").rglob("*.py")):
        for line, module in _imports(path):
            if module == "learnloop.daily_plan" or module.startswith("learnloop.daily_plan."):
                violations.append(f"{path.relative_to(ROOT)}:{line}: {module}")
    assert not violations, "\n".join(violations)
