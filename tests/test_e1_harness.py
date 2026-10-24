"""E1 end to end with fakes only: a fake E0 run (the real E0 code, fake
clients) -> import -> replay verified against E0's own results -> plan ->
the local stage (the worker in-process with a fake model) -> supplementary
labels under E1's own ledger -> score -> report. No network, no torch, no
download, no key."""
from __future__ import annotations

import json
import socket

import pytest

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins
from tests.e0_fakes import FAKE_KEYS, FakeRoleClient, build_e0_vault
from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below
from tests.e1_fakes import FakeV2Model, InProcessLauncher, e1_respond

pytestmark = pytest.mark.usefixtures("verified_prices")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E1 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _factories(clients):
    from learnloop.experiments.contextual_embeddings import live
    from tests.e0_fakes import FakeEmbeddingTransport, qwen_bag_of_words

    qwen = qwen_bag_of_words(4096)

    def role_client(name):
        clients.append(FakeRoleClient(name))
        return clients[-1]

    dims = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}
    return live.LiveFactories(transport=FakeEmbeddingTransport(dims=dims, int8_models=frozenset(
        {"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"})), qwen=lambda _config: (lambda: qwen),
        role_clients=role_client, system_clients={"embedder": qwen})


@pytest.fixture
def e0_run(tmp_path, monkeypatch):
    """A finished fake E0 run through E0's own ``run_live``."""

    from learnloop.experiments.contextual_embeddings import live
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    for name, value in FAKE_KEYS.items():
        monkeypatch.setenv(name, value)
    run_dir = tmp_path / "fixtures-local" / "contextual-embeddings" / "runs"
    plan = dry_run([paths.root], environ=FAKE_KEYS)
    clients: list = []
    result = live.run_live([paths.root], plan=plan, run_dir=run_dir, key_envs={}, factories=_factories(clients))
    assert result["vaults"][paths.root.name].get("retrieval"), result
    for name in FAKE_KEYS:
        monkeypatch.delenv(name, raising=False)
    return {"run": run_dir / plan["run_id"], "vaults": paths.root.parent, "label": paths.root.name,
            "plan": plan, "root": tmp_path / "fixtures-local"}


def _import(e0_run):
    from learnloop.experiments.contextual_embeddings.e1.replay import ImportLayout, import_e0

    destination = e0_run["root"] / "contextual-embeddings" / "e1" / "imports" / e0_run["run"].name
    import_e0(e0_run["run"], e0_run["vaults"], destination)
    return ImportLayout(destination)


def test_the_replay_reproduces_e0_without_any_call_and_the_plan_is_frozen(e0_run):
    from learnloop.experiments.contextual_embeddings.e1.run import dry_run

    layout = _import(e0_run)
    plan = dry_run(import_dir=layout.root, environ={})
    verification = plan["replay"]["verification"][e0_run["label"]]
    assert verification["ok"], verification
    assert verification["compared"] > 50 and set(verification["arms"]) == set(e1_pins.E0_REPRESENTATION_ARMS)
    assert plan["status"] == "frozen" and plan["plan_id"].startswith("e1_") and plan["e0_run_id_rebuilt"]
    assert plan["checks"]["network_calls"] == 0 and plan["checks"]["torch_imported"] is False
    assert plan["keys"] == {"ANTHROPIC_API_KEY": "absent", "VOYAGE_API_KEY": "absent"}
    assert plan["gpu"]["fits"] and plan["gpu"]["cap_hours"] == 4.0
    assert plan["budget"]["cap_usd"] == 5.0 and plan["money"]["expected_usd"] > 0
    # The frozen plan prices labels from E0's own measured novelty, not the prior.
    assert plan["vaults"][e0_run["label"]]["novelty"]["questions"] > 0
    assert plan["money"]["by_vault"][e0_run["label"]]["expected"]["basis"] == "measured_e0_novelty"
    assert plan["money"]["worst_case_usd"] >= plan["money"]["expected_usd"]
    # The same import always rebuilds to the same plan id.
    assert dry_run(import_dir=layout.root, environ={})["plan_id"] == plan["plan_id"]


