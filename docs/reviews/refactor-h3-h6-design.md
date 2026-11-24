# H3 to H6: retiring the difficulty label, a design note

Refactor arc H (`docs/specs/refactor_strategy_v3.md` §2.11). The owner decided on 2026-11-23: **go** on H3 to H6,
and the dormant measured-difficulty path (`mastery.irt.eb_difficulty_enabled`, `ItemParameterState`'s `b`,
`update_item_difficulty` and their config fields) retires with the label. This is the design for review. **Nothing
here is built.** No source changes, no migrations, no tags.

Base: `86f29b0d39` (origin/main). Line numbers are at that commit. The inventory starts from H1's
(`docs/reviews/refactor-h1.md`) and its guard (`tests/test_difficulty_kinds_apart.py`: 54 modules, 161 sites). I
re-checked it with `git grep` at the base.

**The label** means `PracticeItem.difficulty` and `LearningObject.difficulty_prior` (0 to 1, authored, LLM-estimated
or from the solver panel), plus `pf_candidates.difficulty`, with `difficulty_source` beside them. FSRS's D
(`practice_item_state.difficulty`, `activity_card_state.difficulty`, `family_memory_state.difficulty`) is a different
quantity. It is not touched here, and H1's guard keeps the two apart.

## 0. The short version

| Step | What changes | Tag | Migration |
|---|---|---|---|
| H3 | The IRT seam stops reading the label at the tag, so mastery's `b` loses its item term. Surprise scores the answer against AD's serve-time forecast, recorded in `forecast_receipts`, and falls back to mastery's own prediction where there is none. Bayesian surprise still describes the mastery update. The EB path is never run at or above the tag. | one, the next after mvp-0.70 (mvp-0.71 if landing order holds) | none (§3.6) |
| H4 | AD stops reading `z_llm` (the label as a signal), from both frozen serve inputs and historical items. | one, its own | none |
| H5 | Exam pools stop stratifying by the label. Index filters go. Authoring prompts stop asking for a label and bump their versions. Copies of the label stop. | one, for the exam pools (they decide which items are held-out measurements) | none |
| H6 | Writers and DTOs stop. The content hash keeps hashing the stored value as written. Config keys and the EB code leave when the version floor passes H3's tag. | none | none; `pf_candidates.difficulty` and `item_parameter_state` join arc J's drop list if the owner approves |

So three tags: H3 and H4 each change stored projections, and H5 changes which items are reserved as measurements
(the 2026-10-17 rule). §7 has the order and the alternatives.

The decisions I need are in §11. Three come first:

- **Q1:** where mastery's `b` comes from now the label is gone. I recommend dropping the item term. That is H2's arm
  (b) exactly.
- **Q2:** where surprise's prediction comes from. I recommend AD's serve-time receipt, which is arm (c) with the
  prediction recorded at serve rather than recomputed.
- **Q3:** what the upgrade does to history. I recommend re-deriving it, as RO1 did.

## 1. What H2 measured, in the terms this note uses

Two of H2's arms (`docs/reviews/difficulty-four-way.md`) map directly onto the choices below.

**Arm (b), label off the mastery path.** This is `mastery.irt.difficulty_from_prior = false`: every reader of the
seam gets `b = difficulty_default = 0`.
- Synthetic vault: mastery changed in 3 of 4 LOs, median logit-mean shift −0.115. Surprise changed in 12 of 12 rows,
  median predicted-correctness shift +0.059. Queue top-3 overlap 2 of 3, Spearman 0.567, Kendall 0.444. No due date
  moved.
- Owner copies, in words: mastery changed on two of three vaults. The queue moved slightly on two, including one
  where mastery did not change (the scheduler reads the label itself). No direction flipped. No due date moved.

