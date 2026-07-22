-- Preserve generated synthesis candidates before gates/proposal persistence so
-- failures remain inspectable and can be revalidated without another model call.
ALTER TABLE synthesis_runs ADD COLUMN candidate_output_json TEXT;
