"""The per-step selector (``scripts/affected_tests.py``, refactor step A6): its fallback and its import tracing."""

from __future__ import annotations

import importlib.util
import subprocess
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


def test_a_deleted_module_falls_back_to_the_whole_suite(selector, monkeypatch):
    # The graph reads the files that exist, so deleting chooser.py also drops
    # tests/test_workbench_chooser.py's import of it: selecting from the graph finds nothing.
    module, _graph = selector
    deleted = "src/learnloop/hints/chooser.py"
    files = module._python_files()
    monkeypatch.setattr(module, "_python_files", lambda: [p for p in files if p != deleted])
    result = module.select([deleted], module.Graph())
    assert result["mode"] == "full" and result["tests"] == ["tests"]
    assert any(reason.startswith(deleted) for reason in result["reasons"])


def test_a_rename_lists_the_old_path_too(selector, tmp_path, monkeypatch):
    module, _graph = selector

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / "src" / "learnloop").mkdir(parents=True)
    (tmp_path / "src" / "learnloop" / "old_name.py").write_text("X = 1\n", encoding="utf-8")
    git("init", "-q", "-b", "trunk")
    git("add", "-A")
    git("commit", "-q", "-m", "one")
    git("mv", "src/learnloop/old_name.py", "src/learnloop/new_name.py")
    git("commit", "-q", "-m", "two")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    assert {"src/learnloop/old_name.py", "src/learnloop/new_name.py"} <= set(module.changed_paths("HEAD~1"))


def test_a_module_named_by_its_source_path_reaches_the_tests_of_the_code_naming_it(selector):
    # params/parameter_registry.py names local_embeddings/pins.py only as a path in
    # MODULE_INVENTORY, then imports it and reads its source; the registry audit guards
    # pins.py's numeric constants through it.
    module, graph = selector
    assert "learnloop.local_embeddings.pins" in graph.imports["learnloop.params.parameter_registry"]
    assert "tests/test_registry_audit.py" in module.select(["src/learnloop/local_embeddings/pins.py"], graph)["tests"]
    # A source guard naming the file it reads is selected by a change to that file.
    assert "learnloop.source_retrieval.note_gaps" in graph.imports["tests.test_notes_never_read"]


def test_a_module_a_package_registers_reaches_the_tests_of_the_registry(selector):
    # learnloop_sidecar/handlers/__init__.py imports every handler to fill METHOD_REGISTRY;
    # tests/test_sidecar_epigraphs.py reaches its handler only through learnloop_sidecar.server.
    module, graph = selector
    assert "learnloop_sidecar.server" not in graph.imports["learnloop_sidecar.handlers.epigraphs"]
    selected = module.select(["src/learnloop_sidecar/handlers/epigraphs.py"], graph)["tests"]
    assert "tests/test_sidecar_epigraphs.py" in selected


def test_a_module_attribute_string_names_its_module(selector):
    # "learnloop.daily_plan.estimates:load_duration_evidence" names the module before the colon.
    module, graph = selector
    assert "learnloop.daily_plan.estimates" in graph.imports["tests.test_ad_guard_reachable_reads"]


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
    # Built here: a literal path would make this file a source guard of it (it names it).
    changed = "/".join(("tests", "test_rofu_weeks.py"))
    assert module.select([changed], graph)["tests"] == [changed]
    named = module.select(["tests/cli_surface.json"], graph)["tests"]
    assert "tests/test_cli_help_snapshot.py" in named
    assert all("cli_surface.json" in (ROOT / path).read_text(encoding="utf-8") for path in named)
    # Built here, so not even this file names it.
    unnamed = "docs/reviews/" + "-".join(("no", "test", "names", "this")) + ".md"
    assert module.select([unnamed], graph) == {"mode": "selected", "reasons": [], "tests": []}


def test_a_test_module_imported_by_another_passes_its_importers_through(selector):
    # test_p2_leakage_suite reruns test_reader_dialogue's case (tests/test_test_layout.py's one
    # allowed kind of test-to-test import) and does not import the reader's dialogue itself.
    module, graph = selector
    selected = module.select(["src/learnloop/reader/reader_dialogue.py"], graph, depth=0)["tests"]
    assert {"tests/test_reader_dialogue.py", "tests/test_p2_leakage_suite.py"} <= set(selected)
    # StuckFake backs test_hint_h2b_review's grader fixture, which test_workbench_help_kill_switch
    # imports: both through helper modules since refactor step T1.
    changed = "/".join(("tests", "stuck_prompt_helpers.py"))
    selected = module.select([changed], graph)["tests"]
    assert {"tests/test_hint_h2b_review.py", "tests/test_workbench_help_kill_switch.py"} <= set(selected)


def test_a_test_helper_module_passes_its_importers_through(selector):
    module, graph = selector
    selected = module.select(["tests/router_mixture_helpers.py"], graph)["tests"]
    assert "tests/test_ih2_one_open_offer.py" in selected
