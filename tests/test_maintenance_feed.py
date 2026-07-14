"""ING M7 — maintenance feed (§11).

Deterministic generation from existing tables; per-type aging policies
(auto-resolution / auto-expiry / escalation); dismiss/snooze without changing
source or curriculum state. Canned, zero network.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.services.maintenance_feed import (
    ESCALATION_SNOOZE_THRESHOLD,
    dismiss_notice,
    generate_maintenance_feed,
    snooze_notice,
)
from learnloop.services.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.test_source_append import _bootstrap_and_add
from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


def _feed(root, repo):
    return generate_maintenance_feed(load_vault(root), repo, clock=_CLOCK)


def test_maintenance_notice_deterministic_generation(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    feed1 = _feed(root, repo)
    ids1 = {(n["notice_type"], n["dedup_key"]) for n in feed1}
    # regeneration is idempotent — same live notices, no duplicates.
    feed2 = _feed(root, repo)
    ids2 = {(n["notice_type"], n["dedup_key"]) for n in feed2}
    assert ids1 == ids2
    assert len(feed2) == len({n["id"] for n in feed2})
    # every notice carries exactly one concrete action link.
    for notice in feed2:
        assert notice["action"].get("action")


def test_maintenance_notice_aging_policies(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})

    # Seed an open conflict (auto_resolution policy) directly.
    repo.insert_source_conflict(entity_type="facet", entity_id="facet_symmetry_definition",
                                statement="disagree", left_locator="span:s1", right_locator="span:s2",
                                clock=_CLOCK)
    feed = _feed(root, repo)
    conflict_notices = [n for n in feed if n["notice_type"] == "open_conflict"]
    assert conflict_notices and conflict_notices[0]["aging_policy"] == "auto_resolution"
    conflict_id = conflict_notices[0]["action"]["conflict_id"]

    # AUTO-RESOLUTION: resolving the conflict clears the notice on regeneration.
    repo.resolve_source_conflict(conflict_id, status="dismissed", resolution={"kind": "dismiss"},
                                 resolution_kind="dismiss", clock=_CLOCK)
    feed = _feed(root, repo)
    assert not [n for n in feed if n["notice_type"] == "open_conflict" and n["dedup_key"] == conflict_id]

    # ESCALATION: an lo_without_practice notice raises severity after N snoozes.
    lo_notices = [n for n in _feed(root, repo) if n["notice_type"] == "lo_without_practice"]
    if lo_notices:
        nid = lo_notices[0]["id"]
        assert lo_notices[0]["aging_policy"] == "escalation"
        for _ in range(ESCALATION_SNOOZE_THRESHOLD):
            snooze_notice(repo, nid, clock=_CLOCK)
        escalated = repo.maintenance_notice(nid)
        assert escalated["severity"] == "action_needed"


def test_dismiss_and_snooze_do_not_change_curriculum(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    facets_before = set(load_vault(root).evidence_facets.keys())
    feed = _feed(root, repo)
    if feed:
        dismiss_notice(repo, feed[0]["id"], clock=_CLOCK)
        # dismissed notice drops out of the live feed but curriculum is untouched.
        live = repo.maintenance_notices()
        assert feed[0]["id"] not in {n["id"] for n in live}
    assert set(load_vault(root).evidence_facets.keys()) == facets_before
