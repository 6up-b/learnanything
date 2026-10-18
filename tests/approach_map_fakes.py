"""Builders and a fake model for adaptive hints H1's approach-map tests (no network).

``MapFake`` is a ``StructuredClientFake`` that answers the approach-map
builder and the learner-route merge from the prompt's own JSON: a queue of
answers (dicts or callables of the request context) and, when the queue is
empty, a valid map of the CDF item (or a merge that places every new
solution on the reference route). Knobs: ``provider_type`` (``codex_sdk``
bills the subscription, anything else is metered), ``gate`` (a
``threading.Event`` the call waits on: a model still answering) and ``fail``.
Plumbing checks only, never evidence about quality.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.connection import connect
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import NOW_ISO, append_config_toml, create_basic_vault
from tests.structured_ai import StructuredClientFake, _request_context

ITEM = "pi_cdf_1"
SUBJECT = "linear-algebra"
LO = "lo_svd_definition"
PROMPT = "X has density f(x) = 2x on [0, 1]. Find P(X ≤ 1/2)."
EXPECTED = "Integrate the density: F(x) = x^2 on [0, 1]. Therefore P(X ≤ 1/2) = 1/4."
HINTS = ["What is the CDF of X on its support?", "Evaluate the CDF at the point."]
TRACE_CONTRACT = {"status": "available", "recipes": [
    {"id": "cdf_route", "checkpoints": ["cdf", "value"], "dependencies": {"value": ["cdf"]}},
    {"id": "direct_route", "checkpoints": ["value"], "dependencies": {}},
]}
RUBRIC = {"max_points": 4, "criteria": [
    {"id": "cdf", "points": 2, "description": "Finds the CDF on the support."},
    {"id": "value", "points": 2, "description": "Evaluates the probability."},
], "fatal_errors": []}


def write_item(paths: Any, item_id: str = ITEM, *, prompt: str = PROMPT, expected: Any = EXPECTED,
               hints: list[str] | None = None, trace_contract: dict | None = None, family_id: str | None = None,
               facets: tuple[str, ...] = ("recall",), status: str = "active") -> None:
    payload: dict[str, Any] = {
        "schema_version": 1, "id": item_id, "learning_object_id": LO, "subjects": None,
        "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt", "hinted_attempt"],
        "evidence_facets": list(facets), "evidence_weights": {facet: 1.0 for facet in facets},
        "prompt": prompt, "expected_answer": expected, "difficulty": 0.5, "tags": [],
        "hints": list(HINTS if hints is None else hints), "grading_rubric": RUBRIC,
        "provenance": {"origin": "human", "source_refs": []}, "status": status,
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }
    if trace_contract is not None:
        payload["trace_contract"] = trace_contract
    if family_id is not None:
        payload["family_id"] = family_id
        payload["variant_relation"] = "isomorph"
    write_yaml(paths.practice_item_path(SUBJECT, item_id), payload)


def map_vault(tmp_path: Path, *, config: str = "", name: str = "vault", **item: Any):
    paths = create_basic_vault(tmp_path / name)
    write_item(paths, **item)
    if config:
        append_config_toml(paths.root, config)
    return paths


def add_attempt(sqlite_path: Path, attempt_id: str, *, item_id: str = ITEM, correctness: float | None = 1.0,
                answer: str = "F(x) = x^2, so P = 1/4.", attempt_type: str = "independent_attempt",
                created_at: str = "2026-10-17T09:00:00+00:00") -> None:
    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, created_at) VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?)",
            (attempt_id, item_id, LO, attempt_type, answer, correctness, created_at))
        connection.commit()


def add_skeleton(sqlite_path: Path, item_prompt: str = PROMPT, expected: Any = EXPECTED, *,
                 checkpoints: list[str] | None = None) -> str:
    from learnloop.db.stores.pf import insert_skeleton
    from learnloop.vault.hashes import skeleton_content_hash

    with closing(connect(sqlite_path)) as connection:
        insert_skeleton(connection, skeleton_id="sk_1", content_hash=skeleton_content_hash(item_prompt, expected),
                        subject_kind="practice_item", subject_id=ITEM, model_id="fake-skeleton-model",
                        prompt_version="pf_skeleton.v1", techniques=["integrate", "evaluate"],
                        operations=["F = int f", "P = F(1/2)"], checkpoints=checkpoints or ["sk_cdf", "sk_value"],
                        skeleton_text="Integrate the density, then evaluate the CDF.", created_at=NOW_ISO)
        connection.commit()
    return "sk_1"


def rows(sqlite_path: Path, table: str = "approach_maps") -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone()
        if exists is None:
            return []
        order = "version" if table == "approach_maps" else "rowid"
        return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY {order}')]


def ledger(sqlite_path: Path) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'approach_map_valid' ORDER BY created_at, rowid")]


def receipts(sqlite_path: Path) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE owner_kind = 'approach_map' AND parent_call_id IS NULL "
            "ORDER BY started_at, rowid")]


def node(node_id: str, role: str, label: str, state: str, *, checkpoint: str = "", leak: bool = False) -> dict:
    return {"id": node_id, "role": role, "label": label, "state": state, "recognizers": [state[:20]],
            "checkpoint_id": checkpoint, "leak": leak}


def edge(source: str, target: str, *, facets: tuple[str, ...] = ()) -> dict:
    return {"from_node": source, "to_node": target, "technique": "step", "principle": "a principle",
            "facet_ids": list(facets)}


def good_map(context: Any = None, **overrides: Any) -> dict[str, Any]:
    """A valid map of the CDF item: the reference route and, when learner
    solutions are seeded, a learner route through the same nodes."""

    payload = {
        "nodes": [node("g", "given", "Read the density", "f(x) = 2x on [0, 1]"),
                  node("cdf", "step", "Find the CDF on the support", "$F(x) = x^2$ on [0, 1]"),
                  node("goal", "goal", "Evaluate the CDF at the point", "P(X ≤ 1/2) = 1/4")],
        "edges": [edge("g", "cdf", facets=("recall",)), edge("cdf", "goal")],
        "routes": [{"id": "r_ref", "name": "CDF route", "path": ["g", "cdf", "goal"], "origin": "reference",
                    "learner_attempt_ids": []}],
        "goal_node_id": "goal", "goal_answer": "1/4",
    }
    solutions = (context or {}).get("learner_solutions") if isinstance(context, dict) else None
    if solutions:
        payload["routes"][0]["learner_attempt_ids"] = [solution["ref"] for solution in solutions]
    payload.update(overrides)
    return payload


def merge_onto_reference(context: dict[str, Any]) -> dict[str, Any]:
    return {"matches": [{"attempt_ref": solution["ref"], "route_id": "r_ref"}
                        for solution in context["new_learner_solutions"]], "new_routes": []}


def merge_as_new_route(context: dict[str, Any]) -> dict[str, Any]:
    refs = [solution["ref"] for solution in context["new_learner_solutions"]]
    return {"matches": [], "new_routes": [{
        "id": "r_learner", "name": "Complement route", "attempt_refs": refs,
        "nodes": [node("comp", "step", "Use the complement", "P(X > 1/2) = 3/4")],
        "edges": [edge("g", "comp"), edge("comp", "goal")], "path": ["g", "comp", "goal"]}]}


Answer = dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]]


class MapFake(StructuredClientFake):
    provider_name = "fake_maps"
    provider_type = "codex_sdk"
    model = "fake-map-model"

    def __init__(self, answers: list[Answer] | None = None, *, provider_type: str = "codex_sdk",
                 gate: threading.Event | None = None, fail: bool = False) -> None:
        self.answers = list(answers or [])
        self.provider_type = provider_type
        self.gate = gate
        self.fail = fail
        self.started = threading.Event()
        self.requests: list[tuple[str, dict[str, Any]]] = []
        self.prompts: list[str] = []
        self._lock = threading.Lock()

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        from learnloop.ai.errors import AIProviderUnavailable

        context = json.loads(json.dumps(_request_context(request.prompt, request.purpose)))
        with self._lock:
            self.requests.append((request.purpose, context))
            self.prompts.append(request.prompt)
            answer = self.answers.pop(0) if self.answers else None
        self.started.set()
        if self.gate is not None:
            assert self.gate.wait(30), "the test never released the map model"
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 200,
                           "resolved_model": self.model})
        if self.fail:
            raise AIProviderUnavailable("fake failure")
        if answer is None:
            answer = good_map if request.purpose == "approach_map" else merge_onto_reference
        payload = answer(context) if callable(answer) else answer
        return request.result_model.model_validate(payload)

    @property
    def calls(self) -> int:
        return len(self.requests)


__all__ = [
    "EXPECTED", "HINTS", "ITEM", "LO", "MapFake", "PROMPT", "RUBRIC", "SUBJECT", "TRACE_CONTRACT", "add_attempt",
    "add_skeleton", "edge", "good_map", "ledger", "map_vault", "merge_as_new_route", "merge_onto_reference",
    "node", "receipts", "rows", "write_item",
]