**Arm (c), surprise from AD.** Only surprise reads AD's predictive `p̄`, as `b' = μ_prior − logit(p̄)/a`.
- Synthetic vault: mastery and the queue identical to (a). Surprise changed in 12 of 12 rows, median
  predicted-correctness shift +0.108. Tiers: item 10, population 2.
- Owner copies: surprise rows only. No direction flipped.

**Arm (d), both.** Mastery and queue as (b), surprise as (c).

H2's `p̄` was AD's prediction recomputed by replaying AD's events up to each attempt. The design in §3.3 reads
instead the `p̄` that AD recorded when it served the item. The two can differ, so §10 has a comparison step.

## 2. The decisions everything hangs on

### 2.1 Mastery's `b` without the label (Q1)

The label gave each item a `b`. Without it, mastery's EKF needs one from somewhere. No constant may be invented.

| Option | What it is | What it does to H2's numbers | Firewall |
|---|---|---|---|
| **(i) A default.** `b = mastery.irt.difficulty_default` | Today's fallback for an item with no label. Every vault's default is 0 unless its config sets one; §10 checks that on the copies. | Exactly arm (b): the rows above. | Unchanged. |
| **(ii) AD's implied `b'`.** Mastery reads arm (c)'s `b'` | Mastery's prediction becomes AD's `p̄`, so the EKF learns from AD's residual. | Not measured: H2 fed `b'` to surprise only. It would need a new arm (e). Expected: every attempt with an AD prediction moves mastery. The queue moves through mastery. AD's reading terms, lessons and couplings then move mastery. | Lifts A2's "never writes mastery" and A12 limit 2 (reading then moves mastery, which is evidence). Mastery and AD would no longer be two estimates that can check each other. |
| **(iii) Drop IRT's item term.** `p = σ(a·(μ − b_prime))`, where `b_prime` is the priming offset for a primed answer and 0 otherwise | Same as (i) at `difficulty_default = 0`, with no knob left. | Exactly arm (b) on any vault whose default is 0. | Unchanged. |

**Recommendation: (iii).** It is the measured arm. It sets no value anyone chose for an item, and it removes the
last per-item difficulty input to evidence. `difficulty_default` then retires with the other label fields (§6).

The 0 here is not a constant. It is "no term": the 2PL reduced to its learner term. With `a = 1` (today's
`discrimination_default`, untouched) it is the plain logistic on mastery's logit.

The priming offset (`priming_b_offset`, 2.0) stays. It is a fact about the attempt (the source was just re-read),
not about the item, and H2 kept it in every arm. Whether that 2.0 is itself a made-up constant is outside arc H. I
note it for the owner and do not change it.

### 2.2 Surprise's prediction (Q2)

The owner leans to arm (c): the prediction comes from AD's forecast, the formulas stay, and Bayesian surprise keeps
describing the mastery update. The question is where AD's forecast is read from, at grade and in replay.

| Option | Live grade | Replay | History before the tag | Cost and risk |
|---|---|---|---|---|
| **(a) The serve-time receipt.** At every plan presentation, AD's serve hook records `ad_threshold@subject` (never-attempted item) or `ad_threshold_repeat@subject` (repeat) as an `item_unassisted_success` receipt with `p = p̄` and the three category probabilities, bound to the presentation (`adaptive_difficulty/serve.py`, `serving.py:396`, `repeat_receipts.py:52`). Surprise reads the receipt of the attempt's `practice_attempts.plan_presentation_id`. | One indexed read in the grade (`idx_forecast_receipts_plan_presentation`). | The same read. Receipts are append-only raw rows, so replay reproduces the grade exactly, whatever AD becomes (ADM2a, H4). No change to the rebuild order. | Receipts exist since AD1 for first presentations and since EPp for repeats. History is covered wherever they were recorded. | Covers plan-served attempts only. Probes, delayed checks, lesson checks, teach-back, workbench and other non-plan answers fall back. A protected item gets no receipt (A8), so it falls back too. §10 counts the coverage. |
| **(b) A grade-time receipt.** At grade, AD's snapshot as it stood before the attempt, written as a new receipt kind in `forecast_receipts`, bound to the attempt | An AD snapshot read in the grade transaction. It is cached by events fingerprint, so after a serve this is usually a hit; otherwise a full AD replay inside the grade. | Reads the receipt. | None: history falls back, or is snapshotted at upgrade as in L4-2's option 2. | Coverage of every attempt AD can read, at grade-path cost. The kind's vocabulary lives in code (`FORECAST_KINDS`); `binding_kind` and `scope` have no CHECK, so no migration (to confirm in the build). |
| **(c) Recompute in replay.** AD's replayer runs before `learning_state` and records a pre-attempt `p̄` for every graded attempt (H2's prefix method, in `src`) | As (b), at grade. | O(n) AD prefixes per rebuild, or the observer widened to every graded attempt. | Recomputed for all history. | Every AD successor then moves every historical surprise row. It also reorders the rebuild (`adaptive_difficulty` before `learning_state`). |

**Recommendation: (a), with (b) only if (a)'s coverage on the owner copies is too thin to be worth it.** (a) puts
into surprise what AD predicted *before the answer, when it served the item*. That is the honest meaning of a
predictive surprise. It needs no new writer. It is frozen, so AD's later successors never rewrite past surprise. The
fallback for an attempt with no receipt is the mastery prediction under §2.1, which is H2's `default` tier.

H2's `population` tier is already inside a receipt: AD computed `p̄` for an item whose cell had no coordinate through
its own projection when it served it.

**Rules (a) needs, each a choice I am stating, not something I found:**

- **Which receipt.** The subject view's (`@subject`), the view serving reads (H2's choice). Not `@subject_uniform`,
  not `@lo`.
- **Which attempt.** The first graded attempt bound to the presentation, on the receipt's item. A later attempt on the
  same presentation (a retry after feedback) is primed or falls back. A receipt with `status != 'ok'`, an unreadable
  `p`, or one recorded after the serve (`valid_for_serve`, the scorer's rule) falls back.
- **Priming.** For a primed attempt the receipt's logit is shifted by `a·priming_b_offset`. That is the same shift
  H2 applied to `b'`, and the same one the mastery path applies.
