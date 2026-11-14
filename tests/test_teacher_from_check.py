"""A lesson opened from a diagnostic check reads what the check found (``learnloop.teacher.from_check``).

"Teach me this" at a check's end and "Stop diagnosing and teach me" during one open a lesson naming the check's
episode. The brief's ``from_check`` carries the finding as topic-level words only; the check's questions, the learner's
answers, the first error step, the posterior and the tutor's numbers never reach the teacher. Every model is a fake.
"""

from __future__ import annotations

import io
import json

import pytest

from learnloop.teacher import service as S
from learnloop.teacher.from_check import ABOUT, NO_DECISION, NOT_FOUND, OTHER_TOPIC, STILL_OPEN, from_check
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import ITEMS, TeacherFake, build_teacher_vault, clients, plan_turn

MIXUP = "Thinks the eigenvalues of any matrix are its diagonal entries."
FIRST_ERROR = "claim_FIRSTERR_7q"
CONFIDENCE = 0.7123
SCAFFOLD = 0.4321


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _decision(gap: str, *, intent: str = "repair", confidence: float = CONFIDENCE) -> dict:
    """A typed transition decision with every key ``probe_blocks.build_typed_transition_decision`` writes."""

    return {"target_facets": ["facet_eigen"], "diagnosed_gap": gap, "first_error_step_or_claim": FIRST_ERROR,
            "misconception_id": None, "diagnostic_confidence": confidence, "tutor_move": "localize_error",
            "instructional_intent": intent, "instructional_action": None, "scaffold_level": SCAFFOLD,
            "answer_reveal_budget": 1, "expected_learner_action": "attempt_targeted_practice",
            "source_ref_ids": ["ref_x"], "posterior": {gap: confidence, "unfamiliar": 0.1877}}


def _episode(repository, *, lo: str = "lo_eigen", status: str = "converted_to_tutoring", decision=None) -> str:
    episode_id = repository.insert_probe_episode(learning_object_id=lo, status="in_progress", trigger="initial",
                                                 hypothesis_set_id=None, active_state_segment_id=None,
                                                 algorithm_version="test", target_decision=decision)
    with repository.connection() as connection:
        connection.execute("UPDATE probe_episodes SET status = ? WHERE id = ?", (status, episode_id))
        connection.commit()
    return episode_id


def _mixup(repository) -> str:
    return repository.insert_misconception(learning_object_id="lo_eigen", statement=MIXUP, severity=0.6)


def _open(paths, repository, **kwargs):
    fake = TeacherFake([plan_turn])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), **kwargs)
    return fake, view


def _open_turn(repository, lesson_id):
    refs, payload = _rows(repository,
                          "SELECT t.refs_json, p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p "
                          "ON p.turn_id = t.id WHERE t.lesson_id = ? AND t.action = 'open'", (lesson_id,))[0]
    return json.loads(refs or "{}"), json.loads(payload)


