"""Instruct hand-off, the owner's decision 4 (Nov 9; spec_instruct_handoff_v1 §1, §8): no gate on ``cold_failing``.

"cold_failing can be from 1 severe bayesian surprise cold retrieval failure or 2 mild surprise cold retrieval failures, or
none since the failures in the cold retrieval were insignificant/trivial arithmetic. This is something for the action
router/diagnosis/teacher ensemble to decide through the learnloop algorithm." So a topic with a missed cold check since its
last lesson is a lesson candidate (``cold_missed``), with no threshold on the miss's size, its count or its error type, and
its reason says what happened and when ("On Nov 8, a check on it wasn't fully right."). "Since" is from when the last
lesson ended, and an answer the system records as not independent is no cold check (review 3). Off, or below the tag,
mvp-0.54's ``cold_failing``. Fakes only; no model call.
"""

from __future__ import annotations

import inspect
import io
import time
import tokenize
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.db.stores import router_suggestions as store
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective_switches import lesson_candidate_after_cold_miss_on
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.teacher_fakes import TeacherFake, clients, plan_turn
from tests.teacher_te1b_suggestions_helpers import LOS, _vault

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
OFF = "[router_objective]\nlesson_candidate_after_cold_miss = false\n"
T0 = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
NOW = "2026-11-09T09:00:00Z"
#: Self-graded points out of the item's 4: 3 is the trivial slip (0.75), 0 the severe miss.
SLIP, SEVERE, RIGHT = 3, 0, 4


def _world(tmp_path, *, version: str = TAG, config: str = "", name: str = "vault"):
    paths, repository = _vault(tmp_path, version=version, name=name)
    if config:
        append_config_toml(paths.root, config)
    return paths, repository


def _answer(paths, repository, item: str, points: int, *, days_ago: float) -> str:
    attempt = complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="my answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=3),
        clock=FrozenClock(T0 - timedelta(days=days_ago)))
    return attempt.attempt_id


@pytest.fixture
def utc_zone(monkeypatch):
    """The words name a local date: pin the zone so the dates below are the test's."""

    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _candidates(paths, repository, now: str = NOW) -> dict[str, LS.Candidate]:
    candidates, _excluded = SG.build_candidates(load_vault(paths.root), repository, now_iso=now)
    return {candidate.learning_object_ids[0]: candidate for candidate in candidates}


# -- the candidacy condition is structural ------------------------------------------------------------------------------


def _names(source: str) -> list[str]:
    return [token.string for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type in (tokenize.NAME, tokenize.NUMBER, tokenize.OP)]


def test_the_candidacy_condition_reads_no_score_magnitude_count_or_error_type():
    """Static: the condition only asks whether a cold check since the last lesson was not fully right. No count (``len``,
    a slice, ``sum``), no threshold below full, no error type, severity, surprise or stuck flag."""

    body = inspect.getsource(SG.missed_since).split('"""')[2]
    names = _names(body)
    numbers = {name for name in names if name[:1].isdigit()}
    assert numbers == {"1.0"}, numbers  # "not fully right": the definition of a miss, the only number
    for word in ("len", "sum", "count", "max", "min", "error_type", "severity", "surprise", "stuck", "declared_stuck",
                 "hints", "confidence", "diagnosis", ":"):
        assert word not in names, word
    # And nothing the candidates are built from carries an error type, a severity or a surprise.
    reads = inspect.getsource(store.attempts_by_learning_object)
    for word in ("error_type", "severity", "surprise", "diagnos", "stuck"):
        assert word not in reads, word


def test_a_trivial_slip_and_a_severe_miss_are_both_candidates_and_differ_only_through_the_routers_evidence(tmp_path):
    """One slip on ``lo_det`` and one severe miss on ``lo_eigen``: both ``cold_missed``, read the same by the acceptance
    model (the same reason feature), and their values differ only through the mastery model's predicted success (the room
    to learn), which reads the graded answers. Nothing about either miss is in the candidate itself."""

    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=1)
    _answer(paths, repository, "pi_eig_1", SEVERE, days_ago=1)
    found = _candidates(paths, repository)
    slip, severe = found["lo_det"], found["lo_eigen"]
    assert slip.reason == severe.reason == "cold_missed"
    strip = ("ref", "learning_object_ids", "title", "predicted_success")
    assert {k: v for k, v in slip.as_dict().items() if k not in strip} == \
        {k: v for k, v in severe.as_dict().items() if k not in strip}
    context = LS.Context(local_hour=9.0, minutes_left=30.0, reentry=False, days_since_last=None)
    state = LS.AcceptanceState()
    assert state.p_accept(context, slip) == state.p_accept(context, severe), "the acceptance model reads the reason only"
    assert slip.predicted_success > severe.predicted_success, "the graded answers move the mastery model"
    scored = {entry.candidate.learning_object_ids[0]: entry.value for entry in LS.score(state, context, [slip, severe], k=2)}
    assert scored["lo_eigen"] > scored["lo_det"], "more room to learn after the severe miss, by the model's own numbers"


