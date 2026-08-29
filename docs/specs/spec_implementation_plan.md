# LearnLoop v-next: implementation plan for a new developer

**Audience:** a developer new to this repository, implementing the full P0–P4
program defined by `spec_new_improvements_v2.md` (the umbrella) and the five
phase specs, all as amended 2026-07-17 (consensus fold-in, ledger seed) and
2026-07-18 (reader-dialogue fold: U-033–U-036, U-017@v3 — umbrella change
(q)).
**Authority:** each phase spec is the spec of record for its phase; this file
is a guide, not a spec — when they disagree, the spec wins.

---

## 0. What you are building

LearnLoop runs small experiments to infer the structure of a learner's world
model, finds the nearest consequential boundary, selects experiences expected
to move it, and later verifies the boundary moved on cold, unseen tasks. The
MVP slice is "I want to become good at tasks like this": select
end-of-chapter exercises → adaptive probe baseline (2–4 questions) → staged
teaching/practice from the nearest gap → durable cards with rotating surfaces
→ one fresh held-out cold assessment → boundary diff and a `suggest_next`
depth invitation. Certification always derives from the observation ledger,
never from model confidence.

## 1. Day one

Environment:

```bash
uv sync --extra dev            # add --extra pdf for PDF ingest work
uv run pytest                  # config in pyproject: testpaths=tests, pythonpath=src
uv run learnloop --help        # CLI; `learnloop init <vault>` to make a dev vault
cd apps/learnloop-tauri && npm install && npm run dev   # desktop app;
                               # the Rust shell auto-starts the Python sidecar
                               # (LEARNLOOP_VAULT=<path> to pick a vault)
```

Repo map:

| Path | What it is |
|---|---|
| `src/learnloop/services/` | Nearly all business logic (~100 modules) |
| `src/learnloop/db/` | `migrate.py` (runner), `repositories.py` (the one big repo module) |
| `src/learnloop/vault/models.py` | Domain models — `Goal`, closed capability vocabulary, `RequirementModality` |
| `src/learnloop/sim/` | Planted-learner simulation harness (`runner.py`, `profiles.py`, `sweep.py`) |
| `src/learnloop/ingest/` | Extraction IR, marker/pypdf extractors, reanchoring |
| `src/learnloop_sidecar/` | JSON-RPC bridge the desktop app talks to |
| `apps/learnloop-tauri/` | React/Tauri desktop app (the active product surface) |
| `migrations/` | Sequential `NNN_name.sql`; **next free number: 065**; applied by `db/migrate.py` |
| `tests/` | pytest suite (~150 modules); `fixtures/` holds real vault fixtures (`linear_algebra`, `probability`, …) |

Reading order (do not skip; budget 1–2 days):

1. `README.md`, `product_definition.md` — product frame.
2. `spec_new_improvements_v2.md` — the umbrella. §1 (principles), §2
   (architecture + keystones), §8a (delivery order), §9 (resolved
   decisions). Treat everything labeled *invariant* as law.
3. `spec_ownership_ledger.md` — governance. You will maintain this.
4. `spec_tauri_ui.md` — the client-side companion: design-language contract
   (the fifteen rules), per-phase screen/fixture inventory, the five-layer
   RPC recipe, and the inspector/diff replumbing. Read §1–§2 before writing
   any UI; the phase-specific §3 table when you reach that phase.
5. The phase spec you are implementing (see §3 below) — in full.
6. Code anchors, before writing anything: `db/migrate.py`,
   `vault/models.py`, `services/attempts.py`, `services/scheduler.py`,
   `services/probe_episodes.py` + `probe_families.py`,
   `services/canonical_projection.py`, `services/state_sync.py`,
   `services/exam_pool.py`, `sim/runner.py` + `sim/profiles.py`.
7. Background (optional): `research_on_learning.md`, `spec_andymatusnotes.md`.

## 2. Standing rules (violating any of these fails review)

1. **Events are authoritative.** All state is a replayable projection under a
   named algorithm version. Corrections append superseding events; never
   mutate old observations.
