"""E0 stays outside production: only the CLI reaches learnloop.experiments, lazily.

The import-linter contract ``experiments-stay-outside-production`` covers the
packages grimp traverses; this scan also covers the namespace package
``learnloop.content``, function-local imports and any package added later.
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXPERIMENTS = SRC / "learnloop" / "experiments"
CLI_ENTRY = SRC / "learnloop" / "cli" / "experiments.py"


def _imports(path: Path) -> list[tuple[int, str, bool]]:
    """(line, module, at module level) of every import in ``path``."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    top = {id(node) for node in tree.body}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name, id(node) in top) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.lineno, node.module, id(node) in top))
            found.extend((node.lineno, f"{node.module}.{alias.name}", id(node) in top) for alias in node.names)
    return found


def test_no_production_module_imports_the_experiments():
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path == CLI_ENTRY or EXPERIMENTS in path.parents:
            continue
        for line, module, _top in _imports(path):
            if module == "learnloop.experiments" or module.startswith("learnloop.experiments."):
                offenders.append(f"{path.relative_to(ROOT)}:{line} {module}")
    assert not offenders, "\n".join(offenders)


def test_the_cli_imports_the_experiments_only_inside_commands():
    module_level = [module for _line, module, top in _imports(CLI_ENTRY)
                    if top and module.startswith("learnloop.experiments")]
    assert module_level == []
    code = ("import sys, learnloop.cli; "
            "print(any(name.startswith('learnloop.experiments') for name in sys.modules))")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                            cwd=ROOT, timeout=120)
    assert result.stdout.strip() == "False"


def test_the_import_linter_contract_names_every_production_package():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contract = next(item for item in config["tool"]["importlinter"]["contracts"]
                    if item["id"] == "experiments-stay-outside-production")
    assert contract["forbidden_modules"] == ["learnloop.experiments"]
    assert contract["allow_indirect_imports"] is False
    names = {path.stem if path.suffix == ".py" else path.name for path in (SRC / "learnloop").iterdir()
             if (path.suffix == ".py" or (path.is_dir() and (path / "__init__.py").exists()))
             and path.name not in ("__init__.py", "__main__.py")}
    expected = {f"learnloop.{name}" for name in names - {"cli", "experiments"}}
    assert expected <= set(contract["source_modules"])
    assert {"learnloop_sidecar", "learnloop_mobile", "learnloop_mcp"} <= set(contract["source_modules"])


def test_the_experiments_write_sql_only_to_redact_a_service_copy():
    # The one raw SQL write is the redaction of a SERVICE copy's protected
    # block text (Codex review F1; refused outside fixtures-local). Verdicts go
    # through the production append_judgment into the experiment's own
    # repository; nothing writes a frozen copy.
    allowed = {("system_arms.py", "UPDATE ")}
    for path in EXPERIMENTS.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for statement in ("INSERT INTO", "UPDATE ", "DELETE FROM", "REPLACE INTO", "CREATE TABLE"):
            if (path.name, statement) in allowed:
                assert text.count(statement) == 1
                assert "UPDATE source_document_blocks SET text = ''" in text
                continue
            assert statement not in text, f"{path.name}: {statement}"
