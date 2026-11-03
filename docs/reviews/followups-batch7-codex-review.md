# Follow-ups batch 7: Codex review (job `20261102-184305-WIS3AB`)

Stage record: `docs/reviews/followups-batch7.md`. Branch `fix/followups-batch7`.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Low | Exhausted render budget blocks recovery of an already stored build | fixed | 672884eec8 | `tests/test_followups_batch7_prefetch_capped_resume.py` (8 tests added; all 8 failed before the fix) |

The review's one failed claim ("a row with a request already stored still goes through, so it gets linked") is corrected
in `docs/reviews/followups-batch7.md`.

## F1

**Reproduced, and wider than reported.** The repair sat in `run_builds`, behind every admission guard, and
`close_horizons` runs before `run_builds`. So it did not need an exhausted render budget:

* If the horizon passed before the next pass, that pass closed the row `neither` with no request to read openings from,
  with budget to spare.
* The render cap, today's build cap (a request from an earlier day does not count as started today), battery and a rich
  job in flight each held the repair back, leaving the row exposed to its horizon.

The effect was as reported: a figure the learner opened closed `neither`, the report counted the decision as skipped,
and the opening model lost the observation.

**Fix.** `close_horizons` first calls `link_stored_requests`, so nothing closes an unlinked row. It only writes the
decision's `request_id` and `input_hash` (each set once), with no model call and no budget, so no build guard applies.

**One deviation from the suggested fix.** The finding said to reconcile existing requests by `prefetch_decision_id`.
Linking every such request would have dropped a retry: `_RichSpawn.only` commits a rich-only build's request before it
enqueues the job, and an enqueue failure or a stop in between leaves a request with no figure and no job. Linking that
would close the row with nothing to open. So a request counts only when it names a figure or its rich job exists;
otherwise the row stays in the queue and its build is retried, under the guards, since it really does need a build.

**Found on the way, same defect.** After such a retry `_link` chose the oldest request, which was the empty one, so an
opening of the figure could not be seen either. `_link` now prefers a request that names a figure.

**Not changed.**

* Rows that already closed are immutable and stay as they closed, so no backfill and no migration. A row closed this way
  before the fix stays `neither`.
* A row whose request is a `_rich_pending` record (no figure and no job of its own, another request's job is building)
  is not linked by this repair if its pass died first. It waits for its build, as before.

**Spec.** §10b.5 carries an *as built* note.

## Gate

The full suite, the durability lane and whole vitest were not run (owner rule, 2026-10-17: landing gate only).

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`.
* `uv run lint-imports --no-cache`: 42 kept, 0 broken.
* Targeted pytest in the 5G scope, `-n 6`, 16 files: **257 passed**, 0 failed, 0 skipped.
  * `tests/test_followups_batch7_prefetch_capped_resume.py` (29 of those; 21 before this fix)
  * `tests/test_figures_prefetch.py`, `tests/test_figures_prefetch_review_fixes.py`,
    `tests/test_figures_prefetch_boundary.py`, `tests/test_figure_prefetch_migration.py`
  * `tests/test_figures_show_me.py`, `tests/test_figures_rpc.py`, `tests/test_figure_rich_job.py`
  * `tests/test_followups_batch6_prefetch_decided_once.py`, `tests/test_followups_batch6_prefetch_next_section.py`,
    `tests/test_followups_batch6_prefetch_plan_wait.py`, `tests/test_followups_batch6_review_fixes.py`,
    `tests/test_followups_batch6_verify_fixes.py`
  * `tests/test_judge_routes.py`, `tests/test_notes_never_read.py`, `tests/test_module_catalog_inventory.py`
* `tests/test_architecture.py`, same scope, separate run (the new function-local import): **18 passed**.
* Not run because nothing touched them: frontend, `cargo check`, durability-marked tests, DB reference scripts. No
  migration, no schema change, no config key, no new constant, no DB or connection code.

**No live or paid call was made.** Every model is a fake. Only synthetic vaults were opened. The desktop app was not
launched. The runs outside pytest (`uv sync`, `uv pip install`, `lint-imports`) ran under `env -i` with empty, existing
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, with `UV_CACHE_DIR` pointed at the existing uv cache.
