# Figures and explanation videos strategy (K10, 2026-11-14)

Refactor arc K, step K10, job 2. It stands on the map `docs/reviews/k10-figures-map-2026-11-12.md` (ids F10P, F10D, F10B, F10O, F10F, F10C, F10H, F10U, F10V are the map's), re-checked at this tip (§0). **Base: main `f623e525ac`**, branch `refactor/k10-figures-strategy`. Docs only: no file under `src/`, `apps/` or `tests/` changed. **Status: for the owner's review.**

**Evidence** is `file:line` at `f623e525ac`, with the map's convention: `src/learnloop/` is dropped (`figures/service.py:2485` is `src/learnloop/figures/service.py:2485`), `learnloop_sidecar/` keeps its prefix, frontend paths start `apps/`. Counts come from an AST sweep run at this tip (the script and its output are in the orchestrator's scratch, `refactor-k10s/k10s_sweep.py`, `sweep.txt`, `k10s_stage.py`; it imports `scripts/refactor_measures.py`'s import graph and nothing from `learnloop`). Every estimate says so.

## Summary for the owner

**What is wrong.** "Show me" works and much of it is careful: one admission gate, a sealed sketch engine, a sandboxed video render, a pure pre-build model, records for every author attempt. What costs you is three things. Two learner-visible bugs: cancelling a press doesn't cancel it, so its paid calls run and the figure appears anyway, and a figure withheld when it is delivered disappears without a word. Failures you can't ask about afterwards: a video build keeps one reason, a refused request leaves no row, and the reason a tier wasn't offered is computed and dropped. And one 3,959-line module (`figures/service.py`, 78 public names, a 304-line author loop) holds eight jobs, with "may this figure go out now?" answered by about twenty functions in six modules. Every feature switch (thirteen under `[figures]`, all on by default) also keeps its off-path reproducing its predecessor byte for byte, so the prompt version is built from five flags and each press computes up to eleven reuse keys (its own and five other settings', each doubled when the author is sent a learner state: `figures/service.py:2170-2182`).

**The moves that matter:**
1. **Fix the two learner-visible bugs and the lost video trace first** (K10.1-K10.3, each small, from a failing test). Cancel becomes a hold on the build's existing gate, which already checks before every model request and before storing, so no new mechanism is needed.
2. **Pin what nothing pins, then split `service.py` by who calls it** (K10.4-K10.8). The figures' reuse key is in none of K0's identity pins, so that comes first. The split is moves only, in the shape of K2.5, which paid, and not of K2.4, which unified two paths but grew its files. Protection gets one module that states the rule, and that move also ends the package's import cycle.
3. **Make the author loop's rules testable with plain values** (K10.9). Reading the model's answer becomes a pure function that returns its verdict and its record code. It has a stop rule: if it starts growing a K2.4-style configuration record, only the storage part is extracted.
4. **Record why** (K10.11, K10.12): a refusal, a reuse, the tiers left off the menu, and every attempt of a video build.

**What you must decide** (§9 has the detail):

| # | Question | Recommendation | If yes / if no |
|---|---|---|---|
| Q1 | Retire the eight figure content switches that are on by default and only reproduce a predecessor when off (predictions, region, revisions, advanced panels, offers, show me, sketch, checked labels)? | **Yes**, in one step after the split (K10.16). Keep `figures.enabled`, the rich tiers and the Manim opt-in, pre-builds, the help kind and the author's learner state. | Yes: the V1/V2 output contracts, the conditionals that assemble the prompt version, the alternate reuse keys computed per press (kept as a legacy reader until a count says no stored figure needs them), and three of the view's switch-dependent keys go. You lose the ability to turn those features off one by one. No: every later change keeps preserving 2^k variants (F10C2). |
| Q2 | Remove the dormant `js_animation` tier (never on a menu: `figures/rich.py:86`) until its IPC probe passes? | **Yes** (K10.17, S). The spec keeps the design. | Yes: 20 lines in 7 source files go; re-adding later costs about the same. No: nothing breaks; it stays a tier no one can reach. |
| Q3 | Should the phone (or MCP v2) get figures? | **Your call on the product.** The structure answer depends on it: the attempt-host rules move out of the sidecar handler (K10.13) only when a second frontend will call them. | Yes: K10.13 runs before that frontend's figure step. No: K10.13 is not worth doing and stays parked. |
| Q4 | Should a pressed quick build survive a restart (a durable queue job, like a video)? | **No.** K10.1 makes cancel real; a paid answer already survives by its checkpoint, so a re-press after a restart costs nothing. | Yes: a new job type with leases, and a slower start, for "you don't have to press again". No: four execution models stay (F10D1), each with a stated reason. |

