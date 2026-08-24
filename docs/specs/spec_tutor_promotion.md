# Spec: Promote Socratic Tutor Questions to Practice Items / Learning Objects

Status: DRAFT v3 — all open questions resolved; congruence bugs from the v2
infra review fixed; implementation contract in §8. This version is the
authoritative contract for implementation.

## 0. Relationship to the learner-question pipeline

Learner questions already inform new practice items *implicitly*: substantive
unresolved questions adjust facet uncertainty read-side
(`question_adjusted_uncertainty_states`, consumed in `followups.py` before
gating/EIG), which raises follow-up interventions and `intervention_needs`,
which the diagnostic-practice generation path turns into diagnostic items.
That pipeline is sufficient for the *learner's own* questions and this feature
does not duplicate it.

Promotion covers what that pipeline cannot: the **tutor's socratic question**
(which never enters question_events as a question — it lives inside
`answer_md`) captured with **explicit learner intent** ("this particular probe
was good / exposed something I want to chase"). Implicit pipeline = inferred
gaps from asking behavior; promotion = deliberate curation of a specific probe.

Note for later calibration work (fitting contract): promotions logged in
`decision_features` are the positives; the negatives (promotable-but-unpromoted
turns) are simply the answered `question_events` in the same contexts — every
promotion-time feature MUST remain computable read-side from a bare
`question_event` so the denominator can be reconstructed at fit time (this is
the `silent_gate` weak-negative pattern from gate_fit). Do not add
promotion-time-only features that cannot be recomputed for non-promoted events.

## 1. Motivation

The tutor-ask guardrails deliberately deflect with guiding questions instead of
answers. Some of those socratic questions are better probes than anything in the
item bank, and some reveal a knowledge gap the learner wants to chase. Today the
only capture path is "save as note" — inert. This feature adds a one-click
"promote" action next to the 👍/👎 rating in `AskOverlay` that turns a tutor
exchange into a reviewable/auto-applied authoring proposal (Practice Item,
optionally a new Learning Object), **or resolves to scheduling an existing item
that already covers the probe**, and records the promotion as a training signal
for future coefficient fitting.

## 2. UX

In `apps/learnloop-tauri/src/components/AskOverlay.tsx`, next to the existing
👍/👎 spans and "save as note", add a "→ practice" action on any
`answer_status='answered'` tutor turn, available in all three contexts
(`practice`, `feedback`, `library`).

- Click → small two-way intent choice (explicit input, not inferred):
  - **"add to practice"** — the socratic question was a good rep; keep it in
    rotation. → practice route.
  - **"this exposed a gap"** — the learner could not answer it comfortably;
    the system should measure before it schedules. → gap route.
  - In `library` context only "add to practice" is offered (gap route requires
    an origin LO; see §7 Q7).
- Then: optimistic "promoting…" state → sidecar call → result chip:
  - `queued for review` (naming the patch id) when the proposal lands
    review_required,
  - `added: <practice_item_id>` when it auto-applied,
  - `scheduled: <existing_item_id>` when the promotion resolved to an existing
    bank item (dedup, §3 step 0),
  - `gap filed` for the gap route (diagnostic item is always review_required).
- Idempotent: a turn that has already been promoted shows the result chip
  instead of the button. **Promotion and saved-note state must be persisted
  server-side** (from `question_promotions` / `question_events.saved_note_id`)
  and returned by `get_tutor_transcript`, replacing today's ephemeral React
  state that resets on remount.
- **[v3 CHANGED — resolves Q5] Promotion does NOT touch the 👍/👎ratings.**
  `question_events.rating` is consumed by nothing algorithmic today; auto-
  setting it would erase the legitimate "👎 + promote" combination (bad answer,
  good gap) and contaminate the rating column for any future fitting. The
  promotion itself is the high-intent signal and is recorded in
  `decision_features`.

## 3. Pipeline (sidecar `promote_tutor_question(event_id, intent)`)

Service function in new `src/learnloop/services/promotions.py`. Idempotent by
`question_promotions` PK: if a row exists for the event, return it unchanged.

### Step 0 — PromotionAnalysis (both intents)

A structured extraction call (new `PromotionAnalysis` schema in
`codex/schemas.py`, following the `run_misconception_match` precedent; prompt
version constant `PROMOTION_ANALYSIS_PROMPT_VERSION`). Input: the Q&A thread
(reconstruct via the tutor_qa service `_thread`), the origin LO's facet
vocabulary and concept-edge neighbors, and the origin LO's existing practice
items (id, prompt excerpt, surface_family, evidence_facets). Output:

- `attributed_facets`: evidence facet ids the socratic question exercises —
  existing ids strongly preferred, minted only if nothing covers it.
- `question_nature`: `core_recall | mechanism | transfer | edge_case | what_if`.
- `attempted_in_thread`: whether the learner tried the socratic question
  in-thread and failed, vs never engaged (calibration feature).
- `covered_by_practice_item_id` (nullable): an existing item that already
  exercises the same probe (same facets + substantially same demand).

**Dedup short-circuit:** if `covered_by_practice_item_id` is set, do NOT
author anything. Record the promotion with `route='existing_item'` and
`existing_practice_item_id`, and add that item to the requested-items
scheduling floor (§4a) so it surfaces next session. For gap intent the
existing item *is* the measurement instrument — still perform the gap-route
evidence writes (step G2) but skip need filing/authoring. Reuse beats
authoring: no review overhead, no LLM quality risk, no bank bloat.

### Step 1 — Materialize grounding (note)

`evaluate_review_policy` only auto-applies items whose `source_ref_ids` resolve
with *direct grounding* (`note` / `canonical_source` refs). A `question_event`
is not a ref type, so promotion first materializes the exchange as a note:

- Factor the `save_tutor_answer_note` body-building logic (handler
  `tutor_qa.py:121-166`) into a shared service function; the handler and
  promotion both call it. If the turn was already saved as a note
  (`question_events.saved_note_id`, §5), reuse that note.
- The note body carries the full turn: learner question, tutor answer (which
  contains the socratic question), context ids.

**[v3 CHANGED — grounding must be semantically real, not just type-valid.]**
The materialized note by construction cannot contain the expected answer (the
tutor guardrail forbids stating it), so a note-only grounding would satisfy
`_has_direct_grounding` while its intent fails. Therefore:

- `source_refs` = the materialized note **plus the origin LO's existing
  source material**: vault notes whose `related_los` include the origin LO
  (ref_type `note`, or `canonical_source` for notes with
  `source_type='canonical_source'`).
- If the origin LO has **no** such source notes, the item is **forced to
  `review_required` in code** regardless of the model's self-assigned route —
  the synthesized `expected_answer` would have no real material behind it.

### Step 2 — Authoring proposal (practice route)

Call `generate_authoring_proposal` with the source_refs above and
`instructions` = a versioned `TUTOR_PROMOTION_PROMPT` (in `codex/prompts.py`)
containing the Q&A thread, the origin context (practice item id, its LO, that
LO's facets, the Step 0 attribution), and the extraction contract:

1. The practice prompt derives from the tutor's socratic question: extract it
   from the tutor turn and rephrase it to stand alone (self-contained context,
   no reference to the conversation). The rationale must quote the original
   guiding question verbatim for review.
2. **Attachment decision**: if the probed knowledge falls under the origin
   LO (or another existing LO in context), author one `practice_item` create
   against it, reusing existing facet ids (prefer the Step 0 attribution);
   mint a new facet only when nothing covers it. Otherwise author a
   `learning_object` create **plus** its first `practice_item` in the same
   batch.
3. New LOs must use an **existing concept id** from context. If no concept
   fits, still attach to the nearest concept and say so in the rationale.
   **[v3 rationale corrected]** This is a curation rule, NOT a stranding
   concern: the applier auto-creates missing concepts from an LO's `concept`
   field (`patches.py` `_upsert_learning_object_with_concept`), which is
   exactly the silent graph pollution we want to prevent. Concept creates
   also can't auto-apply by policy (`evaluate_review_policy` allows only
   LO/PI/concept_edge).
4. The item must carry `expected_answer` synthesized from the attached source
   material — the tutor never stated it (guardrail), so this is new content
   and the main quality risk; hence the grounding rule in Step 1 and the
   routing policy in Step 3.
5. Full generated-item metadata contract applies (rubric, weights, audit,
   difficulty, surface_family, repair_targets). Note `practice_mode` is a free
   string validated only via `vault.default_rubrics` membership — any mode
   without a default rubric must ship its own `grading_rubric` (existing
   validator `missing_rubric:<mode>`).
6. **Practice mode scales to learner skill.** The promotion context includes
   the origin LO's mastery mean and its `recommended_difficulty_band` (same
   `_success_band_difficulty` mechanism the expansion planner uses, with the
   practice band). The instructions carry a mode ladder keyed to that band:
   low mastery → recognition/structure modes (`ordering`, `classification`,
   `multiple_choice_with_explanation`); mid → recall/application
   (`short_answer`, `worked_calculation`); high → synthesis/transfer
   (`constructed_response`, `proof_explanation`, `teach_back`). For a NEW LO
   (no mastery yet) default to the mid band — the probe will place it.

