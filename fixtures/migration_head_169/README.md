# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
169. Migration 167 adds the learner-field F1 read model
(`facet_outcome_observations`, `question_classifications`); migration 168 adds
PF-a activity-family membership events, proposals and family memory state;
migration 169 adds the learner-field F2 placement receipts
(`assumption_decisions`, `assumption_returns`) and the quick check's queue
state (`placement_quick_checks`). It pins current-head schema coverage while
the original populated fixture and the other vaults remain at historical
versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
