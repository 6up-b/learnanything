"""Router R2c: similar past decisions (``decision/context``), G5 and G6.

* **G5 (retrieval maturity)**: a past decision is shown only when its R_next
  or R_cold attempt was made before the current decision's time, in another
  session and another plan; outcomes are derived on the fly from the ledgers.
* **The inclusion coin** is logged, seeded by the boundary key, and withholds
  the similar decisions from the models on its other side.
* **Gating**: with ``embedding.enabled`` off it is a logged no-op.
* **G6**: replay never needs a vector: removing every vector leaves the
  outcome rebuild identical, and the ids shown stay on the decision row.
* **The backfill** (``learnloop router embed-decisions``) dry-runs first.
"""

from __future__ import annotations

import json
import sqlite3

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.daily_plan import router_retrieval as rr
from learnloop.db.connection import connect
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.db.stores.router import append_router_decision
from learnloop.router.outcomes import derive_router_outcomes

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeEmbedding, FakeLLM, fake_runtime
from tests.split_live_helpers import enable_embeddings


def _decision(connection, decision_id: str, *, session: str, plan: str, at: str, item: str, lo: str) -> None:
    assert append_router_decision(connection, {
        "id": decision_id, "receipt_key": f"plan_block:{decision_id}", "decision_kind": "plan_block",
        "surface": "daily_plan", "mode": "mixture", "policy": "router_mixture_v1", "algorithm_version": "mvp-0.24",
        "log_version": "router_decisions_v1", "session_id": session, "snapshot_hash": "h" + decision_id,
        "candidates_json": json.dumps([{"ref": "maintain:x", "kind": "block", "lane": "maintain", "feasible": True,
                                        "learning_object_ids": [lo], "propensity": 0.5}]),
        "exclusions_json": "{}", "candidate_count": 1, "chosen_ref": "maintain:x", "chosen_practice_item_id": item,
        "chosen_learning_object_id": lo, "propensity": 0.5, "propensity_kind": "exact", "learner_pick": 0,
        "detail_json": json.dumps({"plan_id": plan}), "created_at": at,
    })


def _attempt(connection, attempt_id: str, *, item: str, lo: str, at: str, session: str, correctness: float = 1.0):
    connection.execute(
        "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "correctness, hints_used, primed, latency_seconds, created_at, session_id, evidence_origin) "
        "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, 0, 0, 60, ?, ?, 'human')",
        (attempt_id, item, lo, correctness, at, session),
    )


