"""Secret filtering (spec §4, gate G2 at the capture layer)."""

from __future__ import annotations

import json

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.ingest.originals import canonical_source_raw_path
from learnloop.projects.capture import enroll_repo, load_bundle, sweep
from learnloop.projects.experiment_store import ProjectStore, store_path
from learnloop.projects.redaction import (
    PathRules,
    RedactionCounter,
    load_path_rules,
    redact_diff,
    redact_text,
    scan_line,
)
from tests.project_support import TempRepo, clock_at, isolated_git  # noqa: F401

AWS_KEY = "AKIAQWERTYUIOPASDFGH"
OPENAI_KEY = "sk-proj-Zx81kQ0mN3vB7cX2lP9oR4tY6uI1"
GITHUB_TOKEN = "ghp_aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5"
SLACK_TOKEN = "xoxb-123456789012-abcdefghijkl"
ENTROPY_TOKEN = "Zq8Lr2Vx9Tn4Kp7Wm3Hs6Jd1Fb5Gc0Yt8Qe2Ru"
ENV_SECRET = "hunter2-the-database-password-123"


@pytest.mark.parametrize(
    ("line", "kind"),
    [
        (f'client = OpenAI(api_key="{OPENAI_KEY}")', "api_key_sk"),
        (f"aws_access_key_id = {AWS_KEY}", "aws_access_key"),
        (f"token = '{GITHUB_TOKEN}'", "github_token"),
        (f"SLACK = {SLACK_TOKEN}", "slack_token"),
        ("-----BEGIN RSA PRIVATE KEY-----", "pem_block"),
        ('db_password = "correcthorsebattery"', "credential_assignment"),
        ("export API_KEY=abcdefgh12345678", "credential_assignment"),
        (f"blob = {ENTROPY_TOKEN}", "high_entropy"),
    ],
)
def test_scanner_finds_known_secret_shapes(line, kind):
    assert scan_line(line) == kind


@pytest.mark.parametrize(
    "line",
    [
        "def test_redaction_counts_are_recorded_for_every_kind(self):",
        "commit = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'",
        "digest = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'",
        "token = tokenizer.next_token()",
        "return torch.relu(self.handleUserLoginRequestFactory(x))",
        "task-specific scheduling",
    ],
)
def test_scanner_leaves_ordinary_code_alone(line):
    assert scan_line(line) is None


def test_pem_bodies_are_redacted_line_by_line():
    counter = RedactionCounter()
    text = "before\n-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\nabc\n-----END PRIVATE KEY-----\nafter"
    redacted = redact_text(text, counter)
    assert redacted.splitlines() == ["before"] + ["[REDACTED:pem_block]"] * 4 + ["after"]
    assert counter.as_dict() == {"pem_block": 4}


def test_diff_redaction_keeps_markers_and_headers():
    counter = RedactionCounter()
    diff = (
        "diff --git a/c.py b/c.py\n--- a/c.py\n+++ b/c.py\n@@ -1,2 +1,2 @@\n"
        f" keep = 1\n-old = 2\n+key = \"{OPENAI_KEY}\"\n"
    )
    redacted = redact_diff(diff, counter)
    assert OPENAI_KEY not in redacted
    assert "+[REDACTED:api_key_sk]" in redacted and "+++ b/c.py" in redacted and " keep = 1" in redacted
    assert counter.total == 1


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        (".env", "secret_pattern"),
        (".env.production", "secret_pattern"),
        ("config/server.pem", "secret_pattern"),
        ("keys/deploy.key", "secret_pattern"),
        ("id_rsa", "secret_pattern"),
        ("certs/client.p12", "secret_pattern"),
        ("aws_credentials.json", "secret_pattern"),
        ("secrets/config.yaml", "secret_pattern"),
        ("uv.lock", "noise"),
        ("web/package-lock.json", "noise"),
        ("src/model.py", None),
    ],
)
def test_secret_and_noise_path_patterns(path, reason):
    assert PathRules().exclusion(path) == reason


def test_learnloopignore_patterns(tmp_path):
    (tmp_path / ".learnloopignore").write_text("# private\ndata/\n*.csv\n/notes.md\nsrc/**/fixtures/*.json\n!keep.csv\n")
    rules = load_path_rules(tmp_path)
    assert rules.ignore_hash and rules.ignore_hash.startswith("sha256:")
    assert rules.exclusion("data/raw/a.py") == "learnloopignore"
    assert rules.exclusion("results.csv") == "learnloopignore"
    assert rules.exclusion("keep.csv") == "learnloopignore"  # negation is not supported, never widens
    assert rules.exclusion("notes.md") == "learnloopignore"
    assert rules.exclusion("docs/notes.md") is None
    assert rules.exclusion("src/a/b/fixtures/x.json") == "learnloopignore"
    assert rules.exclusion("src/model.py") is None


