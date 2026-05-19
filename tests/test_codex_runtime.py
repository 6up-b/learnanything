from __future__ import annotations

from pathlib import Path

from learnloop.codex.runtime import CodexAuthRequired, CodexHealthUnavailable, check_codex_runtime
from learnloop.config import CodexConfig
from learnloop.services.doctor import run_doctor
from learnloop.vault.loader import init_vault


def test_codex_runtime_reports_missing_checkout(tmp_path):
    report = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path="missing", revision="<pinned-commit>"),
    )

    assert report.status == "codex_missing"
    assert report.ready is False


def test_codex_runtime_reports_revision_mismatch(tmp_path):
    checkout = _checkout(tmp_path / "codex", revision="abc123")

    report = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path=str(checkout), revision="def456"),
        healthcheck=lambda _path, _config: None,
    )

    assert report.status == "codex_revision_mismatch"
    assert report.actual_revision == "abc123"


def test_codex_runtime_reports_auth_required(tmp_path):
    checkout = _checkout(tmp_path / "codex", revision="abc123")

    def auth_failure(_path: Path, _config: CodexConfig) -> None:
        raise CodexAuthRequired("login required")

    report = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path=str(checkout), revision="abc123"),
        healthcheck=auth_failure,
    )

    assert report.status == "codex_auth_required"
    assert report.message == "login required"


def test_codex_runtime_reports_unavailable_without_transport_or_failed_health(tmp_path):
    checkout = _checkout(tmp_path / "codex", revision="abc123")

    no_transport = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path=str(checkout), revision="abc123"),
    )
    failed = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path=str(checkout), revision="abc123"),
        healthcheck=lambda _path, _config: (_ for _ in ()).throw(CodexHealthUnavailable("down")),
    )

    assert no_transport.status == "codex_unavailable"
    assert failed.status == "codex_unavailable"
    assert failed.message == "down"


def test_codex_runtime_ready_when_checkout_revision_and_health_pass(tmp_path):
    checkout = _checkout(tmp_path / "codex", revision="abc123")

    report = check_codex_runtime(
        tmp_path,
        CodexConfig(checkout_path=str(checkout), revision="abc123"),
        healthcheck=lambda _path, _config: None,
    )

    assert report.status == "ready"
    assert report.ready is True


def test_doctor_includes_codex_runtime_without_failing_local_health(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault)

    report = run_doctor(vault)

    assert report.clean is True
    assert report.codex_runtime is not None
    assert report.codex_runtime.status == "codex_missing"


def _checkout(path: Path, *, revision: str) -> Path:
    path.mkdir(parents=True)
    (path / "HEAD").write_text(revision, encoding="utf-8")
    return path
