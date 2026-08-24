# Spec: Content-bearing misconceptions and discriminating diagnostic follow-ups

Status: draft
Motivating case: attempt `01KWZVQW28SAP6EYDXZTZAH6ZS` (linear_algebra fixture).
The grader precisely diagnosed a belief ("Q turns a vector into coefficients,
Q^T turns it back" — reversed coordinate-change roles), but every downstream
component operates on lossy projections of it (error *types*, facet IDs). The
follow-up selector therefore queued a paraphrase of the failed item
(`pi_diagnostic_orthogonal_diagonalization_inverse`), which is answerable
perfectly while holding the belief.

Target artifact (the exemplar this spec must be able to produce end-to-end):
a generated diagnostic that (a) is authored *from the belief statement*,
(b) forces a behavioral commitment a holder of the belief gets detectably
wrong (concrete Q^T x computation + "which of Qx / Q^T x is the coordinate
vector?" forced choice), (c) carries a rubric fatal error keyed to the
misconception, and (d) is validated by simulation before being queued.

Domain scope: the algorithm serves non-mathematical vaults (arxiv/transformers,
law/bar) equally. All constraints below are stated in domain-general form —
"forced application to a concrete instance with categorically divergent
outcomes" — with computation as merely the math-vault instantiation (law:
commit to a holding on a novel fact pattern; mechanism review: predict a
system's behavior under a stated change).

## 0. Gap analysis

Agreed changes from discussion:

- **C2 — misconception registry**: misconceptions become first-class,
  content-bearing records.
- **C3 — item discrimination metadata**: items declare which misconceptions
  their fatal errors catch; EIG keys on it.
- **C5 — facets stay coarse**: no facet-vocabulary growth; misconception
  records carry fine-grained targeting.

These alone do NOT produce the exemplar. Four additional pieces are required:

- **G1 — structured grader output.** `ErrorAttribution` (grading.py:87) has no
  field for the belief statement; the content exists only in free-text
  `evidence`. Without a structured statement there is nothing to normalize
  into the registry (C2 has no input).
- **G2 — routing.** Nothing fires generation: in the motivating case the
  paraphrase passed the facet-overlap gate, so `no_suitable_item` never
  triggered. With C3 metadata, routing becomes deterministic: active
  misconception + no discriminating candidate → intervention need.
- **G3 — diagnostic generation context + review policy.**
  `build_authoring_context` is subject/notes-scoped; there is no context
  builder that packages ⟨belief statement, learner's verbatim answer, source
  item, constraints⟩, and `evaluate_review_policy` has no checks for
  discrimination properties.
- **G4 — posterior update & resolution rekeying.** Misconception hypotheses
  must update from misconception-keyed fatal-error observations, and
  auto-resolve must be keyed by registry id with "clean attempt" restricted
  to attempts that could actually have caught the belief.

Supporting change:

- **V1 — sim discrimination gate.** Planted misconceptions in the sim harness
  (`sim/profiles.py`) are keyed by `facet_id` + the synthetic error type
  `sim_planted_misconception`; they carry no belief statement, so they cannot
  yet acceptance-test a generated diagnostic.

## 1. Data model

### 1.1 `misconceptions` table (new)

| column | type | notes |
|---|---|---|
| id | ULID pk | |
| learning_object_id | text | primary scope |
| concept_id | text | for neighbor propagation (mirrors `_neighbor_misconceptions`) |
| statement | text | normalized belief, learner-model phrasing: "believes Q maps standard vectors to eigenbasis coefficients (reverses Q / Q^T)" |
| signature | text | what a holder of the belief *does*: the misconception-consistent answer pattern graders/items key on |
| facet_ids | json | coarse facets implicated (C5: targeting resolution lives here, not in new facets) |
| severity | real | max over source events, decayed as in `build_hypothesis_set` |
| status | text | `active` / `resolving` / `resolved` |
| source_error_event_ids | json | provenance, append-only |
| created_at / updated_at / resolved_at | text | |

`error_events` gains a nullable `misconception_id` column. Error events remain
the raw per-attempt evidence; the registry row is the normalized belief.

### 1.2 Practice item schema (vault + proposals)

Rubric fatal errors gain an optional `misconception_id`:

```yaml
grading_rubric:
  fatal_errors:
    - id: fe_q_direction_reversed
      description: States or implies that Q (rather than Q^T) converts a
        standard-coordinate vector into eigenbasis coefficients.
      misconception_id: mc_01ABC...
```

Derived item-level view `discriminates: {misconception_id: [fatal_error_id]}`
(computed, not authored). No change to `evidence_facets` (C5).

### 1.3 `item_misconception_discrimination` table (new)

Discrimination is estimated, not binary. One row per (item, misconception):

| column | type | notes |
|---|---|---|
| practice_item_id | text | pk part |
| misconception_id | text | pk part |
| sensitivity_alpha / sensitivity_beta | real | Beta posterior over P(keyed fatal error fires \| learner holds belief) |
| specificity_alpha / specificity_beta | real | Beta posterior over P(no fire \| clean learner) |
| n_planted_trials / n_clean_trials | int | evidence mass behind the estimates |
| source | text | `sim` / `llm_estimate` / `empirical` |
| updated_at | text | |

Seeded by the sim gate (§6) from trial counts (uniform Beta(1,1) prior +
observed fires). Sim estimates are *priors*, not ground truth — an LLM
role-playing the belief likely overestimates real-learner sensitivity — so
rows are updatable from empirical attempts where the misconception was
independently confirmed/refuted (future work, flagged in §9). Consumers use
the posterior (typically the 25th-percentile lower bound), never a bare point
estimate, so 5-trial estimates are automatically treated with caution.
Discrimination power for gating: Youden's J = E[sens] + E[spec] − 1, with a
conservative variant J_lb from the lower bounds.

### 1.4 Hypothesis labels

`misconception:<misconception_id>` replaces `misconception:<error_type>`.
Legacy rows keep rendering; the label parser treats a non-ULID suffix as a
legacy error-type hypothesis (back-compat path in §3).

## 2. Grader / attribution (G1 → C2)

### 2.1 Schema change — `grading.py`

`ErrorAttribution` gains:

- `misconception_statement: str | None` — required when
  `is_misconception=True`; the belief in learner-model terms, not a
  description of the wrong answer.
- `misconception_consistent_answer: str | None` — optional; what a holder of
  the belief would answer on this item. Feeds `signature` and the sim gate.

Grading prompt template updated accordingly (bump prompt version).

### 2.2 Normalization step (new, `services/misconceptions.py`)

After error events persist, for each event with `is_misconception=True`:

1. Fetch `active`/`resolving` registry rows for the LO and its concept
   neighbors.
2. LLM match: "is ⟨statement⟩ the same belief as any of ⟨existing⟩?" →
   `same:<id>` | `new`. (Deterministic fallback when no provider: exact-ish
   text match; never dedupe by error_type.)
3. `same` → append source event, bump severity/updated_at, set status back to
   `active` if it had been `resolving`. `new` → insert row.
4. Write `misconception_id` back onto the error event.

Ordering requirement: this runs before follow-up evaluation (see §4.3).

## 3. Hypothesis set & EIG (C2 + C3)

`build_hypothesis_set` (probes.py:78):

- Iterate registry rows (`active`/`resolving`) for the LO instead of raw error
  events; dedupe by `misconception_id`. Two distinct conceptual slips now
  coexist with separate priors and decay.
- `Hypothesis` gains `misconception_id`; `severity_at_entry`/decay from the
  registry row.

`conditional_distribution` (probes.py:398) and
`facet_conditional_distribution` (probes.py:497):

- The binary `probes_misconception` flag is replaced by the (sens, spec)
  estimates from §1.3. The outcome space already carries an error dimension
  (`(bucket, error_type)`); the conditional now places mass on the
  keyed-fatal-fired outcome as:
  - under `misconception:<id>`: P(fire) = E[sens] (lower-bound variant for
    conservative gating), remaining mass on graded buckets at the unfamiliar
    ability anchor;
  - under `facet_solid` / other hypotheses: P(fire) = 1 − E[spec], remaining
    mass at the mastered anchor.
- An item with no discrimination row for the hypothesis's misconception
  contributes no fire-mass separation (today's behavior for unlinked items) —
  its EIG on that hypothesis comes only from coverage, which is exactly the
  weakness we're correcting for.
- Back-compat: when the hypothesis is legacy (error-type keyed) or the item
  has no misconception links, fall back to the current
  `error_type in fatal_error_ids` test, so existing vaults don't silently
  lose discrimination.

Effect on EIG: P(fatal-error observation | misconception:⟨id⟩) = sens vs
P(· | facet_solid) = 1 − spec is now an honest, *calibrated* per-item
likelihood; ranking prefers genuinely discriminating items over coverage
lookalikes, and prefers a 0.9/0.95 discriminator over a 0.6/0.7 one.

## 4. Follow-up selection & routing (G2)

All in `_choose_intervention_item` / `evaluate_intervention_followup`
(followups.py).

### 4.1 Discrimination requirement

Let `active_mcs` = registry rows with status `active`, severity ≥
`tau_severe_error`, whose `facet_ids` intersect the diagnostic gate facets
(plus any misconception attributed on *this* attempt, regardless of facets).

When `active_mcs` is nonempty:

- A candidate is **diagnostic-eligible** only if its discrimination power
  J_lb (§1.3) against ≥1 of `active_mcs` meets
  `followup.tau_discrimination_power` (default 0.3; existing facet gates
  still apply on top). Above the threshold, J feeds the ranking through the
  EIG conditionals (§3) rather than as a separate bonus.
- If no candidate is diagnostic-eligible → treat as `no_suitable_item` even
  when facet-eligible candidates exist. The facet-eligible best is NOT queued
  as a consolation; a paraphrase costs a learner-minute and produces evidence
  that can't move the misconception posterior.
- The intervention need gains `misconception_ids` + statements in
  `diagnostic_focus` (payload is already JSON; additive).

When `active_mcs` is empty, current behavior is unchanged.

### 4.2 Slate/telemetry

New slate fields per candidate: `discriminates_target_misconception: bool`,
`filtered_reason: "no_misconception_discrimination"`. New decision outcomes:
`created_need_no_discriminator`. Log when the eligible slate has < 2
candidates (the motivating case's pool-of-one also silently zeroed
`predictive_eig` — surface it).

### 4.3 Ordering fix

`evaluate_attempt_intervention_followup` must run after error-event
persistence AND registry normalization (§2.2), so the just-diagnosed
misconception is visible to `active_mcs` and to the hypothesis prior. (In the
motivating case the prior lacked the conceptual_slip hypothesis entirely.)

## 5. Diagnostic generation (G3)

### 5.1 New generation purpose: `diagnostic_authoring`

Driven off pending intervention needs with `misconception_ids`
(`generate_authoring_proposal` grows a sibling entrypoint or a mode flag).
Context builder packages:

- misconception `statement` + `signature`
- the learner's verbatim graded answer and the grader's evidence text
- the source item (prompt, expected answer, `surface_family`, facets)
- LO facets already demonstrated by the learner (so the item can skip them)

### 5.2 Generation constraints (prompt template, versioned)

1. **Forced application to a concrete instance**: the item must require the
   learner to *apply* their model to a specific case and commit to an output
   — not restate or re-derive the rule. The instance type is domain-native:
   compute a value or choose between operators (math), commit to a holding /
   best answer on a novel fact pattern (law), predict a mechanism's behavior
   under a stated change (paper review, e.g. "with the causal mask removed at
   inference, what does token t attend to?").
2. **Documented categorical contrast**: output must include both
   `expected_answer` and `misconception_consistent_answer`, and they must
   differ *categorically* (different value, holding, choice, or predicted
   behavior), not merely in emphasis or completeness — categorical divergence
   is what an LLM grader can attribute unambiguously.
3. **Misconception-keyed fatal error**: ≥1 rubric fatal error with
   `misconception_id` set, describing the signature.
4. **Surface shift**: `surface_family` must differ from the source item's.
5. **Minimal footprint**: `evidence_facets` ⊆ the implicated facets; do not
   re-test criteria the learner already passed.

### 5.3 Review policy additions (`evaluate_review_policy`)

The new checks are relational — "keyed to the *right* misconception,"
"surface differs from *the source item*," "footprint excludes *demonstrated*
facets" — so the current signature (proposal item, vault, source refs) cannot
express them. Add an optional `DiagnosticTarget` review context:

```python
@dataclass(frozen=True)
class DiagnosticTarget:
    need_id: str
    misconception_ids: list[str]
    misconception_statements: dict[str, str]
    source_practice_item_id: str
    source_surface_family: str | None
    demonstrated_facets: list[str]   # snapshot, see below
```

- Resolved from the intervention need at review time; the need→patch linkage
  already exists (`intervention_needs_for_diagnostic_proposal`).
- `demonstrated_facets` (criteria the learner already passed) is **snapshotted
  into the need's `diagnostic_focus` at need-creation time**, not read from
  live learner state at review time — otherwise the same proposal validates
  differently depending on when it is reviewed, which breaks determinism and
  replay.
- `context=None` keeps today's behavior for ordinary authoring proposals. For
  `diagnostic_authoring` batches a missing context is itself a hard error —
  the checks must not silently soften.

Hard validation errors (with context): no fatal error keyed to one of
`misconception_ids`; missing `misconception_consistent_answer`;
`surface_family` equal to `source_surface_family`. Soft warnings: facet
footprint exceeds the implicated set; footprint intersects
`demonstrated_facets`.

## 6. Sim discrimination gate (V1)

Extend planted misconceptions (`sim/profiles.py`) with optional
`misconception_id` / `statement` / `misconception_consistent_answer`. Add an
item-level acceptance check runnable from the review pipeline:

- Simulate the planted student (answers with the misconception-consistent
  answer / LLM-answers under the belief) and a clean student on the proposed
  item, N trials each, through the production grading path.
- The gate's primary output is not pass/fail but the **(sens, spec) Beta
  posteriors** written to `item_misconception_discrimination` (§1.3):
  sensitivity from fire-counts on planted trials, specificity from
  no-fire-counts on clean trials.
- Accept iff the posterior lower bounds clear
  `review.min_sensitivity_lb` / `review.min_specificity_lb` (defaults 0.7 /
  0.8 at the 25th percentile — specificity errs stricter because false fires
  poison the misconception posterior on ordinary practice).
- Rejection reopens the need with the estimates attached, so the next
  generation round sees *why* the previous item failed (e.g. "clean student
  also tripped the fatal error → contrast not categorical enough").
- The motivating paraphrase item fails this gate immediately (sens ≈ 0: the
  planted student answers it correctly) — this is the regression test for the
  whole spec.

Wire as a post-generation, pre-queue step for `diagnostic_authoring`
proposals; failures reopen the need (mechanism exists:
`_reopen_diagnostic_needs_for_rejected_items`).

## 7. Posterior update & resolution (G4)

- Grading evidence records whether each misconception-keyed fatal error fired;
  the observation updates the `misconception:<id>` hypothesis by likelihood
  ratio from §1.3: fired → sens / (1 − spec); discriminating item, not fired
  → (1 − sens) / spec. Items with no discrimination row leave the
  misconception posterior untouched (their evidence flows through the
  ordinary facet channels only), so weak items can't fake resolution and a
  low-spec item can't poison it — the same estimates gate how hard each
  observation moves the belief.
- Auto-resolve is rekeyed to `misconception_id` and re-expressed in evidence
  terms: instead of "n clean attempts", resolve when the posterior
  P(misconception) falls below `tau_misconception_resolved` — n clean
  attempts on a J≈0 paraphrase moves nothing, one clean attempt on a
  0.9/0.95 discriminator moves a lot, which is the correct asymmetry.
  Resolution flips the registry row to `resolved`; a new matching attribution
  reactivates it (§2.2.3).
- `_is_known_gap_state` and the feedback screen read the registry statement
  for display instead of the error-type label.

## 8. Rollout order

1. §1 migrations + G1 grader schema (additive; statement captured even before
   anything consumes it).
2. §2.2 normalization + §3 hypothesis rekeying (back-compat fallbacks on).
3. §4 routing (behind config flag `followup.require_misconception_discrimination`,
   default on for new vaults).
4. §5 generation + §6 sim gate.
5. §7 resolution rekeying.

Replay/back-compat: legacy `misconception:<error_type>` hypotheses and
link-less items keep the current error-type semantics; nothing in existing
fixtures re-derives differently until a new attempt writes a registry row.

## 9. Open questions

- Statement normalization quality: does LLM dedupe over-merge distinct beliefs
  on the same LO? May need a similarity threshold + "when unsure, new row".
- Sim-estimate validity: sensitivity measured against an LLM role-playing the
  belief is likely an upper bound on real-learner sensitivity. §1.3 mitigates
  (source field, lower-bound consumption, empirical updates), but the
  empirical update path — using attempts where the misconception was later
  independently confirmed/refuted as labels — needs its own design pass.
- Per-domain instantiation guidance for constraint §5.2.1 probably belongs in
  vault config (a `diagnostic_instance_styles` hint per vault: fact-pattern /
  prediction / computation) rather than baked into the shared prompt.
- Cross-LO identity: same belief surfacing on a sibling LO — one registry row
  with two LO scopes, or two rows linked by concept? (Current lean: scope to
  LO, propagate via concept neighbors as today.)
- Cost ceiling: normalization adds ≤1 LLM call per misconception-bearing
  attempt; sim gate adds N·2 graded answers per generated item. Both bounded
  by intervention frequency, but worth a per-session budget.
- Does the manual "?"-tutor flow also write attributions that should feed the
  registry? (question_events telemetry suggests yes, later.)