def test_one_miss_and_two_misses_are_the_same_candidacy(tmp_path):
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=2)
    _answer(paths, repository, "pi_det_2", SEVERE, days_ago=1)
    _answer(paths, repository, "pi_eig_1", SEVERE, days_ago=1)
    found = _candidates(paths, repository)
    assert found["lo_det"].reason == found["lo_eigen"].reason == "cold_missed"


def test_a_miss_followed_by_a_right_answer_is_still_a_candidate(tmp_path):
    """Whether the later right answer settles it is the router's to weigh (AD's posterior reads both), not a rule's."""

    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=2)
    _answer(paths, repository, "pi_det_2", RIGHT, days_ago=1)
    assert _candidates(paths, repository)["lo_det"].reason == "cold_missed"


def test_only_a_miss_since_the_last_lesson_counts(tmp_path):
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=3)
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_det"],
                  clients=clients(TeacherFake([plan_turn])), clock=FrozenClock(T0 - timedelta(days=2)))
    with repository.connection() as connection:
        connection.execute("UPDATE lessons SET closed_at = ?, close_reason = 'learner_stop' WHERE closed_at IS NULL",
                           ((T0 - timedelta(days=2) + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),))
        connection.commit()
    _answer(paths, repository, "pi_det_2", RIGHT, days_ago=1)
    assert "lo_det" not in _candidates(paths, repository) or _candidates(paths, repository)["lo_det"].reason != "cold_missed"
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=0.5)
    assert _candidates(paths, repository)["lo_det"].reason == "cold_missed"


def test_an_unattempted_or_only_right_topic_is_no_cold_miss(tmp_path):
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", RIGHT, days_ago=1)
    found = _candidates(paths, repository)
    assert "lo_det" not in found or found["lo_det"].reason != "cold_missed"
    assert found["lo_eigen"].reason == "new_goal"


# -- the wording and the acceptance model ------------------------------------------------------------------------------


def test_the_reason_reads_honestly(tmp_path, utc_zone):
    assert SG.REASON_WORDS["cold_missed"] == "A check on it wasn't fully right."  # a record with no date
    assert SG.REASON_WORDS["cold_failing"] == "Your last two checks on it didn't come out right."  # the predecessor's
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=1)
    entry = SG._card_entry(_candidates(paths, repository)["lo_det"].as_dict(), as_of=NOW)
    assert entry["why"] == "On Nov 8, a check on it wasn't fully right."


@pytest.mark.parametrize("correctness", [0.0, 0.5, 0.75, 0.9, 0.99])
def test_the_words_hold_for_every_grade_the_condition_admits(tmp_path, utc_zone, correctness):
    """Review 3, m1 (R3): a 0.9 is a success to AD and "correct" on the LLM's card, and the offer must not say it "didn't
    come out right". Every grade below full is truthfully "wasn't fully right", dated from the attempt itself."""

    paths, repository = _world(tmp_path)
    attempt = _answer(paths, repository, "pi_det_1", RIGHT, days_ago=1)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?", (correctness, attempt))
        connection.commit()
    candidate = _candidates(paths, repository)["lo_det"]
    assert candidate.reason == "cold_missed" and candidate.missed_at == "2026-11-08T09:00:00Z"
    assert SG.reason_words(candidate, as_of=NOW) == "On Nov 8, a check on it wasn't fully right."


def test_an_old_miss_followed_by_right_answers_is_dated_as_old(tmp_path, utc_zone):
    """Review 3, m1 (R4): one miss 200 days ago and ten right answers since. Still a candidate (no age rule), and the
    words no longer say "recent": they name the day. A miss in an earlier year names the year."""

    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=200)
    for index in range(10):
        _answer(paths, repository, "pi_det_2" if index % 2 else "pi_det_1", RIGHT, days_ago=150 - index * 10)
    candidate = _candidates(paths, repository)["lo_det"]
    assert candidate.reason == "cold_missed"
    assert SG.reason_words(candidate, as_of=NOW) == "On Apr 23, a check on it wasn't fully right."
    assert SG._card_entry(candidate.as_dict(), as_of=NOW)["why"] == "On Apr 23, a check on it wasn't fully right."
    _answer(paths, repository, "pi_eig_1", SLIP, days_ago=400)
    eigen = _candidates(paths, repository)["lo_eigen"]
    assert SG.reason_words(eigen, as_of=NOW) == "On Oct 5, 2025, a check on it wasn't fully right."


