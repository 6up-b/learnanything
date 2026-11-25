"""The writer fence's review fix round (``docs/reviews/refactor-writer-fence.md``, "Review fix round"; ledger WF-R1 to
WF-R12): the binding belongs to the vault a write was computed from, a refusal is never swallowed, the database's
tag never moves backwards, more stale writes that lose a fact are fenced, and the phone keeps a refusal retryable.

A "process that loaded the predecessor" is this process before ``learnloop upgrade`` runs in another process (a
subprocess here); "another thread reloaded" is a second ``load_vault`` in this process after it. Fakes only.
"""

from __future__ import annotations

import ast
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from learnloop.db import writer_fence
from learnloop.db.connection import connect, reused_connections
from learnloop.db.repositories import Repository
from learnloop.ops import upgrades
from learnloop.ops.upgrades import upgrade
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

from tests.writer_fence_helpers import (
    BEFORE,
    PREDECESSOR,
    TARGET,
    cli_process,  # noqa: F401 - the fixture
    count,
    grade,
    recorded,
    refused,
    vault_at,
)

pytestmark = [pytest.mark.fresh_connections, pytest.mark.usefixtures("cli_process")]


def _fenced_at_predecessor(tmp_path, name="vault"):
    """A vault whose database is fenced at the predecessor: one fence-aware activation behind it."""

    paths = vault_at(tmp_path, BEFORE.predecessor, name)
    assert upgrade(paths.root, to=PREDECESSOR).upgraded
    assert recorded(paths) == PREDECESSOR
    return paths


def _upgrade_elsewhere(paths, to=TARGET) -> None:
    """``learnloop upgrade`` in another process, as beside an open desktop or phone host."""

    done = subprocess.run(
        [sys.executable, "-c",
         "import sys; from learnloop.ops.upgrades import upgrade; "
         "sys.exit(0 if upgrade(sys.argv[1], to=sys.argv[2]).upgraded else 3)", str(paths.root), to],
        env=dict(os.environ), capture_output=True, text=True, timeout=300,
    )
    assert done.returncode == 0, done.stderr
    assert recorded(paths) == to


# -- WF-R1: the binding is the vault's, not the process's newest -----------------------------------------------------


def test_a_repository_opened_for_a_stale_vault_is_refused_after_another_thread_reloaded(tmp_path):
    """The phone job worker's shape: its context loaded the predecessor; another worker reloads the successor in this
    process; the job resumes with its own vault and repository. Its grade is refused, nothing is written."""

    paths = _fenced_at_predecessor(tmp_path)
    job_vault = load_vault(paths.root)
    job_repository = open_vault_repository(job_vault.root, VaultPaths(job_vault.root, job_vault.config).sqlite_path)
    _upgrade_elsewhere(paths)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET  # the other worker's reload
    attempts = count(paths, "practice_attempts")
    with pytest.raises(BaseException) as stale:
        grade(job_vault, job_repository, minutes=5)
    assert refused(stale.value)
    assert count(paths, "practice_attempts") == attempts


