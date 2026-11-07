"""Machine-local configuration for the secondary capture host."""
from pathlib import Path
import re
import tomllib

from pydantic import BaseModel, ConfigDict, Field, field_validator

from learnloop.config.loader import global_settings_path


#: The static PWA, built by ``npm run build`` in apps/learnloop-mobile (gitignored).
APP_DIR = Path(__file__).with_name("static") / "app"


class MobileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = Field(default=False, strict=True)
    vault: Path
    hostname: str
    owner_login: str = Field(min_length=1, max_length=254)
    port: int = Field(default=8765, ge=1, le=65535, strict=True)
    https_port: int = Field(default=443, ge=1, le=65535, strict=True)
    max_upload_mb: int = Field(default=20, ge=1, le=20, strict=True)
    #: Mobile v2 §2.2's kill switch (``mobile.phone_plan``): the phone's Today is the shared plan.
    #: Off, the plan's methods are refused (``phone_plan_off``) and Today is M2a's queue.
    phone_plan: bool = Field(default=True, strict=True)
    #: Mobile v2 V3's kill switch (``mobile.phone_probes``; owner decision D3): the phone serves and answers
    #: phone-eligible probes (diagnostic and FG1's generated follow-ups) under the probe contract, at the vault's
    #: successor tag (PHONE_PROBES_VERSIONS). Off, ``followup_next`` is refused (``phone_probes_off``), a probe
    #: answer is refused (``validation_error``) and the phone is V2's: it leaves every probe for the desktop.
    phone_probes: bool = Field(default=True, strict=True)
    #: Mobile v2 V4's kill switch (``mobile.phone_reader``; owner decision D4): the phone's Reader (text first, the
    #: original page as a host-rendered image on demand), the plan's reading blocks it can show, and the image, page
    #: and asset prompts whose targets the host serves (§2.3). Off, the reader methods are refused
    #: (``phone_reader_off``), the page and asset endpoints answer 404, and the phone is V3's: readings wait for the
    #: desktop.
    phone_reader: bool = Field(default=True, strict=True)
    #: Where the host keeps its rendered pages (§3.3): outside the vault, keyed by the vault and the file's content
    #: address. None: ``$XDG_CACHE_HOME/learnloop/mobile-pages`` (``~/.cache/...``), or beside the config under
    #: ``LEARNLOOP_CONFIG_DIR`` when that is set (an isolated install).
    page_cache_dir: Path | None = None

    @field_validator("page_cache_dir")
    @classmethod
    def absolute_cache(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("page_cache_dir must be an absolute path")
        return value

    def page_cache_root(self) -> Path:
        """The rendered-page cache's root, never inside the vault (§3.3)."""

        import os

        if self.page_cache_dir is not None:
            root = self.page_cache_dir
        elif os.environ.get("LEARNLOOP_CONFIG_DIR"):
            root = Path(os.environ["LEARNLOOP_CONFIG_DIR"]).expanduser() / "cache" / "mobile-pages"
        else:
            xdg = os.environ.get("XDG_CACHE_HOME")
            root = (Path(xdg).expanduser() if xdg else Path.home() / ".cache") / "learnloop" / "mobile-pages"
        if root.resolve().is_relative_to(self.vault.resolve()):
            raise ValueError("The page cache must be outside the vault")
        return root

    @property
    def https_authority(self) -> str:
        """The browser's Host header; HTTPS's default port is implicit."""
        return self.hostname if self.https_port == 443 else f"{self.hostname}:{self.https_port}"

    @property
    def base_url(self) -> str:
        """The external HTTPS origin for pairing and phone URLs, without a path."""
        return f"https://{self.https_authority}"

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
