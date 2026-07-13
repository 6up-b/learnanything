"""Hierarchical family → item calibration shrinkage (spec §9.7, test 26)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import enter_episode, episode_hypothesis_set, resolve_instrument
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_V1,
    record_real_observation_counts,
    shrunk_item_calibration_counts,
)
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_A = "pi_svd_define_001"
ITEM_B = "pi_svd_define_other"
FAMILY = CONTRAST_CONFUSABLE_V1.id
VERSION = CONTRAST_CONFUSABLE_V1.version
GRADER = CONTRAST_CONFUSABLE_V1.grader_policy
CLOCK = FrozenClock(NOW)


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_A,))
    return loaded, repository


def _record(repository, *, item_id, outcome, slot, times):
    for _ in range(times):
        record_real_observation_counts(
            repository,
            family_template_id=FAMILY,
            family_template_version=VERSION,
            posterior_after={slot: 1.0},
            slot_map={slot: slot},
            observed_outcome=outcome,
            grader_version=GRADER,
            practice_item_id=item_id,
            clock=CLOCK,
        )


def test_sparse_item_inherits_family_posterior(tmp_path):
    """§16 test 26: item estimates shrink toward the family posterior until
    the item's own evidence rivals the shrinkage mass."""

    _loaded, repository = _setup(tmp_path)
    # 40 family observations (via item A): unfamiliar learners answered
    # `hedge`, contradicting the card prior's `unanswered`-heavy row.
    _record(repository, item_id=ITEM_A, outcome="hedge", slot="unfamiliar", times=40)

    # Item B has NO evidence of its own: its counts are exactly the family
    # direction, capped at the shrinkage pseudo-count (25 by default).
    blended = shrunk_item_calibration_counts(
        repository,
        FAMILY,
        VERSION,
        practice_item_id=ITEM_B,
        grader_version=GRADER,
        item_shrinkage_pseudo_count=25.0,
    )
    assert blended is not None
    row = blended["unfamiliar"]
    assert row["hedge"] == 25.0  # capped family mass, family direction
    assert sum(row.values()) == 25.0


def test_item_evidence_outgrows_family_shrinkage(tmp_path):
    _loaded, repository = _setup(tmp_path)
    _record(repository, item_id=ITEM_A, outcome="hedge", slot="unfamiliar", times=40)
    # Item B accumulates 100 contrary observations of its own.
    _record(repository, item_id=ITEM_B, outcome="unanswered", slot="unfamiliar", times=100)

    blended = shrunk_item_calibration_counts(
        repository,
        FAMILY,
        VERSION,
        practice_item_id=ITEM_B,
        grader_version=GRADER,
        item_shrinkage_pseudo_count=25.0,
    )
    row = blended["unfamiliar"]
    # The family layer (which pools BOTH items' evidence) contributes at most
    # 25 of mass across the row; the item's own 100 ride on top, so the item's
    # observed direction dominates the contrary family-only signal.
    assert row["unanswered"] >= 100.0
    assert row["hedge"] <= 25.0
    assert row["unanswered"] > 4 * row["hedge"]


def test_resolve_instrument_reads_calibrated_rows(tmp_path):
    """The read path feeds real-learner counts (keyed by the template's
    grader_policy — the same key the write path records under) into
    compilation, so calibrated rows differ from the pure card prior."""

    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    item = loaded.practice_items[ITEM_A]

    before, _ = resolve_instrument(loaded, repository, item, hypothesis_set)
    _record(repository, item_id=ITEM_A, outcome="hedge", slot="unfamiliar", times=40)
    after, _ = resolve_instrument(loaded, repository, item, hypothesis_set)

    assert after.rows["unfamiliar"]["hedge"] > before.rows["unfamiliar"]["hedge"]
