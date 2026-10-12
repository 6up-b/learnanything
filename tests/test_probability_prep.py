"""Paid preparation for the llm_probability arms, with fake endpoints only.

A small real vault (the Slice 1 diagnosis vault: seven graded attempts over
four LOs, one later than the rest) drives the renderers, so the leakage rules
are checked on stored history, hypotheses and tutor questions.

Every attempt except the first gets the pre-grading timing the desktop app
records: a submission intent one minute before the graded attempt row (the
grader ran for that minute) and a five-minute presentation-to-submission
latency. The first attempt has none, so its start is unknown.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import replace
from datetime import timedelta
import hashlib
import json
from pathlib import Path

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.cli.field import _replay_inputs
from learnloop.cli.probability_arms import pairwise_comparisons, prepare_or_load_probability_arms
from learnloop.config.schema import DeciderProviderConfig, OpenRouterProviderConfig
from learnloop.db.connection import connect
from learnloop.field.evaluation import evaluate
from learnloop.field.probability_arms import parse_arm_selection, position_key
from learnloop.field.probability_prep import (
    JudgeRoute, LLM_PROMPT_VERSION, QUESTION_SET_VERSION, TASK, load_arms, prediction_points,
    prepare_judge, render_plan,
)
from learnloop.field.probability_states import CARD_TOKEN_BUDGET, StateRenderer, _fit, estimate_tokens
from learnloop.vault.loader import load_vault
from tests.decider_fakes import ScriptedDecider, fake_decisions
from tests.diagnosis_split_helpers import at, build_diagnosis_vault, seed_history
from tests.openai_fakes import install_fake_openai


GRADING = timedelta(seconds=60)
LATENCY = 300
COMPLETED = {
    "att_02_svd_fail": at(1), "att_03_svd_pass": at(2), "att_04_unrelated_fail": at(3),
    "att_05_eigen_fail": at(4), "att_06_svd_fail": at(5), "att_07_svd_future": at(10),
}


def iso(instant):
    return instant.isoformat().replace("+00:00", "Z")


def record_start(connection, attempt_id, *, intent_at, latency):
    """What the desktop app writes before grading: the intent, then the latency."""

    connection.execute("INSERT OR IGNORE INTO sessions(id, started_at) VALUES ('session-1', ?)", (iso(at(-1)),))
    item = connection.execute(
        "SELECT practice_item_id FROM practice_attempts WHERE id=?", (attempt_id,)).fetchone()[0]
    connection.execute(
        "INSERT INTO submission_intents(submission_id, session_id, practice_item_id, entry_surface, created_at) "
        "VALUES (?, 'session-1', ?, 'desktop_practice', ?)", (f"sub-{attempt_id}", item, iso(intent_at)))
    connection.execute("UPDATE practice_attempts SET submission_id=?, latency_seconds=? WHERE id=?",
                       (f"sub-{attempt_id}", latency, attempt_id))


def started(attempt_id, latency=LATENCY):
    """The cutoff the renderer must compute for an attempt seeded by the fixture."""

    return (COMPLETED[attempt_id] - GRADING - timedelta(seconds=latency + 2)).replace(microsecond=0)


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    paths = build_diagnosis_vault(tmp_path / "vault")
    seed_history(paths)
    with closing(connect(paths.sqlite_path)) as connection:
        for attempt_id, completed in COMPLETED.items():
            record_start(connection, attempt_id, intent_at=completed - GRADING, latency=LATENCY)
        connection.commit()
    loaded = load_vault(paths.root, load_environment=False)
    loaded.config.field.enabled = True
    loaded.config.field.llm_probability_enabled = True
    return loaded, paths


def replay(loaded):
    return _replay_inputs(loaded, legacy_fallback="current_content")


def incumbent(loaded, inputs):
    return {"config": loaded.config.mastery, "general_means": inputs["general_means"],
            "lo_priors": inputs["lo_priors"]}


def points_and_renderer(loaded, inputs, connection, rows=None):
    rows = inputs["attempts"] if rows is None else rows
    renderer = StateRenderer(loaded, connection, rows=rows)
    points = prediction_points((*rows, *inputs["signals"]), incumbent=incumbent(loaded, inputs),
                               start_of=renderer.cutoff)
    return points, renderer


def snapshot(paths):
    connection = connect(paths.sqlite_path, read_only=True)
    connection.execute("BEGIN")
    return closing(connection)


def by_attempt(points):
    return {point.row.attempt_id: point for point in points}


def test_prediction_points_are_exactly_the_harness_positions(seeded):
    loaded, _paths = seeded
    inputs = replay(loaded)
    points = prediction_points((*inputs["attempts"], *inputs["signals"]), incumbent=incumbent(loaded, inputs))
    seen = []

    class Spy:
        name, granularity, version_hash = "spy", "attempt", "spy"

        def __init__(self):
            self.history = []

        def predict(self, features):
            seen.append(position_key(features, self.history))
            return 0.5

        def observe(self, row):
            if hasattr(row, "attempt_id") and hasattr(row, "features"):
                self.history.append((row.attempt_id, row.outcome))

    evaluate((*inputs["attempts"], *inputs["signals"]), arms=[Spy()], bootstrap_samples=2)
    assert seen == [point.position_key for point in points]
    assert [p.row.attempt_id for p in points] == [
        "att_01_transpose_fail", "att_02_svd_fail", "att_03_svd_pass", "att_04_unrelated_fail",
        "att_05_eigen_fail", "att_06_svd_fail", "att_07_svd_future"]
    assert points[0].incumbent["p_success"] > 0 and points[0].history == ()


def test_states_are_past_only_and_never_show_the_answer_or_solution(seeded):
    loaded, paths = seeded
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        sixth = by_attempt(points)["att_06_svd_fail"]
        # The intent (written before grading) minus the latency and the
        # rounding margin; the graded row's own time never sets it.
        assert renderer.cutoff("att_06_svd_fail") == started("att_06_svd_fail")
        assert renderer.cutoff("att_01_transpose_fail") is None
        states = {variant: renderer.render(variant, sixth) for variant in ("v1", "v2", "v3")}
        everything = {variant: json.dumps(state, ensure_ascii=False) for variant, state in states.items()}
        for variant, text in everything.items():
            assert "Sigma V again" not in text, variant  # att_06's own answer
            assert "(future)" not in text, variant  # a later attempt
            # The item never carries its reference solution, rubric or hints
            # (att_03's earlier correct answer may legitimately match it).
            item = json.dumps(states[variant]["item"])
            assert "U Sigma V^T" not in item and "Think about it" not in item and "setup" not in item
        assert states["v1"]["item"]["stem"] == "Write the SVD of A."
        assert states["v1"]["item"]["learning_objective"] == "Compute an SVD"
        assert set(states["v1"]) == {"item"}
        window = states["v2"]["recent_interactions"]
        assert [entry["result"] for entry in window] == ["incorrect", "partial", "correct", "incorrect", "partial"]
        assert window[0]["knowledge_components"][0] == "Transpose a matrix"
        card = states["v3"]["learner_state"]
        relations = {entry["learning_objective"]: entry["relation"] for entry in card["scope"]}
        # The basic vault's own SVD LO shares the concept; confusable and
        # unrelated LOs stay out of V3's scope.
        assert relations == {"Compute an SVD": "target", "SVD definition": "same_concept",
                             "Transpose a matrix": "prerequisite"}
        answers = [entry["answer"] for entry in card["recent_work"]]
        assert answers == ["M stays M", "A = U Sigma V", "B = U Sigma V^T"]  # no unrelated or confusable LO
        assert card["incumbent_predictor"]["name"] == "mastery_ekf"
        statuses = {entry["learning_objective"]: entry["status"] for entry in card["status_by_learning_objective"]}
        assert statuses == {"Compute an SVD": "tested", "SVD definition": "untested",
                            "Transpose a matrix": "tested"}
        assert card["explicit_unknowns"] == ["never tested before this attempt: SVD definition"]
        # Hypotheses from att_02 (written at hour 1) show; att_06's own and
        # att_07's (written at or after the attempt) never do.
        assert card["open_hypotheses"]
        assert all("Sigma V again" not in json.dumps(h) and "future" not in json.dumps(h) for h in card["open_hypotheses"])
        # Every prior state of every point omits that point's own answer.
        for point in points:
            own = next(row for row in inputs["attempts"] if row.attempt_id == point.row.attempt_id)
            assert own.attempt_id not in json.dumps(renderer.render("v3", point))


def test_latency_sets_the_cutoff_and_questions_during_the_attempt_never_show(seeded):
    loaded, paths = seeded
    start = started("att_06_svd_fail", latency=600)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET latency_seconds=600 WHERE id='att_06_svd_fail'")
        rows = [
            ("q_before", "practice", "pi_svd_compute_001", None, "What is Sigma?", "clarification", start - timedelta(minutes=5)),
            ("q_during", "practice", "pi_svd_compute_001", None, "Is V transposed here?", "verification", start + timedelta(minutes=2)),
            ("q_linked", "practice", "pi_svd_compute_001", "att_06_svd_fail", "Linked to the attempt", "strategy", start - timedelta(minutes=1)),
            ("q_after", "feedback", "pi_svd_compute_001", None, "After grading", "mechanism", at(6)),
            ("q_other_lo", "practice", "pi_unrelated_001", None, "Is 1 prime?", "verification", start - timedelta(minutes=3)),
        ]
        for qid, context, item, attempt_id, text, qtype, when in rows:
            connection.execute(
                "INSERT INTO question_events (id, context, practice_item_id, attempt_id, question_md, answer_md, "
                "question_type, created_at) VALUES (?, ?, ?, ?, ?, 'answer', ?, ?)",
                (qid, context, item, attempt_id, text, qtype, when.isoformat().replace("+00:00", "Z")),
            )
        connection.commit()
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        assert renderer.cutoff("att_06_svd_fail") == start
        card = renderer.render("v3", by_attempt(points)["att_06_svd_fail"])["learner_state"]
    assert [q["question"] for q in card["tutor_questions"]] == ["What is Sigma?"]
    assert card["tutor_questions"][0]["type"] == "clarification"


def test_a_long_latency_moves_the_window_and_the_incumbent_back(seeded):
    loaded, paths = seeded
    with closing(connect(paths.sqlite_path)) as connection:
        # Started three and a half hours before submission: att_03 (an SVD
        # pass, hour 2), att_04 and att_05 completed after it began, so none
        # may appear or count.
        connection.execute("UPDATE practice_attempts SET latency_seconds=12600 WHERE id='att_06_svd_fail'")
        connection.commit()
    inputs = replay(loaded)

    def flipped(rows):
        # The forbidden observations' outcomes reversed (review F2's repro).
        return tuple(
            replace(row, outcome=1.0 - row.outcome)
            if row.attempt_id in {"att_03_svd_pass", "att_04_unrelated_fail", "att_05_eigen_fail"} else row
            for row in rows
        )

    with snapshot(paths) as connection:
        states = {}
        for label, rows in (("stored", inputs["attempts"]), ("flipped", flipped(inputs["attempts"]))):
            points, renderer = points_and_renderer(loaded, inputs, connection, rows=rows)
            sixth = by_attempt(points)["att_06_svd_fail"]
            states[label] = {variant: renderer.render(variant, sixth) for variant in ("v2", "v3")}
            if label == "stored":
                # The harness past (every row completed before att_06) would
                # have folded both forbidden rows: the test is sensitive.
                harness_past = prediction_points(
                    (*rows, *inputs["signals"]), incumbent=incumbent(loaded, inputs),
                    start_of=lambda attempt_id: renderer._attempts[attempt_id]["instant"],
                )
                leaky = by_attempt(harness_past)["att_06_svd_fail"].incumbent
                harness_flipped = prediction_points(
                    (*flipped(rows), *inputs["signals"]), incumbent=incumbent(loaded, inputs),
                    start_of=lambda attempt_id: renderer._attempts[attempt_id]["instant"],
                )
                assert by_attempt(harness_flipped)["att_06_svd_fail"].incumbent["p_success"] != leaky["p_success"]
    stored, reversed_ = states["stored"], states["flipped"]
    assert len(stored["v2"]["recent_interactions"]) == 2
    # Every predictor number and region status is fitted before the start, so
    # reversing what happened after it changes nothing in V3.
    assert stored["v3"] == reversed_["v3"] and stored["v2"] == reversed_["v2"]
    card = stored["v3"]["learner_state"]
    assert card["incumbent_predictor"]["observations_before_start"] == 2
    assert [entry["answer"] for entry in card["recent_work"]] == ["M stays M", "A = U Sigma V"]


def test_grading_time_never_moves_the_cutoff_and_an_unknown_start_withholds_history(seeded):
    """Review F1: opened 13:54, submitted 13:59, graded until 14:00."""

    loaded, paths = seeded
    start = COMPLETED["att_06_svd_fail"] - GRADING - timedelta(seconds=LATENCY)
    with closing(connect(paths.sqlite_path)) as connection:
        for qid, when in (("q_before", start - timedelta(seconds=30)), ("q_during", start + timedelta(seconds=30))):
            # Unlinked: only time keeps the second one out.
            connection.execute(
                "INSERT INTO question_events (id, context, practice_item_id, attempt_id, question_md, answer_md, "
                "question_type, created_at) VALUES (?, 'practice', 'pi_svd_compute_001', NULL, ?, 'answer', "
                "'clarification', ?)", (qid, f"asked {qid}", iso(when)))
        connection.commit()
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        # created_at - latency would be 13:55, after the question asked at 13:54:30.
        assert renderer.cutoff("att_06_svd_fail") < start
        card = renderer.render("v3", by_attempt(points)["att_06_svd_fail"])["learner_state"]
    assert [q["question"] for q in card["tutor_questions"]] == ["asked q_before"]
    # No intent, so a logged latency alone cannot place the start.
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET submission_id=NULL WHERE id='att_06_svd_fail'")
        connection.commit()
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        assert renderer.cutoff("att_06_svd_fail") is None
        sixth = by_attempt(points)["att_06_svd_fail"]
        v2, v3 = renderer.render("v2", sixth), renderer.render("v3", sixth)["learner_state"]
    assert v2["recent_interactions"] == [] and "start time was not recorded" in v2["history_withheld"]
    assert "start time was not recorded" in v3["history_withheld"]
    assert v3["recent_work"] == v3["open_hypotheses"] == v3["tutor_questions"] == []
    # The incumbent folds nothing: its numbers are the frozen priors alone.
    assert v3["incumbent_predictor"]["observations_before_start"] == 0
    assert all(entry["status"] == "untested" for entry in v3["status_by_learning_objective"])


def test_v3_budget_drops_successes_then_excerpts_then_attempts_never_typed_fields():
    def card(n):
        return {
            "scope": [], "incumbent_predictor": {"name": "mastery_ekf", "p_success": 0.5},
            "status_by_learning_objective": [{"learning_objective": "LO", "status": "tested"}],
            "explicit_unknowns": ["never tested before this attempt: X"],
            "recent_work": [
                {"answer": "a" * 400, "item": "i" * 200, "blind_grade": {"score": 1}, "_success": i % 2 == 0, "n": i}
                for i in range(n)
            ],
            "open_hypotheses": [{"statement": "h"}], "tutor_questions": [{"question": "q" * 200}],
            "omitted": {"older_successes": 0, "text_excerpts": 0, "older_attempts": 0, "tutor_questions": 0},
        }

    roomy = _fit(card(6))
    assert len(roomy["recent_work"]) == 6 and all("_success" not in e for e in roomy["recent_work"])
    full_size = estimate_tokens(roomy)
    trimmed = _fit(card(6), budget=full_size - 50)
    assert trimmed["omitted"]["older_successes"] >= 1
    assert all(entry["n"] % 2 for entry in trimmed["recent_work"][:1])  # oldest success went first
    starved = _fit(card(6), budget=1)
    assert starved["recent_work"] == [] and starved["tutor_questions"] == []
    assert starved["incumbent_predictor"] == {"name": "mastery_ekf", "p_success": 0.5}
    assert starved["status_by_learning_objective"] and starved["explicit_unknowns"]
    assert starved["omitted"]["older_successes"] == 3 and starved["omitted"]["older_attempts"] == 3
    assert CARD_TOKEN_BUDGET == 16_000


def routes_with(decider_client=None, llm_client=None, *, subscription=False, price=None):
    return {
        "decider": JudgeRoute(
            judge="decider", provider="fake_decider", model="fake/decider", settings={"model": "fake/decider"},
            price_per_million=0.02, client_factory=(lambda: decider_client) if decider_client else None,
        ),
        "llm": JudgeRoute(
            judge="llm", provider="fake_llm", model="fake/llm", settings={"model": "fake/llm"},
            subscription=subscription, price_per_million=price, output_tokens=64,
            client_factory=(lambda: llm_client) if llm_client else None,
        ),
    }


def test_dry_run_and_caps_refuse_before_any_client_call_or_write(seeded, tmp_path):
    loaded, paths = seeded
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()

    def forbidden():
        raise AssertionError("no client in a dry run")

    routes = routes_with()
    routes["decider"].client_factory = forbidden
    routes["llm"].client_factory = forbidden
    arms, report = prepare_or_load_probability_arms(
        loaded, replay(loaded), cache_dir=tmp_path / "cache", selection=parse_arm_selection(["all"]),
        prepare=True, dry_run=True, caps=SpendCaps(max_candidates=100, max_calls=100, max_total_tokens=10**7),
        price_per_million=1.0, output_tokens=64, routes=routes,
    )
    assert arms == [] and report["status"] == "over_budget"  # the metered LLM has no price
    assert report["judges"]["decider"]["status"] == "dry_run"
    assert report["judges"]["decider"]["estimate"]["calls"] == report["judges"]["decider"]["pending"]
    assert report["judges"]["decider"]["estimate"]["estimated_usd"] > 0
    assert report["judges"]["llm"]["reason"].startswith("Unknown price")
    assert not (tmp_path / "cache").exists()
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    capped = routes_with()
    capped["decider"].client_factory = forbidden
    _arms, report = prepare_or_load_probability_arms(
        loaded, replay(loaded), cache_dir=tmp_path / "cache", selection=parse_arm_selection(["decider"]),
        prepare=True, caps=SpendCaps(max_calls=3), price_per_million=None, output_tokens=64, routes=capped,
    )
    assert report["judges"]["decider"]["status"] == "over_budget"
    assert report["judges"]["decider"]["charged"]["calls"] == 0
    assert "max_candidates" in report["judges"]["decider"]["reason"] or "max_calls" in report["judges"]["decider"]["reason"]


def test_switches_and_cache_location_are_enforced(seeded, tmp_path):
    loaded, paths = seeded
    loaded.config.field.llm_probability_enabled = False
    arms, report = prepare_or_load_probability_arms(
        loaded, {}, cache_dir=tmp_path / "cache", selection=parse_arm_selection(["all"]),
        caps=SpendCaps(), price_per_million=None, output_tokens=64, routes=routes_with(),
    )
    assert arms == [] and report["status"] == "disabled"
    loaded.config.field.llm_probability_enabled = True
    with pytest.raises(ValueError, match="outside the vault"):
        prepare_or_load_probability_arms(
            loaded, replay(loaded), cache_dir=paths.root / "cache", selection=parse_arm_selection(["v1"]),
            caps=SpendCaps(), price_per_million=None, output_tokens=64, routes=routes_with(),
        )


def test_decider_end_to_end_through_the_fake_endpoint(seeded, tmp_path, monkeypatch):
    loaded, paths = seeded
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    caps = SpendCaps(max_candidates=100, max_calls=100, max_total_tokens=10**7, max_estimated_usd=1.0)
    with fake_decisions(dialect="openrouter", p_yes=0.64) as server:
        loaded.config.ai.providers["openrouter_decider"] = DeciderProviderConfig(
            base_url=server.base_url, model="perplexity/pplx-decider-v1.1-27b")
        arms, report = prepare_or_load_probability_arms(
            loaded, replay(loaded), cache_dir=tmp_path / "cache", selection=parse_arm_selection(["decider"]),
            prepare=True, caps=caps, price_per_million=None, output_tokens=64,
        )
    assert report["status"] == "complete", report
    judge = report["judges"]["decider"]
    # V1 repeats an identical state for repeated items, so 21 positions need fewer requests.
    assert judge["completed"] == judge["pending"] == len(server.requests) < 21
    assert set(judge["resolved_models"]) == {"perplexity/pplx-decider-v1.1-27b-20261006"}
    assert judge["charged"]["calls"] == len(server.requests)
    for request in server.requests:
        assert set(request["body"]) == {"model", "state", "questions"}
        assert set(request["body"]["questions"]) == {"will_pass"}
        assert request["body"]["questions"]["will_pass"]["type"] == "noul"
    assert len(arms) == 6 and {arm.model for arm in arms} == {"perplexity/pplx-decider-v1.1-27b-20261006"}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        judgments = connection.execute(
            "SELECT judge, judge_model, prompt_version, score FROM judgment_ledger WHERE task=?", (TASK,)).fetchall()
        receipts = connection.execute(
            "SELECT judge, question_set_version, state_hash, purpose, cost FROM model_call_receipts WHERE owner_kind=?",
            (TASK,)).fetchall()
    assert len(judgments) == len(server.requests)
    assert {tuple(row[:3]) for row in judgments} == {
        ("decider", "perplexity/pplx-decider-v1.1-27b-20261006", QUESTION_SET_VERSION)}
    assert {row[3] for row in judgments} == {0.64}
    assert len(receipts) == len(server.requests)
    assert all(row[0] == "decider" and row[1] == QUESTION_SET_VERSION and row[2] and row[4] for row in receipts)
    # Replay: cache only, zero calls, a byte-identical database.
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    monkeypatch.delenv("OPENROUTER_API_KEY")
    cached, report = prepare_or_load_probability_arms(
        loaded, replay(loaded), cache_dir=tmp_path / "cache", selection=parse_arm_selection(["decider"]),
        caps=caps, price_per_million=None, output_tokens=64,
    )
    assert report["status"] == "complete" and len(cached) == 6
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    inputs = replay(loaded)
    evaluation = evaluate(
        (*inputs["attempts"], *inputs["signals"]), arms=["mastery_ekf", *cached], bootstrap_samples=20,
        pairwise=pairwise_comparisons(parse_arm_selection(["decider"])),
    )
    assert {"llm_probability/v3/decider", "llm_probability/v3/decider+recal"} <= set(evaluation["report1"]["arms"])
    assert "llm_probability/v3/decider vs llm_probability/v2/decider" in evaluation["report1"]["pairwise"]
    assert evaluation["recommendation"]["candidates"] == []


def test_llm_judge_metered_route_is_isolated_bounded_and_ledgered(seeded, tmp_path, monkeypatch):
    loaded, paths = seeded
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    responses = [json.dumps({"p_correct": 0.55})] * 40
    fake = install_fake_openai(monkeypatch, *responses,
                               usages=[{"prompt_tokens": 500, "completion_tokens": 9}] * 40)
    loaded.config.ai.providers["or_chat"] = OpenRouterProviderConfig(
        model="vendor/frontier", api_key_env="OPENROUTER_API_KEY", response_format="json_schema")
    loaded.config.ai.routing.llm_probability_llm = "or_chat"
    caps = SpendCaps(max_candidates=100, max_calls=100, max_total_tokens=10**8, max_estimated_usd=5.0)
    arms, report = prepare_or_load_probability_arms(
        loaded, replay(loaded), cache_dir=tmp_path / "cache", selection=parse_arm_selection(["v1/llm", "v3/llm"]),
        prepare=True, caps=caps, price_per_million=1.0, output_tokens=64,
    )
    assert report["status"] == "complete", report
    judge = report["judges"]["llm"]
    assert judge["billing"] == "metered" and judge["physical_request_bound"] is True
    client = fake.instances[0]
    assert len(client.requests) == judge["completed"] == judge["charged"]["calls"]
    prompt = client.requests[0]["messages"][-1]["content"]
    assert "Will the learner answer this item correctly on this attempt?" in prompt
    assert LLM_PROMPT_VERSION in prompt
    assert len(arms) == 4 and {arm.model for arm in arms} == {"vendor/frontier"}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        judges = {row[0] for row in connection.execute(
            "SELECT judge FROM judgment_ledger WHERE task=?", (TASK,))}
        labels = {tuple(row) for row in connection.execute(
            "SELECT judge, question_set_version FROM model_call_receipts WHERE owner_kind=? AND parent_call_id IS NULL",
            (TASK,))}
    assert judges == {"llm"} and labels == {("llm", LLM_PROMPT_VERSION)}


class SubscriptionFake:
    """A Codex-like transport: subscription billing, no physical-request bound."""

    provider_name = "codex"
    provider_type = "codex_sdk"
    model = "gpt-codex-fake"

    def __init__(self, values):
        self.values = list(values)
        self.requests = []

    def supports(self, capability):
        from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION

        return capability in {STRUCTURED_COMPLETION, ISOLATED_TURN}

    def complete(self, request):
        from learnloop.ai.execution import model_call, report_call_usage

        self.requests.append(request)
        with model_call(self, purpose=f"{request.purpose}:sdk_turn", prompt=request.prompt):
            report_call_usage({"input_tokens": 1000, "output_tokens": 10})
            value = self.values.pop(0)
            return request.result_model.model_validate({"p_correct": value})


def test_subscription_llm_estimates_cost_ledgers_invalid_verdicts_and_resumes(seeded, tmp_path):
    loaded, paths = seeded
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        plan = render_plan(points, ("v1",), renderer)
    requests = plan.for_variant("v1")
    fake = SubscriptionFake([1.7] + [0.4] * (len(requests) - 1))
    from learnloop.db.repositories import Repository

    route = routes_with(llm_client=fake, subscription=True)["llm"]
    report = prepare_judge(plan, route=route, variants=["v1"], cache_dir=tmp_path / "cache",
                           repository=Repository(paths.sqlite_path),
                           caps=SpendCaps(max_calls=len(requests), max_total_tokens=1, max_estimated_usd=0))
    # Token and dollar caps are not enforced on the subscription; calls are.
    assert report["billing"] == "subscription" and report["cost_basis"] == "estimated_only"
    assert report["invalid"] == 1 and report["status"] == "incomplete"
    assert all(request.isolated for request in fake.requests)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        scores = sorted(row[0] is None for row in connection.execute(
            "SELECT score FROM judgment_ledger WHERE task=?", (TASK,)))
        usage = [json.loads(row[0]) for row in connection.execute(
            "SELECT usage_json FROM model_call_receipts WHERE owner_kind=? AND usage_json IS NOT NULL", (TASK,))]
    assert scores.count(True) == 1  # the invalid verdict is ledgered with no score
    assert usage and all(entry["cost_basis"] == "estimated_only" for entry in usage)
    _arms, missing = load_arms(plan, cache_dir=tmp_path / "cache", routes={"llm": route},
                               selection=[("v1", "llm")])
    assert missing["missing"] == {"v1/llm": 1}
    # A rerun pays only for the one missing prediction.
    fake.values = [0.3]
    again = prepare_judge(plan, route=route, variants=["v1"], cache_dir=tmp_path / "cache",
                          repository=Repository(paths.sqlite_path), caps=SpendCaps(max_calls=1))
    assert again["pending"] == 1 and again["completed"] == 1 and again["status"] == "complete"


def test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed(seeded, tmp_path, monkeypatch):
    loaded, paths = seeded
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        plan = render_plan(points[:2], ("v1",), renderer)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = {"n": 0}

    def flaky(body):
        calls["n"] += 1
        if calls["n"] == 1:
            return 429, {"error": {"message": "slow", "type": "rate_limit"}}, {"Retry-After": "0"}
        return None

    from learnloop.ai.providers.decider import DeciderProviderClient
    from learnloop.db.repositories import Repository

    sleeps = []
    with fake_decisions(respond=flaky) as server:
        client = DeciderProviderClient("d", DeciderProviderConfig(base_url=server.base_url))
        route = routes_with(decider_client=client)["decider"]
        report = prepare_judge(plan, route=route, variants=["v1"], cache_dir=tmp_path / "cache",
                               repository=Repository(paths.sqlite_path), caps=SpendCaps(max_retries=1),
                               sleep=sleeps.append)
    assert report["status"] == "complete" and report["retries"] == 1 and sleeps == [0.0]
    assert report["charged"]["retries"] == 1
    with fake_decisions(respond=lambda body: (200, {"model": "m", "answers": {}, "usage": {
            "input_tokens": 1, "output_tokens": 1}}, {})) as server:
        client = DeciderProviderClient("d", DeciderProviderConfig(base_url=server.base_url))
        route = routes_with(decider_client=client)["decider"]
        route.settings = {"model": "other"}  # a fresh cache identity
        report = prepare_judge(plan, route=route, variants=["v1"], cache_dir=tmp_path / "cache",
                               repository=Repository(paths.sqlite_path), caps=SpendCaps(max_retries=2))
    assert report["status"] == "provider_failed" and report["error_type"] == "DecisionResponseInvalid"
    assert report["retries"] == 0 and len(server.requests) == 1


def test_scripted_decider_sees_identical_states_for_both_judges(seeded, tmp_path):
    loaded, paths = seeded
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        plan = render_plan(points, ("v2",), renderer)
    from learnloop.db.repositories import Repository

    decider = ScriptedDecider(0.5)
    llm = SubscriptionFake([0.5] * 10)
    routes = routes_with(decider_client=decider, llm_client=llm, subscription=True)
    for judge in ("decider", "llm"):
        prepare_judge(plan, route=routes[judge], variants=["v2"], cache_dir=tmp_path / "cache",
                      repository=Repository(paths.sqlite_path), caps=SpendCaps())
    assert len(decider.states) == len(llm.requests) == len(plan.for_variant("v2"))
    for state, request in zip(decider.states, llm.requests):
        assert json.dumps(state, sort_keys=True, ensure_ascii=False) in request.prompt or json.dumps(
            state, sort_keys=True, ensure_ascii=False)[1:-1] in request.prompt


def test_harness_routes_follow_the_vault_config_not_the_env_override(seeded, monkeypatch):
    from learnloop.cli.probability_arms import resolve_route

    loaded, _paths = seeded
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "deepseek_pro")
    llm = resolve_route(loaded, "llm", price_per_million=None, output_tokens=64)
    assert (llm.provider, llm.subscription) == ("codex", True)
    decider = resolve_route(loaded, "decider", price_per_million=None, output_tokens=64)
    assert decider.provider == "openrouter_decider" and decider.price_per_million == 0.02
    loaded.config.ai.routing.llm_probability_llm = "openrouter_decider"
    with pytest.raises(ValueError, match="decision-model profile"):
        resolve_route(loaded, "llm", price_per_million=None, output_tokens=64)
    loaded.config.ai.routing.llm_probability_llm = "deepseek_flash"
    metered = resolve_route(loaded, "llm", price_per_million=1.0, output_tokens=64)
    assert metered.subscription is False and metered.settings["provider_type"] == "openai_chat"
    loaded.config.ai.routing.llm_probability_decider = "codex"
    with pytest.raises(ValueError, match="requires a decider profile"):
        resolve_route(loaded, "decider", price_per_million=None, output_tokens=64)


def pin_exact_revision(paths, loaded, attempt_id, item_id):
    """The receipts that make the harness treat an attempt as ``exact``:
    a selection snapshot of the item and the contract its grade cites."""

    from learnloop.db.repositories import Repository
    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    item = loaded.practice_items[item_id]
    contract_id = snapshot_for_presentation(Repository(paths.sqlite_path), loaded, item)
    raw = json.dumps(item.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    candidate = f"candidate-{attempt_id}"
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT OR IGNORE INTO practice_item_snapshots VALUES (?,?,?,?)",
                           (digest, item_id, raw, iso(at(-1))))
        connection.execute(
            "INSERT INTO decision_features(id,decision_id,decision_type,ability_vector_json,item_demand_vector_json,"
            "algorithm_version,created_at) VALUES (?,?,'selection','{}',?,'test',?)",
            (candidate, candidate, json.dumps({"content_hash": digest}), iso(at(-1))))
        connection.execute("UPDATE practice_attempts SET scheduler_candidate_id=? WHERE id=?", (candidate, attempt_id))
        connection.execute("UPDATE grading_evidence SET assessment_contract_version_id=? WHERE attempt_id=?",
                           (contract_id, attempt_id))
        connection.commit()
    return digest


def test_history_renders_the_verified_revision_never_todays_edit(seeded):
    """Review F3: an exact earlier attempt keeps its graded stem and frozen rubric."""

    loaded, paths = seeded
    pin_exact_revision(paths, loaded, "att_01_transpose_fail", "pi_transpose_001")
    # Edited after the predicted attempt: a new stem and a second criterion.
    current = loaded.practice_items["pi_transpose_001"]
    authored = current.grading_rubric.model_dump(mode="json")
    rubric = type(current.grading_rubric).model_validate({
        **authored, "max_points": 8,
        "criteria": [*authored["criteria"], {**authored["criteria"][0], "id": "notation"}],
    })
    loaded.practice_items["pi_transpose_001"] = current.model_copy(
        update={"prompt": "FUTURE REPLACEMENT STEM", "grading_rubric": rubric})
    assert loaded.rubric_for_item(loaded.practice_items["pi_transpose_001"]).max_points == 8
    inputs = replay(loaded)
    rows = {row.attempt_id: row for row in inputs["attempts"]}
    assert rows["att_01_transpose_fail"].revision_status == "exact"
    assert rows["att_02_svd_fail"].revision_status == "reconstructed_current"
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        sixth = by_attempt(points)["att_06_svd_fail"]
        v2, v3 = renderer.render("v2", sixth), renderer.render("v3", sixth)["learner_state"]
    assert "FUTURE REPLACEMENT STEM" not in json.dumps([v2, v3])
    assert v2["recent_interactions"][0]["item"] == "Transpose the matrix M."
    first = v3["recent_work"][0]
    assert (first["item"], first["revision"]) == ("Transpose the matrix M.", "exact")
    # The frozen four-point rubric, not today's eight-point one.
    assert first["blind_grade"]["max_points"] == 4.0 and first["blind_grade"]["failed_criteria"] == ["correctness"]
    assert "revision_note" not in first
    later = v3["recent_work"][1]
    assert later["revision"] == "reconstructed_current" and "today's item text" in later["revision_note"]
    # Strict replay: an earlier attempt with no verified revision is omitted and
    # counted, never filled in from today's content.
    strict = tuple(replace(row, revision_status="excluded") if row.attempt_id == "att_02_svd_fail" else row
                   for row in inputs["attempts"])
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection, rows=strict)
        card = renderer.render("v3", by_attempt(points)["att_06_svd_fail"])["learner_state"]
        window = renderer.render("v2", by_attempt(points)["att_06_svd_fail"])["recent_interactions"]
    assert "A = U Sigma V" not in [entry["answer"] for entry in card["recent_work"]]
    assert card["omitted"]["unverified_revision"] == 1
    assert "Write the SVD of A." not in [entry["item"] for entry in window]


def test_rich_state_carries_hypothesis_evidence_and_help_timing_to_both_judges(seeded, tmp_path):
    """Review F5: evidence for and against, source attempts, as-of status, hint timing."""

    loaded, paths = seeded
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET hints_used=1 WHERE id='att_03_svd_pass'")
        connection.execute(
            "INSERT INTO question_events (id, context, practice_item_id, attempt_id, question_md, answer_md, "
            "question_type, seconds_into_attempt, hints_used_before, created_at) VALUES "
            "('q_help', 'practice', 'pi_svd_compute_002', 'att_03_svd_pass', 'Which factor is transposed?', "
            "'answer', 'strategy', 45, 1, ?)", (iso(at(2) - timedelta(minutes=4)),))
        error_event = connection.execute(
            "SELECT id FROM error_events WHERE attempt_id='att_02_svd_fail'").fetchone()[0]
        # A durable misconception resolved only after the predicted attempt.
        connection.execute(
            "INSERT INTO misconceptions (id, learning_object_id, statement, status, source_error_event_ids_json, "
            "created_at, updated_at) VALUES ('mc_1', 'lo_svd_compute', 'Transposes are optional.', 'resolved', ?, ?, ?)",
            (json.dumps([error_event]), iso(at(1) + timedelta(minutes=1)), iso(at(8))))
        connection.commit()
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        plan = render_plan(points, ("v3",), renderer)
        card = renderer.render("v3", by_attempt(points)["att_06_svd_fail"])["learner_state"]
    hypotheses = {entry["statement"]: entry for entry in card["open_hypotheses"]}
    svd = hypotheses["The learner treats V and V transpose as identical."]
    assert svd["source_attempt"] == {"ref": "w2", "days_before": svd["source_attempt"]["days_before"],
                                     "learning_objective": "Compute an SVD", "first_divergence": ["U Sigma V"]}
    assert [(e["ref"], e["kind"]) for e in svd["evidence_for"]] == [("w2", "diagnosed_from")]
    assert [(e["ref"], e["kind"]) for e in svd["evidence_against"]] == [("w3", "passed_later")]
    assert (svd["evidence_for_total"], svd["evidence_against_total"]) == (1, 1)
    assert "validated_evidence_count" not in svd
    # Today's status ("resolved", written after the start) is not shown as of then.
    assert hypotheses["Transposes are optional."]["status"] == "unknown_as_of_this_attempt"
    work = {entry["ref"]: entry for entry in card["recent_work"]}
    assert work["w3"]["hints_used"] == 1
    assert work["w3"]["tutor_questions_during"] == [
        {"seconds_into_attempt": 45, "hints_used_before": 1, "type": "strategy"}]
    assert [q.get("attempt_ref") for q in card["tutor_questions"]] == ["w3"]
    assert any("ordinary hints" in note for note in card["not_recorded"])
    # Both judges receive exactly this state.
    from learnloop.db.repositories import Repository

    decider = ScriptedDecider(0.5)
    llm = SubscriptionFake([0.5] * 10)
    routes = routes_with(decider_client=decider, llm_client=llm, subscription=True)
    for judge in ("decider", "llm"):
        prepare_judge(plan, route=routes[judge], variants=["v3"], cache_dir=tmp_path / "cache",
                      repository=Repository(paths.sqlite_path), caps=SpendCaps())
    sixth = plan.requests[plan.positions["v3"][by_attempt(points)["att_06_svd_fail"].position_key]].state
    assert sixth["learner_state"] == card
    text = json.dumps(sixth, sort_keys=True, ensure_ascii=False)
    assert sixth in decider.states
    assert any(text in request.prompt or text[1:-1] in request.prompt for request in llm.requests)
    # With the transition history, the status as of the start is known.
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO misconception_transition_events (id, misconception_id, from_status, to_status, at, source) "
            "VALUES ('t1', 'mc_1', NULL, 'active', ?, 'test'), ('t2', 'mc_1', 'active', 'resolved', ?, 'test')",
            (iso(at(1) + timedelta(minutes=1)), iso(at(8))))
        connection.commit()
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        card = renderer.render("v3", by_attempt(points)["att_06_svd_fail"])["learner_state"]
    statuses = {entry["statement"]: entry["status"] for entry in card["open_hypotheses"]}
    assert statuses["Transposes are optional."] == "durable_active"


def test_resume_recovers_a_committed_verdict_instead_of_paying_again(seeded, tmp_path, monkeypatch):
    """Review F4: each persistence boundary of one paid prediction."""

    from learnloop.db.repositories import Repository
    from learnloop.field import probability_prep

    loaded, paths = seeded
    inputs = replay(loaded)
    with snapshot(paths) as connection:
        points, renderer = points_and_renderer(loaded, inputs, connection)
        plan = render_plan(points[:3], ("v2",), renderer)
    requests = plan.for_variant("v2")
    assert len(requests) == 3
    decider = ScriptedDecider(0.42)
    route = routes_with(decider_client=decider)["decider"]

    def run():
        return prepare_judge(plan, route=route, variants=["v2"], cache_dir=tmp_path / "cache",
                             repository=Repository(paths.sqlite_path), caps=SpendCaps())

    def judgments():
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            return connection.execute("SELECT left_id FROM judgment_ledger WHERE task=?", (TASK,)).fetchall()

    # 1. Stopped after the verdict committed, before the checkpoint landed.
    real_write = probability_prep._write_checkpoint
    calls = {"n": 0}

    def interrupted_write(path, checkpoint):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        real_write(path, checkpoint)

    monkeypatch.setattr(probability_prep, "_write_checkpoint", interrupted_write)
    first = run()
    assert first["status"] == "cancelled" and len(decider.states) == 1 and len(judgments()) == 1
    # A dry run sees it as recoverable, not as work to pay for.
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        committed = probability_prep.committed_judgments(connection)
    dry = prepare_judge(plan, route=route, variants=["v2"], cache_dir=tmp_path / "cache",
                        repository=None, caps=SpendCaps(), dry_run=True, committed=committed)
    assert dry["recoverable"] == 1 and dry["pending"] == 2 and dry["estimate"]["calls"] == 2
    second = run()
    assert second["status"] == "complete" and second["recovered"] == 1 and second["completed"] == 2
    # Three requests, three calls, three verdicts: nothing was paid twice.
    assert len(decider.states) == 3 and len(judgments()) == 3
    arms, report = load_arms(plan, cache_dir=tmp_path / "cache", routes={"decider": route},
                             selection=[("v2", "decider")])
    assert report["missing"] == {} and {round(p, 2) for p in arms[0]._probabilities.values()} == {0.42}
    recovered = [json.loads(path.read_text()) for path in (tmp_path / "cache").rglob("*.json")]
    assert sum(entry.get("recovered_from") == "judgment_ledger" for entry in recovered) == 1
    # 2. Stopped before the verdict committed: the answer was never durable,
    # so that one request is asked again (and only that one).
    monkeypatch.setattr(probability_prep, "_write_checkpoint", real_write)
    route.settings = {"model": "fake/decider", "fresh": True}  # a fresh cache identity
    real_append = probability_prep.append_judgment
    appends = {"n": 0}

    def interrupted_append(*args, **kwargs):
        appends["n"] += 1
        if appends["n"] == 1:
            raise KeyboardInterrupt
        return real_append(*args, **kwargs)

    monkeypatch.setattr(probability_prep, "append_judgment", interrupted_append)
    before = len(decider.states)
    assert run()["status"] == "cancelled" and len(decider.states) == before + 1
    again = run()
    assert again["status"] == "complete" and again["recovered"] == 0 and again["completed"] == 3
    assert len(decider.states) == before + 4
    # 3. A finished checkpoint: zero calls.
    assert run()["pending"] == 0 and len(decider.states) == before + 4
