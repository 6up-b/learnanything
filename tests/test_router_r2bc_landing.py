"""Router R2b + R2c landing onto main (docs/reviews/router-r2bc.md, "Landing onto main").

Main gained RW3a (the Reader's "check me"), the tutor delivery fixes and
GLM-OCR after the branch's base. The compositions checked here:

* **RW3a's "check me" under the mixture.** At mvp-0.24 Today's blocks are
  drawn from the model mixture and a read may leave the next block's decision
  open. "Check me" still goes through ``plan_learner_pick``: the pick logs
  exactly one router decision (the learner's own, no propensity) or none (a
  planned item is served by its block's mixture decision; a closed plan's
  open-list pick has none), and its answer binds by the pick's own
  presentation; with today's first block still being chosen it is the same.
* **Teach-back summaries and the delivery fixes.** The summarizer reads the
  whole dialogue (no 240- or 600-character cut); only the model's own summary
  points are kept short for the card's budget.
* **Spend.** R2c's query embeddings and the delivery fixes' automatic
  source-block backfill share the embedding route. Each is admitted by its own
  guard (the router's daily guard; the backfill's per-run caps), neither
  counts the other's receipts, and neither is held by the other's guard.
"""

from __future__ import annotations

import re
import sqlite3
import threading

import pytest

from learnloop.algorithm_versions import ROUTER_MIXTURE_ALGORITHM_VERSION
from learnloop.daily_plan import router_runtime
from learnloop.daily_plan import router_teach_back as tb
from learnloop.daily_plan.policy import policy_for
from learnloop.daily_plan.router_runtime import GUARDED_OWNERS, RouterSpend, receipt_usd
from learnloop.db.connection import connect
from learnloop.db.stores.source_service import interventions
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.practice_index_fakes import EMBED_DIMS, HashingEmbedder
from tests.router_mixture_helpers import B, mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, first_option, seed_with_first_uniform
from tests.split_live_helpers import enable_embeddings
from tests.test_daily_plan_build import _wide_items
from tests.test_reader_rw3a_landing import CASES, _call, _check_me, _counts, _picked, _world
from tests.test_source_vector_backfill import SECOND, _backfill_jobs, _Extractor, _import, _runner

assert B == ROUTER_MIXTURE_ALGORITHM_VERSION == "mvp-0.24"

#: The Decider takes the whole draw and puts its mass on the staged rule's
#: pick (the options lead with it), so the mixture's first block is the one
#: R2a's world plans, drawn and logged by the mixture with an exact propensity.
DECIDER_DRAWS = "[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n"


def _mixture_world(tmp_path, monkeypatch, runtime):
    monkeypatch.setattr(router_runtime, "_DEFAULT", runtime)
    paths, ctx = _world(tmp_path, monkeypatch, version=B)
    with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write("\n" + DECIDER_DRAWS)
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, ctx


def _decision(paths, decision_id):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()
    return None if row is None else dict(row)


def _presentation(paths, presentation_id):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM plan_presentations WHERE id = ?", (presentation_id,)).fetchone())


def _no_repeated_receipts(paths) -> bool:
    with sqlite3.connect(paths.sqlite_path) as connection:
        return connection.execute(
            "SELECT receipt_key FROM router_decisions GROUP BY receipt_key HAVING COUNT(*) > 1"
        ).fetchall() == []


def _answer_binds_by_presentation(paths, ctx, session_id, check, step):
    submitted = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": check["practiceItemId"], "answerMd": "My answer.",
        "attemptType": "independent_attempt", "hintsUsed": 0,
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 4},
        "schedulerCandidateId": step.get("schedulerCandidateId"),
        "planPresentationId": step["presentationId"],
    })
    with connect(paths.sqlite_path, read_only=True) as connection:
        bound = connection.execute("SELECT plan_presentation_id FROM practice_attempts WHERE id = ?",
                                   (submitted["attemptId"],)).fetchone()[0]
        outcomes = {row["decision_id"]: row for row in derive_router_outcomes(connection)}
    assert bound == step["presentationId"]
    return submitted["attemptId"], outcomes


# -- RW3a's "check me" under the mixture ------------------------------------------------------