One-shot repair loop applies as in the standard pipeline.

### Step 2.5 — Gap route

**[v3 CHANGED — no sim gate, corrected pipeline attribution.]** The v2 draft
claimed the gap route runs "under the §5.2 diagnostic constraints and the
sim/discrimination gate" — wrong pipeline. Those live in
`generate_diagnostic_proposal` (proposals.py) and the sim gate is
misconception-keyed (planted vs clean students); a gap declaration has no
misconception to plant, so the gate has nothing to discriminate. The gap route
uses `generate_diagnostic_practice_proposal` (practice_generation.py), which
has its own instruction constraints (`_diagnostic_practice_instructions`:
`practice_mode='diagnostic_probe'`, facet-pinned evidence, probe success band,
pinned `review_route='review_required'`) and is structurally unable to
auto-apply (its refs are `manual_context`/`existing_entity`, never direct
grounding). Follow-up (post-v1): let PromotionAnalysis optionally extract a
misconception hypothesis and route those through `generate_diagnostic_proposal`
to get the sim gate.

Gap route steps (requires origin LO — practice/feedback contexts only):

**G1 — Facet attribution:** from Step 0 (`attributed_facets`,
`question_nature`, `attempted_in_thread`).

**G2 — Evidence writes:**

- **Self-report claim**: insert a `learner_claims` row — `claim_type=
  'self_rating'`, scoped to the attributed `evidence_family` (facet) or the
  LO, low `claimed_level` (config, default 0.25), modest `prior_pseudo_count`
  (config, default 2.0), new `source` value `'tutor_gap_declaration'`.
  **[v3 CHANGED — low claims must actually do something.]** Today both claim
  consumers gate on `claimed_level >= claim_skip_threshold`, so a low claim is
  a silent no-op. Amend `initial_mastery_state_for_learning_object`
  (mastery.py) so ANY covering claim seeds the prior:
  `logit_mean = logit(clamp(claimed_level, 0.05, 0.95))`,
  `logit_variance = 1/max(prior_pseudo_count, 0.25)` — the threshold keeps its
  existing role ONLY for probe skip / attempt-target logic (probes.py
  unchanged). This is a deliberate generalization: init-wizard low claims will
  now also seed low priors, which is consistent self-rating semantics.
  For established LOs (mastery already initialized) the claim is inert at
  seeding — that's fine; it is the durable record for the calibration loop,
  and the read-side bump below carries the live effect.
