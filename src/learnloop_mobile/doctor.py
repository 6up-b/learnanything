"""Read-only deployment diagnostics; never edits Serve, policy, or the vault."""

from __future__ import annotations

import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tomllib
from typing import Any
from urllib.parse import urlsplit

from learnloop.config.loader import global_settings_path
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository


def _command(args: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=30, env=env,
    )
    return result.stdout


def read_unit_environment(path: Path) -> dict[str, str]:
    """Parse the deliberately small, literal EnvironmentFile format we ship.

    No shell evaluation, interpolation, ``export``, or multiline values. Refuse
    unsupported syntax rather than claim to have checked a different environment.
    """
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError("Use literal KEY=value entries in mobile.env")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError("Unclosed quote in mobile.env")
            value = value[1:-1]
        if "\\" in value or "\x00" in value:
            raise ValueError("Escapes and multiline entries are unsupported in mobile.env")
        values[key] = value
    return values


def _reaches_backend(target: Any, port: int) -> bool:
    """Whether a Serve ``Proxy``/``TCPForward`` target could reach ``port``.

    Any host is counted, not only loopback names: a second route to the same
    port is refused rather than reasoned about. Unparseable targets fail closed.
    """
    if not isinstance(target, str) or not target.strip():
        return True
    value = target.strip()
    if value.startswith("unix:"):
        return False  # A Unix socket cannot be this TCP listener.
    if value.isdecimal():
        return int(value) == port
    if "://" not in value:
        value = "tcp://" + value
    try:
        parsed = urlsplit(value)
        found = parsed.port
    except ValueError:
        return True
    if found is None:
        found = {"http": 80, "https": 443, "https+insecure": 443}.get(parsed.scheme)
    return found is None or found == port


def _serve_configs(data: dict[str, Any], label: str = "background"):
    """The background config plus every foreground session and Service config."""
    yield label, data
    for name, nested in (data.get("Foreground") or {}).items():
        yield from _serve_configs(nested, f"foreground:{name}")
    for name, nested in (data.get("Services") or {}).items():
        yield from _serve_configs(nested, f"service:{name}")


def serve_checks(data: dict[str, Any], hostname: str, port: int) -> tuple[bool, bool]:
    """Require exactly one route to the backend: background HTTPS Serve on :443.

    Every mapping is inspected, including foreground sessions and Services. A
    raw TCP forward (with or without TLS termination) would bypass Serve's
    identity headers, and a second web route widens exposure, so any other route
    to the backend port fails. Funnel must be off on :443 and on every port that
    carries a route to the backend.
    """
    expected_route = ("background", "web", f"{hostname}:443", "/")
    routes: list[tuple[str, str, str, str]] = []
    funnels: list[str] = []
    for label, config in _serve_configs(data):
        for tcp_port, handler in (config.get("TCP") or {}).items():
            if "TCPForward" in (handler or {}) and _reaches_backend(handler["TCPForward"], port):
                routes.append((label, "tcp", f":{tcp_port}", ""))
        for host_port, web in (config.get("Web") or {}).items():
            for path, handler in ((web or {}).get("Handlers") or {}).items():
                if "Proxy" in (handler or {}) and _reaches_backend(handler["Proxy"], port):
                    routes.append((label, "web", str(host_port), str(path)))
        funnels += [str(address) for address, enabled in (config.get("AllowFunnel") or {}).items()
                    if enabled]
    tcp = (data.get("TCP") or {}).get("443") or {}
    handlers = ((data.get("Web") or {}).get(f"{hostname}:443") or {}).get("Handlers") or {}
    serve = (
        tcp == {"HTTPS": True}
        and handlers == {"/": {"Proxy": f"http://127.0.0.1:{port}"}}
        and routes == [expected_route]
    )
    exposed_ports = {"443"} | {route[2].rsplit(":", 1)[-1] for route in routes}
    no_funnel = not any(address.rsplit(":", 1)[-1] in exposed_ports for address in funnels)
    return serve, no_funnel


def loopback_listener(output: str, port: int) -> bool:
    addresses = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[3].rsplit(":", 1)[-1] == str(port):
            addresses.append(fields[3].rsplit(":", 1)[0])
    return bool(addresses) and all(address == "127.0.0.1" for address in addresses)


def _unit_readiness(vault: Path, values: dict[str, str]) -> dict[str, Any]:
    # Do not inherit the invoking shell's provider keys. The unit's fixed PATH
    # and HOME plus its EnvironmentFile are the entire readiness environment.
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        **values,
    }
    result = _command(
        [sys.executable, "-m", "learnloop_mobile.doctor", str(vault)],
        env=environment,
    )
    return json.loads(result)


def policy_example() -> dict[str, Any]:
    """An optional narrowing recipe (D12: not required). Placeholders only;
    never discover or alter an owner's access policy."""
    return {
        "hosts": {
            "learnloop-phone": "<phone-tailnet-IP>",
            "learnloop-desktop": "<desktop-tailnet-IP>",
            "learnloop-other": "<other-device-tailnet-IP>",
        },
        "grants": [{
            "src": ["learnloop-phone"],
            "dst": ["learnloop-desktop"],
            "ip": ["tcp:443"],
        }],
        "tests": [
            {"src": "learnloop-phone", "accept": ["learnloop-desktop:443"]},
            {"src": "learnloop-other", "deny": ["learnloop-desktop:443"]},
        ],
    }


