"""CLI-level gates: sealing (G5), secrets never reach a model (G2), dry runs and spend."""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest
from typer.testing import CliRunner

from learnloop.ai.execution import model_call
from learnloop.ai.routing import ROUTE_FOR_OPERATION, provider_for_task
from learnloop.ai.spend import SpendCaps, SpendLimitExceeded
from learnloop.cli import app
from learnloop.cli import project as project_cli
from learnloop.config import LearnLoopConfig
from learnloop.projects.ai_contracts import ProbeGrade, ProbeGrades
from learnloop.projects.ai_runtime import PaidCalls, PlannedCall, ProjectRoute
from learnloop.projects.experiment_store import ProjectStore
from tests.helpers import create_basic_vault
from tests.project_support import (
    TempRepo,
    clock_at,
    isolated_git,  # noqa: F401
    make_model_repo,
    project_fake,  # noqa: F401
)
from tests.test_project_redaction import AWS_KEY, ENV_SECRET, GITHUB_TOKEN, OPENAI_KEY, _hunk_header_secret_repo

runner = CliRunner()


@pytest.fixture
def cli(monkeypatch, tmp_path):
    paths = create_basic_vault(tmp_path / "vault")

    def run(args, day=0.0, input_text=None, expect=0):
        monkeypatch.setattr(project_cli, "_clock", lambda: clock_at(day))
        result = runner.invoke(app, ["project", *args, "--vault", str(paths.root)], input=input_text)
        assert result.exit_code == expect, result.output
        return result.output

    run.vault = paths.root
    return run