- **Established LOs — read-side uncertainty bump:** there is NO probe
  re-entry (probes are one-shot; verified) and no derived-state writes.
  Extend `question_signal.py`: gap-declared promotions (join
  `question_promotions` `intent='gap'` within the signal window) count as an
  unresolved-question observation **with their own likelihood-ratio slot**,
  independent of `question_type` (a declaration is explicit, not inferred
  from type). **[v3 CHANGED — no hand-set "heavier weight".]** The ratio is
  fit empirically from the learner's own gap-declaration → subsequent-failure
  lift (same Laplace-smoothed machinery as `resolve_question_likelihood`),
  falling back to config `gap_declaration_solid_likelihood_ratio`
  (default 0.35, i.e. a stronger prior bump than an ordinary ask) below the
  min-samples threshold. Quantiles-not-vibes: the config value is a prior,
  the data owns it once samples accumulate.
- **Frontier interpretation by question nature:** a `core_recall`/`mechanism`
  gap on an established facet applies the bump (feeds goal frontier /
  follow-up gating). A `transfer`/`edge_case`/`what_if` gap on a facet whose
  current state is `solid` must NOT degrade core state — skip the bump for
  that facet; it marks the learner's frontier *boundary*: keep core state and
  bias the filed need's steering toward transfer (same escalation philosophy
  as teach_back).

**G3 — Instrument authoring:** file an `intervention_need` with
`trigger_reason='tutor_gap_declaration'`, `blocked_reason=
'tutor_gap_declaration'` (column is NOT NULL), `learning_object_id` = origin
LO (column is NOT NULL — hence the practice/feedback restriction), target
facets from attribution, `diagnostic_focus` carrying the thread + question
nature as steering context, transfer-biased `desired_intent` when nature is
transfer/edge_case/what_if. Then inline-trigger
`generate_diagnostic_practice_proposal` scoped to that need (when an AI
provider is available; otherwise the need waits for the next generation run).
Diagnostic-practice items are always review_required; no new routing rules.

