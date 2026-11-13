"""A vault whose history the regrade-contract successor (mvp-0.26) reinterprets, for
``tests/test_reader_recap_review_r3.py`` (the upgrade's own suite left with the chain, refactor D3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.held_grade_evidence_helpers import T, _graded_apply
from tests.regrade_contract_replay_helpers import (
    ITEM,
    SIBLING_ITEM,
    _regrade,
    _self_graded_apply,
    _set_result_points,
)
from tests.regrade_contract_successor_helpers import _settle, _vault


PREDECESSOR = METHOD_EXPLICIT_ALGORITHM_VERSION
CLOCK = FrozenClock(datetime(2026, 12, 1, 12, 0, tzinfo=UTC))


def _legacy_vault(tmp_path, *, config=""):
    """An mvp-0.25 vault holding the three shapes the successor meets:
    ``att_keep`` graded and never regraded (cites its contract), ``att_blind``
    regraded within its original maximum by the blind grader (uncited; the
    blind record kept its maximum, 8) and ``att_self`` self-graded then
    regraded on a sibling item (uncited); rebuilt to the predecessor's fixed
    point."""

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR, config=config)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_keep", when=T)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_blind",
                  when=T + timedelta(hours=1))
    _self_graded_apply(vault, repository, SIBLING_ITEM, {"setup": 1.0, "result": 2.0}, attempt_id="att_self",
                       when=T + timedelta(hours=2))
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_blind", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))
    _regrade(vault, repository, "att_self", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1, hours=1))
    _settle(vault, repository)
    return paths, vault, repository
