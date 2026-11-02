# Follow-ups batch 6: Codex review fixes

Stage `followups-batch6`, branch `fix/followups-batch6`, worktree `learnanything-dl2`. Review: Codex
(gpt-6.1-sol), job `20261102-144908-iG3wYr`, on `07e3e85f54`. Four findings, all Medium. The stage record
is `docs/reviews/followups-batch6.md`.

**No live or paid call was made.** Every model is a fake. The one ad-hoc run outside pytest (the CLI help
snapshot `--write`) ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`,
and `LEARNLOOP_FIGURE_PREFETCH=off`. No vault was opened outside pytest's synthetic ones. **No migration, no
schema change, no config key, no successor.**

## Review

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Automatic retries bypass protection for active cold checks | **fixed** | `f76f6fb45d` | `tests/test_followups_batch6_review_fixes.py::test_f1_*` (7 tests; 6 failed before the fix, and the unrelated-check test passed before and after) |
| F2 | Medium | Paced jobs consume retry slots and starve eligible jobs | **fixed** | `f76f6fb45d` | `test_f2_*` (3 tests; all 3 failed before the fix) |
| F3 | Medium | The reported ITT difference conditions on outcome availability | **fixed** (relabelled) | `4fca4f97f3` | `test_f3_*` (2 tests, both failed before the fix); `tests/test_followups_batch6_router_report.py` updated |
| F4 | Medium | G1 changes serving inputs under the existing algorithm tag | **rejected** (successor), ruling wanted; card-version mitigation | `b6799c0b96` | Reason below. `test_f4_*` (1 test, failed before the change) |

### F1: a cold check that starts after the plan wait (fixed)

**Reproduced.** A prebuild's rich job meets the plan's limit. After that, one of the vault's items comes under an
open cold check, and its worked answer is a paragraph of the job's saved context (`input_span_ids`). Before the
fix, three paths ignored the check:
- `retry_plan_waits` requeued the job;
- the Reader's `reader.figures` read requeued it;
- the worker, once requeued, sent the request and stored the figure.

`run_builds` refuses that state for a new build, but none of the retry paths asked the same question.

**Fix.** There is now one core, `service.item_passages(vault, repository, clock=None)` (V1 below replaced its first
form, which took `extra_item_ids`). It returns the passages (`corpus.item_exclusions`) of items under a live
administration (`WITHHELD_COLD`, `WITHHELD_RESERVED`, `WITHHELD_PROBE`) and of the stored plan's open items. It
returns None when protection can't be read, and callers fail closed.
- `prefetch.item_protection` now reads that core. What it covers is unchanged.
- `service.prefetch_plan_waits`, which serves both the Reader's reads and the pass, drops a job whose saved
  context (`rich_base_keys`: its passage, the paragraphs it was sent, its region, retrieved keys and home)
  touches a protected passage. If protection can't be read, it returns nothing.
- `retry_plan_waits` applies the same rule as `run_builds`, through that core.
- **The worker** (`rich.run_rich_job`, prebuilds only) checks `_item_protected` at the start and in its
  hold. The hold runs before every request and before the store. A stop is `exam_material`.

**Corrected by V1.** This section first recorded that the worker checks live administrations only, because reading
the day plan from `figures.rich` would need a new frozen-cycle ignore, and that the plan's items are checked at both
points where a prebuild can start. Both statements were wrong. The Reader's retry was a third starting point that
did not check them, and no ignore was needed. The worker now checks the stored plan too.

**Tests (fakes).** The cold reservation starts **after** the initial plan failure. Each line below is one test:
- the pass's function asks nothing, and a real pass sends nothing;
- the Reader's read asks nothing;
- a direct requeue is stopped by the worker before any request, and nothing is listed;
- a check that starts while the author writes: the request was already sent, but nothing is stored;
- unreadable protection: no requeue, and the worker sends nothing;
- the stored plan's open items are protected in the pass;
- a cold check on an unrelated passage still lets the retry through.

### F2: paced jobs never take a due job's slot (fixed)

**Reproduced.** With `max_daily_builds = 1`, the newer of two waiting jobs was inside its retry interval. The
old code sliced `waiting[:bound]`, so it tried only the paced newer job and never reached the due older one.

**Fix.** The bound now counts successful requeues. The scan orders jobs by `rich.plan_retry_order`: the last
retry in this process, with never-asked jobs first, and the ledger's newest-first order for ties. It goes on
until `max_daily_builds` requeues succeed. A paced job declines without a request and is passed over. No new
constant.

**Tests.**
- A paced job first in line leaves the slot to the due one, and nothing more is asked once the bound is reached.
- The scan goes past three paced jobs to requeue two due ones.
- A job that keeps meeting the limit yields its slot to a never-asked job on the next pass.

### F3: the R_cold comparison is labelled observed-only (fixed by relabelling)

**Agreed.** Accepted lessons can delay the drawn LO's eligible cold retrieval, so which decisions have an outcome
can depend on the arm. Propensity weighting does not correct that.

**Fix.**
- `itt_difference_r_cold` is now `observed_difference_r_cold`.
- Each arm reports `observed_share`, and the text reads "observed k of n".
- The last line reads: "Difference in mean R_cold among observed outcomes only (card - no card): … Descriptive,
  not an intention-to-treat estimate: an accepted lesson can delay its topic's cold check, so which outcomes are
  in yet can differ by arm."
- The funnel rates stay labelled intention to treat: they are taken over every decision of the arm.
- No causal estimate under censoring is attempted. That would be new analysis, not a follow-up.
- The `router report` help text changed, and `tests/cli_help_snapshot.json` was regenerated (`router`,
  `router report`).

**Tests.**
- Differential availability: the card arm has 1 of 3 observed and the no-card arm 2 of 2. The test checks the
  shares, the observed-only difference of +0.50, and that the text never says "ITT difference".
- The CLI runs on logged decisions with observed cold outcomes for both arms. `derive_router_outcomes` is faked to
  final values, which the earlier CLI test never had. The test checks the JSON key, `+1.00`, and the label.

### F4: G1's card line under the existing tag (rejected; ruling wanted)

**The facts are right.** At mvp-0.43, a pending card's "Not now" adds a line to the router card the plan's models
read, and switching suggestions off removes the whole section rather than restoring the pre-batch6 card.

**Why no successor in this step.** Minting one (mvp-0.44) would mean:
- a new tag and its chain entry;
- a defaults snapshot;
- an upgrade step;
- switch-off parity.

That is a successor stage, not a follow-up fix, and it is out of this step's scope. It also goes against what was
decided before:
- **Earlier rulings.** Router-card inputs have been ruled serving-time, not persisted meaning: TE0's confidence
  section, and RW6b part 2's ruling R1, "router input changes without a successor, and router decisions are
  serving-time and not persisted meaning", flagged to the owner. Follow-ups Nov 1c (E) also changed the card
  without a tag.
- **The playbook's in-place exception path.** An amendment before any vault has reached the tag has precedent
  (mvp-0.11), but it needs an owner decision. No vault reached mvp-0.43 before this branch: the owner's vaults
  are at mvp-0.35, and TE1b landed today.

**Mitigation (`b6799c0b96`).** While the section carries a `released` line, the card's version now takes a
further suffix, `+te1b+released` (`SUGGESTION_RELEASE_CARD_SUFFIX`). A stored card and its decision therefore
name the new input. A card without such a line is still TE1b's: same bytes, same version.
`test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own` checks both.

**Ruling wanted (orchestrator or owner), one of:**
- (a) accept G1 in place under mvp-0.43, as with TE0 and RW6b P2 R1, recorded as an in-place amendment before
  any vault reached the tag;
- (b) revert G1's card line at the landing, so that the router card at mvp-0.43 is TE1b's byte for byte, and
  carry it to the next successor;
- (c) gate it behind the next successor's tag when one is minted.

### Not findings

- **Spec conformance "F: shared cue density, still missing".** This was recorded open in the stage record (item F:
  two designs, neither small). It is not a finding of this review, and it is unchanged.
- **"No schema, table-role, replayer, grading, evidence-writing or embedding changes"** still holds after these
  fixes.

## Gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6` at most, one run at a time. The targeted run was serialized behind
`flock /tmp/learnloop-fullsuite.lock`. Per the owner's rule, the full suite, the whole durability lane and the
whole vitest run were not run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken |
| reproduce-first: `pytest tests/test_followups_batch6_review_fixes.py` with `figures/service.py`, `prefetch.py`, `rich.py` and `router/suggestion_report.py` at `07e3e85f54` | 11 failed, 1 passed (the unrelated-check test, which pins behaviour that is kept) |
| reproduce-first F4: `-k f4` with `router/card.py` at the prior commit | 1 failed (import of the new suffix) |
| targeted `uv run pytest -n 6` over the 125 files in `docs/reviews/followups-batch6.targeted-tests.txt` | **2494 passed, 29 skipped, 1 xfailed**, 0 failed (26 min 44 s), at `b6799c0b96` |
| Durability lane, npm/vitest, cargo check, DB reference scripts, desktop catalog | not needed: no migration, DB or connection code, schema, frontend or `src-tauri` change |

