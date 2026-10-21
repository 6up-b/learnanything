"""A fake ``codex`` CLI for the isolated turn's launch check.

``write_fake_codex`` writes an executable that answers ``mcp list --json``,
``features list`` and ``app-server`` the way codex-cli 0.163.0 does in the
parts the check reads (found 2026-10-15, docs/reviews/codex-isolation-app-servers.md):

* ``mcp list --json`` lists the servers a config file defines AND the ones an
  enabled plugin brings; ``-c features.plugins=false`` removes the plugin ones;
* ``-c mcp_servers.<name>.enabled=false`` for a server no config file defines
  creates a table without a transport, and every subcommand (the app-server
  launch included) then fails with ``invalid transport in `mcp_servers.<name>```;
* ``features list`` prints ``name  stage  true|false`` rows; an unknown
  ``-c features.<key>`` is ignored;
* ``-c``/``--config`` (as ``-c V``, ``-cV``, ``-c=V``, ``--config V``,
  ``--config=V``), ``--enable`` and ``--disable`` are global options, read
  wherever they stand (after ``app-server`` too); a later ``-c`` wins, and the
  feature toggles apply after every ``-c`` (enables, then disables), as
  0.163.0's ``cli/src/main.rs`` folds them in;
* ``debug models --bundled`` prints the model catalog shipped in the binary
  (``catalog``, default :func:`bundled_catalog`: 0.163.0's tool fields);
* ``app-server`` prints what it would load: the MCP servers left on and the
  features left on.

``stub_isolation_probe`` is the same model in process, for tests that only
need the check to pass. ``FakeSdkClient`` and ``FakeApprovalMode`` are the SDK
seams the locked-down turn needs (security stage 2026-10-21): a fake
``openai_codex`` module exports ``ApprovalMode`` and its ``Codex`` carries a
``_client`` with an approval handler and a notification router.
"""

from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any

#: The feature rows the fake prints (the real CLI prints every known feature).
FEATURES = ("apps", "plugins", "remote_plugin", "shell_tool", "unified_exec", "multi_agent", "hooks", "memories")

#: The tool fields of codex-cli 0.163.0's bundled ``gpt-5.6-sol`` entry (``codex debug models --bundled``).
BUNDLED_TOOL_FIELDS = {
    "tool_mode": "code_mode_only",
    "apply_patch_tool_type": "freeform",
    "multi_agent_version": "v2",
    "shell_type": "unified_exec",
    "web_search_tool_type": "text_and_image",
    "supports_search_tool": True,
    "experimental_supported_tools": [],
    "node_repl_disabled": False,
    "include_apps_usage_instructions": True,
}


def bundled_catalog(*slugs: str, **fields: Any) -> dict[str, Any]:
    """A ``debug models --bundled`` catalog listing ``slugs`` (default the default model) with 0.163.0's tools."""

    from learnloop.config.schema import DEFAULT_CODEX_MODEL

    names = [slug for slug in slugs if slug] or [DEFAULT_CODEX_MODEL]
    return {"models": [{"slug": slug, **BUNDLED_TOOL_FIELDS, **fields} for slug in dict.fromkeys(names)]}


class FakeApprovalMode(str, Enum):
    deny_all = "deny_all"
    auto_review = "auto_review"


class FakeRouter:
    def __init__(self) -> None:
        self.routed: list[Any] = []

    def route_notification(self, notification: Any) -> None:
        self.routed.append(notification)


class FakeSdkClient:
    """The real SDK client's seams: ``_approval_handler`` (accept-all by default) and ``_router``."""

    def __init__(self) -> None:
        self._router = FakeRouter()
        self._approval_handler = self._default_approval_handler

    @staticmethod
    def _default_approval_handler(method: str, params: Any) -> dict[str, Any]:
        if method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
            return {"decision": "accept"}
        return {}

    def notify(self, method: str, **params: Any) -> None:
        """Deliver one app-server notification the way the SDK's reader thread does (camelCase params)."""

        self._router.route_notification(SimpleNamespace(method=method, payload=SimpleNamespace(params=params)))

    def server_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._approval_handler(method, params)

