"""Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4, §19).

The card at most once a day, "Not now" muting the goal per the seeded recovery prior, Start opening a
TE1 lesson whose origin is the decision, every response logged, the exact propensities, the
intention-to-treat outcome, the kill switch's byte-identical Today and plan, the successor's gating,
and no model call anywhere. Every model is a fake; no network.
"""

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_VERSIONS,
    SUCCESSOR_CHAIN,
    HELP_FOLD_ATTACH_ALGORITHM_VERSION,
    TEACHER_ALGORITHM_VERSION,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.db.stores.router import ROUTER_DESIGNS
from learnloop.router import lesson_suggestions as LS
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import set_algorithm_version
from tests.teacher_fakes import TeacherFake, _item, build_teacher_vault, clients, plan_turn

TAG = LESSON_SUGGESTIONS_ALGORITHM_VERSION
#: The immediate predecessor: follow-ups Nov 2's mvp-0.42 (landed first; ruling R4 at TE1b's landing).
PREDECESSOR_TAG = HELP_FOLD_ATTACH_ALGORITHM_VERSION
T0 = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def _clock(days: float = 0.0, hours: float = 0.0) -> FrozenClock:
    return FrozenClock(T0 + timedelta(days=days, hours=hours))


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


#: The synthetic vault's six LOs (``lo_det`` on determinants, the other five on the SVD concept).
LOS = ("lo_det", "lo_eigen", "lo_inner", "lo_matrices", "lo_svd_definition", "lo_vectors")


def _vault(tmp_path, *, version: str = TAG, goal: bool = True, name: str = "vault"):
    """TE1's teacher vault at TE1b's tag, with one active goal over both concepts (so all six LOs are new
    goal LOs), or no goal at all (no candidate)."""

    paths, repository = build_teacher_vault(tmp_path / name, reserved=False)
    set_algorithm_version(paths, version)
    goals = [{
        "id": "goal_la", "title": "Linear algebra", "status": "active", "priority": 0.5, "due_at": None,
        "created_at": "2026-10-01T00:00:00Z", "updated_at": "2026-10-01T00:00:00Z",
        "facet_scope": {"concepts": ["determinants_c", "singular_value_decomposition"]}, "target_recall": 0.8}]
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": goals if goal else []})
    return paths, repository


@pytest.fixture
def shown(monkeypatch):
    """The draw's uniforms: the mixture's staged component (above the floor), its pick (the highest-valued
    candidate), and the show coin at 0 (a card to act on)."""

    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.0))


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("TE1b made a network call")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _suggestion(paths, repository, clock):
    return SG.today_suggestion(load_vault(paths.root), repository, clock=clock)


def _decisions(repository):
    return _rows(repository, "SELECT * FROM router_decisions WHERE decision_kind = 'lesson_suggestion' "
                             "ORDER BY created_at, id")


# --- the card -------------------------------------------------------------------------------------


def test_the_card_comes_at_most_once_a_day(tmp_path, shown, no_network):
    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    assert card is not None and card["minutes"] == LS.CARD_MINUTES
    assert card["suggestion"]["learning_object_ids"][0] in LOS
    assert card["suggestion"]["reason"] == "new_goal" and card["suggestion"]["why"]
    assert len(card["alternatives"]) == LS.MAX_ALTERNATIVES  # up to two of the other goal LOs
    # Re-opening Today the same day reads the day's decision back: the same card, no second draw.
    assert _suggestion(paths, repository, _clock(hours=3)) == card
    assert len(_decisions(repository)) == 1
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="declined",
               clock=_clock(hours=4))
    # Answered: no card again that day, and still one decision.
    assert _suggestion(paths, repository, _clock(hours=5)) is None
    assert len(_decisions(repository)) == 1
    # The next day draws its own decision.
    _suggestion(paths, repository, _clock(days=1))
    assert [row["receipt_key"] for row in _decisions(repository)] == [
        "lesson_suggestion:2026-11-02", "lesson_suggestion:2026-11-03"]