def test_only_matured_decisions_from_another_session_and_plan_are_similar(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    now = "2026-10-14T09:00:00Z"
    with env.repository.atomic(), env.repository.connection() as connection:
        # A: another session, its R_next observed before now -> similar.
        _decision(connection, "dA", session="s_old", plan="p_old", at="2026-10-10T09:00:00Z", item="pi_m1a", lo="lo_m1")
        _attempt(connection, "aA1", item="pi_m1a", lo="lo_m1", at="2026-10-10T09:01:00Z", session="s_old")
        _attempt(connection, "aA2", item="pi_m1b", lo="lo_m1", at="2026-10-10T09:05:00Z", session="s_old")
        # B: another session, its R_next only after now -> not matured.
        _decision(connection, "dB", session="s_b", plan="p_b", at="2026-10-11T09:00:00Z", item="pi_r1a", lo="lo_r1")
        _attempt(connection, "aB1", item="pi_r1a", lo="lo_r1", at="2026-10-11T09:01:00Z", session="s_b")
        _attempt(connection, "aB2", item="pi_r1b", lo="lo_r1", at="2026-10-14T10:00:00Z", session="s_b2")
        # C: the current session -> excluded even though matured.
        _decision(connection, "dC", session="s_now", plan="p_c", at="2026-10-12T09:00:00Z", item="pi_p1a", lo="lo_p1")
        _attempt(connection, "aC1", item="pi_p1a", lo="lo_p1", at="2026-10-12T09:01:00Z", session="s_now")
        _attempt(connection, "aC2", item="pi_p1b", lo="lo_p1", at="2026-10-12T09:05:00Z", session="s_now")
        # D: the current plan -> excluded.
        _decision(connection, "dD", session="s_d", plan="p_now", at="2026-10-13T09:00:00Z", item="pi_m1b", lo="lo_m1")
        _attempt(connection, "aD1", item="pi_m1b", lo="lo_m1", at="2026-10-13T09:01:00Z", session="s_d")
        _attempt(connection, "aD2", item="pi_m1a", lo="lo_m1", at="2026-10-13T09:05:00Z", session="s_d")
        for index, decision_id in enumerate(("dA", "dB", "dC", "dD")):
            put_vector(connection, record_kind=rr.RECORD_KIND, record_id=decision_id, field=rr.FIELD,
                       content_hash=f"c{index}", model_id="fake-embed", task_prefix=rr.TASK_PREFIX,
                       vector=[1.0, 0.1 * index, 0.0, 0.5])
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        found = rr.similar_decisions(connection, query=[1.0, 0.0, 0.0, 0.5], model_id="fake-embed", decision_time=now,
                                     session_id="s_now", plan_id="p_now", limit=6, vault=env.vault)
    assert [entry["decision_id"] for entry in found] == ["dA"]
    # Its R_next (10-10) and its R_cold (D's answers on 10-13, a day later in
    # another session) both matured before now.
    assert found[0]["outcome"] == {"r_next": 1.0, "r_cold": 1.0}
    assert "Next answer on that topic: correct; a day or more later: correct" in found[0]["line"]
    # The same history, asked as of a time before A's outcome: nothing matured.
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        early = rr.similar_decisions(connection, query=[1.0, 0.0, 0.0, 0.5], model_id="fake-embed",
                                     decision_time="2026-10-10T09:03:00Z", session_id="s_now", plan_id="p_now",
                                     limit=6, vault=env.vault)
    assert early == []


def test_the_inclusion_coin_is_seeded_logged_and_honours_its_rate():
    u, included = rr.include_coin("key-1", 0.5)
    assert (u, included) == rr.include_coin("key-1", 0.5)
    assert rr.include_coin("key-1", 0.0)[1] is False and rr.include_coin("key-1", 1.0)[1] is True
    draws = [rr.include_coin(f"k{index}", 0.5)[1] for index in range(4000)]
    assert 0.45 < sum(draws) / len(draws) < 0.55


def test_without_embeddings_retrieval_is_a_logged_no_op(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(), embedding=FakeEmbedding()))
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions
    for row in decisions:
        assert row["detail_json"]["mixture"]["similar"] == {"status": "disabled"}
        assert row["similar_decision_ids_json"] is None
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM embedding_vectors").fetchone()[0] == 0


def _embedded_env(tmp_path, *, rate: float, llm=None, embedding=None, router: str = ""):
    from tests.router_model_fakes import first_option, seed_with_first_uniform

    env = mixture_env(
        tmp_path, fake_runtime(decider=FakeDecider(choice=first_option), llm=llm or FakeLLM(),
                               embedding=embedding or FakeEmbedding(), seed=seed_with_first_uniform(at_least=0.2)),
        toml=f"[router]\nsimilar_include_rate = {rate}\n{router}[router.weights]\nstaged = 0.5\ndecider = 0.5\n"
             "llm = 0.0\n",
    )
    enable_embeddings(env.vault.root)
    from learnloop.daily_plan.policy import policy_for
    from learnloop.vault.loader import load_vault

    env.vault = load_vault(env.vault.root)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock,
                            runtime=env.policy.chooser.runtime, serve=True)
    return env


