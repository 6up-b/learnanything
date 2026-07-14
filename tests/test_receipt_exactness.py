"""B5 exactness invariant (spec §5.2): the facet evidence timeline's final
folded credit equals the banked canonical ledger credit EXACTLY, on every
fixture vault with attempt history.

This is the test that retires baseline fact 2 ("the drawer claimed exactness
while the timeline omitted grouped caps") and unblocks the exact drawer copy.
Each fixture is copied to a scratch dir, flipped to mvp-0.7, and the canonical
projection is re-banked from its real attempt history so the comparison is
authoritative-fold vs timeline-fold over identical evidence.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.facet_evidence_timeline import (
    _observation_events,
    facet_evidence_timeline,
    fold_demonstrated_timeline,
)
from learnloop.services.canonical_projection import _repeat_discount
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
        facets.update(vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets)
    return sorted(facets)


@pytest.mark.parametrize("fixture_name", FIXTURE_VAULTS)
def test_timeline_final_credit_equals_banked_ledger_credit(tmp_path, fixture_name):
    vault, repository = _loaded_fixture(tmp_path, fixture_name)
    attempts = repository.list_attempt_history()
    if not attempts:
        pytest.skip(f"fixture {fixture_name} has no attempt history")

    project_canonical_facet_state(vault, repository)
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    assert sum(banked.values()) > 0.0, "fixture with attempts should bank some credit"

    for facet in _all_facets(vault, banked):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        expected = banked.get(facet, 0.0)
        # Exact fold over the immutable ledger: only float re-association slack.
        assert final == pytest.approx(expected, abs=1e-12), (
            f"{fixture_name}:{facet} timeline={final} banked={expected}"
        )


def test_from_scratch_fold_equals_incremental_fold_on_real_history(tmp_path):
    """§16 replay invariant on real fixture data: folding every prefix of the
    extracted observation events reproduces the full series byte-identically."""

    vault, repository = _loaded_fixture(tmp_path, "linear_algebra")
    project_canonical_facet_state(vault, repository)
    discount = _repeat_discount(vault)
    checked = 0
    for cell in repository.facet_capability_evidence_all():
        facet = cell.facet_id
        events = _observation_events(vault, repository, facet)
        if not events:
            continue
        full = fold_demonstrated_timeline(events, repeat_surface_discount=discount)
        for i in range(1, len(events) + 1):
            prefix = fold_demonstrated_timeline(events[:i], repeat_surface_discount=discount)
            assert [p.as_dict() for p in prefix] == [p.as_dict() for p in full[:i]]
        checked += 1
    assert checked > 0
