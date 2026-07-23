"""Persistence for the Settings tab.

Two write paths, both new to the codebase (config was previously read-only):

- ``apply_config_updates`` — comment-preserving structured edits to the
  per-vault ``learnloop.toml`` via tomlkit (needle replacement can't target
  repeated keys like ``model =`` across provider tables, and can't create
  absent tables). Atomic write-temp + replace, mirroring
  ``services/vault_upgrade._rewrite_algorithm_version``.
- ``upsert_env_var`` — targeted ``KEY=value`` edits to a dotenv-style file
  (the machine-global ``settings.env``); secrets never land in the committed
  ``learnloop.toml``. Every other line is preserved byte-for-byte.

Callers that change an env var a running process already loaded must ALSO set
``os.environ`` directly: ``learnloop.config.load_dotenv`` never overwrites an
existing key, so a reload alone keeps the stale value until process restart.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from learnloop.config import _ENV_KEY_RE, AIProviderConfig, CODEX_PROVIDER_NAMES


class SettingsStoreError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# The Settings tab exposes coarse use-cases; each expands onto the real
# [ai.routing] task keys consumed by provider_for_task.
USE_CASE_ROUTES: dict[str, tuple[str, ...]] = {
    "grading": ("grading",),
    "ingest": ("canonical_ingest", "canonical_ingest_retry", "authoring"),
    "tutor": ("tutor_qa", "teach_back", "rung_variant"),
    "animation": ("animation",),
}


def openrouter_profile_name(use_case: str) -> str:
    return f"openrouter_{use_case}"


def openrouter_task_profile_values(base: AIProviderConfig, model: str) -> dict[str, Any]:
    """Concrete keys for a per-use-case OpenRouter profile cloned from ``base``.

    Only explicitly-set keys are emitted — pydantic defaults are never dumped
    into the TOML, keeping the committed config minimal."""

    values: dict[str, Any] = {"type": base.type or "openrouter", "model": model}
    for key in (
        "api_key_env",
        "base_url",
        "response_format",
        "thinking",
        "reasoning_effort",
        "max_tokens",
        "timeout_seconds",
        "http_referer",
        "x_title",
    ):
        value = getattr(base, key, None)
        if value is not None:
            values[key] = value
    return values


def apply_config_updates(config_path: Path, updates: Mapping[tuple[str, ...], Any]) -> None:
    """Set dotted key-paths in ``learnloop.toml``, preserving comments/layout.

    Intermediate tables are created when absent. The write is atomic (temp
    sibling + ``Path.replace``); an unparseable file raises without touching
    disk."""

    import tomlkit
    from tomlkit.exceptions import TOMLKitError

    try:
        text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SettingsStoreError("config_missing", f"{config_path} does not exist") from exc
    try:
        document = tomlkit.parse(text)
    except TOMLKitError as exc:
        raise SettingsStoreError("config_unreadable", f"{config_path} is not valid TOML: {exc}") from exc

    for key_path, value in updates.items():
        if not key_path:
            raise SettingsStoreError("invalid_key_path", "empty config key path")
        node: Any = document
        for part in key_path[:-1]:
            existing = node.get(part)
            if existing is None:
                table = tomlkit.table()
                node[part] = table
                node = table
            elif isinstance(existing, (str, int, float, bool, list)):
                raise SettingsStoreError(
                    "invalid_key_path",
                    f"config key {'.'.join(key_path)} traverses non-table value at {part!r}",
                )
            else:
                node = existing
        node[key_path[-1]] = value

    tmp = config_path.with_suffix(config_path.suffix + ".tmp")
    tmp.write_text(tomlkit.dumps(document), encoding="utf-8")
    tmp.replace(config_path)


def copy_ai_settings(source_path: Path, target_path: Path) -> bool:
    """Copy the persisted ``[ai]`` provider selection from one vault's
    ``learnloop.toml`` into another's. Returns True when anything was applied.

    Vault creation uses this so a new vault inherits the provider routing the
    user configured in the vault they created it from — the Settings tab
    persists routing and the materialized ``openrouter_<usecase>`` profiles
    per-vault, while API keys live in the machine-global ``settings.env``.
    Reads the raw TOML (not ``load_config``, whose model mixes auto-seeded
    defaults into ``[ai]``) so only explicitly persisted choices travel.
    Codex profiles are skipped: their machine-local config is env-driven and
    already present in the fresh template."""

    try:
        raw = tomllib.loads(source_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SettingsStoreError("config_missing", f"{source_path} does not exist") from exc
    except tomllib.TOMLDecodeError as exc:
        raise SettingsStoreError(
            "config_unreadable", f"{source_path} is not valid TOML: {exc}"
        ) from exc

    ai = raw.get("ai")
    if not isinstance(ai, Mapping):
        return False

    updates: dict[tuple[str, ...], Any] = {}
    for key in ("active_provider", "fallback_provider"):
        value = ai.get(key)
        if isinstance(value, str):
            updates[("ai", key)] = value

    known_tasks = {task for routes in USE_CASE_ROUTES.values() for task in routes}
    routing = ai.get("routing")
    if isinstance(routing, Mapping):
        for task, value in routing.items():
            if task in known_tasks and isinstance(value, str):
                updates[("ai", "routing", task)] = value

    providers = ai.get("providers")
    if isinstance(providers, Mapping):
        for name, table in providers.items():
            if name in CODEX_PROVIDER_NAMES or not isinstance(table, Mapping):
                continue
            _flatten_into_updates(("ai", "providers", name), table, updates)

    if not updates:
        return False
    apply_config_updates(target_path, updates)
    return True


def save_ai_settings_to(source_path: Path, target_path: Path) -> bool:
    """Mirror a vault's ``[ai]`` selection into ``target_path``, creating the
    target (and its parent dir) if absent.

    Used to persist the machine-global provider defaults so newly created vaults
    can inherit them even when no vault is open. Delegates the actual ``[ai]``
    subset copy to :func:`copy_ai_settings`."""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        target_path.write_text("", encoding="utf-8")
    return copy_ai_settings(source_path, target_path)


def _flatten_into_updates(
    prefix: tuple[str, ...], table: Mapping[str, Any], updates: dict[tuple[str, ...], Any]
) -> None:
    for key, value in table.items():
        if isinstance(value, Mapping):
            _flatten_into_updates((*prefix, key), value, updates)
        else:
            updates[(*prefix, key)] = value


def upsert_env_var(path: Path, key: str, value: str | None) -> None:
    """Set (or remove, when ``value`` is None) ``KEY=value`` in a dotenv file.

    Mirrors ``learnloop.config.load_dotenv``'s grammar (optional ``export ``
    prefix, ``#`` comments, ``_ENV_KEY_RE`` names). All other lines are kept
    byte-for-byte; the file and parent directories are created when absent.
    Best-effort ``chmod 600`` (no-op where unsupported, e.g. Windows ACLs)."""

    if not _ENV_KEY_RE.match(key):
        raise SettingsStoreError("invalid_env_key", f"invalid environment variable name {key!r}")
    if value is not None and any(ch in value for ch in ("\n", "\r")):
        raise SettingsStoreError("invalid_env_value", f"{key} value must not contain newlines")

    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    replaced = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        candidate = stripped[len("export ") :].strip() if stripped.startswith("export ") else stripped
        name, sep, _rest = candidate.partition("=")
        is_target = (
            not replaced
            and sep == "="
            and not stripped.startswith("#")
            and name.strip() == key
        )
        if is_target:
            replaced = True
            if value is not None:
                result.append(f"{key}={value}")
            continue
        result.append(line)
    if not replaced and value is not None:
        result.append(f"{key}={value}")

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = "\n".join(result)
    if text:
        text += "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
