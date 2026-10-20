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
