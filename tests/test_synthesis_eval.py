"""ING M6 — synthesis quality eval harness (spec §14 / §15 M6).

Deterministic when given a canned proposal: scores a synthesized study map
against the hand-authored gold registry for the symmetric-matrices chapter.
"""

from __future__ import annotations

from learnloop.services.synthesis_eval import (
    default_gold_path,
    evaluate,
    extract_candidate_from_vault,
    load_gold,
)
from learnloop.services.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload, _setup


def test_gold_file_loads_and_is_prompt_versioned():
    gold = load_gold(default_gold_path())
    assert gold["prompt_version"] == "mvp-0.7-source-set-synthesis-bootstrap"
    assert len(gold["facets"]) == 2


def test_canned_synthesis_scores_perfect_against_matching_gold(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=None, apply=True)
    vault = load_vault(root)
    candidate = extract_candidate_from_vault(vault, prompt_version="mvp-0.7-source-set-synthesis-bootstrap")
    report = evaluate(load_gold(default_gold_path()), candidate)

    assert report.facet_recall == 1.0
    assert report.facet_precision == 1.0
    assert report.duplicate_rate == 0.0
    assert report.over_fragmentation_rate == 0.0
    assert report.recipe_validity == 1.0
    assert report.criterion_target_accuracy == 1.0
    assert report.provenance_accuracy == 1.0
    assert report.repair_distinctness == 1.0
    assert report.missing_conditions_count == 0


def test_over_fragmentation_and_duplicate_are_reported():
    gold = load_gold(default_gold_path())
    # Candidate splits the single definition facet into two near-identical copies.
    candidate = {
        "prompt_version": gold["prompt_version"],
        "facets": [
            {
                "id": "f1",
                "kind": "definition",
                "claim": "A real square matrix is symmetric exactly when A^T = A.",
                "instructional_repairs": ["contrast symmetric and orthogonal matrices"],
                "provenance": [{"role": "primary_textbook", "span_id": "s1"}],
            },
            {
                "id": "f2",
                "kind": "definition",
                "claim": "A real square matrix is symmetric exactly when A^T = A.",
                "instructional_repairs": ["contrast symmetric and orthogonal matrices"],
                "provenance": [{"role": "primary_textbook", "span_id": "s1"}],
            },
        ],
        "recipes": [],
        "criterion_targets": [],
    }
    report = evaluate(gold, candidate)
    assert report.duplicate_rate > 0.0  # identical fingerprints
    assert report.facet_recall < 1.0  # only one gold facet covered
    assert any("unmatched" in note for note in report.notes)


def test_low_provenance_when_only_exam_role_cited():
    gold = load_gold(default_gold_path())
    candidate = {
        "prompt_version": gold["prompt_version"],
        "facets": [
            {
                "id": "facet_symmetry_definition",
                "claim": "A real square matrix is symmetric exactly when A^T = A.",
                "instructional_repairs": ["r"],
                "provenance": [{"role": "exam", "span_id": "s1"}],
            }
        ],
        "recipes": [],
        "criterion_targets": [],
    }
    report = evaluate(gold, candidate)
    assert report.provenance_accuracy == 0.0  # exam role is not semantic authority


def test_repair_distinctness_flags_false_distinction():
    gold = load_gold(default_gold_path())
    # two facets matched to the two distinct gold facets but sharing repairs.
    candidate = {
        "prompt_version": gold["prompt_version"],
        "facets": [
            {"id": "a", "claim": "A real square matrix is symmetric exactly when A^T = A.",
             "instructional_repairs": ["same"], "provenance": [{"role": "reference", "span_id": "s1"}]},
            {"id": "b", "claim": "The spectral theorem applies to real symmetric matrices.",
             "instructional_repairs": ["same"], "provenance": [{"role": "reference", "span_id": "s2"}]},
        ],
        "recipes": [],
        "criterion_targets": [],
    }
    report = evaluate(gold, candidate)
    assert report.repair_distinctness == 0.0