def test_a_wrong_label_pool_misses_e0s_checkpoints_and_the_replay_is_unverified(e0_run):
    from learnloop.experiments.contextual_embeddings.e1.run import dry_run

    layout = _import(e0_run)
    pools_path = layout.root / "label_pools" / f"{e0_run['label']}.json"
    pools = json.loads(pools_path.read_text())
    first = sorted(pools)[0]
    pools[first] = pools[first][1:]  # one unit dropped from one question's pool
    pools_path.write_text(json.dumps(pools))
    plan = dry_run(import_dir=layout.root, environ={})
    assert plan["status"] == "provisional"
    assert plan["import_problems"]  # the import digest no longer matches either


def test_an_unfinished_e0_run_is_not_imported_and_the_manifest_plan_is_provisional(e0_run):
    from learnloop.experiments.contextual_embeddings.e1.replay import ImportRefused, import_e0
    from learnloop.experiments.contextual_embeddings.e1.run import dry_run

    results = e0_run["run"] / e0_run["label"] / "results.json"
    saved = results.read_bytes()
    results.unlink()
    with pytest.raises(ImportRefused, match="not finished"):
        import_e0(e0_run["run"], e0_run["vaults"], e0_run["root"] / "e1-import")
    plan = dry_run(e0_run_dir=e0_run["run"], environ={})
    assert plan["status"] == "provisional" and plan["checks"]["network_calls"] == 0
    assert plan["e0"]["complete"] is False and plan["vaults"][e0_run["label"]]["units"] > 0
    results.write_bytes(saved)


def test_the_whole_pilot_with_fakes(e0_run, tmp_path, monkeypatch):
    from learnloop.experiments.contextual_embeddings.e1 import run as e1
    from learnloop.experiments.contextual_embeddings.e1.ledger import ledger_dir
    from learnloop.experiments.contextual_embeddings.e1.report import render

    layout = _import(e0_run)
    plan = e1.dry_run(import_dir=layout.root, environ={})
    model = FakeV2Model()
    launcher = InProcessLauncher(model)
    local = e1.run_local(plan, layout, model_dir=tmp_path / "model", launcher=launcher)
    assert local["status"] == "complete" and local["smoke"]["all_ok"], local
    assert local["stored"]["documents_stored"] == local["planned"]["documents"] > 0
    assert local["stored"]["queries_stored"] == local["planned"]["queries"] > 0
    assert not (layout.root.parent.parent / "runs" / plan["plan_id"] / "local" / "01" / "job.json").exists()
    # Resume: nothing left to encode, no second worker.
    assert e1.run_local(plan, layout, model_dir=tmp_path / "model", launcher=launcher)["status"] == \
        "nothing_to_encode"
    assert len(launcher.jobs) == 1
    # The fake corpus is so small that E0's pool already holds every unit; to
    # exercise the paid path, the v2 arms' first ranks count as new here.
    from learnloop.experiments.contextual_embeddings.e1 import supplement

    def first_ranks(question, labels, rankings, depth=10):
        if labels is None or labels.unresolved:
            return []
        return list(dict.fromkeys(unit for arm in sorted(rankings) for unit in rankings[arm].get(
            question.query_id, [])[:2]))[:3]

    monkeypatch.setattr(supplement, "new_candidates", first_ranks)
    # The labels stage: exact counts first, without network or spend.
    priced = e1.run_labels(plan, layout, dry_run_only=True)
    assert priced["status"] == "dry_run" and priced["counts"][e0_run["label"]]["new_candidates"] > 0
    with pytest.raises(e1.PlanRefused, match="authorized"):
        e1.run_labels(plan, layout)
    clients: list = []

    def client(profile):
        clients.append(FakeRoleClient(profile, respond=e1_respond))
        return clients[-1]

    labelled = e1.run_labels(plan, layout, authorized=True, client_factory=client, environ={})
    copy = labelled["copies"][e0_run["label"]]
    assert copy["counts"]["new_candidates"] > 0 and copy["counts"]["stopped"] is None
    assert labelled["ledger"]["cap_usd"] == 5.0 and 0 < labelled["ledger"]["committed_usd"] <= 5.0
    assert {request["purpose"] for item in clients for request in item.requests} <= {
        "e0_label_a", "e0_label_b", "e0_adjudicator"}
    # E1's ledger lives apart from E0's, which it never sealed or carried.
    e0_ledgers = sorted((e0_run["root"] / "contextual-embeddings" / "ledger").glob("e0_*.ledger"))
    assert e0_ledgers and all("superseded" not in json.loads(path.read_text()) for path in e0_ledgers)
    assert sorted(path.name for path in ledger_dir(layout.root).glob("*.ledger")) == [f"{plan['plan_id']}.ledger"]
    results = e1.score(plan, layout)
    assert results["decision"]["e1"] in ("retain_candidate", "non_inferior_cost_latency_only", "stop", "no_verdict")
    assert results["decision"]["production_adoption"] == "not_authorized_by_e1"
    assert results["v2_selected_on_primary_development"] in e1_pins.V2_ARMS
    item = results["copies"][e0_run["label"]]
    assert item["replay_ok"] and {"V2_grouped", "V2_singleton", "R4_grouped"} <= set(item["retrieval"])
    assert item["supplement"]["counts"]["new_candidates"] == copy["counts"]["new_candidates"]
    assert results["gpu_meter"]["processes"] == 1 and results["local"]["smoke"]["all_ok"]
    report = render(results)
    assert "Decision:" in report and "not_authorized_by_e1" in report
    text = json.dumps(results)
    for unit in e0_run["plan"]["corpus"][0]["sources"]:
        assert "Linear Algebra Book" not in text
    assert "vectors" not in results and "Exam question" not in text


