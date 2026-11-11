"""What other test files use from ``tests/test_regrade_contract_successor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import REGRADE_CONTRACT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.split_live_helpers import split_vault
from tests.held_grade_evidence_helpers import T


VERSION = REGRADE_CONTRACT_ALGORITHM_VERSION
JOINT = "[diagnosis]\nsplit_enabled = false"


def _vault(tmp_path, *, version=VERSION, config=""):
    return split_vault(tmp_path, version=version, config=config)


def _rebuild(vault, repository, days=30):
    return rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=days)))


def _settle(vault, repository, days=30):
    """Rebuild to the fixed point. A rebuild reaches it in one pass after a
    regrade (which replays in its own transaction) and in two after a write
    that does not replay (an adjudication, a label move): replay reads the
    canonical projection as each attempt's prior, so the first pass reads the
    projection the change made stale (shown identical at mvp-0.25 in
    ``test_rebuild_converges_after_an_adjudication_as_it_did_before``)."""

    _rebuild(vault, repository, days)
    _rebuild(vault, repository, days)
