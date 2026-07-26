# Causal attribution & minimal repair — plan of changes (v5)

**Status:** agreed direction. v4 retains v3's adversarial-review corrections
(orthogonal attribution axes, three-axis authority, single ownership, P0a/P0b,
scoped verification, support scores rather than posteriors) and adds a bounded
Learning Pattern Discovery track: interpretable residual slices first, latent
profile discovery second, temporal retirement third. v5 relieves the schema
pressure P0b would otherwise reintroduce (prose-first grading output, judgment
fields nullable unless deterministically validatable, thinned candidate causes,
postdictive claims as deterministic implications, mechanism taxonomy EARNED by
clustering at P1 rather than authored at P0b), repairs two phase-ordering
defects (criterion-outcome honesty becomes a P0a precondition of the firewall;
remediation episodes rewire to provisional beliefs so the repair lane survives
the promotion freeze), adds learner self-report disambiguation on unresolved
failures, and adds a variant-authoring honesty track (§5.8: direction-symmetric
deterministic audits for harder/easier siblings, early manipulation contracts,
`rung_shift` typing, no mandated facet inheritance) motivated by a second
exhibit. Predictive patterns remain
derived, corrigible artifacts; they may earn bounded prediction/routing authority
through prospective validation, but never become causal states, mastery evidence,
or learner types. Filename stays `spec_causal_attribution_v1.md` deliberately —
external references point here; the heading is the version of record.

**Successor documents.** `spec_diagnostic_augmentation_v1.md` supersedes the
forward sequencing of §8/§8.5/§9 and owns diagnostic-quality measurement.
`spec_measurement_efficiency_v1.md` owns the instruments this document's
diagnostician reads, the inference that makes measurement unnecessary, and the
certification decision rule. Two clauses here are amended by it and nothing else
is: principle 8 below (machine-resident vs learner-resident uncertainty, its
§3.A8) and the authored fatal-error→misconception link
(`RubricFatalError.misconception_id`), which its A5 extends into a full per-item
discrimination profile feeding §5.1's candidate causes. Every firewall in this
document survives both successors unchanged.

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
   almost nothing cannot masquerade as safe. Fill rates are tracked with the
   same suspicion: a judgment field populated on ~100% of attributions is as
   anomalous as one never populated — real diagnostic signal has variance (the
   exhibit's defect would have surfaced as `target_evidence_families` filled on
   every single error attribution).

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
   orthogonal axes (§5.1), never one mixed enum.
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
   low-cost repair covers the plausible cause set. **Machine-resident**
   uncertainty (grader flakiness, a missing item contract, symbolic correctness
   the CAS could settle, an unmapped repair class) is resolved with machine
   effort, never learner effort: the machine holds everything needed, and buying
   it with learner effort is a tax on the learner for the system's own debt.
   **Learner-resident** uncertainty is a different thing and is not covered by
   that prohibition — what the learner meant by an ambiguous notation, whether a
   skipped step was fluency or a gap, which of two methods they believed they
   were using. That information exists only in the learner's head; no machine
   effort recovers it, and the alternatives are to guess (a harmful write) or to
   discard the measurement (a wasted attempt). One bounded question is strictly
   better than both, and making abstention repairable this way is what removes
   the standing pressure to over-fill that §0 diagnoses. Bounded below: at most
   one question, only against a criterion the grader has flagged hedged or
   abstained-with-reason, never against a confident grade. See
   `spec_measurement_efficiency_v1.md` §3.A8. A clarification rate above a small
   fraction of attempts is evidence of machine-resident uncertainty
   misclassified as learner-resident, and must be fixed machine-side under the
   first half of this principle.
9. **Historical evidence is immutable.** Contracts version append-only; demotion
   and correction never delete audit history; replay reproduces state.
10. **A recurring predictive pattern is not a causal state.** Residual slices and
    clusters identify coherent contexts where the current predictor is wrong.
    Their semantic descriptions are hypotheses; their causal explanations require
    new blind predictions, discriminating observations, or interventions. A
    learner-facing pattern is facet/capability/episode scoped and temporary; a
    system-quality pattern is instrument/family/version scoped. Neither is a
    permanent learner type or a "learning style."

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
| Recurring predictive pattern | Slice/profile discoverer | Chronologically later recurrence against the frozen baseline |
| Pattern's causal explanation | LLM/diagnostician | Discriminating probe, pre-registered contrastive intervention, learner confirmation, adjudication |
| Differential intervention response | Policy learner | Randomized or defensibly adjusted cold outcomes |
| Durable misconception | Nobody directly | Promotion projection only |

This closes the self-serving-abstention loophole: a grader cannot escape a
trace contradiction by declaring the item faulty — it can only *flag*, and the
flag routes to machine-side review, not to learner-state writes.

The NL layer is the *semantic hypothesis generator, simulator, and repair
proposer* — NL-preserving, structure-late, validator-centered, outcome-calibrated.
Its artifacts were the only layer that was right in the exhibit; they earn
epistemic authority through validation, not by being prose.

Chronological recurrence confirms only that a predictive pattern recurs. It does
not confirm the LLM's name for it, its educational mechanism, or why a particular
intervention would work.

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