You also own one count, run on your vault (agents don't open it): how many stored figures exist per `prompt_version` and how many rows still have the legacy `verification = 'verified'`. It decides when K10.16's legacy reuse reads and `shown_row`'s legacy path can go.

**What stays as it is, and why:**
- **The sandboxes and every model-written-code boundary**: the sealed QuickJS-wasm sketch engine pinned by digest, the bubblewrap render inside a capped `systemd-run` scope, the PF sandbox for claims and the book-math check, the desktop's sketch compartment and frame guard, `llmedia://`. No step edits them (§4.6).
- **Python verification reading the desktop's wasm by path** (F10P3): it's deliberate, so both sides run the same engine bytes.
- **The pre-build model** (`figures/prefetch_model.py`): already pure, documented as equations, seeded and recorded.
- **`FiguresGate`**: one admission mechanism, rechecking before every request. K10.1 uses it.
- **Protection's rechecks at request, build, delivery and every read**: deliberate, because the configuration and the exam material can change mid-build. They get one module, not fewer checks.
- **The rich job's intent stored with its quick figure** (F10D4): the second copy is what lets a crash between commit and enqueue recover the job (`figures/service.py:2759-2760`).
- **Tiers implemented twice, once to author and verify and once to draw**: that is inherent in the design, not a structure problem.

**Cost.** Seventeen steps: seven S, nine M, and one M parked on Q3. About 1.5-2 weeks of queue at the strategy's pace, with the three fixes about a day together. That is an estimate (§5).

## 0. The map at this tip

The map was written at `c4556cc700`. Main has moved 330 commits, but only two touched the scope: K1-7's docstring in `figures/service.py`'s `withheld_message` (`8e2dfad2d4`, three lines longer) and the K2.1 and K2.3 edits to `content/pipeline/jobs.py`. `git diff c4556cc700 f623e525ac` is empty for `apps/learnloop-tauri/src/screens/reader/figures/`, `components/askFigures.tsx`, `figure_admission.py`, the sidecar handler, `teacher/visuals.py`, `prefetch_runtime.py`, `db/stores/figures.py`, `concept_animation.py` and every other figures module.

**Where the map is now wrong, or was:**

| # | The map says | At this tip | How counted |
|---|---|---|---|
| 1 | `figures/service.py` is 3,956 lines; `_author_attempts_and_store` at `:2482`, `_build` at `:2116` | 3,959 lines; every line after `:558` moved down 3 (`:2485`, `:2119`). `content/pipeline/jobs.py`: `handle_figure_rich` `:3855` (was `:3871`), `enqueue_figure_rich` `:5051` (was `:5067`) | AST sweep; `git diff` |
| 2 | 31 of `service.py`'s 78 public names have no caller outside it, 11 of those test-only; `request_hash` is grouped with the sidecar's callers (§1.2) | **33** with no caller outside `service.py` in `src`, **12** test-only. `request_hash` has no `src` caller outside `service.py` (26 test references). `offered` (`:431`) and `SpawnRich` (`:2009`) are the other two the map missed | AST sweep resolving `from … import` and module aliases; grep for `.request_hash(` outside `service.py` finds none |
| 3 | `service.py` holds "twelve one-line switch wrappers over `figure_admission`" (§1.2, F10P5) | Twelve switch functions, but only seven delegate to `figure_admission`: `enabled` `:399`, `advanced_enabled` `:490`, `figure_offers_enabled` `:496`, `show_me_enabled` `:502`, `help_enabled` `:508`, `sketch_switch` `:516`, `rich_enabled` `:534`. `teacher_visuals_switch` `:367` reads the config itself. `predictions_enabled`, `region_enabled` and `revisions_enabled` (`:478-488`, through `_switch` `:474`) have **no** `figure_admission` predicate. `sketch_enabled` `:522-531` is not a wrapper: it adds the engine check. | read |
| 4 | `prefetch` imports `service` function-locally 11 times | 10 (`figures/prefetch.py:320`, `:332`, `:463`, `:586`, `:671`, `:801`, `:959`, `:1353`, `:1628`, `:1729`; the map's own list has 10) | grep |
| 5 | The horizon code holds "15 of the module's 26 `execute` calls (`:1469-1642`)" (§5) | 12 of 26 (`:1469`, `:1473`, `:1482`, `:1528`, `:1534`, `:1544`, `:1557`, `:1559`, `:1572`, `:1594`, `:1609`, `:1642`). The 26 total holds, and `prefetch_ledger.py` has 12 | grep `execute(` by line |
| 6 | No module in scope is in the codebase's large import cycle (§1.3) | True of `figures/`: the largest component is now 188 modules and holds none of them. But `learnloop_sidecar/handlers/figures.py` is in the sidecar's **36-module** component (with `context`, `library_ask`, `prefetch_runtime`, `reader`, `tutor_qa`, `sessions` and 29 more), and it and `prefetch_runtime` import each other (`learnloop_sidecar/prefetch_runtime.py:99`, `:189`; the handler's local import of `prefetch_runtime` in `reader_figures`) | `refactor_measures.strongly_connected` over top-level and function-local edges |
| 7 | About 630 comment and docstring lines name a stage or round (§6.1) | 599 distinct lines with the map's eight patterns across the same 30 files. M0's ratchet regex, which counts inline comments only (`scripts/refactor_measures.py:403`), counts **160** in those files: 57 in `service.py`, 27 in the sidecar handler, 20 in `rich.py`, 13 in `prefetch.py` | grep with the map's patterns; `refactor_measures.lean_facts` |
| 8 | (not stated) | No K0 identity pin covers a figure identity: `tests/goldens/identities.toml` (152 lines) has no entry for `request_hash`, the request identity, the prompt versions or the output contracts. A few tests compare keys with each other (`tests/test_figure_rich_contract.py:86-93`, `tests/test_figure_rich_rereview_fixes.py:32-40`), and one golden pins the grammar prompts (`tests/fixtures/figure_prompts_golden.json`: two pressed builds and one pre-build pass, no sketch, no rich menu, no learner state) | grep |

**What I re-checked and found as the map says:** the sizes of every other module in scope (within a line or two); the single 304-line function and the four over 120 (`figures/sketch_verify.py:610`, `figures/sketch.py:457`, `:680`, `figures/service.py:2119`); the four-module cycle `service` ↔ `rich` with `routes` and `prefetch_ledger`, closed only by function-local imports, and what each edge imports (`ALL_SPEC_VERSIONS`, `RICH_BRIEF_MAX`, the three protection functions); `rich`'s copy of `ATTEMPT_HOST_REFS` (`figures/rich.py:365` against `figures/service.py:208`); cancel (`learnloop_sidecar/handlers/figures.py:708-716` only sets `job.cancelled`; `_start` `:241-276` never passes it on); the unread `withheld` (`apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts:322-338` drops the line when `figure` and `rich` are both empty); the rich enqueue writing no `job_enqueued` record (`content/pipeline/jobs.py:5051-5070`; `record_job_enqueued` is called only from `db/stores/{diagnoses,followup_serve,learner_gaps}.py` and `diagnosis/chain_records.py`); the gate's refusal record with no subject and no sub-code (`refusal_records.py:269-275`); the presentation chain copied in `section_figures` (`figures/service.py:3571` against `:1577`); the literal "shown" set (`teacher/visuals.py:277`, `:340`; `apps/learnloop-tauri/src/components/askFigures.tsx:128`, `screens/reader/figures/FigureInline.tsx:569`, `useFigures.ts:331`); the attempt-host section of the handler (`learnloop_sidecar/handlers/figures.py:961-1470`) with its raw SQL (`:1115-1117`, `:1139-1140`) and the borrowed private `_item_cold` (`:1072-1075`); the 14 RPCs (`:84-99`); the two stale vault lines.

**Where "Show me" is offered at this tip.** Backend: the 14 RPCs of `learnloop_sidecar/handlers/figures.py`; the hint chooser's `explore_figure` (`learnloop_sidecar/handlers/hints.py:252-281` → `figures/help.py:383`); the lesson turn's builder (`learnloop_sidecar/handlers/lesson.py:172-186`); figures following a section (`learnloop_sidecar/handlers/correspondents.py:213`); five pre-build triggers (`learnloop_sidecar/prefetch_runtime.py:156-199`). Desktop: two request hooks, `useFigures` (the Reader: `ReaderScreen.tsx`, `AskRail.tsx`, `TutorOffers.tsx`, `intentPalette.ts`) and `askFigures` (the Ask panel in `AskOverlay.tsx`), plus `LessonScreen.tsx`. Two other buttons say "show me" and are not figures: active reading's reveal of the book's step (`apps/learnloop-tauri/src/screens/reader/ActiveReadingCard.tsx:165`, `useActiveReading.ts:235`) and the workbench's "show me a similar example" (`screens/workbench/RouteExample.tsx:28`). That's for the UX audit (§7).

## 1. What K2.4 and K2.5 teach for this area

K2.4 made bootstrap and append one synthesis run. It worked, and the copies stopped drifting. But the two files grew by 106, 6 and 96 lines over its three sub-steps, about 210 in all (`docs/reviews/refactor-k2.4a.md:66-75`, `refactor-k2.4b.md:140-148`, `refactor-k2.4c.md:149-162`). The kept differences became fields on a `SynthesisMode` record: five booleans, then seven more fields, then a ten-value call record. That is about thirty fields a reader must learn before the shared function makes sense. It paid there because 12 of the 15 append commits since Oct 1 had also edited bootstrap. The copies were drifting in practice.

K2.5 moved a 1,081-line frame into named stage functions over one state, in its own module. It changed no line of logic and was proven by AST identity and coverage. The longest function went from 1,081 to 175 lines (`docs/reviews/refactor-k2.5.md:104-106`). It paid at once and had nothing to learn.

**For figures, this means:**
- **Move, don't unify.** What is duplicated here is mostly predicates composed differently for different callers: the protection functions, the tier rules, the "shown" set. A "protection mode" or "host mode" record that unifies them would be K2.4's `SynthesisMode` again, with no drift to justify it. The figures commits don't show the copies drifting apart; they show new copies being added for new paths. So the strategy gathers each question's functions into one module, side by side under a docstring that states the rule. It merges two functions only where they are equal on every input (K2.4a's class ii).
- **A pure core only where a test gets simpler.** The author loop's answer reading is worth extracting: today the loop can't be tested without a gate, a route and a vault (F10F2). The pre-build horizon rules aren't: twelve SQL reads around short rules. L4's stop rule applies throughout: if a split adds more lines than it removes and no test gets simpler, it stops.
- **Every structure step reports its net lines.** The split of `service.py` will add lines: each new module brings imports and a docstring. The estimate is 150-250 lines across K10.6-K10.8. That's the price of locality, and the step says so instead of claiming a smaller package. What shrinks the package is deletion: the switch wrappers (K10.5), the dormant tier (K10.17), and the retired switches' variants (K10.16).

## 2. The problems, ranked by what they cost

| # | Problem | What it costs you | Map | Evidence at this tip | Steps |
|---|---|---|---|---|---|
| 1 | **Cancel doesn't cancel.** The pressed build's thread is never told; both author calls (and the grounding retrieval's) can still be paid, and the figure lists on the next read. | Money, and a figure you cancelled turning up | F10D2, F10U3; K10-1 | `learnloop_sidecar/handlers/figures.py:708-716`, `:275`; `learnloop_sidecar/handlers/library_ask.py:205-214` (`fenced`, unused here) | K10.1 |
| 2 | **A figure vanishes.** Withheld at delivery: the Reader drops the pending line with no word. A stored spec that no longer parses, or a version chain whose pick is withheld now, also leaves the list silently. | A press that seems to do nothing | F10U1, F10D5, F10U7; K10-2 | `learnloop_sidecar/handlers/figures.py:184-185`; `useFigures.ts:323-340`; `figures/service.py:3539-3543`, `:3233-3234` | K10.2, K10.11 |
| 3 | **Failures with no stored answer.** A video build keeps one reason. A refused request leaves no row. The reasons a tier was off are dropped. The gate's `held` has no sub-code and no subject. The video job's records don't join the press's trace. | "Why did the video fail?" and "why didn't Show me work yesterday?" can't be answered | F10O1, F10O2, F10O3, F10O5; K10-3 | `figures/rich.py:783-864`, `:985-988`; `figures/service.py:1945-1993`; `figures/rich.py:126-160`; `refusal_records.py:269-275`; `content/pipeline/jobs.py:5051-5070` | K10.3, K10.11, K10.12 |
| 4 | **"May this figure go out now?" in about twenty functions across six modules**, plus the `service` ↔ `rich` cycle that exists only so `rich` can ask `service`'s predicate. | A new host or tier has to find every one, and a missed one is a leak path | F10B1, F10P2 | `figures/service.py:554-806`, `:3380-3459`; `figures/rich.py:422-446`, `:653-730`; `figures/prefetch.py:315-355`, `:957-1004`; `figures/learner_state.py:420`; `figures/help.py:383` | K10.6 |
| 5 | **`service.py` is eight modules in one**: 3,959 lines, 78 public names (33 unused outside it), a 304-line author loop and a 124-line `_build`, and a 142-line module docstring that is a stage history. | Every change scrolls past seven unrelated jobs; 44 test files import it | F10P1, F10C1 | §0 rows 1-2; `figures/service.py:1-142`, `:2485-2788`, `:2119-2242` | K10.5-K10.9 |
| 6 | **Every switch multiplies variants.** The prompt version is built from five flags (`figures/routes.py:430-437`). The reuse key is computed for the current setting and five others, and doubled with a learner state (`figures/service.py:2172-2182`). The view's keys change with four switches, the prompt contract's with six. | Each change must preserve every off-path byte for byte; the frontend handles every combination | F10C2, F10B5 | as cited; `learnloop_sidecar/handlers/figures.py:102-131` | K10.16 (Q1) |
| 7 | **A new tier costs about fifteen places in seven modules plus the desktop**, and "attempt hosts and lessons are quick-only" is enforced five times. | The next tier (or `js_animation`) is a 15-60-file stage | F10H1, F10B4, F10C3 | map §3.2's list, lines unchanged | K10.9, K10.10, K10.14, K10.17 |
| 8 | **The desktop re-derives what the server decided**: "shown" in three files, all three tiers' badges (the server's `label` unused, its wording different), the quick-only rule. It branches on an English label string. | Two vocabularies for one figure; a server change the desktop doesn't see | F10B3, K10-5 | `FigureInline.tsx:128-133`, `:569`, `:595-596`; `RichFigure.tsx:67-72`; `askFigures.tsx:81-83`, `:128` | K10.14 |
| 9 | **The attempt-host policy is in the sidecar handler**: host resolution with raw SQL, the take step, one hint-equivalent per figure, the reveal rows, the cost line. It is the file co-edited most with figures (28 of 109 commits). | A second frontend would re-implement it | F10B2, F10H2 | `learnloop_sidecar/handlers/figures.py:961-1470` | K10.13 (Q3) |
| 10 | **No note explains the feature**; two vault lines are stale. | A contributor's only map is the stage-history docstring | F10V1, F10V2; K10-4 | `docs/learnloop-architecture-vault/Architecture/AI Architecture.md:53`; ADR-017 `:61` | K10.15 |
| 11 | Small: `js_animation` unreachable but in 7 source files; a third number formatter (`figures/help.py:115-172`); six wall-clock reads outside the injected clock; the source check writing block health while it checks (`figures/source_check.py:167-181`). | Noise | F10C4, F10B6, F10F4, F10D6 | as cited | K10.17; the rest only when a step touches them |

## 3. Principles for this area

**1. The functional core, named.** Pure today, callable with plain values: the pre-build model's arithmetic (`figures/prefetch_model.py`: `Model.decide` `:580-592`, `wait_estimate` `:358-385`, `open_posterior` `:226-241`, `pause_posterior` `:312-325`); the grammar's parse and numeric verification (`figures/spec.py`, `figures/verify.py`); the parsers' prediction salvage (`spec.parse_author_spec`, `sketch.parse_author_sketch`); `request_hash` (`figures/service.py:1709-1778`); the labels (`figures/labels.py`); `display_format`; the record builders (`figures/records.py`). Nearly pure, but for a sealed engine or a budget clock: `sketch_verify.verify_sketch` (`figures/sketch_verify.py:610`), `manim_figure.check_claims` (injectable runner).

Pure decisions hidden among reads and writes, and whether each is worth extracting:

| Decision | Where | Extract? |
|---|---|---|
| What the author's answer is and what happens next (retry with problems, salvage, end with a code) | inside `_author_attempts_and_store` (`figures/service.py:2551-2702`) | **Yes** (K10.9): the loop becomes testable with literal answers, and the core returns its record code (L6) |
| Which tiers are on the menu, and why each other one is off | `rich.tiers_allowed` `figures/rich.py:181-191` over probed facts (`manim_runtime_state` `:126-160` already returns the reason) | **Yes, small** (in K10.11): the rule takes the probed facts and returns the menu and the reasons, which gives F10O3's record for free |
| What a stored figure shows now | `_presented_row` `figures/service.py:1574-1585`, copied at `:3571` | **Already a chain of small functions.** K10.10 removes the copy; nothing to extract |
| Admission (the gate's verdict) | `figure_admission.py:405-430` | **No.** It is short, it is the shell's job, and it is tested |
| The pre-build queue verdict (`build`, `deferred_power`, `deferred_plan`, `capped`) | `figures/prefetch.py:1134-1146`, 13 lines inside `decide_and_log` | **Not in K10.** L4's review covers `figures/prefetch*` (strategy §2.18). My read: worth it only if `figure_prebuild` is rebuilt from the returned verdict under L6 |
| Pre-build horizon outcomes | `figures/prefetch.py:1505-1676` | **No.** Twelve SQL reads around short rules; the split would add lines and simplify no test |
| Verification verdicts | the verifiers above | Already pure or nearly |

**2. The shell, named.** Jobs: the in-memory `LibraryJobs` press (`learnloop_sidecar/handlers/library_ask.py:256-318`), the durable ingest queue for videos, the lesson turn's thread, the pre-build drain thread (`learnloop_sidecar/prefetch_runtime.py:37-92`). Sandboxes: the wasm engines, bubblewrap, the PF sandbox. Storage: `db/stores/figures.py`, judgments, records, media files. Model calls: `FigureRoute.ask` under the gate. Machine probes: `manim --version`, `bwrap`, power. A step may move a decision out of the shell. It never moves the shell into a core.

**3. Move, don't unify, unless the copies drift** (§1). A module boundary is drawn by who calls a group of names (§4, K10.6-K10.8), not by a new abstraction.

**4. What one figure request's trace must answer**, from stored rows, after K10.3, K10.11 and K10.12:
- that it was asked, from which host and origin, by whom (goal author);
- admitted or refused, and the rule code (exam material, a switch, a cold check, not offered, validation, spend);
- the tier menu, and the code for each tier left off (switch, opt-in, `no_bwrap`, `no_manim`, `off_linux`, lesson host, attempt host);
- reused (and which key matched) or built;
- each author attempt's verdict and code (B4 has this today), the tier chosen and its reason;
- the verification verdict per tier, and the source check's outcome;
- stored, or stopped by the gate with its rule and, for `held`, why (protection, power, plan, cancelled);
- for a video: enqueued in the same trace, each rich attempt, the render and its repair, stored or stopped with the job's code;
- delivered, withheld at delivery, or dropped from a list, and why.

It keeps ids and codes only, never prompts or learner text (strategy §4: "storing prompts or free text in records").

**5. The security boundaries are frozen** (§4.6). A structure step that would need to change one stops and goes to the owner.

**6. Comments.** Moved code keeps its comments byte for byte, as K2.5's did, so the move's proof stays an AST identity. The new modules get docstrings that describe them, and `service.py`'s 142-line stage history goes when the module is split (K10.8). Functions a step rewrites (the author loop in K10.9, the presentation in K10.10) get the convention (strategy §2.1): reasons kept, round names dropped, an approach header over 100 lines. There is no separate sweep.

## 4. The steps

**Every step** follows §2.1 of `docs/specs/refactor_strategy_v3.md` and the rules block: one implementer in a worktree; targeted tests under the memory cap; `lint-imports`; `ruff check`; the vault validators; `tests/test_identity_pins.py` and `tests/test_structure_ratchets.py`; the phase's adversarial review (§2.19).

**Named proofs**, beyond §4 of the strategy:
- **P-fail:** a test that fails before the change.
- **P-golden:** K10.4's goldens (prompts, stored rows, judgments, decision records, views and lists for a fixed matrix of fake model answers and fixed sandbox and engine results) identical before and after.
- **P-pins:** K0's identity pins, with K10.4's figure pins, unchanged.
- **P-ast:** every moved function's AST, comments and docstrings removed, identical to its source (A3's and K2.5's method).
- **P-draw:** the pre-build pass at a pinned seed draws the same; `figure_prebuild` records identical.

No step changes learner scoring, so none needs a successor tag.

### 4.1 Behaviour track: the three ledger bugs (fix first)

These land alone, each from a failing test, before or beside anything else (ledger: K10-1 and K10-2 are learner-visible and go first).

**K10.1. Cancel stops the build** (S). Behaviour. K10-1; F10D2, F10U3.
- **Problem:** `reader.figure_job_cancel` sets `job.cancelled` and nothing reads it (`learnloop_sidecar/handlers/figures.py:708-716`). `_start` hands `build_figure` no way to see it (`:241-276`). So the second author call is still sent, the row is stored, and `reader.figures` lists it.
- **Does:**
  - `_start` takes the job through `LibraryJobs.start(..., on_job=...)`, which already exists (`learnloop_sidecar/handlers/library_ask.py:256-280`), and passes `cancelled=lambda: job.cancelled` to `build_figure`.
  - `build_figure` folds it into the gate's `hold` beside the pre-build hold (`figures/service.py:2091-2092`). `FiguresGate` already asks `hold` before every physical model request and at `gate.check("store")` (`figure_admission.py:405-430`; `figures/service.py:2754`, `:2949`, `:3067`). So a cancelled build sends nothing more and stores nothing.
  - A paid first answer keeps its checkpoint under the request identity (`content_key(input_hash, generation)`, `figures/service.py:2229`), so a later press of the same input recovers it with no call.
- **Must not touch:** `LibraryJobs` for the library's other kinds; `fenced`; the gate's rules (`held` stays the rule, and K10.11 adds sub-codes).
- **Left as is, and said so in the record:** a build that passed its last gate check before the cancel landed commits. That figure was paid for and finished, and showing it is honest.
- **Files:** `learnloop_sidecar/handlers/figures.py` (`_start`), `figures/service.py` (`build_figure`'s signature and its hold), a new test file.
- **Deletes:** nothing. **Abstraction:** none (one keyword argument).
- **Proof:** P-fail `tests/test_figure_cancel.py::test_cancel_before_the_second_attempt_sends_nothing_more_and_stores_nothing`: a fake author whose first answer fails verification and blocks on an event; cancel; release. The author made one call, `interactive_figures` has no row, and `reader.figures` lists none. P-fail `::test_a_cancelled_press_is_recovered_free_by_the_next_press`: the same input pressed again makes no new author call for the checkpointed attempt. P-golden for an uncancelled press. **Vault:** none. **Size:** S.

**K10.2. The Reader says when a figure is withheld** (S). Behaviour (desktop). K10-2; F10U1.
- **Problem:** `deliver_figure` returns `{"figure": null, "withheld": true}` (`learnloop_sidecar/handlers/figures.py:184-185`). `useFigures` reads only `figure` and `rich`, so the pending line goes and nothing is said (`apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts:322-338`). The DTO declares `withheld` (`apps/learnloop-tauri/src/api/dto.ts:9709`).
- **Does:** when the finished job's result says `withheld`, the pending line stays as a failed line with code `withheld` and the Reader's existing words for it (`FigureInline.tsx:91`: "that passage is held out"). The Ask panel already shows its generic failed line, so it stays. The final wording is the UX audit's.
- **Files:** `useFigures.ts`, `FigureInline.tsx` if the line needs the code mapped, `readerFigures.test.tsx` (or a new vitest beside it).
- **Proof:** P-fail (vitest): a job that finishes `{figure: null, withheld: true}` leaves a failed line with code `withheld`; it fails at the base. **Vault:** none. **Size:** S.

**K10.3. A video's job continues the press's trace** (S). Behaviour (records only; nothing served changes). K10-3.
- **Problem:** `enqueue_figure_rich` writes no `job_enqueued` record (`content/pipeline/jobs.py:5051-5070`), and nothing in the ingest runner calls `continue_job_trace` (it's called from `diagnosis/text_gaps/jobs.py:530`, `diagnosis/split/jobs.py:327` and `followup_run/jobs.py:92` only). So a video's receipts and records can't be joined to the press. The press's own thread does carry the request's trace (`learnloop_sidecar/background_jobs.py:92-102`).
- **Does:** `enqueue_figure_rich` writes `record_job_enqueued(queue="ingest_jobs", job_kind="figure_rich", facts={build_mode})` once the batch row exists (`db/stores/provenance.py:254`). `handle_figure_rich` (`content/pipeline/jobs.py:3855`) opens a trace scope for the job and calls `continue_job_trace` first.
- **Check in step 0:** whether the ingest worker opens a scope per job. If it doesn't, the handler's own scope must end with the job, so the next job on that thread doesn't inherit the trace (`learnloop_sidecar/post_attempt_worker.py:244` is the pattern).
- **Order:** before K2.7, which moves the job handlers out of `jobs.py`, or after it in its new home, but not beside it.
- **Files:** `content/pipeline/jobs.py`, a test.
- **Proof:** P-fail `tests/test_figure_rich_job.py::test_the_rich_job_continues_the_press_trace`: a press that enqueues a rich job, then the job run with a fake renderer whose gate refuses (a `figure_admission` record). The job's record carries the press's `trace_id` and the `job_enqueued` record is its parent. **Vault:** ADR-017's inventory row for figures. **Size:** S.

### 4.2 Characterize first

**K10.4. Pin the figure identities and golden the build** (M). Structure (tests only). Nothing pins these today (§0 row 8).
- **Problem:** a structure step that moves `request_hash` or the prompt assembly by one byte silently orphans every stored figure: each later press re-pays, as arc C's removal did to synthesis (strategy §2.1, "Identity rules"). The only build golden covers two grammar presses and one pre-build pass.
- **Does:**
  - **Identity pins** (`tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`): `request_hash` through its production path at fixed inputs over the matrix the build computes (panels on and off, sketch on and off, a rich menu, a show-me goal with each grounding, a learner state, `source_check_id`, `different_kind`), each of the five alternate settings, and the recorded-inputs twin; the request identity `content_key({input_hash, generation})`; every `author_prompt_version` combination and `RICH_PROMPT_VERSION`; the JSON schemas of the V1, V2 and V3 output contracts and of the rich author's; `rich_build_key`'s billing members. Shape pins for the types whole-dumped into them (`FigureRequest` fields read by the key, the region).
  - **A build golden** (`tests/fixtures/figure_build_golden.json`, written with `FIGURE_BUILD_WRITE_GOLDEN=1` like the prompt golden). For each case: the prompts sent; the rows written to `interactive_figures`, `figure_requests`, `judgment_ledger`, `figure_source_checks`, `help_assists`, `reveal_events`, `ingest_jobs` and `decision_records` (ids, times and the trace replaced by stable tokens); and the view and the list. Cases: grammar accepted; grammar failed twice; a label-text repair; a dropped prediction; a sketch accepted; a sketch that fails in the engine; V3 Manim with a quick spec; V3 Manim only; unsupported; a source check that differs, then passes; a reuse under another setting; a revision; an attempt host (help rows, reveal); a lesson visual (its status); a delivery withheld.
  - **A rich job golden**, with the fake client, renderer and function runner the tests already have (`tests/figure_rich_job_helpers.py`): success; a claim that fails on attempt 1; a render failure and its repair; each `RichJobStopped` code.
  - **Coverage first**, as K2.5's step 2 did: a `sys.monitoring` run over the functions K10.6-K10.9 move, listing the lines no golden case reaches. Each gets a case or a line in the record saying why not.
- **Ports first (strategy T4).** Tests patch `service`'s public names, and after a move such a patch silently patches nothing: `FS.withheld_message` (7 sites), `FS.search_spans` (4), `FS.prefetch_plan_waits` (4), `FS.item_passages` (3) (grep of `setattr(FS, …)` in `tests/`). Each is ported to patch the one owner that doesn't move (`content/sources/exam_material.spans_withheld`) or to a fake through a public argument. None is pointed at a new location.
- **Files:** `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, a new `tests/test_figure_build_golden.py` with its fixture, the ported tests.
- **Deletes:** nothing. **Abstraction:** none.
- **Proof:** the pins and goldens pass at the tip. Each pin fails on a scratch edit: swap two members of `request_hash`'s key; flip a suffix's order in `author_prompt_version`. **Vault:** none. **Size:** M.

### 4.3 Structure track: the god module, split by who calls it

`figures/service.py`'s public names fall into these groups. Callers are from the AST sweep at this tip; line spans are the groups' top-level definitions.

| Group | Names | Lines (span) | Callers outside `service.py` | Goes to |
|---|---|---:|---|---|
| Switches | `enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled`, `advanced_enabled`, `figure_offers_enabled`, `show_me_enabled`, `help_enabled`, `sketch_switch`, `rich_enabled`, `teacher_visuals_switch`; `sketch_enabled` | about 70 (`:367-537`) | the sidecar handler (17 call sites), `teacher/visuals.py:67`, `learnloop_sidecar/handlers/correspondents.py:90`, `figures/help.py:416` | `figure_admission` (deleted here; K10.5) |
| Protection | `withheld_message`, `keys_withheld`, `row_withheld`, `learner_state_withheld`, `inherited_learner_inputs`, `figure_homes`, `show_me_row`, `figure_withheld`, `item_passages`, `rich_base_keys`, `rich_base_item_protected`, and their private helpers | about 330 (`:554-806`, `:3380-3459`) | `figures/prefetch.py` (8 sites), `figures/rich.py:423`, `:444`, `figures/help.py:416`, `:433`, `cli/reader.py:128`, the sidecar (`handlers/figures.py:184`, `:680`; `handlers/hints.py:351`), `teacher/visuals.py:334` | `figures/protection.py` (K10.6) |
| Request and admission keys | `FigureRefused`, `FigureRequest`, `attempt_hosted`, `lesson_hosted`, `anchored`, `show_me_input`, `offered`, `prediction_home`, `build_key`, `offer_build_key`, `show_me_build_key`, `key_for`, `check_request` (with `_validated_request`, `_validated_prefetch`) | about 390 (`:257-473`, `:1820-1993`) | the sidecar (`check_request` 3 sites, `FigureRequest`, `FigureRefused` 12 sites), `teacher/visuals.py:207`, `figures/prefetch.py:335`, `:1419` | `figures/request.py` (K10.7) |
| Context and grounding | `SourceContext`, `Grounding`, `source_context`, `passages_context`, `FindSources`, `ground`, `crop_image` | about 230 (`:808-1037`) | `figures/prefetch.py:335` (`source_context`); the rest only the build | `figures/grounding.py` (K10.7) |
| Presentation | `shown_row`, `advanced_off_row`, `sketch_row`, `sketch_off_row`, `rich_off_row`, `rich_row`, `reverify_hash`, `sketch_rechecked`, `worded_row`, `drawable_now`, `property_checks`, `figure_view`, `source_rejected`, `redelivered_view`, `fuller_state`, `rebuild_request`'s view half | about 670 (`:1041-1708`) | the sidecar (`:190`, `:1512`), `teacher/visuals.py:337-339`, `figures/help.py:413-421` | `figures/view.py` (K10.8) |
| Listing | `list_figures`, `section_figures`, `rich_pending`, `shown_figure`, `prefetch_pending`, `prefetch_plan_waits`, `stored_plan_open_items`, with `_listed` and the pre-build cue budget | about 560 (`:3172-3378`, `:3461-3788`) | the sidecar (`:740-753`, `:1506`), `learnloop_sidecar/handlers/correspondents.py:213`, `figures/prefetch.py:1746` | `figures/listing.py` (K10.8) |
| Predictions | `record_prediction`, `record_explanation` | about 115 (`:3789-3900`) | the sidecar (`:906`, `:942`) | `figures/predictions.py` (K10.8) |
| Build | `request_hash`, `BuildOutcome`, `SpawnRich`, `build_figure`, `retry_rich_job`, `ensure_rich_job`, `resume_rich_intents`, `revision_request`, `rebuild_request`, `rich_revision_retry`, `build_prefetch_figure`, the author loop, storage, `_RichSpawn` | about 1,350 (`:1709-1819`, `:1997-3171`, `:3513-3530`) | the sidecar (`build_figure` `:262`, `:840`; `retry_rich_job`, `resume_rich_intents`, `revision_request`), `learnloop_sidecar/handlers/lesson.py:180`, `figures/prefetch.py:1431` | stays; renamed `figures/build.py` at the end of K10.8 |

**The order that keeps every landing green** follows the import direction, leaves first. Each moved module imports only what is below it, so no step adds a cycle. Protection imports nothing of the build. The request module asks protection (`check_request` asks the exam predicate). Grounding needs the request's types and protection's recheck. The view needs neither the build nor the request, but listing needs the view and protection. The build needs everything. Each step updates every caller in `src` and `tests` (moves of public names; T4 governs only private ones, and K10.4 ported the patches). `service.py` keeps no re-export: a name lives in one module.

**K10.5. One name per switch** (S). Structure. F10P5, §0 row 3.
- **Problem:** a switch has two names, and callers use both. Three switches (`predictions_enabled`, `region_enabled`, `revisions_enabled`) exist only in `service.py`. Two raw config reads skip the `figures.enabled` parent: `figures/prefetch.py:987` (`show_me_enabled`) and `learnloop_sidecar/prefetch_runtime.py:183` (`offers_enabled`).
- **Does:**
  - The three `_switch` predicates move into `figure_admission.py` beside the other thirteen.
  - The seven delegating wrappers and `teacher_visuals_switch` are deleted; callers ask `figure_admission`, and `teacher.visuals` gets its predicate there.
  - `sketch_enabled` stays, renamed `sketch_ready` and moved to `figures/sketch_engine.py`: it is the switch plus the engine check, a different question.
  - The two raw reads use the predicates. Behaviour is the same on every reachable input: both passes run only with figures on (`learnloop_sidecar/prefetch_runtime.py:137-146`). A test states it.
- **Deletes:** about 60 lines from `service.py`, and `_switch`.
- **Files:** `figure_admission.py`, `figures/service.py`, `figures/sketch_engine.py`, `figures/prefetch.py`, `figures/help.py`, `teacher/visuals.py`, `learnloop_sidecar/handlers/{figures,correspondents}.py`, `learnloop_sidecar/prefetch_runtime.py`, their tests.
- **Proof:** P-golden; P-pins; P-fail-style check that a pass with `figures.enabled` off and `show_me_enabled` on excludes goal candidates (it does today by context; the test makes it construction). **Size:** S.

**K10.6. Protection in one module; the package's cycle cut** (M). Structure. F10B1, F10P2.
- **Problem:** "may this figure go out now?" is answered by about twenty functions in six modules (map §3.1's first table, every line re-checked). `rich` reaches back into `service` for three of them through function-local imports, which is what makes the four-module cycle.
- **Does:**
  - `figures/protection.py` takes the protection group from `service.py` (about 330 lines). It also takes `rich`'s learner-state and base checks (`_withheld`, `_item_protected`, `_inherited_withheld`, `stored_learner_state_withheld`, `intent_learner_state_withheld`, `_learner_state_withheld`, `_carries_learner_state`, `_inherits_learner_state`: `figures/rich.py:422-446`, `:653-730`, about 110 lines) and `rich`'s copy of `ATTEMPT_HOST_REFS` (`figures/rich.py:365`), so the constant has one home.
  - The module opens with the rule in one table: which predicate each moment asks (the request, the build, the rich job's start and each request, delivery, a list, a pre-build filter) and over which inputs (the spans sent, the homes, the learner-state lineage in its three places, an item's own passage). That table is the answer to F10B1 that no function gives today.
  - Functions are merged only where equal on every input. The candidates are none that I could prove by reading. The step 0 compares each pair the map lists and records the verdict.
  - The cycle's other two edges go by moving what they import, L1's method: `prefetch_ledger` reads `ALL_SPEC_VERSIONS` from `figures/service.py:246`, so the version tuples (`SPEC_VERSIONS`, `RICH_SPEC_VERSIONS`, `ALL_SPEC_VERSIONS`) move to `figures/spec.py`. `routes.rich_text()` reads `rich.RICH_BRIEF_MAX` (`figures/routes.py:368`). The constant stays where `params/parameter_registry.py` registers it (`:207` maps the owner `figure_rich` to `figures/rich.py`; `:759`), so the reader moves instead: the build passes the cap in.
- **Deletes:** the `service` ↔ `rich` ↔ `routes` ↔ `prefetch_ledger` component (M0's "modules in any cycle" falls by 4). Ten function-local imports in `prefetch.py` become one top-level import of `protection`.
- **Abstraction:** none; a module boundary.
- **Must not touch:** `content/sources/exam_material.py` (the one predicate's owner), `figure_admission.py` (a leaf on purpose, `figure_admission.py:1-7`), `learner_state.py`'s reads.
- **Files:** `figures/{service,rich,spec,routes,prefetch,prefetch_ledger,help,protection}.py`, `teacher/visuals.py`, `cli/reader.py`, `learnloop_sidecar/handlers/{figures,hints}.py`, the tests importing the moved names.
- **Proof:** P-ast for every moved function; P-golden; P-pins; the structure ratchet lowered for the cycle. **Lines:** about +40 net (imports and the docstring's table), an estimate. **Vault:** the Figures note's protection section (K10.15). **Size:** M.

**K10.7. The request and its grounding out of `service.py`** (M). Structure. F10P1, F10D3.
- **Does:** `figures/request.py` gets the request group (about 390 lines); `figures/grounding.py` gets the context and grounding group (about 230).
  - The handler's own fifteen checks (`learnloop_sidecar/handlers/figures.py:413-511`) stay where they are. Which belong in the request module is K8's question.
  - Where both sides check the same thing with different error codes (the client's `cold_active` as `SidecarError("cold_check")` against a `FigureRefused`), the record says so for K8. Nothing changes here.
- **Proof:** P-ast, P-golden, P-pins. **Lines:** about +50 net (estimate). **Size:** M.

**K10.8. Presentation, listing and predictions out; the rest is the build** (M, two commits). Structure. F10P1, F10C1.
- **Does:**
  - `figures/view.py` takes presentation (about 670 lines), `figures/listing.py` the listing (about 560), `figures/predictions.py` the predictions (about 115).
  - `service.py` keeps only the build (about 1,350 lines with its header) and is renamed `figures/build.py`. Its importers by then are the build's callers: the sidecar handler, the lesson handler, `prefetch`, and the build tests.
  - The 142-line stage-history docstring (`figures/service.py:1-142`) is replaced by one paragraph per module on what it does. The history stays in git and `docs/reviews`.
- **Deletes:** the stage-history docstring (net about −100 lines after the new docstrings).
- **Proof:** P-ast, P-golden, P-pins. The ratchet's stage-comment count must not rise. **Lines:** about +60 net from imports, minus the docstring (an estimate: roughly level). **Vault:** the generated module notes (one per new module). **Size:** M.

### 4.4 Structure track: the author loop and the presentation

**K10.9. The author loop: reading the answer is a pure core** (M, with a stop rule). Structure. F10P1, F10F2, F10O4.
- **Problem:** `_author_attempts_and_store` (`figures/service.py:2485-2788`, 304 lines) interleaves model calls, the gate, the sketch engine and the source check (a database read and a sandbox) with the per-attempt verdict. Nine loop-local variables carry state across attempts (`brief`, `quick_dropped`, `compiled`, `sketched`, `sketch_report`, `unsupported`, `verdict`, `report`, `source_check`). The retry and salvage rules can only be tested through a whole build. The attempt records come from appends the loop makes beside its decisions, so nothing fails when the loop gains an exit `AuthorAttempts` doesn't know (F10O4).
- **Does:**
  - `_read_answer(output, *, menu, sketch, grounding_mode, advanced) -> Answer` is pure. It takes the model's parsed output and returns what it is: unsupported, spec, sketch, rich (with its optional quick candidate), or invalid with problems. It also returns the record code and the tier verdict. It covers the label rule, the V3 menu check, the brief parse and the grammar and sketch parse with prediction salvage (`:2551-2702` without the verifier and source-check calls).
  - The shell's `_verify(answer, ...)` runs numerics (pure), the sketch engine and the source check, and returns problems.
  - The loop (about 40 lines) decides retry from those problems.
  - `_store_quick(...)` writes the row and its transaction (`:2703-2788`).
  - `AuthorAttempts` records what `_read_answer` and `_verify` return, so a new exit is a new code the core returns and a test names (L6). The function gets an approach header.
- **Abstraction and why it pays:** `Answer`, one frozen dataclass of about six fields. It replaces the nine carried variables and lets a test state "a V3 answer with an empty `why_this_tier` is retried with this problem and code" with literals.
- **Stop rule (K2.4's lesson):** if `Answer` needs more than about eight fields, or the split adds more than about 60 net lines with no new literal-value tests, stop after `_store_quick`'s extraction and record why.
- **Must not change:** the order of `gate.check` calls and model requests (the golden holds receipts and records); the prompt bytes; the stored rows.
- **Proof:** P-golden over K10.4's matrix (prompts, rows, receipts, records); P-pins; new tests calling `_read_answer` with literal outputs, one per record code it can return. Functions over 200 lines in scope: 1 to 0 (the ratchet lowered). **Vault:** the Figures note's build section. **Size:** M.

**K10.10. One presentation chain and one shown set** (S). Structure. F10B3 (backend half), F10B6 (the shown set), F10D5.
- **Does:**
  - `section_figures` calls the view's chain with re-verification off instead of copying it minus one step (`figures/service.py:3571` against `:1577`).
  - `teacher/visuals.py:277` and `:340` use `store.SHOWN` (`db/stores/figures.py:40`).
  - `drawable_now` and `shown_figure` are written over the chain.
  - The tier rules that say "attempt hosts and lessons are quick-only" stay at their five sites, because each guards a different door (the menu, the worker, the view, the help record). They get one constant each side imports: `LESSON_TIERS` (`figures/service.py:205`), and an attempt-host tier tuple beside it in `figures/request.py`.
- **Deletes:** the copied chain (about 8 lines), two literals.
- **Proof:** P-golden (the section-figures and lesson cases). **Size:** S.

### 4.5 Structure track: why x and not y

These follow arc B's rules: ADR-017's one record type, ids and codes only, written through `provenance.write` or `write_decision`, and never allowed to change a decision.

**K10.11. Why a request was refused, reused, offered fewer tiers or withheld** (M). F10O2, F10O3, F10O5, F10O6.
- **Does:**
  - **One `figure_request` record per request:** status `refused` with the rule code (each `FigureRefused` and `SidecarError` code at the request: exam material, the switch, origin, validation, cold check, not offered, spend before the loop: `unrouted`, `unpriced`, `not_isolated`); `reused` with which key matched (this setting, another setting, a recorded-inputs twin) and the figure; or `built`. Subject `figure_request:<id>`, or the figure.
  - **The menu as a core:** `tiers_allowed` takes the probed facts and returns the menu and a code for each absent tier (switch, opt-in, `off_linux`, `no_bwrap`, `no_manim`, `models_off`, lesson host, attempt host, no spawner). `manim_runtime_state` already computes the reason (`figures/rich.py:126-160`). The codes go in the request's record.
  - **The gate's record** gains a subject (the request) and, for `held`, the hold's sub-code (exam material, learner state, item protection, power, plan, cancelled from K10.1). `refusal_records.figure_gate_record` (`refusal_records.py:269-275`) takes them as facts.
  - **Delivery and lists:** a figure withheld at delivery (`learnloop_sidecar/handlers/figures.py:184-185`), and a list that drops a chain because its pick is withheld or its spec no longer parses (`figures/service.py:3233-3234`, `:3539-3543`), write one `figure_withheld` record per figure, once per figure per process, not per poll. `reader.figures` runs every 5 s while a video builds (`useFigures.ts:21`).
- **Storage:** one record per press, plus one per withheld figure. It's small, and the step measures bytes per week on a synthetic journey as B6 did.
- **Proof:** P-fail, one per rule code, staged with fakes (`tests/test_why_cases.py` gains a figure case: "why didn't Show me work?"). P-golden is otherwise identical apart from the new rows. **Vault:** `Workflows/Debug a decision.md` (the figure rows). **Size:** M.

**K10.12. Every rich attempt recorded** (M). F10O1; ADR-017's open item for the rich jobs (`Decisions/ADR-017 …md:166`, `:169`).
- **Problem:** a video build keeps one failure reason, the last (`figures/rich.py:783-864`, `:985-988`). Attempt 1's failed claim, the render repair and a stop later requeued leave nothing; the requeue overwrites `ingest_jobs.error_json`.
- **Does:**
  - `run_rich_job` notes each attempt in a `figure_author`-shaped record of tier `manim`: rule codes `brief_invalid`, `scene_invalid`, `claim_failed`, `pacing_failed`, `render_failed`, `render_timeout`, `render_repaired`, `accepted`. It goes through the same `AuthorAttempts` builder (`figures/records.py:296`), given a kind, not a second builder.
  - A stop writes a `figure_rich_stop` record with the `RichJobStopped` code, so a requeue no longer erases it.
  - Under K10.3's trace, all of it joins the press.
- **Order:** after K10.3, and after K10.6 (which moves `rich`'s protection functions).
- **Proof:** P-fail per code with the fake renderer and runner; the rich job golden otherwise identical. **Vault:** ADR-017's figure rows; the open item closed. **Size:** M.

### 4.6 What must stay exactly as it is

No step edits these files or behaviours. A step that finds it would have to stops and goes to the owner:
- `figures/sketch_engine.py` (the sealed QuickJS-wasm runner, its caps, `ENGINE_SHA256` `:57`, the paths into `apps/` `:51-53`); `figures/katex_tree.py`'s engine load; `apps/learnloop-tauri/sketch-engine/engine.lock.json`; the desktop's `screens/reader/figures/sketch/sketchCompartment.ts`, `sketchRunner.ts`, `sketchFrameProtocol.ts`; `src-tauri/src/frame_guard.rs`.
- `content/authoring/concept_animation.py`'s `_sandboxed_command` (`:446`), `capped_scope_prefix` (`:399`), `render_scene` (`:857`) and `store_video_bytes` (`:1156`); `content/authoring/pf_sandbox.py`'s `run_sandboxed_python` (`:120`); `figures/manim_figure.py`'s `sandboxed_runner` and `validate_scene_code`; `figures/source_check_harness.py` and how `source_check.py` sends it to the sandbox as text (F10P4 stays low and as is).
- `src-tauri/src/main.rs`'s `serve_llmedia` (`:109`): content-addressed names only, with Range.
- The Manim opt-in, the `bwrap` requirement and the render's niceness for pre-builds.

The moves in K10.6-K10.8 reach none of these. K10.9 calls `verify_sketch` and the source check exactly as today.

### 4.7 Boundaries: the handler and the desktop

**K10.13. The attempt-host policy under `figures/`** (M). **Parked until a second frontend will call it** (Q3; K8's rule, strategy §2.18: "move a decision under its feature package, only where a second consumer exists"). F10B2, F10H2.
- **Problem:** about 510 lines of the sidecar handler (`learnloop_sidecar/handlers/figures.py:961-1470`) decide attempt-host policy: host resolution with raw SQL on `practice_attempts` and `sessions` (`:1115-1117`, `:1139-1140`), the tutor handler's private `_item_cold` (`:1072-1075`), the take step (`:1078-1100`, with a wall-clock read at `:1093`), one hint-equivalent per figure per attempt and the reveal rows (`record_attempt_figure` `:1297-1385`), and the cost line.
- **Does, when unparked:**
  - `figures/attempt_help.py` takes the decisions; the handler adapts.
  - The two raw queries become store functions.
  - `_item_cold` comes from a public function of its owner (K8 names it).
  - The take step reads the injected clock.
- **Why parked:** today only the desktop calls these, through the sidecar. Moving them adds a module and an interface for no second caller. That's the speculative abstraction the owner ruled out.
- **Proof, when run:** P-golden (the attempt-host cases); P-fail for the clock. **Size:** M.

**K10.14. The desktop reads `shown` and the label from the server** (M). Before the UX overhaul, so it inherits one contract (as K2.11). F10B3, F10U5; K10-5's mechanics.
- **Does:**
  - The view carries `shown: bool` from the presentation chain. The desktop's three literal copies (`askFigures.tsx:128`, `FigureInline.tsx:569`, `useFigures.ts:331`) read it.
  - The desktop stops branching on the server's English label (`FigureInline.tsx:595-596`): the view carries a code for "can't show this kind here".
  - Badges: the view carries the server's `label` code. Whether the desktop draws the server's words or its own is K10-5, the audit's call (§7). This step makes either a one-line change.
  - Attempt hosts' quick-only rule: the server already drops `fuller` (`learnloop_sidecar/handlers/figures.py:1013-1020`), so the desktop's second drop (`askFigures.tsx:81-83`) goes.
- **Not done here:** the view's switch-dependent shape (F10B5). It goes with the switches (Q1, K10.16). Before that, a stable shape would break the switch-off goldens that pin each predecessor's view.
- **Files:** `figures/view.py`, `apps/learnloop-tauri/src/api/dto.ts`, the three desktop files, their vitests.
- **Proof:** vitest per component; P-golden with the new keys added (a deliberate golden change, listed). **Size:** M.

### 4.8 Docs

**K10.15. A Figures note; the two stale lines** (S). F10V1, F10V2; K10-4.
- **Does:**
  - A Concepts note, "Figures and explanation videos": the tiers and how one is chosen; what "checked" means and who owns a label; the source check; the pre-build model; admission and spend; the video job and its sandbox; the protection table from K10.6; the attempt-host rules; where each lives after K10.5-K10.9; and what `why` answers.
  - It is linked from `Home.md` and the Architecture Overview's layer table (`Architecture/Architecture Overview.md:66-73`).
  - The two stale lines are fixed: the AI Architecture route list (`Architecture/AI Architecture.md:53`) gains `figure_author`, `figure_rich_author` and `figure_prefetch_judge`; ADR-017's example `prefetch_eu_v1` (`:61`) becomes `prefetch_decision_v2`.
- **When:** the two lines now (any step can carry them); the note after K10.9, so it describes the split code.
- **Proof:** the four vault validators; the note read against the code by the orchestrator. **Size:** S.

### 4.9 Conditional on the owner

**K10.16. Retire the content switches** (M). Only if Q1 is yes. F10C2, F10B5.
- **Does:**
  - Eight switches are removed: `predictions_enabled`, `region_enabled`, `revisions_enabled`, `advanced_panels_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`, `checked_labels_enabled` (`tests/goldens/effective_defaults.toml:518-537`, all `true`).
  - Each goes into `config/retired.py`'s `RETIRED_FIELDS` in the same commit, so the pinned identities that dumped them keep their bytes.
  - Their off-paths go: the V1 and V2 output contracts (`figures/routes.py:450-456`); the conditionals that assemble the prompt version from the switches (`:430-437`: the suffixes become fixed parts of the version, so the strings new builds carry are byte-identical to today's default); the off-rows (`advanced_off_row`, `sketch_off_row`); the view's keys that are "absent while off" (`figures/service.py:1351-1376`); the contract's switch-dependent keys (`learnloop_sidecar/handlers/figures.py:102-131`); the switch-off goldens' predecessor cases.
- **Kept:** `figures.enabled`, `rich_tiers_enabled` with the Manim opt-in (native code on your machine), `prefetch_enabled` (background spend), `help_kind_enabled` (the cold-check rule), `author_learner_state` (what the author is sent), `teacher.visuals` (the teacher's feature). `prefetch.pressed_waits` goes with D7's kill-switch removals, not here.
- **The reuse key's alternates** (`figures/service.py:2172-2182`) are partly a reader of figures built before a stage landed, not only under a switched-off setting. They stay as a legacy reader until your count (Summary) shows no stored figure under an alternate's prompt version. Then a later chore deletes them, at the cost of one re-paid build per such input pressed again.
- **Proof:** P-pins (the new builds' keys unchanged; a retired field's removal leaves every pin's bytes); P-golden for the default configuration identical; the effective-defaults golden loses eight lines. **Vault:** the generated config notes. **Size:** M.

**K10.17. Remove the dormant `js_animation` tier** (S). Only if Q2 is yes. F10C4.
- **Does:** removes `JS_ANIMATION_BUILD_FLAG` and the tier from `figures/rich.py:82-86`, `:187`, the tier sentence and contract mentions (`figures/routes.py:323`, `:343`, `:363`, `:395`), the records' status set (`figures/records.py:109`), the pre-build model's tier set (`figures/prefetch_model.py:86`), the report's SQL literals (`reader/reader_report.py:490`, `:962`), and the config docstring (`config/schema.py:2762`). 20 lines in 7 files by grep.
- **Check in step 0:** that no stored row has `tier = 'js_animation'` (none can: it was never on a menu) and that `prefetch_model.RICH_TIERS` reaches no identity. The model's `digest()` is recorded on every decision row, so the check runs the pin.
- **Proof:** P-pins; P-golden (the V3 schema unchanged: the tier is named only in comments there); P-draw. **Size:** S.

## 5. Order, dependencies and lanes

```
K10.1 ─┐
K10.2 ─┼─ now, each alone (behaviour; learner-visible first)
K10.3 ─┘  (before K2.7 moves jobs.py's handlers, or after it, not beside)

K10.4 ─→ K10.5 ─→ K10.6 ─→ K10.7 ─→ K10.8 ─→ K10.9 ─→ K10.15 (note)
                    │                   ├─→ K10.10 ─→ K10.14 (before the UX overhaul)
                    │                   └─→ K10.16 (if Q1) ─→ K10.17 (if Q2)
                    └─→ K10.12 (after K10.3)
K10.7 + K10.9 ─→ K10.11
K10.13: parked on Q3 and K8
```

**Dependencies on other arcs:**
- **Arc B:** K10.11 and K10.12 use ADR-017's record, trace and `why` as B1 built them. K10.12 closes B8's open item for the rich jobs. L6's rule (a core returns its record) applies from K10.9 on, though arc E hasn't started: figures are the first place it pays.
- **K8 (the sidecar handlers review):** K10.13 waits for it. K10.7 hands it the handler's fifteen request checks and the duplicated error codes.
- **The UX overhaul:** K10.14 lands before it. K10.2's and K10.14's wording, K10-5 and §7's design questions are the audit's.
- **L1 and M0:** K10.6 removes a four-module component on its own (the "modules in a cycle" ratchet falls by 4). The sidecar's 36-module component (§0 row 6) is L1's or K8's, not K10's.
- **L4:** its review covers `figures/prefetch*`. K10 adds no prefetch step.
- **L5:** K10.9 gives the only figures function over 200 lines its approach header. The other four over 120 (`verify_sketch`, `parse_sketch`, `scene_problems`, `_build`) are L5's if no step touches them.
- **D7 and L7:** `prefetch.pressed_waits` and `prefetch_decision_v1` are D7's. K10.16 follows D7's method for config switches.
- **K2.7:** both it and K10.3 edit the figure handlers in `content/pipeline/jobs.py`.

**What can run beside what.** K10.1-K10.3 can run beside anything; they fill lane 3's "ledger fixes" slot in §2.19's first row. K10.4 can run beside arc D: it is test-only. K10.5-K10.10 all edit `figures/service.py`, so they are one chain, as K2.1-K2.5 were. They fit a lane after D7, beside K2.6-K2.12, whose files they don't share. K10.12 (in `rich.py`) can run beside K10.7-K10.9 once K10.6 has landed. K10.11, K10.14 and K10.15 follow their inputs. Each step lands alone or in a batch of up to four.

**Size per step** (estimates; S about half a day of queue, M about one day, as K2's were):

| Step | Track | Size |
|---|---|---|
| K10.1 Cancel stops the build | behaviour | S |
| K10.2 The Reader says withheld | behaviour | S |
| K10.3 The video job continues the trace | behaviour (records) | S |
| K10.4 Pins and goldens | structure (tests) | M |
| K10.5 One name per switch | structure | S |
| K10.6 Protection in one module, cycle cut | structure | M |
| K10.7 Request and grounding out | structure | M |
| K10.8 View, listing, predictions out; `build.py` | structure | M |
| K10.9 The author loop's pure core | structure | M |
| K10.10 One presentation chain | structure | S |
| K10.11 Why at the request | structure (records) | M |
| K10.12 Every rich attempt recorded | structure (records) | M |
| K10.13 Attempt-host policy (parked) | structure | M |
| K10.14 The desktop reads the server | structure | M |
| K10.15 The Figures note | docs | S |
| K10.16 Retire content switches (Q1) | structure for the default config | M |
| K10.17 Remove `js_animation` (Q2) | structure | S |

**Total:** seven S and ten M, one of them parked. About 1.5-2 weeks of queue for the sixteen that run, an estimate. Of that, the three fixes take about a day and the `service.py` chain (K10.4-K10.10) about a week.

## 6. What a change costs, today and after

"Today" is the map's §7 count (single commits re-counted there; stage unions are its delegated sweep). "After" is my estimate of the figures-specific files a change edits once the steps land. Shared plumbing (migrations, head fixture, generated notes, config goldens) is arc A's and D's and is left out on both sides.

| Change | Today (figures Python / desktop / behaviour tests) | After (estimate) | Why it moves, or doesn't |
|---|---|---|---|
| (a) A grammar element | 6-9 / 3-5 / 1-3 | the same | Already local to its concern: grammar, spec, verify, the prompt text and the renderer. Two sides is the design |
| (b) A verification check | 2-5 / 0-3 / 1-3 | the same | One verifier, its version, a record code. K10.9 makes the code a return value, not a new file |
| (c) A new tier | about 15 places in 7 modules / 8-29 / 15-70 (stage unions) | about 9-10 places in 5 modules / 6-25 / fewer, since the core's literal tests replace whole-build tests | The answer reader, the view and the request are one place each (K10.8-K10.10). The off-state, `drawable_now`'s branch and the desktop badge go (K10.14, K10.16). The menu, prompt and contract, reuse key, records, pre-build tier set and report SQL remain |
| (d) A new place that offers Show me | 4-6 / 2-4 | 3-4 / 2-3 | The origin, key and tier rule sit in `figures/request.py`. The protection call is one module. With K10.13 (if unparked), an attempt-like host is one package call instead of the handler's 510 lines |
| (e) A prompt change | 1 file and 2 goldens | 1 file, the prompt golden, and a K10.4 version pin when the version is bumped; the switch-off golden goes with Q1 | K10.4 adds a pin on purpose: a moved reuse key is the costly silent failure |
| (f) A protection rule ("may this go out?") | about 20 functions in 6 modules to read, 1-3 to edit | 1 module to read, 1 to edit, plus a caller only when a new moment asks it | K10.6 |
| (g) "Why did this figure or video fail?" | the author's attempts: yes (B4); a refusal, a menu, a reuse, a video: no | every item in §3's trace list | K10.3, K10.11, K10.12 |

Package size, honestly: the split adds about 150-250 lines (K10.6-K10.8, imports and docstrings). K10.9 is level or slightly up. The deletions (K10.5 about 60, the old docstring about 140, K10.10 a few, K10.16 perhaps 300-500 across routes, the off-rows, the view and the contract, K10.17 20) are what shrink it. Without Q1, the package ends about where it started, but in modules a reader can hold. With Q1, it ends a few hundred lines smaller. These are estimates.

## 7. Input to the UX journey audit

The map's §8 lists what the learner sees. Here is what this strategy fixes as structure, and what it leaves to the audit as design:

| §8 item | Structure (fixed here) | Design (left to the audit) |
|---|---|---|
| Cancel doesn't cancel (F10U3) | K10.1 | Whether the Ask panel gets a cancel at all (it has none: `askFigures.tsx:98-104`) |
| Withheld at delivery vanishes (F10U1) | K10.2 shows a line with code `withheld` | Its words, and whether to say why |
| A figure vanishes from the list (F10U7) | K10.11 records it with a reason code | Whether the list shows a line for it |
| Failure codes dropped on the desktop (F10U4) | K10.11 makes the codes a closed set the server owns; K10.14 sends them in the view | How each code reads: budget used, no route, switched off, vault busy |
| Why a tier wasn't offered | K10.11 computes and records the codes | Whether the Reader says "no video here because …" |
| The video's "why ▸" shows only the last reason | K10.12 keeps every attempt | Whether "why ▸" shows the attempts |
| No wait estimate for a press; polling with no timeout (F10U2) | none: `prefetch_model.wait_estimate` is pure and measures pressed waits since `prefetch_decision_v2`, so an estimate exists to show | Whether to show it; what a stuck build shows, and when the poll gives up |
| Four hosts, three vocabularies, three poll rates (F10U5) | K10.14 gives them one contract (`shown`, the label code, the failure code) | One pending, failure and badge vocabulary across Reader, Ask panel and lesson; K10-5's badge wording |
| "show me" means three things | none | The figure button, active reading's reveal (`ActiveReadingCard.tsx:165`) and the workbench's "show me a similar example" (`RouteExample.tsx:28`) share a label |
| No figures on the phone (F10U6) | K10.13 when Q3 is yes | Whether, and what, the phone shows |

## 8. Risks, and what would make me stop

**Where the map, and this strategy, could not see:**
- **The sandboxes at run time.** Nothing was run: not the wasm engine, not bubblewrap, not the PF sandbox, not TeX inside the render sandbox. The steps don't touch them, but K10.4's rich golden runs with a fake renderer, so a real render's behaviour is pinned by nothing here. The existing hostile-corpus tests (`tests/test_sketch_hostile.py`, `tests/test_manim_sandbox_hostile.py`) are the only runtime check, and they stay in every step's targeted set.
- **Real media sizes and counts.** No vault was opened. How many figures exist per prompt version and tier, how many legacy `verified` rows, how often presses are cancelled, withheld or refused: all unmeasured. Your count decides K10.16's legacy reads, and K10.11's storage estimate is synthetic.
- **The pre-build pass and the video job under real timing.** The goldens pin draws and rows at a fixed seed and fake clocks. Races between the drain thread, the press and the queue worker are pinned only where existing tests wait for them.

**What a step could break that no test pins today:**
- **The reuse key.** Until K10.4, a move that changed `request_hash`'s bytes would pass every test that only compares keys with each other, and every stored figure would be rebuilt (paid) on its next press. Hence K10.4 first.
- **Patches that become no-ops.** 18 test sites patch `service`'s public names (§4.2). After a move, such a patch would patch nothing, and the test might still pass. K10.4 ports them before any move, and each move step greps for `setattr(FS, "<moved name>")` and `FS.<moved name>`.
- **Function-local imports.** About 265 of the scope's imports are inside functions (map §1.3), including ten `from learnloop.figures.service import …` in `prefetch.py`. A missed one fails only on its path at run time. That's why K10.4's coverage step lists the lines no golden reaches, and why the moves' gate includes `lint-imports` and a scripted check that no `learnloop.figures.service` attribute named in `src` is undefined.
- **The author loop's order.** K10.9 must keep the order of gate checks and model requests, because the order decides which record is written when the configuration changes mid-build. The golden holds receipts and records for that reason.
- **Cancel's window.** K10.1 leaves a build that passed its last check before the cancel landed to commit. That is intended and stated, and a test pins it so no one "fixes" it into a lost paid figure.

**What would make me stop a step:**
- an identity pin or golden that moves in a structure step;
- P-ast failing for a moved function;
- K10.9 crossing its stop rule (`Answer` past about eight fields, or more lines with no simpler test);
- a step needing an edit in §4.6's list;
- K10.13 started without a second consumer.

**Not verified here:** everything the map lists under "Not verified" still applies. In addition, I checked by reading, not running: that `LibraryJobs.start`'s `on_job` runs before the work starts (`learnloop_sidecar/handlers/library_ask.py:279-280`); that the gate's hold is asked at `store` (`figures/service.py:2754`); and that the ingest worker opens no trace scope per job (K10.3's step 0 confirms it). K10.17's claim that `prefetch_model.RICH_TIERS` reaches no identity is unproven until its step 0 runs the pins.

## 9. The owner's decisions, in full

1. **Q1: retire the content switches** (§4.9, K10.16).
   - **Today:** thirteen boolean switches under `[figures]`, all on by default (`tests/goldens/effective_defaults.toml:518-537`), plus `teacher.visuals`. Each off-path must reproduce its predecessor byte for byte: the prompt version from five flags, the reuse key computed under the current setting and five others (doubled with a learner state), the view's keys under four switches, the contract's under six.
   - **Recommended:** retire the eight that only gate a feature already on by default and carry no safety, spend or privacy weight: predictions, region, revisions, advanced panels, offers, show me, sketch, checked labels. Keep the master switch, the rich tiers and Manim opt-in, pre-builds, the help kind, the author's learner state and the teacher's visuals.
   - **If yes:** K10.16 after K10.8. You can no longer turn those eight features off one by one, only figures as a whole.
   - **If no:** nothing breaks. Every later figures change keeps paying the variants, and the desktop keeps handling every combination of keys.
2. **Q2: the dormant `js_animation` tier.**
   - **Recommended:** remove it until the IPC probe (G-SM14) passes. The spec keeps the design (`docs/specs/spec_reader_show_me_figures_v1.md` §9b.2).
   - **If yes:** K10.17, half a day.
   - **If no:** it stays unreachable in seven files.
3. **Q3: figures on the phone, or in MCP v2.** Product first. The structure follows: K10.13 moves the attempt-host rules into the package only before a second frontend's figure step. The phone V4 record says figures "stay off" (`docs/reviews/phone-v2-v4-reader.md:119`), and no one has recorded whether that is final.
4. **Q4: a durable pressed build.**
   - **Recommended:** no. After K10.1 the in-memory press is correct, and a restart costs only a re-press, which recovers the paid answer from its checkpoint for free.
   - **If yes:** a new queue job type with leases and a slower start, to save a press.

**Your count** (not a decision): stored figures per `prompt_version` and per `tier`, and rows with `verification = 'verified'`, from your vault. It decides when K10.16's legacy reuse reads and `shown_row`'s legacy path (`figures/service.py:1041-1050`) can go.
