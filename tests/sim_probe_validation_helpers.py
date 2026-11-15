"""What other test files use from ``tests/test_sim_probe_validation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import vault_repository
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault, set_algorithm_version, set_config_switch


CLOCK = FrozenClock(NOW)


def _vault_with_confusable(
    tmp_path, *, version: str | None = None, value_of_information: bool = False, switches_off: tuple[str, ...] = ()
):
    """The basic vault (at the head, or at ``version``) with one confusable on its learning object.

    The sim drives the opening episode state sync opens per new learning object, so placement stays off (with it
    on, mvp-0.11, sync opens no episode and the report is empty); it serves parametric instances, so FG1 stays off
    (mvp-0.45 generates none for this episode, which then has nothing to serve). Value of information (mvp-0.21)
    is off unless ``value_of_information``: with it off the robust completion gate decides each unstable episode;
    with it on the value stop does, as a vault serves by default. ``switches_off``: further switches set false."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if version is not None:
        set_algorithm_version(paths, version)
    off = ("placement.enabled", "followup.generate_and_serve")
    if not value_of_information:
        off += ("voi_stopping.enabled",)
    for key in (*off, *switches_off):
        set_config_switch(vault_root, key, False)
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects["lo_svd_definition"].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
    return vault_root


def run_records(workdir: Path, planted: str, seed: int) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """What one planted run stored: its episode's completion detail (the value stop's decision, when value
    ended it) and the robust gate's logged decisions in order (``voi_forecasts`` at ``probe_robust_selection``)."""

    vault = load_vault(Path(workdir) / f"run_{planted.replace(':', '_')}_{seed}")
    repository = vault_repository(VaultPaths(vault.root, vault.config))
    with repository.connection() as connection:
        episode = connection.execute(
            "SELECT completion_detail_json FROM probe_episodes WHERE status = 'complete'"
        ).fetchone()
        gate = connection.execute(
            "SELECT forecast_json FROM voi_forecasts WHERE site = 'probe_robust_selection' ORDER BY created_at, id"
        ).fetchall()
    detail = json.loads(episode[0]) if episode is not None and episode[0] else None
    return detail, [json.loads(row[0]) for row in gate]
