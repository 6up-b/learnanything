# Unified implementation plan — causal attribution · diagnostic augmentation · measurement efficiency (v1)

**Status:** agreed shipping order across the three active specs. Derived from a
code audit of the working tree at `0b10c4d` (plus uncommitted changes) on
2026-07-26. Item statuses below are **verified against code**, not against the
specs' own claims.

**Inputs:**

- `spec_causal_attribution_v1.md` — epistemics authority (firewalls, promotion,
  causal-state ownership). P0a/P0b/P1 shipped; P2 partially wired.
- `spec_diagnostic_augmentation_v1.md` — diagnostician measurement & improvement.
  Phase A half-shipped; Phases B–D absent.
- `spec_measurement_efficiency_v1.md` — instruments, inference, certification.
  Step 0 and D3 shipped; everything else absent.

Each stage item carries its provenance tag `[Spec §item]`. Nothing here changes
any spec's content; the only deliberate override of a spec's *internal* ordering
is called out in §2 (measurement §5.7 pulled forward).

---

## 1. Verified status snapshot (audit summary)

### Causal spec — ~90% shipped and wired

- **P0a:** all deletions, both write barriers (`services/grading.py:303-464`,
  wired at validator and attempt boundaries), firewall telemetry + CLI. DONE.
- **P0b:** all §5.1 attribution axes live and consumed; `diagnosis_md`
  prose-first enforced; §5.3 backfill stop + unresolved-cause routing live;
  §5.6 mostly live (contest UI, disambiguation question, remediation from
  provisional beliefs); §5.7 `measurement_status` + `trace_contract` +
  append-only versioning; §5.8 variant direction audit production-wired. DONE
  except: **only 2 of 4 durable-promotion arms exist** — arm (c) mints only a
  candidate, arm (d) adjudication has no path into `_promote_candidate`.
- **P1:** `causal_hypotheses`, receipts + `permitted_uses` (fail-closed),
  `select_minimal_repair` with the exact A1 rank order
  (`REPAIR_POLICY_VERSION = structural_lexicographic_v2`), sympy verifier
  wired, claim-check overlay in UI, inspector CLI. DONE except
  `TestExecutionVerifierAdapter` unreachable (dispatch covers only
  `symbolic_equality`/`exact_match`).
- **P2:** the split is sharp. **Wired:** orchestrator hub + RPCs + post-attempt
  hook, EVSI `decide_probe` + receipts, repair-class-divergence blocking,
  contamination classes, delayed cold verification. **Dark:** the probe
  administration lane — `create_probe_candidate`, `transition_probe_candidate`,
  and `generate_blind_prediction_bundle` have **no production callers**, so
  `instrument_available` is permanently False, `probe_now` always degrades to
  `no_discriminating_instrument`, and `causal_discriminating_observations`
  (migration 130) can never be written. `audit_manipulation_contract` /
  `validate_independent_measurement_contract` have zero callers.
- **P3 / P3.5 / P4:** absent, as sequenced. (`src/learnloop/sim/` belongs to
  older specs.) P4's training substrate (receipts + cold verifications) exists.

### Augmentation spec — Phase A half done; B/C/D absent

- **A1** rank reorder: DONE (exact spec match, typed
  `unverifiable_checkpoint_claim`, `LATENT_COST_RESOLUTION_FLOOR`,
  `selection_basis`).
- **A2** taxonomy key: **NOT done and live** — `mint_causal_mechanism_taxonomy`
  still groups on the exact `operation` string (`exact_operation_v1`), and
  `learnloop build-causal-taxonomy` is accruing append-only assignments under
  the wrong key. Debt grows with every run.
- **A3** typed hold: DONE (as a status, deliberately not an error;
  `needs_disambiguation` reaches the UI).
- **A4** adjudication store: DONE (migration 126, six verdicts, version
  pinning, `queue_reason`, real scoreboard) but **CLI-only** and **cannot
  promote anything** (no arm-(d) path).
- **A5** missing-vocabulary notes: ABSENT. Abstention rate surfaced nowhere
  (`services/causal_health.py` is 348 lines of dead code).
