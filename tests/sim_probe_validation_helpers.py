"""What other test files use from ``tests/test_sim_probe_validation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault, pin_old_basic_vault, set_config_switch


CLOCK = FrozenClock(NOW)


def _vault_with_confusable(tmp_path):
    vault_root = tmp_path / "vault"
    # The sim drives the opening episode state sync opens per new LO without placement (mvp-0.11 opens
    # none) and serves parametric instances (FG1, mvp-0.45, generates none), each episode ended on its
    # count (value of information, mvp-0.21, ends it on value): those three switches serve the path it
    # was written for. Every episode now runs the robust probe path (mvp-0.8), whatever the tag: there
    # the surface_only type is diagnosed 2 times in 5 (refactor bug ledger D-39).
    pin_old_basic_vault(create_basic_vault(vault_root))
    for key in ("placement.enabled", "followup.generate_and_serve", "voi_stopping.enabled"):
        set_config_switch(vault_root, key, False)
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects["lo_svd_definition"].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
    return vault_root
