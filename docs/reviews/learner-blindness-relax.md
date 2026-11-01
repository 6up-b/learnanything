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
