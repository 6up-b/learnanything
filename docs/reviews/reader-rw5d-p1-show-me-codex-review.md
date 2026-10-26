# Reader RW5d P1 "show me": Codex review and fixes

- **Stage:** `reader/rw5d-p1-show-me` in `learnanything-ad1` (stage record: `docs/reviews/reader-rw5d-p1-show-me.md`).
- **Review:** Codex job `20261026-114351-er0HXo`, read-only, from the source alone (its sandbox could not run the
  memory-capped pytest).
- **Method:** each finding was reproduced first with a failing test (the backend tests were run against the pre-fix
  source `11da87ef9`: 24 of the 27 new tests failed there; the 3 that passed are controls), then fixed.
- **Live calls:** none. Every model, the retrieval and the author are fakes; no CLI or paid command was run.
- **No migration, schema, config or successor change.** One new `judgment_ledger` task (`figure_goal_offer`) and one
  new retryable refusal code (`storage_busy`).

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Grounding model calls bypass the figure kill switch | fixed | `879eacecd` | `test_f1_switching_off_during_grounding_stops_its_calls_and_the_author` (×4: show me / figures off, after the 1st / 2nd call), `test_f1_the_control_admits_every_grounding_call`, `test_f1_a_reuse_after_show_me_is_switched_off_is_refused` |
| F2 | High | Non-tutor requests ignore the supplied host's restrictions | fixed | `879eacecd` | `test_f2_a_restricted_question_event_refuses_a_show_me_request` (×5: cold, cold policy, bound to an item, a practice question, a feedback question; each for a goal-only and a joint request), `test_f2_an_open_reader_question_event_derives_a_reader_caller_from_it`, `test_f2_two_different_answers_named_at_once_are_refused` |
| F3 | Medium | Reusing a goal lands it at the first request's passage | fixed | `879eacecd`, `bc916bbd5` | `test_f3_a_reused_goal_lands_at_the_current_requests_home` (×2: grounded, nothing found), `test_f3_an_anchored_figure_is_listed_once_at_its_anchor`; vitest `F3: a reused goal landing at a second paragraph keeps both placements` |
| F4 | Medium | Later held-out checks omit goal-only figures' home spans | fixed | `879eacecd` | `test_f4_a_home_held_out_after_construction_withholds_the_figure`, `test_f4_a_later_placement_held_out_withholds_the_figure_too`, `test_f4_an_unreadable_home_fails_closed` |
| F5 | Medium | Goal-only predictions lose their source context and learning-object anchors | fixed | `879eacecd` | `test_f5_a_goal_only_figures_prediction_is_read_with_its_grounding_passages`, `test_f5_the_gap_reader_is_sent_the_grounding_passage`, `test_f5_an_anchored_figures_text_is_unchanged` |
| F6 | Medium | Tutor figure-goal judgments never reach `judgment_ledger` | fixed | `879eacecd` | `test_f6_the_tutors_goal_has_one_ledger_row_and_the_press_reads_it`, `test_f6_a_goal_in_the_view_with_no_ledger_row_is_refused`, `test_f6_no_goal_writes_no_goal_row` |
| F7 | Medium | Reuse silently loses request-ledger records | fixed | `879eacecd` | `test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses` |
| F8 | Low | Required source peeks and return navigation are missing | fixed | `bc916bbd5` | vitest `F8: open goes to the figure with a back-to-where-I-was crumb, and the crumb restores`, `F8: the thread's cited passages are chips that peek here and open another book as a detour`; pytest `test_f8_every_cited_passage_names_its_source` |
| F9 | Low | The new grounding cap is absent from the parameter registry | fixed | `879eacecd` | `test_f9_the_grounding_cap_is_registered_and_audited`; `tests/test_registry_audit.py` |

All the pytest cases are in `tests/test_figures_show_me_codex_review.py`. The vitest cases are in
`apps/learnloop-tauri/src/screens/reader/figures/showMe.test.tsx`.

## The fixes