def test_capture_never_stores_secret_files_or_lines(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = TempRepo(tmp_path / "repo")
    repo.write("app.py", "def main():\n    return 0\n")
    repo.write(".learnloopignore", "private/\n")
    repo.commit("init", trailer=None)
    repo.write(".env", f"DATABASE_PASSWORD={ENV_SECRET}\n")
    repo.write("deploy.pem", "-----BEGIN PRIVATE KEY-----\nMIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu\n-----END PRIVATE KEY-----\n")
    repo.write("private/notes.py", f"leak = '{ENTROPY_TOKEN}'\n")
    repo.write(
        "app.py",
        "def main():\n"
        f"    client = make_client(api_key=\"{OPENAI_KEY}\")\n"
        f"    aws = '{AWS_KEY}'\n"
        "    total = 0\n    for step in range(3):\n        total += step\n    return total\n",
    )
    repo.commit(f"Wire the client\n\nUses token {GITHUB_TOKEN} for now.")
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    assert sweep(vault, config, clock=clock_at(0)).captured == 1
    store = ProjectStore.for_vault(vault)
    (diff,) = store.diffs()
    skipped = {entry["path"]: entry["reason"] for entry in json.loads(diff["skipped_files_json"])}
    assert skipped == {".env": "secret_pattern", "deploy.pem": "secret_pattern", "private/notes.py": "learnloopignore"}
    assert json.loads(diff["redactions_json"]) == {"api_key_sk": 2, "aws_access_key": 2, "github_token": 1}
    assert diff["redaction_count"] == 5
    bundle_bytes = canonical_source_raw_path(vault, diff["bundle_hash"]).read_bytes()
    bundle = load_bundle(vault, diff["bundle_hash"])
    assert [entry["path"] for entry in bundle["files"]] == ["app.py"]
    stored = bundle_bytes + store_path(vault).read_bytes()
    for wal in store_path(vault).parent.glob("*-wal"):
        stored += wal.read_bytes()
    for secret in (AWS_KEY, OPENAI_KEY, GITHUB_TOKEN, ENV_SECRET, ENTROPY_TOKEN, "MIIBOgIBAAJBAKj34"):
        assert secret.encode() not in stored
    assert b".env" not in bundle_bytes and b"deploy.pem" not in bundle_bytes


def test_hunk_header_context_is_scanned_and_coordinates_kept():
    # Git repeats the enclosing function's line after the hunk coordinates.
    counter = RedactionCounter()
    diff = (
        "diff --git a/c.py b/c.py\n--- a/c.py\n+++ b/c.py\n"
        f"@@ -10,3 +10,4 @@ def connect(key=\"{OPENAI_KEY}\"):\n"
        "     a = 1\n+    b = 2\n     return a\n"
        "@@ -30,2 +31,2 @@ def harmless():\n-    x = 1\n+    x = 2\n"
    )
    redacted = redact_diff(diff, counter)
    assert OPENAI_KEY not in redacted
    assert "@@ -10,3 +10,4 @@ [REDACTED:api_key_sk]" in redacted
    assert "@@ -30,2 +31,2 @@ def harmless():" in redacted
    assert counter.as_dict() == {"api_key_sk": 1}


def _hunk_header_secret_repo(tmp_path):
    repo = TempRepo(tmp_path / "repo")
    body = "".join(f"    step_{index} = {index}\n" for index in range(12))
    repo.write("conn.py", f'def connect(key="{OPENAI_KEY}"):\n{body}    return step_0\n')
    repo.commit("init", trailer=None)
    tail = "    total = step_0 + step_11\n    total *= 2\n    total -= step_5\n    total += step_7\n    return total\n"
    repo.write("conn.py", f'def connect(key="{OPENAI_KEY}"):\n{body}{tail}')
    repo.commit("Sum the first and last steps")
    return repo


def test_hunk_header_secrets_never_reach_the_store(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = _hunk_header_secret_repo(tmp_path)
    raw = repo.git("show", "HEAD")
    headers = [line for line in raw.splitlines() if line.startswith("@@")]
    assert OPENAI_KEY in headers[0]  # git repeats the signature in the hunk header
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    store = ProjectStore.for_vault(vault)
    (diff,) = store.diffs()
    stored = canonical_source_raw_path(vault, diff["bundle_hash"]).read_bytes() + store_path(vault).read_bytes()
    for wal in store_path(vault).parent.glob("*-wal"):
        stored += wal.read_bytes()
    assert OPENAI_KEY.encode() not in stored
    bundle = load_bundle(vault, diff["bundle_hash"])
    assert "@@ -" in bundle["files"][0]["diff"]
