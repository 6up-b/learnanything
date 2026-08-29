"""KM5 §8.4 residual-dependence diagnostics (report-only, deterministic)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.residual_diagnostics import residual_dependence_report
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.test_capability_residual import _build_vault, _drive
from tests.test_km2_write_path import SELECT, SHARED, _attempt, build_mvp07_vault


def test_positive_residual_dependence_flags_missing_factor(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    clock = FrozenClock(NOW)
    # The ambiguous whole-item observes SHARED and SELECT jointly; alternate
    # correct/incorrect so co-failure exceeds the product of the marginals.
    for _ in range(3):
        _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 4}, clock)
        _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, clock)

    report = residual_dependence_report(vault, repository, subject_id="linear-algebra")
    kinds = {s["kind"] for s in report["suggestions"]}
    assert "missing_facet_or_testlet_factor" in kinds
    dep = next(s for s in report["suggestions"] if s["kind"] == "missing_facet_or_testlet_factor")
    assert set(dep["facet_ids"]) == {SHARED, SELECT}

    # Report-only + deterministic: re-running yields the same suggestions.
    again = residual_dependence_report(vault, repository, subject_id="linear-algebra")
    assert again["suggestions"] == report["suggestions"]


def test_capability_divergence_hint(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=False)
    vault, repository = _drive(paths)
    report = residual_dependence_report(vault, repository, subject_id="linear-algebra")
    kinds = {s["kind"] for s in report["suggestions"]}
    assert "transfer_or_capability_divergence" in kinds
