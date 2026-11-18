# Owner comparison refresh, 2026-11-18 (ledger G3-2)

What `mvp-0.60` changes on the owner's data as it stands today, before the owner upgrades (live: `arxiv_v2` at
`mvp-0.59`, `linear_algebra` and `probability` at `mvp-0.58`). Code: main `f8300a3f00`. No source or test changed.

## How

The orchestrator made a fresh backup-API copy of the three live vaults on 2026-11-18. Working copies of it were made with
`learnloop.db.copies.copy_tree_with_databases` under the worktree's gitignored `fixtures-local/` and were deleted
afterwards. Five states per vault:

- **stored**: the state as stored.
- **control**: one `learnloop rebuild-derived-state` at the vault's own tag. It measures drift, meaning state a
  whole-vault rebuild re-derives differently from what live writes left.
- **intermediate** (the two `mvp-0.58` vaults only): `learnloop upgrade --to mvp-0.59`, which is mvp-0.59's own change.
- **upgrade**: `learnloop upgrade --vault <copy>`, exactly what the owner will run.
- **again**: one more rebuild after the upgrade.

Each state was compared table by table (every DERIVED table, `practice_item_state`, `practice_attempts`, the
authoritative grade ledger) and through the product's readers at one fixed instant: knowledge map, facet detail,
evidence timeline, LO certification, Today headline and LO classes, blueprint readiness, and diagnostic labels.
Every command ran alone in a 4 GB scope with no network. The upgrade and rebuilds made no model call.