- **The form.** Surprise's innovation is `(y − p̄_eff)/√(H²P + R_y)`, computed around `b' = μ_prior − logit(p̄_eff)/a`
  as in H2. `y` stays the rubric fraction. Q4 (§11) asks whether to compare against AD's expected category instead.

### 2.3 The upgrade and history (Q3)

| Option | What the upgrade does | Replay of a vault below the tag |
|---|---|---|
| **(i) Re-derive history** (`Link(tag, whole_vault_rebuild)`) | Every LO's mastery is replayed with the item term dropped. Every surprise row is rebuilt from its receipt or the fallback. This is what RO1 (mvp-0.46) did for intervals. | The predecessor path (label, EB if switched on) runs unchanged, so a vault at mvp-0.70 rebuilds to its old rows. |
| **(ii) Start at the upgrade** (`idempotent_projection`) | Attempts before the tag keep label-based mastery steps and surprise. Later attempts use the successor. | Same, plus mixed histories: replay must know each attempt's tag, which today's replay does not key on per attempt. |

**Recommendation: (i).** Mastery is a running state. A half-label, half-no-label history is neither model, and
replay has no per-attempt tag to switch on. The receipts make history's surprise reconstructible from recorded facts.

## 3. H3: mastery and surprise

### 3.1 Every reader today, and its fate

Readers through the seam (`learner/mastery.py:806`, `item_irt_params`; `:831`, `resolve_item_irt_params`). At the
tag the seam returns `(a_default, 0.0)` (§2.1 option iii) and ignores `item_state`. Every reader below then follows
without its own change.

| File:line | Reader | Kind | After H3 |
|---|---|---|---|
| `attempts/attempts.py:4619`, `:4627` | `_grade_evidence`: mastery's `(a, b)`, priming offset | evidence | No item term. Priming stays. |
| `attempts/attempts.py:4628`, `learner/recall_coverage.py:665` | `predicted_correctness_from_prior`: the grade's `expected_correctness`, read by event severities (`recall_coverage.py:482`) and the debug trace (`attempts.py:5197`) | evidence | From the no-item-term `p`. Never from AD (A2). |
| `attempts/attempts.py:4917` | `_belief_update`: the authored `b` as the EB prior | evidence (dark) | Not run at the tag (§3.4). |
| `attempts/attempts.py:4929`, `attempts/surprise.py:56` | `compute_surprise`: innovation, predictive surprise, direction, interval factor | prediction | Predictive part from the receipt (§2.2). Bayesian surprise unchanged in form (mastery's KL). Interval factor: §3.5. |
| `delayed_checks.py:106` | `predicted_item_success`: delayed check's item choice, with the EB posterior | measurement choice | No item term. Not AD: A11 bars an estimated `b` from a cold measurement's item choice. |
| `diagnosis/probes.py:306` | probe response curve, EIG | selection | No item term (Q6). |
| `daily_plan/lesson_suggestion.py:180` | LO prediction (LO prior only) | selection | No item term. |
| `scheduling/scheduler.py:3043` | `_practice_information` | selection | No item term. This is the direct queue move H2 saw (Q6). |
| `scheduling/selection_rewards.py:402` | demand vector's IRT terms | selection | No item term (Q6). |
| `teacher/brief.py:291` | LO prediction, interval and words | display | No item term. |
| `teacher/checks.py:129` | `cold_reference` | measurement | No item term. |
| `teacher/checks.py:153` | `check_mass`: a check's sensitivity and the pool's mass | evidence mass | No item term. Never AD (A2). |
| `learner/lesson_weight.py:447`, `:791` | `recorded_trajectory`, `_outcome_item_params` (static helper, L4-2) | evidence fit | No item term for successor epochs. §9 covers L4-2. |
| `placement/predictor.py:91` | placement item parameters, with cached EB state | selection, claims | No item term. The version hash moves (§3.7). |
| `adaptive_difficulty/forecasters.py:77` | AD's in-process comparator features (`mastery_ekf`, `lo_general+composite`), LLM labels already defaulted | comparator receipt | No item term. Receipts written at serve after the tag differ. Recorded ones stand. |
| `field/outcomes.py:617`, `:615-662` | historical features `a`, `b`, `difficulty_source` and the `_missing_historical_prior` flag | field baseline (DERIVED `facet_outcome_observations`) | `b = 0` for every item. The flag reads "no item term" (to word in the build). |
| `field/predictors.py:202` | LLM-label variance | field baseline | Unread at the tag (no label `b` to doubt). |
| `field/success_head.py:327`, `:370` | the solver-panel `b` feature (`difficulty=True` arms) | field baseline | Dead after the tag, because the seam no longer passes the panel's label (Q7). |
| `field/probability_states.py:326-343` | explains the authored or measured prior in the item view | display | Says "no item term" at the tag. The DTO goes in H6. |

Direct label reads that belong to H4, H5 or H6 are listed in those sections. The guard
(`tests/test_difficulty_kinds_apart.py`) is updated in every step that changes a site, so its counts stay exact.

### 3.2 What replaces it

- **The seam** (`mastery.py:806-848`). At or above the tag it returns `(irt.discrimination_default, 0.0)`. Below the
  tag it runs today's code (label, LO prior, default, EB). One predicate over `successors_from(H3_TAG)` decides it.
  Every reader follows from that one gate. No reader branches itself.
- **Surprise** (`attempts.py:4929`, `surprise.py:56`). `compute_surprise` gains one input: the prediction it scores
  against (`p̄_eff` with its source), or none, meaning the fallback. Mastery's `(a, b)` still drive the update.
  `_grade_evidence` reads the bound receipt through one new read in `db/stores` (owner: the AD receipts store) and
  passes it in.
- **The surprise row** (`attempt_surprise.predicted_score_dist_json`). `a`, `b`, `mu_z` and `expected_correctness`
  keep meaning **mastery's** prediction, because three readers rely on that:
  - `learner/calibration.py:69` calibrates mastery against it;
  - `scheduling/evaluation.py:202` evaluates mastery's predictions;
  - `learner/lesson_weight.py:423` reads `a` and `b` (L4-2).

  New keys record what surprise scored against: `prediction_source` (`ad_receipt` or `mastery_irt`), `receipt_id`,
  `forecaster`, `p_ad` and `p_effective` (after priming), and `sigma_z` stays surprise's own. The column is JSON, so
  there is no migration. H2's arm (c) wrote `b'` into `b`; this design does not, so the meaning of `b` does not
  silently change for those readers.

### 3.3 Stored values that change on upgrade (option 2.3 i)

