"""Gate G1: hooks and sweeps always exit 0, whatever fails (spec P1)."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.config import LearnLoopConfig
from learnloop.projects.capture import auto_sweep, enroll_repo
from learnloop.projects.experiment_store import ProjectStore, pending_path, store_path
from learnloop.projects.hooks import HOOK_BEGIN, HookError, install_hook, uninstall_hook
from tests.helpers import create_basic_vault
from tests.project_support import TempRepo, clock_at, isolated_git, make_model_repo  # noqa: F401


@pytest.fixture
def enrolled(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = make_model_repo(tmp_path / "repo")
    row, _ = enroll_repo(vault, LearnLoopConfig(), repo.path, clock=clock_at(0))
    return vault, repo, row, ProjectStore.for_vault(vault)


def _hook(repo: TempRepo) -> Path:
    return repo.path / ".git" / "hooks" / "post-commit"


def _run_hook(repo: TempRepo, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/bin/sh", str(_hook(repo))],
        cwd=cwd or repo.path,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        check=False,
    )


def test_installed_hook_appends_one_line_per_commit(enrolled):
    vault, repo, row, store = enrolled
    result = install_hook(vault, store, row)
    assert result["status"] == "installed"
    assert os.access(_hook(repo), os.X_OK)
    repo.write("x.py", "x = 1\n")
    sha = repo.commit("human commit", trailer=None)
    entries = [json.loads(line) for line in pending_path(vault).read_text().splitlines()]
    assert entries == [{"repo_id": row["id"], "sha": sha, "at": entries[0]["at"]}]
    assert store.repo(row["id"])["hook_installed"] == 1


def test_hook_exits_zero_under_injected_failures(enrolled, tmp_path):
    vault, repo, row, store = enrolled
    install_hook(vault, store, row)
    pending = pending_path(vault)
    # 1. The pending list cannot be written.
    pending.write_text("")
    pending.chmod(stat.S_IRUSR)
    try:
        assert _run_hook(repo).returncode == 0
    finally:
        pending.chmod(stat.S_IRUSR | stat.S_IWUSR)
    # 2. Not inside a git repository (git rev-parse fails).
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    assert _run_hook(repo, cwd=outside).returncode == 0
    # 3. git and date are not on PATH.
    assert _run_hook(repo, env={"PATH": "/nonexistent"}).returncode == 0
    # 4. The vault's projects directory is gone: nothing is recreated.
    for child in pending.parent.iterdir():
        child.unlink()
    pending.parent.rmdir()
    assert _run_hook(repo).returncode == 0
    assert not pending.parent.exists()
    # 5. A real commit still succeeds with the vault gone.
    repo.write("y.py", "y = 2\n")
    repo.commit("still commits", trailer=None)


def test_existing_shell_hook_is_preserved_and_restored(enrolled):
    vault, repo, row, store = enrolled
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    original = "#!/bin/bash\necho owner-hook >> \"$(git rev-parse --git-dir)/owner.log\"\nexit 0\n"
    hook.write_text(original)
    hook.chmod(0o755)
    assert install_hook(vault, store, row)["status"] == "appended"
    text = hook.read_text()
    assert text.index(HOOK_BEGIN) < text.index("echo owner-hook")  # before any exit
    assert install_hook(vault, store, row)["status"] == "updated"
    assert hook.read_text().count(HOOK_BEGIN) == 1
    repo.write("z.py", "z = 3\n")
    repo.commit("both hooks run", trailer=None)
    assert (repo.path / ".git" / "owner.log").read_text().strip() == "owner-hook"
    assert len(pending_path(vault).read_text().splitlines()) == 1
    assert uninstall_hook(store, row)["status"] == "block_removed"
    assert hook.read_text() == original


def test_our_own_hook_is_removed_entirely(enrolled):
    vault, repo, row, store = enrolled
    install_hook(vault, store, row)
    assert uninstall_hook(store, row)["status"] == "removed"
    assert not _hook(repo).exists()


def test_non_shell_hook_and_shared_hooks_path_are_refused(enrolled):
    vault, repo, row, store = enrolled
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env python3\nprint('hi')\n")
    with pytest.raises(HookError):
        install_hook(vault, store, row)
    hook.unlink()
    repo.git("config", "core.hooksPath", "/tmp/shared-hooks-never-written")
    with pytest.raises(HookError):
        install_hook(vault, store, row)
    assert not Path("/tmp/shared-hooks-never-written/post-commit").exists()


def test_auto_sweep_never_raises(enrolled, tmp_path):
    vault, repo, row, store = enrolled
    config = LearnLoopConfig()
    # No vault at all, and a vault where nothing was ever enrolled: nothing is created.
    assert auto_sweep(tmp_path / "missing", config)["status"] == "not_enrolled"
    empty = tmp_path / "empty-vault"
    empty.mkdir()
    assert auto_sweep(empty, config)["status"] == "not_enrolled"
    assert not (empty / "projects").exists()
    # Kill switch.
    off = LearnLoopConfig.model_validate({"project": {"auto_sweep": False}})
    assert auto_sweep(vault, off)["status"] == "disabled"
    # A git error (the repo vanished) is reported per repo, not raised.
    for path in sorted(repo.path.rglob("*"), reverse=True):
        path.unlink() if path.is_file() or path.is_symlink() else path.rmdir()
    result = auto_sweep(vault, config, clock=clock_at(0))
    assert result["status"] == "partial" and result["errors"]
    assert store.repo(row["id"])["last_sweep_error"]


def test_auto_sweep_survives_a_locked_store(enrolled):
    vault, repo, row, store = enrolled
    locker = sqlite3.connect(store_path(vault), timeout=0.1)
    locker.execute("BEGIN EXCLUSIVE")
    try:
        result = auto_sweep(vault, LearnLoopConfig(), clock=clock_at(0), busy_timeout_ms=50)
    finally:
        locker.rollback()
        locker.close()
    assert result["status"] == "error" and "locked" in result["error"]


def test_auto_sweep_is_throttled_at_plan_build(enrolled):
    vault, repo, row, store = enrolled
    config = LearnLoopConfig()
    assert auto_sweep(vault, config, clock=clock_at(0), trigger="plan_build", min_interval_minutes=15)["status"] == "ok"
    assert auto_sweep(vault, config, clock=clock_at(0.005), trigger="plan_build", min_interval_minutes=15)["status"] == "throttled"
    assert auto_sweep(vault, config, clock=clock_at(0.02), trigger="plan_build", min_interval_minutes=15)["status"] == "ok"


def test_cli_sweep_exits_zero_on_failures(enrolled, tmp_path):
    vault, repo, row, store = enrolled
    runner = CliRunner()
    missing = runner.invoke(app, ["project", "sweep", "--vault", str(tmp_path / "no-vault"), "--json"])
    assert missing.exit_code == 0 and json.loads(missing.output)["status"] == "error"
    basic = create_basic_vault(tmp_path / "basic")
    not_enrolled = runner.invoke(app, ["project", "sweep", "--vault", str(basic.root), "--json"])
    assert not_enrolled.exit_code == 0 and json.loads(not_enrolled.output)["status"] == "not_enrolled"


def test_startup_maintenance_runs_the_sweep_without_creating_anything(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.ops.startup import run_startup_maintenance
    from learnloop.vault.loader import load_vault

    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    run_startup_maintenance(loaded, Repository(paths.sqlite_path))
    assert not (paths.root / "projects").exists()


def test_linked_worktrees_sharing_a_hook_each_log_their_own_commits(enrolled, tmp_path):
    vault, repo, row, store = enrolled
    linked = TempRepo.__new__(TempRepo)
    linked.path = tmp_path / "linked"
    repo.git("worktree", "add", "-q", str(linked.path), "-b", "feature")
    linked_row, _ = enroll_repo(vault, LearnLoopConfig(), linked.path, clock=clock_at(0))
    assert linked_row["id"] != row["id"]
    install_hook(vault, store, row)
    install_hook(vault, store, linked_row)  # same shared hooks directory
    main_sha = (repo.write("m.py", "m = 1\n"), repo.commit("main commit", trailer=None))[1]
    linked_sha = (linked.write("l.py", "l = 1\n"), linked.commit("linked commit", trailer=None))[1]
    entries = [json.loads(line) for line in pending_path(vault).read_text().splitlines()]
    assert [(entry["repo_id"], entry["sha"]) for entry in entries] == [(row["id"], main_sha), (linked_row["id"], linked_sha)]
    # Uninstalling one registration leaves the other working.
    assert uninstall_hook(store, linked_row)["status"] == "block_removed"
    repo.write("m2.py", "m = 2\n")
    again = repo.commit("main again", trailer=None)
    linked.write("l2.py", "l = 2\n")
    linked.commit("linked again", trailer=None)
    entries = [json.loads(line) for line in pending_path(vault).read_text().splitlines()]
    assert [(entry["repo_id"], entry["sha"]) for entry in entries[2:]] == [(row["id"], again)]
    assert uninstall_hook(store, row)["status"] == "removed"
    assert not _hook(repo).exists()


def test_a_first_build_unguarded_block_is_replaced(enrolled):
    vault, repo, row, store = enrolled
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    legacy = (
        "#!/bin/sh\n# >>> learnloop project capture (append-only; never blocks a commit) >>>\n"
        "( echo stale ) || true\n# <<< learnloop project capture <<<\nexit 0\n"
    )
    hook.write_text(legacy)
    assert install_hook(vault, store, row)["status"] == "updated"
    text = hook.read_text()
    assert "echo stale" not in text and f"{HOOK_BEGIN} {row['id']}" in text
