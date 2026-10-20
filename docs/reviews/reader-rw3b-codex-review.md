# Reader RW3b: Codex review and fixes (stage `reader-rw3b`)

Branch `reader/rw3b` (worktree `learnanything-merge4`). Reviewed range
`c9ad9cce1..9b279f163` (Codex job `20261020-141408-1QresM`). Stage record:
`docs/reviews/reader-workbench-RW3b.md`.

## Fix round 1

Every finding was reproduced before it was fixed. Each one has a test that
fails on the reviewed tip `9b279f163` and passes on the fix. To get the
fail-before counts, the new and changed tests were run against `9b279f163`'s
`src/` and `migrations/` (`git archive`, `pytest -o pythonpath=<base>/src`)
and against its six frontend files (copied back in for one vitest run, then
restored):
- **pytest:** 21 of the 23 new or changed cases fail on the base. The two that
  pass are a regression pin (a candidate a misconception already states is
  not a second target) and the holdout-impressions test, whose assertion was
  only relaxed (a density cut carries no propensity). The one-reservation
  test was added after this run and was not run on the base.
- **vitest:** 8 of the 9 new cases fail on the base. The one that passes is a
  pin (a search answered for the targets it asked about is not asked again).

Nothing was rejected. No model was called and no vault copy was opened. Every
judge, embedding and gap job in the tests is a fake.

| id | sev | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Background discovery continues after its kill switch is disabled | fixed | `758fec824` | `test_reader_rw3b_review_fixes.py::test_discovery_stops_before_its_next_request_once_switched_off_and_reloaded`, `::test_a_reload_cancels_the_running_job_and_a_new_ask_starts_one_on_the_new_vault` |
| F2 | High | Paid retrieval bypasses the cue daily spend cap | fixed | `758fec824` | `::test_nothing_is_retrieved_deeply_for_a_judge_that_cannot_run`, `::test_retrievals_metered_requests_reserve_under_the_cue_envelope`, `::test_a_metered_judge_request_reserves_once_under_the_cue_envelope` |
| F3 | Medium | Failed requests and retries evade the per-open call cap | fixed | `758fec824` | `::test_failed_requests_count_against_the_per_open_cap`, `::test_a_retry_is_a_second_request_and_reported_apart_from_judgments` |
| F4 | Medium | Holdouts include cues that were never eligible to appear | fixed | `758fec824` | `::test_with_density_off_nothing_is_held_out`, `::test_a_cue_the_budget_cuts_is_never_a_control_and_a_held_out_cue_keeps_its_slot`, `::test_a_held_out_cue_the_reader_would_have_spaced_out_is_recorded_as_spacing`; vitest `rw3bReview.test.tsx` "F4: …" |
| F5 | Medium | PDF reading records only the treatment arm | fixed | `758fec824` | vitest `rw3bReview.test.tsx` "F5: both arms are measured by their passage…", "F5: on the original PDF no discovered cue is recorded…" |
| F6 | Medium | Switching books sends queued impressions to the wrong extraction | fixed | `758fec824` | vitest `rw3bReview.test.tsx` "F6: opening another book sends…", "F6: a batch the sidecar did not take is sent again once" |
| F7 | Medium | A target arriving during discovery is incorrectly marked handled | fixed | `758fec824` | vitest `rw3bReview.test.tsx` "F7: a search that answered for older targets is asked again…" (plus the not-asked-again pin) |
| F8 | Medium | Newly named gaps do not trigger an in-session plan refresh | fixed | `758fec824` | vitest `ReaderScreen.discoveredCuesReview.test.tsx` "F8: …" (the real `readGuidePlan`, nothing mocked but the sidecar); pytest `::test_the_plan_says_when_background_work_can_still_name_a_target` |
| F9 | Medium | Required target classes are absent | fixed | `758fec824` | `::test_holding_pen_candidates_and_recurrence_groups_are_targets`, `::test_a_candidate_a_durable_misconception_already_states_is_not_a_second_target`, `::test_a_claim_needing_an_independent_check_is_a_try_first_target` |
| F10 | Medium | "Already shown this visit" is replaced with document-order placement | fixed | `758fec824` | `test_reader_cue_value.py::test_a_target_seen_this_visit_ranks_after_targets_not_yet_seen_and_placement_alone_never_demotes` (replaces the test that pinned the old reading), `::test_a_targets_second_passage_in_a_section_waits_behind_targets_not_yet_given_a_slot` |
| F11 | Medium | Repeated visits manufacture independent outcome samples | fixed | `758fec824` | `::test_repeated_visits_never_manufacture_samples`, `::test_the_report_counts_one_unit_per_link_and_matches_the_targets_facets`; `test_reader_cues_cli_report.py` (new output shape) |
| F12 | Medium | "Open · what you worked on" never shows discovered cues' earlier work | fixed | `758fec824` | `::test_open_shows_the_cited_answer_and_the_learners_own_words`, `::test_a_misconceptions_cited_answer_is_its_newest_source_events_attempt`; vitest `ReaderScreen.discoveredCuesReview.test.tsx` "F12: …" |
| F13 | Low | Discovery dry-run provides no cost estimate | fixed | `758fec824` | `::test_the_dry_run_names_settled_targets_and_carries_a_spend_plan`; `test_reader_cues_cli_report.py` (dry run writes nothing) |
| C1 | (claim) | Taps rebuild the guide plan before resolving the cue | fixed | `758fec824` | `::test_a_tap_on_a_drawn_mark_does_not_rebuild_the_plan` (the protection check still runs on a kept cue: `test_reader_rw3b_protection.py` stays green) |

References regenerated on the fix tree: `64c10b33c`.

### What changed, per finding

