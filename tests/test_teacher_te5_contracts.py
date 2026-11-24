"""A provider's V1 contract and the capability-projected execution contract agree."""
from itertools import product

import pytest
from pydantic import ValidationError

from learnloop.teacher import service
from learnloop.teacher.contracts import (
    ACTIONS, TE2_ACTIONS, capabilities, lesson_capabilities, parse_turn,
)
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients
from tests.ux_phase1_support import set_config


def _cases():
    node = {"id": "n", "statement": "Trace the determinant."}
    for action in (*ACTIONS, "note_detour", *TE2_ACTIONS, "unknown"):
        for fields in ({}, {"p": 0}, {"p": 1.01}, {"hypothesis": None}, {"repair": "reteach"},
                       {"readings": []}, {"gap_kind": "prerequisite"}, {"gap": None}, {"ref": "t1"},
                       {"query": "q", "intent": "explain"}, {"extra": False}):
            yield {"requests": [{"action": action, **fields}]}
    for fields in ({}, {"visual": None}, {"visual": {"goal": "Trace", "anchors": ["S1"]}},
                   {"p_held": None}, {"p_held": 0.2}, {"p_held": -1}, {"unknown": "field"}):
        yield {"requests": [{"action": "write_plan", "plan": [{**node, **fields}]}]}
    yield {"visual": None}
    yield {"visual": {"goal": "Trace", "anchors": ["S1"]}}
    yield {"requests": [{"action": "read_note"}] * 9}
    yield {"visual": {"anchors": ["S1"] * 4}}
    yield {"message": "m" * 12001}
    yield {"choices": ["x"] * 7}
    yield {"check": {"node": "n", "question": "Q", "form": "free", "committed_solution": "A",
                     "rubric": [{"id": "c", "fact": "F", "points": 1}]}}
    yield {"requests": [{}]}


@pytest.mark.parametrize(("visuals", "episodes", "probes"), product((False, True), repeat=3))
def test_wire_and_union_admit_the_same_inputs(visuals, episodes, probes):
    allowed = capabilities(visuals=visuals, episodes=episodes, probes=probes)
    wire = service.wire_model(allowed)
    for data in _cases():
        try:
            accepted = wire.model_validate(data)
        except ValidationError:
            with pytest.raises(ValidationError):
                parse_turn(data, allowed)
        else:
            assert parse_turn(data, allowed).model_dump(exclude_unset=True) == accepted.model_dump(exclude_unset=True)
            # The ledger is written from the normalized wire object. Recovery
            # must preserve its default fields and the absence of later fields.
            saved = accepted.model_dump()
            assert parse_turn(saved, allowed).model_dump(exclude_unset=True) == saved


def test_legacy_open_uses_its_journal_and_brief():
    row = {"brief_version": "lesson_brief_v2", "goal": {}}
    turn = {"action": "teacher_turn", "validation": "ok", "payload": {"episodes": "v1"}}
    assert lesson_capabilities(row, []) == {"probes"}
    assert lesson_capabilities(row, [turn]) == {"episodes", "probes"}
    assert lesson_capabilities({**row, "goal": {"capabilities": []}}, [turn]) == set()


def test_a_lesson_uses_the_capabilities_recorded_at_open(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([{"message": "Hello."}, {"message": "Keep going."}])
    set_config(paths.root, {("teacher", "episode_log"): True})
    opened = service.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                                 learning_object_ids=["lo_eigen"], clients=clients(fake))
    lesson_id = opened["lesson_id"]
    state = service.load_state(repository, lesson_id)
    assert state.lesson["goal"]["capabilities"] == ["episodes", "goal_topics", "probes"]
    assert "capabilities" not in state.brief["goal"]
    set_config(paths.root, {("teacher", "episode_log"): False})
    service.take_turn(load_vault(paths.root), repository, lesson_id=lesson_id, action="reply",
                      payload={"text": "Continue."}, clients=clients(fake))
    assert fake.result_models == [service.wire_model(state.capabilities)] * 2


@pytest.mark.parametrize(("visuals", "episodes", "probes"), product((False, True), repeat=3))
def test_recovery_keeps_the_predecessors_plan_and_read_payloads(visuals, episodes, probes):
    from learnloop.teacher import te2

    allowed = capabilities(visuals=visuals, episodes=episodes, probes=probes)
    wire = service.wire_model(allowed).model_validate({"requests": [
        {"action": "write_plan", "plan": [{"id": "n", "statement": "Trace it."}]},
        {"action": "read_source", "refs": ["S1"]},
    ]}).model_dump()
    entry = {"payload": {"turn": wire, "visuals": visuals, "episodes": episodes, "te2": probes}}
    expected = te2.stored_turn(wire)
    recovered = service._recovery_turn(entry)
    assert recovered.model_dump(exclude_unset=True) == expected.model_dump()


@pytest.mark.parametrize(("visuals", "episodes", "probes", "digest"), [
    (False, False, False, "b3d8325536b1a50e9852470b355d61e2cae347fec9fb09e7b30f875a88a51e0c"),
    (False, False, True, "4abd07f9dd1e77523692bf8ddc1bc4df2bc4213f16e22e09e0610bb8c7e28992"),
    (False, True, False, "89ba3e7c4459861c182d62883b8cee1721d92776723ea7379c86f6ccf27416b6"),
    (False, True, True, "305453bb0fa27b8d9227e361be4a5b6edb25610b233653ca8c9ae2d541607684"),
    (True, False, False, "db89fbadccbd9069c613f119f8c794ed8f8906f5f2289f8492a8095ca8187ca0"),
    (True, False, True, "61988c009a3f7d68e54e26183b4c4e538b6fde516cad592d5c2df5ed766bb356"),
    (True, True, False, "f14f53ea2dbcba23e76a55e841ebbcda849e2eb2a620d720890d60a01c3317a7"),
    (True, True, True, "a5df7189cd64b9134b174a3bfa7492d44215fe3d9f8d4118d3e953a36d46edc4"),
])
def test_predecessor_prompt_bytes(visuals, episodes, probes, digest):
    import hashlib

    from learnloop.teacher.brief import SourceBook

    state = service.LessonState(lesson={}, brief={}, book=SourceBook(), turns=[], checks=[], plans=[])
    prompt = service._prompt(state, results=[], help_reply=False, visuals=visuals, episodes=episodes, te2=probes)
    assert hashlib.sha256(prompt.encode()).hexdigest() == digest