def test_the_words_name_the_latest_miss_and_survive_the_record(tmp_path, utc_zone):
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=5)
    _answer(paths, repository, "pi_det_2", RIGHT, days_ago=3)
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=2)
    candidate = _candidates(paths, repository)["lo_det"]
    assert candidate.missed_at == "2026-11-07T09:00:00Z"
    assert LS.Candidate.from_dict(candidate.as_dict()).as_dict() == candidate.as_dict(), "the date is on the record"
    assert SG.reason_words(candidate.as_dict(), as_of=NOW) == "On Nov 7, a check on it wasn't fully right."
    # The other reasons keep their words and their records (no date key).
    new_goal = _candidates(paths, repository)["lo_eigen"]
    assert "missed_at" not in new_goal.as_dict() and SG.reason_words(new_goal, as_of=NOW) == SG.REASON_WORDS["new_goal"]


def test_the_offer_block_and_the_llms_row_carry_the_dated_words(tmp_path, utc_zone):
    """The offer block's reason (which the offer page and the LLM policy's row read) is the same sentence."""

    from learnloop.daily_plan import lesson_offer as LO
    from learnloop.router import requests as rq

    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=1)
    vault = load_vault(paths.root)
    only, _excluded = SG.build_candidates(vault, repository, now_iso=NOW)
    only = [candidate for candidate in only if candidate.learning_object_ids == ("lo_det",)]
    real = SG.build_candidates
    try:
        SG.build_candidates = lambda *_a, **_k: (only, {})
        offer = LO.build(vault, repository, today="2026-11-09", now_iso=NOW, local_hour=9.0, minutes_left=30.0,
                         reentry=False, forced=False)
    finally:
        SG.build_candidates = real
    assert offer.candidate is not None, offer
    assert offer.candidate.reason == "On Nov 8, a check on it wasn't fully right."
    view = SG.offer_card_view(SimpleNamespace(chosen=offer.candidate.annotations, budget_minutes=15, decision_ref="d",
                                              id="b", outcome=None, created_at=NOW))
    assert view["suggestion"]["why"] == offer.candidate.reason
    assert offer.candidate.reason in rq.lesson_offer_description(topic="Determinants", why=offer.candidate.reason,
                                                                 est_minutes=15, p_accept=0.4)


# -- review 3, M2: "since the last lesson" is since it ended, and a non-independent answer is no cold check -------------


def _lesson(paths, repository, *, days_ago: float, minutes: float = 20) -> None:
    opened = T0 - timedelta(days=days_ago)
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_det"],
                  clients=clients(TeacherFake([plan_turn])), clock=FrozenClock(opened))
    with repository.connection() as connection:
        connection.execute("UPDATE lessons SET closed_at = ?, close_reason = 'learner_stop' WHERE closed_at IS NULL",
                           ((opened + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),))
        connection.commit()


def _probe(paths, repository, points: int, *, days_ago: float) -> str:
    attempt = _answer(paths, repository, "pi_det_2", points, days_ago=days_ago)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET attempt_type = 'diagnostic_probe' WHERE id = ?", (attempt,))
        connection.commit()
    return attempt


@pytest.mark.parametrize(("version", "config"), [(TAG, ""), (TAG, OFF), (OLD, "")], ids=["on", "switch_off", "below"])
def test_a_placement_probe_missed_inside_the_lesson_is_the_lessons_not_a_check_after_it(tmp_path, version, config):
    """R2: a right answer, a lesson, its placement probe missed five minutes in, the lesson closed. On: no candidate (the
    miss was while the lesson was open). Off and below the tag: mvp-0.54's rule, as before (no candidate either)."""

    paths, repository = _world(tmp_path, version=version, config=config)
    _answer(paths, repository, "pi_det_1", RIGHT, days_ago=3)
    _lesson(paths, repository, days_ago=2)
    _probe(paths, repository, SEVERE, days_ago=2 - 5 / 1440)
    assert "lo_det" not in _candidates(paths, repository)
    # A check after the lesson ended counts (on). Off, mvp-0.54's rule reads the probe and this one as its two latest
    # cold checks, as it always did.
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=1)
    found = _candidates(paths, repository)
    assert found["lo_det"].reason == ("cold_missed" if config == "" and version == TAG else "cold_failing")