def test_the_decision_logs_the_draw_with_its_exact_propensity(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    (row,) = _decisions(repository)
    assert row["design"] == LS.DESIGN and row["design"] in ROUTER_DESIGNS
    assert row["policy"] == LS.POLICY and row["surface"] == "today_card" and row["algorithm_version"] == TAG
    candidates = json.loads(row["candidates_json"])
    detail = json.loads(row["detail_json"])
    assert sum(c["pi"] for c in candidates) == pytest.approx(1.0)
    assert all(c["pi"] >= 0.02 - 1e-12 for c in candidates)  # the router's epsilon_min floor
    drawn = next(c for c in candidates if c["ref"] == detail["drawn_ref"])
    assert row["chosen_ref"] == drawn["ref"] == card["suggestion"]["ref"] and detail["shown"]
    assert row["propensity_kind"] == "exact" and row["propensity"] == pytest.approx(drawn["pi"] * drawn["p_accept"])
    assert detail["p_no_card"] == pytest.approx(sum(c["pi"] * (1 - c["p_accept"]) for c in candidates))
    for candidate in candidates:  # value = log P(accept) + log(1 - predicted success)
        import math
        assert candidate["value"] == pytest.approx(math.log(candidate["p_accept"]) + math.log(candidate["room"]))
    assert detail["model"]["priors_version"] == LS.PRIORS_VERSION and detail["model"]["updates"] == 0
    assert row["card_hash"] == LS.canonical_hash(detail["card"])


def test_a_day_with_no_card_is_logged_too(tmp_path, monkeypatch):
    """Not shown (the show coin above P(accept)): the decision is still written, chosen_ref no_suggestion, with
    the exact probability of no card (intention-to-treat needs both arms)."""

    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.999999))
    paths, repository = _vault(tmp_path)
    assert _suggestion(paths, repository, _clock()) is None
    (row,) = _decisions(repository)
    detail = json.loads(row["detail_json"])
    assert row["chosen_ref"] == LS.NO_SUGGESTION and not detail["shown"] and row["chosen_learning_object_id"] is None
    # Codex review F3: the outcome is the drawn target's, so the propensity is P(target) · P(no card | target),
    # never the aggregate chance of no card (kept in the detail for the report).
    assert detail["propensity_basis"] == "joint_target_arm"
    assert detail["arm_propensity"] == pytest.approx(1 - detail["p_show_drawn"])
    assert row["propensity"] == pytest.approx(detail["pi_drawn"] * (1 - detail["p_show_drawn"]))
    assert 0 < row["propensity"] < 1 and row["propensity"] != pytest.approx(detail["p_no_card"])
    # The predeclared outcome scope is fixed in both arms: the target and the two it would have offered.
    assert [entry["ref"] for entry in detail["target_scope"]][0] == detail["drawn_ref"]
    assert len(detail["target_scope"]) == 1 + LS.MAX_ALTERNATIVES
    assert _suggestion(paths, repository, _clock(hours=2)) is None and len(_decisions(repository)) == 1


def test_no_candidate_writes_nothing(tmp_path, shown):
    paths, repository = _vault(tmp_path, goal=False)
    assert _suggestion(paths, repository, _clock()) is None
    assert _decisions(repository) == []


def test_the_candidate_reasons(tmp_path):
    """Two cold checks not right: cold_failing; an open lesson or a lesson since the last attempt: left out."""

    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    for offset, item in enumerate(("pi_det_1", "pi_det_2")):
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="not sure", attempt_type="independent_attempt"),
            SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
            clock=FrozenClock(T0 - timedelta(days=3 - offset)))
    candidates, excluded = SG.build_candidates(load_vault(paths.root), repository, now_iso="2026-11-02T09:00:00Z")
    reasons = {c.learning_object_ids[0]: c.reason for c in candidates}
    assert reasons == {lo: "cold_failing" if lo == "lo_det" else "new_goal" for lo in LOS} and excluded == {}
    assert all(0.0 <= (c.predicted_success or 0.0) <= 1.0 for c in candidates)
    # A lesson opened on lo_eigen (still open) leaves it out.
    fake = TeacherFake([plan_turn])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake), clock=_clock())
    candidates, excluded = SG.build_candidates(load_vault(paths.root), repository, now_iso="2026-11-02T10:00:00Z")
    assert "lo_eigen" not in [c.learning_object_ids[0] for c in candidates] and excluded == {"open_lesson": ["lo_eigen"]}


# --- responses ------------------------------------------------------------------------------------


