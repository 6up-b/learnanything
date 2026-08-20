"""ING M7 — lightweight exam-readiness report + conflict resolution (§15/§10.2)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.proposals.conflict_resolution import ConflictResolutionError, resolve_conflict, conflict_with_audit
from learnloop.goals.exam_readiness import exam_readiness_report
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


def test_exam_readiness_report_is_deterministic_and_labels_ready_vs_demonstrated(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    vault = load_vault(root)

    report = exam_readiness_report(vault, repo, subject_id="linear-algebra")
    data = report.as_dict()
    assert data["display_rule"] == "ready_vs_demonstrated"
    assert data["rows"], "at least one blueprint/task-family row"
    row = data["rows"][0]
    # Ready (predicted) and Demonstrated (banked) are reported separately.
    assert "ready" in row and "demonstrated_fraction" in row
    assert row["facet_capabilities"]
    # normalized weights sum to ~1 over the declared distribution.
    total = sum(r["normalized_weight"] for r in data["rows"])
    assert abs(total - 1.0) < 1e-6
    # deterministic: a second run is byte-identical.
    assert exam_readiness_report(vault, repo, subject_id="linear-algebra").as_dict() == data


def test_exam_readiness_predicted_score_distribution_is_analytic(tmp_path):
    """ING M8: per-family + aggregate predicted score distribution, labelled
    predicted-vs-demonstrated, deterministic and Monte-Carlo-free."""

    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    vault = load_vault(root)

    report = exam_readiness_report(vault, repo, subject_id="linear-algebra")
    data = report.as_dict()
    # Aggregate predicted score = weight-normalized Σ wᵢ·pᵢ, reported separately
    # from the demonstrated fraction (never blended).
    assert data["predicted_score"] is not None
    assert "demonstrated_score" in data
    expected_mean = sum(
        r["normalized_weight"] * (r["ready"] or 0.0) for r in data["rows"]
    )
    assert abs(data["predicted_score"]["mean"] - round(expected_mean, 4)) < 1e-4
    for row in data["rows"]:
        assert row["predicted"]["n_items"] == 1  # no total supplied → one representative task
        p = row["ready"] or 0.0
        assert abs(row["predicted"]["variance"] - round(p * (1 - p), 6)) < 1e-4

    # Sizing the exam tightens per-family variance (more items → smaller variance).
    sized = exam_readiness_report(vault, repo, subject_id="linear-algebra", total_exam_items=20)
    for base_row, sized_row in zip(report.rows, sized.rows):
        if base_row.predicted and sized_row.predicted and sized_row.predicted["n_items"] > 1:
            assert sized_row.predicted["variance"] <= base_row.predicted["variance"]
    # Deterministic.
    assert exam_readiness_report(vault, repo, subject_id="linear-algebra").as_dict() == data


def test_conflict_resolution_preserves_locators_and_audit(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    conflict_id = repo.insert_source_conflict(
        entity_type="facet", entity_id="facet_symmetry_definition", statement="disagree",
        left_source_id="src_text", left_locator="span:s1",
        right_source_id="src_alt", right_locator="span:s9", clock=_CLOCK,
    )

    resolved = resolve_conflict(repo, conflict_id, resolution_kind="keep_both_scoped",
                                resolution={"scopes": ["textbook", "lecture"]},
                                actor="user", rationale="both are valid in context", clock=_CLOCK)
    assert resolved["status"] == "resolved"
    # both evidence locators are preserved untouched.
    assert resolved["left_locator"] == "span:s1" and resolved["right_locator"] == "span:s9"

    audit = conflict_with_audit(repo, conflict_id)
    assert len(audit["resolutions"]) == 1
    assert audit["resolutions"][0]["resolution_kind"] == "keep_both_scoped"

    # a second resolution attempt on the now-resolved conflict is rejected.
    with_error = False
    try:
        resolve_conflict(repo, conflict_id, resolution_kind="dismiss", clock=_CLOCK)
    except ConflictResolutionError:
        with_error = True
    assert with_error


def test_conflict_resolution_notation_mapping_materializes_mapping(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    conflict_id = repo.insert_source_conflict(
        entity_type="facet", entity_id="facet_symmetry_definition", statement="notation differs",
        left_locator="span:s1", right_locator="span:s2", clock=_CLOCK,
    )
    resolve_conflict(repo, conflict_id, resolution_kind="notation_mapping",
                     resolution={"canonical_notation": "A^T", "alternate_notation": "A'"},
                     clock=_CLOCK)
    mappings = repo.notation_mappings_for_entity("facet", "facet_symmetry_definition")
    assert any(m["canonical_notation"] == "A^T" and m["alternate_notation"] == "A'" for m in mappings)
