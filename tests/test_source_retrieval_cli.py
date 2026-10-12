"""Slice 2 T6: `learnloop sources search` and `learnloop sources suggest-lo`."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from tests.source_retrieval_fakes import build_retrieval_vault


def test_sources_search_and_suggest_lo(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    runner = CliRunner()
    found = runner.invoke(app, ["sources", "search", "cofactor expansion", "--vault", str(paths.root), "--json"])
    assert found.exit_code == 0, found.output
    report = json.loads(found.stdout)
    assert report["hits"][0]["span_id"] == "s8" and report["basis"] == "keyword"
    text = runner.invoke(app, ["sources", "search", "dot product", "--vault", str(paths.root)])
    assert text.exit_code == 0 and "basis: keyword" in text.stdout and "ext_book/s12" in text.stdout
    suggested = runner.invoke(app, ["sources", "suggest-lo", "--vault", str(paths.root), "--extraction",
                                    "ext_book", "--span", "s12"])
    assert suggested.exit_code == 0
    assert "suggestion (not a provenance link): lo_inner" in suggested.stdout


def test_deep_search_has_a_dry_run_and_caps(tmp_path):
    from contextlib import closing

    from learnloop.db.connection import connect
    from tests.helpers import append_config_toml

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    # A metered rewrite route with a price, so the plan has something to cost.
    append_config_toml(paths.root, "[source_retrieval]\nllm_price_per_million = 2.0\n")

    def receipts() -> int:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            return connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0]

    before = receipts()
    runner = CliRunner()
    planned = runner.invoke(app, ["sources", "search", "Why does swapping rows change a determinant?",
                                  "--vault", str(paths.root), "--deep", "--dry-run", "--json"])
    assert planned.exit_code == 0, planned.output
    plan = json.loads(planned.stdout)
    assert plan["dry_run"] is True and plan["status"] == "planned"
    assert set(plan) >= {"rewrite", "query_embedding", "meaning_search", "caps", "calls", "estimated_usd"}
    assert plan["caps"]["max_calls"] == 3 and plan["caps"]["max_estimated_usd"] == 0.02
    assert plan["query_embedding"]["status"] == "unused"  # no source-block vectors: no meaning search
    assert receipts() == before  # a dry run calls and writes nothing
    text = runner.invoke(app, ["sources", "search", "determinant", "--vault", str(paths.root), "--deep",
                               "--dry-run"])
    assert text.exit_code == 0 and text.stdout.startswith("dry run: planned; 0 paid call(s)")
    typing = json.loads(runner.invoke(app, ["sources", "search", "determinant", "--vault", str(paths.root),
                                            "--dry-run", "--json"]).stdout)
    assert typing["status"] == "no_paid_step" and typing["calls"] == 0


def test_deep_search_caps_bound_the_paid_steps():
    from learnloop.ai.spend import SpendBudget, SpendEstimate, SpendLimitExceeded
    from learnloop.source_retrieval.library import deep_search_caps

    budget = SpendBudget(deep_search_caps(max_calls=1, max_tokens=60_000, max_cost_usd=0.02))
    with budget.request(SpendEstimate(candidates=1, calls=1, total_tokens=100, estimated_usd=0.001)):
        pass
    import pytest

    with pytest.raises(SpendLimitExceeded):
        with budget.request(SpendEstimate(candidates=1, calls=1, total_tokens=100, estimated_usd=0.001)):
            pass