| Table | What moves |
|---|---|
| `learning_object_mastery` | Every LO whose history includes a labelled item or an LO prior: arm (b)'s deltas. |
| `attempt_surprise` | `predicted_score_dist` (mastery's `b` becomes 0, plus the new keys), `predictive_surprise`, `surprise_direction` (H2: no flip on the owner copies under (b), (c) or (d)), `bayesian_surprise` (through mastery's posterior only). The recorded `fsrs_interval_factor` stays 1.0 (removed since mvp-0.46). **To verify in the build:** what the whole-vault rebuild does to `triggered_actions_json`, `suppressed_actions_json` and `gate_diagnostics_json`. The live follow-up gate writes them (`content/proposals/proposals.py:1546`, `db/stores/attempts.py:1278`), and I did not establish whether `learning_state`'s replay restores, recomputes or clears them. |
| `item_parameter_state` | Empty at the tag (EB never runs). Rows of a vault that had EB on are cleared by the rebuild. |
| `facet_outcome_observations` (field) | Features `b` and the source flag. |
| `facet_recall_state`, `facet_capability_evidence` | Through event severities (`expected_correctness`). To be measured by the shadow rebuild. |
| `lesson_weight_*` | Refitted from the changed curves. |
| Due dates | None expected (interval factor removed; FSRS reads neither mastery nor the label). |
| Queue | As arm (b): through mastery and through the scheduler's and rewards' own seam reads. |
| Placement predictions, VOI receipts | New serves only. Recorded receipts stand. |

### 3.4 The EB path

`update_item_difficulty` (`mastery.py:851`), the `item_state` argument of the seam, `ItemParameterState`'s `b`, the
reads at `attempts.py:4033`, `delayed_checks.py:106` and `placement/predictor.py:91`, and the config fields
`eb_difficulty_enabled`, `b_prior_variance`, `b_learning_rate_scale`, `b_max_step` and `b_var_min`.

- At the tag none of it runs, whatever the switch says. `item_parameter_state` stays empty.
- Below the tag it runs as today (the predecessor path). Q8 asks whether it may go sooner.
- Code and config leave in H6, or when the floor passes the tag (§6).

### 3.5 The interval factor

At or above mvp-0.46 the factor is not applied (`scheduler.surprise.remove_interval_factor`, a kill switch, default
on). A vault with it off would let AD's prediction set FSRS intervals through the factor. **Rule:** the factor's
residual is always mastery's (the fallback prediction), never the receipt's. FSRS then reads nothing of AD's under
either setting.

### 3.6 Migrations

None. The receipt read uses an existing table and index. The surprise row's new keys go in its JSON column.

If Q2 picks (b), the grade-time receipt is a new `kind` value in code only (to confirm that no CHECK constrains it).
If the owner wants (b) together with a snapshot of history at upgrade, that is L4-2's option 2 and its storage
(§9).

### 3.7 Identity pins and goldens

