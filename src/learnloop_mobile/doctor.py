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


def serve_checks(data: dict[str, Any], hostname: str, port: int) -> tuple[bool, bool]:
    """Require HTTPS Serve, not a TCP forward; inspect Funnel independently."""
    tcp = data.get("TCP", {}).get("443", {})
    web = data.get("Web", {}).get(f"{hostname}:443", {})
    handlers = web.get("Handlers", {})
    expected = {"Proxy": f"http://127.0.0.1:{port}"}
    serve = (
        tcp == {"HTTPS": True}
        and handlers == {"/": expected}
    )
    no_funnel = not any(
        enabled for address, enabled in data.get("AllowFunnel", {}).items()
        if address.rsplit(":", 1)[-1] == "443"
    )
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
    """Placeholders only: never discover or alter an owner's access policy."""
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
    """Return verified/failed/owner-must-confirm checks, never optimistic guesses."""
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
        check("serve", serve, f"Require HTTPS :443 / → http://127.0.0.1:{config.port}.")
        check("funnel", private, "Funnel must be off on :443.")
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
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        check("tailnet_devices", False, "Could not list owner devices using tailscale status/whois.")
    checks.append({
        "name": "effective_policy", "status": "owner must confirm",
        "detail": "Grants are a union. Remove or narrow overlapping broad rules, including default allow-all. "
                  "Apply the example with real IPs and run its accept/deny policy tests. LearnLoop never edits policy.",
    })
    return {
        "ok": not any(item["status"] == "failed" for item in checks),
        "checks": checks, "devices": devices, "tailnet_devices": tailnet_devices,
        "orphan_originals": orphans, "policy": policy_example(),
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
