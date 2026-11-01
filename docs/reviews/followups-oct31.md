# Follow-ups Oct 31

Stage `followups-oct31`, branch `fix/followups-oct31` (base `2c3507003`). Four small follow-ups found during
the Oct 31 landings, plus one investigation. Nothing here changes persisted meaning, scoring, scheduling,
projections or serving. No migration, no config key, no RPC change. No paid or live model calls were made
(the investigation ran under `env -i` with empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR` on fresh backup
copies, with background preparation stubbed out). Cost: $0.

## 1. The sketch in-flight tests are deterministic

`SketchFigure.test.tsx` › *never draws a superseded frame when a new sample is drawn while a step is in
flight* failed 1 run in 5 alone on main (reproduced: `expected +0 to be 1` at `waitFor(held.length === 1)`).

**Cause.** `t = 0 / 100` shows from the first render (`step` starts at 0), so the test's readiness wait passed
before the engine existed. The play button stays disabled until the first frame is committed
(`state.kind !== "ready"`), so a click that landed while the wasm host was still compiling (`newHost()` inside
the runner factory) was dropped. Nothing was ever sent, and `waitFor`'s 1 s default ran out. A second latent
source: the held step was held for real time while the watchdog (480 ms, a real `setTimeout`) ran, so a slow
machine could pause the sketch mid-test. The sibling test (*… a slider moves while a step is in flight*) had
both problems too, so both were fixed.

**Fix (test only; `SketchFigure.tsx` unchanged).**
- The engine host is created before the sketch opens and passed to `delayedSteps`. Every runner call then
  settles in microtasks.
- `flushUntil(condition)` settles promises and React work round by round with `act`. Its bound counts rounds,
  never milliseconds, and it throws `never settled: …` instead of timing out.
- After the first frame, fake timers (`setTimeout`/`setInterval` and their clears) are installed. Play sends
  nothing until one explicit timer advance, and that tick sends exactly one held `step(200)`. The watchdog
  timer is fake too, so a held step can never pause the sketch.
- The held step is released, both runs settle, and then 4 × the watchdog limit of fake time passes. Nothing
  more is sent: play stopped with the restart.
- **Stronger than before.** The whole call log is asserted exactly:
  `["init 200", "read 200 0", "step 200", "init 400" | "init 200", "read … 0"]`. The released step's
  superseded run reads nothing, and the new init is queued behind the call in flight (the log is unchanged
  right after the slider or new-sample press).
- **Mutation check.** Removing the run-token check after `active.step` in `advanceRun` makes both tests fail.

**Proof.** 20/20 consecutive passes of the new-sample test alone (separate vitest processes). 20/20 of both
in-flight tests alone. Both also pass inside the whole `--maxWorkers=4` vitest run (gate below).

## 2. The project-layer lockdown check is precise

`tests/test_codex_tool_lockdown.py::test_a_workspaces_own_project_layer_never_reaches_the_turn` rejected any
launch override containing the substring `docs`. The model-catalog override names a file under `TMPDIR`, so
the test failed whenever `TMPDIR` or the worktree path had `docs` in it.

- **Fail-first.** With `TMPDIR=…/scratchpad/fu31/learnanything-docs` the old check fails on
  `permissions.….filesystem={…"…/learnanything-docs/learnloop-codex-catalog-…/bundled-….json"…}`.
- **Fix.** `_carries_project_layer(override, workspace, servers)` flags an override when:
  - its key's dotted parts name one of the layer's servers (quotes stripped);
  - its value names the workspace (as given or resolved), and so also its `.codex/`;
  - or its value carries a server name as a TOML token, i.e. not inside a path or a longer name, as in an
    inline table `mcp_servers={docs={…}}`.
- **New test.** `test_the_project_layer_check_tells_the_layer_from_a_path_that_names_it` pins both directions.
  Six shapes the layer could reach a launch in are caught. Four clean overrides under a `…/learnanything-docs/`
  directory are not (the old substring check fails them).
- The whole file passes under the `-docs` `TMPDIR` (133 passed, 1 skipped) and under `/tmp`.

## 3. A section comparison with no hits is on screen (CA3 off)

With `reader_compare.scope_enabled` off, CA5a's find-section compare (and CA5's also-in-your-books `c`) runs
`compareWith`. That asks the library question with both sections' passages as pins and, once the ask lands,
runs the pins' comparison. The pins do not depend on the ask's hits. `LibraryAnswer` drew that comparison only
inside the `ask.hits.length > 0` block, so when the section's question found nothing the comparison ran (and
was paid for) and nothing showed it.

- **Fix (`LibraryAnswer.tsx`).** The pins' comparison block is built once (`pinsCompare`) and drawn in two
  places:
  - under the hits, as before;
  - on its own after *Nothing in your books matched this yet.*, when the ask has no hits, the intent is a
    comparison and CA3's scoped body is not showing. It is headed *Comparing the two sections you chose:*
    (new `LIBRARY_COPY.sectionsCompared`), then shows the table, or `ModelActionState`'s failure line
    (*Couldn't compare these passages.*) with retry.
- The CA3-on path is unchanged: `compareFoundSection` still calls `compareFrom`, and `CompareScopeBody` is not
  touched.
- **Fail-first (vitest, `findSectionReader.test.tsx`).** *with CA3 off and no hits for the section's question,
  the two sections' comparison is on screen* and *… a comparison that fails says so where it would have
  shown* both fail on the old render and pass now.
- Two existing fixtures (`findSectionReader.test.tsx`, `alsoInBooksReader.test.tsx`) returned a table without
  the fields `CompareTableDto` requires (`header`, `alsoDiscussedIn`, `unverifiedSources`, `droppedPins`,
  `droppedLineCount`). They were never drawn before, and now that the table renders they crashed it, so they
  gained the fields. A real table always carries them.

## 4. The desktop catalog validates again

`desktop_validate.py` stopped at the generator's activation audit: *unclassified desktop source
…/pdfSelection/testing/syntheticBook.ts*. Past that, the catalog had not been regenerated since Sep 23 (111
TypeScript files then, 289 now), and two areas of notes collided by case.

- **Classification (`desktop_generate.py`).** Seven files have no path from `src/main.tsx`. Each now has
  positive evidence, per the script's rule that a missing caller is never proof of dormancy:
  - A new activation kind, `vitest-support` (status `ACTIVE`), covers six files: `pdfSelection/testing/
    syntheticBook.ts` and `syntheticPdf.ts`, `copy/denyList.ts`, `fixtures/readerIntentContract.ts`,
    `fixtures/retryRequests.ts`, and `sketch/engineForTests.ts`.
    - A file gets this kind only when a vitest file imports it, directly or through other test support. The
      check walks the vitest files' imports with the build graph's own resolution.
    - The note shows the chain as a *test-import chain*.
  - `testNodeShims.d.ts` is `compiler-implicit`, like `vite-env.d.ts`. `tsconfig.json` includes `src`, and the
    file types the Node built-ins that the vitest files read.
- **Ten new areas** got their one-line responsibility: pdfSelection, pdfSelection/testing, copy, feedback,
  practice, reader/figures, reader/figures/sketch, today, underhood, workbench.
- **Catalog prose.** The text counts the new kind, and the fixture sentence no longer claims every fixture is
  reachable from the app.
- **Note names (`note_path`).** `exerciseCandidates.ts` sits beside `ExerciseCandidates.tsx`, and
  `sketchScene.ts` beside `SketchScene.tsx`. Each pair produced notes whose names differ only by case.
  Obsidian and `validate_vault.py` resolve links case-insensitively, so one note of each pair was unreachable
  from Home. A module with such a sibling now names its extension: `ExerciseCandidates (tsx).md`,
  `exerciseCandidates (ts).md`.
- **Review-gate counts (`desktop_validate.py`).** 289 TS / 5 Rust; 281 entry-build + 2 compiler-implicit +
  6 vitest-support + 5 native; ACTIVE = 294.
- **Regenerated.** 289 TypeScript/TSX notes, 5 Rust notes, 24 area maps and the catalog (277 files). The
  worktree state of every source was `clean`. `desktop_validate.py` passes, reproducible byte-for-byte.
  `validate_vault.py` passes: 1354 notes, 1352/1352 non-template notes reachable.
- **Guard (`tests/test_desktop_activation_audit.py`, 4 tests).** It runs the audit itself, with no git and no
  rendering, and checks that:
  - every source has evidence of a known kind;
  - every area has a responsibility;
  - test support is never reached from the app entry;
  - note names are unique when case is ignored.

  It fails first on the old generator (3 tests, then the case test against the 4a generator).
- **Why the pytest does not run the whole `desktop_validate.py`.** It is not cheap in the sense that matters:
  each note pins its source's last commit and the tests associated with it. Every frontend commit (and
  some `tests/` edits) makes the catalog stale until it is regenerated, and its review-gate counts change
  with every new file. As a test it would fail every stage that touches the frontend. The audit test covers
  the part that rotted silently (classification and areas). Staleness stays a docs step: regenerate, then
  validate.

## Investigation: who rewrites `facet_capability_evidence` and `facet_recall_state` every session

**Method.** I made fresh backup-API copies (`copy_tree_with_databases`) of each of the three pristine
`owner-copies-mvp035` vaults into `fixtures-local/fu31/` (deleted afterwards). On each copy,
`SidecarContext.load(…, maintenance=False)` ran three times (`prepare_new_revisions` stubbed, so nothing
could queue a model call):
- the first load, which migrates;
- a second load, with nothing in between;
- a third load with `refresh_canonical_projection_on_startup` replaced by a no-op.

After those, `project_canonical_facet_state` ran alone. Every table was snapshotted between steps: row
counts, a full-content hash, a hash without `created_at`/`updated_at`, and per-column hashes.

| vault copy | recall rows | capability rows | 2nd load: values | 2nd load: columns that moved | 3rd load (refresh off) |
|---|---:|---:|---|---|---|
| linear_algebra | 76 | 36 | same | recall: `updated_at`; capability: `created_at`, `updated_at` | no table changed |
| probability | 2 | 1 | same | same as above | no table changed |
| arxiv_v2 | 4 | 2 | same | same as above | no table changed |

After the migrating first load, the two facet tables were the only tables that changed on a plain reload.
`project_canonical_facet_state` alone reproduces the change: 0.10–0.14 s per call on these vaults.

**Path.**
1. `SidecarContext.load` (`src/learnloop_sidecar/context.py`, line ~199) calls
   `refresh_canonical_projection_on_startup` unconditionally. Its comment: self-heal vaults that the old
   mvp-0.7 upgrader activated, and stamp a projection-version change once.
2. That function (`substrate/canonical_projection_rollout.py`) always calls `project_canonical_facet_state`
   under the vault mutation lock, even when the baseline is current. It only skips the marker.
3. `project_canonical_facet_state` folds the whole observation ledger and calls
   `Repository.replace_canonical_facet_state`, which runs `DELETE FROM` on both tables and re-`INSERT`s
   every row:
   - recall rows keep `created_at` (the first observation's time) but get `updated_at = now`;
   - capability rows carry no `created_at`, so both columns become `now`.

   The same call also re-derives the capability-residual state and reconciles unresolved-cause factors. Those
   were byte-identical in the probe.
4. `load` is not only startup. `reload()` calls `load(…, maintenance=False)`, and there are 62 `ctx.reload(`
   call sites in the sidecar (handlers after their writes, plus the watcher refresh paths at `context.py`
   ~562/~655). So the full fold and the whole-table rewrite run after many ordinary writes, not once per
   session.

**Values or timestamps?** Timestamps only. Every value column is identical; only `updated_at` (both tables)
and `created_at` (capability) move. The shadow rebuild excludes those columns by design, which is why it
stays 0/0/0. No reader found uses these timestamps for a decision. `facet_state_reader._fold` carries
min/max into the legacy-shaped `FacetRecallState`, and no learner, scheduling, goals or AD code reads them.

**Assessment.**
- *Wasteful:* an O(ledger) fold plus a whole-table DELETE/INSERT, under the vault mutation lock, after every
  reload. That means WAL churn, and the database changes on every session or reload even when nothing
  happened. With storage sync's hourly and per-session snapshots, every session yields a "changed" database.
- *Risk:* low but real. `created_at` on capability rows is meaningless (it is always the last reload). Any
  future reader of "when did this cell first get evidence" or "when did the estimate last change" would be
  wrong. The rewrite also widens the window for lock contention with a second process (the mobile host or a
  CLI) on each reload.

**Proposed fix (not built: it touches a DERIVED writer used by replay and rebuild equivalence, so it is not
trivially safe; it needs no algorithm successor, because values and meaning are unchanged).**
1. **Write only on change.** In `replace_canonical_facet_state`, read the existing rows keyed by
   (`facet_id`, `capability_key`, `practice_item_id`) and (`facet_id`, `capability`). Compare value columns
   only.
   - If all match and the row sets are equal, skip the write entirely.
   - Otherwise delete the vanished keys, insert the new ones, and update only the changed ones. Changed rows
     get `updated_at = now`; every `created_at` is kept.

   `replace_capability_residual_state` would do the same. This keeps the self-heal, makes a no-op reload
   write nothing, and gives `updated_at` a meaning ("the estimate last changed then"). Tests: a second
   `project_canonical_facet_state` over an unchanged ledger leaves the database file's `data_version` and
   both tables byte-identical; a new attempt changes only its cells' `updated_at`; replay/rebuild
   equivalence and the durability lane stay green.
2. **Skip the fold on reload when nothing it reads changed.** Optional and larger. Stamp a cheap input
   fingerprint after each projection: ledger row count and max rowid/`created_at`, `algorithm_version`,
   `CANONICAL_PROJECTION_VERSION`, and the facet-identity/merge revision. `refresh_canonical_projection_on_startup`
   then projects only when it differs. This needs care about every input the fold reads (measurement
   corrections, quarantine, calibration lineage), so I would do (1) first and measure.
3. **Capability `created_at`.** Optional. Give capability rows the first contributing observation's time, as
   recall rows already have, so a rebuild reproduces them byte-for-byte. It is a timestamp-only change,
   excluded from shadow and equivalence comparisons, but it changes stored column values, so it goes to the
   owner as a choice.

Also seen, not investigated: the first (migrating) load changed `learner_claims` values (10 rows) and
`sessions` on the linear_algebra and probability copies. That is expected from the mvp-0.35 → head migrations
(224–228). The copies are behind main.

## Gate (this step; the full suites run once in the landing gate)

| Command (each inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`) | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `uv run pytest -n 6 tests/test_codex_tool_lockdown.py tests/test_desktop_activation_audit.py tests/test_public_tip_guards.py` | 151 passed, 1 skipped |
| `TMPDIR=…/learnanything-docs uv run pytest -n 6 tests/test_codex_tool_lockdown.py` | 133 passed, 1 skipped |
| `desktop_validate.py` / `validate_vault.py` (`env -i`) | pass / pass |
| `npm install`, `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4` SketchFigure, findSectionReader, alsoInBooksReader | 3 files, 40 passed |
| library/compare vitest files (18 files: every file importing `LibraryAnswer`/`useLibraryAsk`/`LIBRARY_COPY`/`readerLibraryCompare`, plus `alsoInBooks`, `findSection`) | 212 passed |
| new-sample in-flight test alone ×20; both in-flight tests alone ×20 | 20/20; 20/20 |
| `npm run frontend:build` | built |
| whole `npx vitest run --maxWorkers=4` (once, under `flock /tmp/learnloop-fullsuite.lock`; required by item 1) | 237 files, 2197 passed (SketchFigure 19/19) |

Not needed: cargo (no `src-tauri` change), durability lane (no DB/connection code), DB reference scripts
(no schema change).

Test files changed or added: `apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx`,
`apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx`,
`apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx`, `tests/test_codex_tool_lockdown.py`,
`tests/test_desktop_activation_audit.py`.

## Open items

- The desktop catalog goes stale at the next frontend commit: CA6 and RW6b land in parallel. Regenerate with
  `desktop_generate.py` after those landings. The new audit test only fails if one of them adds a file with no
  app-entry path and no vitest importer, or a new directory without an area line.
- The facet-table rewrite fix above (1, optionally 2 and 3) is waiting on the owner's go-ahead.