**What the 125 files cover:**
- the stage's earlier 116 files;
- this step's `tests/test_followups_batch6_review_fixes.py`;
- every other test file that imports a changed module (git grep for `figures.service`, `figures.prefetch`,
  `figures.rich`, `router.card`, `router_card`, `suggestion_report`, `cli.router`, `prefetch_plan_waits`,
  `retry_plan_wait`): `test_ad23_contract.py`, `test_judge_routes.py`, `test_router_card_reading_gaps.py`,
  `test_teacher_te1_successor.py`, `test_teacher_te1b_migration.py`, `test_teacher_te1b_rereview_fixes.py`,
  `test_teacher_te1b_suggestions.py`;
- the contract tests: architecture, mobile allowlist, desktop RPC contract, serializer snapshot, CLI help
  snapshot, table roles, tracked fixture databases, coordinated migrations, the registry audit, the prefetch
  boundary and the Codex tool lockdown.

## For the landing

- **Unchanged from the stage record:** merge main first (batch 5), then regenerate the module references.
- **`figures/service.py` gains exported names:** `item_passages`, `rich_base_keys`, `rich_base_item_protected`,
  `ITEM_PASSAGE_PROTECTED` and `LIVE_ADMINISTRATION_REASONS`.
- **`figures/rich.py` gains `plan_retry_order`;** `router/card.py` gains `SUGGESTION_RELEASE_CARD_SUFFIX`.
- **F4 needs its ruling** before the landing: (a), (b) or (c) above.

