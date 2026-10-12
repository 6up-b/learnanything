"""Daily-loop follow-up: the guided-path assessment burned a parked LO's cold surface.

``golden_path.assess_open`` advanced the run to ``assessing`` and opened the cold
administration (the burn: the held-out surface is consumed) before anything
looked at the item's Learning Object, so a dormant or resolved LO's reserved
surface was spent on an assessment the learner had put away. It now refuses
with ``learning_object_inactive`` before touching the run or the surface.
"""

from __future__ import annotations

import pytest

from learnloop.curriculum import golden_path_run as GPR
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.test_sidecar_golden_path_assessment import _call, _setup_run

LO_ID = "lo_svd_definition"


def _set_lo_status(root, status: str) -> None:
    lo_path = VaultPaths(root, load_vault(root).config).learning_object_path("linear-algebra", LO_ID)
    payload = read_yaml(lo_path)
    payload["status"] = status
    write_yaml(lo_path, payload)


def _administrations(repository: Repository, surface_id: str) -> int:
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) AS n FROM activity_administrations WHERE surface_id = ?", (surface_id,)
        ).fetchone()["n"]


@pytest.mark.parametrize("status", ["dormant", "resolved"])
def test_assess_open_refuses_a_parked_lo_without_burning_the_surface(tmp_path, status):
    vault_root = tmp_path / "vault"
    run_id, surface_id = _setup_run(vault_root)
    repository = Repository(VaultPaths(vault_root, load_vault(vault_root).config).sqlite_path)
    _set_lo_status(vault_root, status)

    response = _call(vault_root, "golden_path.assess_open", {"runId": run_id})

    assert response["error"]["data"]["code"] == "learning_object_inactive"
    assert _administrations(repository, surface_id) == 0, "a refused open must never burn"
    assert GPR.project_run(repository, run_id).current_state == "ready_to_assess"

    # Reactivated, the same reserve opens normally: nothing was consumed.
    _set_lo_status(vault_root, "active")
    opened = _call(vault_root, "golden_path.assess_open", {"runId": run_id})["result"]
    assert opened["administrationId"] and _administrations(repository, surface_id) == 1
