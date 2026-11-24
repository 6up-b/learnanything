"""Compaction through the live teacher dispatcher, using only local model doubles."""
from contextlib import nullcontext
import json

import pytest

from learnloop.ai.execution import model_call, record_model_calls
from learnloop.db.stores import lessons as store
from learnloop.teacher import compaction as C, delayed, service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, landed_turn, plan_turn
from tests.teacher_te2log_episodes_helpers import detour_turn


class CountedTeacher(TeacherFake):
    def __init__(self, script, counts):
        super().__init__(script)
        self.counts = iter(counts)

    def complete(self, request):
        if request.purpose != "teacher_turn":
            return super().complete(request)
        with model_call(self, purpose="teacher_turn:physical", prompt=request.prompt) as metadata:
            input_count, output_count = next(self.counts)
            metadata.update(input_tokens=input_count, output_tokens=output_count)
            return super().complete(request)


def opening(context):
    turn = plan_turn(context)
    turn["message"] = "Old explanation. " * 120
    return turn


def open_case(tmp_path, limit, fake):
    config = '[teacher]\nepisode_log = true\n'
    if limit is not None:
        config += f'[ingest.providers.fake_teacher]\ncontext_tokens = {limit}\n'
    paths, repo = build_teacher_vault(tmp_path / "vault", config=config)
    vault = load_vault(paths.root)
    with record_model_calls(repo, owner_kind="sidecar_rpc", owner_id="opening"):
        view = S.open_lesson(vault, repo, entry="learning_object", learning_object_ids=["lo_eigen"],
                             clients=clients(fake))
    return vault, repo, view["lesson_id"]


def take(case, fake, action="reply", **payload):
    vault, repo, lesson = case
    with record_model_calls(repo, owner_kind="sidecar_rpc", owner_id="reply"):
        return S.take_turn(vault, repo, lesson_id=lesson, action=action, payload=payload or {"text": "Go on."},
                           clients=clients(fake))


def decisions(repo):
    with repo.connection() as conn:
        return [(json.loads(facts), detail) for facts, detail in conn.execute(
            "SELECT facts_json, detail_id FROM decision_records WHERE kind='lesson_context_compaction' ORDER BY rowid")]


@pytest.mark.parametrize(("limit", "compact"), [(None, False), (1501, False), (1500, True)])
def test_live_boundary_and_predecessor_bytes(tmp_path, limit, compact):
    # Need = 1200 + (1200 - 1000 + 100). Equality must trigger.
    fake = CountedTeacher([opening, {"message": "Recent words."}, close_turn()], [(1000, 60), (1200, 100), (900, 30)])
    case = open_case(tmp_path, limit, fake)
    take(case, fake, text="First reply.")
    take(case, fake, text="Latest reply.")
    vault, repo, lesson = case
    state = S.load_state(repo, lesson)
    assert all(t["action"] != "context_compacted" for t in state.turns)
    before = next(t["seq"] for t in state.turns if t["action"] == "learner_reply"
                  and t["payload"]["text"] == "Latest reply.")
    state.turns = [t for t in state.turns if t["seq"] <= before]
    history = S.transcript(state)
    full = S._prompt(state, results=[], help_reply=False, episodes=True, te2=True, goal_topics=True)
    projected = fake.contexts[-1]["transcript"]
    with repo.connection() as conn:
        receipt = store.receipt(conn, lesson)
    if compact:
        assert projected[1:] == history[1:]
        assert projected[0]["summary"]["version"] == receipt["summary_version"]
        assert "Old explanation." not in fake.prompts[-1][1]
        [(facts, detail)] = decisions(repo)
        assert (facts["predicted_tokens"], facts["context_limit"], facts["growth_samples"]) == (1500, 1500, 1)
        with repo.connection() as conn:
            notes, owner, purpose = conn.execute(
                "SELECT budget_json, owner_kind, purpose FROM model_call_receipts WHERE id=?", (detail,)).fetchone()
            assert conn.execute("SELECT detail_table FROM decision_records WHERE detail_id=?",
                                (detail,)).fetchone()[0] == "model_call_receipts"
        assert (owner, purpose) == ("sidecar_rpc", "teacher_turn")
        assert json.loads(notes) == {"teacher_lesson_id": lesson, "transcript_prefix": 1,
                                     "summary_version": C.VERSION, "context_summary": projected[0]["summary"]}
        encode = json.JSONEncoder(sort_keys=True, ensure_ascii=False).encode
        assert fake.prompts[-1][1] == full.replace(encode(history), encode(projected), 1)
    else:
        assert projected == history
        assert decisions(repo) == [] and "summary_version" not in receipt
        assert fake.prompts[-1][1] == full
        if limit is None:
            with repo.connection() as conn:
                assert [r[0] for r in conn.execute("SELECT budget_json FROM model_call_receipts "
                                                   "WHERE purpose='teacher_turn'")] == [None] * 3
    assert len(fake.contexts) == 3