Learning-pattern artifacts (§8.5) live outside this causal-state map. They are
rebuildable derived views over frozen predictions and later outcomes; a pattern
may reference causal hypothesis IDs, but never owns or duplicates their
statements.

## 4. P0a — stop the bad writes (ship first, smallest possible kernel)

Deletions, write barriers, and one honesty precondition — no new schema, no
prompt changes. Each lands with its regression fixture.

1. Delete the validator's criterion→facet auto-expansion (`grading.py:377-380`).
2. Delete `_event_facet_ids`' fallback to attempt `evidence_facets`
   (`misconceptions.py:132`).
3. Delete positional contrast assignment (`facets[0]/facets[1]`,
   `misconceptions.py:437`); `_authored_correction` composes distinctions only
   for explicitly asserted contrasts (none exist yet — so none composed).
4. Disable `first_error_trace` durable promotion. Named consequence: repair
   episodes today open only from an ACTIVE DURABLE misconception
   (`services/remediation.py:26-28`), so this silences the remediation lane
   (primed item, cold retry, re-probe) for every first-occurrence error until
   §5.6 rewires episodes to provisional beliefs — that rewiring ships in the
   same release train, not "later". Tighten `probe_reproduction` in the same
   commit: `_promotion_reason` currently fires on
   `attempt_type == diagnostic_probe` alone (`misconceptions.py:263-265`),
   looser than §5.6(a)'s signature-reproduction requirement.
5. **Criterion-outcome honesty (directional half of §5.4, pulled forward).**
   Per-criterion `passed` flags and first-error localization read the RAW
   criterion fraction, never the response-level calibrated
   `expected_true_score_fraction` (`canonical_projection.py:389-396` flattens
   them today; the unresolved gate at `:435-437` already reads raw — extend
   that pattern). This is a precondition, not a refinement: the firewall below
   consumes per-criterion outcomes, and under flattening every criterion in an
   attempt shares one pass/fail state — the firewall would protect everything
   or nothing. Evidence-mass/authority scaling stays calibrated (§5.4 keeps
   the rest).
6. **Passed-facet write barrier** (principle 5) and **repair-target write
   barrier** (a repair suggestion may not target a facet/criterion whose direct
   criteria all passed), enforced at write time with a logged trigger, keyed on
   the raw per-criterion outcomes of item 5.
7. Regression fixtures: the exhibit (no facet targets on the notation error
   event; no durable misconception; retry not targeting the multiplication
   facet; firewall log entries present) PLUS a positive control — a genuine
   multiplication failure whose grader-asserted facet attribution must survive
   untouched. Over-suppression is a deletions-only phase's own failure mode;
   the exhibit fixture alone cannot detect it.
8. Firewall triggers and attribution fill/abstention counters log from day one
   and are CLI-visible, so the P0a→P0b interregnum is observed, not inferred.

## 5. P0b — measurement honesty

### 5.1 Grading schema (`codex/schemas.py`)

**Prose first, structure after.** The schema opens with a free `diagnosis_md`
field generated BEFORE any structured field — field order is causal under
autoregressive decoding — so the grader diagnoses under zero schema pressure
(the layer that was right in the exhibit) and then structures its own words.
Structured fields may only encode what the diagnosis establishes; anchored
fields are checked against it mechanically (a `first_divergence` quote must
appear in the answer text; a named facet must appear in the diagnosis). Held in
reserve if fill-rate telemetry still shows fabrication: two-pass extraction — a
separate, cheaper extractor call structures the prose with explicit permission
to return null. An extractor cannot invent what the prose never said, and
extraction fidelity is auditable prose-vs-structure.

**Required-field rule:** a field may be required only when a validator can
check it against an artifact (quotes, offsets, criterion ids). Pure-judgment
fields (taxonomy picks, confidences, contrasts) are nullable and never
validator-completed.

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
- `operation`: free snake_case only. NO new canonical mechanism taxonomy at
  P0b — that would land a second forced vocabulary in the very release curing
  the first (the grading prompt already forces `error_type` from
  `canonical_error_types`; that channel gets the same fill-rate watch).
  `mechanism` stays derived from the existing `error_type` mapping
  (`map_legacy_error_type`); the canonical mechanism taxonomy is EARNED at P1
  by clustering accumulated free-text operations and cause statements (§6.1) —
  taxonomy from data, per standing constraint 1.
- `first_divergence`: `{anchor_kind: span | between_spans |
  missing_required_step | whole_answer, criterion_id, quote?, quote_hash?,
  char_start?, char_end?, normalized_quote?}` — span anchors validated by
  string/offset match with normalized fallback (reanchor pattern); omissions
  anchor to `missing_required_step` + checkpoint id, which have no quote.
- `localization_confidence`, `causal_confidence` — stored as
  `model_reported_*`; never consumed as posteriors.
- `facet_contrast: {target_facet, confused_with_facet, justification} | null` —
  the ONLY source of a confused-with pair; justification must cite the trace.
