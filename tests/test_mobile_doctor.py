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


def serve_config(https_port: int = 443) -> dict:
    return {
        "TCP": {str(https_port): {"HTTPS": True}},
        "Web": {f"desktop.tail.ts.net:{https_port}": {
            "Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}},
        }},
        "AllowFunnel": {f"desktop.tail.ts.net:{https_port}": False},
    }


def test_serve_requires_private_https_proxy():
    data = serve_config()
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (True, True)
    data["AllowFunnel"]["desktop.tail.ts.net:443"] = True
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (True, False)
    data["TCP"]["443"] = {"TCPForward": "127.0.0.1:8765"}
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (False, False)


def _with(extra: dict) -> dict:
    data = serve_config()
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key] = {**data[key], **value}
        else:
            data[key] = value
    return data


@pytest.mark.parametrize("extra,expected", [
    # A raw TLS-terminated TCP forward on another port, with Funnel: public, and
    # the backend sees client-supplied identity headers.
    ({"TCP": {"8443": {"TCPForward": "127.0.0.1:8765", "TerminateTLS": "desktop.tail.ts.net"}},
      "AllowFunnel": {"desktop.tail.ts.net:8443": True}}, (False, False)),
    # The same raw forward without Funnel still bypasses Serve's identity headers.
    ({"TCP": {"8443": {"TCPForward": "127.0.0.1:8765", "TerminateTLS": "desktop.tail.ts.net"}}},
      (False, True)),
    ({"TCP": {"10000": {"TCPForward": "localhost:8765"}}}, (False, True)),
    # A second HTTPS web route to the same backend, publicly funnelled.
    ({"TCP": {"8443": {"HTTPS": True}},
      "Web": {"desktop.tail.ts.net:8443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}}}},
      "AllowFunnel": {"desktop.tail.ts.net:8443": True}}, (False, False)),
    ({"TCP": {"8443": {"HTTPS": True}},
      "Web": {"desktop.tail.ts.net:8443": {"Handlers": {"/x": {"Proxy": "http://localhost:8765/"}}}}},
      (False, True)),
    # Foreground sessions (`tailscale serve` without --bg) are separate configs.
    ({"Foreground": {"session": {
        "TCP": {"8443": {"TCPForward": "127.0.0.1:8765"}},
        "AllowFunnel": {"desktop.tail.ts.net:8443": True}}}}, (False, False)),
    ({"Foreground": {"session": {
        "TCP": {"443": {"HTTPS": True}},
        "Web": {"desktop.tail.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}}}},
        "AllowFunnel": {"desktop.tail.ts.net:443": True}}}}, (False, False)),
    # Tailscale Services carry their own TCP/Web mappings.
    ({"Services": {"svc:learnloop": {"TCP": {"443": {"HTTPS": True}}, "Web": {
        "learnloop.tail.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}}}}}}},
      (False, True)),
    # An unparseable forward target fails closed.
    ({"TCP": {"9000": {"TCPForward": "not a target"}}}, (False, True)),
    # Unrelated mappings, even funnelled ones, do not reach this backend.
    ({"TCP": {"8443": {"HTTPS": True}},
      "Web": {"desktop.tail.ts.net:8443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:3000"}}}},
      "AllowFunnel": {"desktop.tail.ts.net:8443": True}}, (True, True)),
    ({"TCP": {"2222": {"TCPForward": "127.0.0.1:22"}}}, (True, True)),
])
def test_serve_rejects_any_second_path_to_the_backend(extra, expected):
    assert serve_checks(_with(extra), "desktop.tail.ts.net", 8765) == expected


def test_serve_refuses_wrong_host_or_backend_but_allows_unrelated_handlers():
    data = serve_config()
    assert serve_checks(data, "other.tail.ts.net", 8765)[0] is False
    assert serve_checks(data, "desktop.tail.ts.net", 8888)[0] is False
    data["Web"]["desktop.tail.ts.net:443"]["Handlers"]["/other"] = {"Path": "/private"}
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (True, True)
    data["Web"]["desktop.tail.ts.net:443"]["Handlers"]["/alias"] = {"Proxy": "http://127.0.0.1:8765"}
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (False, True)
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


def shared_serve_config() -> dict:
    """LearnLoop shares a node with an existing public service and Tend."""
    data = serve_config(8445)
    for port, backend in ((443, 8768), (8443, 9842), (8444, 8797)):
        data["TCP"][str(port)] = {"HTTPS": True}
        data["Web"][f"desktop.tail.ts.net:{port}"] = {
            "Handlers": {"/": {"Proxy": f"http://127.0.0.1:{backend}"}},
        }
    data["AllowFunnel"]["desktop.tail.ts.net:443"] = True
    return data


def test_custom_https_port_coexists_with_public_and_private_services():
    data = shared_serve_config()
    before = json.dumps(data, sort_keys=True)
    assert serve_checks(data, "desktop.tail.ts.net", 8765, https_port=8445) == (True, True)
    assert json.dumps(data, sort_keys=True) == before
    # The configured external port must match, even when 443 is valid HTTPS.
    assert serve_checks(data, "desktop.tail.ts.net", 8765) == (False, False)
    data["AllowFunnel"]["desktop.tail.ts.net:8445"] = True
    assert serve_checks(data, "desktop.tail.ts.net", 8765, https_port=8445) == (True, False)


@pytest.mark.parametrize("scope", ["background", "foreground", "service"])
@pytest.mark.parametrize("transport", ["web", "tcp"])
@pytest.mark.parametrize("funnel", [False, True])
def test_custom_https_port_still_rejects_backend_aliases(scope, transport, funnel):
    data = shared_serve_config()
    alias = {
        "TCP": {"10000": {"HTTPS": True} if transport == "web" else {
            "TCPForward": "127.0.0.1:8765", "TerminateTLS": "desktop.tail.ts.net",
        }},
        "AllowFunnel": {"desktop.tail.ts.net:10000": funnel},
    }
    if transport == "web":
        alias["Web"] = {"desktop.tail.ts.net:10000": {
            "Handlers": {"/alias": {"Proxy": "http://localhost:8765"}},
        }}
    if scope == "background":
        for key, value in alias.items():
            data.setdefault(key, {}).update(value)
    else:
        data["Foreground" if scope == "foreground" else "Services"] = {"alias": alias}
    assert serve_checks(data, "desktop.tail.ts.net", 8765, https_port=8445) == (False, not funnel)


def test_unit_does_not_restart_schema_mismatch_or_inherit_shell():
    unit = Path("deploy/learnloop-mobile.service").read_text()
    assert "RestartPreventExitStatus=78" in unit
    assert "TimeoutStopSec=300" in unit
    assert "EnvironmentFile=%h/.config/learnloop/mobile.env" in unit
    assert "/.venv/bin/learnloop-mobile serve" in unit
    assert "sh -c" not in unit


@pytest.mark.parametrize("https_port", [443, 8445])
def test_doctor_checks_fake_deployment_without_mutating_vault(monkeypatch, tmp_path, https_port):
    import learnloop_mobile.doctor as module
    from learnloop.db.connection import connect
    from learnloop_mobile.config import MobileConfig
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    config = MobileConfig(
        enabled=True, vault=paths.root, hostname="desktop.tail.ts.net",
        owner_login="owner@example.com", https_port=https_port,
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
            return json.dumps(serve_config() if https_port == 443 else shared_serve_config())
        if args[1] == "status":
            return json.dumps({"Self": {"UserID": 1}, "Health": ["MagicDNS is not working"], "Peer": {
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
    # D12: the tailnet policy is neither checked nor presented as required work.
    assert {check["status"] for check in result["checks"]} <= {"verified", "warning"}
    assert not any("polic" in check["name"] for check in result["checks"])
    assert "Optional" in result["optional_policy_example"]["note"]
    policy = result["optional_policy_example"]["policy"]
    assert policy == policy_example(https_port)
    assert policy["grants"][0]["ip"] == [f"tcp:{https_port}"]
    assert policy["tests"][0]["accept"] == [f"learnloop-desktop:{https_port}"]
    assert policy["tests"][1]["deny"] == [f"learnloop-desktop:{https_port}"]
    messages = {check["name"]: check["detail"] for check in result["checks"]}
    assert f"HTTPS :{https_port} /" in messages["serve"]
    assert f"off on :{https_port}" in messages["funnel"]
    # §4.7 health warnings are surfaced without failing the deployment.
    assert {"name": "tailscale_health", "status": "warning",
            "detail": "MagicDNS is not working"} in result["checks"]
    assert all("set" not in command for command in calls)
    with connect(paths.sqlite_path, read_only=True) as connection:
        assert list(connection.iterdump()) == before