def test_interrupted_compaction_preserves_evidence_and_replays_receipt(tmp_path):
    def outage(_):
        raise RuntimeError("offline")

    fake = CountedTeacher([opening, detour_turn(), check_turn(), landed_turn(), outage, close_turn()],
                          [(1000, 80), (1200, 100), (1300, 100), (1900, 100), (None, None), (950, 40)])
    case = open_case(tmp_path, 2400, fake)
    vault, repo, lesson = case
    take(case, fake)
    take(case, fake)
    take(case, fake, "answer_check", answer="det(A - tI) = 0", tap=4)
    with pytest.raises(S.LessonError):
        take(case, fake)
    attempted = fake.prompts[-1][1]
    take(case, fake, "resume")
    assert fake.prompts[-1][1] == attempted
    assert len(decisions(repo)) == 1
    state = S.load_state(repo, lesson)
    summary = fake.contexts[-1]["transcript"][0]["summary"]
    assert summary["capabilities"] == sorted(state.capabilities)
    check, = summary["checks"]
    assert (check["attempt_id"], check["correctness"], check["status"]) == (
        state.checks[0]["attempt_id"], 1, "answered")
    episode, = summary["episodes"]
    assert episode["recheck_attempt_id"] == check["attempt_id"] and episode["teacher_p"] == 0.7
    assert summary["landed"] == ["n1"] and fake.contexts[-1]["plan"] == state.plans[-1]["outline"]
    assert "Old explanation." in str(S.transcript(state))
    close = next(t for t in state.turns if t["action"] == "close")
    with repo.connection() as conn:
        live = store.receipt(conn, lesson)
        commitments = {r[0] for r in conn.execute("SELECT id FROM commitments")}
    assert commitments and set(close["refs"]["commitments"]) == commitments
    assert live["episodes"]["detour"] == [episode["id"]] and live["weight_inputs"][0]["attempt_id"] == check["attempt_id"]
    assert rebuild_receipt(case) == live
    assert len(fake.contexts) == 6


def rebuild_receipt(case):
    # Rebuild from the full ledger, including the independent delayed-check draw committed at close.
    vault, repo, lesson = case
    vault = load_vault(vault.root)
    state = S.load_state(repo, lesson)
    payload = next(t["payload"] for t in state.turns if t["action"] == "close")
    return S._receipt(vault, repo, state, reason=payload["reason"], recap=payload["recap"],
                      delayed_checks=payload["delayed_checks"], warnings=[],
                      landed=[{"id": n, "lo_id": state.node_lo(n)} for n in state.landed],
                      rows=state.checks, usage=S._lesson_tokens(state, S._Outcome()),
                      shown_items=delayed.shown_vault_items(vault, S.displayed_texts(state, extra=[payload["recap"]])),
                      closed_at=state.lesson["closed_at"])


