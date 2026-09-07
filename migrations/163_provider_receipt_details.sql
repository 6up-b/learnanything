-- Preserve provider-specific cache accounting without guessing missing values.
ALTER TABLE model_call_receipts ADD COLUMN endpoint TEXT;
ALTER TABLE model_call_receipts ADD COLUMN resolved_model TEXT;
ALTER TABLE model_call_receipts ADD COLUMN cache_write_tokens INTEGER;
ALTER TABLE model_call_receipts ADD COLUMN usage_json TEXT;
