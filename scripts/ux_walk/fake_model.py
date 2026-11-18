"""A local stand-in for an OpenAI-compatible chat endpoint, for walks with faked model routes.

The walk vault's ``walk_fake`` profile is an ordinary ``openai_chat`` profile
whose ``base_url`` points here (the bridge serves it on 127.0.0.1), so the
sidecar runs its real client, routing, receipts and validation; only the
answer is made up. Each structured request carries its JSON schema
(``response_format: json_schema``); the answer is built from it:

- a string property whose name appears as a key in a JSON object inside the
  prompt takes that value (the grader's ``attempt_id`` and ``practice_item_id``
  echo the request, for instance);
- an ``enum`` takes its first value; numbers take the middle of their range;
  arrays take their minimum length; nullable fields stay null;
- other strings read ``[walk fake model: <field>]``, so a person on the walk can
  see which words no model wrote;
- ``fake_answers.json`` beside this file overrides top-level fields by schema
  name (a grader's confidence, say), and a few recipes below fill what a
  route needs to be accepted at all (a grade covers the rubric's criteria).

Nothing here opens a connection; the bridge owns the socket.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

FAKE_PROFILE = "walk_fake"
FAKE_MODEL = "walk-fake-model"
FAKE_KEY_ENV = "LEARNLOOP_WALK_FAKE_KEY"
OVERRIDES_PATH = Path(__file__).with_name("fake_answers.json")
_JSON_START = re.compile(r"[{\[]")


def _embedded_objects(text: str, limit: int = 200) -> list[Any]:
    """Every JSON object or array that parses at some ``{``/``[`` in ``text``."""

    decoder = json.JSONDecoder()
    found: list[Any] = []
    position = 0
    while len(found) < limit:
        match = _JSON_START.search(text, position)
        if match is None:
            break
        try:
            value, end = decoder.raw_decode(text, match.start())
        except ValueError:
            position = match.start() + 1
            continue
        if isinstance(value, (dict, list)):
            found.append(value)
        position = end
    return found


def _scalar_keys(values: list[Any]) -> dict[str, Any]:
    """The first scalar seen under each key, anywhere in the nested values."""

    seen: dict[str, Any] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (str, int, float, bool)) and key not in seen:
                    seen[key] = value
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for value in values:
        visit(value)
    return seen


def _criteria(values: list[Any]) -> list[dict[str, Any]]:
    """Rubric criteria named in the prompt: objects with an ``id`` and ``points``."""

    found: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            criteria = node.get("criteria")
            if isinstance(criteria, list) and all(isinstance(entry, dict) and "id" in entry for entry in criteria):
                if not found:
                    found.extend(criteria)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for value in values:
        visit(value)
    return found


class SchemaInstance:
    """Builds one value that satisfies a strict JSON schema."""

    def __init__(self, schema: dict[str, Any], echoes: dict[str, Any]):
        self.root = schema
        self.echoes = echoes

    def build(self, schema: dict[str, Any] | None = None, key: str = "") -> Any:
        schema = self._resolve(schema if schema is not None else self.root)
        if "const" in schema:
            return schema["const"]
        if "enum" in schema:
            choices = [choice for choice in schema["enum"] if choice is not None]
            return choices[0] if choices else None
        for combinator in ("anyOf", "oneOf"):
            if combinator in schema:
                options = [self._resolve(option) for option in schema[combinator]]
                concrete = [option for option in options if option.get("type") != "null"]
                if any(option.get("type") == "null" for option in options) and key not in self.echoes:
                    return None
                return self.build(concrete[0] if concrete else options[0], key)
        if "allOf" in schema:
            merged: dict[str, Any] = {}
            for part in schema["allOf"]:
                merged.update(self._resolve(part))
            return self.build(merged, key)
        kind = schema.get("type")
        if isinstance(kind, list):
            concrete = [entry for entry in kind if entry != "null"]
            if "null" in kind and key not in self.echoes:
                return None
            kind = concrete[0] if concrete else "null"
        if kind == "object" or "properties" in schema:
            return {
                name: self.build(sub, name) for name, sub in (schema.get("properties") or {}).items()
            }
        if kind == "array":
            return [self.build(schema.get("items") or {}, key) for _ in range(int(schema.get("minItems") or 0))]
        if kind == "string":
            echoed = self.echoes.get(key)
            if isinstance(echoed, str):
                return echoed
            text = f"[walk fake model: {key or 'text'}]"
            minimum = int(schema.get("minLength") or 0)
            return text.ljust(minimum, ".")
        if kind in ("number", "integer"):
            low = schema.get("minimum", schema.get("exclusiveMinimum", 0))
            high = schema.get("maximum", schema.get("exclusiveMaximum", low if low > 1 else 1))
            value = (low + high) / 2
            return int(round(value)) if kind == "integer" else value
        if kind == "boolean":
            return False
        return None

    def _resolve(self, schema: dict[str, Any]) -> dict[str, Any]:
        while isinstance(schema, dict) and "$ref" in schema:
            ref = schema["$ref"]
            node: Any = self.root
            for part in ref.removeprefix("#/").split("/"):
                node = node[part]
            schema = node
        return schema


def _grade_recipe(answer: dict[str, Any], criteria: list[dict[str, Any]]) -> None:
    """A grade names each rubric criterion with half its points, rounded down."""

    if "criterion_evidence" not in answer or not criteria:
        return
    evidence = []
    total = 0
    for criterion in criteria:
        points = int(criterion.get("points") or 0) // 2
        total += points
        evidence.append({
            "criterion_id": str(criterion["id"]),
            "points_awarded": points,
            "evidence": "[walk fake model: half credit on every criterion]",
            "notes": None,
            "learner_confidence": "unknown",
        })
    answer["criterion_evidence"] = evidence
    if "rubric_score" in answer:
        answer["rubric_score"] = total


class Declined(Exception):
    """A route the fake model will not answer: the bridge replies 400 and the app treats the model as unavailable."""


class FakeModel:
    def __init__(self, overrides_path: Path = OVERRIDES_PATH):
        self.overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
        decline = self.overrides.get("_decline") or {}
        self.decline = [re.compile(pattern) for pattern in decline.get("patterns") or []]

    def declines(self, schema_name: str) -> bool:
        return any(pattern.search(schema_name) for pattern in self.decline)

    def answer(self, body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """The chat completion for one request body, and a log record for the analyst.

        Raises :class:`Declined` for a decision or forecast route (``fake_answers.json``'s ``_decline``)."""

        schema_name = ((body.get("response_format") or {}).get("json_schema") or {}).get("name") or ""
        if schema_name and self.declines(schema_name):
            raise Declined(schema_name)
        messages = body.get("messages") or []
        prompt = "\n".join(_message_text(message) for message in messages)
        response_format = body.get("response_format") or {}
        schema_block = response_format.get("json_schema") or {}
        schema = schema_block.get("schema")
        name = schema_block.get("name") or ""
        if schema is None:
            schema = _schema_from_prompt(prompt)
        embedded = _embedded_objects(prompt)
        echoes = _scalar_keys(embedded)
        content: Any
        if schema is None:
            content = {"answer": "[walk fake model]"}
        else:
            content = SchemaInstance(schema, echoes).build()
            if isinstance(content, dict):
                _grade_recipe(content, _criteria(embedded))
                for field, value in (self.overrides.get(name) or {}).items():
                    if field in content:
                        content[field] = value
        text = json.dumps(content)
        completion = {
            "id": f"walkfake-{time.time_ns()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model") or FAKE_MODEL,
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": max(1, len(prompt) // 4), "completion_tokens": max(1, len(text) // 4),
                      "total_tokens": max(1, len(prompt) // 4) + max(1, len(text) // 4)},
        }
        record = {"schema": name or None, "prompt_chars": len(prompt), "answer": text[:2000]}
        return completion, record


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _schema_from_prompt(prompt: str) -> dict[str, Any] | None:
    """A ``json_object`` profile puts the schema in the system prompt; take the largest object schema there."""

    candidates = [value for value in _embedded_objects(prompt) if isinstance(value, dict) and "properties" in value]
    return max(candidates, key=lambda value: len(json.dumps(value))) if candidates else None


def provider_table(base_url: str) -> dict[tuple[str, ...], Any]:
    """The ``learnloop.toml`` keys that make ``walk_fake`` the vault's active provider."""

    prefix = ("ai", "providers", FAKE_PROFILE)
    return {
        ("ai", "active_provider"): FAKE_PROFILE,
        (*prefix, "type"): "openai_chat",
        (*prefix, "model"): FAKE_MODEL,
        (*prefix, "base_url"): base_url,
        (*prefix, "api_key_env"): FAKE_KEY_ENV,
        (*prefix, "response_format"): "json_schema",
        (*prefix, "timeout_seconds"): 60,
    }


def ai_defaults_toml(base_url: str) -> str:
    """The machine-wide AI defaults a vault created during the walk inherits (bootstrap reads them)."""

    return (
        "[ai]\n"
        f'active_provider = "{FAKE_PROFILE}"\n\n'
        f"[ai.providers.{FAKE_PROFILE}]\n"
        'type = "openai_chat"\n'
        f'model = "{FAKE_MODEL}"\n'
        f'base_url = "{base_url}"\n'
        f'api_key_env = "{FAKE_KEY_ENV}"\n'
        'response_format = "json_schema"\n'
        "timeout_seconds = 60\n"
    )
