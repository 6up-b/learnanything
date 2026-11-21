"""Socket-free physical-request recorder for the live dialogue contract baselines."""
from __future__ import annotations

import json

from learnloop.ai.execution import active_request_gate
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.config import AIProviderConfig
from learnloop.teacher import service
from learnloop.vault.loader import load_vault
from tests.openai_fakes import install_fake_openai
from tests.teacher_fakes import build_teacher_vault, clients


class RecordingChat(OpenAIChatProviderClient):
    def __init__(self, profile):
        super().__init__("contract_test", profile)
        self.gates = []
        self.operations = []
        self.error_after = None
        self.after = None
        self.before = None

    def complete(self, request):
        self.gates.append(active_request_gate())
        self.operations.append(request)
        if self.before is not None:
            self.before()
        answer = super().complete(request)
        if self.after is not None:
            self.after()
        if self.error_after is not None:
            raise self.error_after
        return answer


def chat(monkeypatch, answers):
    module = install_fake_openai(monkeypatch, *[
        json.dumps(answer) if isinstance(answer, dict) else answer for answer in answers
    ])
    monkeypatch.setenv("CONTRACT_TEST_KEY", "test-double")
    client = RecordingChat(AIProviderConfig(
        type="openai_chat", base_url="https://example.invalid", api_key_env="CONTRACT_TEST_KEY",
        model="test", response_format="json_schema", timeout_seconds=40,
    ))
    return client, module.instances[0].requests


def teacher(tmp_path, client):
    paths, repository = build_teacher_vault(tmp_path / "vault", config='''
[teacher]
allow_metered = true
metered_price_per_million = 1.0
max_lesson_cost_usd = 10.0
''')
    vault = load_vault(paths.root)
    result = service.open_lesson(vault, repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                                 clients=clients(client))
    return result, repository
