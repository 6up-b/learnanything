-- F5 hypothesis surfaces (spec_hypothesis_surfaces.md §4.3): a durable origin
-- for diagnostic episodes so analytics can separate adversarial selection
-- (e.g. 'overconfidence_list') from ordinary drift.
--
-- Origin previously lived only in the free-form target_decision_json blob under
-- a reserved key, which the target-selection flow overwrites — so origin
-- survived only until target selection. This dedicated nullable column persists
-- it for the life of the episode. Legacy rows keep NULL origin.
ALTER TABLE probe_episodes ADD COLUMN origin TEXT;