- **A6** learner-visible corrections: ABSENT. Demotion events exist
  (migration 116) and a "presented" store exists (`hypothesis_events`), but
  nothing joins them; no `surfaced_to_learner` flag.
- **A7** `agent_runs` token columns: ABSENT (naming precedent in
  migration 093 for reader jobs).
- **B1–B4:** ABSENT. Existing planted harnesses score the *instrument* or use
  hand-constructed grades; none scores the diagnostician blind, and the one LLM
  planted-trial path has the same-model generator/labeler defect B3 names.
- **B5:** 4 of 14 metrics have producers (anchor accuracy, repair-class match,
  abstention precision/recall — all from A4's scoreboard). **No producer** for
  `problems_to_cold_success`, `harmful_write_rate`,
  `tokens_per_resolved_diagnostic_episode`, `planted_vs_adjudicated_agreement`,
  `probe_action_change_rate`, or any of the five §5.7 certification metrics.
- **C1–C4:** ABSENT. Note: C1 (repair-first ordering) conflicts with causal
  §5.1 (`diagnosis_md` first) — only the causal ordering is honored today.
- **Phase D:** ABSENT (blocked on A5 capture). Facet review surface exists
  (`facet-candidates` CLI + RegistryReviewScreen) but nothing routes
  abstentions into it.

### Measurement spec — Step 0 + D3 done; the rest absent

- **Step 0 (§5.8):** done; verdict stands — the bottleneck is the instrument
  pool (86% of contract cells unreachable, 0 coordination instruments, 72% of
  attempts wasted on capability mismatch), so Part III waits.
- **D3** integration gate at ingest: DONE (prompts constraint 14, nullable
  no-default `SynthIntegrationComponent.capability`, dropped-with-diagnostic,
  coordination kept-and-flagged). The 18 already-persisted coordination
  integrations are NOT backfilled.
- **§3.0** persona gate: exists but its only ship/no-ship caller is test-only;
  the live `generate-diagnostics` route never touches it.
- **A1:** synthesis lane can author `targets`; **practice lane cannot** —
  `RubricCriterionPayload` has no `targets` field and pydantic silently drops
  one if emitted. Spread rule NOT inverted. Guards absent.
- **A2–A8, B1–B4, all of Part III, §5.8.2 doctor check, D1 rank, D2, E3, E4:**
  ABSENT. **B2 labels:** plumbing fully wired end-to-end; only the `inferred`
  (and `claimed`) vocabulary is missing. **§5.2:** uncommitted `scope_facets`
  is a real partial move but does not reach `covered_required_fraction`.
- **Uncommitted working tree contains:** D3, the capability-cell fix
  (`_observed_capability`), `scope_facets`, exam-pool conjunctive
  `(facet, capability)` coverage + practice floor, practice-item quality gates,
  strict-schema plumbing, the causal principle-8 amendment authorizing A8.

---

## 2. Ordering principles

1. **Capture-now data ships first** (augmentation standing constraint 6):
   every session without A2/A5/A6/A7 loses irreplaceable data or accrues
   wrong append-only records.
2. **Wire before build:** activating already-built machinery (P2 producers,
   promotion arms) is the highest value-per-line available.
3. **Metrics before the things they gate.** One deliberate override of a
   spec's internal order: measurement **§5.7 (metrics + delayed cold probe)
   moves from Wave 5 to Stage 4**, because Wave 3's instrument revert criteria
   consume those metrics (A1 reverts on the delayed cold probe and
   `harmful_write_rate`; A6/A7 revert on `problems_to_cold_success`).
   Shipping instruments with unmeasurable revert criteria is the exact defect
   the augmentation spec calls out for C3.
4. **Static analysis before instruments; instruments before inference;
   inference before certification.** Part III's unlock condition is the
   spec's own §5.8.2 verdict: the reachability report must show structurally
   certifiable contracts first.
5. **Every inference rule gets a static cells-converted precheck** before it
   is built (the §5.8.2 method generalized: B1 dominance looked like a major
   lever and converted 1 of 25 cells when measured).

---

## 3. Phase lane map

| Spec | Phases → merged stage |
|---|---|
| **Causal** | P0a ✅ · P0b ✅ · P1 ✅ · **P2 → Stage 2** (wiring only) · P3/P3.5 parked · P4 parked (trigger starts accruing at Stage 4) |
| **Augmentation** | **Phase A → Stage 1** (A2, A5, A6, A7; A4 promotion arm → Stage 2) · **B5 producers → Stage 4** · **B1–B4 → Stage 7** · **Phase C → Stage 7** · Phase D → continuous once A5 has volume · Phase E parked |
| **Measurement** | Step 0 ✅ · D3 ✅ · **Wave 1 → Stage 3** · **Wave 2 → Stage 5** · **Wave 3 → Stage 6** · **Wave 4 → Stage 8** · **Wave 5 → Stage 8** (§5.7 → Stage 4) · B4 parked |

---

## 4. Stages

### Stage 0 — land the working tree

~2,236 uncommitted insertions spanning all three specs (D3, capability-cell
fix, `scope_facets`, exam conjunctive coverage, quality gates, principle-8
amendment). Finished work at risk. Commit before anything else.

### Stage 1 — Augmentation Phase A, remaining items

| # | Item | Provenance | Notes |
|---|---|---|---|
| 1.1 | Fix taxonomy grouping key: shared episode repair class + probe discrimination profile; operation string demoted to label | [Aug A2] | **Most urgent item in the plan** — live and accruing wrong append-only assignments (`causal_attribution.py:877-889`); `repair_class_id` already selected and unused. Migrate existing assignments now, while volume is small. |
| 1.2 | `agent_runs` token columns + write path | [Aug A7] | One migration following `migrations/093` naming (`est_/actual_ input_/output_tokens`); populate from `ai/client.py` / `codex/client.py`. Unblocks `tokens_per_resolved_diagnostic_episode`. |
| 1.3 | Missing-vocabulary note store: append-only, written on abstention (incl. §5.8 facet-abstaining variants), version-stamped; abstention *rate* surfaced in the attribution audit CLI | [Aug A5] | Cannot be backfilled. While here: wire `causal_health.py`'s abstention rate into the CLI or delete the module (currently dead). |
| 1.4 | `surfaced_to_learner` flag + correction feed entry on demoted/retired surfaced beliefs | [Aug A6] | Join the existing `hypothesis_events 'presented'` store (migration 055) to `misconception_disposition_events` (migration 116); one new `learner_review_feed` entry kind. |

### Stage 2 — Causal P2 completion

| # | Item | Provenance | Notes |
|---|---|---|---|
| 2.1 | Wire probe-candidate + blind-bundle producers into the orchestrator commissioning path | [Causal §7] | `create_probe_candidate` / `transition_probe_candidate` / `generate_blind_prediction_bundle` currently have zero production callers; readers, EVSI rule, receipts, and migration-130 writer are already live. One producer lights the whole lane. |
| 2.2 | Adjudication → promotion arm (d); finish arm (c) | [Causal §5.6 via Aug A4] | Path from adjudicated verdicts into `_promote_candidate`. Until then the A4 store cannot change any belief. |
| 2.3 | Wire or delete the orphaned manipulation-contract auditors | [Causal §7] | `audit_variant_manipulation_contract` (zero callers incl. tests), `validate_independent_measurement_contract` (zero callers), `resolve_machine_check` (exported, no callers). Decide per §7 below. |

### Stage 3 — Measurement Wave 1 (static, zero learner cost)

| # | Item | Provenance | Notes |
|---|---|---|---|
| 3.1 | Contract-cell reachability as a standing `learnloop doctor` check: `REACHABLE / MISMATCH_ABOVE / MISMATCH_BELOW / NO_INSTRUMENT` per contract cell | [Meas §5.8.2] | Pure static analysis; the check whose absence let 43 attempts land on an uncloseable contract. Output doubles as Stage 5's commissioning queue. |
| 3.2 | Three-state labels `measured / inferred / unknown` (+ E2's `claimed` state) | [Meas B2, E2] | `facet_state_label` plumbing is already wired to the UI end-to-end; the prediction to render exists unlabelled in `selection_rewards.py:438`. Vocabulary change only; writes nothing, certifies nothing. |
| 3.3 | Coverage denominator → contract frontier, with capability axis | [Meas §5.2] | Extend uncommitted `scope_facets` into `covered_required_fraction` (`facet_diagnostics.py:150`); fix the vacuous no-items⇒1.0 case; variance floor relieved by inference at a discount. Ship with a learner-visible recalibration feed entry (uses 1.4) — displayed mastery will jump. Legacy vaults without contracts keep current behaviour. |
| 3.4 | Publish `measurement_rank` | [Meas D1] | Identifiability already computes the observing-criteria signature; this is counting independent dimensions vs facets declared. Analysis only; merges stay behind review. |

### Stage 4 — Scoreboard producers + delayed cold probe (pulled forward)

| # | Item | Provenance | Notes |
|---|---|---|---|
| 4.1 | `harmful_write_rate`, `problems_to_cold_success` producers | [Aug B5] | The two metrics the augmentation spec ranks first; currently no producer. |
| 4.2 | Delayed cold probe per certified LO (+2–3 weeks, held-out surface) + `false_certification_rate` | [Meas §5.7] | The only external validity check in a single-learner vault; also the ground-truth consumer nothing currently computes. Existing cold-probe machinery is repair-scoped — generalize the scheduler. The earlier this runs, the sooner cold-outcome labels accrue (causal P4's unpark trigger). |
| 4.3 | `questions_to_certification`, `certification_regret`, `cells_cleared_per_question` | [Meas §5.7] | Counters over existing attempt/exam logs. |
| 4.4 | `tokens_per_resolved_diagnostic_episode`, `probe_action_change_rate`, `planted_vs_adjudicated_agreement` scaffold | [Aug B5] | Tokens unblocked by 1.2. Agreement metric lands as a producer even while the planted side (Stage 7) is empty. |

**Why here:** Stage 6's instrument hypotheses/reverts are stated in these
metrics. B5 freezes before Phase C (Stage 7), after these are added.

### Stage 5 — Measurement Wave 2 (authoring correctness + gates)

| # | Item | Provenance | Notes |
|---|---|---|---|
| 5.1 | **Rung-correct generation:** practice generation authors at the capability the contract names, consuming 3.1's reachability report as a prioritized commissioning queue for `MISMATCH_BELOW` / `NO_INSTRUMENT` cells | [Meas §5.8.2 verdict; promoted to a named item] | The measured 72% lever — the single highest-ROI change in the measurement spec, and it needs no new instrument class. Hypothesis: contract-cell hit rate of new attempts rises from 28%. Revert: never (this is honoring existing contracts). |
| 5.2 | Backfill the 18 persisted coordination integrations under D3's criterion | [Meas §5.8.3/Wave 2] | Blueprints are vault content; no rebuild touches them. Expect most dropped, some lowered, a few genuinely `coordination` (owed an A1 capstone later). Pilot on one LO first, measure reachable-cell delta, then batch. |
| 5.3 | §3.0 planted-persona gate wired into the **live** generation path — tiered | [Meas §3.0] | Hard ship/no-ship for diagnostic instruments (error-hunts, contrast pairs, profiles); flag-for-review for plain practice items until Aug B2's realism matcher exists (authoring throughput is the measured bottleneck; don't throttle it on an unvalidated simulator). Track gate precision from day one. |
| 5.4 | D2 ingest mint gate: separability + distinct repair, typed rejection reasons, alias-not-mint | [Meas D2] | Before the next ingest round. Reuses the §3.0 harness; ingest payloads (`error_signatures` etc.) are the persona raw material. |

### Stage 6 — Measurement Wave 3 (instruments)

Ship order within the stage: 6.1 → 6.2 → 6.3, then 6.4 as fixtures permit.

| # | Item | Provenance | Notes |
|---|---|---|---|
| 6.1 | A1 conjunctive items: `targets: list[CriterionTargetPayload]` on `RubricCriterionPayload` (fixes the silent pydantic drop); spread rule made **posterior-aware** — author both conjunctive capstones and decomposed fallbacks, let selection pick (conjunctive when P(pass) high / certification hunting; decomposed when localizing a weak learner); guards: `unexercised_supporting_target`, embedded-share cap | [Meas A1, amended per review] | Largest lever on cells-per-question. Blanket spread-rule inversion is deliberately NOT adopted: a pool with only conjunctive items starves diagnosis. |
| 6.2 | A6 opportunistic trace evidence (positive-only, supporting-at-most, never certification-eligible) | [Meas A6] | Required to discharge A1's guard 1. Note `grading.py:600-603` currently *forbids* beyond-declared facets — this is a deliberate policy change at that validator. Elicitation rules: decision-point one-liners, rewarded never required, per-session budget. |
| 6.3 | A8 clarification channel: `provisional_pending_clarification` grade state, one question per attempt on hedged/abstained criteria only, timeout→abstention, replay-stable resolution | [Meas A8; authorized by the causal principle-8 amendment already in tree] | Reinforces the abstention discipline; ship early in the wave. Revert if clarification rate exceeds a small fraction of attempts (machine-resident uncertainty misclassified). |
| 6.4 | A2 laddered stems (kinship: correlated within column, independent across), A3 error-hunts (registry-planted, repair-required, clean-solution rotation — seed from the learner's own misconception registry as repair verification), A4 contrast pairs (`contrast_of` / `differing_component`; post-repair verification preferentially serves the isolating member), A5 discrimination profiles (`no_profile_applies` first-class), A7 adjacent-facet questions **(demoted: only if A8+A6 outcomes justify it)** | [Meas A2–A5, A7] | All behind the §3.0 gate. A5's profiles are Stage 7's planted-ground-truth producer. E4 (success+silence decay) is dropped from the plan (marginal yield, confident-wrongness risk). |

### Stage 7 — Augmentation Phase B, then Phase C

| # | Item | Provenance | Notes |
|---|---|---|---|
| 7.1 | B1 planted-misconception eval harness scoring the diagnostician **blind**, over the §12 regression shapes incl. abstention cases; B3 cross-model separation from day one (the existing planted-trial path has the same-model defect) | [Aug B1, B3] | Consumes A5 discrimination profiles (6.4) as authored planted ground truth — the producer B1 currently lacks. |
| 7.2 | B2 blinded persona-vs-real matcher | [Aug B2] | Licenses every B1 number; also upgrades 5.3's tiered gate to hard. |
| 7.3 | B4 planted-vs-adjudicated agreement live | [Aug B4] | Producer scaffold from 4.4; adjudicated side accrues via the contest-first queue. |
| 7.4 | Freeze B5; ship C1–C4 one rung at a time, each with hypothesis + revert | [Aug C] | **Resolve the C1 ↔ causal §5.1 conflict first** (recommended: diagnosis prose stays first, repaired trace moves ahead of the structured causal fields — satisfies both rationales). C3 revert is measurable via 1.2. C4's eval must include a mid-history cause change. |

### Stage 8 — Measurement Waves 4–5 (inference, then certification)

**Unlock condition:** the 3.1 reachability report shows structurally
certifiable contracts (Stages 5–6 are what create this).

| # | Item | Provenance | Notes |
|---|---|---|---|
| 8.1 | Static cells-converted precheck for B1 dominance and B3 entailment (principle 5 of §2) | [Meas §5.8.2 method] | Free. Last measurement: dominance converts 1 of 25 cells. Build nothing that doesn't move the count. |
| 8.2 | B1 capability dominance (embedded credit, assisted-attempts propagate nothing, sampled direct-probe audit) | [Meas B1] | Only if 8.1 justifies it post-Stage-5/6 (the pool will sit higher on the ladder by then, which is what makes dominance start converting). |
| 8.3 | B3 prerequisite entailment — shadow first, `hard`/`path_specific` edges only, per-edge violation tracking from day one | [Meas B3] | Same precheck discipline. |
| 8.4 | §5.3 substitution rule + certificate receipts (measured vs inferred, margins, integration never substitutable) | [Meas §5.3] | Certificates become withdrawable via 1.4's correction machinery when an edge retires. |
| 8.5 | C1 EIG-per-minute exam selection (adversarial weighting by P(below θ), over contract cells only) | [Meas §5.4, §5.6] | Confined to certification sittings; practice serving keeps the desirable-difficulty band objective — two objectives, one posterior, never conflated. |
| 8.6 | C2 adaptive sittings + posterior-threshold stop (superset reservation preserves leakage guarantees; never described as SPRT) | [Meas §5.5] | Revert if `false_certification_rate` (4.2) rises above baseline. |

---

## 5. Continuous / volume-gated

- **Aug Phase D** (abstention clustering by repair equivalence → facet
  proposals → human review): starts whenever 1.3's notes have volume. No stage
  dependency. Routes into the existing `facet-candidates` review surface.
- **Adjudication accrual** (Aug A4): contest-first queue keeps filling from the
  feedback screen; deliberate CLI verdicts as time permits. Feeds 2.2 and 7.3.

## 6. Parked, with named unpark triggers

| Item | Trigger |
|---|---|
| Aug Phase E / Causal P3 (simulation likelihood arm) | Planted-recovery stable across B1 refreshes + B4 agreement holding + real probe outcomes for prospective comparison |
| Meas B4 as selection model | §5.8 replay shows deterministic EIG leaving material regret + volume to fit item-family params + beats incumbent on held-out replay |
| Meas B4 as belief model | Never (permanent disposition; rationale rests on the receipts/governance mismatch, which multi-learner data does not dissolve) |
| Causal P3.5 (learning patterns) | ~10³ independent groups — realistically multi-learner data |
| Causal P4 (learned repair policy) | Cold-outcome volume from 4.2's delayed probes |
| Meas E4 (success+silence decay) | Dropped; revisit only with a concrete consumer |

## 7. Decisions to resolve (not code)

1. **C1 vs causal §5.1 field ordering** — recommended: diagnosis prose first,
   repaired trace second, structured causal fields last (7.4).
2. **Dead code disposition** — `causal_health.py` (wire the abstention rate or
   delete), `audit_variant_manipulation_contract` /
   `validate_independent_measurement_contract` / `resolve_machine_check`
   (wire at 2.1/2.3 or delete; if deleted, P2's manipulation-contract claim in
   the spec should be annotated as descoped).
3. **Persona-gate tiering** (5.3) — confirm flag-for-review is acceptable for
   plain practice items until B2 lands.
4. **`TestExecutionVerifierAdapter`** — wire a dispatch arm or mark descoped.

## 8. Cross-spec dependency summary

```
Aug A5 notes ──────────────► Aug Phase D (volume)
Aug A7 tokens ─────────────► tokens_per_episode (4.4) ──► C3 revert measurable
Aug A4 store ──► arm (d) (2.2) ──► adjudicated ground truth ──► B4 (7.3)
Causal P2 producers (2.1) ─► probe candidates/bundles ──► probe review ladder
Meas 3.1 reachability ─────► 5.1 commissioning queue ──► Part III unlock (8.x)
Meas §5.7 + B5 (Stage 4) ──► Wave 3 revert criteria (6.x) ──► Phase C gate (7.4)
Meas A5 profiles (6.4) ────► Aug B1 planted ground truth (7.1)
Aug B2 matcher (7.2) ──────► §3.0 gate hardens (5.3)
4.2 cold probes ───────────► false_certification_rate ──► C2 revert (8.6)
                        └──► cold-outcome labels ──► Causal P4 unpark
```

The shape of the whole plan: the causal spec finishes first (Stages 0–2)
because it is ~90% done and everything downstream writes through its
firewalls; the augmentation spec splits — capture items first (Stage 1),
measurement/improvement half late (Stage 7), because the instruments it
measures should exist first; the measurement spec occupies the middle
(Stages 3–6) because its own Step 0 proved the instrument pool — not the
diagnostician, not the decision rule — is the current bottleneck.