def _expose(repository, attempt: str) -> None:
    from learnloop.causal_activity_policy import LESSON_PROBE_EXPOSED_SOURCE

    repository.record_causal_activity_classification(
        attempt_id=attempt, contamination_class="instructional_diagnostic", near_clone=False,
        near_clone_basis="no_source_item", source=LESSON_PROBE_EXPOSED_SOURCE,
        detail={"practice_item_id": "pi_det_2", "exposure": "revealed"}, clock=FrozenClock(T0))


def test_an_answer_recorded_as_not_independent_is_no_cold_check(tmp_path):
    """A lesson probe answered after the lesson showed text on the topic (``lesson_probe_exposed``, the rule
    ``lesson_weight.qualifying_outcomes`` applies) makes no candidate; the same answer unexposed does."""

    paths, repository = _world(tmp_path)
    exposed = _probe(paths, repository, SEVERE, days_ago=1)
    _expose(repository, exposed)
    assert "lo_det" not in _candidates(paths, repository)
    control, control_repository = _world(tmp_path, name="control")
    _probe(control, control_repository, SEVERE, days_ago=1)
    assert _candidates(control, control_repository)["lo_det"].reason == "cold_missed"


@pytest.mark.parametrize(("version", "config"), [(TAG, OFF), (OLD, "")], ids=["switch_off", "below"])
def test_off_or_below_an_exposed_answer_counts_as_before(tmp_path, version, config):
    paths, repository = _world(tmp_path, version=version, config=config)
    for days_ago in (2, 1):
        _expose(repository, _probe(paths, repository, SEVERE, days_ago=days_ago))
    assert _candidates(paths, repository)["lo_det"].reason == "cold_failing"


# -- review 3, m2: a topic AD places below its band keeps below_band ------------------------------------------------


def _below(monkeypatch, *los: str) -> dict[str, dict]:
    band = {lo: {"below": True, "p_band": 0.1, "p_bar": 0.2, "band": [0.7, 0.8]} for lo in los}
    monkeypatch.setattr(SG, "_band_positions", lambda _vault, _repository, ids: {lo: band[lo] for lo in ids if lo in band})
    return band


def test_a_topic_below_its_band_with_a_miss_keeps_below_band(tmp_path, monkeypatch):
    band = _below(monkeypatch, "lo_det")
    paths, repository = _world(tmp_path)
    _answer(paths, repository, "pi_det_1", SLIP, days_ago=1)
    _answer(paths, repository, "pi_eig_1", SLIP, days_ago=1)
    found = _candidates(paths, repository)
    assert found["lo_det"].reason == "below_band" and found["lo_det"].band == band["lo_det"]
    assert found["lo_det"].missed_at is None and SG.reason_words(found["lo_det"]) == SG.REASON_WORDS["below_band"]
    assert found["lo_eigen"].reason == "cold_missed", "a miss on a topic not below its band is still a candidate"


@pytest.mark.parametrize(("version", "config"), [(TAG, OFF), (OLD, "")], ids=["switch_off", "below"])
def test_off_or_below_the_precedence_is_the_predecessors(tmp_path, monkeypatch, version, config):
    _below(monkeypatch, "lo_det", "lo_eigen")
    paths, repository = _world(tmp_path, version=version, config=config)
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=2)
    _answer(paths, repository, "pi_det_2", SEVERE, days_ago=1)
    _answer(paths, repository, "pi_eig_1", SLIP, days_ago=1)
    found = _candidates(paths, repository)
    assert found["lo_det"].reason == "cold_failing" and found["lo_eigen"].reason == "below_band"


