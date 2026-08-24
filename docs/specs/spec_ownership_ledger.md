# Spec ownership ledger (umbrella ↔ phase contract)

**Status:** active governance artifact (umbrella D7). The umbrella
(`spec_new_improvements_v2.md`) is the source of commitments; this file is
the contract between the umbrella and the phase specs. Seeded 2026-07-17 with
the commitments negotiated in the orphan/n=1 review; full umbrella backfill
is pending (U-002).

## 1. Regime

- **IDs are lineage + revision.** `U-NNN` names a commitment lineage;
  `U-NNN@vK` names an immutable revision. Revisions are append-only.
  `supersedes` links carry a class: **semantic** (meaning changed — phases
  pinning an earlier revision must re-triage) or **editorial** (wording only —
  pins remain valid). This mirrors the product's own card-lineage
  fork-vs-survive rule.
- **Phase specs pin and claim.** Each phase spec declares the revisions it
  implements and the lineages it defers (with a deferral target) in an
  ownership-claims block. A phase spec may drop an umbrella commitment only
  by naming it there.
- **Lint 1 — per-phase (pass/fail):** every commitment revision the phase
  pinned whose scope intersects the phase must appear in `implements` or
  `defers`. Checked against the *pinned* revision plus any successors the
  phase explicitly adopts — never against head.
- **Lint 2 — head-delta report (global):** the set of semantic revisions at
  umbrella head not claimed by any phase at any pin. Must be empty, or every
  member explicitly parked, before implementation of any phase begins.
  Editorial revisions never enter this report.
- Lint runs as an agent pass before any phase spec is finalized and before
  any phase implementation starts.

## 2. Entries

Statuses: `active` (governing rule), `implemented-by-spec` (owning phase spec
now specifies it; code lands with that phase), `deferred` (named target),
`split` (part owned now, part deferred), `parked` (explicitly awaiting a
gate).

