# Learner-blindness relax (stage `learner-blindness-relax`)

**Owner direction 2026-11-01: blindness only where it matters, the grader.** Four model contexts that were
blind to the learner may now read the learner's own state, each behind its own kill switch (live by default,
owner rule 2026-10-12). **The blind grader is untouched**: its inputs are byte-identical in every arm and every
switch setting (pinned). Nothing here is an algorithm successor: model contexts only; no scoring, scheduling,
projection or serving change; no migration; the tutor, the narrative, the diagnoser and AD's forecasters still
never write an attempt, a claim, mastery or a grade.

Branch `learner/blindness-relax` from `e9693b3700`. **No live or paid call**: fakes only, synthetic vaults
only; no owner vault, `~/.config/learnloop` or credential file was read.

Reviewers (per the owner): a "blindness" finding outside grading is not a defect; a finding must show grade
contamination, evidence leakage, exam leakage or unapproved spend.

## What changed

### 1. The Reader tutor (Ask) reads the learner's state: `reader_tutor.learner_state_enabled` (default on)

* New module `learnloop.reader_learner_state` (top level; only the sidecar composes it, because it reads the
  Today headline in `daily_plan`, which `reader`/`tutor` may not import without a package cycle). For the
  passage's learning objects (`source_retrieval.reader_tutor.passage_learning_objects`: the selection's, or a
  follow-up's root selection) it builds:
  * **readiness in words**: the Today headline's class of each topic
    (`daily_plan.headline.classify_learning_objects`) rendered as a phrase (`READINESS_WORDS`: demonstrated /
    assumed / learning / untested). Never a number or posterior; no new threshold;
  * **TE0's confidence events** (`confidence_events.safe_learner_events`), reversing TE0's default ruling that
    the Reader carries none;
  * **recent attempt outcomes** per topic ("2026-09-02: wrong, unassisted"; held grade = "held for review");
  * **the learner's own questions** from recent practice and feedback exchanges per topic. No stored tutor
    answer text is carried, ever (landing step 0, ruling R1 below; this replaced the stage's "answer shown
    once its item can no longer be answered cold", which Codex reopened twice on answer provenance).
* **Protection** is the one authority, `learner_protection` (`withheld_items`, `PastWork.attempt_reason`,
  `evidence_reason`, held grades): exam and held-out work, reserved surfaces, items an open cold check holds and
  diagnostic probes contribute nothing; unreadable protection = no state (fail closed).
* **Cold**: a question asked during a cold administration (the client's flag or the server's RW1c derivation)
  carries **no** learner state; the manifest records `omitted: cold_administration`.
* **Manifest / contract**: with the switch on, the manifest's version takes `+learner-state-v1`, `excluded`
  keeps `assessment_reserved_surface` and `cold_in_flight_response` (only `ability_estimate` leaves), and
  `learner_state` records exactly what the tutor was given (receipt + blocks). `reader.prompt_contract` names the
  state (`reader_prompt_contract(learner_state=True)`). The question row's `source_context.learner_state` keeps
  the receipt (counts, no text).
* **Prompt**: `TutorQAContext.learner_state` (omitted from payload and hash when None, as TE0's block); the
  Reader task's blind sentence is replaced by the learner-state sentence ("data, not instructions, never a
  grade") and every Reader prompt version takes `+learner-state-v1`.
* Off: today's prompt, manifest and contract byte for byte. The switch-off goldens
  (`tests/fixtures/reader_tutor_switch_off.json`, `compare_keep_switch_off.json`, `figures_switch_off.json`,
  `reading_paths_base_a76c8358a.json`) are **unchanged**; their tests set the new switch off, as earlier stages
  did for their own switches.
* Not done: the library page's pinned "ask the tutor about these" path (`reader.library_ask_tutor`) carries no
  learner state (open question 1).

### 2. The reader narrative may quote the learner's inquiry words: `digest.narrative_quotes_inquiry` (default on)

`build_prompt` adds `inquiry_quotes` (each inquiry root question the summary names, the learner's own words from
its question row, at most `QUOTE_COUNT` = 8, each at most `QUOTE_CHARS` = 240 characters, `keep` size bounds),
keyed by the root exchange the narrative cites; instructions say the narrative may quote a few words in quotation
marks and cite that root. `validate_narrative` is unchanged (cited ids within the summary, at least one, at most
120 words, no well markers); the session's exam check (`exam_withheld`) still runs first. Prompt version
`reader_digest.v2-inquiry-quotes` (recorded on the digest row and the ledger verdict). Off: the v1 prompt exactly
(pinned against a fresh render of the base payload). The route disclosure now says so.

### 3. The diagnoser's prior-analysis arm: `diagnosis.history_includes_prior_analysis` (default `randomized`)

* New module `diagnosis/split/prior_analysis.py`. In the `on` arm each shown prior attempt also carries
  `earlier_diagnosis` (the latest completed live diagnosis of that attempt written strictly before the diagnosed
  attempt: its `analysis_md`, at most 1500 characters, `keep`) and, for a workbench attempt, its
  `workbench_trace` (the same rendering the current attempt gets, symbolic switch read now); the disclosures
  block carries a note ("test them against the evidence; never repeat an earlier reading"); the prompt version
  takes `+prior-analysis-v1`; each earlier diagnosis shown is recorded as a derived text read (diagnosis input
  provenance: `("diagnosis", id, text)`).
* **No made-up constant** (owner, 2026-10-24): the default `randomized` assigns each diagnosed attempt to one arm
  by a seeded equipoise draw (sha256 of `prior-analysis-arm-v1:<attempt id>`; retries and re-runs land in the
  same arm; `EQUIPOISE = 0.5` is the design's structure, `keep`). `on` / `off` fix the arm. The arm
  (`arm`, `assignment`, `design`, `propensity`, `draw`) is on the diagnosis's context receipt
  (`diagnosis_context_receipts.retrieval_json.prior_analysis`) beside the context hash, in both arms.
* **Measured**: `learnloop diagnose m2-report` gains `e2_prior_analysis_arms`: E2's `anchoring_suspect` rate per
  arm with Wilson intervals and n (`unassigned` = diagnoses written before the arm), and the assignment counts.
  No threshold (O10).
* The `off` arm's context, prompt and hash are today's byte for byte (pinned). The offline review (M1) passes no
  arm and is unchanged. The grader never reads any of it (new import contract
  `graders-never-read-the-learner-relax-contexts`).

### 4. AD's `llm_v3` history card carries answer excerpts: `adaptive_difficulty.history_answer_excerpts` (default on)

`history_card(answers=True)` adds `answer_excerpt` (at most `HISTORY_ANSWER_LIMIT` = 300 characters, `keep`) to
each earlier attempt it lists; the card is read through the material view, which never lists a withheld (exam,
held-out) attempt. The frozen payload's `state_version` is `ad-forecast-state-v2` (and the receipt's
`versions.state` follows the frozen payload). Forecasts stay reporting and scoring only. Off: the v1 card and
state exactly. `llm_v1` is untouched. The route disclosure now says so.

### Supporting changes

* Config: the four keys (schema docstrings), classified in `params/parameter_registry.py` (structural,
  operational; booleans and the arm string, classified so every new key has a rule); all 31 defaults
  fingerprints recomputed (`DEFAULTS_SNAPSHOT_BY_ALGORITHM`, note at `mvp-0.9`, one line on every other).
* Import contracts (40 kept): `reader-learner-state-is-context-only`, `evidence-never-reads-the-reader-learner-state`,
  `graders-never-read-the-learner-relax-contexts`.
* Untouched as instructed: grader inputs, probe bundles, project instruments, `llm_v1`, the figure author (Q9),
  exam protection.

## Owner item (recorded, not implemented)

**`diagnosis.split_enabled = false` (joint mode) puts the learner's history into the grader.** With the split
off, NEW attempts are graded jointly as at `mvp-0.9`: the joint `GradingContext` carries `diagnostic_history`
(raw prior traces; `attempts/ai_contracts.py`, hashed in `grading.grading_context_hash`), so the grade can read
the learner's past. That is the one place blindness matters under the owner's direction. **Recommendation:
retire the joint mode** (remove the `split_enabled` kill switch, or make `false` refuse to grade new attempts
jointly and fall back to blind), keeping already-joint attempts' records and replay as they are (their grader
mode is persisted). It needs an owner decision and its own stage (it changes grading).

## Tests

New: `tests/test_learner_blindness_relax.py` (16): the Reader tutor's state through the protection (probe work and
its exchanges absent; a feedback answer withheld while the item can still be answered cold, shown once closed;
TE0 events; manifest exclusions; receipt; **no new evidence path**: practice attempts, grading evidence, mastery,
claims and certification tables unchanged by the Ask); cold carries none and keeps the exclusions; switch off is
today's; bound question carries no earlier tutor answer; strictly-before cutoff; unreadable protection carries
nothing; contract; narrative quotes under the same checks and switch-off prompt equal to the base render; the arm's
seeded draw; off arm byte-identical context and on arm re-feeding with provenance; live diagnoses record the arm
(`on`/`off`) and no grading prompt carries it; the report per arm; **the blind grader's plan (context hash,
prompt, version) identical across every arm and switch setting**; AD's card excerpts and frozen state version.

