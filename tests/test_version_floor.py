"""The oldest supported tag (ADR-019): a vault below it is refused at every door, ``learnloop upgrade`` included,
with the route through the code tagged ``pre-floor``.

A vault is put below the floor here by rewriting its tag directly, never through ``tests.helpers``'
``set_algorithm_version``, which registers an old vault with the suite's allowance.
"""

from __future__ import annotations

import ast
import io
import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.activation_journal import journal_path
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, OLDEST_SUPPORTED, SUCCESSOR_CHAIN
from learnloop.cli import app
from learnloop.substrate.shadow_rebuild import ConfigOverrideError, build_candidate_config
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop.version_floor import PRE_FLOOR_TAG, BelowOldestSupported, is_below_floor, upgrade_commands
from tests.helpers import create_basic_vault

ROOT = Path(__file__).resolve().parents[1]
#: The tag just below the floor.
BELOW = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED) - 1]


def _retag(root: Path, tag: str) -> None:
    path = root / "learnloop.toml"
    text, count = re.subn(r'algorithm_version = "[^"]+"', f'algorithm_version = "{tag}"', path.read_text("utf-8"),
                          count=1)
    assert count == 1
    path.write_text(text, encoding="utf-8")


def _below_floor_vault(tmp_path: Path, tag: str = BELOW) -> Path:
    paths = create_basic_vault(tmp_path / "vault")
    # A database the vault has opened at the head, so every door below gets as far as the tag.
    open_vault_repository(paths.root, paths.sqlite_path)
    _retag(paths.root, tag)
    return paths.root


def _assert_names_the_three_parts(message: str, root: Path, tag: str) -> None:
    assert tag in message
    assert OLDEST_SUPPORTED in message
    assert f"git worktree add ../learnloop-pre-floor {PRE_FLOOR_TAG}" in message
    assert f"uv run --directory ../learnloop-pre-floor learnloop upgrade --vault {root}" in message


# -- the doors ---------------------------------------------------------------------------------------------------


def _door_load_vault(root: Path) -> str:
    with pytest.raises(BelowOldestSupported) as refused:
        load_vault(root)
    return str(refused.value)


def _door_cli(root: Path) -> str:
    result = CliRunner().invoke(app, ["config", "effective", "--vault", str(root)])
    assert isinstance(result.exception, BelowOldestSupported), result.output
    return str(result.exception)


def _door_rebuild(root: Path) -> str:
    result = CliRunner().invoke(app, ["rebuild-derived-state", "--json", "--vault", str(root)])
    assert isinstance(result.exception, BelowOldestSupported), result.output
    return str(result.exception)


def _door_shadow_rebuild(root: Path) -> str:
    result = CliRunner().invoke(app, ["rebuild", "--shadow", "--json", "--vault", str(root)])
    assert isinstance(result.exception, BelowOldestSupported), result.output
    return str(result.exception)


def _door_upgrade(root: Path) -> str:
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(root)])
    assert result.exit_code == 1, result.output
    assert f"Vault not upgraded (currently {BELOW})" in result.output
    return " ".join(result.output.split())


def _door_doctor(root: Path) -> str:
    from learnloop.ops.doctor import run_doctor

    database = root / "state.sqlite"
    before = database.read_bytes()
    with pytest.raises(BelowOldestSupported) as refused:
        run_doctor(root, fix_state=True)
    # Refused before --fix-state wrote anything.
    assert database.read_bytes() == before
    return str(refused.value)


def _door_sidecar(root: Path) -> str:
    from learnloop_sidecar.server import serve

    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(root)}}
    stdout = io.StringIO()
    serve(io.StringIO(json.dumps(request) + "\n"), stdout)
    error = json.loads(stdout.getvalue().splitlines()[0])["error"]
    assert error["data"]["code"] == "vault_below_oldest_supported"
    details = error["data"]["details"]
    assert (details["algorithm_version"], details["oldest_supported"]) == (BELOW, OLDEST_SUPPORTED)
    return error["message"]