2. **Ownership-ledger discipline.** Before starting a phase: run the two
   lints in `spec_ownership_ledger.md` §1 (per-phase pin lint; head-delta
   report empty or parked). Dropping an umbrella commitment is legal only as
   a named deferral in the phase spec's ownership-claims block.
3. **No uncalibrated knobs.** Every new numeric constant registers in the
   P0 decision-parameter registry at birth: calibration label (`heuristic` |
   `simulation_validated` | `live_calibrated`) + lifecycle state (`active`
   needs a sensitivity certificate — a sim-sweep showing where in the
   plausible range decisions flip; `dormant` needs bind-event logging).
4. **Purpose-specific failure semantics.** Diagnostic / instructional /
   practice / assessment failures update different things. There is no
   universal "incorrect answer" pipeline.
5. **One familiarity/fingerprint ledger**, namespaced, across all activity
   purposes. Salience signals (dwell, skips, highlights) are never learner
   evidence.
6. **Migrations:** new files start at `065`; never renumber or edit an
   applied migration.
7. **Characterization tests first** on any measurement path (grading,
   posteriors, certification, scheduling) before changing behavior.
8. **Manual-first.** Reduce automation before reducing the end-to-end
   experience. LLMs render within owner-reviewed bounds; they never invent
   protocols, cards, or edges on the hot path.
9. **Silent caps are lies.** Every bound (probe budget, candidate counts,
   pool sizes) is surfaced.

## 3. Phases

Order is P0 → P1 → P2 → P3 → P4. Entry gates are in each spec; P3's first
slice (reader rendering + capture + annotations) is the one piece that can
interleave earlier since it has a no-P1 compatibility mode.

### P0 — measurement correctness (`spec_p0_measurement_correctness.md` v0.2)

Order P0.0 → P0.5 per its §8:

- **P0.0** Characterization tests pinning current behavior. Key targets: the
  probe likelihood path (`services/probe_episodes.py` ~1418, no per-attempt
  grader confidence), evidence mass (`services/canonical_projection.py`
  ~265), the ledger query (`db/repositories.py` ~3153 — doesn't select
  `grader_confidence`).
- **P0.1** Final activity substrate (families, cards + versions + lineage,
  surfaces, administrations, exposures) pulled forward from P1, **plus** the
  retirement record (§3.7) and the `interaction_events` envelope (§3.8 —
  attempt durations and retirement reasons logged from day one).
- **P0.2** Coarse outcome schemas; versioned asymmetric Dirichlet
  grader-confusion models; append-only grade/interpretation/adjudication
  events; the three-stream calibration design (§4.7: MNAR tap intake /
  stratified-with-logged-inclusion-probabilities calibration stream /
  learner-correction anchors). **Schedule the retrospective
  owner-adjudication bootstrap session early — it needs the owner, and P0.3
  is better calibrated with it done.** Build the adjudication overlay
  (`spec_tauri_ui.md` §3 P0) alongside — it is the vehicle for that session.
- **P0.3** Robust likelihood composition: grader-channel posterior + the
  `P(Z|H)` perturbation axis (labeled robustness analysis, not calibration);
  reliability propagated into posteriors **and** certification (closes the
  three P0.0 gaps).
- **P0.4** Versioned goal contracts, per-consumer pinning,
  `authorized_depth_step` successors, assessment burn (monotone; feedback
  burns pristine status).
- **P0.5** Decision-parameter registry (labels, lifecycle, sensitivity
  certificates, abstention budget wired to the ensemble-agreement gate),
  adjudication queue, planted-misgrade sim harness, compatibility cutover.

Done = its §9: byte-identical replay of the mvp-0.6 fixture, planted-misgrade
sims that don't silently flip diagnoses, Journey 12 at CLI level
(retire-with-reason, evidence survives, reason in `interaction_events`).

### P1 — shared substrate (`spec_p1_shared_substrate.md` v0.2)

Pre-start (with the owner — see §5): pin the one-page P0↔P1 table-ownership
diff; define the progression-policy object; resolve the
commitment-version/depth-event relationship.

