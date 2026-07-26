-- Causal §5.1 / §7: v1 commissioning exposed observation-conditioned
-- postdictive claims to the nominally blind generator. Existing candidates
-- remain visible for audit but are not servable under the v2 input contract.
ALTER TABLE causal_probe_candidates
  ADD COLUMN blind_input_contract_version TEXT;

ALTER TABLE causal_blind_prediction_bundles
  ADD COLUMN blind_input_contract_version TEXT;