### F1: one live gate for the whole request
- `build_figure` installs the build's `FiguresGate` (`key_for(request)`, reading `live_vault()`) **before grounding**.
  It stays installed through reuse, authoring and storing (the new `_build`).
- Every physical request grounding makes (the sources service's rewrite, embedding and verification calls go through
  `model_call`) is admitted against the configuration as it is now.
- `gate.check("grounding")` replaces the old recheck, which read the captured vault.
- A reuse checks the gate too (`gate.check("reuse")`).
- A change anywhere ends the request as `figures_changed`, with no further call and nothing stored.

### F2: a supplied question event determines the caller, whatever the origin
- `_host_caller` resolves every supplied question event through `caller_for_question_event`: `hostRef.questionEventId`
  from any origin, and a tutor offer's `offerRef`.
- The event's restriction becomes the request's:
  - a cold question refuses with `cold_check`;
  - a question bound to an item derives `assisted_practice` and refuses with `validation_error`.
- A question from any context other than `reader` (practice, feedback, library) is refused as incompatible, because
  P1's hosts are the Reader's.
- Two different events named at once are refused.
- The caller kind follows the origin (spec §7.2): `reader` for selection, show me and library, `tutor` for tutor. The
  event's restriction is kept either way.

### F3: placement belongs to the request
- `figure_view(home=...)`: a reused goal-only figure is delivered at the **current** request's reading position.
- `list_figures` lists a goal-only figure once per distinct home in this source. The homes come from
  `figure_requests.reading_at_json` across the figure and the versions it supersedes, so a "not right?" version keeps
  every placement.
- The Reader's `land` keeps the other placements of a reused figure. A new version takes every placement of the one it
  supersedes.
- Reusable content (`interactive_figures`, keyed as before) stays separate from placement (`figure_requests`).

### F4: homes in the shared admission rule
- `figure_admission.figure_home_keys(connection, figure_id)` is one SQL rule, shared by the figure service and the
  learner-text gap reader (so the gap reader still never imports the figure package).
- It returns every recorded home of a figure that has no passage.
- `row_withheld` (listing, delivery, predictions, explanations, revisions) and `figure_prediction_withheld` recheck
  those homes for held-out material. This check is separate from the passages sent to the author.
- An unreadable stored home fails closed.
- I chose fail-closed per figure: if any of a figure's homes becomes held out, the figure is withheld at all of its
  placements. Held-out changes are rare, and this keeps one predicate for the row.

### F5: the formative text carries the grounding
- For a figure with no passage, `figure_prediction_text` now builds the passage, the learning-object anchors and the
  subject from the passages its goal was grounded in, across sources.
- Those passages are the request's kept keys (`grounding_manifest.kept`). When no kept keys are recorded, it falls back
  to the figure's retrieved keys.
- An anchored figure's text is unchanged; its passage text is byte for byte `_span_texts`, as before.
- The end-to-end test runs the gap job with the fake gap LLM. It asserts that the grounding passage reaches the reader
  and that the learning object is stored as the gap's anchor.

### F6: the tutor's goal is a ledger judgment
- `tutor_qa._record_figure_goal` appends one idempotent `judgment_ledger` row per answer that writes a goal. The row:
  - task: `figure_goal_offer`;
  - id: `fgj_…`, derived from the question event;
  - judge: `llm`, with the model and the prompt version;
  - `input_hash`: the prompt version and the event;
  - `right_id`: the goal's digest (its normalized text and its grounding keys, in order);
  - verdict: `offered`;
  - rationale: the goal and its keys.
- At press time, `tutor_figure_goal` requires that row to match the stored view's goal and grounding. A view edited to
  another goal or other passages, or one with no row, is refused as `not_offered`.
- This follows RW5b's `figure_explorable` pattern (bookkeeping: a failed write is logged and costs only that answer's
  button).

### F7: the reuse's request row is required
- `_reused` no longer swallows `sqlite3.Error`. A request that cannot be recorded fails with `storage_busy`, which is
  retryable (`_refused`).
- The retry reuses the same stored figure (no author call), and its row is written. A success therefore always has its
  ledger row.

