# Diagnosis map (K9, 2026-11-12)

Refactor step K9, job 1: the deep map of `src/learnloop/diagnosis/` that the Nov 8 map (`docs/reviews/architecture-map-2026-11-08.md`) read by outline. It names problems and recommends nothing; job 2 (the structure strategy) stands on it after the orchestrator has checked its claims. **Base: main `95bee5f02a`**, branch `refactor/k9-diagnosis-map`. Docs only; no source, test or vault note changed.

## Summary for the owner

Diagnosis is 110 modules and 73,609 lines (53,389 code): the causal repair lane, probe episodes and blocks, VOI stopping, follow-ups, the blind diagnose job, text gaps, recurrence and offline review. Its parts are often careful (pre-registered blind bundles, content-addressed observations, typed refusals, a pure Bayes step, B7's records). What's expensive is that the questions arc G is about are each answered in several places, by rules that differ, inside two very large modules.

**The five most costly findings:**

1. **Ten sites answer "should we probe?", and one probe answer moves two beliefs over two different locked sets (§3.1, §3.3; D9B1, D9B2, D9D1).** The causal lane's verdict counts repair classes, FG1's lane counts rival hypotheses and its factor counts episode keys, so a miss whose rivals share one repair goes to FG1's probe lane while the causal lane would call it action-equivalent. The episode posterior updates inside the attempt step over `enter_episode`'s set; the discriminating observation is written after the commit against commissioning's set, locked with support scores the second lock doesn't get. Nothing compares them, and there are two more beliefs beside them (a legacy probe-phase posterior and the misconception posterior, D9F5).
2. **A regrade changes neither belief (§2.7; D9D2).** The episode keeps the outcome classified at submission and the discriminating observation is never reclassified, while the diagnosis, the grade interpretation and the recurrence groups move to the new grade. A held grade that is later released never enters the episode posterior.
3. **The probe policy's "fitted" thresholds are constants, and three docstrings at the centre say otherwise (§3.2, §6.1; D9B3, D9C1).** Three copies of one resolver read fitted-parameter scopes that nothing writes (`learnloop fit` writes two other scopes), so `recent_diagnostic_limit = 2`, the 0.0 margins and the 0.8 success cut are hand-set. The orchestrator's docstrings also call the discriminating observation the only support channel (a self-report resolves factors too) and name `failure_triage`, which nothing calls, as its consumer.
4. **Two modules hold the lane's decision, its learner actions, both beliefs, the stopping policy and the serve gate, inside a 21-module cycle closed only by function-local imports (§1; D9P1-D9P3).** `causal_orchestrator.py` (3,471 lines, 48 exports, the 517-line `_status_for_factor`) and `probe_episodes.py` (3,651 lines, seven stopping rules in one function); `probe_blocks` imports the latter's private functions and is imported back inside functions.
5. **The causal lane's verdict and the classifier's declines are outside the trace (§4; D9O1, D9O2, D9D5).** `causal_probe_decision_receipts` is rich but has no `decision_records` row, so a withheld offer is reachable from an attempt only through its factor; the deterministic classifier declines in six ways and records none, and the four grade-keyed hooks still fail to a log line.

**Also worth your attention:**
- **`failure_triage` isn't unimported (§6.2).** Its functions have no caller, but the parameter registry imports it by string to resolve three constants, at sidecar vault open among other places; deleting it needs those entries removed in the same commit. Five `Repository` methods carry its name, three of them live.
- **The block-end hook runs inside the attempt step (D9D4),** while the post-attempt pipeline normalizes outside any transaction because normalization may call a model.
- **The desktop copies backend rules (D9B5),** and one copy is wrong: the "You asked me not to check" message also shows when the offer was withheld for burden or budget (candidate bug K9-1).
- **The one diagnosis concept note describes August's system (D9V1),** and no note explains who decides to probe or the beliefs.

**Deciders and purity (§4).** Pure today: `decide_probe` (given its parameters) and the prior-analysis arm; `value_candidates` is one context object away. Everything else reads the database while deciding, and every record is built after the decision from its outputs.

**Change cost (§7).** A diagnosis change with no migration or successor touched 4-17 files (1-8 in diagnosis, 4-8 callers in `followup_run`, `scheduling`, `daily_plan` and the sidecar). With a migration or successor: 65-834 files, the difference being the head fixture (24), upgrade and pinned tests, `template.py` and, before mid-October, about 350 generated notes. The registry holds 381 `_reg_const` constants (39 in diagnosis), all `heuristic`, none read back at run time.

**Limits.** Code-traced, not run; no vault data. Four sweeps were delegated and spot-checked; what wasn't checked is under "Not verified".

## How to read this

**Scope** (strategy §2.18, K9): `src/learnloop/diagnosis/` whole (110 modules), the callers' side of each boundary (the post-attempt pipeline, `followup_run`, `followup_serve`, `daily_plan`'s follow-up gate, `goals`' cold probes, `scheduling`'s EIG ranking, the sidecar's remediation, feedback, practice and measurement handlers, the desktop's feedback and probe screens), and `params/parameter_registry.py` as a cost every diagnosis change pays.

**Severity** is what a finding costs. **High:** it hides a cause, makes two answers to one question possible, or regularly costs a stage real time. **Medium:** it costs when you're in that area. **Low:** noise. Ids are prefixed `D9` so they don't collide with the Nov 8 map's or K2's: D9P packages and imports, D9D journeys, D9B boundaries and duplicated predicates, D9O decisions and what's recorded, D9F functional core, D9C comments, dead code and onboarding, D9H change cost, D9V vault.

**Evidence** is `file:line` at `95bee5f02a`; `src/learnloop/` is dropped from paths under it, so `diagnosis/probe_episodes.py:1869` means `src/learnloop/diagnosis/probe_episodes.py:1869`. Paths under `src/learnloop_sidecar/` keep the `learnloop_sidecar/` prefix, and frontend paths start `apps/`. A bare `:line` continues the file before it. "Read" means I read the code; "traced" means I followed the calls without running them. Nothing was executed except an AST and import sweep over `src/` (the K2 method; the script and its output are in the orchestrator's scratch, `refactor-k9/sweep_k9.py`, `sweep.txt`) and read-only `git log`. No vault, backup or learner data was opened. Four read-only sweeps were delegated (callers' side of the boundaries; the deletion proof; the vault notes; change cost from git history). Every claim of theirs used below was spot-checked at its cited line, and those not checked are listed in "Not verified".

| § | Contents | Brief item |
|---|---|---|
| 1 | Packages, modules, deep and shallow, long functions, imports and cycles, reachability | 1 |
| 2 | The journeys end to end | 2 |
| 3 | Boundaries and duplicated predicates | 3 |
| 4 | Decision points and what's recorded; which deciders are pure | 4 |
| 5 | Functional core and shell | 5 |
| 6 | Comments, dead code, onboarding | 6 |
| 7 | Change cost, counted; the parameter registry | 7 |
| 8 | The vault notes | 8 |
| | Not verified | |
| A | Every module, classified (replaces the Nov 8 map's Appendix A rows for diagnosis) | |

## 1. Packages and modules

Sizes are from an AST and tokenizer sweep at this tip; "code" means non-blank lines that aren't comments or docstrings, as in the Nov 8 map. The class heuristic is the Nov 8 map's (deep: ≥250 code lines and ≤10 public names, or ≥400 and ≤1 public name per 40 lines; wide: ≥30 public names, or ≥20 with under 20 lines per name; shallow: thin, or a one-importer helper ≤80 lines). Public names here are module-level functions, classes and lower-case assignments without a leading underscore, so counts differ by a few from the Nov 8 map's. Appendix A lists all 110 modules.

| subpackage | owns | modules | raw | code | functions | functions ≥200 lines | in the 191-module cycle |
|---|---|---:|---:|---:|---:|---:|---:|
| root (`diagnosis/*.py`) | causal attribution and the orchestrator, probes, episodes, blocks, hypotheses, families, VOI stopping and forecasting, follow-ups, remediation, misconceptions, calibration sessions, guided redo, scoreboard, reports | 57 | 48,332 | 34,495 | 1,060 | 16 | 34 |
| `split` | the blind grade/diagnosis split: the diagnose and embed jobs, context, history, validation, the card, live causal view | 20 | 9,811 | 7,422 | 317 | 4 | 11 |
| `text_gaps` | learner-text gaps: sources, the reading, judges, Tier 1 (Decider), actions, the gap job queue | 12 | 6,355 | 4,340 | 241 | 0 | 9 |
| `recurrence` | same-cause groups, the live T1 step, escalation, the guard, the backlog | 11 | 4,208 | 3,121 | 144 | 0 | 6 |
| `offline_review` | the M1 offline review runner, judge, planted cases, spot check, report | 10 | 4,903 | 4,011 | 172 | 0 | 5 |
| **total** | | **110** | **73,609** | **53,389** | **1,934** | **20** | **65** |

By class: 43 deep, 52 medium, 8 wide, 2 shallow, 5 package inits. The eight wide modules are the ones a reader has to learn name by name: `causal_orchestrator` (35 public names, 48 in `__all__`, `diagnosis/causal_orchestrator.py:3426`), `probe_episodes` (46), `text_gaps.sources` (39), `voi_stopping` (32), `offline_review.judge` (28), `ai_contracts`, `text_gaps.actions` (25 each) and `text_gaps.judges` (20).

### 1.1 The functions over 200 lines

| lines | function | what it does |
|---:|---|---|
| 517 | `_status_for_factor`, `diagnosis/causal_orchestrator.py:1414` | the whole repair-lane decision for one open factor: classifies the cause set, reads eleven inputs, calls `decide_probe`, writes the receipt and the EVSI-2 shadow, maps the verdict to one of five learner statuses and may mint an episode (§2.1 step 8, §4) |
| 398 | `validate_diagnosis_proposal`, `diagnosis/split/validation.py:225` | validates the diagnoser's proposal against the grade, rubric and evidence |
| 389 | `evaluate_intervention_followup`, `diagnosis/followups.py:155` | the follow-up gate: severity, surprise, probe phase, value of the follow-up, insertion |
| 360 | `record_shadow_selection`, `diagnosis/causal_diagnostic_selector.py:312` | the EVSI-2 shadow selector beside every causal decision receipt (zero live authority, `causal_orchestrator.py:1491-1494`) |
| 357 | `materialize_causal_episode`, `diagnosis/causal_attribution.py:2343` | turns a diagnosis receipt into causal hypotheses, an unresolved-cause factor and a probe need |
| 345 | `_choose_intervention_item`, `diagnosis/followups.py:1682` | picks the follow-up item |
| 342 | `commission_probe_instrument`, `diagnosis/causal_probe_commissioning.py:383` | mints a causal probe candidate: blind bundles, manipulation audit, first lock of the hypothesis set |
| 297 | `_load`, `diagnosis/split/history.py:764` | the diagnoser's history snapshot |
| 290 | `assemble_diagnosis_context`, `diagnosis/split/context.py:680` | the diagnoser's prompt context |
| 281 | `record_remediation_attempt`, `diagnosis/remediation.py:819` | the repair episode's bookkeeping inside the attempt step |
| 260 | `_record_presentation_observation`, `diagnosis/probe_episodes.py:2519` | one probe answer: validates and consumes the presentation, classifies the outcome, the posterior before and after, writes `probe_observations`, the activity fact and the dual-written grade |
| 248 | `_hypothesis_specs`, `diagnosis/causal_attribution.py:1649` | causal hypothesis specs from a receipt |
| 246 | `claim_checked_feedback`, `diagnosis/causal_attribution.py:2975` | the learner-facing causal overlay, gated by claim authority |
| 245 | `_accept_probe_offer`, `diagnosis/causal_orchestrator.py:2077` | "Take the quick check" and FG1's automatic offer: enters or relocks an episode and pins the probe |
| 238 | `record_unresolved_cause_self_report`, `diagnosis/causal_attribution.py:3543` | the learner's own cause report; can resolve a factor (`:3738`) |
| 235 | `_diagnose`, `diagnosis/split/jobs.py:814` | one diagnosis model call: prompt version, prior-analysis arm, spend, agent run, persist |
| 224 | `run_hardcases`, `diagnosis/grading_hardcases.py:629` | a CLI report |
| 211 | `value_candidates`, `diagnosis/voi_stopping.py:996` | values each candidate next observation and decides stop or continue |
| 210 | `reschedule_assisted_cold_retry`, `diagnosis/remediation.py:1137` | moves a cold retry after assisted practice |
| 203 | `select_minimal_repair`, `diagnosis/causal_attribution.py:691` | chooses the repair class |

**`_status_for_factor` read through.** 517 lines, 36 of them comments (`diagnosis/causal_orchestrator.py:1414-1930`). It has one inner function, `finish` (`:1452-1562`), which every arm calls: it writes the decision receipt (`:1467`), runs the EVSI-2 shadow in a `try` that records a `diagnosis_step` failure (`:1495-1515`), optionally mints an episode (`:1516-1525`) and builds the `RepairStatus`. Before the verdict it reads, in order: the hypothesis (`:1427`), two parameter sets from the fitted store (`:1431-1432`), the cause-set classification (`:1434`), the repair-class need (`:1622`), the diagnosis receipt (`:1624`), pending machine checks (`:1637`), the open-episode conflict (`:1652`), the candidates (`:1656`), the locked set's prior basis (`:1686`), the probe burden (`:1713`), the avoided over-teaching minutes (`:1718`), the learner's preference (`:1724`) and the recent burden (`:1730`). It writes before the verdict in two arms (`enqueue_backfill_obligation`, `:1593`; `close_satisfied_backfills`, `:1620`). Then `decide_probe` (`:1740`) returns a verb, and eight `if` arms (`:1800-1930`) map the verb, the instrument's review state, the episode conflict and the learner preference onto the five statuses that the module docstring's table lists (`:20-38`). The docstring's table is the best explanation in the package of what the function does; the function itself starts with no approach paragraph.

**What `causal_orchestrator.py` holds** (3,471 lines; section headers at `:266`, `:350`, `:469`, `:796`, `:853`, `:1183`, `:1933`, `:2376`, `:2446`, `:3012`): its three fitted-parameter knobs and their resolver (`:266-340`); the `RepairStatus` result type (`:350-466`); the machine-check queue, producer and sweep (`:469-793`); the learner's "Not now" preference (`:796-850`); factor and receipt plumbing, including the EVSI inputs (`:853-1180`); the orchestrator, `causal_repair_status` and `_status_for_factor` (`:1183-1930`); the learner actions, accept, defer and "Teach me now" (`:1933-2373`); classification against the pinned bundles (`:2376-2443`); the classification-to-resolution edge, the discriminating observation and the deterministic sensor (`:2446-3009`); and the cold verification context, its recorder and the expired cold retry sweep (`:3012-3420`). So one module holds the repair lane's decision, its learner actions, its second belief channel and its cold check.

**What `probe_episodes.py` holds** (3,651 lines; headers at `:154`, `:824`, `:1163`, `:1866`, `:2097`, `:2899`, `:3444`, `:3570`): the episode lifecycle, entry, relock, adoption and re-probe triggers (`:154-822`); instrument resolution and eligibility (`:824-1160`); presentations, the routine-display refusal, the serving gates and the VOI serve gate (`:1163-1864`); the posterior replay (`:1866-2095`); evidence recording, including the dual-written grades and the regrade's (`:2097-2898`); the completion policy with its seven stopping rules (`:2899-3443`); learner controls (`:3444-3568`); and the client contract (`:3570-3651`). The first belief channel, the stopping rules and the serving gate are in one module, and `probe_blocks` imports two of its private functions (`_evaluate_completion`, `_set_target_decision`, `diagnosis/probe_blocks.py:29-36`).

### 1.2 Imports and cycles

- **Statements.** Diagnosis modules make 1,946 import statements of other `src` modules; 560 of them (29%) are inside functions. The whole package's share at the Nov 8 map was 32% (2,949 of 9,262).
- **No cycle exists among top-level imports inside diagnosis.** Every cycle below is closed by at least one function-local import, so each one is invisible from module heads.
- **Four strongly connected components inside the package** (function-local imports included):

| size | modules | the edges that close it (function-local unless marked T, top-level) |
|---:|---|---|
| 21 | `calibration_sessions`, `causal_orchestrator`, `followups`, `guided_redo`, `misconceptions`, `probe_blocks`, `probe_episodes`, `probe_instance_generation`, `remediation`, `split.jobs`, `recurrence.{backlog, escalation, guard, judging, live}`, `text_gaps.{actions, candidates, jobs, judges, pipeline, tier1}` | `causal_orchestrator` → `probe_episodes` (`diagnosis/causal_orchestrator.py:1996`, `:2031`, `:2165`); `causal_orchestrator` → `remediation` (`:457`) and back (`diagnosis/remediation.py:148`, `:964`); `probe_episodes` → `probe_blocks` (`diagnosis/probe_episodes.py:2173`, `:3465`) and back (`diagnosis/probe_blocks.py:29` T); `probe_episodes` → `probe_instance_generation` (`diagnosis/probe_episodes.py:280`, `:373`, `:793`) and back (`diagnosis/probe_instance_generation.py:1036`, `:1244`, `:1407`); `probe_episodes` → `calibration_sessions` (`diagnosis/probe_episodes.py:3074`) and back (`diagnosis/calibration_sessions.py:19` T); `followups` → `causal_orchestrator` (`diagnosis/followups.py:71`, `:838`, `:986`, `:1048`), `split.jobs` (`:937`), `text_gaps.jobs` (`:957`); `split.jobs` → `followups` (`diagnosis/split/jobs.py:1102`), `misconceptions` (`:1103`), `recurrence.live` (`:354`, `:1100`), `text_gaps.jobs` (`:1151`); `text_gaps.pipeline` → `split.jobs` (`diagnosis/text_gaps/pipeline.py:273`) and `text_gaps.tier1` (`:331`) with `tier1` → `pipeline` (`diagnosis/text_gaps/tier1.py:69` T); `recurrence.guard` ↔ `recurrence.backlog` (`diagnosis/recurrence/guard.py:587`, `diagnosis/recurrence/backlog.py:126`); `probe_blocks` → `followups` (`diagnosis/probe_blocks.py:389`) |
| 7 | `probes`, `probe_families`, `probe_hypotheses`, `probe_outcome_mapping`, `probe_robust`, `voi_forecasting`, `voi_stopping` | `probes` → `voi_stopping` (`diagnosis/probes.py:1455`); `probe_hypotheses` → `probe_families` (`diagnosis/probe_hypotheses.py:186`) with `probe_families` → `probe_hypotheses` (`diagnosis/probe_families.py:632`); `voi_stopping` → `probe_hypotheses`, `probe_families`, `probe_robust`, `voi_forecasting` (`diagnosis/voi_stopping.py:490`, `:2152`, `:2197`, `:2348`) |
| 2 | `causal_attribution`, `missing_vocabulary` | `diagnosis/causal_attribution.py:1210`; `diagnosis/missing_vocabulary.py:71` |
| 2 | `split.embeddings`, `split.retrieval` | `diagnosis/split/embeddings.py:154`; `diagnosis/split/retrieval.py:232`, `:319` |

- **The package and the global cycle.** With function-local imports the largest component of the whole `src` import graph is 191 modules and 166,920 raw lines by this sweep's resolution (the audit's sweep counted 189 and 166,533; the difference is how `from package import name` resolves). Diagnosis holds 65 of them, the same 65 the Nov 8 map counted. Four of the audit's seven cutting edges are in or into diagnosis (audit §2.2): `causal_orchestrator` → `probe_episodes` (three function-local reads, above), `text_gaps.sources` → `source_retrieval.note_gaps` (`diagnosis/text_gaps/sources.py:1041`, `:1052`), `text_gaps.jobs` → `text_gaps.pipeline` (`diagnosis/text_gaps/jobs.py:42`, top-level) and `probe_episodes` → `probe_blocks` (`diagnosis/probe_episodes.py:2173`, `:3465`).
- **Who imports the two largest modules from outside.** `causal_orchestrator`: the sidecar's remediation handler (five names, `learnloop_sidecar/handlers/remediation.py:6-12`), four `followup_run` modules (`followup_run/router.py:98`, `admission.py:394`, `jobs.py:257`, `serving.py:231`, all function-local), `tutor/tutor_qa.py:685` and the CLI (`cli/app.py:5279`). `probe_episodes`: the attempt step (`attempts/attempts.py:3069`, `:3097`, `:3382`, `:3498`, `:3655`), the scheduler (`scheduling/scheduler.py:26`), the sidecar's practice handler (`learnloop_sidecar/handlers/practice.py:41`), the TUI, `instructional/valuation.py:209`, `source_retrieval/passage_cues.py:388`, `substrate/state_sync.py:218`, `curriculum/golden_path_run.py:324`, `curriculum/confusable_concepts.py:6`, `followup_run/admission.py:242` and the simulator.

