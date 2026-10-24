# Reader workbench RW5b: more figure kinds and offered figures (stage `reader-rw5b`)

Branch `reader/rw5b` (worktree `learnanything-dl2`), base `main` at `a9ae97e34` (the RW2c landing tip;
migration head 217; RW5a, RW7a, RW2c and both security landings on main). Spec:
`docs/specs/spec_reader_workbench_v1.md` §8.7 in full, G46 (with G21, G22), §13 step 7, the RW5b test list
(§14). RW5a's owner ruling stands: **no "checked" claim anywhere**, every figure is labelled an AI-built
illustration, nothing of RW5c is built. **No migration** (RW5a's tables carry `origin`, which already
allows `library` | `tutor`). **No algorithm successor.** No model was called: every test uses fakes.

## 1. What was built

### 1.1 Four panels in the same grammar (`learnloop.figures.spec`, `figureSpec.ts`)

Same declarative spec (`ifs-v1`; no spec-version bump, so RW5a's stored figures keep showing), the same
expression grammar, the same two evaluators, no generated code (G21):

| Panel | Shape | Data |
|---|---|---|
| `heatmap_2d` | `{x:{var,min,max,cells?}, y:{…}, expr, contours?:[expr], label}` | `x`, `y` samples, `z` rows by y, contour levels |
| `vector_field_2d` | `{x, y, u, v, heatmap?:{expr, cells?, contours?, label}, label}` | `u`, `v` grids, optional heat map on its own grid |
| `trajectory_2d` | `{x:{var,min,max}, y:{…}, x0, y0, dx, dy, t_max, steps, time?, label}` | `t`, `x`, `y`, `stopped` |
| `iterate_2d` | `{x, y, x0, y0, fx, fy, n, label}` | `k`, `x`, `y`, `stopped` |

- **Point expressions** (`expr`, `u`, `v`, `dx`, `dy`, `fx`, `fy`) may read the parameters, definitions and
  the panel's own variables (`time` for a forced system). They may not use `integral` (no small bound on its
  cost), and every `sum`'s bounds must be countable: a number, a parameter, or the grid's own axis (so
  attention-like weights `exp(s)/sum(exp(…), m, 1, n)` work). Contour levels, `x0`, `y0`, `t_max` read
  parameters only.