_FAKE_CODEX = r'''
import json
import sys
import time
from pathlib import Path

spec = json.loads(Path(__file__).with_name("codex-spec.json").read_text(encoding="utf-8"))
argv = sys.argv[1:]
overrides, toggles, args = [], [], []
index = 0
while index < len(argv):
    arg = argv[index]
    if arg in ("-c", "--config", "--enable", "--disable") and index + 1 < len(argv):
        value, index = argv[index + 1], index + 2
    elif arg.startswith(("--config=", "--enable=", "--disable=")):
        arg, value = arg.split("=", 1)
        index += 1
    elif arg.startswith("-c") and not arg.startswith("--"):
        arg, value = "-c", arg[2:][1:] if arg[2:].startswith("=") else arg[2:]
        index += 1
    else:
        args.append(arg)
        index += 1
        continue
    if arg in ("-c", "--config"):
        overrides.append(value)
    else:
        toggles.append([arg[2:], value])
with open(spec["log"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"overrides": overrides, "toggles": toggles, "command": args}) + "\n")
for rejected in spec.get("rejects_overrides", ()):
    if any(override.split("=", 1)[0] == rejected for override in overrides):
        sys.stderr.write("Error: unknown configuration field `%s`\n" % rejected)
        sys.exit(1)
effective = overrides + ["features.%s=true" % f for kind, f in toggles if kind == "enable"]
effective += ["features.%s=false" % f for kind, f in toggles if kind == "disable"]
values = dict(override.split("=", 1) for override in effective)
off = {key.split(".", 1)[1] for key, value in values.items() if key.startswith("features.") and value == "false"}
off -= set(spec.get("ignored_features", ()))
config = spec.get("config_servers", {})
for key in values:
    if key.startswith("mcp_servers.") and key.endswith(".enabled"):
        name = key[len("mcp_servers."):-len(".enabled")]
        # Codex splits the key on "." (a dotted name addresses another table).
        name = name.split(".")[0] if "." in name else name
        if name not in config and spec.get("rejects_tableless_servers", True):
            sys.stderr.write(
                "Error: failed to load bootstrap configuration\n\nCaused by:\n"
                "    invalid transport\n    in `mcp_servers.%s`\n" % name
            )
            sys.exit(1)

command = " ".join(args[:2])
behaviour = spec.get("behaviour", {}).get(command, "ok")
if behaviour == "hang":
    time.sleep(30)
if behaviour == "slow":
    time.sleep(spec.get("slow_seconds", 0.5))
if behaviour == "fail":
    sys.stderr.write("Error: failed to load configuration\n    secret = \"LEAKED-CONFIG-LINE\"\n")
    sys.exit(2)
if behaviour == "garbage":
    print("not json")
    sys.exit(0)

servers = dict(spec.get("builtin_servers", {}))
if "plugins" not in off:
    servers.update(spec.get("plugin_servers", {}))
servers.update(config)
for name in config:
    setting = values.get("mcp_servers.%s.enabled" % name)
    if setting is not None:
        servers[name] = setting == "true"

if command == "mcp list":
    entries = []
    for name in sorted(servers):
        enabled = servers[name]
        entry = {"name": name, "enabled": enabled, "transport": {"type": "stdio", "command": "SECRET-COMMAND"}}
        if not spec.get("old_shape"):
            entry.update({"disabled_reason": None, "startup_timeout_sec": None, "tool_timeout_sec": None,
                          "auth_status": "unsupported"})
        entries.append(entry)
    print(json.dumps(entries, indent=2))
elif command == "features list":
    for feature in spec["features"]:
        if feature not in spec.get("missing_features", ()):
            print("%-24s stable   %s" % (feature, "false" if feature in off else "true"))
elif command == "debug models":
    print(json.dumps(spec["catalog"]))
elif args[:1] == ["app-server"]:
    print(json.dumps({"launched": True, "servers_on": sorted(name for name, on in servers.items() if on),
                      "features_on": sorted(f for f in spec["features"] if f not in off)}))
else:
    sys.stderr.write("unknown command %r\n" % (args,))
    sys.exit(2)
'''


def write_fake_codex(directory: Path, **spec: Any) -> tuple[Path, Path]:
    """Write a fake ``codex`` into ``directory``; return it and its call log.

    ``spec`` keys: ``config_servers`` / ``plugin_servers`` / ``builtin_servers``
    (name -> enabled; a builtin one is listed whatever the overrides and no
    config file defines it), ``old_shape`` (list entries carry only name,
    enabled and transport), ``behaviour`` (``{"mcp list": "fail" | "hang" |
    "slow" | "garbage", "features list": ...}``; ``slow`` waits
    ``slow_seconds``, default 0.5, then answers), ``ignored_features`` (an
    override Codex does not act on), ``missing_features`` (rows ``features
    list`` omits), ``features`` (the rows ``features list`` prints, default
    :data:`FEATURES`), ``catalog`` (what ``debug models --bundled`` prints,
    default :func:`bundled_catalog`), ``rejects_overrides`` (config keys this
    CLI refuses to load, as a June-era CLI refuses ``agents.enabled``).
    """

    directory.mkdir(parents=True, exist_ok=True)
    log = directory / "codex-calls.jsonl"
    log.write_text("", encoding="utf-8")
    (directory / "codex-spec.json").write_text(
        json.dumps({"features": list(FEATURES), "catalog": bundled_catalog(), **spec, "log": str(log)}),
        encoding="utf-8",
    )
    program = directory / "codex"
    program.write_text(f"#!{sys.executable}\n{_FAKE_CODEX}", encoding="utf-8")
    program.chmod(0o755)
    return program, log


def fake_codex_calls(log: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def stub_isolation_probe(monkeypatch, client, *, config_servers=()) -> list[tuple[Path, tuple[str, ...], tuple[str, ...]]]:
    """Answer the isolated turn's launch check in process: ``config_servers``
    are config-defined (each disabled by its name override), every isolation
    feature reads off when its override is present. Returns the probes run
    (where the turn ran it, sandboxed or not, and its deadline are not
    modelled: the fake-CLI and bubblewrap tests cover them)."""

    calls: list[tuple[Path, tuple[str, ...], tuple[str, ...]]] = []
    catalog = bundled_catalog(getattr(getattr(client, "config", None), "model", "") or "")

    def probe(cwd, overrides, *subcommand, **_launch_context):
        calls.append((Path(cwd), tuple(overrides), tuple(subcommand)))
        if subcommand[:2] == ("debug", "models"):
            return json.dumps(catalog)
        if subcommand[:2] == ("mcp", "list"):
            return json.dumps([
                {"name": name, "enabled": f"mcp_servers.{name}.enabled=false" not in overrides}
                for name in config_servers
            ])
        return "".join(
            f"{feature}  stable  {'false' if f'features.{feature}=false' in overrides else 'true'}\n"
            for feature in FEATURES
        )

    monkeypatch.setattr(client, "_codex_probe", probe)
    return calls
