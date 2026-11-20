"""UX-13: a new learner's first document gets its questions (UX journey audit, part 2).

The walks on the live route (the ChatGPT plan) wrote answers a little over the
size each step asks for: inventory windows up to 3,169 output tokens against
3,000, a synthesis pass 10,352 against 10,000. Each was refused after it was
paid for, nothing retried on its own, and the book's questions never came.

The rule now: the working size is what the model is asked to aim for; a
complete, valid answer is kept up to the step's ceiling (an inventory window:
``inventory_output_ceiling_tokens``; a synthesis pass: what the run's total
output budget leaves), and an answer over it is refused and not kept. An
automatic build retries a failed model step once on its own, reusing every
answer it kept; a second failure stops the build with Retry on the card.

Every model call here is a house fake, or the house fake of a provider's HTTP
client; nothing leaves the machine.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from learnloop.ai.errors import AITurnTimeout
from learnloop.ai.execution import output_limit
from learnloop.ai.usage import TokenUsage
from learnloop.content.pipeline.add_source import latest_auto_outcome, source_status_line
from learnloop.content.pipeline.build_plan import build_build_plan
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.ai_contracts import source_set_synthesis_prompt, source_unit_inventory_prompt
from learnloop.vault.loader import load_vault

from tests.source_inventory_helpers import FakeInventoryClient
from tests.ux_phase1_review_fixes_helpers import _add, _jobs, _metered
from tests.ux_phase1_support import FakeBookSynthesisClient, fake_services, fresh_library, grant_consent, write_book

# What the live model wrote in the walks, as its service reported it.
INVENTORY_WALK_LARGEST = 3_169  # expert-1, told 3,000
SYNTHESIS_WALK_LARGEST = 10_352  # student-2, told 10,000
# Over each step's ceiling: a runaway.
INVENTORY_RUNAWAY = 7_000  # over inventory_output_ceiling_tokens (6,000)
SYNTHESIS_RUNAWAY = 16_500  # over synthesis_output_tokens (16,000), what a first run's pass may use


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


class Script:
    """What each model call answers, shared by every client a build makes.

    ``inventory(unit_id, call_number)`` and ``synthesis(call_number)`` return
    the output tokens the call reports, or an exception the call raises. Every
    request is recorded with the generation limit it was sent under and its
    rendered prompt."""

    def __init__(self, *, inventory=None, synthesis=None):
        self.inventory_answer = inventory or (lambda unit_id, n: 500)
        self.synthesis_answer = synthesis or (lambda n: 500)
        self.inventory_calls: list[str] = []
        self.synthesis_calls = 0
        self.requests: list[tuple[str, int | None, str]] = []

    def inventory_client(self, ctx=None):
        script = self

        class Client(FakeInventoryClient):
            def __init__(self):
                super().__init__()
                self.reported = TokenUsage()

            def snapshot_usage(self):
                return self.reported

            def run_source_unit_inventory(self, context):
                script.inventory_calls.append(context.unit_id)
                script.requests.append(("inventory", output_limit(), source_unit_inventory_prompt(context)))
                answer = script.inventory_answer(context.unit_id, script.inventory_calls.count(context.unit_id))
                if isinstance(answer, BaseException):
                    raise answer
                result = super().run_source_unit_inventory(context)
                self.reported = self.reported + TokenUsage(output_tokens=answer, calls=1)
                return result

        return Client()

    def synthesis_client(self, ctx=None):
        script = self

        class Client(FakeBookSynthesisClient):
            def __init__(self):
                super().__init__()
                self.reported = TokenUsage()

            def snapshot_usage(self):
                return self.reported

            def run_source_set_synthesis(self, context):
                script.synthesis_calls += 1
                script.requests.append(("synthesis", output_limit(), source_set_synthesis_prompt(context)))
                answer = script.synthesis_answer(script.synthesis_calls)
                if isinstance(answer, BaseException):
                    raise answer
                result = super().run_source_set_synthesis(context)
                self.reported = self.reported + TokenUsage(output_tokens=answer, calls=1)
                return result

        return Client()


def _first_document(tmp_path, script: Script):
    """A brand-new library adds its first book; its automatic build runs to
    the end on this thread."""

    root = fresh_library(tmp_path)
    grant_consent(root)
    services = fake_services(inventory_client_factory=script.inventory_client,
                             synthesis_client_factory=script.synthesis_client)
    repo, jobs = _jobs(root, services)
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert outcome["outcome"] == "building"
    build = {job["job_type"]: job for job in repo.ingest_jobs_for_batch(outcome["build_batch_id"])}
    return root, repo, item, build


def _job(repo, job):
    return repo.get_ingest_job(job["id"])


def _checkpoints(repo, purpose: str) -> int:
    with repo.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_work_checkpoints WHERE purpose = ?", (purpose,)
        ).fetchone()[0]


def _line(root, repo, item):
    return source_status_line(repo, load_vault(root), item["source_id"])


def _stopped_with_retry(line) -> None:
    # What Today's cause line reads as "Couldn't get questions ready … Try
    # again" (todayCause.ts: a problem line whose action is Retry).
    assert line["tone"] == "problem", line
    assert line["action"] == {"kind": "retry", "label": "Retry"}, line


# -- A complete answer a little over the working size is kept ----------------


def test_an_inventory_window_a_little_over_its_working_size_completes(tmp_path):
    script = Script(inventory=lambda unit_id, n: INVENTORY_WALK_LARGEST)

    root, repo, item, build = _first_document(tmp_path, script)

    assert _job(repo, build["inventory"])["status"] == "completed"
    assert _job(repo, build["bootstrap_synthesis"])["status"] == "completed"
    # Each unit asked once: kept as it came.
    assert sorted(script.inventory_calls) == sorted(set(script.inventory_calls))
    assert _line(root, repo, item)["tone"] != "problem"


def test_a_synthesis_pass_a_little_over_its_shard_size_completes(tmp_path):
    script = Script(synthesis=lambda n: SYNTHESIS_WALK_LARGEST)

    root, repo, item, build = _first_document(tmp_path, script)

    assert _job(repo, build["bootstrap_synthesis"])["status"] == "completed"
    assert script.synthesis_calls == 1
    assert _line(root, repo, item)["tone"] != "problem"


# -- A runaway answer is still refused -----------------------------------------


def test_a_runaway_inventory_window_is_refused_not_kept_and_asked_once_more(tmp_path):
    script = Script(inventory=lambda unit_id, n: INVENTORY_RUNAWAY)

    root, repo, item, build = _first_document(tmp_path, script)

    inventory = _job(repo, build["inventory"])
    assert inventory["status"] == "failed"
    assert inventory["error"]["code"] == "InventoryValidationError"
    # Refused, so not kept: a retry could only reuse it into the same refusal.
    assert _checkpoints(repo, "inventory_window") == 0
    # The build asked once more on its own, then stopped.
    first_unit = script.inventory_calls[0]
    assert script.inventory_calls.count(first_unit) == 2
    assert _job(repo, build["bootstrap_synthesis"])["status"] == "blocked"
    _stopped_with_retry(_line(root, repo, item))


def test_a_runaway_synthesis_pass_is_refused_not_kept_and_asked_once_more(tmp_path):
    script = Script(synthesis=lambda n: SYNTHESIS_RUNAWAY)

    root, repo, item, build = _first_document(tmp_path, script)

    synthesis = _job(repo, build["bootstrap_synthesis"])
    assert synthesis["status"] == "failed"
    assert synthesis["error"]["code"] == "budget_exceeded"
    assert _checkpoints(repo, "synthesis_pass") == 0
    assert script.synthesis_calls == 2
    _stopped_with_retry(_line(root, repo, item))


# -- A failed step is retried once on its own ----------------------------------


def test_an_inventory_that_fails_once_is_retried_once_without_asking_again_for_what_was_kept(tmp_path):
    failing: list[str] = []

    def inventory(unit_id, n):
        # The second unit asked times out the first time; every other answer is fine.
        if not failing and len(set(script.inventory_calls)) > 1:
            failing.append(unit_id)
        return AITurnTimeout("The model took too long.") if failing == [unit_id] and n == 1 else 500

    script = Script(inventory=inventory)

    root, repo, item, build = _first_document(tmp_path, script)

    inventory_job = _job(repo, build["inventory"])
    assert inventory_job["status"] == "completed"
    assert inventory_job["attempt_count"] == 1  # nobody pressed Retry
    assert failing, "the book has more than one unit"
    # The unit that failed was asked twice; every unit it did not take down was asked once.
    assert {unit_id: script.inventory_calls.count(unit_id) for unit_id in script.inventory_calls} == {
        unit_id: (2 if unit_id == failing[0] else 1) for unit_id in script.inventory_calls
    }
    assert _job(repo, build["bootstrap_synthesis"])["status"] == "completed"
    assert _line(root, repo, item)["tone"] != "problem"


def test_a_synthesis_that_fails_once_is_retried_once_and_the_inventories_are_not_asked_again(tmp_path):
    script = Script(synthesis=lambda n: AITurnTimeout("The model took too long.") if n == 1 else 500)

    root, repo, item, build = _first_document(tmp_path, script)

    synthesis = _job(repo, build["bootstrap_synthesis"])
    assert synthesis["status"] == "completed"
    assert synthesis["attempt_count"] == 1
    assert script.synthesis_calls == 2
    assert sorted(script.inventory_calls) == sorted(set(script.inventory_calls))


def test_a_synthesis_retry_reuses_the_pass_it_kept(tmp_path, monkeypatch):
    """The pass was kept; what failed came after it (the gate stage's
    structuring call): the retry pays nothing again for the pass."""

    from learnloop.content.synthesis import source_set_synthesis as synthesis_module

    real = synthesis_module._model_graph_structuring
    failures = []

    def flaky(*args, **kwargs):
        if not failures:
            failures.append(1)
            raise AITurnTimeout("The model took too long.")
        return real(*args, **kwargs)

    monkeypatch.setattr(synthesis_module, "_model_graph_structuring", flaky)
    script = Script()

    _root, repo, _item, build = _first_document(tmp_path, script)

    assert failures == [1]
    assert _job(repo, build["bootstrap_synthesis"])["status"] == "completed"
    assert script.synthesis_calls == 1


# -- A second failure stops the build with Retry ---------------------------------


def test_an_inventory_that_fails_twice_stops_with_retry_and_the_card_says_so(tmp_path):
    script = Script(inventory=lambda unit_id, n: AITurnTimeout("The model took too long."))

    root, repo, item, build = _first_document(tmp_path, script)

    inventory = _job(repo, build["inventory"])
    assert inventory["status"] == "failed"
    assert inventory["attempt_count"] == 1
    first_unit = script.inventory_calls[0]
    assert script.inventory_calls.count(first_unit) == 2
    batch = repo.get_ingest_batch(build["inventory"]["batch_id"])
    assert batch["status"] == "failed"
    _stopped_with_retry(_line(root, repo, item))


def test_a_synthesis_that_fails_twice_stops_with_retry_and_the_card_says_so(tmp_path):
    script = Script(synthesis=lambda n: AITurnTimeout("The model took too long."))

    root, repo, item, build = _first_document(tmp_path, script)

    synthesis = _job(repo, build["bootstrap_synthesis"])
    assert synthesis["status"] == "failed"
    assert script.synthesis_calls == 2
    assert repo.get_ingest_batch(build["bootstrap_synthesis"]["batch_id"])["status"] == "failed"
    _stopped_with_retry(_line(root, repo, item))


# -- What is sent, and what the learner is shown -----------------------------------


# The requests of a build that fits the working sizes, rendered as before this
# change (computed on the base commit, 713a0efd08): each step's prompt and the
# limit it is sent under, which the plan route states at the prompt's end.
_ULID = re.compile(r"_[0-9A-HJKMNP-TV-Z]{26}")
WITHIN_BUDGET_REQUESTS = "dde2d9311363cd77c271d95d0acb2a5269eae805a79ded4fd44c598bd560177c"


def test_a_build_that_fits_the_working_sizes_sends_the_same_requests(tmp_path):
    script = Script()

    _root, repo, _item, build = _first_document(tmp_path, script)

    assert _job(repo, build["bootstrap_synthesis"])["status"] == "completed"
    assert [(kind, limit) for kind, limit, _prompt in script.requests] == (
        [("inventory", 3000)] * len(script.inventory_calls) + [("synthesis", 10000)]
    )
    # Record ids are new in every library: one placeholder stands for each.
    rendered = _ULID.sub("_ULID", json.dumps(sorted(script.requests), ensure_ascii=False))
    assert hashlib.sha256(rendered.encode()).hexdigest() == WITHIN_BUDGET_REQUESTS


def test_the_build_estimate_charts_what_a_build_may_now_write(tmp_path):
    script = Script()
    root, repo, item, _build = _first_document(tmp_path, script)
    vault = load_vault(root)

    plan = build_build_plan(repo, vault.config, vault, subject_id=None, selections=[
        {"extraction_id": resolve_extraction_id(repo, item["source_id"]), "selected_unit_ids": []},
    ]).as_dict()

    stages = {stage["stage"]: stage for stage in plan["stages"]}
    budgets = vault.config.ingest.budgets
    assert stages["inventory"]["max_output_tokens"] == stages["inventory"]["calls"] * budgets.inventory_output_ceiling_tokens
    assert stages["synthesis"]["max_output_tokens"] == budgets.synthesis_output_tokens


def _openrouter_client():
    from learnloop.ai.providers.openrouter import OpenRouterProviderClient
    from learnloop.config import AIProviderConfig

    return OpenRouterProviderClient(
        "openrouter", AIProviderConfig(type="openrouter", model="test/model", response_format="json_object")
    )


def test_on_a_metered_route_the_retry_spends_only_what_the_estimate_left(tmp_path, monkeypatch):
    """The learner agreed to (or was not asked about) the build's estimate: the
    automatic retry is admitted against what is left of it. Here the first try
    already cost more than the whole estimate, so the retry sends nothing and
    the card asks before spending more."""

    from tests.openai_fakes import install_fake_openai

    fake = install_fake_openai(monkeypatch, "not json", "still not json",
                               usages=[{"prompt_tokens": 900, "completion_tokens": 50, "cost": 0.5}])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-credential")
    root = fresh_library(tmp_path)
    authoring = _metered(root, 0.01)
    repo, jobs = _jobs(root, fake_services(authoring, inventory_client_factory=lambda ctx: _openrouter_client()))
    item = _add(root, jobs, write_book(tmp_path))

    outcome = latest_auto_outcome(repo, item["source_id"])
    assert outcome["estimate_usd"] < 0.5
    inventory = next(job for job in repo.ingest_jobs_for_batch(outcome["build_batch_id"])
                     if job["job_type"] == "inventory")
    assert inventory["error"]["code"] == "spend_paused"
    assert inventory["error"]["details"]["reason"] == "authorization"
    # Each of the first try's workers sent its request, capped at the window's
    # ceiling, and its JSON repair; the retry was stopped before it made a
    # client or sent anything.
    assert 1 <= len(fake.instances) <= 2
    assert [len(instance.requests) for instance in fake.instances] == [2] * len(fake.instances)
    assert {instance.requests[0]["max_tokens"] for instance in fake.instances} == {6000}
    line = _line(root, repo, item)
    assert line["action"] == {"kind": "build_now", "label": "Build them"}


def test_the_plan_route_states_the_working_size_and_a_chat_route_is_capped_at_the_ceiling(monkeypatch):
    from pydantic import BaseModel

    from learnloop.ai.execution import generation_limit
    from learnloop.ai.transport import execute_structured_operation

    from tests.openai_fakes import install_fake_openai

    class Answer(BaseModel):
        ok: bool

    fake = install_fake_openai(monkeypatch, '{"ok": true}', '{"ok": true}')
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-credential")
    client = _openrouter_client()
    with generation_limit(3000):
        execute_structured_operation(client, purpose="probe", prompt="Say ok", result_model=Answer)
    with generation_limit(3000, ceiling=6000):
        execute_structured_operation(client, purpose="probe", prompt="Say ok", result_model=Answer)
    first, second = (request for instance in fake.instances for request in instance.requests)
    assert first["max_tokens"] == 3000
    assert second["max_tokens"] == 6000
    assert {key: value for key, value in first.items() if key != "max_tokens"} == {
        key: value for key, value in second.items() if key != "max_tokens"}


def test_the_plan_route_request_is_byte_identical_under_a_ceiling(tmp_path, monkeypatch):
    from learnloop.ai.chatgpt_plan.session import PlanSession
    from learnloop.ai.execution import generation_limit
    from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
    from learnloop.ai.schemas import WireModel
    from learnloop.ai.transport import execute_structured_operation
    from learnloop.config.schema import ChatGPTPlanProviderConfig

    from tests.chatgpt_plan_fakes import Reply, completed_events, fake_chatgpt, sign_in

    class Answer(WireModel):
        ok: bool

    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        client = ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(
            model="gpt-test-fast", base_url=server.base_url, timeout_seconds=10))
        bodies = []
        for ceiling in (None, 6000):
            server.replies.append(Reply(events=completed_events('{"ok": true}')))
            with generation_limit(3000, **({"ceiling": ceiling} if ceiling else {})):
                execute_structured_operation(client, purpose="probe", prompt="Say ok", result_model=Answer)
            bodies.append(server.requests[-1]["body"])
    assert bodies[0] == bodies[1]
    assert bodies[0]["input"][0]["content"].endswith("Keep the complete JSON response within 3000 output tokens.")
    assert "max_output_tokens" not in bodies[0]


def test_the_ceiling_at_its_default_leaves_every_whole_config_hash_as_it_was():
    """Whole-config dumps are hashed into identities compared later (``identity_dump``; a decision state's and a
    report's config hash): at its default the new field is not in them, so those hashes keep their recorded bytes
    (``tests/test_retired_config_identities.py``, the diagnosis journey golden). A vault that sets another ceiling
    is dumped with it, and the hashes name that setting."""

    from learnloop.ai.execution import content_key
    from learnloop.config.retired import identity_dump
    from learnloop.config.schema import LearnLoopConfig

    default = LearnLoopConfig()
    assert default.ingest.budgets.inventory_output_ceiling_tokens == 6000
    assert "inventory_output_ceiling_tokens" not in identity_dump(default)["ingest"]["budgets"]
    assert "inventory_output_ceiling_tokens" not in default.model_dump_json()

    raised = LearnLoopConfig.model_validate({"ingest": {"budgets": {"inventory_output_ceiling_tokens": 8000}}})
    assert identity_dump(raised)["ingest"]["budgets"]["inventory_output_ceiling_tokens"] == 8000
    assert content_key(identity_dump(raised)) != content_key(identity_dump(default))
