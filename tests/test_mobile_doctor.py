from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from learnloop_mobile.doctor import (
    _unit_readiness,
    loopback_listener,
    policy_example,
    read_unit_environment,
    serve_checks,
)


def serve_config() -> dict:
    return {
        "TCP": {"443": {"HTTPS": True}},
        "Web": {"desktop.tail.ts.net:443": {
            "Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}},
        }},
        "AllowFunnel": {"desktop.tail.ts.net:443": False},
    }


def test_serve_requires_private_https_proxy():
    data = serve_config()
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (True, True)
    data["AllowFunnel"]["desktop.tail.ts.net:443"] = True
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (True, False)
    data["TCP"]["443"] = {"TCPForward": "127.0.0.1:8765"}
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (False, False)


def test_serve_refuses_wrong_host_port_and_extra_handlers():
    data = serve_config()
    assert serve_checks(data, "other.tail.ts.net", 8765)[0] is False
    assert serve_checks(data, "desktop.tail.ts.net", 8888)[0] is False
    data["Web"]["desktop.tail.ts.net:443"]["Handlers"]["/other"] = {"Path": "/private"}
    assert serve_checks(data, "desktop.tail.ts.net", 8765)[0] is False
    assert serve_checks({}, "desktop.tail.ts.net", 8765)[0] is False


@pytest.mark.parametrize("address,expected", [
    ("127.0.0.1", True), ("0.0.0.0", False), ("*", False),
    ("[::]", False), ("100.64.0.1", False),
])
def test_loopback_inspects_actual_listeners(address, expected):
    assert loopback_listener(f"LISTEN 0 128 {address}:8765 0.0.0.0:*", 8765) is expected
    assert not loopback_listener("", 8765)
    assert not loopback_listener(
        "LISTEN 0 128 127.0.0.1:8765 0.0.0.0:*\nLISTEN 0 128 [::]:8765 [::]:*",
        8765,
    )


def test_environment_parser_never_evaluates_shell(tmp_path):
    path = tmp_path / "mobile.env"
    path.write_text("# ignored\nONE=literal\nTWO='space value'\nTHREE=$(echo not-executed)\n")
    assert read_unit_environment(path) == {
        "ONE": "literal", "TWO": "space value", "THREE": "$(echo not-executed)",
    }
    path.write_text("export KEY=value\n")
    with pytest.raises(ValueError):
        read_unit_environment(path)


def test_readiness_uses_only_unit_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "shell-secret-not-for-unit")
    seen = {}

    def run(args, **kwargs):
        seen.update(kwargs)
        assert args[-1] == str(tmp_path)
        return subprocess.CompletedProcess(args, 0, json.dumps({"ready": True, "status": "ready"}))

    monkeypatch.setattr(subprocess, "run", run)
    assert _unit_readiness(tmp_path, {"UNIT_ONLY": "test"})["ready"]
    assert "OPENAI_API_KEY" not in seen["env"]
    assert seen["env"]["UNIT_ONLY"] == "test"
    assert seen["timeout"] == 30


def test_policy_example_has_accept_and_deny_without_broad_grants():
    policy = policy_example()
    assert policy["grants"] == [{
        "src": ["learnloop-phone"], "dst": ["learnloop-desktop"], "ip": ["tcp:443"],
    }]
    assert policy["tests"][1]["deny"] == ["learnloop-desktop:443"]


def test_unit_does_not_restart_schema_mismatch_or_inherit_shell():
    unit = Path("deploy/learnloop-mobile.service").read_text()
    assert "RestartPreventExitStatus=78" in unit
    assert "TimeoutStopSec=300" in unit
    assert "EnvironmentFile=%h/.config/learnloop/mobile.env" in unit
    assert "/.venv/bin/learnloop-mobile serve" in unit
    assert "sh -c" not in unit


def test_doctor_checks_fake_deployment_without_mutating_vault(monkeypatch, tmp_path):
    import learnloop_mobile.doctor as module
    from learnloop.db.connection import connect
    from learnloop_mobile.config import MobileConfig
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    config = MobileConfig(
        enabled=True, vault=paths.root, hostname="desktop.tail.ts.net",
        owner_login="owner@example.com",
    )
    environment = tmp_path / "mobile.env"
    environment.write_text("# no M1 provider keys needed\n")
    environment.chmod(0o600)
    calls = []

    def command(args, **kwargs):
        calls.append(args)
        if args[0] == "ss":
            return "LISTEN 0 128 127.0.0.1:8765 0.0.0.0:*"
        if args[1:3] == ["serve", "status"]:
            return json.dumps(serve_config())
        if args[1] == "status":
            return json.dumps({"Self": {"UserID": 1}, "Peer": {
                "phone": {"HostName": "phone", "UserID": 1, "TailscaleIPs": ["100.64.0.2"]},
            }})
        if args[1] == "whois":
            return json.dumps({"UserProfile": {"LoginName": "owner@example.com"}})
        return json.dumps({"ready": True, "status": "ready"})

    monkeypatch.setattr(module, "_command", command)
    with connect(paths.sqlite_path, read_only=True) as connection:
        before = list(connection.iterdump())
    result = module.doctor(config, env_file=environment)
    assert result["ok"], result
    assert result["tailnet_devices"][0]["untagged"]
    assert any(check["status"] == "owner must confirm" for check in result["checks"])
    assert all("set" not in command for command in calls)
    with connect(paths.sqlite_path, read_only=True) as connection:
        assert list(connection.iterdump()) == before
