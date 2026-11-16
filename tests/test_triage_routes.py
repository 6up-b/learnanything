"""Authored intervention routes used by value-of-information decisions."""

from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault


def test_route_table_is_seeded_data_over_ten_reasons(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    routes = repo.failure_triage_routes()
    assert {r["reason"] for r in routes} == {
        "memory_lapse",
        "unfamiliar_or_missing_knowledge",
        "schema_or_conceptual_hole",
        "false_belief_or_confusion",
        "procedure_execution",
        "method_selection",
        "coordination_or_integration",
        "task_interpretation",
        "surface_or_grading_fault",
        "unknown_or_ambiguous",
    }
    assert len(routes) == 10


def test_only_false_belief_and_unknown_reopen_a_diagnostic_episode(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    reopen = {r["reason"] for r in repo.failure_triage_routes() if r["reopens_diagnostic"]}
    assert reopen == {"false_belief_or_confusion", "unknown_or_ambiguous"}
