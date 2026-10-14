"""Chat frontend C1a: the MCP server as a second process beside the desktop (spec_mcp_frontend_c1 §3).

* Secondary attach refuses a vault whose schema is not this code's (the CLI
  exits 78) and never migrates.
* Attaching and reading run no startup work and write nothing; only telemetry
  and exposure are written, and only by tool calls.
* The loaded vault follows the files (content fingerprint).
* A real second OS process (``python -m learnloop_mcp`` over stdio, the SDK's
  stdio client) serves the vault while the desktop sidecar holds it open: it
  sees what the desktop records, and the desktop sees its telemetry in the
  same ledger. Run with production SQLite durability (WAL, synchronous=FULL).
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import anyio
import pytest
from mcp import Client, StdioServerParameters
from typer.testing import CliRunner

from learnloop.db.connection import connect
from learnloop.remote import views
from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import create_basic_vault
from tests.mcp_world import no_model_calls, table_count

SRC = Path(__file__).resolve().parents[1] / "src"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_secondary_attach_refuses_a_schema_it_does_not_match(tmp_path):
    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    with connect(paths.sqlite_path) as connection:
        latest = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (latest,))
        connection.commit()
    before = table_count_versions(paths.sqlite_path)
    with pytest.raises(SchemaMismatch, match="learnloop doctor"):
        RemoteRuntime.attach(paths.root, load_environment=False)
    result = CliRunner().invoke(app, ["mcp", "serve", "--vault", str(paths.root), "--transport", "stdio"])
    assert result.exit_code == 78
    assert "Schema mismatch" in result.output
    assert table_count_versions(paths.sqlite_path) == before  # never migrated


def table_count_versions(sqlite_path: Path) -> int:
    with connect(sqlite_path) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0])


def test_attach_and_every_view_write_nothing(tmp_path, monkeypatch):
    from learnloop.learner_context import learning_context

    no_model_calls(monkeypatch)
    paths = create_basic_vault(tmp_path / "vault")
    before = _digest(paths.sqlite_path)
    files_before = sorted(str(p.relative_to(paths.root)) for p in paths.root.rglob("*"))
    runtime = RemoteRuntime.attach(paths.root, load_environment=False)
    views.status(runtime)
    views.today(runtime)
    views.progress(runtime)
    views.library(runtime, query="algebra")
    learning_context(runtime.vault(), runtime.read_repository())
    assert _digest(paths.sqlite_path) == before
    assert sorted(str(p.relative_to(paths.root)) for p in paths.root.rglob("*")) == files_before


def test_the_loaded_vault_follows_its_files(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    runtime = RemoteRuntime.attach(paths.root, load_environment=False)
    assert runtime.vault().learning_objects["lo_svd_definition"].title == "SVD definition"
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    lo = read_yaml(lo_path)
    lo["title"] = "SVD, renamed on the desktop"
    write_yaml(lo_path, lo)
    stat = lo_path.stat()
    os.utime(lo_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    runtime._checked_at = float("-inf")  # the 2 s fingerprint cache has expired
    assert runtime.vault().learning_objects["lo_svd_definition"].title == "SVD, renamed on the desktop"


@pytest.mark.durability
def test_a_second_process_serves_the_vault_beside_the_desktop_sidecar(tmp_path):
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    desktop = SidecarContext()
    desktop.load(paths.root, maintenance=False)
    _vault, desktop_repository = desktop.require_vault()
    migrations = table_count_versions(paths.sqlite_path)
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "learnloop_mcp", "--vault", str(paths.root)],
        env={"PYTHONPATH": str(SRC), "LEARNLOOP_CONFIG_DIR": os.environ["LEARNLOOP_CONFIG_DIR"],
             "LEARNLOOP_CHATGPT_SECRET_STORE": "file"},
        cwd=str(tmp_path),
    )

    async def session():
        async with Client(parameters) as client:
            first = await client.call_tool("learning_context", {"learning_object_ids": ["lo_svd_definition"]})
            # The desktop records an answer while the chat process is attached.
            with connect(paths.sqlite_path) as connection:
                connection.execute(
                    "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                    "attempt_type, learner_answer_md, correctness, hints_used, created_at, evidence_origin, "
                    "entry_surface) VALUES ('att_desktop', 'pi_svd_define_001', 'lo_svd_definition', "
                    "'short_answer', 'independent_attempt', 'DESKTOP_ANSWER_7710 rotations', 0.0, 0, "
                    "'2026-10-01T09:00:00Z', 'human', 'desktop_practice')")
                # Graded against one contract (the revision it answered): only then is its text shown.
                connection.execute(
                    "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
                    "schema_version, created_at) VALUES ('acv_desktop', 'pi_svd_define_001', 'h_desktop', "
                    "'{\"prompt\": \"Define the SVD.\"}', 1, '2026-10-01T09:00:00Z')")
                connection.execute(
                    "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, "
                    "created_at, assessment_contract_version_id) VALUES ('ge_desktop', 'att_desktop', 'correct', 0, "
                    "1, '2026-10-01T09:00:00Z', 'acv_desktop')")
                connection.commit()
            second = await client.call_tool("learning_context", {"learning_object_ids": ["lo_svd_definition"]})
            status = await client.call_tool("status", {})
            return first, second, status

    first, second, status = anyio.run(session)
    assert not first.is_error and not second.is_error and not status.is_error
    assert first.structured_content["recent_answer_traces"] == []
    (trace,) = second.structured_content["recent_answer_traces"]
    assert trace["attempt_id"] == "att_desktop" and trace["answer"].startswith("DESKTOP_ANSWER_7710")
    # The desktop's own repository sees the chat process's calls in the same ledger.
    events = desktop_repository.reader_interaction_events(kind="chat_tool_call")
    assert [event["subject_id"] for event in events] == ["learning_context", "learning_context", "status"]
    assert {event["payload"]["transport"] for event in events} == {"stdio"}
    assert table_count_versions(paths.sqlite_path) == migrations
    assert table_count(desktop_repository, "practice_attempts") == 1
