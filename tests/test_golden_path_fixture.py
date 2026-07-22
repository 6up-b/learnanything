"""P2 -- deterministic golden-path fixture bootstrap (spec_p2 §C, §12.7, §12.8)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.services import golden_path_run as GPR
from learnloop.services.golden_path_fixture import (
    EXEMPLAR_A,
    EXEMPLAR_B,
    HELD_OUT,
    build_golden_path_fixture,
)
from learnloop.vault.paths import VaultPaths
from learnloop.vault.loader import load_vault


def test_fixture_bootstrap_confirms_a_certifying_run(tmp_path):
    fixture = build_golden_path_fixture(tmp_path / "vault")
    assert fixture.receipt.mode == "certifying"
    assert fixture.receipt.current_state == "ready"
    assert fixture.exemplar_refs == (EXEMPLAR_A, EXEMPLAR_B)
    assert fixture.held_out_ref == HELD_OUT

    vault = load_vault(fixture.root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    # The run can be walked end to end from the fixture state.
    state = GPR.project_run(repo, fixture.receipt.run_id)
    assert state.current_state == "ready"
    # The reserved assessment surface is the held-out sibling, not an exemplar.
    reservation = repo.golden_path_run(fixture.receipt.run_id)["reserved_surface_id"]
    assert reservation == fixture.assessment_surface_id


def test_fixture_is_deterministic_across_two_builds(tmp_path):
    a = build_golden_path_fixture(tmp_path / "a")
    b = build_golden_path_fixture(tmp_path / "b")
    # Two builds produce identical content hashes (ids/timestamps excluded, §12.8).
    assert a.content_hashes == b.content_hashes
    # ULID ids necessarily differ (proving the hash equality is content, not id).
    assert a.receipt.run_id != b.receipt.run_id


def test_fixture_vault_is_mvp_0_8(tmp_path):
    fixture = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fixture.root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.8"


def test_fixture_blueprint_is_active_after_confirmation(tmp_path):
    fixture = build_golden_path_fixture(tmp_path / "vault")
    vault = load_vault(fixture.root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    assert repo.task_blueprint_version(fixture.blueprint_version_id)["status"] == "active"
