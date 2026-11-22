-- Refactor arc J, step J2: drop the first family of dead tables (docs/reviews/table-review-2026-11-11.md group A,
-- re-verified at this step's tip in docs/reviews/refactor-j2.md).
--
-- No code reads or writes any of these five tables (no SQL names them in src/, scripts/ or tests/), no later
-- migration seeds them, no foreign key points at them, no view or trigger names them, and nothing derived or served
-- reads them, so no algorithm tag moves:
--   * angle_inventories, family_evidence_cap_policies (079, the progression and lapse substrate);
--   * controller_constraint_manifests (096) and controller_prequential_reports (100), the P4 controller's
--     constraint manifests and delayed evaluation reports;
--   * learner_theta (001), the legacy IRT theta table.
-- DROP TABLE removes each table's own indexes and autoindexes with it. angle_inventories is the only one with a
-- foreign key (to activity_family_versions, which stays); none is another's parent, so the order is free.
--
-- A drop never empties a table: the lines below make the upgrade refuse, before anything is written, a database in
-- which any of the five holds a row (learnloop.db.migrate, NonEmptyDropError).
-- refuse-upgrade-if-rows: angle_inventories
-- refuse-upgrade-if-rows: family_evidence_cap_policies
-- refuse-upgrade-if-rows: controller_constraint_manifests
-- refuse-upgrade-if-rows: controller_prequential_reports
-- refuse-upgrade-if-rows: learner_theta
DROP TABLE angle_inventories;
DROP TABLE family_evidence_cap_policies;
DROP TABLE controller_constraint_manifests;
DROP TABLE controller_prequential_reports;
DROP TABLE learner_theta;