Changed for the new default (the off path stays pinned): `test_reader_tutor_switch_off.py`,
`test_compare_keep_switch_off.py`, `test_figures_switch_off.py`, `test_reading_paths.py` (normalizes the on
contract back to the golden), `test_reader_inquiry_kill_switch.py`, `test_reader_intent.py`,
`test_reader_digest_narrative.py`, `test_teacher_te0_confidence_events.py`, `test_judge_routes.py`.

## Gate (this step; the full suite runs once in the landing gate)

See the stage result for exact commands and counts. All pytest runs inside
`systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`. No frontend, Rust, migration, DB or
connection change, so no npm/vitest/cargo/durability/DB-reference run. The docs vault's generated references
(Configuration field catalog, module pages) are left for the landing's regeneration.

## Open questions

1. Should the library page's pinned-passages tutor (`reader.library_ask_tutor`) carry the learner state too? It
   is the Reader tutor on pinned passages across books; left out to keep this stage to the Reader's Ask.
2. Retire joint grading (owner item above)?
3. The Reader's learner state counts "readiness" by the Today headline's classes (the only categorical reading
   with no new threshold). A finer "ability in words" would need a learned mapping (LP track), not a constant.

## Landing onto main

Branch `learner/blindness-relax` (worktree `learnanything-ad1`), from `c8e0b26b2a`. The orchestrator fast-forwards
and pushes. Every Python or CLI run outside pytest ran under `env -i` with an empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`, and `TMPDIR` outside the worktree. pytest, vitest and npm ran in
`systemd-run --user --scope` (the full suite at 10G under `flock /tmp/learnloop-fullsuite.lock`, the rest at 5G),
vitest with `--maxWorkers=4`. No live model call was made. No owner vault was opened: only fresh backup-API copies of
`fixtures-local/owner-copies-mvp035` were used.

### Step 0: structural simplification (`a2d2176b10`)

The stuck-loop rule applied: Codex reopened F1 twice, both times on stored tutor answer provenance. The second
reopen was job `20261101-160205-68yc5y`, a cross-item feedback chain. The owner principle is to include learner data
when it is beneficial and leave it out when it is noise. Under both, **the Reader learner state no longer re-shows
any stored tutor, practice or feedback answer text.** It carries:

- readiness in words;
- confidence events;
- recent attempt outcomes;
- the learner's own question text from recent practice and feedback exchanges, filtered through `learner_protection`
  as before.

The question query selects only the question columns, never `answer_md` or `source_context_json`.

Removed:

- `answer_shown`, `answer_left_out` and the `answers_left_out` count;
- `answer_source_refs`, `_thread_turns`, `_source_reason`, `_decoded` and `ANSWER_SOURCES_UNKNOWN`;
- the `bound_item_id` parameter, which only suppressed answers;
- `practice_leakage.teaching_link_refs`, which only this module used.

The tutor's learner-state sentence, the Reader prompt contract and the config docstring now say "the learner's own
questions, never the answers they were given". The learner's own attempt answer was never part of the state. The F2
session resolution and the F3 trace fold are unchanged.

Tests:

- The earlier F1 reproductions now pass because the answer text is absent, before and after the protection
  changes. They cover the held-out linked passage, the retrieved passage, the two-turn thread and the feedback
  thread.
- A new cross-item chain test.
- A source pin, `test_the_module_never_reads_stored_answer_text`.
- Every entry has exactly `date`, `when` and `learner_question`.

Targeted run: **561 passed** (16 files). The codex-review record carries the orchestrator ruling. The orchestrator's
scoped Sol verify of `a2d2176b10` (job `20261101-161412-U9Ejhw`) came back **CLEAN**: F1 is closed structurally and
F2/F3 are intact.

**Note from that verify, accepted:** `confidence_events.taps_before` (the `taps_so_far` aggregate) still counts
protected taps. That is aggregate confidence metadata, not exam text.

### Merges

| Commit | What |
|---|---|
| `20f1cdacf0` | References regenerated on the tree. Main `e9693b3700` was the merge base, so there was nothing to merge. The four new config leaves move the prose count from 1104 to 1108. |
| `182a9f4d64` | Merge of main `7401484f91` (Reader follow-ups Nov 1b). Only the generated references conflicted: main's side was taken and regenerated in `31e1d2cbab`. The parameter registry auto-merged with both sides' entries. No template conflict. |
| `05da25ac4a` | Merge of main `ea1366fff5` (curriculum C3). `config/template.py` had 31 snapshot hunks: C3's note and this branch's note were both kept, and every fingerprint was recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`. A second pass changed 0. Generated references: main's side, then regenerated in `eb8b10323f` (prose count composed to 1109: main's 1105 plus this branch's 4). The parameter registry kept both sides' entries. |
| `30e6ff4f57` | Full-suite fix, below. |
| `6ab368e64e` | Merge of main `02614cfddd` (sketch compartment). `config/template.py` had 31 snapshot hunks: main's `sketch_enabled = true` note and this branch's note were both kept, and every fingerprint was recomputed. A second pass changed 0. Generated references: main's side, regenerated in `cd18f84803` (1109 leaves, 78 sections; catalog 302 TS / 6 Rust / ACTIVE 308). No `src-tauri` conflict, and the branch changes nothing under `src-tauri`, so no cargo check was run. |

