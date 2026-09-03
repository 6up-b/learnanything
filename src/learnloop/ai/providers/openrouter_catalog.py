"""OpenRouter model capability catalog.

OpenRouter publishes every model's declared input modalities on the public,
unauthenticated ``GET /api/v1/models`` endpoint (``architecture.input_modalities``
with values such as ``text``, ``image``, ``file``, ``audio``, ``video``). This
module fetches that list, reduces it to LearnLoop's modality vocabulary and
caches it on disk under the machine config directory with a TTL.

The catalog only *proposes* capabilities: the runtime authority remains the
provider profile's ``input_modalities`` in ``learnloop.toml`` (see
``learnloop.ai.native_media``), which the settings surface writes after
detection. Ingestion never calls this module, so an offline machine behaves
exactly as its config says.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Mapping

from learnloop.config.loader import global_settings_path
from learnloop.config.schema import KNOWN_INPUT_MODALITIES

logger = logging.getLogger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
CATALOG_TTL_SECONDS = 24 * 3600
FETCH_TIMEOUT_SECONDS = 15.0
CATALOG_VERSION = 1
#: OpenRouter's ``input_modalities`` values → LearnLoop modalities (``text`` is implicit).
MODALITY_BY_OPENROUTER_INPUT: Mapping[str, str] = {
    "file": "pdf",
    "audio": "audio",
    "image": "image",
    "video": "video",
}


class OpenRouterCatalogError(RuntimeError):
    """No catalog could be produced (no cache and the fetch failed or was disallowed)."""


@dataclass(frozen=True)
class CatalogSnapshot:
    #: model slug → declared LearnLoop modalities, in KNOWN_INPUT_MODALITIES order.
    models: Mapping[str, tuple[str, ...]]
    fetched_at: str
    source: Literal["network", "cache"]
    #: True when the data is older than the TTL (served because nothing fresher exists).
    stale: bool


def catalog_cache_path() -> Path:
    return global_settings_path().parent / "openrouter_models.json"


def _fetch_models_payload(timeout: float) -> dict[str, Any]:
    """The raw models listing. Module-level so tests can replace it."""

    request = urllib.request.Request(
        OPENROUTER_MODELS_URL,
        headers={"Accept": "application/json", "User-Agent": "learnloop-desktop"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 — fixed https URL
        return json.loads(response.read().decode("utf-8"))


def reduce_models_payload(payload: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """``{"data": [{"id", "architecture": {"input_modalities": [...]}}]}`` → slug → modalities."""

    entries = payload.get("data") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        # An error body or a changed shape must not be cached as an empty
        # catalog for a day.
        raise OpenRouterCatalogError("unexpected OpenRouter models payload (no data list)")
    models: dict[str, tuple[str, ...]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        slug = entry.get("id")
        if not slug:
            continue
        architecture = entry.get("architecture") or {}
        inputs = architecture.get("input_modalities") if isinstance(architecture, Mapping) else None
        declared = {
            MODALITY_BY_OPENROUTER_INPUT[str(value)]
            for value in (inputs or [])
            if str(value) in MODALITY_BY_OPENROUTER_INPUT
        }
        models[str(slug)] = tuple(modality for modality in KNOWN_INPUT_MODALITIES if modality in declared)
    return models


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _read_cache(path: Path) -> tuple[dict[str, tuple[str, ...]], str] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("version") != CATALOG_VERSION:
        return None
    models = payload.get("models")
    fetched_at = payload.get("fetched_at")
    if not isinstance(models, dict) or not isinstance(fetched_at, str):
        return None
    parsed: dict[str, tuple[str, ...]] = {}
    for slug, mods in models.items():
        if not isinstance(mods, list) or not all(isinstance(m, str) for m in mods):
            return None  # a hand-edited or truncated file: refetch rather than crash
        parsed[str(slug)] = tuple(mods)
    return parsed, fetched_at


def _write_cache(path: Path, models: Mapping[str, tuple[str, ...]], fetched_at: str) -> None:
    """Atomic replace so a crash mid-write never leaves a truncated catalog."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": CATALOG_VERSION, "fetched_at": fetched_at, "models": {k: list(v) for k, v in models.items()}}
    handle, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as tmp:
            json.dump(payload, tmp, sort_keys=True)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _is_fresh(fetched_at: str, now: datetime, ttl_seconds: int) -> bool:
    stamp = _parse_timestamp(fetched_at)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return stamp is not None and now - stamp <= timedelta(seconds=ttl_seconds)