@pytest.mark.parametrize("case", sorted(CASES))
def test_check_me_under_the_mixture_is_logged_once_and_binds_to_its_presentation(tmp_path, monkeypatch, case):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option), llm=FakeLLM(),
                           seed=seed_with_first_uniform(at_least=0.2))
    paths, ctx = _mixture_world(tmp_path, monkeypatch, runtime)
    session_id, check, result, before = _picked(ctx, paths, CASES[case])
    step = result["step"]
    assert step["kind"] == "item" and step["practiceItemId"] == check["practiceItemId"] and step["presentationId"]
    after = _counts(paths)
    assert after["plan_presentations"] - before["plan_presentations"] == 1
    presentation = _presentation(paths, step["presentationId"])
    decision = _decision(paths, presentation["router_decision_id"])
    with connect(paths.sqlite_path, read_only=True) as connection:
        [delivery] = interventions(connection)
    assert presentation["practice_item_id"] == check["practiceItemId"] and _no_repeated_receipts(paths)
    # The mixture decided Today's blocks (the Decider drew, exactly, wherever
    # there was a choice; a single option is decided by the rule and logged so).
    blocks = [row for row in _rows(paths) if not row["learner_pick"]]
    assert blocks and all(row["mode"] == "mixture" for row in blocks)
    assert case == "open_list" or any(row["policy"] == "router_mixture_v1" for row in blocks)
    if case == "open_list":
        assert presentation["origin"] == "open_list" and decision is None
        assert after["router_decisions"] == before["router_decisions"] and delivery["router_decision_id"] is None
        return
    assert decision["receipt_key"] == f"plan_block:{step['blockId']}"
    if case == "new_pick_block":
        # The learner's own block decision: logged once, no propensity, even under the mixture.
        assert presentation["origin"] == "learner_pick"
        assert (decision["learner_pick"], decision["propensity"], decision["propensity_kind"]) == (1, None, "none")
        assert after["router_decisions"] - before["router_decisions"] == 1
    else:
        # A planned item opened from the list is served by its block: the mixture's draw.
        assert after["router_decisions"] == before["router_decisions"]
        assert decision["learner_pick"] == 0 and presentation["origin"] != "learner_pick"
        assert decision["policy"] == "router_mixture_v1" and decision["propensity_kind"] == "exact"
        assert 0.0 < decision["propensity"] <= 1.0
    assert delivery["router_decision_id"] == decision["id"]
    assert result["proposalPick"]["routerDecisionId"] == decision["id"]
    attempt_id, outcomes = _answer_binds_by_presentation(paths, ctx, session_id, check, step)
    outcome = outcomes[decision["id"]]
    assert (outcome["action_status"], outcome["action_attempt_id"], outcome["action_binding"]) == (
        "taken", attempt_id, "presentation",
    )


def _rows(paths):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id")]


def test_check_me_while_todays_first_block_is_still_being_chosen(tmp_path, monkeypatch):
    """A read leaves the mixture's first decision open (the models are still
    out). "Check me" then is the learner's own one-item block: one decision,
    one presentation, its answer bound by it; the mixture decides the next
    block separately once a serving step finds the models answered."""

    gate = threading.Event()
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, gate=gate), llm=FakeLLM(gate=gate),
                           inline=False, seed=seed_with_first_uniform(at_least=0.2))
    paths, ctx = _mixture_world(tmp_path, monkeypatch, runtime)
    try:
        session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
        view = _call(ctx, "get_daily_plan", {"sessionId": session_id})
        assert view["plan"]["deciding"] is True and view["plan"]["blocks"] == []
        before = _counts(paths)
        check = _check_me(ctx)
        assert _counts(paths) == before
        result = _call(ctx, "plan_learner_pick", {"practiceItemId": check["practiceItemId"], "sessionId": session_id,
                                                  "proposalId": check["proposalId"]})
        step = result["step"]
        assert step["kind"] == "item" and step["practiceItemId"] == check["practiceItemId"] and step["presentationId"]
        after = _counts(paths)
        assert (after["router_decisions"] - before["router_decisions"],
                after["plan_presentations"] - before["plan_presentations"]) == (1, 1)
        presentation = _presentation(paths, step["presentationId"])
        decision = _decision(paths, presentation["router_decision_id"])
        assert presentation["origin"] == "learner_pick"
        assert (decision["learner_pick"], decision["propensity"], decision["propensity_kind"]) == (1, None, "none")
        assert result["proposalPick"]["routerDecisionId"] == decision["id"]
        attempt_id, outcomes = _answer_binds_by_presentation(paths, ctx, session_id, check, step)
        assert (outcomes[decision["id"]]["action_attempt_id"], outcomes[decision["id"]]["action_binding"]) == (
            attempt_id, "presentation")
        # The models answer; the next serving step decides the mixture's block.
        gate.set()
        served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
        assert served["step"]["kind"] == "item" and served["plan"]["deciding"] is False
        drawn = [row for row in _rows(paths) if not row["learner_pick"]]
        assert drawn and drawn[0]["policy"] == "router_mixture_v1" and drawn[0]["id"] != decision["id"]
        assert served["step"]["presentationId"] != step["presentationId"]
        assert _decision(paths, decision["id"]) == decision and _no_repeated_receipts(paths)
    finally:
        gate.set()


