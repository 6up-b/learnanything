"""The E0 dry run: zero network calls, nothing written to the copies, the frozen plan."""
from __future__ import annotations

import json
import socket
import urllib.request

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings import runner as R
from tests.e0_fakes import FAKE_KEYS, build_e0_vault

SECRET = FAKE_KEYS["PERPLEXITY_API_KEY"]


@pytest.fixture
def socket_tripwire(monkeypatch):
    """A test-level socket guard under the dry run's own guard."""

    attempts = []

    def refuse(*args, **kwargs):
        attempts.append(args)
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    return attempts


def test_the_guard_blocks_and_counts_network_attempts():
    with R.network_guard() as guard:
        with pytest.raises(R.NetworkForbidden):
            socket.create_connection(("example.com", 443))
        with pytest.raises(Exception):
            urllib.request.urlopen("https://example.com", timeout=1)
        assert guard.attempts >= 2
    assert socket.create_connection is not guard.refuse


def test_the_dry_run_makes_no_network_call_and_writes_nothing(tmp_path, socket_tripwire):
    paths, _repository = build_e0_vault(tmp_path)
    before = R.tree_digest(paths.root)
    plan = R.dry_run([paths.root], environ={})
    assert R.tree_digest(paths.root) == before
    assert socket_tripwire == []
    assert plan["checks"] == {"network_calls": 0, "copies_changed": 0, "copy_tree_digests_equal": True,
                              "settings_file_read": False, "database_mode": "read_only"}
    assert plan["status"] == "dry_run"


def test_the_plan_has_every_arm_question_count_estimate_and_key_state(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    plan = R.dry_run([paths.root], environ={"PERPLEXITY_API_KEY": SECRET})
    assert {row["arm"] for row in plan["embedding_arms"]} == {
        "R1", "R2", "R3", "R4_grouped", "R4_singleton", "R4_independent", "R5_grouped", "R5_singleton",
        "R5_independent"}
    assert {row["arm"] for row in plan["system_arms"]} == {"R0", "R1_service"}
    assert set(plan["delivery_arms"]) == {"D0", "D1", "D2", "D3"}
    assert {row["role"] for row in plan["llm_roles"]} == set(pins.ROLE_PINS)
    totals = plan["totals"]
    assert totals["cap_usd"] == 25.0 and set(totals["categories"]) == set(pins.ALLOCATION_USD)
    assert totals["estimated_usd"] == pytest.approx(sum(c["estimated_usd"] for c in totals["categories"].values()),
                                                    abs=1e-3)
    assert plan["keys"] == {"PERPLEXITY_API_KEY": "present", "VOYAGE_API_KEY": "absent",
                            "OPENROUTER_API_KEY": "absent"}
    assert plan["bank"]["totals"]["development"] > 0
    assert plan["baseline"]["delivery_fixes"]["merge_commit"] == "275fd5f7e"
    allowlist = plan["baseline"]["vaults"][paths.root.name]["config_allowlist"]
    assert allowlist["embedding.enabled"] is False and allowlist["source_retrieval.llm_price_per_million"] == "unset"


def test_the_plan_is_aggregate_only_and_never_holds_a_key(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    plan = R.dry_run([paths.root], environ={"PERPLEXITY_API_KEY": SECRET})
    text = json.dumps(plan, default=str)
    for private in (SECRET, "Definition 1.1", "Linear Algebra Book", "Exam question", "ext_book", "src_book"):
        assert private not in text, private


def test_the_cli_dry_run_with_an_env_file_never_prints_the_key(tmp_path, monkeypatch, socket_tripwire):
    paths, _repository = build_e0_vault(tmp_path)
    for name in FAKE_KEYS:
        monkeypatch.setenv(name, "placeholder")  # recorded, so teardown removes whatever the run loads
        monkeypatch.delenv(name)
    env_file = tmp_path / "keys.env"
    env_file.write_text(f"PERPLEXITY_API_KEY={SECRET}\n", encoding="utf-8")
    out = tmp_path / "fixtures-local" / "plan.json"
    before = R.tree_digest(paths.root)
    result = CliRunner().invoke(app, ["experiments", "e0", "run", "--copy", str(paths.root), "--dry-run",
                                      "--env-file", str(env_file), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert SECRET not in result.output and SECRET not in out.read_text()
    assert "PERPLEXITY_API_KEY present" in result.output
    assert json.loads(out.read_text())["checks"]["network_calls"] == 0
    assert R.tree_digest(paths.root) == before and socket_tripwire == []


def test_a_paid_run_is_refused_without_authorization(tmp_path, socket_tripwire):
    paths, _repository = build_e0_vault(tmp_path)
    result = CliRunner().invoke(app, ["experiments", "e0", "run", "--copy", str(paths.root)])
    assert result.exit_code == 1
    assert "i-am-authorized-to-spend" in result.output
    assert socket_tripwire == []


def test_split_strata_is_deterministic_and_complete(tmp_path):
    paths_a, _ = build_e0_vault(tmp_path, "one")
    paths_b, _ = build_e0_vault(tmp_path, "two", exam=False)
    from learnloop.experiments.contextual_embeddings.corpus import build_snapshot, open_copy

    snapshots = [build_snapshot(open_copy(paths_a.root)), build_snapshot(open_copy(paths_b.root))]
    split = R.split_strata(snapshots)
    for stratum, count in pins.DEV_STRATA.items():
        assert sum(split[label][stratum] for label in split) == count
    assert split == R.split_strata(snapshots)
