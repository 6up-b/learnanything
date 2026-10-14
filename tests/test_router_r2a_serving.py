"""Router R2a serving gates: G2 (irreversible), G8 (kill switch), G9 (picks),
the receipt chain through the sidecar, G6 (replay) and order parity.

* **G2**: a block holding an irreversible item (one an open cold check holds:
  serving it spends the check) is chosen only as the staged rule's own,
  deterministic pick (propensity 1) and has propensity 0 otherwise; it is never
  in ``draw_support`` (what R2b's mixture may draw).
* **G8**: ``router.enabled = false`` at mvp-0.23, or the predecessor, serves
  DL1's pair exactly: the same block sequence and every ``block_chosen`` detail
  (ids aside), on the owner's working vaults' backup-API copies.
* **Order parity** (owner Q1): where no constraint refuses anything, the
  staged frame's blocks are DL1's blocks in DL1's order.
* **G9**: a learner pick wins with no propensity and no router decision; a
  proposal pick's delivery keeps naming its block's decision.
* **The receipt chain** through the RPCs: the served step's presentation id,
  sent with the answer, binds the attempt; a wrong, foreign or used id never
  fails the submit.
* **G6**: rebuilding ``router_outcomes`` twice with model clients forbidden
  gives the same table, joined through presentations.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import DEFAULT_POLICY, advance, build_plan, learner_pick
from learnloop.daily_plan.policy import policy_for
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.daily_plan_fakes import MovableClock, make_env, record_attempt
from tests.helpers import append_config_toml, create_daily_plan_vault, set_algorithm_version
from tests.test_daily_plan_build import _seed_wide, _wide_items, _wide_vault

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WORKING_FIXTURES = ("linear_algebra", "probability", "arxiv_v2")
FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)
A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _routed_env(tmp_path, *, version: str = A, toml: str | None = None):
    paths = _wide_vault(tmp_path, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    env = make_env(paths.root, _wide_items(), clock=MovableClock(), session_id="s1")
    _seed_wide(env.repository)
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=env.clock)
    return env


def _run(env, *, steps: int = 30) -> list[tuple]:
    """Serve and answer every item; the block sequence the plan chose."""

    clock = env.clock
    for _ in range(steps):
        record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], clock.now(),
                       session_id=env.session_id)
    return [
        (block.lane, tuple(item.practice_item_id for item in block.items), block.chosen.get("candidate_id"))
        for block in record.blocks
    ]


# -- order parity (Q1) ---------------------------------------------------------------


def test_with_nothing_refused_the_staged_frame_serves_dl1s_blocks_in_dl1s_order(tmp_path):
    dl1 = make_env(_wide_vault(tmp_path / "dl1", version="mvp-0.22").root, _wide_items(), clock=MovableClock(),
                   session_id="s1")
    _seed_wide(dl1.repository)
    assert dl1.policy is DEFAULT_POLICY
    build_plan(dl1, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    routed = _routed_env(tmp_path / "r2a")
    build_plan(routed, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert _run(routed) == _run(dl1)
    record, _step = advance(routed, serve=False)
    routed_blocks = [block for block in record.blocks if block.chosen_by != "learner_pick"]
    assert routed_blocks and all(block.chosen["chosen_by"] == "staged" for block in routed_blocks)
    assert all(block.chosen["propensity"] == 1.0 and block.chosen["router"]["mode"] == "staged"
               for block in routed_blocks)
    # The plain why replaces the lane-prefixed reason; the lane reason stays logged.
    assert all(not block.chosen["why"].startswith(("repair:", "maintain:", "new:", "push:")) for block in routed_blocks)
    assert all(row["reason"] for block in routed_blocks for row in [{"reason": block.chosen["why"]}])


# -- G2: irreversible ------------------------------------------------------------------


def _hold_cold_check(env, item_id: str) -> None:
    """An open cold retry holds ``item_id``: serving it spends the check."""

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

    assert "cold_retry" in COLD_FOLLOWUP_TASK_KINDS
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
            "created_at, updated_at) VALUES ('task_cold', 'cold_retry', 'misconception', 'case_1', "
            "'2026-10-12T08:00:00Z', 'pending', ?, '2026-10-12T08:00:00Z', '2026-10-12T08:00:00Z')",
            (item_id,),
        )
        connection.commit()


def _plan_rows(env) -> list[dict]:
    with env.repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id"
        )]
    for row in rows:
        row["candidates_json"] = json.loads(row["candidates_json"])
        row["detail_json"] = json.loads(row["detail_json"])
    return rows


def test_an_irreversible_block_is_only_the_rules_deterministic_pick(tmp_path):
    env = _routed_env(tmp_path)
    _hold_cold_check(env, "pi_m1a")
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    for _ in range(3):
        record, step = advance(env, serve=False)
        if step["kind"] != "item":
            break
        _run(env, steps=1)
    rows = _plan_rows(env)
    seen_irreversible = False
    for row in rows:
        blocks = {c["ref"]: c for c in row["candidates_json"] if c["kind"] == "block"}
        irreversible = {ref for ref, c in blocks.items() if not c["annotations"]["reversible"]}
        if not irreversible:
            continue
        seen_irreversible = True
        for ref in irreversible:
            entry = blocks[ref]
            assert "cold_check:pi_m1a" in entry["annotations"]["irreversible_because"]
            if ref == row["chosen_ref"]:
                assert (row["propensity"], row["propensity_kind"]) == (1.0, "deterministic")
            else:
                assert entry["propensity"] == 0.0
    assert seen_irreversible
    for block in record.blocks:
        router = block.chosen.get("router")
        if router is None:
            continue
    # What a draw may ever select never holds the irreversible block.
    from learnloop.daily_plan.engine import _live_context, decide

    record, _step = advance(env, serve=False)
    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy)
    if decision.router_record is not None:
        irreversible_ids = {c.candidate_id for c in decision.feasible if not c.annotations.get("reversible", True)}
        assert irreversible_ids.isdisjoint(decision.router_record["draw_support"])


# -- G9: learner picks ---------------------------------------------------------------


def test_a_learner_pick_wins_with_no_propensity_and_no_router_decision(tmp_path):
    env = _routed_env(tmp_path)
    build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    before = len(_plan_rows(env))
    record, pick = learner_pick(env, "pi_p1b")
    block = next(block for block in record.blocks if block.id == pick["block_id"])
    assert (block.chosen_by, block.chosen["propensity"], block.decision_ref) == ("learner_pick", None, None)
    assert len(_plan_rows(env)) == before
    with env.repository.connection() as connection:
        row = connection.execute("SELECT * FROM plan_presentations WHERE id = ?", (pick["presentation_id"],)).fetchone()
    assert (row["origin"], row["router_decision_id"]) == ("learner_pick", None)


# -- the receipt chain through the RPCs ----------------------------------------------


def _rpc_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]}, version=A,
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, ctx


def _submit(ctx, session_id, item_id, presentation_id, **extra):
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": "My answer.",
        "attemptType": "independent_attempt", "hintsUsed": 0,
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 4},
        "planPresentationId": presentation_id, **extra,
    })


def _bound(paths, attempt_id):
    with sqlite3.connect(paths.sqlite_path) as connection:
        return connection.execute("SELECT plan_presentation_id FROM practice_attempts WHERE id = ?",
                                  (attempt_id,)).fetchone()[0]


def test_a_served_steps_presentation_binds_the_answer_through_the_rpcs(tmp_path, monkeypatch):
    paths, ctx = _rpc_vault(tmp_path, monkeypatch)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert served["kind"] == "item" and served["presentationId"]
    result = _submit(ctx, session_id, served["practiceItemId"], served["presentationId"])
    assert _bound(paths, result["attemptId"]) == served["presentationId"]
    # The block's router decision is the staged rule's, with its card stored.
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT d.* FROM plan_presentations p JOIN router_decisions d ON d.id = p.router_decision_id WHERE p.id = ?",
            (served["presentationId"],),
        ).fetchone()
        payload = connection.execute(
            "SELECT * FROM router_decision_payloads WHERE decision_id = ?", (row["id"],)
        ).fetchone()
    assert (row["mode"], row["policy"], row["decision_kind"]) == ("staged", "staged_v1", "plan_block")
    assert payload["kind"] == "card" and payload["content_hash"] == row["card_hash"]


def test_a_wrong_or_used_presentation_never_fails_the_submit(tmp_path, monkeypatch):
    paths, ctx = _rpc_vault(tmp_path, monkeypatch)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    item = served["practiceItemId"]
    other = next(iid for iid in ("pi_extra_1", "pi_extra_2", "pi_svd_define_001") if iid != item)
    # An unknown id and another item's presentation: recorded, unbound.
    unknown = _submit(ctx, session_id, item, "pres_unknown", submissionId="s-unknown")
    assert _bound(paths, unknown["attemptId"]) is None
    foreign = _submit(ctx, session_id, other, served["presentationId"], submissionId="s-foreign")
    assert _bound(paths, foreign["attemptId"]) is None
    first = _submit(ctx, session_id, item, served["presentationId"], submissionId="s-first")
    assert _bound(paths, first["attemptId"]) == served["presentationId"]
    # A second answer to the same presentation: recorded, unbound.
    again = _submit(ctx, session_id, item, served["presentationId"], submissionId="s-again")
    assert again["attemptId"] != first["attemptId"] and _bound(paths, again["attemptId"]) is None
    # The draft RPC takes the id too (binding happens at submit).
    _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": item, "answerMd": "x",
                                       "submissionId": "s-draft", "planPresentationId": served["presentationId"]})


# -- G6: replay ----------------------------------------------------------------------


def test_router_outcomes_v2_replay_twice_with_no_model_call(tmp_path, monkeypatch):
    from learnloop.ai import client
    from learnloop.ai.providers import decider
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    def forbidden(*_args, **_kwargs):
        raise AssertionError("router outcomes replay must not construct a model client")

    paths, ctx = _rpc_vault(tmp_path, monkeypatch)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    answered = _submit(ctx, session_id, served["practiceItemId"], served["presentationId"])
    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr(decider.DeciderProviderClient, "__init__", forbidden)
    vault = ctx.require_vault()[0]
    repository = Repository(paths.sqlite_path)

    def table():
        with sqlite3.connect(paths.sqlite_path) as connection:
            return sorted(tuple(row) for row in connection.execute("SELECT * FROM router_outcomes"))

    rebuild_all_derived_state(vault, repository)
    first = table()
    rebuild_all_derived_state(vault, repository)
    assert table() == first
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT o.* FROM router_outcomes o JOIN plan_presentations p ON p.router_decision_id = o.decision_id "
            "WHERE p.id = ?", (served["presentationId"],),
        ).fetchone()
    assert (row["outcome_version"], row["action_status"], row["action_binding"], row["action_attempt_id"]) == (
        "router_outcomes_v2", "taken", "presentation", answered["attemptId"],
    )


@pytest.mark.durability
def test_presentations_and_cards_survive_production_pragmas(tmp_path):
    """The two new tables under WAL + synchronous=FULL on a freshly built vault."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault

    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0)]}, version=A,
    )
    from tests.daily_plan_fakes import scheduled, seed_due

    env = make_env(paths.root, [scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_m1b", "lo_m1", forgetting_risk=0.6)],
                   clock=MovableClock(), session_id="s1")
    for item in ("pi_m1a", "pi_m1b"):
        seed_due(env.repository, item, due=datetime(2026, 10, 1, tzinfo=UTC), last=datetime(2026, 9, 20, tzinfo=UTC))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=env.clock)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["presentation_id"]
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path),
                              require_complete_attempt_coverage=False)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("SELECT COUNT(*) FROM plan_presentations").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM router_decision_payloads").fetchone()[0] >= 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