# -- teach-back summaries: the whole dialogue ----------------------------------------------------


def test_the_teach_back_summarizer_reads_the_whole_dialogue(tmp_path):
    calls: list = []

    def answer(request):
        calls.append(request)
        return {"explained_correctly": ["x" * 400], "missing_or_wrong": [], "learner_words": []}

    runtime = fake_runtime(llm=FakeLLM(answer=answer))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    turns = "".join(
        f"## Follow-up {index}\n\n**Student asked:** Why does step {index} hold?\n\n"
        f"**Learner answered:** Because the {index}-th vector is a combination of the earlier ones, "
        "so removing it keeps the span the same and the remaining list stays independent.\n\n"
        for index in range(1, 40)
    )
    transcript = "# Teach-back transcript\n\n## Opening explanation\n\nA basis spans and is independent.\n\n" + turns
    transcript += "THE-LAST-WORDS-OF-THE-DIALOGUE"
    assert len(transcript) > 4 * 600
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, primed, latency_seconds, created_at, session_id, learner_answer_md) "
            "VALUES ('att_long', 'pi_m1a', 'lo_m1', 'teach_back', 'teach_back', 0.5, 0, 0, 300, "
            "'2026-10-11T09:00:00Z', 's0', ?)", (transcript,),
        )
        connection.commit()
    summary = tb.summarize(env.vault, env.repository, "att_long", runtime=runtime)
    (request,) = calls
    # No source-passage-style cut: the dialogue reaches the summarizer whole.
    assert transcript in request.prompt and "THE-LAST-WORDS-OF-THE-DIALOGUE" in request.prompt
    # Only the model's own summary points are kept short (the card's budget).
    assert len(summary["explained_correctly"][0]) == tb.POINT_LIMIT


# -- spend: the router's embeddings and the source backfill --------------------------------------


def _set_line(root, pattern: str, replacement: str) -> None:
    path = root / "learnloop.toml"
    text, count = re.subn(pattern, replacement, path.read_text(encoding="utf-8"), count=1, flags=re.M)
    assert count == 1, pattern
    path.write_text(text, encoding="utf-8")


def _receipts(repository, owners) -> list[dict]:
    return [row for row in repository.model_call_spend_rows(started_since="1970-01-01T00:00:00")
            if row.get("owner_kind") in owners]


def _purposes(repository, owner_kind: str) -> set[str]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return {row[0] for row in connection.execute(
            "SELECT DISTINCT purpose FROM model_call_receipts WHERE owner_kind = ?", (owner_kind,))}


def _reload(env):
    env.vault = load_vault(env.vault.root)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock,
                            runtime=env.policy.chooser.runtime, serve=True)


def _next_day(env) -> list[dict]:
    """A new day's plan, served and answered; returns its mixture decisions."""

    seen = {row["id"] for row in rows(env)}
    env.clock.advance(24 * 60)
    run(env)
    return [row for row in rows(env) if row["id"] not in seen and row["policy"] == "router_mixture_v1"]