def test_open_commitment_and_learner_refs_survive_repeat_compaction(tmp_path):
    def posed(context):
        turn = opening(context)
        turn["check"] = check_turn()["check"]
        return turn

    reminder = {"message": "Recent reminder. " * 100, "prediction": {"node": "n1", "prompt": "Which way?"}}
    fake = CountedTeacher([posed, reminder, {"message": "Keep thinking."}, {"message": "One more clue."}],
                          [(1000, 90), (1200, 100), (1300, 100), (900, 30)])
    case = open_case(tmp_path, 1500, fake)
    take(case, fake, text="Help me first.")
    take(case, fake, text="Give me a clue.")
    context = fake.contexts[-1]
    assert context["open_check"]["check"]["committed_solution"] == check_turn()["check"]["committed_solution"]
    assert context["open_prediction"]["prompt"] == "Which way?"
    assert context["help_reply"] and context["transcript"][0]["summary"]["version"]
    first_clue = context["transcript"][-1]
    take(case, fake, text="Another clue.")
    second_clue = fake.contexts[-1]["transcript"][-1]
    # The intervening message writes only its teacher turn, execution marker and usage row.
    assert int(second_clue["ref"][1:]) - int(first_clue["ref"][1:]) == 4
    assert (first_clue["ref"], second_clue["ref"]) == ("t12", "t16")
    assert [facts["replaced_entries"] for facts, _ in decisions(case[1])] == [1, 4]


@pytest.mark.parametrize("limit", [1500, None])
def test_last_turn_plan_in_receipt_matches_stored_versions(tmp_path, limit):
    def revise_and_close(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][1]["statement"] = "Compute a second eigenvalue."
        turn["requests"] += close_turn()["requests"]
        return turn

    fake = CountedTeacher([opening, {"message": "Continue."}, revise_and_close], [(1000, 90), (1200, 100), (900, 30)])
    case = open_case(tmp_path, limit, fake)
    take(case, fake)
    take(case, fake)
    _, repo, lesson = case
    with repo.connection() as conn:
        receipt = store.receipt(conn, lesson)
        assert receipt["plan_versions"] == store.plans(conn, lesson)
    assert receipt.get("summary_version") == (C.VERSION if limit else None)
    assert [p["version"] for p in receipt["plan_versions"]] == [1, 2]
    assert rebuild_receipt(case) == receipt


def test_growth_spread_and_cold_start_are_lesson_local(tmp_path):
    fake = CountedTeacher([opening, {"message": "More."}, {"message": "Again."}],
                          [(1000, 30), (1100, 50), (1300, 100)])
    vault, repo, lesson = open_case(tmp_path, 20_000, fake)
    take((vault, repo, lesson), fake)
    take((vault, repo, lesson), fake)

    def forecast(lesson_id):
        return C.forecast(repo, lesson_id, fake, prefix=0, estimated_input=420, output_budget=250,
                          estimate=lambda text: 420)

    learned = forecast(lesson)
    assert (learned["growth_samples"], learned["mean_need"], learned["uncertainty_tokens"],
            learned["predicted_tokens"]) == (2, 225, 75, 1600)
    other = CountedTeacher([opening], [(None, None)])
    second_id = S.open_lesson(vault, repo, entry="learning_object", learning_object_ids=["lo_eigen"],
                              clients=clients(other))["lesson_id"]
    cold = forecast(second_id)
    assert (cold["basis"], cold["growth_samples"], cold["predicted_tokens"]) == ("output_allowance", 0, 670)