The same pipeline was also run on the old comparison set (the Nov 12 copies at `mvp-0.58`, on which the owner accepted
`mvp-0.60`'s value changes). It reproduces the accepted numbers exactly.

## What the upgrade changes, per vault (aggregate counts)

`learnloop upgrade` exits 0 in 2 to 5 s on each vault. Since `linear_algebra` and `probability` are at `mvp-0.58`,
their upgrade applies `mvp-0.59` too.

| | `arxiv_v2` (53 attempts) | `linear_algebra` (70) | `probability` (3) |
|---|---|---|---|
| due dates that move | 3 of 75, each 1 s earlier (drift) | 0 of 99 | 0 of 77 |
| LO mastery means that move | 2 of 37, under 1e-6 logit | 3 of 21, at most 0.039 logit (0.59) | 1 of 18, under 1e-6 |
| knowledge-map numbers that move | 95 of 3,520, largest 0.042 (evidence mass) | 188 of 3,468, largest 0.31 (evidence mass) | 42 of 2,612, largest 0.0046 |
| capability Demonstrated flags | 0 | 1 false to true (0.60) | 0 |
| diagnostic labels | 0 | 3 solid to uncertain (0.59) | 1 unexamined to uncertain (0.59) |
| LO certifications, Today headline | 0 | 0 | 0 |
| blueprint readiness | 2 LOs, at most 0.002 | 5 LOs, at most 0.009 | 1 LO, 0.0004 |
| a second rebuild | nothing moves | nothing moves | nothing moves |

**The three causes:**

- **(a) mvp-0.60's fixes.** The grade channel re-reads, once, the answers whose live grade observation earlier rebuilds
  never superseded (D-55). These are `linear_algebra` 7 answers, `arxiv_v2` 2 and `probability` 1 (no value change).
  Every re-reading is more certain. On all three vaults these changes match what the owner accepted digit for digit:
  the same answers, canonical facet cells, column sizes and Demonstrated flag. On `arxiv_v2` the 50 answers added
  since the old copies add no re-reading. The readers show the same kinds of change on more items, at the same or
  smaller sizes. One knock-on is new. The rebuild under the new tag appends 16 superseding versions of existing
  diagnostic hypotheses, which change only an error-severity number (by at most 0.0003). They leave statement and
  status unchanged and call no model.
- **(b) Drift.** On `linear_algebra` and `probability`, a rebuild at the vault's own tag changes no value a learner
  sees. On `arxiv_v2`, the copy was taken on the day of a session, and a rebuild derives rows that live writes had not
  yet left for that day's answers (AD traces, forecast scores, cold-measurement and router outcome rows). It also moves
  3 due dates by one second and readers' numbers below 1e-4. One older answer loses a follow-up trigger that its live
  write recorded.
- **(c) Anything else.** Nothing beyond (a) and (b) on any vault. The remaining learner-visible changes on
  `linear_algebra` and `probability` all come from `mvp-0.59`, which their upgrade also applies. The owner accepted
  that tag with its aggregate numbers (`refactor-dfb.md` §4: credit total 17.2 to 16.6, 3 LO means up to 0.04 logit).
  Its label moves were not reported there: 3 solid to uncertain on `linear_algebra` and 1 unexamined to uncertain on
  `probability`. Nor was one facet's cumulative credit falling from 1.13 to 0.78 on the evidence timeline, which flips
  no capability flag.

**Judgment.** The acceptance of `mvp-0.60` still covers what it does on today's data. Before upgrading
`linear_algebra` and `probability`, the owner should look at the `mvp-0.59` label moves above, because the
`mvp-0.59` review did not show them.

## Owner lane on the fresh set

The lane ran on a copy of the whole fresh set with `-m owner_vaults -n 2`, through an isolated wrapper that passes
`LEARNLOOP_OWNER_VAULTS` through. Result: **85 passed, 11 failed, 4 skipped**. The old set gives 92 passed and
8 skipped, over the same 100 tests. The lane did not skip silently: the 4 skips are the vaults neither set holds.
The old set's 4 other skips are the `test_why_real_cases` cases that need a backup newer than Nov 8. They now run:
3 pass and 1 fails.

In my judgment, every failure is a test assuming the old set's contents, not a defect:

- 6 failures (`test_router_r2a_serving`, `test_router_r2b_serving`, each on all three vaults). The test helper refuses
  to append a `[router]` table that the owner's configs now contain. The configs were edited after the old set was
  taken.
- 1 failure (`test_ad23_successor`, `arxiv_v2`). The test asserts that a selection table is empty, but the copy already
  holds rows written live.
- 2 failures (`test_placement_fixture_copies`, `arxiv_v2`). They pin the one learning object the old copy stranded,
  and the fresh copy holds one more. The parity check and the latest-tag check in the same file pass.
- 1 failure (`test_plan_follows_path` G47 parity, `arxiv_v2`). The two arms differ only in the router's seeded draw.
  Rerun with both arms on the same pinned seeds, they are identical.
- 1 failure (`test_why_real_cases` case 4). The copy now holds native decision records, which start with a build, so
  no skip precedes it. The test's native branch expects a skip before the first build.

## Recommendation

Use the fresh set for owner comparisons of algorithm changes from now on. It holds far more practice on `arxiv_v2`.
For `mvp-0.60` it confirmed the accepted numbers and showed a knock-on the old set could not show.

For the landing gate's owner lane, keep the old set as the default until the six test files above stop assuming the
old contents. Otherwise the 11 failures would fail every landing. Then switch the default and refresh on a schedule:
before each tag's owner comparison and at least monthly, with each refresh in a dated directory and the previous one
kept for one cycle. The switch needs two kinds of change:

- the gate's copy script (its default source directory);
- the tests: set the router switch inside an existing table, assert only on selection rows the run adds, derive the
  stranded set from the copy, draw the same seeds in both G47 arms, and accept a native case-4 answer with no
  preceding skip.

No test was edited here.

## Not verified

- The live vaults themselves; only the Nov 18 copy was measured. Part of `arxiv_v2`'s drift is the same day's
  derived rows that live writes had not yet left.
- The desktop and phone surfaces. The readers were called directly, and no Today plan was built.
- One placement failure was not traced learning object by learning object.

All working copies are deleted.
