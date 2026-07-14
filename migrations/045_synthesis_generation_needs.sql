-- Synthesis-time generate-discriminator needs for ING M6
-- (spec_source_ingestion_v2 §8.7 identifiability gate; knowledge-model §11.3).
--
-- The synthesis-time identifiability gate analyzes a bootstrap proposal's
-- criteria/facet-capability targets and recipes. When a distinction between two
-- facets is not identifiable by any assessment the proposal offers, the gate
-- emits a generate-discriminator need FIRST (anchor/contrast probe or item),
-- and only recommends coarsening when no distinguishing assessment exists AND
-- the instructional repairs are identical (knowledge-model §11.3).
--
-- This mirrors the probe-time `probe_generation_needs` machinery (migration
-- 028) but is synthesis-scoped: at synthesis time there is no probe episode or
-- learning object yet, so needs key on (subject_id, need_kind, target_key). The
-- probe table is left untouched so its episode/LO invariants stay intact.
--
-- ING M6 owns migration 045 (041-044 are taken by M4/M5).

CREATE TABLE synthesis_generation_needs (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  source_set_id TEXT,
  synthesis_run_id TEXT,
  need_kind TEXT NOT NULL,           -- generate_discriminator | coarsen_distinction
  target_key TEXT NOT NULL,          -- discriminating signature / confusable facet pair
  missing_capability TEXT NOT NULL,  -- capability the discriminator must observe
  facet_ids_json TEXT NOT NULL DEFAULT '[]',
  detail TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (subject_id, need_kind, target_key)
);

CREATE INDEX idx_synthesis_generation_needs_subject
  ON synthesis_generation_needs(subject_id, status);
