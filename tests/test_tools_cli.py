"""S4 (§10.5): `learnloop sources tools` and `learnloop sources tool` for external agents."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.stores.source_service import tool_calls
from tests.source_service_fakes import build_service_vault


def _run(*args):
    return CliRunner().invoke(app, ["sources", *args])


def test_tools_lists_every_schema():
    payload = json.loads(_run("tools", "--json").stdout)
    assert [tool["name"] for tool in payload["tools"]] == [
        "find_practice", "find_sources", "compare_sources", "find_facets", "practice_availability"]


def test_tool_runs_as_an_agent_with_receipts(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    dry = _run("tool", "find_facets", "--args", '{"query": "determinant"}', "--dry-run", "--json",
               "--vault", str(paths.root))
    assert dry.exit_code == 0 and json.loads(dry.stdout)["policy"] == "reading"
    with repository.connection() as connection:
        assert tool_calls(connection) == []
    ran = _run("tool", "find_facets", "--args", '{"query": "determinant"}', "--json", "--vault", str(paths.root))
    payload = json.loads(ran.stdout)
    assert ran.exit_code == 0 and payload["status"] == "ran"
    assert payload["result"]["facets"][0]["facet_id"] == "facet_determinant"
    with repository.connection() as connection:
        rows = tool_calls(connection, caller_kind="agent")
    assert [row["row_kind"] for row in rows] == ["request", "run"]
    bad = _run("tool", "find_facets", "--args", '{"query": "x", "policy": "post_attempt"}', "--json",
               "--vault", str(paths.root))
    assert bad.exit_code == 1 and json.loads(bad.stdout)["code"] == "invalid_arguments"
