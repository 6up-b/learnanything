# Proof alternatives and the confidence arm

Branch `grading/proof-alternatives`, worktree `learnanything-grading-proofs`,
base `f2f02e32` (main at mvp-0.14, migration 180). Two owner-approved items
from the ITS research sweep (2026-10-13):

- **Part 1.** The valid-alternative gate is extended to proofs and
  explanations. It ships as an algorithm successor with a kill switch:
  `mvp-0.15`, a **placeholder** tag. The P2 hard-case gold set and its eval
  command come with it.
- **Part 2.** Offline predictor arms for the learner's pre-answer confidence
  and for hedging. There is no successor; they never feed serving.

## Plan

1. **Part 2 first**, because it is small and self-contained. The answer
   signals reach the replay rows, the arms register in the field harness, and
   the Brier score is split. A pinned-digest test proves the change is
   additive.
2. **Part 1 core.**
   - the proof-like item reader;
   - the independent route check and its deterministic gate;
   - wiring into the live blind door and the regrade path;
   - the successor (`mvp-0.15`), its upgrade and kill switch;
   - migration 185 for the clarification trigger, with the head fixture
     renamed;
   - recomputed defaults snapshots.
3. **P2.** The gold set as a tracked fixture, the harness and the
   `learnloop grading hardcases` CLI, with fakes in tests. Then a live
   interface check on one case, the full live eval and a rerun.
4. **Real data.** The replay with the new arms runs on backup-API copies of
   the owner's vaults (no model calls), then the playbook's shadow rebuild.
5. **Gate.** Then this record.

## Part 1: the gate for proofs and explanations

### What was there

PF-c's gate (`attempts/grading_support.py`) fires only when the
deterministic `final_answer_check` returns `matches_reference`. A "prove",
"show that", "justify", "derive" or "explain why" answer is almost always
`undecidable` or `no_conclusion`, so those items got no protection. arXiv
2605.16207 reports that LLM judges wrongly reject 13–91% of valid
alternative proof steps and wrongly accept 7–71% of wrong ones. The error is
mostly a property of the model, and showing the reference did not help.

### Design

The smallest sound path follows the computed task. One independent
re-derivation runs after the blind grade, and a deterministic gate applies
it. The sweep's cheaper variant, a second trigger inside the grader's own
prompt, was not built. It keeps the error inside one model, and the paper
says model choice is most of the error.

