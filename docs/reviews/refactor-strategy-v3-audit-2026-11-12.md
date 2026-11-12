# Audit of refactor strategy v3, and what to add (2026-11-12)

An independent read of `docs/specs/refactor_strategy_v3.md` against the owner's brief (the Nov 8 insight: a disciplined, surgical refactor for local reasoning, change locality, discoverability, low conceptual overhead, observability and economy, with decision records, why-comments, a functional core for the ML parts and a package as small as it can be). **Base: main `e9a7733612`.** Docs only. **Status: the owner approved the additions on Nov 12 ("I agree with your audit additions"); they are in the strategy as §2.18, with the two tracks in §2.1 and the structure measures in §6.** Which CLI-only code stays is still the owner's call.

**How I checked.** I read the strategy whole, the map's §1, §3, §5-§7, the baseline, the bug ledger and K2's strategy. I reran `scripts/refactor_measures.py` at this tip. I wrote one read-only AST sweep of `src/` (imports with function-local ones kept apart, strongly connected components, reachability from the entry points, a heuristic for numeric modules that also run SQL) and counted commits per package since Oct 12. I ran no test and no model. Numbers marked "sweep" are mine, and their limits are in §4.

## Summary for the owner

**The plan is good, and it is narrower than your brief.** What it covers, it covers well: every claim is checked against code, each step names its proof, it can stop after any arc, and it says what not to do. Arc B delivered `learnloop why`. D2a alone justified the work: moving the test vault to the head found bugs on the path your vaults actually run (the ledger's D-1 to D-6).

It restructures about a fifth of the package: the router's top layer (E), history (D), two central functions (I) and ingestion (K2). The rest gets records, removals or nothing.

**The seven gaps that matter, in order:**

| # | Gap | Evidence | Addition |
|---|---|---|---|
| 1 | **The shrink is small and nothing holds it.** | After arcs A-C and K0-K3: code lines down 1.0%, functions over 200 lines still 83. October grew about 6,000 code lines a day, so the 5-9% target is a week or two of growth. | M0, L7 |
| 2 | **The largest obstacle to local reasoning is declined, though it has a cheap cut.** | The 189-module cycle exists only through function-local imports. Seven edges hold it together: without them the largest piece is 36. | L1 |
| 3 | **The most-changed code has no map.** | `learnloop_sidecar` is in 30% of the last month's commits, `db` in 22%, `params` in 11%. None has a step. Diagnosis, the largest package, has none for its layout. | K8, K9, L2 |
| 4 | **The functional core stops at the router.** | The map's own F5, F7 and F8 have no step. Other learned models fit beside their SQL. | L4 |
| 5 | **Comments aren't moving.** | Stage-artifact comments: 2,312 at the map, 2,297 now. `config/schema.py` lost 107 lines of a planned 2,000. | L5 |
| 6 | **15% of the package never runs when a learner uses the app, and you can't tell from where it sits.** | 241 modules, 92,000 lines, reachable only from the CLI. | L3 |
| 7 | **About a quarter of the plan isn't refactoring.** | G2, G4, H3-H6, D8, arc F, Z1, K3 and the ledger's successors change behaviour, speed or documents. | §2.7: two tracks |

**What I'd add:** eight small steps and two reviews (§3), roughly 12-18% on top of §2.15, an estimate. M0 is the one to do now: it costs one small step and makes every later gain stick.

**What you'd decide:** whether the behaviour changes move to their own track (§2.7); whether `repositories.py` is split by file at a quiet point (L2); which CLI-only code you still use (L3, which extends your decision 7).

**One correction to the request.** Ingestion has been evaluated deeply since you last looked: K2's map and strategy landed Nov 11 (`docs/reviews/k2-ingestion-map-2026-11-11.md`, `k2-ingestion-strategy-2026-11-11.md`), K3.1-K3.4 are on main, and K2.1-K2.12 wait for arc D. I found nothing to add there.

## 1. Where the refactor stands

The `refactor` session is busy. From git and its worktrees: arcs A, B and C are closed; K0, K1, K2's two documents, K3.1-K3.4, T1 and D2a are on main. In flight: K3.5 and D2b (one landing batch), and three fix branches for the bug ledger (facet-belief successor, diagnosis fixes, ingest fixes). D1 waits on the owner's `vault_report.py` run and the floor.

**Measured at this tip against S0** (`scripts/refactor_measures.py`, same script):

| Measure | S0 (Nov 9) | Now | Z2 target |
|---|---:|---:|---|
| Python files | 1,285 | 1,277 | down 6-11% |
| Raw lines; code lines | 632,055; 441,708 | 622,736; 437,129 (−1.5%; −1.0%) | down 5-9% |
| Functions over 100; over 200 lines | 477; 83 | 472; 83 | down |
| `config/template.py`; `schema.py` | 4,255; 5,218 | 125; 5,090 | about 450; (about 2,000 out) |
| `mvp-0.N` in code / docstring / comment | 310 / 987 / 3,144 | 262 / 944 / 780 | under 60 / 300 / 500 |
| `Repository` methods | 945 | 910 | at least 58 fewer |
| Upgrade modules (lines) | 45 (9,613) | 46 (9,840) | 1 table |
| Import contracts | 43 | 42 | lower |
| Test lines | about 457,000 (map) | 474,795 | none set |

`git diff --shortstat a810f628d8 HEAD`: `src` +9,189 −18,508; `tests` +41,616 −36,085; `apps` +47 −4,249. Arc A's targets were met where they were about plumbing (digests gone, head fixture stable, notes unstamped). The size targets wait on arc D, as the strategy says.

## 2. Deficiencies

### 2.1 Coverage: a fifth of the package gets structure

| Package | Lines | Commits touching it since Oct 12 (of 1,413) | Structural step in v3 |
|---|---:|---:|---|
| `learnloop_sidecar` | 38,720 | 422 | none (C3, C5 delete calls) |
| `db` | 47,011 | 304 (`repositories.py` alone 85) | declined (§4), dead methods only |
| `daily_plan`, `router_objective`, `router` | 41,400 | 233, 80, 66 | **arc E** |
| `config` | 5,852 | 226 | **A3** (done) |
| `cli` | 19,642 | 203 | D3 takes about 400 lines of `app.py` |
| `content`, `ingest` | 66,200 | 194 | **K2** |
| `source_retrieval` | 29,432 | 186 | K6, a review of side effects only |
| `diagnosis` | 73,609 | 171 | G1-G5 change what it decides, not its layout |
| root modules | 20,843 | 167 | **D3** (upgrades), E1 |
| `params` | 4,047 | 159 | none |
| `reader`, `figures`, `adaptive_difficulty` | 56,400 | 147, 109, 124 | records (B4), H4 |
| `attempts`, `scheduling` | 37,600 | 105, 98 | **I1, I2** (one function each), D4 |
| desktop TypeScript | about 177,000 | not counted | deletions, K2.11 |

Three rows stand out.

- **The sidecar is the most-changed package and the next three frontends are planned on it.** The phone dispatches its handlers, and the TUI rebuild and MCP v2 are specified as consumers of its registry. So whatever logic sits in `handlers/reader.py` (2,981 lines, imports 71 modules) and `handlers/practice.py` (2,287, 43) is the application layer. The map classed handlers by size only.
- **`params/parameter_registry.py` is in 11% of commits.** The map's B4 names it as a tax every feature pays (about 380 `_reg_const` entries). No step asks what reads those rows, or which entries could go.
- **Diagnosis is the largest package and holds 65 of the cycle's 189 modules.** Arc G changes its decisions under the playbook. Nobody has mapped how it's laid out, the way K2 did for ingestion.

### 2.2 Local reasoning: P1 and P2 are declined, and both have a cut the strategy didn't look for

§4 is right to refuse a wholesale `Repository` split and a head-on attack on the cycle. It doesn't follow that nothing surgical exists.

**The cycle (sweep).** No cycle exists among top-level imports. All of it is function-local: 2,836 module-to-module edges, in 564 modules, appear only inside functions. With them, the largest component is 189 modules and 166,533 lines (diagnosis 65, scheduling 19, adaptive_difficulty 17, content 14, source_retrieval 13, attempts 12). `daily_plan` isn't in it. The base is already clean: `config` imports no package, `vault` and `db` import only each other and `ingest`'s IR, `ai` imports only `config`.

A greedy search for the single edge whose removal shrinks the largest component most gives seven:

| Largest after | Edge | What it imports |
|---:|---|---|
| 144 | `learner/assessment_contracts.py:31` → `attempts.grading` | one function, `resolved_rubric` |
| 123 | `diagnosis/causal_orchestrator.py:1996, :2031, :2165` → `diagnosis.probe_episodes` | three function-local reads |
| 107 | `diagnosis/text_gaps/sources.py:1041, :1052` → `source_retrieval.note_gaps` | two calls, a declared exception |
| 93 | `reader/reader_progression.py:73` → `content.authoring.practice_generation` | function-local |
| 69 | `diagnosis/text_gaps/jobs.py:42` → `text_gaps.pipeline` | top-level |
| 41 | `substrate/replay.py:9` → `attempts.attempts` | three names |
| 36 | `diagnosis/probe_episodes.py:2173, :3465` → `diagnosis.probe_blocks` | function-local |

After all seven, the largest component is 36 (a second one that exists today), and modules in any cycle fall from 286 to 183. That isn't a layered system, but the unit a reader can't reason about locally goes from 189 modules to 36.

**`repositories.py` (27,508 lines, 910 methods).** It already inherits seven store mixins, and `db/stores/` has 56 files of functions over a connection. Moving method groups into mixin files by feature changes no call site and no interface. The strategy's objection (406 importers, a diff that proves nothing) is to changing the interface. A file split is a different move: it makes "which feature owns this table" the file name. Its real cost is merge conflicts with every branch in flight, which is a question of timing.

### 2.3 Size: the target is modest, and nothing stops regrowth

- **Measured:** −1.0% code after a planned 27% of the cost. The stopping-point table says "after arc C, dead code gone", which reads larger than it was.
- **Growth:** the map counts about 291,000 code lines on Oct 15 and 436,042 on Nov 8, about 6,000 a day. Between the map and S0 (one day) the package grew 7,540 raw lines. A one-time 5-9% is one or two weeks of that.
- **No standing rule.** D1 sets a floor once and D7 removes switches once. Nothing says when the floor moves next. The chain is 49 tags long, `config/schema.py` has 123 `enabled` booleans and 1,181 effective leaves, and each successor adds a switch and a gate by the playbook. Arc D will have to be run again.
- **Serving against tooling (sweep).** 1,030 modules are reachable from the sidecar, phone host and MCP server. 241 modules and 92,381 lines (15%) are reachable only from the CLI or TUI: `cli` 19,532, `experiments` 14,110, `ops` 11,116 of 14,478, `evsi_calibration` 10,490 (all of it), `diagnosis` 6,868 in 14 modules, `field` 4,142 of 7,047 in 11 of its 18 modules, `projects` 2,529, `tui` 2,459, `curriculum` 2,357. A new engineer can't tell which side a module is on.
- **A dead module the map missed.** `diagnosis/failure_triage.py` (1,054 lines) has no importer in `src` or `apps`: only eight test files and a `Repository` method name it. The strategy's §2.10 lists it among the readers arc G must keep working.

### 2.4 Functional core: F1-F4 only

The brief asks for a functional core "for a lot of the ML-heavy parts". The strategy takes the map's F1-F4. The map's F5 (`adaptive_difficulty/serving.py:181` `decide_slot`), F7 (the EKF's prior reads claims, `learner/mastery.py:293`) and F8 (the learned tail fits inside a connection scope, `router_objective/tail_serve.py:122`) have no step.

The sweep's heuristic (a numeric import or heavy `math` use, and `.execute(` in the same module) adds candidates nobody has read for this: `figures/prefetch.py` (1,862 lines, 26 SQL calls), `learner/lesson_weight.py` (1,097; 14), `daily_plan/objective_inputs.py` (886; 11), `router_objective/stop_coin.py` (645; 7), `source_retrieval/student_encoder.py` (545; 8), `router_objective/preferences.py` (430; 2). AD's modules use plain Python arithmetic, so the heuristic misses them. It's a list to read, not a finding.

### 2.5 Comments: the convention is right, the mechanism isn't working

- **Stage-artifact comments** (ruling, Codex, round, landing, F- or R-numbers; my regex, near the map's): 2,297 of 32,615 comment lines. The map counted about 2,312. "Touch it, fix it" hasn't moved it in three arcs.
- **`config/schema.py`:** A3 planned about 2,000 history lines out. The record (`refactor-a3.md`) shows 1,054 out and 947 in, net 107. The file is 5,090 lines for about 1,800 of code.
- **C4, the map's only high comment finding,** has no step: the longest functions are thinly explained. Functions over 200 lines: 83 at S0, 83 now. The convention reaches only functions a step touches, and most steps don't touch these.
- **Tests carry history too.** 196 of 1,403 test files are named for a stage or a fix round (`test_ad1_fix_round4.py` to `_round9.py`, `test_ad23_fix_r5.py` to `_r9.py`). The name says when it was written, not what it proves.

### 2.6 Observability: built beside the deciders, not returned by them

Arc B works and its discipline is good (no prose, never changes a decision, an inventory with no silent gap). As built, records come from builder modules (`daily_plan/plan_records.py`, `boundary_records.py`, `diagnosis/chain_records.py`, `figures/records.py`, `attempts/grade_records.py`, `refusal_records.py`: 35 construction sites in 12 modules) that assemble a record "from what its caller already holds", after the decision. The builders are pure. But the decider and its record are two functions, and nothing fails when a decider gains a branch its builder doesn't know.

The brief asked for the decision-producing function to return the record. E2 promises that for the router's choice. I1, I2 and G1 don't say it.

Two smaller things. Direct wall-clock reads (`datetime.now`, `time.time`, `time.monotonic`, `date.today`) number 321 in 125 modules, beside an injected clock that 439 modules import; some are legitimate deadlines, and arc K's own sweep counted about 247 with no step. And "time to locate" as measured rewards the comments the convention removes, which the baseline says itself.

### 2.7 Scope: two kinds of work under one name

| Kind | Steps |
|---|---|
| Changes what the learner gets, under the playbook | G2, G4, H3-H6, D8 (four gaps), the ledger's facet-belief successor |
| Bug fixes | K3.1-K3.5, 28 ledger rows |
| Speed | F1-F3 |
| Documents | Z1 (the paper), Z3 |

Each is argued well and most are owner-approved. The cost is to the refactor's own discipline. "A refactor step changes no value" can't be checked arc-wide when the arc holds a successor. The queue is near 100 steps with 21 large ones, against a brief that asked for no ton of big changes. And the stopping points mix "the code is easier to change" with "the algorithm changed".

**Recommendation:** keep every step, and label two tracks in the strategy. **Structure:** P-shadow and P-draw identical is the whole proof, and stopping points count only these. **Behaviour:** playbook steps, each queued after the structure step that makes it small (I1 before H3, G1 before G2, as now). Arc H and G4 then read as algorithm stages that the refactor made cheaper, which is what they are.

### 2.8 Measures: the brief's goals mostly have none

§6 measures size, change cost, speed, tests and `why`. It has no number for the largest import cycle, function-local imports, first-level names (46 packages and 80 root modules today, 36 after D3), config leaves, switches, clock reads or history comments. Those are the brief's local reasoning, discoverability and conceptual overhead.

## 3. Additions

Same form as the strategy's steps. Each is small, adds at most one test or one file, and has a stop rule. None changes a served value: the proof for all is P-tests, `lint-imports`, and P-shadow and P-draw identical.

**M0. Measures that can't slip back** (S). Now, beside arc D.
- **Problem:** §2.3, §2.8. Features land during and after the refactor.
- **Files:** `scripts/refactor_measures.py`; new `tests/goldens/structure.toml` and `tests/test_structure_ratchets.py`.
- **Adds:** the measures of §2.8, plus CLI-only lines, functions over 200 lines and stage-named test files. One test: a number may fall, and may rise only if the golden changes in the same commit. It's A3's pattern (`effective_defaults.toml`), so no new concept.
- **Proof:** the test passes at the tip and fails on a scratch edit that adds a function-local import across packages.

**L7. The floor follows the vaults** (S). With D1, in ADR-018.
- **Problem:** §2.3: arc D is a one-off.
- **Does:** states the rule: when the owner's `vault_report.py` shows every live vault past a tag, one chore step raises `OLDEST_SUPPORTED` and removes the gates and switches at or below it. A test lists switches whose tag is at or below the floor: it must be empty, or each must be on a short kept-because list.
- **Target:** the next floor move is one step, not an arc.

**L1. Cut the cycle at its seven edges** (M). After D6, which edits the same packages; recompute the edges first.
- **Problem:** §2.2.
- **Does:** for each edge, reads what's imported and moves that name to the lower module, or passes the value in. No interface, no registry, no injection framework.
- **Stop:** an edge that needs more than about three definitions moved is left and recorded.
- **Proof:** M0's largest-component number at or under 40; the frozen-cycle contract in `pyproject.toml` loses the modules that left.

**L2. `repositories.py` by feature file, same interface** (M; owner's call). At an arc boundary with no branch touching the file.
- **Does:** methods move into mixin files grouped by the tables they touch. `Repository` keeps every method. No call site changes. Afterwards a method still moves to its feature's store when a step touches it, as §4 says.
- **Proof:** a script shows every method body AST-identical and `dir(Repository)` unchanged, with no name defined twice.
- **Doesn't do:** shrink the interface. It buys discoverability only.

**L3. The serving core is visible** (S).
- **Problem:** §2.3.
- **Does:** one import contract: the sidecar, phone host, MCP server and the packages they reach never import `cli`, `tui`, `experiments`, `evsi_calibration` or `sim`. The generated module notes gain one field, reach (serving, tooling, tests only), from the closure script C1 already uses. The owner gets the CLI-only list per package as part of decision 7, with `failure_triage` and `field`'s 11 modules on it.
- **Doesn't do:** move packages. If the owner wants the top level to say it, that's a rename for E9.

**L4. Learned models callable without a database** (M review, then steps only where it pays). Review beside arc D; steps with arc I.
- **Review:** for each fit, update or score in `adaptive_difficulty`, `learner`, `router_objective`, `field`, `placement`, `figures/prefetch*` and the episode posterior: can it be called with plain values, and are its inputs recorded as of the decision?
- **Steps, each M:** F5, F7, F8 and whichever of §2.4's candidates the review confirms. Reads gather an inputs dataclass, a pure function returns the result, the shell writes. The same shape as I1.
- **Stop:** skip a module where the split adds more lines than it removes and no test gets simpler.
- **Proof:** a test calls the core with literals and no connection.

**L5. Approach headers where the steps don't reach** (M, in batches at arc closes).
- **Problem:** §2.5.
- **Does:** for each function over 200 lines that no arc rewrites (listed at step 0): two to five sentences on its approach, why the obvious one is wrong, and what must stay true. Review-round names inside it go. It also settles `schema.py`: either the planned 2,000 lines come out, or the target is changed with the reason.
- **Proof:** the module's AST with docstrings and comments removed is identical (A3's `ast_same.py`). A read-only Codex pass checks each header against the code. M0 holds the stage-comment count.
- **Not a sweep:** about 80 functions, not 32,000 comment lines.

**L6. A core returns its record** (rule; no step of its own). From E2 on.
- **Does:** every pure core the arcs extract (E2, I1, I2, G1's `probe_facts`, L4's) returns its `DecisionRecord` with its result. For each, `tests/test_why_cases.py` stages one case per rule code the core can return, so a new branch without a record fails.

**K8. The sidecar handlers as the application layer** (M; review). Before the TUI rebuild and MCP v2.
- **Questions:** which handlers decide and which adapt; what the phone, TUI and MCP would need again; which rules the desktop's TypeScript copies (K2.11 found four disagreements in ingest alone).
- **Output:** steps that move a decision under its feature package, only where a second consumer exists.

**K9. Diagnosis: deep map and structure strategy** (L; review, two jobs, K2's method). Before arc G.
- **Scope:** `diagnosis/` (110 files), with `causal_orchestrator.py` and `probe_episodes.py` first. Include `params/parameter_registry.py`'s cost per change (§2.1).
- **Output:** K9.1... after arc D. K6 widens from side effects to `source_retrieval`'s structure the same way, if K9 proves the method pays a second time.

**T2. Tests named for what they prove** (M; lowest priority). With the Codex docs stage.
- **Does:** renames the 196 stage-named test files to behaviour names, one commit per feature, no assertion changed. `scripts/affected_tests.py` follows imports, so selection doesn't move.

**Changes to existing steps:**
- **§2.10:** `failure_triage` has no production caller. It joins C's removal list, or the owner's list.
- **E9:** after D3 the root holds 36 modules. Those owned by one feature move into it (by name: `figure_admission`, `reader_learner_state`, `reading_sources`, `held_grades`, `grading_epochs`, `delayed_checks`, `hint_window`; step 0 confirms by importers). The root keeps cross-cutting leaves.
- **§2.14:** state the measured shrink at each stopping point, not the planned one.
- **§6:** add M0's measures. Time-to-locate gets a second run with fix comments masked, so it measures the map and `why`.

**Order.** M0 now. L7 with D1. K8, K9 and L4's review are read-only and run beside arc D, as K2 did. L1 after D6. L5 in batches at arc closes. L2 at a quiet boundary. L3 with J. L6 from E2.

**What not to add.** A layered architecture enforced top-down; a `Repository` interface split; a `lab` package move before the owner says which tools stay; typed wrappers for config; any step in the frontend beyond what K8 and the UX audit name.

## 4. Limits

- **The sweep resolves imports by name.** `from pkg import name` goes to `pkg.name` when that's a module, otherwise to `pkg`. `importlib` paths (the parameter registry's `MODULE_INVENTORY`, `open_world_gate`) are invisible to it, as they were to the map, so "CLI-only" and "no importer" need the strategy's step-0 proof before anything is deleted. My component is 189 modules; the map's was 191.
- **The seven edges are greedy, not minimal,** and each is read only as far as its import line. L1's step 0 decides whether each can move.
- **Commit counts** are non-merge commits touching a package since Oct 12, a measure of where changes land, not of difficulty.
- **Not read:** the frontend, the sidecar handlers' bodies, `parameter_registry.py`, ADR-017, the K1 and K0 records beyond their summaries in the strategy, arc B's fix round. §2.6 rests on the record builders' module docstrings and call sites, not a full read.
- **Not run:** any test, the timed lanes, P-shadow, P-draw.
- **The `refactor` session wasn't contacted.** Its state is from git, worktrees and its landing notes.
