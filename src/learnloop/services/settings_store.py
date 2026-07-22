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
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from learnloop.config import _ENV_KEY_RE, AIProviderConfig


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
