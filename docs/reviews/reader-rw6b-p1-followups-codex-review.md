# Reader RW6b part 1: Codex review fixes (`reader/rw6b-followups`)

The Codex review of the stage (`gpt-6.1-sol`, job `20261031-142011-eGzO0z`) reported 4 High and 8 Medium findings.
I reproduced each one first with a failing test, then fixed it, or rejected it with a reason.
The repro tests are `tests/test_reader_followups_review.py` and `tests/test_reader_followups_successor.py`.
Before the fixes, every repro test failed for the reason the finding gives: 21 failures out of 21 tests in
`test_reader_followups_review.py`; the F4 gating did not exist.

**Spend: $0.** No model or paid calls. Tests use fakes only. Every Python run outside pytest used `env -i` with
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` under `fixtures-local/rw6b-env/`: the reference
generator, the CLI help snapshot writer and the fingerprint computation. No owner vault, `~/learnloop-vaults`,
`~/learnloop-retired` or `~/learnloop-books` was opened.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Exposed follow-ups can still be served as cold checks | fixed | `4741c4f5e` | `test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks`, `test_f1_a_related_worked_example_is_only_a_label_for_a_discriminating_check` |
| F2 | High | Automatic commitments override explicit learner intent | fixed | `4741c4f5e` | `test_f2_an_automatic_follow_up_never_lands_in_a_scope_the_learner_chose[pause,master]`, `test_f2_creation_refuses_an_item_the_learner_committed_since_the_search` |
| F3 | High | Crashes can leave live checks outside the digest and revaluation machinery | fixed | `4741c4f5e` | `test_f3_a_failure_before_the_digest_is_written_leaves_no_orphan_commitment`, `test_f3_a_session_another_process_planned_meanwhile_is_not_published_twice` |
| F4 | High | The serving change has no algorithm successor | fixed (successor `mvp-0.39`) | `ea98440d8`, `SUCCESSOR_COMMIT` | `tests/test_reader_followups_successor.py` (17 tests: the constant, the tag/switch gate, plan parity, the upgrade link, interrupted activations, shadow 0/0/0) |
| F5 | Medium | Daily revaluation makes paid calls outside its advertised controls | fixed | `4741c4f5e` | `test_f5_revaluation_never_reaches_the_exposure_judge`, `test_f5_with_the_source_switches_off_revaluation_values_nothing_and_keeps_the_check`, `test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes` |
| F6 | Medium | Partial success turns a budget interruption into permanent truncation | fixed | `4741c4f5e` | `test_f6_a_budget_stop_after_a_pick_stays_incomplete_and_resumes_with_the_pick` |
| F7 | Medium | Repair decisions never reach the EVSI path | fixed | `4741c4f5e` | `test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question`, `test_f7_revaluation_passes_the_stored_pending_decision` |
| F8 | Medium | Required candidate kinds cannot complete the follow-up pipeline | rejected (deferred to a follow-up stage) | — | See "F8" below: the instrument arm conflicts with the probe episode's own administration, and the import arm needs paid authoring and vault writes from a background job, with a generation cap that does not exist yet. |
| F9 | Medium | Formative-only questions are discarded by the retention adapter | fixed | `4741c4f5e` | `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`; `test_formative_records_add_questions_only_with_their_switch` (updated) |
| F10 | Medium | The way back disappears when there was no inquiry | fixed | `4741c4f5e` | `test_f10_the_workbench_session_carries_the_way_back_without_an_inquiry`, `test_f10_a_formative_record_and_the_studied_passage_are_the_fallbacks` |
| F11 | Medium | Repair ownership is too broad and is checked only during initial planning | fixed | `4741c4f5e` | `test_f11_a_retry_owns_only_the_facets_its_item_assesses`, `test_f11_a_repair_retry_scheduled_after_the_follow_up_takes_its_place` |
| F12 | Medium | Familiar siblings receive undiscounted value | fixed | `4741c4f5e` | `test_f12_a_familiar_sibling_counts_for_less_than_its_undiscounted_value`, `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount` |

## What changed, per finding

**F1 and F11: one serve-time gate.** The new module `scheduling/intent/followup_gate.py` re-checks a reader
follow-up before DL2 serves it cold. It makes no model call. It checks two things:

- Exposure since valuation, using the sources spec's full exposure rule at serve
  (`db.stores.source_service.serve_time_exposure`). The rule counts:
  - an attempt;
  - a reveal on the item or its family;
  - source text shown from the item's span;
  - an impression from any proposal;
  - a studied worked example the judge called equivalent or related, or that nobody judged.

  The window starts at whichever is later: the valuation, or the start of the cold delay
  (`serve_eligibility.COLD_RETRIEVAL_DELAY`). Studied worked examples are read in the question's teaching scope,
  recorded on the provenance as `exposure_scope_extraction_ids`. A related worked example only labels a
  `discriminate` check; it never excludes it, which is the valuation's own rule.
- Repair ownership (`owning_retry`). A repair `cold_retry` owns a facet only when the item it measures assesses
  that facet. It may do so on the claim's own attempt, or on an item of the claim's learning objects. A retry with
  no item yet owns what its source attempt touched.

`split_check` (DL2) consults the gate for `via: reader_followup` checks only. A gated candidate is held, with its
reasons recorded in `CheckState.gated`, and is never administered cold.

The daily re-valuation applies the same gate:

- An exposure retires the check (`exposed_since_valuation`) and marks its question incomplete with no
  continuation, so the next plan runs a fresh search.
- Repair ownership retires the check (`repair_retry_owns`).

Creation uses the same `owning_retry` rule. Neither retirement is shown as good news on the card.

**F2: explicit intent.** `committed_items` lists the items that some other commitment decides, using DL2 §5.3's
resolution: Pause, Master, Learn, Keep, reference-only, the learner's own "Check once", or another session's
follow-up. Those items go to `find_practice` as `exclude_item_ids`, so they are never valued, and the receipt keeps
them as `learner_intent_item_ids`. The publication transaction checks again. An item the learner committed during
the search is skipped with `learner_intent`. An automatic check therefore never becomes the newest choice over an
explicit one. Its eventual `satisfied` never replaces an ongoing learning commitment, because such an item is
never a candidate.

**F3: one publication.** `plan_session` runs every paid search first. One transaction (`_publish`) then does the
following:

1. Re-reads the digest. If another process has planned the session, or changed its row since, that row stands and
   nothing is published.
2. Re-checks the learner's intent.
3. Creates the commitments.
4. Writes the digest receipt and bumps the queue revision.

The process-local lock now only stops this process from starting two jobs.

**F4: the successor `mvp-0.39`** (`READER_FOLLOWUPS_ALGORITHM_VERSION`, after `mvp-0.38`). It is the spec's own
fallback.

- `followups_enabled` requires the tag and `followups.enabled`. Planning, re-valuation and the background job are
  gated on it.
- `learnloop.reader_followups_upgrade` is the chain's next journalled link. It accepts `mvp-0.38`, or `mvp-0.9`
  onwards through the chain. It is wired into `learnloop upgrade --to`, the CLI and sidecar completions,
  `activation_journal`, and the import-linter module list.
- The defaults snapshot for `mvp-0.39` is recorded. The `[followups]` comment and the registry rationale now name
  the switch as the successor's kill switch.
- Plan parity: with the switch off, `get_today_queue` at `mvp-0.39` serves exactly what `mvp-0.38` serves, and
  writes no digest or commitment.
- 30 chain-pin test files moved their latest from `mvp-0.38` to `mvp-0.39`. The CLI help snapshot was regenerated;
  only `upgrade` changed.

**F5: no paid call on the synchronous path.**

- `default_valuer` passes `eligibility=_applied_exposure` to `value_request`, so the worked-example judge is
  unreachable. The exposure rule has already run from persisted judgments (the gate).
- With `source_service.enabled` or `discriminating_search` off, re-valuation values nothing and keeps each check,
  recording the switch.
- A check whose only exposure is an unjudged studied worked example is kept as `exposure_refresh_needed`.
  `refresh_exposure` then asks the judge in the background job (`prepare_followups`), under both envelopes
  (`followup_spend`) and the switches.

**F6: early stops stay incomplete.** Any `budget` or `judge_unavailable` paging marks the question incomplete,
even when it already chose checks. Its `continue_from` (the proposal id) is kept. The next plan resumes through
`continuation_cursor`, whose cursor carries the relevant candidates found so far, so the earlier picks take part in
conditional valuation. A mismatched or missing cursor falls back to a fresh search. Picks are published as they are
chosen and never duplicated.

**F7: decision questions.** For each session attempt with an open causal factor, `pending_causal_decision` (S2b's
reader) gives the locked hypothesis set and its repair classes. Each set becomes its own `decide:<set>` question, so
spaces are never merged. Its `pending_decision` goes to `find_practice`, which passes it to the valuer, so
`rank_feasible`/`robust_evsi` runs. The decision is also stored on the provenance for re-valuation. An unavailable
decision is a typed note.

**F9: formative-only retention.** A retention question that only formative records raised names itself with a
`retention` ref. `open_hypotheses` then passes `formative=True`, and `retention_problem` poses it on
`formative_anchor`: the most recently attempted item of the LO and facet, or else its first active item carrying
the facet. The prior is the active predictor's P(success). The record changes which question is asked, never a
number.

**F10: the way back.** `_session_spans` now adds three sources:

- the spans of the workbench sessions that worked an item of the question's learning objects;
- the spans of formative records whose spans or facets touch those learning objects;
- with neither, the session's other workbench and formative spans, or else the first span of the section read
  last.

**F12: familiarity.** `valuation.discount_members` composes `recall_coverage.familiarity_discount` into each item's
members as d·P(E|H) + (1−d)·P(E). Under d, the observation carries d of an independent one's evidence. d = 1 leaves
the item unchanged, and the composition adds no new number. `value_request(familiarity=True)` applies it and puts
the discount on the receipt: the candidate entry, the chosen check and the chosen line. RW6b's search and
re-valuation turn it on. Other callers of `find_practice` are unchanged.

### F8 (rejected for this stage; deferred)

- **Instruments.** A `diagnostic_probe` instrument is administered by its open probe episode. DL2's admission
  refuses a fresh diagnostic surface outside the episode's own administration (the freshness and probe gates in
  `serving_exclusions.admission_reason`). The episode already serves its eligible instruments the same day.
  Turning one into a dated `test_me_later` would double-schedule a single-use surface. The episode's rival question
  is still a `discriminate` question here (`episode_label`), valued over ordinary items, and closing the episode
  answers it.
- **Unimported textbook exercises.** Making one a check needs three things:
  - a paid authoring call;
  - the key verifier ladder;
  - a vault YAML write and reload, run from the sidecar's background job.

  It also needs the generation spend cap (`followups.generation_max_daily_cost_usd`), which, like §9.3 item 8's
  generation, has no source-anchored request API to build on. Exercises still reach the valuation as unvalued,
  `not_imported` candidates, and never as checks. This is a stage of its own, not a fix.

## Claims corrected

- "DL2 re-checks independence at serve": it now does, through `followup_gate` with the full rule.
- "Re-valuation makes no model call": it now holds. The judge runs only in the background refresh, inside both
  envelopes.
- "A budget stop leaves the digest incomplete": it now holds even after a pick.
- "The provenance carries the way back": it now holds with or without an inquiry.
- "Formative records add questions": those questions are now valued.
- "No successor": `mvp-0.39`. The stage record carries a pointer to this file.
- G35 reuse: the familiarity discount is composed into the valuation.

## Gate

GATE_PLACEHOLDER
