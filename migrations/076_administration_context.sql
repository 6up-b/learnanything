-- P1 step 5 (spec_p1_shared_substrate §3.10): purpose-specific administration
-- adapters need the administration's context recorded alongside its immutable
-- purpose. Additive nullable columns on the P0 (migration 065) administration row
-- -- byte-safe for replay (mirrors the 068 episode-pin ALTER precedent); the
-- existing snapshot_json and purpose columns are untouched. Context is genuinely
-- new per-administration data (owner decision A.1's sanctioned ALTER exception).
--
-- reading_phase (U-033): before_section / during_section / after_section, set only
--   when the administration occurs inside a reader session. An owner-placed reading
--   question is an ordinary instructional administration with source_visible=true
--   and a reading phase, NOT a new activity kind (§3.10).
-- admin_context_json: cold/scaffolded, hints, feedback exposure, timing, tools,
--   collaboration, source visibility, goal-terminal conditions (§3.10). Independent
--   of purpose; the ADAPTER is selected by family purpose, never by attempt_type.

ALTER TABLE activity_administrations ADD COLUMN reading_phase TEXT;
ALTER TABLE activity_administrations ADD COLUMN admin_context_json TEXT;
