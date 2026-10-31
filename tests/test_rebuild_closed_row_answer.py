"""Followups Oct 27 (3): answers on an LO one of whose items closed outside the attempt ledger.

The mobile PR-3/PR-4 landing found it on an owner copy: answering a row closed by
``set_practice_item_active(False)`` left ``rebuild --shadow`` at mastery 1 / schedule 1.
The cause is not the answered row's own write. The attempt path reads the
lifecycle of its LO's items: ``lo_relative_coverage`` (via ``required_facets``)
counts only the facets of the LO's *active* items, so a sibling measuring a facet
nothing else measures moves the LO's coverage, mastery and the item's due date.
Live, each attempt sees the siblings as they were at its time. Replay sees one
state for the whole history: an unattempted sibling's row is not reset, so it is
closed throughout (wrong for every answer before its closure); an attempted
item's row is rebuilt active and re-closed after the LO's last replayed attempt
(``keep_practice_items_inactive``), so it is open throughout (wrong for every
answer after its closure).

Production closes rows outside the ledger: ``retire_item`` (through
``deactivate_practice_item_serving``) and content sync (an item retired in its
YAML, removed from the vault, parked for review or superseded by a measurement
correction), probe retirement (``retire_probe_instance``), a probe dialogue's
single use and an applied proposal patch. None leaves a time replay can apply
the closure at, so no replay-only rule is exact: closed-throughout is right when
the closure came before every answer, open-throughout when it came after. Exact
replay needs a successor (the design is in docs/reviews/followups-oct27.md);
these tests pin the gap until then.
"""
from __future__ import annotations

import pytest

from learnloop.content.authoring.item_authoring import retire_item
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW_ISO
from tests.test_rebuild_equivalence import ZERO, _answer, _at, _shadow_summary, _vault

APPLY_ITEM = "pi_svd_apply_001"

_NEEDS_A_LIFECYCLE_LEDGER = pytest.mark.xfail(strict=True, reason=(
    "followups Oct 27 (3), pre-existing on main at mvp-0.36 and mvp-0.37: an attempt reads its LO's "
    "active items (required_facets -> lo_relative_coverage); a closure outside the attempt ledger has "
    "no time replay can apply it at, so replay sees the item still active. Needs a successor that "
    "records closures as ledger events (design in docs/reviews/followups-oct27.md)"
))


def _with_an_application_item(tmp_path):
    """The placement vault plus a second facet on lo_svd_definition, measured only by one item."""

    paths, _vault_before, repository = _vault(tmp_path)
    upsert_practice_item(
        paths.root,
        {
            "id": APPLY_ITEM,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["application"],
            "evidence_weights": {"application": 1.0},
            "prompt": "Use the SVD of a 2x2 matrix to find its rank.",
            "expected_answer": "The number of non-zero singular values.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct rank."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=_at(0),
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0.5))
    return paths, vault, repository


@_NEEDS_A_LIFECYCLE_LEDGER
def test_an_answer_after_a_sibling_was_retired_rebuilds_to_live(tmp_path):
    """The production path: the sibling is retired, the primary load's content sync closes its row."""

    paths, vault, repository = _with_an_application_item(tmp_path)
    _answer(vault, repository, "pi_svd_define_001", minutes=1)
    retire_item(paths.root, repository, practice_item_id=APPLY_ITEM, reason="duplicate_surface", clock=_at(2))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(3))
    assert repository.practice_item_state(APPLY_ITEM).active is False
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO


@_NEEDS_A_LIFECYCLE_LEDGER
def test_an_answer_after_the_landing_harness_closed_a_sibling_rebuilds_to_live(tmp_path):
    """The landing's case: the row closed directly, as content sync keeps a parked or superseded row."""

    paths, vault, repository = _with_an_application_item(tmp_path)
    _answer(vault, repository, "pi_svd_define_001", minutes=1)
    repository.set_practice_item_active(APPLY_ITEM, active=False, clock=_at(2))
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO


@_NEEDS_A_LIFECYCLE_LEDGER
def test_a_sibling_retired_after_the_last_answer_rebuilds_to_live(tmp_path):
    """The most common order (retire an unanswered duplicate later): replay sees it closed from the start."""

    paths, vault, repository = _with_an_application_item(tmp_path)
    _answer(vault, repository, "pi_svd_define_001", minutes=1)
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)
    retire_item(paths.root, repository, practice_item_id=APPLY_ITEM, reason="duplicate_surface", clock=_at(62))
    sync_vault_state(load_vault(paths.root), repository, clock=_at(63))
    assert repository.practice_item_state(APPLY_ITEM).active is False

    assert _shadow_summary(paths)["summary"] == ZERO


def test_control_every_sibling_open_rebuilds_to_live(tmp_path):
    paths, vault, repository = _with_an_application_item(tmp_path)
    _answer(vault, repository, "pi_svd_define_001", minutes=1)
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO
