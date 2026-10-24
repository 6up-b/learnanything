# Reader workbench RW2c: what helps this learner

Stage `reader-rw2c`, branch `reader/rw2c` in `learnanything-dl2`, base `7e7bdff1b` (the RW5a landing tip, migration
head 217). Spec: `docs/specs/spec_reader_workbench_v1.md` §1 (RW2c), §5.10, §5.4's evidence table, §11 ("RW2c's help
outcomes are pure reads"), G39, G40, §13's test list.

## 0. Plan (written before the code)

**No migration, no new table, no new reveal kind, no new `interaction_events` kind.** Everything is a read of
existing rows, a context line, a display, a learner pick, or a row in the existing `help_assists` table with the
kinds migration 210 already carries (`bridge`, `example`, `compare_methods`) and the columns it already has
(`options_json`, `probabilities_json`, `drawn_option_json`, `propensity`, `seed`, `policy_version`).

1. **`help_outcomes` (G39), a pure read** — new `learnloop/workbench/help_outcomes.py`:
   `help_outcomes(sqlite_path, facet_ids, as_of, *, item_facets) -> HelpOutcomesV1`. Opens the database read-only,
   reads only rows stamped at or before `as_of`, and is deterministic (no clock, no model, sorted output):
   * per help kind (a hint kind with its strategy and levels; a passage role: the bridge, the worked example; a
     comparison; and the sources spec's S5 interventions by kind) on each requested facet: shown; the immediate
     continuation (the next shown check of the same problem, with no other hint shown between, found the first
     questionable step gone or moved on: the workbench's own placement, which the hint service hands to the Reader,
     H2b §9); "doesn't connect" replies (the service's `hint_fit` ledger rows); the attempt's grade; the later
     independent outcome on the same facets (the next attempt with `hints_used = 0`, not primed) with how many have
     no later observation yet;
   * S5's `retrieval_interventions` + `retrieval_intervention_outcomes` are read for retrieval-supported help
     (R_next, R_cold with its censoring) instead of re-deriving them; an outcome whose attempt is after `as_of` reads
     as pending; absent tables read as absent;
   * where the work goes off: per facet, the check's error-kind guesses on first questionable steps (labelled
     guesses) and the diagnoser's typed causes at Submit (`causal_class`, `operation`, the registry match's id;
     never a statement), with counts and dates;
   * `lines_for(outcomes, facet_ids)` gives the typed lines (kinds, levels, counts, outcomes; never text), labelled
     "what preceded recovery for you".
2. **Lines to the hint writer and chooser** — `WorkbenchHintContext` gains `help_outcomes` (a tuple of typed lines,
   default empty); `prompt_block()` and `decider_extra()` add a `help_outcomes` key only when it is non-empty, so with
   `workbench.help_outcomes_enabled` off (or no history) the writer's prompt and the chooser's state are
   byte-identical. `ladder.hint_context` fills it when the switch is on.
3. **The logged passage draw** — new `learnloop/workbench/passage_draw.py`: a uniform draw (seeded, reproducible)
   between two or more passages that all passed the judge (for the worked example, within the best verdict class,
   so `follows_learner_route` stays first). The bridge and the example rows carry the options, probabilities, drawn
   option, propensity and seed. "another passage" (`workbench.another_passage`) shows the next option, no search, as
   a `learner_pick` row (counted by nothing, not a call). Switch `workbench.passage_draw_enabled`; off, the bridge
   takes the first passage exactly as before.
4. **The worked example in your route (G40)** — new `learnloop/workbench/route_example.py` over the sources spec's
   `find_sources(intent="worked_example", item=…, learner_work_md=…)` under the workbench's server-derived caller
   (`assisted_practice` for the item: no exercise, solution or linked block, answer overlap withheld, exam material
   withheld), with a second leak and exam filter on what comes back. After a shown level-3+ hint in the Reader (in
   the background, beside the bridge) or on "Show me a similar example" (`workbench.show_example`). A row
   `assist_kind = 'example'`, written before the search (one of the problem's calls), counted by nothing (the book's
   own rule counts a peek). Without S3 (no `worked_example` intent, or the source service off) it is absent: the
   offer is not shown and nothing is searched. Switch `workbench.examples_enabled`.
5. **Compare methods (G40)** — new `learnloop/workbench/compare_methods.py`: after a correct Submit of a workbench
   problem, the feedback screen offers "Compare with the book's method". The reference is read by id: the item's
   key, or, when the item's key status is `book_solution`, the book's solution passage through `canonical_exercise`
   and the check's recorded span ids (exam material never). Before anything is shown, one `reveal_events` row of the
   existing kind on the ITEM (`answer_display`, or `source_review` for the book's passage; `attempt_id` NULL, never
   the submitted attempt) is written in the same transaction as the `compare_methods` row. The one-line-per-difference
   comparison runs on `workbench_check`'s route (its `CheckRoute`, `PaidCalls`, the workbench's caps; no new route).
   A valid different route is named valid. Switch `workbench.compare_methods_enabled`.
