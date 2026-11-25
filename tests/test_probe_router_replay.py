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
                                           router_decision_id=_automatic_decision(repository, vault, factor, "probe"),
                                           clock=CLOCK)
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


def _automatic_decision(repository, vault, factor: str, chosen_ref: str) -> str:
    """The automatic lane's real router decision on the factor (FG1, as below the probe router's tag): a probe-lane
    workflow on a graded miss an hour before, naming its committed decision."""

    from learnloop.db.stores import followup_serve as store
    from learnloop.router.plan_log import log_followup_decision

    from tests.causal_orchestrator_helpers import LO_ID

    from datetime import timedelta

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
    from learnloop.clock import FrozenClock

    from tests.probe_block_end_helpers import _grade
    from tests.probe_router_authority_helpers import CLOCK

    earlier = FrozenClock(CLOCK.now() - timedelta(hours=1))
    at = earlier.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    # A miss graded and applied live, as the automatic lane's source answer is.
    miss = apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="answer",
                           attempt_type="independent_attempt"),
        attempt_id="att_miss", grade=_grade(0), grading_source="ai"), clock=earlier)
    assert miss is not None
    with repository.atomic(), repository.connection() as connection:
        store.insert_workflow(connection, {"id": "wf_automatic", "source_attempt_id": "att_miss", "revision_key": "r1",
                                           "learning_object_id": LO_ID, "session_id": None, "surface": "desktop",
                                           "origin": "practice", "lane": "probe", "feedback_held": 0,
                                           "created_at": at})
        decision_id = log_followup_decision(connection, {
            "workflow": {"id": "wf_automatic", "learning_object_id": LO_ID, "source_attempt_id": "att_miss",
                         "factor_id": factor},
            "chosen_ref": chosen_ref, "propensity": 0.8, "router_record": {}, "config": vault.config,
            "decided_at": at})
        store.update_workflow(connection, "wf_automatic", at=at, factor_id=factor, decision_id=decision_id,
                              chosen_ref=chosen_ref)
    return str(decision_id)


def test_a_predecessor_decisions_pin_answered_after_activation_rebuilds_to_the_live_rows(tmp_path):
    """G2-R36: a real predecessor decision (the automatic lane's router decision, as below the tag) pins its probe; the
    vault is upgraded and the pin is answered after the activation, under the tag. The live rows, snapshotted before
    any rebuild, are what two rebuilds leave: nothing live wrote is rewritten, the first rebuild adds only its receipt,
    derived projections live had not built and the activity catalog backfill, and the second reproduces the first."""

    from learnloop.diagnosis import causal_orchestrator as causal
    from learnloop.diagnosis import probe_offer
    from learnloop.substrate.state_sync import sync_vault_state

    from tests.causal_orchestrator_helpers import _activate_probe_candidate, _add_probe_item, _seed_factor, _vault
    from tests.helpers import admit_probe_instrument_card
    from tests.probe_block_end_helpers import _submit
    from tests.probe_router_authority_helpers import CLOCK, PROBE_ITEM

    _first_vault, repository, root = _vault(tmp_path / "answered_after", with_probe_item=True, version=BEFORE)
    _add_probe_item(root, item_id="pi_causal_probe_002", surface="second_contrast_surface")
    factor, first, second = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM, "pi_causal_probe_002"))
    _activate_probe_candidate(repository, factor, first, second)
    vault = load_vault(root)
    sync_vault_state(vault, repository)  # as the app does when it opens the vault: the items' states and hashes
    status = causal.causal_repair_status(vault, repository, misconception_id=first, start_repair=False, clock=CLOCK)
    assert status.probe_offered
    from learnloop.router.plan_log import PROBE_REF

    decision_id = _automatic_decision(repository, vault, factor, PROBE_REF)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()[0] == 1
    offer = probe_offer.accept_probe_offer(vault, repository, factor_id=factor,
                                           decision_receipt_id=status.decision_receipt_id,
                                           router_decision_id=decision_id, clock=CLOCK)
    assert offer.accepted
    assert upgrade(root, to=HEAD).upgraded
    vault = load_vault(root)
    assert vault.config.algorithms.algorithm_version == HEAD
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)  # this process, reloaded after it
    result = _submit(vault, repository, item_id=PROBE_ITEM, presentation_id=offer.presentation_id, score=0)
    assert result.probe_block_end is not None
    live = _rows(root)
    with repository.connection() as connection:
        answered = connection.execute("SELECT COUNT(*) FROM probe_observations o JOIN practice_attempts a "
                                      "ON a.id = o.attempt_id WHERE a.probe_presentation_id = ?",
                                      (offer.presentation_id,)).fetchone()[0]
    assert answered == 1  # the predecessor decision's pin, answered under the tag
    rebuild_all_derived_state(vault, repository)
    first_rows = _rows(root)
    rebuild_all_derived_state(load_vault(root), repository)
    second_rows = _rows(root)
    assert _without_receipts(second_rows) == _without_receipts(first_rows)
    catalog = {"activity_cards", "activity_card_versions", "activity_families", "activity_family_versions",
               "activity_surfaces"}
    for table, rows in _without_receipts(first_rows).items():
        if rows == live.get(table, []):
            continue
        if TABLE_ROLES[table] is TableRole.DERIVED and not live.get(table):
            continue
        assert table in catalog and set(live.get(table, [])) <= set(rows), table