| Pin or golden | Expected | Why |
|---|---|---|
| C1, the placement predictor version hash (whole `MasteryConfig`) | **Move deliberately in H3's commit** | The predictor's `b` changes at a fixed config. Without a move, its forecasts across the tag share one version label and VOI receipts would be deduped across two meanings. H3 adds the item-term generation (the tag's flag) to the hashed view and regenerates. |
| C2, the field predictor version hashes | Move deliberately | Same reason. |
| C2p, the cached LLM probability position key (`asdict(ItemFeatures)`) | Values move for items that had labels, not shape | `b = 0` in the features. If the route is retired (strategy §2.11 lists `field_llm_probability` as retired), nothing is reused and nothing is lost. To confirm. |
| `tests/goldens/due_queue/*` | Move (`difficulty_b` 0.25 → 0.0) | The scheduler's seam read. |
| `tests/goldens/grade_application/history.json` | Expected **not** to move: its `b` is already 0.0, or −2.0 when primed, and it has no AD receipt | To verify. |
| `mastery_seed_replay.json`, `placement_stored_misses.json` | To verify | |
| `tests/goldens/effective_defaults.toml` | The tag line only | No default changes. |
| A9 and A19 (whole `PracticeItem` dumps) | Unchanged | The fields stay on the model. |

### 3.8 Tests H3 adds

- The seam at and below the tag, with literal values. H1's 24 cases stay the predecessor's.
- Surprise from a bound receipt, primed and unprimed, and every fallback: no presentation, no receipt, a bad receipt,
  a second attempt on one presentation, a protected item.
- The row keeps mastery's `a`, `b` and `expected_correctness`.
- The predecessor replays to its golden at mvp-0.70.
- An upgrade from mvp-0.70 and a second, idempotent rebuild.
- H2's script reproduces the successor's rows as its arm (d) on the synthetic vault, after the script learns to read
  receipts (§10).
- A guard that neither `item_parameter_state` nor a label field is read at or above the tag.
- AD's protection guard classifies `attempt_surprise` explicitly as `DENIED`. Today it is refused only as
  unclassified, which is fail-closed but implicit.

## 4. H4: AD's own signal

| File:line | Reader | After H4 |
|---|---|---|
| `adaptive_difficulty/serve_inputs.py:117-120` | `_z_llm`: the label as a signal, frozen into `item_serve_inputs` at serve | Not computed. New rows record it unavailable with `why: "retired"`. |
| `adaptive_difficulty/replay.py:246-249` | `_historical_signals`: `z_llm` for an item with no frozen inputs | Not read. |
| `adaptive_difficulty/replay.py:254` | `_frozen_signals`: reads every recorded signal, `z_llm` included | Skips `z_llm`. The recorded rows stay as written. |
| `adaptive_difficulty/forecasters.py:74-88` | comparator features; `difficulty_source` into `ItemFeatures` | `b` already from the seam (H3). `difficulty_source` stays a transported value until H6. |
| `adaptive_difficulty/data_check.py:78`, `:111-113` | the label/correctness correlation report | Kept as a report on what the label was, reading only recorded values. Or removed: Q9. |
| `adaptive_difficulty/generation.py:11` | the contract text's note that `llm_estimate` stays on the item | Reworded in H5 with the prompts. |

**Kept:** `z_panel` (`serve_inputs.py:134-156`). It is a measurement from the solver panel's rates in
`pf_candidates.panel_json`, not the label, so H4 does not touch it.

**Stored values on upgrade:** `ad_state`, `ad_attempt_trace` and `item_forecast_scores` (whole-vault rebuild of AD).
The `α` for `z_llm` leaves the priors, so AD's priors version moves (`ad_priors_vN`).

**Replay of old rows:** the predecessor's code path (with `z_llm`) runs below the tag. Receipts recorded before the
tag keep their `z_llm`-influenced `p̄`. Under §2.2 (a), surprise rows read those recorded values, which is correct:
it is what AD predicted then.

**Pins:**
- AD's events fingerprint and state hash, which hash `ItemSpec` signals and the banks.
- The `forecaster_version` strings (`THRESHOLD_VERSION:PRIORS_VERSION:HYPER_VERSION`).
- Selection receipts' state hashes.

All move deliberately in H4's commit.

**Proof:** AD's scoring report with and without `z_llm`. H2's script already produces it (`--ad-without-z-llm`), and
H4's shadow rebuild report produces it again on the final code.

## 5. H5: exam strata, filters, authoring, copies

### 5.1 Exam pools (`goals/exam_pool.py:42-55`, `:194`, `:242`, `:250`)

Ties in the reservation prefer a stratum (`<0.34`, `<0.67`, else, or `unknown`) not yet represented.

| Option | Effect |
|---|---|
| **Drop the stratification** (recommended in the strategy) | Ties go to the next rule (novel surface group), then the item id. |
| Stratify on AD's predictive frozen at pool build | AD reading candidate exam items before reservation. A8 withholds protected material from AD, so this needs the protection argument made explicitly. |

Recorded reservations keep their `difficulty_stratum` (written provenance, `migrations/023_exam_pool.sql`). Only new
reservations change. Pools are raw reservations, not replayed, so the tag exists for the 2026-10-17 rule: it changes
which items become held-out measurements.

**Proof:** a read-only count of unreleased pools by stratum on the copies (§10), and on a copy the pools
`reserve_exam_pool` would choose with and without strata for each active goal. That second part is a script, not a
SQL query.

### 5.2 Index filters

`practice_index/retrieval.py:174-216`, `:292-294`; `practice_index/tool.py:32-33`;
`learnloop_sidecar/handlers/practice_index.py:27-28`.

`min_difficulty` and `max_difficulty` filter on the label. **Remove the parameters.** Accepting and ignoring them
would answer a different question than the one asked. This is a contract change for the agent tool and the RPC. No
CLI parameter names them, so `tests/cli_surface.json` is unaffected (checked).

### 5.3 Authoring

These prompts and gates ask for or check a label:

- `content/authoring/practice_generation.py:464`, `:661`: band inversion through `difficulty_prior_scale`.
- `practice_generation.py:1802`: band check of a declared label.
- `practice_generation.py:2195`, `:2205`, `:2325`: contract text.
- `tutor/promotions.py:985-1032`: the recommended difficulty band.
- `content/authoring/rung_variants.py:108-145`, `:886`: direction audit and prompt.
- `diagnosis/contrast_pairs.py:466`, `:486`: band audit.
- `substrate/surface_mint.py:205`, `:293`: bounds gate.
- `ops/pf_generation.py:1255`: panel-to-label scale.
- `content/proposals/ai_contracts.py:841`: "Set `difficulty_source`".

**Change:**
- Band prompts move to AD's generation contract, which needs no band.
- Rung "easier/harder" stays a relation and is audited by its held axes, not by the number.
- Each prompt bumps its version. The golden prompts and `tests/goldens/synthesis_tail/*` (they carry `difficulty` in
  payloads) are updated knowingly.
- The structured-prompt identity pins move deliberately.

**Result schemas:** removing `difficulty` from authoring and proposal result models changes `model_json_schema`, so
A20 (schema-keyed checkpoint keys) moves, and an in-flight generation's checkpoint is not reused. Two options:
- remove them in H5 with the prompt bumps (one cost, said in the landing note);
- keep the fields optional in the schemas and stop asking for them, and remove them later.

I recommend the first: the prompt bump already invalidates those checkpoints.

### 5.4 Copied values

These stop copying the label:

- `tutor/teach_back.py:935-936`, `:1375`;
- `diagnosis/probe_remint.py:188-189`;
- `content/authoring/rung_variants.py:281`, `:849`;
- `diagnosis/contrast_pairs.py:642`;
- `teacher/actions.py:191`;
- `instructional/tools.py:276`;
- `diagnosis/causal_probe_coherence.py:1268`;
- `ops/pf_generation.py:204`, `:488`, `:1739`, `:1787`.

No meaning moves, so there is no tag. A new item is simply written without the field.

## 6. H6: writers, DTOs, the hash

- **Writers stop:**
  - `content/authoring/exercise_authoring.py:844-845`;
  - `content/proposals/ai_contracts.py:209`, `:550` (if §5.3 kept them);
  - `ops/pf_publish.py:169-170`;
  - `curriculum/golden_path_fixture.py:296`;
  - `learner/recall_calibration.py`'s synthetic item.

  `vault/writer.py:89-90`, `:121` and `db/stores/pf.py:22` are order and transport lists. They stay while the fields
  and the column exist.
- **The model fields stay optional and readable**, so old YAML still loads. A9 and A19 dump whole items, so the fields
  must stay on the model.
- **The content hash** (`vault/hashes.py:37`) keeps hashing the stored value as written. This is the one permanent
  reader, labelled "frozen hash input". A test pins an existing item's hash on the head fixture.
- **DTOs go:**
  - `learnloop_sidecar/handlers/serializers.py:421`, `:546`;
  - `handlers/facets.py:122`;
  - `handlers/knowledge_map.py:170`;
  - frontend: `apps/learnloop-tauri/src/api/dto.ts` `FacetMasteryPracticeItem`, `KnowledgeMapPoint`,
    `PracticeItemDetail`, `ToolPracticeItemDto`, `LearningObjectDetail.difficultyPrior`,
    `ReaderExerciseImportedItem` (`PracticeItemStateDto.difficulty` is FSRS D and stays);
  - `components/InspectorOverlay.tsx:405-409`, `:655-659`;
  - `screens/KnowledgeMapScreen.tsx:507`;
  - `screens/TodayScreen.tsx:1607-1610`.

  A screen whose layout would need redesigning without them goes on the UX list instead.
- **The terminal app's H1-1 crossing** (`tui/screens/practice.py:519-525`) goes with the scalar bar. That closes the
  strict xfail.
- **Config and EB code.** `RETIRED_FIELDS` must never list "a field something should read"
  (`config/retired.py`). The predecessor path below H3's tag still reads `difficulty_from_prior`,
  `difficulty_prior_scale`, `difficulty_default` and the five EB fields. So:
  - they leave the models only when the version floor (ADR-019) reaches H3's tag;
  - they then go into `RETIRED_FIELDS` with their defaults, so C1 and C2 keep their post-H3 bytes;
  - the label branch of `item_irt_params`, `update_item_difficulty` and the EB reads are deleted in that same commit.

  Until then H6 removes writers and DTOs only. Q10 asks whether to move the floor right after the owner's vaults are
  upgraded.
- **`mastery.irt.difficulty_from_prior`** is a kill switch (`config/kill_switches.py:143`). Its off state is
  exactly H3's mastery path, so the successor makes it meaningless. It retires with the floor, like the others.
- **Columns:** `pf_candidates.difficulty` and the `item_parameter_state` table go on arc J's drop list if the owner
  approves.
- **The vault's Learning System and Concepts notes** are regenerated with the landing.

## 7. Tags and landing order

**Tags, in landing order** (mvp-0.69 is inline checks; mvp-0.70 is L4-2):

1. **mvp-0.71, H3.** It changes mastery and surprise for history and for new answers. `Link(tag, whole_vault_rebuild)`.
2. **mvp-0.72, H4.** It changes AD's state for history. `whole_vault_rebuild` (AD's replayers). It lands alone so its
   effect on AD's scoring is seen apart from H3's.