| ID | Rev | Commitment | Owner | Status |
|---|---|---|---|---|
| U-001 | v1 | This governance regime: version-aware ledger, two lints, semantic/editorial revision classes | umbrella §1 | active |
| U-002 | v1 | Full backfill of umbrella commitments into this ledger | owner | parked (gate before P1+ implementation) |
| U-010 | v2 | Affect tap: full typed vocabulary with commitment-level semantics (pause / retire / burden edit); signal capture live from P0 | P0 (capture), P2 (run semantics) | implemented-by-spec |
| U-011 | v2 | Affect auto-downgrade `auto_within_envelope` → `suggest_next`: enforcement point | auto-depth package (U-018) | deferred |
| U-012 | v2 | Retirement record + reason taxonomy + replacement hook; Journey 12 at CLI level | P0 | implemented-by-spec |
| U-013 | v2 | `interaction_events` corpus envelope; log-now-model-later; attempt durations + retirement reasons from day one; P3 adds reading kinds | P0 (envelope), P3 (reading kinds) | implemented (P3 reading kinds landed, 2026-07-21; migration 091) |
| U-014 | v2 | Likelihoods as weak priors: P0's `P(Z\|H)` perturbation axis is robustness analysis, **not** calibration; hierarchical updating deferred with resume path (card-level outcome counts; retroactive via replay) | P0 (axis); deferred (hierarchy) | split |
| U-015 | v2 | Card psychometrics: accrual is a deferred projection; event sufficiency (card version, outcome, administration context) is a P1 acceptance gate | P1 | implemented-by-spec (gate) |
| U-016 | v2 | Depth-edge two-level authoring (owner templates, LLM instances, generator demotion) | auto-depth package (U-018) | deferred |
| U-017 | v3 | Planner-driven automatic reading-question insertion only (`ask_now` planner + density policy; learned timing = P4 shadow, next-cold-outcome horizon). **Semantic** supersede of v2: owner-placed reader questions carved out to U-033 (P2); P3 keeps mode gating + per-question controls | deferred (P4 shadow) | deferred |
| U-018 | v1 | Auto-depth package boundary — deferred as one unit: LLM edge-instance generation, `auto_within_envelope` activation authority, affect-downgrade enforcement. Live from first cut: curated edges, `suggest_next`, envelope objects (P1), full affect semantics. Ships with its dead-man switch or not at all | umbrella §2 (D8); enforced by P2/P4 | active |
| U-020 | v1 | Three calibration streams, never conflated: misgraded tap = MNAR error intake (never a denominator); stratified random adjudication with logged inclusion probabilities = calibration stream (influence prioritization is the stratification design); structured learner corrections = individual anchors; retrospective bootstrap over existing attempts with logged sampling frame | P0 | implemented-by-spec |
| U-021 | v1 | Abstention budget: "diagnostician abstains ≤ X%" as a registered, monitored parameter; sim-chosen prior concentrations; live alarm | P0 | implemented-by-spec |
| U-022 | v2 | Decision-parameter registry lifecycle with a **two-artifact** discipline: the **sensitivity certificate** is a *coverage* artifact required for every `active` decision parameter (documents where in the swept range decisions flip; flip points do not invalidate it; a value change outside the covered hash does) — an active param lacking coverage is `active_pending_certificate` debt (audit warning / release-gate failure); **promotion evidence** is a separate *normative* gate for status beyond `heuristic` (sim evidence carries the `decision_stable` refusal → `simulation_validated`; real-outcome manifest → `live_calibrated`). `dormant` (frozen, bind-event logged, no coverage certificate) / `deleted` (proven redundant); class-asymmetric (inert shaping weights → deletion candidates; inert constraint params → dormant-with-monitoring). **Semantic** supersede of v1: v1 read `active` as requiring a single pass/fail sensitivity certificate only when claiming calibrated authority; v2 makes coverage mandatory-for-all-active and splits validation into promotion evidence | P0 registry | implemented-by-spec |
| U-023 | v1 | Constrained decision-cost hierarchy: (1) constraints, (2) expected wasted learner-minutes among feasible (`λ_time ≡ 1`; `L(h,a)` derivable from routes + durations), (3) ordinal harms only via defined entry points (constraint thresholds / dominance filter / documented tie-break); route entries registered + inspectable | P4 (P2 routes) | implemented (P4 code, 2026-07-21; step 3) |
| U-024 | v1 | One randomization layer: micro-randomized reversible near-equivalent decisions + ε tie-breaking, propensities logged; proximal outcomes at next spaced cold review (never end-of-session); commitment-level parallel randomization for durable interventions; explicit carryover models otherwise → hypothesis-grade | P4 | implemented (P4 code, 2026-07-21; step 4) |
| U-025 | v1 | Scorer decomposition: predictive components promotable via prequential held-out scoring; action chooser stays the staged policy; monolithic action-chooser promotion deferred at n=1 | P4 §7 | implemented (P4 code, 2026-07-21; step 6, descoped) |
| U-026 | v1 | Soft-kinship kernel: LLM-judged heuristic feature behind a sim admission gate; learned weight training deferred (sparse labels at n=1) | P4 | split (feature + sim gate implemented P4 code, 2026-07-21; learned kernel deferred) |
| U-027 | v1 | P2 triage mechanism: deterministic route table where evidence is decisive; otherwise provisional proposed distribution presented as a decision aid with alternatives; overrides logged as anchors; registered `heuristic` channel | P2 | implemented (P2 code, 2026-07-20; migration 083) |
| U-028 | v1 | Surface-pool provenance: LLM drafts within admitted cards/blueprint bounds; owner review before pool admission | P2 | implemented (P2 code, 2026-07-20; migration 085) |
| U-030 | v1 | UI design-language contract: term.tsx tokens, fifteen screen rules, CommandOverlayFrame overlay form factor, glyph+label+color for non-monotone state, one-quantity-per-channel viz discipline | spec_tauri_ui.md §1 | implemented-by-spec |
| U-031 | v1 | Per-phase screen + fixture inventory; delivery surface = Tauri app + sidecar (resolves the P3 surface question); fixtures-are-the-mock-layer with per-screen offline-render acceptance | spec_tauri_ui.md §3–§5 | implemented-by-spec |
| U-032 | v1 | Inspector/diff replumbing for the three-hash + lineage world: three identity rows, new entity kinds, fork-break lineage navigation, lineage-aware diff entries, administration context on attempts, algorithm_version compatibility seam | spec_tauri_ui.md §3 (timed with P0.4/P1) | implemented-by-spec |
| U-033 | v1 | Minimal bidirectional reader dialogue: `reader` tutor context (learner-controlled answer mode: direct / guide / ask-me-first); owner-placed reading questions as source-visible instructional administrations with `reading_phase`; four-disposition picker (comprehension_only / check_once_later / keep_developing / reference_only) mapping to existing purposes; formative answers → replay-derived routing prior superseded by first cold observation; AI answers append exposure (familiarity warming); reader event kinds on the U-013 envelope | P2 (umbrella §6.9) | implemented (P2 code, 2026-07-20; migration 086) |
| U-034 | v1 | Authoring pipeline as reviewable artifacts: candidate extraction → reinforcement-target selection (goal-grounded, `select_none` legitimate) → pattern selection from admitted registry → bounded rendering (target+pattern fixed) → functional lint; artifacts not API calls; batch-and-rank; rejected candidates + reasons logged to corpus | umbrella §6.10; P2 consumes for pool authoring, P3 for demand-paged synthesis | active |
| U-035 | v1 | `learning_process` metadata on ActivityPattern versions (closed vocabulary); controller-side routing metadata only — never an evidence/projection input | P1 §3.5 | implemented-by-spec |
| U-036 | v1 | Renderer classes beyond text: interactive diagrams, notebook/code handoff, artifact annotation/grading, project-grounded dynamic media, voice — deferred as one unit; media choice must be representational when it lands | deferred (post-MVP) | deferred |

