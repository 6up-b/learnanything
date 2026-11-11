"""What other test files use from ``tests/test_batch3_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.algorithm_versions import ONE_ASK_ALGORITHM_VERSION, REPLAY_LEDGER_ALGORITHM_VERSION
from learnloop.ops.vault_upgrade import rewrite_algorithm_version


TAG = ONE_ASK_ALGORITHM_VERSION
PREDECESSOR = REPLAY_LEDGER_ALGORITHM_VERSION


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _vault_at(tmp_path, name, version):
    from tests.helpers import create_placement_vault

    return create_placement_vault(tmp_path / name, version=version)


def _activated(paths, version=TAG) -> bool:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


def _interrupted(tmp_path, name):
    """What a death between the publication and the commit leaves: the tag's
    label over the predecessor's database, with the journal naming both."""

    paths = _vault_at(tmp_path, name, PREDECESSOR)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    assert not _activated(paths)
    return paths