def _door_mcp(root: Path) -> str:
    from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch

    with pytest.raises(SchemaMismatch) as refused:
        RemoteRuntime.attach(root, load_environment=False)
    assert isinstance(refused.value.__cause__, BelowOldestSupported)
    return str(refused.value)


def _door_phone_host(root: Path) -> str:
    pytest.importorskip("starlette")
    from learnloop_mobile.config import MobileConfig
    from learnloop_mobile.host import SchemaMismatch, attach

    config = MobileConfig(enabled=True, vault=root, hostname="desktop.tail.ts.net", owner_login="owner@example.com")
    with pytest.raises(SchemaMismatch) as refused:
        attach(config)
    assert isinstance(refused.value.__cause__, BelowOldestSupported)
    return str(refused.value)


DOORS = {
    "load_vault": _door_load_vault,
    "cli": _door_cli,
    "rebuild": _door_rebuild,
    "shadow_rebuild": _door_shadow_rebuild,
    "doctor": _door_doctor,
    "sidecar": _door_sidecar,
    "mcp": _door_mcp,
    "phone_host": _door_phone_host,
    "upgrade": _door_upgrade,
}


@pytest.mark.parametrize("door", sorted(DOORS))
def test_a_vault_below_the_floor_is_refused_at_each_door(tmp_path, door):
    root = _below_floor_vault(tmp_path)
    message = DOORS[door](root)
    _assert_names_the_three_parts(message, root.resolve(), BELOW)


@pytest.mark.parametrize("tag", sorted({OLDEST_SUPPORTED, LATEST_ALGORITHM_VERSION}))
def test_a_vault_at_the_floor_or_the_head_opens(tmp_path, tag):
    paths = create_basic_vault(tmp_path / "vault")
    _retag(paths.root, tag)
    assert load_vault(paths.root).config.algorithms.algorithm_version == tag
    result = CliRunner().invoke(app, ["config", "effective", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output


def test_a_vault_whose_config_names_no_tag_is_refused(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = paths.root / "learnloop.toml"
    text, count = re.subn(r'algorithm_version = "[^"]+"\n', "", config.read_text("utf-8"), count=1)
    assert count == 1
    config.write_text(text, encoding="utf-8")
    with pytest.raises(BelowOldestSupported) as refused:
        load_vault(paths.root)
    assert refused.value.tag is None
    message = str(refused.value)
    assert "names no algorithm_version" in message and OLDEST_SUPPORTED in message
    assert f"learnloop upgrade --to mvp-0.7 --vault {paths.root.resolve()}" in message


def _journal_below_the_floor(tmp_path: Path) -> VaultPaths:
    """A vault published at the floor over its predecessor's database: the journal of an upgrade from below."""

    paths = create_basic_vault(tmp_path / "vault")
    open_vault_repository(paths.root, paths.sqlite_path)
    _retag(paths.root, OLDEST_SUPPORTED)
    journal_path(paths.sqlite_path).write_text(
        json.dumps({"predecessor": BELOW, "target": OLDEST_SUPPORTED}, sort_keys=True), encoding="utf-8"
    )
    return paths


def test_a_journal_naming_a_link_below_the_floor_is_refused(tmp_path):
    paths = _journal_below_the_floor(tmp_path)
    with pytest.raises(BelowOldestSupported) as refused:
        open_vault_repository(paths.root, paths.sqlite_path)
    message = str(refused.value)
    assert refused.value.journal == (BELOW, OLDEST_SUPPORTED)
    _assert_names_the_three_parts(message, paths.root.resolve(), BELOW)
    assert journal_path(paths.sqlite_path).exists()


def test_the_upgrade_command_refuses_a_journal_from_below_the_floor_with_the_route(tmp_path):
    paths = _journal_below_the_floor(tmp_path)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 1, result.output
    message = " ".join(result.output.split())
    assert f"unfinished upgrade from {BELOW} to {OLDEST_SUPPORTED}" in message
    _assert_names_the_three_parts(message, paths.root.resolve(), BELOW)
    assert journal_path(paths.sqlite_path).exists()


def test_a_journal_from_the_floor_is_still_completed_by_an_opener(tmp_path, monkeypatch):
    from learnloop import activation_journal

    paths = create_basic_vault(tmp_path / "vault")
    journal = journal_path(paths.sqlite_path)
    journal.write_text(json.dumps({"predecessor": OLDEST_SUPPORTED, "target": "mvp-0.999"}), encoding="utf-8")
    completed: list[Path] = []

    def complete(root: Path) -> None:
        completed.append(root)
        journal.unlink()

    monkeypatch.setattr(activation_journal, "_COMPLETER", complete)
    open_vault_repository(paths.root, paths.sqlite_path)
    assert completed == [paths.root]


def test_a_shadow_rebuild_cannot_be_forced_below_the_floor(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = load_vault(paths.root).config
    with pytest.raises(ConfigOverrideError, match=re.escape(OLDEST_SUPPORTED)):
        build_candidate_config(config, [f"algorithms.algorithm_version={BELOW}"])
    candidate, _applied = build_candidate_config(config, [f"algorithms.algorithm_version={OLDEST_SUPPORTED}"])
    assert candidate.algorithms.algorithm_version == OLDEST_SUPPORTED
    result = CliRunner().invoke(app, ["rebuild", "--shadow", "--json", "--vault", str(paths.root),
                                      "--set", f"algorithms.algorithm_version={BELOW}"])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == "shadow_rebuild_failed"


# -- the floor itself ------------------------------------------------------------------------------------------


def test_the_floor_is_a_tag_of_the_chain_and_the_chain_counts_up():
    assert OLDEST_SUPPORTED in SUCCESSOR_CHAIN
    numbers = [int(tag.removeprefix("mvp-0.")) for tag in SUCCESSOR_CHAIN]
    # is_below_floor compares tag numbers, which is the chain's order only while the numbers count up.
    assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
    assert all(is_below_floor(tag) for tag in SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED)])
    assert not any(is_below_floor(tag) for tag in SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED):])
    assert is_below_floor("mvp-0.6") and is_below_floor(None)
    assert not is_below_floor("mvp-0.9999") and not is_below_floor("not-a-tag")


