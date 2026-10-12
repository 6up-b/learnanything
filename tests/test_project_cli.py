"""CLI-level gates: sealing (G5), secrets never reach a model (G2), dry runs and spend."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

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
    MODEL_PY_RELU,
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
    assert payload["status"] == "dry_run" and payload["sweep"]["dry_run"] is True
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
        return capability in {"structured_completion", "tool_free"}

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
        return capability in {"structured_completion", "tool_free"}

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


def _captured_route_configs(monkeypatch, config, roles):
    from learnloop.projects import ai_runtime

    seen = {}

    class _Resolved:
        ready = True
        client = None
        runtime = type("R", (), {"model": "m", "message": None})()

        def __init__(self, name):
            self.provider_name = name

    def fake_ready(workdir, effective, task):
        name = provider_for_task(effective, task).provider_name
        seen[task] = effective.ai.providers[name].reasoning_effort
        return _Resolved(name)

    monkeypatch.setattr(ai_runtime, "ready_client_for_task", fake_ready)
    with ai_runtime.project_routes(Path("."), config, roles) as routes:
        return seen, routes


def test_project_grading_runs_at_high_effort_by_default(monkeypatch, tmp_path):
    config = LearnLoopConfig()
    assert config.ai.routing.grading == "codex_low"
    seen, routes = _captured_route_configs(monkeypatch, config, ("authoring", "grading"))
    assert seen["grading"] == "high"
    assert seen["project"] == "low"  # authoring keeps its route's own effort


def _turn_effort(monkeypatch, tmp_path, config, role):
    from learnloop.ai.providers.codex import CodexSDKProviderClient
    from learnloop.projects.ai_runtime import config_for_role
    from tests.project_support import install_fake_codex_sdk

    captured = install_fake_codex_sdk(monkeypatch)
    effective = config_for_role(config, role)
    name = provider_for_task(effective, "grading" if role == "grading" else "project").provider_name
    client = CodexSDKProviderClient(name, effective.ai.providers[name], tmp_path)
    client._run_structured("p", {"type": "object"}, purpose="project_probe_grading")
    return captured["turns"][-1]["effort"].value


def test_the_effective_grading_request_carries_high_effort(monkeypatch, tmp_path):
    config = LearnLoopConfig()
    assert _turn_effort(monkeypatch, tmp_path, config, "grading") == "high"
    assert _turn_effort(monkeypatch, tmp_path, config, "authoring") == "low"
    config.project.grading_reasoning_effort = ""  # the owner keeps the route's own effort
    assert _turn_effort(monkeypatch, tmp_path, config, "grading") == "low"
    config.project.grading_reasoning_effort = "medium"
    assert _turn_effort(monkeypatch, tmp_path, config, "grading") == "medium"


def test_grading_effort_leaves_chat_profiles_without_an_effort_alone():
    from learnloop.projects.ai_runtime import config_for_role, describe_routes

    config = LearnLoopConfig()
    config.ai.routing.grading = "openrouter"
    assert config_for_role(config, "grading").ai.providers["openrouter"].reasoning_effort is None
    config.ai.routing.grading = "deepseek_pro"
    config.project.grading_reasoning_effort = "medium"
    assert config_for_role(config, "grading").ai.providers["deepseek_pro"].reasoning_effort == "medium"
    assert config.ai.providers["deepseek_pro"].reasoning_effort == "high"  # the shared profile is untouched
    assert describe_routes(config)["grading"]["reasoning_effort"] == "medium"


def test_probes_spends_one_budget_across_generation_and_grading(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep", "--capture-only"])
    output = cli(["probes", "--max-calls", "3"], day=8, input_text="It applies relu.\n\nIt scales x.\n\n")
    # Generation needs all three calls (authoring, closed-book, its grading);
    # the two answers are saved and their grading is deferred, not re-budgeted.
    assert project_fake.calls == {"authoring": 1, "closed_book": 1, "grading": 1}
    assert "Grading deferred" in output
    store = ProjectStore.existing(cli.vault)
    assert [row["grade_status"] for row in store.responses()] == ["pending", "pending"]


def test_probes_dry_run_estimates_generation_and_the_grading_it_enables(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep", "--capture-only"])
    payload = json.loads(cli(["probes", "--dry-run", "--json"], day=8))
    # 3 generation calls, then one grading call for each of the 2 questions it will serve.
    assert payload["estimate"]["calls"] == 5
    assert payload["questions_to_serve"] == 2
    assert project_fake.requests == []
    capped = json.loads(cli(["probes", "--dry-run", "--json", "--max-calls", "4"], day=8))
    assert capped["estimate"]["status"] == "over_budget"


def test_failed_grades_can_be_retried_with_spend_controls(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])
    store = ProjectStore.existing(cli.vault)
    probe_id = next(probe["id"] for probe in store.all_probes() if probe["selected"])
    project_fake.fail_grading = True
    cli(["answer", probe_id, "--text", "It applies relu after scaling."], day=8)
    for _ in range(2):
        cli(["grade"], day=8)
    (response,) = store.responses()
    assert response["grade_status"] == "failed"
    project_fake.fail_grading = False
    assert json.loads(cli(["grade", "--json"], day=9))["status"] == "nothing_to_grade"
    receipts = len(store.receipts())
    dry = json.loads(cli(["grade", "--retry-failed", "--dry-run", "--json"], day=9))
    assert dry["status"] == "dry_run" and dry["estimate"]["calls"] == 1
    assert store.response(response["id"])["grade_status"] == "failed" and len(store.receipts()) == receipts
    assert json.loads(cli(["grade", "--retry-failed", "--max-calls", "0", "--json"], day=9))["status"] == "over_budget"
    assert store.response(response["id"])["grade_status"] == "failed"  # nothing reset when nothing can run
    retried = json.loads(cli(["grade", "--retry-failed", "--json"], day=9))
    assert retried["status"] == "complete"
    graded = store.response(response["id"])
    assert graded["grade_status"] == "graded" and graded["answer"] == "It applies relu after scaling."
    assert len(store.receipts()) > receipts  # the failed attempts' receipts are kept


def test_failed_generation_can_be_retried_without_re_authoring(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    project_fake.fail_closed_book = True
    for _ in range(3):
        cli(["sweep"])
    store = ProjectStore.existing(cli.vault)
    (diff,) = store.diffs()
    assert diff["probe_status"] == "failed" and project_fake.calls["authoring"] == 1
    project_fake.fail_closed_book = False
    assert json.loads(cli(["sweep", "--json"]))["generation"]["status"] == "nothing_to_generate"
    dry = json.loads(cli(["sweep", "--retry-failed", "--dry-run", "--json"]))
    assert dry["generation"]["estimate"]["calls"] == 2  # closed-book and its grading; authoring is kept
    assert store.diff(diff["id"])["probe_status"] == "failed"
    cli(["sweep", "--retry-failed"])
    assert store.diff(diff["id"])["probe_status"] == "generated"
    assert project_fake.calls["authoring"] == 1


def _store_files(vault):
    return sorted(str(path.relative_to(vault)) for path in vault.rglob("*") if path.is_file() and "-wal" not in path.name and "-shm" not in path.name)


def test_sweep_dry_run_includes_commits_the_real_sweep_would_capture(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    cli(["enroll", str(repo.path)])
    cli(["sweep"])  # the enrollment-time commit is captured and generated
    store = ProjectStore.existing(cli.vault)
    rescale = "".join(f"y = y * {factor}\n        " for factor in range(2, 8))
    repo.write("model.py", MODEL_PY_RELU.replace("return torch.relu(y)", rescale + "return torch.relu(y)"))
    repo.commit("Rescale before the relu\n\nSo the GRU sees a centred input.")
    before = (len(store.diffs()), len(store.receipts()), _store_files(cli.vault))
    payload = json.loads(cli(["sweep", "--dry-run", "--json"], day=1))
    assert payload["generation"]["prospective_captures"] == 1
    assert payload["generation"]["estimate"]["calls"] == 3
    assert (len(store.diffs()), len(store.receipts()), _store_files(cli.vault)) == before
    calls = sum(project_fake.calls.values())
    cli(["sweep"], day=1)
    assert sum(project_fake.calls.values()) - calls == 3  # what the dry run estimated


def test_sweep_dry_run_includes_queued_hook_entries(isolated_git, project_fake, cli, tmp_path):
    repo = make_model_repo(tmp_path / "repo")
    sha = repo.git("rev-parse", "HEAD").strip()
    repo.git("checkout", "-q", "--detach", "HEAD~1")
    repo.git("branch", "-q", "-D", "main")  # only the hook's entry can find it now
    cli(["enroll", str(repo.path)])
    store = ProjectStore.existing(cli.vault)
    repo_id = store.repos()[0]["id"]
    (cli.vault / "projects" / "pending.jsonl").write_text(json.dumps({"repo_id": repo_id, "sha": sha, "at": "x"}) + "\n")
    payload = json.loads(cli(["sweep", "--dry-run", "--json"]))
    assert payload["generation"]["prospective_captures"] == 1 and payload["generation"]["estimate"]["calls"] == 3
    assert store.diffs() == [] and store.pending_commits() == []