## 3. Change log

- **2026-07-17** — Created; regime defined (version-aware IDs, per-phase pin
  lint, head-delta report); seeded with U-001–U-028 from the orphan/n=1
  consensus. Full backfill parked as U-002.
- **2026-07-17 (later)** — U-030–U-032 added from the Tauri UI formalization
  (`spec_tauri_ui.md`): design-language contract, per-phase screen/fixture
  inventory (delivery surface named), inspector/diff replumbing.
- **2026-07-18** — Bidirectional-reader review fold (umbrella change (q)).
  U-017 revised to v3 (**semantic**): scope narrowed to planner-driven
  automatic insertion; P3's pin of U-017@v2 re-triaged in its
  ownership-claims block. U-033 (P2 minimal reader dialogue), U-034
  (five-stage authoring pipeline), U-035 (`learning_process` metadata),
  U-036 (non-text renderer deferral) added.
- **2026-07-19** — U-022 revised to v2 (**semantic** supersede of v1; owner
  decision) resolving audit finding F1. The sensitivity certificate becomes a
  *coverage* artifact required for every `active` decision parameter (flip points
  do not invalidate it), and a separate *promotion evidence* artifact becomes the
  normative gate for status beyond `heuristic`; an `active_pending_certificate`
  debt state is added (audit warning / strict-release-gate failure). P0 is the
  only phase pinning U-022 and re-pins it @v2 (implemented-by-spec); no other
  phase pin re-triage is required.
- **2026-07-20** — **P2 code landed.** U-027 (triage mechanism), U-028
  (surface-pool provenance), and U-033 (minimal bidirectional reader dialogue)
  move from `implemented-by-spec` to `implemented (P2 code)` — migrations 081–087
  plus the composed golden-path services and acceptance/leakage suites (see
  `spec_p2_narrow_golden_path.md` §14). U-010@v2 (P2 affect run semantics) and
  U-018@v1 (auto-depth deferral) are unchanged: P2 ships the affect capture/run
  semantics and holds U-018 inert (`LIVE_ACTIVATION_ENABLED = False`, no unprompted
  depth activation). **Lint 1 (P2):** every P2-scoped revision appears in the P2
  ownership-claims block — implements U-010@v2, U-027@v1, U-028@v1, U-033@v1;
  defers U-018@v1 (with U-011). PASS.
