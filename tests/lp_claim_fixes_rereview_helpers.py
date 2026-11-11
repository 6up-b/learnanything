"""What other test files use from ``tests/test_lp_claim_fixes_rereview.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, SUCCESSOR_CHAIN
from learnloop.ops.vault_upgrade import rewrite_algorithm_version

from tests.lp_claim_fixes_review_helpers import _journal, _predecessor_vault_with_claims


TAG = CLAIM_FIXES_ALGORITHM_VERSION
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]


def _interrupted(tmp_path, name):
    """The state a death between the publication and the commit leaves.

    The successor's label over the predecessor's database, with the journal
    (``test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal``
    produces it with a real death; this builds the same three facts directly)."""

    paths = _predecessor_vault_with_claims(tmp_path, name)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    return paths
