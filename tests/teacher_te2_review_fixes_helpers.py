"""What other test files use from ``tests/test_teacher_te2_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _cells(lesson):
    keep = ("facet_id", "capability_key", "practice_item_id", "recall_alpha", "recall_beta", "raw_coverage_mass",
            "independent_evidence_mass")
    return sorted(tuple("" if getattr(cell, key) is None else getattr(cell, key) for key in keep)
                  for cell in lesson.repository.canonical_facet_recall_states())


def _identity_model(repository, *, prompt, schema, tag):
    """A grader_identity-scope calibration model for the (``ai``, prompt, schema) grader, told apart by ``tag``."""

    from learnloop.attempts import grader_calibration as gc
    from learnloop.attempts.outcome_schemas import COARSE_RESPONSE_SLUG, ensure_builtin_schemas

    ensure_builtin_schemas(repository)
    version = repository.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    gih = gc.grader_identity_hash(provider="ai", model_revision=None, prompt_version=prompt,
                                  output_schema_version=schema)
    model_id = repository.insert_calibration_model(
        model={"semver": "0.1.0", "content_hash": f"te2-f7-{tag}", "scope_level": "grader_identity",
               "grader_provider": "ai", "grading_prompt_version": prompt, "grader_output_schema_version": schema,
               "grader_identity_hash": gih, "outcome_schema_id": version["schema_id"],
               "outcome_schema_version": int(version["version"]), "backoff_chain_json": "[]",
               "status": "heuristic"},
        alphas={"success": {"success|high": 9.0}, "other": {"other|high": 1.0}},
    )
    return gih, model_id
