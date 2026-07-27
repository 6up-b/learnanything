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

**Progress:** items are marked ✅ as they land, with a one-line note on what
shipped. Stage 0 ✅ · Stage 1 ✅ · Stage 2 ✅ · Stage 3 ✅ · Stage 4 ✅ ·
Stage 5 ⚠️ (5.1 ✅ 5.2 ✅ 5.3 ✅ 5.4 ⚠️, audited 2026-07-27) ·
Stage 6 ✅ (6.1 ✅ 6.2 ✅ 6.3 ✅ 6.4 ✅) · Stage 7 ✅ · Stage 8 ⚠️ (8.1 ✅;
8.2–8.6 pending).

**Original-spec audit correction (2026-07-26):** 5.3's gate mechanics are live,
but augmentation B2's blinded persona-vs-real matcher does not land until Stage
7. The measurement spec explicitly says pre-B2 verdicts “do not count,” so 5.3
cannot be called fully compliant yet. 5.4 uses exclusive normalized error
signatures as a structural authorability proxy; it does not actually author and
grade a discriminating item through §3.0's shared planted-persona harness. Both
are useful fail-typed scaffolds, but neither is the complete original gate.

**Verified integration state at Stage 3 close:** 309 tests pass across all new
work plus its regression surface; `tsc --noEmit` clean; migrations 131-134,
138-140 apply both as a fresh build from zero and as an incremental upgrade of both
real vaults, with `foreign_key_check` and `integrity_check` clean on each.

**Known pre-existing failures — 18, all present at `101474c`** and unrelated to
this plan; each reproduced on a pristine checkout of HEAD:
`tests/test_activity_backfill.py` ×2 (the fixture DB gained exam attempts the
backfill does not replay), `tests/test_grading_cli.py` ×2 (`registry audit` exits
1), `tests/test_sidecar_contract.py` ×2 (fixture facet drift),
`tests/test_graph_editor_reads.py` ×2 (the test asserts an empty facet registry
but `fixtures/linear_algebra/facets.yaml` carries 39 facets at HEAD; the other
fails on a drifted concept id), `tests/test_p0_projection_cutover.py` ×2,
`tests/test_tutor_promotion_w2.py` ×3, `tests/test_state_sync.py` ×2,
`tests/test_deferred_regrade.py` ×1,
`tests/test_ingest_transcripts.py` ×1 and `tests/test_span_view.py` ×1 —
**18 in total**. Not caused by any stage below. Fixing them is unclaimed work
outside this plan.

**Six more pre-existing failures found during Stage 6**, each verified against a
pristine checkout (a `git worktree` at HEAD, or by stashing the working tree):
`tests/test_registry_audit.py` ×6 (unregistered `animation.*` config leaves and
`grading:FIREWALL_*` module constants — Stage 6 adds none of its own; every new
decision parameter is registered), `tests/test_grading_context.py` ×1
(`target_criterion_ids` no longer in `targeting_policy`),
`tests/test_receipt_derivation.py::test_ready_derivation_none_on_legacy_vault`
(its skip guard checks for `mvp-0.7` but the fixture has drifted to `mvp-0.8`),
`tests/test_cli_json.py::test_doctor_json_contract`,
`tests/test_p0_cutover_mvp08.py` ×1, and
`tests/test_sim_probe_validation.py::test_planted_types_pass_the_checkpoint_gate`.
`tests/test_span_view.py` now passes. Also outside the plan; listed so a later
reader does not attribute them to Stage 6.

Those last five share **one** root cause worth knowing before anyone chases them
individually: `config.py`'s `claim_prior_min_variance = 2.0` at HEAD, against tests
that assert the pre-change `0.25`/`1.0` seeds (`mastery.py` computes
`max(1/4.0, 2.0) = 2.0`). `config.py`, `mastery.py` and `state_sync.py` are all
unmodified in the working tree, so it is a config/expectation drift, not code.

**`fixtures/*/state.sqlite` show as modified**, and the change is benign: both
live vaults had migrations 131-134, 138, 139 applied when a service opened them
(`Repository()` migrates on construction). Schema-only — attempt counts are
unchanged at 43 and 27. Reverting would only defer the same migration to the next
time the app opens the vault.

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
- **§3.0** persona gate mechanics: LIVE but validity-gated at Stage 5.3 —
  `services/persona_gate.py` rides the
  `row_transform` seam on every generation route. (The bypass, located: the gated
  entry point `proposals.generate_diagnostic_proposal(need_id=)` had *no* production
  callers, while `learnloop generate-diagnostics` goes through
  `practice_generation.generate_diagnostic_practice_proposal`.)
- **A1:** synthesis lane can author `targets`; **practice lane cannot** —
  `RubricCriterionPayload` has no `targets` field and pydantic silently drops
  one if emitted. Spread rule NOT inverted. Guards absent.
- **A2–A8, B1–B4, all of Part III, §5.8.2 doctor check, E3, E4:**
  ABSENT. **D1 rank:** shipped at 3.4. **D2 structural proxy:** shipped at Stage 5.4
  (`services/facet_mint_gate.py`, wired in `source_set_synthesis._normalize`);
  the literal shared-harness execution remains open. **B2 labels:** plumbing fully wired end-to-end; only the `inferred`
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

### Stage 0 — land the working tree ✅

~2,236 uncommitted insertions spanning all three specs (D3, capability-cell
fix, `scope_facets`, exam conjunctive coverage, quality gates, principle-8
amendment). Finished work at risk. Commit before anything else.

**Landed as `101474c`** ("last commit save before big changes").

### Stage 1 — Augmentation Phase A, remaining items ✅

| # | Item | Provenance | Notes |
|---|---|---|---|
| 1.1 ✅ | Fix taxonomy grouping key: shared episode repair class + probe discrimination profile; operation string demoted to label | [Aug A2] | **Most urgent item in the plan** — live and accruing wrong append-only assignments (`causal_attribution.py:877-889`); `repair_class_id` already selected and unused. Migrate existing assignments now, while volume is small. |
| 1.2 ✅ | `agent_runs` token columns + write path | [Aug A7] | One migration following `migrations/093` naming (`est_/actual_ input_/output_tokens`); populate from `ai/client.py` / `codex/client.py`. Unblocks `tokens_per_resolved_diagnostic_episode`. |
| 1.3 ✅ | Missing-vocabulary note store: append-only, written on abstention (incl. §5.8 facet-abstaining variants), version-stamped; abstention *rate* surfaced in the attribution audit CLI | [Aug A5] | Cannot be backfilled. While here: wire `causal_health.py`'s abstention rate into the CLI or delete the module (currently dead). |
| 1.4 ✅ | `surfaced_to_learner` flag + correction feed entry on demoted/retired surfaced beliefs | [Aug A6] | Join the existing `hypothesis_events 'presented'` store (migration 055) to `misconception_disposition_events` (migration 116); one new `learner_review_feed` entry kind. |

**1.1 as shipped** (migration 133): the grouping key is
`(repair_equivalence_id, cause_scope, discrimination_profile)`, algorithm
`repair_equivalence_probe_profile_v1`. Two structural findings forced design
choices the item did not anticipate: (a) `repair_class_id` hashes `episode_id`,
so it can never relate two episodes — a cross-episode `repair_equivalence_id`
(operator + target/preserve refs, model self-reports excluded per A1) is what
the key actually needs; (b) the repair-class *definition* lived only in
`attempt_debug_payloads`, which replay rebuilds, so migration 133 adds a durable
append-only `causal_repair_class_definitions` store written at materialization.
`cause_scope` joins the profile because a `learner_state` and an `item_contract`
cause need different instruments even under an identical repair. Four typed
abstention arms (`insufficient_support`, `unmapped_repair_class`,
`repair_class_definition_missing`, `open_set_arm`). Existing string-keyed
taxonomies are retired via an append-only
`causal_mechanism_taxonomy_retirements` table (119's triggers forbid a status
edit); pinned receipts still resolve, `latest_active_…` skips retired. Both live
vaults held **zero** taxonomy versions and one hypothesis, so no assignments
needed remapping — the debt was caught before it accrued. Requires one
`learnloop build-causal-taxonomy --activate` run to mint under the new key.

**1.3 as shipped** (migration 134): `missing_vocabulary_notes`, content-addressed
(so regrade/replay re-materialization is idempotent), with both producers wired —
diagnostic abstention at `materialize_causal_episode`, and causal §5.8 rule 4's
facet-abstaining authored items at `proposals.accept_items` (on acceptance, not
generation: a reviewer who filled the facets in withdrew the abstention).
`causal_health.py` is no longer dead — `causal_lane_health` and the new
abstention rate both report through `learnloop causal-attribution-audit`, which
also warns on `uncaptured_diagnostic_abstentions` (the one hole capture cannot
heal). Resolves §7 decision 2's `causal_health.py` arm: **wired, not deleted**.

**1.4 as shipped** (migration 132): `surfaced_to_learner` is written only where a
belief's wording actually reaches the learner (`hypothesis_claims.present_claims`
insert + visibility-debounce paths, and the Repair-screen `_case_dto`, which
bypasses `ClaimSurface`), gated on *unsuppressed AND visible*; the wording as
shown is stored alongside, because the belief text may be rewritten before the
correction fires. New `learner_review_feed` kind `belief_withdrawn`, keyed on the
disposition event so re-reads re-derive rather than duplicate. Three findings:
(a) the plan's presumed join does not exist as an equality join — `claim_ref` is
caller-shaped and the two diagnosis surfaces disagree, so Review presentations
matched and **every Feedback presentation silently missed**; fixed by normalizing
to `belief_kind`/`belief_id` at capture. (b) `hypothesis_events` carried no
wording at all: `claim_text` existed in the handler and was dropped before the
repository. (c) The disposition vocabulary the spec names
(`retired_misdiagnosed`, `contradicted_by_trace`) **does not exist in code** —
migration 116's CHECK admits only `demoted`/`superseded`, and nothing had ever
written that store, so A6's four typed reasons live in `reason` with
`disposition` as the coarse arm. Consequence: narration is live and tested, but
**no production path yet decides to withdraw a belief** — that is item 2.2.

### Stage 2 — Causal P2 completion ✅