- `candidate_causes`: list of `{statement, cause_scope, target_ref?}` — always
  including the open-set arm (reuse `H_OTHER` semantics; never a closed set).
  Deliberately thin: models pad lists, and every required sub-field on a padded
  entry is a fabrication. Its only P0b job is opening an unresolved factor
  referencing ≥2 hypotheses plus the open-set arm; full structure (operation,
  confidences, claims) attaches at P1 when a cause promotes into
  `causal_hypotheses` — exactly when something starts consuming it (standing
  constraint 2 applied to this spec's own proposal).
- `postdictive_claims` (renamed from v2's inline predictions): a list of
  deterministic implications (`{criterion_id, must: fail | not_full_credit}` —
  "if H, criterion C must fail"), plus optional free-text soft claims. NOT
  per-criterion outcome distributions: the only consumers are the §5.6
  trace-consistency veto (deterministic) and advisory reviewer context, and
  distributions over four outcomes × criteria × causes are fabricated
  precision at real token cost. Produced after the model saw the trace, so
  they are explanatory claims usable for deterministic consistency checks (a
  contradiction is a contradiction whenever predicted) — they NEVER feed
  synthetic likelihood or probe discrimination. Blind prediction bundles are a
  separate P2 artifact (§7).

`RepairSuggestion`: add `target_criterion_ids`; allow empty
`target_evidence_families`. Bump `GRADING_PROMPT_VERSION`.

### 5.2 Prompt & targeting policy rewrite

Name a facet only when the failed step exercises that facet's *claim*; prefer an
item-step/criterion target or a reasoned abstention over stretching to the
nearest listed facet. Passing a criterion that exercises a facet is positive
evidence FOR it. `facet_contrast` only for demonstrated contract-swaps. Spell
out confidence semantics (causal ≠ outcome). Abstention is the stated default
and FILLING is what needs justification: naming a facet requires citing the
step that exercises its claim; null never needs a defense (the reasoned
`abstention_reason` covers the resolution axis, not every empty field).

Sequencing: the "no listed facet applies" arm is the single highest-leverage
change in this spec and the schema already tolerates empty target lists — it
ships as the first commit after P0a, ahead of the full rewrite.

### 5.3 Unresolved-cause routing

Stop backfilling `attribution_json` for attributions that are not `resolved`
(`attempts.py:~1182`), so failed multi-target criteria reach
`observed_unresolved_failure` and open an unresolved-cause factor referencing
the candidate hypothesis set.

One caution while P0-era factors exist: their candidate causes are the
criterion's AUTHORED targets — the vocabulary under indictment (on the exhibit,
{multiplication, addition}, neither the true cause). Cause-set discrimination
probes (`probe_targeting.py`, §11.1 priority 1 — a live consumer today) stay
gated until candidate causes carry the open-set arm: spending learner effort
discriminating between two wrong causes violates principle 8 in a new way.

### 5.4 Criterion-level calibration fix

Never replace the criterion vector with a response-wide score. Until
criterion-level calibrated interpretations exist: the **raw criterion fraction is
the directional outcome** (pass/fail, localization, attribution); response-level
calibration (`expected_true_score_fraction`, certainty LCB) scales **evidence
mass/authority only**. Touchpoint: `canonical_projection.py:355-420`. The
directional half ships at P0a (§4 item 5) as the firewall's precondition; this
section retains the evidence-mass side.

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
  valid probe reproduces the blind pre-registered signature — enforced in code,
  not by attempt type: `_promotion_reason`'s probe arm must check signature
  reproduction, not `attempt_type == diagnostic_probe` (§4 item 4); (b)
  recurrence on a fingerprint-distinct independent evidence group (near-clones
  do not count); (c) deterministic proof the response necessarily instantiates
  the rule + learner confirmation; (d) human adjudication.
- **Trace-consistency check:** hard veto only when a *deterministic* postdictive
  claim ("if H, criterion C must fail") is contradicted by a full-credit
  criterion that actually elicited the rule; soft free-text claims are advisory
  context for review, never quantitative likelihood. Hypotheses carry
  `applies_when` / `does_not_apply_when` so non-elicitation isn't contradiction.
- `doesnt_fit` learner feedback is bounded negative evidence with typed reasons
  (slipped / notation confused me / item ambiguous / other valid approach /
  diagnosis wrong) — an evidence channel, not an override.
- **Remediation runs on provisional beliefs.** Repair episodes and cold retries
  currently require an ACTIVE DURABLE misconception
  (`services/remediation.py:26-28`); with `first_error_trace` disabled, every
  first-occurrence error would leave the repair lane dark until recurrence.
  Rewire episode opening to accept a provisional belief — routing and probe
  selection are inside its permitted uses, and a cold retry is practice
  targeting, not facet damage. This also rights an inverted flywheel:
  provisional belief → repair episode → cold retry on a distinct surface → a
  reproduced error IS promotion condition (b). Facet locks and permanent
  corrections still require durable status.
- **Learner self-report disambiguation.** When an unresolved-cause factor
  opens, the feedback screen asks ONE typed question — reusing the
  `doesnt_fit` vocabulary (slipped / I believed X / item unclear / other valid
  approach) — before the learner context-switches. Learner confirmation is a
  §2-sanctioned confirmation channel, and the question costs seconds on
  principle 8's burden scale: the cheapest probe the system will ever run, at
  the moment context is freshest. A self-report is evidence toward resolution,
  never an override; "I believed X" plus a trace-consistent hypothesis resolves
  the factor and yields the provisional belief immediately.

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
  `missing_required_step` anchors their referents. `trace_contract` is NULLABLE
  with a declared status: some expected answers do not decompose cleanly, and
  forcing a checkpoint chain recreates the `criterion_facet_weights` disease
  one level up — an authored map obligated to exist is false at mint time. A
  contract may declare `no_reliable_decomposition`; repair machinery then
  degrades to whole-answer anchors and skips backtracking-depth terms.
- **Attempted items are never rewritten in place.** Original contract versions
  preserved; corrections create new versions plus append-only measurement
  corrections tagged with the consuming projection version. Unattempted items
  may be re-audited directly.
- Misconception cleanup: existing `first_error_trace` rows (including
  `01KY64GVAMY6MWXKXHK4DKW7B7`) marked `demoted`/superseded, history intact.

### 5.8 Variant authoring honesty (harder/easier siblings)

Second exhibit: batch `01KY8JWGDNWFGHBGBRWCKA54BQ` (fixtures/linear_algebra)
requested a HARDER sibling of "find two distinct square roots of 𝑖" — a
multi-step inverse problem (expand a general square, equate parts, sign-case
analysis, enumerate both roots) — and produced a single-step forward affine
evaluation in a story context with a prompt-enumerated binary "method choice":
difficulty 0.32 against the parent's 0.35, span `single_step` against
`multi_step`. Two causes, same disease as §0: the parent's facets name
component arithmetic, not demand structure (root cause 8 corrupting authoring
instead of attribution), and the rung ladder redefined "harder" as "next
capability waypoint" whose bounds legislated the parent's depth away — while
the variant prompt *mandated* facet inheritance
(`rung_variants.py:_variant_instructions`). The item was valid, numerically
audited, and fully compliant; the contract encoded the wrong meaning of
"harder." A specification failure, not a compliance failure.

Rules — all direction-symmetric; every guard binds `easier` as the mirror:

1. **Deterministic direction audit.** `harder` ⇒ variant difficulty strictly
   above the parent's; `easier` ⇒ strictly below. No demand axis (span,
   complexity, response, scaffolding, transfer) may move AGAINST the declared
   direction — regress under `harder`, deepen under `easier` — unless declared
   as an intended trade (rule 2) and surfaced at review. Pure structural
   comparison, no LLM, no threshold, no new schema: it ships at the front of
   the queue, alongside the P0a release train. On the exhibit batch it fires
   twice (0.32 < 0.35; `single_step` < `multi_step`).
