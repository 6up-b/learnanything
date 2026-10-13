""""Write what you can" replaces "I don't know" (mvp-0.13).

Fakes only: the blind grader and diagnoser are ``tests.diagnosis_fakes``
answering from the real prompts, so the stuck prompt, wire models, validators
and persistence are exercised without a network or a paid call.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_ai_required,
    complete_self_graded_attempt,
)
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.attempts.stuck import (
    STUCK_PROMPT_TEXT,
    STUCK_READING_KEY,
    StuckReading,
    stuck_answers,
    stuck_attempt_type,
    stuck_prompt_active,
    verified_stuck_reading,
)
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.jobs import NOT_NEEDED, diagnosis_status
from learnloop.field.outcomes import load_attempt_rows
from learnloop.field.signals import (
    FAST_TRACK_BLOCKING_TYPES,
    STUCK_CONFUSION_SIGNAL,
    blocks_fast_track,
    confusion_blocks_fast_track,
    load_interaction_signals,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import set_algorithm_version
from tests.split_live_helpers import ReadyRuntime, append_config, at, drain_jobs, split_vault

ITEM = "pi_svd_compute_001"
LO = "lo_svd_compute"


class StuckFake(ReviewFakeClient):
    """The M1/M2 fake, plus a stuck reading whenever the prompt asks for one."""

    def __init__(self, *, reading: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reading = reading or {"attempts_answer": True, "describes_confusion": False, "confusion_quote": ""}
        self.contexts: list[dict] = []

    def _blind_grading(self, request, context):
        self.contexts.append(context)
        model = request.result_model
        if "stuck_reading" not in getattr(model, "model_fields", {}):
            return super()._blind_grading(request, context)
        base_model = model.__mro__[1]
        base = super()._blind_grading(SimpleNamespace(result_model=base_model), context)
        return model.model_validate({**base.model_dump(mode="json"), "stuck_reading": self.reading})

    def _grading(self, request, context):
        # The joint grader (split off): the stuck reading when the joint
        # prompt asks for one (review F3), the plain proposal otherwise.
        self.contexts.append(context)
        base = super()._grading(request, context)
        model = request.result_model
        if "stuck_reading" not in getattr(model, "model_fields", {}):
            return base
        return model.model_validate({**base.model_dump(mode="json"), "stuck_reading": self.reading})


class RefusingClient(ReviewFakeClient):
    """Any model call is a test failure (the empty path has nothing to grade)."""

    def complete(self, request):  # pragma: no cover - must not run
        raise AssertionError(f"no model call expected, got {request.purpose}")


def _stuck_vault(tmp_path, *, config: str = ""):
    return split_vault(tmp_path, version="mvp-0.13", config=config)


def _draft(answer: str, *, stuck: bool = True, **kwargs) -> AttemptDraft:
    return AttemptDraft(
        practice_item_id=kwargs.pop("item_id", ITEM),
        learner_answer_md=answer,
        attempt_type=kwargs.pop("attempt_type", "independent_attempt"),
        declared_stuck=stuck,
        **kwargs,
    )


def _grade(vault, repository, client, draft, *, when=21):
    from learnloop.clock import FrozenClock

    clock = FrozenClock(at(when))
    result = complete_attempt_with_ai_required(
        vault, repository, draft, runtime=ReadyRuntime(), ai_client=client, clock=clock
    )
    run_post_attempt_pipeline(vault, repository, result=result, clock=clock)
    return result


def _field_row(vault, repository, attempt_id):
    with connect(repository.sqlite_path, read_only=True) as connection:
        # The scheduler never scored these items, so their graded revision is
        # the current content (the vault's legacy fallback, stated here).
        rows = {
            row.attempt_id: row
            for row in load_attempt_rows(connection, vault, legacy_fallback="current_content")
        }
    return rows[attempt_id]


# -- the gate -------------------------------------------------------------------


def test_the_successor_gates_the_control_and_the_switch_restores_it(tmp_path):
    for version in ("mvp-0.10", "mvp-0.11", "mvp-0.12"):
        _paths, vault, _repository = split_vault(tmp_path / version, version=version)
        assert not stuck_prompt_active(vault), version
    _paths, vault, _repository = _stuck_vault(tmp_path / "b")
    assert stuck_prompt_active(vault)
    _paths, vault, _repository = _stuck_vault(tmp_path / "c", config="[stuck_prompt]\nenabled = false")
    assert not stuck_prompt_active(vault)


def test_a_stuck_draft_is_refused_where_the_control_is_not_offered(tmp_path):
    for version, config in (
        ("mvp-0.10", ""), ("mvp-0.12", ""), ("mvp-0.13", "[stuck_prompt]\nenabled = false"),
    ):
        _paths, vault, repository = split_vault(tmp_path / version, version=version, config=config)
        with pytest.raises(AttemptValidationError, match="I'm stuck"):
            complete_attempt_with_ai_required(
                vault, repository, _draft(""), runtime=ReadyRuntime(), ai_client=RefusingClient()
            )
    _paths, vault, repository = _stuck_vault(tmp_path / "dk")
    with pytest.raises(AttemptValidationError, match="never dont_know"):
        complete_attempt_with_ai_required(
            vault, repository, _draft("", attempt_type="dont_know"), runtime=ReadyRuntime(),
            ai_client=RefusingClient(),
        )


def test_stuck_attempt_type_matches_the_answer_box():
    assert stuck_attempt_type(["independent_attempt", "hinted_attempt"]) == "independent_attempt"
    assert stuck_attempt_type(["independent_attempt", "hinted_attempt"], hints_used=1) == "hinted_attempt"
    assert stuck_attempt_type(["open_text"], hints_used=1) == "open_text"
    assert stuck_attempt_type([], probe=True) == "diagnostic_probe"
    assert stuck_attempt_type(None) == "independent_attempt"


# -- a non-empty stuck answer -------------------------------------------------------


def test_a_partial_stuck_answer_is_graded_blind_at_standard_mass_and_diagnosed(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    client = StuckFake()
    result = _grade(vault, repository, client, _draft("A = U Sigma, then I am not sure"))

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["attempt_type"] == "independent_attempt"
    assert attempt["declared_stuck"] is True and attempt["declared_dont_know"] is False
    assert attempt["manual_review_reason"] != "blank_answer"
    # The grader was told how the answer was asked for, and asked for a reading.
    assert client.calls[0] == "blind_grading"
    assert client.contexts[0]["answer_prompt"]["prompt"] == STUCK_PROMPT_TEXT
    assert "STUCK PROMPT" in client.prompts[0]
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    assert record["prompt_version"].endswith("+stuck-v1")
    assert record[STUCK_READING_KEY]["attempts_answer"] is True
    assert record[STUCK_READING_KEY]["describes_confusion"] is False
    # The base grader's calibration identity: the scoring rules are unchanged.
    assert record["calibration_prompt_version"] == "grading_prompt_v2_1_blind_reference_policy"
    # Standard attempt mass: the attempt type's own mass, not dont_know's 0.7.
    row = _field_row(vault, repository, result.attempt_id)
    assert row.effective_mass > 0
    assert row.outcome == 0.0
    # Diagnosed like any blind-graded non-pass answer, with the reading shown.
    assert diagnosis_status(repository, result.attempt_id)["status"] != NOT_NEEDED
    drain_jobs(vault, repository, client)
    diagnosis = repository.latest_attempt_diagnosis(result.attempt_id)
    assert diagnosis is not None and diagnosis["status"] == "completed"
    diagnosis_prompt = client.prompts[client.calls.index("diagnosis")]
    assert '"stuck_reading"' in diagnosis_prompt and "I'm stuck" in diagnosis_prompt


def test_an_ordinary_answer_keeps_its_prompt_and_context_exactly(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    client = StuckFake()
    result = _grade(vault, repository, client, _draft("A = U Sigma V wrong", stuck=False))

    assert "answer_prompt" not in client.contexts[0]
    assert "STUCK PROMPT" not in client.prompts[0]
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    assert record["prompt_version"] == "mvp-2.1-blind-reference-policy"
    assert STUCK_READING_KEY not in record
    assert repository.fetch_practice_attempt(result.attempt_id)["declared_stuck"] is False


def test_confusion_text_is_marked_and_becomes_a_fast_track_blocking_signal(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    answer = "I don't get why the last factor is transposed"
    client = StuckFake(
        reading={
            "attempts_answer": False,
            "describes_confusion": True,
            "confusion_quote": "why the last factor is transposed",
        }
    )
    result = _grade(vault, repository, client, _draft(answer))

    assert result.rubric_score == 0  # graded as an answer
    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = stuck_answers(connection)
        signals = load_interaction_signals(connection, vault, ())
    assert [row["attempt_id"] for row in rows] == [result.attempt_id]
    assert rows[0]["learner_answer_md"] == answer and rows[0]["has_text"]
    assert rows[0]["describes_confusion"] is True
    assert rows[0]["reading"]["confusion_quote"] == "why the last factor is transposed"
    assert rows[0]["reading"]["quote_verified"] is True
    stuck = [signal for signal in signals if signal.signal_type == STUCK_CONFUSION_SIGNAL]
    assert len(stuck) == 1
    signal = stuck[0]
    assert (signal.lo_id, signal.attempt_id) == (LO, result.attempt_id)
    # A routing signal only: the attempt itself is the graded observation.
    assert signal.outcome is None and signal.effective_mass == 0.0
    assert STUCK_CONFUSION_SIGNAL in FAST_TRACK_BLOCKING_TYPES and blocks_fast_track(signal)
    subject = signal.subject_id
    assert not confusion_blocks_fast_track(signals, lo_id=LO, subject_id=subject, as_of="2026-01-01T00:00:00Z")
    assert confusion_blocks_fast_track(signals, lo_id=LO, subject_id=subject, as_of="2027-01-01T00:00:00Z")
    assert not confusion_blocks_fast_track(
        signals, lo_id=LO, subject_id=subject, as_of="2027-01-01T00:00:00Z", self_report_known=True
    )


def test_a_stuck_attempt_without_confusion_writes_no_signal(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    _grade(vault, repository, StuckFake(), _draft("A = U Sigma"))
    with connect(repository.sqlite_path, read_only=True) as connection:
        signals = load_interaction_signals(connection, vault, ())
    assert not [signal for signal in signals if signal.signal_type == STUCK_CONFUSION_SIGNAL]


def test_a_quote_that_is_not_verbatim_is_dropped_but_the_flag_stands():
    reading = StuckReading(
        attempts_answer=False, describes_confusion=True, confusion_quote="something the learner never wrote"
    )
    marker = verified_stuck_reading(reading, "I can't see where Sigma comes from")
    assert marker["describes_confusion"] is True
    assert marker["confusion_quote"] == "" and marker["quote_verified"] is False
    spaced = verified_stuck_reading(
        StuckReading(attempts_answer=False, describes_confusion=True, confusion_quote="where  SIGMA comes"),
        "I can't see where Sigma comes from",
    )
    assert spaced["quote_verified"] is True


# -- an empty stuck answer -----------------------------------------------------------


def test_an_empty_stuck_answer_scores_zero_without_a_model_call(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    client = RefusingClient()
    result = _grade(vault, repository, client, _draft("   "))

    assert client.calls == []
    assert (result.rubric_score, result.correctness, result.grading_source) == (0, 0.0, "deterministic")
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["attempt_type"] == "independent_attempt"
    assert attempt["declared_stuck"] is True and attempt["declared_dont_know"] is False
    assert attempt["manual_review_reason"] is None  # a deliberate empty answer, not a blank
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert evidence and {row.grader_tier for row in evidence} == {2}
    assert {row.points_awarded for row in evidence} == {0.0}
    # Never sent to a model later either, and never diagnosed (nothing to read).
    assert result.attempt_id not in {row["id"] for row in repository.pending_self_grade_regrade_attempts()}
    assert repository.latest_blind_grade_record(result.attempt_id) is None
    assert diagnosis_status(repository, result.attempt_id)["status"] == NOT_NEEDED
    # A bare 0 at the standard mass: no error tag (owner decision 2026-10-12).
    assert repository.error_events_for_attempt(result.attempt_id) == []
    assert attempt["error_type"] is None
    row = _field_row(vault, repository, result.attempt_id)
    assert row.outcome == 0.0 and row.effective_mass > 0
    with connect(repository.sqlite_path, read_only=True) as connection:
        stuck = stuck_answers(connection)
    assert [(row["attempt_id"], row["has_text"], row["reading"]) for row in stuck] == [
        (result.attempt_id, False, None)
    ]


def _attribution_rows(repository, attempt_id: str) -> dict[str, int]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}" WHERE attempt_id = ?', (attempt_id,)).fetchone()[0]
            for table in ("error_events", "causal_hypotheses", "unresolved_cause_factors", "causal_attribution_reports")
        }


def test_an_empty_stuck_answer_is_a_bare_zero_with_no_error_tag(tmp_path):
    """Owner decision 2026-10-12: an empty "I'm stuck" answer is just a score
    of 0. It says nothing about understanding beyond "the learner could not
    write anything", so it writes no error tag (no retrieval_failure, and no
    scaffold_failure after hints), no error event and no attribution, live or
    replayed. Historical dont_know rows keep their deterministic tag."""

    _paths, vault, repository = _stuck_vault(tmp_path)
    plain = _grade(vault, repository, RefusingClient(), _draft(""), when=21)
    hinted = _grade(
        vault, repository, RefusingClient(),
        _draft("  ", item_id="pi_transpose_001", attempt_type="hinted_attempt", hints_used=1), when=22,
    )
    for result in (plain, hinted):
        assert (result.rubric_score, result.correctness, result.grading_source) == (0, 0.0, "deterministic")
        attempt = repository.fetch_practice_attempt(result.attempt_id)
        assert attempt["declared_stuck"] is True and attempt["error_type"] is None
        assert repository.error_events_for_attempt(result.attempt_id) == []
        assert _attribution_rows(repository, result.attempt_id) == {
            "error_events": 0, "causal_hypotheses": 0, "unresolved_cause_factors": 0,
            "causal_attribution_reports": 0,
        }
        assert {row.points_awarded for row in repository.fetch_grading_evidence(result.attempt_id)} == {0.0}
        # Still an ordinary zero in the learner field, at the standard mass.
        row = _field_row(vault, repository, result.attempt_id)
        assert row.outcome == 0.0 and row.effective_mass > 0
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(at(30)))
    for result in (plain, hinted):
        assert repository.fetch_practice_attempt(result.attempt_id)["error_type"] is None
        assert repository.error_events_for_attempt(result.attempt_id) == []

    # A historical dont_know keeps its meaning, before and after the upgrade.
    paths, old_vault, old_repository = split_vault(tmp_path / "old", version="mvp-0.12", seed=False)
    dont_know = complete_self_graded_attempt(
        old_vault, old_repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=3),
        clock=FrozenClock(at(21)),
    )
    tags = [event["error_type"] for event in old_repository.error_events_for_attempt(dont_know.attempt_id)]
    assert tags == ["retrieval_failure"]
    set_algorithm_version(paths, "mvp-0.13")
    rebuild_all_derived_state(load_vault(paths.root), old_repository, clock=FrozenClock(at(30)))
    assert [
        event["error_type"] for event in old_repository.error_events_for_attempt(dont_know.attempt_id)
    ] == tags


def test_an_empty_stuck_answer_needs_no_provider_and_ignores_a_self_grade(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    not_ready = SimpleNamespace(ready=False, status="codex_missing")
    fallback = complete_attempt_with_ai_fallback(
        vault, repository, _draft(""), SelfGradeInput(criterion_points={"setup": 2, "result": 2}, confidence=5),
        runtime=not_ready, ai_client=None,
    )
    assert (fallback.rubric_score, fallback.grading_source) == (0, "deterministic")
    self_graded = complete_self_graded_attempt(
        vault, repository, _draft(""), SelfGradeInput(criterion_points={"setup": 2, "result": 2}, confidence=5)
    )
    assert (self_graded.rubric_score, self_graded.grading_source) == (0, "deterministic")


def test_an_empty_stuck_answer_carries_the_standard_mass_not_dont_knows(tmp_path):
    """No separate dont_know weight: the attempt type's own mass applies.

    On a first answer (no familiarity or assistance discount) the field reads
    the empty stuck answer at independent_attempt's 1.0 and a dont_know at its
    configured 0.7. Later answers take the ordinary discounts, as any answer.
    """

    _paths, vault, repository = split_vault(tmp_path / "new", version="mvp-0.13", seed=False)
    stuck = _grade(vault, repository, RefusingClient(), _draft(""), when=21)
    _paths2, vault2, repository2 = split_vault(tmp_path / "old", version="mvp-0.12", seed=False)
    dont_know = complete_self_graded_attempt(
        vault2, repository2,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md="", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={}, confidence=3),
    )
    stuck_row = _field_row(vault, repository, stuck.attempt_id)
    dont_know_row = _field_row(vault2, repository2, dont_know.attempt_id)
    assert stuck_row.outcome == dont_know_row.outcome == 0.0
    assert stuck_row.effective_mass == pytest.approx(1.0)
    assert dont_know_row.effective_mass == pytest.approx(0.7)


# -- surfaces ---------------------------------------------------------------------


def _call(ctx, name: str, params: dict):
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(root):
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(root)
    # No provider at all: the empty path must not need one.
    ctx.grading_provider_override = "manual"
    session = _call(ctx, "start_session", {"energy": "medium"})
    return ctx, session["sessionId"]


def test_sidecar_empty_stuck_submission_is_instant_and_routes_to_feedback(tmp_path):
    paths, _vault, repository = _stuck_vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    assert ctx.app_snapshot()["config"]["practice"]["stuckPrompt"] is True

    payload = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "",
        "attemptType": "independent_attempt", "declaredStuck": True, "submissionId": "stuck-empty-1",
    })
    assert payload["rubricScore"] == 0 and payload["gradingSource"] == "deterministic"
    assert not (payload.get("probeEpisode") or {}).get("feedbackDeferred")
    attempt = repository.fetch_practice_attempt(payload["attemptId"])
    assert attempt["declared_stuck"] is True and attempt["attempt_type"] == "independent_attempt"
    # A retried submission answers from its receipt.
    again = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "",
        "attemptType": "independent_attempt", "declaredStuck": True, "submissionId": "stuck-empty-1",
    })
    assert again["attemptId"] == payload["attemptId"]


def test_sidecar_dont_know_records_an_empty_stuck_answer_in_an_active_vault(tmp_path):
    paths, _vault, repository = _stuck_vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    payload = _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": ITEM})
    attempt = repository.fetch_practice_attempt(payload["attemptId"])
    assert attempt["attempt_type"] == "independent_attempt"
    assert attempt["declared_stuck"] is True and attempt["declared_dont_know"] is False
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM practice_attempts WHERE attempt_type = 'dont_know'"
        ).fetchone()[0] == 0


def _dont_know_shape(repository, attempt_id):
    attempt = repository.fetch_practice_attempt(attempt_id)
    evidence = repository.fetch_grading_evidence(attempt_id)
    return {
        "attempt_type": attempt["attempt_type"],
        "declared_stuck": attempt["declared_stuck"],
        "declared_dont_know": attempt["declared_dont_know"],
        "rubric_score": attempt["rubric_score"],
        "correctness": attempt["correctness"],
        "error_type": attempt["error_type"],
        "manual_review_reason": attempt["manual_review_reason"],
        "evidence": sorted((row.criterion_id, row.points_awarded, row.grader_tier) for row in evidence),
    }


def test_kill_switch_restores_dont_know_exactly(tmp_path):
    """Switch off in mvp-0.13 == mvp-0.12, for the button, a stale stuck
    submission and the scoring (attempt shape, field mass)."""

    shapes, masses = {}, {}
    for label, version, config in (
        ("previous", "mvp-0.12", ""),
        ("switched_off", "mvp-0.13", "[stuck_prompt]\nenabled = false"),
    ):
        paths, vault, repository = split_vault(tmp_path / label, version=version, config=config)
        ctx, session_id = _sidecar(paths.root)
        assert ctx.app_snapshot()["config"]["practice"]["stuckPrompt"] is False
        button = _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": ITEM})
        # A surface drawn before the switch flipped still sends "stuck, empty".
        stale = _call(ctx, "submit_attempt", {
            "sessionId": session_id, "practiceItemId": "pi_svd_compute_002", "answerMd": "",
            "attemptType": "independent_attempt", "declaredStuck": True,
        })
        shapes[label] = [_dont_know_shape(repository, button["attemptId"]), _dont_know_shape(repository, stale["attemptId"])]
        masses[label] = [
            round(_field_row(load_vault(paths.root), repository, payload["attemptId"]).effective_mass, 9)
            for payload in (button, stale)
        ]
    assert shapes["switched_off"] == shapes["previous"]
    assert masses["switched_off"] == masses["previous"]
    assert {shape["attempt_type"] for shape in shapes["previous"]} == {"dont_know"}


def test_sidecar_text_stuck_answer_is_graded_like_any_answer(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    paths, _vault, repository = _stuck_vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    client = StuckFake()
    monkeypatch.setattr(
        practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client)
    )
    payload = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "A = U Sigma and then?",
        "attemptType": "independent_attempt", "declaredStuck": True,
    })
    assert client.calls[0] == "blind_grading"
    attempt = repository.fetch_practice_attempt(payload["attemptId"])
    assert attempt["declared_stuck"] is True
    assert payload.get("diagnosisStatus") in {"pending", "running", "completed"}


def test_cli_attempt_stuck_and_dont_know_conversion(tmp_path):
    from learnloop.cli.app import app

    paths, _vault, repository = _stuck_vault(tmp_path)
    runner = CliRunner()
    stuck = runner.invoke(app, [
        "attempt", ITEM, "--stuck", "--answer", "", "--json", "--vault", str(paths.root), "--ai-provider", "manual",
    ])
    assert stuck.exit_code == 0, stuck.output
    payload = json.loads(stuck.output)
    assert payload["declared_stuck"] is True and payload["attempt"]["rubric_score"] == 0
    converted = runner.invoke(app, [
        "attempt", "pi_svd_compute_002", "--attempt-type", "dont_know", "--json", "--vault", str(paths.root),
        "--ai-provider", "manual",
    ])
    assert converted.exit_code == 0, converted.output
    payload = json.loads(converted.output)
    assert "I'm stuck" in payload["note"]
    attempt = repository.fetch_practice_attempt(payload["attempt"]["attempt_id"])
    assert attempt["attempt_type"] == "independent_attempt" and attempt["declared_stuck"] is True


def test_cli_refuses_stuck_where_it_is_not_offered(tmp_path):
    from learnloop.cli.app import app

    paths, _vault, _repository = split_vault(tmp_path)
    result = CliRunner().invoke(app, [
        "attempt", ITEM, "--stuck", "--answer", "", "--vault", str(paths.root), "--ai-provider", "manual",
    ])
    assert result.exit_code == 1


def test_tui_ctrl_d_opens_the_stuck_prompt_and_an_empty_submit_records_it(tmp_path):
    import asyncio

    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.practice import PracticeScreen

    from tests.helpers import begin_session

    paths, _vault, repository = _stuck_vault(tmp_path)
    before = {row["id"] for row in repository.list_attempt_history()}

    async def scenario():
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, PracticeScreen)
            assert screen.stuck_prompt is True and screen.stuck is False
            await pilot.press("ctrl+d")
            await pilot.pause()
            assert screen.stuck is True and screen.has_class("-stuck")
            # The key opens the prompt; it records nothing.
            assert {row["id"] for row in repository.list_attempt_history()} == before
            return await screen.submit_stuck_empty()

    result = asyncio.run(scenario())
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(result.attempt_id)
    assert attempt["declared_stuck"] is True and attempt["rubric_score"] == 0
    assert attempt["entry_surface"] == "tui_practice"


def test_an_empty_stuck_probe_answer_is_the_unanswered_observation(tmp_path):
    """On a diagnostic presentation the attempt keeps its measurement type and
    an empty stuck answer classifies as `unanswered`, as dont_know did."""

    from learnloop.attempts.attempts import complete_empty_stuck_attempt
    from learnloop.diagnosis.probe_episodes import enter_episode

    from tests.test_probe_episodes import CLOCK, ITEM_ID, LO_ID, _commit, _setup

    _root, loaded, repository = _setup(tmp_path, algorithm_version="mvp-0.13")
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode)
    result = complete_empty_stuck_attempt(
        loaded,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="",
            attempt_type="diagnostic_probe",
            probe_presentation_id=presentation.id,
            declared_stuck=True,
        ),
        clock=CLOCK,
    )
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    observation = repository.probe_observation_for_attempt(result.attempt_id)
    assert attempt["attempt_type"] == "diagnostic_probe"
    assert attempt["declared_stuck"] is True and attempt["declared_dont_know"] is False
    assert observation is not None and observation.eligible_for_completion
    assert observation.grader_channel["observed_outcome"] == "unanswered"


def test_the_owner_summary_counts_text_share_confusion_and_grading_runs(tmp_path):
    from learnloop.attempts.stuck import stuck_answer_summary

    _paths, vault, repository = _stuck_vault(tmp_path)
    _grade(vault, repository, RefusingClient(), _draft(""), when=20)
    confused = StuckFake(reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "why"})
    _grade(vault, repository, confused, _draft("why is V transposed"), when=21)
    _grade(vault, repository, StuckFake(), _draft("A = U Sigma V wrong", stuck=False), when=22)
    with connect(repository.sqlite_path, read_only=True) as connection:
        summary = stuck_answer_summary(connection)
    assert {key: summary[key] for key in ("total", "with_text", "empty", "share_with_text")} == {
        "total": 2, "with_text": 1, "empty": 1, "share_with_text": 0.5,
    }
    assert summary["graded_with_reading"] == 1 and summary["describes_confusion"] == 1
    # One stuck grading run (the ordinary answer's run is not counted).
    assert summary["grading_wait_seconds"]["runs"] == 1


# -- review F1: a stuck answer never takes the option-letter shortcut ----------------

MC_ITEM = "pi_svd_mc_001"


def _with_mc_item(paths, repository):
    """A multiple-choice item whose correct option is C (deterministic-gradable)."""

    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.yaml_io import write_yaml

    from tests.diagnosis_split_helpers import _item

    payload = _item(
        MC_ITEM, LO, "Which factor of A = U Sigma V^T is transposed?\nA. U\nB. Sigma\nC. V\nD. none",
        "C", ["recall"], [("correct_selection", 4)], "svd_mc",
    )
    payload["practice_mode"] = "multiple_choice"
    write_yaml(paths.practice_item_path("linear-algebra", MC_ITEM), payload)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository)
    return vault


@pytest.mark.parametrize(
    "answer",
    [
        "A bit lost: which one is it?",
        "Because of the SVD I think, not sure",
        "Confused about why the last factor is transposed",
        "Don't see which factor flips",
        "Every factor looks the same to me",
        "First I wrote U, but I'm unsure",
        "Got lost after Sigma",
        "How do I tell which one is transposed?",
        "C, but I don't understand why",
    ],
)
def test_a_stuck_answer_on_a_choice_item_goes_to_the_grader_not_the_letter_shortcut(tmp_path, answer):
    paths, _vault, repository = _stuck_vault(tmp_path)
    vault = _with_mc_item(paths, repository)
    client = StuckFake(
        reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": ""}
    )
    result = _grade(vault, repository, client, _draft(answer, item_id=MC_ITEM))

    assert client.calls[:1] == ["blind_grading"], "a stuck answer must be read by the grader"
    assert result.grading_source != "deterministic"
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    assert record[STUCK_READING_KEY]["describes_confusion"] is True


def test_the_fallback_door_also_skips_the_letter_shortcut_for_a_stuck_answer(tmp_path):
    paths, _vault, repository = _stuck_vault(tmp_path)
    vault = _with_mc_item(paths, repository)
    not_ready = SimpleNamespace(ready=False, status="codex_missing")
    result = complete_attempt_with_ai_fallback(
        vault, repository, _draft("Confused about why the last factor is transposed", item_id=MC_ITEM),
        SelfGradeInput(criterion_points={"correct_selection": 0}, confidence=2),
        runtime=not_ready, ai_client=None,
    )
    # No grader: the learner's own self-grade, never "Correct, option C".
    assert result.grading_source == "self"
    assert result.rubric_score == 0
    # An ordinary (not stuck) letter answer still takes the free shortcut.
    letter = complete_attempt_with_ai_fallback(
        vault, repository, _draft("C", item_id=MC_ITEM, stuck=False),
        SelfGradeInput(criterion_points={"correct_selection": 0}, confidence=2),
        runtime=not_ready, ai_client=None,
    )
    assert (letter.grading_source, letter.rubric_score) == ("deterministic", 4)


# -- review F6: the grader's reading is a verdict in judgment_ledger ------------------


def _stuck_judgments(repository, attempt_id):
    with connect(repository.sqlite_path, read_only=True) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM judgment_ledger WHERE task = 'stuck_reading' AND left_id = ? "
                "ORDER BY created_at, id",
                (attempt_id,),
            )
        ]


CONFUSED = {
    "attempts_answer": False,
    "describes_confusion": True,
    "confusion_quote": "why the last factor is transposed",
}


def test_the_stuck_reading_appends_a_judgment_with_the_blind_record(tmp_path):
    _paths, vault, repository = _stuck_vault(tmp_path)
    answer = "I don't get why the last factor is transposed"
    result = _grade(vault, repository, StuckFake(reading=CONFUSED), _draft(answer))

    blind = repository.latest_blind_grade_record(result.attempt_id)
    judgments = _stuck_judgments(repository, result.attempt_id)
    assert len(judgments) == 1
    judgment = judgments[0]
    assert (judgment["left_kind"], judgment["right_kind"], judgment["right_id"]) == ("attempt", None, None)
    assert (judgment["judge"], judgment["judge_model"]) == ("llm", "fake-model")
    assert judgment["prompt_version"] == blind["record"]["prompt_version"]
    assert judgment["prompt_version"].endswith("+stuck-v1")
    assert judgment["input_hash"] == blind["context_hash"]
    assert judgment["supersedes_id"] is None
    verdict = json.loads(judgment["verdict"])
    assert verdict == blind["record"][STUCK_READING_KEY]
    assert verdict["describes_confusion"] is True and verdict["quote_verified"] is True
    # The read-back view names the verdict it read.
    with connect(repository.sqlite_path, read_only=True) as connection:
        row = stuck_answers(connection)[0]
    assert row["judgment_id"] == judgment["id"] and row["describes_confusion"] is True
    # An ordinary answer is not classified.
    other = _grade(vault, repository, StuckFake(), _draft("A = U Sigma V wrong", stuck=False), when=22)
    assert _stuck_judgments(repository, other.attempt_id) == []


def test_a_regrade_appends_a_superseding_stuck_judgment(tmp_path):
    from learnloop.attempts.regrade import regrade_attempt

    _paths, vault, repository = _stuck_vault(tmp_path)
    result = _grade(vault, repository, StuckFake(reading=CONFUSED), _draft("I don't get why the last factor is transposed"))
    first = _stuck_judgments(repository, result.attempt_id)[0]

    calm = StuckFake(reading={"attempts_answer": True, "describes_confusion": False, "confusion_quote": ""})
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=calm, grading_source="ai", clock=None)

    judgments = _stuck_judgments(repository, result.attempt_id)
    assert len(judgments) == 2
    latest = [row for row in judgments if row["id"] != first["id"]][0]
    assert latest["supersedes_id"] == first["id"]
    assert json.loads(latest["verdict"])["describes_confusion"] is False
    with connect(repository.sqlite_path, read_only=True) as connection:
        row = stuck_answers(connection)[0]
        signals = load_interaction_signals(connection, vault, ())
    assert row["judgment_id"] == latest["id"] and row["describes_confusion"] is False
    assert not [signal for signal in signals if signal.signal_type == STUCK_CONFUSION_SIGNAL]


# -- review F3: joint grading (split off) reads the stuck answer too -------------------


@pytest.mark.parametrize("split", [True, False], ids=["split", "joint"])
def test_confusion_is_read_and_signalled_in_both_grading_modes(tmp_path, split):
    config = "" if split else "[diagnosis]\nsplit_enabled = false"
    _paths, vault, repository = _stuck_vault(tmp_path, config=config)
    answer = "Why is V transposed?"
    client = StuckFake(
        reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "Why is V transposed?"}
    )
    result = _grade(vault, repository, client, _draft(answer))

    assert client.calls[0] == ("blind_grading" if split else "grading")
    assert "STUCK PROMPT" in client.prompts[0]
    assert client.contexts[0]["answer_prompt"]["prompt"] == STUCK_PROMPT_TEXT
    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = stuck_answers(connection)
        signals = load_interaction_signals(connection, vault, ())
        run = connection.execute(
            "SELECT prompt_version FROM agent_runs WHERE purpose = 'grading' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
    assert run[0].endswith("+stuck-v1")
    assert rows[0]["reading"]["describes_confusion"] is True
    assert rows[0]["reading"]["confusion_quote"] == "Why is V transposed?"
    assert rows[0]["judgment_id"] is not None
    stuck = [signal for signal in signals if signal.signal_type == STUCK_CONFUSION_SIGNAL]
    assert [(signal.lo_id, signal.attempt_id) for signal in stuck] == [(LO, result.attempt_id)]
    assert blocks_fast_track(stuck[0])
    judgment = _stuck_judgments(repository, result.attempt_id)[0]
    assert judgment["prompt_version"] == run[0]


def test_an_ordinary_joint_answer_keeps_its_prompt_and_hash_exactly(tmp_path):
    from dataclasses import asdict

    from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION, grading_prompt
    from learnloop.attempts.grading import build_grading_context, grading_context_hash

    _paths, vault, repository = _stuck_vault(tmp_path, config="[diagnosis]\nsplit_enabled = false")
    client = StuckFake()
    result = _grade(vault, repository, client, _draft("A = U Sigma V wrong", stuck=False))
    assert client.calls[0] == "grading"
    assert "answer_prompt" not in client.contexts[0]
    assert "STUCK PROMPT" not in client.prompts[0]
    assert f"prompt_version: {GRADING_PROMPT_VERSION}\n" in client.prompts[0]
    assert _stuck_judgments(repository, result.attempt_id) == []
    # The context, its rendered prompt and its hash carry no stuck field.
    item = vault.practice_items[ITEM]
    context = build_grading_context(vault, item, attempt_id="att_x", learner_answer_md="A")
    assert "answer_prompt" not in grading_prompt(context)
    payload = asdict(context)
    payload.pop("answer_prompt", None)
    assert grading_context_hash(context) == grading_context_hash(type(context)(**payload))


def test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes(tmp_path):
    from learnloop.attempts.regrade import regrade_attempt

    _paths, vault, repository = _stuck_vault(tmp_path, config="[diagnosis]\nsplit_enabled = false")
    result = _grade(vault, repository, StuckFake(reading=CONFUSED), _draft("I don't get why the last factor is transposed"))
    first = _stuck_judgments(repository, result.attempt_id)[0]
    calm = StuckFake(reading={"attempts_answer": True, "describes_confusion": False, "confusion_quote": ""})
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=calm, grading_source="ai", clock=None)

    assert calm.calls == ["grading"] and "STUCK PROMPT" in calm.prompts[0]
    judgments = _stuck_judgments(repository, result.attempt_id)
    latest = [row for row in judgments if row["id"] != first["id"]]
    assert len(latest) == 1 and latest[0]["supersedes_id"] == first["id"]
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert stuck_answers(connection)[0]["describes_confusion"] is False


# -- review F4: the TUI shows the worked answer after an empty stuck answer -----------


def test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer(tmp_path):
    import asyncio

    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.feedback import FeedbackScreen
    from learnloop.tui.screens.practice import PracticeScreen

    from tests.helpers import begin_session

    paths, vault, repository = _stuck_vault(tmp_path)

    async def scenario():
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            expected = practice.practice_item.expected_answer
            await pilot.press("ctrl+d")
            await pilot.pause()
            await practice.action_submit()
            await pilot.pause()
            feedback = app.screen
            assert isinstance(feedback, FeedbackScreen), type(feedback).__name__
            assert feedback.graded and feedback.has_class("-graded")
            assert feedback.result is not None and feedback.result.rubric_score == 0
            assert feedback.result.grading_source == "deterministic"
            worked = str(feedback.query_one("#worked-answer").render())
            assert expected in worked
            assert feedback.query_one("#worked-answer").display
            return feedback.result

    result = asyncio.run(scenario())
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(result.attempt_id)
    assert attempt["declared_stuck"] is True and attempt["rubric_score"] == 0
    assert attempt["entry_surface"] == "tui_practice"


def test_tui_empty_stuck_probe_answer_keeps_feedback_deferred(tmp_path, monkeypatch):
    """Inside a diagnostic check the answer is not revealed (as for "I don't
    know"): the empty stuck answer is recorded and the screen returns."""

    import asyncio

    import learnloop.attempts.post_attempt as post_attempt
    import learnloop.tui.screens.practice as practice_module
    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.feedback import FeedbackScreen
    from learnloop.tui.screens.practice import PracticeScreen

    from tests.helpers import begin_session

    paths, _vault, _repository = _stuck_vault(tmp_path)
    recorded: list = []

    def fake_record(vault, repository, draft, **_kwargs):
        recorded.append(draft)
        return SimpleNamespace(attempt_id="att-probe", practice_item_id=draft.practice_item_id)

    monkeypatch.setattr(practice_module, "complete_empty_stuck_attempt", fake_record)
    monkeypatch.setattr(post_attempt, "run_post_attempt_pipeline", lambda *args, **kwargs: None)

    async def scenario():
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            assert isinstance(practice, PracticeScreen)
            practice.probe_presentation_id = "pres-1"  # a committed diagnostic presentation
            await pilot.press("ctrl+d")
            await pilot.pause()
            await practice.action_submit()
            await pilot.pause()
            assert not isinstance(app.screen, FeedbackScreen)
            assert not isinstance(app.screen, PracticeScreen)

    asyncio.run(scenario())
    assert [(draft.attempt_type, draft.declared_stuck, draft.probe_presentation_id) for draft in recorded] == [
        ("diagnostic_probe", True, "pres-1")
    ]


# -- review F2: the stuck marker survives draft recovery ------------------------------


def test_the_draft_checkpoint_keeps_the_stuck_marker_across_a_restart(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice
    from learnloop_sidecar.context import SidecarContext

    paths, _vault, repository = _stuck_vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    draft = {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "Why is V transposed?",
        "hintsUsed": 0, "submissionId": "stuck-draft-1", "declaredStuck": True,
    }
    _call(ctx, "save_practice_draft", draft)

    # The app restarts before grading commits: a fresh sidecar reloads it.
    restarted = SidecarContext()
    restarted.load(paths.root)
    checkpoint = _call(restarted, "get_session", {"sessionId": session_id})["checkpoint"]
    assert checkpoint["currentAnswer"] == "Why is V transposed?"
    assert checkpoint["submissionId"] == "stuck-draft-1"
    assert checkpoint["declaredStuck"] is True

    # Submitting the recovered draft records the stuck answer it was.
    client = StuckFake(reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "Why is V transposed?"})
    monkeypatch.setattr(
        practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client)
    )
    payload = _call(restarted, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": checkpoint["currentAnswer"],
        "attemptType": "independent_attempt", "declaredStuck": checkpoint["declaredStuck"],
        "submissionId": checkpoint["submissionId"],
    })
    assert repository.fetch_practice_attempt(payload["attemptId"])["declared_stuck"] is True

    # Leaving stuck mode ("never mind") clears the marker on the next save.
    _call(restarted, "save_practice_draft", {**draft, "practiceItemId": "pi_svd_compute_002", "submissionId": "k2", "declaredStuck": False})
    assert _call(restarted, "get_session", {"sessionId": session_id})["checkpoint"]["declaredStuck"] is False
    # An older client that never sends the field reads as not stuck.
    legacy = {key: value for key, value in draft.items() if key != "declaredStuck"}
    _call(restarted, "save_practice_draft", {**legacy, "practiceItemId": "pi_svd_compute_002", "submissionId": "k3"})
    assert _call(restarted, "get_session", {"sessionId": session_id})["checkpoint"]["declaredStuck"] is False