def test_every_response_is_logged_once(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    card = _suggestion(paths, repository, _clock())
    alternative = card["alternatives"][0]
    chose = SG.respond(vault, repository, decision_id=card["decision_id"], response="chose_alternative",
                       candidate_ref=alternative["ref"], clock=_clock(hours=1))
    assert chose["lesson"]["learning_object_ids"] == alternative["learning_object_ids"]
    assert chose["lesson"]["lesson_id"].startswith("les_")
    # The same response again is the same answer (idempotent); a different one is refused.
    again = SG.respond(vault, repository, decision_id=card["decision_id"], response="chose_alternative",
                       candidate_ref=alternative["ref"], clock=_clock(hours=2))
    assert again == chose
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(vault, repository, decision_id=card["decision_id"], response="declined", clock=_clock(hours=2))
    assert refused.value.code == "already_answered"
    with pytest.raises(SG.SuggestionError):
        SG.respond(vault, repository, decision_id="nope", response="accepted", clock=_clock(hours=2))
    (row,) = _rows(repository, "SELECT * FROM router_suggestion_responses")
    assert row["response"] == "chose_alternative" and row["candidate_ref"] == alternative["ref"]
    assert row["lesson_id"] == chose["lesson"]["lesson_id"] and row["responded_at"] == "2026-11-02T10:00:00Z"


def test_a_card_left_unanswered_is_recorded_ignored_the_next_day(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    assert _rows(repository, "SELECT * FROM router_suggestion_responses") == []
    _suggestion(paths, repository, _clock(days=1))
    (row,) = _rows(repository, "SELECT * FROM router_suggestion_responses")
    assert row["decision_id"] == card["decision_id"] and row["response"] == "ignored" and row["lesson_id"] is None
    assert json.loads(row["detail_json"])["shown_on"] == "2026-11-02"


def test_responses_move_the_acceptance_model(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    card = _suggestion(paths, repository, _clock())
    started = SG.respond(vault, repository, decision_id=card["decision_id"], response="accepted", clock=_clock(hours=1))
    # The Start's lesson opens (an unopened one would hold the next day's card: codex re-review F2).
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=started["lesson"]["lesson_id"],
                  clock=_clock(hours=1))
    _suggestion(paths, repository, _clock(days=1))
    second = json.loads(_decisions(repository)[1]["detail_json"])["model"]
    first = json.loads(_decisions(repository)[0]["detail_json"])["model"]
    assert first["updates"] == 0 and second["updates"] == 1
    assert second["means"]["intercept"] > first["means"]["intercept"]  # a Start raises P(accept)


# --- "Not now" ------------------------------------------------------------------------------------


def test_not_now_mutes_the_goal_per_the_recovery_prior(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    card = _suggestion(paths, repository, _clock())
    declined_lo = card["suggestion"]["learning_object_ids"][0]
    other_lo = card["alternatives"][0]["learning_object_ids"][0]
    SG.respond(vault, repository, decision_id=card["decision_id"], response="declined", clock=_clock(hours=1))

    def p_accept(day: int, lo: str) -> float:
        row = _rows(repository, "SELECT candidates_json FROM router_decisions WHERE receipt_key = ?",
                    (f"lesson_suggestion:{(T0 + timedelta(days=day)).date().isoformat()}",))[0]
        return next(c["p_accept"] for c in json.loads(row["candidates_json"])
                    if c["learning_object_ids"] == [lo])

    seen = {}
    for day in (1, 3, 7, 15):
        card = _suggestion(paths, repository, _clock(days=day))
        if card is not None:  # Leave each card unanswered (ignored: no decline, no Start).
            pass
        seen[day] = (p_accept(day, declined_lo), p_accept(day, other_lo))
    # The declined goal starts well below the one it was not, recovers along log(1 + days) on the seeded
    # grid (centred on 7 days), and is back with the other by two weeks.
    assert seen[1][0] < 0.3 < seen[1][1]
    assert seen[1][0] < seen[3][0] < seen[7][0] < seen[15][0]
    assert seen[15][0] == pytest.approx(seen[15][1], abs=0.02)
    # The declined goal is not the card the day after (the draw prefers the goal not declined).
    day_one = json.loads(_rows(repository, "SELECT detail_json FROM router_decisions WHERE receipt_key = ?",
                               ("lesson_suggestion:2026-11-03",))[0]["detail_json"])
    assert day_one["drawn_learning_object_ids"] == [other_lo]


def test_the_seeded_priors_reproduce_one_a_day_and_a_week_long_mute():
    state = LS.AcceptanceState()
    context = LS.Context(local_hour=9.0, minutes_left=None, reentry=False, days_since_last=None)

    def p(days):
        return state.p_accept(context, LS.Candidate("lesson:x", ("x",), "new_goal", None, days))

    assert p(None) == pytest.approx(LS.LEGACY_DAILY_SHOW, abs=1e-6)
    assert p(0.0) == pytest.approx(LS.LEGACY_DECLINED_SHOW, abs=1e-6)
    assert p(1.0) < 0.2 and p(7.0) > 0.75 and p(14.0) == pytest.approx(p(None), abs=1e-9)
    assert LS.RECOVERY_DAYS_GRID[len(LS.RECOVERY_DAYS_GRID) // 2] == 7.0
    assert list(state.weights()) == pytest.approx([1 / len(LS.RECOVERY_DAYS_GRID)] * len(LS.RECOVERY_DAYS_GRID))


def test_re_acceptance_after_a_decline_teaches_the_recovery_rate():
    """Learners who come back after two days move the grid toward short recoveries; after twelve, long ones."""

    context = LS.Context(local_hour=9.0, minutes_left=None, reentry=False, days_since_last=1.0)
    quick, slow = LS.AcceptanceState(), LS.AcceptanceState()
    for _ in range(6):
        quick.observe(context, LS.Candidate("lesson:x", ("x",), "new_goal", None, 2.0), True)
        slow.observe(context, LS.Candidate("lesson:x", ("x",), "new_goal", None, 2.0), False)
        slow.observe(context, LS.Candidate("lesson:x", ("x",), "new_goal", None, 12.0), True)
    shortest = 0
    assert quick.weights()[shortest] > slow.weights()[shortest]
    assert slow.weights()[-1] > quick.weights()[-1]
    replayed = LS.replay([LS.Observation(context, LS.Candidate("lesson:x", ("x",), "new_goal", None, 2.0), True,
                                         "2026-11-02T00:00:00Z")] * 6)
    assert replayed.summary() == quick.summary()


# --- Start ----------------------------------------------------------------------------------------


class _Ctx:
    def __init__(self, paths, repository):
        self.paths, self.repository = paths, repository
        self.grading_provider_override = None
        self.reloads = 0

    def require_vault(self):
        return load_vault(self.paths.root), self.repository

    def reload(self, maintenance: bool = True):
        self.reloads += 1


def test_start_opens_a_lesson_whose_origin_is_the_decision(tmp_path, shown, monkeypatch, no_network):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = _vault(tmp_path)
    ctx = _Ctx(paths, repository)
    card = H.lesson_suggestion(ctx, H.LessonSuggestionInput())["suggestion"]
    started = H.lesson_suggestion_respond(ctx, H.LessonSuggestionRespondInput(
        decision_id=card["decisionId"], response="accepted"))
    lesson = started["lesson"]
    assert lesson["learningObjectIds"] == card["suggestion"]["learningObjectIds"]
    fake = TeacherFake([plan_turn])
    monkeypatch.setattr(H, "_clients", lambda ctx, vault: clients(fake))
    opened = H.lesson_turn(ctx, H.LessonTurnInput(
        action="open", entry="learning_object", origin="router_suggestion",
        suggestion_decision_id=card["decisionId"], lesson_id=lesson["lessonId"]))
    assert opened["lessonId"] == lesson["lessonId"]
    (row,) = _rows(repository, "SELECT origin, origin_ref, learning_object_ids_json FROM lessons")
    assert row["origin"] == "router" and row["origin_ref"] == card["decisionId"]
    assert json.loads(row["learning_object_ids_json"]) == lesson["learningObjectIds"]
    # A second Start resumes the same lesson; nothing opens on a suggestion the learner did not accept.
    with pytest.raises(SidecarError) as again:
        H.lesson_turn(ctx, H.LessonTurnInput(action="open", entry="learning_object", origin="router_suggestion",
                                             suggestion_decision_id=card["decisionId"], lesson_id=lesson["lessonId"]))
    assert again.value.code == "lesson_exists" and again.value.details["lesson_id"] == lesson["lessonId"]
    with pytest.raises(SidecarError) as forged:
        H.lesson_turn(ctx, H.LessonTurnInput(action="open", entry="learning_object", origin="router_suggestion",
                                             suggestion_decision_id=card["decisionId"], lesson_id="les_forged"))
    assert forged.value.code == "not_found"
    assert len(_rows(repository, "SELECT id FROM lessons")) == 1


def test_a_closed_suggested_lessons_receipt_names_the_decision(tmp_path, shown):
    from tests.teacher_fakes import close_turn

    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    card = _suggestion(paths, repository, _clock())
    started = SG.respond(vault, repository, decision_id=card["decision_id"], response="accepted", clock=_clock())
    fake = TeacherFake([plan_turn])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(fake),
                  origin="router", origin_ref=card["decision_id"], lesson_id=started["lesson"]["lesson_id"],
                  clock=_clock())
    fake.turns = [close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=started["lesson"]["lesson_id"], action="reply",
                payload={"text": "That's enough for today."}, clients=clients(fake), clock=_clock(hours=1))
    (receipt,) = _rows(repository, "SELECT receipt_json FROM lesson_receipts")
    assert json.loads(receipt["receipt_json"])["origin"] == card["decision_id"]


# --- the intention-to-treat outcome -----------------------------------------------------------------


def test_the_outcome_is_r_cold_on_the_drawn_lo_shown_or_not(tmp_path, shown):
    from learnloop.router.outcomes import R_COLD_ITT_RULE, derive_router_outcomes

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    lo = card["suggestion"]["learning_object_ids"][0]
    item = f"pi_itt_{lo}"
    write_yaml(paths.practice_item_path("linear-algebra", item), _item(item, lo, "State it.", "okapi lemur: it"))
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="declined",
               clock=_clock(hours=1))
    with repository.connection() as connection:
        (pending,) = [o for o in derive_router_outcomes(connection, reader_exposures=None) if o["decision_id"] == card["decision_id"]]
    assert pending["r_cold_status"] == "pending" and pending["action_status"] == "not_taken"
    assert pending["target_learning_object_id"] == lo
    # Same day: too soon; two days later: the cold retrieval.
    for when in (_clock(hours=2), _clock(days=2)):
        complete_self_graded_attempt(
            load_vault(paths.root), repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="an answer", attempt_type="independent_attempt",
                         evidence_origin="human"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=when)
    with repository.connection() as connection:
        (outcome,) = [o for o in derive_router_outcomes(connection, reader_exposures=None) if o["decision_id"] == card["decision_id"]]
    assert outcome["r_cold_status"] == "observed" and outcome["r_cold_value"] == 1.0, outcome["detail_json"]
    assert outcome["s_status"] == "final" and outcome["s_value"] == 1.0 and outcome["r_next_status"] == "not_applicable"
    detail = json.loads(outcome["detail_json"])
    assert detail["r_cold_rule"] == R_COLD_ITT_RULE and detail["arm"] == "shown" and detail["response"] == "declined"


# --- the kill switch, the successor -----------------------------------------------------------------


def _dump(repository) -> dict[str, list[tuple]]:
    with repository.connection() as connection:
        tables = [r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {t: [tuple(r) for r in connection.execute(f"SELECT * FROM {t}").fetchall()] for t in tables}


@pytest.mark.parametrize("setting", ["switch_off", "below_tag", "router_off", "lessons_off"])
def test_off_or_below_the_tag_nothing_is_drawn_or_written(tmp_path, shown, setting):
    from tests.ux_phase1_support import set_config

    paths, repository = _vault(tmp_path, version=PREDECESSOR_TAG if setting == "below_tag" else TAG)
    if setting == "switch_off":
        set_config(paths.root, {("router", "lesson_suggestions", "enabled"): False})
    elif setting == "router_off":
        set_config(paths.root, {("router", "enabled"): False})
    elif setting == "lessons_off":
        set_config(paths.root, {("teacher", "enabled"): False})
    vault = load_vault(paths.root)
    assert not SG.suggestions_active(vault)
    before = _dump(repository)
    assert SG.today_suggestion(vault, repository, clock=_clock()) is None
    assert _dump(repository) == before
    with pytest.raises(SG.SuggestionError) as refused:
        SG.respond(vault, repository, decision_id="x", response="accepted", clock=_clock())
    assert refused.value.code == "suggestions_disabled"


def test_with_the_switch_off_the_desktop_config_is_byte_identical(tmp_path):
    from learnloop_sidecar.context import config_dto
    from tests.ux_phase1_support import set_config

    on_paths, _ = _vault(tmp_path, name="on")
    off_paths, _ = _vault(tmp_path, name="off")
    set_config(off_paths.root, {("router", "lesson_suggestions", "enabled"): False})
    below_paths, _ = _vault(tmp_path, version=PREDECESSOR_TAG, name="below")
    on, off, below = (config_dto(load_vault(p.root)) for p in (on_paths, off_paths, below_paths))
    assert on["teacher"] == {"lessons": True, "suggestions": True}
    assert off["teacher"] == below["teacher"] == {"lessons": True}


def test_todays_plan_is_byte_identical_with_a_suggestion_drawn(tmp_path, shown):
    """The card is its own RPC: drawing the day's suggestion (a router decision row) changes nothing the
    plan shows; the plan read at the predecessor's tag and at TE1b's is the same but for the version label."""

    from learnloop.daily_plan.engine import PlanEnv
    from learnloop_sidecar.handlers.daily_plan import _current_view

    paths, repository = _vault(tmp_path, version=PREDECESSOR_TAG)
    clock = _clock()
    before = _current_view(PlanEnv(load_vault(paths.root), repository, clock=clock))
    set_algorithm_version(paths, TAG)
    assert SG.today_suggestion(load_vault(paths.root), repository, clock=clock) is not None
    after = _current_view(PlanEnv(load_vault(paths.root), repository, clock=clock))
    dumped = json.dumps(after, sort_keys=True).replace(TAG, PREDECESSOR_TAG)
    assert dumped == json.dumps(before, sort_keys=True)


def test_the_successor_is_the_latest_link_after_followups_nov2():
    assert SUCCESSOR_CHAIN[-13:-10] == (TEACHER_ALGORITHM_VERSION, PREDECESSOR_TAG, TAG) == ("mvp-0.41", "mvp-0.42", "mvp-0.43")
    assert LATEST_ALGORITHM_VERSION == "mvp-0.53"
    assert LESSON_SUGGESTIONS_VERSIONS == frozenset({TAG, "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53"})


def test_the_upgrade_from_teacher_te1_and_its_refusals(tmp_path):
    from learnloop.lesson_suggestions_upgrade import PREDECESSOR, upgrade_to_lesson_suggestions

    assert PREDECESSOR == PREDECESSOR_TAG
    # From the immediate predecessor, and from teacher TE1's tag through it (the chain).
    direct, _ = build_teacher_vault(tmp_path / "direct", version=PREDECESSOR_TAG, reserved=False)
    result = upgrade_to_lesson_suggestions(direct.root)
    assert result.upgraded and result.from_version == PREDECESSOR_TAG and result.to_version == TAG
    paths, _repository = build_teacher_vault(tmp_path / "vault", reserved=False)
    result = upgrade_to_lesson_suggestions(paths.root)
    assert result.upgraded and result.from_version == TEACHER_ALGORITHM_VERSION and result.to_version == TAG
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_lesson_suggestions(paths.root)
    assert not again.upgraded and again.problems
    old, _ = build_teacher_vault(tmp_path / "old", version="mvp-0.8", reserved=False)
    refused = upgrade_to_lesson_suggestions(old.root)
    assert not refused.upgraded and "cannot upgrade" in refused.problems[0]


def test_the_openers_install_this_links_completion():
    import inspect

    from learnloop.cli import runtime
    from learnloop_sidecar import context

    assert "learnloop.phone_probes_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.phone_probes_upgrade" in inspect.getsource(context._complete_interrupted_activation)


def test_every_defaults_snapshot_drops_to_te1s_value_without_the_suggestion_keys():
    """The two new keys are all that moved the snapshots recorded before the tag."""

    import hashlib
    import tomllib

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, \
        defaults_fingerprint_for_version

    # main's values at f9bc4254b3 (follow-ups Nov 2's landing), frozen here.
    mains = {"mvp-0.9": "daf9970ef448c318aa457a8b08b878c51062f2c468fd23ab52e922f57d442401",
             "mvp-0.41": "bbf65e7656841b5190a519004dc9242617b22a1eff471382c28e03fda0da6567",
             "mvp-0.42": "f4d3a0772f4abebe1177f59b74929e625cdddcee24f39ab1ace2fb7d85ce9825"}
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version)
    for version, main in mains.items():
        config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(version)))
        dumped = config.model_dump(mode="json", exclude_none=False)
        assert dumped["router"].pop("lesson_suggestions") == {"enabled": True, "ceiling_per_day": 3}
        # Teacher TE2-log (no successor): its teacher.episode_log moved them too.
        assert dumped["teacher"].pop("episode_log") is True
        from tests.test_teacher_te2_successor import drop_te2_keys

        drop_te2_keys(dumped)  # teacher TE2's keys (mvp-0.51; tests/test_teacher_te2_successor.py), inert below it
        from tests.test_te3a_successor import drop_te3a_keys

        drop_te3a_keys(dumped)  # teacher TE3a's key (mvp-0.52; tests/test_te3a_successor.py), inert below it
        # Reader RW5d P5 landed after TE1b: its [figures] prefetch keys and route moved them too.
        # Reader RW5c P1 landed after it too: its kill switch moved them.
        dumped["figures"].pop("checked_labels_enabled")
        dumped.pop("data_capture")  # data capture's keys (mvp-0.44; tests/test_data_capture_successor.py)
        dumped.pop("followup")  # FG1's keys (mvp-0.45; tests/test_followup_successor.py)
        dumped.pop("router_objective")  # RO0's switch (no successor) and RO1's keys (mvp-0.46; tests/test_ro1_successor.py)
        dumped["scheduler"]["surprise"].pop("remove_interval_factor")
        dumped["ui"].pop("show_router_decisions")
        dumped["ai"]["routing"].pop("followup_probe_author", None)
        dumped["practice"].pop("device_eligibility_enabled")  # mobile PR-6 landed after it too
        dumped["figures"].pop("prefetch_enabled")
        dumped["figures"].pop("prefetch")
        dumped["ai"]["routing"].pop("figure_prefetch_judge")
        # Router objective RO2 (no successor): its forecaster in the default list and its card budget.
        dumped["adaptive_difficulty"]["outside_forecasters"].remove("llm_history_v1")
        assert dumped["adaptive_difficulty"].pop("history_card_token_budget") == 48_000
        digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == main, version
    assert TAG in DEFAULTS_SNAPSHOT_BY_ALGORITHM


