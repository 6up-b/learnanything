"""Machine-local configuration for the secondary capture host."""
from pathlib import Path
import re
import tomllib

from pydantic import BaseModel, ConfigDict, Field, field_validator

from learnloop.config.loader import global_settings_path


class MobileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = Field(default=False, strict=True)
    vault: Path
    hostname: str
    owner_login: str = Field(min_length=1, max_length=254)
    port: int = Field(default=8765, ge=1, le=65535, strict=True)
    max_upload_mb: int = Field(default=20, ge=1, le=20, strict=True)

    @field_validator("vault")
    @classmethod
    def absolute_vault(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("vault must be an absolute path")
        return value

    @field_validator("hostname")
    @classmethod
    def tailnet_hostname(cls, value: str) -> str:
        label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        if len(value) > 253 or not re.fullmatch(rf"{label}(?:\.{label})*\.ts\.net", value):
            raise ValueError("hostname must be a bare lowercase ts.net hostname")
        return value


def config_path() -> Path:
    return global_settings_path().with_name("mobile.toml")


def load_config(path: Path | None = None) -> MobileConfig:
    with (path or config_path()).open("rb") as stream:
        return MobileConfig.model_validate(tomllib.load(stream))


def sqlite_path(config: MobileConfig) -> Path:
    """Resolve only storage configuration, without dotenv or vault loading."""
    with (config.vault / "learnloop.toml").open("rb") as stream:
        storage = tomllib.load(stream).get("storage", {})
    path = (config.vault / Path(storage.get("sqlite_path", "state.sqlite"))).resolve()
    if not path.is_relative_to(config.vault.resolve()):
        raise ValueError("Database must be inside the pinned vault")
    return path
