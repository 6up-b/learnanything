"""The practice index through its adapters: CLI commands and sidecar RPCs."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.practice_index.dossiers import generate_dossiers
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.practice_index_fakes import FakePracticeLLM, build_practice_vault, enable_practice_index


@pytest.fixture(autouse=True)
def no_real_clients(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("tests never resolve a real paid client")

    monkeypatch.setattr("learnloop.practice_index.paid.ready_client_for_task", refuse)
    monkeypatch.setattr("learnloop.practice_index.query_vectors.ready_client_for_task", refuse)


@pytest.fixture
def vault_paths(tmp_path):
    paths = build_practice_vault(tmp_path / "vault")
    open_vault_repository(paths.root, paths.sqlite_path)
    return paths


def _json(result):
    assert result.stdout, result.output
    return json.loads(result.stdout)


def test_cli_dossier_dry_run_changes_nothing(vault_paths):
    before = vault_paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, ["practice-index", "dossiers", "--vault", str(vault_paths.root),
                                      "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    report = _json(result)
    assert report["status"] == "dry_run" and report["pending"] == 6
    assert report["dossiers_enabled"] is False
    assert vault_paths.sqlite_path.read_bytes() == before
    disabled = CliRunner().invoke(app, ["practice-index", "dossiers", "--vault", str(vault_paths.root), "--json"])
    assert disabled.exit_code == 1
    assert _json(disabled)["status"] == "disabled"


def test_cli_eval_dry_run_find_coverage_status_and_tool_spec(vault_paths):
    enable_practice_index(vault_paths, embeddings=False)
    generate_dossiers(load_vault(vault_paths.root), caps=SpendCaps(), client=FakePracticeLLM())
    root = str(vault_paths.root)
    runner = CliRunner()
    before = vault_paths.sqlite_path.read_bytes()
    dry = runner.invoke(app, ["practice-index", "eval", "--vault", root, "--dry-run", "--json",
                              "--queries", "10"])
    assert dry.exit_code == 0, dry.output
    assert _json(dry)["status"] == "dry_run"
    assert vault_paths.sqlite_path.read_bytes() == before

    found = runner.invoke(app, ["practice-index", "find", "orthogonal vectors", "--vault", root,
                                "--no-rerank", "--limit", "2", "--json"])
    assert found.exit_code == 0, found.output
    report = _json(found)
    assert report["status"] == "ok" and report["rerank_status"] == "disabled"
    assert report["items"][0]["practice_item_id"].startswith("pi_orthogonal_")

    usage = runner.invoke(app, ["practice-index", "usage", "--vault", root,
                                "--proposal", report["proposal_id"],
                                "--item", report["items"][0]["practice_item_id"],
                                "--signal", "skipped", "--json"])
    assert usage.exit_code == 0, usage.output

    coverage = runner.invoke(app, ["practice-index", "coverage", "--vault", root,
                                   "--min-eligible", "4", "--json"])
    assert coverage.exit_code == 0, coverage.output
    targets = _json(coverage)["targets"]
    assert {target["facet_id"] for target in targets} == {
        "facet_eigen", "facet_determinant", "facet_matmul", "facet_independence",
        "facet_span", "facet_orthogonal",
    }
    assert all(target["deficit"] == 1 for target in targets)

    status = runner.invoke(app, ["practice-index", "status", "--vault", root, "--json"])
    assert status.exit_code == 0, status.output
    payload = _json(status)
    assert payload["dossiers"]["counts"]["current"] == 6
    assert payload["path"] == "direct"
    assert payload["usage"]["signals_by_path"] == {"direct": {"learner_card:skipped": 1}}

    spec = runner.invoke(app, ["practice-index", "tool-spec"])
    assert json.loads(spec.stdout)["name"] == "find_practice"


def test_sidecar_rpcs(vault_paths):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(vault_paths.root)

    def call(name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    result = call("find_practice", {"query": "determinant of a matrix", "limit": 3, "rerank": False,
                                    "learningObjectIds": ["lo_matrices"]})
    assert result["version"] == 1 and result["status"] == "ok"
    assert result["serves"] is False
    assert len(result["items"]) == 3
    assert {item["learningObjectId"] for item in result["items"]} == {"lo_matrices"}
    item_id = result["items"][0]["practiceItemId"]
    recorded = call("record_practice_usage", {"proposalId": result["proposalId"],
                                              "practiceItemId": item_id, "signal": "not_what_i_asked"})
    assert recorded["signal"] == "not_what_i_asked"
    with pytest.raises(SidecarError):
        call("record_practice_usage", {"proposalId": result["proposalId"],
                                       "practiceItemId": item_id, "signal": "bogus"})
    with pytest.raises(SidecarError):
        call("find_practice", {"query": "x", "minDifficulty": 0.9, "maxDifficulty": 0.1})
    coverage = call("get_practice_coverage", {"minEligible": 3})
    assert coverage["targets"] == [] and coverage["facets"] == 6
