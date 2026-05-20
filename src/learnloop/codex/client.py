from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from dataclasses import dataclass, field
from typing import Protocol

from learnloop.config import CodexConfig
from learnloop.codex.schemas import AuthoringProposal, GradingProposal


@dataclass(frozen=True)
class AuthoringContext:
    vault_root: str
    source_ids: list[str]
    instructions: str | None = None
    subjects: list[str] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    concepts: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    learning_objects: list[dict] = field(default_factory=list)
    practice_items: list[dict] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class GradingContext:
    attempt_id: str
    practice_item_id: str
    prompt: str
    expected_answer: str
    learner_answer_md: str
    rubric: dict


class CodexClient(Protocol):
    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        ...

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        ...


class CodexUnavailable(RuntimeError):
    pass


class HttpCodexClient:
    """Minimal local Codex app-server client.

    The MVP transport is intentionally small: JSON POSTs to a local app-server.
    The server may return the proposal directly or under a top-level
    ``proposal`` key.
    """

    def __init__(self, config: CodexConfig):
        self.config = config

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        payload = self._post(self.config.authoring_path, {"context": asdict(context)})
        return AuthoringProposal.model_validate(payload.get("proposal", payload))

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        payload = self._post(self.config.grading_path, {"context": asdict(context)})
        return GradingProposal.model_validate(payload.get("proposal", payload))

    def _post(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            _url(self.config.base_url, path),
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.healthcheck_timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise CodexUnavailable(f"Codex app-server HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise CodexUnavailable(str(exc.reason)) from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexUnavailable("Codex app-server returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise CodexUnavailable("Codex app-server response must be a JSON object")
        return decoded


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")