## Verify fixes

The scoped Codex verify (job `20261102-154041-zRi7s1`, on `07101cd63f`) reported two Mediums, both ruled real. **No
live or paid call was made**, every model is a fake, and only pytest's synthetic vaults were opened. **No migration,
no successor, no config key and no new constant.** `main` was not merged.

| Id | Severity | Title | Commit | Tests |
|---|---|---|---|---|
| V1 | Medium | Stored-plan protection is missing on the Reader's retry path and in the worker | `4f0f20451d` | `tests/test_followups_batch6_verify_fixes.py::test_v1_*` (11) |
| V2 | Medium | Plan-wait retries can spend while the learner is away | `cb5b877397` | `test_v2_*` (8) |

### V1: one core, and it always reads the stored plan

**Reproduced on `07101cd63f`.** A prebuild meets the plan's limit, and then the day plan selects a question whose
worked answer is in the job's saved context. Real plan rows, with `item_exclusions` faked:
- `prefetch_plan_waits` still named the job, and the Reader's read sent a request (2 author calls, expected 1);
- the worker, once the job was requeued, built and stored the figure (`completed`, expected `exam_material`).

**A second defect found on the way.** An unreadable plan read as *no plan*: `prefetch._plan_record` catches every
exception and returns None. So `item_protection` reported protection as available, which is failing open.

**Fix.**
- `service.item_passages(vault, repository, *, clock=None)` reads the stored plan itself, through the new
  `service.stored_plan_open_items`. `extra_item_ids` and `prefetch.held_plan_item_ids` are gone, so no caller can
  leave the plan out.
- Everything reads that core: `prefetch_plan_waits` (Reader and pass), `prefetch.item_protection`, and the worker's
  start and hold checks (before every request and before the store).
- A plan that can't be read now makes the core return None, and every caller fails closed.
- Who is covered is unchanged. Only prebuilds reach the worker's check, and a learner's own press keeps its
  behaviour (`test_v1_a_learners_own_press_keeps_its_behaviour`).

**How the import stays clean.** `figures.service` imports `daily_plan.records` inside the function and reads the rows
through `db.stores.daily_plans`. `records` is a pure module that imports only `daily_plan.types`. `assemble` is the
plan's own fold, so there is one meaning of "open" and no second fold to drift. The engine is not imported, and no
frozen-cycle ignore was added (42 contracts kept). The earlier record's claim that this needed an ignore was wrong.

**A limit of the linter.** `learnloop/content/` has no `__init__.py`, so the import graph omits that whole package,
including `content.pipeline.jobs -> figures.rich`. The contracts say nothing about cycles through it. This edge is
safe at import time because it is function-local and `records` reaches nothing above it. If `daily_plan` ever reaches
`figures` through a package the linter can see, the contract will flag this edge.

### V2: only the learner's own action retries

**Reproduced on `07101cd63f`.** Deferred gap drains through the sidecar's real wiring, and `_schedule_prefetch` for
Today's read, each produced a pass that requeued the waiting job with no learner action.

**Fix.** `Trigger.learner_activity` defaults to False, and `run_trigger` calls `retry_plan_waits` only when it is
True. A hook that doesn't say never counts. No time window was added.

