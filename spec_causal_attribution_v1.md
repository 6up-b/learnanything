# Causal attribution & minimal repair — plan of changes (v3)

**Status:** agreed direction. v3 folds a second (adversarial) review into v2: the
attribution status splits into orthogonal axes, authority becomes three axes with
a producer/confirmer matrix, causal state gets a single-ownership map, P0 splits
into a small write-barrier kernel (P0a) and measurement honesty (P0b), and several
overclaims are corrected (scoped deterministic verification, support scores not
posteriors, softened scheduling gate, observable cost metrics). Filename stays
`spec_causal_attribution_v1.md` deliberately — external references point here; the
heading is the version of record.

Derived from the post-mortem of attempt `01KY64FZE7ZVJ79YJFWAYZH53Q`
(fixtures/linear_algebra). Counterfactual framing from arXiv:2402.01607 (natural
counterfactuals / necessary backtracking) and arXiv:2505.02435 (BRACE): we import
their *objective structure* (target constraint + backtracking distance +
naturalness constraint; observed-space vs latent-space minimality), never their
SCM assumptions or estimators.

**Standing constraints on everything below:**

1. **Bitter-lesson alignment.** The durable investments are data and substrate —
   immutable traces, deterministic verifiers, receipts, and cold-outcome labels
   (`learning_outcome_labels` is the real objective). Hand-engineered taxonomies,
   thresholds, and policies are provisional scaffolding: they must generate clean
   training records so learned components can replace them, and we do not encode
   cleverness where a better model on the same substrate would win. The
   deterministic firewalls are the exception — they are safety invariants and
   survive the handoff.
2. **Schema minimalism, without the lazy-model loophole.** The original disease
   was schema-without-abstention plus authority laundering. Rules: every enum has
   an abstention arm; fields are nullable by default; hypotheses/evidence live in
   JSON until a demonstrated query need promotes them to tables; no structure
   ships unless it changes a decision worth its plumbing cost. BUT abstention
   must be **explicit and reasoned** — a supported attribution or a typed
   abstention with reason; silent omission is invalid, and abstention/missing-
   field rates are tracked per model and prompt version so a model that returns
   almost nothing cannot masquerade as safe.

---

## 0. Motivating failure (the exhibit)

Item: "Find two distinct square roots of 𝑖" (`pi_exercise_01ky5raxvexp8axggqn8e73vkh`,
facets: complex multiplication 0.8 / componentwise addition 0.2). Learner expanded
and formed equations perfectly, dropped the negative branch of `2a²=1`, and wrote
`±√(1/2)+√(1/2)i` with ± scoped over the real part only.

Right: criterion-level grading evidence (correct localization), learner-facing
`feedback_md` (correct minimal repair), the two-event mechanism split. Wrong —
every consumer of structured facet IDs: retry targeted the facet the learner aced;
both facets took recall damage; a durable misconception was minted from one attempt
claiming the learner confuses addition with multiplication; the follow-up gate
scored 0.007 and asked nothing; `unresolved_cause_factors` stayed empty.

**Root-cause chain (all verified in code):**

1. Grading prompt forces facet naming; no "no listed facet applies" outcome
   (`codex/client.py:_grading_prompt`, `services/grading.py` targeting_policy).
2. **Validator auto-expansion:** for every criterion the grader targets, the
   validator appends ALL of that criterion's `criterion_facet_weights` facets to
   `target_evidence_families` (`grading.py:377-380`) — criterion-only localization
   is silently converted into facet attribution.
3. `_event_facet_ids` falls back to the attempt's full `evidence_facets` when the
   grader names none (`misconceptions.py:132`).
4. `attempts.py:~1182` backfills `attribution_json` from the forced picks, making
   `observed_unresolved_failure` (`canonical_projection.py:199`, requires *no*
   attribution) unreachable — the §5.3 safeguard never fires.
5. Positional contrast: `target_facet = facets[0]`, `confused_with_facet =
   facets[1]` (`misconceptions.py:437`) — list ordering presented as diagnosis.
6. `first_error_trace` promotion spends outcome confidence (grader_confidence
   ≥ 0.9) as causal confidence (`misconceptions.py:266`); `target_facet` is always
   non-null, so it fires on essentially every confident misconception flag.
