"""The per-step selector (``scripts/affected_tests.py``, refactor step A6): its fallback and its import tracing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def selector():
    spec = importlib.util.spec_from_file_location("affected_tests_script", ROOT / "scripts" / "affected_tests.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        yield module, module.Graph()
    finally:
        sys.modules.pop(spec.name, None)


@pytest.mark.parametrize("path", ["tests/conftest.py", "tests/helpers.py", "pyproject.toml", "uv.lock",
                                  "migrations/001_initial.sql", "src/learnloop/db/connection.py"])
def test_a_path_every_test_depends_on_falls_back_to_the_whole_suite(selector, path):
    module, graph = selector
    result = module.select([path], graph)
    assert result["mode"] == "full" and result["tests"] == ["tests"] and result["reasons"]


def test_a_module_selects_the_tests_importing_it_and_nothing_unrelated(selector):
    module, graph = selector
    result = module.select(["src/learnloop/hints/chooser.py"], graph)
    assert result["mode"] == "selected"
    assert "tests/test_workbench_chooser.py" in result["tests"]
    assert "tests/test_ad23_sim.py" not in result["tests"]
    assert result["tests"] == sorted(result["tests"])
    # Deterministic: the same change gives the same list.
    assert module.select(["src/learnloop/hints/chooser.py"], graph) == result


def test_depth_widens_the_selection_and_never_narrows_it(selector):
    module, graph = selector
    near = set(module.select(["src/learnloop/hints/chooser.py"], graph, depth=0)["tests"])
    wide = set(module.select(["src/learnloop/hints/chooser.py"], graph, depth=2)["tests"])
    assert near and near <= set(module.select(["src/learnloop/hints/chooser.py"], graph)["tests"]) <= wide


def test_a_changed_test_file_selects_itself_and_a_doc_selects_only_tests_naming_it(selector):
    module, graph = selector
    assert module.select(["tests/test_rofu_weeks.py"], graph)["tests"] == ["tests/test_rofu_weeks.py"]
    named = module.select(["tests/cli_surface.json"], graph)["tests"]
    assert "tests/test_cli_help_snapshot.py" in named
    assert all("cli_surface.json" in (ROOT / path).read_text(encoding="utf-8") for path in named)
    # Built here, so not even this file names it.
    unnamed = "docs/reviews/" + "-".join(("no", "test", "names", "this")) + ".md"
    assert module.select([unnamed], graph) == {"mode": "selected", "reasons": [], "tests": []}


def test_a_test_helper_module_passes_its_importers_through(selector):
    module, graph = selector
    selected = module.select(["tests/router_mixture_helpers.py"], graph)["tests"]
    assert "tests/test_ih2_one_open_offer.py" in selected