def test_the_renamed_reason_enters_the_acceptance_model_through_the_same_effect_with_its_history():
    """No new effect and no hand-set number: ``cold_missed`` sets the ``reason_cold_failing`` effect as ``cold_failing``
    did, so every earlier answer to a ``cold_failing`` card keeps teaching it, and the prior set is unchanged."""

    context = LS.Context(local_hour=9.0, minutes_left=None, reentry=False, days_since_last=None)
    old = LS.Candidate(ref="lesson:lo_a", learning_object_ids=("lo_a",), reason="cold_failing", predicted_success=0.3)
    new = LS.Candidate(ref="lesson:lo_a", learning_object_ids=("lo_a",), reason="cold_missed", predicted_success=0.3)
    for recovery in LS.RECOVERY_DAYS_GRID:
        assert (LS.design_vector(context, old, recovery) == LS.design_vector(context, new, recovery)).all()
    assert LS.PRIORS_VERSION == "suggestion_priors_v1" and "cold_missed" in LS.REASONS
    # History: three declines of cold_failing cards lower P(accept) of a cold_missed card exactly as of a cold_failing one.
    state = LS.AcceptanceState()
    before = state.p_accept(context, new)
    for _ in range(3):
        state.observe(context, old, False)
    assert state.p_accept(context, new) == state.p_accept(context, old) < before


# -- the switch and the tag --------------------------------------------------------------------------------------------


def _history(paths, repository) -> None:
    _answer(paths, repository, "pi_det_1", SEVERE, days_ago=3)
    _answer(paths, repository, "pi_det_2", SEVERE, days_ago=2)
    _answer(paths, repository, "pi_eig_1", SLIP, days_ago=1)


@pytest.mark.parametrize(("version", "config"), [(TAG, OFF), (OLD, "")], ids=["switch_off", "below_the_tag"])
def test_off_or_below_the_tag_candidates_and_wording_are_the_predecessors(tmp_path, version, config):
    paths, repository = _world(tmp_path, version=version, config=config, name="held")
    _history(paths, repository)
    found = _candidates(paths, repository)
    assert found["lo_det"].reason == "cold_failing"  # its two latest cold checks below full
    assert "lo_eigen" not in found, "one slip: not a candidate under mvp-0.54's rule"
    assert SG._card_entry(found["lo_det"].as_dict())["why"] == "Your last two checks on it didn't come out right."
    on_paths, on_repository = _world(tmp_path, name="on")
    _history(on_paths, on_repository)
    on = _candidates(on_paths, on_repository)
    assert on["lo_det"].reason == on["lo_eigen"].reason == "cold_missed"
    assert set(on) - set(found) == {"lo_eigen"}
    # Everything else about the candidates is unchanged.
    rest = set(found) - {"lo_det"}
    assert {lo: found[lo].as_dict() for lo in rest} == {lo: on[lo].as_dict() for lo in rest}


def test_the_switch_needs_the_tag_defaults_on_and_is_registered(tmp_path):
    assert LearnLoopConfig().router_objective.lesson_candidate_after_cold_miss is True
    on, _r = _world(tmp_path, name="on")
    off, _r = _world(tmp_path, config=OFF, name="off")
    below, _r = _world(tmp_path, version=OLD, name="below")
    plain, _r = _world(tmp_path, config="[router_objective]\nenabled = false\n", name="plain")
    assert lesson_candidate_after_cold_miss_on(load_vault(on.root).config)
    assert not lesson_candidate_after_cold_miss_on(load_vault(off.root).config)
    assert not lesson_candidate_after_cold_miss_on(load_vault(below.root).config)
    # It needs no objective: it says what is offerable wherever lesson candidates are built.
    assert lesson_candidate_after_cold_miss_on(load_vault(plain.root).config)
    rule = classify_config_path("router_objective.lesson_candidate_after_cold_miss")
    assert rule is not None and "kill switch" in rule.rationale and "decision 4" in rule.rationale


def test_the_switch_is_not_in_the_prefetch_key_and_moves_no_seed_by_itself(tmp_path):
    """It changes which candidates exist, and a boundary's identity already holds the offer it built (its log row and
    annotations), so a flip that changes the offer changes the key, and one that changes nothing leaves the job right."""

    from learnloop.daily_plan.objective_chooser import objective_settings
    from learnloop.router_objective_switches import SEED_NEUTRAL_OBJECTIVE_KEYS, SEED_NEUTRAL_SWITCHES

    on, _r = _world(tmp_path, name="on")
    off, _r = _world(tmp_path, config=OFF, name="off")
    assert objective_settings(load_vault(on.root).config) == objective_settings(load_vault(off.root).config)
    assert "lesson_candidate_after_cold_miss" not in SEED_NEUTRAL_SWITCHES + SEED_NEUTRAL_OBJECTIVE_KEYS


def test_every_lo_of_the_fixture_is_accounted_for(tmp_path):
    """A guard on the fixture these tests read: six LOs, all on the goal."""

    paths, repository = _world(tmp_path)
    assert set(_candidates(paths, repository)) == set(LOS)
