"""TOML, dotenv, and environment-backed configuration loading."""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from learnloop.config.compat import normalize_config_input
from learnloop.config.schema import (
    CODEX_LOW_PROVIDER,
    CODEX_MEDIUM_PROVIDER,
    CodexHTTPProviderConfig,
    CodexSDKProviderConfig,
    LearnLoopConfig,
)
from learnloop.config.template import write_default_config


ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CODEX_CHECKOUT_ENV = "LEARNLOOP_CODEX_CHECKOUT_PATH"


class ConfigLoadError(ValueError):
    def __init__(self, path: Path, message: str):
        self.path = path
        super().__init__(message)


def global_settings_path() -> Path:
    """Return the machine-global LearnLoop settings environment file."""

    override = os.environ.get("LEARNLOOP_CONFIG_DIR")
    if override:
        base = Path(override).expanduser()
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        root = Path(xdg).expanduser() if xdg else Path.home() / ".config"
        base = root / "learnloop"
    return base / "settings.env"


def global_ai_defaults_path() -> Path:
    """Return the machine-global default AI provider selection file."""

    return global_settings_path().parent / "ai_defaults.toml"


def load_config(path: Path) -> LearnLoopConfig:
    """Load, compatibility-normalize, validate, and environment-overlay TOML."""

    # Precedence: shell env > vault-local .env > machine-global settings.env.
    # load_dotenv never overwrites keys already in os.environ, so loading the
    # vault .env first lets it win over the global file for the same key.
    load_dotenv(path.parent / ".env")
    load_dotenv(global_settings_path())
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLoadError(path, _format_toml_error(path, exc)) from exc
    config = LearnLoopConfig.model_validate(normalize_config_input(raw))
    return _apply_global_overrides(config)


def load_dotenv(path: Path) -> None:
    """Load environment variables without overriding the current process."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not ENV_KEY_RE.match(key) or key in os.environ:
            continue
        os.environ[key] = _parse_dotenv_value(value)


def _apply_global_overrides(config: LearnLoopConfig) -> LearnLoopConfig:
    """Overlay per-machine settings after the vault model is validated."""

    checkout = os.environ.get(CODEX_CHECKOUT_ENV, "").strip()
    if checkout:
        resolved = str(Path(checkout).expanduser())
        provider = config.ai.providers.get("codex")
        if isinstance(provider, (CodexSDKProviderConfig, CodexHTTPProviderConfig)):
            provider.checkout_path = resolved
        for provider_name in (CODEX_LOW_PROVIDER, CODEX_MEDIUM_PROVIDER):
            provider = config.ai.providers.get(provider_name)
            if isinstance(provider, (CodexSDKProviderConfig, CodexHTTPProviderConfig)):
                provider.checkout_path = resolved
    return config


def _format_toml_error(path: Path, exc: tomllib.TOMLDecodeError) -> str:
    message = f"Could not parse {path}: {exc}"
    hint = _windows_path_hint(path, exc)
    return f"{message}\n{hint}" if hint else message


def _windows_path_hint(path: Path, exc: tomllib.TOMLDecodeError) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    line_number = getattr(exc, "lineno", None) or _line_number_from_toml_error(
        str(exc)
    )
    line = _line_at(text, line_number)
    if line is None or "\\" not in line or "=" not in line:
        return None
    key = line.split("=", 1)[0].strip()
    if key not in {
        "checkout_path",
        "sdk_python_path",
        "sdk_codex_bin",
        "sdk_launch_command",
    }:
        return None
    return (
        "Likely cause: a Windows path is written with backslashes inside a "
        "double-quoted TOML string. TOML treats sequences like \\U as escapes. "
        "For Codex paths, use forward slashes, for example "
        'checkout_path = "C:/Users/banan/OneDrive/Documents/thinking/learnloop/codex", '
        "or use single quotes around the Windows path."
    )


def _line_number_from_toml_error(message: str) -> int | None:
    match = re.search(r"line (\d+)", message)
    return int(match.group(1)) if match else None


def _line_at(text: str, line_number: int | None) -> str | None:
    if line_number is None:
        return None
    lines = text.splitlines()
    if line_number < 1 or line_number > len(lines):
        return None
    return lines[line_number - 1]


def _parse_dotenv_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if "#" in value:
        value = value.split("#", 1)[0].rstrip()
    return value


__all__ = [
    "CODEX_CHECKOUT_ENV",
    "ConfigLoadError",
    "ENV_KEY_RE",
    "global_ai_defaults_path",
    "global_settings_path",
    "load_config",
    "load_dotenv",
    "write_default_config",
]