def load_catalog(
    *,
    refresh: bool = False,
    now: datetime | None = None,
    ttl_seconds: int = CATALOG_TTL_SECONDS,
    allow_network: bool = True,
    timeout: float = FETCH_TIMEOUT_SECONDS,
) -> CatalogSnapshot:
    """Return the catalog, fetching only when the cache is missing/expired or ``refresh``.

    A network failure with an expired cache serves the cache marked ``stale``;
    ``allow_network=False`` never touches the network (the settings payload
    uses it) and raises only when there is no cache at all.
    """

    now = now or datetime.now(timezone.utc)
    path = catalog_cache_path()
    cached = _read_cache(path)
    if cached is not None and not refresh and _is_fresh(cached[1], now, ttl_seconds):
        return CatalogSnapshot(models=cached[0], fetched_at=cached[1], source="cache", stale=False)
    if not allow_network:
        if cached is not None:
            return CatalogSnapshot(models=cached[0], fetched_at=cached[1], source="cache", stale=True)
        raise OpenRouterCatalogError(
            "no cached OpenRouter model catalog; detecting capabilities needs one network fetch"
        )
    try:
        models = reduce_models_payload(_fetch_models_payload(timeout))
    except Exception as exc:  # noqa: BLE001 — every failure degrades to the cache or a typed error
        if cached is not None:
            logger.warning("OpenRouter catalog refresh failed; serving the cached copy: %s", exc)
            return CatalogSnapshot(models=cached[0], fetched_at=cached[1], source="cache", stale=True)
        raise OpenRouterCatalogError(f"could not fetch the OpenRouter model catalog: {exc}") from exc
    fetched_at = now.isoformat()
    try:
        _write_cache(path, models, fetched_at)
    except OSError as exc:
        logger.warning("could not write the OpenRouter catalog cache at %s: %s", path, exc)
    return CatalogSnapshot(models=models, fetched_at=fetched_at, source="network", stale=False)


def model_input_modalities(snapshot: CatalogSnapshot, slug: str) -> tuple[str, ...] | None:
    """Declared modalities for ``slug``; ``None`` when the catalog does not list it."""

    return snapshot.models.get(slug)


def cached_catalog_state(*, now: datetime | None = None, ttl_seconds: int = CATALOG_TTL_SECONDS) -> dict[str, Any]:
    """Cache-only status for a settings payload; never touches the network, never raises."""

    now = now or datetime.now(timezone.utc)
    path = catalog_cache_path()
    try:
        cached = _read_cache(path)
    except Exception as exc:  # noqa: BLE001 — a settings read must survive any cache file
        logger.warning("unreadable OpenRouter catalog cache at %s: %s", path, exc)
        cached = None
    return {
        "cached": cached is not None,
        "fetched_at": cached[1] if cached is not None else None,
        "stale": cached is not None and not _is_fresh(cached[1], now, ttl_seconds),
        "path": str(path),
    }


__all__ = [
    "CATALOG_TTL_SECONDS",
    "CatalogSnapshot",
    "MODALITY_BY_OPENROUTER_INPUT",
    "OPENROUTER_MODELS_URL",
    "OpenRouterCatalogError",
    "cached_catalog_state",
    "catalog_cache_path",
    "load_catalog",
    "model_input_modalities",
    "reduce_models_payload",
]
