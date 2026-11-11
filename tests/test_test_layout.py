"""No file under ``tests/`` imports from a ``test_*.py`` module (refactor step T1).

What several test files share (fixtures, builders, fakes, constants) lives in helper modules
without the ``test_`` prefix (``tests/helpers.py``, ``tests/<topic>_helpers.py``, ``*_fakes.py``),
which pytest does not collect. Two reasons. A test file importing another runs that file's
imports too, and ``scripts/affected_tests.py`` follows them: before T1, one fixture module
(``test_source_inventory``) put 500 test files one step from everything it imported, and a
typical change selected minutes more tests than it needed. And a narrow helper imports only
what its fixtures use, so a change reaches only the tests that use it.

``ALLOWED`` is a ratchet: each entry says why it stays, and an entry nothing needs any more fails.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.ast_cache import source_ast, source_text

TESTS = Path(__file__).resolve().parent

#: (importing module, imported test module) -> why the import stays.
ALLOWED = {
    ("test_p2_leakage_suite", "test_reader_dialogue"):
        "the P2 leakage suite reruns a track test function under a private alias (one named place for every "
        "leakage guard); moving it out would move the test itself",
    ("test_p2_leakage_suite", "test_surface_pool"):
        "the P2 leakage suite reruns two track test functions under private aliases, as above",
    ("rw2b_fix10_base_sequence", "test_stuck_prompt"):
        "the fallback import when the script runs in `git archive 7d4c5f4ce`'s tree "
        "(test_reader_rw2b_fix10's base run), where StuckFake is still in test_stuck_prompt",
    ("rw2b_fix11_base_sequence", "test_stuck_prompt"):
        "the same fallback, for test_reader_rw2b_fix11's base run",
}


def _test_module_imports(tree: ast.Module) -> set[tuple[str, int]]:
    """The ``test_*`` modules a module imports, with the line, in any form (function-local ones too)."""

    found: set[tuple[str, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.removeprefix("tests.")
                if name.startswith("test_") and alias.name.startswith("tests."):
                    found.add((name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level == 0 and module.startswith("tests.test_"):
                found.add((module.split(".")[1], node.lineno))
            elif node.level == 1 and module.startswith("test_"):
                found.add((module.split(".")[0], node.lineno))
            elif (node.level == 0 and module == "tests") or (node.level == 1 and not module):
                found.update((alias.name, node.lineno) for alias in node.names if alias.name.startswith("test_"))
    return found


def _all_imports() -> dict[tuple[str, str], list[int]]:
    imports: dict[tuple[str, str], list[int]] = {}
    for path in sorted(TESTS.glob("*.py")):
        for module, line in _test_module_imports(source_ast(source_text(path))):
            if (TESTS / f"{module}.py").exists():
                imports.setdefault((path.stem, module), []).append(line)
    return imports


def test_no_file_under_tests_imports_a_test_module():
    offending = {pair: sorted(lines) for pair, lines in _all_imports().items() if pair not in ALLOWED}
    assert not offending, (
        "move what these files share into a helper module without the test_ prefix "
        "(tests/<topic>_helpers.py) and import it from there:\n"
        + "\n".join(f"  tests/{importer}.py lines {lines} import tests/{module}.py"
                    for (importer, module), lines in sorted(offending.items())))


def test_every_allowed_import_is_still_needed():
    stale = sorted(set(ALLOWED) - set(_all_imports()))
    assert not stale, f"remove these entries from ALLOWED: {stale}"


def test_the_guard_sees_every_import_form():
    forms = {
        "from tests.test_a import x": "test_a",
        "import tests.test_b as B": "test_b",
        "from tests import test_c": "test_c",
        "from .test_d import x": "test_d",
        "from . import test_e": "test_e",
        "def f():\n    from tests.test_f import x\n": "test_f",
    }
    for source, module in forms.items():
        assert {name for name, _ in _test_module_imports(ast.parse(source))} == {module}, source
    assert not _test_module_imports(ast.parse("from tests.helpers import x\nfrom tests import source_inventory_helpers"))
