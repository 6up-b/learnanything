# Follow-ups batch 6 (stage `followups-batch6`, branch `fix/followups-batch6`)

Base `d82e7a3666` (main: RW5d P5 figures ahead of need, migration 237; TE1b router lesson suggestions,
mvp-0.43, migration 236; follow-ups Nov 2; P4b; TE1). Worktree `learnanything-dl2`.

> **Updated by the Codex review fixes** (`docs/reviews/followups-batch6-codex-review.md`). This record describes the
> stage before them. Three statements changed: (D) the bound now counts requeues, and item protection is checked
> before a retry and in the worker; (G1) a card with a released line is versioned `+te1b+released`, and the
> successor question is still open; (G2) the R_cold difference is `observed_difference_r_cold`, labelled
> descriptive and not an ITT estimate. The scoped verify's fixes (V1, V2, same file) corrected (D) below in place:
> the stored plan's open items are in the one protection core, on every path, and only a pass that follows the
> learner's own action retries.

Seven queued follow-ups (A to G). Each defect has a reproduce-first test, and each item is its own commit.
**No successor and no migration.** No config key was added. Kill switches are unchanged.

**No live or paid call was made.** Every model is a fake. The two ad-hoc runs outside pytest (the CLI help
snapshot `--write` and `module_validate.py`) ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME`
and `LEARNLOOP_CONFIG_DIR`. No vault was opened outside pytest's synthetic ones: no owner vault,
`~/.config/learnloop`, `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`. The desktop
app was not launched.

| Item | Commit | What |
|---|---|---|
| A | `f9a4a9dd94` | query-student test race (test-only) |
| B | `bd736df165` | the Reader's `(iv) peek` vitest under load (test-only) |
| C | `cb9b441235` | the power probes are cached for a `keep` window, and a sysfs change drops the cache |
| D | `a84b490fdc` | the prefetch pass retries prebuilds' plan waits itself (P5 F17) |
| E | `8111b301cc` | the section trigger's next section follows RW7b's reading path |
| F | `e31610b09b` | recorded: why prebuilt lines and margin marks keep separate counts |
| G1 | `bc9e4580bc` | a pending card's "Not now" gets its own router-card line, not a decline's |
| G2 | `260b796502` | `learnloop router report`: the lesson suggestions' ITT split |

## (A) `test_a_client_that_gives_up_never_stops_the_query_process` race

**Cause.** The test polled for the socket file. `serve_forever` creates that file at `bind()`, one step before
`listen()`, so the client could connect in between and get `ConnectionRefusedError`. The failed test then left
its server thread running, and teardown reported it as leaked. Two sibling tests used the same wait:
`test_the_query_process_answers_over_its_unix_socket_and_exits_idle` and
`test_a_resident_gpu_student_yields_before_an_index_batch`.

**Production is not affected.** `serve_forever` calls its `ready` callback after `listen()`, and the real query
process writes its `ready` status there. The client side waits for that status.

**Fix (tests only).** A `_serving()` context manager in `tests/test_query_student.py` waits on a
`threading.Event` set by `serve_forever(ready=...)`. On exit it sends `shutdown` to a thread that is still
serving and joins it. All three tests now use it.

**Reproduce-first.** `_SlowChmod` slows `student_server.os.chmod` by 0.3 s, which widens the window between
`bind()` and `listen()`. With that delay, the old wait failed every run (`ConnectionRefusedError`, 1 of 1). The
fixed gives-up test keeps the delay and passed 8 of 8 runs alone (3 tests per run). The whole file passed:
43 passed, 8 skipped.

## (B) `sideBySideCorrespondence.test.tsx` "(iv) peek…" under load

**Cause.** The failure was the 1 s `waitFor` at line 142 (`openAlso`'s focus wait), and the failing test took
1019 ms. `openAlso` pressed `x` as soon as the "also in your books" line was drawn. But the Reader only learns
that the line exists through an effect (`onAvailableChange` → `setAlsoAvailable`). On a loaded machine,
React's scheduler uses up its 5 ms slice and yields between the commit and its effects. The press then reached
the Reader's `x` handler first, while `alsoKeyRef` still read "no line", and was dropped.

**Reproduced deterministically.** Skewing `performance.now` by 10 ms per read makes the scheduler yield after
every task. Under that skew, 4 of the file's 11 tests failed at exactly line 142.

**Fix (tests only).** `openAlso` now waits for the key bar's `x` hint ("also in your books"). The key bar draws
from the same state the handler reads (`alsoKeyRef` is assigned in that render). This is awaited state, not a
longer timeout. A new test, "(iv) the same on a loaded machine…", runs the peek flow under the skewed clock. It
fails without the wait (1 failed, 11 passed) and passes with it. `alsoInBooksReader.test.tsx` "x opens the list
at its first line" pressed `x` the same way and gets the same wait.

**No production change.** A person never presses a key within one React task of a line appearing.

## (C) `power_state()` started `powerprofilesctl get` on every call

**The cache.** `figures/power.py` now caches each probe's answer for `PROBE_CACHE_SECONDS` = 30 s. This is a
`keep` (operational) structural bound on process starts, not a model parameter, and it is registered as
`figure_power:PROBE_CACHE_SECONDS`. It applies to:
- `powerprofilesctl get` on Linux;
- `pmset -g batt` on macOS.

**What drops it early.** On Linux, the cache key is the power-supply inventory that call read from sysfs: each
supply's `type`, `scope`, `online` and `status`. Plugging in, unplugging or a battery status change therefore
probes again at once. The sysfs files are still read on every call, so mains and battery are never stale. A
battery's `capacity` is not read, so it never drops the cache. macOS has no cheap change signal, so `pmset` uses
the window only.

**Failure handling (still fail closed).**
- A failed probe (timeout or missing tool) is cached and reads as before.
- A probe that raises is never cached; `power_state()` then reads `unknown`, which counts as not on mains.

**Other details.**
- One lock is held across a probe, so concurrent callers share one process start (at most
  `PROBE_TIMEOUT_SECONDS` of waiting).
- `set_power_reader()` clears the cache.
- Injected readers (`profile=`, `run=`) are never cached.
- The launch sites are unchanged: `_profile` and `mac_power_state` each keep one `subprocess.run`, and the
  lockdown allowlist test passes.

**Worst-case lag.** Switching to power-saver reaches background builds within 30 s, and unplugging a Mac does
too.

**Tests.** `tests/test_followups_batch6_power_probe_cache.py` has 11 tests that count process starts through a
fake `subprocess.run`:
- 30 `power_state()` calls → 1 start;
- a sysfs unplug → a new probe, and the reading turns to battery;
- the window edge, and a clock that runs backwards;
- power-saver is cached;
- a timeout is cached and fails closed;
- a probe that raises is not cached;
- 8 concurrent threads → 1 start;
- no tool → 0 starts;
- `pmset` is cached;
- the reset;
- the registry entry.

Fail-first against the old module: 7 failed. The 4 that passed pin behaviour that is kept: a raising probe is
not cached, injected readers are not cached, the reset, and the registry entry (which was not reverted for that
run).

## (D) P5 F17: hidden plan-wait retries came only from Reader polls

**Cause (landing ruling R2, recorded open).** A hidden rich-only prebuild that met the plan's limit was retried
only by `reader.figures` reads of its source. After a quick re-failure, per-job pacing refused the next retry
for 300 s, the Reader stopped polling, and that retry was lost.

**Fix.** `prefetch.retry_plan_waits(env, result)` runs in a prefetch pass whose trigger carries learner activity
(verify V2, below), before the pass's own builds, so a build from the same pass that meets the limit is not asked
again at once. It applies the background guards:
- It runs only when the pass itself would build: on mains, the plan not paused, and the author route on the
  plan.
- It calls `service.prefetch_plan_waits` (now `extraction_id=None` for every source) on the vault as configured
  now: switch, rich tiers, mains, passage not held out.

It is bounded:
- It keeps only jobs whose decision's horizon is still open (`request_ids`), because a closed decision's
  prebuild is no longer ahead of need.
- It retries at most `[figures.prefetch] max_daily_builds` jobs per pass. This reuses an existing cap; no new
  constant.

The requeue goes through a new `PrefetchEnv.retry_plan_wait` seam. The runtime wires it to
`handlers.figures.retry_plan_wait`, the same paced requeue the Reader's reads use (`rich.due_for_plan_retry`), so
the pass and the Reader share one clock per job. `PassResult.plan_wait_retries` records what was asked.

**Retries follow the learner's actions, not a timer (corrected by verify V2).** This section first said that every
pass comes from learner activity. That was wrong: the gap worker polls on its own, and any nonempty drain fires a
pass. A retry now runs only when the trigger says the learner just acted (`Trigger.learner_activity`, default False):

| Trigger | Fired by | Retries? | Why |
|---|---|---|---|
| `section` | `reader.mark_section_progress` | yes | sent only for the learner's reading: the seen count advancing, a reveal, a completion |
| `offer` (tutor) | the tutor's answer | yes | the answer to the learner's own question |
| `offer` (library) | the read of a finished library job | yes | the learner's own ask, and once per ask (`offers_seen`) |
| `lesson`, `gap` with ref `lesson:<id>` | `lesson.turn` | yes | the learner's own open or turn |
| `plan`, `gap` with ref `plan:<id>` | `get_daily_plan` | **no** | a read: Today's queue-revision poll refetches it when background work lands, and its deciding and waiting timers do too, with nobody at the keyboard |
| `gap` with ref `gaps` | the gap worker's nonempty drain | **no** | a poll tick fires it, even for deferred or failed work; a drain carries no sign that a learner attempt started it |

So **a pass's retry step makes no plan request while the learner is away**, and a retry that became due waits for
their next action above. Two other things can still ask, and this claim does not cover them; both are unchanged:
- **The ordinary work of the same passes.** A `plan` or worker-origin `gap` pass still judges and runs `run_builds`
  (`test_v2_characterization_a_worker_origin_pass_still_runs_ordinary_builds`). See the review record's "For the
  orchestrator".
- **The Reader's own reads of an open source** (`reader.figures`), which keep their paced retries while the Reader
  polls.

**Tests.** `tests/test_followups_batch6_prefetch_plan_wait.py` has 7 tests; all 7 failed against the pre-fix
sources.
- **The F17 path end to end:** the pass prebuilds and hits the limit; one Reader read retries and fails again;
  the next read is paced; the Reader stops. Once the interval has passed, a later pass with no Reader read
  retries the job, and the job completes.
- **Shared pacing in both directions** between passes and Reader reads.
- **Guards:** nothing is retried on battery, while the plan is paused, with the switch off as loaded now, for a
  held-out passage, or for a closed horizon.
- **The cap,** and no retries without the seam.
- **The runtime's wiring,** including its pacing.

## (E) The section trigger's next section ignored RW7b's reading path

**Change.** P5 deviation 7: the spec's table (§10b.2) says "the next section the path or book order gives".
`prefetch.next_section` now reads `reading_paths.plan_path` when `reading_paths.enabled` is on. That read uses
stored judgments only and calls no model.
- **The path is followed** (judged for the learner's current state): the next section is the next one the path
  plans after this one in book order. "Planned" means core or prerequisite, with the learner's "read it anyway"
  and "skip it" applied by `plan_path`. Withheld spans are still skipped.
- **The path is held out for an exam:** it plans nothing.
- **Anything else** (switch off, no depth, not judged, stale, or the path unreadable): book order, as before.

**Tests.** `tests/test_followups_batch6_prefetch_next_section.py` has 6 tests on a three-section book with a
constructed `PlanPath`. The path's own correctness is pinned by `tests/test_plan_follows_path.py`. Fail-first: 3
failed; the 3 that passed pin the book-order fallbacks.

**Not done:** completed sections are not skipped. Book order did not skip them either.

## (F) Prebuilt lines and margin marks: one per-section count — recorded as not a small change

Unpressed prebuilt lines are cut to the cue density budget per section (P5 F11), but that count is not net of
the section's margin marks. Sharing one count is not a small change:

- **The marks come from another read.** They are `reader.guide_plan`'s: built from the Guide's plan and, with
  RW3b's discovery on, merged and remembered for the taps (`reader_cue_discovery.remember`, a write on that
  read).
- **Sharing on the server** would rebuild the Guide's plan and the RW3b merge on every `reader.figures` read.
  The Reader polls that read while a prebuild is coming.
- **Sharing in the Reader** needs two things:
  - a new "unpressed prebuilt" flag on the figure view (the pressed state is not in the view);
  - a re-cut that joins the two reads by section on every refresh of either.

The decision is recorded in `_prebuilt_within_budget`'s docstring (`e31610b09b`). Behaviour is unchanged.

**Worst case today:** a section shows its marks plus up to the same budget again of collapsed "▸" prebuilt
lines.

## (G) TE1b open items

### (G1) The router card's "not now on X" line

**What the code did.** The task describes a `released` showing as a decline; the code did something different.
The router card's lesson-suggestion section read learner responses only. So a pending card's "Not now"
(`released`) was missing from the card, and the card said only "started the suggested lesson on X". (The
acceptance model already counted a release as a decline of its LOs, and that is unchanged.)

**Fix.**
- **Inputs:** the section now also reads `released` rows.
- **Wording:** each release is its own line, newest first, placed after its Start: "let the started lesson on X
  go before it opened (not now)". It is never folded into a decline's "not now on X", because the learner took
  the suggestion first.
- **Expired reservations stay off the card.** An `expired` reservation was set aside by the app when its lesson
  could no longer open, so it is not the learner's answer.

The card version keeps `+te1b`. The section's content is in the stored payload and the card hash.

**Tests.** `tests/test_followups_batch6_te1b_card.py` has 3 tests. Fail-first: 1 failed; the 2 that passed pin
that the decline line is kept and that expired stays off.

### (G2) `learnloop router report`

**The command.** There was no `router report` command; this adds one (`--vault`, `--json`). It is read-only like
`router log`. It reads only the logged ledgers:
- the `lesson_suggestion` decisions;
- the response ledger and its releases;
- the lessons opened from a suggestion;
- the outcomes, derived on the fly the way `router log` derives them.

**What it prints, per randomized arm (card shown / no card):**
- the funnel: offered; accepted (including a chosen alternative); opened (a lesson whose `origin_ref` is the
  decision); completed (closed with `goal_reached`);
- the response mix;
- R_cold on the drawn topic, observed and pending.

**Weighting.** Rates are Hájek estimates weighted by `1 / P(arm | drawn target)`, the logged `arm_propensity`.
Raw counts are printed beside them. A decision without an arm propensity is counted, named and left out of the
weighted figures. The ITT difference in R_cold is printed once both arms have an observation, with no switch
claimed. The pure core is `src/learnloop/router/suggestion_report.py`.

**Snapshot.** `tests/cli_help_snapshot.json` was regenerated: root help, `router` help and the new command.

**Tests.** `tests/test_followups_batch6_router_report.py` has 4 tests. All failed before, because the module did
not exist.
- **Synthetic ledgers:** weights, funnel, releases, a lesson belonging to another decision, unweighted rows.
- **An empty ledger.**
- **The CLI on three logged days:** card + Start + opened + completed; no card; card + "Not now". Checked as JSON
  and as text, with the database's bytes unchanged.
- **Refusal before migration 236.**

The Decider and the router LLM still do not score lesson candidates; TE1b R1 stays deferred.

## Successor decision

None.
- A, B and F change no behaviour.
- C changes only how often a read-only probe runs.
- D changes when an already-decided prebuild's job is asked again, not what is decided.
- E changes which section a prefetch decision targets, logged with its propensity in the raw prefetch ledger.
  That ledger is not scoring, scheduling or projection, and it matches the spec's table.
- G1 adds model-input lines to the router card, under TE1b's tag. The card is versioned by its stored payload and
  hash, and the router's logged propensities hold.
- G2 is a read-only report.

**Ruling wanted on G1:** whether a router-card wording change needs its own card-version suffix.

## Gate

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`. pytest ran at `-n 6`, vitest at
`--maxWorkers=4`, and only one test run at a time. The targeted pytest run was serialized behind
`flock /tmp/learnloop-fullsuite.lock`. Per the owner's rule, the full suite, the whole durability lane and the
whole vitest run were not run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken |
| targeted `uv run pytest -n 6` over the 116 files in `docs/reviews/followups-batch6.targeted-tests.txt` | **2239 passed, 28 skipped, 1 xfailed**, 0 failed (19 min 56 s) |
| `npm install`, `npm run typecheck` | ok, no errors |
| `npx vitest run --maxWorkers=4 src/screens/reader/sideBySideCorrespondence.test.tsx src/screens/reader/alsoInBooksReader.test.tsx` | 2 files, **27 passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| Durability lane, cargo check, DB reference scripts, desktop catalog | not needed: no migration, DB or connection code, schema or `src-tauri` change, and no frontend file added |