- **2026-07-21** — **P3 code landed (slices 1–3).** U-013@v2 moves from
  `implemented-by-spec` to `implemented (P3 reading kinds landed)` — migration
  091 widened the P0-owned `interaction_events` envelope with the reading-event
  kinds and the §8.1 columns/indexes (see `spec_p3_reader_integration.md` §17).
  U-034@v1 (authoring pipeline as reviewable artifacts) is now consumed by P3's
  demand-paged synthesis + learner Q+A authoring (`reader_authoring`), still
  `active`. U-017@v3 wording is unchanged and stays **deferred (P4 shadow)**: P3
  landed only the mode gating + per-question controls it already claimed; the
  `ask_now` planner and automatic question density remain out of scope. U-018@v1
  is unchanged — P3 keeps live `auto_within_envelope` activation inert behind
  `depth_transition.LIVE_ACTIVATION_ENABLED = False`. **Lint 1 (P3):** every
  P3-scoped revision appears in the P3 ownership-claims block — implements
  U-013@v2 (reading kinds) and extends U-033@v1 (mode presentation +
  per-question controls); consumes U-034@v1; defers U-017@v3 and U-036@v1. PASS.
- **2026-07-21** — **P4 code landed (final package: descoped steps 5–6 + the
  open-world §14.1 dependency gate).** U-023@v1 (constrained decision-cost hierarchy),
  U-024@v1 (one randomization layer), and U-025@v1 (scorer decomposition) move from
  `implemented-by-spec` to `implemented (P4 code)` — migrations 096–100 plus the staged
  controller / EVSI / dispersion / randomization / shadow-component services and their
  acceptance/firewall/prequential suites (see `spec_p4_controller_and_scale.md` §18).
  U-025 ships the shadow predictive components with individual prequential promotion and
  the structural no-promotion guard on the monolithic action chooser (§7.4). U-026@v1
  stays **split**: the heuristic LLM-judged soft-kinship feature + its planted-learner
  sim admission gate landed (firewall — computed + logged, consulted by nothing; the sim
  can only reach `simulation_validated`, U-022 promotion-evidence emitted through the
  registry), while the LEARNED kernel-weight path remains deferred (sparse n=1 labels).
  U-017@v3 stays **deferred (P4 shadow)**: P4's shadow predictive-component discipline
  now COVERS the reader-question policy (scored against the next spaced cold outcome),
  but live insertion stays owner-placed static — no `ask_now` planner promoted. U-018@v1
  is unchanged (auto-activation OFF, `LIVE_ACTIVATION_ENABLED = False` on both the depth
  transition and the kinship feature). Open-world expansion (U-none; §10) is NOT
  implemented — the §14.1 dependency gate is landed as an executable check that currently
  evaluates NOT MET, so no expansion worker or successor-set UI is enabled.
  **Lint 1 (P4):** every P4-scoped revision appears in the P4 ownership-claims block
  (`spec_p4_controller_and_scale.md` intro) — implements U-023@v1, U-024@v1, U-025@v1
  (monolithic promotion deferred), U-026@v1 (heuristic LLM-judged feature; learned
  weights deferred — the ledger's `split`); owns the U-017@v3 shadow path; defers U-011
  behind the auto-depth package (U-018). Every one lands in `implements`/`owns`/`defers`.
  PASS.
- **2026-07-21 (Lint 2 — head-delta, global; P0–P4 all implemented)** — the set of
  semantic umbrella-head revisions not claimed by any phase at any pin is **empty**
  (every U-0NN lineage above is either `implemented`/`implemented-by-spec`/`split` under
  an owning phase, `active` as a governing rule, or `deferred`/`parked` with a named
  target). No unparked semantic head revision remains. PASS.