2. **Directed-manipulation contract, declaration half at P0b.** A variant
   proposal declares `intended_manipulations` (axes moved, with direction),
   `incidental_changes`, `held_constant`, and — when the parent carries a
   trace contract — which checkpoints it preserves / deepens / drops. Dropping
   checkpoints under `harder`, or adding them under `easier`, must be declared;
   silent divergence is rejected deterministically wherever comparable
   (difficulty, task features, checkpoint sets). The adversarial-LLM half of
   the diff audit joins at P2 (§7) — the declarations are its training and
   audit substrate in the meantime.
3. **`rung_shift` is not a direction.** When the target rung's task-feature
   bounds cap any axis below the parent's current value (or floor one above
   it, for `easier`), the request is a capability SHIFT, not a harder/easier
   sibling — type it `rung_shift` and route it as trajectory movement.
   Harder/easier-within-waypoint (difficulty moves inside the band, same
   capability, demand axes free to move WITH the direction) and climbing or
   descending the ladder are different products; conflating them is how
   "harder" produced easier.
4. **No mandated facet inheritance.** Replace "evidence_facets MUST be exactly
   the source item's facet ids" with: the parent's facets are a PRIOR; the
   variant independently recompiles its measurement targets, may name a strict
   subset, and may abstain per §5.1/§5.2 — an abstention here becomes a
   missing-vocabulary note (§13), which on this parent is the first step
   toward minting the facets the vocabulary lacks (sign-case analysis,
   solution enumeration). This is §7's no-inheritance rule for probes, applied
   to variants at P0b.
5. **The generator sees the demand profile, not excerpts.** Variant generation
   receives the parent's full rubric criteria, task features, difficulty, and
   trace contract when present — not truncated prompt/answer excerpts plus
   facet ids. "Same knowledge, different depth" is not expressible in a
   vocabulary that cannot state the depth.

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

**The mechanism taxonomy is minted here, from data.** P0b stores only free
snake_case `operation` values and NL cause statements (§5.1). At P1, cluster
the accumulated free-text operations and statements to propose the canonical
mechanism taxonomy; ids then attach to hypotheses (and to existing rows via
mapping), and the grading schema may reference the taxonomy only AFTER it
exists — with the abstention arm and fill-rate watch every enum gets. An
authored-up-front mechanism vocabulary is explicitly rejected: it would be
`criterion_facet_weights` again, one layer up.

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
contamination status (§7).

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
  Rung variants adopted the declaration half at P0b (§5.8); the
  adversarial-LLM half of their diff audit arrives here, sharing one
  mechanism across probes and harder/easier siblings.
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

## 8.5. P3.5 — Learning Pattern Discovery (shadow first)