1. **Which items: an LLM reading, not a keyword list.**
   - `attempts/proof_check.py` defines `ItemKindReading`. It reads the item's
     prompt, rubric criteria and metadata (practice mode, capability, trace
     contract, allowed attempt types).
   - It never sees the answer or the reference.
   - It returns a `response_kind` and `reasoning_is_graded` (whether the
     rubric credits the validity of the learner's own steps).
   - `proof_like` follows that judgment: reasoning is graded and the kind is
     not recall or classification. This covers proofs, derivations,
     justifications, explanations, and computations whose rubric credits the
     working; for those, the final-answer check rarely verifies a different
     route either. A live result decided the computation case (see results).
   - The reading is cached per item content: `judgment_ledger`, task
     `proof_like_item`, with the input hash taken over the reader's payload.
     Each item version is read once, and an edited item is read again.

2. **The independent re-derivation** (`ProofRouteCheck`).
   - One isolated call per new blind grade on a proof-like item.
   - Input: the item, the rubric and the answer (plus the clarification
     exchange on a clarification regrade). It never sees the grader's verdict
     or the reference.
   - It restates the route, checks each step on its own terms, and returns
     one verdict per criterion: `established`, `not_established` (the first
     failing step quoted verbatim) or `cannot_tell`.
   - A criterion phrased in terms of one method counts as established by any
     valid method that establishes the same fact.

3. **Route: not the grader's model where possible** (`proof_check_route`).
   - `ai.routing.proof_check` when set.
   - Otherwise, the first route the vault already sends learner text to
     (diagnosis, same-cause judge, diagnosis judge, tutor, active, fallback)
     whose configured model differs from the grader's.
   - Otherwise, the grading route, recorded `independent: false`.
   - Learner text never goes to a provider the vault does not already use.
   - On the owner's vaults every route is Codex `gpt-5.6-sol`, so the check
     is **not independent until `ai.routing.proof_check` is set** (owner
     commands below).

4. **The gate** (`apply_proof_route_gate`). It is deterministic and runs
   after PF-c's gate. It follows PF-c's outcome types and its rule that a
   criterion may be marked down only where a concrete error is located in
   the learner's words. Per criterion:

   | Grader | Check | Outcome |
   |---|---|---|
   | below full, no located error | established | **restored**: full points, assessed. The evidence row says so and keeps the grader's note. Attributions on it are withdrawn from the grade and kept on the blind record |
   | below full, located error (verbatim quote) | established | **disputed**: unverified, which PF-c's rule makes unassessed. The grade is provisional. One clarification is asked only when the checker says the dispute turns on what the learner meant (`ambiguous_notation`, `skipped_step`, `method_ambiguity`). A disagreement between two models about a written step is machine-resident and never costs the learner (causal principle 8) |
   | full points | not established, failing step quoted verbatim | **flagged**: the grade stands. The review reason is `proof_route_check_flag` and the criterion carries a note quoting the step. Never silent |
   | agreement, `cannot_tell`, or an unquoted refutation | — | the grader's grade, recorded |

   - A grade with fatal errors is never restored. A check that disputes it
     is a flag.
   - When the gate applies, PF-c's own support keys are rewritten over both
     gates (`unverified_criterion_ids`, `valid_alternative_gate_applied`,
     `assessed_shortfall`, the interpretation mark). The attempt step,
     diagnosis queueing, placement and the learner field therefore treat a
     route-check outcome exactly as a PF-c one, with no change to any of
     them.
   - `valid_alternative_gate = {final_answer, proof_route}` tells the two
     gates apart.

5. **Review reasons** (`gated_review_reason`). The grader's own concern
   wins. Then, in order: a flag; a pending clarification
   (`provisional_pending_clarification`, A8's state); unverified criteria
   (PF-c's non-blocking log). A restore alone leaves nothing to review.

6. **Agreement and disagreement** go to `judgment_ledger` (task
   `proof_route_check`, left = the attempt, judge `llm`, model = the
   checker's). The verdict holds per-criterion outcomes and verdicts, an
   agreement count and the checker route. The score is the agreeing share.
   It is written in the grading transaction, and a regrade supersedes it.

7. **Never fails a grade.** No ready client, a provider error or invalid
   output leaves the grader's grade in force. The blind record then carries
   `proof_route_check.status = "unavailable"` and the error type.

### Successor, switch, migration

- **The successor tag.** `PROOF_ROUTE_CHECK_ALGORITHM_VERSION = "mvp-0.15"`
  is a placeholder. The merge chain is adding router R1 (`mvp-0.15`) and
  learner-text gaps (`mvp-0.16`), so expect a relabel to the next free tag,
  as the stuck prompt and DL1 were relabelled.
  - It is appended to `SUCCESSOR_CHAIN`, so `LATEST_ALGORITHM_VERSION` and
    every version set follow.
  - `PROOF_ROUTE_CHECK_VERSIONS` gates it.
  - New vaults start there.
- **The upgrade.** `learnloop upgrade --to mvp-0.15` (the default target)
  runs `proof_check_upgrade.upgrade_to_mvp015`.
  - It accepts `mvp-0.14`, or `mvp-0.9`–`mvp-0.13` through the chain,
    including T1's guard below `mvp-0.12`. Anything older is refused.
  - It is a tag change plus an idempotent rebuild of the same projection
    namespace. Nothing is rewritten.
- **The kill switch.** `[proof_check] enabled = false` grades new answers
  exactly as `mvp-0.14`. A test compares every attempt column and evidence
  row with a real `mvp-0.14` vault.
- **The route.** `ai.routing.proof_check` is unset by default.
- **Migration 185.** Built as 185 (main's chain takes 181–183; expect
  renumbering). It rebuilds the append-only `grading_clarifications` with
  every row, index and trigger. Only its `trigger` CHECK gains
  `route_check_disagreement`. Foreign keys are off for the rebuild, and the
  responses table's foreign key resolves to the rebuilt table.
- **The head fixture.** `fixtures/migration_head_180` is renamed
  `migration_head_185`, with only 185 applied (rollback journal,
  `integrity_check` ok, `foreign_key_check` clean). The README and every
  hard-coded path are updated: ten tests and two `_scripts`.
- **Defaults.** Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was recomputed;
  each moves only because the effective config gains `[proof_check]` and the
  route. `mvp-0.15` has its own entry.
- **Reference docs.** The DB/config reference was regenerated: schema head
  185, 299 table notes, 680 config leaves in 41 sections.

### Playbook items

1. **New tag.** Yes: `mvp-0.15`, a placeholder.
2. **Ledgers immutable.** The ledgers are append-only. A regrade supersedes
   its verdict, and the clarification table rebuild keeps every row.
3. **Upgrade function.** It refuses jumps and prepares the projection before
   the atomic config rename (`tests/test_mvp015_upgrade.py`).
4. **Defaults fingerprint.** Recorded for `mvp-0.15`; every other snapshot
   was recomputed.
5. **Table roles.** No new table.
6. **Replay and rebuild.** Same-version rebuild equivalence holds on a vault
   holding a restored, unverified and flagged grade. Two rebuilds equal the
   projection before, and replay never calls the checker
   (`test_replay_reproduces_route_checked_grades_without_a_model`).
7. **Shadow rebuild.** Run on a backup-API copy of `linear_algebra`: upgraded
   `mvp-0.8` → `mvp-0.9` → `mvp-0.14`, rebuilt to its fixed point, then
   upgraded to `mvp-0.15`.
   - `learnloop rebuild --shadow`: facets 0 changes (79 unchanged), schedule
     0 changes (99 unchanged).
   - Mastery: 21 rows changed, and the only field that differs is the row's
     `algorithm_version` label (`mvp-0.14` → `mvp-0.15`), as at every
     successor.
   - The live database hash was unchanged.
8. **Head fixture path.** Upgrade, foreign-key check, doctor and an
   idempotent rebuild all pass.
   - Doctor on the owner's copy reports one error, `layout:missing_directory`
     (`rubrics`). It is the same on the copy before any change.

## Part 2: offline confidence and hedging arms

All of this is in `field/answer_signals.py`, registered in the learner
field's arm registry. They are offline only:
- `calibrated_uncertainty = False`, so G11 keeps them out of
  `field.active_predictor`;
- no serving module imports them, and a test pins that;
- the purity contract covers the module (`field-predictors-are-pure`);
- no successor.

**Signals** (`AnswerSignals` on `AttemptRow`, never on `ItemFeatures`, so no
other arm or prepared cache key changes):
- `confidence`: the pre-answer tap (1–5), mapped to a probability by the
  duel's own mapping (1→.1 … 5→.9);
- `hedged_share`: of the criteria the grader read the learner's tone on
  (`grading_evidence.learner_confidence`, confident or hedged), the share
  read as hedged. It shares the grading call, and the report says so.

**Arms.** Each is a MAP logistic fit, by Newton's method, on its own past
only. Each abstains where its signal is absent, so it pairs with its base on
the attempts that carry it.

| Arm | What | Fit |
|---|---|---|
| `answer_confidence` (a) | confidence alone | `logit p = a + b·logit(map(c))`, a ~ N(0,1), b ~ N(1,1): it starts at the duel's mapping |
| `<base>+answer_confidence` (b) | the existing arm plus confidence, for `mastery_ekf` (the incumbent) and `lo_general+composite` (the best exploratory arm on the owner's vault so far) | one parameter: `logit p = logit(p_base) + b·x`, b ~ N(0,1). It starts at the base, so a gain is the signal's (the sweep's "+recal" method, applied to the signal) |
| `answer_hedging` (c) | the grader-read hedging share alone | `logit p = a + b·(2h − 1)`, neutral priors |
| `<base>+answer_hedging` | (c) stacked on the same bases | as (b) |
| `<base>+answer_*:control` | the same rows and fit as each stack, with the signal replaced by a constant | It only recalibrates the base, so (control, stack) is what the signal adds |

**Reports.**
- Every metric block now carries Murphy's split, `brier_decomposition`:
  reliability, resolution, uncertainty and the within-bin residual, so the
  split is exact (`numeric.brier_decomposition`).
- The markdown table shows reliability and resolution.
- `counts` and `field data-check` report how often each signal is present.
- Each arm reports a split by presence.
- `learnloop eval --section field` adds the pairs (base, stack) and
  (control, stack) by default.
- The calibration duel (`goals/exam_calibration.py`) reports both sides'
  reliability and resolution, the uncertainty, and how often ordinary
  unprimed, unhinted graded attempts carry a tap (`confidence_present`,
  `confidence_eligible`, `confidence_share`).
- The UI's duel line is unchanged.

**Additivity proof.** `tests/test_eval_harness.py` strips what the arms add
(arms, split, two split dimensions, four counts, one limitation). Every report
then hashes to the digests recorded before them. A row without signals hashes
in the data snapshot exactly as before.

## Results

### P2: hard cases, live (OpenRouter, on a backup-API copy)

The gold set (`fixtures/grading_hardcases/cases_v1.json`) has 14 hand-checked
cases in linear algebra and probability:
- 6 valid alternative proofs (null space vs SVD; Rayleigh quotient;
  orthonormal columns; tail sum; disjoint split vs inclusion–exclusion;
  complement vs inclusion–exclusion);
- 4 correct answers with flawed reasoning ("invertible matrices commute";
  "det is the sum of eigenvalues"; "expectation is multiplicative";
  "variance is linear");
- 4 wrong proofs that look right (AB = 0 ⇒ A = 0 or B = 0; singular matrices
  form a subspace; "P(B|A) = P(A|B)"; E[max] = max E).

Routes, both strong cheap judges at $0.10 / $0.50 per million input / output
tokens:
- `anthropic/claude-haiku-5.5` (`or_haiku`);
- `openai/gpt-6-luna`, `reasoning_effort = low` (`or_luna`).

**Calls and cost.** The dry run planned 84 calls with an upper bound of
$0.24, inside the $3 cap. 85 requests were sent:
- 6 on one case to verify the interface ($0.0051);
- 78 for the rest of the run ($0.0720);
- 1 rerun of a failed case ($0.0037).

**Billed in total: $0.0808.** Every request is recorded in the copy's
receipts.

| Judge | Route | Wrong rejection (valid) | Wrong acceptance (flawed + wrong) | Failed |
|---|---|---|---|---|
| grader | Haiku 5.5 | 0/6 [0.00, 0.39] | 0/7 [0.00, 0.35] | 1 |
| checker | Haiku 5.5 | 0/6 [0.00, 0.39] | 0/8 [0.00, 0.32] | 0 |
| grader | GPT-6 Luna | 0/6 [0.00, 0.39] | 0/8 [0.00, 0.32] | 0 |
| checker | GPT-6 Luna | 0/6 [0.00, 0.39] | 0/8 [0.00, 0.32] | 0 |
| gate | each of the 4 (grader, checker) pairs | 0/6 | 0/7 or 0/8 | 0 or 1 |

Intervals are 95% Wilson.

- **The one failure is real and reproducible.** Haiku's grader returned an
  invalid key (`local_analysis_md_check`) on the Bayes case, twice, under
  `response_format = "json_object"`. It counts as failed, not as an
  acceptance.
- **The item reader** called all 14 proof-like on Haiku and 13 on Luna under
  the first rule (proof-like kinds only). Luna read "find the standard
  deviation of X − Y and justify each step" as `computation` with
  `reasoning_is_graded = true`, so that rule would have left a graded
  justification unprotected. The rule now follows `reasoning_is_graded`
  (recall and labels excepted), and under it both readers mark all 14. The
  stored readings are re-derived on load, so no cache is invalidated.
- **What this says.** The set does not separate these two models: both make
  neither error on any cell, as grader, checker or gate. Upper bounds of
  0.32–0.39 are all 14 cases can show. The paper's 13–91% / 7–71% came from
  step-level judgments across many models. The set needs harder and real
  cases to rank routes. Open question 1 has the sources.

**Eedi MAP.** Its `True_Misconception` rows (a correct multiple-choice answer
explained with a named misconception, about 2% of rows) are real
correct-but-flawed traces and could fill that cell. Limits:
- they are short school-maths explanations of a chosen option, not proofs;
- they are competition data, so check Kaggle's rules before committing a row;
- the label match is the sweep's inference, not verified here.

None are used. The note travels in every report.

### Part 2 on the owner's vaults (backup-API copies, no model calls)

On `linear_algebra`, the strict default (`exclude`) leaves 0 eligible rows,
as the 2-3 integration found. The numbers below use the labelled
`current_content` reconstruction. `probability` has 2 graded attempts, which
is too few to say anything.

- **How often confidence is present.**
  - The learner tapped on 29 of 70 graded attempts (41%) and 28 of 54
    ability-scored ones (52%).
  - Taps are nearly constant: 26 × "5", 3 × "4".
  - The grader read the tone on 69 of 70 attempts.
- **Confidence rows** are almost all correct. The outcome uncertainty there
  is 0.0092 (vs 0.041 overall), and no binary failure exists for an AUC.

Each row below covers the attempts where that arm's own signal is present
(log loss in nats):

| Arm | n | Log loss | Brier | Reliability | Resolution |
|---|---:|---:|---:|---:|---:|
| `mastery_ekf` (all rows) | 54 | 0.457 | 0.092 | 0.049 | 0.001 |
| `lo_general+composite` (all rows) | 54 | 0.375 | 0.057 | 0.014 | 0.001 |
| `answer_confidence` | 28 | 0.179 | 0.008 | 0.000 | 0.002 |
| `mastery_ekf+answer_confidence` | 28 | 0.211 | 0.019 | 0.010 | 0.002 |
| `…:control` | 28 | 0.248 | 0.028 | 0.020 | 0.001 |
| `answer_hedging` | 53 | 0.336 | 0.043 | 0.010 | 0.009 |
| `mastery_ekf+answer_hedging` | 53 | 0.333 | 0.044 | 0.018 | 0.017 |

| Paired comparison (positive = the challenger is better) | n | Mean | 95% bootstrap CI |
|---|---:|---:|---|
| `mastery_ekf+answer_confidence` vs `mastery_ekf` | 28 | +0.186 | [0.100, 0.269] |
| … vs its control (the tap's own share) | 28 | +0.037 | [0.000, 0.071] |
| `lo_general+composite+answer_confidence` vs its control | 28 | +0.016 | [−0.013, 0.044] |
| `mastery_ekf+answer_hedging` vs `mastery_ekf` | 53 | +0.127 | [0.057, 0.192] |
| … vs its control | 53 | +0.029 | [−0.023, 0.114] |

**Reading it.** About four fifths of the stack's gain over the incumbent is
recalibration of a miscalibrated base on those rows. On that subset the
incumbent's reliability is 0.072, and the control captures it. The tap
itself adds a hair (+0.037, interval touching 0) because it barely varies.

Hedging alone sorts outcomes well: AUC 0.99 on 40 binary outcomes, resolution
0.009 of an uncertainty of 0.042. But it is written by the call that grades,
so it is a shared judgment, not independent evidence. One learner, so
exploratory, as every field report says.

Reports are in `fixtures-local/proofs-eval/field-*` and are not committed.

## Gate

Run on the branch tree after the last code commit (`0248f84e`; later commits
are docs only). No frontend or `src-tauri` file changed, so the npm and cargo
steps do not apply.

- **Setup.** `uv sync --extra dev --extra mobile`, then `uv pip install
  pypdfium2`: done, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.
- **`uv run lint-imports --no-cache`:** 14 kept, 0 broken. The purity
  contract now covers `field.answer_signals`.
- **Full suite** (`flock /tmp/learnloop-fullsuite.lock uv run pytest -n
  auto`): **8741 passed**, 0 failed.
- **Durability lane** (`flock /tmp/learnloop-fullsuite.lock uv run pytest -m
  durability`): **94 passed**, 8647 deselected.
- **DB reference scripts.** `db_generate_reference.py`, then
  `db_validate_reference.py`: **0 errors**. Schema head 185, 299 table
  notes, 680 configuration leaves in 41 sections.
- **CLI help snapshot.** Regenerated for `upgrade` and the new `grading
  hardcases`.
- **No sidecar RPC was added**, so `tests/test_mobile_allowlist.py` is
  unchanged.

## Owner commands

The owner's vaults are at `mvp-0.8` (`linear_algebra`). The route check acts
only from `mvp-0.15`, through the whole chain, so take the playbook's shadow
rebuild on a copy first.

```bash
# Make the check independent of the grader (Codex gpt-5.6-sol on every route
# today): add a cheap strong judge and route the check to it.
#   [ai.providers.or_haiku]
#   type = "openrouter"
#   model = "anthropic/claude-haiku-5.5"   # or openai/gpt-6-luna with reasoning_effort = "low"
#   api_key_env = "OPENROUTER_API_KEY"
#   [ai.routing]
#   proof_check = "or_haiku"

uv run learnloop rebuild --shadow --json --vault <copy>
uv run learnloop upgrade --vault <vault>   # default target: mvp-0.15 (placeholder tag)
# kill switch, no downgrade needed:  [proof_check] enabled = false

# Hard cases: dry run first, then the run (receipts and checkpoints go to the copy)
uv run learnloop grading hardcases --vault <copy> --route or_haiku --route or_luna \
  --input-price-per-million 0.10 --output-price-per-million 0.50 --max-cost-usd 3 --dry-run
uv run learnloop grading hardcases --vault <copy> --route or_haiku --route or_luna \
  --input-price-per-million 0.10 --output-price-per-million 0.50 --max-cost-usd 3
# a Codex or ChatGPT-plan route needs no price (subscription, estimated only)

# Confidence and hedging arms (offline replay, no model calls)
uv run learnloop eval --vault <copy> --section field --legacy-fallback current_content
uv run learnloop field data-check --vault <copy> --json   # answer_signals coverage
```

## Paid calls

- **Planned (dry run):** 84 calls, upper bound $0.24.
- **Sent:** 85 OpenRouter requests to `anthropic/claude-haiku-5.5` and
  `openai/gpt-6-luna`. **Billed in total, as provider-reported: $0.0808**:
  - 6 to verify the interface ($0.0051);
  - 78 in the full run ($0.0720);
  - 1 rerun of a failed case ($0.0037).
- **Where:** only the backup-API copy
  `fixtures-local/proofs-eval/linear_algebra`.
- **Keys:** loaded by the app itself; no key file was read.
- **Vault rule:** no tracked working vault was opened except to make the
  copies.
- **Free call:** a listing of OpenRouter's model IDs and prices from the
  public `/models` endpoint.

## Open questions

1. **A harder gold set.** Both judges score perfectly on v1, so it cannot
   rank routes yet. Proposed v2 sources:
   - the owner's own adjudicated proofs from the vaults;
   - the MAP `True_Misconception` rows, after a licence check;
   - frontier-written alternatives checked by the owner;
   - step-level cases, the paper's own unit.

   Run the sweep's two ablations on it too: reference vs solve-first, and the
   final-answer check early vs late.
2. **Disputed criteria leave the grade.** With every criterion disputed,
   nothing is assessed, and PF-c's rule then schedules the attempt as
   correct. That rule was justified by a verified final answer, but here it
   rests on the checker's affirmative validation. Should a fully disputed
   proof instead keep the grader's grade as provisional, pending review?
3. **A flag is a real review concern.** `proof_route_check_flag` makes the
   grade "unresolved" for retention reports and not clean for fast-track,
   unlike PF-c's non-blocking log. That is the protective intent. Should it
   instead be a non-blocking log like PF-c's?
4. **Computation items whose rubric credits the working are now checked.**
   This follows the reader's `reasoning_is_graded`, and the generous default
   costs one more call per such attempt. Narrow it back to proof, derivation,
   justification and explanation if the calls are not worth it.
5. **Haiku 5.5 and `json_object`.** Haiku broke the grader's schema once in
   14, twice in a row on the same case. Should `response_format =
   "json_schema"` be recommended for an OpenRouter check route?
6. **Latency.** The check is synchronous: one more call on a proof-like
   answer, two the first time an item is seen. Live today, behind the kill
   switch. Should it move to the post-attempt queue as a regrade if it
   proves slow?
7. **Part 2 next step.** Taps are nearly constant on this vault (26 of 29
   are 5), so it cannot tell yet. Hedging looks informative but shares the
   grader's call. Keep both offline, and reread once there are more
   confidence-present rows with failures.