6. **Config**: `workbench.help_outcomes_enabled`, `.examples_enabled`, `.compare_methods_enabled`,
   `.passage_draw_enabled` (all `true`, the spec's defaults), classified in the parameter registry; the app config DTO
   carries each only while on.
7. **UI** in new components (`screens/workbench/RouteExample.tsx`, `screens/feedback/CompareMethods.tsx`), narrow
   edits in `StepHints.tsx`, `useWorkbenchHelp.ts`, `FeedbackScreen.tsx`.
8. **Tests**: `test_help_outcomes.py` (G39, replay determinism, S5 faked and absent, leak), `test_workbench_passage_draw.py`,
   `test_workbench_route_example.py` (G40, faked `find_sources`), `test_compare_methods.py` (G40, by id, reveal row,
   cold lane), `test_rw2c_switch_off.py` (byte-identical writer/chooser inputs, workbench and feedback payloads with all
   four off), parameter-registry classification; vitest for the new components and the switch-off pins.

## 1. What was built

The stage was interrupted once during implementation (session restart, 2026-10-21); the resumed run inspected the
uncommitted partial work (config switches, the `help_assists` store's passage and compare helpers, the four new
`learnloop/workbench/` modules, the RPC adapter, the Tauri passthroughs, the hint-context lines and the backend
tests), kept all of it, fixed what it found (below), and added the frontend, the remaining pins and this record.

**No migration, no new table, no new reveal kind, no new `interaction_events` kind, no new model route, no new
Codex call path.** Migration head stays 217.

1. **`help_outcomes` (G39)** — `src/learnloop/workbench/help_outcomes.py`. `help_outcomes(repository | path,
   facet_ids, as_of, *, item_facets) -> HelpOutcomesV1`: opens the database read-only, reads only rows stamped at or
   before `as_of`, no clock, no model, sorted output. Per help kind on each facet (a hint kind with its strategy
   slug and levels; a bridge or worked example by passage role; a comparison; S5's interventions by kind):
   `shown`, `continuation` (the next shown check of the same problem with no other hint between found a new valid
   step: `continued` / `not_continued`, else `more_help` / `no_later_check`), `attempt` (the grade, `held` for a
   held grade, `not_submitted`), `later_independent` (the next attempt on the facet with `hints_used = 0` and not
   primed: `pass` / `fail` / `ungraded` / `held`, or `pending`), `doesnt_connect` (the hint service's own `hint_fit`
   replies by shortcut). S5's `retrieval_interventions` + `retrieval_intervention_outcomes` are read for
   retrieval-supported help instead of a second derivation (a cold attempt after `as_of` reads as pending; absent
   tables read as `absent`). **Where the work goes off**: per facet, the check's error-kind guesses on first
   questionable steps (labelled guesses) and the diagnoser's typed causes at Submit on the workbench's submitted
   problems (`operation` or `causal_class` slug, `misconception:<registry id>`; never a statement or the analysis).
   Labelled "what preceded recovery for you (associations, not what works)". Stored step verdicts are read through
   `learnloop.symbolic_view.verdict_records` (the one accessor; only the verdict is used).
   `lines_for(outcomes)` gives typed lines only (the keys are pinned): a label line, at most 3 help kinds per facet
   and 4 in all (most shown, then most observed outcomes, then most recent), then the goes-off lines. A strategy
   that is not a slug is dropped (free text never travels).
2. **Lines to the hint writer and the chooser** — `WorkbenchHintContext.help_outcomes` (default `()`);
   `prompt_block()` adds `help_outcomes` and a one-sentence `help_outcomes_rule` ("associations, not what works …
   never mention them") and `decider_extra()` adds `help_outcomes`, **only when non-empty**. `ladder.hint_context`
   fills it from `lines_for_item` while `workbench.help_outcomes_enabled` is on; a failed read logs and gives `()`
   (context never blocks a hint).
3. **The logged passage draw** — `src/learnloop/workbench/passage_draw.py`. A uniform draw from a seeded
   `random.Random` over at most 3 options; the bridge draws only when T6's manifest says `retrieved_verified`
   (every span passed the listwise judge), the worked example only within the best verdict class
   (`follows_learner_route` before `worked_example`, so a route-following passage is never displaced). Logged on the
   bridge / example row in the columns migration 210 already has: `options_json` (ids and labels, never text),
   `probabilities_json`, `drawn_option_json`, `propensity` (= 1/n, the draw probability), `seed`, `policy_version`
   (`passage-draw-v1`). "another passage" (`workbench.another_passage`) writes a new row of the same kind with
   `chooser = 'learner_pick'`, no propensity or seed, `counted_by` NULL, no search and no call (the workbench's call
   count excludes picks). Resume shows the latest pick with its options.
4. **The worked example in your route (G40)** — `src/learnloop/workbench/route_example.py`. The sources spec's
   `propose_sources(..., intent="worked_example", learner_work_md=<numbered steps>)` under the workbench session's
   server-derived caller (`caller_for(..., context="practice", item_id=…)` → `assisted_practice`; a cold
   administration derives cold and retrieves nothing), inside the service's own daily cap. Kept only when the
   verification status is `verified`/`cached`; a second filter drops `exercise`/`solution` roles, any span whose
   text overlaps the item's key (`span_leaks_expected`) and exam material (`exam_withheld`). Runs in the background
   after a shown level-3+ hint in a Reader problem (`exampleJobId` on the hint result; never delays the hint) and on
   "show me a similar example" (`workbench.show_example`). Its `example` row is written BEFORE the search in the
   transaction that checks `workbench.max_calls_per_session`; it counts nothing (the book's own rule counts a
   peek). Without S3 (no `worked_example` intent, or the source service / retrieval switched off) it is **absent**:
   nothing written, nothing searched, `exampleJobId` null, `examplesAvailable` false, the RPC refuses
   `examples_unavailable`. On main S3 is present, so no "record and skip" fallback was needed.
5. **Compare methods (G40)** — `src/learnloop/workbench/compare_methods.py`. Offered (`workbench.compare_offer`)
   only after a correct (≥ 0.999), unheld Submit of a workbench problem, never for an exam/held-out item (the shared
   `exam_material` / `item_exam_status` and the reserved pool). The reference is read by id: the item's key, or,
   when `effective_key_status` is `book_solution`, the book's passage through `canonical_exercise` and the span ids
   the key check recorded (`blocks_by_key`; exam material anywhere → the key instead). Opening
   (`workbench.compare_methods`) writes the `compare_methods` row and ONE `reveal_events` row ON THE ITEM
   (`answer_display`, or `source_review` for the book's passage; `attempt_id` NULL; basis
   `compare_methods:<assist id>`; stamped no earlier than the attempt's second + 1 so the next window sees it) in
   one transaction, before the reference is returned; a second open returns the first (one reveal). The lines run
   on `workbench_check`'s `CheckRoute` (its `PaidCalls`, receipts, per-session and daily caps) with a new output
   model and prompt version (`workbench_compare_methods.v1`) — no new route; a line naming a step that does not
   exist is dropped; a valid different route gets "Your route is valid — a different method from the reference."
6. **Config** — `[workbench] help_outcomes_enabled`, `examples_enabled`, `compare_methods_enabled`,
   `passage_draw_enabled`, all `true` (the spec's defaults), classified in the parameter registry
   (structural / operational). The app config DTO carries `examples`, `compareMethods`, `passageDraw` under
   `workbench.help` only while each is on. Defaults snapshots for mvp-0.9 … mvp-0.29 recomputed (the effective
   config gains the keys; no successor, no serving change).
7. **RPCs** (desktop only, pinned in `tests/test_mobile_allowlist.py`, Tauri passthroughs in `commands.rs` /
   `main.rs`): `workbench.show_example`, `workbench.another_passage`, `workbench.compare_offer`,
   `workbench.compare_methods`; `workbench.help_job` reads the `example` and `compare` jobs; `workbench.help_state`
   gains `examples_available` / `examples` only while examples are on; hint views gain `example` only while on;
   bridge views gain `alternatives` / `option_id` / `draw_assist_id` only on a row that logged a draw.
8. **UI** — new `screens/workbench/RouteExample.tsx` (the `useRouteExamples` hook, `PassageExtras` under a hint,
   `ShowMeExample` under the steps) and `screens/feedback/CompareMethods.tsx`; narrow edits: `StepHints.tsx` (an
   optional `extras` slot after the bridge line), `useWorkbenchHelp.ts` (two optional callbacks, the bridge's draw
   fields only when logged), `Workbench.tsx` (the hook, two `HintCard` props, one `ShowMeExample`),
   `FeedbackScreen.tsx` (one gated `<CompareMethods>` after `FeedbackSurface`, simple view), `algoConfig.ts` (three
   optional flags present only while on), `api/client.ts`, `api/dto.ts`.

### Fixes made on resume (each with a test that fails on the partial work)

* `lines_for` rebound its ranking function's name to an int inside the loop, so an item with two facets raised
  `TypeError` on the second facet's sort (every hint request on such an item would have lost its lines through the
  ladder's catch). Fixed; `test_lines_for_ranks_every_requested_facet`.
* `help_outcomes` read `step_verdicts_json` raw, outside the one symbolic accessor
  (`test_architecture.py::test_stored_symbolic_results_are_read_only_through_the_one_accessor` failed); now through
  `verdict_records`, and the module is added to the architecture test's accessor-reader list.
* `tests/test_rw2c_switch_off.py` copies its helper script with `shutil.copy`; recorded in
  `tests/test_sqlite_file_copies.py`'s audit list (not a database).
* **The example could displace the bridge under the per-problem cap.** With threaded jobs the example after a
  hint (started beside the bridge) could take the problem's last call before RW2b's bridge took its place, so the
  bridge read `session_capped` (found by `test_reader_rw2b_review.py::test_f9_…`). The example now waits for its
  sibling bridge job (`BRIDGE_WAIT_SECONDS = 60`) before its own reservation; under the cap it is the example that
  reads `session_capped`. `test_workbench_route_example.py::test_under_the_problems_cap_the_example_never_displaces_the_bridge`
  (a slow-starting bridge, threaded jobs, one call) fails with the wait disabled and passes with it.
* Pins re-recorded **only for this stage's keys**: `test_workbench_help_kill_switch.py` (the on-DTO gains the three
  RW2c flags), `test_reader_rw2b_review.py::test_f11` (the RW2b key set excludes RW2c's four, which
  `test_rw2c_switch_off.py` classifies), `test_reader_rw2b_review.py::test_f9_the_search_takes_its_place…` (it
  stubs the bridge and runs it by hand, so RW2c's sibling example is switched off there; its ordering is pinned
  above), and `test_library_exercises.py`'s held-out contract gains a value for `assist_id` (so every RW2c RPC is
  now in that no-held-out-statement sweep).
* Frontend (new in this run): "another passage" showed under a bridge with `passageDraw` off when a restored
  view carried alternatives; it is now gated on the switch (`RouteExample.test.tsx`, "with the draw off …").

## 2. Deviations

* **The example's query** is the shown hint's own text plus the step it is about (the writer wrote that hint from
  the learner's route and the questionable step), not a separate writer-authored query: a second writer call per
  example would add a call path through the hint service for no gain the verifier does not already give
  (`learner_work_md` carries the route). On "show me" the query is the focused step.
* **Compare methods in the classic feedback view** is not added (the simple view is the default; classic is the
  legacy screen kept byte-identical).
* **The S5 continuation** uses S5's next-attempt fields (`next_correctness ≥ 0.5`, S5's own report threshold) as
  the "immediate continuation" for retrieval help, since S5 records no workbench check.
* **Figures, tutor exchanges and library asks** (named in §5.10's input list) are not yet read as help kinds:
  figure views and tutor offers have no facet-bound outcome row to join today without a second derivation; recorded
  as an open item for RW2d/RW6b rather than approximated.

## 3. Leak control and evidence (binding notes 1–3)

* No write to `practice_attempts`, mastery, scheduling or certification anywhere in the stage
  (a grep of the changed and new `src/` files for `practice_attempts`, `INSERT` and `UPDATE` finds two SELECTs
  and no write to it). Compare methods writes only the
  existing reveal kinds, on the item, `attempt_id` NULL (`test_compare_methods.py`).
* Writer/chooser lines are typed records only; the pinned key sets and the leak test check the item's answer,
  reference fragments, the diagnoser's statement and analysis never appear (`test_help_outcomes.py`).
* The example never reproduces the answer (policy + second filter) and never surfaces exam material
  (`test_workbench_route_example.py`); compare methods is never offered on exam material and never shows an exam
  passage (`test_compare_methods.py`).
* The only model call added is compare methods' line, on the existing `workbench_check` route through `CheckRoute`
  / `PaidCalls`; the example search is the sources spec's existing `source_rerank` path. No new Codex call path.
* **No live or paid calls** were made: everything model-backed is tested with fakes; no CLI or app run against any
  vault (no manual smoke run was needed). One local text-edit script (frontend `api/client.ts`) ran as plain
  `python3` rather than under the `env -i` isolation before the rule was applied; it imported nothing from the app
  and made no network call. Every later script ran under `env -i` with empty HOME / CODEX_HOME /
  LEARNLOOP_CONFIG_DIR.

## 4. Files

New: `src/learnloop/workbench/help_outcomes.py`, `passage_draw.py`, `route_example.py`, `compare_methods.py`;
`src/learnloop_sidecar/handlers/workbench_rw2c.py`; `apps/learnloop-tauri/src/screens/workbench/RouteExample.tsx`
(+ `.test.tsx`), `apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx` (+ `.test.tsx`);
`tests/rw2c_base_sequence.py`, `tests/test_help_outcomes.py`, `tests/test_workbench_passage_draw.py`,
`tests/test_workbench_route_example.py`, `tests/test_compare_methods.py`, `tests/test_rw2c_switch_off.py`; this file.

Changed: `src/learnloop/config/schema.py`, `config/template.py` (defaults snapshots), `params/parameter_registry.py`,
`db/stores/help_assists.py` (`settle_bridge` / `mark_bridge_shown` take the passage kind; `settle_compare`,
`compare_rows_for`, `PASSAGE_KINDS`), `hints/workbench.py` (the lines in the writer block and chooser state),
`workbench/bridge.py` (the draw), `workbench/check.py` (`session_calls_on` counts examples, not picks;
`CheckRoute.ask` takes an output model and prompt version), `workbench/ladder.py` (the lines, example views,
`standalone_examples`, bridge draw fields); `learnloop_sidecar/context.py` (config DTO flags),
`handlers/__init__.py`, `handlers/workbench_help.py` (example/compare jobs, the example after a hint, help-state
examples, the draw on the bridge); `apps/learnloop-tauri/src-tauri/src/commands.rs`, `main.rs`;
`apps/learnloop-tauri/src/api/client.ts`, `api/dto.ts`, `app/algoConfig.ts`, `screens/FeedbackScreen.tsx`,
`screens/workbench/StepHints.tsx`, `useWorkbenchHelp.ts`, `Workbench.tsx`,
`screens/FeedbackScreen.phase4.test.tsx` (two RW2c tests appended); `tests/test_mobile_allowlist.py`,
`tests/test_architecture.py` (accessor reader list), `tests/test_sqlite_file_copies.py` (audit entry),
`tests/test_workbench_help_kill_switch.py`, `tests/test_reader_rw2b_review.py`, `tests/test_library_exercises.py`
(re-recorded for RW2c's keys only, §1).

## 5. Gate (targeted; the full suite runs once, in the landing gate)

Environment: `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`, `TMPDIR=<worktree>/fixtures-local/tmp`.
No migration, no DB/connection change, no schema change (so no head fixture, table_roles or DB reference work).

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 29 kept, 0 broken |
| targeted pytest, `-n 8`, the 89 files below | **1917 passed, 1 skipped** (RW4e's base-tree-only golden recorder) |
| `uv run pytest -m durability tests/test_help_assists_schema.py` (the store module changed; no migration) | 1 passed |
| `npm install`, `npm run typecheck` | clean |
| `npx vitest run` on the 20 files below | **257 passed** |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, no errors |

**Pytest files (89).** Contract pins: `test_sqlite_file_copies`, `test_cli_help_snapshot`,
`test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`,
`test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_config_refactor`
(defaults snapshots). RW2c: `test_help_outcomes` (11), `test_workbench_passage_draw` (6),
`test_workbench_route_example` (9), `test_compare_methods` (8), `test_rw2c_switch_off` (4, incl. the
byte-identical run of the base `7e7bdff1b` archive). RW2b/H3 and the hint service: `test_reader_rw2b_review`,
`test_reader_rw2b_fix3` … `fix15`, `test_workbench_assistance`, `_check`, `_check_map`, `_chooser`,
`_discriminate`, `_help_kill_switch`, `_hint_service`, `_hints`, `_in_session_gaps`, `_report`, `_step_graph`,
`_text_gaps`, `_trace`, `test_hint_service`, `test_hint_h2a_review` (+ rounds 2–4), `test_hint_h2b_review`,
`_rereview`, `_fix3`, `_fix4`, `test_hint_kill_switch`, `test_hint_report`, `test_hint_telemetry`,
`test_hint_feedback_texts`, `test_hint_feedback_widening`, `test_hint_authored_reveal_ruling`,
`test_help_assists_schema`, `test_approach_maps`, `test_approach_map_replay`. RW4b: `test_reader_rw4b_fix6`,
`test_reader_rw4b_admission_idempotency`, `test_dl2_rw4b_keyed_pick_check`, `test_library_exercises`,
`test_rw4_kill_switches`, `test_exam_protection`, `test_exam_protection_review`, `test_reader_intentions`.
Other readers of touched modules and the switch-off pins: `test_ad1_attempt_columns`, `test_ad1_migration`,
`test_adaptive_difficulty_ad1`, `test_figure_predictions`, `test_figures_migration`, `test_library_asks_migration`,
`test_reader_recap`, `test_reader_recap_review`, `test_reader_wrap_up`, `test_ux_phase4_feedback`,
`test_compare_keep_switch_off`, `test_figures_switch_off`, `test_reader_rw3b_switch_off`,
`test_reader_tutor_switch_off`, `test_roles_switch_off`, `test_roles_switch_off_legacy_parity`. Reveals, the cold
lane and the sources spec: `test_reveal_ledger`, `test_remediation_cold_retry`, `test_serve_eligibility`,
`test_find_sources_intents`, `test_reader_find_sources_callers`.

**Vitest files (20).** New: `screens/workbench/RouteExample.test.tsx` (8), `screens/feedback/CompareMethods.test.tsx`
(4). Touched or affected: `screens/FeedbackScreen.phase4.test.tsx` (+2 RW2c), `FeedbackScreen.test.tsx`,
`FeedbackScreen.liveQueue.test.tsx`, `FeedbackScreen.plan.test.tsx`, `screens/workbench/` (`HelpLadder`,
`Workbench`, `reviewFixes`, `switchOff`, `symbolicOff`, `fingerprint`, `stepModel`), `screens/feedback/answerExposure`
(+ `.shell`), `ReaderScreen.workbench`, `PracticeScreen.workbench`, `reader/readerWorkbenchExercise`,
`reader/readerWorkbenchQueue`, `app/practiceFeedback`. The RW2b vitest files are the frontend switch-off pins
(their api mocks name only RW2b's calls and their config carries no RW2c key); `RouteExample.test.tsx`'s "off" test
and the phase4 "RW2c off" test pin it explicitly.

**For the landing gate.** With `workbench.examples_enabled` on by default, every shown level-3+ Reader hint in the
suite now also starts a background example search through the sources spec's `propose_sources`. In a test vault
with no sources it returns `none` before any verification (a probe showed no model-call receipt); with sources
and no fake for `source_rerank`, its verification resolves the vault's provider like the tutor's retrieval does.
If the full suite shows receipt-count drift in Reader hint tests, that is the cause.

## 6. Open questions (with the defaults taken)

1. **Draw size**: at most 3 options per draw (`MAX_OPTIONS`). Default 3: enough variation for the report, one
   or two clicks to see all. Owner may raise it.
2. **Help-outcome line budget**: 3 kinds per facet, 4 in all, plus goes-off lines. Default as stated (prompt-size
   bound, ~0.5K tokens).
3. **"Later independent"** counts the next attempt on the facet with no hint and not primed, whatever its surface.
   A RW6b follow-up will be one such attempt; RW6b may want its own label. Default: one definition.
4. **Example trigger**: level 3 or higher (`MIN_HINT_LEVEL`), Reader problems only (a practice-screen workbench has
   no book beside it). Default per §5.10.
5. **Compare offer on a "valid but partial" route**: offered only at correctness ≥ 0.999 (the attempt window's
   "correct"). Default per §5.10 ("after a correct Submit").
6. **Classic feedback view**: no compare offer (the simple view is the default). Default: leave classic as it is.

## 7. Friction notes for RW2d and RW6b

* **RW2d** (workbench signals in the learner field): `help_outcomes(...).as_dict()` is the read to adapt; its
  `goes_off` per facet (guesses vs diagnosed causes, kept apart) is the natural signal, and its `as_of` makes
  replay straightforward. Do not reuse `lines_for` (a prompt-size view). Passage draws carry `propensity`/`seed`
  in `help_assists`; the learner picks (`chooser = 'learner_pick'`) must be excluded from any IPS estimate (they
  are choices among a draw's options, not draws).
* **RW6b** (cold follow-ups, family exclusion): compare methods' reveal is an ordinary `reveal_events` row on the
  item (basis `compare_methods:<assist id>`), so the family exclusion reads it with no change; the cold lane test
  here (`test_compare_methods.py`) shows `cold_check_decision` deferring after it. A RW6b follow-up's outcome
  will appear in `later_independent` automatically (it is an unassisted attempt on the facet).
* `help_outcomes` reads `practice_attempts` and `judgment_ledger` in full per call (n = 1 scale, fine today);
  RW6b's report may want a facet-filtered query if vaults grow.
* Figures, tutor exchanges and library asks are not yet help kinds in `help_outcomes` (§2); RW6b's narrative is
  the first consumer that would want them.

## 8. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw2c-onto-main`, cut from main at `2cff2c1f4` (the
second security landing: the Codex tool lockdown and its hardening rounds 2-3, every Codex turn tool-free; migration
head 217 with `migration_head_217`, which holds 215, 216 and 217 and no 214). The stage tip is `56b8567ab` (base
`7e7bdff1b`), unchanged. The orchestrator's final verify on `56b8567ab` (an Opus adversarial reviewer; Codex is out of
quota) was clean. Main was neither fast-forwarded nor pushed here.

### Commits and conflicts

- `1d972a6d1`: the `--no-ff` merge of `reader/rw2c` onto `2cff2c1f4`. **No conflicts.** Since the stage's base, main
  gained only the security stage (the lockdown in `ai/providers/codex*.py`, `codex_lockdown.py`, its tests and
  records). The two sides share no file: `config/template.py`, the parameter registry, `test_mobile_allowlist.py`,
  the CLI help, the RPC pins, the workbench and feedback screens, the hint service, the S5 substrate, `dto.ts` /
  `client.ts` and `commands.rs` / `main.rs` are RW2c's changes alone.
- `55faad94d`: **RW2c's comparison lines pinned to the lockdown.** `tests/test_codex_tool_lockdown.py` gains a
  `compare_methods` shape that drives `CheckRoute.ask` (the workbench check's route object: `PaidCalls`, receipts,
  caps) with the comparison's own prompt (`compare_methods.build_prompt`) and prompt version
  (`workbench_compare_methods.v1`), exactly as `compare_methods.compare_lines` asks it, through the locked-down
  turn: `deny_all` on the thread and turn, the decline-all approval handler, the isolated empty cwd, every tool-bearing
  feature off (7 shapes pass). RW2c adds no new call path: the worked-example search is the sources spec's existing
  `source_rerank` path, already covered by the `paid_calls` shape.
- `395b4bb59`: the regeneration (below). **This is the gate head.**
- This record (docs only).

### Regeneration (`395b4bb59`)

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head **217**,
  **339** table notes, **956** configuration leaves in **69** sections (RW2c's four `[workbench]` switches; the
  workbench section has 14 leaves, was 10). The two prose counts (`Configuration.md`, `Database.md`) were updated from
  952. Every other change is the notes' `source_commit` provenance and the new source/test paths on the
  `help_assists`, `workbench_sessions` and `workbench_steps` notes.
- **Defaults snapshots.** Template `.pyc` cleared, run with `-B` under `env -i`: all **20** entries already match
  (`0 mismatches`; the stage recomputed them and main's security stage changed no default). Unchanged.
- **CLI help snapshot, RPC pins, mobile allowlist, serializer snapshot**: unchanged (their tests pass in the full
  suite).
- **`validate_vault.py`**: passes (1,142 notes, 1,140/1,140 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **999** issues (987 at the RW5a
  landing; RW2c's and the security stage's new modules have no module notes).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0); `TMPDIR` was merge2's
`fixtures-local/tmp`; every later command `uv run --no-sync`. Both suite lanes ran on `395b4bb59` under
`flock /tmp/learnloop-fullsuite.lock` (logs in `fixtures-local/rw2c-landing/`). Other stages' worktrees and processes
(T1 in `learnanything-plan` among them, whose test run shared the machine; load average 35-55) were not touched. Every
test uses fakes. **This is the first full run over RW2c's code.** A first full run was cut by a session restart
(`fullsuite-cut.log`); the run below is the one that counts.

| Check | Result |
|---|---|
| `lint-imports --no-cache` | **30 kept**, 0 broken (as at the second security landing) |
| full suite `pytest -n auto` | **15,689 passed, 1 failed, 2 skipped, 2 xfailed** (41 min 3 s). The failure, `test_reading_request_sweep.py::test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts` ("the deferred request was stranded"), is a `_wait_for` timeout under machine load in the reading-build sweep, which RW2c does not touch: rerun alone 3 times, **14 passed** each time |
| `pytest -m durability` | **119 passed**, 15,575 deselected (2 min 28 s) |
| `npm install`, `npm run typecheck` | ok; clean |
| `npm test` (the whole vitest run) | **173 files, 1,489 tests passed**, no unhandled error (the second security landing: 1,469) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (RW2c's four passthroughs) |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend runs; no `-wal` / `-shm` beside a fixture |

An earlier `-n 8` run of the whole suite (meant as a pin run; `prelim-fullsuite-n8.log`, not under the lock) had one
different load failure of the same kind, `test_reading_hardening_2_fixes.py::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`
(a 60 s wait): alone 3 times, 5 passed each time. **No real failure, so no landing fix.**

### Parity (backup-API copies; no model call was made)

**Setup.** Scripts in `fixtures-local/landing-rw2c/scripts/`, adapted from the RW5a landing's; new: `ab_rw2c.sh`,
`c_rw2c.sh`, `rw2c_run.py`, `bind.py`, `ccmp_rw2c.py`, `sdiff.py`, `rowpeek.py`.
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once with `copy_tree_with_databases`
  from the main checkout into `fixtures-local/landing-rw2c/orig/`; every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both start at schema 165, label `mvp-0.8`, 0 receipts.
- **Code.** Main's is `git archive 2cff2c1f4`; the merge's `git archive 395b4bb59`.
- **Environment.** `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR` and `LANG`; the
  three directories empty, and empty afterwards.
- **Routes.** `neutralize3.py` under each code: every route field to `127.0.0.1:9` (59 on both; RW2c adds no route),
  the active provider to that loopback profile with no fallback, query rewrite / rerank / dense / embeddings /
  learner-text gaps off, `build_on_serve` and outcome placement off. `routes.py` resolved 62 `AITask`s on both;
  nothing outside the loopback profiles except the disabled, keyless `embedding`; `workbench_check`, `hint_writer`
  and `source_rerank` on `blackhole` (`openai_chat`, `http://127.0.0.1:9/v1`).

**(a) No schema change**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main / merge | 165 → 217, 51 applied, on both | the same |
| schema, main vs merge | **identical**: 1,451 objects each, none on one side only, no SQL differs | **identical** (1,450) |
| rows of every table (344), all columns | **identical** (16,542 rows); `schema_migrations` 203 rows each, differing only in `applied_at` | **identical** (7,640 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both | the same |
| `rebuild --shadow --json` | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json` | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes.** The merge ran at its defaults (all four RW2c switches **on**), frozen clock 2026-10-19
09:00 UTC: certification with recipe gaps and curves; the Today queue (no session, session, greedy); the daily plan
(read, served twice, read again).

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` | cert (132,860 bytes), Today (504,488), plan (546): **byte-identical** | cert (17,494), Today (709,910), plan (546): **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; rc 0), opened by each code | cert (129,651) and Today (528,665) **byte-identical** | cert (17,495) and Today (741,269) **byte-identical** |
| then to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; rc 0) | cert and Today **byte-identical** | the same |
| the daily plan at mvp-0.27 and mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three fields, and from the merge's in exactly these three (`plan_repeat.sh`): run-to-run noise, as at the earlier landings | the same |

**(c) The real sidecar** over stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC (`sidecar_clock.py`), on copies of
main's mvp-0.29 vaults; driver `rw2c_run.py`, compared by `ccmp_rw2c.py` (every response, ids, digests, timestamps and
the vault path normalised) and `sdiff.py`. Runs: (i) `cm` main's code; (ii) `coff` the merge with the four RW2c
switches off; (iii) `cdef` the merge at its defaults. Items: probability `pi_prob_derive_complement`, linear_algebra
`pi_axiom_closure_recall_01`.
- **Phase a** (one sidecar): `initialize`; `get_config`; `set_grading_provider manual`; `start_session`; a Reader
  workbench problem (`workbench.open` origin `reader`, entry `work_through`) with the steps of a correct answer (3 /
  2); `workbench.help_state`; `workbench.check` (polled); `workbench.request_help` at level 3 (polled, then its
  bridge and example jobs when named); `workbench.show_example` on the last step; `workbench.help_state`;
  `workbench.get`; `workbench.submit`; then the answer box: `submit_attempt` with a full self-grade (correctness 1.0),
  acknowledged; `workbench.compare_offer` on that attempt; `get_session`; `shutdown`.
- **Between the phases** (`bind.py`, each side's own code): the workbench problem is marked submitted with that
  correct attempt through `reader.workbench.mark_submitted`, what `workbench.submit` does after a graded attempt. This
  stands in for a correct workbench Submit, which needs an AI grader (manual grading refuses
  `grading_fallback_required`, and every route is unreachable).
- **Phase b** (a second sidecar): `initialize`; `workbench.compare_offer`; `workbench.compare_methods`, its lines job
  polled; `workbench.compare_methods` again; `workbench.help_state`; `shutdown`.
- Then `learnloop hints report --json` and `learnloop hints report --surface workbench --json` on each copy.

| Step | (i) main vs (ii) switches off | (iii) defaults: every difference from (i) |
|---|---|---|
| `initialize` | **RW2c's four RPCs register while off** (429 → 433 methods); nothing else | the same |
| `get_config` | **identical** (the DTO carries no RW2c flag while off) | `workbench.help` gains `examples`, `compareMethods`, `passageDraw` (all true) |
| `workbench.help_state` (twice) | **identical** | gains `examplesAvailable: true` and `examples: []`; the hint view gains `example: null` |
| `workbench.check` | **identical**: refused before any request, `unpriced` ("A metered check route needs workbench.price_per_million.") | identical |
| `workbench.request_help` (level 3) and its bridge | **identical**: the item's authored hint at level 3 (the writer route refused `unpriced`), its bridge `none` ("no matching step in your books for this hint") | the hint result gains `exampleJobId`; that job ends `none` ("no worked example in your books fits this step yet"), with nothing searched beyond the vault's empty retrieval |
| `workbench.show_example` | (i) `method_not_found`; (ii) refused `examples_unavailable` | a job, `none` (the same line) |
| `workbench.get`, `workbench.submit` | **identical**: the submit refused `grading_fallback_required`, the problem stays open | identical |
| the answer-box attempt | **identical** (correctness 1.0) | identical |
| `workbench.compare_offer`, answer-box attempt | (i) `method_not_found`; (ii) `{available: false, reason: disabled}` | `{available: false, reason: not_a_workbench_submit}` |
| `workbench.compare_offer`, workbench attempt | (i) `method_not_found`; (ii) `disabled` | `{available: true, referenceKind: item_key, label: "Compare with the book's method"}` |
| `workbench.compare_methods` (twice) | (i) `method_not_found`; (ii) refused `compare_unavailable` (`reason: disabled`) | the comparison (the item's key beside the learner's steps, `revealId`), its lines job ending **`unpriced`** before any request; the second open returns **the same comparison and reveal** (and starts one more lines job, since the first ended without lines: review F7's rule), which also ends `unpriced` |
| `hints report --json` (both surfaces) | **identical** | gains the `compare_methods` kind (shown 1, chooser `none`, no attempt), so `totals.shown` 1 → 2 and `totals.unattached` 0 → 1; the `workbench` section is identical |

So (i) and (ii) are identical call by call apart from the method registry and the refusal codes of RW2c's own RPCs.

**Rows the runs added** (over the merge-opened copy, `deltas.py` and `rowpeek.py`), the same on both vaults:
- **Attempt evidence is unchanged:** the one attempt and its rows in every evidence table (`practice_attempts`,
  `activity_observations`, `raw_grade_events`, `learning_object_mastery`, the scheduling and certification
  projections) are identical across (i)-(iii) once ids are normalised.
- **Reveals:** (i) and (ii) none; (iii) **exactly one**, `answer_display` on the item, `attempt_id` NULL, basis
  `compare_methods:<assist id>`, stamped 2026-10-19T09:00:01Z (the attempt's second + 1).
- **`help_assists`:** (i) and (ii) the hint (`authored`, `fallback`, shown, counted by the server) and its bridge (not
  shown); (iii) those two plus two `example` rows (after the hint and from "show me"; not shown, counted by nothing,
  no draw logged) and the `compare_methods` row (shown, counted by nothing).
- No `model_call_receipts`, `judgment_ledger`, `approach_maps` or learner-text gap rows on any run.

**(d) `model_call_receipts`.** 34 learner databases under `landing-rw2c/` carry the table. **No row of any status**
in any of them (so none completed): every model-backed step was refused before a request (`unpriced`) or found
nothing to search.

### New findings

1. **No source composition was needed (none).** The merge had no conflict and no landing fix; the only commit beyond
   the regeneration is the lockdown pin for the comparison lines.
2. **The hint report counts a comparison as a shown, unattached help row (Low).** `learnloop hints report` lists
   `compare_methods` as its own kind (labelled, chooser `none`), but adds it to `totals.shown` and
   `totals.unattached`, which read as hint totals. The workbench section is unchanged. A report that separates
   comparisons from hints is a follow-up (with L1's adoption of `workbench_unaided_progress` there).
3. **A second open after failed lines starts another lines job (by design; Low).** Each reopen while the lines are
   missing tries again on the check's route, inside its per-problem and daily caps; on a refused route nothing is
   called. The reveal is still written once.
4. **Load flakes (Low, from before this stage).** Two reading-build sweep tests (`test_reading_request_sweep.py`,
   `test_reading_hardening_2_fixes.py`) time out their 60 s waits at load average ~50; both pass alone.
5. **The RW2c RPCs register while off.** Off, each refuses (`examples_unavailable`, `compare_unavailable`) or
   answers `disabled`, and nothing is searched, called or written; only `initialize`'s method list (and so the
   refusal codes) differs from main, as for RW5a's and RW7a's RPCs.

### For the owner

- **No migration.** The head stays 217; no table, reveal kind or route is added; your algorithm version is
  unchanged and there is no successor. Nothing served moves (parity (a), (b)).
- **What you see.**
  - In a Reader problem, after a level-3 or higher hint, "a similar example from your books" may appear under the
    hint once a verified passage that follows your route is found (in the background; the hint never waits). Under
    your steps, "Show me a similar example" asks for one on the step you are on. An example never shows the answer,
    an exercise or solution, or exam material, and seeing it counts nothing.
  - When a bridge or an example has more than one verified passage, the one shown is drawn at random (logged with
    its probability) and "another passage" shows the next one, with no new search.
  - After a correct Submit of a workbench problem, the feedback screen offers "Compare with the book's method":
    your steps beside the item's key (or the book's own solution), then one line per difference, and "Your route is
    valid — a different method from the reference." when it is. **Opening it records a reveal on the item** (not on
    your attempt): the next attempt on that item counts as primed, the same as seeing the answer.
  - Hints in the workbench are written with typed lines about what preceded your recovery before ("associations,
    not what works"); they never show in the hint.
- **The switches** (`[workbench]`, all `true`): `help_outcomes_enabled` (the lines to the hint writer and chooser),
  `examples_enabled` (the worked example and "Show me a similar example"), `compare_methods_enabled` ("Compare with
  the book's method"), `passage_draw_enabled` (the logged draw and "another passage"). Off, each part is gone and the
  rest is as before (pinned byte for byte against the stage's base, and in parity (c) against main).
- **With examples on by default, every shown level-3+ Reader hint starts a background example search** through the
  sources spec's `propose_sources` (the existing `source_rerank` path, inside the source service's daily cap and the
  problem's `workbench.max_calls_per_session`).
- **The comparison's lines use the check's route** (`ai.routing.workbench_check`), its caps and receipts; they run
  through the Codex lockdown like every other call (pinned at this landing).

### Open questions (defaults taken; §6)

1. Draw size: at most 3 options per draw.
2. Help-outcome line budget: 3 kinds per facet, 4 in all, plus the goes-off lines.
3. "Later independent": the next attempt on the facet with no hint and not primed, whatever its surface (one
   definition; RW6b may want its own label).
4. Example trigger: level 3 or higher, Reader problems only.
5. Compare offer: only at correctness ≥ 0.999.
6. The classic feedback view gets no compare offer.

### Open items

- **L2:** the workbench's per-problem call cap is not cumulative for examples (as for RW2b's bridge); each search is
  bounded by the source service's daily cap.
- **L3:** switch-off residue in stored rows (a bridge's `placement.source_id`, the draw columns) and in
  `session_calls_on`, which still counts example rows made while on; all of it is serialized only while on.
- **L5:** `help_outcomes` runs synchronously on the hint-request path (n = 1 scale); a facet-filtered or cached read
  if latency shows.
- **L7:** cross-book bridge navigation works only with the passage draw on.
- **L-a:** `workbench.compare_offer` raises `exercise_withheld` (the statement gate) before it checks the switch, so
  off, a withheld exercise's attempt refuses instead of answering `disabled`.
- **L-b:** the compare worker does not recheck the exercise's withheld status just before its call (the RPC checked
  it at open).
- **L-c, L-d:** conservative asymmetries in the "continued" rules (from the orchestrator's final verify).
- **Deferred help kinds:** figures, tutor exchanges and library asks are not yet read as help kinds in
  `help_outcomes` (§2).
- **Deviation against C13:** the workbench continuation has no "time to the next valid step" (adaptive hints §6.1);
  the hint report still reports its workbench rows as `workbench_state_unknown` and can adopt the shared function and
  that time at its next change.
- **From this landing:** finding 2 (comparisons in the hint report's totals), finding 4 (load flakes in the
  reading-build sweep tests).
