"""Teacher topic requests resolve first and create through C0b only on the learner's decision."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from learnloop.teacher import service as S
from learnloop.teacher.contracts import capabilities, parse_turn
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.teacher_fakes import RESERVED_SENTINEL, TeacherFake, build_teacher_vault, clients

PHRASE = "when diagonalization fails"


def proposal(context):
    return {"message": "Here is another topic you could study.", "requests": [
        {"action": "create_goal_lo", "phrase": PHRASE, "title": "Defective matrices",
         "statement": "Recognize a missing eigenvector.", "anchors": []}]}


def _open(tmp_path, *, resolver, turns):
    paths, repo = build_teacher_vault(tmp_path / "vault")
    teacher = TeacherFake(turns)
    providers = clients(teacher)
    providers.resolver = lambda: resolver
    view = S.open_lesson(load_vault(paths.root), repo, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=providers)
    return paths, repo, providers, view


def _reply(paths, repo, providers, lesson, text):
    return S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="reply", payload={"text": text},
                       clients=providers)


def _offers(repo, lesson):
    return [row for row in S.load_state(repo, lesson).turns if row["action"] == "topic_offer"]


def test_lookup_consent_replay_and_receipt(tmp_path):
    resolver = DeliverableFake(unmatched=(PHRASE,))
    def anchored(context):
        turn = proposal(context)
        turn["requests"][0]["anchors"] = [context["brief"]["sources"]["sections"][0]["passages"][0]["alias"]]
        return turn

    paths, repo, providers, view = _open(tmp_path, resolver=resolver, turns=[
        {"message": "Which topic next?"}, anchored, {"message": "Library results."}])
    lesson = view["lesson_id"]
    view = _reply(paths, repo, providers, lesson, PHRASE)
    offer, = _offers(repo, lesson)
    assert resolver.calls == 1 and offer["payload"]["status"] == "pending"
    assert not any(lo.startswith("lo_goal_") for lo in load_vault(paths.root).learning_objects)
    ref = f"t{offer['seq']}"
    text = next(row["text"] for row in view["feed"] if row["kind"] == "notice" and "Reply" in row["text"])
    assert text.index(f"Library {ref}") < text.index(f"Add {ref}") < text.index(f"Skip {ref}")
    _reply(paths, repo, providers, lesson, f"Library {ref}")
    state = S.load_state(repo, lesson)
    lookup, = [row for row in state.turns if row["action"] == "find_sources"]
    assert lookup["payload"]["request"]["query"] == PHRASE
    assert lookup["payload"]["result"]["tool_call_id"]
    assert "passages" in lookup["payload"]["result"] and "refused" not in lookup["payload"]["result"]
    result, = providers.teacher().contexts[-1]["results"]
    assert result["action"] == "find_sources" and result["result"]["passages"] == lookup["payload"]["result"]["passages"]
    assert not any(row["action"] == "goal_lo" for row in state.turns)
    accepted = _reply(paths, repo, providers, lesson, f"Add {ref}")
    assert accepted["vault_changed"]
    _reply(paths, repo, providers, lesson, f"Add {ref}")
    _reply(paths, repo, providers, lesson, f"Skip {ref}")
    state = S.load_state(repo, lesson)
    entry, = [row for row in state.turns if row["action"] == "goal_lo"]
    decision, = [row for row in state.turns if row["action"] == "topic_accepted"]
    assert decision["refs"]["offer"] == offer["id"]
    lo = entry["payload"]["learning_object_id"]
    provenance = load_vault(paths.root).learning_objects[lo].provenance
    assert lo in state.los and provenance.mechanism == "teacher_goal_v1"
    passage = state.book.passages[offer["payload"]["anchors"][0]]
    source, = provenance.source_refs
    assert source.ref_type == "canonical_source" and source.ref_id == passage["extraction_id"]
    assert source.span_ids == [passage["span_id"]]
    S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="close", payload={}, clients=providers)
    with repo.connection() as con:
        assert con.execute("SELECT count(*) FROM lesson_episodes WHERE created_lo_id=?", (lo,)).fetchone()[0] == 1
        assert con.execute("SELECT json_extract(receipt_json,'$.created_los[0]') FROM lesson_receipts").fetchone()[0] == lo
    assert resolver.calls == 1


def test_decline_then_stale_consent_never_creates(tmp_path):
    paths, repo, providers, view = _open(tmp_path, resolver=DeliverableFake(unmatched=(PHRASE,)), turns=[proposal])
    lesson = view["lesson_id"]
    offer, = _offers(repo, lesson)
    _reply(paths, repo, providers, lesson, f"Skip t{offer['seq']}")
    _reply(paths, repo, providers, lesson, f"Add t{offer['seq']}")
    assert [row["action"] for row in S.load_state(repo, lesson).turns if row["refs"].get("offer")] == ["topic_declined"]
    assert not any(lo.startswith("lo_goal_") for lo in load_vault(paths.root).learning_objects)


def test_existing_topic_never_offers_creation(tmp_path):
    paths, repo, providers, view = _open(tmp_path, resolver=DeliverableFake(needs=("lo_eigen",)), turns=[proposal])
    offer, = _offers(repo, view["lesson_id"])
    assert offer["payload"] == {"status": "matched", "learning_object_ids": ["lo_eigen"]}
    assert "already has a matching topic" in str(view["feed"])
    assert not any(lo.startswith("lo_goal_") for lo in load_vault(paths.root).learning_objects)


@pytest.mark.parametrize(("field", "bad"), [("anchors", ["S9999"]), ("statement", RESERVED_SENTINEL)])
def test_guard_precedes_resolver(tmp_path, field, bad):
    turn = proposal({})
    turn["requests"][0][field] = bad
    resolver = DeliverableFake(unmatched=(PHRASE,))
    _, repo, _, view = _open(tmp_path, resolver=resolver, turns=[turn, {"message": "We can continue."}])
    assert resolver.calls == 0 and not _offers(repo, view["lesson_id"])
    assert any(row["validation"] in ("invalid", "withheld") for row in S.load_state(repo, view["lesson_id"]).turns)
    assert RESERVED_SENTINEL not in str(view["feed"])


def test_pre_offer_schema_and_executor_refuse_new_action():
    allowed = capabilities(visuals=True, episodes=True, probes=True)
    turn = proposal({})
    with pytest.raises(ValidationError):
        S.wire_model(allowed).model_validate(turn)
    with pytest.raises(ValidationError):
        parse_turn(turn, allowed)
    new = S.wire_model(allowed | {"goal_topics"}).model_validate(turn).model_dump()
    recovered = S._recovery_turn({"payload": {"turn": new, "te2": True, "episodes": True, "visuals": True,
                                              "goal_topics": True}})
    assert recovered.model_dump(exclude_unset=True) == new


def test_resume_after_yaml_publication_finishes_consent_once(tmp_path, monkeypatch):
    from learnloop.goals import goal_lo

    paths, repo, providers, view = _open(tmp_path, resolver=DeliverableFake(unmatched=(PHRASE,)), turns=[proposal])
    lesson = view["lesson_id"]
    offer, = _offers(repo, lesson)

    def interrupted(*args, **kwargs):
        raise RuntimeError("interrupted before database sync")

    with monkeypatch.context() as patch:
        patch.setattr(goal_lo, "sync_vault_state", interrupted)
        with pytest.raises(RuntimeError, match="interrupted before database sync"):
            _reply(paths, repo, providers, lesson, f"Add t{offer['seq']}")
    lo, = [key for key in load_vault(paths.root).learning_objects if key.startswith("lo_goal_")]
    assert not any(row["action"] == "goal_lo" for row in S.load_state(repo, lesson).turns)
    assert repo.mastery_state(lo) is None
    for _ in range(2):
        S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="resume", payload={}, clients=providers)
    assert repo.mastery_state(lo) is not None
    state = S.load_state(repo, lesson)
    assert [row["action"] for row in state.turns if row["action"] in ("topic_requested", "topic_accepted", "goal_lo")
            ] == ["topic_requested", "topic_accepted", "goal_lo"]
    assert len(providers.teacher().prompts) == 1


def test_consent_rechecks_a_changed_catalog(tmp_path):
    from learnloop.source_retrieval.deliverables import create_lesson_topic

    resolver = DeliverableFake(unmatched=(PHRASE,))
    paths, repo, providers, view = _open(tmp_path, resolver=resolver, turns=[proposal])
    lesson = view["lesson_id"]
    offer, = _offers(repo, lesson)
    existing = create_lesson_topic(load_vault(paths.root), repo, lesson_id="earlier", phrase=PHRASE,
                                   title="Defective matrices", statement="Recognize a missing eigenvector.",
                                   subject_id=offer["payload"]["subject_id"])
    resolver.unmatched = ()
    resolver.needs = (existing["learning_object_id"],)
    after = _reply(paths, repo, providers, lesson, f"Add t{offer['seq']}")
    assert resolver.calls == 2
    assert "resolution changed" in str(after["feed"])
    assert [row["action"] for row in S.load_state(repo, lesson).turns if row["refs"].get("offer")] == ["topic_refused"]
    assert [key for key in load_vault(paths.root).learning_objects if key.startswith("lo_goal_")] == [
        existing["learning_object_id"]]
