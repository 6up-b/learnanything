""""Write what you can" replaces "I don't know" (mvp-0.11).

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
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
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
    return split_vault(tmp_path, version="mvp-0.11", config=config)


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
    _paths, vault, _repository = split_vault(tmp_path / "a")
    assert not stuck_prompt_active(vault)  # mvp-0.10
    _paths, vault, _repository = _stuck_vault(tmp_path / "b")
    assert stuck_prompt_active(vault)
    _paths, vault, _repository = _stuck_vault(tmp_path / "c", config="[stuck_prompt]\nenabled = false")
    assert not stuck_prompt_active(vault)


def test_a_stuck_draft_is_refused_where_the_control_is_not_offered(tmp_path):
    for version, config in (("mvp-0.10", ""), ("mvp-0.11", "[stuck_prompt]\nenabled = false")):
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
    # The same deterministic attribution dont_know writes, at the standard mass.
    assert [event["error_type"] for event in repository.error_events_for_attempt(result.attempt_id)] == [
        "retrieval_failure"
    ]
    row = _field_row(vault, repository, result.attempt_id)
    assert row.outcome == 0.0 and row.effective_mass > 0
    with connect(repository.sqlite_path, read_only=True) as connection:
        stuck = stuck_answers(connection)
    assert [(row["attempt_id"], row["has_text"], row["reading"]) for row in stuck] == [
        (result.attempt_id, False, None)
    ]


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

    _paths, vault, repository = split_vault(tmp_path / "new", version="mvp-0.11", seed=False)
    stuck = _grade(vault, repository, RefusingClient(), _draft(""), when=21)
    _paths2, vault2, repository2 = split_vault(tmp_path / "old", seed=False)
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
    """Switch off in mvp-0.11 == mvp-0.10, for the button, a stale stuck
    submission and the scoring (attempt shape, field mass)."""

    shapes, masses = {}, {}
    for label, version, config in (
        ("previous", "mvp-0.10", ""),
        ("switched_off", "mvp-0.11", "[stuck_prompt]\nenabled = false"),
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
            return screen.submit_stuck_empty()

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

    _root, loaded, repository = _setup(tmp_path, algorithm_version="mvp-0.11")
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