def test_a_sidecar_request_writes_under_its_own_contexts_vault(tmp_path, monkeypatch):
    """Every host dispatches through the sidecar's handler: a request on a context still holding the predecessor is
    refused even when another context of the process loaded the successor, whatever connection the handler opens."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from learnloop_sidecar.server import _handle

    paths = _fenced_at_predecessor(tmp_path)
    job = SidecarContext()
    job.load_secondary(paths.root)
    _upgrade_elsewhere(paths)
    rpc = SidecarContext()
    rpc.load_secondary(paths.root)  # the other worker's reload

    def stale_write(ctx, _params):
        with closing(connect(Path(ctx.repository.sqlite_path))) as connection:
            connection.execute("INSERT INTO lesson_checks DEFAULT VALUES")
        return {"ok": True}

    spec = METHOD_REGISTRY["get_queue_revision"]
    monkeypatch.setitem(METHOD_REGISTRY, "get_queue_revision", replace(spec, handler=stale_write))
    response = _handle(job, {"jsonrpc": "2.0", "id": 1, "method": "get_queue_revision", "params": {}})
    assert response["error"]["data"]["code"] == "vault_upgraded_while_open"


def test_a_cli_command_writes_under_the_vault_it_loaded_first(tmp_path):
    """``exam finish`` loads the vault, then opens its repository: an upgrade between the two does not rebind it."""

    from learnloop.cli.runtime import _repository

    paths = _fenced_at_predecessor(tmp_path)
    command_vault = load_vault(paths.root)
    _upgrade_elsewhere(paths)
    repository = _repository(paths.root)
    attempts = count(paths, "practice_attempts")
    with pytest.raises(BaseException) as stale:
        grade(command_vault, repository, minutes=5)
    assert refused(stale.value)
    assert count(paths, "practice_attempts") == attempts


def test_a_pool_checkout_reads_its_binding_once(tmp_path, monkeypatch):
    """A reload between the pool key's read and the registration's would file a successor connection under the
    predecessor's key: one read per checkout serves both."""

    paths = _fenced_at_predecessor(tmp_path)
    answers = iter([frozenset({PREDECESSOR}), frozenset({TARGET})] * 4)
    monkeypatch.setattr(writer_fence, "binding", lambda sqlite_path: next(answers))
    with reused_connections():
        connection = connect(paths.sqlite_path)
        names = {row[0] for row in connection.execute(
            "SELECT name FROM pragma_function_list WHERE name GLOB 'learnloop writes under *'")}
        connection.close()
    assert names == {writer_fence.TAG_FUNCTION_PREFIX + PREDECESSOR}


# -- WF-R2, WF-R12: a refusal is never swallowed ---------------------------------------------------------------------


def _stale_repository(paths) -> Repository:
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        return Repository(paths.sqlite_path)


def test_the_forecast_receipt_writer_does_not_swallow_a_refusal(tmp_path):
    """A stale serve's receipt is refused, and the refusal reaches the serve, which rolls back whole."""

    from learnloop.scheduling.forecast_receipts import ForecastReceipt, record_receipts

    paths = _fenced_at_predecessor(tmp_path)
    _upgrade_elsewhere(paths)
    receipt = ForecastReceipt(
        receipt_key="item_unassisted_success:stale", kind="item_unassisted_success", forecaster="stale",
        forecaster_version="v", scope="presentation", decision_kind="serve", binding_kind="plan_presentation",
        event="unassisted_success", forecast={"p": 0.5}, inputs={}, parameters=[], p=0.5)
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        repository = Repository(paths.sqlite_path)
        with pytest.raises(BaseException) as stale:
            record_receipts(repository, [receipt])
    assert refused(stale.value)


def test_a_refusal_is_not_an_exception_a_broad_except_could_take():
    refusal = writer_fence.WriterFenceRefusal(writer_fence.REFUSAL)
    assert not isinstance(refusal, Exception) and writer_fence.is_refusal(refusal)


def test_a_refusal_on_a_connection_this_code_opened_is_the_fences_own_exception(tmp_path):
    paths = _fenced_at_predecessor(tmp_path)
    _upgrade_elsewhere(paths)
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        with closing(connect(paths.sqlite_path)) as connection:
            with pytest.raises(writer_fence.WriterFenceRefusal):
                connection.execute("INSERT INTO lesson_checks DEFAULT VALUES")
            with pytest.raises(writer_fence.WriterFenceRefusal):
                connection.cursor().executemany("INSERT INTO lesson_checks DEFAULT VALUES", [()])
            with pytest.raises(sqlite3.IntegrityError):  # any other constraint stays what it was
                connection.execute("INSERT INTO writer_fence(id, algorithm_version, updated_at) VALUES (1, 'x', 'y')")


def test_mcp_drops_its_cached_vault_on_a_refusal(tmp_path):
    from learnloop.remote.runtime import RemoteRuntime
    from learnloop_mcp.server import ToolCalls

    paths = _fenced_at_predecessor(tmp_path)
    runtime = RemoteRuntime.attach(paths.root)
    first = runtime.vault()
    calls = ToolCalls(runtime, transport="in_process")

    def fenced(_call_id):
        raise sqlite3.IntegrityError(writer_fence.REFUSAL)

    with pytest.raises(Exception):  # the SDK's ToolError, with the plain words
        calls.run("status", {}, None, fenced)
    assert runtime.vault() is not first


# -- WF-R4: the database's tag never moves backwards; an upgrade starts from it ------------------------------------