3. **mvp-0.73, H5's exam pools.** Replay is unchanged but new reservations differ. `idempotent_projection`.

H5's other parts and H6 change no persisted meaning, so they have no tag.

**Fewer tags:** if the owner accepts dropping the strata without a separate look, H5's pool change can ride on H3's
tag (two tags in all). I do not recommend folding H4 into H3: AD's and mastery's effects would land together, and
neither could be read alone.

**Order of landings:**

1. **L4-2 (mvp-0.70)** first, so H3 builds on its capture (§9).
2. **H3**, then its owner-copy report and the upgrade of the owner's vaults to mvp-0.71.
3. **H4**, with AD's scoring report. If ADM2a is near, H4 still goes first: ADM2a's report should compare against an
   AD that no longer reads the label (Q11).
4. **H5**: the pools (mvp-0.73) and the authoring prompt bumps can land separately ("split per review").
5. **H6.**
6. **The floor move to mvp-0.71 or later** and the config and EB deletion (§6).

**Stopping point 9:** do not stop between H3 and H6 unless the successor serves cleanly. Under this design the label
is unread at the tag, so readers and writers disagree only in that items are still written with a field nothing
reads. That is harmless, but it is the reason H5 and H6 follow promptly.

**Migrations:** none in H3 to H6 (§3.6). The last migration on main is 269 (`269_ink_transcriptions_guard.sql`).
L4-2 may take one (§9). Drops go to arc J.

## 8. The firewall change, stated exactly

**Today.** AD is a predictor (A2). It never writes `grading_evidence`, mastery, facet recall, FSRS state or
certification credit. Reading is a learning opportunity whose effects stay in prediction and selection (A12 limit 2).
`spec_router_objective_v1.md` §11 lists "the surprise source: AD's item-conditioned predictive" as needing this ruling.

**Lifted, and only this.** AD's serve-time forecast receipt for the attempt's own presentation
(`forecast_receipts`, kind `item_unassisted_success`, forecaster `ad_threshold@subject` or
`ad_threshold_repeat@subject`, status `ok`, its `p`) may be read by `compute_surprise` as the prediction the answer
is scored against. That sets four things:

- `predictive_surprise`;
- `surprise_direction` (except the error-type rule, which reads the active errors);
- `predicted_score_dist.p_ad` and `p_effective`;
- the residual behind the direction.