# -- review F5: the paid CLI door has a dry run and spend admission -------------------


def _cli_attempt(monkeypatch, root, client, *args, item=ITEM):
    import learnloop.cli as cli_module
    from learnloop.cli.app import app

    built: list[str] = []

    def ready(*_args, **_kwargs):
        built.append("client")
        return ("fake", ReadyRuntime(), client)

    monkeypatch.setattr(cli_module, "_ready_provider_for_task", ready)
    result = CliRunner().invoke(
        app,
        [
            "attempt", item, *args, "--criterion-points", "setup=0,result=0",
            "--json", "--no-diagnose", "--vault", str(root),
        ],
    )
    return result, built


def _attempt_ids(repository):
    return {row["id"] for row in repository.list_attempt_history()}


def test_cli_stuck_dry_run_estimates_the_grading_calls_with_no_call_and_no_write(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path)
    before = _attempt_ids(repository)
    client = StuckFake()
    result, built = _cli_attempt(monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?", "--dry-run")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "dry_run"
    grading = payload["grading"]
    assert grading["kind"] == "blind" and grading["calls"] == 1
    assert grading["prompt_version"].endswith("+stuck-v1")
    assert grading["estimated_input_tokens_per_call"] > 500
    assert grading["route"]["billing"] == "subscription" and grading["admissible"] is True
    assert payload["diagnosis"]["conditional"] is True
    assert (built, client.calls) == ([], [])
    assert _attempt_ids(repository) == before

    empty, _built = _cli_attempt(monkeypatch, paths.root, client, "--stuck", "--answer", "", "--dry-run")
    assert empty.exit_code == 0, empty.output
    assert json.loads(empty.output)["grading"]["calls"] == 0
    # A metered route with no price is not admissible, and says so.
    metered, _built = _cli_attempt(
        monkeypatch, paths.root, client, "--stuck", "--answer", "Why?", "--dry-run", "--ai-provider", "openrouter"
    )
    assert metered.exit_code == 1, metered.output
    plan = json.loads(metered.output)["grading"]
    assert plan["route"]["billing"] == "metered" and plan["admissible"] is False
    assert "price" in plan["reason"].lower()
    assert _attempt_ids(repository) == before


def test_cli_metered_stuck_grading_is_refused_before_any_call_without_a_price(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path)
    before = _attempt_ids(repository)
    client = StuckFake(provider_type="openai_compatible", model="fake-metered")
    result, _built = _cli_attempt(monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?")
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["status"] == "over_budget"
    assert client.calls == []
    assert _attempt_ids(repository) == before


def test_cli_metered_stuck_grading_is_admitted_and_charged_with_a_price(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path)
    client = StuckFake(provider_type="openai_compatible", model="fake-metered")
    result, _built = _cli_attempt(
        monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?", "--price-per-million", "2.0"
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert client.calls == ["blind_grading"]
    spend = payload["spend"]
    assert spend["charged"]["calls"] == 1
    assert spend["charged"]["metered_total_tokens"] > 0
    assert spend["charged"]["metered_estimated_usd"] > 0
    assert spend["routes"]["grading"]["billing"] == "metered"
    assert repository.fetch_practice_attempt(payload["attempt"]["attempt_id"])["declared_stuck"] is True


def test_cli_subscription_grading_counts_calls_without_a_token_bound(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path)
    client = StuckFake()  # codex_sdk: the owner's subscription
    result, _built = _cli_attempt(
        monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?", "--max-tokens", "0"
    )
    assert result.exit_code == 0, result.output
    spend = json.loads(result.output)["spend"]
    assert spend["charged"]["calls"] == 1 and spend["charged"]["metered_total_tokens"] == 0
    assert spend["routes"]["grading"]["billing"] == "subscription"
    assert spend["routes"]["grading"]["cost_basis"] == "estimated_only"
    assert spend["routes"]["grading"]["input_tokens"] > 0  # estimated from reported usage
    # The command still owns the grading call's receipt, and it records the caps.
    with connect(repository.sqlite_path, read_only=True) as connection:
        receipts = connection.execute(
            "SELECT owner_kind, budget_json FROM model_call_receipts WHERE purpose = 'blind_grading'"
        ).fetchall()
    assert receipts and {row[0] for row in receipts} == {"cli"}
    budget = json.loads(receipts[0][1])
    assert budget["max_calls"] == 10 and budget["max_retries"] == 4
    # The call cap still holds on the subscription.
    before = _attempt_ids(repository)
    capped, _built = _cli_attempt(
        monkeypatch, paths.root, StuckFake(), "--stuck", "--answer", "Still lost", "--max-calls", "0",
        item="pi_svd_compute_002",
    )
    assert capped.exit_code == 1 and json.loads(capped.output)["status"] == "over_budget"
    assert _attempt_ids(repository) == before


# -- re-review F7: a spend refusal mid-grade is over budget, never a self-grade -------


class MeteredTurnsFake(StuckFake):
    """A metered grader whose calls take ``turns`` physical requests each.

    A turn after the first is what a transport retry or a JSON repair looks
    like to the spend collector; ``input_tokens`` is the usage each request
    reports (so a first sample can use more than its estimate).
    """

    def __init__(self, *, turns: int = 1, input_tokens: int = 500, **kwargs) -> None:
        super().__init__(provider_type="openai_compatible", model="fake-metered", **kwargs)
        self.turns = turns
        self.input_tokens = input_tokens

    def complete(self, request):
        from learnloop.ai.execution import model_call, report_call_usage

        from tests.diagnosis_fakes import prompt_payload

        self.calls.append(request.purpose)
        self.prompts.append(request.prompt)
        self.isolated.append(request.isolated)
        for _turn in range(self.turns):
            with model_call(self, purpose=f"{request.purpose}:fake_turn", prompt=request.prompt):
                report_call_usage({"input_tokens": self.input_tokens, "output_tokens": 200})
        context = prompt_payload(request.prompt).get("context") or {}
        return getattr(self, f"_{request.purpose}")(request, context)


def _grading_runs(repository):
    with connect(repository.sqlite_path, read_only=True) as connection:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT status, error_message FROM agent_runs WHERE purpose = 'grading' ORDER BY started_at, id"
            ).fetchall()
        ]


def _assert_over_budget_and_nothing_recorded(result, repository, before):
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "over_budget", payload
    # Not the self-grade: no attempt at all, and the grading run is closed failed.
    assert _attempt_ids(repository) == before
    runs = _grading_runs(repository)
    assert runs and runs[-1]["status"] == "failed", runs
    assert "exceeds max_" in (runs[-1]["error_message"] or ""), runs
    assert "exceeds max_" in payload["message"]
    return payload


def test_cli_a_retry_refused_by_the_caps_is_over_budget_not_a_self_grade(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path)
    before = _attempt_ids(repository)
    client = MeteredTurnsFake(turns=2)  # the second physical request is a retry
    result, _built = _cli_attempt(
        monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?",
        "--price-per-million", "2.0", "--max-retries", "0",
    )
    payload = _assert_over_budget_and_nothing_recorded(result, repository, before)
    # The first request of the sample was sent and is charged in the summary.
    assert payload["spend"]["charged"]["calls"] == 1


def test_cli_a_later_sample_refused_by_the_caps_is_over_budget_not_a_self_grade(tmp_path, monkeypatch):
    paths, _vault, repository = _stuck_vault(tmp_path, config="[diagnostic_augmentation]\nsample_count = 2\n")
    before = _attempt_ids(repository)
    # The first sample reports far more input than its estimate, so the
    # second sample no longer fits the token cap the plan was admitted on.
    client = MeteredTurnsFake(input_tokens=400_000)
    result, _built = _cli_attempt(
        monkeypatch, paths.root, client, "--stuck", "--answer", "Why is V transposed?", "--price-per-million", "2.0",
    )
    payload = _assert_over_budget_and_nothing_recorded(result, repository, before)
    assert client.calls == ["blind_grading"]  # the refused sample was never sent
    assert payload["spend"]["charged"]["metered_total_tokens"] >= 400_000


# -- re-review F8: the TUI's worked answer is a reveal; the retry is primed -----------


def _tui_empty_stuck_feedback(paths):
    """Empty stuck submit in the TUI; returns (result, item id) once the
    feedback screen shows the worked answer."""

    import asyncio

    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.feedback import FeedbackScreen

    from tests.helpers import begin_session

    async def scenario():
        app = LearnLoopApp(paths.root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            await pilot.press("ctrl+d")
            await pilot.pause()
            await practice.action_submit()
            await pilot.pause()
            feedback = app.screen
            assert isinstance(feedback, FeedbackScreen)
            assert feedback.query_one("#worked-answer").display
            return feedback.result, practice.practice_item.id

    return asyncio.run(scenario())


def test_the_tui_worked_answer_is_recorded_as_a_reveal_and_primes_the_retry(tmp_path):
    paths, vault, repository = _stuck_vault(tmp_path)
    result, item_id = _tui_empty_stuck_feedback(paths)

    reveals = repository.reveal_events(practice_item_id=item_id)
    assert [(row["source_kind"], row["amount"], row["attempt_id"]) for row in reveals] == [
        ("answer_display", 1.0, result.attempt_id)
    ]
    assert reveals[0]["learning_object_id"] == vault.practice_items[item_id].learning_object_id
    assert reveals[0]["basis"] == "worked_answer:stuck_empty:tui"

    # The learner retries the item at once (the same second, typically): the
    # answer they just read makes it primed evidence, not an unassisted recall.
    retry = complete_self_graded_attempt(
        load_vault(paths.root),
        repository,
        _draft(vault.practice_items[item_id].expected_answer, stuck=False, item_id=item_id),
        SelfGradeInput(criterion_points={}, confidence=4),
    )
    attempt = repository.fetch_practice_attempt(retry.attempt_id)
    assert attempt["primed"] == 1
    assert (repository.attempt_debug_payload(retry.attempt_id) or {})["auto_primed_reveal_total"] == pytest.approx(1.0)


def test_a_worked_answer_shown_in_the_attempts_own_second_still_primes_the_retry(tmp_path):
    """Timestamps have one-second resolution and the submit window starts
    AFTER the last attempt; the display is linked to that attempt, so it
    counts even when stamped in the same second. Charged once per attempt."""

    from learnloop.attempts.reveal_ledger import record_answer_display_reveal
    from learnloop.clock import FrozenClock

    paths, vault, repository = _stuck_vault(tmp_path)
    clock = FrozenClock(at(21))
    item = vault.practice_items[ITEM]
    empty = complete_attempt_with_ai_required(
        vault, repository, _draft(""), runtime=ReadyRuntime(), ai_client=RefusingClient(), clock=clock
    )
    for _reopen in range(2):
        record_answer_display_reveal(
            repository, attempt_id=empty.attempt_id, practice_item_id=ITEM,
            learning_object_id=item.learning_object_id, basis="worked_answer:stuck_empty:tui", clock=clock,
        )
    assert len(repository.reveal_events(attempt_id=empty.attempt_id)) == 1

    retry = complete_self_graded_attempt(
        vault, repository, _draft(item.expected_answer, stuck=False),
        SelfGradeInput(criterion_points={}, confidence=4), clock=clock,
    )
    assert repository.fetch_practice_attempt(retry.attempt_id)["primed"] == 1
    # The window then moves past the retry: the one after it is unprimed again.
    later = complete_self_graded_attempt(
        vault, repository, _draft(item.expected_answer, stuck=False),
        SelfGradeInput(criterion_points={}, confidence=4), clock=FrozenClock(at(22)),
    )
    assert repository.fetch_practice_attempt(later.attempt_id)["primed"] == 0


def test_only_post_attempt_displays_cross_the_same_second_boundary(tmp_path):
    """The other kinds keep their window exactly (no behaviour change outside
    the mvp-0.13 display): a tutor answer linked to the last attempt and
    stamped in its second is still outside the next attempt's window."""

    from learnloop.clock import FrozenClock

    paths, vault, repository = _stuck_vault(tmp_path)
    clock = FrozenClock(at(21))
    item = vault.practice_items[ITEM]
    first = complete_self_graded_attempt(
        vault, repository, _draft("A = U Sigma V wrong", stuck=False),
        SelfGradeInput(criterion_points={}, confidence=4), clock=clock,
    )
    repository.insert_reveal_event(
        {
            "practice_item_id": ITEM, "learning_object_id": item.learning_object_id,
            "source_kind": "tutor_answer", "amount": 1.0, "attempt_id": first.attempt_id,
        },
        clock=clock,
    )
    retry = complete_self_graded_attempt(
        vault, repository, _draft(item.expected_answer, stuck=False),
        SelfGradeInput(criterion_points={}, confidence=4), clock=clock,
    )
    assert repository.fetch_practice_attempt(retry.attempt_id)["primed"] == 0


def test_migration_179_widens_the_reveal_kinds_and_keeps_the_ledger(tmp_path):
    """Built as migration 173 and renumbered 179 at the merge. On a populated
    ledger holding every kind main writes (tutor answers and cited source
    spans from tutor_qa, repair displays, and the reserved guided_redo), the
    rebuild keeps every row and column, every index and both append-only
    triggers exactly, and only widens the CHECK by ``answer_display``."""

    import sqlite3

    from learnloop.attempts.reveal_ledger import REVEAL_SOURCE_KINDS
    from learnloop.db.migrate import apply_migrations, default_migrations_dir

    before_179 = tmp_path / "before_179"
    before_179.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) < 179:
            (before_179 / path.name).write_bytes(path.read_bytes())
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=before_179)
    main_kinds = ("tutor_answer", "repair_display", "guided_redo", "source_review")
    assert set(REVEAL_SOURCE_KINDS) == {*main_kinds, "answer_display"}

    def schema_objects(connection):
        return {
            (row[0], row[1]): row[2]
            for row in connection.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE tbl_name = 'reveal_events' AND type IN ('index', 'trigger')"
            )
        }

    def ledger(connection):
        return [tuple(row) for row in connection.execute("SELECT * FROM reveal_events ORDER BY id")]

    with connect(sqlite_path) as connection:
        for index, kind in enumerate(main_kinds):
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, remediation_episode_id, "
                "source_kind, amount, basis, question_event_id, attempt_id, created_at) "
                "VALUES (?, 'pi_1', 'lo_1', ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"rev_{index}", f"ep_{index}" if index % 2 else None, kind, 0.25 * index,
                    f"{kind}:basis", f"q_{index}" if kind in {"tutor_answer", "source_review"} else None,
                    f"att_{index}", f"2026-10-12T00:00:0{index}Z",
                ),
            )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) "
                "VALUES ('rev_x', 'pi_1', 'answer_display', 1.0, '2026-10-12T00:00:00Z')"
            )
        rows_before = ledger(connection)
        objects_before = schema_objects(connection)
        columns_before = [tuple(row) for row in connection.execute("PRAGMA table_info(reveal_events)")]
    assert len(rows_before) == len(main_kinds)

    from learnloop.db.migrate import discover_migrations

    # 179, then whatever follows it at the head (DL1's 180 does not touch
    # reveal_events).
    assert [migration.version for migration in apply_migrations(sqlite_path)] == [
        migration.version for migration in discover_migrations() if migration.version >= 179
    ]
    with connect(sqlite_path) as connection:
        assert ledger(connection) == rows_before
        assert [tuple(row) for row in connection.execute("PRAGMA table_info(reveal_events)")] == columns_before
        # Every index and trigger as migration 154 built them, byte for byte.
        assert schema_objects(connection) == objects_before
        assert {name for _type, name in objects_before} == {
            "sqlite_autoindex_reveal_events_1",  # the primary key
            "idx_reveal_events_item_created", "idx_reveal_events_episode",
            "reveal_events_no_update", "reveal_events_no_delete",
        }
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, attempt_id, created_at) "
            "VALUES ('rev_new', 'pi_1', 'answer_display', 1.0, 'att_9', '2026-10-12T00:00:09Z')"
        )
        for kind in main_kinds:
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) "
                "VALUES (?, 'pi_2', ?, 0.5, '2026-10-12T00:01:00Z')",
                (f"rev_after_{kind}", kind),
            )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) "
                "VALUES ('rev_3', 'pi_1', 'bogus', 1.0, '2026-10-12T00:00:02Z')"
            )
        # Still append-only.
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE reveal_events SET amount = 0.1 WHERE id = 'rev_1'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM reveal_events WHERE id = 'rev_1'")
        assert connection.execute("SELECT name FROM sqlite_master WHERE name = 'reveal_events_new'").fetchone() is None
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