def test_each_decision_embeds_its_context_after_the_decision_and_logs_the_coin(tmp_path):
    embedding = FakeEmbedding()
    llm = FakeLLM()
    env = _embedded_env(tmp_path, rate=1.0, llm=llm, embedding=embedding)
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions and embedding.calls
    with env.repository.connection() as connection:
        stored = {row[0] for row in connection.execute(
            "SELECT record_id FROM embedding_vectors WHERE record_kind = 'decision' AND field = 'context'")}
    assert {row["id"] for row in decisions} <= stored
    for row in decisions:
        similar = row["detail_json"]["mixture"]["similar"]
        assert similar["status"] == "included" and similar["rate"] == 1.0 and similar["included"] is True
        assert row["similar_decision_ids_json"] == similar["ids_shown"]
        assert "context_vector" not in similar
    withheld = _embedded_env(tmp_path / "w", rate=0.0)
    run(withheld)
    for row in [row for row in rows(withheld) if row["policy"] == "router_mixture_v1"]:
        similar = row["detail_json"]["mixture"]["similar"]
        assert similar["status"] == "withheld" and similar["ids_shown"] == [] and row["similar_decision_ids_json"] == []


def test_the_context_text_has_no_ids_or_times():
    card = {
        "session": {"plan_kind": "normal", "reentry": False, "minutes_left": 12, "days_since_last_activity": 0},
        "candidates": [{"kind": "maintain", "topics": ["Bases"], "reason_code": "review", "reversible": True}],
        "learning_objects": {"lo_m1": {"title": "Bases", "status": "learning", "predictor": {"p_success": 0.8},
                                       "recall_now": 0.9}},
        "open_hypotheses": [{"kind": "misconception", "topic": "Bases", "learning_object_id": "lo_m1"}],
        "decision": {"decided_at": "2026-10-14T09:00:00Z"},
    }
    text = rr.context_text(card)
    assert "2026" not in text and "lo_m1" not in text
    assert "topic Bases: learning" in text and "open problem: misconception on Bases" in text
    assert rr.content_hash(text) == rr.content_hash(rr.context_text(card))


def test_replay_never_needs_a_vector(tmp_path):
    env = _embedded_env(tmp_path, rate=1.0)
    run(env)

    def outcomes():
        with connect(env.repository.sqlite_path, read_only=True) as connection:
            return derive_router_outcomes(connection)

    before = outcomes()
    shown = [row["similar_decision_ids_json"] for row in rows(env)]
    with env.repository.connection() as connection:
        connection.execute("DELETE FROM embedding_vectors")
        connection.commit()
    assert outcomes() == before
    assert [row["similar_decision_ids_json"] for row in rows(env)] == shown


def test_the_query_embedding_is_admitted_by_the_daily_guard(tmp_path):
    # Codex review F3: the prefetch's query embedding is a metered request
    # like the models'. With no money left today it is refused before it is
    # sent, and retrieval is a logged "unavailable" (reason: spend).
    from learnloop.clock import utc_now_iso
    from learnloop.daily_plan.router_runtime import RouterSpend

    embedding = FakeEmbedding()
    env = _embedded_env(tmp_path, rate=1.0, embedding=embedding, router="max_daily_cost_usd = 0.0\n")
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions and embedding.calls == []
    for row in decisions:
        assert row["detail_json"]["mixture"]["similar"] == {"status": "unavailable", "reason": "spend", "rate": 1.0}
        assert row["detail_json"]["mixture"]["models"]["decider"]["status"] == "spend"
    assert RouterSpend().spent_today(env.repository, env.vault.config, utc_now_iso()) == 0.0


