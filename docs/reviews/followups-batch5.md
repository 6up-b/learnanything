# Follow-ups batch 5 (stage `followups-batch5`, branch `fix/followups-batch5`)

Base `f9bc4254b3` (main: followups-nov2, help-fold successor mvp-0.42, migration 235, head
`fixtures/migration_head_235`; RW5d P4b; TE1+C4 mvp-0.41/234; C2b 233; P3 232). Worktree
`learnanything-merge2`.

Ten queued items (A-J), one commit each, defects reproduced first. **No migration, no successor**: nothing
here changes scoring, scheduling, projections, serving or what replay reads; kill switches are unchanged.
**No live or paid call**: every model is a fake; ad-hoc scripts (the architecture-vault generators and
validators) ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`; no
owner vault, `~/.config/learnloop` or tracked working vault was opened; no desktop window was launched.

## A. An earlier lesson's recap re-checked against current protection (TE1 post-land verify, High)

Codex job 20261102-050349-DQNXMf: "Start a fresh lesson" imported lesson 1's recap through `last_lessons`
(`teacher/brief.py`) after passage P that recap quoted became held out; the fresh lesson recorded today's
protection as its baseline, so `protection_changed` never fired and the first teacher prompt carried P.
`read_history(l:...)` returned the same recap.

* `teacher/brief.py` `recap_admissible(vault, repository, lesson_id, current=...)`: the recap was written
  under the protection its lesson recorded (a change mid-lesson ends that lesson with no recap). While the
  vault's protection digest is the same, it stands. When it changed, or the lesson recorded none, it stands
  only if every passage the lesson delivered (its open book plus every read action's `book_additions`, so the
  recap's cited aliases too) is still teachable (`passage_teachable`, the predicate the live lesson uses) and
  no item the lesson was shown while unwithheld (brief probes, tutor-question and unprotected attempt
  history, `find_practice` results, its own checks) has since become exam or reserved material. Protection
  that cannot be read omits the recap: fail closed for that recap only; the lesson still opens.
* `admitted_recap` is used by `_last_lessons` (one `protection_state` read for all recaps) and by
  `actions.read_history` for `l:` refs. An omitted recap is `None` with `recap_omitted` (no content).
* Why items as well as passages: a recap can quote a probe stem the old brief showed. A protected history
  entry is excluded (it was already withheld at that lesson's baseline and showed no text), as are cold
  checks (`a check waiting in the app`: the lesson's own delayed checks, which exclude what the recap
  displayed), so the ordinary case (lesson 1's own delayed checks committed at its close) keeps the recap.
* Tests (`tests/test_followups_batch5_recap_protection.py`, 7; real brief, protection, gate and prompt
  builders, synthetic teacher vault): held-out P is absent from every prompt of the fresh lesson; `read_history`
  cannot fetch it; unchanged protection keeps the recap; a change elsewhere (another unit held out) keeps it;
  a probe item reserved for an exam since drops it; unreadable protection drops only the recap; a lesson with
  no recorded protection re-checks its passages. 5 of 7 failed before the fix (the two keep-the-recap controls
  passed, as expected).

## B. Settings' hidden notes name a vault note's kind (C2b)

`note_links.hidden` gave `origin_label` only for Pocket Notes, so a vault note's row ended at "linked by you".
It now labels a vault note by its kind (`VAULT_ORIGIN_LABELS`: "your note in the Reader" for an annotation,
"your capture" for a capture; `hidden_origin_label`). Pocket Notes keeps its label; a tend-era note stays
unlabelled (its title and heading name it). The Reader's link lines (`link_view`) are unchanged.
The title and path were already on the row (`title › heading`); the missing part was where the note came from.
Tests: `tests/test_notes_linked.py` (the R5 test now asserts both labels; it asserted `None` before),
`hiddenNotesSettings.test.tsx` (+1: a Reader note's and a capture's rows show their kind).

## C. The lesson's unavailable-route copy is true to what was saved (TE1)

With the teacher's route not ready, `lesson.turn` said "...; your lesson is saved." even for an opening,
which resolves its route before writing anything (no lesson row). The sidecar's `teacher()` now raises
`_RouteUnavailable`, and `lesson_turn` words it by state (`route_unavailable_message`): a step of an existing
lesson, or an opening whose error carries a `lesson_id`, says the lesson is saved and resumes; an opening says
the lesson didn't start and nothing was saved. The service's own outage line (a teacher call failing after the
save) was already true and is unchanged. Tests (`tests/test_followups_batch5_lesson.py`, 3) drive the real
handler with `ready_client_for_task` reporting the route not ready.

## D. Resume makes no extra teacher call (TE1 F16, ruled Low at R3): a small change, done

`_pending_call` and `_owes_followup` treated `check_withdrawn` as an action boundary, but it is written as an
effect of the accepted turn that gave the check away (`refs.turn`). After a help action that withdrew the
check, resume saw a step "waiting" and called the teacher again; with a read follow-up, the follow-up turn was
taken for its action's first and owed another call. `_boundary`: a step marked as a turn's effect is never a
boundary. Tests count teacher calls: 0 on resume in both shapes (they were 1 and 1 before the fix); the
follow-up's deferred reads still ride with the next learner action. F14/F15 tests unchanged and passing.

## E. A figures daily-budget refusal leaves a teacher visual unavailable (P4b)

`visuals._budget_refused` treated any `SpendLimitExceeded` in the exception chain as the lesson's envelope
refusing. The figure service raises `FigureRefused("capped")` from the `SpendLimitExceeded` of the figures'
shared daily envelope (`figures.max_daily_cost_usd`), so that refusal closed the whole lesson with `budget`.
Only the lesson gate's own `refusal` closes it now; the daily-budget refusal records the visual as
`unavailable` (`capped`) and the lesson goes on. Tests: the daily-budget refusal keeps the lesson open and the
next reply reaches the teacher (failed before); a real refusal of the lesson's envelope (a per-lesson cap with
no price, admitted through `model_call`) still closes it with `budget`; the predicate decides by the gate
alone. P4b's Codex F4 test (`test_review_f4_...`) simulated the lesson's refusal with a bare
`SpendLimitExceeded`; it now drives that real lesson-gate refusal (same assertions, all three actions).

## F. The sketch sandbox review's t_max test is deterministic

`sketchSandboxReview.test.tsx` "keeps the checks ... played to t_max" waited on the real 60 ms play interval for
100 ticks (6.0 s alone) under a 12 s `waitFor`; in the whole vitest run the interval drifted past it. It now
fakes only `setInterval`/`clearInterval`, fires each tick with `vi.advanceTimersToNextTimerAsync()` inside
`act` (the engine's queued promise work finishes before the next tick; real `setTimeout` yields between
timers), bounds the loop in ticks (`PLAY_TICKS + 1`), not time, and drops the explicit 15 s test timeout. It
also asserts play stopped at t_max. 225 ms per run, 3/3; the figures vitest directory 411/411.

## G. P4a followed figures and correspondence lookups: nothing to do

* **Recomputed on every Reader read?** No. Correspondents are read once per section crossing
  (`correspondentsRead.ts` `quietCorrespondents`: one request in flight per section answers CA5's line and
  CA5a's find; `FindSection`/`useSideBySide` read on their own press), not per passage read. The sidecar keeps
  the parsed library (`_library_cache(ctx).get`); `_with_figures` calls `FS.section_figures` once per
  correspondent reading, a read of `_listed` rows with no engine run and no write (P4a Codex F3). Keeping
  nothing between crossings is P4a's design: "Protection is read again on every call (through
  `LibraryCache.get` and `list_figures`)" (docs/reviews/reader-rw5d-p4a-figures-follow-section.md), so a
  cache of the figure listing would have to be invalidated on every protection change, which is what the
  re-read already gives. A followed figure's own listing is read only at the press (`useFigures.follow`).
* **Followed state lost on reload?** It is in memory (`useFigures` `followed`) and cleared when the book
  changes, by design: P4a writes nothing and copies nothing (Q8: no `source_objects` mirroring); the figure is
  shown "in place with its home named" while the learner is in the corresponding section, and the *also in
  your books* line offers it again at the next crossing (one press). Persisting it would need a write P4a
  rules out, so it is not state that "should persist".

## H. C5 judgment-ledger audit: nothing to fix, pinned

C5's commits (ad2c282a43, 1ff5051916, 906e471141, 6e008ac03d, dfb053fddb, 236a323c92; followups-nov2's
929592c6e4) add no `append_judgment` call. A note's reading writes through the shared writers every learner
text uses: `judges.log_reading` (`learner_gap_kind`, rationale = the named gap as JSON), the Decider's kind
verdict (`decider_rationale`), `ask_needed` and `matching.judge.judge_pairs` for the pair tasks. The report
(`text_gaps/report.py`) reads gap rows (`by_source`, kinds by chooser) and pair verdicts by task, for every
source kind. `tests/test_followups_batch5_c5_ledger.py` pins it: every ledger row a note's reading writes
fills task, kinds, judge, model, prompt version, input hash, verdict and rationale; the report counts the
note's gap (`by_source.learner_note == 1`). The C5 open item about the kind verdict's rationale naming a
note's gap stands as recorded there (owner 2026-11-01: learner notes are not private; no off-plan consumer).

## I. `diagnosis/text_gaps/__init__.py` added

Checked first: `text_gaps` was the only directory under `src/learnloop` with modules and no `__init__.py`, so
grimp skipped it and import-linter checked none of its imports. With the file, 4 contracts broke:

* `notes-are-never-a-source-or-evidence`, `evidence-never-reads-the-workbench`,
  `evidence-never-reads-reader-observations`: all 100 broken chains ran through one edge, C5's declared note
  door `learnloop.diagnosis.text_gaps.sources -> learnloop.source_retrieval.note_gaps` (opt-in,
  function-local). Each contract now ignores exactly that edge, with the reason.
* `frozen-cross-package-cycles`: that edge, and three existing edges into text_gaps that close cross-package
  cycles (`goals.goal_lo -> text_gaps.actions`, `learner_protection -> text_gaps.provenance`,
  `reader.active_reading -> text_gaps.jobs`), are frozen as they stood. No new edge was added.

Every other text_gaps import is now checked (before: none). `tests/test_notes_never_read.py`'s graph test now
sees text_gaps: it asserts the C5 edge exists and, set aside, that nothing in its `NEVER` list reaches the
notes' code (its static pin of the single importer is unchanged). No namespace-package assumption elsewhere:
`test_instructional_layering.py` and `test_e0_isolation.py` name `learnloop.content` (still a namespace
package), and both pass.

## J. Architecture-vault catalogs

* `module_validate.py`: **FAILED with 1354 issues** (474/1136 modules, 33/63 package maps: last generated in
  September). `module_generate.py` needed descriptions for the 30 packages added since (written from each
  package's docstring); `GENERATED_DATE` 2026-11-02. Regenerated: 1136 module notes, 63 package maps, 1
  catalog. The validator's duplicate test-case rule then failed 25 notes where two test files define a test of
  the same name (the generator lists cases per test file); the rule now applies per test file. The new notes
  made 14 bare table links in `Maps/LearnLoop Pipeline Map.md` ambiguous; they now name the Database table
  note. Result: module_validate PASS (1136/1136, 63/63, 1200/1200 YAML, 39198 wikilinks, 37062 file links);
  validate_vault PASS (2080 notes).
* `desktop_validate.py`: stale after B's `dto.ts` comment; `desktop_generate.py` rerun; PASS (307/307 TS + 6/6
  Rust, reproducible byte for byte).
* `db_generate_reference.py` rerun (A's and B's line shifts in cited sources, commit stamps);
  `db_validate_reference.py` errors `[]`.

## Gate (targeted; the full suite runs once in the landing gate)

Commands run (every pytest/vitest/npm command inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`):

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`
- `uv run lint-imports --no-cache`: **42 kept, 0 broken** (after I; 42 kept before it too, with text_gaps ungraphed)
- targeted pytest, `uv run pytest -n 6` over the 103 files below (under `flock /tmp/learnloop-fullsuite.lock`):
  **2087 passed, 13 skipped, 2 xfailed, 0 failed** (608 s)
- `npm install`; `npm run typecheck` (clean); `npx vitest run --maxWorkers=4` over `hiddenNotesSettings.test.tsx`,
  the whole `src/screens/reader/figures/` folder (`sketchSandboxReview` included) and `LessonScreen*`:
  **19 files, 430 passed**; `sketchSandboxReview.test.tsx` alone 3/3 (225 ms for the t_max test)
- `npm run frontend:build`: built
- architecture vault: `module_validate` PASS, `desktop_validate` PASS, `validate_vault` PASS,
  `db_validate_reference` errors `[]` (after the regenerations in J)
- not needed: no Rust change (no cargo), no schema or migration change (no durability lane), no config default
  or CLI change (no snapshot tests)

Pytest files: `test_ad23_contract`, `test_ad2_model`, `test_ai_tool_isolation`, `test_approach_map_boundaries`, `test_architecture`, `test_batch3_landing`, `test_blind_grading_contract`, `test_causal_repair_sidecar_rpcs`, `test_codex_lockdown_round2`, `test_curriculum_c3_exam_scoping`, `test_daily_plan_rpc`, `test_decider_landing`, `test_deliverable_rpcs`, `test_deliverable_scope`, `test_desktop_activation_audit`, `test_desktop_rpc_contract`, `test_diagnosis_contract`, `test_diagnosis_input_provenance_landing`, `test_diagnosis_input_provenance`, `test_e0_isolation`, `test_embedding_backfill`, `test_figure_predictions`, `test_figures_codex_review`, `test_figures_fix_round2`, `test_figures_fix_round3`, `test_figures_fix_round4`, `test_figures_scope_redesign`, `test_figures_show_me_codex_review`, `test_figures_show_me`, `test_figures_switch_off`, `test_followups_batch5_c5_ledger`, `test_followups_batch5_lesson`, `test_followups_batch5_recap_protection`, `test_followups_nov2_figure_provenance`, `test_followups_nov2_note_gap_unlinked`, `test_held_grade_composition`, `test_help_assist_figures_migration`, `test_help_assist_work_md_migration`, `test_help_fold_attach_successor`, `test_hint_feedback_texts`, `test_hint_feedback_widening`, `test_hint_h2b_review`, `test_hypothesis_reference_contract`, `test_instructional_layering`, `test_intent_rpc`, `test_judge_routes`, `test_learner_gap_unlinked_migration`, `test_learner_notes_migration`, `test_learner_note_source_kind_migration`, `test_learner_notes_vault_origin_migration`, `test_learner_text_gaps_composition`, `test_learner_text_gaps_flow`, `test_learner_text_gaps`, `test_learner_text_gaps_rereview`, `test_learner_text_gaps_review`, `test_learner_text_source_widening`, `test_mcp_c1a_landing`, `test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_tools`, `test_mobile_allowlist`, `test_mvp016_upgrade`, `test_notes_as_learner_text`, `test_notes_c2b_review5`, `test_notes_linked`, `test_notes_never_read`, `test_notes_vault_search`, `test_probability_cli`, `test_query_student`, `test_reader_active_reading`, `test_reader_formative_texts`, `test_reader_observation_records`, `test_reader_question_note_id_placement`, `test_reader_rw1b_review`, `test_reader_rw3b_protection`, `test_reader_rw3b_review_fixes`, `test_reader_rw5d_p4b_teacher_visuals`, `test_reader_tutor_retrieval`, `test_recurrence_commands`, `test_regrade_contract_replay`, `test_regrade_contract_successor`, `test_regrade_contract_upgrade`, `test_required_method_round3_review`, `test_router_card_reading_gaps`, `test_section_coverage_rpcs`, `test_sidecar_close_cancels_jobs`, `test_sidecar_contract`, `test_source_inventory`, `test_source_space_resolver`, `test_t6_followup_composition`, `test_teacher_te0_fix_round2`, `test_teacher_te0_review_fixes`, `test_teacher_te1_curriculum_c4`, `test_teacher_te1_lesson`, `test_teacher_te1_migration`, `test_teacher_te1_review_fixes`, `test_teacher_te1_successor`, `test_teacher_te1_weight`, `test_tier1_decider`, `test_ux_phase4_landing`, `test_workbench_hint_service`, `test_workbench_in_session_gaps`, `test_workbench_text_gaps`.

## Open items

* B's labels are server words for two vault kinds; if the owner wants the note's location in the label too
  (the title and heading already show it), that is a copy change in `VAULT_ORIGIN_LABELS`.
* The module catalog goes stale again with every landing that adds modules (TE1b and P5 will); nothing
  regenerates it automatically. Rerunning `module_generate.py` at the end-of-queue docs pass keeps it current.
* I's frozen edges are the existing cycles made visible, not fixed; the end-of-queue architecture pass may cut
  them.
