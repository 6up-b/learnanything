"""B5 exactness invariant (spec §5.2): the facet evidence timeline's final
folded credit equals the banked canonical ledger credit EXACTLY, on every
fixture vault with attempt history — under BOTH canonical algorithm versions.

This is the test that retires baseline fact 2 ("the drawer claimed exactness
while the timeline omitted grouped caps") and unblocks the exact drawer copy.
Each fixture is copied to a scratch dir, pinned to the parametrized algorithm
version, and the canonical projection is re-banked from its real attempt
history so the comparison is authoritative-fold vs timeline-fold over
identical evidence.

The mvp-0.8 arm exists because the original mvp-0.7-only pin hid a real
divergence: the projection discounts evidence mass through the calibrated
response channel (``p0_effective_evidence_mass``) while the timeline read the
raw attempt-type mass, so the learner-facing Demonstrated curve over-reported
the banked ledger — including banking nonzero credit for legacy attempts the
projection banks at ZERO (no active interpretation). A guard that pins the
version it guards away is not a guard.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.causal_activity_policy import resolve_attempt_activity_policy
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
ALGORITHM_VERSIONS = ("mvp-0.7", "mvp-0.8")


def _loaded_fixture(tmp_path, name, algorithm_version="mvp-0.7"):
    root = tmp_path / name
    shutil.copytree(FIXTURES / name, root)
    toml_path = root / "learnloop.toml"
    text, count = re.subn(
        r'algorithm_version = "[^"]+"',
        f'algorithm_version = "{algorithm_version}"',
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


@pytest.mark.parametrize("algorithm_version", ALGORITHM_VERSIONS)
@pytest.mark.parametrize("fixture_name", FIXTURE_VAULTS)
def test_timeline_final_credit_equals_banked_ledger_credit(
    tmp_path, fixture_name, algorithm_version
):
    vault, repository = _loaded_fixture(tmp_path, fixture_name, algorithm_version)
    attempts = repository.list_attempt_history()
    if not attempts:
        pytest.skip(f"fixture {fixture_name} has no attempt history")

    project_canonical_facet_state(vault, repository)
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    activity_by_attempt = repository.all_causal_activity_classifications()
    has_certification_eligible_attempt = any(
        resolve_attempt_activity_policy(
            attempt_type=str(attempt["attempt_type"]),
            primed=bool(attempt.get("primed")),
            hints_used=int(attempt.get("hints_used") or 0),
            recorded=activity_by_attempt.get(str(attempt["id"])),
        ).eligible_for_certification
        for attempt in attempts
    )
    if algorithm_version == "mvp-0.7" and has_certification_eligible_attempt:
        assert sum(banked.values()) > 0.0, "fixture with attempts should bank some credit"
    # Assisted/primed attempts certify nothing under either version.  Under
    # mvp-0.8, a fixture whose attempts predate P0.2 interpretations can also
    # bank ZERO reliable mass (no active interpretation -> no silent full
    # credit). The per-facet equality below remains the divergence detector.

    for facet in _all_facets(vault, banked):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        expected = banked.get(facet, 0.0)
        # Exact fold over the immutable ledger: only float re-association slack.
        assert final == pytest.approx(expected, abs=1e-12), (
            f"{fixture_name}@{algorithm_version}:{facet} timeline={final} banked={expected}"
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