def test_a_lesson_opened_from_a_stopped_check_is_told_the_finding_in_topic_words(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    misconception = _mixup(repository)
    episode = _episode(repository, decision=_decision(f"misconception:{misconception}"))

    fake, view = _open(paths, repository, probe_episode_id=episode)

    entry = fake.contexts[0]["brief"]["from_check"]
    assert entry == {"about": ABOUT, "topic": load_vault(paths.root).learning_objects["lo_eigen"].title,
                     "learning_object_id": "lo_eigen",
                     "ended": "the learner stopped the check and asked to be taught",
                     "gap": {"kind": "mix_up", "words": MIXUP}, "next_step": "repair the belief",
                     "confidence": "about 70%"}
    # Nothing of the check's questions, answers, trace, posterior or the tutor's numbers reaches the teacher.
    teacher_prompts = "\n".join(p for purpose, p in fake.prompts if purpose == "teacher_turn")
    for leaked in (FIRST_ERROR, str(CONFIDENCE), str(SCAFFOLD), "0.1877", "localize_error", "ref_x"):
        assert leaked not in teacher_prompts
    dumped = json.dumps(entry)
    for _lo, prompt, answer in ITEMS.values():
        assert prompt not in dumped and answer not in dumped
    # The lesson's record names the episode it was opened from.
    refs, payload = _open_turn(repository, view["lesson_id"])
    assert refs["probe_episode"] == episode
    assert payload["from_check"] == {"version": "lesson_from_check_v1", "probe_episode_id": episode,
                                     "status": "used", "why": ""}
    assert payload["brief"]["from_check"] == entry


def test_a_lesson_opened_any_other_way_has_no_from_check(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _episode(repository, decision=_decision("unfamiliar", intent="instruct"))

    fake, view = _open(paths, repository)

    assert "from_check" not in fake.contexts[0]["brief"]
    refs, payload = _open_turn(repository, view["lesson_id"])
    assert "probe_episode" not in refs and "from_check" not in payload


@pytest.mark.parametrize("case", ["unknown", "other_topic", "still_open", "opening_stamp", "no_decision"])
def test_an_episode_that_does_not_fit_is_ignored_and_the_lesson_still_opens(tmp_path, case):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    episode, why = {
        "unknown": lambda: ("ep_nowhere", NOT_FOUND),
        "other_topic": lambda: (_episode(repository, lo="lo_det", decision=_decision("unfamiliar")), OTHER_TOPIC),
        "still_open": lambda: (_episode(repository, status="in_progress", decision=_decision("unfamiliar")), STILL_OPEN),
        "opening_stamp": lambda: (_episode(repository, status="complete", decision={"kind": "placement_opening"}),
                                  NO_DECISION),
        "no_decision": lambda: (_episode(repository, status="complete", decision=None), NO_DECISION),
    }[case]()

    fake, view = _open(paths, repository, probe_episode_id=episode)

    assert view["lesson_id"] and "from_check" not in fake.contexts[0]["brief"]
    refs, payload = _open_turn(repository, view["lesson_id"])
    assert "probe_episode" not in refs
    assert payload["from_check"] == {"version": "lesson_from_check_v1", "probe_episode_id": episode,
                                     "status": "ignored", "why": why}


@pytest.mark.parametrize(("gap", "intent", "kind", "words", "next_step"), [
    ("unfamiliar", "instruct", "not_learned_yet", "has not learned this topic yet", "teach it"),
    ("procedure_without_selection", "instruct", "procedure_without_selection",
     "can run the procedure but not choose when to use it", "teach it"),
    ("confuses_with:lo_det", "repair", "confused_with", None, "repair the belief"),
    ("confuses_with:c_nowhere", "repair", "confused_with", "mixes this topic up with a neighbouring topic",
     "repair the belief"),
    ("misconception:sign_flip", "repair", "mix_up", "sign flip", "repair the belief"),
    ("", "instruct", "unnamed", "a cause the check could not name", "teach it"),
])
def test_each_kind_of_gap_is_named_in_the_topic_s_own_words(tmp_path, gap, intent, kind, words, next_step):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    episode = _episode(repository, status="complete", decision=_decision(gap, intent=intent, confidence=0.35))

    entry, record = from_check(vault, repository, probe_episode_id=episode, learning_object_ids=["lo_eigen"])

    expected = words or f"mixes this topic up with {vault.learning_objects['lo_det'].title}"
    assert entry["gap"] == {"kind": kind, "words": expected}
    assert entry["ended"] == "the check finished" and entry["next_step"] == next_step
    assert entry["confidence"] == "about 40%" and record["status"] == "used"


def test_the_stop_reports_its_episode_and_a_real_decision_reads_as_topic_words(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.probe_episodes import enter_episode
    from learnloop_sidecar.server import serve
    from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository)
    episode = enter_episode(load_vault(vault_root), repository, "lo_svd_definition", clock=FrozenClock(NOW))
    messages = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
                {"jsonrpc": "2.0", "id": 2, "method": "stop_probe_diagnosing",
                 "params": {"practiceItemId": "pi_svd_define_001"}}]
    stdout = io.StringIO()
    serve(io.StringIO("".join(json.dumps(m) + "\n" for m in messages)), stdout)
    result = [json.loads(line) for line in stdout.getvalue().splitlines()][1]["result"]

    assert result["stopped"] is True
    assert result["episodeId"] == episode.id and result["learningObjectId"] == "lo_svd_definition"
    entry, record = from_check(load_vault(vault_root), repository, probe_episode_id=episode.id,
                               learning_object_ids=["lo_svd_definition"])
    assert record["status"] == "used"
    assert set(entry) <= {"about", "topic", "learning_object_id", "ended", "gap", "next_step", "confidence"}
    assert entry["ended"] == "the learner stopped the check and asked to be taught"
    decision = repository.probe_episode(episode.id).target_decision
    assert decision["tutor_move"] not in json.dumps(entry)


def test_the_lesson_rpc_passes_the_episode_only_for_a_learner_s_own_start(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    seen = []
    monkeypatch.setattr(H.S, "open_lesson", lambda *args, **kwargs: seen.append(kwargs) or {"lesson_id": "les_x"})

    class _Ctx:
        grading_provider_override = None

        def require_vault(self):
            return load_vault(paths.root), repository

        def reload(self, maintenance: bool = True):
            pass

    H.lesson_turn(_Ctx(), H.LessonTurnInput(action="open", entry="learning_object", learning_object_ids=["lo_eigen"],
                                            probe_episode_id="ep_1"))
    H.lesson_turn(_Ctx(), H.LessonTurnInput(action="open", entry="learning_object", origin="router_suggestion",
                                            suggestion_decision_id="dec_1", lesson_id="les_1",
                                            probe_episode_id="ep_1"))
    assert [call["probe_episode_id"] for call in seen] == ["ep_1", None]
