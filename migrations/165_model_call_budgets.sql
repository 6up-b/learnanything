-- The token budgets a root operation ran under, as JSON, so usage can be
-- compared with the budgets actually in force rather than today's config.
-- NULL when the caller declared none.
ALTER TABLE model_call_receipts ADD COLUMN budget_json TEXT;