After each merge: `db_validate_reference` errors [], `desktop_validate` reproducible byte for byte, `validate_vault`
passed, and all 31 defaults fingerprints equal `defaults_fingerprint_for_version`.

### Gate

| Step | Tree | Result |
|---|---|---|
| `uv run lint-imports --no-cache` | `a2d2176b10`, `31e1d2cbab`, `30e6ff4f57`, final | **40 kept, 0 broken** |
| Full pytest (`flock … systemd-run … -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | `eb8b10323f` (after the C3 merge) | 23517 passed, 90 skipped, 47 xfailed, **1 failed** (48:20). See below; fixed in `30e6ff4f57`. |
| Durability lane (`pytest -m durability -n 6`, 5G, under the flock) | `eb8b10323f` | **179 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh `copy_tree_with_databases` copies in the gitignored `fixtures-local/landing-blindness/`, remade before each run) | `20f1cdacf0`, `31e1d2cbab`, `30e6ff4f57` | **83 passed, 2 failed, 4 skipped** each time. Both failures are the known ones: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]`. |
| Targeted after the C3 merge (39 files: every defaults-snapshot test, C3's tests, this stage's tests, architecture) | `05da25ac4a` | **823 passed, 12 skipped, 3 xfailed** |
| Targeted after the compartment merge | `6ab368e64e` | **1004 passed, 12 skipped, 3 xfailed** (the 39 files above plus the e0 isolation, switch-off goldens, reading paths and every sketch test file) |
| Frontend: `npm install`, `npm run typecheck`, whole vitest, `npm run frontend:build` | `20f1cdacf0` (apps = `e9693b3700`) | typecheck ok, **247 files, 2367 passed**, build ok |
| Same | `30e6ff4f57` (apps = `ea1366fff5`) | typecheck ok, **249 files, 2375 passed**, build ok |
| Same | final (apps = `02614cfddd`) | typecheck ok, **250 files, 2397 passed**, build ok |
| `cargo check` | none | Not run: the branch changes nothing under `src-tauri`, and no merge conflicted there. |

**The full-suite failure was a stage defect.** The stage's targeted gates never ran it.
`test_e0_isolation::test_the_import_linter_contract_names_every_production_package` requires every top-level
production module to be a source of the `experiments-stay-outside-production` contract. The new
`learnloop.reader_learner_state` was missing. The failure is deterministic: the test compares the module listing with
the contract. `30e6ff4f57` adds the module to the contract. After the fix, `test_e0_isolation.py` gave 4 passed;
with the architecture test and this stage's tests, 48 passed; lint-imports 40 kept.

The full suite was not rerun after that one-line contract list change. It was not rerun after the compartment merge
either, because that resolution was snapshot data only, per the orchestrator's rule. The final tree's Python
differs from the gated `eb8b10323f` only by that contract line and the merged sketch compartment, which carried its
own full gate on main.

### Smoke on fresh owner copies (`fixtures-local/landing-blindness-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). The code came from `git archive` of main `ea1366fff5` and of the branch `eb8b10323f`, each with
`src/`, `migrations/` and `tests/`. Each copy ran under its own side's code: a bare `upgrade` (mvp-0.35 → mvp-0.40,
head 229), the primary desktop start, `migrate_vault`, then `rebuild-derived-state`. An audit hook logged every
process start and refused non-loopback sockets and Codex starts. The Reader tutor ran through the sidecar's own
`reader.ask` with a fake tutor that records the prompt: frozen clock, deterministic ids, a fresh copy per run.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| rebuild-derived-state | 8 LOs, 70 attempts | ok | 3 LOs, 3 attempts |
| Today (3 queue variants, frozen clock), branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| Daily plan dump, branch vs main | **identical** (84,705 bytes) | identical (124,030) | identical (32,442) |
| Reader tutor, switch **off**, vs main: prompt and manifest per passage | **identical** for all 4 passages | identical (1) | identical (3) |
| Reader tutor, switch **on** (default) | manifest `p3-reader-branches-v1+learner-state-v1`, `given: true`; readiness words on every passage; outcomes (5, 7, 3 and 7 attempts); learner questions on 3 passages (4, 2 and 4 entries, each with exactly `date`/`when`/`learner_question`); confidence events; **0 stored answers** in the state, and no `answer_shown`/`answer_left_out` key | readiness, 3 outcomes, 3 learner questions, confidence events, **0 stored answers** | readiness on all 3 passages (no attempts or questions on those topics), **0 stored answers** |
| Blind grader plan (context hash, prompt sha256, version) for the real items of the latest attempts, main vs branch | **identical** (5 items) | identical (1 item) | identical (no item has a stored answer) |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0 | 0/0/0 |

