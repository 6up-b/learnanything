"""Follow-ups batch 7 (C): the module catalog names every source module, and only those.

Every landing that added modules left ``Reference/Modules`` stale until someone regenerated it.
``module_validate.py`` runs in about 3 s, but its whole check reads each note's contents, links and
test anchors, which change with ordinary edits. So this guard runs only its inventory, by path:
a source module with no note, or a note with no module.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "docs" / "learnloop-architecture-vault" / "_scripts"
GENERATE = "uv run python docs/learnloop-architecture-vault/_scripts/module_generate.py"


def _validator() -> Any:
    spec = importlib.util.spec_from_file_location("module_validate_for_inventory", SCRIPTS / "module_validate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_every_source_module_has_a_note_and_every_note_a_module():
    missing, orphaned = _validator().inventory_gaps()
    problems = []
    if missing:
        problems.append("Source modules or packages with no catalog note. Regenerate the catalog: "
                        f"{GENERATE}\n  " + "\n  ".join(missing))
    if orphaned:
        problems.append("Catalog notes with no source module (the generator never deletes one). Delete them, then "
                        f"regenerate: {GENERATE}\n  " + "\n  ".join(orphaned))
    assert not problems, "\n".join(problems)


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path, Path]:
    """A small repo: one package with a module, its note, its map and the catalog."""

    validator = _validator()
    source = tmp_path / "src" / "learnloop"
    catalog = tmp_path / "docs" / "learnloop-architecture-vault" / "Reference" / "Modules"
    for path in (source / "alpha.py", source / "sub" / "beta.py", catalog / "Module Catalog.md",
                 catalog / "learnloop" / "_package.md", catalog / "learnloop" / "alpha.md",
                 catalog / "learnloop" / "sub" / "_package.md", catalog / "learnloop" / "sub" / "beta.md"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(validator, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validator, "CATALOG_ROOT", catalog)
    monkeypatch.setattr(validator, "SOURCE_ROOTS", (source, tmp_path / "src" / "learnloop_sidecar"))
    return validator, source, catalog


def test_a_tree_in_step_has_no_gaps_whatever_its_notes_say(tree):
    validator, _source, catalog = tree
    assert validator.inventory_gaps() == ([], [])
    (catalog / "learnloop" / "alpha.md").write_text("not even frontmatter, and stale besides\n", encoding="utf-8")
    assert validator.inventory_gaps() == ([], [])  # a note's contents are never read


def test_a_new_module_is_missing_and_a_new_package_its_map_too(tree):
    validator, source, _catalog = tree
    (source / "gamma.py").write_text("x\n", encoding="utf-8")
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([f"{prefix}/gamma.md"], [])
    (source / "fresh").mkdir()
    (source / "fresh" / "delta.py").write_text("x\n", encoding="utf-8")
    assert validator.inventory_gaps()[0] == [f"{prefix}/fresh/_package.md", f"{prefix}/fresh/delta.md",
                                             f"{prefix}/gamma.md"]


def test_a_module_gone_leaves_its_note_orphaned_and_its_emptied_packages_map_too(tree):
    validator, source, _catalog = tree
    (source / "sub" / "beta.py").unlink()
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([], [f"{prefix}/sub/_package.md", f"{prefix}/sub/beta.md"])
