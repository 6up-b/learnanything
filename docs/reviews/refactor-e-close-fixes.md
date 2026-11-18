# Arc E close fixes

## E-2 · Goal history

A diagnosed attempt after a checkpoint could stop Today's goal details from loading.
The historical replay deleted the attempt's diagnosis in a scratch copy, where SQLite
still enforced the append-only delete trigger.

Goal replay drops the scratch copy's delete guards before pruning. It reads them from
the copy's schema (every trigger that refuses a delete), so a table that gains a guard
later is covered without an edit; eleven of them hang off attempts today. The test
covers direct deletes and a cascade, then checks that the live trigger definitions and
all reachable table row counts match exactly. A second test
(`test_the_scratch_guard_drop_reads_every_delete_guard_from_the_schema`) holds the drop
to the schema.

Before the fix, `tests/test_goal_series.py::test_series_prunes_append_only_rows_only_in_scratch` had two failures.
`[diagnosis]` raised `sqlite3.IntegrityError: attempt_diagnoses are append-only`.
`[all-guards]` raised `sqlite3.IntegrityError: diagnosis_context_receipts are append-only`.
Both cases passed after the fix. The desktop interaction and owner vaults were outside
the verification run.

## E-1 · Attempt availability

An empty receipt sorted before every timestamp in SQL, while the loaded-row cutoff
used the attempt's occurrence time. The attempt insert now stores NULL for an empty
or whitespace-only receipt, so both cutoff readers use occurrence time.

Before the fix, `tests/test_ro1_availability.py::test_blank_received_at_stores_null_and_agrees_at_cutoffs` had two failures.
`[empty]` stored `('', 'recorded')` and `[whitespace]` stored `(' \t\n', 'recorded')`.
Both cases passed after the fix and agreed before, at, and after occurrence. Historical
rows with blank receipts and owner vaults were outside the verification run.

## Checks for both rows

`affected_tests.py --files` selected the whole suite because `conftest.py` imports
`repositories.py`. The filename filter selected 19 files. Those runs had 210
passes and two skips. The full suite was outside the verification run.

Identity pins and structure ratchets passed. The SQLite copy audit flagged two
`shutil.copyfile` calls in the UX walk harness (`scripts/ux_walk/start.py`: the walk
client script and the persona's upload documents, never a database); they are audited
in `tests/test_sqlite_file_copies.py` in this landing. Ruff passed, and
the import linter kept all 43 contracts.

The implementer's sandbox could not write the Git index; the orchestrator committed the
work after review, with the schema-read drop and the copy audit as its own edits.
