# Second audit of refactor strategy v3 (2026-11-16)

A second read of `docs/specs/refactor_strategy_v3.md` against the owner's brief (the Nov 8 insight), four days and about 650 commits after the first audit (`docs/reviews/refactor-strategy-v3-audit-2026-11-12.md`). **Base: main `250b0e16fe`.** Docs only. **Status: for the owner's review. Nothing here changes the queue until the owner says so.** The steps already running continue as approved.

**How I checked.** I read the strategy whole, the first audit, the orchestrator's running log from Nov 14 on, the records of the two steps in flight and their diffs, the bug ledger's status column, and `tests/goldens/structure.toml`. I counted files and lines with git at this tip and at S0 (`a810f628d8`) and the map's base (`a525dbcef4`). Three read-only mappers charted the code the owner's new ideas touch (adaptive difficulty's model, the Decider and the model packets, the "assisted" label and hypotheses); I re-read the lines their main claims rest on. I ran no test and no model.

## Summary for the owner

**The plan is good and it is working.** What the first half promised is on main: `learnloop why`, one upgrade table in place of 42 modules, the test vault at the head, the floor, the two central functions with pure cores, ingestion's five-step chain. Arc D's review found real bugs on the path your vaults run (a rebuild that appends history and drops an adjudication, D-36 and D-52). The first audit's ratchet (M0) holds every structure number it measures.

**Six deficiencies now, in order of what they cost you:**

| # | Gap | Evidence | Addition (§3) |
|---|---|---|---|
| 1 | **The plan can no longer be read in one sitting, and its status isn't in the repo.** | 1,193 lines, with three sub-strategies of 38, 74 and 79 KB beside it. The summary still says 66 steps; with arc K, §2.18 and the ledger it is about 140. Which step is done is recorded only in a 680 KB private log of the orchestrator's. This session had to rebuild the state from transcripts. | S1 |
| 2 | **Nothing measures what the refactor itself costs, so nothing says when a tail stops paying.** | Removing seven kill switches (D7 batch 3, part 1) took one implementer about 570,000 tokens and three hours, for 244 net source lines and 7 of 1,171 config leaves. The usage limit stopped the queue on Nov 14 and 15. | S2 |
| 3 | **The cheapest large gain for local reasoning waits behind a 17-step chain on a help feature.** | L1 (seven edges: the import component from 189 modules to 36) could start when D6 landed. It hasn't; the component is 186. L4's review (learned models callable without a database) hasn't started either. The figures chain is at step 8 of 17. | S3 |
| 4 | **The largest file on the serving path grew through the refactor and has no step.** | `daily_plan/engine.py`: 5,977 lines at the map, 6,546 at S0, 6,788 now. §4 rules out reworking it. The ratchet doesn't see file size. | K11, M1 |
| 5 | **"A core returns its record" (L6) is a rule nobody is held to.** | I1 and I2 landed after the rule. Their records are still built beside them (`attempts/grade_records.py`, `scheduling/slate_record.py`); neither step's record mentions L6. | L6a |
| 6 | **The strategy doesn't know what's built next, so it isn't shaping the code those features land in.** | §2.16 lists TE4, RE3-RE8, phone and MCP. The next model work you've named (adaptive difficulty's memory, evidence packets for the action model) lands in `adaptive_difficulty/` and the model-context builders. Neither has a structure step ahead of it except E7's second half, which waits behind all of arc E. | S4, E7b, B-row |

Two smaller ones: the test tree gained 119,000 lines of golden JSON since S0 with no measure on it (§2.7), and landing by fast-forward into your working checkout now collides with your uncommitted edits (§2.8).

**The new ideas** (adaptive difficulty's memory, the Decider and the packets, "assisted", hypotheses as claims) are evaluated in §4. All of them fit, two need tuning, and they are behaviour-track work: none belongs inside a refactor step. Two draft specs carry them: `docs/specs/spec_ad_memory_v1.md` and `docs/specs/spec_evidence_packets_v1.md`.

**What you'd decide:**
1. Whether D7 stops after batch 3, with the rest left to the next floor move (S2; my recommendation: yes).
2. Whether L1 and L4's review go ahead of the remaining figures steps (S3; yes).
3. Whether `engine.py` gets a read-only map before arc E (K11; yes).
4. How landings reach main while you have edits in the main checkout (§2.8).
5. The two specs' open questions.

## 1. Where the refactor stands

**Landed** (from the step records in `docs/reviews` and the log): S0; arcs A, B and C with J1; K0, K1 and its fixes, K2's two documents, K3.1-K3.5; D1, D2a, D2b, D3, D4, D5, D6; D7's inventory and batch 1 parts 1-4 (12 switches); I1, I2; F1; RE2; K2.1-K2.5; K9's and K10's maps and strategies; K9.0; K10.4-K10.6; M0, L7, T1, T3; the phase-1 adversarial review and its fix rounds; arc D's close fixes, groups 1 and 2.

**In flight today:**

| Step | State |
|---|---|
| K10.7 + K10.8 (figures: `service.py` split into request, grounding, view, listing, predictions, build) | Complete. My own check: 161 of 162 top-level definitions AST-identical to the base (`__all__` is the one that differs), no golden or fixture changed. In its landing gate. |
| D7 batch 3, part 1 (seven switches of Today) | Complete, with its own sweep green (29,015 passed). **Can't land:** it edits `config/schema.py`, `tests/goldens/effective_defaults.toml` and a Config note, which the main checkout holds with uncommitted edits (§2.8). Part 2 is running on top of it. |
| The rebuild fix (D-36, D-52, D-35, D-53; `fix/arc-d-close-3`) | Landing-ready since Nov 15. **Waits on the owner:** it changes derived facet values on two vault copies (`scratchpad-backup/adfix3-deltas.md`), and it needs to know whether any vault is already at mvp-0.59. |

**Not started:** L1, L2, L4's review, L5, K4-K8, H2, G3, D7 batches 2 and 4, D8, all of arc E.

**Measured** (git at each tip; `structure.toml` for the held numbers):

| Measure | S0 (Nov 9) | First audit (Nov 12) | Now | Target |
|---|---:|---:|---:|---|
| Python files under `src` | 1,285 | 1,277 | 1,238 (−3.7%) | down 6-11% |
| Raw lines under `src` | 632,055 | 622,736 | 614,415 (−2.8%) | down 5-9% |
| Upgrade modules | 45 | 46 | 0, and one table of 422 lines | 1 table |
| Root modules | 78 | 78 | 35 | about 28 |
| Functions over 200 lines | 83 | 83 | 73 | down |
| Largest import component | | 189 | 186 | 40 or fewer |
| Modules in any import cycle | | 286 | 279 | down |
| Comment lines naming a stage artifact | | 2,424 | 2,374 | down |
| `db/repositories.py` lines | | 27,508 | 27,449 | (L2: by file) |
| `daily_plan/engine.py` lines | 6,546 | | 6,788 | none |
| Effective config leaves | | 1,189 | 1,171 (1,164 after part 1) | down |
| Bug ledger | | 28 rows | 130 rows: 39 open, 12 queued | none open at an arc's close |
| Landing gate tests | 31,037 | | 31,014 | |

`git diff --shortstat a810f628d8 HEAD`: `src` +19,779 −37,428; `tests` +177,987 −47,713, of which 118,935 added lines are golden JSON in 44 files and the Python is +55,755 −47,705.

**Reading it.** Arc D delivered what the strategy said it would: history is gone and the numbers that depended on it moved (root modules, upgrade code, functions over 200 lines). The numbers that describe local reasoning (the import component, the cycle, the two largest files) have barely moved, because the steps that move them haven't run.

## 2. Deficiencies

### 2.1 The plan itself is now hard to read, and its state lives outside the repo

The strategy began as 66 steps in eleven arcs with a one-page summary. It has since gained arc K (§2.17), the first audit's additions (§2.18), the lanes and test rules (§2.19), and three sub-strategies in other files: K2 (12 steps), K9 (18) and K10 (17). The summary table, the cost section (§2.15: "45-90M tokens", "3.5-6 weeks") and the stopping points still describe the 66.

A step's state is in none of these. "Done" is marked in prose for a handful (M0, L7, K1, K2), and everything else is in `merge-queue-notes.md`, a 680 KB file in one session's private scratch directory. When the orchestrator's session was cleared on Nov 14 and again today, the state was rebuilt from that log, the transcripts and `git worktree list`. Each of the last three handoffs lost something: the first audit never contacted the running session; this one found two implementers dead for 22 hours with finished work uncommitted or unlanded.

That is the cost the refactor exists to remove (discoverability, onboarding), in the refactor's own plan.

### 2.2 No economy measure for the refactor

§2.15 says "I have no per-stage usage figure to calibrate against". There are figures now, in each implementer's completion notice, and nobody records them:

| Step | Implementer tokens | What it bought |
|---|---:|---|
| D7 batch 3, part 1 | about 570,000, 3.1 h | 7 switches; `src` +169 −413; 7 config leaves; kept-because list 82 to 75 |
| The rebuild fix (three hand-backs) | about 490,000 | 4 ledger rows fixed, 3 found |

A landing gate is 45-60 minutes of the one full-suite lock, and behaviour steps and most D7 parts land alone. With about 75 steps left, the gate alone is more than 75 machine-hours, and the weekly usage limit has already stopped the queue twice.

D7 is where it shows. The inventory lists 84 kept-because switches; batch 1 took five parts for 14 switches. The log already says batch 2 "is not mechanical" (three switches the planted-type simulation needs off) and batch 4 waits on arc E. L7's rule means a switch left today goes at the next floor move at no extra design cost. The strategy has no rule that says "this tail has stopped paying; leave it on the list".

### 2.3 Order: what moves the brief's numbers is at the back

The first audit's additions were approved on Nov 12. Since then M0 and L7 landed and K9 and K10 were written. L1 was ordered "after D6"; D6 landed on Nov 14. L4's review was ordered "beside arc D". Neither has started. Both Opus slots have gone to D7 and to the figures chain, which is at K10.8 of 17.

Figures are help, never certification, and the owner ruled on Nov 14 that the phone and MCP get none. `figures/service.py` was a god module and its split is good work, but K10.9-K10.17 are records, a pure reader, a note and two retirements for one desktop feature. L1 is one medium step that takes the unit a reader can't reason about locally from 186 modules to about 36. L4's review is read-only and decides how every learned model gets tested, including the one the owner wants to change next (§4).

### 2.4 `engine.py` grew 13% and nothing reads it

`daily_plan/engine.py` decides what Today serves. §4 says not to rework it "beyond I2 and E6", for a good reason: it carries real policy. But arc B's records, IH and the fix rounds added 811 lines to it since the map, and arc E's nine steps restructure the chooser and the objective underneath while leaving the traversal alone. After arc E the engine will be the largest module on the serving path by a wide margin, with no map of its phases and no ceiling.

`attempts/attempts.py` (5,812 lines, up 160 since the map, after I1 took 774 lines' worth of logic into a core) shows the same thing: a core was extracted and the file didn't shrink.

M0's ratchet counts functions over 200 lines, which is the right unit for comprehension, but it doesn't notice a file that grows by adding functions of 150.

### 2.5 L6 has no teeth

L6: "every pure core the arcs extract (E2, I1, I2, G1's `probe_facts`, L4's) returns its `DecisionRecord` with its result. For each, `tests/test_why_cases.py` stages one case per rule code the core can return." I1 and I2 are on main. `grep DecisionRecord src/learnloop/attempts src/learnloop/scheduling` finds only the builder modules arc B wrote. The steps' briefs didn't carry the rule, so the implementers didn't apply it, and nothing failed.

The risk L6 names is live: a core that gains a branch its builder doesn't know leaves a record that says less than the decision did.

### 2.6 The next features aren't in "what builds on this"

§2.16 was written on Nov 9. The work the owner has named since (§4 of this audit) lands in three places:

| Where | What changes there | Structure step ahead of it |
|---|---|---|
| `adaptive_difficulty/state.py`, `replay.py`, `model.py`, `outcomes.py` | Which attempts train the model, new latent terms, a learned decay | L4's review, not started; nothing AD-specific. 17 AD modules sit in the import component |
| The model-context builders (the router's card and history, diagnosis packets, the tutor's context) | Facts about each attempt in place of one label; hypotheses with their evidence | E7's `learner_signals`, the last step but two of arc E. The map counted 11 files for one new signal (TE0) |
| The attempt's own facts (what help preceded the answer) | One record of each fact, read by scoring, AD and every packet | None. Appendix B's table has no row for it |

Observability is uneven at the same place. Arc B records why a decision was made from numbers and ids. What a model was shown is recorded in one of the three places it matters: the action model's card keeps a count of entries cut per section in the objective trace (`objective_chooser.py:875`, `objective_card.py:76`). The Decider's card and the diagnoser's context trim too (`router/card.py`, `diagnosis/split/context.py`) and keep nothing, and `why` shows none of it. Once a cheap model helps choose what goes in a packet (§4.2), that choice is a non-deterministic decision upstream of every other, and it needs a record in the same place as the rest.

### 2.7 Goldens: 119,000 lines nobody will read

The move steps prove themselves with goldens, which is the right proof for a move. 44 JSON files hold them now; `tests/goldens/grade_application/history.json` alone is 40,815 lines and `tests/fixtures/figure_build_golden.json` 21,384. Once the moves are done, a byte-level golden of a whole journey makes every later behaviour change regenerate tens of thousands of lines, and a reviewer can't see the one value that mattered. The rebuild fix already had to regenerate `history.json` and attach an accounting by hand. T5's shape pass doesn't mention goldens, and no measure counts them.

### 2.8 Landing into a checkout that isn't the orchestrator's

Landings fast-forward main in `/home/saturn/Documents/thinking/learnanything`, where the owner also edits. Today that checkout holds uncommitted edits to 17 files (the Sol model default and the Decider's billing fields), and a Codex session is running in it. A fast-forward that touches any of those files is refused, which blocks D7 batch 3 now and will block every D7 part and config change after it. The rules block forbids implementers from touching that checkout but says nothing about how the orchestrator lands when it's dirty.

## 3. Additions

Same form as the strategy's steps. All structure-track unless marked.

**S1. One status table, in the repo** (S). Now.
- **Problem:** §2.1.
- **Files:** new `docs/reviews/refactor-status.md`; the strategy's summary, §2.14 and §2.15.
- **Does:** one row per step, every arc and sub-strategy included: state (landed, in flight, waiting on, not started, dropped), the landing commit, the record, the owner's call it waits on, and the implementer's tokens. The orchestrator edits it in each landing commit. The strategy's summary is rewritten to the real count, and its landed steps collapse to one line each pointing at their records. No private data.
- **Adds:** one file, and it replaces the private log as the source of state. The log stays as working notes.
- **Proof:** a fresh session answers "what is running, what is next, what waits on the owner" from that file alone.

**S2. A stop rule for tails** (a rule; no step).
- **Problem:** §2.2.
- **Does:** each step's record states its implementer tokens and gate count beside what it removed. A batch step (D7, L5, K2.10-style folds) stops when its last part cost more than twice the batch's first part per line or leaf removed; what's left goes on its list with the reason.
- **Applied now:** D7 ends with batch 3. Batch 2's three switches go on the kept-because list as the simulation's. Batch 4's `router_objective.*` switches go with the arc E step that opens their file. `replay.ledger_bounded` and `mastery.claim_fixes_enabled` go with the rebuild fix's landing, which already edits them.

**S3. Reorder the open lanes** (no step).
- **Problem:** §2.3.
- **Does:** L1 takes the next free slot. L4's review takes the next read-only slot, with `adaptive_difficulty` and `router_objective/memory.py` first (S4). L2 runs at arc D's close as planned. K10.9-K10.17 fill gaps, and K10.14 (the desktop reads `shown` and the label from the server) keeps its place before the UX overhaul.

**S4. The strategy names what's built next** (S, docs).
- **Problem:** §2.6.
- **Does:** §2.16 gains two rows: adaptive difficulty's memory model (depends on L4 for AD) and evidence packets (depends on E7b and the facts row below). Appendix B gains a row: **what help preceded an answer**, one owner, with today's holders listed (the reveal ledger, `help_assists`, the help questions, the attempt's own columns, AD's `AttemptFacts`), so that G5's method applies to it.

**E7b. `learner_signals` ahead of arc E** (M).
- **Problem:** E7's second half ("then `learner_signals(connection, lo, at)` for the other context builders") depends on nothing in E1-E6: it touches `diagnosis/split/context.py`, the tutor's and the hints' context builders, not the chooser.
- **Does:** that half moves to run beside arc E's start. The router's sensors (`daily_plan/sensors.py`) stay E7.
- **Proof:** E7's: input hashes that include a context must not move at the same inputs (K0's pins).

**K11. `engine.py`: a map, then steps only where one names a cost** (M; review, K2's method on one file). Before E2.
- **Problem:** §2.4.
- **Questions:** the traversal's phases and what each reads and writes; which of the 811 added lines are record assembly that L6 would move; what arc E's steps leave in it; whether its phases can be named functions in one module each without a new concept.
- **Stop:** if the map finds no named cost, it says so and no step follows.

**M1. File ceilings in the ratchet** (S).
- **Problem:** §2.4.
- **Files:** `scripts/refactor_measures.py`, `tests/goldens/structure.toml`.
- **Adds:** the line counts of the five largest serving modules as held numbers (`engine.py`, `attempts.py`, `repositories.py`, `scheduler.py`, `handlers/reader.py`), and the golden JSON line total (§2.7). M0's pattern; no new test.

**L6a. L6 applies to the cores already extracted** (M).
- **Problem:** §2.5.
- **Does:** `attempts/grade_application`'s core and `rank_due` return their record with their result; `grade_records.py` and `slate_record.py` lose what moved. `tests/test_why_cases.py` gains one staged case per rule code each can return. From here the rules block carries L6, so a brief can't omit it.
- **Stop:** if returning the record from `rank_due` would put a write on the read path I2 just cleaned, the record is returned and written by the caller, as §3.2 already says.

**P1. A record of what a model was shown** (M). Before the evidence-packet spec's first build step.
- **Problem:** §2.6.
- **Does:** one `packet` record per model call that informs a decision, built by the packet's own builder (L6): per section, rows offered, rows included, rows cut and the rule that cut them, bytes; the versions of the builder and the prompt. Ids and numbers only, as §3.7 requires. `why` shows it under the `model_answer` it fed. The action model's card already counts what it cut; that count moves into the record, and the Decider's card and the diagnoser's context gain the same.
- **Abstraction:** none new: a `kind` on the existing table.

**T5 widened: goldens reviewed at the shape pass** (part of T5).
- **Problem:** §2.7.
- **Does:** each move-proof golden is either kept because it pins persisted meaning or a prompt, replaced by the narrower test that states what mattered, or deleted with its reason. M1 holds the total.

**A landing checkout** (owner's call).
- **Problem:** §2.8.
- **Options:** (a) the owner commits or branches their edits before a landing window, as today but stated; (b) the orchestrator lands from its own clean worktree by pushing to `origin/main`, new worktrees branch from `origin/main`, and the owner's checkout pulls when it's clean. (b) removes the collision; it means local `main` in the owner's checkout can be behind.

**What not to add.** A rewrite of the strategy; a second ratchet test; a packet store beside the receipts; a registry of signals; any new arc for `source_retrieval`, `reader` or `teacher` before K8 and K11 say what they'd buy.

## 4. The new ideas

Each was checked against the code first. The specs hold the designs; this is the verdict and the tuning.

### 4.1 Adaptive difficulty: families, memory, a learned decay

**What the code does today** (`adaptive_difficulty/replay.py:466-476`, `priors.py:33-39`, spec §5):
- Only the first graded attempt on each surface group trains the model. Every repeat is excluded with reason `repeat_surface` ("repeat attempts on the same surface are FSRS's job", D10). Repeats still count as exposures.
- The model has no forgetting of the mean. Variance drifts by 0.01 a day.
- "Warmth" isn't a six-hour delay or window. It's a covariate, `w = exp(−Δh / 6)`, with a learned coefficient ζ, over hours since the last exposure to the learning object. Nothing is dropped inside six hours. The six is a fixed constant.
- Each item's residual is integrated out per attempt, which is only right because each item is seen once.
- The router's objective combines AD's prediction for an unseen item with FSRS retrievability through a fitted logistic (`router_objective/memory.py`).
- A per-family FSRS projection exists (`family_memory_state`, keys item, family, learning object) and nothing reads it for decisions.

**Verdict: the direction is right, and it reverses a decision (D10) rather than filling a hole.** Repeats are most of what a returning learner produces, and the model throws them away. Your four mechanisms are the standard structure of the models that do this well (DASH and DAS3H: ability, difficulty and a history term over time windows; hierarchical item and family effects), and they fall out of one change: let a repeat train, and give the model somewhere other than ability to put the credit.

**Tuning:**
1. **Dependence comes first, not last.** If repeats train and nothing else changes, five successes on one familiar item count as five independent measurements of ability. The item and family effects have to land in the same successor as the repeats, or the posterior becomes overconfident. With them, your "repeated successes update item memory or family proficiency when the explanations fit" is what the update does on its own: credit splits by how uncertain each term is, so a repeat on a well-measured learner moves the item and family terms, and a novel family, whose terms are at their prior, moves ability.
2. **Your decay equation contains FSRS.** `dm/dt = −m / τ(m, z)` with `τ = T(z) · m^(−κ)` has a closed form, `m(t) = m₀ · (1 + κ t m₀^κ / T)^(−1/κ)`: exponential as κ goes to 0, a power law otherwise. The curve this codebase uses (`scheduling/fsrs.py:58`, FSRS-6), `R = (1 + f t / S)^(−d)`, is the member with `κ = 1/d` and `T = S / (f d)`, where `d` is already one of FSRS's weights. So the learned decay can start exactly at FSRS and learn its departure from it: `d`, and `T(z) = S · exp(wᵀz) / (f d)`, which is the "liquid stability" already kept as optional in `spec_learned_parameters_v1` §4.6 and re-specified as RE8. No ODE solver is needed, which matters because replay must be deterministic.
3. **One memory, not a fourth.** The system has FSRS per item, FSRS per family (unused), facet recall state, and the router's combiner. A memory state owned by AD would be a fifth forgetting model. The spec puts the learned curve behind RE2's one retrievability function and has AD read it for item and family keys, read side only at first; whether the scheduler and the rollouts move to it is a later call of yours, with a replay report.
4. **Warmth: learn the scale with a basis, as AD already does for reading dose.** The filter is linear in its state, so a decay constant can't be a state coordinate. AD's own precedent (`DOSE_SCALES`: "a basis, not a shape") is two or three fixed scales with learned weights; a sum of exponentials with learned weights is a learned decay curve. The prior puts all the weight on six hours, so at the prior it is today's model.
5. **Data.** Your largest vault holds on the order of a hundred graded attempts, and RE8 counted at most 19 same-item repeats. Every new term will sit near its prior for months, so the priors are the design: seeded from FSRS's population fit and from today's constants, never hand-set per item, and the report says how far the data has moved each one.
6. **What it doesn't change:** AD still serves only never-attempted items; the forecast event stays "unassisted success"; certification's coldness rules (`MIN_COLD_DELAY`, the reveal threshold) are a different authority and stay.

**A structure step it needs first:** L4 for AD (the update callable with literals), so the new terms are tested without a vault. That's S3 and S4.

### 4.2 The Decider and the GPT prompt

**What the code does today.** The Decider is called from about fifteen places, always as a chooser, sensor or judge; it never selects what another model sees. Most of those sites already send it the same prompt the LLM gets and log both verdicts under one input hash (`judgment_ledger`, `ai/agreement.py`). The router is the exception, and only since the objective path (RO4):

| | Decider (`router/card.py`, card v3 as text) | Action model (`daily_plan/objective_card.py`, JSON) |
|---|---|---|
| Size limit | 16,000 "tokens" counted as bytes / 4: about 64 KB | 48,000, named tokens, counted as bytes: 48 KB |
| Open hypotheses (statement, status, since), the learner's marks | yes | **no**: learner-named gaps and cause-class probabilities only |
| Help requests, questions, reveals, the learner's own statements | **no** | yes |
| Goals with weights, exam sittings, other topics | dates only | yes |
| Whole answers | 400-character excerpts, 30 attempts | up to 4,000 characters, 400 rows |
| The objective, in words | **no** | yes |

So the two are compared on different evidence, and the model that decides has the smaller limit and no hypotheses at all.

**Verdict: both ideas are sound and they share one prerequisite; do that first.** Comparing two models on different information tells you about the information. Having the Decider help build the packet makes packet building a non-deterministic decision. Both need the same thing: one typed view of the evidence (attempts with their facts, hypotheses with their support), built once, rendered twice. That is E7b's `learner_signals` with a schema. The older router path (`BoundaryRequest`) worked this way: one state text, two instruction wrappers.

**Tuning:**
- **The Decider annotates and orders; it never removes.** Its judgments (does this attempt bear on this hypothesis; was it independent) decide the order rows are admitted under the size limit and are shown as labels. A row it ranks low is cut only by the limit, and the packet says how many were cut. This is the rule G2 already uses for the learner's own narrowing.
- **Off the Next path.** Router speed's target is still unmet. Judgments are made in the post-attempt jobs and cached by content; the packet builder reads the cache and never waits. A missing judgment falls back to the deterministic order, and the record (P1) says so.
- **Comparison without a shadow stage.** With one view, asking the Decider the same question the action model answers is one more cheap call on decisions already being made, logged beside the outcome. Agreement by decision kind, and which one the later outcome favoured, come from rows.
- **Its reliability is learned,** from agreement with the action model and with outcomes, not set.

### 4.3 "Assisted" becomes separate facts

**What the code does today.** There is no stored "assisted". It is derived on read, in at least twelve places, from three inputs (`attempt_type`, `hints_used`, `primed`), and the derivations disagree:

| Where | "Assisted" means |
|---|---|
| `diagnosis/causal_activity_policy.py:168` (the canonical one) | one of three assisted attempt types, or any hint, or primed |
| `substrate/intervention_outcomes.py:103` | any attempt type outside three unaided ones (so an open-text answer is assisted), or a hint, or primed |
| `learner_context.py:1389`, `daily_plan/router_card.py:818` (what chat and the Decider's card are told) | **primed only**; hints sit in the next field |
| `attempts/coldness_receipt.py:1457` | any hint, primed, or any recorded reveal at all |
| `teacher/brief.py:363` | three kinds: cold, assisted, primed |
| `diagnosis/split/context.py:476` (the diagnoser) | two bare booleans, `assisted` and `primed`, that its prompt never defines |

The inputs are themselves collapsed at the fold: hint levels 1-3 become a count, levels 4-5 become `primed`, a figure counts as a hint, and a reveal over 0.35 forces `primed` (`db/stores/help_assists.py:270`, `attempts/attempts.py:2436`). The facts underneath are all stored: `help_assists` has one row per assist with its kind, level and time, `reveal_events` one per reveal with its source and amount, and the attempt has `first_hint_progress`.

**Verdict: yes, and this is as much a refactor finding as a feature.** Twelve copies of one predicate is the duplication the strategy's G6 removed for protection ("one authority per question"). AD already shows the target shape: `adaptive_difficulty/outcomes.py`'s `AttemptFacts` carries hints, when the first hint came relative to the draft, help questions before or after work, pre-exposure, priming and "stuck" as separate fields and derives its categories from them. One definition of those facts, read by scoring, AD and every packet, is Appendix B's method (S4's new row).

**Tuning:** nothing needs backfilling, because the facts are already rows; attempts from before `help_assists` (migration 210) say "help: not recorded in detail". Each reader that needs a category (certification's "independent", AD's outcome category, FSRS's rating cap) keeps it as a named function over the facts, in one module, so the first step changes no value. Where two derivations disagree today, the step that unifies them names the difference and it goes on the bug ledger; it isn't silently resolved.

### 4.4 Hypotheses as claims with their context

**What the code does today.** The action model is shown no hypotheses. The Decider's card shows a line each (`topic: kind (status, since DATE): statement`). The diagnoser sees a count of supporting evidence and a last-updated date that is really the newest version's creation time. No table links a hypothesis to the observations that supported or contradicted it, and none has a last-supported time; weights sit inside `evidence_json`. The richest rendering in the code is a research arm nobody serves from (`field/probability_states.py:587`: evidence for and against as bounded lists of attempts with days and results, repairs tried).

**Verdict: yes; it depends on 4.3, and it runs into one earlier decision.** A hypothesis shown with only its statement looks as current as the day it was raised. The four things you list (what supported it, when it was last supported, which later attempts bear on the same skill, and whether those were independent, repeated or helped) are what the action model needs to discount a stale one, and the last of them is 4.3's facts. No new table is needed: support and later attempts are derivable from the hypothesis's episode, the cold verifications, the marks and `facet_outcome_observations`, which already holds each attempt's facets and surface group and which nothing reads. The spec defines the claim card and what's counted instead of listed when there are many.

**The earlier decision:** slip-versus-gap (mvp-0.57) gives the action model cause-class probabilities and "never the hypothesis statements, which can restate the expected answer". Putting claims in its packet reverses that for the action model. The statements already go to the Decider and to chat under the existing withholding rule (`statement_text`), and the action model isn't the grader, so I recommend the same rule; it is your call (the spec's Q3).

### 4.5 Others worth wrapping in

- **P1, the packet record** (§3): the highest return here, because every item in 4.2-4.4 changes what a model is shown.
- **A stratified prequential report for AD:** log loss and calibration by first surface, repeat item, repeat family and novel family, by delay bucket and by help facts. It is the acceptance test for 4.1 and it reuses `adaptive_difficulty/scoring.py` and the simulation library.
- **Help as a learned effect, not an exclusion.** With facts separated, AD can learn what a hint rung does to the chance of success instead of scoring every helped attempt as a failure of the unassisted event. Later, and only after 4.3.
- **Slip versus gap reads memory.** A miss on an item the memory term says is strong is more likely a slip. One covariate into mvp-0.57's model, once 4.1 exists.

## 5. Limits

- **Token figures** are from two completion notices in the previous session's transcript. Most steps' figures were not kept, so S2's rule is argued from two rows.
- **"Not started"** is from the absence of a record in `docs/reviews` and of a mention in the log since Nov 14. A read-only review could have run without leaving either.
- **The mappers' reports** were checked only at the lines their main claims rest on (the AD constants and eligibility, the outcome categories, the router's combiner). The specs say where a claim is the mapper's alone.
- **Not read:** arc E's code, `engine.py` itself (the claim in §2.4 is its size and the strategy's text), the K9 and K10 strategies beyond their summaries, the frontend.
- **Not run:** any test, the timed lanes, `scripts/refactor_measures.py` (the held numbers are from its golden).