def _restore_config(paths, tag) -> None:
    """Only ``learnloop.toml`` restored from an older copy: the database stays where it is."""

    named = upgrades.published_algorithm_version(paths.root / "learnloop.toml")
    upgrades.rewrite_algorithm_version(paths.root / "learnloop.toml", named, tag, durable=True)


def test_an_upgrade_from_a_restored_older_config_never_moves_the_database_back(tmp_path):
    paths = _fenced_at_predecessor(tmp_path)
    assert upgrade(paths.root, to=TARGET).upgraded and recorded(paths) == TARGET
    _restore_config(paths, BEFORE.predecessor)
    result = upgrade(paths.root, to=PREDECESSOR)
    assert recorded(paths) == TARGET
    assert not result.upgraded and any(TARGET in problem for problem in result.problems)
    # The config names the database's tag again, so the openers write under it.
    assert upgrades.published_algorithm_version(paths.root / "learnloop.toml") == TARGET


def test_an_upgrade_to_the_restored_configs_own_tag_repairs_the_config(tmp_path):
    """The refusal loop: the restored file names a tag whose activation committed; ``upgrade --to`` that tag used to
    answer "already" and leave the file behind the database."""

    paths = _fenced_at_predecessor(tmp_path)
    assert upgrade(paths.root, to=TARGET).upgraded
    _restore_config(paths, PREDECESSOR)
    upgrade(paths.root, to=PREDECESSOR)
    assert upgrades.published_algorithm_version(paths.root / "learnloop.toml") == TARGET
    assert recorded(paths) == TARGET


def test_an_activation_refuses_a_database_at_another_tag_than_its_predecessor(tmp_path):
    paths = _fenced_at_predecessor(tmp_path)
    assert upgrade(paths.root, to=TARGET).upgraded
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(writer_fence.FenceMismatch):
            writer_fence.advance(connection, predecessor=PREDECESSOR, target=TARGET, recorded_at="t")
        with pytest.raises(writer_fence.FenceMismatch):
            writer_fence.advance(connection, predecessor=BEFORE.predecessor, target=PREDECESSOR, recorded_at="t")
        connection.rollback()
    assert recorded(paths) == TARGET


# -- WF-R2, WF-R6, WF-R8, WF-R9: more stale writes that lose a fact are fenced ---------------------------------------


@pytest.mark.parametrize("table", ["plan_presentations", "probe_presentations", "grade_adjudications"])
def test_a_stale_serve_presentation_probe_pin_or_adjudication_is_refused(tmp_path, table):
    paths = _fenced_at_predecessor(tmp_path)
    _upgrade_elsewhere(paths)
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        with closing(connect(paths.sqlite_path)) as connection:
            with pytest.raises(BaseException) as stale:
                connection.execute(f"INSERT INTO {table} DEFAULT VALUES")
            assert refused(stale.value)


def test_a_stale_reader_cannot_first_complete_a_section_but_still_records_progress(tmp_path):
    paths = _fenced_at_predecessor(tmp_path)
    _upgrade_elsewhere(paths)
    columns = ("extraction_id, section_id, spans_seen, span_count, revealed_at, completed_at, updated_at, "
               "completion_cause, completion_algorithm_version")
    with closing(sqlite3.connect(paths.sqlite_path)) as setup:
        setup.execute("PRAGMA foreign_keys = OFF")
        setup.execute(f"INSERT INTO reader_section_progress({columns}) VALUES "
                      "('ex', 'open', 1, 4, NULL, NULL, 't', NULL, NULL)")
        setup.commit()
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        with closing(connect(paths.sqlite_path)) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            with pytest.raises(BaseException) as first:
                connection.execute(f"INSERT INTO reader_section_progress({columns}) VALUES "
                                   "('ex', 'new', 4, 4, NULL, 't', 't', 'reached_end', ?)", (PREDECESSOR,))
            assert refused(first.value)
            with pytest.raises(BaseException) as completing:
                connection.execute("UPDATE reader_section_progress SET completed_at = 't' WHERE section_id = 'open'")
            assert refused(completing.value)
            connection.execute("UPDATE reader_section_progress SET spans_seen = 2 WHERE section_id = 'open'")
            connection.commit()


# -- WF-R11: the phone keeps the host's retryability --------------------------------------------------------------