def test_a_provisional_plan_runs_no_stage(e0_run, tmp_path):
    from learnloop.experiments.contextual_embeddings.e1 import run as e1

    layout = _import(e0_run)
    plan = e1.dry_run(e0_run_dir=e0_run["run"], environ={})
    assert plan["status"] == "provisional"
    for stage in (lambda: e1.run_local(plan, layout, model_dir=tmp_path, launcher=InProcessLauncher(FakeV2Model())),
                  lambda: e1.run_labels(plan, layout, authorized=True), lambda: e1.score(plan, layout)):
        with pytest.raises(e1.PlanRefused, match="provisional"):
            stage()


def test_the_e1_ledger_is_cumulative_across_e1_plans_and_never_touches_e0(tmp_path):
    from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, Request
    from learnloop.experiments.contextual_embeddings.e1.ledger import authorized_ledger

    anchor = tmp_path / "fixtures-local" / "contextual-embeddings" / "e1"
    e0_ledger = tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger" / "e0_1111111111111111.ledger"
    e0_ledger.parent.mkdir(parents=True)
    e0_ledger.write_text(json.dumps({"entries": {}}))
    first = authorized_ledger(anchor, "e1_aaaaaaaaaaaaaaaa")
    with first.admit(Request(category="labels_audits", provider="anthropic", route="claude-sonnet-5-5",
                             purpose="label_a", estimated_usd=3.0)) as charge:
        charge.settle(actual_usd=3.0)
    with pytest.raises(PermissionError):
        authorized_ledger(anchor, "e1_bbbbbbbbbbbbbbbb")
    second = authorized_ledger(anchor, "e1_bbbbbbbbbbbbbbbb", new_authorization="re-plan")
    with pytest.raises(E0BudgetExceeded):
        second.reserve(Request(category="labels_audits", provider="anthropic", route="claude-sonnet-5-5",
                               purpose="label_a", estimated_usd=1.9))
    assert json.loads(e0_ledger.read_text()) == {"entries": {}}


