"""G2: the probe router changes future decisions, never what replay derives from recorded history; so its upgrade row is
``Link(PROBE_ROUTER_ALGORITHM_VERSION, idempotent_projection)`` (``docs/reviews/refactor-g2-design.md`` §3, "Upgrade
action", and §8's bounded verification: "one same-history rebuild test with a stored value-stopped episode").

Each history is recorded at the probe router's predecessor: an episode ended by its value stop, and a learner-lane probe
pinned with a router decision (as the automatic lane pins it below the tag), answered, with its block closed and its
completion evaluated. Copies of the same history are rebuilt whole at the predecessor and at the tag, and once more
after ``learnloop upgrade``: every table, every row, compares equal once surrogate ids, timestamps and the tag string
are set aside. A rebuild at the tag repeated gives the same rows. No recorded decision, probe, observation, lock or
episode is rewritten.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from learnloop.algorithm_versions import PROBE_ROUTER_ALGORITHM_VERSION
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.ops.upgrades import UPGRADES, idempotent_projection, upgrade
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import _set_algorithm_version_at
from tests.probe_router_helpers import BEFORE_PROBE_ROUTER

HEAD = PROBE_ROUTER_ALGORITHM_VERSION
BEFORE = BEFORE_PROBE_ROUTER
_SURROGATE = re.compile(
    r"(?<![A-Za-z0-9])(?:[0-9A-HJKMNP-TV-Z]{26}|[0-9a-hjkmnp-tv-z]{26}|[0-9a-f]{32}|[0-9a-f]{64}|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?![A-Za-z0-9])")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")


def _masked(value: object) -> str:
    text = json.dumps(value, sort_keys=True, default=str)
    text = _TIME.sub("<time>", _SURROGATE.sub("<id>", text))
    return text.replace(HEAD, "<tag>").replace(BEFORE, "<tag>")


def _rows(root: Path) -> dict[str, list[str]]:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    out: dict[str, list[str]] = {}
    with repository.connection() as connection:
        present = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for table in sorted(TABLE_ROLES):
            if table not in present:
                continue
            out[table] = sorted(_masked(dict(row)) for row in connection.execute(f'SELECT * FROM "{table}"'))
    return out


def _rebuilt_at(source: Path, tmp_path: Path, name: str, version: str, *, twice: bool = False) -> dict[str, list[str]]:
    root = tmp_path / name
    copy_tree_with_databases(source, root)
    _set_algorithm_version_at(root, version)
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    rebuild_all_derived_state(vault, repository)
    if twice:
        first = _rows(root)
        rebuild_all_derived_state(load_vault(root), repository)
        assert _without_receipts(_rows(root)) == _without_receipts(first)
    return _rows(root)


def _without_receipts(rows: dict[str, list[str]]) -> dict[str, list[str]]:
    """A second rebuild appends its own receipt; everything else is the first's."""

    return {table: values for table, values in rows.items() if table != "derived_state_rebuilds"}


def _value_stopped_history(tmp_path, monkeypatch) -> Path:
    from tests.voi_stopping_helpers import _answer_probe, _long_probe_vault, _minutes

    vault, repository = _long_probe_vault(tmp_path / "value_stop", BEFORE)
    _minutes(monkeypatch, 10_000.0)
    episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "value_of_information_stop"
    return Path(vault.root)


def _router_pinned_history(tmp_path) -> Path:
    from learnloop.diagnosis import causal_orchestrator as causal
    from learnloop.diagnosis import probe_offer

    from tests.causal_orchestrator_helpers import _activate_probe_candidate, _add_probe_item, _seed_factor, _vault
    from tests.helpers import admit_probe_instrument_card
    from tests.probe_block_end_helpers import _submit
    from tests.probe_router_authority_helpers import CLOCK, PROBE_ITEM

    _first_vault, repository, root = _vault(tmp_path / "router_pinned", with_probe_item=True, version=BEFORE)
    _add_probe_item(root, item_id="pi_causal_probe_002", surface="second_contrast_surface")
    factor, first, second = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM, "pi_causal_probe_002"))
    _activate_probe_candidate(repository, factor, first, second)
    vault = load_vault(root)
    status = causal.causal_repair_status(vault, repository, misconception_id=first, start_repair=False, clock=CLOCK)
    assert status.probe_offered and status.router_state is None
    offer = probe_offer.accept_probe_offer(vault, repository, factor_id=factor,
                                           decision_receipt_id=status.decision_receipt_id,
                                           router_decision_id="history_router_decision", clock=CLOCK)
    assert offer.accepted
    result = _submit(vault, repository, item_id=PROBE_ITEM, presentation_id=offer.presentation_id, score=0)
    assert result.probe_block_end is not None
    return Path(root)


def test_the_upgrade_row_is_an_idempotent_projection():
    (link,) = [link for link in UPGRADES if link.tag == HEAD]
    assert link.activate is idempotent_projection


@pytest.mark.parametrize("history", ["value_stopped", "router_pinned"])
def test_the_same_history_rebuilds_to_the_same_rows_at_the_predecessor_and_at_the_tag(history, tmp_path, monkeypatch):
    source = (_value_stopped_history(tmp_path, monkeypatch) if history == "value_stopped"
              else _router_pinned_history(tmp_path))
    recorded = _rows(source)
    # The rebuild has something to derive: the history's attempts and their projections.
    assert recorded["practice_attempts"] and recorded["probe_observations"]
    before = _rebuilt_at(source, tmp_path, "rebuilt_before", BEFORE)
    at_tag = _rebuilt_at(source, tmp_path, "rebuilt_at_tag", HEAD, twice=True)
    assert _without_receipts(at_tag) == _without_receipts(before)
    # Nothing the history recorded is rewritten by either rebuild: the episodes, their presentations, observations and
    # locks, the causal factors and the decisions and receipts.
    for table in ("probe_episodes", "probe_presentations", "probe_observations", "hypothesis_sets",
                  "unresolved_cause_factors", "causal_probe_decision_receipts", "router_decisions"):
        assert at_tag.get(table) == recorded.get(table) == before.get(table), table
    # Through the upgrade itself: the row activates with no rebuild and changes no derived row.
    upgraded = tmp_path / "upgraded"
    copy_tree_with_databases(source, upgraded)
    result = upgrade(upgraded, to=HEAD)
    assert result.upgraded
    after_upgrade = _rows(upgraded)
    derived = [table for table in recorded if TABLE_ROLES[table] is TableRole.DERIVED]
    assert {table: after_upgrade.get(table) for table in derived} == {table: recorded[table] for table in derived}