### F8: peeks and the return crumb (spec §6.2)
- The Ask rail's show-me line renders each cited passage as a `§` chip:
  - in this book, the chip peeks, through the return stack, with its crumb;
  - in another book, it opens that book as a detour (`openLibraryHit`), as the tutor's citations do.
- "open" expands the figure and goes there through `peekPassage`, so "back to where I was" appears when the learner had
  scrolled away.
- The server now names each cited passage's source (`source_id`, and the title when missing, read from the stored
  extraction). The chip can therefore open another book, including a tutor goal's given keys.

### F9: registered
- `figure_admission` is in `MODULE_INVENTORY`.
- `figure_admission:GROUNDING_PASSAGES` is registered as structural, `constraint`, with a `keep` rationale: it bounds
  prompt size (spec §8.3, §15). It is never a weight, margin or threshold.

## Claims corrected
- "Every request, built or reused, appends one row" now holds (F7).
- "A goal-only figure lands at its reading position" now holds for reuse too (F3).
- "Held-out rechecks cover the home's spans" now holds after construction (F4).
- "Supplied host references determine the restricted caller" now holds for every origin (F2).
- The stage record's open points 5 and 6 are updated: citation peeks and the return crumb are shipped, not follow-ups
  (F8).

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6` and vitest at `--maxWorkers=4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| New `tests/test_figures_show_me_codex_review.py` against the pre-fix source `11da87ef9` (reproduction) | 24 failed, 3 passed (the 3 are controls) |
| New file + `tests/test_figures_show_me.py` after the fixes | 51 passed |
| Targeted set, 96 files, one run (below) | **7706 passed, 12 skipped** (the owner-vault lane), 0 failed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| `npx vitest run --maxWorkers=4 src/screens/reader src/api` | 88 files, **805 passed** (`showMe.test.tsx`: 9, of which 3 are new; all 3 failed against the pre-fix frontend) |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `-m durability` | not run: no migration, DB or connection code changed |
| DB reference generate / validate | not run: no schema change |

**The targeted set** (pytest `-n 6`):
- **Every test file that names a module changed here** (git grep: `figure_admission`, `text_gaps.sources`, `figure_prediction`,
  `caller_for_question_event`, `parameter_registry`, `figures.service`, `handlers.figures`, `tutor_figure_goal`,
  `_record_explorable_verdicts`).
- **Every figure file:** `test_figure*.py` and `test_figures_*.py`, the new one included.
- **The tutor and Reader-tutor files:** `test_tutor*.py`, `test_reader_tutor*.py` and `test_reader_rw1c*.py`.
- **The learner-text gap files:** `test_learner_text_gaps*.py`, `test_reader_formative_texts.py`, `test_workbench_text_gaps.py`,
  `test_hint_feedback_texts.py` and `test_diagnosis_input_provenance.py`.
- **The contract tests:** `test_architecture.py`, `test_registry_audit.py`, `test_table_roles.py`, `test_desktop_rpc_contract.py`,
  `test_mobile_allowlist.py`, `test_sidecar_registry.py`, `test_sidecar_serializer_snapshot.py`, `test_cli_help_snapshot.py`,
  `test_tracked_fixture_databases.py`, `test_coordinated_migrations.py` and `test_public_tip_guards.py`.
- **Retrieval and reading:** `test_salience_firewall.py`, `test_reading_paths.py` and `test_reader_find_sources_callers.py`.
- **The upgrade-chain files the registry grep selects:** `test_mvp0*_upgrade.py`, `test_method_explicit_upgrade.py` and
  `test_regrade_contract_upgrade.py`.
- **The other files the grep selects:** AD, field, kinship, LP, TE0, tool dispatch and others.

The exact list is the 96 paths passed to that run.

## Re-review (Codex job `20261026-130931-cbjykg`)