**What the 116 files cover:**
- this stage's five new test files and `tests/test_query_student.py`;
- every test file that imports a changed module (git grep): `figures.power`, `figures.prefetch`, `figures.service`,
  `handlers.figures`, `prefetch_runtime`, `router_card`, `router.card`, `cli.router`, `student_server`,
  `parameter_registry`, `reading_paths`, `router_suggestions`;
- the rich-job and router suites;
- the contract tests: architecture, mobile allowlist, desktop RPC contract, serializer snapshot, sidecar contract,
  CLI help snapshot, table roles, tracked fixture databases and coordinated migrations.

**Reproduce-first runs** (each against the pre-fix sources, restored from git for one run and then put back):

| Item | Result before the fix |
|---|---|
| A | the old wait, with the bind-to-listen window widened: 1 of 1 failed |
| B | the new loaded-machine test without the wait: 1 failed, 11 passed |
| C | 7 of 11 failed |
| D | 7 of 7 failed |
| E | 3 of 6 failed |
| G1 | 1 of 3 failed |
| G2 | collection error: the module did not exist |

## For the landing

- **Merge main first.** Follow-ups batch 5 lands first. `git merge-tree HEAD fix/followups-batch5` is clean, and
  no file overlaps.
- **Regenerate the module references after that merge.** The new module is `router/suggestion_report.py`. On
  base `d82e7a3666` the module catalog is already stale (`module_validate.py`: 1376 issues), and batch 5
  regenerates it. Regenerating it here would only conflict with that.
