"""What other test files use from ``tests/test_diagnosis_input_provenance.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import NOW_ISO
from tests.mcp_world import LO, build_world, hold_att_held, no_model_calls


SVD_WRONG = "A = U Sigma V wrong"
SVD_RIGHT = "A = U Sigma V^T"


def _wp() -> Any:
    """The write-time records (``db.stores.write_provenance``), imported late."""

    import learnloop.db.stores.write_provenance as module

    return module


def _dp() -> Any:
    """What a diagnosis read (``diagnosis.split.provenance``), imported late."""

    import learnloop.diagnosis.split.provenance as module

    return module


def _trace(context: dict[str, Any], attempt_id: str) -> dict[str, Any]:
    return next(trace for trace in context["recent_answer_traces"] if trace["attempt_id"] == attempt_id)


def _rows(repository: Any, kind: str | None = None) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT kind, record_id, writer, complete, incomplete_reasons_json, inputs_json, derived_from_json "
            "FROM text_write_provenance" + (" WHERE kind = ?" if kind else "") + " ORDER BY created_at, id",
            (kind,) if kind else (),
        ).fetchall()
    return [dict(row) for row in rows]


class ProvenanceFake(ReviewFakeClient):
    """The M1 fake with a chosen summary and, in the snapshot mode, the
    workspace activity the transport reports (``activity(workspace)``)."""

    def __init__(self, *, analysis: str = "The learner keeps the last factor untransposed.",
                 activity: Any = "unset", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.analysis = analysis
        self.activity = activity

    def workspace_activity(self) -> list[str] | None:
        if self.activity == "unset":
            return super().workspace_activity()
        if self.activity is None or not self.workspaces:
            return None
        return list(self.activity(self.workspaces[-1]))

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        return result.model_copy(update={"analysis_md": self.analysis})


# -- the chat world (mcp_world): the other reproductions ------------------------------------


@pytest.fixture
def world(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    hold_att_held(monkeypatch)
    return build_world(tmp_path / "w")


def _solve_pi_own(world, attempt_id: str = "att_own_solved", at_iso: str = "2026-09-30T09:00:00Z") -> None:
    """A later correct, pinned answer on ``pi_own``: its attempt window closes."""

    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES (?, 'pi_own', ?, 'short_answer', 'independent_attempt', 'SOLVED_8812 any row works', 1.0, 0, "
            "?, 'old', 'human', 'desktop_practice')", (attempt_id, LO, at_iso))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES (?, ?, 'correct', 1, 1, ?, 'acv_own')",
            (f"ge_{attempt_id}", attempt_id, NOW_ISO))
        connection.commit()


def _diagnose(world, diagnosis_id: str, analysis: str, reads: Any, *, attempt_id: str = "att_own") -> str:
    """A diagnosis written exactly as the job writes it (``jobs._persist``):
    its reads recorded in the transaction that inserts it."""

    from learnloop.diagnosis.split.jobs import record_diagnosis_reads

    proposal = {"analysis_md": analysis}
    with world.repository.atomic():
        record_diagnosis_reads(world.repository, diagnosis_id=diagnosis_id, proposal=proposal, reads=reads)
        world.repository.insert_attempt_diagnosis(
            diagnosis_id=diagnosis_id, attempt_id=attempt_id, diagnosis_prompt_version="test", mode="live",
            history_mode="full", status="completed", proposal=proposal, causal_view=None, validation_report=None,
            receipt=None)
    return diagnosis_id


def _own_reads(*topics: str, shown: tuple[Any, ...] = ()) -> Any:
    return _dp().reads_of_context(
        current_attempt_id="att_own", current_item_id="pi_own", current_learning_object_id=LO,
        learning_object_ids=topics or (LO,), attempts=(), hypotheses=(), registry=(), repairs=(),
    ).join(_dp().DiagnosisReads(attempts=shown))


def _misconception_from(world, misconception_id: str, statement: str, *, attempt_id: str,
                        diagnosis_id: str | None = None) -> None:
    """A belief normalized from the attempt's event (the normalizer's own
    provenance: the attempt's grading and the diagnosis over the event)."""

    from learnloop.diagnosis.misconceptions import _event_statement_provenance

    record = _event_statement_provenance(world.repository, attempt_id, {"diagnosis_id": diagnosis_id})
    world.repository.insert_misconception(id=misconception_id, learning_object_id=LO, statement=statement,
                                          severity=0.8, provenance=record, provenance_writer="normalizer")


def _belief(context: dict[str, Any], misconception_id: str) -> dict[str, Any]:
    return next(entry for entry in context["misconceptions"] if entry["misconception_id"] == misconception_id)


def _record_drafted(world, lo_id: str, attempt_id: str, item_id: str) -> None:
    """The drafter's record for a prerequisite drafted from a stuck answer,
    written as the gap pipeline writes it (``pipeline._record_written_texts``)."""

    from learnloop.diagnosis.text_gaps.actions import ActionOutcome
    from learnloop.diagnosis.text_gaps.contract import LearnerText
    from learnloop.diagnosis.text_gaps.pipeline import _record_written_texts
    from learnloop.diagnosis.text_gaps.provenance import drafter_record

    vault = load_vault(world.root)
    text = LearnerText(source_kind="stuck_answer", source_id=attempt_id, text="stuck", context_judge="gap_reader",
                       created_at=NOW_ISO, subject_id="linear-algebra", anchor_learning_object_ids=(LO,),
                       practice_item_id=item_id, attempt_id=attempt_id)
    with world.repository.atomic():
        connection = world.repository.connection()
        drafted = drafter_record(connection, vault, text, None, subject_id="linear-algebra")
        outcome = ActionOutcome("created_prerequisite", created_learning_object_id=lo_id,
                                created_provenance=drafted.as_json())
        _record_written_texts(connection, vault, text, outcome, gap_id=f"gap_for_{lo_id}", learner_words="stuck",
                              clock=None)


def _question(world, question_id: str, *, context: str, item: str | None, attempt: str | None = None,
              contract: str | None = None, text: str = "is a row swap a sign flip?", gap_id: str | None = None,
              record: bool = True) -> str:
    """A learner question (``insert_question_event``, Q10) and its gap, with
    the gap's words recorded as the gap pipeline records them."""

    from learnloop.diagnosis.text_gaps.actions import ActionOutcome
    from learnloop.diagnosis.text_gaps.pipeline import _record_written_texts
    from learnloop.diagnosis.text_gaps.sources import tutor_question_text
    from tests.mcp_world import gap_row

    world.repository.insert_question_event({
        "id": question_id, "context": context, "practice_item_id": item, "attempt_id": attempt,
        "question_md": text, "answer_md": "an answer", "answer_status": "answered",
        **({"assessment_contract_version_id": contract} if contract else {}),
        "created_at": "2026-09-25T09:00:00Z",
    })
    gap_id = gap_id or f"gap_{question_id}"
    with world.repository.connection() as connection:
        gap_row(connection, gap_id, source_kind="tutor_question", source_id=question_id, attempt_id=attempt,
                item_id=item, text=text, target_kind=None, target_id=None, action="signal_only")
        connection.commit()
    if record:
        vault = load_vault(world.root)
        learner_text = tutor_question_text(vault, world.repository, question_id)
        with world.repository.atomic():
            _record_written_texts(world.repository.connection(), vault, learner_text, ActionOutcome("signal_only"),
                                  gap_id=gap_id, learner_words=text, clock=None)
    return gap_id


def _gap(context: dict[str, Any], gap_id: str) -> dict[str, Any]:
    return next(entry for entry in context["open_learner_text_gaps"] if entry["gap_id"] == gap_id)
