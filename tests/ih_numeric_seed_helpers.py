"""What other test files use from ``tests/test_ih_numeric_seed.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.daily_plan import objective_chooser as OC

from tests.rospeed2_connections_helpers import _canon


@pytest.fixture
def spy(monkeypatch):
    """Every boundary identity hashed (the dict the prefetch key hashes, its snapshot naming every switch; the seed's own
    hash names fewer, so it is not one), and every numeric run with its seed and its evaluation at a fixed draw count."""

    real_hash, real_numeric = OC._hash, OC.run_numeric
    control = SimpleNamespace(identities=[], runs=[])

    def recording(value):
        if (isinstance(value, dict) and str(value.get("kind", "")).startswith("objective_")
                and "held_reading_map" in (value.get("objective") or {}).get("followup_switches", {})):
            control.identities.append(value)
        return real_hash(value)

    def numeric(vault, repository, **kwargs):
        fixed = {**kwargs, "keep_going": lambda: False, "forecasts": None, "publish": None, "defer_carried": None,
                 "deadline": None}

        def values(seed: str) -> Any:
            return _canon(real_numeric(vault, repository, **{**fixed, "seed": seed}).evaluation.valued)

        # Evaluated only for the run a test asserts on: a journey to a boundary makes many.
        control.runs.append({"seed": kwargs["seed"], "support": list(kwargs["support"]), "values": values})
        return real_numeric(vault, repository, **kwargs)

    monkeypatch.setattr(OC, "_hash", recording)
    monkeypatch.setattr(OC, "run_numeric", numeric)
    return control
