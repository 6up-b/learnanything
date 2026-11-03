"""The external HTTPS origin is independent of the loopback listener."""

import pytest
from pydantic import ValidationError

pytest.importorskip("starlette")
from starlette.testclient import TestClient
from typer.testing import CliRunner

from learnloop_mobile import cli
from learnloop_mobile.config import MobileConfig, load_config
from learnloop_mobile.host import create_app
from tests.helpers import create_basic_vault


@pytest.fixture(params=[443, 8445])
def deployment(tmp_path, request):
    paths = create_basic_vault(tmp_path / "vault")
    return MobileConfig(
        enabled=True, vault=paths.root, hostname="desktop.tail.ts.net",
        owner_login="owner@example.com", https_port=request.param,
    )


@pytest.mark.parametrize("https_port,authority", [(None, "desktop.tail.ts.net"), (8445, "desktop.tail.ts.net:8445")])
def test_load_https_port_and_canonical_origin(tmp_path, https_port, authority):
    path = tmp_path / "mobile.toml"
    path.write_text(
        f'vault = "{tmp_path.as_posix()}"\nhostname = "desktop.tail.ts.net"\n'
        'owner_login = "owner@example.com"\n'
        + (f'https_port = {https_port}\n' if https_port is not None else "")
    )
    config = load_config(path)
    assert config.https_port == (443 if https_port is None else https_port)
    assert config.port == 8765
    assert config.https_authority == authority
    assert config.base_url == f"https://{authority}"


@pytest.mark.parametrize("port", [0, -1, 65536, True, 8445.0, "8445"])
def test_invalid_https_ports_are_rejected(tmp_path, port):
    with pytest.raises(ValidationError):
        MobileConfig(vault=tmp_path, hostname="desktop.tail.ts.net",
                     owner_login="owner@example.com", https_port=port)


def test_hostname_stays_a_bare_hostname(tmp_path):
    with pytest.raises(ValidationError):
        MobileConfig(vault=tmp_path, hostname="desktop.tail.ts.net:8445",
                     owner_login="owner@example.com")


def test_configured_https_origin_can_pair_and_read_status(deployment):
    identity = {"Tailscale-User-Login": deployment.owner_login, "Origin": deployment.base_url}
    with TestClient(create_app(deployment), base_url=deployment.base_url) as client:
        assert client.get("/pair", headers=identity).status_code == 200
        from learnloop.capture import create_pairing
        pending = create_pairing(cli._repo(deployment), scope="capture")
        response = client.post("/pair", json={"code": pending["code"]}, headers=identity)
        assert response.status_code == 200
        token = response.json()["token"]
        status = client.get("/api/v1/status", headers={**identity, "Authorization": f"Bearer {token}"})
        assert status.status_code == 200
        assert status.json()["schema_ok"]


@pytest.mark.parametrize("header,value,code", [
    ("Host", "desktop.tail.ts.net:9445", "invalid_host"),
    ("Host", "other.tail.ts.net:8445", "invalid_host"),
    ("Origin", "https://desktop.tail.ts.net:9445", "invalid_origin"),
    ("Origin", "http://desktop.tail.ts.net:8445", "invalid_origin"),
    ("Origin", "https://other.tail.ts.net:8445", "invalid_origin"),
    ("Origin", "null", "invalid_origin"),
])
def test_different_https_origins_stay_rejected(deployment, header, value, code):
    with TestClient(create_app(deployment), base_url=deployment.base_url) as client:
        response = client.get("/pair", headers={"Tailscale-User-Login": deployment.owner_login, header: value})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == code


def test_other_port_is_rejected_even_on_the_same_hostname(deployment):
    other_authority = (deployment.hostname if deployment.https_port != 443
                       else f"{deployment.hostname}:8445")
    with TestClient(create_app(deployment), base_url=deployment.base_url) as client:
        for header, value in (("Host", other_authority), ("Origin", f"https://{other_authority}")):
            assert client.get("/pair", headers={"Tailscale-User-Login": deployment.owner_login,
                                               header: value}).status_code == 403


def test_pairing_command_uses_configured_base_url(deployment, monkeypatch):
    monkeypatch.setattr(cli, "_config", lambda _: deployment)
    result = CliRunner().invoke(cli.app, ["pair", "--scope", "capture"])
    assert result.exit_code == 0, result.output
    assert f"{deployment.base_url}/pair#s=" in result.output


def test_https_port_does_not_change_loopback_binding(deployment, monkeypatch):
    import uvicorn
    monkeypatch.setattr(cli, "_config", lambda _: deployment)
    monkeypatch.setattr("learnloop_mobile.host.create_app", lambda _: object())
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    result = CliRunner().invoke(cli.app, ["serve"])
    assert result.exit_code == 0, result.output
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == deployment.port == 8765
