"""What other test files use from ``tests/test_sim_probe_validation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault, pin_old_basic_vault


CLOCK = FrozenClock(NOW)


def _vault_with_confusable(tmp_path):
    vault_root = tmp_path / "vault"
    # Old path only (D2a): the sim drives the opening episode state sync opened per new LO and serves
    # parametric instances. mvp-0.11 (placement) opens no such episode, so at the head every run
    # finds none and the report is empty; with opening probes kept it still serves nothing, since
    # mvp-0.45 (FG1) generates no parametric instance.
    pin_old_basic_vault(create_basic_vault(vault_root))
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects["lo_svd_definition"].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
    return vault_root
