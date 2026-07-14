-- Extraction quality is part of the durable IR contract. Without this column,
-- a reload silently discarded page flags and made repair suggestions vanish.
ALTER TABLE source_extraction_runs ADD COLUMN health_json TEXT;
