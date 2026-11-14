# Diagnosis strategy (K9, 2026-11-14)

Refactor arc K, step K9, job 2. It stands on the map `docs/reviews/k9-diagnosis-map-2026-11-12.md` (ids D9P, D9D, D9B, D9O, D9F, D9C, D9H, D9V are the map's), re-checked at this tip (§0). **Base: main `ace5d5f9b4`**, branch `refactor/k9-diagnosis-strategy`. Docs only: no file under `src/`, `apps/` or `tests/` changed. **Status: for the owner's review.**

**Evidence** is `file:line` at `ace5d5f9b4`, with the map's convention: `src/learnloop/` is dropped (`diagnosis/probe_episodes.py:1869` is `src/learnloop/diagnosis/probe_episodes.py:1869`), `learnloop_sidecar/` keeps its prefix, frontend paths start `apps/`. Counts come from read-only sweeps run at this tip, each through an `env -i` wrapper with an empty `HOME`, no model call and no vault opened (orchestrator scratch, `refactor-k9s/`): the map's own AST and import sweep re-run unchanged (`sweep_k9_copy.py`, output `now/sweep.txt`), a name-level caller sweep (`names_k9.py`, `now/names_*.txt`), a section-level reference graph (`intra.py`) and a split simulation over the import graph (`simsplit.py`, §4.3). Every estimate says so.

## Summary for the owner

**What is wrong.** Diagnosis works and much of it is careful: bundles written before the answer, content-addressed observations, typed refusals, a pure Bayes step and a pure repair choice. What costs you is five things. Three learner-visible faults: "Stop diagnosing and teach me" mid-check leaves the block's answers un-normalized, undiagnosed and their feedback never shown (ledger TH-3); the screen says "You asked me not to check" when the system withheld the check for burden or budget (K9-1); and a probe answer whose grade was held and then released, or regraded, never moves either belief (K9-3). Two questions you cannot ask afterwards: why the quick check wasn't offered (the causal lane's verdict has no decision record) and why a probe answer wasn't read (the classifier's six declines and the four per-attempt hooks' failures leave a log line at most). And two modules of about 3,500 lines each (`causal_orchestrator.py`, `probe_episodes.py`) hold, between them, the repair lane's decision, its learner actions, both beliefs, the stopping policy and the serve gate, tied into a 21-module import cycle that only function-local imports hide.

**The moves that matter:**
1. **Fix the three ledger faults first** (K9.1-K9.3), each small and from a failing test. TH-3 is due at arc D's close.
2. **Pin what nothing pins, then split the two large modules by who calls them** (K9.5-K9.11). Diagnosis has no golden and only one identity pin today. The split is moves only, in the shape of K2.5 (which paid), not K2.4 (which unified and grew). It cuts the 21-module diagnosis cycle to 11 by a simulation (§4.3), ends `probe_blocks`' imports of private functions, and puts arc G's two targets (the probe decision and the discriminating observation) in modules of about 1,000 and 600 lines instead of one of 3,471.
3. **Record why** (K9.12, and the verdict's record inside G1): a withheld offer, an unread probe answer and a failed hook each get a row the trace reaches.
4. **Let arc G do the deciding.** K9 does not build `probe_facts`, the router as decider or one belief. It hands G1 a shape that its reads already allow (§4.6) and gives G4 a posterior that can be tested with literals (K9.13, conditional).

**What you must decide** (§9 has the detail):

| # | Question | Recommendation | Yes costs / No costs |
|---|---|---|---|
| Q1 | When does a repair episode whose primed attempt is never taken end (R1-2)? | **When the item's next ordinary review comes due**, with "the learner declined" added if the UX audit gives them a decline | Either: one small behaviour step (K9.4) on the existing sweep seam, no migration (`abandoned` is already a state, `migrations/058_remediation_episodes.sql:6`). No answer: the episode stays open and its cold item's protection stays tied to the cold retry only |
| Q2 | Should a held grade that is later released, or a regrade, move the beliefs (K9-3)? And where is it fixed? | **Yes for the episode posterior. Fold it into G4 if G3 says G4 runs; otherwise its own small successor (K9.17).** The discriminating observation follows G4's answer | Yes: a successor with a kill switch and a shadow rebuild (P-playbook). No: write down that a probe answer's first classification is final, and the ledger row closes as "by design" |
| Q3 | Delete `diagnosis/failure_triage.py` (no caller; the registry imports it by string; L3's list)? | **Yes** (K9.15, S) | Yes: 1,054 lines, its three registry entries and the two `Repository` methods only it uses go; the table stays readable for `causal_health`. No: it stays dead code that a deletion by import alone would break |
| Q4 | Retire the EVSI-2 shadow selection that runs beside every probe decision with zero live authority? | **Yes, with or after G2** (K9.16, M) | Yes: about 600 lines (`record_shadow_selection`, its receipts writer, the readiness report) go, and you lose the "causal selection readiness" panel on the measurement-health screen. No: every probe decision keeps paying for a shadow nothing promotes |
| Q5 | The parameter registry: should diagnosis get a new way to register constants? | **No step in K9.** Moves keep each registered path in the same commit. If you want registration beside the constant, make it one cross-package step for all 380 entries, not a diagnosis-only second way | §4.9 |

**What stays as it is, and why:**
- **The guarantees arc G names** (§3, principle 5): bundles before the answer, the pin of ids, the locked set before the answer, the posterior at selection, the discriminating observations' eight readers, old rows readable. No step here edits them.
- **The pure pieces that are already pure:** `_bayes_update` (`diagnosis/probe_episodes.py:2074`), `select_minimal_repair` (`diagnosis/causal_attribution.py:691`, called with plain values only), `decide_probe` given its parameters (`diagnosis/causal_probe_coherence.py:413`), robust composition, the prior-analysis arm (`diagnosis/split/prior_analysis.py:86`), the instrument likelihoods (`diagnosis/probe_families.py:450`, `:505`, `:716`).
- **The episode lifecycle, instruments and posterior stay together** in `probe_episodes.py`: they reference each other in both directions (§4.4), so splitting them would add a cycle, not remove one.
- **The hypothesis-label literals in five modules** (D9C3): no label has been added since the Aug 20 squash, so the copies have not drifted. One vocabulary module would be K2.4's lesson again: an abstraction with nothing yet to pay for it.
- **The SQL CHECKs for stop reasons and gap source kinds** (D9H4): their cost is the head fixture and upgrade tests, which arcs A and D own.
- **`split/`, `text_gaps/`, `recurrence/` and `offline_review/`**: no step restructures them. Their remaining 11-module cycle (§4.3) runs through `apply_diagnosis`'s hook list, and cutting it is L1's edge work.

**Cost.** Seventeen steps: twelve that run without your answer (four S, eight M), four that wait on Q1-Q4 (two S, two M) and one M conditional on G3. About two weeks of queue at the strategy's pace, with the three fixes about a day together (§5; an estimate). The package grows by about 100-150 lines through the moves and shrinks only by deletion: about 190 lines without your answers, about 1,850 with Q3 and Q4 (§6; estimates).

## 0. The map at this tip

The map was written at `95bee5f02a`. Main has moved 442 commits (403 without merges), but diagnosis moved little: `git diff --stat 95bee5f02a ace5d5f9b4 -- src/learnloop/diagnosis` touches 12 files, +111 −384, and none of `causal_orchestrator.py`, `probe_episodes.py`, `probe_blocks.py`, `causal_probe_coherence.py`, `causal_attribution.py`, `followups.py`, `voi_stopping.py`, `chain_records.py` or `attempts/post_attempt.py`. So every line the map cites in those files still holds, and this document cites them as checked (the diff for the file is empty). The callers moved more: `attempts/attempts.py` (+/−236), `scheduling/scheduler.py` (+/−731, the due queue's serve/read split), `followup_run/router.py` (4 lines).

**Where the map is now wrong, or was:**

| # | The map says | At this tip | How counted |
|---|---|---|---|
| 1 | 110 modules, 73,609 raw and 53,389 code lines | **109** modules (`recurrence/upgrade.py` went with the 47 below-floor upgrade modules, `edc48a765e`), **73,336** raw, **53,192** code | the map's sweep re-run unchanged |
| 2 | 20 functions over 200 lines | **19**: `reschedule_assisted_cold_retry` (210) was split by P6 (`ab1431ee12`) into a 66-line shell and `_reschedule_assisted_cold_retry` (167, `diagnosis/remediation.py:1203`) | sweep; AST |
| 3 | 1,946 import statements to `src`, 560 function-local | **1,924**, **555** | sweep |
| 4 | The largest import component is 191 modules (189 by the audit), 65 of them diagnosis | **188**, still **65** diagnosis. The four diagnosis-internal components are unchanged: 21, 7, 2, 2 | sweep; the split simulation reproduces 188/65 with no split (§4.3) |
| 5 | `causal_orchestrator.__all__` has 48 names | **47** by AST. The module defines 61 public top-level names counting upper-case constants, 35 without (the map's count) | `names_k9.py` |
| 6 | The registry has 381 `_reg_const` entries; 157 commits touched it since Oct 12, 24 of them also diagnosis | **380** (39 diagnosis, unchanged by owner); **166** non-merge commits since Oct 12, **27** of the 211 that touched diagnosis | `grep -c '^_reg_const('`; owners by `grep -oP '^_reg_const\("\K[a-z_]+(?=:)'`; `git log --no-merges --since=2026-10-12` |
| 7 | The attempt step reads `probe_episodes` at `attempts/attempts.py:3069`, `:3097`, `:3382`, `:3498`, `:3655` | `:3045`, `:3073`, `:3365`, `:3481`, `:3635` (`record_remediation_attempt` at `:3471`) | `names_k9.py` |
| 8 | Scheduler EIG ranking at `scheduling/scheduler.py:3464-3477`; FG1's `decide_probe` call at `followup_run/router.py:128-149`, `hard_refusal` at `:93-118` | `scheduling/scheduler.py:3613-3622` inside `probe_score` (`:3488`); `followup_run/router.py:129-151` (`_observe`, `decide_probe` at `:136`), `hard_refusal` `:95-126` | grep |
| 9 | `misconception_posterior` at `diagnosis/misconceptions.py:850`, its clamp `:841-842` | `:756`, clamp `_PRIOR_FLOOR`/`_PRIOR_CEIL` `:747-748`; resolution `:822-861`. D5b removed the statement-matching normalization (998 to 904 lines) | AST; `git diff` |
| 10 | (not stated) `probe_blocks` imports two private functions of `probe_episodes` | Also the reverse: `stop_diagnosing_and_teach` imports `probe_blocks`' private `_first_error_from_block` (`diagnosis/probe_episodes.py:3466-3470`). Two more modules import `probe_episodes` privates: `probe_audit` (`_bayes_update`, `_observation_likelihoods_from_row`, `diagnosis/probe_audit.py:21`) and `diagnostic_surface_supply` (`_record_generation_need`, `:479`) | `names_k9.py` |
| 11 | (not stated) | Two public functions of `probe_episodes` have no caller in `src`, `apps` or `scripts`, only tests: `plan_precommitted_block` (151 lines, `:1664`; 2 test files) and `abandon_episode` (19 lines, `:3549`; 1 test file). Both are as old as the Aug 20 squash (`b19e81d999`) | `names_k9.py`; `grep -rw` |
| 12 | (not stated) | `_content_id` is defined three times, byte-identical: `diagnosis/causal_attribution.py:225`, `diagnosis/causal_orchestrator.py:343`, `diagnosis/causal_probe_coherence.py:189`. It mints the ids `cdo`, `bpb`, `bpi`, `cpc`, `cco`, `ccv`, `pma`, `rv`, `rc`, `dr` | grep; read |
| 13 | (not stated) | Diagnosis has **one** identity pin (`diagnostic_gate.fire_checkpoint`, `tests/identity_pins_helpers.py:610`) and **no** golden: none of the content ids above, the prior-analysis draw, the text-gap judge keys (`diagnosis/text_gaps/judges.py:241`, `:414`) or a journey's rows is pinned | grep of `tests/goldens/identities.toml`, `tests/identity_pins_helpers.py`, `tests/*golden*` |
| 14 | The strategy's G2 says "six sites answer" whether to probe | The map's ten still stand at this tip (#1-#10 of its §3.1 re-checked; new lines for #2, #3 and #9 above) | read |
| 15 | (after the map) | TH-3 was found by the teach hand-off routing (`docs/reviews/teach-handoff-routing.md:180-192`): a mid-check stop never ends the block. It is in the map's area and gets K9.1 | ledger `docs/reviews/refactor-bug-ledger.md:135` |

**What I re-checked and found as the map says** (files unchanged since the map unless a line is given): `_status_for_factor`'s 517 lines, its eleven reads and two pre-verdict writes (`diagnosis/causal_orchestrator.py:1414-1930`, writes `:1593`, `:1620`); `decide_probe`'s ladder and its "every threshold is resolved from the fitted store" (`diagnosis/causal_probe_coherence.py:432-433`); the eight withheld-offer and status arms (`diagnosis/causal_orchestrator.py:1800-1930`); `hard_refusal`'s copy of `_probe_episode_conflict`'s four lines and its order (preference before machine checks, `followup_run/router.py:105-120`, against `diagnosis/causal_orchestrator.py:2007-2017`); the held-grade inert observation and the replay skip (`diagnosis/probe_episodes.py:2596-2602`, `:1924-1927`); the six `decision_records` kinds (`diagnosis/chain_records.py:38-43`); the four grade-keyed hooks that only log (`diagnosis/followups.py:853-906`); `failure_triage`'s string import by the registry (`params/parameter_registry.py:127`, `:3099`) and its three entries (`:1130-1136`); `CausalAttribution.tsx`'s withheld line (`apps/learnloop-tauri/src/components/CausalAttribution.tsx:403-407`); the wall clock in the primed-sibling ranking (`learnloop_sidecar/handlers/feedback.py:1107`); the 14 CLI-only modules and `failure_triage`'s "none" reach; every commit count in the map's §7 table (`git show --name-only`, all ten re-run).

**What D4-D6 change here.** D4 and D5 deleted nothing in diagnosis; D5b removed the statement-matching normalization (`cf7d65e7e0`). D6 is not on main. Its branch (`refactor/d6-part2-wip`) removes five tag halves in diagnosis (`use_robust_probe` in `diagnosis/probe_robust.py`, the `VOI_STOPPING_VERSIONS` tests in `diagnosis/voi_stopping.py:243`, `:262`, `remediation.py:1131`, `text_gaps/actions.py:481`) and three beside it (`followup_serve/gates.py`, `followup_run/router.py:188-191`, `phone_probes_on`'s dead argument), +36 −86 lines. **No step below plans for code D6 deletes**, and the moves in K9.9-K9.11 start only after D6 lands, because D6 edits `probe_episodes.py:157-225` and `:2335-2360`. D7 (kill switches) would delete the off-paths that keep the count cap serving (`diagnosis/probe_episodes.py:1560-1566`, `:1599`, `:3055-3058`; `diagnosis/followups.py:348-349`) and FG1's predecessor in eight diagnosis sites. The moves carry those branches unchanged; if D7 runs first, they move less.

## 1. What K2.4, K2.5, I1 and I2 teach for this area

- **K2.4 unified two drifting paths, and its files grew.** The three sub-steps added 106, 6 and 96 lines (`docs/reviews/refactor-k2.4a.md`, `refactor-k2.4b.md:138-148`, `refactor-k2.4c.md:148-162`), and the kept differences became about thirty fields of mode records. It paid there because the copies drifted in 12 of 15 commits.
- **K2.5 moved a 1,081-line function into named stages with no logic change** and paid at once (longest function 1,081 to 175; `docs/reviews/refactor-k2.5.md:100-106`).
- **I1 extracted a two-stage pure core whose reads were exactly today's**, and it paid: 798 lines became a 100-line shell over pure stages, tested with literals. Its file grew 413 lines (types, docstrings, bindings; `refactor/i1-grade-application-core`'s `docs/reviews/refactor-i1.md` §6, not yet on main).
- **I2 stopped at step 0** because its pure core would have needed reads ahead of need, through `VoiContext` among others (`docs/reviews/refactor-i2.md:7-15`). That was the owner's call to make.

**For diagnosis, this means:**
- **Move, don't unify.** The duplicated predicates here (§3.1 of the map) are mostly arc G's: who decides, which belief. G1 and G2 replace them. K9 doesn't build a "probe policy" object over them, because G2 deletes the verdict it would wrap. K9 merges only what is byte-identical (`_content_id`) or a copy of a function it can call (`hard_refusal`'s conflict check).
- **The split is worth it here, by the commits.** Of the 17 non-merge commits since Oct 12 that touched `causal_orchestrator.py`, about 14 changed one of its sections only, by their hunks' line numbers at the time (mostly the learner actions, `:1933-2375`, and the discriminating observation, `:2446-3011`). Of the 26 that touched `probe_episodes.py`, about 20 did (mostly presentations and evidence). An estimate: hunk lines move between commits. A reader of those changes read a 3,500-line module to change a 400-700-line part.
- **A pure core only where the reads allow it, as I1's did.** `_status_for_factor`'s reads are unconditional after two early arms (§4.6), so G1's `probe_facts` is I1-shaped. The stopping policy's are not: `_evaluate_completion` reads eligibility only when the earlier rules let it continue, so a pure rule ladder would read ahead of need (I2's case), and K9 doesn't plan it.
- **Every structure step reports its net lines.** The moves add imports and docstrings: about 25-40 lines per new module, nine new modules, about +300 (estimate). Only deletion shrinks the package (§6).

## 2. The problems, ranked by what they cost

| # | Problem | What it costs you | Map | Evidence at this tip | Steps |
|---|---|---|---|---|---|
| 1 | **A mid-check stop never ends the block.** "Stop diagnosing and teach me" converts the episode; nothing runs the block end, and the attempt pipeline had deferred each in-block answer's normalization, workflow and diagnosis to it. | Answers never normalized (the lesson's brief misses their misconceptions), never diagnosed, their withheld feedback never shown | TH-3 | `diagnosis/probe_episodes.py:3447-3494`; `attempts/post_attempt.py:155-188`, `:312-322`; `diagnosis/probe_blocks.py:314-401` | K9.1 |
| 2 | **A wrong line on screen.** "You asked me not to check again for now" shows for every withheld offer, including the two the learner never asked for. The DTO's comment repeats the mistake. | The learner is told they did something they didn't | D9B5; K9-1 | `apps/learnloop-tauri/src/components/CausalAttribution.tsx:403-407`; `apps/learnloop-tauri/src/api/dto.ts:2008-2010`; `diagnosis/causal_orchestrator.py:1875-1903` | K9.2 |
| 3 | **A held grade released later, or a regrade, never reaches either belief.** The episode keeps the submission's outcome; the discriminating observation is never reclassified. | A probe's verdict can rest on a grade you overturned | D9D2, D9B2; K9-3 | `diagnosis/probe_episodes.py:1924-1927`, `:2596-2602`, `:2462-2463`; `diagnosis/causal_orchestrator.py:2984-2989` | Q2: G4 or K9.17 |
| 4 | **A repair episode whose primed attempt is never taken never ends.** | Its cold item's protection rests on another record; an open episode with no lifetime | R1-2 | ledger `:58`; `scheduling/serving_exclusions.py:130`, `:154`, `:339` | Q1: K9.4 |
| 5 | **"Why wasn't the check offered?" and "why wasn't this answer read?" have no stored answer.** The verdict's receipt has no `decision_records` row; the classifier's six declines write nothing; four per-attempt hooks fail to a log line. | Each such question is a code read, not a `learnloop why` | D9O1, D9O2, D9D5 | `diagnosis/causal_orchestrator.py:1467`, `:2967-3001`; `diagnosis/chain_records.py:38-43`; `diagnosis/followups.py:853-906` | G1 (its record), K9.12 |
| 6 | **Two modules hold the lane.** `causal_orchestrator.py` (3,471 lines: decision, learner actions, machine checks, the second belief, the cold check) and `probe_episodes.py` (3,651: lifecycle, presentations and serve gates, the posterior, evidence, seven stopping rules, controls). | A change to one part is read against all; G1, G2 and G4 all land in them | D9P1, D9P2 | §4.3, §4.4 | K9.6-K9.11 |
| 7 | **A 21-module cycle closed by function-local imports**, and modules importing each other's privates (§0 rows 10). | No module's imports say what it depends on; a missed local import fails only on its path | D9P3, D9P4 | sweep; `diagnosis/probe_blocks.py:29-36`; `diagnosis/probe_episodes.py:2173`, `:3465-3470` | K9.6-K9.11 (to 11) |
| 8 | **Nothing pins diagnosis's identities or rows.** | A move that changes a content id's input silently forks the idempotent ids written so far | (new) | §0 row 13 | K9.5 |
| 9 | **Three docstrings at the lane's centre are false.** | A reader goes to the wrong place first | D9C1; K9-4 | `diagnosis/causal_orchestrator.py:15-16`, `:2736-2738`; `diagnosis/causal_probe_coherence.py:432-433` | K9.6-K9.8 |
| 10 | **The parameter registry costs a line per constant in nine diagnosis modules and none in the other 100**, and calls hand-set numbers "decision" parameters. | A new constant in `voi_stopping` fails a test until registered; the 0.40 sensor cut in `causal_orchestrator` needs nothing | D9H3, D9B3 | §4.9 | Q5 (none in K9) |
| 11 | **Dead and shadow code beside the serving code.** `failure_triage` (no caller), the EVSI-2 shadow (no authority), two test-only functions. | About 1,850 lines a reader must learn to ignore | D9P5, D9C2 | §0 row 11; `diagnosis/causal_orchestrator.py:1491-1515` | K9.10, K9.11, Q3, Q4 |
| 12 | **The one concept note describes August's system.** | A reader starting there finds states that don't exist | D9V1, D9V2 | `docs/learnloop-architecture-vault/Concepts/Diagnosis and Remediation.md:8`, `:28-37` | K9.14 |
| 13 | Small: the primed-sibling ranking reads the wall clock, re-implementing `remediation._rank_items`. | A frozen-clock test sees wall time | D9B5; K9-2 | `learnloop_sidecar/handlers/feedback.py:1063-1107`; `diagnosis/remediation.py:437` | K9.3 |

## 3. Principles for this area

**1. The functional core, named.** Pure today (callable with plain values, no database, clock or model): the weighted Bayes step and entropy (`diagnosis/probe_episodes.py:2074-2094`, `:150`); the instrument likelihoods and outcome classification (`diagnosis/probe_families.py:450`, `:505`, `:716`); `decide_probe` given `parameters` (`diagnosis/causal_probe_coherence.py:413`; it reads the store only when none are passed, `:436`); `rows_are_separable` (`:370`); the repair choice `select_minimal_repair` (`diagnosis/causal_attribution.py:691`); the support arithmetic `_measured_hypotheses` and `_observation_support_scores` (`diagnosis/causal_orchestrator.py:2482`, `:2538`); the VOI math between `diagnosis/voi_stopping.py:480` and `:2176`; robust composition; the prior-analysis arm.

Pure decisions hidden among reads and writes, and whether each is worth extracting:

| Decision | Where | Extract? |
|---|---|---|
| The value of a probe and the verdict (gain, chance it changes the repair, burden, classes, hard stops) | `_status_for_factor`'s reads `diagnosis/causal_orchestrator.py:1622-1738`, then `decide_probe` `:1740` | **Yes, but it is G1's step** (`probe_facts`). §4.6 gives G1 the shape: the reads are unconditional after two early arms, so two stages with today's exact reads, as I1 |
| The episode posterior | `episode_posterior` `diagnosis/probe_episodes.py:1869-1981` gathers observations, incidental attempts, segments and the held predicate around the pure fold | **Yes, conditionally** (K9.13): a gather and a pure fold, before G4 or with K9-3's own successor. Not if G3 says G4 is skipped and Q2 says no |
| The stopping rules | `_evaluate_completion` `diagnosis/probe_episodes.py:2902-3052` | **No.** Eligibility is read only when the earlier rules continue (`:2973-2981`, `:2984-3002`), so a pure ladder reads ahead of need (I2's stop). The stability test (`:2939-2945`) is two lines |
| VOI's context | `VoiContext` `diagnosis/voi_stopping.py:389-479` | **Not in K9.** I2 found the scheduler needs it frozen too; it is L4's |
| The causal prior's weighting | `build_causal_hypothesis_set` `diagnosis/causal_probe_coherence.py:747-801` | **No**, unless G4 needs it: 55 lines, and G4's recommendation reuses commissioning's set instead of recomputing a prior |
| The admission of a discriminating observation | the ladder `diagnosis/causal_orchestrator.py:2788-2796` | **No**: its arithmetic is already pure; the ladder is three reads deep and G4 changes what it decides |
| The repair choice | `select_minimal_repair` | **Already pure** |

**2. The shell, named.** Episodes and their segments, presentations (commit, serve, invalidate), the attempt step's evidence recording, the block end, the post-attempt hooks, the diagnose, embed, gaps and follow-up jobs (`learnloop_sidecar/post_attempt_worker.py`), the receipts and records, model calls (diagnoser, judges, authoring), the sidecar's remediation and practice handlers. A step may move a decision out of the shell. It never moves the shell into a core.

**3. Move, don't unify, unless the copies drift** (§1). A module boundary is drawn by who calls a group of names and by the direction of references between sections (§4.3, §4.4), not by a new abstraction. No registry, no policy object, no injection (strategy §4).

**4. What one diagnostic decision's trace must answer**, from stored rows, after G1, K9.12 and arc B as built:
- the miss and its grade, and whether the grade was held (B7 has this);
- the diagnosis and its arm (B7);
- whether the causal lane offered the check, and if not, the rule code: common repair, one repair class, pending machine checks, the learner's "Not now", recent burden, the session budget, no instrument, an episode conflict, a value below cost (G1's record);
- on FG1's lane, the router's decision and its refusals (B6, B7);
- which candidate and locked set were pinned (the `probe_offer` record and the presentation);
- for the answer: classified or declined, with the decline's code (K9.12), and admitted or not (the observation row);
- the factor's resolution and by which writer (the factor row);
- the episode's stop and its rule (the episode row; K9.12 adds the rules that didn't fire to the detail it already writes);
- a hook that failed, by name (K9.12).

It keeps ids and codes only, never prompts or learner text (strategy §4).

**5. The guarantees no step may touch** (strategy §2.10, and the owner's decisions behind them):
- prediction bundles written before the answer, content-addressed (`diagnosis/causal_probe_coherence.py:989-1000`; migration 121's `generated_without_observation`);
- the pin of ids on the presentation (`diagnosis/causal_orchestrator.py:2186`, `:2223-2249`);
- the hypothesis set locked before the answer, and never shrunk after (the learner's narrowing reweights, never removes: `docs/specs/spec_learner_input_after_miss_v1.md:13`, `:226`);
- the posterior at selection written on `probe_presentations` (`diagnosis/probe_episodes.py:1285`);
- the discriminating observations as inputs to `scoreboard`, `failure_triage` (until Q3), `causal_health`, `evsi_calibration/live_report`, `causal_factor_deferral`, `router_objective/picks`, `ops/capture_report`, `hypothesis_marks`;
- old rows readable by shape (the robust channel's NULL hash keeps the point path after D6);
- the grader blind (no learner-derived field in its context), the diagnoser never writing evidence, replay never calling a model (`docs/specs/spec_blind_grading_diagnosis_split_v1.md:114`, `:121`, `:126`);
- causes hidden before the probe is answered, and a probe whose causes were shown recorded as not independent (`docs/specs/spec_followup_generate_serve_v1.md:259`).

A step that would need to change one stops and goes to the owner.

**6. Comments.** Moved code keeps its comments byte for byte, so P-ast stays the move's proof. The new modules get docstrings that describe them; the false sentences (K9-4) are corrected in the module docstrings the moves write. Functions a step rewrites get the convention (strategy §2.1): reasons kept, round names dropped, an approach header over 100 lines. There is no separate sweep.

## 4. The steps

**Every step** follows §2.1 of `docs/specs/refactor_strategy_v3.md` and the rules block: one implementer in a worktree; targeted tests under the memory cap; `lint-imports`; `ruff check`; the vault validators; `tests/test_identity_pins.py` and `tests/test_structure_ratchets.py`; the phase's adversarial review (§2.19).

**Named proofs**, beyond §4 of the strategy:
- **P-fail:** a test that fails before the change.
- **P-golden:** K9.5's goldens (rows of every diagnosis table and `decision_records`, for fixed fake model outputs and pinned draws) identical before and after.
- **P-pins:** K0's identity pins with K9.5's diagnosis pins, unchanged.
- **P-ast:** every moved function's AST, docstrings removed, identical to its source (A3's and K2.5's method).
- **P-draw**, **P-shadow**, **P-playbook:** the strategy's.

Only K9.4 (with Q1), K9.17 (with Q2) and G4 change persisted meaning; the rest are bug fixes without a successor or structure.

### 4.1 Behaviour track: the ledger faults (fix first)

Each lands alone, from a failing test, before or beside anything else.

**K9.1. A mid-check stop settles the block's answers** (S). Behaviour, no successor. TH-3; due at arc D's close.
- **Problem:** `stop_diagnosing_and_teach` (`diagnosis/probe_episodes.py:3447-3494`) invalidates the presentation, writes the transition and sets `converted_to_tutoring`. `end_diagnostic_block` then returns early for a non-`in_progress` episode (`diagnosis/probe_blocks.py:332-333`), and nothing calls it anyway. The attempt pipeline had skipped each in-block answer's normalization, workflow and diagnosis job because the block end would run them (`attempts/post_attempt.py:155-188`, `_defers_to_block_end` `:312-322`).
- **Does:**
  - The block end's steps 1, 2 and 2b (release withheld feedback, normalize joint-graded answers or enqueue a blind answer's diagnosis, resume the deferred causal hooks: `diagnosis/probe_blocks.py:337-401`) become one function, `settle_block_answers(vault, repository, episode, *, ai_client, clock)`, which `end_diagnostic_block` calls where those lines were.
  - `stop_diagnosing_and_teach` calls it before it changes the episode's status. It passes `ai_client=None`, as the attempt step's block end does today (`attempts/attempts.py:3481-3483`).
  - The stop returns the released feedback ids with its decision, so the sidecar's `stop_probe_diagnosing` (`learnloop_sidecar/handlers/practice.py:668`) can show them. How the screen shows them is the UX audit's.
- **Must not touch:** the stop's route (no tutoring route; the lesson hand-off stays as `docs/reviews/teach-handoff-routing.md` built it), the calibration dialogue's stop (it already ends its block), the claim check and routing of `end_diagnostic_block` (`:406-465`).
- **Check in step 0:** that normalization with `ai_client=None` makes no model call on this path (the map's D9D4 left it untraced), and that `settle_block_answers` is idempotent per answer, as the block end's normalization is "per error event" (`:357`).
- **Files:** `diagnosis/probe_blocks.py`, `diagnosis/probe_episodes.py` (the stop), `learnloop_sidecar/handlers/practice.py` (the returned ids), a new test file.
- **Deletes:** nothing. **Abstraction:** none (one function from existing lines).
- **Proof:** P-fail `tests/test_teach_handoff_stop_settles.py::test_a_mid_check_stop_normalizes_joint_answers_and_releases_their_feedback` (a joint vault: two in-block misses, stop; the misconception rows exist and the feedback is released) and `::test_a_mid_check_stop_queues_the_blind_answers_diagnosis` (a blind vault: one `diagnose` job per answer). The existing block-end and teach hand-off tests unchanged. **Vault:** the Diagnosis note's line "the block is not ended" (`Concepts/Diagnosis and Remediation.md:66`). **Size:** S.

**K9.2. The screen says why the check was withheld** (S). Behaviour (desktop). K9-1; D9B5.
- **Problem:** the status's `reason` is the verb (`defer_learner_preference`, `defer_recent_burden`, `defer_session_budget`; `diagnosis/causal_orchestrator.py:1875-1903`) and the DTO carries it (`apps/learnloop-tauri/src/api/dto.ts:1996-2002`), but the component branches on `!probeOffered` alone (`CausalAttribution.tsx:403-407`).
- **Does:** the "You asked me not to check" line shows only for `reason === "defer_learner_preference"`. For the other two the component shows the server's `message` (`DEFERRED_OFFER_MESSAGE`, `diagnosis/causal_orchestrator.py:235-238`, which already says nothing about the learner). The DTO comment at `dto.ts:2008-2009` is corrected. Final wording is the UX audit's.
- **Proof:** P-fail (vitest, a new `CausalAttribution.test.tsx`): a status with `reason: "defer_recent_burden"` doesn't render "You asked me". **Size:** S.

**K9.3. The primed-sibling ranking takes a clock** (S). Behaviour (tests and replay only). K9-2.
- **Problem:** `_pick_primed_sibling` reads `SystemClock().now()` (`learnloop_sidecar/handlers/feedback.py:1107`) where the ranking it re-implements takes one (`diagnosis/remediation.py:437`). The sidecar injects no clock today (no handler reads one), so production behaviour is the same; a frozen-clock test is not.
- **Does:** a `clock` parameter through `_pick_primed_sibling`'s three callers (`:962`, `:971`, `:1004`), defaulting to the wall clock. Whether the copy should call `remediation._rank_items` instead (it differs: a boolean facet overlap and the source item excluded) is a policy question for K8's handler review, recorded there, not changed here.
- **Proof:** P-fail: a frozen clock inside the recent-attempt window ranks an item answered "minutes ago" last. **Size:** S.

**K9.4. An untaken repair episode ends** (S). Behaviour. R1-2; **only after Q1**.
- **Does (recommended answer):** the existing sweep seam (`sweep_expired_cold_retries`, reached from `sweep_machine_checks`, `diagnosis/causal_orchestrator.py:666`) also ends a remediation episode in `prescribed` or `treatment` whose primed attempt was never taken once the item's next ordinary review is due, writing `abandoned` (already in the CHECK, `migrations/058_remediation_episodes.sql:6`), which frees its reserved cold item as `withdraw_cold_measurement` does (`diagnosis/remediation.py:1438`). `routine_serving_exclusions` (`scheduling/serving_exclusions.py:114-160`) then reads the wider set, as the ledger row asks.
- **Proof:** P-fail per arm; the serving-exclusion tests. Lands alone. **Size:** S.

### 4.2 Characterize first

**K9.5. Pin diagnosis's identities and golden its journeys** (M). Structure (tests only).
- **Problem:** §0 row 13. A move that edits a content id's input (a key order, a dumped object's shape under `default=str`) writes new ids for the same facts; an idempotent insert then stops matching rows already written.
- **Does:**
  - **Identity pins** (`tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`), each through its production path at fixed inputs: the content ids `cdo` (`diagnosis/causal_orchestrator.py:2655`, `:2816`), `bpb` and `bpi` (`diagnosis/causal_probe_coherence.py:989-1000`), `cpc` (`:1562`), `cco` (`:1812`), `ccv` (`:1962`), `pma` (`:1478`), `rv`, `rc`, `dr` and the mechanism id (`diagnosis/causal_attribution.py:285`, `:688`, `:2687`, `:1105`); `missing_vocabulary`'s `mvn` (`:111`); the prior-analysis draw (`diagnosis/split/prior_analysis.py:93`); the text-gap judges' checkpoint keys (`diagnosis/text_gaps/judges.py:241`, `:414`); the recurrence verdicts' reuse key (`diagnosis/recurrence/guard.py:10-20`); the diagnosis prompt version with its suffixes (`diagnosis/split/jobs.py:853-867`). Shape pins for any type dumped whole into one of them.
  - **A journey golden** (`tests/fixtures/diagnosis_journey_golden.json`, written with a `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1` switch as the figure prompts golden): for each case, the rows written to every diagnosis table and to `decision_records`, with ids, times and the trace replaced by stable tokens. Cases on fixed fake model outputs (`tests/structured_ai.py`) and pinned draws: the causal lane through each of the five statuses; accept, a matched answer, resolution, repair and a cold check that passes and one that fails; FG1's lane through ask now and wait; a block to a value stop and to its budget; a mid-check stop (after K9.1); a held grade on a probe answer, released; a regrade of a probe answer; a text gap that creates a prerequisite; a recurrence group by the judge.
  - **Coverage first**, as K2.5's step 2: a `sys.monitoring` run over the functions K9.6-K9.11 move, listing the lines no case reaches. Each gets a case or a line in the record saying why not.
- **Ports first (T4).** Seven test sites patch names in the two modules: `tests/test_ux_phase4_feedback.py:2747` (`refuse_routine_display_covered`), `:2785` (`_answer_shown`), `tests/test_voi_v2.py:448` (`_robust_completion_override`), `:530` (`_robust_gate_verdict`), `tests/test_daily_loop_lo_lifecycle_serving.py:127` (`enter_episode`), `tests/test_causal_shadow_selection.py:338`, and the string target at `tests/test_attempt_chain_records.py:230`. Each is ported to call the code with plain values or to a fake through a public argument, not pointed at a new location.
- **Files:** the two pin files, a new `tests/test_diagnosis_journey_golden.py` and its fixture, the ported tests.
- **Proof:** the pins and golden pass at the tip; each pin fails on a scratch edit (swap two keys of `cdo`'s identity). Keep the golden under G8's 5 MB (I1's was 2.3 MB). **Size:** M.

### 4.3 Structure track: `causal_orchestrator.py`, split by who calls it

Its public names fall into these groups (callers from `names_k9.py` at this tip; sizes are the sections' top-level definitions, from `intra.py`):

| Group | Names | Lines | Callers outside the module | Goes to |
|---|---|---:|---|---|
| Factor and receipt reads, EVSI inputs | `diagnosis_receipt`, `open_factors_for_hypothesis`, `DiscriminationInputs`, `_discrimination_inputs`, `_probe_burden_minutes`, `_avoided_overteaching_minutes`, `_recent_diagnostic_burden`, `_case_repair_class_id`, `_receipt_repair_class_id` and the rest of `:853-1182`; `CausalRepairError`; `_content_id`; the shared constants (`CAUSAL_ORCHESTRATOR_FORMULA_VERSION` and the machine-check kinds) | about 370 | none directly; every other group | `diagnosis/causal_reads.py` (K9.6) |
| Hard stops | `LEARNER_PREFERENCES`, `record_learner_preference`, `learner_preference`, `episode_conflict_reason`, `_probe_episode_conflict`, `causal_origin`, `causal_origin_factor`, `EPISODE_CONFLICT_*` | about 130 | `followup_run/router.py:98` (four names), `followup_run/serving.py:231`, `followup_run/jobs.py:257` | `diagnosis/probe_hard_stops.py` (K9.6) |
| Machine checks | `backfill_obligation`, `instrument_commissioning_obligation`, `enqueue_backfill_obligation`, `sweep_machine_checks`, `close_satisfied_backfills`, `resolve_machine_check`, `pending_machine_checks_for_factor`, `MACHINE_CHECK_*` | about 306 (`:469-795`) | `diagnosis/followups.py:838`, `:986`; `cli/app.py:4892`; `followup_run/router.py:98` | `diagnosis/machine_checks.py` (K9.7) |
| Cold verification | `cold_verification_context`, `record_cold_verification_from_task`, `sweep_expired_cold_retries` | about 402 (`:3012-3420`) | `diagnosis/remediation.py:964`, `diagnosis/followups.py:838`; and the machine-check sweep (`:666`) | `diagnosis/causal_cold_verification.py` (K9.7) |
| The discriminating observation | `pinned_causal_probe`, `classify_probe_response`, `DiscriminatingObservation`, `record_learner_embedded_prediction`, `record_probe_classification`, `deterministic_probe_features`, `auto_classify_pinned_probe` | about 600 (`:2376-3011`) | `diagnosis/followups.py:838`, `tutor/tutor_qa.py:685` | `diagnosis/causal_discrimination.py` (K9.8) |
| Learner actions | `ProbeOffer`, `accept_probe_offer`, `_accept_probe_offer`, `defer_probe_offer`, `request_teaching_now` | about 370 (`:1933-2375` less the hard stops) | `learnloop_sidecar/handlers/remediation.py:6`; `followup_run/admission.py:394` | `diagnosis/probe_offer.py` (K9.8) |
| The decision | the parameters and resolver, `RepairStatus`, `RepairAction`, `causal_repair_status`, `_status_for_factor`, the messages | about 1,020 (`:1-465`, `:1183-1932`) | `learnloop_sidecar/handlers/remediation.py:6`, `diagnosis/remediation.py:148`, `diagnosis/followups.py:1048` | stays `causal_orchestrator.py` |

**The order that keeps every landing green** follows the references between sections (`intra.py`), leaves first: the reads and the hard stops reference nothing above them; cold verification references the reads; the machine checks reference cold verification (their sweep runs the cold sweep, `:666`); the discriminating observation references the reads; the decision references the reads, the hard stops and the machine checks; the learner actions reference the decision (`request_teaching_now` reads `causal_repair_status`). Each moved module imports only what is below it, at top level. `causal_orchestrator.py` keeps no re-export: a name lives in one module, and each step updates every caller in `src` and `tests`.

**K9.6. The reads and the hard stops out; one `_content_id`** (M). Structure. D9P1, D9B1 (#3), K9-4 in part.
- **Does:**
  - `diagnosis/causal_reads.py` takes the reads group, `CausalRepairError` and the shared constants.
  - `_content_id` lives there once; the byte-identical copies in `causal_attribution.py:225` and `causal_probe_coherence.py:189` go. K9.5's pins prove the ids unchanged.
  - `diagnosis/probe_hard_stops.py` takes the hard-stops group, with `_probe_episode_conflict` made public as `probe_episode_conflict`.
  - `followup_run/router.py`'s `hard_refusal` calls `probe_episode_conflict` instead of its four-line copy (`:115-119`). It keeps its own order (preference, then machine checks, then the conflict), because the order decides which reason a router decision records; G1 owns that order. The module docstring states the four hard stops and the two orders.
  - The module docstring of `causal_orchestrator.py` loses "the ONLY channel through which diagnosis support may move" (`:15-16`) and says what is true: the discriminating observation and the learner's self-report (`diagnosis/causal_attribution.py:3738`) resolve a factor, and the episode posterior moves on its own (K9-4, first sentence).
- **Deletes:** two `_content_id` copies (10 lines), `hard_refusal`'s copy (about 5).
- **Must not touch:** any id's bytes (P-pins); `decide_probe`'s ladder order (`diagnosis/causal_probe_coherence.py:469-480`).
- **Files:** `diagnosis/{causal_orchestrator,causal_reads,probe_hard_stops,causal_attribution,causal_probe_coherence}.py`, `followup_run/{router,serving,jobs}.py`, the tests importing moved names.
- **Proof:** P-ast, P-golden, P-pins. **Lines:** about +60 net (two docstrings and imports; an estimate). **Size:** M.

**K9.7. Machine checks and the cold check out** (M). Structure. D9P1.
- **Does:** `diagnosis/causal_cold_verification.py` and `diagnosis/machine_checks.py` take their groups. `diagnosis/remediation.py`'s function-local import of `cold_verification_context` (`:964`) and `followups`' of the two sweeps (`:838`, `:986`) point at the new modules.
- **Proof:** P-ast, P-golden. **Lines:** about +50 net (estimate). **Size:** M.

**K9.8. The discriminating observation and the learner actions out** (M). Structure. D9P1, K9-4.
- **Does:**
  - `diagnosis/causal_discrimination.py` takes the classification and the observation (the second belief channel G3 and G4 read). Its docstring states the admission ladder and says that `validator_owned` support is recorded for its readers; the sentence naming `failure_triage`'s promotion arm (`:2736-2738`) goes, since nothing calls that arm.
  - `diagnosis/probe_offer.py` takes the learner actions, importing the decision from `causal_orchestrator` at top level, which today imports nothing back.
  - `causal_orchestrator.py` is then the decision only (about 1,020 lines), and `_status_for_factor` gets the approach header its module docstring's table now stands in for (`:20-38`).
- **Order:** `_accept_probe_offer` imports `commit_presentation` and `RoutineDisplayCovered` from `probe_episodes` (`:2165-2169`), which K9.10 moves. Land K9.8 and K9.10 in either order; the later one updates that import.
- **Proof:** P-ast, P-golden, P-pins. **Lines:** about +60 net (estimate). **Vault:** the generated module notes. **Size:** M.

`decide_probe`'s "every threshold is resolved from the fitted store" (`diagnosis/causal_probe_coherence.py:432-433`), K9-4's third sentence, is corrected in K9.6 if that module is touched there (it is, for `_content_id`): it says the resolver reads a fitted scope that nothing writes today (`cli/fit.py:36`, `:130`), so the defaults serve.

### 4.4 Structure track: `probe_episodes.py`, split by who calls it

| Group | Names (selection) | Lines | Callers outside | Goes to |
|---|---|---:|---|---|
| Lifecycle, instruments, the posterior | `enter_episode` (5 `src` callers, 48 test files), `retarget_episode_to_causal_factor`, the re-probe triggers, `episode_hypothesis_set` (8 callers), `administered_surface_exclusions`, `eligible_instruments` (9), `resolve_instrument`, `episode_posterior` (10), `_bayes_update` | about 1,250 (`:1-1162`, `:1866-2096`) | scheduler, valuation, passage cues, curriculum, sim, substrate, the sidecar, six diagnosis modules | stays `probe_episodes.py` |
| The completion policy | `_evaluate_completion` (made public), `persist_episode_beliefs`, `_set_target_decision` (made public), `close_diagnostic_segment`, `episode_maximum_binds`, `robust_gate_counterfactual`, the value and robust gates | about 590 (`:2899-3443` plus three functions) | `diagnosis/probe_blocks.py:29`, `scheduling/scheduler.py:26`, `curriculum/golden_path_run.py:331` | `diagnosis/probe_completion.py` (K9.9) |
| Presentations and serve gates | `commit_presentation`, `serve_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`, `commit_item_presentation`, `validate_presentation_for_submission`, `RoutineDisplayCovered`, `presentation_commit_payload`, `record_presentation_forecast` | about 510 after the deletion below (`:1163-1865`) | the sidecar's practice handler, the TUI, the scheduler, `attempts/attempts.py:3635`, `probe_dialogue`, sim | `diagnosis/probe_presentations.py` (K9.10) |
| Evidence recording | `record_episode_evidence`, `record_presentation_activity_classification`, the dual writes, `_record_presentation_observation` | about 740 (`:2097-2898` less `persist_episode_beliefs`) | `attempts/attempts.py:3045`, `:3073`, `:3365`, `:3481` | `diagnosis/probe_evidence.py` (K9.11) |
| Learner controls and the client contract | `stop_diagnosing_and_teach`, `episode_contract`, `next_probe_item` | about 130 (`:3444-3651` less the moved three) | the sidecar's practice handler, the TUI | `diagnosis/probe_controls.py` (K9.11) |

**The order** follows the references (`intra.py`): the core's three sections reference each other both ways, so they stay together. The completion policy references only the core. Presentations reference the core and the completion policy (`robust_gate_counterfactual`). Evidence references the core, presentations and the completion policy, and calls the block end; `probe_blocks` references the core and the completion policy. The controls reference the core and `probe_blocks`' helpers. So: core < completion < presentations < `probe_blocks` < evidence and controls. Evidence's call into `probe_blocks` (today function-local, `diagnosis/probe_episodes.py:2173`) and the controls' (`:3465-3470`) become top-level downward imports, and `probe_blocks` imports public names only.

**K9.9. The completion policy out** (M). Structure. D9P2.
- **Does:** `diagnosis/probe_completion.py` takes the group. `_evaluate_completion` and `_set_target_decision` lose their underscore, since `probe_blocks` calls them; `probe_blocks`' import (`:29-36`) names public functions. Each of the seven rules gets a one-line comment naming its code (`completion_reason`), so the rule list reads from the function.
- **Order:** after D6 (which edits `:157-225` and `:2335-2360`). If D7 has not run, the value gate's off-path (`voi_probe_site_active`, `:3055-3058`) moves as is.
- **Proof:** P-ast (apart from the two renames), P-golden. **Lines:** about +40 net (estimate). **Size:** M.

**K9.10. Presentations out; the dead precommitted block goes** (M). Structure. D9P2.
- **Does:** `diagnosis/probe_presentations.py` takes the group. `plan_precommitted_block` (151 lines, `:1664-1814`) is deleted after step 0's deletion proof (strategy §2.1: no import, function-local or `importlib`; no string dispatch; no frontend, replay or upgrade path); its two test files' cases are deleted or, where they test a shared helper, ported. Callers in the sidecar's practice handler and the TUI (`learnloop_sidecar/handlers/practice.py:41`, `tui/screens/practice.py:26`) import from the new module.
- **Deletes:** about 150 lines.
- **Proof:** P-ast, P-golden; the deletion proof in the record. **Lines:** about −110 net (estimate). **Size:** M.

**K9.11. Evidence and controls out; the `probe_episodes` ↔ `probe_blocks` cycle cut** (M). Structure. D9P2, D9P3.
- **Does:** `diagnosis/probe_evidence.py` and `diagnosis/probe_controls.py` take their groups. `abandon_episode` (19 lines, `:3549-3567`, one test file, no caller) goes after the same deletion proof. The attempt step's four function-local imports (`attempts/attempts.py:3045`, `:3073`, `:3365`, `:3481`) name `probe_evidence`. `probe_blocks`' private `_first_error_from_block` is made public for the controls.
- **Deletes:** about 20 lines; the `probe_episodes` → `probe_blocks` edge, one of the audit's seven cutting edges (strategy §2.18 L1).
- **Proof:** P-ast, P-golden; M0's ratchet for modules in a cycle lowered if it falls. **Lines:** about +50 net (estimate). **Vault:** the generated module notes. **Size:** M.

**What the two splits buy, by simulation.** `simsplit.py` re-runs the import graph with each module replaced by its parts, edges into a part assigned by the names the importer uses and edges out by the names each part uses. Without a split it reproduces today's numbers (largest component 188, diagnosis 65; diagnosis-internal components 21, 7, 2, 2). With both splits:
- the diagnosis-internal 21-module component becomes **11** (`followups`, `split.jobs`, five `recurrence` and four `text_gaps` modules), plus a 3 (`causal_orchestrator`, `remediation`, `guided_redo`) and a 2 (`probe_episodes`, `probe_instance_generation`);
- the largest component of the whole graph does **not** shrink: it holds 195 nodes, because the new parts of a module already inside it are counted separately. Cutting that component is L1's, by its seven edges.

It is an estimate: the moves will turn some function-local imports into top-level ones, and step 0 of each re-measures with M0's script.

### 4.5 Structure track: why x and not y

These follow arc B's rules: ADR-017's one record type, ids and codes only, written through `write_decision` and never allowed to change a decision.

**K9.12. Why a probe answer wasn't read, and which hook failed** (M). Structure (records). D9O2, D9D5, D9O5 in part.
- **Does:**
  - `auto_classify_pinned_probe`'s six declines (`diagnosis/causal_orchestrator.py:2967-3001`, in `causal_discrimination.py` after K9.8) each write one `probe_classification` record with a code (already observed, no pinned probe, no assessed criterion, held, no feature, not separable: the step 0 names each from the code), subject the presentation, parent the attempt's trace. Today the docstring makes the silence deliberate (`:2952-2953`); the record replaces a log line, not a decision.
  - The four grade-keyed hooks (`diagnosis/followups.py:853-906`) write `diagnosis_step` records on failure, as the post-diagnosis hooks already do (`:994-1003`), with the hook's name.
  - An episode's stop writes, in the `completion_detail_json` it already writes (`diagnosis/probe_episodes.py:3347-3372`), the codes of the rules it evaluated and passed before the one that fired. No row is written for "continue": a record per answer is the noise strategy §4 rules out.
- **Must not change:** which answers are classified, which factors resolve, the stop chosen.
- **Proof:** P-fail per decline code (`tests/test_why_cases.py` gains "why wasn't this probe answer read?"); P-golden otherwise identical apart from the new rows, listed. **Vault:** `Workflows/Debug a decision.md`, `Workflows/Inspect Persistent State.md:186` (the fifth `diagnosis_step`, `causal_shadow_selection`, which it omits). **Size:** M.

### 4.6 Inside arc G: what K9 hands G1, G3 and G4

These are not K9 landings; they are inputs to arc G's steps, written here because K9 read the code they change.

**G1, the probe facts.** After K9.6-K9.8, G1 edits `causal_orchestrator.py` (about 1,020 lines), not 3,471. Its shape, by the reads:
- `_status_for_factor` has two early arms that write before any verdict (legacy facet basis, `:1575`; incomplete mapping, `:1592-1618`, which enqueues a backfill), then `close_satisfied_backfills` (`:1620`). After that its reads are unconditional: the repair-class need (`:1622`), the diagnosis receipt (`:1624`), pending checks (`:1638`), the episode conflict (`:1652`), the candidates (`:1659`), the chosen candidate's locked set (`:1686`, depending only on the candidate rows), burden, avoided minutes, the preference and recent burden (`:1713-1731`).
- So `probe_facts` is I1-shaped, not I2-shaped: the shell runs the early arms and the reads in today's order (with the candidate pick, a pure helper over the rows, between the candidates and the locked-set read), and a pure function returns the facts, the hard stops and the verdict.
- **The verdict's record (D9O1) belongs here**, under L6: `probe_facts` returns its `DecisionRecord` (`probe_verdict`, with the rule code from §3's trace list), and `finish` (`:1452-1562`) writes it beside the receipt. Until G1 lands, a withheld offer stays reachable only through its factor.
- **The resolvers (D9B3, D9B4):** G1 merges `resolve_causal_probe_parameters` and `resolve_orchestrator_parameters` only if they still differ in data alone; G2 deletes the verdict's margins and `recent_diagnostic_limit` with the verdict. The cold-check resolver in `goals/certification_cold_probe.py:248-282` is G1's to merge or leave.

**G3, the disagreement report.** It can also count, on the copies, how many probe answers were held and later released, and how many were regraded: the size of Q2's fix.

**G4, one belief.** K9.13 (below) makes the posterior a gather and a pure fold before G4 changes what it gathers. If Q2 is "fold into G4", G4's gather reads the latest grading epoch per attempt and the released holds, and its tests state the posterior with literals.

**K9.13. The episode posterior as a gather and a pure fold** (M). Structure. D9F1. **Only if G3 says G4 runs, or Q2 chooses K9.17;** with L4's review of the episode posterior.
- **Does:** `episode_posterior` (`diagnosis/probe_episodes.py:1869-1981`) becomes a shell that gathers `EpisodeEvidence` (the locked set and prior; per observation and incidental attempt, its likelihoods and weight, in replay order; the held set) with today's reads in today's order, and a pure `fold_posterior(evidence) -> EpisodePosterior` over `_bayes_update`.
- **Check in step 0 (I2's stop):** that no read depends on a value the fold computes. By reading, the gather depends on rows and the held predicate only (`:1896-1910`, `:1943-1945`, `:1985`). If one does, the step stops and says which.
- **Abstraction and why it pays:** `EpisodeEvidence`, one frozen dataclass. It lets G4's and K9.17's tests say "this released hold moves the posterior by this much" with literals. **Stop rule:** more than about eight fields, or more than about 80 net lines with no new literal test, and it stops.
- **Proof:** P-golden; P-shadow (the posterior is persisted through `persist_episode_beliefs`); new literal tests of the fold. **Size:** M.

**K9.17. A released hold or a regrade enters the episode posterior** (M). Behaviour, lands alone, P-playbook. **Only if Q2 chooses its own successor.** K9-3.
- **Does:** on a hold's release or a regrade of a probe answer, the observation is re-derived from the current grading epoch as a superseding row (the old one kept); replay reads the latest per attempt. A successor tag and kill switch serve the predecessor exactly.
- **Proof:** P-fail `tests/test_probe_held_release.py::test_a_released_hold_moves_the_episode_posterior` and `::test_a_regrade_of_a_probe_answer_moves_the_episode_posterior` (strict xfails until then, as the fail-first tests of a queued fix); P-playbook. **Size:** M.

### 4.7 Docs

**K9.14. The Diagnosis note true at this tip** (S). D9V1, D9V2.
- **Does:** `Concepts/Diagnosis and Remediation.md` loses the states that don't exist (`concentrated`, `burden_stop`, `:28-37`) and gains: who decides whether to probe today (the map's ten sites, in one table, with arc G's plan beside it), the two beliefs over hypotheses and where they differ (the map's §3.3 table), the module layout after K9.6-K9.11, and what `why` answers (§3's list). `implementation_version` is updated. It links ADR-016, ADR-017 and the ADR-020 that G2 will add.
- **When:** after K9.11, so the paths are right. The full rewrite stays with the vault plan's last stage (strategy §5), after G2 and G4 change what the note describes.
- **Proof:** the four validators; the orchestrator reads the note against the code. **Size:** S.

### 4.8 Conditional on the owner

**K9.15. Delete `failure_triage`** (S). **Only if Q3 is yes.** D9C2, D9P5.
- **Step 0:** strategy §2.1's deletion proof again, at that tip.
- **Does:** removes `diagnosis/failure_triage.py` (1,054 lines), its `MODULE_INVENTORY` entry and three `_reg_const` entries (`params/parameter_registry.py:127`, `:1130-1136`) in the same commit, and the two `Repository` methods only it uses (`append_failure_triage_event`, `failure_triage_event`). The live route methods stay (`failure_triage_routes`, `failure_triage_route_for_reason`: read by `diagnosis/voi_stopping.py:476` and three others), and so does `failure_triage_events_for`, which `diagnosis/causal_health.py:327` reads. The table stays, readable.
- **Proof:** `tests/test_registry_audit.py`, `tests/test_architecture.py`'s resolution check, the five test files that import it deleted or ported. **Size:** S.

**K9.16. Retire the EVSI-2 shadow selection** (M). **Only if Q4 is yes;** with or after G2.
- **Does:** removes `record_shadow_selection` (360 lines, `diagnosis/causal_diagnostic_selector.py:312`) and its call in `finish` (`diagnosis/causal_orchestrator.py:1491-1515`), the readiness report (`diagnosis/causal_selection_audit.py`, 228 lines; `cli/app.py:4436`; `learnloop_sidecar/handlers/measurement.py:8`) and its panel. `build_causal_loss_table` and `likelihood_regime_for_candidate` stay where `instructional/valuation.py:251`, `:727` read them (they move into `causal_discrimination.py` or a small module, by step 0's read). `causal_shadow_selection_receipts` stays readable.
- **Proof:** P-golden less the shadow rows; P-draw (the shadow is never read by a decision, `:1491-1494`). **Size:** M.

### 4.9 The parameter registry

**What a new constant costs today.** `tests/test_registry_audit.py:92-94` asserts that every upper-case numeric module constant of a `MODULE_INVENTORY` module (`params/parameter_registry.py:3018-3036`) has a `REGISTRY` entry. Nine of the 109 diagnosis modules are in the inventory (`voi_stopping`, `robust_composition`, `contrast_pairs`, `probe_families`, `discrimination_profiles`, `failure_triage`, `error_hunt`, `diagnostic_pack`, `probe_episodes`), with 39 entries. So a numeric constant in those nine costs one `_reg_const` call (two or three lines) in a 3,565-line file of another package, with a class, kind, owner and rationale; in the other 100 it costs nothing, and isn't registered (the 0.40 sensor cut, `diagnosis/causal_orchestrator.py:2935`). All 380 entries default to `heuristic`, none is read back by the code that uses it, and two `record_bind` sites exist, both in scheduling (`scheduling/constraint_engine.py:358`, `scheduling/randomization_layer.py:176`). 27 of the 211 non-merge commits that touched diagnosis since Oct 12 also touched the registry.

**A hazard the moves must respect.** A constant moved from an inventory module into a new module that isn't in the inventory is silently unregistered: the test scans only the inventory. Each move step's rule: a registered constant that moves takes its registry path along in the same commit, and a module carved from an inventory module joins the inventory. In K9's plan only `probe_episodes.FALLBACK_FAMILY_VERSION` (`params/parameter_registry.py:908`) is registered in a module that splits, and it stays in the core.

**What would make it one place.** A declaration beside the constant that the registry collects through the import it already makes (`importlib.import_module`, `:3099`), instead of a line in the registry file. Estimate for diagnosis alone: about 120 lines leave the registry and about 120 arrive in nine modules: level. Its benefit is change locality for a cost that is two or three lines per constant today. Done for diagnosis only, it would leave two ways to register. So K9 plans no step, and Q5 asks whether you want one cross-package step for all 380, which is not K9's.

## 5. Order, dependencies and lanes

```
K9.1 (TH-3, due at arc D's close) ─┐
K9.2 (K9-1) ───────────────────────┼─ now, each alone (behaviour)
K9.3 (K9-2) ───────────────────────┘
K9.4 ─ after Q1, alone
K9.5 (goldens, pins; tests only) ─ beside arc D

after D6 (and best after D7):
K9.5 ─→ K9.6 ─→ K9.7 ─→ K9.8 ─┐
K9.5 ─→ K9.9 ─→ K9.10 ─→ K9.11 ┴─→ K9.12 ─→ K9.14 (note)
K9.8 ─→ G1 (with the verdict's record) ─→ G2 ─→ K9.16 (if Q4)
G3 ─→ K9.13 (if G4 runs, or Q2 chooses K9.17) ─→ G4 or K9.17
K9.15 (if Q3) ─ any time after K9.5, alone
```

**Dependencies on other arcs:**
- **Arc B:** K9.12 uses ADR-017's record and `why` as B1 built them. The verdict's record lands with G1 under L6, since `probe_facts` is the core that returns it.
- **Arc D:** K9.1 is due at arc D's close (ledger). The moves start after D6 (it edits `probe_episodes.py`, `voi_stopping.py`, `remediation.py`). D7 removes the kill switches' off-paths that the moves would otherwise carry (§0).
- **Arc G:** K9.6-K9.8 before G1 (G1's file becomes the decision only). K9.9-K9.11 before G4. K9.13 between G3 and G4. K9.16 with or after G2. G6 (protection) is untouched: diagnosis's protection reads (held grades, routine display, reserved items) move as they are.
- **K8 (the sidecar handlers):** receives K9.3's copy question (`_pick_primed_sibling` against `remediation._rank_items`) and the practice handler's episode parking (`learnloop_sidecar/handlers/practice.py:573-581`), a lifecycle transition in a handler (map §3.4). K9 moves nothing out of handlers: the phone and TUI already call the same diagnosis functions through the sidecar registry, and no second consumer of these two decisions is named.
- **L1:** the remaining 11-module diagnosis cycle and the global component's edges are L1's. K9.11 removes one of its seven edges (`probe_episodes` → `probe_blocks`); K9.6-K9.8 make the `causal_orchestrator` → `probe_episodes` reads downward.
- **L4 and L5:** K9.13 is L4's episode-posterior item, done here when G4 needs it. L5 covers the 19 functions over 200 lines that no step rewrites; K9.8 gives `_status_for_factor` its header.
- **The UX overhaul:** K9.1's released feedback and K9.2's line need wording from it (§7).

**What can run beside what.** K9.1-K9.3 beside anything; they fill lane 3's "ledger fixes" slot. K9.5 beside arc D: it is test-only. The two split chains (K9.6-K9.8 on `causal_orchestrator.py`, K9.9-K9.11 on `probe_episodes.py`) can run in two lanes after D6; K9.8 and K9.10 share one import and land in sequence. They share no file with K2.6-K2.12 or G6. K9.12 after both chains. Each step lands alone or in a batch of up to four.

**Size per step** (estimates; S about half a day of queue, M about one day, as K2's and K10's):

| Step | Track | Size |
|---|---|---|
| K9.1 A mid-check stop settles the block's answers | behaviour | S |
| K9.2 The screen says why the check was withheld | behaviour (desktop) | S |
| K9.3 The primed-sibling ranking takes a clock | behaviour (tests) | S |
| K9.4 An untaken repair episode ends (Q1) | behaviour | S |
| K9.5 Pins and journey golden | structure (tests) | M |
| K9.6 Reads and hard stops out; one `_content_id` | structure | M |
| K9.7 Machine checks and the cold check out | structure | M |
| K9.8 Discriminating observation and learner actions out | structure | M |
| K9.9 Completion policy out | structure | M |
| K9.10 Presentations out; dead block planner gone | structure | M |
| K9.11 Evidence and controls out; cycle edge cut | structure | M |
| K9.12 Why a probe answer wasn't read; failed hooks | structure (records) | M |
| K9.13 Posterior as gather and fold (conditional) | structure | M |
| K9.14 The Diagnosis note | docs | S |
| K9.15 Delete `failure_triage` (Q3) | structure | S |
| K9.16 Retire the EVSI-2 shadow (Q4) | structure | M |
| K9.17 Released holds and regrades enter the posterior (Q2) | behaviour (successor) | M |

**Total:** seventeen steps. The twelve that run without an answer (K9.1-K9.3, K9.5-K9.12, K9.14) are four S and eight M: about 1.5-2 weeks of queue, of which the three fixes take about a day and the two split chains about a week. The four that wait on Q1-Q4 (K9.4, K9.15 S; K9.16, K9.17 M) and K9.13 (M, if G3 says so) add about three days. These are estimates.

## 6. What a change costs, today and after

"Today" is the map's §7 counts, every commit re-counted at this tip with `git show --name-only` (§0). "After" is my estimate of the diagnosis files a change reads and edits once the steps land. Shared plumbing (migration, head fixture, upgrade tests, notes) is arcs A's and D's and is left out on both sides.

| Change | Today | After (estimate) | Why it moves, or doesn't |
|---|---|---|---|
| (a) A causal factor shape | 2 diagnosis + 4 callers + 4 tests (`7d730fa39d`) | the same | Local already: attribution and FG1's lanes |
| (b) A probe instrument | 6 diagnosis + 8 other `src` + 3 tests (`e444e25dd0`) | 5-6 diagnosis + 8 | The family, compile and commissioning stay three places by design; the pin moves to `probe_offer.py`. Not cheaper, but each file read is 400-700 lines, not 3,500 |
| (c) A stopping rule | 3-4 diagnosis + 4-14 callers, plus a migration for the CHECK (`bc756e53d6`, `82a50f4121`) | 1 module (`probe_completion.py`) + the CHECK's migration | The rule list reads in one 590-line module; its record codes come with K9.12. The CHECK is arc D's |
| (d) A text-gap judge or source kind | 5-8 diagnosis + 1-7 callers (`877ad6d3f8`, `c3089b99ea`, `ad2c282a43`) | the same | No K9 step in `text_gaps` |
| (e) A registered constant | 1 call in the registry for 9 modules, none elsewhere (`6e55832891`: 15 files, of which the registry was one) | the same | Q5 |
| (f) A change to the quick-check offer or its actions | `causal_orchestrator.py` (3,471 lines) and its callers | `probe_offer.py` (about 370) or `causal_orchestrator.py` (about 1,020) | K9.6-K9.8; the commits since Oct 12 mostly touched one section (§1) |
| (g) "Why wasn't the check offered / this answer read / this hook run?" | no row; read the code | a `probe_verdict` record (G1), a `probe_classification` record and `diagnosis_step` rows (K9.12) | §3's trace list |

**Package size, honestly.** The moves add about +300 lines (nine modules' imports and docstrings, K9.6-K9.11). The deletions without your answers: `plan_precommitted_block` 151, `abandon_episode` 19, two `_content_id` copies 10, `hard_refusal`'s copy about 5: about 185. So diagnosis ends about 100-150 lines larger, in modules a reader can hold. With Q3 and Q4: `failure_triage` 1,054, the shadow and its report about 600 (plus their tests): about 1,850 lines smaller than today. K9.12 and G1's records add a few dozen lines each. These are estimates.

## 7. Input to the UX journey audit

What the learner sees that is a structure problem this strategy fixes, and what it leaves to the audit as design:

| What the learner sees | Structure (fixed here) | Design (left to the audit) |
|---|---|---|
| After "Stop diagnosing and teach me" mid-check, the answers' feedback never appears (TH-3) | K9.1 settles the answers and returns the released feedback ids | Where that feedback appears once the learner is in a lesson |
| "You asked me not to check" when they didn't (K9-1) | K9.2 shows it only for their own "Not now" | The words for a check withheld for burden or budget, or whether to say anything |
| A probe answer that changes nothing they can see, because it was declined unread | K9.12 records the decline's code | Whether the feedback says the answer couldn't be read and why |
| Two lanes offer a check after a miss (the causal lane's button on the feedback screen, FG1's next question with feedback held) | none; G2 makes the router the one decider (the post-miss probe stays at Next with feedback held, owner's decision 10) | One way the check is offered and declined after G2 |
| The quick check's wording names neither the causes nor why they matter (causes stay hidden by the owner's rule) | none | How to say "a quick check will tell which of two explanations fits" without priming |

**The personas, as observations:**
- **A beginner who needs prerequisite discovery.** Diagnosis serves them through learner-text gaps: a stuck answer with text is read, judged, and can create a prerequisite concept and its seed item (`diagnosis/text_gaps/actions.py:256-320`; map §2.3). It fails them where no text is written: a stuck answer without text, or a silent miss, reaches only the causal lane, whose hypotheses come from the diagnosis of what was written. A beginner's "I don't know where to start" is text the lane can read; a blank is not. Whether the stuck screen should ask for words is the audit's.
- **A student who needs a warm start.** The opening episode (`adopt_ignored_opening_episode`, `diagnosis/probe_episodes.py:561`) and the cold-start hypothesis templates (`build_episode_hypothesis_set`, `:309-322`) serve a first diagnostic block without history. They fail a student whose first misses come in the ordinary queue: the causal lane needs a diagnosis receipt and divergent repair classes before it offers anything (`diagnosis/causal_orchestrator.py:1622-1652`), and `recent_diagnostic_limit = 2` defers a third check in a short session (`diagnosis/causal_probe_coherence.py:103`). Whether a warm start should check more readily is a design question; G2 makes it the router's, not a constant's.

## 8. Risks, and what would make me stop

**Where the map, and this strategy, could not see:**
- **Nothing was run** but static sweeps and `git`. The split simulation is a graph estimate; the commit locality (§1) uses hunk lines at the time of each commit, which drift.
- **No data.** How often the two beliefs disagree, how often holds release mid-episode, how often a probe answer is regraded, how often the classifier declines, whether a remediation episode is ever left untaken: all unmeasured. G3 and the owner's counts decide Q2's size and K9.13's worth.
- **Normalization at the stop (K9.1).** I traced that the block end passes `ai_client=None` (`diagnosis/probe_blocks.py:369-376`), not whether a `None` client can still reach a model inside normalization. K9.1's step 0 checks it; if it can, the stop moves normalization to the diagnose thread instead.
- **The desktop beyond the two components read.** `FollowupPanel.tsx`, `PracticeScreen.tsx` and the TUI's practice screen were not read; K9.2 may find the same line elsewhere.

**What a step could break that no test pins today:**
- **Content ids.** Until K9.5, a move that changed `_content_id`'s input would pass every test that compares ids with each other, and new rows would stop deduplicating against old ones. Hence K9.5 first, and K9.6 merges the three copies only under its pins.
- **Function-local imports.** 555 of the package's import statements are inside functions. A missed one fails only on its path. K9.5's coverage list, `lint-imports`, and a scripted check that no attribute of a split module named in `src` or `tests` is undefined are the moves' gate.
- **Patches that become no-ops.** Seven test sites patch the two modules (§4.2). K9.5 ports them before any move.
- **Registered constants that leave the inventory** (§4.9).
- **Order inside the attempt step.** The evidence recording, the block end and the remediation bookkeeping run in one transaction in a fixed order (`attempts/attempts.py:3471-3483`). The moves keep the calls where they are; P-golden holds the rows.

**What would make me stop a step:**
- an identity pin or golden that moves in a structure step;
- P-ast failing for a moved function;
- K9.13 crossing its stop rule, or a gather read that depends on the fold;
- a step needing to change one of §3's guarantees;
- a new module that would have to import upward to stay green (the order in §4.3 or §4.4 was wrong; re-measure, don't add a local import).

**Not verified here:** everything the map lists under "Not verified" still applies. In addition, by reading, not running: that `settle_block_answers`' three parts are idempotent per answer; that the sidecar has no injected clock (no handler reads one, by grep); that `_status_for_factor`'s reads after `:1620` are unconditional (by reading the arms between `:1622` and `:1740`); that `abandoned` frees a reserved cold item for an episode with no task (by `diagnosis/remediation.py:1438`'s docstring).

## 9. The owner's decisions, in full

1. **Q1: the lifetime of an untaken repair episode** (R1-2).
   - **Today:** a remediation episode whose primed attempt is never taken has no task, no expiry and nothing that writes `abandoned`. The routine queue withholds its cold item only while a cold retry is open (ledger `:58`).
   - **Options:** (a) it ends when the learner declines it; (b) it ends when the item's next ordinary review comes due.
   - **Recommended:** (b), because it needs no new learner action and bounds the cold item's protection by a date the scheduler already has; add (a) if the UX audit gives the learner a decline for the repair.
   - **Either:** K9.4, half a day, no migration. **No answer:** the ledger row stays open past arc D.
2. **Q2: held grades released later, and regrades** (K9-3).
   - **Today:** neither moves the episode posterior; the discriminating observation is never reclassified. The diagnosis, grade interpretation and recurrence groups do move.
   - **Recommended:** yes, they should move the episode posterior. G3 first (it counts how often this happens). If G4 runs, fold the fix into G4, whose one belief makes the discriminating observation's resolution follow the posterior. If G4 is skipped, K9.17, a small successor for the episode posterior alone.
   - **If yes:** a successor and kill switch, a shadow rebuild on copies (P-playbook), after K9.13. **If no:** the rule "a probe answer's first classification is final" goes into the Diagnosis note, and the ledger row closes as by design.
3. **Q3: delete `failure_triage`.**
   - **Today:** 1,054 lines whose functions have no caller; the registry imports the module by string for three constants; it is the only writer of `failure_triage_events`, which `causal_health` reads (old rows).
   - **Recommended:** yes, K9.15 (S). L3's list already names it for you.
   - **If no:** it stays, and any deletion by import alone breaks `refresh`.
4. **Q4: retire the EVSI-2 shadow selection.**
   - **Today:** every causal probe decision also computes and stores a shadow selection with zero live authority (`diagnosis/causal_orchestrator.py:1491-1515`), read only by a readiness report on the measurement-health screen. Your rule since Oct is live changes over shadow stages.
   - **Recommended:** yes, with or after G2, when the router decides and the shadow has nothing left to ready for. K9.16 (M).
   - **If yes:** about 600 lines go and the readiness panel goes. **If no:** it stays as a report, and each decision keeps paying for it.
5. **Q5: the parameter registry.**
   - **Recommended:** no diagnosis-only change. If you want a constant registered beside its definition, ask for one cross-package step (all 380 entries, 96 modules), outside K9. Until then, a moved constant takes its registry path with it.

## Added at landing (orchestrator, 2026-11-14): ledger D-39

This strategy was written before D6's first landing reported ledger row D-39, so no step here covers it. D6 removed the point probe path, which no supported vault takes, and moved the checkpoint-3 planted-type simulation (`tests/test_sim_probe_validation.py`, `learnloop.sim.diagnostic_validation`) onto the robust probe path every supported vault takes. There it diagnoses the planted `surface_only` type 2 times in 5, under its 0.6 gate; the test is a strict xfail. It passed before only because it ran at an old tag on the old path.

That is a question about what diagnosis concludes, not about its layout, and it comes before the structure steps that touch the same code:

- **K9.0 (behaviour, investigation first; due at arc D's close with D-39).** Reproduce the simulation at the head with more trials and every planted type, with the seeds recorded, and report per type how often the robust path names it and what it names instead. Then say which it is: the robust path's likelihoods or stopping rule under-separate `surface_only` from its neighbours (a real fault: a fix is a successor under the playbook, with a shadow comparison); the simulation's planted learner is not what the robust path's instruments measure (the simulation is wrong: fix the simulation and say why); or five trials were too few to tell (the gate needs a sample size that can pass or fail). No step K9.6 to K9.11 that moves the posterior or the instruments lands before K9.0 reports, so a move cannot hide or shift the behaviour being measured.
- It needs no vault data: the simulation is synthetic. Whether the same shows on real histories is unknown and stays unknown until the owner's vaults hold enough probe episodes to look.