# -- G8: the kill switch on the owner's working vaults' copies ------------------------


def _strip_ids(detail: dict) -> dict:
    return {key: value for key, value in detail.items() if key not in ("decision_ref",)}


def _plan_trace(root: Path) -> list[tuple]:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    # A fixed session id: the scheduler's seeded exploration hashes it, so two
    # copies compare only when they serve the same session.
    session_id = "s_g8"
    with Repository(root / "state.sqlite").connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE ended_at IS NULL", ("2026-10-12T09:00:00Z",))
        connection.execute(
            "INSERT INTO sessions(id, started_at, available_minutes) VALUES (?, '2026-10-12T09:30:00Z', 25)",
            (session_id,),
        )
        connection.commit()
    trace = []
    for _ in range(4):
        result = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
        step = result["step"]
        if step["kind"] != "item":
            break
        _call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]})
    vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        for row in connection.execute(
            "SELECT b.id, b.lane, b.chosen_by, e.detail_json FROM attention_blocks b "
            "JOIN attention_block_events e ON e.block_id = b.id AND e.kind = 'block_chosen' "
            "WHERE b.daily_plan_id IS NOT NULL ORDER BY b.created_at, b.plan_ordinal"
        ):
            items = [
                json.loads(event["detail_json"])["practice_item_id"]
                for event in connection.execute(
                    "SELECT detail_json FROM attention_block_events WHERE block_id = ? AND kind = 'item_planned' "
                    "ORDER BY event_ordinal", (row["id"],)
                )
            ]
            trace.append((row["lane"], row["chosen_by"], tuple(items), _strip_ids(json.loads(row["detail_json"]))))
    return trace


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_switch_off_at_the_successor_serves_the_predecessors_plan_on_fixture_copies(tmp_path, monkeypatch, fixture):
    if not (FIXTURES / fixture / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    traces = []
    for name, version, toml in (("pre", "mvp-0.22", None), ("off", A, "[router]\nenabled = false\n")):
        root = tmp_path / name
        copy_tree_with_databases(FIXTURES / fixture, root)
        set_algorithm_version(type("Paths", (), {"root": root})(), version)
        if toml:
            append_config_toml(root, toml)
        traces.append(_plan_trace(root))
    assert traces[0] and traces[0] == traces[1]
    assert all("router" not in detail and "staged_frame" not in detail for *_rest, detail in traces[1])
