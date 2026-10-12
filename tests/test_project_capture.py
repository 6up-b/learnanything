"""Capture (spec §3, §10 test_project_capture): temp repos only."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.projects import capture
from learnloop.projects.capture import (
    capture_commit,
    capture_working_tree,
    detect_agent,
    enroll_repo,
    load_bundle,
    parse_trailers,
    scope_range,
    strip_agent_trailers,
    sweep,
)
from learnloop.projects.experiment_store import ProjectStore, pending_path
from tests.project_support import (
    BASE_TIME,
    CLAUDE_TRAILER,
    MODEL_PY_RELU,
    TempRepo,
    clock_at,
    isolated_git,  # noqa: F401 - fixture
    make_model_repo,
)


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


def _enroll(vault, repo, config=None, **kwargs):
    config = config or LearnLoopConfig()
    row, _created = enroll_repo(vault, config, repo.path, clock=clock_at(0), **kwargs)
    return row, ProjectStore.for_vault(vault), config


@pytest.mark.parametrize(
    ("trailer", "agent"),
    [
        ("Co-Authored-By: Claude <noreply@anthropic.com>", "claude_code"),
        ("Co-authored-by: Claude Opus 5.5 <noreply@anthropic.com>", "claude_code"),
        ("Co-authored-by: Codex <codex@openai.com>", "codex"),
        ("Co-authored-by: GitHub Copilot <copilot@github.com>", "other"),
        ("Assisted-by: aider", "other"),
        ("Signed-off-by: Owner <owner@example.com>", None),
        ("Co-authored-by: A Human <human@example.com>", None),
    ],
)
def test_trailer_detection(trailer, agent):
    assert detect_agent(parse_trailers(trailer)) == agent


def test_generated_with_claude_code_body_marker_counts_as_agent():
    assert detect_agent([], "Fix\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)") == "claude_code"


def test_strip_agent_trailers_removes_attribution_only():
    message = f"Add relu\n\nBecause negatives hurt.\n\nSigned-off-by: Me <me@x>\n{CLAUDE_TRAILER}\n🤖 Generated with [Claude Code](x)"
    stripped = strip_agent_trailers(message)
    assert "Claude" not in stripped and "anthropic" not in stripped
    assert "Because negatives hurt." in stripped and "Signed-off-by" in stripped


def test_sweep_captures_agent_trailer_commits_once(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo")
    row, store, config = _enroll(vault, repo)
    report = sweep(vault, config, clock=clock_at(0), trigger="manual")
    assert report.captured == 1 and report.errors == []
    (diff,) = store.diffs()
    assert diff["agent"] == "claude_code" and diff["agent_source"] == "trailer"
    assert diff["capture_timing"] == "post_commit" and diff["capture_source"] == "sweep"
    assert diff["probe_status"] == "pending" and diff["head_sha"] == repo.git("rev-parse", "HEAD").strip()
    bundle = load_bundle(vault, diff["bundle_hash"])
    assert "Co-Authored-By" not in bundle["commit_message"]
    assert "Co-Authored-By" in diff["commit_message"]  # the full message stays local
    (entry,) = bundle["files"]
    assert entry["path"] == "model.py" and entry["status"] == "M"
    assert "torch.relu(y)" in "\n".join(entry["excerpts"][0]["lines"])
    # Idempotent: the second sweep captures nothing new.
    assert sweep(vault, config, clock=clock_at(1)).captured == 0
    assert len(store.diffs()) == 1


def test_sweep_ignores_human_commits_and_commits_before_the_window(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("a.py", "x = 1\n")
    repo.commit("human work", trailer=None)
    repo.write("a.py", "x = 1\ny = 2\nz = 3\nw = 4\nv = 5\nu = 6\n")
    repo.commit("old agent work", when=BASE_TIME - timedelta(days=30))
    row, store, config = _enroll(vault, repo)
    assert sweep(vault, config, clock=clock_at(0)).captured == 0
    assert store.diffs() == []


def test_backfill_window_captures_recent_agent_commits(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo", when=BASE_TIME - timedelta(days=3))
    row, store, config = _enroll(vault, repo, backfill_days=7)
    assert sweep(vault, config, clock=clock_at(0)).captured == 1
    other_vault = vault.parent / "vault2"
    other_vault.mkdir()
    row2, store2, _ = _enroll(other_vault, repo, backfill_days=1)
    assert sweep(other_vault, config, clock=clock_at(0)).captured == 0


def test_working_tree_capture_is_pre_commit_and_deduplicated(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("model.py", "def f(x):\n    return x\n")
    repo.commit("init", trailer=None)
    repo.write("model.py", "def f(x):\n    y = x * 2\n    y += 1\n    y -= 3\n    return y\n")
    row, store, config = _enroll(vault, repo)
    result = capture_working_tree(store, vault, config, row, clock=clock_at(0), agent="codex")
    assert result.status == "captured"
    diff = store.diff(result.diff_id)
    assert diff["capture_timing"] == "pre_commit" and diff["snapshot_kind"] == "working_tree"
    assert diff["agent"] == "codex" and diff["agent_source"] == "flag"
    again = capture_working_tree(store, vault, config, row, clock=clock_at(0), agent="codex")
    assert again.status == "duplicate" and again.diff_id == result.diff_id
    # Committing the same change with a trailer later is the same patch: not captured twice.
    repo.commit("double f", trailer=CLAUDE_TRAILER)
    report = sweep(vault, config, clock=clock_at(1))
    assert report.captured == 0 and report.duplicates == 1


def test_renames_are_captured_with_their_old_path(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("old_name.py", "".join(f"line_{index} = {index}\n" for index in range(40)))
    repo.commit("init", trailer=None)
    repo.git("mv", "old_name.py", "new_name.py")
    text = (repo.path / "new_name.py").read_text().replace("line_5 = 5", "line_5 = 500")
    repo.write("new_name.py", text)
    repo.commit("rename and tweak")
    row, store, config = _enroll(vault, repo)
    sweep(vault, config, clock=clock_at(0))
    (diff,) = store.diffs()
    (entry,) = json.loads(diff["files_json"])
    assert entry["status"] == "R" and entry["old_path"] == "old_name.py" and entry["path"] == "new_name.py"
    bundle = load_bundle(vault, diff["bundle_hash"])
    assert "rename from old_name.py" in bundle["files"][0]["diff"]


def test_untracked_files_need_the_flag_and_respect_gitignore(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write(".gitignore", "build/\n*.log\n")
    repo.write("main.py", "print('hi')\n")
    repo.commit("init", trailer=None)
    repo.write("helper.py", "".join(f"def h{index}():\n    return {index}\n" for index in range(5)))
    repo.write("build/out.py", "generated = True\n")
    repo.write("debug.log", "noise\n")
    row, store, config = _enroll(vault, repo)
    without = capture_working_tree(store, vault, config, row, clock=clock_at(0))
    assert without.status == "nothing_to_capture"
    result = capture_working_tree(store, vault, config, row, clock=clock_at(0), include_untracked=True)
    assert result.status == "captured"
    paths = [entry["path"] for entry in json.loads(store.diff(result.diff_id)["files_json"])]
    assert paths == ["helper.py"]


def test_merge_commits_are_not_captured(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("a.py", "a = 1\n")
    repo.commit("init", trailer=None)
    repo.git("checkout", "-q", "-b", "side")
    repo.write("b.py", "b = 1\nc = 2\nd = 3\ne = 4\nf = 5\n")
    repo.commit("side work", trailer=None)
    repo.git("checkout", "-q", "main")
    repo.write("c.py", "c = 1\n")
    repo.commit("main work", trailer=None)
    repo.git("merge", "-q", "--no-ff", "side", "-m", f"merge\n\n{CLAUDE_TRAILER}")
    row, store, config = _enroll(vault, repo)
    assert sweep(vault, config, clock=clock_at(0)).captured == 0
    merge = repo.git("rev-parse", "HEAD").strip()
    assert capture_commit(store, vault, config, row, merge, capture_source="accept", trigger="manual").status == "refused"


def test_trivial_diffs_are_captured_but_not_probed(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("a.py", "a = 1\n")
    repo.commit("init", trailer=None)
    repo.write("a.py", "a = 2\n")
    repo.commit("typo")
    row, store, config = _enroll(vault, repo)
    report = sweep(vault, config, clock=clock_at(0))
    assert report.excluded == 1
    (diff,) = store.diffs()
    assert diff["excluded_reason"] == "trivial" and diff["probe_status"] == "excluded"


def test_pending_list_feeds_trailerless_commits_to_the_unattributed_list(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo", agent_commit=False)
    row, store, config = _enroll(vault, repo)
    sha = repo.git("rev-parse", "HEAD").strip()
    path = pending_path(vault)
    path.write_text(json.dumps({"repo_id": row["id"], "sha": sha, "at": "x"}) + "\nnot json\n", encoding="utf-8")
    report = sweep(vault, config, clock=clock_at(0))
    assert report.unattributed == 1 and report.pending_malformed == 1 and report.captured == 0
    assert [entry["sha"] for entry in store.unattributed()] == [sha]
    # Re-reading the list does not double count: the offset moved past it.
    assert sweep(vault, config, clock=clock_at(0)).pending_lines == 0
    # One tap ("this was AI-written") captures it and resolves the entry.
    result = capture_commit(store, vault, config, row, sha, capture_source="accept", trigger="manual", agent="codex", agent_source="flag")
    assert result.status == "captured"
    assert store.diff(result.diff_id)["agent"] == "codex"
    assert store.unattributed() == []


def test_pending_list_captures_agent_commits_outside_the_branch_window(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo")
    sha = repo.git("rev-parse", "HEAD").strip()
    repo.git("checkout", "-q", "--detach", "HEAD~1")
    repo.git("branch", "-q", "-D", "main")
    row, store, config = _enroll(vault, repo)
    pending_path(vault).write_text(json.dumps({"repo_id": row["id"], "sha": sha, "at": "x"}) + "\n", encoding="utf-8")
    report = sweep(vault, config, clock=clock_at(0))
    assert report.captured == 1
    assert store.diffs()[0]["capture_source"] == "pending_list"


def test_scope_range_finds_the_enclosing_function():
    lines = MODEL_PY_RELU.splitlines()
    start = next(i for i, line in enumerate(lines, 1) if "torch.relu" in line)
    header, end = scope_range(lines, start, start)
    assert lines[header - 1].strip().startswith("def forward")
    assert end == len(lines)


def test_context_extends_to_the_enclosing_scope_within_budget(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    body = "".join(f"        value_{index} = {index}\n" for index in range(60))
    repo.write("long.py", f"class Big:\n    def run(self):\n{body}        return value_59\n")
    repo.commit("init", trailer=None)
    text = (repo.path / "long.py").read_text().replace("value_59 = 59", "value_59 = 5900\n        value_60 = 1\n        value_61 = 2\n        value_62 = 3")
    repo.write("long.py", text)
    repo.commit("tweak run")
    config = LearnLoopConfig.model_validate({"project": {"context_lines": 3}})
    row, store, _ = _enroll(vault, repo, config=config)
    sweep(vault, config, clock=clock_at(0))
    bundle = load_bundle(vault, store.diffs()[0]["bundle_hash"])
    starts = [excerpt["start_line"] for excerpt in bundle["files"][0]["excerpts"]]
    assert starts == [2] and not bundle["truncated"]  # extended from ±3 lines up to `def run`


def test_budget_truncation_is_honest(isolated_git, tmp_path, vault):
    repo = TempRepo(tmp_path / "repo")
    repo.write("seed.py", "seed = 0\n")
    repo.commit("init", trailer=None)
    for index in range(3):
        repo.write(f"big_{index}.py", "".join(f"item_{index}_{n} = {n}\n" for n in range(400)))
    repo.commit("add three big files")
    config = LearnLoopConfig.model_validate({"project": {"context_token_budget": 3000}})
    row, store, _ = _enroll(vault, repo, config=config)
    sweep(vault, config, clock=clock_at(0))
    diff = store.diffs()[0]
    bundle = load_bundle(vault, diff["bundle_hash"])
    assert diff["truncated"] == 1 and bundle["truncated"] is True
    assert any(entry["omitted"] for entry in bundle["files"])
    assert diff["token_estimate"] <= 3000 + 200


def test_remote_credentials_are_stripped(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo")
    repo.git("remote", "add", "origin", "https://owner:ghp_secretsecretsecretsecret1234@github.com/owner/repo.git")
    row, _store, _ = _enroll(vault, repo)
    assert row["remote_url"] == "https://github.com/owner/repo.git"


def test_enroll_rejects_a_non_repo(tmp_path, vault, isolated_git):
    (tmp_path / "plain").mkdir()
    with pytest.raises(capture.GitError):
        enroll_repo(vault, LearnLoopConfig(), tmp_path / "plain")


def test_a_pending_entry_survives_a_sweep_while_its_repo_is_unavailable(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo", agent_commit=False)
    other = make_model_repo(tmp_path / "other")
    row, store, config = _enroll(vault, repo)
    _enroll(vault, other)
    sha = repo.git("rev-parse", "HEAD").strip()
    pending_path(vault).write_text(json.dumps({"repo_id": row["id"], "sha": sha, "at": "x"}) + "\n", encoding="utf-8")
    away = tmp_path / "repo-away"
    repo.path.rename(away)  # e.g. an unmounted drive
    report = sweep(vault, config, clock=clock_at(0))
    assert report.status == "partial" and store.unattributed() == []
    away.rename(repo.path)
    report = sweep(vault, config, clock=clock_at(0))
    assert report.status == "ok"
    assert [entry["sha"] for entry in store.unattributed()] == [sha]
    # Processed once: a later sweep neither loses nor re-counts it.
    assert sweep(vault, config, clock=clock_at(0)).unattributed == 0
    assert [entry["sha"] for entry in store.unattributed()] == [sha]


def test_a_single_repo_sweep_keeps_other_repos_pending_entries(isolated_git, tmp_path, vault):
    repo = make_model_repo(tmp_path / "repo", agent_commit=False)
    other = make_model_repo(tmp_path / "other")
    row, store, config = _enroll(vault, repo)
    other_row, _store, _config = _enroll(vault, other)
    sha = repo.git("rev-parse", "HEAD").strip()
    pending_path(vault).write_text(json.dumps({"repo_id": row["id"], "sha": sha, "at": "x"}) + "\n", encoding="utf-8")
    sweep(vault, config, clock=clock_at(0), repo_ids={other_row["id"]})
    assert store.unattributed() == []
    sweep(vault, config, clock=clock_at(0))
    assert [entry["sha"] for entry in store.unattributed()] == [sha]


def _many_agent_commits(tmp_path, count):
    repo = TempRepo(tmp_path / "repo")
    repo.write("base.py", "x = 0\n")
    repo.commit("init", trailer=None)
    for index in range(count):
        repo.write(f"m{index}.py", "".join(f"value_{index}_{line} = {line}\n" for line in range(6)))
        repo.commit(f"Add module {index}")
    return repo


def test_the_sweep_pages_through_history_beyond_one_git_log_page(isolated_git, tmp_path, vault, monkeypatch):
    monkeypatch.setattr(capture, "SWEEP_PAGE_COMMITS", 2)
    repo = _many_agent_commits(tmp_path, 6)
    row, store, config = _enroll(vault, repo)
    report = sweep(vault, config, clock=clock_at(0))
    assert report.status == "ok" and report.captured == 6
    assert len(store.diffs()) == 6


def test_history_beyond_the_scan_limit_is_reported_not_silently_skipped(isolated_git, tmp_path, vault, monkeypatch):
    monkeypatch.setattr(capture, "SWEEP_PAGE_COMMITS", 2)
    monkeypatch.setattr(capture, "SWEEP_MAX_SCANNED_COMMITS", 4)
    repo = _many_agent_commits(tmp_path, 6)
    row, store, config = _enroll(vault, repo)
    report = sweep(vault, config, clock=clock_at(0))
    assert report.status == "partial"
    assert report.repos[0]["history_incomplete"] is True
    assert "not scanned" in store.repo(row["id"])["last_sweep_error"]