def test_the_phone_adapter_keeps_an_explicit_no_retry():
    from learnloop_mobile.adapter import translate

    status, body = translate({"error": {"message": "Restart LearnLoop", "data": {
        "code": "vault_upgraded_while_open", "retryable": False}}})
    assert body["error"]["retryable"] is False
    _status, retry = translate({"error": {"message": "try again", "data": {
        "code": "vault_upgraded_while_open", "retryable": True}}})
    assert retry["error"]["retryable"] is True
    _status, unsaid = translate({"error": {"message": "busy", "data": {"code": "database_busy"}}})
    assert unsaid["error"]["retryable"] is True


# -- the guards: nothing can swallow a refusal ---------------------------------------------------------------------


def _caught(handler: ast.ExceptHandler) -> set[str]:
    def names(node):
        if node is None:
            return {"<bare>"}
        if isinstance(node, ast.Tuple):
            return set().union(*(names(element) for element in node.elts))
        if isinstance(node, ast.Attribute):
            return {node.attr}
        if isinstance(node, ast.Name):
            return {node.id}
        return set()

    return names(handler.type)


def _reraises(handler: ast.ExceptHandler) -> bool:
    return any(isinstance(node, ast.Raise) for node in ast.walk(ast.Module(body=handler.body, type_ignores=[])))


def _handlers():
    for path in sorted(Path("src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                yield path, node, tree


def test_no_handler_that_can_catch_a_refusal_swallows_it():
    """A refusal is a ``BaseException``: only ``except BaseException`` and a bare ``except`` can catch it. Each such
    handler re-raises, or is registered in ``writer_fence.REFUSAL_BOUNDARIES`` (it answers a job or a waiter with
    the refusal, never drops it)."""

    found = set()
    for path, node, _tree in _handlers():
        for handler in node.handlers:
            if _caught(handler) & {"BaseException", "<bare>"} and not _reraises(handler):
                found.add(f"{path.as_posix()}:{_enclosing(path, handler)}")
    assert found <= set(writer_fence.REFUSAL_BOUNDARIES), sorted(found - set(writer_fence.REFUSAL_BOUNDARIES))
    assert set(writer_fence.REFUSAL_BOUNDARIES) <= found, "a registered boundary no longer exists"


#: Keep-alive loops that never write a fenced table, as ``path:line`` of their ``try``: a lease's or a heartbeat's
#: renewal, a model call's retry, the notebook runtime. A refusal cannot reach them.
KEEP_ALIVE_WITHOUT_FENCED_WRITES = {
    "src/learnloop/content/pipeline/runner.py": "the ingest job's lease renewal",
    "src/learnloop/daily_plan/router_runtime.py": "the router's model call and its retry",
    "src/learnloop/db/stores/judgment_claims.py": "a judgment claim's lease renewal",
    "src/learnloop/hints/map_builder.py": "an approach map's claim renewal",
    "src/learnloop/notebook_runtime/runtime.py": "the notebook sessions' sweep",
    "src/learnloop/notebook_runtime/supervisor.py": "a notebook server's readiness poll",
    "src/learnloop/source_retrieval/service_spend.py": "the source service's spend lease",
}


def test_every_keep_alive_loop_survives_a_refusal():
    """A loop that keeps a worker alive past one failure (``while`` around ``try``/``except Exception``) also takes a
    refusal, or a refusal would end the worker: the iteration's writes rolled back, the next one loads afresh."""

    missing = []
    for path in sorted(Path("src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for loop in ast.walk(tree):
            if not isinstance(loop, ast.While):
                continue
            for statement in loop.body:
                if not isinstance(statement, ast.Try):
                    continue
                caught = set().union(*(_caught(handler) for handler in statement.handlers))
                keeps_alive = any("Exception" in _caught(handler) and not _reraises(handler)
                                  for handler in statement.handlers)
                if keeps_alive and "WriterFenceRefusal" not in caught and (
                        path.as_posix() not in KEEP_ALIVE_WITHOUT_FENCED_WRITES):
                    missing.append(f"{path.as_posix()}:{statement.lineno}")
    assert not missing, missing


def _enclosing(path: Path, handler: ast.ExceptHandler) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    best = "<module>"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno <= handler.lineno <= (
                node.end_lineno or node.lineno):
            best = node.name
    return best
