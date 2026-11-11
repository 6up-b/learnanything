"""What other test files use from ``tests/test_pfc_unassessed_readers.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.field.outcomes import load_facet_rows
from learnloop.substrate.canonical_projection import UNVERIFIED_CRITERION_BLOCK


def _field_outcomes(vault, repository, attempt_id: str) -> dict[str, float]:
    with repository.connection() as connection:
        return {
            row.facet_id: row.outcome
            for row in load_facet_rows(connection, vault, legacy_fallback="current_content")
            if row.attempt_id == attempt_id
        }


_BASE_BLOCK = json.dumps(
    {"targets": [], "negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK},
    sort_keys=True, separators=(",", ":"),
)


def _as_the_base_implementation_wrote_it(patch) -> None:
    """The live door exactly as ``mvp-0.10`` shipped before the rule (22023ab4).

    The three write-time differences, and nothing else: the unverified row's
    block carried no interpretation mark; the grade was the grader's own
    derived score (kept points included); the gate recorded no
    ``assessed_shortfall``. The shared step got no unassessed set (the base
    door handed the unverified ids to ``apply_attempt`` only for stamping),
    which the wrapper reproduces by stamping the base block itself.
    """

    from dataclasses import replace

    from learnloop.attempts import attempts as attempts_module
    from learnloop.attempts import grading_support as support_module

    original_apply = attempts_module.apply_attempt

    def base_apply(vault, repository, attempt, *, clock=None, **kwargs):
        unverified = set(attempt.unverified_criterion_ids)
        if unverified:
            rows = [
                {**row, "attribution_json": _BASE_BLOCK}
                if row.get("criterion_id") in unverified and row.get("attribution_json") is None
                else row
                for row in attempt.grade.evidence_rows
            ]
            attempt = replace(
                attempt, grade=replace(attempt.grade, evidence_rows=rows), unverified_criterion_ids=()
            )
        return original_apply(vault, repository, attempt, clock=clock, **kwargs)

    def base_score(rubric, points, fatal_errors, *, unassessed_criterion_ids, answer_validated=True):
        return attempts_module.calculate_rubric_score(rubric, dict(points), list(fatal_errors))

    original_run = support_module.request_blind_grading_run

    def base_run(*args, **kwargs):
        run = original_run(*args, **kwargs)
        for key in ("assessed_shortfall", "unverified_interpretation"):
            run.grading_support.pop(key, None)
        return run

    patch.setattr(attempts_module, "apply_attempt", base_apply)
    patch.setattr(attempts_module, "assessed_rubric_score", base_score)
    patch.setattr(support_module, "request_blind_grading_run", base_run)