### 1.3 Reachability

From the sidecar, the phone host and the MCP server (static imports with function-local ones and package inits included), 95 of the 110 modules are reachable. Fourteen modules (6,868 raw lines, the audit's figure exactly) are reachable only from the CLI: `gate_fit`, `grading_hardcases`, `offline_review.{links, report, spot_check}`, `probe_audit`, `probe_coverage`, `probe_lifecycle`, `recurrence.{benchmarks, report}`, `split.{pfc_report, reports}`, `taxonomy_regrade`, `text_gaps.report`. The TUI reaches none of them (the sweep's root set included it; nothing in `tui/` names them or their commands). Two qualifications the import graph can't see:
- **The desktop can run any CLI command.** The sidecar's `run_cli_command` (`learnloop_sidecar/handlers/cli.py:18-19`) runs `python -m learnloop <argv>` as a subprocess (`:63-64`), so these 14 are one palette command away from a serving process. The phone's allowlist doesn't include it (delegated, grep only).
- **Three string imports name diagnosis modules,** which a static sweep misses: the parameter registry's `MODULE_INVENTORY` (`params/parameter_registry.py:106-175`, nine diagnosis modules, imported by `importlib.import_module` at `:3099` through `MODULE_IMPORTS`, `:296-299`), `instructional/valuation.py:387`, `:396` (`text_gaps.pipeline`) and `scheduling/open_world_gate.py:97` (`robust_composition`).

