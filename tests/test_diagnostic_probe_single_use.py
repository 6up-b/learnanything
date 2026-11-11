"""Single-use diagnostic_probe surfaces (owner design intent).

A vault-authored ``practice_mode: diagnostic_probe`` item exists to carry
exactly one *diagnostic* administration: re-serving it conflates memorization
of the question with understanding. Diagnostic attempts are deliberately
excluded from FSRS (measurement hygiene), so nothing ever re-dues the card —
before these guards the item simply lived in the ordinary scheduler pool
forever.

Doors pinned here:

* the freshness reserve: a diagnostic surface never enters the ordinary
  scheduler pool at all — not even before its administration — so ordinary
  practice cannot burn its freshness (probe/pack/follow-up flows serve it;
  see test_diagnostic_probe_freshness.py);
* attempt recording deactivates the item (shared compute path, so replay
  reproduces the flip);
* the scheduler's candidate gate skips an already-administered diagnostic
  probe even when its state row is still active (pre-fix vaults);
* vault sync never force-reactivates an administered diagnostic probe.
"""

from __future__ import annotations

from learnloop.substrate.replay import replay_learning_object
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state

from tests.diagnostic_probe_single_use_helpers import CLOCK, DIAG_ITEM, LO_ID, _diagnostic_attempt, _vault

def _queue_ids(vault, repository) -> set[str]:
    queue = build_due_queue(
        vault, repository, clock=CLOCK, persist_explanations=False
    )
    return {item.practice_item_id for item in queue}


def test_diagnostic_probe_item_deactivates_after_its_attempt(tmp_path):
    vault, repository = _vault(tmp_path)
    # Freshness reserve: even before its administration the surface is kept
    # out of the ordinary pool (it is served through diagnostic flows only).
    assert DIAG_ITEM not in _queue_ids(vault, repository)

    _diagnostic_attempt(vault, repository)

    state = repository.practice_item_state(DIAG_ITEM)
    assert state is not None and state.active is False
    assert DIAG_ITEM not in _queue_ids(vault, repository)


def test_attempted_diagnostic_probe_is_gated_even_while_still_active(tmp_path):
    """Defensive scheduler gate for vaults whose administration predates the
    attempt-time deactivation: last_attempt_at set + active True still skips."""

    attempted, fresh = "pi_diag_attempted", "pi_diag_fresh"
    vault, repository = _vault(tmp_path, item_ids=(attempted, fresh))
    repository.upsert_practice_item_state(
        attempted,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
        clock=CLOCK,
    )

    ids = _queue_ids(vault, repository)
    assert attempted not in ids
    # A never-administered diagnostic probe is ALSO reserved out of the
    # ordinary pool (freshness reserve); it is served through diagnostic
    # flows only, so neither surface appears here.
    assert fresh not in ids


def test_vault_sync_does_not_reactivate_an_administered_diagnostic_probe(tmp_path):
    vault, repository = _vault(tmp_path)
    _diagnostic_attempt(vault, repository)
    assert repository.practice_item_state(DIAG_ITEM).active is False

    sync_vault_state(vault, repository, clock=CLOCK)

    assert repository.practice_item_state(DIAG_ITEM).active is False


def test_rebuild_derived_state_reproduces_the_deactivation(tmp_path):
    """practice_item_state is derived: the replay path must re-flip active."""

    vault, repository = _vault(tmp_path)
    _diagnostic_attempt(vault, repository)

    replay_learning_object(vault, repository, LO_ID)

    state = repository.practice_item_state(DIAG_ITEM)
    assert state is not None and state.active is False
    assert DIAG_ITEM not in _queue_ids(vault, repository)
