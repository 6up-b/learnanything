# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
167 (activity-family membership events, proposals, and family memory state).
It pins current-head schema coverage while the original populated fixture
and the other vaults remain at historical versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