def test_the_scoped_launcher_caps_memory_and_passes_no_key(tmp_path, monkeypatch):
    from learnloop.experiments.contextual_embeddings.e1.gpu_meter import GpuMeter
    from learnloop.experiments.contextual_embeddings.e1.local import ScopedLauncher

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real")
    seen = {}

    class Process:
        returncode = 0

        def poll(self):
            return 0

        def wait(self):
            return 0

    def popen(command, env, **_kwargs):
        seen.update(command=command, env=env)
        (tmp_path / "fixtures-local" / "w" / "01" / "out.json").write_text(json.dumps({"status": "complete"}))
        return Process()

    workdir = tmp_path / "fixtures-local" / "w" / "01"
    launcher = ScopedLauncher(tmp_path / "env" / "bin" / "python", popen=popen)
    output = launcher({"limits": {}}, workdir, meter=GpuMeter(tmp_path / "meter"), plan_id="e1_aaaaaaaaaaaaaaaa")
    command = seen["command"]
    assert command[:4] == ["systemd-run", "--user", "--scope", "--quiet"]
    assert f"MemoryMax={e1_pins.SCOPE_MEMORY_MAX}" in command and f"MemorySwapMax={e1_pins.SCOPE_SWAP_MAX}" in command
    assert command[command.index("--") + 1:][:2] == [str(tmp_path / "env" / "bin" / "python"), "-I"]
    assert "ANTHROPIC_API_KEY" not in seen["env"] and seen["env"]["HOME"].startswith(str(workdir))
    assert output["status"] == "complete" and output["supervised"]["status"] == "exited"
    job = json.loads((workdir / "job.json").read_text())
    assert job["limits"]["deadline_unix"] > 0


def test_the_cli_plans_from_e0_manifests_offline(e0_run, tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app

    out = tmp_path / "plan.json"
    result = CliRunner().invoke(app, ["experiments", "e1", "plan", "--e0-run", str(e0_run["run"]), "--out", str(out)])
    assert result.exit_code == 0, result.output
    plan = json.loads(out.read_text())
    assert plan["status"] == "provisional" and plan["checks"]["network_calls"] == 0
    assert "GPU: expected" in result.output


def test_preflight_reports_every_check_and_is_not_ready_without_the_model(e0_run, tmp_path):
    from learnloop.experiments.contextual_embeddings.e1 import run as e1

    layout = _import(e0_run)
    plan = e1.dry_run(import_dir=layout.root, environ={})
    healthy = {"ok": True, "problems": [], "host_available_gib": 24.0}
    report = e1.preflight(plan, layout, model_dir=tmp_path / "no-model", env_python=tmp_path / "python",
                          resources=lambda: healthy, versions=lambda _python: {"ok": True})
    checks = report["checks"]
    assert not report["ready"] and not checks["model_files"]["ok"]
    assert checks["plan"]["ok"] and checks["import"]["ok"] and checks["replay"]["ok"] and checks["gpu_meter"]["ok"]
    assert checks["environment"] == {"ok": False, "error": "no interpreter at --env-python"}


def test_the_separate_environment_must_carry_the_pinned_versions(tmp_path):
    from types import SimpleNamespace

    from learnloop.experiments.contextual_embeddings.e1.run import environment_versions

    wanted = dict(item.split("==") for item in e1_pins.LOCAL_REQUIREMENTS)
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs["env"]))
        return SimpleNamespace(returncode=0, stdout=json.dumps({**wanted, "qwen3_5_model": True}) + "\n")

    assert environment_versions(tmp_path / "python", run=run)["ok"]
    assert calls[0][0][1] == "-I" and set(calls[0][1]) == {"PATH", "HOME"}

    def old(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps({**wanted, "transformers": "4.57.6",
                                                                "qwen3_5_model": False}))

    result = environment_versions(tmp_path / "python", run=old)
    assert not result["ok"] and result["mismatched"] == ["transformers"]