The protection held on real data. linear_algebra's practice and feedback questions on a teach-back item held by an
open check ("a check waiting in the app") and on a diagnostic probe are absent from the state. "0 stored answers"
means that no stored `answer_md` (24 characters or more, compared by its first 60 characters after whitespace
normalization) occurs in the state.

**0 new `model_call_receipts`** across all 24 smoke databases: every probability copy holds probability's 56
historical rows (42 completed, 14 failed), exactly as the source copy does, and the others have none. **Audit:** 0
process starts, 0 socket connects, nothing refused.

The smoke ran against main `ea1366fff5`, before the sketch compartment merge. That merge touches figures and the
sketch tier, not Today, the plan, the Reader tutor's prompt or the grader. On main it carried its own owner-copy
smoke (Today and the plan identical).

### Orchestrator rulings (verbatim)

- R1: "F1 (stored tutor answers carrying exam-derived text) is closed structurally: the Reader learner state never re-shows stored model answer text; it carries readiness, confidence, outcomes and the learner's own questions. The model's past answers were low-value context relative to the provenance risk (owner principle: include when beneficial, omit when noise)."
- R2: "diagnosis.split_enabled=false (joint mode) still puts diagnostic history into the grader; recorded as an owner item recommending retirement, not changed here."
- R3: "The diagnoser prior-analysis arm is randomized (seeded, equipoise) with arm and propensity on the receipt and E2 anchoring_suspect per arm in the report. Accepted."

