"""PF-c unassessed criteria, read the same way outside the grade (Codex review).

The stage made a PF-c unverified criterion unassessed in the grade, the
canonical projection, the evidence timeline and the attempt step. The review
found readers that still turned it into evidence:

* F1: the attempt step and the learner field fell back to "every facet gets
  the attempt's outcome" when an item has no criterion -> facet map, so the
  unverified criterion's facet still got credit there;
* F2: an attempt with NOTHING assessed (correct only for scheduling) could
  confirm a repair through the cold-retry hook;
* F3: a pinned probe's deterministic sensor read the unverified criterion's
  raw points as a measured feature;
* F4: the diagnoser's history listed it as a failed criterion and accepted a
  recurrence citation on it;
* F5: records written before the rule carried no mark of the interpretation
  they were written under;
* F6: retention eligibility still read the informational review flag as an
  unresolved grade.

Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    assessed_rubric_score,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.grading_support import UNVERIFIED_REVIEW_REASON
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.field.outcomes import load_facet_rows
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import (
    UNVERIFIED_CRITERION_BLOCK,
    project_canonical_facet_state,
    unassessed_evidence_row,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at
from tests.split_live_helpers import ReadyRuntime, split_vault, submit
from tests.test_field_split_outcomes import _ZeroEverythingWithoutAttribution
from tests.test_pfc_unverified_unassessed import (
    CLOCK,
    ITEM,
    VERIFYING_ANSWER,
    _PartialWithoutAttribution,
    _mass,
    _mapped_split_vault,
)


def _field_outcomes(vault, repository, attempt_id: str) -> dict[str, float]:
    with repository.connection() as connection:
        return {
            row.facet_id: row.outcome
            for row in load_facet_rows(connection, vault, legacy_fallback="current_content")
            if row.attempt_id == attempt_id
        }


def _apply_graded(
    vault,
    repository,
    item_id: str,
    *,
    points: dict[str, float],
    unverified: tuple[str, ...] = (),
    clock,
    attempt_type: str = "independent_attempt",
    presentation_id: str | None = None,
    primed: bool = False,
):
    """One graded attempt through the shared step, as the live door hands it:
    the grade over the assessed criteria, the unverified ones stamped."""

    item = vault.practice_items[item_id]
    rubric = resolved_rubric(vault, item)
    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U Sigma V^T",
                attempt_type=attempt_type,
                probe_presentation_id=presentation_id,
                primed=primed,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=assessed_rubric_score(rubric, points, [], unassessed_criterion_ids=unverified),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": new_ulid(),
                        "criterion_id": criterion_id,
                        "points_awarded": float(awarded),
                        "evidence": "graded",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 3,
                        "created_at": now_iso,
                    }
                    for criterion_id, awarded in points.items()
                ],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=UNVERIFIED_REVIEW_REASON if unverified else None,
                feedback_md="",
                repair_suggestions=[],
            ),
            unverified_criterion_ids=tuple(unverified),
        ),
        clock=clock,
    )


# -- F5: each record names the interpretation it was written under ------------------------


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

    def base_score(rubric, points, fatal_errors, *, unassessed_criterion_ids):
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


def test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded(tmp_path, monkeypatch):
    """F5: replay never reinterprets a base-implementation PF-c record (its
    persisted 3/4 and its M2 evidence stay paired); a new record carries the
    unassessed mark; a regrade is the upgrade path."""

    _paths, vault, repository = _mapped_split_vault(tmp_path)
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")
    with monkeypatch.context() as patch:
        _as_the_base_implementation_wrote_it(patch)
        base = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)
    support = repository.latest_blind_grade_record(base.attempt_id)["record"]["grading_support"]
    assert "assessed_shortfall" not in support and "unverified_interpretation" not in support
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(base.attempt_id)}
    assert json.loads(rows["result"].attribution_json) == json.loads(_BASE_BLOCK)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    attempt = repository.fetch_practice_attempt(base.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (3, 0.75)
    debug = repository.attempt_debug_payload(base.attempt_id)
    assert "unassessed_criteria" not in debug
    assert debug["facet_outcomes"]["recall"] == pytest.approx(0.5)
    # The M2 projection: the kept point is credited, the shortfall is no failure.
    positive, negative = _mass(repository, "recall")
    assert positive > recall_before[0]
    assert negative == pytest.approx(recall_before[1])
    m2_recall = (positive, negative)
    # Identified: an unverified row, but not one written under the unassessed rule.
    from learnloop.substrate.canonical_projection import unverified_evidence_row

    assert unverified_evidence_row(rows["result"].attribution_json)
    assert not unassessed_evidence_row(rows["result"].attribution_json)

    # An identical answer graded now is written under the rule, and marked so.
    new = submit(
        vault, repository, _PartialWithoutAttribution(), item_id="pi_svd_compute_002",
        answer="Another route.\nFinal answer: U Sigma V^T",
    )
    new_rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(new.attempt_id)}
    assert unassessed_evidence_row(new_rows["result"].attribution_json)
    new_support = repository.latest_blind_grade_record(new.attempt_id)["record"]["grading_support"]
    assert new_support["unverified_interpretation"] == "unassessed"
    assert (repository.fetch_practice_attempt(new.attempt_id)["rubric_score"]) == 4
    assert _mass(repository, "recall") == pytest.approx(m2_recall)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.fetch_practice_attempt(base.attempt_id)["rubric_score"] == 3
    assert _mass(repository, "recall") == pytest.approx(m2_recall)

    # The upgrade path: a regrade writes the record again under the rule.
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(base.attempt_id),
        runtime=ReadyRuntime(), client=_PartialWithoutAttribution(), grading_source="ai", clock=None,
    )
    upgraded = repository.fetch_practice_attempt(base.attempt_id)
    assert (upgraded["rubric_score"], upgraded["correctness"]) == (4, 1.0)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(base.attempt_id)}
    assert unassessed_evidence_row(rows["result"].attribution_json)
    assert repository.attempt_debug_payload(base.attempt_id)["unassessed_criteria"] == ["result"]
    assert _mass(repository, "recall") == pytest.approx(recall_before)
