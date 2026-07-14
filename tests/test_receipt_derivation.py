"""B5 phase 2 (spec §5.1): per-observation itemization + Ready derivation.

Two invariants that unblock the full receipt payload:

1. The per-observation derivation (raw vs capped credit per cell) sums, with the
   correction-replaces-attempt fold semantics, EXACTLY to the banked canonical
   ledger credit — the itemization is not a parallel approximation.
2. The Ready-derivation ingredients are folded from the *same* persisted
   canonical recall slices the projection wrote, so they match byte-for-byte.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import (
    _repeat_discount,
    project_canonical_facet_state,
)
from learnloop.services.facet_evidence_timeline import (
    _observation_events,
    facet_evidence_timeline,
    facet_ready_derivation,
    fold_demonstrated_timeline,
)
from learnloop.vault.loader import load_vault

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE_VAULTS = sorted(
    path.name for path in FIXTURES.iterdir() if (path / "state.sqlite").exists()
)


def _loaded_fixture(tmp_path, name):
    root = tmp_path / name
    shutil.copytree(FIXTURES / name, root)
    toml_path = root / "learnloop.toml"
    text, count = re.subn(
        r'algorithm_version = "[^"]+"',
        'algorithm_version = "mvp-0.7"',
        toml_path.read_text(encoding="utf-8"),
        count=1,
    )
    assert count == 1
    toml_path.write_text(text, encoding="utf-8")
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    return vault, repository


def _all_facets(vault, banked):
    facets = set(banked)
    for item in vault.practice_items.values():
        facets.update(vault.canonical_facet_id(str(f)) for f in item.evidence_facets)
    return sorted(facets)


@pytest.mark.parametrize("fixture_name", FIXTURE_VAULTS)
def test_per_observation_itemization_sums_to_banked_credit(tmp_path, fixture_name):
    vault, repository = _loaded_fixture(tmp_path, fixture_name)
    if not repository.list_attempt_history():
        pytest.skip(f"fixture {fixture_name} has no attempt history")

    project_canonical_facet_state(vault, repository)
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit

    for facet in _all_facets(vault, banked):
        events = _observation_events(vault, repository, facet)
        # Each event's itemization reproduces the epoch's authoritative capped
        # credit for this facet exactly (no parallel math).
        for event in events:
            item_sum = sum(d.capped_credit for d in event.derivation)
            assert item_sum == pytest.approx(event.raw_positive, abs=1e-12)
            for d in event.derivation:
                assert d.capped_credit <= d.raw_credit + 1e-12

        # Fold the itemization with correction-replaces-attempt semantics: the
        # latest epoch per attempt supersedes the earlier one, exactly as the
        # banked ledger accumulates.
        latest_by_attempt: dict[str, float] = {}
        for event in events:
            latest_by_attempt[event.attempt_id] = sum(
                d.capped_credit for d in event.derivation
            )
        itemized_total = sum(latest_by_attempt.values())
        expected = banked.get(facet, 0.0)
        assert itemized_total == pytest.approx(expected, abs=1e-12), (
            f"{fixture_name}:{facet} itemized={itemized_total} banked={expected}"
        )


def test_ready_derivation_matches_canonical_recall_slices(tmp_path):
    vault, repository = _loaded_fixture(tmp_path, "linear_algebra")
    project_canonical_facet_state(vault, repository)

    # Fold the persisted aggregate recall slices the projection wrote — the same
    # arithmetic the canonical state reader uses (alpha = 1 + Σ(alpha_c - 1)).
    aggregate: dict[str, list] = {}
    for row in repository.canonical_facet_recall_states():
        if row.practice_item_id is not None:
            continue
        aggregate.setdefault(row.facet_id, []).append(row)

    checked = 0
    for facet, rows in aggregate.items():
        series = facet_evidence_timeline(vault, repository, facet)
        ready = facet_ready_derivation(
            vault, repository, facet, series, clock=FrozenClock(parse_utc("2026-07-14T00:00:00Z"))
        )
        assert ready is not None and ready.supported

        exp_alpha = 1.0 + sum(r.recall_alpha - 1.0 for r in rows)
        exp_beta = 1.0 + sum(r.recall_beta - 1.0 for r in rows)
        exp_mass = sum(r.independent_evidence_mass for r in rows)
        assert ready.recall_alpha == pytest.approx(exp_alpha, abs=1e-12)
        assert ready.recall_beta == pytest.approx(exp_beta, abs=1e-12)
        assert ready.pooled_recall_mean == pytest.approx(
            exp_alpha / (exp_alpha + exp_beta), abs=1e-12
        )
        assert ready.independent_evidence_mass == pytest.approx(exp_mass, abs=1e-12)
        assert {s.capability for s in ready.pooled_capabilities} == {
            r.capability_key for r in rows
        }

        # Observation counts fold from the Demonstrated series (one per attempt).
        attempts = {p.attempt_id for p in series}
        assert ready.direct_observation_count == len(attempts)
        assert ready.unassisted_observation_count <= ready.direct_observation_count
        checked += 1

    assert checked > 0


def test_ready_derivation_none_on_legacy_vault(tmp_path):
    root = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "linear_algebra", root)
    vault = load_vault(root)  # left at its native (mvp-0.6) algorithm version
    repository = Repository(root / "state.sqlite")
    if vault.config.algorithms.algorithm_version == "mvp-0.7":
        pytest.skip("fixture is already canonical-state")
    ready = facet_ready_derivation(vault, repository, "facet_x", [])
    assert ready is None