7. **Calibration flattening:** the calibrated response-level
   `expected_true_score_fraction` replaces the raw points fraction *for every
   criterion* (`canonical_projection.py:355, 389-390, 420`) — even per-criterion
   `passed` flags are computed from the flattened value. The criterion vector the
   attribution layer needs is destroyed before it runs.
8. **Authoring forces the smear:** the authoring contract requires
   `criterion_facet_weights` to cover EVERY criterion with a nonempty map
   (`codex/prompts.py:326-328`); the exhibit's `solve_equations: {mult 0.5,
   add 0.5}` is false at mint time because the vocabulary has no facet for branch
   retention and the schema forbids saying so.

## 1. Design principles

1. **Facets are stable, reusable, independently testable knowledge claims.** The
   error space is unbounded; the facet space is small. A facet is never an error
   label. Split a facet only when the distinction changes measurement, prediction,
   or intervention (decision-relative resolution).
2. **Layered error representation:** canonical facet / item-local step / mechanism
   / observed signature / causal hypothesis / repair class — separate fields, never
   collapsed into `target_evidence_families`. Attribution state is factored into
   orthogonal axes (§4.1), never one mixed enum.
3. **Abstention is first-class and explicit.** "No facet confidently identified"
   and "unknown" are valid, preferred outcomes — never coerced to the nearest
   known ID, and never silent (standing constraint 2).
4. **Confidences are plural and labeled.** Outcome, localization, mechanism,
   causal, repair — every raw LLM number is a *model-reported proposal*.
   "Posterior" is reserved for updates whose likelihood channel and calibration
   status are explicit; until then the system speaks in support scores, plausible
   sets, and ordinal rankings.
5. **Passed-facet firewall (deterministic invariant):** if all assessable criteria
   directly measuring facet F passed and no failed assessable criterion directly
   measures F, this attempt may not write negative evidence against F or target F
   for repair. Overridable only by a valid discriminating observation.
6. **Promotion discipline is real:** one well-explained answer can justify a local
   hypothesis, a targeted repair, a candidate, a high-priority follow-up — not a
   durable learner-wide belief.
7. **Minimal repair = least-backtracking feasible intervention**, in two spaces:
   minimal change to the learner's displayed reasoning AND minimal change to the
   hypothesized learner state, plus instructional burden. Keep three distinct
   anchors: first observable divergence, earliest supported faulty commitment,
   repair insertion point. They often coincide; they are not definitional
   synonyms.
8. **Probe only when it changes the action** — and prefer no probe when a
   low-cost repair covers the plausible cause set. Machine-side uncertainty
   (grader, item contract, symbolic correctness) is resolved with machine effort,
   never learner effort.
9. **Historical evidence is immutable.** Contracts version append-only; demotion
   and correction never delete audit history; replay reproduces state.

## 2. Authority model

Authority is three separate axes, not one ladder:

- **Provenance/mutability** — is this an immutable record of what happened?
  Raw grader output is immutable evidence *that the grader said X* — not evidence
  that X is true.
- **Epistemic authority** — how much should this claim move belief? Determined by
  the channel's calibration status and the claim's validation history.
- **Permitted use** — which state writes may this artifact drive (§6.2)?

For conflicts about the *same claim*, arbitration precedence runs:

1. **Immutable observations** — learner answer, timestamps, hints, exposure, raw
   provider outputs (as records of occurrence).
2. **Deterministic verification, within its verified parse and contract.** CAS
   checks, test execution, span/offset matches, pre-registered signature matches.
   Outcomes are typed: `verified | contradicted | unsupported | parse_failed |
   assumption_missing`. A CAS proof that a parsed expression squares to −i is
   maximal authority *for that parsed expression*; the LLM step that parsed
   ambiguous prose into it is not, and `parse_failed`/`unsupported` confer
   nothing. Passing tests proves conformance to those tests, not correctness.
3. **Measurement interpretation** — criterion outcomes, calibrated grade
   channels, assessability/localization.
4. **Derived causal hypotheses** — NL statements, mechanism proposals,
   postdictive claims, blind prediction bundles, simulation artifacts. Preserved
   verbatim; typed as proposals.
5. **Validated causal record** — receipts: support scores, contradictions, repair
   classes, permitted uses.
6. **Learner-state and policy projections.**

**Producer-authority matrix** — no component may confirm its own claim:

| Claim | May propose | May confirm |
|---|---|---|
| Learner-state cause | Grader/diagnostician | Probe reproduction, fingerprint-distinct recurrence, learner confirmation, adjudication |
| Item-contract fault | Grader (flag only) | Contract validator / human review |
| Grader fault | Validator (suspect) | Regrade disagreement / adjudication |
| Deterministic contradiction | Formal verifier | The verification contract itself |
| Durable misconception | Nobody directly | Promotion projection only |

This closes the self-serving-abstention loophole: a grader cannot escape a
trace contradiction by declaring the item faulty — it can only *flag*, and the
flag routes to machine-side review, not to learner-state writes.

The NL layer is the *semantic hypothesis generator, simulator, and repair
proposer* — NL-preserving, structure-late, validator-centered, outcome-calibrated.
Its artifacts were the only layer that was right in the exhibit; they earn
epistemic authority through validation, not by being prose.

## 3. Causal state ownership

One role per store; every cross-reference carries IDs and versions, never copied
mutable statements. This is the guard against the v2 residual risk: overlapping
attribution representations with unclear lifecycle.

| Store | Role |
|---|---|
| `error_events` | Immutable observed occurrence (what happened on this attempt) |
| `causal_hypotheses` (P1) | Versioned hypothesis definition/episode occurrence — the single home of hypothesis statements, scopes, predictions refs, status |
| `unresolved_cause_factors` | Active uncertainty: a set of hypothesis IDs, open/retired — no duplicated statements |
| `diagnosis_receipts` (P1) | Immutable decision snapshot: IDs + versions + scores + permitted uses at decision time |
| `hypothesis_sets` | Locked experimental set for a probe episode (existing machinery, incl. `H_OTHER`) — reused, not duplicated |
| `misconceptions` | Durable learner-state projection; written by the promotion projection only |
| `misconception_candidates` | **Retired at P1** — becomes a projection over `causal_hypotheses` (status = candidate); P0 keeps it running unchanged |

## 4. P0a — stop the bad writes (ship first, smallest possible kernel)

Deletions and write barriers only — no new schema, no prompt changes, no
calibration changes. Each lands with the regression fixture.

1. Delete the validator's criterion→facet auto-expansion (`grading.py:377-380`).
2. Delete `_event_facet_ids`' fallback to attempt `evidence_facets`
   (`misconceptions.py:132`).
3. Delete positional contrast assignment (`facets[0]/facets[1]`,
   `misconceptions.py:437`); `_authored_correction` composes distinctions only
   for explicitly asserted contrasts (none exist yet — so none composed).
4. Disable `first_error_trace` durable promotion.
5. **Passed-facet write barrier** (principle 5) and **repair-target write
   barrier** (a repair suggestion may not target a facet/criterion whose direct
   criteria all passed), enforced at write time with a logged trigger.
6. Exhibit regression fixture asserting: no facet targets on the notation error
   event; no durable misconception; retry not targeting the multiplication
   facet; firewall log entries present.

## 5. P0b — measurement honesty

### 5.1 Grading schema (`codex/schemas.py`)

Extend `ErrorAttribution` with orthogonal axes (not one mixed enum):

- `resolution_status`: `resolved | unresolved | abstained` (+ required
  `abstention_reason` when abstained).
- `cause_scope`: `learner_state | transient_execution | interaction_context |
  item_contract | grader_interpretation | unknown`. Per the §2 matrix,
  `item_contract`/`grader_interpretation` are *flags* routing to machine-side
  review — never direct learner-state writes.
- Typed `target_ref` (union: facet-capability | criterion | item-step |
  answer-span | none) — the ref's kind IS the target scope; `missing_vocabulary`
  is a property of a proposed-curriculum note, not a cause. Permitted actions
  derive from the (resolution, scope, target-kind) tuple.
- `mechanism`, `operation` (canonical taxonomy id + free snake_case).
- `first_divergence`: `{anchor_kind: span | between_spans |
  missing_required_step | whole_answer, criterion_id, quote?, quote_hash?,
  char_start?, char_end?, normalized_quote?}` — span anchors validated by
  string/offset match with normalized fallback (reanchor pattern); omissions
  anchor to `missing_required_step` + checkpoint id, which have no quote.
- `localization_confidence`, `causal_confidence` — stored as
  `model_reported_*`; never consumed as posteriors.
- `facet_contrast: {target_facet, confused_with_facet, justification} | null` —
  the ONLY source of a confused-with pair; justification must cite the trace.
- `candidate_causes`: list of `{cause_scope, mechanism, operation, target_ref,
  statement, model_reported_confidence, postdictive_claims}` — always including
  the open-set arm (reuse `H_OTHER` semantics; never a closed set).
- `postdictive_claims` (renamed from v2's inline predictions): per criterion, a
  distribution over `{pass, partial, fail, unassessable}`. Produced after the
  model saw the trace, so they are explanatory claims usable for deterministic
  consistency checks (a contradiction is a contradiction whenever predicted) —
  they NEVER feed synthetic likelihood or probe discrimination. Blind prediction
  bundles are a separate P2 artifact (§8).

`RepairSuggestion`: add `target_criterion_ids`; allow empty
`target_evidence_families`. Bump `GRADING_PROMPT_VERSION`.

### 5.2 Prompt & targeting policy rewrite

Name a facet only when the failed step exercises that facet's *claim*; prefer an
item-step/criterion target or a reasoned abstention over stretching to the
nearest listed facet. Passing a criterion that exercises a facet is positive
evidence FOR it. `facet_contrast` only for demonstrated contract-swaps. Spell
out confidence semantics (causal ≠ outcome).

### 5.3 Unresolved-cause routing

Stop backfilling `attribution_json` for attributions that are not `resolved`
(`attempts.py:~1182`), so failed multi-target criteria reach
`observed_unresolved_failure` and open an unresolved-cause factor referencing
the candidate hypothesis set.

### 5.4 Criterion-level calibration fix

Never replace the criterion vector with a response-wide score. Until
criterion-level calibrated interpretations exist: the **raw criterion fraction is
the directional outcome** (pass/fail, localization, attribution); response-level
calibration (`expected_true_score_fraction`, certainty LCB) scales **evidence
mass/authority only**. Touchpoint: `canonical_projection.py:355-420`.

### 5.5 Criterion-scoped facet evidence

Facet evidence derives from the criteria that genuinely measure the facet
(per-criterion fraction × criterion-facet link), not the attempt scalar — behind
the P0a firewalls. On the exhibit: multiplication receives
`expand_square`-weighted positive evidence; the branch/scope failure writes no
facet damage.

### 5.6 Promotion lifecycle (`services/misconceptions.py`)

Authority lifecycle: `ephemeral cause → candidate hypothesis → provisional belief
→ reproduced durable misconception → resolving | resolved_learned |
contradicted_by_trace | retired_misdiagnosed | merged | superseded`.

- A single attempt yields at most a *provisional belief* with high diagnostic
  priority — usable for learner feedback, routing, probe selection; barred from
  reducing canonical facet state, permanent corrections, long-term scheduling.
- Durable promotion (projection-only, per §2 matrix) requires one of: (a) a
  valid probe reproduces the blind pre-registered signature; (b) recurrence on a
  fingerprint-distinct independent evidence group (near-clones do not count);
  (c) deterministic proof the response necessarily instantiates the rule +
  learner confirmation; (d) human adjudication.
- **Trace-consistency check:** hard veto only when a *deterministic* postdictive
  claim ("if H, criterion C must fail") is contradicted by a full-credit
  criterion that actually elicited the rule; probabilistic claims contribute
  strong negative support instead. Hypotheses carry `applies_when` /
  `does_not_apply_when` so non-elicitation isn't contradiction.
- `doesnt_fit` learner feedback is bounded negative evidence with typed reasons
  (slipped / notation confused me / item ambiguous / other valid approach /
  diagnosis wrong) — an evidence channel, not an override.

### 5.7 Authoring honesty & contract versioning

- Rubric criteria gain `measurement_status`: `direct | supporting | composite |
  item_local | no_canonical_facet`. Empty facet targets are VALID with a declared
  status. The authoring prompt's "cover every criterion" requirement is replaced
  with "link only what the criterion genuinely measures." Validator flags
  uniform smears for re-audit.
- **Embedded trace contract** (minimal, versioned, inside the assessment
  contract — no separate storage):

  ```yaml
  trace_contract:
    recipes:
      - id: cartesian_solution
        checkpoints: [expand_square, equate_components,
                      select_sign_relation, enumerate_roots, state_roots]
        dependencies:
          enumerate_roots: [select_sign_relation]
  ```

  Compiled from `expected_answer` at authoring time; alternate valid recipes get
  their own checkpoint chains. This is what makes "step", "backtracking depth",
  and "earliest commitment" computable rather than LLM prose, and gives
  `missing_required_step` anchors their referents.
- **Attempted items are never rewritten in place.** Original contract versions
  preserved; corrections create new versions plus append-only measurement
  corrections tagged with the consuming projection version. Unattempted items
  may be re-audited directly.
- Misconception cleanup: existing `first_error_trace` rows (including
  `01KY64GVAMY6MWXKXHK4DKW7B7`) marked `demoted`/superseded, history intact.

**P0 acceptance (a+b):** replaying the exhibit yields — no facet targets on the
notation error event; an open unresolved-cause factor referencing ≥2 candidate
hypotheses plus the open-set arm; retry targeting `solve_equations`;
multiplication facet recall unpenalized (firewall log); no durable misconception;
a provisional belief with high follow-up priority; per-criterion outcomes
preserved under the calibrated channel. A synthetic attempt with asserted,
trace-consistent contrast still yields a provisional belief immediately.

## 6. P1 — causal records & structural minimal repair

### 6.1 `causal_hypotheses` (one table; ownership per §3)

(id, attempt_id, learning_object_id, cause_scope, statement, mechanism,
operation, target_ref_json, applicability_json, postdictive_claims_json,
evidence_json, repair_class_id, status, generation_agent_run_id, model,
created_at). Blind prediction bundles and simulation evidence attach by ID as
they arrive (P2/P3). `misconception_candidates` becomes a projection over this
table. Append-only episode record, not a second concept graph.

### 6.2 Diagnosis receipts with permitted uses

Immutable decision snapshot (persisted like `attempt_debug_payloads`; table only
on demonstrated cross-attempt query need): criterion outcomes + assessability,
divergence anchors (all three notions), resolution/scope axes, valid targets,
hypothesis IDs + versions, `support_scores` / `plausible_set` / ordinal ranking
(NOT "posterior" until a calibrated likelihood channel exists), repair-class
ranking, probe decision + reason, and `permitted_uses ⊆ {learner_feedback,
routing, probe_selection, durable_belief, facet_negative_evidence}`. A
single-attempt candidate permits the first three only. Receipts double as the
training records for the P4 learned policy.

### 6.3 Repair classes (episode-scoped) and typed repair targets

`RepairClass {id, operator, target_refs, preserve_refs, expected_minutes,
answer_reveal_budget}`. Equivalence is **episode_repair_equivalence** — scoped to
the current decision horizon and versioned by repair policy: two causes sharing
an immediate repair may still differ in delayed verification, transfer testing,
and recurrence interpretation, so equivalence collapses the *probe decision*,
never the hypothesis records.

### 6.4 Minimal repair, structurally

- The grader emits a **repaired trace**: learner's work verbatim to the repair
  insertion point, minimal edit, downstream regenerated in the learner's own
  notation.
- **Minimality receipt:** preserved spans/criteria, all three divergence anchors,
  changed latent claims, changed trace steps (against the trace contract's
  checkpoints), trace edit cost, latent change cost, backtracking depth,
  estimated minutes. The text diff is the audit artifact and the observed-space
  term — NOT the whole objective (BRACE's d_X vs d_U).
- **Lexicographic selection** (no λ before outcome data): 1 reject evidence
  contradictions; 2 reject invalid rules; 3 preserve demonstrated capabilities
  (deterministic firewall tiers); then 4 fewest latent claims changed; 5 fewest
  checkpoints changed; 6 lowest-burden sufficient repair (LLM-judged tiers break
  ties among already-safe candidates only).
- **Common-repair cover:** before any probe, generate the minimal repair per
  plausible hypothesis, group by episode repair class, and check whether one
  low-cost repair covers the plausible set. If yes — serve it; skip diagnosis.

### 6.5 Deterministic verifier adapter

Adapter contract with typed outcomes (§2): `verified | contradicted |
unsupported | parse_failed | assumption_missing`, plus the parsed form and
assumptions used. Math: CAS (sympy) verification of final answers and
pre-registered signatures. Code: test execution (proves conformance to the
tests). Adapters may also emit **discrimination features** — open-keyed
observation facts (`listed_root_count: 2`, `sign_scope: real_only`,
`verified_each_root: false`) with a mandatory `unparsed` fallback — populated
deterministically where the domain permits, by a frozen blinded extractor
otherwise. These are adapter *outputs*, not required core schema: criterion
outcomes alone under-discriminate (both exhibit hypotheses predict
`solve=partial, state=partial`), and features close that gap without freezing a
per-domain IR into contracts.

### 6.6 Feedback: receipt-checked, typed display

Generation path unchanged through P0 (it was the layer that worked). At P1, a
**claim-check overlay**: rendered feedback is validated against the receipt's
`permitted_uses` before display, and the learner surface types its sections —
verified correction (deterministic-backed) / causal hypothesis (labeled
uncertain) / what remains unverified / proposed next action — plus what-you-
already-demonstrated (✓ per criterion), first divergence (the learner's own
line), why we are NOT reviewing X (firewall rationale), and the contest action
with typed reasons (5.6). Different claim types get different wording and
display policies; an answer-revealing repaired trace is display-gated by
contamination status (§8).

### 6.7 Causal-episode inspector

A debug surface (CLI first: `learnloop show <attempt> --causal`) rendering the
receipt: evidence, candidate causes with support, permitted uses, repair choice,
and why alternatives were rejected. Diagnosis must be auditable by a human
without reading JSON.

## 7. P2 — probe coherence

- **Gate integration (softened):** an open unresolved-cause factor whose top
  hypotheses fall in *different episode repair classes* creates a high-priority
  diagnostic need and **blocks serving unrelated remediation for that cause** —
  it does not unconditionally mandate an immediate probe. Session budget,
  learner preference, recent diagnostic burden, and pending machine-side checks
  (which run first, principle 8) still schedule it. Cause-set targeting moves
  from facet-divergence to repair-class-divergence.
- **Decision rule (EVSI-flavored):** probe only when no low-cost repair covers
  the plausible cause set AND the probe's expected information would change the
  selected repair; compare probe burden against expected avoided over-teaching.
- **Manipulation contracts** replace "vary exactly one factor":
  `intended_manipulations` (minimized), `incidental_changes` (declared),
  `held_constant`; the diff audit — deterministic/structural where the trace
  contract permits, adversarial LLM otherwise — rejects undeclared differences.
- **No inheritance of parent facet weights** — that map is the defect under
  investigation. A probe inherits lineage (source family, parent item, surface
  style, difficulty *as a prior*) and independently recompiles measurement
  targets, criterion links, assessability.
- **Blind prediction bundles:** generated by a stage that receives hypothesis +
  item + rubric + trace contract — never the learner answer, awarded scores, or
  observed divergence — and stamped `{generated_without_observation: true,
  model_revision, outcome_schema_version}`. Only blind bundles feed probe
  discrimination and synthetic likelihood; grading the administered probe is
  classification against them (deterministic match where possible). Probe
  hypothesis sets lock via existing `hypothesis_sets` machinery including
  `H_OTHER`.
- **Contamination classes:** `pure_diagnostic | instructional_diagnostic |
  repair_activity | verification`. An instructional diagnostic closes the
  pre-intervention causal segment and cannot feed certification or FSRS
  retention; near-clone probes never certify.
- **Delayed cold verification:** after a local repair, one fresh task on a
  different surface family avoiding the same notation affordance, updating
  learner capability, diagnosis support, and repair-effect support separately —
  a successful repair does not retroactively prove the diagnosis (hard
  invariant).

## 8. P3 — simulations (shadow with routing authority)

Model tiering: **cheap model for persona simulation** (high volume, k samples,
role-play fidelity over depth); **strong model for hypothesis enumeration and
contrast assertion** (low volume, quality determines everything downstream).
Routing is per-purpose config keyed by `agent_runs.purpose`.

From day one (reversible, ordinal uses only): `synthetic_support_score` for
ranking which hypothesis to probe first; probe discrimination gating (do
personas produce distinguishable answers against the blind bundles?);
cycle-consistency (simulated traces → blinded matcher → recovers the
hypothesis?); non-applicable controls (a simulator reproducing the error outside
`applies_when` is modeling incompetence, not a bounded misconception);
**role-adherence checks** before samples count (the persona must not copy the
misconception statement into its answer or exceed the specified epistemic
state).

Not until calibrated: real-learner likelihoods, posterior authority, durable-
belief influence. Ladder: synthetic plausible → simulator-validated → shadow
likelihood → calibrated → live authority. **Calibration channels:** (a)
**planted misconceptions** — synthetic learners with known implanted causes,
scoring whether simulation + matching recovers them (available immediately, no
real-learner data needed); (b) prospective comparison against real probe
outcomes as they accumulate. (a) unblocks the ladder in a single-learner vault
where (b) accrues slowly.

**Three noise channels stay distinct** — P(real response | learner hypothesis),
P(simulated response | prompted hypothesis, simulator), P(grader output | true
response) — separate identities, parameters, evidence streams.

**Token accounting & cache:** every agent run logs actual input, cached input,
output, and reasoning tokens (new nullable `agent_runs` columns), plus latency,
retries, cache hit, validator outcome. Simulation cache key: hypothesis
id+version+statement hash, item content hash, assessment-contract version,
simulator provider/model/revision, prompt version, outcome schema version,
decoding params. Accepted position: the spend is worth it; the audit trail
verifies that per purpose, it does not pre-emptively minimize.

## 9. P4 — learned repair policy (deferred until cold outcomes exist)

Estimate repair effectiveness from receipts + cold verification; fit burden
trade-offs; bounded randomization among safe near-equivalent repairs — which is
also what makes "avoided problem" claims estimable (§12). Longer term: learn the
discrimination-feature extractor and repair policy from receipts, retaining the
deterministic firewalls as safety invariants; cluster recurring
missing-vocabulary notes and propose microfacets only when a cluster predicts a
distinct repair or measurement need. This is the bitter-lesson handoff: P0–P2
structural rules exist to generate uncorrupted training data for their own
replacement. The structural minimal-repair selector (6.4) does NOT wait.

## 10. Golden path integration

The golden path run (documentation §17) already practices this spec's epistemics
at run scale: tier-one triage routes deterministically only on decisive evidence,
ambiguity becomes a learner-confirmed decision aid, overrides log as adjudication
anchors, routes snapshot before tutor prose, fault/ambiguous reasons open no
ladder rung, and nothing certifies except the reserved cold surface. This spec
repairs the attempt-level substrate those mechanisms consume; the run's cold
assessment supplies the outcome labels P4 needs. Explicit deliverables:

- **Triage input rekeying (P2, depends on P0b fields).** The tier-one
  high-confidence signature route (`failure_triage.py`) currently keys on the
  grader-confidence bucket — outcome confidence spent as causal confidence, the
  exhibit bug at run scale. Rekey on causal support: a trace-consistent
  hypothesis with concentrated support stays tier-one; low support or competing
  candidate causes downgrades to the tier-two decision aid, which renders the
  hypothesis set as its content and prior ordering. System hypotheses NEVER
  silently overrule the learner's own report.
- **Rung-divergence probe gate (P2).** The pattern ladder's rungs are a shipped
  closed repair-class vocabulary; the triage-reason → entry-rung map is cause →
  repair-class routing. Probe only when plausible causes map to *different entry
  rungs* (exhibit: transient slip → `independent_repair` vs structured-negation
  belief → `explanation` — divergent, probe-worthy); same rung → common-repair
  cover, route without diagnosing. The passed-facet firewall is what makes
  "nearest useful rung, not always the bottom" trustworthy.
- **Make the no-rung routes reachable (P0a effect).** The journey already has
  slots for item-fault / grader-fault / unresolved ("opens no ladder rung") —
  near-dead paths today because upstream manufactures certainty. The P0a
  deletions let them fire. Before "three failures on distinct surfaces" flags a
  run for review, run machine-side resolution (regrade, verifier — 6.5) to test
  whether the *surfaces* were bad.
- **Probe review ladder (P2).** Generated edit-script probes respect "never
  invent a diagnostic instrument on the hot path": minted as candidates with
  blind prediction bundles, pass the diff audit and discrimination test, then
  register → review → activate — becoming the pre-authored reviewed cards
  baseline/triage may administer.
- **Receipt chain to cold outcomes (P4 feed).** Diagnosis receipt → repair class
  → rung outcomes → burned cold-assessment result is a complete training record;
  the golden path is the only flow disciplined enough to produce it
  uncontaminated. `permitted_uses` matches the run's contract: provisional
  beliefs may route but never certify.
- **Scope boundary.** Ladder rung outcomes stay lightweight self-reports;
  rich attribution applies where grading evidence exists (baseline,
  practice-pool attempts, cold assessment). Do not grow rung logging into a
  candidate-cause questionnaire.

## 11. Migrations & cleanup

- P0a: none (deletions + barriers + fixture).
- P0b: attribution axes + divergence anchors + candidate causes on grading
  storage; `measurement_status` + embedded `trace_contract` on assessment
  contracts (append-only versioning for attempted items); misconception
  lifecycle statuses; demote-don't-delete.
- P1: `causal_hypotheses` table; receipt payloads (existing storage);
  `misconception_candidates` → projection.
- P3: `agent_runs` token/latency/cache columns; simulation cache.
- **Thresholds follow the parameter-registry lifecycle** (heuristic default →
  simulator-validated → pooled-calibrated → locally fitted). P0 leans on
  structural rules needing no threshold: no auto-expansion, no fallback, no
  positional contrast, no single-attempt durability, no negative evidence
  without an assessable failed target, no probe when one repair covers.

## 12. Validation

- **Regression matrix, not only the exhibit** (the exhibit alone would overfit
  the architecture to one failure shape). Fixtures: the exhibit; genuine
  multiplication failure; genuine addition-vs-multiplication confusion; pure
  final-line notation typo over valid reasoning; missing step with no quotable
  divergence (`missing_required_step` anchor); alternate correct solution path
  (recipe 2); ambiguous/defective item (`item_contract` flag routing); grader
  mistake contradicted by verifier (`grader_interpretation` + regrade); composite
  criterion with one passed supporting facet (firewall edge); correct final
  answer from invalid reasoning; unparseable notation (`parse_failed` — verifier
  confers nothing). Exhibit case extended through triage (P2): must downgrade to
  a tier-two decision aid and gate its probe on rung divergence.
- **Replay harness:** re-normalize existing vault attempts; report blocked
  promotions, firewall triggers, facet-outcome deltas, abstention rates by
  model/prompt version.
- **Metrics** (primary first): problems-to-cold-success; wrong-facet damage rate
  (should → ~0); unnecessary-problem rate; probe action-change rate; common-
  repair skip savings; repair preservation rate; first-divergence accuracy vs
  adjudication; abstention precision; item-contract fault rate; diagnosis
  contest rate; misdiagnosis retirement rate; simulation calibration (P3+,
  planted-misconception recovery rate); **tokens per resolved diagnostic
  episode, per action-changing probe, and per eventual cold success** ("avoided
  problem" claims are reserved for P4's randomized comparisons — they are not
  observable from deterministic logs).
- **Promotion precision counts only adjudicated contradiction/misdiagnosis** —
  `resolved_learned` is the system working, not a false promotion.

## 13. Non-goals

- No on-the-fly minting of canonical facets (provisional hypotheses stay
  item-local; missing-vocabulary notes accumulate for clustered review — P4).
- No SCM estimation machinery (flows, Lagrangians, noise-space optimization);
  LLM judgment + support scores + deterministic verifiers estimate what the
  counterfactual framing says to compute.
- No separate solution-graph storage — the embedded, versioned, recipe-aware
  `trace_contract` inside assessment contracts (5.7).
- No learned utility function before cold-outcome data (lexicographic policy
  until then).
- No changes to the learner-facing feedback *generation* path through P0; at P1
  it becomes receipt-checked with typed display (6.6) — checked, not
  regenerated.
- No schema growth beyond demonstrated decision value (standing constraint 2):
  when in doubt, keep it NL + JSON and let validators, not fields, carry rigor —
  with abstention explicit and its rates watched.