Steps per its §8: commitments (+versions/targets/depth repositories, explicit
commit service) → capability aliases + TaskFeatures + ActivityPattern
registry → family/card contract extensions → edit classification +
card-lineage state (+ PracticeItem projection) → purpose-specific
administration adapters (replacing purpose-blind FSRS writes at
`services/attempts.py` ~1455) → namespaced fingerprint groups + soft-kinship
features + `familiarity_projection_v1` → mint/gate infrastructure (fixed and
rotating surfaces, durable pre-mint jobs) → angle progression + one-edge
depth-transition service (`suggest_next` semantics; a confirmed
`auto_within_envelope` stores intent but behaves as `suggest_next`) →
dual-write cutover behind six ordered gates → replay + Journey 6 + the §9.8
event-sufficiency replay prototype (per-card outcome counts from ledger
events alone — the U-014 resume path).

The cutover touches the attempt hot path; dual-write bugs are
silent-corruption-shaped. The six gates are mandatory, in order.

### P2 — narrow golden path (`spec_p2_narrow_golden_path.md` v0.2)

The first learner-visible payoff: the whole loop on one chapter fixture.
Exemplar selection → one atomic confirmation (goal contract v1 + commitment +
depth policy/envelope + assessment reservation) → pre-authored diagnostic
pack (2–4 items) → two-tier triage (§6.1: deterministic route table when
decisive; otherwise a provisional distribution as a decision aid, overrides
logged as anchors) → pattern ladder (explanation → example study/comparison →
completion → setup-only → repair → integration) → rotating practice surfaces
→ one fresh held-out cold assessment with burn semantics → restoration +
boundary diff → milestone + **`suggest_next` depth invitation only** (one
edge per decision; automatic activation is deferred to the auto-depth
package, U-018).

P2 also carries the **minimal bidirectional reader dialogue** (U-033, its
§7.6): span-grounded Ask in a new `reader` tutor context with a per-ask
answer-mode toggle; owner-placed reading questions as source-visible
instructional administrations with `reading_phase`; the four-disposition
picker; AI-answer exposure propagation. No `ask_now` planner, no automatic
density (U-017@v3). It runs on block-level span views — not the P3
annotation layer — and the golden path must complete with it disabled.

Owner-in-the-loop moments to plan around: blueprint review (now including
reading-question placement at section boundaries), diagnostic-pack review,
practice/assessment pool admission (LLM drafts within admitted bounds,
owner reviews), depth-edge review.

Done = its §12–§13: the 10-step fixture journey, fault injection after every
write boundary, event-replay equivalence, planted-learner profiles, leakage
suite, and *no unprompted depth activation*.

### P3 — reader integration (`spec_p3_reader_integration.md` v0.2, re-triaged against U-017@v3)

The delivery surface is resolved: the Tauri app + Python sidecar
(`spec_tauri_ui.md`, U-031 — screen inventory in its §3). Pre-start (with
the owner): decide the TS/Rust/Python split for render views and selection
anchoring, and cut the ten steps into 2–3 shippable slices. Suggested:
(1) render views + crosswalk
+ block health/crop fallback + annotations + capture outbox; (2) palette +
demand-paged synthesis + source objects; (3) authoring coach + arcs + depth
display + restoration.

Watch items: block-level extraction health is new (`ingest/ir.py` models
health per page today); sub-block anchor reanchoring across marker
re-extraction needs a review-volume budget; the capture outbox must pass the
§15.2 kill-process crash test; reading events are new kinds on the P0-owned
`interaction_events` envelope.

Done = its §15: Journeys 1, 2, 7; the salience-firewall test (reading signals
never touch evidence); annotation survival across re-extraction; replay.

### P4 — controller and scale (`spec_p4_controller_and_scale.md` v0.2)

Follow its §15 order. Steps 1–4 are the core: ControllerSnapshot +
versioned constraint engine (constraints define the feasible set; scores rank
only within it) → transparent staged policy (one edge per decision, affect
checks before any edge commits) → robust EVSI with the minutes-based loss
table (`L(h,a)` derived from triage routes + logged durations; `λ_time ≡ 1`;
non-time harms via constraint thresholds / dominance / documented tie-break)
and the LCB stop rule → stage-aware dispersion/interleaving constraints + the
single randomization layer (MRT + ε tie-breaking, logged propensities,
proximal outcomes at the *next spaced cold review*, commitment-level
parallel randomization for durable interventions).