This is the intermediate learning layer between the explicit LearnLoop model and
any future recurrent/state-space residual predictor. It does **not** cluster
learners. It discovers temporary, decision-relevant contexts in which a frozen
explicit prediction is systematically wrong.

The three jobs are separate:

1. **Residual slice discovery** — find compact, interpretable conditions under
   which the baseline systematically mispredicts.
2. **Latent regime discovery** — find recurring multivariate residual profiles
   not captured by authored descriptive templates.
3. **Temporal regime tracking** — determine whether a previously validated
   pattern is still active for this facet/capability neighborhood.

The governing rule is: **a learning pattern is a recurring predictive regime.**
Any semantic or causal explanation attached to it is a hypothesis that must make
new predictions. The user-facing term is `learning pattern`, never cluster,
learner type, or learning style.

### 8.5.1 Two residuals with different prerequisites

Keep two concepts distinct:

- **Predictive residual:** observed outcome minus the exact pre-response
  prediction frozen at decision time. For binary correctness,
  \(r_t = y_t - p_t^{(0)}\). This can be constructed as soon as honest baseline
  predictions and later outcomes join.
- **Causal-hypothesis residual:** observed response/signature features minus a
  candidate hypothesis's *blind* predicted features. This requires P2 blind
  prediction bundles. Postdictive claims generated after seeing the response
  cannot define this residual.

Predictive patterns can reveal learner structure, measurement failure, item or
grader artifacts, policy-version artifacts, or omitted context. They do not by
themselves choose among those explanations.

Every baseline record is immutable and contains the prediction, model and
algorithm versions, prediction timestamp, pre-decision feature snapshot, candidate
slate, selection propensity when randomized, and snapshot hash. Never recompute a
historical "baseline" with the improved pattern model — that erases the residual
being explained.

### 8.5.2 Two derived data views

The first implementation materializes versioned artifacts, not live normalized
state.

**Residual event** — one row per prediction opportunity:

```yaml
identity: {learner_id, administration_id, timestamp}
baseline: {prediction, model_version, algorithm_version, policy_version}
outcome: {value, outcome_kind, observed_at, availability_reason}
residuals:
  immediate_correctness: null
  criterion_distribution: null
  cold_retention: null
  cold_transfer: null
  latency: null
  hint_use: null
  confidence_calibration: null
context:
  facet_capabilities: []
  depth_rung: null
  representation_mode: null
  surface_family: null
  practice_intent: null
  directness: null
  measurement_ambiguity: null
  scaffold_level: null
  source_visible: null
  delay: null
  recent_exposure: null
  intervention_family: null
  grader_reliability: null
versions: {feature_schema: ..., projection: ...}
```

**Residual profile** — a past-only rolling summary for
learner × facet × capability × cutoff time:

```yaml
support:
  observation_count: 0
  independent_surface_count: 0
  independent_group_count: 0
  time_span_days: 0
residual_summary:
  mean_immediate: null
  mean_cold: null
  variance: null
  trend: null
contrasts:
  scaffold_independent_gap: null
  familiar_novel_surface_gap: null
  component_integration_gap: null
  confidence_calibration_gap: null
  by_representation: {}
  by_depth_rung: {}
  by_delay_band: {}
quality:
  direct_evidence_fraction: null
  cold_evidence_fraction: null
  grader_reliability: null
  measurement_ambiguity: null
```

Profiles are runtime state representations, not independent statistical samples.
Overlapping snapshots derived from the same attempts never multiply support.
Bootstrap/resampling units are independent groups such as learner (when pooled),
session/time block, item fingerprint family, and correlation/surface group — not
profile rows.

Delayed retention and transfer outcomes are selectively observed. Every residual
dimension carries an availability mask and scheduling reason; unobserved future
outcomes are never imputed as zero. Evaluation stratifies or adjusts for the
measurement policy and logged propensities where appropriate.

### 8.5.3 Discovery-time versus decision-time features

Retrospective discovery may use the completed response, immediate residual, and
later cold/transfer residuals. A live gate predicting whether the *next*
opportunity matches a pattern uses only information available before that
opportunity's answer:

```text
pre-response explicit state
item/task properties
past residual history
representation and depth demand
surface familiarity and source exposure
session context
```

Each feature declares an availability phase:
`pre_selection | pre_response | post_response | delayed_outcome`. The prospective
gate fails closed if its input includes a later phase than its decision.

Residual features primarily determine novel-pattern geometry. Contextual
descriptors explain, stratify, and prospectively recognize the result. Do not let
high-cardinality facet/item/source IDs or task metadata dominate the geometry and
merely rediscover "diagram questions" or one domain. Structured residuals and
semantic embeddings are separate discovery views:

- structured view — under what measurable conditions is the predictor wrong?
- semantic view — what do the answers, items, or first-error traces mean?
- agreement — does a stable pattern appear in both views, and can a compact rule
  recover it?

Never concatenate a large semantic embedding to a small structured vector and
interpret the resulting Euclidean clusters as learning regimes.

### 8.5.4 Staged discovery stack

**Stage A — authored descriptive templates + interpretable slices.** Begin with a
small, provisional, open-set library:

```text
warm_success_cold_failure
scaffold_dependence
surface_familiarity
representation_transfer_gap
component_integration_gap
systematic_underprediction
systematic_overprediction
item_grader_or_generation_mismatch
unstable_or_insufficient_evidence
H_OTHER
```