| # | Item | Provenance | Notes |
|---|---|---|---|
| 2.1 ✅ | Wire probe-candidate + blind-bundle producers into the orchestrator commissioning path | [Causal §7] | `create_probe_candidate` / `transition_probe_candidate` / `generate_blind_prediction_bundle` currently have zero production callers; readers, EVSI rule, receipts, and migration-130 writer are already live. One producer lights the whole lane. |
| 2.2 ✅ | Adjudication → promotion arm (d); finish arm (c) | [Causal §5.6 via Aug A4] | Path from adjudicated verdicts into `_promote_candidate`. Until then the A4 store cannot change any belief. |
| 2.3 ✅ | Wire or delete the orphaned manipulation-contract auditors | [Causal §7] | `audit_variant_manipulation_contract` (zero callers incl. tests), `validate_independent_measurement_contract` (zero callers), `resolve_machine_check` (exported, no callers). Decide per §7 below. |

**2.1 as shipped** — new `services/causal_probe_commissioning.py`, no migration.
The pipeline is: divergence check → lock hypothesis set → blind bundles per
hypothesis → discrimination → manipulation audit → `create_probe_candidate` →
`registered`. It stops at `registered` deliberately: only `active` is servable
and `registered → reviewed` requires a reviewer, so a producer that activated its
own instruments would defeat the register → review → activate ladder it exists to
feed. Eleven typed outcomes rather than a bare success/failure, because "no
instrument" has six different remedies.

**The blind generator runs no model and consumes no learner observation.** The
first audit implementation incorrectly derived its frame from
`postdictive_claims`; causal §5.1 expressly forbids observation-conditioned
claims from feeding probe discrimination. The corrected generator maps only the
hypothesis's typed `target_ref` into criterion targets authored on the fresh
probe rubric (`criterion`, or an explicitly targeted `facet_capability`).
`item_step` / `answer_span` targets and unmatched facet targets abstain rather
than guessing. Each bundle declares over the union of those observation-free
target commitments, with rival-only criteria predicted to earn full credit.
That complement is an added reviewer-visible commitment, gated by the review
ladder; when wrong it yields `no_bundle_matched` (open-set evidence, resolves
nothing) — never a promotion. Regression tests vary postdictive learner claims
while holding typed targets constant and require byte-identical bundles.
The allowlisted input is stamped `observation_free_hypothesis_target_v2`;
pre-correction candidates lack that stamp, cannot be registered/activated or
served, and are withdrawn through the candidate event log on the next
commissioning sweep. The commissioning policy is consequently v2.

**A learner-visible verb changes, correctly.** The orchestrator already had a
`unreviewed_probe_candidate` reason that no vault could ever reach, because
nothing minted candidates; commissioning makes it reachable for the first time.
A divergent factor now reports `no_discriminating_instrument` before
commissioning and `unreviewed_probe_candidate` after — both under
`blocked_pending_review`, and the second is the more actionable statement (a
human owes a review, rather than the pool owing an instrument).

**Queue producer:** `sweep_machine_checks` (already on the post-attempt path) now
also emits `MACHINE_CHECK_INSTRUMENT_COMMISSIONING` for a divergent factor with
no candidate, so the machine's instrument debt is drainable instead of re-derived
and forgotten every attempt. It is deliberately **not** in
`PROBE_BLOCKING_MACHINE_CHECK_KINDS`: `defer_machine_checks` means "the machine
can still resolve this itself", which is false of commissioning — it builds the
instrument rather than resolving the uncertainty — and folding it in would relabel
a missing instrument as a resolvable check and hide the instrument-pool
bottleneck behind a softer verb. `no_discriminating_instrument` remains the honest
learner-facing state. New CLI: `learnloop commission-causal-probes` (drains the
queue, discharges each check via `resolve_machine_check` with grounds) and
`learnloop review-causal-probe` (walks the ladder).

