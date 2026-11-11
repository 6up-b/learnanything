"""What other test files use from ``tests/test_router_card_reading_gaps.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.sources import exam_material as EM

from tests.daily_plan_fakes import iso
from tests.mcp_c1a_landing_helpers import A, LAST


def _exam_passage(monkeypatch, *spans) -> None:
    """The exam predicate: these (extraction, span) passages are exam material."""

    material = EM.Material(spans=frozenset(spans))
    monkeypatch.setattr(EM, "exam_material",
                        lambda _vault, _repo: EM.ExamMaterial(material=material, held_out=EM.Material()))


def _gap(env, gap_id: str, source_kind: str, source_id: str, words: str) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO learner_text_gaps(id, source_kind, source_id, attempt_id, practice_item_id, "
            "anchor_learning_object_id, learner_text, chooser, context_judge, kind, action, algorithm_version, "
            "pipeline_version, created_at) VALUES (?, ?, ?, NULL, NULL, 'lo_m1', ?, 'context_model', ?, "
            "'misconception', 'unplaced', ?, 'v1', ?)",
            (gap_id, source_kind, source_id, words, "tutor" if source_kind == "tutor_question" else "gap_reader",
             A, iso(LAST)))
        connection.commit()