def doctor(config: Any, *, env_file: Path | None = None) -> dict[str, Any]:
    """Return verified/failed checks plus non-fatal warnings, never optimistic guesses."""
    from learnloop.capture import list_devices, report_orphan_originals
    from learnloop_mobile.config import sqlite_path

    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "verified" if passed else "failed", "detail": detail})

    vault = Path(config.vault)
    try:
        database = sqlite_path(config)
    except (OSError, ValueError, TypeError):
        database = None
    check("vault", database is not None and vault.is_dir() and database.is_file(), str(vault))
    try:
        expected = {migration.version for migration in discover_migrations()}
        schema_ok = database is not None and applied_versions(database) == expected
    except Exception:
        schema_ok = False
    check(
        "schema", schema_ok,
        "Schema matches this host." if schema_ok else
        f"Open the desktop app or run learnloop doctor --vault {vault} once to migrate.",
    )
    try:
        check("loopback", loopback_listener(_command(["ss", "-H", "-ltn"]), config.port),
              f"All listeners on port {config.port} must bind 127.0.0.1; start the unit first.")
    except (OSError, subprocess.SubprocessError):
        check("loopback", False, "Could not inspect listeners with ss.")
    try:
        data = json.loads(_command(["tailscale", "serve", "status", "--json"]))
        serve, private = serve_checks(data, config.hostname, config.port)
        check("serve", serve,
              f"Require HTTPS :443 / → http://127.0.0.1:{config.port} as the only Serve route "
              f"(background, foreground or Service) to port {config.port}; no TCP forwards.")
        check("funnel", private, f"Funnel must be off on :443 and on any route to port {config.port}.")
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        check("serve", False, "Could not verify tailscale serve status --json.")
        check("funnel", False, "Funnel exposure is unverified.")

    env_file = env_file or global_settings_path().with_name("mobile.env")
    try:
        mode_ok = (
            env_file.is_file() and stat.S_IMODE(env_file.stat().st_mode) == 0o600
            and not env_file.is_symlink()
        )
        check("environment_permissions", mode_ok, "mobile.env must be a regular, non-symlink file with mode 0600.")
        if mode_ok:
            readiness = _unit_readiness(vault, read_unit_environment(env_file))
            check("grading", bool(readiness["ready"]),
                  f"Unit environment grading readiness: {readiness['status']} (not needed for M1 capture).")
        else:
            check("grading", False, "Not checked until mobile.env permissions are safe.")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        check("environment_permissions", False, "Cannot read a valid mobile.env.")
        check("grading", False, "Unit environment readiness could not be checked.")

    devices: list[dict[str, Any]] = []
    orphans: Any = []
    if schema_ok:
        try:
            repository = Repository.attach(database, read_only=True)
            devices = list_devices(repository)
            orphans = report_orphan_originals(repository, root=vault)
            check("orphan_originals", not orphans,
                  f"{len(orphans)} unreferenced originals; report only, nothing deleted.")
        except Exception:
            check("capture_storage", False, "Could not inspect devices and originals read-only.")

    tailnet_devices = []
    try:
        status = json.loads(_command(["tailscale", "status", "--json"]))
        own_user = status.get("Self", {}).get("UserID")
        for peer in status.get("Peer", {}).values():
            if peer.get("UserID") != own_user:
                continue
            ips = peer.get("TailscaleIPs", [])
            if not ips:
                continue
            identity = json.loads(_command(["tailscale", "whois", "--json", ips[0]]))
            tailnet_devices.append({
                "name": peer.get("HostName"), "ips": ips, "tags": peer.get("Tags", []),
                "login": identity.get("UserProfile", {}).get("LoginName"),
                "untagged": not peer.get("Tags"),
            })
        check("tailnet_devices", True, "The phone must remain user-owned and untagged.")
        # Spec §4.7: surfaced, never fatal (e.g. broken MagicDNS on the desktop).
        for warning in status.get("Health") or []:
            checks.append({"name": "tailscale_health", "status": "warning", "detail": str(warning)})
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        check("tailnet_devices", False, "Could not list owner devices using tailscale status/whois.")
    # The tailnet policy is deliberately not checked (spec §4.7, D12): the
    # tailnet is single-user and general phone → desktop access is intended.
    return {
        "ok": not any(item["status"] == "failed" for item in checks),
        "checks": checks, "devices": devices, "tailnet_devices": tailnet_devices,
        "orphan_originals": orphans,
        "optional_policy_example": {
            "note": "Optional and not needed for acceptance (D12). LearnLoop never checks or edits "
                    "tailnet policy. Use only if you want to narrow access to this port yourself.",
            "policy": policy_example(),
        },
    }


def _readiness_main(vault: Path) -> None:
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.config.compat import normalize_config_input
    from learnloop.config.schema import LearnLoopConfig

    # Unlike load_config, do not silently supplement the unit environment from
    # vault .env or global settings.env. No LoadedVault or sidecar is constructed.
    with (vault / "learnloop.toml").open("rb") as handle:
        config = LearnLoopConfig.model_validate(normalize_config_input(tomllib.load(handle)))
    resolved = ready_client_for_task(vault, config, "grading")
    print(json.dumps({"ready": resolved.ready, "status": resolved.runtime.status}))


if __name__ == "__main__":
    _readiness_main(Path(sys.argv[1]))
