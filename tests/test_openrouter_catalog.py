from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone

import pytest

from learnloop.ai.providers import openrouter_catalog as catalog

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

PAYLOAD = {
    "data": [
        {"id": "google/gemini-2.5-pro", "architecture": {"input_modalities": ["text", "image", "file", "audio"]}},
        {"id": "meta/muse-spark-1.3", "architecture": {"input_modalities": ["text", "image", "video", "file", "audio"]}},
        {"id": "text-only/model", "architecture": {"input_modalities": ["text"]}},
        {"id": "odd/model", "architecture": {"input_modalities": ["text", "hologram"]}},
        {"id": "no-arch/model"},
        {"not": "a model"},
    ]
}


@pytest.fixture(autouse=True)
def _isolated_config_dir(tmp_path, monkeypatch):
    # The catalog cache lives under the machine config dir; give every test its own.
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))


def _install_fetch(monkeypatch, payload=PAYLOAD, *, fail=False):
    calls: list[float] = []

    def fake_fetch(timeout: float):
        calls.append(timeout)
        if fail:
            raise OSError("network down")
        return payload

    monkeypatch.setattr(catalog, "_fetch_models_payload", fake_fetch)
    return calls


def test_reduce_maps_openrouter_inputs_to_learnloop_modalities():
    models = catalog.reduce_models_payload(PAYLOAD)
    assert models["google/gemini-2.5-pro"] == ("audio", "pdf", "image")
    assert models["meta/muse-spark-1.3"] == ("audio", "pdf", "image", "video")
    assert models["text-only/model"] == ()
    assert models["odd/model"] == ()
    assert models["no-arch/model"] == ()
    assert "not" not in models and None not in models


def test_first_load_fetches_and_caches_atomically(monkeypatch):
    calls = _install_fetch(monkeypatch)

    snapshot = catalog.load_catalog(now=T0)

    assert snapshot.source == "network" and snapshot.stale is False
    assert catalog.model_input_modalities(snapshot, "google/gemini-2.5-pro") == ("audio", "pdf", "image")
    assert catalog.model_input_modalities(snapshot, "unknown/slug") is None
    path = catalog.catalog_cache_path()
    assert path.is_file()
    assert not list(path.parent.glob("*.tmp"))
    assert calls == [catalog.FETCH_TIMEOUT_SECONDS]

    state = catalog.cached_catalog_state(now=T0)
    assert state["cached"] is True and state["stale"] is False and state["path"] == str(path)


def test_fresh_cache_is_served_without_network(monkeypatch):
    calls = _install_fetch(monkeypatch)
    catalog.load_catalog(now=T0)

    again = catalog.load_catalog(now=T0 + timedelta(hours=1))

    assert again.source == "cache" and again.stale is False
    assert len(calls) == 1
    offline = catalog.load_catalog(now=T0 + timedelta(hours=1), allow_network=False)
    assert offline.source == "cache" and offline.stale is False


def test_expired_cache_refetches_and_refresh_forces_it(monkeypatch):
    calls = _install_fetch(monkeypatch)
    catalog.load_catalog(now=T0)

    later = catalog.load_catalog(now=T0 + timedelta(hours=25))
    assert later.source == "network" and len(calls) == 2

    forced = catalog.load_catalog(now=T0 + timedelta(hours=25, minutes=1), refresh=True)
    assert forced.source == "network" and len(calls) == 3


def test_network_failure_serves_stale_cache(monkeypatch):
    _install_fetch(monkeypatch)
    catalog.load_catalog(now=T0)
    _install_fetch(monkeypatch, fail=True)

    stale = catalog.load_catalog(now=T0 + timedelta(days=2))

    assert stale.source == "cache" and stale.stale is True
    assert catalog.cached_catalog_state(now=T0 + timedelta(days=2))["stale"] is True
    offline = catalog.load_catalog(now=T0 + timedelta(days=2), allow_network=False)
    assert offline.stale is True


def test_no_cache_and_no_network_is_typed(monkeypatch):
    _install_fetch(monkeypatch, fail=True)
    with pytest.raises(catalog.OpenRouterCatalogError):
        catalog.load_catalog(now=T0)
    with pytest.raises(catalog.OpenRouterCatalogError):
        catalog.load_catalog(now=T0, allow_network=False)
    assert catalog.cached_catalog_state(now=T0) == {
        "cached": False,
        "fetched_at": None,
        "stale": False,
        "path": str(catalog.catalog_cache_path()),
    }


def test_corrupt_cache_is_ignored(monkeypatch):
    calls = _install_fetch(monkeypatch)
    path = catalog.catalog_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")

    snapshot = catalog.load_catalog(now=T0)

    assert snapshot.source == "network" and len(calls) == 1


def test_malformed_cache_values_are_ignored_and_never_crash_the_settings_read(monkeypatch):
    calls = _install_fetch(monkeypatch)
    path = catalog.catalog_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": 1, "fetched_at": T0.isoformat(), "models": {"x/y": None, "a/b": "audio"}}),
        encoding="utf-8",
    )

    state = catalog.cached_catalog_state(now=T0)
    assert state["cached"] is False

    snapshot = catalog.load_catalog(now=T0)
    assert snapshot.source == "network" and len(calls) == 1


def test_unexpected_payload_shape_is_not_cached(monkeypatch):
    _install_fetch(monkeypatch, payload={"error": {"message": "temporarily unavailable"}})

    with pytest.raises(catalog.OpenRouterCatalogError):
        catalog.load_catalog(now=T0)
    assert not catalog.catalog_cache_path().exists()

    # With a cache present the bad payload degrades to the cached copy.
    _install_fetch(monkeypatch)
    catalog.load_catalog(now=T0)
    _install_fetch(monkeypatch, payload={"data": {"not": "a list"}})
    stale = catalog.load_catalog(now=T0, refresh=True)
    assert stale.source == "cache" and stale.models


def test_naive_now_is_treated_as_utc(monkeypatch):
    _install_fetch(monkeypatch)
    catalog.load_catalog(now=T0)
    snapshot = catalog.load_catalog(now=T0.replace(tzinfo=None))
    assert snapshot.source == "cache" and snapshot.stale is False