def test_the_replay_restores_e0s_strata_order_from_the_sorted_json_plan():
    from learnloop.experiments.contextual_embeddings.e1.replay import e0_strata

    frozen = {name: 1 for name in sorted(pins.DEV_STRATA)}
    plan = json.loads(json.dumps({"bank": {"vaults": {"v": {"development_strata": frozen}}}}, sort_keys=True))
    assert list(e0_strata(plan, "v")) == list(pins.DEV_STRATA)
    assert list(plan["bank"]["vaults"]["v"]["development_strata"]) != list(pins.DEV_STRATA)


def test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends(tmp_path):
    from learnloop.experiments.contextual_embeddings import corpus as C
    from learnloop.experiments.contextual_embeddings.budget import E0ProviderFailure
    from learnloop.experiments.contextual_embeddings.callers import Checkpoints, checkpoint_key
    from learnloop.experiments.contextual_embeddings.e1.replay import ReplayMiss, ReplayRoleCaller
    from learnloop.experiments.contextual_embeddings.retrieval import GeneratedContexts

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    store = Checkpoints(tmp_path / "fixtures-local" / "llm")
    caller = ReplayRoleCaller(handle, store, tmp_path / "fixtures-local" / "scratch")
    pin = pins.ROLE_PINS["context"]
    identity = caller._client(pin)[1]

    def key(prompt):
        return checkpoint_key(pin, prompt, GeneratedContexts, identity=identity, output_bound=caller.output_bound(pin))

    store.put(key("hit"), {"result": {"contexts": [{"ref": "p1", "context": "c"}]}, "latency_s": 1.0, "receipts": []})
    assert caller.call("context", prompt="hit", result_model=GeneratedContexts).contexts[0].ref == "p1"
    store.mark_failed(key("classified"), ["r1"], failure={"classification": "refusal", "reason": "x"})
    with pytest.raises(E0ProviderFailure) as refused:
        caller.call("context", prompt="classified", result_model=GeneratedContexts)
    assert refused.value.classification == "refusal"
    (store.directory / f".{key('old')}.failed.json").write_text(json.dumps(["r2"]))
    with pytest.raises(E0ProviderFailure) as truncated:
        caller.call("context", prompt="old", result_model=GeneratedContexts)
    assert truncated.value.classification == "truncated" and caller.inferred_truncations == 1
    with pytest.raises(ReplayMiss):
        caller.call("context", prompt="never", result_model=GeneratedContexts)
    assert caller.ledger.report()["requests"] == 0


def test_a_smoke_only_local_run_loads_checks_and_stores_nothing(e0_run, tmp_path):
    from learnloop.experiments.contextual_embeddings.adapters import VectorStore
    from learnloop.experiments.contextual_embeddings.e1 import run as e1

    layout = _import(e0_run)
    plan = e1.dry_run(import_dir=layout.root, environ={})
    launcher = InProcessLauncher(FakeV2Model())
    summary = e1.run_local(plan, layout, model_dir=tmp_path / "model", launcher=launcher, smoke_only=True)
    assert summary["status"] == "complete" and summary["smoke_only"] and summary["smoke"]["all_ok"]
    assert summary["planned"] == {"documents": 0, "queries": 0} and summary["profile"] == {}
    job = launcher.jobs[0]
    assert job["documents"] == [] and job["queries"] == [] and job["profile"] == {}
    root = layout.root.parent.parent / "runs" / plan["plan_id"]
    assert not list((root / "vectors").glob("*.jsonl")) if (root / "vectors").exists() else True
    # The full stage still has everything to encode afterwards.
    full = e1.run_local(plan, layout, model_dir=tmp_path / "model", launcher=launcher)
    assert full["planned"]["documents"] > 0 and full["stored"]["documents_stored"] == full["planned"]["documents"]
