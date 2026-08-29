-- Repair opportunities are born at treatment selection, before the primed/cold
-- pair is ranked.  The episode is the durable bridge from that pre-selection
-- opportunity to the later primed attempt and scheduled follow-up task.
--
-- This is separate from migration 151 so development vaults that applied the
-- initial opportunity substrate before repair selection moved earlier can
-- adopt the bridge monotonically.

ALTER TABLE remediation_episodes
  ADD COLUMN cold_measurement_opportunity_id TEXT;

CREATE INDEX idx_remediation_episodes_cold_measurement_opportunity
  ON remediation_episodes(cold_measurement_opportunity_id);