def test_the_ceiling_binds_and_is_logged(tmp_path, shown):
    from tests.ux_phase1_support import set_config

    paths, repository = _vault(tmp_path)
    set_config(paths.root, {("router", "lesson_suggestions", "ceiling_per_day"): 0})
    assert _suggestion(paths, repository, _clock()) is None
    (row,) = _decisions(repository)
    detail = json.loads(row["detail_json"])
    assert detail["ceiling"] == {"per_day": 0, "shown_today": 0, "bound": True}
    # The ceiling decides the arm (probability 1), the target is still drawn (codex review F3).
    assert row["chosen_ref"] == LS.NO_SUGGESTION and detail["arm_propensity"] == 1.0
    assert row["propensity"] == pytest.approx(detail["pi_drawn"])


# --- parity with the teacher's own reads --------------------------------------------------------------


def test_the_shell_reads_lessons_and_room_to_learn_as_the_teacher_does(tmp_path):
    """The draw's room to learn (``1 − p``) is the lesson brief's predicted success; the below-band reason
    is adaptive difficulty's, not this (codex review F6: tested below)."""

    from learnloop.teacher.brief import lo_prediction
    from tests.ux_phase1_support import set_config

    paths, repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    assert SG.suggestions_active(vault) and S.lessons_active(vault)
    for lo in ("lo_eigen", "lo_det"):
        assert SG._predicted(vault, repository, lo, "2026-11-02T09:00:00Z") == pytest.approx(
            lo_prediction(vault, repository, lo)["p"], abs=5e-5)
    set_config(paths.root, {("teacher", "enabled"): False})
    off = load_vault(paths.root)
    assert not SG.suggestions_active(off) and not S.lessons_active(off)
