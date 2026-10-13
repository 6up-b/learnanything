-- Canonical sources S2a (spec_source_practice_and_probes_v1.md §8.6): what a
-- value intent's proposal was valued on. Receipts only (nullable ADD COLUMN;
-- the table's role is unchanged): the valuation receipt, one section per
-- hypothesis space, and raw exercises' provisional, quote-verified metadata.
ALTER TABLE practice_index_proposals ADD COLUMN valuation_json TEXT;
ALTER TABLE practice_index_proposals ADD COLUMN provisional_json TEXT;
