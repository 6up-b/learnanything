"""TE5 review fix round, protection (TE5-R1, TE5-R2): nothing protected reaches a model, nothing protected is shown
again.

R1: the topic resolver's catalog is screened record by record (``deliverables.catalog_screen``), whichever topic the
request is about: a clean proposal never carries another topic's summary that quotes a question kept for an exam.
R2: ``lesson.view`` and every action's returned feed pass the saved strings through today's protection: a turn that
quotes a question reserved since it was written is withheld in plain words, the closing action's response included.
"""
from __future__ import annotations

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.deliverable_fixtures import DeliverableFake
from tests.teacher_fakes import RESERVED_SENTINEL, TeacherFake, build_teacher_vault, clients

PHRASE = "when diagonalization fails"
#: A question that becomes reserved for an exam after a lesson's turn quoted it.
LATER_QUESTION = "Explain why the zebrafinch matrix quokkamarmot has a repeated eigenvalue of seven"


def proposal(_context):
    return {"message": "Here is another topic you could study.", "requests": [
        {"action": "create_goal_lo", "phrase": PHRASE, "title": "Defective matrices",
         "statement": "Recognize a missing eigenvector.", "anchors": []}]}


def _summary(paths, lo_id: str, summary: str) -> None:
    path = paths.learning_object_path("linear-algebra", lo_id)
    record = read_yaml(path)
    record["summary"] = summary
    write_yaml(path, record)


def test_catalog_never_sends_another_topics_protected_summary(tmp_path):
    paths, repo = build_teacher_vault(tmp_path / "vault")
    # Another topic's summary quotes the question the vault keeps for an exam (the teacher's topic is clean).
    _summary(paths, "lo_det", f"Determinants. Worked example: {RESERVED_SENTINEL}: compute it.")
    resolver = DeliverableFake(unmatched=(PHRASE,), needs=("lo_det",))
    teacher = TeacherFake([proposal])
    providers = clients(teacher)
    providers.resolver = lambda: resolver
    view = S.open_lesson(load_vault(paths.root), repo, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=providers)
    assert resolver.calls == 1
    sent = resolver.prompts[-1]
    assert "RESERVEDSENTINEL" not in sent
    topics = {record["id"] for record in resolver.contexts[-1]["topics"]}
    assert "lo_det" not in topics and "lo_eigen" in topics
    assert "RESERVEDSENTINEL" not in teacher.all_prompts()
    # A protected record cannot be chosen either: the fake names lo_det, the resolution drops it.
    offer, = [row for row in S.load_state(repo, view["lesson_id"]).turns if row["action"] == "topic_offer"]
    assert "lo_det" not in str(offer["payload"])


def test_typed_goal_catalog_is_screened_and_fails_closed(tmp_path, monkeypatch):
    from learnloop.source_retrieval import deliverables as DL
    from learnloop import learner_protection as LP

    paths, repo = build_teacher_vault(tmp_path / "vault")
    _summary(paths, "lo_det", f"Determinants. Worked example: {RESERVED_SENTINEL}: compute it.")
    resolver = DeliverableFake(unmatched=(PHRASE,))
    result = DL.resolve_typed_goal(load_vault(paths.root), repo, "eigenvalues", client=resolver)
    assert result.status == "ready" and "RESERVEDSENTINEL" not in resolver.prompts[-1]
    monkeypatch.setattr(LP, "reserved_book", lambda *_a, **_k: LP.ReservedBook(unreadable=True))
    calls = resolver.calls
    result = DL.resolve_typed_goal(load_vault(paths.root), repo, "determinants please", client=resolver)
    assert result.status == "unavailable" and result.reason == "protection_unavailable"
    assert resolver.calls == calls