| Trigger | Fired by | Classified | Why |
|---|---|---|---|
| `section` | `reader.mark_section_progress` | learner | sent only for the learner's reading: the seen count advancing, a reveal, a completion |
| `offer` (tutor) | the tutor's answer | learner | the answer to their own question |
| `offer` (library) | the read of a finished library job | learner | their own ask, once per ask (`offers_seen`) |
| `lesson`, `gap` with ref `lesson:<id>` | `lesson.turn` | learner | their own open or turn |
| `plan`, `gap` with ref `plan:<id>` | `get_daily_plan` | **not learner** | a read that timers can fire: `TodayScreen`'s 3 s queue-revision poll invalidates the plan query when background work lands, and the deciding and waiting timers refetch it |
| `gap` with ref `gaps` | the gap worker's nonempty drain | **worker** | a poll tick fires it, deferred and failed work included. A drain following a real attempt is not counted either: the drain carries no link to one, and today no retry depends on it |

Classifying Today's read as not learner activity goes beyond the finding's two sites. The sidecar can't tell a press
from a poll on that RPC without a frontend and RPC change, so this errs towards not spending. The cost is that opening
Today no longer retries a hidden prebuild.

### For the orchestrator (reported, not changed)

**Can P5's ordinary `run_builds` spend from worker-origin passes? Yes.**
- `run_trigger` still builds on any trigger when on mains with the plan available. A decision deferred for power is
  built by a poll tick's pass, which sends a request to the rich author (a fake in the test:
  `test_v2_characterization_a_worker_origin_pass_still_runs_ordinary_builds`).
- From reading the code, not run: the same pass can also call the gap judge (`candidates(..., call=call)`).
- The bounds: plan route only (never metered), foreground work first, `max_daily_builds`, `max_daily_render_minutes`,
  and mains power.
- A deferred gap job fires a full pass on every worker poll tick (`IDLE_POLL_SECONDS` = 30 s) for as long as it stays
  deferred.
- Passes from `get_daily_plan` behave the same way.

**"No plan request while the learner is away" is true of a pass's retry step only.** The stage record now says so.
Besides the ordinary builds above, the **Reader's own reads** still retry: `reader.figures` keeps its paced retries,
hidden prebuilds included, while a source is open and polling. From reading `useFigures.ts`, not run: with a pressed
build waiting for the plan, the Reader polls without end, so a Reader left open keeps asking once per job per interval.
Closing this needs a poll-or-open signal on the RPC.

**A finished prebuild is not re-checked when listed.** V1 covers a job up to its store. A figure stored *before* the
plan selected the item, or before a cold check started, stays listed: `list_figures` filters held-out material, not
`item_passages`. This is existing P5 behaviour.

### Gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6` at
most, one run at a time. The targeted run was behind `flock /tmp/learnloop-fullsuite.lock`. The full suite was not run.

| Command | Result |
|---|---|
| reproduce-first: `pytest tests/test_followups_batch6_verify_fixes.py` on `07101cd63f`'s sources | 14 failed, 5 passed |
| `lint-imports --no-cache` at `cb5b877397` | 42 kept, 0 broken |
| targeted `pytest -n 6` over 63 paths at `cb5b877397` | **1415 passed, 1 skipped**, 0 failed (4 min 18 s) |

- **The 5 that passed first** pin kept behaviour: the three answered-item cases, the press and the ordinary-builds
  characterization.
- **8 of the 14 failed on the behaviour itself:** the Reader's read, the shared rule, the worker's two checks, the
  unreadable plan, the deferred drains, Today's read and the unstated trigger.
- **6 of the 14 failed on a missing name, so they show only that the code was absent:** the fold comparison (written
  against a store helper later dropped for the plan's own fold; it now calls `stored_plan_open_items`),
  `test_v1_only_todays_plan_holds_an_item` (no `clock` argument, after its first assertion passed) and the four
  hook provenance tests (no `learner_activity` field).
- **The 63 paths:** 59 test files and 4 helpers that collect nothing. The test files are every one naming
  `figures.rich`, `figures.prefetch`, `figures.service`, `handlers.figures`, `handlers.lesson`, `post_attempt_worker`
  or `prefetch_runtime`, plus the prefetch boundary, architecture, table roles, registry audit and Codex tool lockdown
  tests, and this stage's test files. They are merged into `docs/reviews/followups-batch6.targeted-tests.txt`, whose
  other files (the stage's earlier list) were not rerun here.

**Changed tests.** `_pass` and three triggers in `test_followups_batch6_prefetch_plan_wait.py` now state
`learner_activity=True`. `test_f1_the_pass_also_protects_the_stored_plans_open_items` now uses real plan rows.

**For the landing.** `figures/service.py` gains `stored_plan_open_items`. `prefetch.held_plan_item_ids` and the
`extra_item_ids` arguments are gone, and `prefetch_plan_waits` and `rich_base_item_protected` take `clock`.
