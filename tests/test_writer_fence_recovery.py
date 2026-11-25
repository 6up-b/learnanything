"""The writer fence's round 4 (``docs/reviews/refactor-writer-fence.md``, "Round 4"; ledger R4-F1 to R4-F5): a host
recovers from a refusal without a second one, and no host loop ends on a refusal; a same-vault reload hands new ingest
claims to the successor; a vault with no database takes the upgrade path; a repeated completion of a Reader section
is no fenced write.

Fakes only; an upgrade "elsewhere" is ``learnloop upgrade`` in a subprocess, as beside an open desktop."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from learnloop.db import writer_fence
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from learnloop.vault import repository as vault_repository

from tests.writer_fence_helpers import (
    PREDECESSOR,
    TARGET,
    cli_process,  # noqa: F401 - the fixture
    count,
    fenced_at_predecessor,
    recorded,
    restore_config,
    upgrade_elsewhere,
)

pytestmark = [pytest.mark.fresh_connections, pytest.mark.usefixtures("cli_process")]


def _add_learning_object_without_mastery(paths: VaultPaths, lo_id: str = "lo_svd_rank") -> None:
    """A learning object the database has no mastery row for: the next state sync writes one (a fenced write)."""

    write_yaml(paths.learning_object_path("linear-algebra", lo_id), {
        "schema_version": 1, "id": lo_id, "title": "SVD and rank", "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition", "knowledge_type": "definition", "status": "active",
        "contradicts": None, "summary": "The rank is the number of nonzero singular values.", "prerequisites": [],
        "confusables": [], "difficulty_prior": 0.5, "tags": [], "provenance": {"origin": "human", "source_refs": []},
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    })


def _stale_write(ctx, _params):
    """A fenced write under the context's own vault (the shape of a grade's first write). The fence's trigger runs
    before the row's own constraints, so a write the fence admits fails on them instead, and that is success here."""

    with closing(connect(Path(ctx.repository.sqlite_path))) as connection:
        try:
            connection.execute("INSERT INTO lesson_checks DEFAULT VALUES")
        except sqlite3.IntegrityError:
            pass  # admitted by the fence; the empty row breaks the table's own NOT NULL
    return {"ok": True}


# -- R4-F1: recovery compares the tags before any write; no host loop ends on a refusal ------------------------------


def test_the_desktop_survives_a_restored_older_config_and_says_to_run_upgrade(tmp_path, monkeypatch):
    """The review's scenario, through the stdio loop itself: the desktop loaded the predecessor; an upgrade elsewhere
    moved the database on; ``learnloop.toml`` was restored from an older copy and a learning object without a mastery
    row was added. The next write is refused; the recovery's reload used to sync the new object (a second fenced
    write), the refusal escaped the handler and ``serve`` closed. Now the reload compares the config's tag with the
    database's before it writes anything, the answer says to run ``learnloop upgrade``, and the loop keeps serving:
    once the config is repaired, the same request succeeds."""

    from learnloop.ops.upgrades import upgrade
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from learnloop_sidecar.server import serve

    paths = fenced_at_predecessor(tmp_path)
    spec = METHOD_REGISTRY["get_queue_revision"]
    monkeypatch.setitem(METHOD_REGISTRY, "get_queue_revision", replace(spec, handler=_stale_write))

    mastery_rows: list[int] = []

    def lines():
        yield json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"vaultPath": str(paths.root)}}) + "\n"
        upgrade_elsewhere(paths)
        restore_config(paths, PREDECESSOR)
        _add_learning_object_without_mastery(paths)
        yield json.dumps({"jsonrpc": "2.0", "id": 2, "method": "get_queue_revision", "params": {}}) + "\n"
        yield json.dumps({"jsonrpc": "2.0", "id": 3, "method": "get_queue_revision", "params": {}}) + "\n"
        # Nothing was written while the config named the predecessor: no mastery row for the new object.
        mastery_rows.append(count(paths, "learning_object_mastery"))
        upgrade(paths.root, to=PREDECESSOR)  # sets the config back to the database's tag
        yield json.dumps({"jsonrpc": "2.0", "id": 4, "method": "initialize",
                          "params": {"vaultPath": str(paths.root)}}) + "\n"
        yield json.dumps({"jsonrpc": "2.0", "id": 5, "method": "get_queue_revision", "params": {}}) + "\n"
        yield json.dumps({"jsonrpc": "2.0", "id": 6, "method": "rpc.ping", "params": {}}) + "\n"

    class Out:
        def __init__(self):
            self.responses = []

        def write(self, text):
            self.responses.append(json.loads(text))

        def flush(self):
            pass

    out = Out()
    serve(lines(), out)  # type: ignore[arg-type]
    by_id = {response["id"]: response for response in out.responses}
    assert sorted(by_id) == [1, 2, 3, 4, 5, 6]
    assert "result" in by_id[1]
    for refused_id in (2, 3):
        error = by_id[refused_id]["error"]
        assert error["data"]["code"] == "vault_upgraded_while_open"
        assert error["data"]["retryable"] is False
        assert "learnloop upgrade" in error["message"] and TARGET in error["message"]
    assert mastery_rows == [1]
    assert "result" in by_id[4] and by_id[5]["result"] == {"ok": True} and "result" in by_id[6]
    assert recorded(paths) == TARGET


