"""Synthetic wire answers for the step 5 pre-adoption measurements."""

from types import SimpleNamespace

from learnloop.ai.chatgpt_plan.responses import ResponsesStream, StreamResult
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.providers.openrouter import OpenRouterProviderClient
from learnloop.config import AIProviderConfig
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.diagnosis.ai_contracts import FollowupProbeAuthored, FollowupProbeContext
from tests.followup_serve_helpers import AuthorFake
from tests.structured_ai import RecordingStructuredClientFake, StructuredClientFake
from tests.openai_fakes import install_fake_openai


CONTEXT = FollowupProbeContext(
    learning_object_title="Eigenvalues",
    learning_object_concept="eigenvalue",
    learning_object_summary="Scalars a matrix stretches its eigenvectors by.",
    target_facets=["facet_eigen"],
    hypotheses=[
        {"hypothesis_ref": "H1", "statement": "confuses rows and columns", "cause_scope": "", "target_ref": None},
        {"hypothesis_ref": "H2", "statement": "confuses the two conditions", "cause_scope": "", "target_ref": None},
    ],
    router_decision={"action": "probe"},
)
GOOD = AuthorFake().run_followup_probe_authoring(CONTEXT)
EMPTY = FollowupProbeAuthored(prompt_md="", expected_answer_md="k" * 636, surface_suffix="s" * 24)


class CaptureAuthor(RecordingStructuredClientFake):
    def run_followup_probe_authoring(self, context):
        return GOOD


class JobAuthor(StructuredClientFake, AuthorFake):
    """Workflow-shaped answers, with public callbacks at send boundaries."""

    def __init__(self, *changes):
        AuthorFake.__init__(self)
        self.changes = iter(changes)
        self.requests = []
        self.before_send = lambda: None
        self.profile = SimpleNamespace(timeout_seconds=40)

    def complete(self, request):
        self.before_send()
        self.requests.append(request)
        return super().complete(request)

    def run_followup_probe_authoring(self, context):
        good = AuthorFake.run_followup_probe_authoring(self, context)
        return good.model_copy(update=next(self.changes))


class Crash(BaseException):
    """Simulated process death, outside the worker's handled Exception tree."""


def plan_client(monkeypatch, answers):
    """Real plan completion/repair logic; public stream seam, no socket or sign-in."""
    replies = iter(answers)
    requests = []

    def send(self, body, **kwargs):
        requests.append(body)
        answer = next(replies)
        if isinstance(answer, Exception):
            raise answer
        text = answer if isinstance(answer, str) else answer.model_dump_json()
        return StreamResult(response={}, text=text, request_id=None, status=200,
                            seconds_to_headers=0, seconds_to_first_event=0, seconds_total=0)

    monkeypatch.setattr(ResponsesStream, "send", send)
    session = SimpleNamespace(check_usable=lambda **kwargs: None, access_token=lambda **kwargs: "fake",
                              note_success=lambda observed: None)
    client = ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(model="test-model", timeout_seconds=40),
                                       session=session)
    return client, requests


def provider_client(monkeypatch, provider, answers):
    if provider == "plan":
        return plan_client(monkeypatch, answers)
    monkeypatch.setenv("TEST_FOLLOWUP_KEY", "fake")
    fake = install_fake_openai(monkeypatch, *[
        answer if isinstance(answer, (str, Exception)) else answer.model_dump_json() for answer in answers
    ])
    client = OpenRouterProviderClient("router", AIProviderConfig(
        type="openrouter", model="test-model", api_key_env="TEST_FOLLOWUP_KEY", timeout_seconds=40))
    return client, fake.instances[0].requests