(With Q2 (b): also AD's grade-time receipt of the same kind, bound to the attempt.)

**So these readers may now see AD's influence**, all of them selection or diagnosis triggers:

- the follow-up gate (`diagnosis/followups.py:254`: direction AND Bayesian surprise);
- the gate score (`diagnosis/gate_score.py:253-254`);
- the re-probe trigger (`diagnosis/probe_episodes.py:697-700`: direction AND predictive surprise);
- the quantiles' sample selection (`diagnosis/signal_quantiles.py:67`: negative direction);
- the miss-cause read (`router_objective/miss_cause.py:380`);
- the Teacher's read of predictive surprise (`teacher/service.py:2670`);
- the EVSI live report.

**Through AD, reading opportunities, lessons and couplings may now change a follow-up or a re-probe.** This needs A12
limit 2's list ("draws, forecasts and readiness numbers") to gain "the surprise's prediction, through AD's recorded
forecast". It is the amendment the owner rules on.

**Still may not flow:**
1. **Into mastery.** Not its `b`, prediction, gain, posterior or variance floor, and not `bayesian_surprise`, which
   stays mastery's KL from prior to posterior (§2.1 recommends iii; option ii would lift this and A2).
2. **Into the grade's `expected_correctness`, event severities, facet recall, capability evidence, `grading_evidence`,
   or any evidence mass.** That includes lesson-check masses (`teacher/checks.py:153`) and the lesson-weight fit.
3. **Into FSRS state or intervals.** The interval factor's residual is mastery's in every configuration (§3.5).
4. **Into certification, levels, requirement points or a cold measurement's item choice** (A11). That includes
   delayed checks' item choice (`delayed_checks.py:106`).
5. **Into AD itself.** AD's guard refuses `attempt_surprise` (H3 classifies it `DENIED` explicitly) and
   `learning_object_mastery` (except the named `mastery_ekf` comparator carve-out, unchanged). So surprise cannot feed
   back into the forecasts it is scored against. **This binds ADM3:** RE8's memory inputs list "surprise". If ADM3 is
   built after H3, it may read only `bayesian_surprise` (mastery's, AD-free), never the predictive surprise or the
   direction. Otherwise AD would read its own residual (Q12).
6. **Answer text, salience, dwell or minutes** into anything, exactly as today. The receipt carries none of them.

**What the lift does not need:** no new writer for AD, no table AD writes, no change to AD's reads. It is a read by
the grade of a receipt AD already writes.

## 9. L4-2's capture after H3

L4-2 (`docs/reviews/algorithm-mvp-0.70.md`, mvp-0.70, being built) captures, per newly applied grade epoch, "the
effective discrimination and difficulty actually passed to mastery after empirical-difficulty and priming
adjustments".

**After H3 the capture holds mastery's own pair:** `(discrimination_default, −priming_b_offset)` for a primed answer
and `(discrimination_default, 0.0)` otherwise. It holds no label-derived `b` (unread) and no EB `b` (never run). It
never holds AD's `p̄` or `b'`, because AD does not reach mastery (§8.1).

Consequences:

- **For epochs graded at or above H3's tag,** L4-2's defect (the reconstruction depends on the item's current authored
  content) disappears. The pair no longer depends on content, so a capture and a reconstruction agree. L4-2's owner
  choice (start at upgrade, or freeze history) then matters only for epochs before H3's tag.
- **If H3 lands before L4-2's captures** are written on a vault, which it cannot under the order of §7, the capture
  would start with constant pairs. Nothing breaks.
- **H3 needs nothing from L4-2's storage.** Surprise's prediction lives in `forecast_receipts` (§2.2 a). The
  surprise row's `a` and `b` keep mastery's meaning, which `lesson_weight.py:423` reads (§3.2).
- **One request to L4-2's builder** if L4-2 makes a new table: give it a JSON detail column. A later step (Q2 (b) with
  a historical snapshot) could then add a key without amending a landed migration. That is a suggestion, not a
  dependency.

## 10. The owner-copy procedure (read-only)

For the orchestrator, on backup-API copies (`learnloop.db.copies.copy_tree_with_databases`), through the scratch
wrapper. Counts and digests only go into a tracked file, never ids or values.

**Before building H3, to decide Q2 and Q8.** `COPY_DB` is the copy's `state.sqlite`.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
PRAGMA query_only = ON;
-- Graded attempts and how many a serve-time AD receipt covers (the first attempt bound to its presentation).
WITH firsts AS (
  SELECT a.plan_presentation_id AS pid, min(a.created_at || a.id) AS first_key
  FROM practice_attempts a WHERE a.plan_presentation_id IS NOT NULL GROUP BY a.plan_presentation_id
), attempts AS (
  SELECT a.id, a.primed, a.attempt_type, a.plan_presentation_id,
         (a.created_at || a.id) = f.first_key AS first_on_presentation
  FROM practice_attempts a LEFT JOIN firsts f ON f.pid = a.plan_presentation_id
), receipts AS (
  SELECT plan_presentation_id AS pid, count(*) AS n FROM forecast_receipts
  WHERE kind = 'item_unassisted_success' AND status = 'ok' AND p IS NOT NULL
    AND forecaster IN ('ad_threshold@subject', 'ad_threshold_repeat@subject')
  GROUP BY plan_presentation_id
)
SELECT count(*) AS attempts,
       count(*) FILTER (WHERE plan_presentation_id IS NOT NULL) AS bound,
       count(*) FILTER (WHERE first_on_presentation AND r.n > 0) AS with_ad_receipt,
       count(*) FILTER (WHERE first_on_presentation AND r.n > 0 AND primed) AS with_ad_receipt_primed,
       count(*) FILTER (WHERE r.n > 1) AS presentations_with_two_receipts
FROM attempts LEFT JOIN receipts r ON r.pid = attempts.plan_presentation_id;
-- The same split by attempt type (no ids).
SELECT attempt_type, count(*) AS attempts, count(plan_presentation_id) AS bound
FROM practice_attempts GROUP BY attempt_type ORDER BY attempt_type;
-- EB: rows ever written (the config is read separately).
SELECT count(*) AS item_parameter_rows FROM item_parameter_state;
-- Exam pools: unreleased reservations by stratum.
SELECT coalesce(difficulty_stratum, 'null') AS stratum, count(*) AS reserved
FROM exam_pool_items WHERE released_at IS NULL GROUP BY stratum ORDER BY stratum;
SELECT count(*) AS foreign_key_violations FROM pragma_foreign_key_check;
PRAGMA integrity_check;
SQL
```

- **Config:** `learnloop config effective --vault "$COPY" --json`, through the wrapper. Report only
  `mastery.irt.eb_difficulty_enabled`, `mastery.irt.difficulty_default`, `mastery.irt.difficulty_from_prior` and
  `scheduler.surprise.remove_interval_factor`.
- **Label census:** the vault's YAML holds the labels, which SQL cannot see. Use a read-only extension of
  `scripts/difficulty_four_way.py`'s loader that prints items by `difficulty_source` (and `none`) and LOs with a
  `difficulty_prior`, as counts.
- **Two new arms for `scripts/difficulty_four_way.py`** (a script change only, its own small step with its tests):
  - (e) surprise from the bound receipt, with the fallback;
  - (f) (b) plus (e), which is H3 as designed.

  Each reports what H2's arms report, plus tier counts (receipt or fallback), the direction transitions, and the
  follow-up gate's would-fire count. It also compares the receipt `p̄` with H2's prefix-replay `p̄` per attempt where
  both exist (median and max absolute difference). This answers how far "AD at serve" differs from "AD just before the
  answer".

**After H3 is built, per the playbook (steps 7 and 8), on disposable copies of one predecessor backup:**

1. Record the original database hash. On the mvp-0.70 copy, run the inspections above and `learnloop rebuild
   --shadow --json`.
2. `learnloop upgrade --vault "$COPY" --to mvp-0.71`, then `learnloop doctor`, then the successor's shadow rebuild.
   Report mastery, surprise (and the stored follow-up actions, §3.3), facet and capability, lesson weight, due dates
   and queue deltas, plus the receipt/fallback tiers.
3. Rebuild again. The semantic digests must agree with step 2. Check the original database hash. Report before any
   live upgrade.

H4 repeats steps 1 to 3 with AD's scoring report. H5's pools add the pools-with-and-without-strata count.

## 11. Open questions, with options

| # | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Mastery's `b` without the label | (i) `difficulty_default`; (ii) AD's `b'`; (iii) drop the item term | (iii), which is exactly arm (b) (§2.1) |
| Q2 | Where surprise reads AD | (a) serve receipt; (b) grade-time receipt; (c) recomputed in replay | (a), plus (b) only if coverage is thin (§2.2) |
| Q3 | History at upgrade | (i) re-derive; (ii) start at upgrade | (i) (§2.3) |
| Q4 | What surprise compares the score against | `p̄` (unassisted success, as H2 did); or AD's expected category score from the receipt's three probabilities; or a categorical surprise on the observed category | `p̄`: it is what H2 measured and the owner leaned to. Another form needs its own replay arm first. |
| Q5 | The firewall amendment of §8 | as written; narrower (direction only, not predictive surprise); or none (then surprise reads mastery's no-item-term prediction, and arm (c) drops out) | As written |
| Q6 | Selection readers (scheduler information, selection rewards, probes, lesson suggestion, placement) after the label | stay on "no item term"; or read AD's `p̄` later, each its own successor | Stay on no item term in H3. AD for selection is a later question, item by item. |
| Q7 | The field's solver-panel `b` feature (`success_head.py:327`) | let it die with the seam; or feed it from the panel's rates as AD's `z_panel` does | Feed it from the rates in H3. The panel is a measurement, not the label. If the owner prefers fewer moving parts: let it die and record that the `+difficulty` arms equal their base arms. |
| Q8 | The EB code | keep it for vaults below the tag until the floor passes H3 (the playbook's default); or delete now and refuse `eb_difficulty_enabled = true` at load, if the copies show it was never on | Keep until the floor. Deleting now needs a compatibility decision (`substrate.compat` rule). |
| Q9 | AD's label/correctness report (`data_check.py`) | keep, reading recorded values; or remove | Remove in H4. Its question is answered. |
| Q10 | When the label's config fields and EB code leave | at the floor move after every owner vault is at mvp-0.71 or later; or keep indefinitely | Move the floor right after the owner's vaults are upgraded, then delete in one commit (§6) |
| Q11 | H4 before or after ADM2a | before; folded into ADM2a; after | Before |
| Q12 | ADM3's memory inputs list "surprise" | Bayesian surprise only; or none | Bayesian surprise only (§8 item 5) |
| Q13 | Exam strata | drop; or AD-predictive strata frozen at build | Drop, unless the pools-with-and-without count shows pools losing their spread |
| Q14 | Authoring result schemas | remove the field in H5 with the prompt bumps; or keep it optional and unasked | Remove in H5 (§5.3) |
| Q15 | H5's pool change: its own tag, or on H3's | own (three tags); or on H3's (two) | Own |

## 12. Checked, and not checked

**Checked at `86f29b0d39`:**
- Every file:line in §3 to §6 against the code. The seam, `_grade_evidence`, `_belief_update` and `compute_surprise`
  were read whole.
- The serve hook's receipt writers and their names, the scorer's binding chain, `forecast_receipts`' schema and
  index, and `practice_attempts.plan_presentation_id`.
- AD's guard (no class for `attempt_surprise`, so refused; `learning_object_mastery` `DENIED` with the comparator
  carve-out).
- The surprise row's readers.
- The rebuild order (`adaptive_difficulty` after `learning_state`; this design needs no change to it).
- The kill-switch entry for `difficulty_from_prior`.
- `RETIRED_FIELDS`' rule.
- The identity sites C1, C2, C2p, A9, A19 and A20.
- The goldens that hold `b` or `difficulty_b`.
- The last migration number.

**Not checked:**
- What the whole-vault rebuild does to the follow-up actions stored on `attempt_surprise` (§3.3).
- Whether any CHECK constrains a new receipt `kind` (only needed for Q2 b).
- Whether `field_llm_probability` still reuses C2p's key.
- The grade-application, mastery-seed and placement goldens' behaviour under H3.
- Receipt coverage on any vault, and how the receipt `p̄` differs from H2's prefix `p̄`. Both are §10's job.

No test was run. No vault, copy or private file was read. No model was called.