def test_a_load_refuses_a_config_behind_its_database_before_it_writes(tmp_path):
    """The comparison is the load's own: a context opening such a vault writes nothing and serves nothing."""

    from learnloop_sidecar.context import SidecarContext

    paths = fenced_at_predecessor(tmp_path)
    upgrade_elsewhere(paths)
    restore_config(paths, PREDECESSOR)
    _add_learning_object_without_mastery(paths)
    context = SidecarContext()
    try:
        with pytest.raises(vault_repository.ConfigBehindDatabase):
            context.load(paths.root)
    finally:
        context.close()
    assert count(paths, "learning_object_mastery") == 1


def test_a_refusal_raised_while_answering_another_failure_is_still_answered(tmp_path, monkeypatch):
    """The last boundary of every request: a refusal raised inside a handler of another failure (here the reload of
    the refusal's own recovery) is answered, never raised out of the request."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from learnloop_sidecar.server import _handle

    paths = fenced_at_predecessor(tmp_path)
    context = SidecarContext()
    context.load(paths.root)
    try:
        def refused_twice(*_args, **_kwargs):
            raise writer_fence.WriterFenceRefusal(writer_fence.REFUSAL)

        spec = METHOD_REGISTRY["get_queue_revision"]
        monkeypatch.setitem(METHOD_REGISTRY, "get_queue_revision", replace(spec, handler=refused_twice))
        monkeypatch.setattr(SidecarContext, "reload", refused_twice)
        response = _handle(context, {"jsonrpc": "2.0", "id": 7, "method": "get_queue_revision", "params": {}})
        assert response["error"]["data"]["code"] == "vault_upgraded_while_open"
        assert response["error"]["data"]["retryable"] is False
        assert "Restart LearnLoop" in response["error"]["message"]

        # A refusal from a handler of an ordinary failure (here the validation error's figure record).
        def invalid(*_args, **_kwargs):
            raise writer_fence.WriterFenceRefusal(writer_fence.REFUSAL)

        monkeypatch.setattr("learnloop.figures.records.write_records", invalid)
        response = _handle(context, {"jsonrpc": "2.0", "id": 8, "method": "figure.request", "params": []})
        assert response["error"]["data"]["code"] == "vault_upgraded_while_open"
    finally:
        context.close()


def test_a_cli_command_stops_on_a_refusal_with_its_words(monkeypatch, capsys):
    """The CLI's entry point answers a refusal plainly (its words, exit status 1), never with a traceback."""

    import typer

    from learnloop import cli

    @cli.app.command("fence-refusal-probe", hidden=True)
    def probe() -> None:
        raise writer_fence.WriterFenceRefusal(writer_fence.REFUSAL)

    try:
        with pytest.raises(SystemExit) as stopped:
            cli.app(["fence-refusal-probe"], prog_name="learnloop")
    finally:
        cli.app.registered_commands[:] = [
            command for command in cli.app.registered_commands if command.name != "fence-refusal-probe"]
    assert stopped.value.code == 1
    assert writer_fence.REFUSAL in capsys.readouterr().err
    assert typer  # the app is a Typer application


# -- R4-F2: a same-vault reload hands new ingest claims to the successor's repository --------------------------------


def _bound_repository(paths):
    from learnloop.vault.loader import load_vault
    from learnloop.vault.repository import open_vault_repository, vault_writes

    vault = load_vault(paths.root)
    with vault_writes(vault):
        return open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)