### Owner items

1. **Retire joint grading** (R2; the owner item above). With `diagnosis.split_enabled = false`, new attempts are
   graded jointly with `diagnostic_history` in the grading context. The recommendation is to remove the switch, or
   make `false` grade blind, in its own stage, because it changes grading.
2. **The library tutor's learner state is deferred** (open question 1). The library page's pinned-passages tutor
   (`reader.library_ask_tutor`) carries no learner state. Should it?
3. Four switches default on (live by default): `reader_tutor.learner_state_enabled`,
   `digest.narrative_quotes_inquiry`, `adaptive_difficulty.history_answer_excerpts`, and
   `diagnosis.history_includes_prior_analysis = "randomized"`. With each one off, its context is today's byte for
   byte. No migration, no successor, and no `rebuild-derived-state` is needed for this stage.

### Open items

1. The `taps_so_far` aggregate counts protected taps (noted by the orchestrator's verify): accepted as aggregate
   confidence metadata. Revisit only if confidence aggregates gain a text surface.
2. The diagnosed attempt's own workbench trace (RW2b) is accounted only by its item being a solution read. It is
   not marked incomplete for its assists' passages. This predates the stage; follow-up recorded in the codex-review
   record.
3. A finer "ability in words" than the Today headline's classes would need a learned mapping (LP track), not a
   constant (open question 3).
