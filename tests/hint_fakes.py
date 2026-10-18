"""Builders and fake models for adaptive hints H2a's tests (no network).

``WriterFake`` is a ``StructuredClientFake`` answering the hint writer from a
queue of answers (dicts or callables of the prompt's context); with the queue
empty it writes a valid answer for the chosen kind on the CDF item
(:func:`good_answer`). ``ChooserFake`` is a decision client whose
``kind_level`` and ``horizon`` distributions are callables of the asked
options. Knobs: ``provider_type`` (``chatgpt_plan``: subscription, no price
needed; ``openrouter``: metered; ``codex_sdk``: refused by the writer), a
``delay`` (a slow Decider) and ``error``. Plumbing checks only, never evidence
about hint quality.
"""
from __future__ import annotations

import json
import time
from contextlib import closing
from pathlib import Path
import sqlite3
from typing import Any, Callable, Mapping

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult, ScoreAnswer
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.connection import connect
from learnloop.hints.writer import empty_output
from tests.approach_map_fakes import EXPECTED, HINTS, ITEM, LO, PROMPT, map_vault
from tests.structured_ai import StructuredClientFake, _request_context

__all__ = [
    "ChooserFake", "EXPECTED", "HINTS", "ITEM", "LO", "PROMPT", "WriterFake", "add_hypothesis", "assists",
    "good_answer", "hint_vault", "judgments", "receipts", "reveals", "store_map", "WORK",
]

#: A draft on the CDF item: its first line stands, its second is questionable.
WORK = "F(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) + 1"


def hint_vault(tmp_path: Path, *, config: str = "", name: str = "vault", **item: Any):
    """The CDF item's vault (the H1 builders), maps on but no build on serve."""

    base = "[hints.maps]\nbuild_on_serve = false\n"
    return map_vault(tmp_path, config=base + config, name=name, **item)


def _no_sources(*_args: Any, **_kwargs: Any) -> Any:
    from types import SimpleNamespace

    return SimpleNamespace(hits=[], manifest={}, status="ok", policy="test")


def store_map(paths: Any, payload: dict[str, Any] | None = None) -> str:
    """A map for the item's current revision, built and stored through H1's
    own builder with H1's fake model (so the service reads it with
    ``current_map``); ``payload`` replaces the default good map."""

    from learnloop.db.repositories import Repository
    from learnloop.hints import map_builder
    from learnloop.vault.loader import load_vault
    from tests.approach_map_fakes import MapFake

    fake = MapFake([payload] if payload is not None else None)
    outcome = map_builder.build_map(load_vault(paths.root), Repository.attach(paths.sqlite_path), ITEM,
                                    trigger="cli", client=fake, find=_no_sources)
    assert outcome.status == "built", outcome.as_dict()
    return str(outcome.map_id)


def add_hypothesis(sqlite_path: Path, hypothesis_id: str, statement: str, *, attempt_id: str = "att_h") -> None:
    """An open candidate hypothesis on the item's LO (a rival)."""

    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO causal_hypotheses (id, episode_key, version, attempt_id, learning_object_id, cause_scope, "
            "statement, statement_normalized, status, created_at) "
            "VALUES (?, ?, 1, ?, ?, 'learner_state', ?, ?, 'candidate', '2026-10-17T09:00:00Z')",
            (hypothesis_id, f"ep_{hypothesis_id}", attempt_id, LO, statement, statement.lower()))
        connection.commit()


