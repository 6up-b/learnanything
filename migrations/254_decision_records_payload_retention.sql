-- Arc B close, fix round (docs/specs/refactor_strategy_v3.md §3.7, Decisions/ADR-017): router.payload_retention_days
-- prunes an old decision record's alternatives_json and facts_json and keeps the row.
--
-- Migration 253 refused every update, so the retention §3.7 and ADR-017 promised could not run. This replaces only the
-- no-update trigger: an update is allowed when it changes nothing but those two columns, sets them to the fixed
-- placeholders ('[]' and '{"payload_pruned":true}'), and the row is at least a day old (payload_retention_days is at
-- least 1, and db.stores.provenance.prune_decision_payloads clears only rows older than the configured window).
-- Every identity column (id, trace, parent, kind, status, subject, chosen, decided_by, rule, versions, detail, error,
-- created_at) stays immutable, and the no-delete trigger is unchanged. No row changes here, and nothing replays the
-- table (no successor: a receipt's retention carries no persisted meaning).
DROP TRIGGER decision_records_no_update;

CREATE TRIGGER decision_records_no_update
BEFORE UPDATE ON decision_records
WHEN NOT (
    NEW.id IS OLD.id AND NEW.trace_id IS OLD.trace_id AND NEW.parent_id IS OLD.parent_id AND NEW.kind IS OLD.kind
    AND NEW.status IS OLD.status AND NEW.subject_kind IS OLD.subject_kind AND NEW.subject_id IS OLD.subject_id
    AND NEW.chosen_ref IS OLD.chosen_ref AND NEW.decided_by IS OLD.decided_by AND NEW.rule IS OLD.rule
    AND NEW.versions_json IS OLD.versions_json AND NEW.detail_table IS OLD.detail_table
    AND NEW.detail_id IS OLD.detail_id AND NEW.error_type IS OLD.error_type AND NEW.error_where IS OLD.error_where
    AND NEW.created_at IS OLD.created_at
    AND NEW.alternatives_json = '[]' AND NEW.facts_json = '{"payload_pruned":true}'
    AND OLD.created_at < strftime('%Y-%m-%dT%H:%M:%S', 'now', '-1 day')
)
BEGIN
    SELECT RAISE(ABORT, 'decision_records is append-only');
END;