def test_router_embeddings_and_the_source_backfill_each_answer_to_their_own_guard(tmp_path, monkeypatch):
    # Every receipt counts as "today" (the router's guard and the test both run
    # on the system clock, the plans on a movable one).
    monkeypatch.setattr(router_runtime, "_day_start", lambda _now: "1970-01-01T00:00:00")
    embedder = HashingEmbedder()  # one embedding model, as one route serves both in a vault
    env = mixture_env(
        tmp_path, fake_runtime(decider=FakeDecider(choice=first_option), llm=FakeLLM(), embedding=embedder,
                               seed=seed_with_first_uniform(at_least=0.2)),
        toml="[router]\nsimilar_include_rate = 1.0\nmax_daily_cost_usd = 5.0\n"
             "[router.weights]\nstaged = 0.5\ndecider = 0.5\nllm = 0.0\n",
    )
    root = env.vault.root
    enable_embeddings(root)
    _set_line(root, r"^dimensions = 4096$", f"dimensions = {EMBED_DIMS}")
    _reload(env)
    config = env.vault.config
    assert config.embedding.backfill_sources_on_extract and config.embedding.model == embedder.model_id

    # 1. Router decisions: each query embedding is a router receipt.
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions and all(
        row["detail_json"]["mixture"]["similar"]["status"] in {"included", "withheld"} for row in decisions)
    router_rows = _receipts(env.repository, GUARDED_OWNERS)
    assert _purposes(env.repository, "router_decision") >= {"embedding"}

    # 2. A source import on the same vault: its block backfill runs under its own caps.
    extractor = _Extractor()
    extractor.embedder = embedder
    runner = _runner(VaultPaths(env.vault.root, env.vault.config), extractor)
    calls_before = len(embedder.calls)
    _import(runner, str(tmp_path / "eigen.md"))
    [job] = _backfill_jobs(runner.repo)
    assert job["status"] == "completed" and job["result"]["status"] == "complete", job
    backfill_rows = _receipts(env.repository, {"embedding_backfill"})
    assert backfill_rows
    # Its run counted its own requests only (not the router's earlier ones).
    assert job["result"]["charged"]["calls"] == len(embedder.calls) - calls_before

    # No double count: the router's guard sums exactly its own receipts; the
    # backfill's receipts are priced, and not in it.
    spent = RouterSpend().spent_today(env.repository, config, "2026-10-14T12:00:00Z")
    assert spent == pytest.approx(sum(receipt_usd(config, row) for row in router_rows)) and spent > 0
    assert sum(receipt_usd(config, row) for row in backfill_rows) > 0
    assert {row["owner_kind"] for row in _receipts(env.repository, set(GUARDED_OWNERS) | {"embedding_backfill"})} == {
        "router_decision", "embedding_backfill"}

    # 3. The router's guard spent out: its own query embedding is refused (and
    # its models'), while a re-extraction's backfill still runs under its caps.
    _set_line(root, r"^max_daily_cost_usd = 5\.0$", f"max_daily_cost_usd = {spent:.10f}")
    _reload(env)
    refused = _next_day(env)
    assert refused and all(
        row["detail_json"]["mixture"]["similar"] == {"status": "unavailable", "reason": "spend", "rate": 1.0}
        for row in refused)
    assert RouterSpend().spent_today(env.repository, env.vault.config, "2026-10-15T12:00:00Z") == pytest.approx(spent)
    extractor.texts, extractor.version = SECOND, "2"
    _import(runner, str(tmp_path / "eigen.md"))
    assert [(job["status"], job["result"]["status"]) for job in _backfill_jobs(runner.repo)] == [
        ("completed", "complete")] * 2

    # 4. The backfill's cap spent out: a third extraction's backfill is held
    # over budget, while the router (its guard raised again) embeds as before.
    _set_line(root, r"^max_daily_cost_usd = [0-9.]+$", "max_daily_cost_usd = 5.0")
    _set_line(root, r"^backfill_enabled = true$", "backfill_enabled = true\nsource_backfill_max_cost_usd = 0.0")
    _reload(env)
    embedded = _next_day(env)
    assert embedded and all(
        row["detail_json"]["mixture"]["similar"]["status"] in {"included", "withheld"} for row in embedded)
    extractor.texts, extractor.version = ["A third reading of the eigenvalue chapter with yet another engine."], "3"
    _import(runner, str(tmp_path / "eigen.md"))
    jobs = sorted(_backfill_jobs(runner.repo), key=lambda job: job["id"])
    assert [(job["status"], (job["result"] or {}).get("status")) for job in jobs] == [
        ("completed", "complete"), ("completed", "complete"), ("failed", None)]
    assert jobs[2]["error"]["code"] == "over_budget" and jobs[2]["error"]["details"]["caps"]["max_estimated_usd"] == 0.0
