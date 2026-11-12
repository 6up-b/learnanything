# Diagnosis map (K9, 2026-11-12)

Refactor step K9, job 1: the deep map of `src/learnloop/diagnosis/` that the Nov 8 map (`docs/reviews/architecture-map-2026-11-08.md`) read by outline. It names problems and recommends nothing; job 2 (the structure strategy) stands on it after the orchestrator has checked its claims. **Base: main `95bee5f02a`**, branch `refactor/k9-diagnosis-map`. Docs only; no source, test or vault note changed.

## Summary for the owner

(Written last; see the end of this section.)

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
