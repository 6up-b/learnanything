"""Follow-ups batch 7 (C): the module catalog names every source module, and only those.

Every landing that added modules left ``Reference/Modules`` stale until someone regenerated it.
``module_validate.py`` runs in about 3 s, but its whole check reads each note's contents, links and
test anchors, which change with ordinary edits. So this guard runs only its inventory, by path:
a source module with no note, or a note with no module.

Verify V2: only what git tracks, as the fixture walkers do (``tests/test_public_tip_guards.py``), so a
stray local file or a generated one (an untracked probe, an ignored ``build/`` directory, a temporary
note) can't fail an unrelated suite. ``module_validate.main`` keeps its whole-tree inventory.
"""

from __future__ import annotations

import importlib.util
import subprocess
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
    try:
        missing, orphaned = _validator().inventory_gaps()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    problems = []
    if missing:
        problems.append("Tracked source modules or packages with no tracked catalog note. Regenerate the catalog: "
                        f"{GENERATE}\n  " + "\n  ".join(missing))
    if orphaned:
        problems.append("Tracked catalog notes with no tracked source module (the generator never deletes one). Delete them, then "
                        f"regenerate: {GENERATE}\n  " + "\n  ".join(orphaned))
    assert not problems, "\n".join(problems)


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path, Path]:
    """A small repo with all of it tracked: one package with a module, its note, its map and the catalog."""

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
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    return validator, source, catalog


def test_a_tree_in_step_has_no_gaps_whatever_its_notes_say(tree):
    validator, _source, catalog = tree
    assert validator.inventory_gaps() == ([], [])
    (catalog / "learnloop" / "alpha.md").write_text("not even frontmatter, and stale besides\n", encoding="utf-8")
    assert validator.inventory_gaps() == ([], [])  # a note's contents are never read


def test_a_new_module_is_missing_and_a_new_package_its_map_too(tree):
    validator, source, _catalog = tree
    (source / "gamma.py").write_text("x\n", encoding="utf-8")
    _git(source, "add", "gamma.py")
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([f"{prefix}/gamma.md"], [])
    (source / "fresh").mkdir()
    (source / "fresh" / "delta.py").write_text("x\n", encoding="utf-8")
    _git(source, "add", "fresh")
    assert validator.inventory_gaps()[0] == [f"{prefix}/fresh/_package.md", f"{prefix}/fresh/delta.md",
                                             f"{prefix}/gamma.md"]


def test_a_module_gone_leaves_its_note_orphaned_and_its_emptied_packages_map_too(tree):
    validator, source, _catalog = tree
    (source / "sub" / "beta.py").unlink()
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([], [f"{prefix}/sub/_package.md", f"{prefix}/sub/beta.md"])


def test_an_untracked_module_or_note_is_no_gap_until_git_tracks_it(tree):
    validator, source, catalog = tree
    (source / "local_probe.py").write_text("x\n", encoding="utf-8")
    (source / "scratch").mkdir()
    (source / "scratch" / "probe.py").write_text("x\n", encoding="utf-8")
    (catalog / "learnloop" / "tmp_note.md").write_text("x\n", encoding="utf-8")
    assert validator.inventory_gaps() == ([], [])
    # Added, the module counts, and so does the note left with no module.
    _git(source, "add", "local_probe.py")
    _git(catalog, "add", "learnloop/tmp_note.md")
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([f"{prefix}/local_probe.md"], [f"{prefix}/tmp_note.md"])


def test_an_ignored_generated_module_is_no_gap(tree):
    validator, source, catalog = tree
    (source.parents[1] / ".gitignore").write_text("build/\n", encoding="utf-8")
    (source / "build").mkdir()
    (source / "build" / "generated.py").write_text("x\n", encoding="utf-8")
    (catalog / "build").mkdir()
    (catalog / "build" / "rendered.md").write_text("x\n", encoding="utf-8")
    assert validator.inventory_gaps() == ([], [])


def test_a_tracked_module_with_no_note_still_fails_even_with_an_untracked_note(tree):
    """An untracked note doesn't satisfy a tracked module: a commit of this tree would have none."""

    validator, source, catalog = tree
    (source / "gamma.py").write_text("x\n", encoding="utf-8")
    _git(source, "add", "gamma.py")
    (catalog / "learnloop" / "gamma.md").write_text("x\n", encoding="utf-8")
    assert validator.inventory_gaps() == (["docs/learnloop-architecture-vault/Reference/Modules/learnloop/gamma.md"], [])


def test_a_tracked_file_deleted_from_the_working_tree_counts_as_gone(tree):
    validator, source, catalog = tree
    (catalog / "learnloop" / "alpha.md").unlink()
    prefix = "docs/learnloop-architecture-vault/Reference/Modules/learnloop"
    assert validator.inventory_gaps() == ([f"{prefix}/alpha.md"], [])
    (source / "alpha.py").unlink()
    assert validator.inventory_gaps() == ([], [])


def test_main_keeps_its_whole_tree_inventory(tree):
    validator, source, _catalog = tree
    (source / "local_probe.py").write_text("x\n", encoding="utf-8")
    assert source / "local_probe.py" in validator.source_files()
