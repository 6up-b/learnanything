"""What other test files use from ``tests/test_rebuild_equivalence_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import add_followup_item, create_placement_vault
from tests.rebuild_equivalence_helpers import _answer, _at


def _two_attempt_history(tmp_path, name, *, version, config=""):
    """The LP-min record's oracle case at ``version``: two attempts on one
    item with no claim, whose replay differed from live below the tag."""

    from tests.helpers import append_config_toml

    paths = create_placement_vault(tmp_path / name, version=version)
    add_followup_item(paths.root)
    if config:
        append_config_toml(paths.root, config)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    _answer(vault, repository, "pi_svd_define_001", minutes=1, points=4.0)
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)
    return paths, vault, repository


def _rebuilt(vault, repository):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.rebuild_equivalence_helpers import _mastery

    rebuild_all_derived_state(vault, repository)
    return _mastery(repository)
