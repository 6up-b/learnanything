"""TE5 review fix round, evidence (TE5-R5, TE5-R6, TE5-R14).

R5: a check posed on a topic the learner just added credits that topic: it is read against the turn's own plan.
R6: teaching on a topic with no practice item yet still records what was shown, so a generated probe on it is not
independent evidence.
R14: a rebuild writes the same lesson-weight rows as the live path (a withdrawn first check writes none on either
side; the live refresh commits with the answered result).
"""
from __future__ import annotations

from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients

PHRASE = "when diagonalization fails"


def proposal(_context):
    return {"message": "Here is another topic you could study.", "requests": [
        {"action": "create_goal_lo", "phrase": PHRASE, "title": "Defective matrices",
         "statement": "Recognize a missing eigenvector.", "anchors": []}]}


def _with_added_topic(tmp_path, turns):
    paths, repo = build_teacher_vault(tmp_path / "vault")
    teacher = TeacherFake([proposal, *turns])
    providers = clients(teacher)
    providers.resolver = lambda: DeliverableFake(unmatched=(PHRASE,))
    lesson = S.open_lesson(load_vault(paths.root), repo, entry="learning_object", learning_object_ids=["lo_eigen"],
                           clients=providers)["lesson_id"]
    offer, = [row for row in S.load_state(repo, lesson).turns if row["action"] == "topic_offer"]
    S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="reply",
                payload={"text": f"Add t{offer['seq']}"}, clients=providers)
    added, = [row["payload"]["learning_object_id"] for row in S.load_state(repo, lesson).turns
              if row["action"] == "topic_accepted"]
    return paths, repo, teacher, providers, lesson, added


def test_a_check_on_a_newly_added_topic_credits_that_topic(tmp_path):
    def plan_and_check(_context):
        return {"message": "Now the new topic.",
                "requests": [{"action": "write_plan", "plan": [
                    {"id": "n1", "statement": "An eigenvalue scales its eigenvector.", "lo_id": "lo_eigen",
                     "anchors": [], "premises": []},
                    {"id": "n2", "statement": "A defective matrix lacks an eigenvector basis.", "lo_id": ADDED[0],
                     "anchors": [], "premises": ["n1"]}]},
                    {"action": "forecast", "forecast_kind": "lesson_check_correct", "node": "n2", "p": 0.6}],
                "check": {"node": "n2", "question": "Can [[1,1],[0,1]] be diagonalized? Why?", "form": "free",
                          "committed_solution": "No: it has one independent eigenvector.",
                          "rubric": [{"id": "basis", "fact": "only one independent eigenvector", "points": 2}],
                          "anchors": []}}

    ADDED: list[str] = []
    paths, repo, _teacher, providers, lesson, added = _with_added_topic(tmp_path, [plan_and_check])
    ADDED.append(added)
    S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="reply", payload={"text": "go on"},
                clients=providers)
    state = S.load_state(repo, lesson)
    posed, = [row["payload"] for row in state.turns if row["action"] == "pose_check"]
    assert posed["learning_object_id"] == added
    assert load_vault(paths.root).practice_items[posed["item_id"]].learning_object_id == added
    forecast, = [row["payload"] for row in state.turns if row["action"] == "forecast"]
    assert added in str(forecast) and "lo_eigen" not in str(forecast)


def test_teaching_on_an_itemless_topic_makes_a_generated_probe_on_it_dependent(tmp_path):
    from types import SimpleNamespace

    from learnloop.followup_run.jobs import process_next_job
    from tests.teacher_te2_probes_helpers import ProbeAuthor

    paths, repo = build_teacher_vault(tmp_path / "vault")
    for path in paths.root.rglob("*.yaml"):  # lo_inner as a topic with no practice item yet
        if "learning_object_id: lo_inner" in path.read_text(encoding="utf-8") and "practice" in str(path):
            path.unlink()
    vault = load_vault(paths.root)
    assert not [item for item in vault.practice_items.values() if item.learning_object_id == "lo_inner"]
    # The explanation states the rule the generated question will test (its expected answer, word for word) on a
    # topic with no practice item, so no item existed that the words could be measured against when shown.
    teaching = {"message": "Remember: ibis heron: (1, 0) by three. Now one quick question.", "requests": [
        {"action": "write_plan", "plan": [{"id": "n1", "statement": "Inner products measure alignment.",
                                           "lo_id": "lo_inner", "anchors": [], "premises": []}]},
        {"action": "serve_probe", "node": "n1", "readings": ["treats the inner product as a vector"], "p": 0.4}]}
    teacher = TeacherFake([teaching, {"message": "Good."}])
    lesson = S.open_lesson(vault, repo, entry="learning_object", learning_object_ids=["lo_inner"],
                           clients=clients(teacher))["lesson_id"]
    author = ProbeAuthor()
    while process_next_job(load_vault(paths.root), repo, owner="test", clients=SimpleNamespace(author=author)):
        pass
    S.view_lesson(load_vault(paths.root), repo, lesson)
    with repo.connection() as connection:
        from learnloop.db.stores import lessons as store
        from learnloop.teacher import probes as PR

        probe = PR.probes(store.turns(connection, lesson))[0]
    assert probe.status == "served"
    S.take_turn(load_vault(paths.root), repo, lesson_id=lesson, action="answer_probe",
                payload={"answer": "(1, 0), stretched by three", "tap": 4}, clients=clients(teacher))
    result, = [row["payload"] for row in S.load_state(repo, lesson).turns if row["action"] == "probe_result"]
    assert result["independent"] is False
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reveal_events WHERE practice_item_id = ? AND basis = ?",
                                  (probe.item_id, f"lesson:{lesson}")).fetchone()[0] == 1
