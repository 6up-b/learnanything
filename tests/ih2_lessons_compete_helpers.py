"""What other test files use from ``tests/test_ih2_lessons_compete.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import ast
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.stores import followup_serve as store
from learnloop.followup_run import jobs, router
from learnloop.followup_serve import workflow as wf
from learnloop.router_objective import mix

from tests.daily_plan_fakes import record_attempt, scheduled
from tests.followup_serve_helpers import AuthorFake
from tests.router_mixture_helpers import mixture_env, rows
from tests.router_model_fakes import fake_runtime
from tests.daily_plan_build_helpers import _wide_items
from tests.te3b_offers_helpers import OFFER


TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
QUIET = "[router_objective]\nstop_coin = 0.0\n"
OFF = "[router_objective]\nstop_coin = 0.0\nlessons_compete_with_followups = false\n"
#: No day's check block in the way: these tests need an ordinary block with questions left.
NO_CHECKS = '[router_objective]\nstop_coin = 0.0\ncheck_rate = "off"\n'
OFF_NO_CHECKS = NO_CHECKS + "lessons_compete_with_followups = false\n"
FOLLOWUP_ITEM = "pi_diag_mid"


@pytest.fixture
def draw(monkeypatch):
    """Which ref the mix serves: the first of ``draw.prefer`` in the support (its probability the exact ``μ``, so G3 still
    holds); the uniforms are not reproduced, which no test here reads. Nothing named: the real draw."""

    real = mix.draw
    control = SimpleNamespace(prefer=(), never_stop=False, avoid=())

    def fake(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        for ref in control.prefer:
            match = next((option for option in support if str(option).startswith(ref)), None)
            if match is not None:
                return replace(drawn, chosen=match, propensity=drawn.pi[match])
        avoid = (*(("stop_for_today",) if control.never_stop else ()), *control.avoid)
        if str(drawn.chosen).startswith(avoid):
            other = next(ref for ref in support if not str(ref).startswith(avoid))
            return replace(drawn, chosen=other, propensity=drawn.pi[other])
        return drawn

    monkeypatch.setattr(mix, "draw", fake)
    return control


def _env(tmp_path, *, version: str = TAG, toml: str = QUIET, session_id: str = "s1", items: Any = None):
    return mixture_env(tmp_path, fake_runtime(), version=version, toml=toml, items=items, session_id=session_id)


def _objective_rows(env, kind: str = "plan_block") -> list[dict[str, Any]]:
    return [row for row in rows(env, kind) if row["policy"] == mix.POLICY]


def _open_offer(env, draw) -> dict[str, Any]:
    """Serve and answer until the feedback prefetch draws the objective's first boundary: the offer, open and unanswered
    (the Nov 8 trace's 12:37 pm draw)."""

    draw.prefer = (OFFER,)
    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=False)
        if _objective_rows(env):
            assert step["kind"] == "lesson_offer"
            return step
    raise AssertionError("the objective never decided a boundary")


def _ready_probe(env, *, item: str | None = None, held: int = 1, decision: str | None = None,
                 chosen: str | None = None) -> dict[str, Any]:
    """A real workflow whose generated probe became ready while the offer waits (the workflow path)."""

    record = E.latest_today(env)
    planned = {entry.practice_item_id for entry in record.items()}
    probe = item or sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    lo = str(env.vault.practice_items[probe].learning_object_id)
    record_attempt(env.repository, probe, lo, env.clock.now(), session_id=env.session_id)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_test", "source_attempt_id": attempt_id, "revision_key": "joint", "learning_object_id": lo,
            "session_id": env.session_id, "surface": "desktop", "origin": "practice", "feedback_held": held,
            "created_at": env.now_iso(),
        })
    wf.move(env.repository, "fw_test", to_state=wf.READY, reason="test", practice_item_id=probe, decision_id=decision,
            chosen_ref=chosen, factor_id="f", clock=env.clock)
    return wf.get(env.repository, "fw_test")


def _need_path_env(tmp_path, *, version: str = TAG, toml: str = QUIET):
    """The need path: a generated item the scheduler flags as a follow-up after the plan was built (Nov 8's probe)."""

    live = list(_wide_items())
    env = _env(tmp_path, version=version, toml=toml, items=lambda: list(live))
    return env, live


def _need_probe_arrives(live: list[Any]) -> str:
    live.insert(0, scheduled(FOLLOWUP_ITEM, "lo_diag", followup_kind="negative_surprise_followup"))
    return FOLLOWUP_ITEM


