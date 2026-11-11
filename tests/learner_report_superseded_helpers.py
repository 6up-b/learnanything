"""What other test files use from ``tests/test_learner_report_superseded.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.algorithm_versions import SUPERSEDED_CLAIMS_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import add_followup_item, create_placement_vault
from tests.rebuild_equivalence_helpers import _at


TAG = SUPERSEDED_CLAIMS_ALGORITHM_VERSION


def _vault(tmp_path, version=TAG, name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    return paths, vault, repository