def test_the_backfill_dry_runs_and_then_embeds_what_is_missing(tmp_path, monkeypatch):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
    run(env)
    root = env.vault.root
    result = CliRunner().invoke(app, ["router", "embed-decisions", "--vault", str(root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["dry_run"] is True and report["pending"] == report["decisions"] > 0 and report["embedded"] == 0
    # Codex review F3: the dry run prices the work and names the caps it would run under.
    assert report["estimate"]["estimated_usd"] > 0 and report["caps"]["max_estimated_usd"] == 0.25
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM embedding_vectors").fetchone()[0] == 0
    # Off: nothing is sent.
    result = CliRunner().invoke(app, ["router", "embed-decisions", "--vault", str(root), "--json"])
    assert json.loads(result.output)["status"] == "disabled" and result.exit_code == 1
    # On, with a fake embedding client: every decision with a stored card gets its vector.
    from learnloop.ai.spend import SpendCaps
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    enable_embeddings(root)
    vault = load_vault(root)
    vault.config.embedding.model, vault.config.embedding.dimensions = "fake-embed", 8
    repository = Repository.attach(env.repository.sqlite_path)
    report = rr.backfill(vault, repository, caps=SpendCaps(max_candidates=1_000), dry_run=False,
                         price_per_million=0.01, client_factory=FakeEmbedding)
    assert report["status"] == "complete" and report["embedded"] == report["pending"] > 0
    again = rr.backfill(vault, repository, caps=SpendCaps(), dry_run=True, price_per_million=0.01)
    assert again["pending"] == 0
    with sqlite3.connect(env.repository.sqlite_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM embedding_vectors WHERE record_kind = 'decision'").fetchone()[0] == report["embedded"]
        owners = {row[0] for row in connection.execute("SELECT DISTINCT owner_kind FROM model_call_receipts "
                                                       "WHERE purpose = 'embedding'")}
    assert owners == {"embedding_backfill"}


def test_the_backfill_is_held_to_its_money_cap(tmp_path):
    # Codex review F3: the backfill runs under an enforced budget: a cap
    # below the priced estimate refuses the run before any request is sent.
    from learnloop.ai.spend import SpendCaps
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
    run(env)
    enable_embeddings(env.vault.root)
    vault = load_vault(env.vault.root)
    vault.config.embedding.model, vault.config.embedding.dimensions = "fake-embed", 8
    repository = Repository.attach(env.repository.sqlite_path)
    planned = rr.backfill(vault, repository, caps=SpendCaps(max_candidates=1_000), dry_run=True,
                          price_per_million=0.01)
    usd = planned["estimate"]["estimated_usd"]
    assert planned["status"] == "dry_run" and usd > 0
    embedding = FakeEmbedding()
    refused = rr.backfill(vault, repository, caps=SpendCaps(max_candidates=1_000, max_estimated_usd=usd / 2),
                          dry_run=False, price_per_million=0.01, client_factory=lambda: embedding)
    assert refused["status"] == "over_budget" and refused["embedded"] == 0 and embedding.calls == []


def _graded_run(env, *, steps: int = 30):
    from learnloop.daily_plan.engine import advance

    from tests.daily_plan_fakes import iso

    record = None
    for index in range(steps):
        record, step = advance(env, serve=True)
        if step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        with env.repository.connection() as connection:
            _attempt(connection, f"att_{env.session_id}_{index}", item=step["practice_item_id"],
                     lo=step["learning_object_id"], at=iso(env.clock.now()), session=env.session_id)
            connection.commit()
    return record


def test_a_matured_decision_from_an_earlier_day_is_shown_to_the_models(tmp_path):
    from learnloop.daily_plan.policy import policy_for

    llm = FakeLLM()
    env = _embedded_env(tmp_path, rate=1.0, llm=llm)
    _graded_run(env)
    day_one = {row["id"] for row in rows(env) if row["policy"] == "router_mixture_v1"}
    assert day_one
    # The next day, a new session and a new plan.
    env.clock.advance(24 * 60)
    env.session_id = "s2"
    env.policy = policy_for(env.vault, env.repository, session_id="s2", clock=env.clock,
                            runtime=env.policy.chooser.runtime, serve=True)
    _graded_run(env, steps=3)
    later = [row for row in rows(env) if row["policy"] == "router_mixture_v1" and row["id"] not in day_one]
    assert later
    shown = [row for row in later if row["similar_decision_ids_json"]]
    assert shown, [row["detail_json"]["mixture"]["similar"] for row in later]
    for row in shown:
        assert set(row["similar_decision_ids_json"]) <= day_one
    prompts = [request.prompt for request in llm.requests if "# Similar past decisions" in request.prompt]
    assert prompts and "Next answer on that topic:" in prompts[0]
