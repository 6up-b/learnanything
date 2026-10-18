"""Fakes and builders for adaptive difficulty AD1's tests (no network, no paid call).

``AuditDecider`` is a decision client answering each audited dimension from a
table of distributions (a tie on purpose where a test needs one) and the
``will_pass`` noul question with a fixed ``p_yes``. ``ForecastLLM`` is a
structured client answering the feature audit's LLM judge and the item
forecasts, recording every prompt. ``ad_plan_vault`` is the daily-plan vault
with AD1's switches as given and the plan items' task features stamped.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from typing import Any

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult, NoulAnswer
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault

PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
ITEMS = ("pi_m1a", "pi_m1b", "pi_m1c")
LO = "lo_m1"
TASK_FEATURES = {"complexity": 1, "transfer": "same_context", "scaffolding": "cue", "span": "single_step",
                 "response": "short_constructed", "tools": ["closed_book"]}

ALL_OFF = """
[adaptive_difficulty]
forecast_receipts = false
outside_forecasters = []
rating_tap = false
feature_audit = false
"""


def rows(sqlite_path: Path, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def ad_receipts(sqlite_path: Path) -> list[dict[str, Any]]:
    return rows(sqlite_path, "SELECT * FROM forecast_receipts WHERE kind = 'item_unassisted_success' "
                             "ORDER BY created_at, rowid")


def stamp_task_features(paths: Any, item_id: str, features: Mapping[str, Any] = TASK_FEATURES, **extra: Any) -> None:
    import yaml

    path = paths.practice_item_path("linear-algebra", item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["capability"] = "retrieval"
    payload["task_features"] = dict(features)
    payload["task_feature_schema"] = "p1_launch@1"
    payload.update(extra)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def ad_plan_vault(tmp_path: Path, *, config: str = "", version: str = "mvp-0.22", items: tuple[str, ...] = ITEMS,
                  features: bool = True):
    los = {LO: [(item, 2.0) for item in items]}
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=version)
    if features:
        for item in items:
            stamp_task_features(paths, item, difficulty_source="llm_estimate")
    if config:
        append_config_toml(paths.root, config)
    return paths


def plan_env(paths: Any, *, clock: MovableClock | None = None, items: tuple[str, ...] = ITEMS, session: str = "s1"):
    clock = clock or MovableClock()
    env = make_env(paths.root, [scheduled(item, LO, forgetting_risk=0.6) for item in items], clock=clock,
                   session_id=session)
    for item in items:
        seed_due(env.repository, item, due=PAST, last=None)
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at, available_minutes) VALUES (?, ?, 30)",
                           (session, iso(clock.now())))
        connection.commit()
    return env, clock


class AuditDecider:
    """A Decider: a distribution per choice question, ``p_yes`` per noul question."""

    provider_name = "fake_decider"
    provider_type = "decider"
    model = "perplexity/pplx-decider-v1.1-27b"

    def __init__(self, distributions: Mapping[str, Mapping[str, float]] | None = None, *, p_yes: float = 0.7,
                 error: Exception | None = None) -> None:
        self.distributions = dict(distributions or {})
        self.p_yes = p_yes
        self.error = error
        self.calls: list[dict[str, Any]] = []
        self.settings = type("S", (), {"price_per_million_input": 0.02})()

    def decide(self, state, questions, *, purpose: str, timeout_seconds: float | None = None) -> DecisionResult:
        from learnloop.ai.decisions import request_body

        body = json.dumps(request_body(self.model, state, questions), sort_keys=True, default=str)
        with model_call(self, purpose=purpose, prompt=body):
            self.calls.append({"state": state, "questions": dict(questions), "purpose": purpose, "body": body})
            if self.error is not None:
                raise self.error
            report_call_usage({"input_tokens": 300, "output_tokens": 3, "cost": 0.0004,
                               "resolved_model": self.model})
            answers: dict[str, Any] = {}
            for name, question in questions.items():
                wire = question.wire()
                if wire["type"] == "choice":
                    options = list(wire["criteria"])
                    given = self.distributions.get(name)
                    probabilities = ({option: float(given.get(option, 0.0)) for option in options} if given
                                     else {option: (0.9 if index == 0 else 0.1 / max(1, len(options) - 1))
                                           for index, option in enumerate(options)})
                    total = sum(probabilities.values()) or 1.0
                    probabilities = {option: value / total for option, value in probabilities.items()}
                    top = max(probabilities, key=probabilities.get)
                    answers[name] = ChoiceAnswer(choice=top, probabilities=probabilities, confidence=0.5)
                else:
                    answers[name] = NoulAnswer(p_yes=self.p_yes)
            return DecisionResult(answers=answers, model=self.model, input_tokens=300, output_tokens=3,
                                  cost=0.0004, response_id="r", provider="Fake")


class ForecastLLM:
    """A structured chat client: the audit's LLM judge and the item forecasts."""

    provider_name = "fake_llm"
    provider_type = "chatgpt_plan"
    model = "fake-forecaster"

    def __init__(self, *, p_correct: float = 0.6, audit: Mapping[str, str] | None = None,
                 fail: Exception | None = None) -> None:
        self.p_correct = p_correct
        self.audit = dict(audit or {})
        self.fail = fail
        self.prompts: list[str] = []
        self.purposes: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        self.prompts.append(request.prompt)
        self.purposes.append(request.purpose)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 20,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        if request.result_model.__name__ == "FeatureAuditV1":
            return request.result_model.model_validate(self.audit)
        return request.result_model.model_validate({"p_correct": self.p_correct})


def everything_text(sqlite_path: Path) -> str:
    """Every AD receipt, payload and audit row, as one text (the sentinel test reads it)."""

    parts = []
    for table in ("forecast_receipts", "item_forecast_payloads", "item_serve_inputs", "ad_reading_opportunities"):
        parts.append(json.dumps(rows(sqlite_path, f"SELECT * FROM {table}"), default=str))
    parts.append(json.dumps(rows(sqlite_path, "SELECT * FROM judgment_ledger WHERE task IN "
                                              "('ad_feature_audit', 'ad_item_forecast')"), default=str))
    return "\n".join(parts)


__all__ = [
    "ALL_OFF", "AuditDecider", "ForecastLLM", "ITEMS", "LO", "TASK_FEATURES", "ad_plan_vault", "ad_receipts",
    "everything_text", "plan_env", "rows", "stamp_task_features",
]