def test_decision_write_failure_retries_before_any_compacted_send(tmp_path, monkeypatch):
    fake = CountedTeacher([opening, {"message": "Continue."}, close_turn()], [(1000, 90), (1200, 100), (900, 30)])
    case = open_case(tmp_path, 1500, fake)
    vault, repo, lesson = case
    take(case, fake)
    with monkeypatch.context() as patch:
        patch.setattr(C.provenance, "write", lambda conn, record: None)
        with pytest.raises(S.LessonError):
            take(case, fake)
    assert len(fake.prompts) == 2 and decisions(repo) == []
    with repo.connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_call_receipts WHERE "
                            "json_extract(budget_json, '$.summary_version') IS NOT NULL").fetchone()[0] == 0
    # This retry has no outer receipt writer.
    S.take_turn(vault, repo, lesson_id=lesson, action="resume", payload={}, clients=clients(fake))
    assert len(fake.prompts) == 3
    [(_, detail)] = decisions(repo)
    with repo.connection() as conn:
        assert tuple(conn.execute("SELECT owner_kind, owner_id, status FROM model_call_receipts WHERE id=?",
                                  (detail,)).fetchone()) == ("lesson", lesson, "completed")
        assert conn.execute("SELECT input_tokens FROM model_call_receipts WHERE parent_call_id=?",
                            (detail,)).fetchone()[0] == 900


@pytest.mark.parametrize("nested", [False, True])
def test_compacted_correction_records_one_boundary(tmp_path, nested):
    from learnloop.ai.structured_contracts import RECOVERY_NOTE

    fake = CountedTeacher([opening, {"message": "Continue."}, {}, close_turn()],
                          [(1000, 90), (1200, 100), (900, 30), (920, 40)])
    case = open_case(tmp_path, 1500, fake)
    vault, repo, lesson = case
    take(case, fake)
    with record_model_calls(repo, owner_kind="sidecar_rpc", owner_id="closing"):
        with model_call(fake, purpose="outer_operation", wrapper=True) if nested else nullcontext():
            S.take_turn(vault, repo, lesson_id=lesson, action="reply", payload={"text": "Go on."}, clients=clients(fake))
    assert len(fake.prompts) == 4
    [(_, detail)] = decisions(repo)
    with repo.connection() as conn:
        roots = conn.execute("SELECT id, budget_json FROM model_call_receipts WHERE owner_id='closing' "
                             "AND purpose='teacher_turn' ORDER BY rowid").fetchall()
        assert store.receipt(conn, lesson)["summary_version"] == C.VERSION
    original, correction = [json.loads(r[1]) for r in roots]
    assert roots[0][0] == detail
    assert original["context_summary"] == fake.contexts[-1]["transcript"][0]["summary"]
    assert original["transcript_prefix"] == correction["transcript_prefix"] == 1
    assert original["summary_version"] == correction["summary_version"] == C.VERSION
    assert "context_summary" not in correction
    if not nested:
        assert RECOVERY_NOTE in correction
    stats = C.forecast(repo, lesson, fake, prefix=1, estimated_input=0, output_budget=0, estimate=lambda text: 0)
    assert (stats["growth_samples"], stats["input_baseline"]) == (2, 920)


def test_a_long_current_reply_after_short_measured_sends_is_forecast(tmp_path):
    """L42-R12: the current prompt is already rendered. A pasted reply that lifts it past the learned growth is
    counted before the output's allowance: the last send's measured input plus the estimated growth of its prompt
    since, so the forecast is never the previous send's input plus a short margin."""

    fake = CountedTeacher([opening, {"message": "More."}, {"message": "Again."}], [(1000, 30), (1100, 50)])
    vault, repo, lesson = open_case(tmp_path, 20_000, fake)
    take((vault, repo, lesson), fake)

    def estimate(text):
        return 600  # the last send's prompt, as the request gate would estimate it

    short = C.forecast(repo, lesson, fake, prefix=0, estimated_input=620, output_budget=250, estimate=estimate)
    assert (short["growth_samples"], short["predicted_tokens"]) == (1, 1100 + 150)
    long = C.forecast(repo, lesson, fake, prefix=0, estimated_input=5000, output_budget=250, estimate=estimate)
    # 1100 measured, 4400 estimated since, then the most this lesson's answers have needed (50 tokens).
    assert long["predicted_tokens"] == 1100 + 4400 + 50
    assert (long["current_input"], long["current_input_basis"], long["output_need"]) == (
        5500, "measured_plus_estimated_growth", 50)
