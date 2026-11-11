"""What other test files use from ``tests/test_rbeq_pr2_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, REPLAY_LEDGER_ALGORITHM_VERSION
from learnloop.ops.vault_upgrade import rewrite_algorithm_version

from tests.rebuild_equivalence_helpers import _mastery
from tests.rebuild_equivalence_review_helpers import _rebuilt, _two_attempt_history


TAG = REPLAY_LEDGER_ALGORITHM_VERSION
PREDECESSOR = CLAIM_FIXES_ALGORITHM_VERSION


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _predecessor_with_old_replay(tmp_path, name):
    """A predecessor vault whose last rebuild left the predecessor's replay
    (which differs from live on this history), and the live mastery."""

    paths, vault, repository = _two_attempt_history(tmp_path, name, version=PREDECESSOR)
    live = _mastery(repository)
    assert _rebuilt(vault, repository) != live
    return paths, live


def _interrupted(tmp_path, name):
    """The three facts a death between the publication and the commit leaves:
    the tag's label, the predecessor's database, and the journal naming both."""

    paths, live = _predecessor_with_old_replay(tmp_path, name)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    return paths, live