**[v3 NEW] Staleness:** the existing staleness logic is trigger-aware only for
repeat-failure reasons, so `tutor_gap_declaration` needs would never expire.
Extend `_stale_repeat_failure_need`-style handling: a tutor_gap need goes
stale when every target facet has ≥1 *successful* attempt after need creation
(mirrors question-signal resolution semantics), or after
`gap_need_ttl_days` (config, default 21).

**G4 — Calibration loop:** the `decision_features` row records intent +
attribution + question nature + attempted_in_thread; once the diagnostic item
(or the deduped existing item) is attempted, the graded outcome is ground
truth for the self-report — over time this calibrates how much a learner's
gap declarations should be trusted (fitting `prior_pseudo_count` and the
likelihood slot for `tutor_gap_declaration`, gate_fit pattern).

### Step 3 — Persist + route (practice route)

Standard path: validation → one-shot repair → `_auto_apply_rows`.

**Routing policy (enforced in code at promotion time, never trusting the
model's self-assigned route):**

- Attach-to-existing-LO items may auto-apply under the normal policy ONLY
  when the Step 1 grounding rule is met (origin LO source notes attached).
- Any promotion batch containing a `learning_object` create is forced to
  `review_required` for the whole batch (downgrade `review_route` on the rows
  before persisting) — a synthesized `expected_answer` plus a net-new LO is
  too much unreviewed surface.
- All promotion-origin items get tag `tutor_promoted` for pruning/analysis.

### Step 4 — Record the promotion

- Insert `question_promotions` row (§5) with created entity ids + patch id +
  route + analysis outputs.
- Insert a `decision_features` row with `decision_type="question_promotion"`,
  `decision_id=event_id` (mirrors `_record_followup_decision_features`;
  requires the CHECK-constraint migration, §5). Features go in the existing
  `ability_vector_json` / `item_demand_vector_json` / `context_json` blobs
  (there is no `facets_json` column): question_type, hint_equivalent, rating
  (as-is, NOT auto-set), seconds_into_attempt, origin LO mastery mean/var,
  facet uncertainty snapshot, context, intent, question_nature,
  attributed_facets, attempted_in_thread, covered_by, and the outcome
  (existing_item vs attached-to-existing-LO vs new-LO, auto vs review).

## 4. Downstream integration with the learning algorithm

Verified against current infra — the reconciliation path already handles new
LOs; no mastery-model changes are required beyond §3 G2:

- `sync_vault_state` initializes mastery for the new LO (logit 0/var 1
  default, or claim-seeded per §3 G2) and `_enter_initial_probes` enters a
  probe because the batch ships the LO with a practice item (items with no
  `practice_item_states` row count as active for `_has_active_local_item`).
- Scheduler cold-start gate: the LO becomes schedulable through the probe
  path (probe EIG scoring), exactly like any authored LO.
- Goal scope: `resolve_goal_scope` resolves live from concept/facet
  membership, so a promoted LO whose concept/facets fall inside an active
  goal's `facet_scope` automatically joins the goal.
- Practice-item-only promotion: item joins that LO's pool; if the LO's probe
  is complete it is immediately eligible.
- Caveat: a brand-new promoted LO has exactly one item during its probe;
  hypothesis discrimination is weak. Post-probe `generate-practice` backfills.
  Acceptable.

### 4a. [v3 NEW] Requested-items scheduling floor

Promotion is the learner saying "I want to chase this" — nothing in the base
scheduler guarantees the item surfaces soon, and the priority weights are
decision-inert (sim-sweep finding: queue order sorts by raw selection_reward;
weights only gate membership), so this must be a **composition-level**
mechanism like `_apply_goal_quota`, not a weight:

- Definition: *requested items* = practice items referenced by a
  `question_promotions` row (`created_practice_item_id` or
  `existing_practice_item_id`) with zero `practice_attempts`.
- On queue build, if any eligible candidate is a requested item, guarantee at
  most `requested_items_per_session` (config, default 1) of them a slot via a
  prefix-floor reorder applied before the limit slice (so short sessions honor
  it), oldest promotion first.
- Eligibility is unchanged (active item, probe/exam-pool rules respected) —
  the floor reorders, it never bypasses gates.
- For the gap route this doubles as measurement-latency control: the
  calibration loop is only as good as time-to-first-attempt.

### 4b. Question-signal resolution **[v3 — resolves Q6: no promotion-time clearing]**

There are TWO read-side channels with different semantics; promotion changes
neither's resolution rules:

- Marginal/EIG channel (`question_signal.py`): resolution requires a
  *successful* later attempt on the facet. This already resolves the promoted
  question automatically once the promoted/deduped item is attempted
  successfully — zero new code, and clearing earlier would lower displayed
  uncertainty on a declared-but-unmeasured gap (backwards; violates
  evidence-not-mastery).
- Display bump (`facet_diagnostics.py`): cleared by any later attempt;
  unchanged.
- The one real cost of keeping the bump — followups filing a duplicate need on
  the same facet — is handled by dedup at need-filing time: skip filing when a
  pending `tutor_gap_declaration` need already targets the facet.

## 5. Schema (net-new — migration 027)

```sql
CREATE TABLE question_promotions (
  question_event_id TEXT PRIMARY KEY REFERENCES question_events(id) ON DELETE CASCADE,
  intent TEXT NOT NULL CHECK (intent IN ('practice', 'gap')),
  attributed_facets_json TEXT,        -- PromotionAnalysis output
  question_nature TEXT CHECK (question_nature IN
    ('core_recall','mechanism','transfer','edge_case','what_if')
    OR question_nature IS NULL),
  attempted_in_thread INTEGER,        -- PromotionAnalysis output (nullable bool)
  learner_claim_id TEXT,              -- gap route: the self_rating claim written
  intervention_need_id TEXT,          -- gap route: the filed need
  proposed_patch_id TEXT,             -- practice route (gap route's patch comes via the need)
  saved_note_id TEXT,                 -- grounding note (reused or created)
  existing_practice_item_id TEXT,     -- dedup route: promotion resolved to an existing item
  created_practice_item_id TEXT,      -- filled when applied
  created_learning_object_id TEXT,    -- filled when a new LO was applied
  route TEXT NOT NULL CHECK (route IN
    ('auto_apply', 'review_required', 'diagnostic_pending', 'existing_item')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

**[v3]** `route` gains `'diagnostic_pending'` (gap route: no patch at
promotion time) and `'existing_item'` (dedup short-circuit) so it can stay
NOT NULL.

Other migrations in 027 (SQLite CHECK changes require table rebuilds):

- `ALTER TABLE question_events ADD COLUMN saved_note_id TEXT` — and
  `save_tutor_answer_note` writes it (backfills the §1 missing link; the UI
  "saved" state becomes persistent). Preferred over a null-patch
  `question_promotions` row: keeps promotion-row semantics clean.
- Rebuild `learner_claims` extending the `source` CHECK with
  `'tutor_gap_declaration'`.
- **[v3 — was missing in v2]** Rebuild `decision_features` extending the
  `decision_type` CHECK with `'question_promotion'` (currently
  `('selection','probe','grading','followup')` — the insert would throw).
- `intervention_needs.trigger_reason` is free text — no rebuild, but
  staleness/consumer code must accept `'tutor_gap_declaration'` (§3 G3).

Config additions (`[tutor_promotion]` section, following existing config
class patterns): `gap_claim_level` (0.25), `gap_claim_pseudo_count` (2.0),
`gap_declaration_solid_likelihood_ratio` (0.35),
`gap_declaration_likelihood_min_samples` (reuse question-signal default),
`gap_need_ttl_days` (21), `requested_items_per_session` (1).

## 6. Telemetry summary

| Signal | Where | Consumer |
|---|---|---|
| promotion decision + features | `decision_features` (`question_promotion`) | future offline fitting (gate_fit pattern; negatives = answered question_events, §0) |
| promotion outcome/linkage | `question_promotions` | UI idempotency, analysis, requested-items floor |
| gap self-report vs graded outcome | `learner_claims` (`tutor_gap_declaration`) + first attempt on created/deduped item | calibrating gap-declaration trust (likelihood slot + pseudo_count) |
| item lineage | `provenance` on created item (note ref) + `tutor_promoted` tag | pruning, quality audits |

**[v3]** The v2 row "implied usefulness → question_events.rating → existing
gate fitting" was wrong twice over (rating feeds nothing; gate fitting joins
`followup_ratings`, not question ratings) and is deleted along with the
rating auto-set.

## 7. Resolved questions (v3)

1. **Prompt text** — derived from the tutor's socratic question, rephrased to
   stand alone; rationale quotes the original verbatim.
2. **Routing** — auto-apply only for attach-to-existing-LO items WITH real
   source grounding (§3 Step 1); new-LO batches always review_required;
   enforced in code.
3. **Unbounded LO growth** — review + `tutor_promoted` pruning suffices at
   current scale; the dedup short-circuit (§3 Step 0) is the structural
   mitigation. Optional soft UI cap deferred.
4. **Practice mode** — mode ladder keyed to mastery band (§3 Step 2.6); new
   LOs default mid band.
5. **Rating coupling** — decoupled. Promotion never writes `rating`.
6. **Question-signal resolution** — no promotion-time clearing; existing
   success-based resolution covers it (§4b).
7. **Library context** — practice route only (new-LO, always review). Gap
   route requires an origin LO (`intervention_needs.learning_object_id` is
   NOT NULL) and is restricted to practice/feedback.
8. **Concepts** — hard rule: existing concepts only. Rationale is graph
   curation + preventing silent applier-side concept auto-creation (NOT batch
   stranding, which cannot happen).

Deferred (v1.1, recorded here so the design accounts for them):

- **Answer-in-thread graded evidence**: let the learner answer the socratic
  question in-thread; grade via the existing grading seam and emit a
  discounted attempt through `apply_attempt` (exam-seeding pattern:
  ResolvedGrade + FrozenClock, discounted evidence mass). Gives immediate
  evidence at declaration time and same-session ground truth for G4. The gap
  route's claim machinery gets simpler once this exists.
- **Intent preselect from thread behavior** (default to "gap" when the
  learner visibly attempted and whiffed in-thread).
- **Misconception-keyed gap route** through `generate_diagnostic_proposal`
  + sim gate when PromotionAnalysis extracts a misconception hypothesis.

## 8. Implementation plan (contract for subagents)

Workstream boundaries — each item lists owned files; do not edit outside your
workstream.

**W1 — Foundations (migrations, repositories, note back-link, config):**
- `migrations/027_question_promotions.sql` per §5 (question_promotions,
  saved_note_id, learner_claims rebuild, decision_features rebuild).
- `src/learnloop/db/repositories.py`: question_promotions CRUD
  (insert/update/get by event id, list for requested-floor join,
  pending-gap-need lookup by facet), `set_question_event_saved_note`,
  extend `_decode_question_event` + transcript queries to surface
  `saved_note_id` and promotion state.
- `src/learnloop/config.py`: `[tutor_promotion]` config class + knobs (§5).
- `src/learnloop_sidecar/handlers/tutor_qa.py` + `services/tutor_qa.py`:
  factor the note-body builder into the service; `save_tutor_answer_note`
  writes `saved_note_id`.
- Tests: migration, repo CRUD, back-link.

**W2 — Learner model & scheduler (after W1):**
- `services/mastery.py`: generalize claim seeding (§3 G2), clamp levels.
- `services/question_signal.py`: gap-declaration observation slot with own
  fitted likelihood + config fallback; nature-based skip for solid facets.
- `services/practice_generation.py`: staleness for tutor_gap needs (§3 G3).
- `services/scheduler.py`: requested-items prefix floor (§4a), modeled on
  `_apply_goal_quota` composition.
- Tests for each.

**W3 — Promotion service & codex (after W1, parallel with W2):**
- `src/learnloop/codex/schemas.py`: `PromotionAnalysis`.
- `src/learnloop/codex/prompts.py`: `TUTOR_PROMOTION_PROMPT` + versions.
- `src/learnloop/codex/client.py`: `run_promotion_analysis` (mirror
  `run_misconception_match`).
- New `src/learnloop/services/promotions.py`: `promote_tutor_question` per
  §3 (idempotency, analysis, dedup, note grounding + LO source refs,
  routing enforcement, gap route: claim + bump linkage + need + inline
  diagnostic generation, decision_features, promotions row).
- Tests: routing downgrade, grounding fallback, dedup short-circuit, gap
  route writes, idempotency, decision_features CHECK.

**W4 — Sidecar/Tauri/frontend (after W2+W3):**
- Sidecar handler `promote_tutor_question(event_id, intent)`; transcript
  returns promotion + saved-note state.
- Tauri: Rust command, dto, `client.ts` (note: new Rust commands need a full
  app restart — stale_app_binary).
- `AskOverlay.tsx`: intent choice, optimistic state, result chips, persisted
  promoted/saved state.
