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
  reuses by input hash (spec version `ifs-v1`; the hash already carried the origin).
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