- **RK4** is fixed-step, written in the same operation order in both evaluators
  (`k1..k4`, `x + h/6*(k1 + 2k2 + 2k3 + k4)`, `t = h*(i+1)`), so a trajectory built from `+ - * /` only is
  **identical step for step** (the corpus's `exact` cases are compared with `===` in vitest).
- **A path stops honestly.** It is cut where it leaves its plot window padded by 25% a side
  (`ESCAPE_MARGIN`; `stopped: "left_plot"`, nothing past it drawn) or where a value stops being finite
  (`"not_finite"`); one that starts outside is `"starts_outside"`. The renderer says each in words.

**Code-owned caps on computation** (parameters cannot raise them; the same constants in both evaluators and
pinned by the corpus): `MAX_HEATMAP_CELLS = 40` per axis (default 40: 41×41 samples), `MAX_FIELD_CELLS = 20`
(default 12), `MAX_TRAJECTORY_STEPS = 2,000` (default 400), `MAX_ITERATIONS = 500` (default 50),
`MAX_CONTOURS = 8`, and over the whole figure **`MAX_PANEL_WORK = 250,000` expression steps per evaluation**
(points × the expanded nodes of each point expression, a sum's body counted once per term, four RK4 stages per
step). Measured in Python: a 41×41 heat map of a 45-node expression verifies (81 grid points) in about 1 s,
a 2,000-step trajectory in about 2.5 s, so verification stays bounded (RW5a's friction note).

### 1.2 Verification (`learnloop.figures.verify`): RW5a's steps 1-2, unchanged

Step 1 now reads every value the new panels show (grids, arrows, overlay, path points) and their render
scales, at every parameter-grid point; any value not finite fails the figure (**refuse, never draw
garbage**). Added invariant-style sanity gates for paths (`path_problems`): a path that stops being finite or
starts outside its plot at any grid point fails step 1; a path cut where it **leaves** its plot is shown,
cut and labelled (boundedness within the panel range is enforced by the cut itself). Step 2 (declared
invariants) applies unchanged.

### 1.3 The renderer (`AdvancedPanels.tsx`, dispatched from `FigurePanels.tsx`)

A heat map is one hue whose opacity rises with the value (greyscale-safe) with contour lines by marching
squares over the computed grid (display only, never past the data); a vector field's arrows are scaled by
the longest, over its heat map; a trajectory or iterated map is its points from a marked start, with the
stop said in words. Every panel has a values table (`t`), sampled to about a dozen rows/columns. Nothing
animates.

### 1.4 Figures offered, not only requested (§8.7)

- **Code decides the block, the judge only yes/no.** `figure_admission.offerable` (the one rule): block
  type `Equation`, `Figure`, `FigureGroup`, `Picture`, `PictureGroup`; `offerable_blocks` reads them.
- **Organizer (RW4a).** When an equation or figure block is among the passages and offers are on, the
  organizer's **same single listwise call** carries `explorable: yes|no` per judgment
  (`OrganizerExplorableResult` / `OrganizerRolesExplorableResult`, prompt versions
  `library_organizer.v1-explorable` / `library_organizer.v2-explorable`; the candidates of such blocks are
  marked `block: equation|figure`). A note carries `explorable: true` only when the block is offerable, the
  judge said yes, and its own line was kept. A missing or unknown field reads as no.
- **Tutor (RW1c).** With offers on (and RW1c's retrieval and offers on, its surface), and an equation or
  figure among the delivered passages, the Reader tutor's **same answer** uses
  `ReaderTutorExplorableQAContext` (no new context field) → `ReaderTutorExplorableAnswer(+WithTools)` with
  `explorable: [{extraction_id, span_id, explorable}]`, prompt versions `…reader-modes-explorable` (and
  `…-source-tool-requests-explorable`). `reader_modes.finalize` keeps a yes only on a block the answer shows
  as cited (never on abstention); the sidecar's `offers()` adds `make_explorable` buttons for this book's
  offerable blocks.
- **Pressing builds.** `reader.figure_request` takes `origin` (`selection` default, `library`, `tutor`) and
  `offerRef` (the library question / the tutor answer's question event). An offered request must name
  exactly one block the stored judgment offered (re-read from the stored output, block rule re-applied; no
  region) or it is refused `not_offered` before any job or call. It then runs RW5a's pipeline unchanged
  (held-out refusal, the selection plus two blocks each side as context — "retrieval supplies the equation,
  figure and assumptions" — the author's two attempts, verification steps 1-2), stores that origin, and
  reuses by input hash (spec version `ifs-v1`). The hash names no origin (Codex review F2: a block is one
  figure whatever offered it) and a shown figure of the same input under the other prompt version is reused
  when it can be drawn now; see `reader-rw5b-codex-review.md`.
- **One admission point.** The offer button makes no call. Every figure-derived request goes through RW5a's
  `FiguresGate`; an offered build's key (`offer_build_key`) adds `figures.offers_enabled`, and every build's
  key adds `figures.advanced_panels_enabled` (the author's prompt depends on it). A "not right?" version of
  an offered figure is a revision (governed by `revisions_enabled`, not the offers switch).
- **Frontend.** `TutorOffers` renders `make this explorable` (the press shows "building an interactive
  version under the passage" and builds with origin `tutor`); `LibraryAnswer`'s hit carries it where
  `note.explorable` is true; `ReaderScreen` builds in this book at once, or opens the hit's book as a detour
  and builds there once it is open (the press lapses if another book opens instead). `useFigures.request`
  sends an offered request only while the contract names `offers`.
- **Report.** `learnloop reader report`'s `figures` block gains `offered: {library, tutor}` by verification,
  only while offers are on.

### 1.5 Kill switches (classified in `params/parameter_registry.py`, structural / operational)

- `figures.advanced_panels_enabled` (true). Off: the author's prompt is RW5a's byte for byte
  (`figure_author.v1`; on it is `figure_author.v2-panels`, so RW5a's reuse hashes are unchanged while off),
  `parse_spec(advanced=False)` refuses the four kinds (two attempts, then `failed` naming the switch), and a
  stored figure that uses one lists as the unsupported-kind state ("can't draw this yet — needs a panel kind
  that is switched off …") with no spec sent; predictions on it are refused.
- `figures.offers_enabled` (true). Off: the organizer's and tutor's prompts, models and outputs are RW4a's /
  RW4e's / RW1c's byte for byte (a stored note's `explorable` is stripped on output), the prompt contract's
  `figures` is RW5a's key for key (no `offers`), no `make_explorable` button, and an offered request is
  refused (`offers_disabled`, in the RPC and the service).
- With offers on but **no equation or figure block** among the passages, the organizer and tutor requests
  are also byte-identical to theirs (nothing to judge, no tokens spent).
- Unsupported requests keep RW5a's "can't draw this yet" with the per-kind count; the author's
  unsupported examples no longer name "a vector field" while the panels are on.

## 2. Deviations (each with its reason)

1. **A separate corpus file** (`figurePanelsCorpus.json`, `tests/figure_panels_corpus.py`) instead of
   new cases in RW5a's golden corpus: RW5a's corpora stay byte for byte (a pinned property of the RW5a
   landing), and RW5a's "covers every panel kind" test keeps its meaning.
2. **`exact` parity on arithmetic-only cases, 1e-9 elsewhere.** Python's libm and V8's fdlibm may differ by
   an ulp on `exp`/`sin`/`cos`; the chaotic Hénon map and the RK4 oscillator use `+ - * /` only, so they are
   compared exactly (G46's "identical step for step"). The other cases are within the corpus tolerance.
3. **The offer rule is by block type only** (no ingest-role widening): one rule shared by the organizer,
   the tutor and the RPC without the tutor package importing `source_retrieval` (the frozen acyclic
   contract).
4. **The judgment is asked only when there is a block to judge** (an equation or figure among the
   passages), rather than on every call while offers are on: no tokens on prose-only answers, and RW4a/RW1c
   pins stay byte-identical.
5. **Tutor offers live under RW1c's offers** (`reader_tutor.offers_enabled`, where the buttons render) and
   only for the open book, as "try the next step first" does. Library offers may name any book; the press
   opens it as a detour and builds there.
6. **The prompt contract adds `offers: true` only while on** (RW5a's three keys otherwise); the RW5a pin
   `test_figures_rpc.py::test_the_prompt_contract…` is re-recorded for this stage's key only.
7. **`ifs-v1` unchanged**: the panels are additions to the same version (spec §8.2 lists them under
   `ifs-v1`); a new spec version would hide every RW5a figure from `list_figures`.

## 3. Tests

(counts in §6)

- `tests/test_figure_panels.py` (new): the panels corpus as generated; RW5a's corpus untouched; coverage
  (every kind, every stop, overlay, time variable, contours, sum weights, an exact RK4 case); the caps;
  each corpus figure's values; each rejected spec; RK4 against an independent textbook RK4 step for step
  and the closed form (fourth order: halving h cuts the error ~16×); an iterated map is its recurrence; the
  cut never draws past the padded window; verification refuses not-finite and starts-outside paths and a
  heat map with a value that is not finite, accepts a path cut at the plot's edge; invariants unchanged;
  the switch at parse time; the work cap counts a sum's terms; the RK4 lines in `figureSpec.ts`.
- `tests/test_figure_offers.py` (new): the rule; the organizer judges in its one call (one request, its
  own version, `block` marks, yes only on equation/figure blocks, a yes on prose is no offer, old outputs
  read as no, no block → RW4a byte for byte, offers off → its own version and no field, a stored offer is
  stripped once offers are off, the roles request composes); the tutor (prompt/version/answer model, the
  view keeps a yes only on a cited block, abstention keeps none, the buttons, the context asks only with a
  block to judge); the press (library and tutor build through RW5a with the right origin and are reused
  by input hash; five not-offered cases refused before any call; offers off refused in RPC and service;
  selection unaffected); admission (an offered build stops when offers flip before its request; a
  selection build does not; the advanced switch flipping stops a build; the gate keys); the advanced
  switch on the build path (RW5a prompt byte for byte while off; a vector field shown while on; stored
  ones become "can't draw this yet" and new ones are refused while off); the reader report's `offered`.
- `figurePanels.test.ts` (new): the same corpus in TypeScript, exact on `exact` cases; rejected specs;
  caps equal Python's.
- `advancedPanels.test.tsx` (new): each panel renders (cells, contours, arrows, start, stop words,
  iterates, values tables); marching squares stays inside the grid; an RW5b figure opens under its
  passage; the tutor offer calls nothing until pressed, then builds with origin `tutor`; offers off in the
  contract builds nothing; no handler → no button; the library offer only where judged, naming the question.
- Changed pin: `tests/test_figures_rpc.py` (the contract gains `offers`).

## 4. Owner notes

- Both switches default **on** (frictionless defaults). With them on, a library question or tutor answer
  that cites an equation or figure shows "make this explorable"; pressing it is one figure build (inside
  `figures.max_daily_cost_usd`); the judgment itself costs a few output tokens in the call already made.
- No migration, no successor, no new route: `figure_author`, `library_organizer` and `tutor_qa` as before.
- Window keydown listeners: **none added** (the UX2 `screenLeavesKey` guard needs nothing here).
- The config reference pages (`Configuration/Fields/Config - figures.md`) gain the two keys at the
  landing's reference regeneration.

## 5. Open questions (with the defaults in force)

1. **Library offers on another book open it as a detour** (Alt+← back). Default: yes. Alternative: build
   in the background and show it only when that book is opened.
2. **Offers only on equation and figure blocks by extracted type.** Default: yes (a passage of prose that
   states a formula inline gets no offer; the learner can still select it and press "make this explorable").
3. **Heat-map colour is one hue by opacity**, not a diverging map for signed values. Default: one hue
   (greyscale-safe); a signed map could follow if owners ask.
4. **A path that leaves its plot is shown cut**, not refused. Default: shown and labelled (it is often the
   point: divergence at a large learning rate); a not-finite value or a start outside is refused.
5. **Re-judging old library answers when offers come on** (no extra call is made; stored answers keep no
   offers). Default: no; new questions carry them.

## 6. Gate (implement step; owner rule 2026-10-17: targeted only)

Run on `eadd382a7` (the tree this section is committed on adds only this section), with
`TMPDIR=fixtures-local/tmp`; every pytest/npm/vitest command inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- …` (the 2026-10-23 memory rule),
pytest `-n 6`, vitest `--maxWorkers=4`, one test command at a time. No model was called; no vault copy was run.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **30 kept, 0 broken** |
| targeted pytest, 80 files (list below) | **2,204 passed, 1 skipped** (a pre-existing golden-writer skip in `test_figures_switch_off.py`), 243 s |
| `npm install`; `npm run typecheck` | ok, no errors |
| targeted vitest: `src/screens/reader` (all), `src/screens/ReaderScreen.*`, `src/app/App.wrapUpSkim.test.tsx`, `src/screens/attentionBudget.test.tsx` | **79 files, 762 passed** |
| `npm run frontend:build` | ok (the existing chunk-size warning only) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference generate/validate; durability lane | not run: no migration, no schema or connection change |

New tests: `tests/test_figure_panels.py` 49, `tests/test_figure_offers.py` 28, `figurePanels.test.ts` 32,
`advancedPanels.test.tsx` 12. Changed pins: `tests/test_figures_rpc.py` (16), `tests/test_figures_switch_off.py`,
`tests/test_reader_tutor_switch_off.py`, `tests/test_reading_paths.py`.

Pytest files run (for reading the landing gate against): the figure files
(`test_figure_grammar`, `test_figure_offers`, `test_figure_panels`, `test_figure_predictions`,
`test_figure_region`, `test_figure_revisions`, `test_figure_verification`, `test_figures_codex_review`,
`test_figures_final_round`, `test_figures_fix_round2`..`5`, `test_figures_migration`, `test_figures_rpc`,
`test_figures_scope_redesign`, `test_figures_switch_off`); library ask (`test_library_ask`,
`test_library_ask_expand`, `test_library_ask_review`, `test_library_asks_migration`); the Reader tutor
(`test_reader_tutor_offers`, `test_reader_tutor_retrieval`, `test_reader_tutor_switch_off`, `test_tutor_qa`,
`test_tutor_citations`, `test_tutor_tool_requests`, `test_tutor_delivery_fixes`, `test_source_retrieval_tutor`,
`test_source_retrieval_search`, `test_reader_rw1c_review`); the organizer and roles (`test_roles_judges`,
`test_roles_switch_off`, `test_rw4_kill_switches`, `test_source_roles`, `test_reader_find_sources_callers`,
`test_rw4d_rw3b_composition`, `test_compare_sources_keep`, `test_compare_keep_switch_off`,
`test_rw2c_switch_off`, `test_reading_paths`, `test_reading_step_switch`); the report and sidecar
(`test_reader_report`, `test_reader_cues_cli_report`, `test_sidecar_reader`, `test_sidecar_source_retrieval`,
`test_sidecar_registry`, `test_reader_inquiry_kill_switch`, `test_reader_intent`); exam protection and
routes (`test_exam_protection`, `test_exam_protection_review`, `test_judge_routes`, `test_codex_tool_lockdown`,
`test_codex_lockdown_round2`, `test_codex_lockdown_round3`, `test_codex_output_schema`,
`test_ai_tool_isolation`, `test_structured_transport_parity`); and the contract pins (`test_config_refactor`
(defaults snapshot), `test_registry_audit`, `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`,
`test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`,
`test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`).

## 7. Fix round 2 (orchestrator)

The re-review of the Codex fix round (on `dc88795a0`) found F1-F7 clean and three new issues, all fixed
here, each with a test that failed on `dc88795a0`. No migration, no successor, no model call (fakes only).

- **F8 [Medium], a regression from F3's fix: a library offer on a repeated or forked ask was refused
  `not_offered` on every press.** `offered_spans` required the note's ledger row's `left_id` to be this
  ask, but listwise ledger ids are derived from the request (input hash and passage key), never the ask: a
  second identical ask is answered from the ledger (`cached`) and its notes name the first ask's rows, and
  RW4d's `fork_ask` copies `organizer_json` under a new id. **Chosen: drop the `left_id` comparison** and
  pin the row structurally instead: the note's `ledger_id` row must be the organizer's own task and kind
  (`task == library_contribution`, `left_kind == library_ask`, i.e. `ORGANIZER_TASK.ledger_task` /
  `.left_kind`), on this very block (`right_id == note key`), recording `explorable: yes`. Not chosen:
  recomputing the ledger id from this ask's request, because the id hashes the prompt as built at ask
  time together with the route's model, output budget and reasoning effort; recomputing at press time
  would refuse whenever any of those drifted since (a config change, a re-routed model), the same false
  refusal in another form, and a fork has no request of its own to recompute. The task check matters now
  that F10 puts the tutor's verdict in its rationale: a tutor `figure_explorable` yes on the same block
  cannot stand in for the organizer's row.
  Tests (`tests/test_figures_rw5b_fix_round2.py`): the same question asked twice, pressed on the second
  ask (one organizer call; the note's row has the first ask's `left_id`; builds); a forked ask pressed on
  the fork (builds); a note pointed at the tutor's yes row on the same block is refused (a guard for the
  new check; it also passed before, where the `left_id` and the empty rationale refused it).
- **F9 [Low]: a library press could say "building it under the passage" forever.** The Reader settled the
  press `true` at dispatch, and never when the detour's book did not open (`openLibraryHit` returned
  early, or `openSource` caught its error) or figures were off when the book opened (the effect returned
  and kept waiting; it would even build later, unseen, if they came back on). Now `useFigures.request`
  resolves to the build's outcome (`shown | not_shown | cancelled | skipped`); `openSource` and
  `openLibraryHit` resolve to how the open ended (`opened | preparing | not_opened`); each press carries its
  own `settle`, and the Reader settles it on what actually happened. The hit says `built under the
  passage`, or goes back to its button with a line naming the outcome: refused or failed, stopped,
  another reading, another book opened first, another passage pressed first, that book did not open, still
  being prepared, figures switched off (`LIBRARY_EXPLORABLE_COPY.lapsed`, typed against
  `ExplorableOutcome`). With no book on screen (the library page) the open's own outcome settles the press.
  Tests: `src/screens/reader/figures/libraryOfferSettle.test.tsx` (new, the Reader end to end: a press in
  this book the server refuses `not_offered`; a press in this book that builds says building until the
  figure lands, then built; a detour whose book fails to open; a detour that opens after figures went off,
  then figures come back on: no build, the line says figures are off). All four failed on `dc88795a0`'s
  sources (the hit kept "building it under the passage"). `advancedPanels.test.tsx`: the F6 lapse test and
  the "keeps saying so" test moved to the outcome API, plus one case per lapsed outcome (8).
- **F10 [Low]: the tutor's `figure_explorable` ledger rows hashed the verdict into `input_hash`**, so
  `ai/agreement.py` (which pairs by input hash) could never pair an owner or verifier label with them, and
  the rationale was `""`. Now `input_hash = content_key([prompt_version, event_id, extraction_id,
  span_id])[:40]` (the input only) and `rationale = {"explorable": "yes"|"no"}`. The row id
  (`tutor_explorable_judgment_id`) is unchanged, so the F1 tutor press path reads the same rows (it checks
  task, left id and verdict); a test presses a tutor offer through it. Tests: the hash and rationale for a
  yes and a no verdict; the tutor press still builds from its rows.

Changed source: `src/learnloop_sidecar/handlers/figures.py` (`offered_spans`), `src/learnloop/tutor/tutor_qa.py`
(`_record_explorable_verdicts`), `ReaderScreen.tsx`, `reader/LibraryAnswer.tsx`, `reader/LibraryPane.tsx`,
`reader/figures/useFigures.ts`, `reader/useReaderInquiry.ts` (its `openSourceRef` type returns `Promise<unknown>`).

Gate (memory rule: every pytest/vitest/npm command under `systemd-run --user --scope -p MemoryMax=5G
-p MemorySwapMax=1G`, pytest `-n 6`, vitest `--maxWorkers=4`, `TMPDIR=fixtures-local/tmp`, one at a time):

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` (under `env -i`, empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR) | **30 kept, 0 broken** |
| targeted pytest: §6's list plus `test_figures_rw5b_review`, `test_figures_rw5b_fix_round2`, `test_decider_agreement` (72 files) | **2,224 passed, 1 skipped** (the pre-existing golden-writer skip), 247 s |
| targeted vitest: `src/screens/reader` (all), `src/screens/ReaderScreen.*`, `src/app/App.wrapUpSkim.test.tsx`, `src/screens/attentionBudget.test.tsx` | **81 files, 778 passed** |
| `npm run typecheck` | ok, no errors |
| `npm run frontend:build` | ok (the existing chunk-size warning only) |
| `cargo check`, DB reference, durability lane | not run: nothing under `src-tauri`, no migration, no schema or connection change |

## 8. Landing onto main

Landed in the `learnanything-merge4` worktree on branch `merge/rw5b-onto-main`, cut from main at `558e85ab1` (the UX2
landing record; migration head 217 with `migration_head_217`, which holds 215, 216 and 217 and no 214). The stage tip
is `33f2002b5` (base `a9ae97e34`, the RW2c landing), unchanged; the orchestrator's final verify (Opus) on it was
CLEAN. Main was neither fast-forwarded nor pushed here. T1 has not landed and is not part of this merge.

### Commits and conflicts

- `3c53842db`: the `--no-ff` merge of `reader/rw5b` onto `558e85ab1`. Since the stage's base, main gained only UX
  Phase 2 (the simple shell, `ui.shell`, the `screenLeavesKey` guard, `classicIsBase.test.ts`). One file conflicted:
  - `config/template.py`: 20 snapshot entries, each with both sides' comment lines (UX2's, then RW5b's) and main's
    fingerprint for now; the fingerprints were recomputed in the regeneration commit.
  - Auto-merged without conflict, both sides present: `params/parameter_registry.py` (RW5b's two `figures.*` rules
    and UX2's `ui.shell` rule), `config/schema.py` (`FiguresConfig`'s two switches and `UiConfig.shell`),
    `ReaderScreen.tsx`, `reader/LibraryPane.tsx` and `reader/useReaderInquiry.ts` (UX2's guards on every listener,
    RW5b's offer press, settle and `Promise<unknown>` open).
  - `LibraryAnswer.tsx`, `useFigures.ts`, `TutorOffers.tsx`, `dto.ts` and `client.ts` were changed by RW5b only.
- **Routing.** Main changed nothing under `src/learnloop/ai`, `figures`, `tutor` or the library ask since `a9ae97e34`,
  and RW5b changed nothing under `ai/` (no route, no task). So `figure_author`, `library_organizer` and `tutor_qa`,
  and the build behind the offer button (RW5a's `FiguresGate` path), resolve exactly as main's equivalent tasks do,
  tool-free under the Codex lockdown. Re-run on the merged tree (5G scope, `-n 6`): `test_figure_offers`,
  `test_figures_scope_redesign` (the `FiguresGate` files), `test_codex_tool_lockdown`, `test_codex_lockdown_frozen`,
  `test_codex_lockdown_round2`, `_round3`, `test_codex_output_schema`, `test_ai_tool_isolation`, `test_judge_routes`,
  `test_structured_transport_parity`, the figure RPC and RW5b review files and the contract pins: **1,061 passed,
  1 skipped** (the pre-existing golden-writer skip).
- **Keydown guard.** RW5b adds no `window` or `document` keydown listener (`git diff a9ae97e34 reader/rw5b` adds no
  `addEventListener` or `onKey` line under `src/`); `keymap.test.ts`'s scan passes on the merged tree unchanged.
- `4127892e6`: **`classicIsBase.test.ts`.** On the merged tree it failed twice: nine RW5b files under `screens/`
  (the figures, `LibraryAnswer`, `TutorAnswer`, `TutorOffers`) showed up as unlisted, and `LibraryPane.tsx`'s new
  `ExplorableOutcome` import failed the guard-file line check. The brief said to move `BASE` to this merge's first
  parent (`558e85ab1`); that cannot pass with the manifest unchanged, since the tree's diff against main is RW5b's,
  not UX2's, and the palette and classic-verbatim checks need the pre-UX2 base. So `BASE` stays `a9ae97e34`
  (classic's base) and the two diff checks (the file list, and "the guard files change only by the guard lines")
  compare `BASE` with a new `UX2_LANDED = "558e85ab1"`, this merge's first parent (UX2 landed and recorded, nothing
  after it). They check exactly UX2's changes, as before, and need no move at later landings (UX2's landing finding
  2). The manifest and every check are unchanged; the file-list check no longer adds untracked files, since it
  compares two commits. The checks that read the tree (gates present, classic snippets verbatim in tree and base,
  the classic palette, the unfocusable frame body) still read it. All 6 pass.
- `b5a276a6c`: the regeneration (below). **This is the gate head.**
- This record (docs only).

### Regeneration (`b5a276a6c`)

- **Defaults snapshots.** Template `.pyc` cleared; recomputed and checked with `-B` under `env -i` (empty `HOME`,
  `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`): all **20** entries rewritten (main's `ui.shell` plus RW5b's two switches),
  then **0 mismatches**.
- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head **217**,
  **339** table notes, **959** configuration leaves in **69** sections (`Config - figures` 6 → 8 leaves). The two
  prose counts (`Configuration.md`, `Database.md`) were updated from 957. The rest is `source_commit` provenance and
  shifted `schema.py` line anchors (410 reference files).
- **CLI help snapshot, RPC pins, serializer snapshot, mobile allowlist**: unchanged (their tests pass, targeted and in
  the full suite). No RPC method was added; `reader.figure_request` gains the optional `origin` / `offerRef`.
- **`validate_vault.py`**: passes (1,142 notes, 1,140/1,140 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **999** issues (as at the UX2
  landing).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0); `TMPDIR` was merge4's
`fixtures-local/tmp`; every later command `uv run --no-sync`. Logs in `fixtures-local/landing-rw5b/logs/`. Every
test, npm and cargo command ran alone in a `systemd-run --user --scope` (the suite lanes at 10G / 2G swap under
`flock /tmp/learnloop-fullsuite.lock`, `-n 8`; everything else at 5G / 1G, pytest at most `-n 6`, vitest
`--maxWorkers=4`). Other stages' worktrees and processes were not touched. Every test uses fakes. **This is the first
full run over RW5b's code.**

| Check | Result |
|---|---|
| `lint-imports --no-cache` (under `env -i`) | **30 kept**, 0 broken |
| full suite `pytest -n 8` (10G scope) | **15,802 passed, 1 failed, 2 skipped, 2 xfailed** (50 min). The failure, `test_reading_hardening_2_fixes.py::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`, is the 60 s `_wait_for` timeout in the reading-build sweep that RW5b does not touch (the same load flake as at the RW2c and UX2 landings). The file alone, 3 times (5G scope): **5 passed** each time |
| `pytest -m durability -n 8` (10G scope) | **119 passed** |
| `npm install`, `npm run typecheck` (5G) | ok; clean |
| `npm test -- --maxWorkers=4` (the whole vitest run, 5G) | **201 files, 1,718 tests passed**, no unhandled error, no snapshot written (UX2's landing: 1,658) |
| `npm run frontend:build` (5G) | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` (5G) | ok |
| tracked fixtures, worktree | `git status` clean after every lane; no `-wal` / `-shm` beside a fixture |

**No real failure, so no landing fix.**

### Parity (backup-API copies; no model call was made)

**Setup.** Scripts in `fixtures-local/landing-rw5b/scripts/`, adapted from the UX2 landing's (`ab_rw5b.sh`,
`plan_repeat.sh`, `neutralize3.py`, `routes.py`, the dump and compare scripts, the `E` wrapper); new: `c_rw5b.sh`,
`rw5b_run.py`, `ccmp_rw5b.py`, `ccmp2_rw5b.py`. Each script ran in a 5G `systemd-run` scope.
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once with `copy_tree_with_databases`
  from the main checkout into `fixtures-local/landing-rw5b/orig/`; every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both start at schema 165, label `mvp-0.8`, 0 receipts.
- **Code.** Main's is `git archive 558e85ab1`; the merge's `git archive b5a276a6c` (both without `fixtures/`,
  `docs/`, `apps/`).
- **Environment.** `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR` and `LANG`; the
  three directories empty (afterwards `HOME` holds only uv's cache from the lint run; `CODEX_HOME` and the config
  directory are empty).
- **Routes.** `neutralize3.py` under each code: every route field to `127.0.0.1:9` (59 on both), the active provider
  to that loopback profile with no fallback, rewrite / rerank / dense / embeddings / learner-text gaps off,
  `build_on_serve` and outcome placement off. `routes.py` resolved 62 `AITask`s on both, nothing outside the loopback
  profiles except the disabled, keyless `embedding`.

**(a) No schema change**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main / merge | 165 → 217, 51 applied, on both | the same |
| schema, main vs merge | **identical**: 1,451 objects each, none on one side only, no SQL differs | **identical** (1,450) |
| rows of every table (344), all columns | **identical** (16,542 rows); `schema_migrations` 203 rows each, differing only in `applied_at` | **identical** (7,640 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both | the same |
| `rebuild --shadow --json` | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json` | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes** (frozen clock 2026-10-19 09:00 UTC; the merge at its defaults, both RW5b switches on)

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` | cert (132,860 bytes), Today (504,488), plan (546): **byte-identical** | cert (17,494), Today (709,910), plan (546): **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; rc 0), opened by each code | cert (129,651) and Today (528,665) **byte-identical** | cert (17,495) and Today (741,269) **byte-identical** |
| then to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; rc 0) | cert and Today **byte-identical** | the same |
| the daily plan at mvp-0.27 and mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three fields, and from the merge's in exactly these three (`plan_repeat.sh`): run-to-run noise, as at the earlier landings | the same |

**(c) The real sidecar** over stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC (`sidecar_clock.py`), driver
`rw5b_run.py`, on fresh copies of main's mvp-0.29 copy: (i) `cm`, main's code; (ii) `coff`, the merge with
`[figures] advanced_panels_enabled = false` and `offers_enabled = false`; (iii) `cdef`, the merge at its defaults.
Calls: `initialize`; `reader.prompt_contract`; `reader.figures` on the passage's extraction; `reader.library_ask` on
an **equation** block (probability `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY:s38`, linear_algebra
`ext_01KY2YGNVCCVEQCGCE4RH3BWHQ:s52`), polled with `reader.library_job`, then `reader.library_ask_notes`, polled;
`reader.ask` (the Reader tutor) on the same block; `reader.figure_request` on that selection, polled with
`reader.figure_job`; `reader.figures` again; `shutdown`. Then `learnloop reader report --json` (its `figures` block)
on each copy. Compared call by call by `ccmp2_rw5b.py` (ids, digests, timestamps and the vault path normalised; each
run of job polls collapsed to its last response, since the number of polls is timing).

| Call | (i) vs (ii) | (i) vs (iii) |
|---|---|---|
| `initialize`, `reader.figures` (both), `library_ask` (pending, then done) | identical | identical |
| `reader.prompt_contract` | identical | `figures` gains `offers: true` (RW5a's three keys otherwise) |
| the notes job (the organizer) | identical | `promptVersion` `library_organizer.v2` → `library_organizer.v2-explorable` (an equation block among the passages, so the same single call carries the yes/no judgment); the call is unavailable at the loopback on all three, `notes: []` on all three |
| `reader.ask` | identical: refused `provider_unavailable` before any call | the same refusal |
| `reader.figure_request` → `reader.figure_job` | identical: the build fails `unpriced` (RW5a's metered-route rule) before any call | the same |
| `learnloop reader report --json` | identical apart from `window.until` (the CLI's wall clock) | `figures.offered = {library: {}, tutor: {}}` added (only while offers are on), and `window.until` |
| rows added over the copy opened by the merge (`deltas.py`) | the same rows on all three runs: `library_asks` 1, `interaction_events` 3, `source_exposure_events` 14, and the replayed facet rows (probability 1 / 2; linear_algebra 36 / 76 / 30 `practice_item_state`) | the same |

Apart from the JSON-RPC request ids (which count the polls), (i) and (ii) are **byte-identical** on both copies.
**Method registration:** no RPC method was added or removed (the figures handler's method list is RW5a's); the only
contract change is `reader.figure_request`'s optional `origin` / `offerRef`, which (i)-(iii) did not send. **No
figure row, no `judgment_ledger` row and no model call appeared** on any run.

**(d) Frontend and receipts.**
- The whole vitest run passes (201 files, 1,718 tests), including `classicIsBase.test.ts` (6), the keymap scan
  (`keymap.test.ts`, 15), `figurePanels.test.ts` (32), `advancedPanels.test.tsx` (23), `libraryOfferSettle.test.tsx`
  (4) and `tutorOfferPress.test.tsx` (1).
- `model_call_receipts`: 34 learner databases under `landing-rw5b/` carry the table; **no row of any status** in any
  of them, so none completed.

### New findings

1. **`classicIsBase.test.ts`'s base question is settled.** The brief's "move `BASE` to main" cannot pass once a later
   stage changes `screens/` or `components/`; the diff checks now compare UX2's own landed range
   (`a9ae97e34..558e85ab1`), so no later landing needs to move anything. The orchestrator may prefer a different
   shape; the manifest and checks are as UX2 left them.
2. **The organizer's prompt version moves at defaults whenever an equation or figure block is among a library ask's
   passages**, even when its call then fails (parity (c)): `library_organizer.v2-explorable` instead of `.v2`. This is
   the designed behaviour (§1.4, deviation 4), recorded so the owner reads it as expected; it also means a ledger hit
   from an earlier `.v2` ask on the same passages is not reused once offers are on.
3. **Load flake (Low, from before this stage).** The reading-build sweep test timed out under the full suite again
   and passes alone.
4. **The brief counts six open questions; §5 lists five.** The five are recorded below; no sixth was found in this
   document or in `reader-rw5b-codex-review.md`.

### For the owner

- **No migration.** The head stays 217; no table, route, RPC method or successor; your algorithm version is unchanged.
  Nothing served moves (parity (a), (b)); with both switches off the sidecar answers byte for byte as main's
  (parity (c)).
- **What you see** (the defaults):
  - **New figure kinds.** Besides RW5a's curves and shaded areas, a figure can now be a heat map (one colour that
    deepens with the value, with contour lines), a vector field (arrows, over an optional heat map), a trajectory
    (a path from a marked start, stepped with RK4) or an iterated map (the points of a recurrence). A path that leaves
    its plot is drawn up to the edge and labelled as stopped there; one that blows up or starts outside is refused.
    Every panel has a values table. Nothing animates. Every figure is still an AI-built illustration; nothing says
    "checked".
  - **Make this explorable.** When a library answer or a Reader tutor answer cites an equation or figure block, a
    *make this explorable* button can appear under it (the judge says yes or no in the call it already makes, and
    only equation and figure blocks qualify). Pressing it builds the figure under the passage (in another book, it
    opens that book first; Alt+← goes back). The line under the button says when it was built, or why not (refused,
    stopped, another reading or book opened first, figures off). A block already built from a selection is reused,
    whatever offered it.
- **The switches** (`[figures]` in the library's `learnloop.toml`): `advanced_panels_enabled = false` returns the
  author to RW5a's prompt and shows stored figures that use a new kind as "can't draw this yet";
  `offers_enabled = false` removes every *make this explorable* button and returns the organizer's and tutor's
  calls to theirs byte for byte. Both default to on; `figures.enabled = false` still turns figures off altogether.
- **Notes.** A press is one figure build inside `figures.max_daily_cost_usd`; the judgment costs a few output tokens in
  a call already made. A metered figure route still needs `figures.price_per_million` (as with RW5a).

### Open questions (defaults taken; §5)

1. Library offers on another book open it as a detour (Alt+← back): yes.
2. Offers only on equation and figure blocks by extracted type: yes.
3. Heat-map colour is one hue by opacity, not a diverging map: one hue.
4. A path that leaves its plot is shown cut and labelled, not refused: shown.
5. Old library answers are not re-judged when offers come on: no; new questions carry offers.

### Open items

- **Low:** "not built: the build was stopped" is shown when a generation change or a replaced run loses track of a
  build that actually continues (`useFigures.ts:141-157` and the `OFFER_OUTCOME` mapping; the request key has no
  origin).
- The tutor offer's own label still settles at dispatch (the library press settles on its outcome since F9).
- Copy: pressing B during A's detour says "that book did not open".
- **From this landing:** findings 1 (the `classicIsBase` shape, for the orchestrator to confirm), 2 (the organizer's
  prompt version with offers on, expected) and 3 (the load flake).
