"""``Reference/_generated.md`` vouches for each generator's notes only (arc A close, fix 4).

One shared stamp written by every generator let one generator certify notes it never
regenerated: commit a new function, run only ``db_generate_reference.py``, and the
stamp moved although the module notes lacked the function. Each generator now records
its own commit, and rewrites only its own row.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "docs" / "learnloop-architecture-vault" / "_scripts"
NAMES = ("module_generate.py", "desktop_generate.py", "db_generate_reference.py")


@pytest.fixture
def provenance(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("generated_provenance_for_test", SCRIPTS / "generated_provenance.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(module, "NOTE_PATH", tmp_path / "Reference" / "_generated.md")
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _sources_at(module, monkeypatch, commit: str, dirty: list[str]) -> None:
    monkeypatch.setattr(module, "inputs_provenance", lambda: (commit, f"ts-{commit[:4]}", list(dirty)))


def test_one_generator_never_moves_another_generators_commit(provenance, monkeypatch):
    old, new = "a" * 40, "b" * 40
    _sources_at(provenance, monkeypatch, old, [])
    for name in NAMES:
        provenance.write(name)
    assert provenance.note_errors() == []
    module_row = next(line for line in provenance.NOTE_PATH.read_text(encoding="utf-8").splitlines()
                      if line.startswith("| `_scripts/module_generate.py`"))

    # A new commit, then only the db generator runs.
    _sources_at(provenance, monkeypatch, new, ["src/learnloop/x.py"])
    provenance.write("db_generate_reference.py")
    recorded = provenance.recorded()
    assert recorded["module_generate.py"]["source_commit"] == old
    assert recorded["desktop_generate.py"]["source_commit"] == old
    assert recorded["db_generate_reference.py"]["source_commit"] == new
    assert recorded["db_generate_reference.py"]["uncommitted_inputs"] == ["src/learnloop/x.py"]
    text = provenance.NOTE_PATH.read_text(encoding="utf-8")
    assert module_row in text.splitlines()
    assert provenance.note_errors() == []

    # Running it again on the same sources changes nothing.
    provenance.write("db_generate_reference.py")
    assert provenance.NOTE_PATH.read_text(encoding="utf-8") == text


def test_a_generator_that_never_ran_is_an_error(provenance, monkeypatch):
    _sources_at(provenance, monkeypatch, "c" * 40, [])
    provenance.write("module_generate.py")
    errors = provenance.note_errors()
    assert len(errors) == 2 and all("never recorded" in error for error in errors)


def test_each_generator_writes_only_its_own_row():
    for name in NAMES:
        source = (SCRIPTS / name).read_text(encoding="utf-8")
        calls = re.findall(r"generated_provenance\.(?:write|render_for)\(([^)]*)\)", source)
        assert calls == [repr(name).replace("'", '"')], (name, calls)