def _assert_exact_mu(row: dict[str, Any]) -> dict[str, float]:
    """G3: the logged mixture recomputes to the logged per-candidate probabilities, and the row's propensity is the
    chosen ref's."""

    mixture = row["detail_json"]["mixture"]
    mu = mix.recompute(mixture)
    assert abs(sum(mu.values()) - 1.0) < 1e-9
    logged = {entry["ref"]: entry["propensity"] for entry in row["candidates_json"] if entry["ref"] in mu}
    assert set(logged) == set(mu)
    for ref, value in mu.items():
        assert logged[ref] == pytest.approx(value, abs=1e-12), ref
    assert row["propensity"] == pytest.approx(mu[row["chosen_ref"]], abs=1e-12)
    return mu


def _answer(env, *, questions_left: bool = True) -> dict[str, Any]:
    """Build the plan, then serve and answer a question, with no lesson available and no stop drawn on the way (the draws
    are live, and what comes after is what the test is about). ``questions_left``: until an answer leaves questions in
    its block, since a block may hold one."""

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(SG, "build_candidates", lambda vault, repository, *, now_iso: ([], {}))
        real = mix.draw

        def never_stop(support, parts, weights, epsilon, seed):
            drawn = real(support, parts, weights, epsilon, seed)
            if drawn.chosen != "stop_for_today":
                return drawn
            other = next(ref for ref in support if ref != "stop_for_today")
            return replace(drawn, chosen=other, propensity=drawn.pi[other])

        patch.setattr(mix, "draw", never_stop)
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        for _ in range(12):
            _record, step = advance(env, serve=True)
            assert step is not None and step["kind"] == "item"
            env.clock.advance(1)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
            env.clock.advance(1)
            # Reconciled, as the next step would: an answer can take a question out of its block (a check that waits).
            record = E.reconcile(env, E.latest_today(env))
            block = next(b for b in record.blocks if b.id == step["block_id"])
            if not questions_left or any(item.practice_item_id != step["practice_item_id"] and not item.resolved
                                         for item in block.items):
                return step
    raise AssertionError("no block held a second question")


def _miss_env(tmp_path, *, version: str = TAG, toml: str = NO_CHECKS, questions_left: bool = False):
    env = mixture_env(tmp_path, fake_runtime(), version=version, toml=toml, items=lambda: list(_wide_items()))
    step = _answer(env, questions_left=questions_left)
    with env.repository.connection() as connection:
        attempt_id = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
    with env.repository.atomic(), env.repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": "fw_miss", "source_attempt_id": attempt_id, "revision_key": "joint",
            "learning_object_id": step["learning_object_id"], "session_id": env.session_id, "surface": "desktop",
            "origin": "practice", "feedback_held": 1, "created_at": env.now_iso(),
        })
    return env, wf.get(env.repository, "fw_miss")


def _author_refuses(monkeypatch) -> None:
    """The author is reached (the decision came first, and the lesson lost) and its question is refused: the arm's own
    path ends there, with nothing of the workflow's probe machinery needed."""

    from learnloop.followup_run import admission

    def refuse(*_a, **_k):
        raise admission.OfferRefused("author_reached")

    monkeypatch.setattr(admission, "author_probe", refuse)


def _run_lane(env, row, monkeypatch, author: Any = None) -> AuthorFake:
    """The generation slot's decision and whatever follows it, on the standing plan."""

    author = author or AuthorFake()
    monkeypatch.setattr(router, "hard_refusal", lambda *_a, **_k: None)
    monkeypatch.setattr(router, "_card_facts", lambda *_a, **_k: [])
    monkeypatch.setattr(router, "observational", lambda *_a, **_k: {})
    monkeypatch.setattr(jobs.identity, "retire_unbound", lambda *_a, **_k: None)

    def context(*_a, **_k):
        from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

        restraint = env.policy.restraint
        record = E.get_or_create_today(env, create=False)
        gate = ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                     card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                     may_defer=False)
        return env, record, gate

    monkeypatch.setattr(router, "_plan_context", context)
    clients = SimpleNamespace(author=author, authoring=None, runtime=env.policy.restraint.runtime)
    choice = SimpleNamespace(factor_id="f", hypothesis_ids=())
    jobs._run_probe_lane(env.vault, env.repository, row, choice=choice, clients=clients, clock=env.clock)
    return author


EVIDENCE_WORDS = ("stuck", "correctness", "miss_count", "misses", "n_misses", "score_on_attempt", "last_score")


def _names_in(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            found.add(node.attr.lower())
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 40:
            found.add(node.value.lower())
    return found