@pytest.mark.parametrize(
    ("tag", "steps"),
    [
        ("mvp-0.6", ["--to mvp-0.7", "--to mvp-0.8", "--to mvp-0.9"]),
        ("mvp-0.8", ["--to mvp-0.9"]),
        ("mvp-0.9", []),
        (BELOW, []),
    ],
)
def test_the_commands_run_the_pre_floor_code_through_its_steps(tag, steps):
    commands = upgrade_commands(Path("/v"), tag)
    upgrade = "uv run --directory ../learnloop-pre-floor learnloop upgrade"
    assert list(commands) == [
        f"git worktree add ../learnloop-pre-floor {PRE_FLOOR_TAG}",
        *(f"{upgrade} {step} --vault /v" for step in steps),
        f"{upgrade} --vault /v",
    ]


def test_production_code_never_enters_the_test_allowance():
    """Only tests/helpers.py's allow_below_floor registers a vault below the floor; src/ and scripts/ never do."""

    names = {"allow_below_floor_in_tests", "end_test_allowance", "_TEST_ROOTS", "_TEST_OPEN"}
    offenders = []
    for base in ("src", "scripts"):
        for path in sorted((ROOT / base).rglob("*.py")):
            if path == ROOT / "src" / "learnloop" / "version_floor.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else None
                if name in names:
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                if isinstance(node, ast.ImportFrom) and any(alias.name in names for alias in node.names):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == []


def test_the_suites_allowance_opens_any_vault_until_the_test_ends(tmp_path):
    from learnloop.version_floor import end_test_allowance
    from tests.helpers import allow_below_floor

    registered = _below_floor_vault(tmp_path / "a")
    copy = _below_floor_vault(tmp_path / "b")
    allow_below_floor(registered)
    # A copy of the registered vault (the test's own, or production's scratch copy) opens during the test.
    load_vault(copy)
    end_test_allowance()  # what tests/conftest.py does after every test
    load_vault(registered)  # a registered root stays open, for fixtures that outlive one test
    with pytest.raises(BelowOldestSupported):
        load_vault(copy)