Scope: `11da87ef9..reader/rw5d-p1-show-me`. F1 was confirmed fixed. F2 was reopened as a partial fix. F10 is new.
Each was reproduced first with a failing test, then fixed. No live calls. No migration, schema, config or successor change.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Grounding model calls bypass the figure kill switch | confirmed fixed (no change) | `879eacecd` | as above |
| F2 | High | A tutor goal's `offerRef` overwrote a different `hostRef.questionEventId` before the references were validated | fixed | `51a775f36` | `test_f2_rereview_a_valid_goal_offer_with_a_different_host_is_refused` (×2: cold host, open host). It uses a **valid** tutor goal offer with its ledger row. It failed before the fix (DID NOT RAISE: the request started under `reading`). |
| F10 | Medium | Multiple placements interfere with prediction radio controls | fixed | `0e241f5e6` | vitest `RW5d re-review F10: a figure placed under two paragraphs opens at one placement, and its prediction is that placement's` and `RW5d re-review F10: two mounted prediction controls for one figure never share a radio group`. Both failed before the fix: both placements expanded, and both groups were named `prediction-fig_1-0`. |

**F2 fix.** `_request_figure` (`src/learnloop_sidecar/handlers/figures.py`) now passes the supplied `host_ref` and `offer_ref`
to `_host_caller` unchanged. A tutor goal whose `offerRef` differs from `hostRef.questionEventId` is refused there with
"two different answers" (`validation_error`), before any job, retrieval or model call. The request's `host_ref` is set to
the offering answer only after that validation. If both references are the same, or the host is left out, the request
builds as before. The test checks that its stored `host_ref` is `{question_event_id: <offer>}`.

**F10 fix.** Expansion is now tracked per placement, not per figure ID. `useFigures` exposes `expandedKey`
(`figurePlacementKey` = figure ID plus anchor span), and `setExpanded(figure | null)` replaces `setExpanded(figureId)`.
The Ask rail's "open" passes the figure's placement. Only one placement is open at a time, as before.
`PredictionBlock` names each radio group with `useId()`, so no two mounted controls share a native group. Prediction
results stay shared by figure ID (`patchPrediction` is unchanged), and the test shows the result at both placements.

### Re-review gate

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| New F2 test against the pre-fix handler (reproduction) | failed (DID NOT RAISE) |
| `pytest -k f2 tests/test_figures_show_me_codex_review.py` after the fix | 9 passed |
| Targeted pytest set 1 (`-n 6`, below) | **463 passed**, 0 failed |
| Targeted pytest set 2 (`-n 6`, below) | **76 passed**, 0 failed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| New F10 vitest against the pre-fix frontend (reproduction) | 2 failed, 14 passed |
| `npx vitest run --maxWorkers=4 src/screens/reader/figures/` | 8 files, **247 passed** |
| `npx vitest run --maxWorkers=4 src/screens/reader/splitRails.test.tsx` | 1 file, **5 passed** |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `-m durability`, DB reference generate / validate | not run: no migration, DB, connection or schema change |

Every pytest, npm and vitest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

**Targeted pytest set 1:** `tests/test_figures_show_me_codex_review.py`, `tests/test_figures_show_me.py`,
`tests/test_figure_offers.py`, `tests/test_figure_region.py`, `tests/test_figures_codex_review.py`, `tests/test_figures_rpc.py`,
`tests/test_figures_rw5b_fix_round2.py`, `tests/test_figures_rw5b_review.py`, `tests/test_figures_scope_redesign.py`,
`tests/test_plan_first_transport_offer_grants.py`, `tests/test_plan_first_transport_offer_grants_r5.py`,
`tests/test_mobile_allowlist.py`, `tests/test_architecture.py`.

**Targeted pytest set 2:** `tests/test_desktop_rpc_contract.py`, `tests/test_figures_switch_off.py`, `tests/test_figure_predictions.py`,
`tests/test_figure_revisions.py`, `tests/test_figures_final_round.py`, `tests/test_figures_fix_round2.py`,
`tests/test_figures_fix_round3.py`, `tests/test_figures_fix_round4.py`, `tests/test_figures_fix_round5.py`.

**Vitest files:** all 8 under `src/screens/reader/figures/`, including the changed `FigureInline.test.tsx` and
`showMe.test.tsx`. Also `src/screens/reader/splitRails.test.tsx`.