Steps 5–6 are descoped per the consensus: soft-kinship kernel = LLM-judged
heuristic feature behind a sim admission gate (no fitted kernel in P4);
shadow work = *predictive components* promotable individually via prequential
scoring (composed-selector telemetry secondary and time-boxed — the
monolithic action chooser is never promoted at n=1). Open-world hypothesis
expansion is strictly last, behind its six-condition dependency gate.

The riskiest transition in the whole program is the dual-controller
coexistence window (its §14.2 step 3): the staged policy composing P2 runs
while the legacy scheduler composes other Today work, sharing one exposure
ledger. Treat that cutover with P1-cutover-level care.

Done = its §16, including the interval-width viability acceptance (robust
EVSI must remain usable under `heuristic`-width channels, tied to the P0
abstention budget).

## 4. Cross-phase working practices

- **Sims are part of the definition of done.** Any new selection signal,
  threshold, or weight ships with a planted-learner sim demonstrating it
  changes decisions, correctly (`sim/`; follow the `default_sweep.yaml`
  pattern). That sim doubles as the sensitivity certificate.
- **Verify end-to-end, not just unit tests:** exercise changes against a
  fixture vault (`fixtures/linear_algebra`, `fixtures/probability`) through
  the CLI or the desktop app; `uv run learnloop doctor` for vault health.
- **Registry hygiene:** `config.py` defaults get labels during P0; every
  constant you add gets a label + lifecycle state at birth.
- **Ledger hygiene:** when a phase spec's scope changes, update its
  ownership-claims block and re-run the lints; record spec changes in the
  spec's own change log and the umbrella's §12 if umbrella-level.
- **Ask, don't decide** anything in §5. Everything else that is reversible:
  decide, note it in the spec's change log, move on.

## 5. Open questions — raise with the owner, do not decide alone

1. Criterion-level grader-channel calibration: does the 4-class criterion
   schema get its own confusion models and anchors? (P0.3 blocker.)
2. Progression-policy object: referenced normatively in P1 §3.6, no schema.
   (P1 blocker.)
3. `commitment_versions` vs depth-change events: does a policy/envelope
   change force `version_appended`? (P1.)
4. Evidence-cap soft-kinship clustering: how are "tight clusters" identified
   from the feature vector? (P1 §4.3.)
5. P3 slice boundaries and the TS/Rust/Python split for render views and
   anchoring. (Surface itself is resolved: Tauri + sidecar,
   `spec_tauri_ui.md`.)
6. Dual-controller coexistence rules for the shared exposure ledger. (P4
   §14.2 step 3.)
7. `goals.yaml` ↔ SQLite drift reconciliation when a YAML edit races the
   confirmed contract head. (P0.4.)
8. Routing-prior representation (U-033): P0 invariant 10 and P2 §7.6 name a
   replay-derived routing prior superseded by the first cold observation,
   but its storage/projection schema and decay are unspecified. (P2
   pre-start.)
9. `reader` tutor-context profile: prompt contract and context manifest for
   the fourth tutor context (what it may reveal vs. the practice profile;
   which spans/exchange history it receives). Owner reviews the prompt like
   any other. (P2 pre-start.)

## 6. Suggested sequence (single developer)

1. P0.0–P0.2 (characterization → substrate → grader channel + bootstrap
   session with the owner).
2. P0.3–P0.5 (propagation, contracts, registry, cutover).
3. P1 steps 1–8; pause before cutover for the owner review; steps 9–10.
4. P2 end-to-end on the fixture chapter — **first end-to-end learner value;
   demo it before continuing.**
5. P3 slice 1 (can start any time after P0 if a change of pace is needed —
   it has a no-P1 compatibility mode).
6. P4 steps 1–4, then the §14.2 cutover, then P3 slices 2–3, then P4
   open-world last.

Each phase ends with its spec's acceptance section run in full and a
check-in against the owner before the next phase starts. Do not lower an
acceptance bar silently — if something must be cut, it becomes a named
deferral in the ownership ledger.