These are observable pattern descriptions, not causes or canonical facets.
Initially a template is `matched | compatible | contradicted | insufficient`;
there is no invented probability without a fitted, calibrated recognizer.
Interpretable subgroup/error-slice discovery searches for compact conditional
rules whose residual distribution differs materially from the baseline, with
complexity/multiple-testing control and chronological confirmation. This is the
first production candidate and the highest-ROI path for item, grader, generator,
warm/cold, familiar/novel, representation, and integration failures.

**Stage B — density discovery in shadow.** Run HDBSCAN over a compact, robustly
scaled residual-profile vector with an explicit noise outcome. Sweep reasonable
minimum-cluster sizes and calculate block-bootstrap co-membership. HDBSCAN
membership strength, outlier score, and bootstrap stability remain separately
labeled — none is a posterior probability that a learner state is real.

**Stage C — interpretation.** For each stable candidate, assemble:

```text
medoid profiles and events
nearest nonmembers/counterexamples
compact rule approximation
dominant residual dimensions
overrepresented task and version properties
independent support and stability
chronological validation status
existing facets, hypotheses, and repair classes
```

The LLM returns a descriptive label, candidate mechanism, alternatives,
confounders to check, discriminating probe, safe user language, and claims not
supported. Local code owns membership, stability, residual estimates, validation,
and permitted uses. The LLM never determines membership or promotion.

**Research comparators, not v1 dependencies:** PLSCAN
(arXiv:2512.16558) tests multiscale density persistence; a variational Bayesian
Gaussian mixture may test soft ellipsoidal regimes; Domino-style
(arXiv:2203.14960) or MCSD-style (AAAI-26, DOI:10.1609/aaai.v40i33.40016)
methods become relevant for the separate unstructured/semantic view. SSD++-style
MDL subgroup lists (DOI:10.1007/s10618-022-00856-x) inform Stage A. These methods
must beat the simpler slice/HDBSCAN baselines on LearnLoop's chronological
outcomes before earning plumbing.

The error-slice framing follows Slice Finder (ICDE 2019) rather than generic
learner clustering. The human slice-discovery evaluation
(DOI:10.1609/hcomp.v11i1.27548) motivates the separate interpretation-validation
gate: coherent examples can help hypothesis formation without proving that the
attached explanation is correct.

### 8.5.5 Uncertainty, promotion, and permitted uses

Store distinct quantities with distinct semantics:

```text
assignment_support          # method-specific, e.g. HDBSCAN strength
outlier_score
resampling_stability        # co-membership frequency under blocked resampling
prospective_match_probability  # only after a fitted/calibrated past-only gate
causal_support_score        # belongs to causal hypotheses, never the cluster
```

Lifecycle:

```text
candidate
  → resampling_stable
  → described
  → future_validated
  → routing_authorized
  → intervention_linked
  → causally_tested
  → resolving | retired | superseded
```

- `candidate`: no authority.
- `resampling_stable`: analytics only.
- `described`: may generate a machine-review or diagnostic proposal.
- `future_validated`: may receive a bounded prediction adjustment or routing
  suggestion under an explicit authorization receipt.
- `intervention_linked`: observational treatment response; shadow intervention
  ranking only.
- `causally_tested`: limited intervention-policy input, requiring randomized or
  defensibly adjusted cold outcomes and action overlap.

`causally_tested` authorizes only the tested pattern × intervention relation.
It does not promote the LLM's educational mechanism, and a successful repair
does not retroactively prove the diagnosis (§7).

Promotion uses eligibility gates, not one cluster-quality score:

1. independent support;
2. future residual materially different from zero;
3. resampling/hyperparameter stability;
4. chronological generalization;
5. compact description or reliable prototype;
6. a decision that would change;
7. non-artifact evidence, or explicit routing to the system-quality path;
8. abstention for ambiguous/low-support assignments.

Among eligible patterns, rank by a registered observable decision metric such as
problems or learner minutes to cold success, with uncertainty handled in the
conservative direction — never silhouette score. Claims of minutes *saved*
require the randomized comparisons reserved for P4.

Initial permitted uses are:

```text
analytics
machine-side item/grader/generator review routing
diagnostic proposal generation
shadow prediction correction
```

After prospective validation and per-use authorization:

```text
bounded prediction correction
bounded queue/probe routing
verification-timing adjustment
suppression of redundant near-clones
```

Always forbidden:

```text
mastery or canonical facet writes
depth certification
durable misconception promotion
causal-edge creation
permanent learner classification
unvalidated learning-style intervention
```

A system-artifact pattern flags review or regrade; it does not let the discoverer
confirm its own item/grader diagnosis or quarantine content by itself. Machine-side
confirmation follows the §2 producer/confirmer matrix.

### 8.5.6 Bounded correction and action robustness

For a future-validated pattern \(k\), estimate its correction directly on the
logit scale rather than adding a mean probability residual to a logit:

\[
b_k = \arg\min_b \sum_{t \in k} w_t\,
\mathrm{BCE}(y_t,\sigma(\mathrm{logit}(p_t^{(0)}) + b)) + \lambda b^2.
\]

