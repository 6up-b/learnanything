"""The reading step's kill switch (UX Phase 1 usability round 1, U4).

U4 changed what the plan's reading block serves: the step continues from the
furthest section the learner read into and is never front or back matter
while a chapter is left. The branch built it as its own successor tag (a
placeholder, round-2 re-review F2). At its landing on main the owner's
standing decision applied instead: live changes behind kill switches, not
successors, for serving changes that replay never reads (the facet-locks F6
ruling; docs/reviews/ux-phase1.md, "Landing onto main"). So the selection acts
wherever the plan acts, behind ``plan.reading_from_furthest``; off, it is
DL1's selection exactly (``tests/test_ux_phase1_round2_review.py`` compares
it with DL1's code across four reading histories). Replay never reads it: a
rebuild with the switch on or off leaves every DERIVED table the same.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import learnloop.algorithm_versions as algorithm_versions
from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    ROUTE_RULES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.stuck import stuck_prompt_active
from learnloop.clock import FrozenClock
from learnloop.config.template import (
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    default_config_text,
    defaults_fingerprint_for_version,
    effective_defaults_fingerprint,
)
from learnloop.daily_plan.engine import plan_active, reading_from_furthest_active
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.placement.state import placement_active
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.recurrence_groups import recurrence_active
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_202"
CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def test_the_reading_step_is_not_a_successor_tag():
    # No version names it, and the chain is main's: the route rules in the
    # grader (mvp-0.20, which landed after UX Phase 1), value-of-information
    # stopping (mvp-0.21) and Tier 1's Decider judgments (mvp-0.22, the
    # latest) follow it.
    assert not [name for name in dir(algorithm_versions) if "READING_FROM_FURTHEST" in name]
    # Router R2a's staged frame (mvp-0.23) followed, and router R2b + R2c's
    # model mixture (mvp-0.24) is now the latest.
    assert SUCCESSOR_CHAIN[-5] == ROUTE_RULES_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.24"
    assert len(SUCCESSOR_CHAIN) == len(set(SUCCESSOR_CHAIN))


def test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.9")
    expected = {
        "mvp-0.9": (False, False),
        "mvp-0.13": (False, False),
        DAILY_PLAN_ALGORITHM_VERSION: (True, True),
        LATEST_ALGORITHM_VERSION: (True, True),
    }
    for version, flags in expected.items():
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        assert (plan_active(vault), reading_from_furthest_active(vault)) == flags, version
    append_config_toml(paths.root, "[plan]\nreading_from_furthest = false\n")
    switched_off = load_vault(paths.root)
    assert reading_from_furthest_active(switched_off) is False
    # The kill switch keeps the version and every other behaviour.
    assert switched_off.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    assert plan_active(switched_off) and split_grading_active(switched_off) and placement_active(switched_off)
    assert recurrence_active(switched_off) and stuck_prompt_active(switched_off)
    # The plan's own switch still turns the whole plan off, reading step included.
    append_config_toml(paths.root, "enabled = false\n")
    assert reading_from_furthest_active(load_vault(paths.root)) is False


def test_new_vaults_read_on_from_the_furthest_section(tmp_path):
    from learnloop.vault.loader import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(NOW))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    assert plan_active(fresh) and reading_from_furthest_active(fresh)


def test_every_defaults_snapshot_records_the_switch_on():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig

    for version in SUCCESSOR_CHAIN:
        assert defaults_fingerprint_for_version(version) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
        config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(version)))
        assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM[version], version
        assert config.plan.reading_from_furthest is True, version


def _plan_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT COUNT(*) FROM daily_plans").fetchone()[0]


def test_replay_never_reads_the_switch(tmp_path):
    """On the migration-head fixture at the latest tag: a rebuild with the
    switch on and one with it off leave every DERIVED table the same, and
    neither writes a plan row."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, LATEST_ALGORITHM_VERSION)
    repository = Repository(root / "state.sqlite")
    derived = set(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {
                table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                for table in sorted(derived)
            }

    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    switched_on = snapshot()
    append_config_toml(root, "[plan]\nreading_from_furthest = false\n")
    assert reading_from_furthest_active(load_vault(root)) is False
    rebuild_all_derived_state(load_vault(root), repository, clock=CLOCK)
    assert snapshot() == switched_on
    assert _plan_rows(root / "state.sqlite") == 0