def test_a_same_vault_reload_after_an_upgrade_gives_new_ingest_claims_the_successors_repository(tmp_path):
    """The host's reload binds the ingest jobs again with the successor's repository. The runner used to stay the
    predecessor's (kept for its interrupt handle), so every new claim wrote under the old tag and was refused (a
    reread's carried-over completion, migration 276) until the host restarted. Now a new claim runs on a runner bound
    to the successor; the predecessor's runner claims nothing more (it would only finish a claim it holds)."""

    from learnloop.content.pipeline.job_contracts import JobSpec
    from learnloop.content.pipeline.jobs import IngestJobManager

    paths = fenced_at_predecessor(tmp_path)
    jobs = IngestJobManager()
    jobs.bind(_bound_repository(paths), paths.root, background=False)
    predecessor_runner = jobs._require_runner()
    upgrade_elsewhere(paths)
    jobs.bind(_bound_repository(paths), paths.root, background=False)  # SidecarContext.reload's bind
    outcomes: list[str] = []

    def fenced_write(ctx):
        try:
            with ctx.repo.atomic():
                ctx.repo.connection().execute("INSERT INTO lesson_checks DEFAULT VALUES")
        except sqlite3.IntegrityError:
            outcomes.append("admitted")  # past the fence; the empty row breaks the table's own NOT NULL
        except writer_fence.WriterFenceRefusal:
            outcomes.append("refused")
        return {"ok": True}

    runner = jobs._require_runner()
    runner.handlers["fence_probe"] = fenced_write
    runner.enqueue_batch("import", [JobSpec("fence_probe")])
    jobs.drain_foreground()
    assert outcomes == ["admitted"]
    assert runner is not predecessor_runner and predecessor_runner.run_next() is False


def test_a_same_tag_reload_keeps_the_ingest_runner(tmp_path):
    """A reload that does not change the tag keeps the runner, and with it a live call's interrupt handle."""

    from learnloop.content.pipeline.jobs import IngestJobManager

    paths = fenced_at_predecessor(tmp_path)
    jobs = IngestJobManager()
    jobs.bind(_bound_repository(paths), paths.root, background=False)
    first = jobs._require_runner()
    jobs.bind(_bound_repository(paths), paths.root, background=False)
    assert jobs._require_runner() is first


# -- R4-F3: a vault with no database takes the upgrade path; the owner's tag walks to the head ------------------------

#: The tag the owner's live vaults are at (2026-11-25): their upgrade must walk cleanly to the head.
OWNER_TAG = "mvp-0.61"


def _remove_database(paths: VaultPaths) -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(f"{paths.sqlite_path}{suffix}").unlink(missing_ok=True)


def test_a_content_only_vault_with_no_database_takes_the_upgrade_path(tmp_path):
    """Intact vault files and no ``state.sqlite``: the walk's fence-tag probe opened the absent file read-only and
    failed before the repository opener could create it. An absent database has no recorded tag; the walk goes on
    through the existing creation path and ends with the database at the head."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, SUCCESSOR_CHAIN
    from learnloop.ops.upgrades import upgrade
    from tests.helpers import create_basic_vault, set_algorithm_version

    assert OWNER_TAG in SUCCESSOR_CHAIN
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OWNER_TAG)
    _remove_database(paths)
    result = upgrade(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OWNER_TAG, LATEST_ALGORITHM_VERSION)
    assert paths.sqlite_path.exists() and recorded(paths) == LATEST_ALGORITHM_VERSION


def test_an_existing_database_that_cannot_be_read_still_stops_the_upgrade(tmp_path):
    from learnloop.ops.upgrades import upgrade
    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OWNER_TAG)
    _remove_database(paths)
    paths.sqlite_path.write_bytes(b"this is not a database" * 64)
    with pytest.raises(sqlite3.DatabaseError):
        upgrade(paths.root)
    assert paths.sqlite_path.read_bytes() == b"this is not a database" * 64


def test_the_owners_tag_walks_to_the_head_with_its_history(tmp_path):
    """The walk the owner's vaults take, end to end on a vault with a database and graded history written at their
    tag: every link from it activates, the database's tag and the config reach the head, and the history stays."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.ops import upgrades
    from learnloop.ops.upgrades import UPGRADES, upgrade
    from tests.writer_fence_helpers import vault_at

    paths = vault_at(tmp_path, OWNER_TAG)
    attempts = count(paths, "practice_attempts")
    result = upgrade(paths.root)
    assert result.upgraded and not result.problems
    assert (result.from_version, result.to_version) == (OWNER_TAG, LATEST_ALGORITHM_VERSION)
    walked = UPGRADES[next(i for i, link in enumerate(UPGRADES) if link.predecessor == OWNER_TAG):]
    assert walked[-1].tag == LATEST_ALGORITHM_VERSION
    repository = Repository(paths.sqlite_path)
    assert all(link.activate.committed(repository, link.tag) for link in walked)
    assert recorded(paths) == LATEST_ALGORITHM_VERSION
    assert upgrades.published_algorithm_version(paths.root / "learnloop.toml") == LATEST_ALGORITHM_VERSION
    assert count(paths, "practice_attempts") == attempts


def test_the_upgrade_command_takes_a_content_only_vault_to_the_head(tmp_path):
    from typer.testing import CliRunner

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.cli import app
    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OWNER_TAG)
    _remove_database(paths)
    done = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert done.exit_code == 0, done.output
    assert f"{OWNER_TAG} -> {LATEST_ALGORITHM_VERSION}" in done.output
    assert recorded(paths) == LATEST_ALGORITHM_VERSION
