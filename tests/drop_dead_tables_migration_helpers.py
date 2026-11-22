"""What earlier migrations' upgrade diffs use from the dead-table drop (``tests/test_drop_dead_tables_migration.py``),
kept here because a test file never imports another (``tests/test_test_layout.py``)."""

from __future__ import annotations


#: The five tables the drop removes (refactor step J2, the table review's group A still dead at its tip).
J2_DROPPED_TABLES = frozenset({
    "angle_inventories",
    "family_evidence_cap_policies",
    "controller_constraint_manifests",
    "controller_prequential_reports",
    "learner_theta",
})
#: Everything that goes with them (each table's own indexes and autoindexes): earlier migrations' "nothing else
#: changed" diffs on the way to head admit these as removed, the way they admit a later migration's added objects.
J2_DROPPED_OBJECTS = J2_DROPPED_TABLES | frozenset({
    "sqlite_autoindex_angle_inventories_1",
    "idx_angle_inv_family",
    "sqlite_autoindex_family_evidence_cap_policies_1",
    "sqlite_autoindex_family_evidence_cap_policies_2",
    "sqlite_autoindex_controller_constraint_manifests_1",
    "sqlite_autoindex_controller_constraint_manifests_2",
    "sqlite_autoindex_controller_prequential_reports_1",
    "idx_controller_prequential_reports_target",
    "idx_controller_prequential_reports_hash",
    "sqlite_autoindex_learner_theta_1",
    "idx_learner_theta_unique",
})