**2.2 as shipped** — new `services/durable_promotion.py`, no migration. Arms (c)
and (d) are **late evidence**: a learner confirmation arrives after the feedback
screen renders and a human verdict days later, so neither is decidable inside
`misconceptions`'s normalization loop — a branch there would have been permanently
dead. The module is a re-driver reaching durable state through the one existing
door (`_promote_candidate`), wired at three production sites:
`diagnosis_adjudication` (arm d), `handlers/feedback` (arm c's confirmation half),
and a sweep from `misconceptions`. Verdict mapping: only `correct` promotes (the
sole verdict affirming both anchor and repair); `wrong_anchor` /
`should_have_abstained` **withdraw** — the first real producer of 1.4's
`belief_withdrawn` entries, which closes the loop 1.4 correctly reported as open;
`wrong_repair` and both abstention verdicts are explicitly neutral, each with a
recorded reason (`wrong_repair` says "right place, wrong fix", so withdrawing
would contradict the verdict and promoting would launder it). **The §5.6
trace-consistency veto survives both arms**: adjudication outranks the system's
uncertainty, never its evidence — if the grade ledger deterministically falsifies
H, promoting H would write permanent facet damage for a belief the learner
demonstrably does not hold. Idempotency is structural rather than flag-guarded (a
promoted candidate stops being a candidate), so replay reproduces it.

**3.1 as shipped** — new `services/contract_reachability.py`, wired as a standing
`learnloop doctor` check plus a `learnloop contract-reachability` report. **It
independently reproduces Step 0's own numbers**, which is the strongest available
evidence it measures the right thing: on `fixtures/linear_algebra`,
`facets_declared: 39 / facets_instrumented: 14` against §5.8.2's stated 14/39 =
0.36, and 55 of 64 cells unreachable (85.9%) against Step 0's "86% of contract
cells unreachable". `integration_reachable_share: 0.0` reproduces "0 coordination
instruments". Verdict split: 9 `REACHABLE`, 15 `MISMATCH_BELOW`, 1
`MISMATCH_ABOVE`, 39 `NO_INSTRUMENT`, plus an `INDETERMINATE` abstention arm.
`fixtures/arxiv` reports 0 cells over 15 LOs — no authored contracts, so the
legacy path correctly has nothing to check rather than faking a score. **This is
Stage 5.1's commissioning queue**: the 15 `MISMATCH_BELOW` cells are the
authoring-at-the-wrong-rung lever, and the 39 `NO_INSTRUMENT` cells are the
authoring backlog.

**2.3 as shipped** — all four orphans resolved by wiring, none deleted:
`validate_independent_measurement_contract` and `audit_manipulation_contract` now
have production callers through 2.1; `resolve_machine_check` gets its first
caller in the commissioning drain (an explicit discharge that records *what*
satisfied the obligation, where the sweep would only have said "obligation no
longer present"); `audit_variant_manipulation_contract` is wired into
`generate_rung_variant`'s row transform, which also adds real deterministic
coverage the direction audit lacked — `undeclared_differences` and
`held_constant_violations` now surface as rung-gate violations. Per §5.8 rule 2
the audit is persisted on every variant even with no reviewer, since the
declarations are the adversarial reviewer's audit substrate in the meantime.

### Stage 3 — Measurement Wave 1 (static, zero learner cost) ✅

| # | Item | Provenance | Notes |
|---|---|---|---|
| 3.1 ✅ | Contract-cell reachability as a standing `learnloop doctor` check: `REACHABLE / MISMATCH_ABOVE / MISMATCH_BELOW / NO_INSTRUMENT` per contract cell | [Meas §5.8.2] | Pure static analysis; the check whose absence let 43 attempts land on an uncloseable contract. Output doubles as Stage 5's commissioning queue. |
| 3.2 ✅ | Three-state labels `measured / inferred / unknown` (+ E2's `claimed` state) | [Meas B2, E2] | `facet_state_label` plumbing is already wired to the UI end-to-end; the prediction to render exists unlabelled in `selection_rewards.py:438`. Vocabulary change only; writes nothing, certifies nothing. |
| 3.3 ✅ | Coverage denominator → contract frontier, with capability axis | [Meas §5.2] | Extend uncommitted `scope_facets` into `covered_required_fraction` (`facet_diagnostics.py:150`); fix the vacuous no-items⇒1.0 case; variance floor relieved by inference at a discount. Ship with a learner-visible recalibration feed entry (uses 1.4) — displayed mastery will jump. Legacy vaults without contracts keep current behaviour. |
| 3.4 ✅ | Publish `measurement_rank` | [Meas D1] | Identifiability already computes the observing-criteria signature; this is counting independent dimensions vs facets declared. Analysis only; merges stay behind review. |

**3.2 as shipped** — new `services/measurement_state.py` holds the closed
four-label vocabulary in one place; render sites read the label and never
re-derive it. Precedence `measured > inferred > claimed > unknown`: a claim is a
prior so it can never outrank evidence, and a pooled prediction never outranks
direct evidence over the mass gate. The sharp edge is that **ignorance is not
inference** — `predicted_facet_recall` returns a 0.5 default when there is
nothing to pool from, and labelling that `inferred` would be exactly the
confident wrongness the vocabulary exists to prevent, so it reports `unknown`.
Emitted from `capability_grid` and `goal_projection`, through
`handlers/goals`, rendered in `term.tsx`. Display-only by construction: no
threshold, certification, or stored belief reads the label, which is §B2's own
revert condition.

**3.4 as shipped** — `measurement_rank` in `services/identifiability.py`,
published per subject through `subject_registry`, the CLI, and
`RegistryReviewScreen`. It separates the two ways a vocabulary can outrun its
instruments, and **the split is the finding**:

- `fixtures/linear_algebra` / `vector-spaces`: 39 declared, 15 independent
  dimensions (ratio 0.385 — §5.8.2 reports 14/39 = 0.36), deficit 24, **all from
  unobserved facets**, none from collapse. This vault's problem is missing
  instruments, which is the same verdict 3.1 reached independently.
- `fixtures/arxiv` / `attn`: 101 declared, 38 independent dimensions, deficit 63
  — **all 63 from collapse**, across 21 groups of facets no authored criterion
  can separate. Roughly 62% of that subject's facet vocabulary is redundant *by
  measurement*, which is precisely the case D1 exists for. Merges stay behind
  review: publishing the rank triggers nothing.

  **This deficit is NOT over-minting, and D2 would not have prevented it** —
  established at 5.4 by re-judging all 101 facets under the D2 gate: **100 MINT,
  1 ABSTAIN, 0 ALIAS**. Two independent reasons. (1) All 101 carry **zero**
  `error_signatures` and **zero** `instructional_repairs` (provenance origin
  `facet_normalization`, not `sourceset_synthesis`), so D2's raw material is
  simply absent. (2) Within-group lexical Jaccard peaks at 0.17–0.64 — e.g.
  `add_to_embedding` / `pattern_as_weights` / `values_as_content` /
  `weighted_sum_column` are four genuinely different atoms. They collapse because
  **one criterion observes several at once**: under-instrumentation, which A1/A2/A4
  fix, not vocabulary bloat, which D1/D2 fix. The one true near-duplicate on the
  vault (`dot_product_ab` ~ `dot_product_ac`, 0.875) is exactly the ABSTAIN.
  Corollary for sequencing: **this deficit is Stage 6's problem, not Part IV's.**
- A subject with no declared facets reports `rank_ratio: None`, not 0.0.

Two corrections to this item's one-line description. First, "identifiability
already computes the observing-criteria signature" is true but **insufficient**:
criteria alone rank `linear_algebra` at 3/39, because that vault has only 5
criterion targets. §D1 asks what *the item pool* can resolve, so the signature is
the union of criterion signatures and observing practice items — which is what
reproduces §5.8.2's own measurement. The item observations are deliberately not
read by the seven existing checks (a test asserts `analyze_identifiability` is
bit-identical with and without them, and the registry hash is unchanged, so the
doctor watermark is untouched). Second, and more useful: on `arxiv`
`analyze_identifiability` reports **0 findings** while the rank reports a
63-facet collapse deficit — check 1 sees only criterion signatures and that vault
has no per-item rubric targets. **The rank surfaces a real D1 signal the seven
checks are structurally blind to**, which is an argument for treating it as a
first-class report rather than a derived statistic.

**3.3 as shipped** (migration 138): `contract_frontier(vault, lo, repository)`
returns the `(facet, capability)` cells the LO's blueprint recipes require, plus
an `authored` flag; `covered_required_fraction` switches denominators on that
flag, so legacy vaults with no authored blueprint components keep their previous
behaviour byte-for-byte (§5.2 is strictly additive) and their "nothing required ⇒
1.0" arm survives. The vacuous case is fixed in the direction the floor exists to
express: an LO that *declares* obligations but has no instruments now reports 0.0
instead of 1.0. The capability axis reads the per-cell ledger
(`facet_capability_evidence`), so evidence at `retrieval` no longer closes a
`transfer` cell — the 72% mismatch Step 0 measured; a vault predating that ledger
falls back to facet-level mass and *says so* in `denominator_basis`
(`contract_frontier_facet_mass`) rather than claiming per-cell precision it does
not have. `inferred_cells` + `INFERRED_CELL_COVERAGE_DISCOUNT` are the §5.2
inference-relief seam, inert until Stage 8 supplies inferred cells — deliberately,
so the discount is decided once in the open rather than by whichever inference
rule ships first.

Two judgment calls worth flagging: (a) the frontier is the **union** over recipes,
not the best-covered single recipe — that overstates debt where recipes are true
alternatives, which is the conservative direction for a variance floor, and it
keeps one definition of "required cell" in the vault (`required_capabilities_for_facet`
already reads the same components); per-recipe routing belongs with §5.3's
substitution rule, which owns "for SOME blueprint". (b) Displayed mastery moves
with no new evidence, so it is narrated through 1.4's machinery — but the existing
recalibration boundary keys on `algorithm_version` / `canonical_projection_version`,
and attributing this to either would name a cause that was not the cause. Migration
138 adds `coverage_denominator_version` as a third independent boundary (following
122's precedent for the second), so the switch surfaces as exactly one honest
"estimates recomputed, your evidence unchanged" entry that can say which version
moved.

### Stage 4 — Scoreboard producers + delayed cold probe (pulled forward) ✅

| # | Item | Provenance | Notes |
|---|---|---|---|
| 4.1 ✅ | `harmful_write_rate`, `problems_to_cold_success` producers | [Aug B5] | The two metrics the augmentation spec ranks first; currently no producer. |
| 4.2 ✅ | Delayed cold probe per certified LO (+2–3 weeks, held-out surface) + `false_certification_rate` | [Meas §5.7] | The only external validity check in a single-learner vault; also the ground-truth consumer nothing currently computes. Existing cold-probe machinery is repair-scoped — generalize the scheduler. The earlier this runs, the sooner cold-outcome labels accrue (causal P4's unpark trigger). |
| 4.3 ✅ | `questions_to_certification`, `certification_regret`, `cells_cleared_per_question` | [Meas §5.7] | Counters over existing attempt/exam logs. |
| 4.4 ✅ | `tokens_per_resolved_diagnostic_episode`, `probe_action_change_rate`, `planted_vs_adjudicated_agreement` scaffold | [Aug B5] | Tokens unblocked by 1.2. Agreement metric lands as a producer even while the planted side (Stage 7) is empty. |

**4.2 as shipped** (migration 139) — new
`services/certification_cold_probe.py` plus `learnloop cold-probe-schedule` /
`cold-probe-audit`. **Generalized, not parallel**: `followup_tasks` gained a second
`kind` (`certification_cold_probe` / `case_kind='certification'`), reusing the
existing `not_before` invisibility window, serve/consume/expire, migration 124's
carry-the-inputs `context_json`, and the unassisted-attempt guard in
`attempts._validate` — which now keys on a `COLD_FOLLOWUP_TASK_KINDS` lane class
rather than one literal. The readers gained a `kind=` filter and the repair lane
now asks for `cold_retry` **by name**; without that a queued certification probe on
the same item would have shadowed the repair retry. "Held out" reuses the existing
vocabulary only: `surface_group_id(item)` not in the union of
`independent_surface_groups` over the certified cells, with `held_out_basis` taken
verbatim from `causal_activity_policy.NEAR_CLONE_BASES`. Horizon lives in the fitted
store (house rule) under scope `certification_cold_probe`: due at +14d, expires at
+21d, which is how §5.7's "+2–3 weeks" stays a range rather than a magic number.

Three findings that changed the design, none anticipated by the item:

1. **There is no durable certificate record anywhere** — §5.3's receipts are plan
   8.4 and unbuilt. So "which certificate" is *derived* and content-hashed over
   (LO, blueprint, recipe, cells): requirements, not evidence, so extra practice
   never mints a new certificate while a re-authored recipe does.
2. **Certification has no timestamp anywhere.** `facet_capability_evidence.updated_at`
   is projection time, which a rebuild moves. `certified_at` is derived as the max
   `last_observed_at` over the certifying cells — projected from immutable attempt
   timestamps — and when absent the horizon runs from discovery, which only ever
   *delays* a probe.
3. **`certification_credit` is monotone non-decreasing**, so failing new work can
   never withdraw a certificate. The metric's numerator is therefore not
   self-suppressing (good), but the `certificate_withdrawn` abstention arm is
   reachable only through authoring/ledger changes.

The consume hook sits in `apply_attempt` **before** `_project_canonical_belief`,
deliberately, so a failing probe is scored against the certificate it falsified
rather than one its own evidence just withdrew. `lo_certification`'s per-recipe
predicate was extracted to `recipe_gaps()` and the authority now calls it, so the
probe naming the satisfying recipe cannot drift from the code deciding
certification. **Live-vault state:** the one certified LO in
`fixtures/linear_algebra` has no held-out surface, so the metric reports
`certificates_unmeasurable: 1` rather than a rate — the honest answer.

**4.1/4.3/4.4 as shipped** — new `services/scoreboard.py` assembling all 14 B5
metrics plus `learnloop scoreboard`, composing (never reimplementing) the four
adjudication-owned metrics, `measurement_rank`, and 4.2's
`false_certification_rate`; tests monkeypatch each upstream and require the board
to move, so a silent reimplementation fails them.

**The availability discipline is structural, not conventional.** `Metric` refuses
at construction to carry a value on an unavailable arm, and `_rate` is the single
choke point — there is no code path from an empty denominator to a number. Four
distinct unavailable arms, because each implies a different remedy: `no_data`
(producer ran, denominator empty), `no_producer` (nothing produces it yet),
`unmeasured` (the events exist but the measurement was never captured and cannot
be backfilled), `requires_replay`.

That discipline immediately earned its keep — **two metrics would otherwise have
rendered as successes**:

- `learner_minutes_to_cold_success` was `unmeasured`: **all 43 attempts in
  `fixtures/linear_algebra` had NULL `latency_seconds`**. B5 requires this as
  `problems_to_cold_success`'s companion. A trajectory with any NULL latency is
  excluded outright rather than summed over the recorded subset. **Fixed — see
  the scope addition below.**
- `tokens_per_resolved_diagnostic_episode` is `unmeasured`: 2 of 3 episodes are
  unmetered (a run reporting 0/0 is indistinguishable from a pre-migration-131
  run). Without the guard it would have reported **0.0 tokens for a loop that
  demonstrably calls a grader**.

**`harmful_write_rate` — definition chosen: surfaced-then-withdrawn.** Numerator:
distinct beliefs with `surfaced_to_learner = 1` later withdrawn as *false*
(`contradicted_by_trace` / `adjudicated` / `retired_misdiagnosed`); denominator:
distinct beliefs surfaced. B5's own wording decides it — "being told something
false about your own mind" — so the harm is in the telling, which is the same
argument migration 132's scope guard makes. `superseded` is excluded (A6 defines
it as a better-supported replacement, not a lie) and reported separately. The
adjudication-verdict arm rides alongside in `detail["arms"]` with an
`arms_agree` flag; `wrong_repair` is excluded from it because the adjudication
scoreboard already counts that verdict as anchor-*correct*.

**Architectural finding at 4.3: there is no persisted "certified at" record.**
`lo_certification` is a pure predicate, so `questions_to_certification` and
`certification_regret` require a prefix replay over the attempt sequence.
Certification credit is monotone in the prefix, so the implementation **bisects**
(exact, not a coarse grid), memoized across LOs and budgeted: ~5s per cutoff, 7
cutoffs, 35.8s on `fixtures/linear_algebra`. Opt-in behind `--replay`; otherwise
the metric reports `requires_replay` rather than a number.
`cells_cleared_per_question` uses `contract_reachability.contract_cells` rather
than `facet_diagnostics.contract_frontier`, because the frontier drops the LO from
the cell identity (so cells collide across LOs) and carries a legacy item-mode arm
that §5.2 itself calls an authoring artifact.

**Scope addition (not a listed item): attempt latency was never captured.** The
entire backend path existed and worked — `SubmitAttemptInput.latencySeconds`, the
sidecar `PracticeInput`/`DontKnowInput` fields, `AttemptDraft.latency_seconds`
with its non-negative validation, and the `latency_seconds` column — but **no
Tauri client ever populated it**, so every attempt in both live vaults recorded
NULL. `PracticeScreen` already kept an `openedAtMs` ref for the ask overlay, so
the fix is to send elapsed seconds from it on submit and on don't-know, and to
time `DialogueProbe` **per turn** rather than per block (each turn is its own
committed attempt; a block-scoped timer would bill every turn for the ones before
it). Wall-clock, deliberately not idle-adjusted: subtracting time the learner
"wasn't really working" would be a fabrication, and the metric is denominated in
their actual elapsed experience.

This is outside the plan's items, but it is un-backfillable capture-now data —
ordering principle 1's exact category, and the same shape as A5/A6 — and without
it 4.1 ships a metric that reports `unmeasured` forever. Guarded by `tsc --noEmit`
on the client side; the backend path is already covered by the scoreboard's own
tests (30+60+90s ⇒ 3.0 minutes). Note that **the scoreboard is itself the
regression detector**: if a client stops sending latency, the metric flips back to
`unmeasured` loudly rather than silently reporting a number.

**Board on `fixtures/linear_algebra`:** 5 of 15 available (`no_data` 7,
`no_producer` 1, `unmeasured` 2). `problems_to_cold_success` 1.25 [10/8];
`questions_to_certification` 5 and `certification_regret` **1** — one certified
LO, certified at its 5th of 6 questions, so regret is real and now measurable;
`cells_cleared_per_question` 0.093 [4 of 64 cells over 43 questions];
`measurement_rank` 0.385.

**Why here:** Stage 6's instrument hypotheses/reverts are stated in these
metrics. B5 freezes before Phase C (Stage 7), after these are added.

### Stage 5 — Measurement Wave 2 (authoring correctness + gates) ⚠️

| # | Item | Provenance | Notes |
|---|---|---|---|
| 5.1 ✅ | **Rung-correct generation:** practice generation authors at the capability the contract names, consuming 3.1's reachability report as a prioritized commissioning queue for `MISMATCH_BELOW` / `NO_INSTRUMENT` cells | [Meas §5.8.2 verdict; promoted to a named item] | The measured 72% lever — the single highest-ROI change in the measurement spec, and it needs no new instrument class. Hypothesis: contract-cell hit rate of new attempts rises from 28%. Revert: never (this is honoring existing contracts). |
| 5.2 ✅ | Backfill the 18 persisted coordination integrations under D3's criterion | [Meas §5.8.3/Wave 2] | Blueprints are vault content; no rebuild touches them. Expect most dropped, some lowered, a few genuinely `coordination` (owed an A1 capstone later). Pilot on one LO first, measure reachable-cell delta, then batch. **Applied to `fixtures/linear_algebra` with narration — see below.** |
| 5.3 ✅ | §3.0 planted-persona gate wired into the **live** generation path — tiered | [Meas §3.0] | Stage 7's B2 matcher now licenses the authored-signature corpus: pre-license passes remain provisional, indistinguishable corpora harden the plain-practice tier, and separable corpora invalidate otherwise passing results. |
| 5.4 ⚠️ | D2 ingest mint gate: separability + distinct repair, typed rejection reasons, alias-not-mint | [Meas D2] | Structural proxy shipped. It normalizes the same persona material but does not yet run an authored item through the shared §3.0 grading harness, so literal D2 compliance remains open. |

**5.1 as shipped** — new `services/contract_commissioning.py`, consumed by
`build_practice_expansion_plan`; `depth_rungs` gains `waypoint_slug_for_capability`
/ `capability_rung`.

*The mechanism 72% came from, located:* `select_rung` keys the generation waypoint
to the learner's mastery band (or a probe hypothesis, or a commitment milestone)
and therefore **independently of the blueprint**, while `_RungGate` then hard-failed
any generated item whose capability differed from that waypoint. The blueprint's
declared capability reached the authoring model only as prose
(`blueprint_components`), and the one deterministic gate in the path actively
*rejected* items authored at it. Measured on `fixtures/linear_algebra`: on 3 of the
4 LOs at the head of the commissioning queue the band rung is `recall` /
`retrieval` while the contract asks `schema_interpretation` /
`procedure_execution` / `method_selection` — the `MISMATCH_BELOW` shortfall
manufactured at generation time.

*What drives target selection now:* for an LO that declares contract cells the
contract **is** the waypoint. `commission_plan` walks
`ContractReachabilityReport.commissioning_queue()` in the order `_queue_sort_key`
already encodes — no second priority is invented — resolves each
`MISMATCH_BELOW` / `NO_INSTRUMENT` cell to the trajectory waypoint at *its*
capability, and hands the cells to the prompt in that order. Target ordering (and
so `max_los` truncation) follows each LO's best queue rank, which is the
"prioritized" half of the item. `_RungGate`'s admission set becomes the set of
capabilities the LO's contract names: an item at one of them is validated against
that capability's waypoint (it used to hard-fail), and an item outside them
hard-fails (it used to pass). No knob, no threshold: an LO with **no** contract
cells keeps `select_rung`'s behaviour byte-for-byte, which is why `fixtures/arxiv`
(0 cells over 15 LOs) is untouched.

*Integration cells, per §5.8.3/D3 criterion 2:* a `coordination` cell is
**deferred** with the typed reason `coordination_requires_reviewed_depth_envelope`,
never re-aimed one rung lower (that would be a blueprint edit disguised as
generation — 5.2's job) and never authored off-trajectory. All 18 coordination cells
on the fixture are integration cells; the one integration cell at
`method_selection` is commissioned like any other, since its role does not change
what a rung means. Deferrals ride on the plan, not the prompt.

*Measured before-number for the hypothesis:* `services/contract_commissioning.contract_cell_hit_rate`
+ `learnloop contract-hit-rate` (with `--since` for "new attempts").
`fixtures/linear_algebra`: **12/43 = 28% contract-cell hit rate**, reproducing Step
0's 28% exactly, with the miss decomposed as 28/43 = 65% rung loss (contract facet,
wrong capability) + 3/43 = 7% off-contract — total miss 72%, also §5.8.2's number.
One honest divergence: §5.8.2 reports a 100% *facet* hit rate, this reports 93%; the
3 attempts responsible observe a facet its LO declares only in a `facilitating`
component, which 3.1's `CONTRACT_MODALITIES` correctly excludes from the contract.

**5.2 as shipped, and where it stopped** — new `services/integration_backfill.py`
+ `learnloop integration-backfill` (diff-only unless `--apply`).

D3's two criteria, applied retroactively with structural proxies: criterion 1 fails
as `no_assembly_to_fail` (fewer than two *binding* `all_of` components — nothing to
assemble) or `facet_duplicates_component` (the integration names a facet the recipe
already lists, so its failure is not *separately repairable* — the same part one
rung harder, exactly the shape §5.8.3 diagnosed). Criterion 2 is **measured**, not
assumed: `coordination` counts as observable once some active instrument observes
anything at it, so once 6.1's A1 capstones exist the same code stops lowering with
no flag flipped.

Verdicts on the 18 coordination integrations of `fixtures/linear_algebra`:
**17 DROP** (13 `facet_duplicates_component`, 4 `no_assembly_to_fail`), **1 LOWER**
(`lo_compute_and_interpret_coordinate_vector_operatio`, three distinct binding
components plus a genuinely distinct integration facet → `method_selection`), **0
KEEP**. The plan expected "a few genuinely `coordination`"; on this vault that set
is **empty** — 18 of 19 integration components name a facet the recipe already
declares. Independent corroboration: applying the batch on a temp copy clears 17
`identifiability:component_vs_integration` and 17 `identifiability:missing_anchor`
doctor warnings and adds none.

Measured on temp copies: the **pilot** (the single LOWER) moves no verdict at all —
64 cells, 9 reachable, before and after — it moves the cell from
`(facet, coordination)` to `(facet, method_selection)`, i.e. from *deferred* to
*commissionable* (queue: 36 → 37 commissioned, 19 → 18 deferred). The **batch**
takes 64 → 47 cells with reachable still 9, so 14% → 19%, and integration cells
19 → 2. That is §5.8.3's own prediction reproduced: "it removes a third of the
contract cells outright — but it does not move the reachable-cell count at all".

**Raised as a decision, then applied with narration (owner-approved).** Two
objections had to clear first, and both did: (b) D3's stated revert trigger is
"certified LOs failing the §5.7 delayed cold probe", which is item **4.2** — that
landed, so the detector for "we dropped a real assembly obligation" now exists;
and (a) removing 17 contract cells shrinks 3.3's `covered_required_fraction`
denominator, so displayed mastery moves with **no new evidence** — which a
vault-content edit would bypass, since nothing on the YAML write path records a
rebuild. Rather than accept (a), the write path now narrates it.

**The narration mechanism, and why the version is content-addressed.**
`coverage_denominator_version(vault, repository)` (in `facet_diagnostics.py`) is
now `coverage_contract_frontier_v1` **plus a hash of the effective sorted
`(LO, facet, capability)` frontier** — deliberately not a hash of the authored
YAML, which would be wrong in both directions: an `updated_at` or comment touch
would mint a phantom boundary and narrate a recalibration that did not happen,
while a facet alias/merge that changes which canonical cells resolve would move
the denominator with no file changing. Hashing the resolved cell set makes the
version a function of the thing being versioned, which buys two properties for
free: a rerun of the backfill and any later ordinary rebuild recompute the same
value and emit **nothing**, and a real cell change emits **exactly once**. Both
the backfill and the ordinary rebuild path call the same helper, so they cannot
drift.

`apply_integration_backfill_and_recalibrate` orders the work the only way that
works: **every YAML edit, then reload the vault, then rebuild the affected LOs,
then one batch marker.** Reloading between edit and rebuild is what lets the
rebuild see the new blueprints (the frontier is read from vault content, not the
database); one marker for the batch rather than one per LO is what keeps the
learner from seeing an 18-entry flood they appear to have caused. A dry run writes
no files and **no boundary**.

One reader fix this exposed: `derived_state_rebuild_version_changes` compared a
NULL coverage version as a real value, so an unstamped rebuild between two stamped
ones would have minted two phantom boundaries. A NULL now means "this writer did
not report a version", carries the last reported one forward, and can never itself
be a boundary.

**Applied to `fixtures/linear_algebra`:** 18 files written, 18 LOs rebuilt, cells
**64 → 47**, reachable still 9 so the share moves **14.1% → 19.1%**, integration
cells **19 → 2**, and **exactly one** recalibration entry
(`coverage_contract_frontier_v1:0d9f26c30373a770`). Verified live afterwards: a
second `--apply` writes 0 files and a subsequent `learnloop rebuild-derived-state`
(8 LOs, 43 attempts replayed) leaves the count at exactly one entry.

**5.3 as shipped** — new `services/persona_gate.py`, chained as a `row_transform`
into all four generation routes in `practice_generation` (diagnostic, post-probe,
goal-population, cross-source) plus a narrow read method
`Repository.persona_gate_audit_rows`.

*Why the live path bypassed the gate, located:* the gated entry point,
`proposals.generate_diagnostic_proposal(need_id=)`, has **no production callers** —
only `tests/test_diagnostic_generation`. `learnloop generate-diagnostics` calls
`practice_generation.generate_diagnostic_practice_proposal`, which reaches
`proposals.generate_authoring_proposal` directly and never constructs the
`MisconceptionRecord` the old signature demands. The gate was never disabled; it was
attached to the branch of the generation tree production does not use.

*Tiering is structural, not a flag:* `classify_instrument(payload)` reads the
instrument class off the row's own payload (error-hunt / contrast-pair /
discrimination-profile by `practice_mode` or tag; misconception-diagnostic by a
`misconception_consistent_answer` or a `misconception_id`-keyed fatal error; plain
practice otherwise), and `tier_for` maps the diagnostic classes to HARD and plain
practice to ADVISORY. Because the gate is chained into *every* route, a row that is
structurally a diagnostic instrument is hard-gated even when the plain-practice route
authored it. There is no `strict=` parameter to forget. A `practice_mode` of
`diagnostic_probe` alone does **not** promote a row: it names no belief, so it makes
no discrimination claim to check, and blocking it would throttle exactly the
authoring throughput §7.3 protects.

*Four typed outcomes, recorded not logged:* `PASS` / `FLAG_FOR_REVIEW` / `BLOCK` /
`UNTESTED`, each with a closed `PersonaGateReason`, written to
`proposed_patch_items.audit_json` under `persona_gate` (with
`persona_realism_validated: false` stamped on every row, per §3.0's B2 precondition).
`BLOCK` also sets `validation_status="invalid"`, which `patches` refuses to accept,
and reopens the intervention need with `diagnostic_proposal_rejected:` rather than
letting an undiscriminating instrument consume it. `FLAG_FOR_REVIEW` sets `"warning"`
+ loses auto-apply — it ships to review. `UNTESTED` is the abstention arm (no persona
material exists for the item's targets) and changes no route; on the legacy vault
with no facet registry that is the common outcome, which is deliberate — flagging
every item would make the flag meaningless.

*Gate precision:* `persona_gate.gate_precision(repository, *, blinded_labels=None,
since=None) -> scoreboard.Metric` (`learnloop persona-gate-precision`). Precision =
of the items the gate **blocked or flagged**, how many were genuinely bad; `PASS` and
`UNTESTED` are excluded because the gate made no prediction about them. The
denominator is countable today; the numerator needs a **blinded** label, which only
Aug B2's realism matcher or Stage 7 B1's planted side can supply. So it reports
`no_data` over an empty denominator and `no_producer` once predictions exist without
labels — never 0.0 and never 1.0. Reviewer decisions ARE captured from day one but
are reported only as descriptive counts in `detail.reviewer_decisions`: the gate
writes its reason into `validation_errors`, which is what the reviewer reads, so a
reviewer-decision numerator would be caused by the prediction it is meant to score.

**5.4 as shipped** — new `services/facet_mint_gate.py` (pure functions over payload
dicts), wired into `source_set_synthesis._normalize` as a two-pass facet loop, plus
`learnloop facet-mint-gate` (read-only, re-judges the registry).

*Typed rejection reasons:* `no_authorable_discriminating_item` (each side must own an
error signature the other does not — symmetric, so a subset facet is a collapse),
`same_repair_class` (no `instructional_repairs` entry the neighbour lacks),
`insufficient_payload_to_test` (the abstention arm), against the admitting reasons
`separable_and_distinct_repair` and `no_neighbour`. Neighbours are nominated by shared
error signature, identical claim, or the §8.7 lexical hint at the same threshold — the
hint can put a pair in front of the harness but never decides one (D1: "never promoted
to a merge criterion").

*Alias-not-mint:* an `ALIAS` verdict emits **no facet row**. Instead
`facet_client_to_id` redirects every downstream reference (recipe components, criterion
targets, item evidence facets) to the neighbour, and the candidate id is appended to the
neighbour's `aliases` — in place when the neighbour is minted in the same batch, via a
`facet` `update` row when it is already registered — so `loader._facet_aliases` keeps
resolving the id and evidence filed against it lands on the surviving facet. Candidates
are judged in order and may only alias into a registered facet or an earlier *minted*
candidate, which makes alias chains impossible without a compression pass. Dependencies
are rewired through a new `facet_dep_client` map; leaving them on the aliased candidate
would be a dangling requirement.

*One documented departure from a literal reading:* D2 says "otherwise it is registered
as an alias", but that sentence describes a candidate that was **tested and collapsed**.
Aliasing on ignorance would delete the very missing-vocabulary record D2 asks for, so
`insufficient_payload_to_test` mints at `status: "proposed"` instead of the `"reviewed"`
D2 names as today's defect. Nothing minted through that arm is born reviewed.

*What D2 would have done to `fixtures/arxiv`'s 101 facets* (measured read-only on a
temp copy; 3.4's numbers reproduce exactly: 101 declared, 38 dimensions, deficit 63 from
collapse across 21 groups): **100 MINT (`no_neighbour`), 1 ABSTAIN, 0 ALIAS.** The gate
would not have prevented that backlog, and the reason matters. Those 101 facets carry
**zero** `error_signatures` and **zero** `instructional_repairs` — their provenance
origin is `facet_normalization`, not `sourceset_synthesis`, so the raw material D2
assumes "is already in the payload" is simply absent. And the collapse is not synonymy:
maximum within-group lexical Jaccard across the 21 groups is 0.17–0.64 (e.g.
`add_to_embedding` / `pattern_as_weights` / `values_as_content` / `weighted_sum_column`
are four genuinely different atoms), so they collapse because **one criterion observes
several of them at once** — under-instrumentation, which A1/A2/A4 fix, not
over-minting. The single genuine near-duplicate pair on the vault
(`dot_product_ab` ~ `dot_product_ac`, Jaccard 0.875) is exactly the one ABSTAIN, and it
says "I cannot test this, here is the record" rather than guessing. On the vaults whose
facets *did* come from `sourceset_synthesis` (`linear_algebra` 39, `probability` 39,
`arxiv_v2` 59 — all 100% populated on both fields) the gate admits every facet, so it
costs nothing retroactively; what it stops is future growth, which the two identical
cross-shard facets in `test_source_set_synthesis` now demonstrate at its smallest scale
(4 rows for 2 atoms became 2 + 2 aliases).

### Stage 6 — Measurement Wave 3 (instruments)

Ship order within the stage: 6.1 → 6.2 → 6.3, then 6.4 as fixtures permit.

| # | Item | Provenance | Notes |
|---|---|---|---|
| 6.1 | A1 conjunctive items: `targets: list[CriterionTargetPayload]` on `RubricCriterionPayload` (fixes the silent pydantic drop); spread rule made **posterior-aware** — author both conjunctive capstones and decomposed fallbacks, let selection pick (conjunctive when P(pass) high / certification hunting; decomposed when localizing a weak learner); guards: `unexercised_supporting_target`, embedded-share cap | [Meas A1, amended per review] | Largest lever on cells-per-question. Blanket spread-rule inversion is deliberately NOT adopted: a pool with only conjunctive items starves diagnosis. |
| 6.2 | A6 opportunistic trace evidence (positive-only, supporting-at-most, never certification-eligible) | [Meas A6] | Required to discharge A1's guard 1. Note `grading.py:600-603` currently *forbids* beyond-declared facets — this is a deliberate policy change at that validator. Elicitation rules: decision-point one-liners, rewarded never required, per-session budget. |
| 6.3 | A8 clarification channel: `provisional_pending_clarification` grade state, one question per attempt on hedged/abstained criteria only, timeout→abstention, replay-stable resolution | [Meas A8; authorized by the causal principle-8 amendment already in tree] | Reinforces the abstention discipline; ship early in the wave. Revert if clarification rate exceeds a small fraction of attempts (machine-resident uncertainty misclassified). |
| 6.4 | A2 laddered stems (kinship: correlated within column, independent across), A3 error-hunts (registry-planted, repair-required, clean-solution rotation — seed from the learner's own misconception registry as repair verification), A4 contrast pairs (`contrast_of` / `differing_component`; post-repair verification preferentially serves the isolating member), A5 discrimination profiles (`no_profile_applies` first-class), A7 adjacent-facet questions **(demoted: only if A8+A6 outcomes justify it)** | [Meas A2–A5, A7] | All behind the §3.0 gate. A5's profiles are Stage 7's planted-ground-truth producer. E4 (success+silence decay) is dropped from the plan (marginal yield, confident-wrongness risk). |

**6.1 as shipped** (migration 141) — `CriterionTargetPayload` + `targets` and
`depends_on` on `RubricCriterionPayload` closes F2's asymmetry; new
`services/conjunctive_items.py` owns the shape vocabulary and both guards;
`_CONJUNCTIVE_ITEM_RULE` is chained into both practice-generation routes;
`services/proposals._criterion_target_errors` types the authoring rejections.

*The pydantic drop was silent in both directions.* `codex/schemas.py` declares no
`model_config` anywhere, so every payload model runs pydantic's default
`extra="ignore"` — a model emitting `targets` had it dropped with no error from
either side — while `_strict_json_schema` forces `additionalProperties: false` on
the schema sent to the provider, so on the strict path the model was actively
*forbidden* to emit it. Both directions failed closed toward "no targets", which
is why F2 reads as accidental rather than as a decision.

*Guard 1 (`unexercised_supporting_target`) is symmetric and it bites today.* A
supporting target claims the step *consumed* the facet; crediting that without
the trace showing it is positive smearing, which the passed-facet firewall does
not cover and which nobody contests. So an unexercised supporting target confers
**nothing** — not credit and not blame; writing only the negative half would make
a supporting target an instrument that can only ever hurt. Matching is on the
facet, never the `(facet, capability)` cell: A6 reports that the trace shows a
facet being used, and which rung that counts at is the criterion's authored
target — a deterministic quantity — so letting the grader's report pick the cell
would invert standing constraint 8. **The guard is not inert on existing data**:
neither live vault has an authored supporting target yet, but the legacy compile
path already mints `role='supporting'` from `measurement_status='supporting'`, and
on `fixtures/linear_algebra` one cell
(`facet_a_vector_space…@method_selection`) now records 0.452 unexercised mass
where it previously banked embedded credit. Verified afterwards: the vault's one
certified LO (`lo_orient_to_the_vector_space_idea`) still certifies.

*Guard 1 drops the claim from the contract rather than filtering at each write
site, and that distinction is load-bearing.* An adversarial review caught the
naive version: `allocate_success_mass` normalizes across the targets it is given,
so leaving a discarded supporting target in the list diluted the primary's mass
to 1/1.3, and `observed_unresolved_failure` counts candidate causes, so it opened
an unresolved-cause factor and suppressed the primary's negative evidence
entirely. Net effect of the naive version: **authoring an honest supporting
target strictly removed measurement** and spawned a spurious diagnostic episode —
the exact opposite of what A1 is for. The shipped version splits the list once,
before allocation, attribution weighting and the ambiguity gate; the record of
what the discarded claims *would* have earned is computed separately against the
contract as authored. With an A6 observation present the supporting target
becomes a genuine second candidate cause and the ambiguity gate correctly fires.

*The receipt fold had to learn the same rules.* `facet_evidence_timeline` runs a
second, independent fold over the same ledger, and
`test_receipt_exactness` asserts the two agree to the float. The first
implementation taught only the projection, so the learner-facing "Demonstrated"
curve **overstated the banked ledger** and that dedicated invariant broke. Both
guards now live in both folds through one shared predicate
(`conjunctive_items.supporting_unexercised`) and one shared cap
(`cap_embedded_credit`), and the per-cell cap is applied inside
`fold_demonstrated_timeline` because it is a statement about a cell's whole
history. Relatedly, the direct/embedded split of banked credit is recovered from
`itemize_observation_contributions`'s per-group `group_scale` rather than an
attempt-wide ratio: the caps bind per correlation group, so a cell staged in two
groups with different embedded shares would otherwise get a slightly wrong split.

*Guard 2 is applied per cell over the whole history, not per attempt.* An
attempt-local cap can pass on every attempt while the cell still ends up entirely
embedded. `direct_certification_credit` / `embedded_certification_credit` are
banked separately (the group caps scale proportionally, so the split of what
survives is the split of what was staged) and `certification_credit` — still the
one number `capability_grid` reads — is computed from them at row-build time.
With `max_embedded_credit_share = 0.5`, a cell with zero direct credit reads
**0**: not zero evidence (the mass is in the ledger and Part II may label it
`inferred`) but zero *certification* credit, which is precisely §5.3's line.

*The spread rule was NOT inverted, per the plan's amendment.* Authoring emits both
shapes and `selection_rewards` picks: `conjunctive_fit` is `(2p−1)` scaled by a
saturating conjunctive strength, so a capstone is preferred exactly when the
learner is predicted to pass (a pass is what clears several cells at once) and the
decomposed item exactly when they are not. Under the REPAIR intent it is a flat
penalty — repair exists to localize, and a capstone answers that question worst. A
single-cell item scores exactly 0, so a pool with no conjunctive items is
untouched. PROBE deliberately abstains: its ranking is already EIG over a
hypothesis set and a second shape term would double-count the same argument.

*One consumer had to be taught that an item is no longer one capability.*
`exam_pool._item_components` derived a single capability per item from
`item.capability`; under A1 a capstone observes different facets at different
rungs, and reading only the item-level field would have hidden every cell but one
from the greedy selector — i.e. priced A1's whole gain at zero. It now reads
authored **primary** targets through `compile_criterion_targets`; supporting
targets are excluded because the question that function answers is "which cells
can this item *close*", and §5.3 says embedded credit never certifies a component
on its own. An item authoring no targets behaves byte-for-byte as before.
`CANONICAL_PROJECTION_VERSION` → `canonical_projection_v5_supporting_requires_trace`,
which routes the change through 1.4's recalibration entry rather than letting the
numbers move under the learner.

**6.2 as shipped** (migration 141) — `ExercisedFacetObservation` on
`GradingProposal`, `grading._validated_exercised_facets`, the append-only
`trace_exercised_facets` log, and `services/trace_evidence.py` for the elicitation
boundary and the reports. New CLI `learnloop trace-evidence`.

*The three A6 bounds are enforced by what the schema omits, not by fields.* There
is no polarity column (positive only — indicting a facet the item never intended
to measure is the smearing principle 5 forbids, and there is no criterion to
appeal to); `role` is a one-value CHECK rather than the usual two-value vocabulary,
so the channel cannot become primary through a later edit that forgets why; and
there is **no capability** anywhere in the store, because standing constraint 8
says the rung an observation counts at is a deterministic property of the
criterion's target, never a model-reported one.

*The validator is deliberately stricter and looser than the attribution channel.*
Looser: an A6 observation is by definition allowed to name a facet the item never
declared — that is the whole channel, and the existing `known_facets` gate
(`grading.py`) would have dropped every one of them. Stricter: the facet must be
in the vault's canonical registry, or the observation files evidence into a cell no
contract, report or grid ever reads. A registry miss is dropped rather than raised
— a bonus channel must never take a graded attempt down. `observation_scope` is
*derived* (`declared` vs `opportunistic`), because A6's revert criterion is a
statement about the opportunistic population only.

*One correction to this item's own note.* The item says `grading.py:600-603`
"currently *forbids* beyond-declared facets — this is a deliberate policy change
at that validator." Two things are off. First, that code does not forbid: it
collects unknown targets into `unknown_target_families` and surfaces them as a
soft `manual_review_reason`, dropping the target silently. Second, and more
importantly, **that validator must not be relaxed.** It gates *attribution*
targets — the negative and repair channel — and A6 is positive-only by
construction: "may credit a facet; it may never indict one." Opening the
attribution gate to undeclared facets would authorize exactly the indictment A6
forbids and principle 5 exists to prevent. The policy change belongs in a
separate channel with its own closed-world rule, which is what shipped.

*The desktop surface, and the shape of "never required".* `get_practice_item`
carries the elicitation decision; `PracticeScreen` renders one optional line
under the answer, held in state that is never checkpointed and appended at submit
behind a shared delimiter — so a blank line produces a body **byte-identical** to
an un-elicited answer and there is no representation of "declined" anywhere in
the system. The session budget counts lines actually written, read back through
`Repository.session_learner_answers` scoped to the session id rather than a
started/ended window. `FeedbackScreen` renders the reward strip; the
`observation_scope` split is what keeps it honest, since telling a learner their
explanation demonstrated the facet the item was already grading them on is noise,
not a reward. `insert_trace_exercised_facets` now **requires** the scope rather
than defaulting to `opportunistic`: that arm is the reward-eligible,
revert-criterion-counted one, and a caller that forgot the field has a bug, not a
default.

*Elicitation is bounded by the discriminator that already existed.* An item with an
`available` trace contract is self-documenting — the steps *are* the explanation
— so it never elicits; only `method_selection` / `schema_interpretation` items
whose answer underdetermines the reasoning do, at most
`[trace_evidence].max_elicitations_per_session` times, one line at a decision
point, rewarded (`elicitation_reward`) and never required. Every non-ask is typed,
because "we did not ask" has four different meanings.

**6.3 as shipped** (migration 142) — `ClarificationRequest` on `GradingProposal`,
`grading._validated_clarification`, `services/clarification.py`, and
`learnloop clarification {list,expire,rate}`.

*Status is derived, not stored, and that is what makes replay reproduce the
resolved grade.* Two append-only tables — the request, and the learner's answer —
with `answered` / `timed_out` / `pending` computed from the pair plus the clock.
The resolved grade itself lives in `grading_evidence` as a new revision superseding
the provisional one, so replay (which makes no provider call) reproduces it without
re-asking, per causal §1 principle 9.

*`provisional_pending_clarification` joins the existing grade-state vocabulary
rather than starting a second one.* There is no `grade_state` column in this
codebase; every "this grade is not final" state is a string in
`manual_review_reason` (`codex_manual_review`, `low_grader_confidence`,
`attribution_scope:*`). Putting A8's state anywhere else would hide it from every
surface that already reads that field. It never overrides an existing reason: a
grade that already needs a human is not made less so by also asking the learner.

*The timeout arm writes nothing at all, and that is the design.* "An unanswered
clarification times out to the abstention that triggered it, never to a guess" is
achieved structurally — the provisional grade already recorded the hedge or
abstention, so expiry only clears the review state. There is no code path from
"the learner ignored the question" to a filled-in diagnosis.

*The desktop surface.* `FeedbackScreen` renders the question with an answer box
and an explicit skip; the copy states that it is optional, that the grade is
currently provisional, and that skipping leaves the honest uncertainty in place
rather than a guess. Skip writes nothing at all.
`provisional_pending_clarification` renders as "provisional grade · not final"
wherever `manual_review_reason` already surfaced, rather than as "manual review
recommended" — the two are different obligations and reading one as the other
would send the learner looking for a reviewer.

*Resolution reuses the existing regrade door.* `_regrade_attempt` gained a
`clarification_exchange` that travels in the grading context (and therefore in
`grading_context_hash`, so the resolved grade is attributable to the exchange that
produced it) rather than being spliced into the learner's answer text, plus
`supersede_tiers=(1, 3)` so the provisional model grade is superseded instead of
leaving two gradings of one criterion in the replay log. The answer is persisted
**before** the regrade is attempted: the answer is the un-backfillable half
(standing constraint 6) and the regrade can always be re-run, so a provider outage
must lose the second and never the first. `regrade_failed` is a recorded outcome,
distinguishable from "never answered". `abstained` is first-class — a learner may
answer and the grader may still be unable to name a cause, and recording that is
what stops A8 from becoming a machine for manufacturing resolutions.

*The boundary has a standing watch.* `clarification_rate` is denominated in
attempts that *could have been asked* — ever model-graded (including superseded
evidence, since a regraded attempt still went through a grader that could ask)
unioned with attempts carrying a clarification at all, which is direct proof they
did. A self-graded attempt has no grader that could have asked, and including it
would dilute the rate toward zero, hiding exactly the over-asking the criterion
watches for. The metric abstains below 20 attempts and warns over 15%; over
threshold means machine-resident uncertainty misclassified as learner-resident,
which principle 8's unamended half says must be fixed machine-side.

*Expiry has a caller.* `expire_clarifications` runs in `run_startup_maintenance`,
before the deferred regrades. Without a sweep, an ignored question would leave
`provisional_pending_clarification` on the attempt forever while
`pending_clarification` correctly stopped offering the question after the TTL —
so the surface would read "provisional, not final" with no action available.

**6.4 as shipped** (migration 143) — four new services
(`discrimination_profiles`, `contrast_pairs`, `error_hunt`, `laddered_stems`),
three append-only stores, `learnloop instrument-audit` and
`commission-contrast-pairs`. Ship order was A5 → A4 → A3 → A2 because A5's
profiles are the oracle the other three consume.

**A5 — discrimination profiles.** Three consumers, exactly as §3.A5 names them:
`persona_gate.build_personas` plants every profile as highest-authority belief
material (and a profile-bearing item is promoted to the HARD gate tier
*structurally*, not by a flag); the grading context carries them as a **prior**
with `fails_criteria` deliberately withheld — handing the grader the criteria the
author expects to fail would turn a prior into a postdictive claim, which is the
disease §3.A5 warns this item can become; and `profiles_by_facet` feeds A4's
commissioning. `no_profile_applies` is a sibling arm in one closed vocabulary and
a **row** in `discrimination_profile_matches` rather than the absence of one —
which is what makes both tails of the fill-rate watch computable, since a rate
whose numerator is "no row was written" cannot be distinguished from "nothing was
graded".

**A4 — contrast pairs.** A new `ContrastPairGate` chained after the persona gate
on all four generation routes: both members in the band via the existing
`_success_band_difficulty` inversion, a within-pair gap cap, a symmetric declared
`differing_component`, and a structural-manipulation test that masks numerals and
refuses identical answer skeletons (values-only is a clone, and kinship would
refuse to count it twice anyway). Both members are refused together — half a pair
is not an instrument. Commissioning follows `contract_commissioning`'s shape:
`analyze_identifiability` findings become authoring requests on the plan, not a
report someone might read. Non-adjacency and order randomization live in the
serving path with a deterministic seed on `(session_id, pair_key)`, so the revert
criterion ("within-pair differences dominated by order effects") is measurable
rather than assumed away.

**A3 — error hunts.** `PlantedError.source` has **no freehand arm** — a freehand
error is an untyped instrument — and `required_repair` is mandatory, which is what
keeps the class on the right side of the no-recognition-items gate. The §3.0 gate
is *inverted* here: the belief-holder passes by **not seeing** the plant, so
`error_hunt_verdict` blocks visible plants, uncorroborated plants, flag-only
plants, plant==repair, and any prompt stating the error count. §10's clean-rotation
case is honoured end to end: a learner who "finds" an error in correct work mints
a **misconception candidate** in the existing store, and facet failures are
stripped with an audit event rather than written.

**A2 — laddered stems.** The kinship rule goes through the one existing
implementation (augmentation §8's "one code path"): two edge cases inside
`familiarity.tight_kinship_clusters`, threaded through to
`progression.apply_evidence_cap`. The finding worth keeping: `canonical_projection`
**already** satisfied A2, because its accumulator is keyed per
`(facet, capability)` — the pass that was capability-blind was the warmth-based
one, so that is the only one that changed.

**Correction to the above, from the Stage 6 review — A2's kinship half is
staged, not live.** The plan note originally said "inert when no item declares
stem columns", which undersells it: `apply_evidence_cap` /
`evidence_cap_grouping` / `tight_kinship_clusters` have **no production callers
at all** today, and `stem_columns_for_surfaces` (the only builder of the
`stem_columns` mapping) has none either. §10's bullet — two parts at one
capability count as ~one group, two at different capabilities count as two — is
satisfied by tests that call `apply_evidence_cap` directly, and by nothing on a
real run. It is *harmless* rather than wrong, because the projection independently
gets the answer right; but the code shipped for the rule is waiting on a consumer
that does not exist yet, and it should be read that way rather than as a live
guarantee.

**Every class ships its revert-criterion producer**, all under
`learnloop instrument-audit`: `discrimination_profile_rejection_rate` (two-tailed
— collapse *and* saturation), `contrast_pair_order_effect`,
`error_hunt_constructed_response_agreement`, `laddered_stem_cross_column_agreement`.
Each abstains as `no_data` with counts visible rather than reporting a fake
0.0/1.0, and the audit reads the **durable store** rather than the debug payload,
so `rebuild-derived-state` cannot silently zero the watched tail.

**The Stage 6 adversarial review found this note's original framing wrong, and
the correction is the most important line in the stage.** It said the missing
render of an error hunt's `worked_solution_md` and a laddered stem's
`stimulus_md` was "presentation only". It is not: the missing field is the
**stimulus**. Nothing filtered these items out of the due queue, so the live path
was authored → gated → scheduled → learner sees "correct the worked solution
below" with no solution → grader (which *does* receive the solution) marks every
plant missed → the projection banks negative facet mass for a repair the learner
was never shown the material to make. A harmful write manufactured by the serving
path, and worse than a missing instrument because it looks like evidence.

Fixed by `services/instrument_serving.unservable_reason`, called from
`scheduler.build_due_queue` and the exam-pool candidate build: an item whose
stimulus the surface cannot render is **not schedulable**, with a typed reason
and a stated remedy. Deliberately not a config flag — "can the app show this?" is
a fact about the code, and the correct way to lift the filter is to render the
stimulus and delete the arm. The desktop surface for these two classes remains
outstanding; until it lands they are authored, gated, stored and audited, but
never served.

**Two other claims in this note did not survive review and are corrected below**
(A2's kinship half, and `profiles_by_facet` feeding A4's commissioning — the
latter was false when written and is now true, wired into
`commission_contrast_pairs` so a request carries the authored profiles standing
on its facets).

**Stage 6 adversarial review — what it caught, and what changed.** Two blockers,
six serious, five minor. The two blockers were both *silent* failures that looked
like evidence, which is the failure shape this whole program exists to prevent:

1. **Unservable instruments were schedulable** (above). Fixed with a typed
   servability filter on both serving paths.
2. **§10's clean-solution line was honoured in the attribution channel and not in
   the ledger.** `suppress_facet_failures_on_clean_solution` emptied
   `target_evidence_families`, but an emptied list is indistinguishable from one
   the grader never filled: `_stamp_observation_lineage` wrote `attribution_json`
   NULL, and the projection's single-target fallback then attributed the whole
   failure to the criterion's own target — **0.75 units of negative mass banked
   against the exact facet the guard exists to protect.** The shipped test
   asserted the audit event and the suppression flag and never read
   `facet_capability_evidence`. Fixed with a typed `facet_write_blocked` reason
   that travels with the emptied list to the observation ledger, alongside the
   existing `machine_review_scope` arm; the test now projects and asserts zero
   negative mass on every cell, and fails without the stamp.

The six serious findings, all fixed: **(a)** the two folds shared the guard
predicate but not its *input* — the timeline read A6 facet ids raw while the
projection merge-resolved them, so a facet merge would desynchronise them and
break receipt exactness in the direction that understates the learner's curve;
**(b)** an attempt could sit `provisional_pending_clarification` forever, because
the sweep walked clarification rows while two states reach that review reason with
no row behind them (a deferred regrade that emits a request the regrade path never
recorded, and an answered clarification whose resolving regrade re-asked) — the
sweep is now keyed on the *attempt*, which is the actual invariant: the review
state exists to point at a pending question; **(c)** §10's "a confidently-graded
criterion never triggers a clarification" was unenforced, since
`learner_confidence` describes how confident the *learner* sounded and licensed a
question about a criterion awarded full credit at grader confidence 0.99;
**(d)** A4's gate blocked every honestly-authored pair, because with no semantic
oracle wired the deterministic rule reports "fails both" for any belief signature
that is not a byte-identical copy of one member's expected answer — one string
cannot model a holder who answers one member correctly and the other wrongly, so
that case is now a typed `CONTRAST_PAIR_UNJUDGED` abstention that ships to review
rather than a verdict; **(e)** A4's revert metric was a coin flip — its null value
*equalled* its threshold, and a reviewer simulation flagged pure-manipulation data
in 83 of 200 pools, now 2 of 200 after requiring an exact two-sided binomial
deviation while a genuinely order-driven pool still fires; **(f)** a re-grade
recorded neither its A6 observations nor its clarification request, which is what
produced (b)'s first arm.

**The one genuine regression, caught on the second pass and proven three ways.**
6.1's note and the code comment both claimed the shape term was inert on a pool
with no conjunctive items. **False.** `classify_item_shape` derived its cells
from `compile_criterion_targets`, whose *legacy* fallback maps each criterion to
its own facet — so any pre-A1 rubric naming different facets across criteria
already yielded two or more primary cells. On `fixtures/linear_algebra`, a vault
authored entirely before A1, **6 of 55 items scored as conjunctive, five of them
with no authored targets at all**, perturbing `selection_reward` by up to ±0.067
on ordinary content. The consequence was worse than the perturbation: it made
`test_sweep_flags_decision_relevant_and_inert_params` fail, i.e. it blinded the
calibration sweep to a genuinely decision-relevant scheduler parameter, and a
change that blinds the harness that validates scheduler weights is worth less
than the item it buys. `ItemShape` now carries `has_authored_targets` and both
`is_conjunctive` and `conjunctive_strength` require it, which is also the honest
reading: A1's shape rule is about items *authored* as capstones, and a legacy
rubric with one criterion per facet observes several cells without being one.
Pre-A1 vaults are now genuinely unaffected.

Minor fixes: a pair key claimed by three rows is refused as a group
(`PAIR_OVERSUBSCRIBED`) rather than having the first two members' verdict
recorded against the third — admitting or refusing a row on evidence about a
different item; the A6 reward no longer claims an explanation the learner did not
write (`observation_scope` says whether the *item* declared a facet, not whether
the *learner* volunteered anything); `profile_match_telemetry` had two
implementations, one of whose docstrings claimed there was exactly one; a bare
`KeyError` surfaced as "Internal sidecar error"; and `classify_item_shape` was
compiling every candidate's rubric on every scheduling decision.

**Verified and held up** (the reviewer's own list): `rebuild-derived-state` is
idempotent and reproduces the new columns byte-identically; A1 guard 1's headline
0.452 figure is real; the two folds agree within 1e-12 with A6 observations
present in the non-merge case; `exam_pool._item_components` is unchanged on all
55 legacy items; A6's three bounds are structural rather than conventional; the
elicitation state is genuinely never checkpointed and has no "declined"
representation; `profile_prior_payload` really does withhold `fails_criteria`;
the §3.0 gate writes no learner state; and all four revert producers read durable
stores rather than the debug payload.

### Stage 7 — Augmentation Phase B, then Phase C ✅

| # | Item | Provenance | Notes |
|---|---|---|---|
| 7.1 ✅ | B1 planted-misconception eval harness scoring the diagnostician **blind**, over the §12 regression shapes incl. abstention cases; B3 cross-model separation from day one (the existing planted-trial path has the same-model defect) | [Aug B1, B3] | Consumes A5 discrimination profiles (6.4) as authored planted ground truth — the producer B1 currently lacks. |
| 7.2 ✅ | B2 blinded persona-vs-real matcher | [Aug B2] | Licenses every B1 number; also upgrades 5.3's tiered gate to hard. |
| 7.3 ✅ | B4 planted-vs-adjudicated agreement live | [Aug B4] | Producer scaffold from 4.4; adjudicated side accrues via the contest-first queue. |
| 7.4 ✅ | Freeze B5; ship C1–C4 one rung at a time, each with hypothesis + revert | [Aug C] | **C1 is amended to repair-before-structure:** `diagnosis_md` stays first, the repaired trace comes second, and structured causal fields come last. This preserves causal §5.1's prose-first invariant while letting the checkable repair constrain structured attribution; it does not claim to implement literal repair-first ordering. C3 revert is measurable via 1.2. C4's eval must include a mid-history cause change. |

**7.1–7.3 as shipped** — migration 144 adds three append-only evaluation
ledgers, structurally separate from learner attempts and projections. B1 runs
the live grading contract with discrimination profiles and planted labels
withheld, scores all 14 fixed regression shapes by shape and in aggregate, and
refuses a decision license unless the matrix contains a real open-vocabulary
abstention plus the mid-history cause-change control. B3 canonicalizes model
families across provider aliases, so routing GPT through two gateways is not
independence. `learnloop diagnostic-eval` requires separate generator and
diagnostician providers and accepts a strict JSON oracle manifest; unknown
oracle fields fail closed.

B2's leave-pair-out matcher sees text-shape features only and persists hashes
and aggregate scores, never real learner traces. Insufficient volume abstains
and a separable corpus rejects. A B1 license is bound to the exact persona
corpus hash that B2 saw, preventing a realism pass over corpus A from licensing
scores over corpus B. The standalone `learnloop persona-realism` command
licenses only the authored-signature corpus used by §3.0; generated regression
personas are licensed only inside the B1 commissioning transaction. A successful
authored-signature license upgrades plain-practice failures from advisory to
hard; a separable corpus invalidates an otherwise passing gate result. B4 now
reads only licensed planted labels, joins them to A4 adjudications on overlap,
and retains `no_producer` when only unlicensed synthetic runs exist.

**7.4 as shipped** — B5's metric names and order remain frozen. The live
non-deterministic grading path now emits diagnosis prose, then the repaired
trace, then structured causal fields (C1); supplies typed verifier observations
whose `parse_failed`/`unsupported` arms confer no support (C2); samples three
independent diagnoses and turns disagreement into an unresolved cause set (C3);
and supplies bounded raw prior traces from the same canonical facet and surface
family without exposing prior diagnoses (C4). Sample agreement is stored as
provisional support but is deliberately absent from the durable-promotion
authorities. Every live augmented grade appends its prompt/model pin, context
arms, sample support, history ids, hypothesis, and revert criterion; the Stage-7
report exposes those receipts without inventing a verdict before outcomes
accrue.

### Stage 8 — Measurement Waves 4–5 (inference, then certification)

**Unlock condition:** the 3.1 reachability report shows structurally
certifiable contracts (Stages 5–6 are what create this).

| # | Item | Provenance | Notes |
|---|---|---|---|
| 8.1 ✅ | Static cells-converted precheck for B1 dominance and B3 entailment (principle 5 of §2) | [Meas §5.8.2 method] | Free. Last measurement: dominance converts 1 of 25 cells. Build nothing that doesn't move the count. |
| 8.2 | B1 capability dominance (embedded credit, assisted-attempts propagate nothing, sampled direct-probe audit) | [Meas B1] | Only if 8.1 justifies it post-Stage-5/6 (the pool will sit higher on the ladder by then, which is what makes dominance start converting). |
| 8.3 | B3 prerequisite entailment — shadow first, `hard`/`path_specific` edges only, per-edge violation tracking from day one | [Meas B3] | Same precheck discipline. |
| 8.4 | §5.3 substitution rule + certificate receipts (measured vs inferred, margins, integration never substitutable) | [Meas §5.3] | Certificates become withdrawable via 1.4's correction machinery when an edge retires. |
| 8.5 | C1 EIG-per-minute exam selection (adversarial weighting by P(below θ), over contract cells only) | [Meas §5.4, §5.6] | Confined to certification sittings; practice serving keeps the desirable-difficulty band objective — two objectives, one posterior, never conflated. |
| 8.6 | C2 adaptive sittings + posterior-threshold stop (superset reservation preserves leakage guarantees; never described as SPRT) | [Meas §5.5] | Revert if `false_certification_rate` (4.2) rises above baseline. |

**8.1 as shipped** — new `services/inference_precheck.py`, exposed by
`learnloop inference-precheck` and the desktop measurement-health panel. It is a
pure counterfactual over the exact 3.1 reachability snapshot: no attempt or
learner-state reads, no provider, no writes, and no inferred credit. B1's count is
the `MISMATCH_ABOVE` set by construction. B3 requires a directly reachable
downstream anchor and an explicitly typed prerequisite relation; missing
modality fails closed as `UNTYPED`, `instructional_order`/`facilitating` convert
nothing, and `path_specific` candidates are reported separately because a static
pass cannot prove the path was exercised. Integration cells remain visible as
prediction-only and are excluded from the later substitution count. Overlap
between B1 and B3 is set-deduplicated.

The post-Stage-5/6 measurement on `fixtures/linear_algebra` is decisive and
reproduces the old conclusion rather than assuming the new instrument wave moved
it: 9 of 47 cells are directly reachable; B1 converts **1 of the 38 gaps**
(2.6%, 1 of 47 overall), the same
`facet_vector_addition_must_be_commutative_and_associat@procedure_execution`
cell already identified by §5.8.2. B3 converts **0**. All 30 LO prerequisite
declarations are `UNTYPED`; the 42-edge prerequisite graph has 12 edges not
referenced by an LO declaration. That is a typed upstream-data verdict, not a
claim that entailment has no value: 8.3 is not justified until prerequisite
relations are reviewed into `hard`/`path_specific` and the precheck is rerun.
No B1/B3 belief or certification path was built by this item.

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

1. ✅ **C1 vs causal §5.1 field ordering** — **resolved as
   repair-before-structure:** diagnosis prose first, repaired trace second,
   structured causal fields last (7.4). C1's literal repair-first wording is
   amended rather than treated as silently compatible with the causal spec's
   prose-first invariant.
2. ✅ **Dead code disposition** — **all wired, nothing deleted.** `causal_health.py`
   now reports through `learnloop causal-attribution-audit` alongside A5's
   abstention rate (1.3); `audit_variant_manipulation_contract` is wired into
   `generate_rung_variant`; `validate_independent_measurement_contract` and
   `audit_manipulation_contract` are reached through 2.1's commissioning path;
   `resolve_machine_check` discharges the commissioning obligation with recorded
   grounds. P2's manipulation-contract claim stands as written — no descoping
   annotation needed.
3. ✅ **Persona-gate tiering** (5.3) — **confirmed:** diagnostic-purpose
   instruments are hard-rejected when the personas do not separate. Plain
   practice items receive an advisory review flag before a successful B2 run;
   an indistinguishable authored-signature corpus upgrades that tier to hard,
   while a separable corpus invalidates an otherwise passing result. A pre-B2
   pass is still not treated as persona-realism validation or diagnostic
   evidence.
4. ✅ **`TestExecutionVerifierAdapter`** — **wired**, with the trust boundary made
   explicit. A `test_execution` dispatch arm now exists, and the execution result
   arrives via a new `execution_result` parameter on `validate_repair_candidate`
   rather than from the model-authored `suggestion` payload: a repair that could
   attach its own `returncode: 0` would be issuing itself a deterministic
   `verified` verdict, which is the exact inversion the P0a write barriers exist
   to prevent. `test_execution` is requestable by the model (the schema Literal
   now admits it) and carries no result field. With no caller-supplied result the
   verdict is `unsupported`, never a pass. Regression-tested both ways.

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
