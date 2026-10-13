"""The display read of a learning object's active errors under the Slice 1 split.

``Repository.active_errors_by_learning_object`` selects raw ``error_events``:
on a blind-graded (mvp-0.10+) vault those rows carry only the grader's
localization. ``active_errors_by_learning_object_overlaid`` lays each
attempt's live diagnosis over them, the way ``error_events_for_attempt`` does
for one attempt, so display surfaces (the Reader Guide, the TUI feedback
screen) show the diagnoser's statement. Joint-graded vaults read as stored.
"""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace

from learnloop.diagnosis.split import jobs as jobs_module
from learnloop.diagnosis.split.jobs import DONE, diagnosis_status
from learnloop.tui.screens.feedback import FeedbackScreen

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import NOW_ISO
from tests.split_live_helpers import drain_jobs, split_vault, submit

_DIAGNOSED = "The learner thinks V needs no transpose in the SVD."


class _StatementFake(ReviewFakeClient):
    """The M1 fake, with the diagnoser naming a misconception statement."""

    def __init__(self, *, causal_class: str = "learner_state", **kwargs):
        super().__init__(**kwargs)
        self.causal_class = causal_class

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        events = [
            event.model_copy(
                update={"misconception_statement": _DIAGNOSED, "causal_class": self.causal_class}
            )
            for event in result.event_diagnoses
        ]
        return result.model_copy(update={"event_diagnoses": events})


def test_overlaid_read_carries_the_diagnosers_statement_and_verdict(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, seed=False)
    client = _StatementFake()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE

    raw = repository.active_errors_by_learning_object("lo_svd_compute")
    overlaid = repository.active_errors_by_learning_object_overlaid("lo_svd_compute")

    assert [event.id for event in overlaid] == [event.id for event in raw]
    assert all(event.misconception_statement is None for event in raw)
    assert {event.misconception_statement for event in overlaid} == {_DIAGNOSED}
    # The diagnoser's verdict (learner_state, valid measurement), not the
    # grader's taxonomy prior.
    assert all(event.is_misconception for event in overlaid)
    # Grader-owned fields are kept.
    for before, after in zip(raw, overlaid):
        assert (after.error_type, after.severity, after.created_at, after.learning_object_id) == (
            before.error_type, before.severity, before.created_at, before.learning_object_id,
        )
    # The overlay is a read: the stored rows are unchanged.
    assert all(
        not event["misconception_statement"]
        for event in repository.raw_error_events_for_attempt(result.attempt_id)
    )


def test_overlaid_read_takes_the_diagnosers_not_a_misconception_verdict(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, seed=False)
    client = _StatementFake(causal_class="transient_execution")
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)

    raw = repository.active_errors_by_learning_object("lo_svd_compute")
    overlaid = repository.active_errors_by_learning_object_overlaid("lo_svd_compute")
    # The stored flag is the grader's taxonomy prior (a conceptual error is a
    # misconception prior here); the diagnoser called this one a slip.
    assert raw and all(event.is_misconception for event in raw)
    assert overlaid and not any(event.is_misconception for event in overlaid)
    assert {event.misconception_statement for event in overlaid} == {_DIAGNOSED}


def test_overlaid_read_keeps_events_of_other_attempts_and_without_an_attempt(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, seed=False)
    client = _StatementFake()
    diagnosed = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    pending = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V wrong")
    repository.insert_error_event({
        "id": "err-no-attempt", "learning_object_id": "lo_svd_compute",
        "error_type": "conceptual_slip", "severity": 0.2,
        "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": "A stored statement.",
    })

    raw = {event.id: event for event in repository.active_errors_by_learning_object("lo_svd_compute")}
    overlaid = {
        event.id: event for event in repository.active_errors_by_learning_object_overlaid("lo_svd_compute")
    }
    assert set(overlaid) == set(raw)
    diagnosed_ids = {e["id"] for e in repository.raw_error_events_for_attempt(diagnosed.attempt_id)}
    pending_ids = {e["id"] for e in repository.raw_error_events_for_attempt(pending.attempt_id)}
    assert diagnosed_ids and pending_ids
    for event_id in diagnosed_ids:
        assert overlaid[event_id].misconception_statement == _DIAGNOSED
    for event_id in pending_ids | {"err-no-attempt"}:
        assert overlaid[event_id] == raw[event_id]


def test_overlaid_read_equals_the_raw_read_on_a_joint_vault(tmp_path):
    _paths, vault, repository = split_vault(
        tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true"
    )
    client = _StatementFake()
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)

    for learning_object_id in vault.learning_objects:
        assert repository.active_errors_by_learning_object_overlaid(
            learning_object_id
        ) == repository.active_errors_by_learning_object(learning_object_id)


# -- the TUI feedback screen (display only) ---------------------------------------


class _Widget:
    def __init__(self) -> None:
        self.content = None

    def update(self, content) -> None:
        self.content = content


class _FeedbackStub:
    """Just enough of FeedbackScreen to run its rendering helpers headless."""

    _error_content = FeedbackScreen._error_content
    _run_inline_diagnosis = FeedbackScreen._run_inline_diagnosis

    def __init__(self, vault, repository) -> None:
        self.state = SimpleNamespace(vault=vault, repository=repository)
        self.widgets: dict[str, _Widget] = defaultdict(_Widget)

    def query_one(self, selector, _widget_type=None):
        return self.widgets[selector]


def test_tui_error_attributions_show_the_diagnosers_statement_once_diagnosed(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, seed=False)
    client = _StatementFake()
    result = submit(vault, repository, client)
    real_drain = jobs_module.drain
    monkeypatch.setattr(
        jobs_module,
        "drain",
        lambda vault, repository, **kwargs: real_drain(
            vault, repository, client_factory=lambda: client, embedding_factory=lambda: None, **kwargs
        ),
    )
    screen = _FeedbackStub(vault, repository)
    error_type = repository.raw_error_events_for_attempt(result.attempt_id)[0]["error_type"]

    # Rendered with the grade, before the inline diagnosis: the error type.
    assert error_type in screen._error_content(result).plain

    screen._run_inline_diagnosis(result)

    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE
    rendered = screen.widgets["#error-attributions"].content
    assert rendered is not None
    assert _DIAGNOSED in rendered.plain
    assert "misconception" in rendered.plain


def test_tui_error_attributions_are_not_rerendered_when_no_diagnosis_is_needed(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, seed=False)
    client = _StatementFake()
    result = submit(vault, repository, client, answer="A = U Sigma V^T")
    monkeypatch.setattr(jobs_module, "drain", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))
    screen = _FeedbackStub(vault, repository)

    screen._run_inline_diagnosis(result)

    assert "#error-attributions" not in screen.widgets
