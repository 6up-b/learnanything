"""What an ingest job type is: its row in ``content/pipeline/job_types.py``.

``EXPECTED`` is the characterization: for every job type the host runs, the
handler that runs it and whether it applies vault content (the sidecar reloads
its vault after one), bumps Today's queue revision when it completes, runs in
the parallel lane, and waits for the learner's one AI OK before it starts. It
was first checked against the five lists the table replaced, unchanged.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.config.schema import AIRoutingConfig
from learnloop.content.pipeline import job_types as JT
from learnloop.content.pipeline.runner import IngestRunner, RunnerServices

SRC = Path(__file__).resolve().parents[1] / "src"

#: type: (handler name, applies_vault, affects_queue, parallel, waits_for_ai_ok)
EXPECTED: dict[str, tuple[str, bool, bool, bool, bool]] = {
    "import": ("handle_import", False, False, False, False),
    "auto_study_map": ("handle_auto_study_map", False, False, False, False),
    "legacy_ingest": ("handle_legacy_ingest", True, False, False, True),
    "exam_ingest": ("handle_legacy_ingest", True, False, False, True),
    "inventory": ("handle_inventory", False, False, False, True),
    "bootstrap_synthesis": ("handle_bootstrap_synthesis", True, False, False, True),
    "append_synthesis": ("handle_append_synthesis", True, False, False, True),
    "extraction_repair": ("handle_extraction_repair", False, False, False, False),
    "reader_quick_check": ("handle_reader_quick_check", False, False, True, True),
    "reader_exercise_import": ("handle_reader_exercise_import", True, True, False, True),
    "source_exercise_import": ("handle_source_exercise_import", True, False, False, True),
    "practice_expansion": ("handle_practice_expansion", True, True, False, True),
    "goal_population": ("handle_goal_population", True, True, False, True),
    "question_promotion": ("handle_question_promotion", True, True, False, True),
    "rung_variant": ("handle_rung_variant", True, True, False, True),
    "concept_animation": ("handle_concept_animation", False, False, False, True),
    "figure_rich": ("handle_figure_rich", False, False, False, True),
    "source_embedding_backfill": ("handle_source_embedding_backfill", False, False, False, True),
    "curriculum_coverage_on_extract": ("handle_curriculum_coverage_on_extract", False, False, False, False),
    "local_source_index": ("handle_local_source_index", False, False, False, False),
    "source_fallback_backfill": ("handle_source_fallback_backfill", False, False, False, False),
}


def _observed() -> dict[str, tuple[str, bool, bool, bool, bool]]:
    return {
        row.name: (row.handler.__name__, row.applies_vault, row.affects_queue, row.parallel, row.waits_for_ai_ok)
        for row in JT.JOB_TYPES
    }


def test_every_job_type_runs_as_characterized() -> None:
    assert _observed() == EXPECTED


def test_every_type_has_exactly_one_row_and_every_row_a_handler() -> None:
    names = [row.name for row in JT.JOB_TYPES]
    assert len(names) == len(set(names))
    assert all(callable(row.handler) for row in JT.JOB_TYPES)
    assert JT.default_handlers() == {row.name: row.handler for row in JT.JOB_TYPES}


def test_the_runner_runs_exactly_the_table(tmp_path) -> None:
    runner = IngestRunner(SimpleNamespace(sqlite_path=tmp_path / "state.sqlite"), vault_root=tmp_path,
                          worker_id="w")
    assert runner.handlers == JT.default_handlers()


def test_the_derived_lists_follow_the_flags() -> None:
    assert set(JT.applying_job_types()) == {name for name, row in EXPECTED.items() if row[1]}
    assert JT.parallel_job_types() == ("reader_quick_check",)
    assert JT.job_type("no_such_type") is None


def _job_spec_types() -> tuple[set[str], list[str]]:
    """Every job type a module of the source tree enqueues through ``JobSpec``: a literal, or a module constant."""

    found: set[str] = set()
    dynamic: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = ".".join(path.relative_to(SRC).with_suffix("").parts).removesuffix(".__init__")
        # A job type constant is often imported inside the function that enqueues it.
        origin = {alias.asname or alias.name: node.module for node in ast.walk(tree)
                  if isinstance(node, ast.ImportFrom) and node.module for alias in node.names}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "JobSpec"):
                continue
            arg = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "job_type"), None)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.add(arg.value)
            elif isinstance(arg, ast.Name) and isinstance(
                    value := getattr(importlib.import_module(origin.get(arg.id, module)), arg.id, None), str):
                found.add(value)
            else:
                dynamic.append(f"{module}:{node.lineno}")
    return found, dynamic


def test_every_job_type_the_code_enqueues_has_a_row() -> None:
    found, _dynamic = _job_spec_types()
    assert found, "the scan found no JobSpec call"
    assert found - set(EXPECTED) == set()


def test_every_client_route_is_a_routing_task() -> None:
    routes = {route for row in JT.JOB_TYPES for route in row.client_routes}
    assert routes <= set(AIRoutingConfig.model_fields)


#: The services' client each type's handler asks for, read from the handlers (``ctx.services.<method>``).
_CLIENTS = {
    "inventory": ("inventory_client",),
    "bootstrap_synthesis": ("synthesis_client",),
    "append_synthesis": ("synthesis_client",),
    "reader_quick_check": ("quick_check_client",),
    "reader_exercise_import": ("exercise_import_client",),
    "source_exercise_import": ("exercise_import_client",),
    "practice_expansion": ("synthesis_client",),
    "goal_population": ("synthesis_client",),
    "question_promotion": ("promotion_analysis_client", "promotion_authoring_client"),
    "rung_variant": ("rung_variant_client",),
    "concept_animation": ("animation_client",),
}


@pytest.mark.parametrize("name", sorted(_CLIENTS))
def test_a_rows_routes_are_the_routes_its_default_clients_resolve(name, tmp_path, monkeypatch) -> None:
    import learnloop.ai.routing as routing
    import learnloop.vault.loader as loader

    resolved: list[str] = []

    def ready_client_for_task(_root, _config, task, **_kwargs):
        resolved.append(task)
        return SimpleNamespace(client=SimpleNamespace(), runtime=None, provider_name="fake")

    monkeypatch.setattr(routing, "ready_client_for_task", ready_client_for_task)
    monkeypatch.setattr(loader, "load_vault", lambda _root: SimpleNamespace(config=None))
    ctx = SimpleNamespace(vault_root=tmp_path, bind_interruptible=lambda _client: None)
    services = RunnerServices()
    for method in _CLIENTS[name]:
        getattr(services, method)(ctx)
    row = JT.job_type(name)
    assert row is not None
    # The video client reads its route from the config directly (no fallback chain may redirect a billable video).
    assert tuple(resolved) == tuple(route for route in row.client_routes if route != "video_generation")


def test_the_legacy_lane_resolves_its_rows_route(tmp_path, monkeypatch) -> None:
    import learnloop.ai.routing as routing
    import learnloop.vault.loader as loader
    from learnloop.content.pipeline.runner import IngestRunnerError

    resolved: list[str] = []

    def ready_client_for_task(_root, _config, task, **_kwargs):
        resolved.append(task)
        return SimpleNamespace(client=None, runtime=SimpleNamespace(message="no provider", status="unavailable"))

    monkeypatch.setattr(routing, "ready_client_for_task", ready_client_for_task)
    monkeypatch.setattr(loader, "load_vault", lambda _root: SimpleNamespace(config=None))
    with pytest.raises(IngestRunnerError):
        RunnerServices().legacy_ingest(vault_root=tmp_path, source="s.md", subject_id="s", mode="canonical",
                                       progress=None, clock=None)
    assert resolved == list(JT.job_type("legacy_ingest").client_routes) == list(JT.job_type("exam_ingest").client_routes)
