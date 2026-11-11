"""What other test files use from ``tests/test_diagnosis_history_modes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.diagnosis.split.context import current_attempt_from

from tests.diagnosis_split_helpers import blind_record


def _current(vault, store, attempt_id="att_06_svd_fail"):
    attempt = store.attempt(attempt_id)
    item = vault.practice_items[attempt.practice_item_id]
    record = blind_record(
        score=2, max_points=4, criteria={"setup": 2, "result": 0},
        attributions=[{"error_type": "conceptual_slip", "evidence": "Blind evidence here.",
                       "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": attempt.learner_answer_md.split()[-1]},
                       "target_evidence_families": ["recall"], "resolution_status": "unresolved", "validity_scope": "valid_measurement"}],
        local_analysis="Blind local reading of this answer.",
    )
    return item, current_attempt_from(vault, item, attempt_id=attempt_id, completed_at=attempt.completed_at,
                                      learner_answer_md=attempt.learner_answer_md, blind_grade=record)
