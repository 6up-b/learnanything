-- Causal-attribution P2 (§3.8): record WHY a locked hypothesis set carries the
-- prior it carries.
--
-- `build_causal_hypothesis_set` falls back to a uniform 1.0 weight whenever no
-- arm has a support score — which, with single-attempt receipts, is every set
-- produced today.  Stored unlabelled, that authored fallback is indistinguishable
-- from a locked experimental prior, and every consumer downstream reads it as
-- evidence.  `prior_basis` is 'uniform_fallback' or 'support_weighted'.
--
-- Scope note: the rest of §3 needs no schema change.  Cohort pinning reads the
-- `model_revision` / `outcome_schema_version` columns that migration 121 already
-- puts on causal_blind_prediction_bundles; pinned bundle references already live
-- in causal_probe_candidates.blind_bundle_ids_json (and, for a served probe, in
-- the free-form probe_presentations.selection_components_json); and declared
-- feature key sets are per-bundle payload, deliberately NOT a global feature
-- registry (standing constraint 2 — no schema growth without a second consumer).
-- hypothesis_sets, unlike those, dates from 001 and is live in every vault, so
-- this one column needs a forward migration rather than an edit to unapplied 121.

ALTER TABLE hypothesis_sets ADD COLUMN prior_basis TEXT;