def test_no_command_renders_a_sealed_question(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    store = ProjectStore.existing(cli.vault)
    questions = [probe["question"] for probe in store.all_probes()]
    references = [probe["reference_answer"] for probe in store.all_probes()]
    assert questions
    selected = [probe for probe in store.all_probes() if probe["selected"]]
    outputs = []
    for json_flag in ([], ["--json"]):
        outputs += [
            cli(["status", *json_flag], day=6),
            cli(["status", "--disclosure", "--diffs", *json_flag], day=6),
            cli(["report", *json_flag], day=6),
            cli(["probes", "--list", *json_flag], day=6),
            cli(["sweep", *json_flag], day=6),
            cli(["sweep", "--dry-run", *json_flag], day=6),
            cli(["probes", "--dry-run", *json_flag], day=6),
            cli(["answer", selected[0]["id"], "--text", "x", *json_flag], day=6, expect=1),
            cli(["answer", selected[0]["id"], "--skip", "--dry-run", *json_flag], day=6, expect=1),
        ]
    outputs.append(cli(["probes"], day=6, input_text="relu\n\n"))
    everything = "\n".join(outputs)
    for text in questions + references:
        assert text not in everything
    # The sealing message is identical for sealed and unknown probes.
    unknown = cli(["answer", "01NOSUCHPROBE0000000000000", "--skip"], day=6, expect=1)
    sealed = cli(["answer", selected[0]["id"], "--skip"], day=6, expect=1)
    assert unknown.replace("01NOSUCHPROBE0000000000000", "ID") == sealed.replace(selected[0]["id"], "ID")
    # On the due date the question is served.
    assert selected[0]["question"] in cli(["probes", "--list"], day=7)


def test_end_to_end_answering_and_reveal(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    session = cli(["probes"], day=8, input_text="It applies relu after scaling.\n/looked\n\n/dk\n")
    assert "Grade: correct (0.90)" in session
    assert "Reference:" in session and "model.py" in session
    store = ProjectStore.existing(cli.vault)
    responses = store.responses()
    assert [r["response_kind"] for r in responses] == ["answer", "dont_know"]
    assert responses[0]["declaration"] == "looked"
    report = json.loads(cli(["report", "--json"], day=9))
    assert report["answers"]["by_kind"] == {"answer": 1, "dont_know": 1}
    assert report["answers"]["accuracy_assisted"]["mean"] == 0.9
    assert report["capture"]["by_agent"] == {"claude_code": 1}


def test_quitting_leaves_questions_due(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    assert "Stopped" in cli(["probes"], day=8, input_text="/quit\n")
    assert ProjectStore.existing(cli.vault).responses() == []


def test_generation_waits_for_a_due_diff_when_sweep_was_capture_only(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep", "--capture-only"])
    assert project_fake.calls == {}
    assert "No questions are due" in cli(["probes"], day=3)
    assert project_fake.calls == {}  # not due yet, so nothing is generated
    listed = cli(["probes", "--list", "--json"], day=7)
    assert project_fake.calls["authoring"] == 1
    assert len(json.loads(listed)["due"]) == 2


def test_sweep_dry_run_makes_no_calls_and_no_writes(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    store = ProjectStore.existing(cli.vault)
    receipts_before = len(store.receipts())
    payload = json.loads(cli(["sweep", "--dry-run", "--json"]))
    assert payload["status"] == "dry_run" and payload["sweep"] is None
    estimate = payload["generation"]["estimate"]
    assert estimate["calls"] == 3 and estimate["total_tokens"] > 0
    assert payload["generation"]["routes"]["authoring"]["subscription"] is True
    assert estimate["subscription_cost_label"] == "estimated_only" and estimate["subscription_estimated_usd"] > 0
    assert project_fake.requests == [] and store.all_probes() == [] and len(store.receipts()) == receipts_before


def test_secrets_never_reach_a_model(isolated_git, project_fake, cli, tmp_path):
    repo = TempRepo(tmp_path / "repo")
    repo.write("app.py", "def main():\n    return 0\n")
    repo.commit("init", trailer=None)
    repo.write(".env", f"DATABASE_PASSWORD={ENV_SECRET}\n")
    repo.write(
        "app.py",
        "def main():\n"
        f"    client = make_client(api_key=\"{OPENAI_KEY}\")\n"
        f"    aws = '{AWS_KEY}'\n"
        "    total = 0\n    for step in range(3):\n        total += step\n    return total\n",
    )
    repo.commit(f"Wire the client\n\nUses token {GITHUB_TOKEN} for now.")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    cli(["probes"], day=8, input_text="It sums the steps.\n\n/skip\n")
    prompts = "\n".join(prompt for _purpose, prompt in project_fake.requests)
    assert {purpose for purpose, _ in project_fake.requests} == {
        "project_probe_authoring", "project_closed_book_check", "project_probe_grading",
    }
    for secret in (AWS_KEY, OPENAI_KEY, GITHUB_TOKEN, ENV_SECRET, "DATABASE_PASSWORD"):
        assert secret not in prompts
    assert ".env" not in prompts


def test_hunk_header_secrets_never_reach_a_model(isolated_git, project_fake, cli, tmp_path):
    repo = _hunk_header_secret_repo(tmp_path)
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    assert {purpose for purpose, _ in project_fake.requests} >= {"project_probe_authoring"}
    prompts = "\n".join(prompt for _purpose, prompt in project_fake.requests)
    assert OPENAI_KEY not in prompts and "@@ -" in prompts


def test_metered_routes_fail_closed_without_a_price(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    caps = SpendCaps(max_candidates=10, max_pairs=0, max_retries=1, max_calls=5, max_total_tokens=10_000, max_estimated_usd=1.0)
    metered = {"authoring": {"subscription": False}}
    subscription = {"authoring": {"subscription": True}}
    plan = [PlannedCall("authoring", 4_000, 4_000, candidates=6)]
    with pytest.raises(SpendLimitExceeded, match="Unknown price"):
        PaidCalls(store, caps=caps, run_id="r").plan(plan, metered)
    priced = PaidCalls(store, caps=caps, run_id="r", price_per_million=5.0).plan(plan, metered)
    assert priced["metered_estimated_usd"] == pytest.approx(0.04)
    # Metered token caps bind; the subscription has no token or dollar cap...
    with pytest.raises(SpendLimitExceeded, match="total_tokens"):
        PaidCalls(store, caps=caps, run_id="r", price_per_million=5.0).plan([PlannedCall("authoring", 6_000, 6_000)], metered)
    huge = [PlannedCall("authoring", 400_000, 400_000, candidates=1)]
    assert PaidCalls(store, caps=caps, run_id="r").plan(huge, subscription)["metered_tokens"] == 0
    # ...but call and candidate caps still stop a runaway loop.
    with pytest.raises(SpendLimitExceeded, match="calls"):
        PaidCalls(store, caps=caps, run_id="r").plan([PlannedCall("authoring", 1, 1)] * 6, subscription)
    with pytest.raises(SpendLimitExceeded, match="candidates"):
        PaidCalls(store, caps=caps, run_id="r").plan([PlannedCall("authoring", 1, 1, candidates=11)], subscription)


class _RetryingClient:
    """Emits two physical requests inside one logical call, like a provider retry."""

    provider_name = "metered"
    provider_type = "openrouter"
    model = "m"

    def supports(self, capability):
        return capability == "structured_completion"

    def complete(self, request):
        for _attempt in range(2):
            with model_call(self, purpose="chat_request", prompt="p") as receipt:
                receipt.update(input_tokens=10, output_tokens=5)
        return ProbeGrades(grades=[ProbeGrade(id="a1", verdict="correct", score=1.0, feedback="")])


@contextmanager
def _route(subscription):
    yield ProjectRoute(role="grading", task="grading", provider_name="metered", provider_type="openrouter",
                       model="m", subscription=subscription, ready=True, message=None, client=_RetryingClient())


def test_hidden_retries_are_admitted_only_against_max_retries(tmp_path):
    store = ProjectStore.for_vault(tmp_path)

    def caps(retries):
        return SpendCaps(max_candidates=10, max_pairs=0, max_retries=retries, max_calls=10, max_total_tokens=10_000, max_estimated_usd=1.0)

    with _route(subscription=False) as route:
        paid = PaidCalls(store, caps=caps(1), run_id="r", price_per_million=1.0)
        paid.call(route, purpose="project_probe_grading", prompt="x", result_model=ProbeGrades, output_tokens=10)
        assert paid.summary()["retries"] == 1 and paid.summary()["admitted_calls"] == 2
        strict = PaidCalls(store, caps=caps(0), run_id="r2", price_per_million=1.0)
        with pytest.raises(SpendLimitExceeded):
            strict.call(route, purpose="project_probe_grading", prompt="x", result_model=ProbeGrades, output_tokens=10)
    with _route(subscription=True) as route:
        unbounded = PaidCalls(store, caps=caps(0), run_id="r3")
        unbounded.call(route, purpose="project_probe_grading", prompt="x", result_model=ProbeGrades, output_tokens=10)
        summary = unbounded.summary()
        assert summary["retries"] == 0 and summary["subscription_tokens"] == 30
        receipt = [row for row in store.receipts() if row["owner_id"] == "r3" and row["parent_call_id"] is None][0]
        assert receipt["cost_label"] == "estimated_only"
        assert receipt["estimated_usd"] == pytest.approx(30 * 10.0 / 1_000_000)


def test_project_route_defaults_to_grading_then_active():
    config = LearnLoopConfig.model_validate({"ai": {"active_provider": "codex"}})
    config.ai.routing.grading = None
    assert provider_for_task(config, "project", allow_env=False).provider_name == "codex"
    config.ai.routing.grading = "codex_low"
    assert provider_for_task(config, "project", allow_env=False).provider_name == "codex_low"
    config.ai.routing.project = "codex_medium"
    assert provider_for_task(config, "project", allow_env=False).provider_name == "codex_medium"
    assert ROUTE_FOR_OPERATION["project_probe_authoring"] == "project"
    assert ROUTE_FOR_OPERATION["project_closed_book_check"] == "project"
    assert ROUTE_FOR_OPERATION["project_probe_grading"] == "grading"


def test_accept_and_provenance_commands(isolated_git, project_fake, cli, tmp_path):
    repo = TempRepo(tmp_path / "repo")
    repo.write("a.py", "def f():\n    return 1\n")
    repo.commit("init", trailer=None)
    cli(["enroll", str(repo.path)])
    repo.write("a.py", "def f():\n    x = 1\n    y = 2\n    z = 3\n    return x + y + z\n")
    accepted = json.loads(cli(["accept", "--repo", str(repo.path), "--agent", "codex", "--json"]))
    diff_id = accepted["results"][0]["diff_id"]
    assert accepted["results"][0]["status"] == "captured"
    cli(["provenance", diff_id, "--accept-style", "per_hunk", "--usage", "we_iterated"])
    cli(["provenance", diff_id, "--accept-style", "sideways"], expect=1)
    store = ProjectStore.existing(cli.vault)
    assert store.latest_provenance()[diff_id] == {"accept_style": "per_hunk", "usage_tap": "we_iterated"}
    assert store.diff(diff_id)["capture_timing"] == "pre_commit"


def test_declaration_tokens_are_whole_words(monkeypatch):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("I aimed /aim at relu\n\n"))
    assert project_cli._read_answer() == ("I aimed /aim at relu", "answer", "unassisted")
    monkeypatch.setattr("sys.stdin", io.StringIO("it is relu /ai\n\n"))
    assert project_cli._read_answer() == ("it is relu", "answer", "used_ai")
    monkeypatch.setattr("sys.stdin", io.StringIO("/dk /looked\n\n"))
    assert project_cli._read_answer() == (None, "dont_know", "looked")
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert project_cli._read_answer()[1] == "quit"


class _BudgetRecorder:
    provider_name = "recorder"
    provider_type = "openrouter"
    model = "m"

    def __init__(self):
        self.budgets = []

    def supports(self, capability):
        return capability == "structured_completion"

    def complete(self, request):
        self.budgets.append(request.output_budget_tokens)
        return ProbeGrades(grades=[ProbeGrade(id="a1", verdict="correct", score=1.0, feedback="")])


def _grading_route(client, *, subscription):
    return ProjectRoute(role="grading", task="grading", provider_name="r", provider_type="openrouter",
                        model="m", subscription=subscription, ready=True, message=None, client=client)


def test_metered_calls_carry_their_admitted_output_limit(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    caps = SpendCaps(max_candidates=10, max_pairs=0, max_retries=1, max_calls=10, max_total_tokens=10_000, max_estimated_usd=1.0)
    recorder = _BudgetRecorder()
    metered = PaidCalls(store, caps=caps, run_id="m", price_per_million=1.0)
    metered.call(_grading_route(recorder, subscription=False), purpose="project_probe_grading", prompt="x",
                 result_model=ProbeGrades, output_tokens=32)
    # The subscription keeps no output restraint (Slice A plan §5 rule 6).
    PaidCalls(store, caps=caps, run_id="s").call(_grading_route(recorder, subscription=True), purpose="project_probe_grading",
                                                  prompt="x", result_model=ProbeGrades, output_tokens=32)
    assert recorder.budgets == [32, None]


def test_metered_output_limit_reaches_the_provider_request_and_its_repair(tmp_path, monkeypatch):
    from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
    from learnloop.config import AIProviderConfig
    from tests.openai_fakes import install_fake_openai

    monkeypatch.setenv("FAKE_ROUTER_KEY", "test-key")
    valid = json.dumps({"grades": [{"id": "a1", "verdict": "correct", "score": 1.0, "feedback": ""}]})
    module = install_fake_openai(
        monkeypatch, "not json", valid,
        usages=[{"prompt_tokens": 10, "completion_tokens": 12}, {"prompt_tokens": 10, "completion_tokens": 5}],
    )
    client = OpenAIChatProviderClient("router", AIProviderConfig(
        type="openai_chat", base_url="https://router.invalid/v1", api_key_env="FAKE_ROUTER_KEY",
        model="m", response_format="json_object", max_tokens=8192,
    ))
    store = ProjectStore.for_vault(tmp_path)
    caps = SpendCaps(max_candidates=10, max_pairs=0, max_retries=1, max_calls=10, max_total_tokens=10_000, max_estimated_usd=1.0)
    PaidCalls(store, caps=caps, run_id="m", price_per_million=1.0).call(
        _grading_route(client, subscription=False), purpose="project_probe_grading", prompt="x",
        result_model=ProbeGrades, output_tokens=32,
    )
    requests = module.instances[0].requests
    assert [request["max_tokens"] for request in requests] == [32, 20]