`failure_triage` (1,054 lines) has no static importer anywhere in `src`, but it is not unreachable: the registry imports it at run time to resolve its three registered constants (§6.2). Its functions are called by nothing outside tests.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9P1 | high | **The repair lane is one 3,471-line module with 48 exported names, and its central function is 517 lines.** `_status_for_factor` reads eleven inputs from the database, writes in three places, asks `decide_probe` for a verb and maps it onto five statuses with eight `if` arms. The decision, its learner actions, the second belief channel and the cold check share the module, so a change to any one is read against all of them. | §1.1; `diagnosis/causal_orchestrator.py:1414-1930`, `:3426` |
| D9P2 | high | **`probe_episodes.py` holds the episode posterior, the seven stopping rules and the VOI serving gate in one 3,651-line module, and the module next to it imports its private functions.** `probe_blocks` imports `_evaluate_completion` and `_set_target_decision`, and `probe_episodes` imports `probe_blocks` back inside two functions. | `diagnosis/probe_blocks.py:29-36`; `diagnosis/probe_episodes.py:2173`, `:3465`, `:2899-3443` |
| D9P3 | high | **A 21-module cycle joins the causal lane, episodes, blocks, follow-ups, the diagnose job, recurrence and text gaps, and every edge that closes it is a function-local import.** A reader of any of the 21 can't tell from its imports what it depends on; `split.jobs` alone reaches back into five of them inside functions. | §1.2 table; `diagnosis/split/jobs.py:354`, `:1100-1103`, `:1151`, `:1430-1431` |
| D9P4 | medium | **29% of the package's imports hide in functions**, and the package holds 65 of the 191 modules in the global cycle, through four of its seven cutting edges. | §1.2 |
| D9P5 | medium | **15 modules (7,922 lines) are tooling or dead weight beside the serving code, and nothing marks which side a module is on.** 14 report modules are reached only from the CLI (and so from the desktop palette's generic `run_cli_command`); `failure_triage`'s functions are called by nothing, yet the registry imports the module by string. An import sweep alone gets both wrong. | §1.3; §6.2 |
| D9P6 | low | Shallow modules are two (`offline_review.spend`, 6 lines; `offline_review.decider_links`, 83). Not a cost. | Appendix A |

## 2. The journeys end to end

Two lanes act on a miss. The **causal lane** (`causal_orchestrator`) decides with `decide_probe` and offers the learner "Take the quick check"; the **FG1 lane** (`followup_serve` and `followup_run`) holds feedback, lets the router decide, authors a probe and pins it through the same `accept_probe_offer`. Both lanes classify the answer through the same discriminating-observation edge, and both run beside the **episode lane** (`probe_episodes`), whose posterior updates inside the attempt step.

**Processes.** The desktop sidecar runs the submit request and, after it, four daemon threads (`learnloop_sidecar/post_attempt_worker.py:3-6`): `diagnose` (one at a time, in attempt order), `embed`, `gaps` (`learner_text_gap_jobs`) and `followup` (`followup_generation_jobs`), each on its own connection, lease-fenced, started lazily on the first notify (`:13-15`). The CLI drains the same queues (`diagnosis/split/jobs.py:1266`). Persistence below is SQLite unless marked **[Y]** (a vault YAML file).

### 2.1 A miss on an ordinary item, through the causal lane

1. **Grade.** The blind door grades (one model call, the blind grader's route), then in one transaction applies the attempt and appends the blind record (`attempts/attempts.py:2415-2441`): `practice_attempts`, grading evidence, `blind_grade_records`, the `grade` decision record (B7). The hold for review is evaluated in flight (`grade_held_for_review`, `:2433`).
2. **Inside the attempt step,** before the blind record exists, the episode lane runs if the learning object has an open episode: `record_episode_evidence` (`attempts/attempts.py:3498-3515`, `diagnosis/probe_episodes.py:2100`) replays the posterior and writes `probe_episode_beliefs` through `persist_episode_beliefs` (`:2164-2166`). An ordinary item updates belief as incidental evidence (`:2049-2071`), damped by hints and exam type (`:1967-1971`). The repair-lane bookkeeping runs here too (`record_remediation_attempt`, `attempts/attempts.py:3488`).
3. **Post-attempt pipeline** (`attempts/post_attempt.py:89`), under a cross-process completion lock (`:125`): the certification cold-probe schedule and the feedback metadata (`:137-139`, `:299-309`); a held grade suppresses every insertion (`:145-154`); a joint-graded attempt is normalized here outside any transaction because normalization may call a model (`:156-161`, docstring `:114-117`); FG1 may open a workflow that owns the miss (`:163-172`, §2.2); then `evaluate_attempt_intervention_followup` (`:173-184`) and, for a blind vault, the `diagnose` job is enqueued in the completion's transaction (`:185-188`). A stuck answer with text is queued for the gap reader after the commit (`:211`).
4. **Grade-keyed causal hooks** (`diagnosis/followups.py:668-683`, `_run_causal_orchestrator_hooks` at `:803`): the re-probe trigger, the machine-check sweep (`:846`), the cold verification when this attempt consumed a cold retry (`:864-878`), the deterministic classification of a pinned probe (`:886`), and, for a joint vault only, the common-repair consultation (`:895-900`). These run even when the grade is held, because the held check only suppresses insertion (`:685-696`). Each failure is a log line only (`:856`, `:880`, `:890`, `:902`).
5. **Diagnose job** (sidecar `diagnose` thread; `diagnosis/split/jobs.py:689`, `_diagnose` at `:814`). One model call on route `diagnosis` (`:70`, admitted through spend caps `:883-887`), prompt `diagnosis-v1-split` (`diagnosis/split/settings.py:16`) with suffixes for workbench traces, figures and the prior-analysis arm (`diagnosis/split/jobs.py:853-867`). **Randomness:** the prior-analysis arm is a SHA-256 draw over the attempt id (`diagnosis/split/prior_analysis.py:93-95`), recorded on the context receipt. **Clocks:** `started_at` is the forecasts' `inputs_as_of` (`diagnosis/split/jobs.py:915`); latency is monotonic (`:948`, `:1034`). Writes: `agent_runs` (`:916`), `attempt_diagnoses` with the `diagnosis` decision record in the lease-checked `_persist` (`:418`, `:1046`), and diagnosis forecasts in the same transaction (`:1037-1044`). A failure releases the job with backoff up to `max_attempts` (`:1006-1011`).
6. **Apply the diagnosis** (`diagnosis/split/jobs.py:1058`): reproject canonical facet state under `BEGIN IMMEDIATE` (`:1112-1115`); the recurrence step, which may call the same-cause judge and the embedding route (`:1117-1121`, §2.4); misconception normalization with no model client (`:1122-1129`), which materializes causal hypotheses and the `unresolved_cause_factors` row from the diagnosis; the post-diagnosis hooks (`:1130`, `diagnosis/followups.py:967`): the machine-check sweep and `_consult_common_repair` (`:1006`); pattern verdicts (`diagnosis/split/jobs.py:1138`); the escalation receipt (`:1140`); and the gap enqueue (`:1151-1153`). Failures of the last three steps and the hooks leave `diagnosis_step` records (`:1146`, `:1156`; `diagnosis/followups.py:996`, `:1002`).
7. **Hypothesis set and the first lock.** For a divergent factor the probe instrument is commissioned (`diagnosis/causal_probe_commissioning.py:383`): blind prediction bundles are written before any answer exists, content-addressed (`diagnosis/causal_probe_coherence.py:928`, ids from `_content_id("bpb", ...)`, `:968`), and the hypothesis set is locked with the diagnosis receipt's support scores (`diagnosis/causal_probe_commissioning.py:669-676`; `diagnosis/causal_probe_coherence.py:814`). The prior is support-weighted, else the grader's verbalized prior floored, else uniform, with `H_OTHER` given `max(Σw·0.1, 0.1)` (`:747-801`, defaults `:95-107`).
8. **The probe decision.** `_consult_common_repair` calls `causal_repair_status(start_repair=False)` only for a non-divergent factor (`diagnosis/followups.py:1062-1078`); a divergent factor waits for the learner's feedback screen, whose handler calls `causal_repair_status` (`learnloop_sidecar/handlers/remediation.py:6-12`). `_status_for_factor` (§1.1) reads its inputs, calls `decide_probe` (`diagnosis/causal_orchestrator.py:1740`) and writes `causal_probe_decision_receipts` on every arm (`:1467`), including a read with `start_repair=False` (docstring `:1261-1264`). `decide_probe` is a fixed ladder (`diagnosis/causal_probe_coherence.py:457-524`): common repair, one repair class, pending machine checks, the learner's preference, recent burden against `recent_diagnostic_limit = 2`, the session budget, then EIG, action change and avoided minutes against margins of 0.0.
9. **Presentation.** "Take the quick check" calls `accept_probe_offer` (`diagnosis/causal_orchestrator.py:2045`), which writes the `probe_offer` record (`:2070-2073`) after `_accept_probe_offer` (`:2077`): the first reviewed-active candidate in the shared order (`:2120-2143`), the routine-display check (`:2157`), then either a relock of an empty open episode (`:2293-2301`) or `enter_episode` with the factor (`:2302-2316`). **`enter_episode` locks the hypothesis set a second time, without support scores** (`diagnosis/probe_episodes.py:291-302`), so its prior basis can differ from the candidate's lock in step 7, and a new set id is minted (§3.3). The presentation is committed with the candidate, the candidate's (first) hypothesis set id and the bundle ids pinned under `selection_components.causal_probe` (`diagnosis/causal_orchestrator.py:2223-2249`); the episode's posterior at selection is written on `probe_presentations` by `commit_presentation` (`diagnosis/probe_episodes.py:1285`).
10. **The answer.** The probe answer is an attempt with `probe_presentation_id`. Inside the attempt step `_record_presentation_observation` (`diagnosis/probe_episodes.py:2519`) consumes the presentation, computes the posterior before by full replay (`:2570`), classifies the outcome from the card snapshot (`:2629-2635`), damps the weight for contamination, dialogue share and long-form traces (`:2668-2678`), and writes `probe_observations` with both posteriors and the realized information gain (`:2707-2727`) and the dual-written grade (`:2748`). A held grade writes an inert observation (`:2573-2612`).
11. **The second belief update.** After the attempt commits, the grade-keyed hooks call `auto_classify_pinned_probe` (`diagnosis/causal_orchestrator.py:2943`), which reads the criterion outcomes as features (`deterministic_probe_features`, `:2886`; "passed" is `fraction >= 0.40`, `:2935`), and `record_probe_classification` (`:2692`) matches them exactly against the pinned bundles of the *candidate's* locked set (`:2758`, `:2430-2436`), checks independence against reveals and FG1 exposure (`:2784`, `:2565-2602`), and writes `causal_discriminating_observations` with a content-addressed id (`:2807-2816`, `:2828`).
12. **Resolution.** An admitted `matched_single` resolves the factor (`:2821-2827`). Other resolvers of the same factor are listed in §3.1.
13. **Repair.** With the factor resolved, the next `causal_repair_status` call maps it to `started` and `_episode_for` mints a `remediation_episodes` row (`diagnosis/causal_orchestrator.py:1516-1525`); a held repair raises `RemediationBlocked` to the caller (`diagnosis/remediation.py:162-163`). Passages are prescribed by `prescribe_remediation` (`:178`).
14. **The cold check.** The primed repair attempt's bookkeeping (`record_remediation_attempt`, `diagnosis/remediation.py:819`) schedules a cold retry whose task carries the context resolved now (`cold_verification_context`, `diagnosis/causal_orchestrator.py:3015-3122`). When the retry is answered, the grade-keyed hooks call `record_cold_verification_from_task` (`diagnosis/followups.py:864-878`, `diagnosis/causal_orchestrator.py:3125`), which writes `causal_cold_verifications` with success at correctness ≥ 0.8 (`diagnosis/causal_probe_coherence.py:101`, `:1912`), and a confirmed repair resolves matching open factors (`diagnosis/causal_factor_deferral.py:217-225`). An unmeasurable retry writes `causal_cold_outcomes` (`diagnosis/remediation.py:782`, `:910`).

### 2.2 The follow-up generate-and-serve lane (FG1), beside the causal lane

1. **Open.** In the completion's transaction, a miss on a surface with the pending UI opens a workflow and holds feedback (`attempts/post_attempt.py:219-252`; `followup_serve/workflow.py:86`). Its `followup_workflows` row suppresses the predecessor's insertion (`attempts/post_attempt.py:169-172`); in a joint vault the generation job is queued at once (`:199-202`), in a blind vault after the diagnosis.
2. **Run** (sidecar `followup` thread; `followup_run/jobs.py:328`). A blind attempt without a finished diagnosis takes the practice lane (`:340-345`). `open_rival_causes_factor` opens a factor when the miss has rival causes (`followup_run/lanes.py:45-57`); `select_lane` takes the probe lane only for a factor with two concrete rivals (`:60-71`); a cause that reproduces a reserved question goes to practice (`followup_run/jobs.py:350-361`).
3. **Decide.** `router.decide_once` (`followup_run/jobs.py:392`) runs `hard_refusal` (preference, machine checks, episode conflict; `followup_run/router.py:93-118`), then the router's follow-up gate, FG1's `FollowupGate` or, at the router-objective tag, `ObjectiveFollowupGate` (`:183-195`). The gate's arms are ask now, wait, no intervention, a lesson offer or decline (`followup_run/jobs.py:393-420`). `decide_probe` is also called, with every value input fixed at 0.0, only to fill the decision's `observational` field (`followup_run/router.py:128-149`); with those inputs it can never return `probe_now`.
4. **Wait releases feedback and marks the probe exposed** (`followup_run/jobs.py:418-420`), so its answer can't resolve the cause (`diagnosis/causal_orchestrator.py:2589-2593`).
5. **Author, persist, commission, pin.** One authoring call on a plan route (`followup_run/jobs.py:432-435`), `hard_refusal` again after the model wrote (`:437-439`), the item persisted **[Y]** (`:440`), then `commission_and_pin` (`followup_run/admission.py:376`): commissioning with blind bundles over the deterministic vocabulary (`:79-112`) and the first lock (step 7 above), then `accept_probe_offer` with `router_decision_id` (`:421`), which enters the episode and locks the second set (step 9).
6. **Answer and settle.** The answer is classified by the same deterministic edge (steps 10-12; FG1's bundles are built for it, `followup_run/admission.py:80-84`), and `probe_answered` settles the workflow in the completion's transaction (`attempts/post_attempt.py:196-198`; `followup_serve/workflow.py:514`). A declined workflow retires its rival-causes factor (`followup_serve/workflow.py:481-491`).

### 2.3 A learner-text gap, from the learner's words to a created prerequisite or belief

1. **Sources** (`diagnosis/text_gaps/jobs.py:101-283`): a stuck answer (`:150`, from the post-attempt pipeline), a diagnosis (`:126`, from `apply_diagnosis`), a tutor question, a lesson gap, a Reader formative answer, figure predictions and explanations, hint feedback, workbench text and linked notes, each one row in `learner_text_gap_jobs` with a `job_enqueued` record.
2. **Run** (sidecar `gaps` thread; `process_next_gap_job`, `:501`): the job continues its enqueuer's trace (B7), reads the text and either resumes recorded progress or reads it afresh (`diagnosis/text_gaps/pipeline.py:889`, `:951`, `_resume` at `:589`).
3. **Kind.** The context model's reading (the tutor's, the diagnoser's or one stuck-text reader call, `diagnosis/text_gaps/judges.py:353`) and the Decider's typed choice (`:293`) are both appended to `judgment_ledger`; since Tier 1 (mvp-0.22) the Decider is authoritative and the LLM fills only what it didn't answer (`diagnosis/text_gaps/pipeline.py:18-22`; `diagnosis/text_gaps/tier1.py:266`).
4. **Match.** Candidate pairs from an embedding shortlist (`diagnosis/text_gaps/pipeline.py:411`) are judged by the LLM judge and the Decider (`:317`), with `SAME_PREREQUISITE` and `SAME_BELIEF` as the match kinds (`diagnosis/text_gaps/kinds.py:70`, `:90`). A match needs a settled verdict on every pair, else the job is retried (`diagnosis/text_gaps/pipeline.py:378-385`, docstring `:41-50`).
5. **Act** (`diagnosis/text_gaps/actions.py`): a "needed?"-gated prerequisite edge (`:161`, after `ask_needed`, `diagnosis/text_gaps/judges.py:394`); a created prerequisite concept and learning object written **[Y]** under the vault mutation lock, then `sync_vault_state` (`diagnosis/text_gaps/actions.py:256-316`); its seed item (`:320`); a belief recorded as a holding-pen candidate or sighting in the ledger row's transaction (`:377`); the sooner check (`:487`). Ids are derived from the text and recorded in the job's progress before the write (`diagnosis/text_gaps/pipeline.py:51-58`).
6. **Log.** One append-only `learner_text_gaps` row per reading (`:981`), which the router's learner-state card reads (`:1162`).

### 2.4 Recurrence groups

Inside the diagnose job, before normalization (`diagnosis/split/jobs.py:1117`; `diagnosis/recurrence/live.py:113`): materialize the attempt's hypotheses, refresh the groups, then, with embeddings on, shortlist pairs against earlier hypotheses and let the same-cause judge decide each, capped per attempt (`diagnosis/recurrence/live.py:1-14`, `:166`). The judge route is `ai.routing.same_cause_judge`, defaulting to the diagnosis route (`diagnosis/recurrence/judging.py:157-158`); verdicts are reused per producer, `model@effort` (`diagnosis/recurrence/guard.py:10-20`). Groups also merge through the diagnoser's validated citations without a judge call (`record_pattern_verdicts`, `diagnosis/split/jobs.py:1160`; `diagnosis/recurrence/guard.py:27-30`) and through the learner's "same mistake" tap (`diagnosis/split/card.py:14-18`). After normalization, `record_escalation` writes the escalation receipt when the cause recurred `ESCALATION_RECURRENCE_K` times (`diagnosis/recurrence/live.py:297`), and the deferral sweep resolves an unengaged factor as `escalated_unrepaired` (`diagnosis/causal_factor_deferral.py:436-470`).

### 2.5 VOI stopping and continuation

Two sites in diagnosis value the next observation in minutes (`diagnosis/voi_stopping.py:139-142` names four):
- **Serving an episode's item.** The sidecar's probe contract asks `probe_value_block_reason` (`diagnosis/probe_episodes.py:1577`), which replays the posterior, lists eligible instruments and calls `probe_episode_decision` (`diagnosis/voi_stopping.py:2176`); a refusal returns `value_below_minutes_cost` and the handler writes a `probe_value` record (B7). The count cap it replaced still serves when the site is off (`diagnosis/probe_episodes.py:1560-1566`).
- **Continuing an episode.** `_evaluate_completion` (`:2902`) is the stopping policy: observation budget (`:2919-2922`), action equivalence (`:2955-2956`, `:3037-3038`), the robust gate's abstention (`:2963-2967`), parking with a generation need when no instrument is left (`:2973-2981`), the value stop (`:2984-3002`, `:3040-3051`, through `_value_of_information_stop`, `:3406`), decision stability with breadth (`:3023-3024`) and the strong-claim fast path (`:3029-3034`). Each stop writes the episode's `completion_reason` and posterior (`_complete`, `:3347-3372`).
- **Follow-up value.** The follow-up gate values candidates and appends `followup_value_decisions` (`diagnosis/voi_stopping.py:2274-2319`) with a `followup_value` record.

`value_candidates` (`:996`) values with a `VoiContext` that reads latencies and triage routes from the database lazily (`:389-479`). Minutes come from the learner's own latency median, else the mode's median shrunk toward the authored minutes with three pseudo-observations, else a default (`:441-469`, `:225`).

### 2.6 A diagnostic block or episode, from entry to budget exhaustion

1. **Entry.** `enter_episode` (`diagnosis/probe_episodes.py:228`) is idempotent per learning object (`:263-286`); a new episode locks its hypothesis set from the cold-start templates (`build_episode_hypothesis_set`, `:309-322`; labels at `diagnosis/probe_hypotheses.py:31-37`) or the causal factor (`:291-307`), opens a state segment (`:352-357`), and goes `in_progress` with an eligible instrument, else `pending_items` with one generation need, enqueued for FG1's worker or generated inline (`:360-377`).
2. **Serve.** Serving gates (`:1540-1574`, `:1577-1623`), commit and serve (`:1285`, `:1517`).
3. **Answer.** Inside the attempt step (§2.1 step 10), and the block is checked for completion (`:2171-2177`).
4. **Block end** (`diagnosis/probe_blocks.py:314`), **inside the attempt step**: release withheld feedback (`:337-354`); normalize the block's joint-graded attempts, or enqueue a blind one's diagnosis (`:356-377`); resume the deferred causal hooks (`:389-401`); claim-check the feedback overlay (`:406-437`); persist beliefs, the open-set trigger and the completion policy (`:441-447`); route to tutoring, the next block or ordinary practice (`:452-465`); invalidate stale presentations and open a fresh segment (`:471-487`).
5. **Exhaustion.** `observation_budget_exhausted` when the episode's maximum binds (`diagnosis/probe_episodes.py:2919-2922`); while value decides, the maximum is lifted and the value stop ends it instead (`:2916-2918`).

### 2.7 A regrade or a held grade arriving mid-episode

- **A regrade** appends a superseding blind record and, in the same transaction, queues a `rediagnose` job (`db/stores/diagnoses.py:100-165`). The new diagnosis supersedes the old (`diagnosis/split/jobs.py:874`, `:1051-1055`) and `apply_diagnosis` runs again. The probe answer's grade interpretation is re-dual-written under the new grader identity, but "the probe observation's posterior is the submission's and is not changed here" (`diagnosis/probe_episodes.py:2437-2516`, `:2462-2463`), and the episode replay reads the outcome recorded at submission (`:2015-2025`). The discriminating observation is never reclassified: `auto_classify_pinned_probe` declines an already-observed presentation (`diagnosis/causal_orchestrator.py:2984-2989`).
- **A held grade** moves no episode posterior: the answer writes an inert observation (`diagnosis/probe_episodes.py:2573-2612`) and replay skips held attempts by the predicate (`:1907-1910`, `:1924-1927`, `:1962-1963`). A later release doesn't bring it back: replay skips any observation with `updates_belief = 0` (`:1926`), and the inert row has it (`:2600`). The discriminating channel doesn't consult the held predicate; it is protected because a route-rule hold has no assessed criterion, so the deterministic sensor supplies no feature and declines (`diagnosis/causal_orchestrator.py:2921-2926`, `:2991-2992`; `held_grades.py:10-14`). The grade-keyed hooks run on a held grade all the same (§2.1 step 4).

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9D1 | high | **One probe answer updates two beliefs over two locked sets, in two transactions, by two rules.** The episode posterior moves inside the attempt step over `enter_episode`'s set; the discriminating observation is written after the commit, against the candidate's set from commissioning, which was locked with support scores the second lock doesn't get. Nothing compares them (§3.3). | `diagnosis/probe_episodes.py:291-302`, `:2707`; `diagnosis/causal_probe_commissioning.py:669-676`; `diagnosis/causal_orchestrator.py:2430-2436`, `:2828` |
| D9D2 | high | **A regrade changes neither belief.** The episode keeps the outcome classified at submission and the discriminating observation is never reclassified, while the grade interpretation, the diagnosis and the recurrence groups all move to the new grade. A held grade that is later released never enters the episode posterior. | `diagnosis/probe_episodes.py:2462-2463`, `:1926`, `:2600`; `diagnosis/causal_orchestrator.py:2984-2989` |
| D9D3 | medium | **The discriminating channel is kept off held grades by a coincidence, not the predicate.** It reads criterion features, and a route-rule hold has no assessed criterion; the grade-keyed hooks that call it run on held grades. If the hold rule changes (the replay-only contract hold already differs), nothing here would notice. | `diagnosis/followups.py:668-696`; `diagnosis/causal_orchestrator.py:2921-2926`; `held_grades.py:10-26` |
| D9D4 | medium | **The block-end hook runs inside the attempt step.** It releases feedback, normalizes, resumes the causal hooks, claim-checks the overlay and routes, all within the step's transaction, while the post-attempt pipeline goes out of its way to normalize outside any transaction because normalization may call a model. The step passes no client (`ai_client` defaults to None), and I didn't trace whether normalization can make one. | `attempts/attempts.py:3498-3513`; `diagnosis/probe_episodes.py:2171-2177`; `diagnosis/probe_blocks.py:314-487`; `attempts/post_attempt.py:114-117` |
| D9D5 | medium | **The live per-attempt hooks still fail to a log line.** B7 gave the post-diagnosis hooks `diagnosis_step` records, but the four grade-keyed hooks (machine-check sweep, cold verification, deterministic classification, common repair) only log. A failed classification leaves the factor open with no row saying why. | `diagnosis/followups.py:853-906`; compare `:994-1003` |
| D9D6 | medium | **Where a decision runs depends on the vault's grading mode.** In a joint vault the common-repair consultation runs in the submit request; in a blind vault it runs in the diagnose thread after the diagnosis; inside a block it runs at block end, inside the attempt step. The same receipt is written from three places and three processes. | `attempts/post_attempt.py:182`; `diagnosis/followups.py:895-900`, `:967-1003`; `diagnosis/probe_blocks.py:389-401` |

## 3. Boundaries and duplicated predicates

### 3.1 Who answers each question

**"Should we probe?" — ten sites.**

| # | Site | Rule | Decides? |
|---|---|---|---|
| 1 | `decide_probe`, `diagnosis/causal_probe_coherence.py:413`, via `_status_for_factor`, `diagnosis/causal_orchestrator.py:1740` | the ladder of §2.1 step 8; margins 0.0, recent limit 2 | yes, the causal lane's offer |
| 2 | `decide_probe` again, `followup_run/router.py:128-149` | value inputs fixed at 0.0; preference, machine checks, burden and budget not passed; repair classes from `repair_class_need_for_factor`, not the orchestrator's `classify_cause_set` (`diagnosis/causal_orchestrator.py:1434`, `:1741`) | no: an `observational` field that can't say `probe_now` |
| 3 | `hard_refusal`, `followup_run/router.py:93-118` | preference ≠ `allow`, pending machine checks, episode conflict; its conflict check (`:113-117`) is a copy of the orchestrator's private `_probe_episode_conflict` (`diagnosis/causal_orchestrator.py:2007-2017`), and it orders preference before machine checks where `decide_probe` does the reverse (`diagnosis/causal_probe_coherence.py:469-480`) | yes, FG1's refusals |
| 4 | `select_lane`, `followup_run/lanes.py:60-71` | two concrete rival *hypotheses* (`:28-42`); `decide_probe` and `repair_class_need_for_factor` count distinct *repair classes*, so two rivals sharing one repair take FG1's probe lane | yes, which lane exists |
| 5 | `open_rival_causes_factor`, `diagnosis/causal_attribution.py:2225-2246` | two distinct `episode_key`s among non-retired hypotheses, and the grade not held | yes, whether FG1 opens a factor |
| 6 | the router's follow-up gate, `daily_plan/router_chooser.py:866` (`FollowupGate`) or `daily_plan/objective_chooser.py:2119` (`ObjectiveFollowupGate`) | a logged mixture over ask now, wait, no intervention | yes, FG1's timing and worth |
| 7 | the follow-up value suppression, `diagnosis/followups.py:388-410` | VOI on the follow-up slate | yes, the predecessor's insertion |
| 8 | the episode's serving and continuation: `probe_serving_block_reason` (`diagnosis/probe_episodes.py:1540`), `probe_value_block_reason` (`:1577`), `_evaluate_completion` (`:2902`) | session cap or VOI per item; seven stopping rules | yes, the episode lane |
| 9 | the scheduler's probe EIG, `scheduling/scheduler.py:3464-3477` | predictive EIG over prior entropy, else hypothesis EIG over log of the set's size, times familiarity; `eligible_instruments` orders the same candidates by information *rate* times a redundancy penalty (`diagnosis/probe_episodes.py:1019-1033`) | yes, ranking in the queue |
| 10 | the desktop, `apps/learnloop-tauri/src/screens/FeedbackScreen.tsx:1977-1990` | asks for a live repair status only when the receipt says divergent or incomplete mapping, mirroring `_consult_common_repair`'s own skip (`diagnosis/followups.py:1062-1065`) | yes, whether the offer is ever shown |

The Nov 8 map counted six. The four it didn't name are #4 and #5 (the lane and the factor, two different counts of rivals), #9 as a ranking separate from the episode's own order, and #10, a rule copied into TypeScript.

**"Is this resolved?" — nine writers of a closed state, three readers that re-derive it.**
- Factor resolved by a blind probe match (`diagnosis/causal_orchestrator.py:2821-2827`), by the learner's own cause report (`diagnosis/causal_attribution.py:3738`), by a confirmed repair (`diagnosis/causal_factor_deferral.py:217-225`), as escalated-unrepaired (`:436-470`, `:483`), or retired when FG1's question won't be asked (`followup_serve/workflow.py:481-491`).
- Misconception resolved by its posterior falling below `tau_misconception_resolved` (`diagnosis/misconceptions.py:916-944`).
- Episode completed by one of the seven rules (`diagnosis/probe_episodes.py:2902-3052`), or stopped by the learner (`:3447`).
- Machine checks closed when their obligation is gone (`diagnosis/causal_orchestrator.py:689-740`).
- Readers that decide "still open" themselves: the plan's repair lane, raw SQL over factors and learner-state hypotheses (`db/stores/daily_plans.py:319-344`); FG1's `waiting_still_valid` (`followup_serve/workflow.py:436-454`); FG1's `_abandon_if_empty`, a copy of `episode_has_observations` because "a leaf imports no domain package" (`followup_serve/workflow.py:494-506`; original `diagnosis/probe_episodes.py:383`).

**"Which factor, which case?"** Each caller takes the first of a list it built: `factors[0]` of a misconception's open factors (`diagnosis/causal_orchestrator.py:1401`; again in `cold_verification_context`, `:3054-3056`), the first factor with two rivals (`followup_run/lanes.py:63-66`), the first hypothesis of the causal episode (`diagnosis/followups.py:1066-1067`), and on the desktop `matchedMisconception.id ?? causalHypotheses[0].hypothesisId` (`apps/learnloop-tauri/src/screens/FeedbackScreen.tsx:1986-1989`). Nothing states that these firsts agree.

**"Is this the same mistake?" — seven producers of a same-cause or same-belief verdict.** Misconception normalization's registry and model match (`diagnosis/misconceptions.py:83-100`); the recurrence judge (`SAME_CAUSE`, `diagnosis/recurrence/kind.py:57`); the diagnoser's validated citations, merged at the judge's authority without a judge call (`diagnosis/split/jobs.py:1160`; `diagnosis/recurrence/guard.py:27-30`); the learner's "same mistake" tap (`diagnosis/split/card.py:14-18`, `:371`); the text-gap match kinds (`diagnosis/text_gaps/kinds.py:70`, `:90`); the guard's planted pairs (`diagnosis/recurrence/guard.py:68`); and the offline review's link judge (`diagnosis/offline_review/judge.py:314`). They share `judgment_ledger` and `MatchKind`, and recurrence and text gaps share `judge_pairs`; normalization's match is separate.

### 3.2 Parameter resolvers that look the same

`resolve_causal_probe_parameters` (`diagnosis/causal_probe_coherence.py:151-186`), `resolve_orchestrator_parameters` (`diagnosis/causal_orchestrator.py:309-340`) and `resolve_cold_probe_parameters` (`goals/certification_cold_probe.py:248-282`) are the same algorithm with different data: copy the defaults; return them with no repository or no active fitted set; for each default key, reject booleans, non-numbers, non-finite and out-of-bounds values into `invalid_keys`; return `lifecycle = "fitted"` even if every key was invalid. Each has its own dataclass with an identical `manifest()` (`diagnosis/causal_probe_coherence.py:120-148`, `diagnosis/causal_orchestrator.py:288-306`, `goals/certification_cold_probe.py:209-245`). They don't differ in behaviour, only in scope and knobs.

**Nothing writes any of the three scopes.** `learnloop fit` writes only `fsrs_weights` and `followup_gate` (`cli/fit.py:36`, `:130`), and they are the only callers of `insert_fitted_parameters` in `src`. So every fitted arm above is unreachable in production, the receipts' `"lifecycle": "heuristic_default"` is the only value they record, and `decide_probe`'s "every threshold is resolved from the fitted store" (`diagnosis/causal_probe_coherence.py:432-433`) describes a store with nothing in it. The Fable review's "the gate's margins are 0.0 and its claim to be fitted is unverified" (strategy §2.10, G2) is now verified as not fitted.

### 3.3 The two belief updates over locked hypotheses

| | Episode posterior | Discriminating observation |
|---|---|---|
| Function | `episode_posterior`, `diagnosis/probe_episodes.py:1869`; `_bayes_update`, `:2074` | `record_probe_classification`, `diagnosis/causal_orchestrator.py:2692`; `classify_against_blind_bundles`, `diagnosis/causal_probe_coherence.py:1144` |
| Locked set | the episode's, locked by `enter_episode` without support scores (`diagnosis/probe_episodes.py:291-302`, `:309-322`) | the candidate's, locked at commissioning with support scores (`diagnosis/causal_probe_commissioning.py:669-676`), pinned on the presentation (`diagnosis/causal_orchestrator.py:2235`) |
| Rule | L_w = w·L + (1−w)·Σπ(h)L(h); π′ ∝ π·L_w (`diagnosis/probe_episodes.py:2081-2094`) | exact key match to the pinned bundles; 1.0 to the matched hypothesis, 0.0 to every other *measured* one, no entry for an unmeasured one (`diagnosis/causal_orchestrator.py:2538-2562`) |
| Evidence | the instrument card's outcome likelihoods, every presentation answer and incidental attempts, damped by contamination, hints, exam type, dialogue share and trace mass (`diagnosis/probe_episodes.py:1915-1972`, `:2668-2678`) | the criterion features of the probe attempt only (`:2886-2940`) |
| Independence | a discount on the weight (`:2669`) | a refusal to admit (`diagnosis/causal_orchestrator.py:2778-2796`) |
| Held grades | the predicate, both channels (`diagnosis/probe_episodes.py:1907-1910`) | not consulted; protected by the criterion rule (§2.7) |
| When | inside the attempt step | after the commit, in the grade-keyed hooks |
| Stored | `probe_observations` (before and after), recomputed by every read | `causal_discriminating_observations`: `support_scores`, `resolved_factor` |
| Read by | the scheduler (`scheduling/scheduler.py:2754-2774`), valuation (`instructional/valuation.py:207-226`, renormalized over concrete labels), passage cues (`source_retrieval/passage_cues.py:377-417`, raw mass, not renormalized), episode completion | the eight readers in strategy §2.10 |

**Where they can disagree.** Different priors (support-weighted against verbalized or uniform), different evidence (the whole episode against one attempt's criteria), different independence rules, and a regrade that neither absorbs. A factor can be resolved by a single matched observation while the episode posterior still spreads its mass, or the episode can complete `decision_stable` on a hypothesis the discriminating channel never measured. Nothing compares them, and they don't share a set id.

### 3.4 What each boundary passes, and whether each side can change alone

| Boundary | What crosses | Change alone? |
|---|---|---|
| Attempt step → episode lane | ten arguments to `record_episode_evidence`, among them the in-flight held flag and the grader identity (`attempts/attempts.py:3500-3513`); returns the block-end payload | No: the block end runs inside the step (D9D4), and the step reads `probe_episodes` in five places (`:3069`, `:3097`, `:3382`, `:3498`, `:3655`) |
| Post-attempt pipeline → follow-ups | the `AttemptResult` plus five behaviour flags (`normalization_prepared`, `applied_probe_episode_id`, `suppress_insertion_reason`, `defer_diagnosis_hooks`, `insertion_only`; `diagnosis/followups.py:586-601`) | No: each flag is a mode the other side must know about; `insertion_only` exists for FG1's fallback (`followup_run/lanes.py:100-104`) |
| Sidecar → causal lane | `misconception_id` or `factor_id`, and `decision_receipt_id` (`learnloop_sidecar/handlers/remediation.py:159-228`) | Mostly: five functions, though the desktop copies the status mapping (`apps/learnloop-tauri/src/components/CausalAttribution.tsx:403-407` shows "You asked me not to check" for every withheld offer, while the orchestrator also withholds for recent burden and session budget, `diagnosis/causal_orchestrator.py:1875-1903`) |
| FG1 → causal lane | `factor_id`, `candidate_id`, `router_decision_id`, `followup_workflow_id` into `accept_probe_offer` (`followup_run/admission.py:421`); four private-feeling helpers into `hard_refusal` | No: `hard_refusal` re-implements the orchestrator's conflict check, and the router's card facts read `repair_class_need_for_factor` (`followup_run/router.py:157-165`) |
| Scheduler → episode lane | eleven names from `probe_episodes`, `probes.HypothesisSet` and `voi_stopping` (`scheduling/scheduler.py:26-39`, `:55`) | No: the scheduler builds its own probe ranking over the episode's entries (§3.1 #9) |
| Readers → episode posterior | `episode_posterior(vault, repository, episode)` | Yes for the signature; but each reader normalizes differently (valuation renormalizes over concrete labels, passage cues doesn't) |
| Sidecar practice → episode lane | the probe contract calls eleven functions and itself parks the episode when no grader is ready (`learnloop_sidecar/handlers/practice.py:573-581`) | No: an episode lifecycle transition lives in a handler |
| Sidecar feedback → remediation | `_pick_primed_sibling` (`learnloop_sidecar/handlers/feedback.py:1063`) re-implements `remediation._rank_items` (`diagnosis/remediation.py:437`) with a boolean facet overlap, the source item excluded and `SystemClock().now()` (`learnloop_sidecar/handlers/feedback.py:1107`) instead of the injected clock | No |

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9B1 | high | **Ten sites answer "should we probe?", and two of them count rivals differently.** FG1's lane takes two rival hypotheses; the causal lane's verdict needs two repair classes; FG1's factor needs two episode keys. A miss whose rivals share one repair goes to FG1's probe lane while the causal lane would say "action equivalent". | §3.1 #1-#10; `followup_run/lanes.py:60-71`; `diagnosis/causal_probe_coherence.py:437-468`; `diagnosis/causal_attribution.py:2239-2244` |
| D9B2 | high | **Two belief updates over two locked sets, and nothing reconciles them** (the Nov 8 map's finding, confirmed and widened: the sets differ by construction, the evidence differs, and a regrade moves neither). | §3.3; D9D1, D9D2 |
| D9B3 | high | **The probe policy's "fitted" thresholds are constants.** Three resolvers read scopes nothing writes, so `recent_diagnostic_limit = 2`, the 0.0 margins, the 0.8 success cut, the 0.1 open-set weight and the burden defaults are hand-set numbers with a fitting path that can't run. | §3.2; `cli/fit.py:36`, `:130` |
| D9B4 | medium | **Three copies of one resolver,** each with its own dataclass and manifest. (The delegated sweep also named `failure_triage.py:208` and `goals/goal_contracts.py:243`; I read both, and they share only the boolean-or-number check, not the resolver.) | §3.2 |
| D9B5 | medium | **The desktop and a handler copy backend rules.** The feedback screen's divergence gate, the "Not now" copy that is wrong for two of the three withheld-offer arms, the primed-sibling ranking with the wall clock, and the probe contract's episode parking. | §3.4; `apps/learnloop-tauri/src/components/CausalAttribution.tsx:403-407` |
| D9B6 | medium | **"Still open" is re-derived by three readers outside the package** (the plan's raw SQL, FG1's two checks), one of them a deliberate copy to keep a leaf clean. | §3.1 |
| D9B7 | medium | **"Which factor" is "the first one" at five sites,** with no rule that they pick the same. | §3.1 |
| D9B8 | medium | **Seven producers of same-cause verdicts,** one of which (normalization's match) shares no machinery with the others. | §3.1 |

## 4. Decision points and what is recorded

Records in diagnosis today: the domain receipts (`causal_probe_decision_receipts`, `causal_discriminating_observations`, `causal_probe_preference_events`, `causal_cold_verifications`, `causal_cold_outcomes`, `causal_shadow_selection_receipts`, `followup_value_decisions`, `probe_observations`, the episode row's completion fields, `learner_text_gaps`, `judgment_ledger`) and six `decision_records` kinds from `diagnosis/chain_records.py:38-43`: `diagnosis`, `diagnosis_step`, `followup_value`, `voi_forecast`, `probe_value`, `probe_offer`. Each kind has a pure builder (`*_record`, e.g. `:93`, `:195`, `:270`) that the shell calls *after* the decision, from its outputs, and a writer that never raises (`:78-87`). That is §2.18 L6's problem in this package: the builders are beside the deciders, not returned by them.

"Pure" below means callable with plain values and no database, clock or model, returning its result; "could return its record" means its inputs and alternatives are all in its arguments, so a record could come back with the result.

| Decision | Code | What answers "why x and not y" from stored rows today | Silent | Pure? Could return its record? |
|---|---|---|---|---|
| Probe verdict (`decide_probe`) | `diagnosis/causal_probe_coherence.py:413` | `causal_probe_decision_receipts`: verb, reason, inputs with EVSI provenance, both parameter manifests, candidate statuses (`diagnosis/causal_orchestrator.py:1467-1490`, `:1773-1798`) | the ladder's arms not taken; on FG1 the logged verb is meaningless (§3.1 #2) | **Pure when given `parameters`** (it otherwise resolves them from the repository, `:436`; FG1 passes the repository, `followup_run/router.py:145`). Returns a reason string, not a rule code; yes, it could return a record |
| Repair status (`_status_for_factor`) | `diagnosis/causal_orchestrator.py:1414` | the same receipt, plus the status and `RepairStatus.actions` (not stored) | why the offer was withheld (`offered` isn't a receipt column; it is inferable only from verb plus preference) | No: eleven reads, three writes |
| Common-repair consultation | `diagnosis/followups.py:1006` | the receipt it writes | **its skips** (no factor, already consulted, divergent, no misconception id: `:1037-1069`) leave nothing | No |
| Accept the offer | `diagnosis/causal_orchestrator.py:2045`, `:2077` | `probe_offer` (reason, ids) and the presentation's pin | which candidates lost (only the head is pinned) | No |
| Admit a discriminating observation | `diagnosis/causal_orchestrator.py:2692` | the observation row: outcome, admitted, `admission_reason`, measured and unmeasured ids, independence (`:2828-2874`) | nothing; but **the auto-classifier's six declines are silent** by design (`:2967-3001`, docstring `:2952-2953`), so "why wasn't this probe answer read?" has no row | Partly: `_measured_hypotheses` and `_observation_support_scores` (`:2482`, `:2538`) are pure; the admission ladder (`:2788-2796`) sits in the shell |
| Lock a hypothesis set (prior) | `diagnosis/causal_probe_coherence.py:705`, `diagnosis/probe_episodes.py:309` | `hypothesis_sets.prior_basis`, the prior | that a second lock happened with a different basis | No (reads the factor and hypotheses); the weighting (`:747-801`) could be pure |
| Probe selection (which instrument) | `eligible_instruments`, `diagnosis/probe_episodes.py:846`; scheduler ranking `scheduling/scheduler.py:3464` | the committed presentation: EIG, posterior at selection, `shadow_selection_rankings` (`diagnosis/probe_episodes.py:1166`) | instruments filtered out of eligibility; the scheduler's and the episode's rankings aren't stored side by side | No |
| Serve gate (VOI per item) | `diagnosis/probe_episodes.py:1577` | the admitted decision on the presentation; `probe_value` when refused | `probe_serving_block_reason`'s `session_cap_reached` and `onboarding_practice_ceiling` (`:1560-1573`) return a string to the caller | No |
| Episode stop | `_evaluate_completion`, `diagnosis/probe_episodes.py:2902` | `completion_reason`, the posterior and, for a value stop, the decision in `completion_detail_json` (`:3347-3372`) | the rules not taken, and "continue" (no row when the episode goes on) | No: reads observations and eligibility; the decision-stability arithmetic (`:2939-2945`) could be pure |
| VOI value | `value_candidates`, `diagnosis/voi_stopping.py:996` | `SiteDecision.as_dict()` in the receipts above | candidates beyond `MAX_RECORDED_CANDIDATES = 6` (`:220`) | **Nearly**: it takes a `VoiContext` whose properties read the database lazily (`:422-479`); with those values supplied it would be pure, and it already returns a decision dict |
| Follow-up value | `diagnosis/followups.py:388-410`, `diagnosis/voi_stopping.py:2274` | `followup_value_decisions` and `followup_value` | none found | No |
| FG1 lane | `select_lane`, `followup_run/lanes.py:60` | the workflow's `lane` and reason | which factor was skipped and why | No (reads hypotheses) |
| FG1 refusal | `hard_refusal`, `followup_run/router.py:93` | the router decision's refusals | none | No |
| Diagnosis job: live, shadow or none | `enqueue_diagnosis`, `diagnosis/split/jobs.py:112` | `job_enqueued`; `diagnosis` with `excluded` for `not_needed` (`diagnosis/chain_records.py:50-51`) | none found | No |
| Prior-analysis arm | `assign`, `diagnosis/split/prior_analysis.py:86` | the context receipt | none | **Yes**, pure (setting, attempt id); returns the arm with its probability and draw |
| Misconception resolved | `diagnosis/misconceptions.py:916` | the status and `transition_source="posterior"` (`:941-946`) | the posterior value and `tau` at the flip | No |
| Factor resolved by repair, escalation or retirement | §3.1 | `resolution_kind` and `resolution_detail` on the factor | none found | No |
| Cold check success | `diagnosis/causal_probe_coherence.py:1833`, cut at `:1912` | `causal_cold_verifications` | none found | No |
| Same cause, same belief | §3.1 | `judgment_ledger` verdicts per producer | normalization's match outcome other than the link it writes (not traced) | No |
| Text-gap kind, match, act | `diagnosis/text_gaps/pipeline.py:825`, `:889` | `judgment_ledger`, the `learner_text_gaps` row with `detail` | none found | No |
| EVSI-2 shadow | `diagnosis/causal_diagnostic_selector.py:312` | `causal_shadow_selection_receipts`, read by `causal_selection_audit.py:126` | none | No |

**The chain from a miss to its repair.** B7 links grade → `job_enqueued` → `diagnosis` → `followup_value` and `probe_offer` through one trace. What a single trace still can't answer: why the causal lane didn't offer (the receipt has no `decision_records` row, so `learnloop why attempt:<id>` reaches it only by the factor), why a probe answer wasn't classified (silent declines), and which of the two beliefs the plan and the scheduler acted on.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9O1 | high | **The causal lane's central decision has no `decision_records` row.** Its receipt is rich, but the trace reaches it only through `probe_offer`, which exists only when the learner pressed the button. A withheld offer, a deferral or a `skip_*` verb is outside the trace. | `diagnosis/causal_orchestrator.py:1467`; `diagnosis/chain_records.py:38-43` |
| D9O2 | high | **"Why wasn't this probe answer read?" has no answer.** The deterministic classifier declines in six ways and records none, and its failure is a log line (D9D5). | `diagnosis/causal_orchestrator.py:2967-3001`; `diagnosis/followups.py:885-894` |
| D9O3 | medium | **Only two deciders in the package are pure,** `decide_probe` (given parameters) and the prior-analysis arm; `value_candidates` is one context object away. The rest read the database inside the decision, so none can return its record as L6 asks without a split first. | table above |
| D9O4 | medium | **Records are built after the decision from its outputs,** so a new branch in a decider (a new verb, a new stop rule) is silently absent from its record. `decide_probe` returns prose reasons, not rule codes. | `diagnosis/chain_records.py:93-296`; `diagnosis/causal_probe_coherence.py:457-524` |
| D9O5 | medium | **Stops record only the rule that fired.** The episode's seven rules, the serve gate's two count caps and the consultation's four skips leave no row for the arms that didn't fire or for "continue". | `diagnosis/probe_episodes.py:2902-3052`, `:1560-1573`; `diagnosis/followups.py:1037-1069` |

## 5. Functional core and shell

What can be called with plain values today, and what reads the database or the clock inside.

| Piece | Code | Core or shell |
|---|---|---|
| Weighted Bayes step | `_bayes_update`, `diagnosis/probe_episodes.py:2074-2094`; `_entropy`, `:150` | **pure** |
| Episode posterior | `episode_posterior`, `:1869` | **shell**: reads the hypothesis set, observations, every attempt on the learning object, presentations, state segments and the held predicate (`:1896-1910`, `:1943-1945`, `:1985`), and is recomputed from scratch by every reader (scheduler, valuation, passage cues, completion, the serve gate) |
| Instrument likelihoods | `instrument_conditionals`, `instrument_observation_likelihoods`, `classify_outcome` (`diagnosis/probe_families.py:450`, `:505`, `:716`) | **pure** (an instrument and values) |
| Incidental likelihoods | `_incidental_likelihoods`, `diagnosis/probe_episodes.py:2049`; `generic_bucket_marginals`, `diagnosis/probe_hypotheses.py:94` | the marginals are pure; the caller reads the item, rubric and the old IRT scalar through the vault (`resolve_item_irt`, `diagnosis/probe_episodes.py:2058`), the map's X2 path |
| Causal prior | `build_causal_hypothesis_set`, `diagnosis/causal_probe_coherence.py:705` | **shell**: the weighting (`:747-801`) is inline with factor, hypothesis and parameter reads (`:725-747`) |
| Probe verdict | `decide_probe`, `:413` | **pure** given `parameters`; it falls back to a repository read otherwise (`:436`) |
| EVSI inputs | `_discrimination_inputs`, `_probe_burden_minutes`, `_avoided_overteaching_minutes`, `_recent_diagnostic_burden` (`diagnosis/causal_orchestrator.py:1115`, `:1067`, `:1014`, `:1090`) | the first is pure over a candidate row; the other three read the database |
| Separability, classification | `rows_are_separable` (`diagnosis/causal_probe_coherence.py:370`) pure; `classify_against_blind_bundles` (`:1144`) and `blind_bundle_discrimination` (`:1040`) read the bundles by id | mixed |
| Support scores | `_measured_hypotheses`, `_observation_support_scores` (`diagnosis/causal_orchestrator.py:2482`, `:2538`) | **pure**; the deterministic sensor (`:2886`) reads attempts, rubric and evidence, with a hard-coded 0.40 "passed" cut (`:2935`) |
| VOI math | `_predictive`, `_posterior`, `_normalized` (`diagnosis/voi_stopping.py:613-660`), `predictive_information` (`:1494`), `greedy_information_admission` (`:1958`), `value_candidates` (`:996`) | **pure except the context**: no repository or clock read appears between `:480` and `:2176`; `VoiContext` reads latencies with raw SQL and the triage routes lazily (`:422-479`) |
| Robust composition | `diagnosis/robust_composition.py:228`, `:600` | **pure**, seeded `random.Random(seed)`; its convention is stdlib only for bit-for-bit replay (`:24`) |
| Misconception posterior | `misconception_posterior`, `diagnosis/misconceptions.py:850` | **shell**: an odds update over persisted attempts and events; prior clamped to [0.05, 0.95] (`:841-842`, `:868`) |
| Stopping rules | `_evaluate_completion`, `diagnosis/probe_episodes.py:2902` | **shell**: reads observations, eligibility and robust gates while deciding; the stability test (`:2939-2945`) is a two-line pure predicate inside it |

**Clocks and randomness.** Diagnosis reads time through the injected `Clock`, with `SystemClock()` as the default at nine sites (`diagnosis/probes.py:120`, `diagnosis/probe_hypotheses.py:159`, `diagnosis/remediation.py:484`, `:954`, `:1305`, `diagnosis/followups.py:2048`, `:2625`, `diagnosis/causal_factor_deferral.py:389`, `diagnosis/split/jobs.py:261`); `time.monotonic` only for latency (`diagnosis/split/jobs.py:948`, `diagnosis/split/diagnoser.py:142`). Two report modules read `datetime.now` for a header (`diagnosis/split/reports.py:303`, `diagnosis/recurrence/report.py:221`). The one handler copy uses the wall clock where the original uses the injected one (`learnloop_sidecar/handlers/feedback.py:1107`). Randomness: seeded `random.Random` in robust composition, instance generation (`diagnosis/probe_instance_generation.py:640`) and offline review; the prior-analysis arm is a SHA-256 draw (`diagnosis/split/prior_analysis.py:93-95`); ids are ULIDs (23 `new_ulid()` sites), and the observation and bundle ids are content-addressed.

**Four beliefs over hypotheses, not two.** Beside the episode posterior and the discriminating support (§3.3) there are the legacy probe-phase posterior (`probes.probe_posterior`, `diagnosis/probes.py:1147`), which the follow-up gate still reads for frozen pre-redesign phases (`diagnosis/followups.py:1174-1201`), and the misconception posterior above. The router's miss-cause sensor reads a fifth view, the episode's stored posteriors mapped to causal classes with its own SQL (`router_objective/miss_cause.py:280-290`).

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9F1 | high | **The episode posterior can't be called without a database, and every reader recomputes it from the whole learning object's history.** The Bayes step under it is pure; the replay that gathers its inputs is the shell, and five readers each run it and then normalize differently. | `diagnosis/probe_episodes.py:1869-1981`; §3.3 |
| D9F2 | medium | **The stopping policy decides while it reads.** Seven rules interleave database reads, the robust gate and eligibility, so no rule can be tested with literals. | `diagnosis/probe_episodes.py:2902-3052` |
| D9F3 | medium | **VOI is one object away from a functional core.** `VoiContext` mixes the settings, the minutes model and the loss tables with lazy raw SQL; supplied as values, `value_candidates` and the site functions would be pure. | `diagnosis/voi_stopping.py:389-479`, `:996` |
| D9F4 | medium | **Hand-set numbers in the likelihood path:** the deterministic sensor's 0.40 "passed" cut, a rubric maximum of 4 when an item is missing (`diagnosis/probe_episodes.py:2041-2046`; again `diagnosis/probe_blocks.py:350`), the misconception prior's [0.05, 0.95] clamp, and the "fitted" probe policy that nothing fits (D9B3). | `diagnosis/causal_orchestrator.py:2935`; `diagnosis/misconceptions.py:841-842`, `:868` |
| D9F5 | medium | **Four beliefs over hypotheses** (episode, discriminating, legacy probe phase, misconception) and a fifth reader's view; strategy G3-G4 names two. | above |

## 6. Comments, dead code, onboarding

### 6.1 Comments

The package has 4,087 comment lines. A regex for review-round and stage names (`review F\d`, `re-review`, `fix round`, `round \d`, `ruling`, `Codex`, `owner batch`, `U-0\d\d`) matches 269 comment and docstring lines in 51 of the 110 modules (most: `text_gaps/jobs.py` 23, `voi_stopping.py`, `text_gaps/pipeline.py` and `probe_episodes.py` 17 each); `mvp-0.N` appears 131 times. Examples that name a round instead of saying what breaks: `diagnosis/split/jobs.py:844-846` ("codex re-review F3"), `:892` ("review F12"), `:938-940` ("RW2b fix round 14, item 3"), `:1111` ("review F3"); `diagnosis/probe_episodes.py:2756` ("TE2 landing ruling R1 (the re-review's open question)"); `diagnosis/causal_orchestrator.py:2027-2028`, `:2154`, `:2251`, `:2290-2291` ("UX Phase 4 round 7"); `diagnosis/followups.py:952` ("Codex review F8"). Most of these also say the why beside the tag, so the cost is noise, not missing reasons.

**Why-comments that are the model** (strategy §2.1's convention): `diagnosis/causal_orchestrator.py:2199-2202` (accepting twice would strand a pin), `:2229-2231` (why the pin is nested under one key), `:2778-2783` (independence before admission); `diagnosis/probe_episodes.py:1951-1956` (the in-flight response counted twice), `:2713-2714` (signed information gain); the module docstrings of `causal_orchestrator` (`:1-99`), `probe_blocks` (`:1-19`), `text_gaps.pipeline` (`:1-58`) and `recurrence.live` (`:1-31`).

**Long functions without an approach header:** `_status_for_factor` (517 lines, no docstring; the approach is in the module docstring's table), `_record_presentation_observation` (260, no docstring, `diagnosis/probe_episodes.py:2519-2535`), `_evaluate_completion` (151, seven rules, no docstring, `:2902-2911`).

**Docstrings the code contradicts:**
- `record_probe_classification` says validator-owned support "unlocks the §2.1 `causal_authority` promotion arm in `failure_triage`" (`diagnosis/causal_orchestrator.py:2736-2738`); `failure_triage` has no caller (§6.2).
- `decide_probe` says "every threshold is resolved from the fitted store" (`diagnosis/causal_probe_coherence.py:432-433`); nothing writes the store (§3.2).
- The orchestrator's module docstring calls the discriminating observation "the ONLY channel through which diagnosis support may move" (`diagnosis/causal_orchestrator.py:15-16`); a learner's self-report resolves a factor too (`diagnosis/causal_attribution.py:3738`), and the episode posterior moves independently.

### 6.2 Dead and near-dead code

- **`failure_triage.py`** (1,054 lines). Deletion-proof checks (strategy §2.1), delegated and spot-checked:
  - static imports, function-local included, in `src`, `apps`, `scripts`: none;
  - string dispatch: **yes** — `MODULE_INVENTORY["failure_triage"]` (`params/parameter_registry.py:127`) becomes `MODULE_IMPORTS` (`:296-299`), and `refresh` (`:3231`) imports it through `importlib.import_module` (`:3099`) to resolve its three registered constants (`:1136-1141`); `refresh` runs in the `registry` CLI, in 48 upgrade call sites and, through `figure_wait_upgrade.complete_interrupted_activation`, at sidecar vault open (`learnloop_sidecar/context.py:825-827`). No `METHOD_REGISTRY` entry, Typer command or TUI path names it;
  - frontend callers: none;
  - replay and rebuild: `rebuild_orchestrator`, `shadow_rebuild` and `doctor` don't reach it;
  - its public functions `triage`, `decide`, `override`, `triage_status` have no caller in `src`;
  - five `Repository` methods carry its name, not one: `failure_triage_routes` and `failure_triage_route_for_reason` are live (read by `voi_stopping.py:476`, `causal_probe_coherence.py:597`, `voi_forecasting.py:75`, `probe_episodes.py:3158`; the routes are seeded by `migrations/083_diagnostic_pack_and_triage.sql:149`), `failure_triage_events_for` is read by `causal_health.py:327`, and `append_failure_triage_event` (`db/repositories.py:24535`) and `failure_triage_event` (`:24621`) are used only by the module;
  - tests: five files import it, eight name it.

  **So the audit's "no importer" is wrong in letter and right in effect:** removing the module also needs its three registry entries removed in the same commit, or `refresh` fails on import (inferred from `:3099`, not run). The table it writes (`failure_triage_events`) is still read by `causal_health`, so the module is the table's only writer.
- **The legacy probe-phase posterior** (`probes.probe_posterior`, `diagnosis/probes.py:1147`) "serves only frozen pre-redesign phases" (`diagnosis/followups.py:1174-1175`), and `record_probe_attempt` is "kept only for pre-redesign replay" (`attempts/attempts.py:3494-3496`). Legacy-only, still read.
- **14 CLI-only report modules** (§1.3) are tooling, not dead; each has a CLI command and tests.
- **The EVSI-2 shadow selector** (`causal_diagnostic_selector.py`, 671 lines) has zero live authority (`diagnosis/causal_orchestrator.py:1491-1494`); its receipts are read by `causal_selection_audit.py:126` for the measurement-health screen. Live, as a report.

### 6.3 What a new contributor must read to add a thing

| Add | Read and edit today | Why so many |
|---|---|---|
| (a) an episode hypothesis label | `probe_hypotheses.py:31-37` (label), `:45-53` (triage reason), `:94` (generic marginals), the template builder; `probe_families.py:807-892` (family rows naming labels); `voi_stopping.py:360-369` (the unresolved-cost label sets); `probe_blocks.py:459` (a literal `"robust_initial_grasp"`); `curriculum/depth_rungs.py:337-338`; a new triage reason also needs migration 083's CHECK widened (`migrations/083_diagnostic_pack_and_triage.sql:99-103`) | the label vocabulary is restated as string literals in five modules |
| (a′) a causal hypothesis kind | `causal_attribution._hypothesis_specs` (`:1649`), repair classes and `probe_targeting.classify_cause_set`, `causal_probe_coherence` (prior, bundles), `followup_run/lanes.concrete_rivals` | two vocabularies meet (`diagnosis/causal_probe_coherence.py:713-722` says so) |
| (b) a probe instrument | a family in `probe_families.py` and its admission gate (`:1521`), `probe_instance_generation.py`, the card and compile path in `probe_episodes.resolve_instrument` (`:1037`); for a causal instrument also commissioning (`causal_probe_commissioning.py:383`), blind bundles, the manipulation audit (`causal_probe_coherence.py:1400`) and the review ladder (`:47`); for FG1, `followup_run/admission.py` and `authoring.py`; registry entries for any new module constant | the instrument is defined in the family, compiled in the episode, and commissioned in the causal lane |
| (c) a stopping rule | `_evaluate_completion` (`probe_episodes.py:2902`), the `completion_reason` CHECK (`migrations/200_probe_value_of_information_stop.sql:36-50`, so a migration and the head fixture), a version gate and kill switch if it changes behaviour, and the serve gate if it applies per item | rules are positional `if`s in one function; the vocabulary is a CHECK |
| (d) a text-gap judge or source kind | `text_gaps/judges.py` (prompt, executor, caps `:85`), `tier1.py` (Decider), `pipeline.py` (`_judge_all`, `_pair_authority`, `:317`, `:365`), `kinds.py` (match kinds), `sources.py` and `contract.py` for a source kind, `jobs.py` (enqueue), and the `source_kind` CHECK (`migrations/212_hint_feedback_source_kind.sql:27`; again in 231) | the source vocabulary is a CHECK, and authority is split across three modules |

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9C1 | high | **Three docstrings at the centre of the causal lane are false:** the support channel isn't the only one, the thresholds aren't fitted, and the promotion arm it names has no caller. Each sends a reader to the wrong place. | §6.1 |
| D9C2 | medium | **`failure_triage` is dead code that the registry imports at run time,** and the only writer of a table another module reads. A deletion that follows imports breaks `refresh`. | §6.2 |
| D9C3 | medium | **The hypothesis label vocabulary is restated as literals in five modules,** and the stop and source vocabularies are SQL CHECKs, so adding one is a migration. | §6.3 |
| D9C4 | medium | **The three longest decision functions start with no approach paragraph;** two have no docstring at all. | §6.1 |
| D9C5 | low | 269 comment and docstring lines name review rounds or rulings, mostly beside a real reason. | §6.1 |

## 7. Change cost, counted

**Activity.** Since Oct 12, 170 non-merge commits touched `src/learnloop/diagnosis` (207 with merges) of 3,414 (3,669); the brief's 171 is one more, a date-boundary difference. 157 non-merge commits touched `params/parameter_registry.py`; 24 touched both. Most-changed files: `text_gaps/sources.py` 27, `text_gaps/jobs.py` 26, `probe_episodes.py` 25, `text_gaps/pipeline.py` 21, `text_gaps/provenance.py` 17, `split/jobs.py` and `causal_orchestrator.py` 16 each (delegated; the commit counts I reran with `git log --since=2026-10-12 [--no-merges] -- <path>`).

**Real changes.** Files per commit, counted with `git show --name-only` (I reran the eight marked ✓; the others are the delegated sweep's). "Pin" is the head fixture (`fixtures/migration_head/`), `*_upgrade.py`, successor and upgrade tests, `config/template.py`'s digests and the CLI snapshots; "notes" are generated vault notes, which before mid-October rewrote every module note's commit stamp on each regeneration.

| Kind | Commit | diagnosis | other `src` | tests | pin and fixture | notes | total |
|---|---|---:|---:|---:|---:|---:|---:|
| (a) hypothesis kind: a new factor shape from rival causes (no episode label has been added since the Aug 20 squash) | `7d730fa39d` ✓ | 2 | 4 (`followup_run`, `followup_serve`) | 4 | 0 | 0 | 10 |
| (a) the open-set arm kept on old factors | `8a6a50b24f` | 1 | 1 | 2 | 0 | 0 | 4 |
| (b) probe instrument: FG1's generated probe, commissioning and admission | `e444e25dd0` ✓ | 6 | 8 (a route, a disclosure, a switch, four `followup_run` modules, the workflow) | 3 | 0 (moved later) | 0 | 17 |
| (b) the whole FG1 stage, `mvp-0.45`, migration 241 (net diff of 46 commits) | `bdfa849256^..d9c19b3bc4` | 11 | 53 | 25 behaviour + 47 pin-like | 50 | 623 | 834 |
| (c) stopping rule: VOI lifts four caps, `mvp-0.17` | `82a50f4121` ✓ | 4 | 14 (scheduler, plan engine and lanes, router log, registry, schema, versions, CLI, `Repository`, TUI, sidecar) | 9 | 7 upgrade files and `template.py` | 355 (stamps only) | 385 |
| (c) a value stop ends the episode, migration 187 | `bc756e53d6` ✓ | 3 | 4 | 14 | 24 fixture + 8 upgrade | 353 | 403 |
| (c) EVSI study ranks 1-3 behind switches | `17819ec036` ✓ | 2 | 5 (incl. registry +12 lines) | 3 | `template.py` | 0 | 11 |
| (d) text-gap judge: the Decider decides Tier 1, new `tier1.py` | `877ad6d3f8` ✓ | 8 | 7 (every other Tier-1 caller) | 1 | 0 | 0 | 16 |
| (d) a source kind, `hint_feedback`, migration 212 | `c3089b99ea` ✓ | 6 | 1 | 32 (about two thirds pin-like) | 24 fixture + 15 upgrade | 0 | 65 |
| (d) a source kind, `learner_note`, migration 231 | `ad2c282a43` ✓ | 5 | 7 | 48 | 24 fixture + 15 upgrade | 0 | 89 |
| (e) registry: three `_reg_const`s for VOI constants | `6e55832891` ✓ | 5 | 5 | 1 | 0 | 0 | 15 (3 in `apps/`) |

**What the counts say.** A diagnosis change with no migration and no successor costs 4-17 files, of which 1-8 are in diagnosis and 4-8 are callers in `followup_run`, `scheduling`, `daily_plan` and the sidecar. A migration adds the 24-file head fixture and 15 upgrade tests (strategy arc D addresses it). A successor adds `template.py`, an upgrade module and about 7-30 pinned tests; TE2's review records "the 69 version-pinned test files ... 44 failed (the pins)" (`docs/reviews/teacher-te2.md:199`), and `docs/reviews/voi-stopping.md:147-183` that every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was recomputed. Generated notes once added 350 files per change; since the commit-stamp change (arc A) a regeneration touches about a dozen (delegated, not rerun). The vocabularies in SQL CHECKs (§6.3) are why a new source kind or stop reason is a migration.

### 7.1 The parameter registry as a cost

- **Shape** (`params/parameter_registry.py`, 3,565 lines): one `ParameterSpec` per entry (`:74-91`) in a module-level `REGISTRY` (`:94`); `MODULE_INVENTORY` names 96 modules, nine of them diagnosis (`:106-292`); `_reg_const` registers a module constant (`:302-327`); 172 `_ConfigRule`s classify config leaves (`:1562-2945`, first match wins, with a frozen catch-all).
- **`_reg_const` entries: 381** (`grep -c '^_reg_const('`), 127 `decision` and 254 `structural`, all with the default status `heuristic` (an AST count of the calls). **39 name diagnosis modules** (25 decision, 14 structural): `voi_stopping` 10, `robust_composition` 8, `contrast_pairs` 5, `probe_families` 4, `discrimination_profiles` 4, `failure_triage` 3, `error_hunt` 2, `diagnostic_pack` 2, `probe_episodes` 1. `text_gaps`, `causal_orchestrator`, `causal_probe_coherence` and `followups` aren't in the inventory, so their constants (the 0.40 sensor cut, `EXAM_SITTING_INTERVENTION_CAP`, the resolvers' defaults) aren't registered at all.
- **What an entry buys.** Metadata: a kind, a class, an owner, a rationale and a promotion gate. Its value is whatever the module says: `refresh` resolves it by importing the module and reading the attribute (`:3089-3106`, `:3231`), and writes a per-vault projection (`parameter_registry` rows) with a value hash and a demotion rule. `source_of_value` is `"module_constant"` on both branches of its conditional (`:323`). **All 381 are constants nothing varies at run time:** no `_reg_const` value is read from the projection by the code that uses the constant, and only two `record_bind` call sites exist, both in scheduling (`scheduling/constraint_engine.py:358`, `scheduling/randomization_layer.py:176`). 11 entries carry a `bind_site`.
- **Who reads the registry at run time:** upgrades (`freeze_manifest` and `refresh` in 46 upgrade modules, including `diagnosis/recurrence/upgrade.py`), the `learnloop registry` CLI, the sidecar's interrupted-activation recovery at vault open (`learnloop_sidecar/context.py:825-827`), the controller snapshot's manifest hash of three scheduling owners, and sensitivity certificates (delegated; the first three spot-checked). No diagnosis module reads a value from it.
- **What a diagnosis change pays.** A new numeric constant in an inventory module must get a `_reg_const` or `tests/test_registry_audit.py` fails; a new numeric config leaf must match a `_ConfigRule`; deleting a module must delete its entries or `tests/test_architecture.py`'s resolution check fails (delegated: `:633-639`). The identity pin B9 hashes only the three controller owners' entries, so diagnosis entries move no golden (delegated). In the counted commits the registry was one file of 11-15 and a few lines each; its cost is the rule that a constant in nine diagnosis modules can't be added without it, and the false impression that the 25 diagnosis "decision" constants are calibrated.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9H1 | high | **A behaviour change in diagnosis pays the release machinery, not the diagnosis edit.** Five of the ten counted changes touched 1-8 diagnosis files and 65-834 files in all, the rest pins, fixtures, upgrade tests and notes. | table above |
| D9H2 | medium | **A diagnosis change edits 4-8 callers outside the package** (FG1, scheduler, plan engine, sidecar handlers), because the boundaries pass modes and private helpers (§3.4). | `e444e25dd0`, `82a50f4121`, `877ad6d3f8` |
| D9H3 | medium | **The registry describes 381 constants as parameters, all heuristic and none read back,** and covers 9 of 110 diagnosis modules. It buys an audit trail of names and a test that forces new constants into it; it doesn't make any of them vary. | §7.1; `params/parameter_registry.py:302-327`, `:3089-3106` |
| D9H4 | medium | **Stop reasons and gap source kinds live in SQL CHECKs,** so each new one is a migration with the head fixture's 24 files and about 15 upgrade tests. | `migrations/200_probe_value_of_information_stop.sql:36-50`; `migrations/212_hint_feedback_source_kind.sql:27`; `c3089b99ea`, `ad2c282a43` |

## 8. The vault notes for diagnosis

Delegated (read and grep only); each verdict below was spot-checked at the cited note line.

| Note | Verdict | Evidence |
|---|---|---|
| `Concepts/Diagnosis and Remediation.md` | **stale**: `implementation_version: mvp-0.9` (`:8`); its state diagram has states `concentrated` and `burden_stop` (`:33-37`) that exist nowhere in `src`, where `action_equivalent` and the value stop are completion *reasons* (`migrations/200_probe_value_of_information_stop.sql:36-50`) and the statuses are `pending_items`, `in_progress`, `complete`, `abandoned`, `converted_to_tutoring`; it predates blind grading, recurrence, text gaps, VOI stopping, FG1 and the records, and names no decider and no second belief | |
| `Concepts/Algorithm Versions and Reproducibility.md` | **partly stale**: the table stops at `mvp-0.34` and says LATEST is `mvp-0.34` "today" (`:58`, `:60`); missing FG1 (`mvp-0.45`), teacher and phone probes, slip or gap (`mvp-0.57`) | |
| `Maps/LearnLoop Pipeline Map.md` | **partly stale**: LATEST at `mvp-0.27` (`:105`); FG1's follow-up described as a mid-block `plan_interrupt` (delegated, `:230`), not the itemless gate with refusals | |
| `Architecture/Architecture Overview.md:83` | **partly stale**: "Diagnosis owns hypotheses, probes, ... remediation", while FG1's probes live in `followup_run` and `followup_serve` | |
| `Workflows/Inspect Persistent State.md:186` | **true, one omission**: lists four failed `diagnosis_step`s; the code has five (`causal_shadow_selection`, `diagnosis/causal_orchestrator.py:1513`) | |
| `Concepts/Attempt Processing.md`, `Workflows/Process Model Output.md` | **partly stale** (delegated): the joint-grading completion only; no blind path | |
| ADR-016 (blind grading) | **true** (delegated) | |
| ADR-017 | **true** for diagnosis; `diagnosis/chain_records.py` isn't in its `source_paths` | |
| `Reference/Modules/learnloop/diagnosis/` | **complete**: 110 notes and five package maps; but every diagnosis module note lists `concepts: ["Learning System"]`, because the generator maps the package there (`_scripts/module_generate.py:136`), so none links to the diagnosis concept note | |

**Missing notes** (no hand-written note explains them; delegated grep for each name returned nothing in Architecture, Concepts, Workflows, Examples, Maps, Decisions): who decides whether to probe and FG1's lane (no ADR for "the router decides, `decide_probe` logs"); the discriminating observation and the two (four) beliefs; VOI stopping; recurrence groups; learner-text gaps; diagnostic blocks and the block-end hook; calibration sessions; guided redo; offline review; the diagnosis reports and `diagnose` CLI; hypothesis marks; machine checks, commissioning, failure triage and the scoreboard.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D9V1 | high | **The one diagnosis concept note describes August's system** and names states that don't exist; a reader starting there won't find the decider, the second belief, the split or FG1. | above |
| D9V2 | high | **No note explains who decides whether to probe, or the beliefs over hypotheses** — the two questions arc G changes. | above |
| D9V3 | medium | **The version notes stop at `mvp-0.27` and `mvp-0.34`,** and the generated module notes all point at "Learning System". | above |

## Possible bugs found (for the ledger)

The rules ask for a row in `docs/reviews/refactor-bug-ledger.md` per bug found; this step's brief limits its output to this document, so the candidates are listed here for the orchestrator to file.

| Candidate | Where | What |
|---|---|---|
| K9-1 | `apps/learnloop-tauri/src/components/CausalAttribution.tsx:403-407` | "You asked me not to check again for now" is shown for every withheld offer, but the orchestrator also withholds it for recent burden and the session budget (`diagnosis/causal_orchestrator.py:1875-1903`), when the learner asked nothing. Learner-visible wrong copy. |
| K9-2 | `learnloop_sidecar/handlers/feedback.py:1107` | The primed-sibling ranking reads `SystemClock().now()` instead of the injected clock its original uses (`diagnosis/remediation.py:437`), so a frozen-clock test or replay sees wall time. |
| K9-3 | `diagnosis/probe_episodes.py:1926`, `:2600` | A probe answer whose grade was held and is later released never enters the episode posterior (its observation keeps `updates_belief = 0`). Intent not established; may be by design. |
| K9-4 | `diagnosis/causal_orchestrator.py:15-16`, `:2736-2738`; `diagnosis/causal_probe_coherence.py:432-433` | Three docstrings the code contradicts (D9C1). |

## Not verified

- **Nothing was run** except the AST sweep and `git log`/`git show`. The import graph is static: three string imports (§1.3) were found by grep, and others could exist.
- **Delegated and only partly spot-checked:** the frontend survey (I read `FeedbackScreen.tsx:1975-1992` and `CausalAttribution.tsx:400-408`; the polling intervals, `FollowupPanel.tsx`, `PracticeScreen.tsx` and the TS `tauFollowupNats` default were not read); the sidecar handler table beyond `remediation.py:1-20`, `practice.py:573-581` and `feedback.py:1063-1131`; the phone allowlist; the registry's run-time readers other than `refresh` and the projection readers; `tests/test_registry_audit.py` and `tests/test_architecture.py:633-639`; the B9 identity pin's scope; the FG1 stage total (`bdfa849256^..d9c19b3bc4`), `fe4440d3c7` and `8a6a50b24f`; the vault notes' verdicts for `Attempt Processing`, `Process Model Output`, ADR-016 and the Pipeline Map's `:230`; the "missing notes" greps.
- **Not traced:** whether normalization can create a model client when the attempt step's block end passes none (D9D4); what normalization's misconception match records; `router_objective/miss_cause.py` beyond `:280-290`; `probe_dialogue`, `calibration_sessions`, `guided_redo`, `quick_check`, `error_hunt`, `contrast_pairs`, `scoreboard`, `offline_review` (sizes and imports only); `causal_attribution.py` beyond the lines cited.
- **Interpretation:** "hypothesis kind" in §6.3 and §7 is read two ways (an episode label, a causal factor shape); no episode label has been added since the Aug 20 squash, so (a)'s counts are the nearest real changes. The pin-like split of test files in the delegated counts is a regex heuristic.
- **No data:** no vault or backup was opened, so how often the two beliefs disagree, how often the classifier declines, and whether any fitted set exists in a real vault (the code says none can be written) are unmeasured.

## Appendix A: every module in diagnosis, classified

Replaces the Nov 8 map's Appendix A rows for `learnloop.diagnosis`. "Importers" count modules, outside and inside the package; "imports" counts `src` modules imported; reach is from the sidecar, phone host and MCP server by static imports (§1.3). Module names drop `learnloop.diagnosis.`.

| module | raw | code | public | importers outside | importers inside | imports | longest fn | class | reach |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `__init__` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | init | serving |
| `ai_contracts` | 396 | 321 | 25 | 3 | 4 | 3 | 33 | wide | serving |
| `calibration_sessions` | 391 | 274 | 8 | 3 | 3 | 9 | 116 | deep | serving |
| `causal_activity_policy` | 407 | 220 | 8 | 7 | 3 | 3 | 56 | medium | serving |
| `causal_attribution` | 3780 | 2929 | 23 | 13 | 14 | 15 | 357 | deep | serving |
| `causal_diagnostic_selector` | 671 | 507 | 5 | 1 | 2 | 8 | 360 | deep | serving |
| `causal_factor_deferral` | 499 | 308 | 2 | 0 | 4 | 3 | 142 | deep | serving |
| `causal_health` | 359 | 255 | 3 | 2 | 0 | 3 | 156 | deep | serving |
| `causal_orchestrator` | 3471 | 2440 | 35 | 7 | 2 | 18 | 517 | wide | serving |
| `causal_probe_coherence` | 2010 | 1572 | 28 | 6 | 9 | 10 | 183 | deep | serving |
| `causal_probe_commissioning` | 759 | 522 | 8 | 2 | 0 | 4 | 342 | deep | serving |
| `causal_selection_audit` | 228 | 189 | 1 | 2 | 0 | 5 | 169 | medium | serving |
| `chain_records` | 296 | 195 | 12 | 1 | 4 | 2 | 44 | medium | serving |
| `contrast_pairs` | 1043 | 611 | 18 | 5 | 0 | 10 | 155 | medium | serving |
| `diagnosis_adjudication` | 865 | 625 | 9 | 2 | 3 | 5 | 156 | deep | serving |
| `diagnostic_augmentation` | 1243 | 1019 | 16 | 3 | 3 | 13 | 176 | deep | serving |
| `diagnostic_gate` | 514 | 363 | 6 | 6 | 3 | 6 | 146 | deep | serving |
| `diagnostic_pack` | 501 | 344 | 12 | 2 | 0 | 5 | 88 | medium | serving |
| `diagnostic_surface_supply` | 494 | 301 | 7 | 2 | 0 | 12 | 108 | deep | serving |
| `discrimination_profiles` | 571 | 274 | 11 | 5 | 1 | 3 | 114 | medium | serving |
| `error_hunt` | 728 | 407 | 9 | 4 | 0 | 11 | 120 | deep | serving |
| `error_taxonomy` | 107 | 88 | 1 | 2 | 0 | 5 | 66 | medium | serving |
| `error_taxonomy_map` | 266 | 148 | 2 | 5 | 3 | 0 | 30 | medium | serving |
| `failure_triage` | 1054 | 751 | 8 | 0 | 0 | 6 | 142 | deep | none |
| `followups` | 2626 | 2020 | 16 | 8 | 2 | 30 | 389 | deep | serving |
| `forecast_receipts` | 610 | 435 | 7 | 1 | 2 | 8 | 130 | deep | serving |
| `gate_fit` | 206 | 156 | 5 | 1 | 0 | 5 | 66 | medium | tooling-only |
| `gate_score` | 337 | 235 | 6 | 1 | 2 | 4 | 52 | medium | serving |
| `grading_hardcases` | 930 | 662 | 10 | 1 | 0 | 16 | 224 | deep | tooling-only |
| `guided_redo` | 354 | 218 | 6 | 3 | 2 | 6 | 82 | medium | serving |
| `longform_trace` | 276 | 190 | 7 | 0 | 1 | 0 | 80 | medium | serving |
| `misconceptions` | 998 | 650 | 9 | 2 | 8 | 16 | 144 | deep | serving |
| `missing_vocabulary` | 465 | 333 | 6 | 3 | 1 | 5 | 79 | deep | serving |
| `offline_review` | 16 | 0 | 0 | 0 | 0 | 0 | 0 | init | serving |
| `offline_review.decider_links` | 83 | 51 | 3 | 0 | 1 | 3 | 35 | shallow | serving |
| `offline_review.judge` | 376 | 272 | 28 | 0 | 5 | 3 | 34 | wide | serving |
| `offline_review.links` | 132 | 109 | 1 | 1 | 0 | 8 | 89 | medium | tooling-only |
| `offline_review.planted` | 471 | 384 | 13 | 0 | 1 | 8 | 49 | medium | serving |
| `offline_review.probes` | 289 | 193 | 12 | 0 | 2 | 6 | 43 | medium | serving |
| `offline_review.report` | 1068 | 937 | 8 | 1 | 4 | 5 | 107 | deep | tooling-only |
| `offline_review.runner` | 1980 | 1683 | 21 | 1 | 5 | 37 | 132 | deep | serving |
| `offline_review.spend` | 6 | 1 | 0 | 5 | 9 | 1 | 0 | shallow | serving |
| `offline_review.spot_check` | 482 | 381 | 9 | 1 | 1 | 10 | 144 | deep | tooling-only |
| `predictive_eig` | 231 | 170 | 4 | 0 | 1 | 4 | 86 | medium | serving |
| `probe_audit` | 727 | 562 | 13 | 2 | 1 | 7 | 117 | deep | tooling-only |
| `probe_blocks` | 499 | 355 | 5 | 1 | 2 | 12 | 186 | deep | serving |
| `probe_coverage` | 174 | 144 | 1 | 1 | 0 | 4 | 140 | medium | tooling-only |
| `probe_dialogue` | 464 | 362 | 8 | 1 | 0 | 15 | 165 | deep | serving |
| `probe_episodes` | 3651 | 2612 | 46 | 11 | 10 | 36 | 260 | wide | serving |
| `probe_families` | 1793 | 1454 | 24 | 6 | 11 | 3 | 101 | deep | serving |
| `probe_hypotheses` | 273 | 182 | 7 | 3 | 11 | 7 | 102 | medium | serving |
| `probe_instance_generation` | 1532 | 1191 | 17 | 7 | 4 | 16 | 195 | deep | serving |
| `probe_lifecycle` | 271 | 213 | 8 | 1 | 0 | 5 | 80 | medium | tooling-only |
| `probe_outcome_mapping` | 178 | 98 | 5 | 0 | 2 | 2 | 23 | medium | serving |
| `probe_remint` | 326 | 183 | 5 | 1 | 0 | 8 | 102 | medium | serving |
| `probe_robust` | 309 | 207 | 9 | 3 | 2 | 10 | 43 | medium | serving |
| `probe_targeting` | 860 | 577 | 15 | 0 | 2 | 5 | 123 | medium | serving |
| `probes` | 1571 | 1181 | 22 | 9 | 7 | 7 | 137 | deep | serving |
| `quick_check` | 432 | 335 | 4 | 2 | 0 | 15 | 73 | deep | serving |
| `recurrence` | 14 | 0 | 0 | 0 | 0 | 0 | 0 | init | serving |
| `recurrence.backlog` | 280 | 225 | 4 | 1 | 3 | 15 | 82 | medium | serving |
| `recurrence.benchmarks` | 1379 | 1028 | 26 | 1 | 0 | 19 | 82 | medium | tooling-only |
| `recurrence.display` | 83 | 44 | 5 | 2 | 3 | 0 | 16 | medium | serving |
| `recurrence.escalation` | 179 | 130 | 5 | 0 | 2 | 5 | 43 | medium | serving |
| `recurrence.guard` | 721 | 563 | 15 | 1 | 2 | 18 | 113 | medium | serving |
| `recurrence.judging` | 326 | 203 | 19 | 2 | 7 | 18 | 48 | medium | serving |
| `recurrence.kind` | 184 | 145 | 4 | 0 | 6 | 4 | 66 | medium | serving |
| `recurrence.live` | 530 | 401 | 7 | 0 | 1 | 19 | 118 | deep | serving |
| `recurrence.report` | 295 | 241 | 2 | 1 | 0 | 6 | 52 | medium | tooling-only |
| `recurrence.upgrade` | 217 | 141 | 3 | 2 | 0 | 13 | 54 | medium | serving |
| `remediation` | 1484 | 1020 | 19 | 11 | 4 | 16 | 281 | deep | serving |
| `repair_splice` | 279 | 158 | 7 | 1 | 0 | 1 | 47 | medium | serving |
| `robust_composition` | 607 | 396 | 14 | 10 | 4 | 1 | 91 | medium | serving |
| `scoreboard` | 1833 | 1213 | 17 | 4 | 3 | 16 | 122 | deep | serving |
| `signal_quantiles` | 141 | 105 | 2 | 0 | 2 | 3 | 56 | medium | serving |
| `split` | 18 | 0 | 0 | 0 | 0 | 0 | 0 | init | serving |
| `split.card` | 482 | 373 | 8 | 3 | 0 | 12 | 72 | deep | serving |
| `split.context` | 1030 | 797 | 19 | 1 | 8 | 10 | 290 | deep | serving |
| `split.contract` | 350 | 262 | 16 | 1 | 4 | 8 | 21 | medium | serving |
| `split.diagnoser` | 250 | 197 | 4 | 1 | 2 | 11 | 140 | medium | serving |
| `split.embeddings` | 416 | 323 | 12 | 1 | 7 | 12 | 98 | medium | serving |
| `split.figure_trace` | 145 | 99 | 1 | 0 | 3 | 3 | 83 | medium | serving |
| `split.history` | 1423 | 1058 | 12 | 1 | 9 | 13 | 297 | deep | serving |
| `split.jobs` | 1732 | 1291 | 22 | 12 | 7 | 40 | 235 | deep | serving |
| `split.legacy_view` | 214 | 174 | 3 | 0 | 3 | 2 | 35 | medium | serving |
| `split.live` | 499 | 351 | 11 | 2 | 6 | 19 | 83 | medium | serving |
| `split.pfc_report` | 437 | 379 | 6 | 1 | 0 | 14 | 110 | deep | tooling-only |
| `split.prior_analysis` | 189 | 116 | 7 | 0 | 3 | 3 | 50 | medium | serving |
| `split.provenance` | 619 | 378 | 17 | 0 | 4 | 2 | 63 | medium | serving |
| `split.reports` | 349 | 293 | 2 | 1 | 0 | 6 | 85 | deep | tooling-only |
| `split.retrieval` | 400 | 319 | 8 | 0 | 5 | 6 | 86 | deep | serving |
| `split.settings` | 71 | 49 | 2 | 1 | 8 | 0 | 19 | medium | serving |
| `split.snapshot` | 380 | 324 | 4 | 1 | 1 | 5 | 115 | deep | serving |
| `split.validation` | 687 | 553 | 6 | 0 | 3 | 6 | 398 | deep | serving |
| `split.workbench_trace` | 120 | 86 | 1 | 0 | 4 | 2 | 68 | medium | serving |
| `taxonomy_regrade` | 120 | 85 | 1 | 1 | 0 | 6 | 79 | medium | tooling-only |
| `text_gaps` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | init | serving |
| `text_gaps.actions` | 655 | 446 | 25 | 3 | 1 | 21 | 66 | wide | serving |
| `text_gaps.candidates` | 287 | 214 | 6 | 0 | 2 | 10 | 81 | medium | serving |
| `text_gaps.contract` | 409 | 254 | 4 | 1 | 9 | 4 | 10 | deep | serving |
| `text_gaps.jobs` | 824 | 521 | 23 | 12 | 2 | 15 | 165 | medium | serving |
| `text_gaps.judges` | 532 | 391 | 20 | 1 | 3 | 19 | 67 | wide | serving |
| `text_gaps.kinds` | 203 | 155 | 6 | 0 | 2 | 6 | 20 | medium | serving |
| `text_gaps.pipeline` | 1203 | 828 | 12 | 0 | 2 | 23 | 93 | deep | serving |
| `text_gaps.provenance` | 413 | 249 | 9 | 1 | 2 | 4 | 40 | medium | serving |
| `text_gaps.report` | 298 | 225 | 6 | 1 | 0 | 8 | 71 | medium | tooling-only |
| `text_gaps.sources` | 1223 | 844 | 39 | 0 | 4 | 13 | 71 | wide | serving |
| `text_gaps.tier1` | 305 | 213 | 4 | 0 | 1 | 12 | 68 | medium | serving |
| `voi_forecasting` | 618 | 468 | 8 | 1 | 3 | 11 | 112 | deep | serving |
| `voi_stopping` | 2503 | 1662 | 32 | 3 | 5 | 13 | 211 | wide | serving |