- **No DB, schema, config or desktop-catalog change.** No frontend source file was added; only two test files
  changed.

## Open items

- (F) The shared per-section count is not done; see (F) for the two designs.
- (D) A source whose prebuild hit the limit, with no learner action afterwards, waits for the next one (a Reader
  read of that source, a press, section progress, a question, a lesson's turn). Opening Today does not retry it.
- (E) Completed sections are not skipped (book order did not skip them either).
- (C) Power-saver and Mac unplugging reach background builds within 30 s.

## Landing onto main

Prepared on `fix/followups-batch6` (worktree `learnanything-dl2`) from the stage tip `e3bfedcb86` (re-verify job
`20261102-160534-hqxd06` CLEAN, reporting one pre-existing P5 defect, step 0 below); the orchestrator
fast-forwards main and pushes. No migration, no successor and no config key.

### Step 0: a candidate is decided once for its trigger — `d12f346b5b`

**The defect (P5's, not this batch's).** A closed horizon removes a decision's open-key protection, and plan
candidate generation kept returning the plan's reading after the plan ended. So every `get_daily_plan` read after
that decided each unbuilt candidate again: a new decision row and a fresh Thompson draw per read (the re-verify
estimated 120 x candidates rows per hour at one read per 30 s). Repeated draws until one builds also make the
logged propensity understate the real chance of a build.

**Same defect on the section trigger, found while reproducing.** Once the next section is marked read, its decision
closes, and each further progress report on the earlier section decided it again. The brief named only the plan,
but its rule (a pass with unchanged inputs adds 0 rows and 0 draws) covers this, so the fix includes it.

**Fix (`figures/prefetch.py`; no new constant, no migration).** The brief offered either of two guards. Both went
in, because each covers a case the other leaves open:
- An ended plan offers no candidates. `candidates()` checks `_plan_ended`, which uses `_plan_end`, the instant
  `horizon_at` closes decisions on (now one function, so the two can't disagree). There is no judge call, row or
  build for it, including a plan that ended before anything was decided (on battery all day, say). A plan with no
  stored row does not count as ended here; only a test fake's plan reaches that case, since a real record was just
  read from its row.
- `filter_candidates` drops a request already decided for this same trigger, its horizon closed or not
  (`decided_requests`: kind, ref and request key). This is the section trigger's guard, and it also means a reopened
  plan (a raised budget, RW7b's path reading) keeps its decision and does not draw again. The `gap` trigger already
  worked this way (`_decided_refs`).

**Consequences to review.**
- A `void` row does not count as decided: it says the passage was withheld, and once released it is new input (one
  more decision, with its own row and propensity). The withheld filter keeps it out until then.
- A reopened plan's deferred decision that closed when the plan ended is not retried. That plan's next read decides
  nothing for it, and the next day's plan decides for itself (a later plan is a new trigger, pinned by a test).
- A `section` ref is stable, so a section's candidate is decided once ever (a void row aside), until the section's
  text changes the request.
- R6 is unchanged: `next_section` still does not skip a completed section. A section already read that was never
  decided gets its one decision, as before.

**Reproduce-first.** `tests/test_followups_batch6_prefetch_decided_once.py` has 10 tests using the real pass and
real model with a fake judge and author, on real `daily_plans` and `reader_section_progress` rows; they check rows,
decision calls and the generator's state across repeated passes, before and after the end. Against `e3bfedcb86`'s
`prefetch.py`: 8 failed, 2 passed (those two pin behaviour that is kept: a built decision and a void one). With the
fix: 10 passed. The neighbouring prefetch files (`test_figures_prefetch*`, the batch 6 prefetch tests, the P4b
visuals) passed with the fix unchanged.

Also in that commit: the module docstring, an as-built line under spec §10b.2's filters, and the new test file in
`docs/reviews/followups-batch6.targeted-tests.txt`.

### Merge: main `a5b2b23e17` (follow-ups batch 5) — `856ce60f74`

No conflicts. `src/learnloop_sidecar/handlers/lesson.py` auto-merged, `teacher/*` needed nothing, and `pyproject.toml`
holds both sides' import-linter ignores. References regenerated last (`8cc40194b6`):
- `db_generate_reference` wrote 372 table notes; `db_validate_reference` errors `[]`.
- `desktop_generate` wrote 308 TS/TSX and 6 Rust notes; `desktop_validate` passed.
- `module_generate` wrote 1148 module notes and 63 package maps. The one new note is `router/suggestion_report`.
  `module_validate` PASS (1212/1212 YAML, 39627 wikilinks, 37638 file links).
- `validate_vault` passed (2096 notes).

The Configuration and Database notes changed only in their source commit stamps. No config default changed, so no
fingerprint recompute. Main was re-read just before the gate and at the end of the smoke: still `a5b2b23e17`, so no
second merge.

### Gate (tip `8cc40194b6`, main `a5b2b23e17`)

| Check | Result |
|---|---|
| `lint-imports --no-cache` | 42 kept, 0 broken |
| Targeted pytest (145 listed files, 4 `test_followups_batch5_*`) | 2796 passed, 29 skipped, 1 xfailed |
| Targeted vitest (Reader figures folder, sideBySideCorrespondence, alsoInBooksReader) | 19 files, 442 passed |
| Full suite (`-n 8 --dist worksteal`, 10G scope, `flock`, `env -i`) | **24128 passed, 0 failed**, 90 skipped, 47 xfailed (42:33) |
| Durability lane | 188 passed, 1 skipped |
| Owner lane (fresh backup-API copies, `fixtures-local/landing-batch6/owner-lane`) | 83 passed, 4 skipped, and the 2 known failures only (`test_activity_backfill.py::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies.py::...[arxiv_v2]`) |
| Frontend | `npm install` (lockfile unchanged), typecheck clean, whole vitest 260 files / **2475 passed** (`--maxWorkers=4`, 5G scope), `frontend:build` built |

No unexpected failure, so nothing needed a rerun. `test_query_student` passed in the full run, and neither known
vitest flake recurred. `src-tauri` does not differ from main, so cargo check was not run.

### Smoke (fresh owner copies, `fixtures-local/landing-batch6-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Adapted from batch 5's.
- Fresh backup-API copies of the three mvp035 owner copies, each neutralized under its own side's code: every AI
  route at the `127.0.0.1:9` blackhole with the key variable unset.
- `env -i` with an empty `HOME`, `CODEX_HOME` and config directory.
- An audit hook logging every process start and socket connect, refusing non-loopback sockets and Codex starts. Its
  self-test refused `1.1.1.1:443` and `codex --version`.
- Code: `git archive` of main `a5b2b23e17` and the branch `8cc40194b6`, each with `src/` and `migrations/`.
- On each side: a bare `upgrade` mvp-0.35 -> **mvp-0.43**, the primary desktop load, `migrate_vault` (head 237,
  0 applied) and `rebuild-derived-state` (mvp-0.43).

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, branch vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump, branch vs main | byte-identical (84721 B) | byte-identical (124046 B) | byte-identical (32458 B) |
| Router decisions in the plan dump, card hash included (no released line) | 1, identical | 4, identical | 1, identical |
| `router card --json` on the copy's own decisions, main vs branch | none on this copy | 2 of 2 byte-identical | none on this copy |
| `router report --json` | exit 0, database and WAL hash unchanged | same | same |
| `rebuild --shadow` (branch) | facet/mastery/schedule 0/0/0, live unchanged | same | same |

**Repeated prefetch passes.** Four passes per phase, identical on all three copies. These copies' plans hold no
reading block and the routes are blackholed, so `scripts/prefetch_repeat.py` uses three smoke seams, on these copies
only: the real plan's reading overlaid on a real section, a stubbed judge answer, and a seeded measured wait so the
real model draws. Rows per pass:

| Phase | main | branch |
|---|---|---|
| plan open | 1, 0, 0, 0 | 1, 0, 0, 0 |
| plan ended | **1, 1, 1, 1** (4 more draws) | 0, 0, 0, 0 (0 draws) |
| section, next unread | 1, 0, 0, 0 | 1, 0, 0, 0 |
| section, next read | **1, 1, 1, 1** (4 more draws) | 0, 0, 0, 0 (0 draws) |
| offer | 2, 0, 0, 0 | 2, 0, 0, 0 |

Every verdict was `deferred_plan` (the blackholed author route), so nothing was built: 0 figures, 0 requests.

**Power probe.** Process starts for 30 `power_state()` calls, then 30 more after the window: main 30 and 30, branch
1 and 1. Across the whole smoke, `powerprofilesctl get` started 72 times on main's code and 5 on the branch's.

**Audit.**
- 0 new `model_call_receipts` across 12 compared databases.
- No socket connect beyond the self-test's refused one, and no Codex start beyond the self-test's refused one.
- The only other process starts were `powerprofilesctl get` and the self-test's `true`.
- The Codex processes on the machine all started before the smoke (the latest Nov 2 15:15).
- After each close, the only thread left is `learnloop-reading-sweep`, on both sides.

### Rulings (orchestrator, verbatim)

- R1 (F4): "Option (a): G1's card line is accepted in place under mvp-0.43, as an in-place amendment before any vault reached the tag (the owner's vaults are at mvp-0.35; TE1b landed Nov 2). Precedent: TE0's confidence section, RW6b part 2 R1, follow-ups Nov 1c (E). The +te1b+released card suffix stays. The re-verify found no persisted blocker."
- R2 (item F): "Not built, with the reason recorded in the code. Prebuilt lines and margin marks keep separate per-section counts. Queued for the UX journey audit: build a shared count only if the Reader looks crowded."
- R3 (V2): "A pass retries plan waits only when its trigger carries learner_activity=True. get_daily_plan passes do not retry, because the sidecar can't tell a press from a poll; opening Today not retrying a hidden prebuild is accepted."
- R4: "Ordinary run_builds from worker-origin passes stay allowed: plan route only, foreground first, max_daily_builds, max_daily_render_minutes, mains. The owner kept prefetch on deliberately, and has been told about this."
- R5: "reader.figures keeps its paced retries while a source is open and polling. Closing this needs a poll-or-open signal on the RPC; not worth building now."
- R6 (E): "The next section follows the reading path when reading_paths.enabled is on, and does not skip completed sections, as book order did not."
- R7: "Finished prebuilt figures stay listed after an item is planned or a cold check begins. Accepted on the re-verify's evidence: during a cold attempt the source pane and its inline figures are covered together, and a merely planned item's passage is visible in the Reader anyway."
- R8: "learnloop/content/ has no __init__.py, so the import graph omits that package and the contracts say nothing about cycles through it. Queued for the end-of-queue Opus architecture review."
- R9 (step 0): "Fixed at landing: see the review record."

### Open items (landing)

* `learnloop/content/` has no `__init__.py`, so the import graph omits that package and the contracts say nothing
  about cycles through it: for the end-of-queue Opus architecture review (R8).
* The shared per-section cue count: for the UX journey audit, built only if the Reader looks crowded (R2).
* A poll-or-open signal on `reader.figures`: not planned (R5).
