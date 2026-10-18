"""Adaptive difficulty AD1: the rating tap (G-AD1-3) and the first-hint progress marker (G-AD1-10).

Spec §12, §11.2, §5.3. The optional "Felt: easy / about right / hard" tap is
sent with the submit, so it is stored only when tapped and only before
feedback; a submit without it succeeds. The practice screen keeps a marker of
whether an answer had been started when the first hint was revealed, keeps it
in the saved draft and sends it on submit; a client that sends none stores
null (read as ``unknown``). Both are logged only. Fails before AD1: no
``practice_attempts.difficulty_rating`` / ``first_hint_progress`` column, and
the submit RPC refuses the fields (``extra="forbid"``). The live sidecar path
(manual self-grade), no model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext, config_dto
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import append_config_toml, create_basic_vault

ITEM = "pi_svd_define_001"
SELF_GRADE = {"criterionPoints": {"correctness": 4}, "confidence": 4}


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = _call(ctx, "start_session", {"energy": "medium"})
    return paths, ctx, session["sessionId"]


def _submit(ctx, session_id, key, **extra):
    params = {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": "A = U Sigma V^T.",
              "attemptType": "hinted_attempt" if extra.get("hintsUsed") else "independent_attempt",
              "selfGrade": SELF_GRADE, "submissionId": key, **extra}
    return _call(ctx, "submit_attempt", params)


def _attempt(paths, attempt_id):
    return Repository(paths.sqlite_path).fetch_practice_attempt(attempt_id)


# -- G-AD1-3 ----------------------------------------------------------------------------------


def test_rating_tap_optional_never_blocks_submit(tmp_path):
    paths, ctx, session_id = _sidecar(tmp_path)
    untapped = _submit(ctx, session_id, "k-untapped")
    assert _attempt(paths, untapped["attemptId"])["difficulty_rating"] is None
    tapped = _submit(ctx, session_id, "k-tapped", difficultyRating="hard")
    assert _attempt(paths, tapped["attemptId"])["difficulty_rating"] == "hard"
    # Only before feedback: the tap rides the submit itself. A retried submit
    # carrying a later tap answers with the committed attempt and changes nothing.
    again = _submit(ctx, session_id, "k-tapped", difficultyRating="easy")
    assert again["attemptId"] == tapped["attemptId"]
    assert _attempt(paths, tapped["attemptId"])["difficulty_rating"] == "hard"
    with pytest.raises(ValidationError):
        _submit(ctx, session_id, "k-bad", difficultyRating="very_hard")
    # "I don't know" carries the tap too, when one was made.
    dont_know = _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": ITEM,
                                                "submissionId": "k-dk", "difficultyRating": "hard",
                                                "selfGrade": SELF_GRADE})
    assert _attempt(paths, dont_know["attemptId"])["difficulty_rating"] == "hard"


def test_the_rating_tap_switch_stores_nothing(tmp_path):
    paths, ctx, session_id = _sidecar(tmp_path, config="[adaptive_difficulty]\nrating_tap = false\n")
    tapped = _submit(ctx, session_id, "k1", difficultyRating="hard")
    assert _attempt(paths, tapped["attemptId"])["difficulty_rating"] is None
    assert config_dto(ctx.vault)["adaptiveDifficulty"] == {"ratingTap": False, "firstHintProgress": True}


def test_the_attempt_layer_validates_the_tap_and_the_marker(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, AttemptValidationError, SelfGradeInput, complete_self_graded_attempt
    from learnloop.vault.loader import load_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    for draft in (AttemptDraft(practice_item_id=ITEM, learner_answer_md="x", difficulty_rating="meh"),
                  AttemptDraft(practice_item_id=ITEM, learner_answer_md="x", hints_used=1,
                               attempt_type="hinted_attempt", first_hint_progress="typing")):
        with pytest.raises(AttemptValidationError):
            complete_self_graded_attempt(vault, repository, draft,
                                         SelfGradeInput(criterion_points={"correctness": 4}, confidence=4))


# -- G-AD1-10 ---------------------------------------------------------------------------------


def _reveal(ctx, session_id, key, answer):
    return _call(ctx, "practice.record_hint_reveal", {"sessionId": session_id, "practiceItemId": ITEM,
                                                      "submissionId": key, "authoredIndex": 0, "answerMd": answer})


def _save_draft(ctx, session_id, key, answer, **extra):
    return _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer,
                                              "hintsUsed": 1, "submissionId": key, **extra})


def _checkpoint(ctx, session_id):
    return _call(ctx, "get_session", {"sessionId": session_id})["checkpoint"]


def test_first_hint_progress_recorded_and_missing_is_null(tmp_path):
    paths, ctx, session_id = _sidecar(tmp_path)
    # A first hint revealed with an empty answer: no_draft.
    _reveal(ctx, session_id, "k-empty", "")
    empty = _submit(ctx, session_id, "k-empty", hintsUsed=1, firstHintProgress="no_draft")
    assert _attempt(paths, empty["attemptId"])["first_hint_progress"] == "no_draft"
    # After typing: draft_started.
    _reveal(ctx, session_id, "k-typed", "A = U")
    typed = _submit(ctx, session_id, "k-typed", hintsUsed=1, firstHintProgress="draft_started")
    assert _attempt(paths, typed["attemptId"])["first_hint_progress"] == "draft_started"
    # A restored draft keeps the marker (under its retry key only).
    _save_draft(ctx, session_id, "k-restored", "A = U", firstHintProgress="no_draft")
    checkpoint = _checkpoint(ctx, session_id)
    assert checkpoint["submissionId"] == "k-restored" and checkpoint["firstHintProgress"] == "no_draft"
    _save_draft(ctx, session_id, "k-restored", "A = U Sigma")          # a client save without it keeps it
    assert _checkpoint(ctx, session_id)["firstHintProgress"] == "no_draft"
    _save_draft(ctx, session_id, "k-next", "")                           # another draft never inherits it
    assert "firstHintProgress" not in _checkpoint(ctx, session_id)
    # A client that sends none stores null; so does an attempt with no hint.
    silent = _submit(ctx, session_id, "k-silent", hintsUsed=1)
    assert _attempt(paths, silent["attemptId"])["first_hint_progress"] is None
    unhinted = _submit(ctx, session_id, "k-unhinted", firstHintProgress="no_draft")
    assert _attempt(paths, unhinted["attemptId"])["first_hint_progress"] is None
    with pytest.raises(ValidationError):
        _submit(ctx, session_id, "k-bad", hintsUsed=1, firstHintProgress="typing")


def test_the_marker_is_null_with_forecast_receipts_off(tmp_path):
    paths, ctx, session_id = _sidecar(tmp_path, config="[adaptive_difficulty]\nforecast_receipts = false\n")
    _save_draft(ctx, session_id, "k1", "", firstHintProgress="no_draft")
    assert "firstHintProgress" not in _checkpoint(ctx, session_id)
    submitted = _submit(ctx, session_id, "k1", hintsUsed=1, firstHintProgress="no_draft")
    assert _attempt(paths, submitted["attemptId"])["first_hint_progress"] is None


def test_the_app_snapshot_names_the_client_switches_only_while_on(tmp_path):
    paths = create_basic_vault(tmp_path / "on")
    ctx = SidecarContext()
    ctx.load(paths.root)
    assert config_dto(ctx.vault)["adaptiveDifficulty"] == {"ratingTap": True, "firstHintProgress": True}
    off = create_basic_vault(tmp_path / "off")
    append_config_toml(off.root, "[adaptive_difficulty]\nrating_tap = false\nforecast_receipts = false\n")
    ctx_off = SidecarContext()
    ctx_off.load(off.root)
    assert "adaptiveDifficulty" not in config_dto(ctx_off.vault)
