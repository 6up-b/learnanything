from __future__ import annotations

import pytest

from tests.helpers import create_basic_vault, seed_due_item


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 — registers methods
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    context = SidecarContext()
    context.load(tmp_path / "vault")
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_goals_list_includes_report_for_active_goals(ctx):
    out = _call(ctx, "goals_list", {})
    assert out["version"] == 1
    goal = out["goals"][0]
    assert goal["id"] == "goal_linear_algebra_ml"
    assert goal["report"]["total"] > 0
    assert 0 <= goal["report"]["atRiskCount"] <= goal["report"]["total"]
    # Dual-axis + pace fields for the banner.
    report = goal["report"]
    assert {
        "certifiedCount",
        "examinedCount",
        "attainmentFraction",
        "predictedRecallMean",
        "attemptsRemaining",
        "attemptsRemainingIsPartial",
        "pace",
        "latestExam",
    } <= set(report)
    assert report["attainmentFraction"] is None or 0.0 <= report["attainmentFraction"] <= 1.0
    assert {
        "attemptsPerDay",
        "attemptsLast14d",
        "daysLeft",
        "attemptsRemaining",
        "neededPerDay",
        "onPace",
        "attemptsLogged",
    } <= set(report["pace"])
    assert report["latestExam"] is None  # no exam taken in this fixture


def test_goal_report_lists_at_risk_facets(ctx):
    out = _call(ctx, "get_goal_report", {"goalId": "goal_linear_algebra_ml"})
    report = out["report"]
    assert len(report["atRisk"]) == report["atRiskCount"]
    entry = report["atRisk"][0]
    assert {
        "learningObjectId",
        "facetId",
        "label",
        "currentRecall",
        "projectedRecall",
        "predictedCurrent",
        "predictedAtHorizon",
        "evidenceMass",
        "certified",
        "attemptsToCertify",
    } <= set(entry)
    # Sorted worst-first: uncertified before certified, low predictions first.
    keys = [(f["certified"], f["predictedAtHorizon"]) for f in report["atRisk"]]
    assert keys == sorted(keys)


def test_create_goal_writes_yaml_and_reloads(ctx):
    created = _call(
        ctx,
        "create_goal",
        {
            "title": "Exam prep!",
            "targetRecall": 0.9,
            "concepts": ["singular_value_decomposition"],
            "facets": [],
            "examEnabled": True,
            "dueAt": "2026-08-15T00:00:00Z",
        },
    )
    goal = created["goal"]
    assert goal["id"] == "goal_exam_prep"
    assert goal["targetRecall"] == pytest.approx(0.9)
    assert goal["exam"]["enabled"] is True
    assert goal["report"]["total"] > 0

    # Duplicate title gets a distinct id.
    again = _call(
        ctx,
        "create_goal",
        {
            "title": "Exam prep!",
            "targetRecall": 0.8,
            "concepts": ["singular_value_decomposition"],
            "facets": [],
            "examEnabled": False,
        },
    )
    assert again["goal"]["id"] == "goal_exam_prep_2"


def test_create_goal_rejects_empty_scope(ctx):
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError):
        _call(
            ctx,
            "create_goal",
            {"title": "Nothing", "targetRecall": 0.8, "concepts": [], "facets": [], "examEnabled": False},
        )


def test_update_goal_status_and_paused_goals_skip_reports(ctx):
    out = _call(ctx, "update_goal_status", {"goalId": "goal_linear_algebra_ml", "status": "paused"})
    assert out["goal"]["status"] == "paused"
    assert out["goal"]["report"] is None
    listed = _call(ctx, "goals_list", {})
    assert listed["goals"][0]["status"] == "paused"


def test_goal_feasibility_transient_probe(ctx):
    out = _call(
        ctx,
        "goal_feasibility",
        {"concepts": ["singular_value_decomposition"], "facets": [], "targetRecall": 0.8},
    )
    assert out["scopeFacetCount"] > 0
    assert out["uncoveredConcepts"] == []
    # Unknown concept has no LOs -> uncovered.
    missing = _call(
        ctx,
        "goal_feasibility",
        {"concepts": ["concept_nonexistent"], "facets": [], "targetRecall": 0.8},
    )
    assert missing["uncoveredConcepts"] == ["concept_nonexistent"]


def test_goal_report_series_endpoint(ctx):
    out = _call(
        ctx,
        "get_goal_report_series",
        {"goalId": "goal_linear_algebra_ml", "maxPoints": 3},
    )
    assert out["goalId"] == "goal_linear_algebra_ml"
    assert 1 <= len(out["series"]) <= 3
    assert {
        "at",
        "onTrackCount",
        "total",
        "onTrackFraction",
        "certifiedCount",
        "examinedCount",
        "attainmentFraction",
        "predictedRecallMean",
    } <= set(out["series"][-1])