def _rows(sqlite_path: Path, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def assists(sqlite_path: Path) -> list[dict[str, Any]]:
    return _rows(sqlite_path, "SELECT * FROM help_assists ORDER BY requested_at, rowid")


def judgments(sqlite_path: Path, task: str) -> list[dict[str, Any]]:
    return _rows(sqlite_path, "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, rowid", (task,))


def receipts(sqlite_path: Path, owner_kind: str) -> list[dict[str, Any]]:
    return _rows(sqlite_path, "SELECT * FROM model_call_receipts WHERE owner_kind = ? AND parent_call_id IS NULL "
                 "ORDER BY started_at, rowid", (owner_kind,))


def reveals(sqlite_path: Path) -> list[dict[str, Any]]:
    return _rows(sqlite_path, "SELECT * FROM reveal_events ORDER BY created_at, rowid")


def good_answer(context: Mapping[str, Any]) -> dict[str, Any]:
    """A valid writer answer for the chosen kind on the CDF item and map."""

    chosen = context["chosen"]
    kind, level = chosen["kind"], chosen["level"]
    work = context.get("learner_work") or ""
    has_work = bool(work.strip())
    lines = [line for line in work.splitlines() if line.strip()]
    stands = lines[0] if has_work else ""
    questionable = lines[1] if len(lines) > 1 else ""
    placement = {"route_id": "r_ref" if context.get("approach_map") else "",
                 "reached_node_id": ("cdf" if has_work else "g") if context.get("approach_map") else "",
                 "first_questionable_quote": questionable, "stands_quote": stands,
                 "quotes": [stands] if has_work else [], "work_matches_a_route": True, "work_valid_so_far": True}
    target = chosen.get("target_node_id") or ("goal" if placement["reached_node_id"] == "cdf" else "cdf")
    strategy = f"{kind}-{len(context.get('earlier_hints') or [])}"
    base = dict(placement=placement, route_id=placement["route_id"],
                target_node_id=target if context.get("approach_map") else "", strategy=strategy)
    if chosen.get("downgrade"):
        return empty_output(**base, hint_md="Check the step after your first line against the density.")
    if kind == "approach_question":
        return empty_output(**base, hint_md="What would your first move be?" if not has_work else
                            "What do you know about F at the right end of the support?", asks_about="first_move"
                            if not has_work else "goal")
    if kind == "localize":
        return empty_output(**base, hint_md=f"Look again at: {questionable}")
    if kind == "next_step":
        return empty_output(**base, hint_md="Evaluate your CDF at the point the question asks about.")
    if kind == "waypoint":
        return empty_output(**base, hint_md="Aim for the probability as a value of your CDF.")
    if kind == "subgoal_plan":
        return empty_output(**base, hint_md="Find the CDF on the support · Evaluate the CDF at the point",
                            plan_labels=[{"node_id": "cdf", "label": "Find the CDF on the support", "current": False},
                                         {"node_id": "goal", "label": "Evaluate the CDF at the point",
                                          "current": True}], label_register="abstract")
    if kind == "error_specific":
        return empty_output(**base, hint_md=f"In '{questionable}' a CDF value is a probability on its own.",
                            principle="A CDF already gives P(X <= x).")
    if kind == "worked_parallel":
        return empty_output(**base, hint_md="For a density 3y^2 on [0, 1], F(y) = y^3, so P(Y <= c) = c^3.",
                            source_origin="ai")
    if kind == "continuation":
        # Placed at the givens (the map has one step before the goal), so the
        # continuation can end short of the goal.
        start = {**placement, "reached_node_id": "g" if context.get("approach_map") else "",
                 "stands_quote": "", "first_questionable_quote": lines[0] if has_work else "",
                 "quotes": [lines[0]] if has_work else []}
        return empty_output(**{**base, "placement": start},
                            hint_md="Integrate the density from 0 to x to get the CDF on the support.",
                            end_node_id="cdf")
    if kind == "worked_chunk":
        return empty_output(**base, hint_md="To find P(X <= c) it is enough to know F(c).",
                            pieces=[{"establishes": "P(X <= c) = F(c)", "how": "definition of the CDF",
                                     "why": "the question asks for P(X <= c)"}], gap="Evaluate F at the point.")
    if kind == "walkthrough":
        return empty_output(**base, hint_md="F(x) = x^2 on [0, 1], so P(X <= 1/2) = (1/2)^2 = 1/4.")
    if kind == "discriminating":
        rivals = context.get("rivals") or []
        predictions = [{"rival_id": rival["id"], "answer": str(index)} for index, rival in enumerate(rivals)]
        return empty_output(**base, candidates=[{"question_md": "What does your formula give at x = 0?",
                                                 "predictions": predictions}],
                            fallback_hint_md="What would your first move be?" if level == 1
                            else "Evaluate your CDF at the point.", asks_about="first_move" if level == 1 else "")
    raise AssertionError(f"no fake answer for {kind}")


Answer = Mapping[str, Any] | Callable[[Mapping[str, Any]], Mapping[str, Any]]


class WriterFake(StructuredClientFake):
    provider_name = "fake_writer"
    provider_type = "chatgpt_plan"
    model = "fake-writer-model"

    def __init__(self, answers: list[Answer] | None = None, *, provider_type: str = "chatgpt_plan",
                 fail: Exception | None = None, gate: Any = None) -> None:
        self.answers = list(answers or [])
        self.provider_type = provider_type
        self.fail = fail
        #: A ``threading.Event`` the call waits on (a writer still answering).
        self.gate = gate
        self.contexts: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = json.loads(json.dumps(_request_context(request.prompt, request.purpose)))
        self.contexts.append(context)
        self.prompts.append(request.prompt)
        if self.gate is not None:
            assert self.gate.wait(30), "the test never released the hint writer"
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 120,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        answer = self.answers.pop(0) if self.answers else good_answer
        payload = answer(context) if callable(answer) else answer
        return request.result_model.model_validate(payload)

    @property
    def calls(self) -> int:
        return len(self.contexts)


def uniform(options: list[str]) -> dict[str, float]:
    return {option: 1.0 / len(options) for option in options}


def prefer(option: str, weight: float = 0.9) -> Callable[[list[str]], dict[str, float]]:
    def choose(options: list[str]) -> dict[str, float]:
        if option not in options:
            return uniform(options)
        rest = (1.0 - weight) / max(1, len(options) - 1)
        return {name: (weight if name == option else rest) if len(options) > 1 else 1.0 for name in options}
    return choose


class ChooserFake:
    provider_name = "fake_decider"
    provider_type = "decider"
    model = "perplexity/pplx-decider-v1.1-27b"

    def __init__(self, choice: Callable[[list[str]], dict[str, float]] | None = None, *,
                 horizon: dict[int, float] | None = None, delay: float = 0.0, error: Exception | None = None,
                 cost: float = 0.0004) -> None:
        self.choice = choice or uniform
        self.horizon = horizon or {0: 0.1, 1: 0.5, 2: 0.3, 3: 0.1}
        self.delay = delay
        self.error = error
        self.cost = cost
        self.calls: list[dict[str, Any]] = []
        self.settings = type("S", (), {"price_per_million_input": 0.02})()

    def estimated_cost(self, input_tokens: int) -> float:
        return input_tokens * 0.02 / 1_000_000

    def decide(self, state, questions, *, purpose: str, timeout_seconds: float | None = None) -> DecisionResult:
        from learnloop.ai.decisions import request_body

        body = json.dumps(request_body(self.model, state, questions), sort_keys=True, default=str)
        with model_call(self, purpose=purpose, prompt=body):
            self.calls.append({"state": state, "questions": dict(questions), "purpose": purpose,
                               "timeout_seconds": timeout_seconds})
            if self.delay:
                time.sleep(self.delay)
            if self.error is not None:
                raise self.error
            report_call_usage({"input_tokens": 300, "output_tokens": 3, "cost": self.cost,
                               "resolved_model": self.model + "-dated"})
            answers: dict[str, Any] = {}
            for name, question in questions.items():
                wire = question.wire()
                if wire["type"] == "choice":
                    probabilities = self.choice(list(wire["criteria"]))
                    top = max(probabilities, key=probabilities.get)
                    answers[name] = ChoiceAnswer(choice=top, probabilities=probabilities, confidence=0.5)
                else:
                    levels = list(range(len(wire["criteria"])))
                    probabilities = {level: self.horizon.get(level, 0.0) for level in levels}
                    answers[name] = ScoreAnswer(score=1.0, probabilities=probabilities, confidence=0.5)
            return DecisionResult(answers=answers, model=self.model + "-dated", input_tokens=300, output_tokens=3,
                                  cost=self.cost, response_id="r", provider="Fake")