At runtime, with a calibrated past-only gate \(\pi_k(x_t)\):

\[
\mathrm{logit}(p'_t) =
\mathrm{logit}(p_t^{(0)}) +
\mathrm{clip}\left(\sum_k \pi_k(x_t)b_k,\,-c,\,c\right).
\]

Shrinkage \(\lambda\), authority bound \(c\), eligibility, and calibration status
follow the parameter-registry lifecycle. A low-support or unstable pattern stays
near the explicit baseline; an unassigned profile receives no correction.

Typed routing is usually more valuable than the scalar correction:

| Pattern | Bounded action |
|---|---|
| Warm success / cold failure | Stop immediate clones; schedule delayed novel-surface verification |
| Scaffold dependence | Preserve guided evidence but require independent reconstruction before exit |
| Surface familiarity | Increase surface distance; withhold transfer authority from near-clones |
| Representation gap | Preserve demonstrated representation; serve a matched cross-representation probe |
| Components strong / integration weak | Skip prerequisite drilling; serve setup/whole-task coordination |
| Systematic underprediction | Offer a deeper measurement without certifying it |
| Item/grader/generator mismatch | Route to regrade/contract review; suspend no state solely from the pattern |
| Unmodeled residual | Open hypothesis expansion or one action-changing diagnostic proposal |

When two plausible pattern assignments imply the same safe action, take the
common action rather than probing membership. Probe only when the action differs,
matching §6.4's common-repair cover and §7's EVSI rule.

### 8.5.7 Temporal retirement

V1 uses an explicit lifecycle before a hidden-state model:

- activation requires independent, future-validated recurrence;
- authority decays with time and loss of applicability;
- cold contradictions move the pattern toward `resolving`;
- fresh independent success retires the routing adjustment while preserving
  history;
- a policy/item/grader version change can segment or supersede a pattern.

Bayesian online changepoint detection is a later comparator for sufficiently
dense, regularly interpretable streams such as cold residual or
visual-symbolic-gap sequences. HDP-HSMM and other duration models are research
only. Sparse irregular per-facet streams default to the explicit lifecycle;
model complexity cannot manufacture temporal identifiability.

### 8.5.8 Minimal persistence and rollout

Do not begin with normalized `residual_events`, profiles, runs, assignments,
prototypes, hypotheses, validations, routing rules, and changepoints tables.
Residual events/profiles are reproducible joins over immutable snapshots,
predictions, outcomes, and versions.

First persist one content-addressed, versioned pattern-run artifact registered
with the derived-state rebuild machinery. It contains:

```text
input and availability manifests
feature schema/transforms and training cutoff
event/profile hashes and independent-group map
algorithm, parameters, seeds, and resampling manifest
assignments, outlier scores, and stability
medoids, counterexamples, and compact rules
LLM interpretation proposal + agent run
artifact audit and prospective validation
permitted uses and authorization receipt refs
```

Add a small append-only `learning_pattern_events` lifecycle table only when
cross-run activation/retirement queries demonstrate the need. Promote other
payloads to tables only on demonstrated query or integrity requirements. A
routing authorization is an immutable receipt, never a mutable property silently
attached to a cluster.

Rollout:

1. **Residual data artifact:** P0 measurement honesty, frozen predictions,
   feature-availability audit, past-only profiles, cold-outcome linkage. No
   pattern authority.
2. **Interpretable slices:** authored descriptive templates and compact subgroup
   rules, with item/grader/generator audits first. Analytics and machine review.
3. **Density discovery:** HDBSCAN grid, blocked-bootstrap consensus, prototypes,
   LLM descriptions. Shadow only.
4. **Prospective gate:** chronological validation and explicit abstention.
5. **Bounded authority:** prediction/routing uses promoted independently.
6. **Temporal and causal use:** change detection only when data-dense; treatment
   response only after overlap/randomization and cold outcomes.

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

Future recurrent, state-space, or other sequence predictors may consume
future-validated prospective pattern assignments as a low-weight auxiliary target.
Cold delayed-outcome prediction remains the primary objective; the auxiliary
weight is ablated/decayed so the learned model is not forced to reproduce an
imperfect discovered ontology. This spec does not pre-commit to a GRU or any
particular successor model. Learning patterns remain interpretable diagnostic
views even if a later predictor internalizes their useful signal.

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
- **Make the no-rung routes reachable (P0a effect, P0b volume).** The journey
  already has slots for item-fault / grader-fault / unresolved ("opens no
  ladder rung") — near-dead paths today because upstream manufactures
  certainty. The P0a deletions make them reachable; the traffic arrives with
  P0b, when 5.2's abstention arm and 5.3's backfill stop remove the forced
  facet naming that keeps suppressing them in the interim. Before "three
  failures on distinct surfaces" flags a run for review, run machine-side
  resolution (regrade, verifier — 6.5) to test whether the *surfaces* were bad.
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
- **Learning-pattern boundary (P3.5).** The run's frozen pre-decision snapshots
  and burned cold surface feed residual-pattern validation. Only a
  future-validated, routing-authorized pattern may adjust run priority or
  verification timing; its name never opens a rung, certifies a capability, or
  substitutes for the triage cause set. Pattern receipts and diagnosis receipts
  cross-reference IDs without copying claims.
- **Scope boundary.** Ladder rung outcomes stay lightweight self-reports;
  rich attribution applies where grading evidence exists (baseline,
  practice-pool attempts, cold assessment). Do not grow rung logging into a
  candidate-cause questionnaire.

## 11. Migrations & cleanup

- P0a: none (deletions + barriers + the directional criterion-outcome fix +
  fixtures).
- P0b: attribution axes + divergence anchors + thin candidate causes on grading
  storage; `measurement_status` + embedded nullable `trace_contract` on
  assessment contracts (append-only versioning for attempted items);
  misconception lifecycle statuses; demote-don't-delete; remediation episodes
  keyed to provisional beliefs; rung-variant direction typing
  (`harder | easier | rung_shift`) and manipulation-declaration +
  direction-audit fields on variant proposals (§5.8 — the direction audit
  itself needs no schema and lands with the P0a release train).
- P1: `causal_hypotheses` table; receipt payloads (existing storage);
  `misconception_candidates` → projection; canonical mechanism taxonomy minted
  from clustered free-text `operation`/statement values (§6.1).
- P3: `agent_runs` token/latency/cache columns; simulation cache.
- P3.5: no normalized residual/cluster schema initially. Persist one versioned,
  content-addressed pattern-run artifact through the derived-state rebuild
  machinery. Add append-only `learning_pattern_events` only after demonstrated
  cross-run lifecycle queries; routing authority lives in receipts.
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
  Variant-authoring fixtures (§5.8): the harder-sibling exhibit (batch
  `01KY8JWGDNWFGHBGBRWCKA54BQ` — the direction audit rejects the difficulty
  inversion and span regression and offers `rung_shift` retyping); its
  easier-direction mirror (an "easier" sibling that silently deepens demand is
  rejected symmetrically); a legitimate harder-within-waypoint variant that
  passes all audits (positive control — the guards must not suppress valid
  variants); and a facet-abstaining variant whose abstention yields a
  missing-vocabulary note rather than a validation failure.
- **Replay harness:** re-normalize existing vault attempts; report blocked
  promotions, firewall triggers, facet-outcome deltas, abstention AND fill
  rates by model/prompt version (both tails of the lazy/eager spectrum,
  standing constraint 2).
- **Learning-pattern regression matrix (P3.5):** warm-success/cold-failure;
  familiar-surface success/novel-surface failure; symbolic success/visual
  failure; component success/composite failure; one generator/grader-version
  artifact; general underprediction; insufficient-evidence/no-pattern; a pattern
  that genuinely resolves; and two ambiguous assignments sharing one safe
  action. Each fixture asserts the frozen baseline, feature availability,
  independent-group accounting, artifact routing, and forbidden state writes.
- **Pattern leakage and dependence tests:** a profile at cutoff \(t\) contains
  only prior events; a live gate cannot read post-response/delayed features;
  missing cold outcomes stay masked; overlapping rolling profiles do not
  multiply support; resampling blocks by learner/session/item-fingerprint or
  correlation group; historical baselines are never recomputed.
- **Pattern evaluation:** chronological, prequential prediction lift (log loss,
  Brier, ECE, cold-transfer calibration); blocked-bootstrap co-membership and
  hyperparameter stability; assignment abstention/outlier consistency; compact
  rule fidelity against medoids and nearest counterexamples; and an artifact
  audit over algorithm, policy, grader, generator prompt, source, template,
  session position, and interface versions. Silhouette score is diagnostic only,
  never a promotion gate.
- **Pattern decision value:** false rung exits, unnecessary probes/near-clones,
  irrelevant prerequisite drills, bad-item/grader routing precision,
  problems-to-cold-success, and learner minutes to cold success. A routing rule
  promotes independently from a prediction correction; each must beat the
  explicit-baseline action on chronological data before live authority.
- **Interpretation validity:** reviewers see medoids and nearest nonmembers, then
  judge whether the description captures the shared predictive issue, whether
  included examples differ materially, and whether recognizing it changes an
  action. A fluent LLM description and stable geometry are never sufficient
  causal validation.
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
- No clustering of people, permanent learner types, or learning-style routing.
  Learner-facing patterns are temporary facet/capability/episode-scoped
  predictive regimes; system-quality patterns are instrument/family/version
  scoped. Both have an explicit no-pattern arm.
- No cluster membership as mastery, certification, misconception, causal edge,
  or item/grader confirmation. A cluster may propose or route a check; it cannot
  confirm its own interpretation.
- No research-stack maximalism in v1: HDBSCAN follows interpretable slices;
  PLSCAN, Bayesian mixtures, BOCPD, active constrained clustering, and hidden
  semi-Markov models remain comparators until data and held-out decision lift
  justify their plumbing.
- No recomputation of historical baseline predictions, no treating overlapping
  rolling profiles as independent samples, and no zero-imputation of missing
  delayed outcomes.
- No changes to the learner-facing feedback *generation* path through P0; at P1
  it becomes receipt-checked with typed display (6.6) — checked, not
  regenerated.
- No schema growth beyond demonstrated decision value (standing constraint 2):
  when in doubt, keep it NL + JSON and let validators, not fields, carry rigor —
  with abstention explicit and its rates watched.