- **F1.** A discovery job keeps the vault generation it started on
  (`ctx.loaded_vault`, AD1's provider). Its `cancelled()` check returns true
  on any of these: a cancel, `shutdown_requested`, a different published
  generation (any reload or vault switch), or discovery switched off in the
  vault loaded now. `discover` asks it before each target, after the
  shortlist, and before every request (`SpendBudget(cancelled=…)` raises
  `SpendCancelled`, and the listwise judge reports `cancelled`). Protection is
  read again for each target. When a job from an older generation is still
  running, a new ask marks it cancelled and starts a fresh job instead of
  joining it.
- **F2.** `_judge_readiness` resolves the judge's route and client, and checks
  its skip reasons, before any retrieval. A judge that cannot run gets no
  shortlist, so no query embedding is bought. A metered judge with nothing
  left of today's allowance is refused before retrieval. The whole loop runs
  under `spend_envelopes(cue envelope)`, so every metered request reserves
  in `cues.max_daily_cost_usd`, the query embedding inside `search_spans`
  included. If that reservation is refused, retrieval falls back to the
  keyword lists (`search_spans` never raises for a paid step). The judge
  reuses the envelope object the discovery already activated, so each
  request makes one reservation, never two (pinned). Subscription requests
  are still never refused for money.
- **F3.** `discovery_budget`: one `SpendBudget` per source open. Its
  `max_calls` and `max_retries` are `cues.max_calls_per_source_open`, and its
  dollar cap is the daily cap. All targets share it. `calls` is now
  `budget.used.calls`: every admitted request, a failed one and a retry
  included. `judged` (targets judged) and `usage` (requests, retries,
  billing, cost basis) are reported separately. Subscription calls still
  count against the call cap (it is not a money cap) and are priced
  `estimated_only`.
- **F4.** `merged_cues` now orders each section, applies the density budget,
  and only then draws the holdout among the cues the budget admitted. A
  held-out cue keeps its slot and its global rank. The cut cues are never
  promoted into the empty slot and carry no propensity. The Reader places
  held-out cues alongside the marks (`placeCueMarks(…, heldOut)`). A held-out
  cue takes part in the spacing and restored-line rules as if it were drawn,
  but is never drawn. One that a rule set aside is sent with that reason, and
  the server records `spacing` or `restored_line` instead of `holdout`,
  outside both arms. Skim mode and working mode record nothing, as for marks.
- **F5.** The Reader measures discovered cues by their passage, with one
  criterion for both arms: half the passage in view, or half the reading
  area for a passage taller than it (`passageInView`). The criterion applies
  equally to drawn marks, held-out cues the Reader would have drawn, and
  cues set aside. MarginMark's own "in view" no longer counts for a
  discovered mark. On the original PDF, which draws no element per passage,
  neither arm is recorded. RW3a's Guide marks keep their own rule.
- **F6.** Each queued receipt carries the extraction and visit it was seen in.
  A flush groups receipts by that pair, so the batch sent on leaving a book
  names that book and its visit. A batch the sidecar rejects is sent once
  more. If that also fails, the receipt is dropped and can be observed again.
- **F7.** The hook keeps the targets it asked about separate from the targets
  the job answered for. A job answering for other targets (the sidecar
  joined a search already running), or a cancelled one, is asked again for
  the current targets, at most `DISCOVERY_MAX_REASKS` (3) times per
  (source, targets).
- **F8.** The plan's `discovery.targets_pending` is true while a learner-text
  gap job is queued or leased (`text_gaps.jobs.pending_jobs`, with the
  pipeline on). Meanwhile the Reader re-reads the plan with growing pauses
  (4 s to 60 s). When the gap lands, the next plan has a new `targetsKey`,
  which asks for discovery in the same session.
- **F9.** `cue_targets` now reads every source the spec names:
  - **Open episode hypotheses.** A legacy hypothesis (one with no
    `misconception_id`) is rendered by the statement of the error event it
    was entered from.
  - **Holding-pen candidates** (`misconception_candidates_for_learning_object`:
    the table's candidates and the open causal hypotheses projected into
    it). A class seen more than once is a `recurrence_group` keyed by its
    recurrence key. One seen once is a `hypothesis`. Both are open by their
    lifecycle (`p_open` 1.0, `candidate_lifecycle`).
  - **Claims needing an independent check** (RW6a's
    `session_summary(...)["claims_needing_independent_check"]` for the
    current and previous reader sessions). Each becomes an `unchecked_claim`
    target that only "try this step first" can link to. The judge's prompt
    marks it `try_first_only`, and any other pick is dropped in code.
  - Each statement becomes one target only (deduplicated against
    misconceptions and hypotheses).
  - Migration 215 admits `unchecked_claim`. The head fixture was rebuilt with
    the backup API (rollback mode, integrity ok, no companions). The prompt
    version is now `passage_cue_judge.v2`.
- **F10.** "Already shown this visit" is now read from the learner's shown
  impressions in the current reader session on this source (`seen_targets`).
  A session here means impressions less than `SESSION_GAP` (30 min) apart,
  the newest less than that before the plan's build. Each impression maps to
  its target through its link, or through the Guide cue it still is. It is
  read when the plan is built, a layout boundary, so nothing moves while the
  learner scrolls. Within a section the order is greedy: each target gets
  one slot before any target gets a second. Placing a mark in an earlier
  section no longer demotes its target.
- **F11.** The report's unit is the randomized link. The holdout draws once
  per link, so all of a link's impressions in one arm form one unit, exposed
  at its first in-window impression. The outcome is the next attempt after
  that exposure on the target's facets. Those facets are stored on the link
  (`passage_links.target_facets_json`); when a target names none, its
  learning object stands in. The outcome's attempt id is kept. Links whose
  outcome is the same attempt form one cluster: the IPS mean runs over
  links, the variance over clusters. An arm needs 2 distinct outcome
  attempts before it gets an estimate. The report also shows links,
  distinct outcomes, units still pending, and outcomes shared across arms.
- **F12.** Targets carry their provenance:
  - **Misconception:** its newest source error event's attempt.
  - **Episode hypothesis:** the event it was entered from.
  - **Candidate or group:** its newest member's attempt.
  - **Gap:** its attempt, plus the learner's own words for a tutor question,
    a workbench step, a formative answer or hint feedback.
  - **Claim:** its newest assisted attempt.

  "Open" on a discovered cue shows the date answered and the question as it
  was answered, through RW3a's shared `earlier_work` helper and its
  answered-question contract. The answer and the gap's own words appear in
  the learner's voice. The passage's quote and the target's statement appear
  in the model's voice, apart. Demonstrated-facet targets have no single
  cited attempt and keep the statement only.
- **F13.** The dry run reads settled targets without writing and names them
  `current`, so they are skipped. It gives pending targets past the cap the
  status `would_cap`. Its `spend_plan` carries:
  - the resolved route, its billing and its cost basis (`estimated_only` on
    the subscription);
  - the judge calls and estimated tokens and dollars
    (`PaidCalls.plan` over each pending target's keyword-shortlist prompt);
  - the query embeddings a run may buy;
  - the caps, with today's spend and what remains.
- **C1.** `reader.cue_tap` resolves a drawn mark through the plan's cues kept
  for the reading, after checking the protection again. It builds the plan
  only for a cue not among them, such as a "not relevant" being undone.

### Deviations recorded

- The stage record's deviations 3 ("already shown" read within the plan),
  4 (recurrence groups reserved), 5 ("unchecked claim" read as any open
  target) and 6 (on the PDF only drawn marks logged) are superseded by
  F10, F9, F9 and F5 above.
- `reader_cue_impressions` is unchanged. `passage_links` gains
  `target_facets_json` and the `unchecked_claim` kind. Migration 215 is
  still unlanded, so it was amended in place rather than given a new
  migration.
- "Check me" still asks `find_practice` with the cue's learning object (the
  review's conformance table: target facets and rivals). That is a spec
  conformance note, not a numbered finding, so it is left for the owner
  (open question below).

### Open questions

- **Q5.** Should "Check me" on a discovered cue narrow `find_practice` to the
  target's facets (now on the link) and, for a hypothesis with rivals open,
  use `intent="discriminate"`? Default: unchanged (RW3a's LO-wide request).
- **Q6.** An `unchecked_claim` target reads RW6a's claims for the current
  and previous reader sessions. Should older sessions' claims count too?
  Default: those two sessions only.

### Gate (fix step; targeted per the owner rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`. The landing gate's
full suite was running (`/tmp/learnloop-fullsuite.lock` held by another
stage). Targeted pytest needs no lock, and nothing here took it. There was
no full suite, whole durability lane or whole vitest run.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `uv run pytest -n auto` over the 117 files in `fixtures-local/rw3b-scripts/affected-fix1.txt`: the stage's 105-file affected list, `tests/test_reader_rw3b_review_fixes.py`, and every test file naming `reader_report`, `reader_cues`, `passage_cues`, `reader_cue_links`, `reader_cue_discovery`, `cli_help_snapshot`, `migration_head_215`, `recap` or `reader_sessions` (the list includes `test_architecture`, `test_cli_help_snapshot`, `test_coordinated_migrations`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_salience_firewall`, `test_table_roles`, `test_tracked_fixture_databases`, `test_sidecar_reader`, the defaults snapshots and `test_registry_audit`) | **2,247 passed** (template `.pyc` cleared first) |
| after the one-envelope change: the 9 RW3b files, `test_reader_rw3b_review_fixes.py`, `test_cli_help_snapshot.py`, `test_salience_firewall.py`, `test_sidecar_reader.py` | **154 passed** |
| `pytest -m durability` on `test_reader_rw3b_migration`, `test_ad1_migration`, `test_library_asks_migration`, `test_approach_maps_schema`, `test_help_assists_schema`, `test_migrations`, `test_coordinated_migrations`, `test_tracked_fixture_databases` | **7 passed** |
| `pytest --durable-sqlite` on the 8 RW3b behaviour files and `test_reader_rw3b_review_fixes.py` | **75 passed** |
| `npm install`; `npm run typecheck` | clean |
| `npx vitest run src/screens/ReaderScreen src/screens/reader/ src/components/PdfReaderPane.marks.test.tsx src/app/readerCheck.test.ts` (59 files, the 2 new ones and the RW3a switch-off snapshots among them) | **425 passed** |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| head fixture `migration_head_215` | rebuilt from the base's 213 head with the backup API: applied [215], checkpoint (0, 0, 0), `journal_mode=DELETE`, header 1/1, integrity ok, `foreign_key_check` empty, no companions |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | head 215, 335 table notes; errors []; passed (1,132 notes, all reachable) |
| CLI help snapshot | rewritten (`learnloop reader cues discover --dry-run` help) |

**Model calls in this step: none.** No vault copy was made or opened. The
tracked working vaults and credential files were not touched.

## Re-review (fix round 2)

Codex re-reviewed `9b279f163..reader/rw3b` (job
`20261020-151049-JcL075`, verdict REOPENED). It confirmed F1 and F2 fixed and
raised two new Medium findings. Both reproduced: each new test failed on
`d4fa3a1a9`, checked by putting the base's file back temporarily, and passes
on the fix.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | discovery outlives its kill switch | confirmed fixed (round 1) | `758fec824` | (re-review: CONFIRMED-FIXED) |
| F2 | High | paid retrieval before judge readiness; envelope | confirmed fixed (round 1) | `758fec824` | (re-review: CONFIRMED-FIXED) |
| F14 | Medium | tall passages can be read without recording an impression | fixed | `d38a6c95f` | `rw3bReview.test.tsx` "F14: a passage taller than the reading area is recorded once it fills half of it" (failed on base: 0 requests) and "F14: a sliver of a tall passage is not in view" |
| F15 | Medium | cached taps bypass the try-first kill switch | fixed | `d38a6c95f` | `test_reader_rw3b_review_fixes.py::test_a_cached_try_first_tap_is_refused_once_try_first_is_switched_off_and_reloaded` and `::test_the_kept_cues_are_dropped_on_a_reload_and_kept_within_one` (both failed on base) |

### What changed

- **F14** (`apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts`).
  `passageThresholds(passageHeight, areaHeight)` adds the ratio
  `0.5 * area / passage` to the observer thresholds when a passage is taller
  than the reading area (the viewport, the observer's root). That is the
  point where the passage fills half the area. Passages are grouped by their
  threshold set, one observer per set. Short passages keep RW3a's
  thresholds, so they share one observer as before. A `resize` updates the
  area height, which rebuilds the observers. `passageInView` allows one pixel
  of rounding between the ratio and the visible height. The criterion itself
  is unchanged: half the passage, or half the area for a tall one. The test's
  fake observer calls back only when a threshold is crossed, as a browser's
  does.
- **F15** (`src/learnloop_sidecar/handlers/reader_cue_discovery.py`,
  `reader.py`). `remember(..., vault=)` keeps the cues together with the
  `LoadedVault` they were computed on. `_cues_now` reuses them only for that
  same vault object. A reload or a vault switch publishes a new one, so the
  cues are rebuilt under the switches loaded now. Within one load a tap
  still resolves without rebuilding the plan (the existing test
  `test_a_tap_on_a_drawn_mark_does_not_rebuild_the_plan` still passes).
  `reader.cue_tap` also refuses a try-first cue while
  `PC.try_first_enabled(vault)` is false. In that case nothing is recorded:
  no impression and no `learner_card` verdict. Impressions read through the
  same bound cache.

No migration, config key, RPC shape, CLI help or snapshot changed.

### Gate (fix round 2; targeted per the owner rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`. There was no full
suite, whole durability lane or whole vitest run.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `uv run pytest -n auto` on 25 files: `test_architecture`, `test_mobile_allowlist`, `test_desktop_rpc_contract`, `test_sqlite_file_copies`, `test_passage_links`, `test_reader_cue_holdout`, `test_reader_cue_value`, `test_reader_cues`, `test_reader_cues_cli_report`, `test_reader_guidance`, `test_reader_quick_check`, `test_reader_reconnect`, `test_reader_rw3a_landing`, `test_reader_rw3b_migration`, `test_reader_rw3b_protection`, `test_reader_rw3b_review_fixes`, `test_reader_rw3b_switch_off`, `test_reader_try_first`, `test_reader_wrap_up`, `test_reading_hardening_landing`, `test_required_method_round3`, `test_reread_safety`, `test_reread_safety_landing`, `test_salience_firewall`, `test_sidecar_reader` (every test file naming `reader_cue_discovery`, `cue_tap`, `cue_impressions` or `guide_plan`) | **584 passed** |
| durability | not run: no migration and no DB or connection code changed |
| `npm install`; `npm run typecheck` | clean |
| `npx vitest run` on the 38 test files naming `useCueImpressions`, `useReaderCues` or `ReaderScreen` (`rw3bReview.test.tsx`, every `ReaderScreen.*.test.tsx`, `reader/cues.test.ts`, `reader/readerHooks.parity.test.tsx`, the RW3a switch-off snapshots among them) | **302 passed** |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB references | not run: the schema did not change |

**Model calls in this step: none.** No vault copy was made or opened. The
tracked working vaults and credential files were not touched.

## Fix round 3 (orchestrator)

Codex's scoped verify of `d4fa3a1a9..reader/rw3b` (job
`20261020-152052-iUbGOj`, verdict REOPENED) confirmed F1, F2 and F15 fixed
and reopened F14 for a case the round 2 fix missed. The reproduction was
confirmed: the new regression sends no request on `5cf7f2383` and one after
the fix.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | discovery outlives its kill switch | confirmed fixed (verify) | `758fec824` | (verify: CONFIRMED-FIXED) |
| F2 | High | paid retrieval before judge readiness; envelope | confirmed fixed (verify) | `758fec824` | (verify: CONFIRMED-FIXED) |
| F14 | Medium | width-only reflow leaves tall passages without impressions | fixed | this round's commit | `rw3bReview.test.tsx` "F14 verify: a passage reflowed from 2,000 to 6,000 px at the same window height is still recorded" (failed on base: 0 requests), "F14 verify control: a 4,000 px passage that keeps its size is recorded once, its observer kept", "F14 verify: repeated reflows never log a passage twice in one visit" |
| F15 | Medium | cached taps bypass the try-first kill switch | confirmed fixed (verify) | `d38a6c95f` | (verify: CONFIRMED-FIXED) |

### What changed

- **F14** (`apps/learnloop-tauri/src/screens/reader/useCueImpressions.ts`).
  Round 2 rebuilt the observers only when the window's height changed, but
  a passage's thresholds also depend on its own height. When the window
  narrows, a passage can reflow from 2,000 to 6,000 px while the window's
  height stays the same. Its added threshold (0.15) is then above the
  largest ratio it can reach (0.10), so it was never recorded. The hook no
  longer keeps the area height in React state. Inside the observer effect,
  a `ResizeObserver` watches every measured passage and the reading
  container (`bodyRef`), and the window's `resize` event is still heard.
  Every size notification restarts a settle timer
  (`CUE_REFLOW_SETTLE_MS`, 150 ms). When the timer fires, the hook works out
  each uncounted passage's thresholds again from its height and
  `window.innerHeight`. If any passage's threshold set changed, all the
  observers are rebuilt. If nothing changed, they are kept. A passage
  already in view is added to a per-run `counted` set: a rebuild never
  observes it again, and a late callback for it is ignored. The receipt key
  in `sentRef` (source, visit, cue) still allows one receipt per cue per
  visit, so a rebuild cannot log twice. Where `ResizeObserver` is missing,
  the window's resize event still triggers the check. The criterion is
  unchanged: half the passage, or half the area for a tall one.

No migration, config key, RPC shape, CLI help or snapshot changed. Python
was not touched.

### Fail-before

`5cf7f2383`'s `apps/learnloop-tauri` was extracted with `git archive` to the
scratchpad. The worktree's `node_modules` was symlinked in and the new
`rw3bReview.test.tsx` copied over. The base's `useCueImpressions.ts` was
used unchanged. Result: **2 failed, 10 passed** out of 12.

- The width-only reflow regression failed: `readerCueImpressions` was called
  0 times, and 1 was expected.
- The repeated-reflow check failed because the base never rebuilds its
  observers on a reflow.
- The fixed-size control passed with one request, as it does after the fix.

On the fix all 12 pass.

### Gate (fix round 3; targeted per the owner rule of 2026-10-17)

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **425 passed** (58 files) |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| pytest, lint-imports, durability, cargo, DB references | not run: no Python, schema or `src-tauri` change |

**Model calls in this step: none.** No vault was opened or copied.

## Fix round 4 (orchestrator)

Codex's whole-stage verify of `c9ad9cce1..60f5fe9db` (job
`20261020-152744-TxWCs1`, verdict REOPENED) confirmed:

- the 213→215 and 213→214→215 upgrades;
- the head fixture and the append-only enforcement;
- the switch-off pins;
- protection, display-only and the dry run;
- F1, F2 and F15.

It found one High and four Mediums. Each one reproduced, and each is fixed
here under the orchestrator's binding rulings, with tests that fail on
`60f5fe9db`.

| id | severity | title | verdict | test or reason |
|---|---|---|---|---|
| F14 | Medium | rounded thresholds still miss tall-passage impressions | fixed | `rw3bReview.test.tsx` "F14 round 4: a 24,100 px passage is recorded at the exact half-area crossing" and "... the half-area threshold is the exact ratio, kept within (0, 1]" |
| F16 | High | in-session discovery resets the per-open call allowance | fixed | `test_reader_rw3b_fix_round4.py::test_a_target_change_mid_open_never_refills_the_opens_call_budget`, `::test_failures_and_retries_of_one_open_share_its_budget_across_jobs`, `::test_a_source_open_id_names_one_source`; `rw3bReview.test.tsx` "F16: every discovery ask of one source open names the same open" |
| F17 | Medium | delayed impressions classified against the wrong plan | fixed | `::test_an_impression_queued_before_a_density_change_is_recorded_against_its_own_plan`, `::test_an_unknown_plan_id_is_refused_and_nothing_is_stored`, `::test_an_expired_or_dropped_plan_is_refused_and_nothing_is_stored`; `rw3bReview.test.tsx` "F17: each queued impression carries the plan it was seen on" |
| F18 | Medium | stored propensity differs from the draw probability | fixed | `::test_the_draw_and_its_propensity_use_one_unrounded_rate`, `::test_a_logged_impression_stores_the_exact_propensity` |
| F19 | Medium | holdout intervals omit cross-arm covariance | fixed (interval withheld, per ruling) | `::test_shared_outcome_attempts_withhold_the_interval_and_say_why`, `::test_without_shared_outcomes_the_interval_is_kept` |

### What changed

- **F14** (`useCueImpressions.ts`). `passageThresholds` adds the exact
  ratio `0.5 * area / passage` as a threshold, kept within (0, 1]. It is no
  longer rounded to four places. Rounded, a 24,100 px passage's threshold
  became 0.0124: the observer fired at 298.9 px, short of the 300 px
  criterion even with the pixel of slack, and nothing after that called back.
- **F16** (`useCueDiscovery.ts`, `reader_cue_discovery.py`,
  `passage_cues.discover`).
  - The Reader mints a `copen_…` id when a source is opened. A new source,
    or the Reader mounted again, is a new open.
  - Every `reader.cue_discovery` request sends this id as
    `source_open_id`, which is now required.
  - `CueDiscoveryJobs` keeps one `_OpenBudget` per id: one
    `discovery_budget`, built when the open's first request arrives, and a
    lock. Every job, re-ask, failure and retry of that open draws on it. The
    open's jobs run one at a time, and before every request the budget asks
    the cancel check of the job now running.
  - `discover(..., budget=)` uses the shared budget when it is given one.
    Its `calls` and `usage` count that run's own requests, and the new
    `open_calls` counts the open's so far. The CLI's single run keeps a
    budget of its own.
  - An open id sent with a different source is refused.
  - Opens are kept up to `MAX_KEPT_OPENS` (4,096), the oldest dropped first.
- **F17** (`reader_cue_discovery.py`, `reader.py`,
  `useCueImpressions.ts`, `dto.ts`, `client.ts`).
  - `remember` gives each served cue plan a `discovery.plan_id`
    (`cplan_…`). It keeps a deep copy of the plan's cue index and density
    under that id, together with the database path and the source.
  - Each queued receipt in the Reader carries the plan id it was seen on.
    Batches are grouped by (source, visit, plan).
  - `reader.cue_impressions` now requires `plan_id`. It resolves arm,
    density, suppression, seed and propensity from the kept plan only, never
    from the current one.
  - A plan id is refused with `cue_plan_unknown`, and nothing is stored,
    when any of these holds:
    - it was never served;
    - it was dropped (`MAX_KEPT_PLANS` = 256);
    - it expired (`PLAN_TTL_SECS` = 12 h);
    - it belongs to another vault's database or another source.
  - Taps are unchanged: they still resolve through the vault-bound cache
    (F15).
- **F18** (`passage_cues.py`). `holdout_rate` is the one normalization
  (clamped to [0, 0.99]). `holdout_draw` uses that value unchanged for the
  draw and returns `rate` or `1 - rate` unrounded as the propensity, so
  `0.123456789` stores `0.876543211`.
- **F19** (`reader_report.py`). When any outcome attempt counts in both
  arms, `interval_95` is `None` and `effect_label` is "point estimate
  only". `interval_withheld` then says plainly: "N outcome attempts counted
  in both arms: LearnLoop can't separate the arms yet, so no interval is
  given and the effect is a point estimate only." With no shared attempt the
  interval is kept as before, labelled "point estimate with a 95% interval".
  No covariance estimator was built.

Existing tests were updated for the two required parameters
(`source_open_id`, `plan_id`) and for the fixtures' `planId`. No
migration, config key or CLI help changed. Two RPC shapes changed:
`reader.cue_discovery` now requires `source_open_id`, and
`reader.cue_impressions` requires `plan_id`. Both pass through
`src-tauri` unchanged.

### Fail-before

- **Backend.** `git archive 60f5fe9db` (without `fixtures`, `apps`,
  `docs` and `tests`) was extracted to the scratchpad. The worktree's new
  test file was then run with `-o pythonpath=<scratch>/src`, and
  `learnloop.__file__` was checked to resolve to the scratch copy. Result:
  **10 of 10 failed**.
  - F18: `assert 0.876543 == 0.876543211`.
  - F19: `[-0.98, 0.98] is None`, and the `interval_withheld` key was
    missing.
  - F16 and F17: refused for the new parameters (`extra_forbidden`), or
    `KeyError: 'plan_id'`.
- **Base behaviour (F16, F17).** A temporary probe, run the same way
  without the new parameters and deleted afterwards, reproduced the
  verify's scenarios.
  - F16: **14 judge calls in one source open** with a cap of 12.
  - F17: the shown impression was stored as `shown=False`,
    `suppressed_reason='density'`, `density='off'`, with no propensity.
- **Frontend.** `60f5fe9db`'s `apps/learnloop-tauri` was extracted to
  the scratchpad, with the worktree's `node_modules` symlinked in and the
  new `rw3bReview.test.tsx` copied over. Result: **6 failed, 10 passed**
  of 16.
  - The four new tests failed: F14 sent `[]`, and the threshold was
    `0.0124` rather than `0.012448…`; F17 sent one batch, not two; F16's
    `sourceOpenId` was undefined.
  - The two F6 tests failed because their expected calls now carry
    `planId`.

### Gate (fix round 4; targeted per the owner rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `uv run pytest -n auto` on 32 files: `test_architecture`, `test_desktop_rpc_contract`, `test_judge_routes`, `test_library_ask`, `test_mobile_allowlist`, `test_passage_links`, `test_reader_cue_holdout`, `test_reader_cues_cli_report`, `test_reader_cues`, `test_reader_cue_value`, `test_reader_guidance`, `test_reader_intent`, `test_reader_quick_check`, `test_reader_reconnect`, `test_reader_report`, `test_reader_rw1b_review`, `test_reader_rw3a_landing`, `test_reader_rw3b_fix_round4`, `test_reader_rw3b_migration`, `test_reader_rw3b_protection`, `test_reader_rw3b_review_fixes`, `test_reader_rw3b_switch_off`, `test_reader_try_first`, `test_reader_tutor_offers`, `test_reader_wrap_up`, `test_reading_hardening_landing`, `test_required_method_round3`, `test_reread_safety_landing`, `test_reread_safety`, `test_salience_firewall`, `test_sidecar_reader`, `test_sqlite_file_copies` (the RW3b files, every test file naming `reader_report`, `cue_impressions`, `reader_cue_discovery`, `holdout_draw`, `merged_cues`, `PC.discover` or `guide_plan`, and the named contract files) | **691 passed** |
| durability | not run: no migration, DB or connection code changed |
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **429 passed** (58 files) |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| references | not regenerated: the schema, the config and the module set are unchanged. `module_validate.py` is clean. `desktop_validate.py` stops on an untouched file (`components/pdfSelection/testing/syntheticBook.ts`, unclassified activation), not on this round's files. |

**Model calls in this step: none.** No vault was opened or copied.

## Fix round 5 (orchestrator)

Codex's verify of round 4 (job `20261020-154905-XXS9CH`, verdict REOPENED)
confirmed:

- F14, F18 and F19;
- the immutable plans and their refusals;
- the callers of the changed RPCs;
- protection, switch-off, the head fixture and the migrations.

It reopened F16 (High) and F17 (Medium) and raised F20 (Medium). Each one
reproduced on `1455cbf29` and is fixed here under the orchestrator's
binding rulings.

| id | severity | title | verdict | test or reason |
|---|---|---|---|---|
| F16 | High | changing only the open id refills the allowance | fixed: a durable per-source daily cap on top of the per-open budget | `test_reader_rw3b_fix_round5.py::test_new_open_ids_a_reload_and_a_restart_never_exceed_the_sources_daily_calls`, `::test_failed_requests_count_against_the_daily_cap_and_the_cli_run_is_held_to_it`, `::test_the_daily_cap_refuses_a_retry_that_would_pass_it`, `::test_the_dry_run_names_the_daily_cap` |
| F17 | Medium | taps store metadata from the wrong plan | fixed | `::test_a_tap_after_the_plan_changed_keeps_the_seen_plans_density_and_propensity`, `::test_a_tap_naming_an_unknown_plan_is_recorded_but_writes_no_impression`, `::test_a_tap_requires_a_plan_id`; `rw3bReview.test.tsx` "F17 round 5: a tap names the plan its cue was first seen on"; `ReaderScreen.discoveredCues.test.tsx` (taps carry `planId`) |
| F20 | Medium | passage observers submit an obsolete plan id | fixed | `rw3bReview.test.tsx` "F20: a new plan with the same placement and targets rebinds the observers; a passage first seen under B sends plan_B" |

### What changed

- **F16** (`config/schema.py`, `params/parameter_registry.py`,
  `ai/disclosures.py`, `passage_cues.py`, `handlers/reader_cue_discovery.py`).
  - New key `cues.max_calls_per_source_per_day` (default 36, three opens'
    worth), classified structural/operational with the other cue spend
    bounds and named in the privacy disclosure.
  - `PC.discovery_calls_today(repository, extraction_id)` counts the cue
    judge's root receipts (`model_call_receipts`, owner kind
    `passage_cue_judge`, owner id `<extraction_id>|…`) started since local
    midnight. Each receipt is written before its request is sent, so failed,
    unfinished and retried requests all count. Because the count comes from
    durable rows, a new open id, a remount, a vault reload or a restart
    cannot reset it. The same vault database gives the "per vault" scope.
  - `discover` checks that count before each target, ahead of any deep
    (paid) retrieval. It also passes an `admit` to `judge_listwise`, which
    `PaidCalls` calls before every attempt, the retry pre-check included. At
    the cap, the request is refused with `SpendLimitExceeded`
    (`cues.max_calls_per_source_per_day`) before anything is sent, on any
    route, the subscription included. Capped targets carry that reason.
  - The run reports `source_calls_today`, and the dry run's caps name the
    new limit and today's count. The CLI's single run is held to the same
    cap.
  - The per-open budget is unchanged. The sidecar now runs one discovery job
    per (vault database, source) at a time, instead of one per open, so the
    durable count each job reads is exact within the process. Two processes
    on one vault (the CLI beside the desktop sidecar) could each pass the
    check before the other's receipt lands; that bound is per process.
- **F17** (`reader_cue_discovery.py`, `useCueImpressions.ts`,
  `useReaderCues.ts`, `client.ts`, `dto.ts`).
  - `reader.cue_tap` now requires a `plan_id`. The Reader sends the plan
    the cue was first seen on in this visit, from `impressions.planFor(cue)`:
    the plan of the cue's first queued receipt, else the plan served now.
  - The tap still resolves the cue for its event and verdict as before (the
    vault-bound cache, F15).
  - The impression part uses only the named kept plan. A missing impression
    is created from that plan's index entry and density. With an unknown or
    expired plan the tap is recorded, nothing is written to the impression
    (no row, no response), and the reply carries
    `impression: "refused: cue_plan_unknown"`.
  - Current-plan synthesis in taps is gone.
- **F20** (`useCueImpressions.ts`). The observer effect now also depends on
  the served `planId`, so a new plan rebuilds the observers even when
  placement and `targetsKey` are unchanged. The observers also call this
  render's queue through a ref. Receipts already queued keep the plan they
  were seen on, and a passage seen again after a rebuild is not sent again
  (`sentRef`).
- **Snapshots and references.** All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  fingerprints were recomputed with `defaults_fingerprint_for_version`.
  They moved only for the new key, as the comment in `config/template.py`
  records. `db_generate_reference.py` regenerated the reference, which now
  has 927 effective configuration leaves (the hand-written counts in
  `Configuration.md` and `Database.md` were raised from 926).
  `db_validate_reference.py` reports errors []. `validate_vault.py` passed
  (1,132 notes, all reachable).

Existing tests were updated for the tap's required `plan_id`. No migration,
CLI help or `src-tauri` change.

### Fail-before (`1455cbf29`)

- **Backend.** `git archive 1455cbf29` (without `fixtures`, `apps`, `docs`
  and `tests`) was extracted to the scratchpad and run with
  `-o pythonpath=<scratch>/src`. Result: **7 of 7 failed**.
  - The failures-count test failed on its assertion: 12 judge calls, not 3.
  - The retry test failed on its assertion: 2 requests, not 1.
  - The first F16 test and the dry-run test failed because the base has no
    `max_calls_per_source_per_day`.
  - Two tap tests failed because the base refuses `plan_id`
    (`extra_forbidden`), and the third failed because the base accepts a tap
    without one.
- **Base behaviour.** A temporary probe, run the same way and deleted
  afterwards, measured the base directly.
  - F16: **51 judge calls in one day for one source** (five open ids, a
    reload and a fresh context; every one of the 51 targets judged).
  - F17: the A, B, tap sequence stored B's `normal` / `0.8` instead of A's
    `more` / `0.876543211`.
- **Frontend.** `1455cbf29`'s `apps/learnloop-tauri` was extracted to the
  scratchpad, with the worktree's `node_modules` symlinked in and the new
  `rw3bReview.test.tsx` and `ReaderScreen.discoveredCues.test.tsx` copied
  over. Result: **4 failed, 22 passed** of 26.
  - F20 sent `plan_A` for the passage first seen under B.
  - `planFor` does not exist on the base.
  - Both screen-level taps were sent without a `planId`.

### Gate (fix round 5; targeted per the owner rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `uv run pytest -n auto` on 70 files: round 4's 32, `test_reader_rw3b_fix_round5.py`, `test_registry_audit.py`, `test_config_refactor.py` (the defaults snapshots), and every test file naming `parameter_registry`, `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, `defaults_fingerprint` or the AI disclosures | **1,408 passed** |
| `uv run pytest -n auto` on `test_cli_help_snapshot.py` and the other files naming `[cues]` or `CuesConfig` (`test_ingest_runner`, `test_reader_recap`, `test_source_ingestion_adapters`, `test_source_ingestion_v2lite`) | **97 passed** |
| durability | not run: no migration, DB or connection code changed |
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **431 passed** (58 files) |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| references | regenerated: `db_validate_reference.py` errors [], `validate_vault.py` passed |

**Model calls in this step: none.** No vault was opened or copied.

## Fix round 6 (orchestrator)

Codex's verify of round 5 (job `20261020-161743-cY0Gz9`, verdict REOPENED)
confirmed F17, the receipt-before-send ordering, the migrations, and F18
and F19. It found two defects. Both reproduced on `99e32cd00` and are fixed
here under the orchestrator's binding rulings.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F16 | High | a DST fall-back refills the daily allowance | fixed: rolling 24 hours in UTC | `test_reader_rw3b_fix_round6.py::test_the_fall_back_never_refills_the_allowance`, `::test_the_spring_forward_keeps_the_last_24_hours_counted`, `::test_an_ordinary_local_midnight_does_not_refill_the_allowance`, `::test_a_receipt_24_hours_and_a_second_old_drops_out_of_the_window` |
| F21 | Medium | buffered observer entries pick up the replacement plan | fixed | `rw3bReview.test.tsx` "F21: a disconnected generation's delayed callback is discarded; measured again under B, the passage is sent once as plan_B" |

### What changed

- **F16** (`passage_cues.py`). The daily cap now counts the source's root
  judge receipts with `started_at >= now_utc - 24h`; receipts carry
  `started_at`, not `created_at`. This removes all timezone and DST
  handling. The old local-midnight rule took the current offset, so on New
  York's fall-back it put midnight at 05:00Z instead of 04:00Z.
  - `discovery_calls_today` is renamed `discovery_calls_last_24h`.
  - The run reports `source_calls_last_24h`. The dry run's caps name the
    window ("rolling 24 hours (UTC)") and `source_calls_last_24h`.
  - The refusal now reads "… (36 per rolling 24 hours) reached for this
    source".
  - The key keeps its name, `cues.max_calls_per_source_per_day`. It is
    documented as "per rolling 24 hours" in the schema, the registry, the
    disclosure and the template comment.
  - The defaults fingerprints are unchanged, since the value did not
    change.
- **F21** (`useCueImpressions.ts`). Round 5's shared `queueNow` ref is
  gone. Each observer generation captures its own render's `queue`, bound to
  that render's plan, in a closure. Each observer is registered as live and
  removed on disconnect, both on a plan change and on a reflow rebuild. A
  callback the browser delivers after its observer was disconnected is
  discarded: it never queues, under either plan. The replacement observer
  measures the passage again and sends it once, under its own plan.

### Fail-before (`99e32cd00`)

- **Backend.** `git archive` to the scratchpad, run with
  `-o pythonpath=<scratch>/src` and `TZ=America/New_York`: **4 of 4 failed
  on their assertions**.
  - Fall-back: 4 more calls after 36 already in 24 h.
  - Spring-forward and ordinary midnight: calls were admitted.
  - Edge: 4 calls, not 1.
- **Frontend.** The base app was extracted to the scratchpad with the new
  test file: **1 failed, 18 passed**. The A observation was sent as
  `plan_B` before B measured anything.

### Gate

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `uv run pytest -n auto` on 76 files (round 5's 70 and 5, plus `test_reader_rw3b_fix_round6.py`) | **1,509 passed** |
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **432 passed** (58 files) |
| `npm run frontend:build` | built |
| references | regenerated (source-commit labels); `db_validate_reference.py` errors [], `validate_vault.py` passed |
| durability, `cargo check` | not run: no migration, DB code or `src-tauri` change |

**Model calls: none.** Every script outside pytest was static: reference
generation and validation, and the fingerprint computation. The surviving
throwaway vaults under `.pytest_tmp` were swept for completed receipts. Every
one with a real provider name came from a pytest fake: it had no real
endpoint or response id, or pointed at a 127.0.0.1 fake server, and finished
in at most 0.17 s.

## Fix round 7 (orchestrator)

Codex's verify of round 6 (job `20261020-163751-IU2Qhc`, verdict REOPENED)
confirmed:

- F16's rolling window and F21;
- no cap bypass;
- protection, display-only, the dry run, switch-off and the migrations;
- the backend plan binding.

One Medium remained, F22. It reproduced on `3f63a582e` and is fixed here
under the orchestrator's ruling: round 6's rule now applies to Guide marks
too.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F22 | Medium | Guide-mark observers relabel buffered impressions | fixed | `rw3bReview.test.tsx` "F22: a Guide mark's delayed callback from plan A is discarded; measured again under B, it is sent once as plan_B" |

### What changed

- **One implementation.** The new `apps/learnloop-tauri/src/screens/reader/observerGeneration.ts`
  holds the generation-bound observer helper. Each generation tracks its
  live observers, and a callback delivered after its observer was
  disconnected is discarded. `useCueImpressions` (passages) and
  `MarginMark` (Guide marks) both use it.
- **`MarginMark.tsx`.**
  - A new `planId` prop is added to the effect's dependencies, so each plan
    gets its own observer generation, and a plan change measures the mark
    again.
  - The generation's callback is bound in its closure to the plan it was
    built for and to that render's `onSeen`, and it passes that plan
    (`onSeen(planId)`).
  - A sighting from a hover, focus or click passes the plan served now.
  - With discovery off, `planId` is null and the observer calls
    `onSeenRef.current` exactly as RW3a's did.
- **The chain.**
  - `ReaderScreen` passes `planId={cueCtl.planId}` and
    `onSeen={(planId) => cueCtl.noteSeen(cue, planId)}`.
  - `useReaderCues` exposes `planId` and forwards the plan through
    `noteSeen(cue, planId)` to `impressions.noteShown(cue, planId)`.
  - `queue` takes the sighting's plan, falling back to the plan served now.
    That plan also becomes the first-seen plan that later taps name.
- **RW3a.** Its `cue_shown` event and its dedupe are unchanged.
  `ReaderScreen.cuesSwitchOff.test.tsx` and the other switch-off snapshots
  pass, and no snapshot file changed.

### Fail-before (`3f63a582e`)

`3f63a582e`'s `apps/learnloop-tauri` was extracted to the scratchpad, with
the worktree's `node_modules` symlinked in and the new test file copied
over. Result: **1 failed, 19 passed**. The A sighting, delivered after B
rendered, was sent (as `plan_B`) before B measured anything.

### Gate

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **433 passed** (58 files) |
| `npm run frontend:build` | built |
| Python, references, `cargo check` | not run: frontend only |

**Model calls: none.** Nothing was run outside vitest and the build.

## Fix round 8 (orchestrator)

Codex's verify of round 7 (job `20261020-164749-YFl0Nl`, verdict REOPENED)
confirmed F22 and every backend invariant. It found three defects. Each
reproduced on `051d73237` and is fixed here under the orchestrator's
binding rulings.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F23 | High | the discovery-off observer differs from RW3a | fixed | `ReaderScreen.marginMarks.test.tsx` "discovery off: a sighting the webview buffered before the mark unmounted still counts, as in RW3a (F23)" (passes on `c9ad9cce1`, fails on `051d73237`) |
| F24 | Medium | "fewer" bypasses the first-seen plan | fixed | `rw3bReview.test.tsx` "F24: 'fewer' goes to the plan the cue was first seen on, after its first receipt failed and the plan changed" |
| F25 | Medium | discovered marks lose their first-seen plan before taps | fixed | `rw3bReview.test.tsx` "F25: a discovered mark {observed, hovered, focused, clicked} on the {pdf, text} under plan A keeps plan A for its taps after plan B" (8 cases) |

### What changed

- **F23** (`MarginMark.tsx`). The observer effect branches at the top.
  - With `planId === null` (discovery off) it runs RW3a's observer
    verbatim, as at `c9ad9cce1`. A visible entry the webview buffered
    before skim unmounted the mark is still delivered and records
    `cue_shown`.
  - The generation-discard rule from F21 and F22 applies only while
    discovery is on. `onSeen`'s plan argument is optional again, so the
    discovery-off call is `onSeenRef.current?.()` as before.
- **F24** (`useCueImpressions.ts`). `noteFewer` passes `planFor(cue)` to
  `queue` explicitly, never the plan served now by default.
- **F25** (`useCueImpressions.ts`, `useReaderCues.ts`).
  - A new `rememberSeen` records the cue's first-seen plan for the visit.
    It runs for every sighting or touch, Guide or discovered, PDF or text:
    in view, hover, focus or click.
  - This is kept apart from whether the sighting makes an automatic
    impression. A discovered mark's own sighting is still no receipt, so
    the accepted PDF measurement policy is unchanged.
  - `noteShown` remembers first, then queues only a Guide mark's receipt.
  - `useReaderCues.noteSeen` hands every sighting to `noteShown` while
    discovery is on, ahead of RW3a's once-per-visit `cue_shown` dedupe.
  - Taps (open, check me, try first) and "fewer" name `planFor(cue)`, the
    remembered plan.
  - Discovery off, `noteSeen` is RW3a's count alone.

### Fail-before (`051d73237`)

`051d73237`'s `apps/learnloop-tauri` was extracted to the scratchpad, with
the worktree's `node_modules` symlinked in and both test files copied over.
Result: **10 failed, 36 passed** of 46.

- F23: `cue_shown` was `[]`, not `['cue_b1']`.
- F24: "fewer" was sent as `plan_B`.
- F25: all 8 cases returned `plan_B`.

The F23 test also passes on `c9ad9cce1` (RW3a): 17 of 17.

### Gate

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **443 passed** (58 files; the switch-off snapshots unchanged) |
| `npm run frontend:build` | built |
| Python, references, `cargo check` | not run: frontend only |

**Model calls: none.** Nothing was run outside vitest and the build.

## Fix round 9 (orchestrator)

Codex's verify of round 8 (job `20261020-165636-s3ij4K`, verdict REOPENED)
confirmed:

- F23, and that discovery off no longer differs from the base;
- the tap side of F24 and F25;
- the migration fixture.

One Medium remained, F26. It reproduced on `5568692fa` and is fixed here
under the orchestrator's ruling.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F26 | Medium | automatic receipts bypass the first-seen plan | fixed | `rw3bReview.test.tsx` "F26: a discovered mark seen under A before its passage counted is recorded under A when the passage counts under B" and "F26: a Guide mark whose receipt failed twice under A is recorded under A when it is observed again under B" |

### What changed

`useCueImpressions.ts`'s `queue` now resolves the plan for every receipt,
whether from the passage observers, a Guide mark's sighting or "fewer". It
uses the cue's remembered first-seen plan for the visit when there is one.
Otherwise it takes the sighting's own plan (the observer generation's, else
the plan served now), which then becomes the cue's first-seen plan.

The rejection of callbacks from disconnected generations (F21, F22) is
unchanged: such a callback still never reaches `queue`.

### Fail-before (`5568692fa`)

`5568692fa`'s `apps/learnloop-tauri` was extracted to the scratchpad, with
the worktree's `node_modules` symlinked in and the new test file copied
over. Result: **2 failed, 29 passed**. Both regressions submitted `plan_B`.

### Gate

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| `npx vitest run src/screens/reader/ src/screens/ReaderScreen src/components/PdfReaderPane.marks.test.tsx` | **445 passed** (58 files) |
| `npm run frontend:build` | built |
| Python, references, `cargo check` | not run: frontend only |

**Model calls: none.** Nothing was run outside vitest and the build.
