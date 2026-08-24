# Hypothesis Surfaces — learner-facing UI/UX for trust, remediation, and telemetry

Status: draft v3 (2026-07-14). v1 design; v2 code-verified with attention budget and launch
cuts; v3 after two external reviews, all code claims verified against the tree: typed claim
surfaces replace the universal verdict card, remediation gets a real episode/task model,
forecast issuance/censoring semantics, authored corrections, the exact-receipt blocker, a
three-way intake split, and the calibration duel promoted into launch scope. Companion to
`spec_knowledge_model.md` (KM3 §9.5 dual-axis, §9.6 provenance UI, §10 error taxonomy),
`spec_misconception_diagnostics.md` (registry §2.2, resolution §7), and
`spec_source_ingestion_v2.md` (§11 analytics, §14 exposure).

## 1. Purpose and principles

Every surface in this spec answers one of the questions a learner actually asks: *what do I
do now, will I be ready by the due date, is my time working, what don't I know that I think
I know, why was I wrong, can I trust this thing.*

Principles, in priority order:

1. **Demonstrated and Predicted are never blended** (KM3 §9.5). Ambient surfaces may lead
   with Ready; goal/certification surfaces lead with Demonstrated. They never share an
   axis: co-plotting implies commensurability more strongly than any label can undo (§4.1).
2. **Every rendered system belief is a claim, and renders as a typed claim surface** (§2).
   The response affordances match what the claim *is* — an estimate invites "seems
   high/low"; a ledger fact invites "show me the receipt"; nothing invites a coerced label.
3. **Learner responses are feedback signals, not ground truth.** "Ready is too low" is
   another prediction; a schedule dispute is a preference; a diagnosis denial is
   self-report. Telemetry stores them as signals and never promotes them to labels.
4. **Non-monotone honesty.** Regrades, decays, and misconception reactivations are shown,
   annotated, never smoothed. Hiding a downgrade anywhere destroys trust everywhere.
5. **Deterministic core.** Any number, count, derivation, evidence citation, or correction
   shown to the learner is template-rendered from ledger or authored content. Nothing a
   generative model produces at render time is presented as fact (§5.3, §4.7).
6. **No fabricated precision.** A projection without a validated model behind it is either
   not shown, or shown with its provenance and model coverage ("decay estimated from 8 of
   12 facets") and entered into the forecast ledger (§6.3) so it can be graded later. This
   applies to the system's telemetry claims too (§7.2).
7. **Content gaps are not learner gaps.** A facet that cannot be demonstrated because no
   supporting items exist (`attempts_to_certify = None`) is the system's debt, not the
   learner's, and is always labeled as such.
8. **Local by default.** Belief, response, and correction events never leave the vault
   without explicit opt-in (§2.5).

## 2. Typed claim surfaces

### 2.1 Claim classes

Every claim surface shares one visual shell — claim, provenance, receipt link, response
area — but the response vocabulary is class-specific. Confirm/dispute/correct/skip
uniformly applied was a survey system; these are not:

| claim_class    | claim_type(s)                 | rendered claim                                   | response vocabulary |
|----------------|-------------------------------|--------------------------------------------------|---------------------|
| `estimate`     | `ready_estimate`              | "You'd probably get this right (ready {p})"      | seems high / about right / seems low / not sure |
| `estimate`     | `forecast`                    | "At current pace, ready around {date}"           | pace is typical / atypical, plus ONE structured planning override: "use my usual {n} study days/week" (a learner-supplied scenario, labeled as such, entered into the forecast ledger) |
| `diagnosis`    | `misconception`               | §4.7 statement pair                              | fits / doesn't fit / partly / edit the interpretation |
| `policy`       | `schedule_choice`             | "Chosen next because {dominant reason}"          | useful / choose something else → reason: too easy / too hard / irrelevant / recently done / bad item |
| `ledger_fact`  | `regrade`                     | "Earlier credit on {facet} was regraded down"    | view receipt (old vs. new) / **request review** — an appeal that routes to grading review, not a confirm button |
| `ledger_fact`  | `session_delta`               | "This session moved {facet} prediction {±Δ}"     | view receipt only. Derived arithmetic solicits no verdict — there is no valid label |

Rules that hold across classes:

- Responses **never mutate** canonical content, Demonstrated state, or grading evidence.
  The surface says what a response does ("flags this for grading review") so the
  affordance doesn't feel like a telemetry sink.
- Dismissal is free, one tap or ignore, and never blocks the embedding flow. Dismissals
  are recorded for fatigue analysis and **excluded from training labels**.
- A `regrade` remains a disputable judgment — the re-grading decision can be wrong — but
  the channel is "request review" with an old-vs-new receipt, feeding the same
  grading-review machinery as `probe_regrade_checks`.

### 2.2 Telemetry schema

One append-only table, `hypothesis_events`:

```
hypothesis_events(
  id, created_at,
  presentation_id,        -- links a response to the exact presentation it answered
  event_type,             -- 'presented' | 'responded' | 'dismissed'
  claim_class,            -- §2.1 enum
  claim_type,             -- §2.1 enum, extensible
  claim_ref,              -- structured identity: misconception id / (facet, capability) / forecast id / item id
  claim_version,          -- version or snapshot hash of the claim's rendered value
  producer_version,       -- algorithm_version that produced the belief; SELECTION_POLICY_VERSION for schedule_choice
  surface,                -- 'today' | 'feedback' | 'finish' | 'log' | ...
  temperature,            -- 'hot' (moment of error) | 'cold' (reflective review)
  visible_at,             -- actual viewport exposure, not component render
  suppression_reason,     -- set when the §2.4 budget rendered this without affordances
  response_payload_json,  -- class-specific response, present on event_type='responded'
  session_id, visit_id    -- visit_id covers Today/Log interaction outside a practice session
)
```

- **Presentations are logged when exposed to the learner**, not when a component renders.
- **Debounce by (claim_ref, claim_version, surface, session/visit)** — a materially
  changed estimate in the same session is a new presentation, not a suppressed duplicate.
- **Provenance cannot be backfilled**: a `ready_estimate` response collected under mvp-0.7
  is not comparable to one after the next projection change; every row is stamped.

### 2.3 Hot/cold protocol

A `diagnosis` claim rejected **hot** (at the moment of error, in Feedback) is flagged and
re-presented **cold** on the learner's next Log visit ≥1 day later (§4.9 working
hypotheses). Passive re-ask only — Log lives on the tab bar, so re-presentation happens on
the next reflective visit for free; no push scheduler is built. The raw pair is linked via
presentation ids and left uninterpreted: **no `defensive_dispute` label** — the correction
was shown between the two verdicts, so hot-deny → cold-agree may be learning from the
correction, not defensiveness. Hot-reject + cold-reject feeds the grading/registry review
queue (§4.10 intake). Neither response alone is trusted.

### 2.4 Attention budget and dispatcher

Verdict fatigue corrupts the telemetry this spec exists to collect: a learner who
reflex-dismisses claim #7 is also giving corrupted non-engagement data on claims #1–6.

- Global cap: **2 response-soliciting presentations per session** (config:
  `[hypothesis].session_card_budget`). **One slot is reserved for hot Feedback claims** —
  otherwise Today can consume the whole budget before an important error occurs.
- Per-claim cooldown: a claim that received any response is not re-solicited for its
  cooldown window (default 7 days), except the §2.3 cold re-ask.
- **At most one cold re-ask per Log visit.**
- Over-budget claims render as plain annotated text — no affordances — and log
  `presented` with a `suppression_reason`.
- Priority when competing: `misconception` > `regrade` > `forecast` > `ready_estimate` >
  `schedule_choice`.

### 2.5 Privacy boundary

All `hypothesis_events` data — especially learner-authored corrections and misconception
statements — stays in the local vault. Export or any training use is explicit opt-in. The
data is inspectable and deletable from the app. This lands with the schema, not later:
the spec anticipates training use, so the boundary is part of the contract.

*(v2's §2.5 verdict weighting is deleted, not deferred: answer-calibration does not
establish reliability about grading, explanations, or scheduling preferences, and
down-weighting miscalibrated learners discounts exactly the people the product exists
for. Preserve raw signals; stratify at analysis time.)*

## 3. Error taxonomy → three-way routing

The §10.1 mechanism taxonomy (`error_taxonomy_map.py`) carries the load-bearing
distinction via `MECHANISM_IS_MISCONCEPTION` (6 of 9 mechanisms). Routing derives from the
mechanism, the facet knowledge state (`facet_state_label`), and source exposure
(`source_exposure_events`, ING §14) — but intake is **three queues, not one**, and a
mechanism classification alone never mints a case:

1. **Repair** — a **durable registry misconception** (`active`/`resolving` row) only.
   A one-off graded error whose mechanism has `is_misconception = true` is *evidence
   toward promotion* under the KM4 promotion discipline, never a committed statement-pair
   case by itself. Committing a case on one observation contradicts the registry's own
   epistemics.
2. **Diagnose** — an unresolved-cause state (the §4.7 "consistent with N causes" card) or
   the analytics signal `repeated_failure_despite_coverage` (a notice kind in
   `source_outcome_analytics`: exposure event exists AND repeated failure). The route is
   a short diagnostic (probe episode), not a repair.
3. **Read first** — `unexamined` facets with no exposure event. Content intake, not
   repair; mixing them into either queue misassigns blame.

Mechanism → treatment preference (within Repair):

| mechanism | treatment preference |
|---|---|
| `conceptual_schema_error`, `condition_assumption_error` | disambiguating passages (target + confused-with) then retry |
| `procedure_execution_error`, `selection_planning_error` | **worked example / contrast items over re-reading** — procedure and selection errors rarely dissolve by reading |
| `representation_notation_error` | notation-mapped passages (notation_mappings) |
| `transfer_context_error` | contrast/transfer items; re-read last |
| `retrieval_failure` (not misconception) | **practice, not re-reading**; scheduled retrieval |
| `local_slip` | no remediation; volume signal only (severity 0.15) |
| `assessment_ambiguity` | item review — routes to registry/authoring, invisible to the learner's queues |

Legacy five-vault error types route through `map_legacy_error_type` first.

## 4. Surfaces — walking the loop

### 4.1 Today / Sit down: "Will I be ready?" — two aligned lanes

Demonstrated coverage and predicted recall are different quantities; they get **two
compact, time-aligned lanes**, never one axis (the shipped GoalBanner already separates
these encodings — the two-line chart would have re-blended them):

- **Demonstrated lane**: step line of capability-matched certification credit ("12/20
  facets"), from goal report checkpoints (`get_goal_report_series`). Non-monotone;
  corrections render as visible steps down.
- **Ready lane**: historical predicted-recall estimate, plus the dotted **do-nothing
  line** — FSRS retrievability decay projected to the due date. This replaces the
  trailing-4-point least-squares fit (`linearFit()`), which is deleted; four noisy points
  extrapolated linearly is fabricated trend. Target-recall reference line and due-date
  tick live in this lane only (the target has no meaning for the Demonstrated lane).
- **Model coverage disclosure**: `goal_projection` holds facets flat when they carry no
  FSRS information ("no decay information is not the same as no decay"). The lane says
  so: *"decay estimated from 8 of 12 facets; 4 held flat — not enough history."*
- **This is a backend delta, not a frontend swap** (§6.4): `GoalSeriesPointDto` carries
  no FSRS data today.
- **No "if you follow the plan" line at launch.** It appears only when the forecast
  ledger has a backtest behind it.

Rendered forecasts **reference issued forecast rows** (§6.3); rendering never writes one.

### 4.2 Today: "How much more practice do I need?"

One sentence under the hero:

> **≈ {attempts_remaining} qualifying attempts outstanding**{", at least" when partial}
> — at your recent goal pace of {pace}/day that's ~{days} days; the due date allows
> {days_left}. {on_pace ? "On pace." : "Behind pace — {needed_per_day}/day needed."}

Rules:

- **Qualifying pace, honestly computed.** The numerator uses the same eligibility
  semantics as the denominator: goal-scoped attempts only, qualification-compatible
  (unassisted / capable of advancing the certification debt), window clipped to days the
  goal existed. (Track 0 bug: `compute_goal_pace` currently counts every vault attempt in
  14 days against goal-scoped remaining work — an unrelated subject makes any goal look
  on pace. The scoped primitive already exists in the same function.) Until the numerator
  is qualified, the copy must say "recent activity," never "qualifying pace."
- Edge states are explicit: zero recent pace ("no goal practice in 14 days — no pace to
  project"), passed due date, partial/unknowable remaining work (`attempts_remaining`
  None). The `_ASSUMED_FRESH_DISCOUNT` inversion is approximate: say "roughly N", and
  never render a precise completion date when recent goal activity is zero or sparse.
- **Planning override** (the `forecast` claim's structured response): "use my usual {n}
  study days/week" — recompute the sentence under the learner's scenario, labeled as
  theirs, logged to the ledger like any forecast.
- Facets with `attempts_to_certify = None` are excluded from the debt and called out:
  "{n} facets have no practice items yet" → coverage bar (§4.11). System debt.
- Days, not minutes — no time-cost model exists and none is invented.

### 4.3 Today: "What should I do now?"

The queue, with an honest **reason column** from the dominant term of the scheduler's
per-item `components` map (already serialized to the frontend). The dominant reason is
computed **server-side** (§6.9) so Tauri, TUI, and the claim's stored value all record
the same reason the learner saw — a client-derived argmax the backend can't reproduce
would poison the response telemetry. Each reason is a `schedule_choice` claim with the
§2.1 structured reasons. This is the feedback stream the decision-inert scheduler weights
need: these responses are the first real-world signal that could justify re-weighting.

The session-narrative line (`TodayScreen.tsx`) anchors the **overconfidence list**:
at-risk facets where `ready` is high and `demonstrated` is false, sorted by ready ×
blueprint weight, gated on minimum evidence mass (cold-start noise guard). One tap starts
a probe; `origin = 'overconfidence_list'` so analytics can separate adversarial selection
from drift.

Below the queue: last session's diff (§4.8), three lines, linking to Log.

### 4.4 Today: the welcome-back diff

When `now - last session end` > 7 days, Today opens with a re-entry panel *before* the
forecast, ordered survival-first:

> Still solid: {n} facets. Slipped below target while you were away: {m} — {top 3 by
> weight}. Your best next session: {k} refreshers.

Same FSRS data, deliberately ordered to prevent the guilt spiral. Never leads with
losses; never mentions the streak.

### 4.5 Today: no-goal and fresh-vault fallbacks

- **No goal, has history**: the hero slot is **decay pressure** — facets whose
  retrievability crosses the target threshold soonest, as a list with a **"crosses
  target in ~N days"** column. Facets held flat for lack of FSRS history are excluded
  from confident copy (they get "not enough history"). No per-facet decay sparklines —
  near-identical exponentials convey nothing the number doesn't.
- **Fresh vault (no goal, no FSRS history)**: decay pressure cannot exist. Offer three
  real actions: read first (§3 queue), set a goal, or run a short diagnostic.

### 4.6 Practice: the calibration duel (launch scope)

After the learner has **composed an answer, before submit/reveal**, one optional tap:
**"How likely is this answer to be correct?"** — predicting their own composed answer,
not the prompt. Implementation:

- **Reuse the `answer_confidence` 1–5 selector** (migration 031, already in the probe
  banner) — the vault has three confidence scales; the duel must not mint a fourth.
- **Explicit probability mapping at consumption time** (not storage): 1→0.10, 2→0.30,
  3→0.50, 4→0.70, 5→0.90. Stored taps stay 1–5 so the mapping can be recalibrated later.
- The duel compares learner vs. model **only on matched attempts: unassisted, unprimed**,
  where both made a pre-outcome prediction. Two Brier scores, rendered in the track
  record (§4.12).
- Skippable, never gates submission, absence unscored.

### 4.7 Feedback: the wrong belief, evidence-bound

When a graded error event matches an active registry misconception, render the statement
card beside `AttemptTraceView`:

> Your last answer was consistent with confusing **{X}** and **{Y}**. The distinction to
> use here: *{authored correction}*.

Rules:

- The copy states the **evidence relation** (a signature match on error events), not a
  belief attribution — it is both gentler and more accurate than "you appear to believe."
  The registry keeps its crisp internal statement; the render changes, the stored claim
  does not.
- **The correction is authored, not derived.** "Derived from canonical content" at render
  time is generation wearing a deterministic costume (§1.5). Migration 047 has no
  correction column: a provenance-backed `correction_statement` is authored at registry
  promotion time (§6.2) and validated like any content. The card is blocked on this
  delta, deliberately.
- **Never show the misconception naked** (myth-repetition): the correction is always in
  the same visual unit. This rule applies everywhere the statement renders, including
  Log's cold cards (§4.9).
- **Card hierarchy:** a matched statement card *replaces* `UnresolvedCauseCard` for that
  attempt; "consistent with N causes" shows only when no committed hypothesis matched.
  Two cards asserting different diagnoses in the same moment is trust poison.
- Full `diagnosis` affordances (§2.1), `temperature = 'hot'`; rejections enter the §2.3
  cold re-ask.
- If the mechanism routes to Repair (§3), the card carries **"repair this"** → §4.10.

### 4.8 Finish: the session diff

`SessionEndSummary` (today: `attemptsRecorded, itemsReviewed, followupsQueued, streak`)
gains learning fields:

```
facets_demonstrated: int                 -- new certification credit this session
predictions_moved: {up, down}            -- counts past a materiality threshold; NO net
                                         -- (+6/−6 netting to 0 hides everything)
corrections: int                         -- regrades applied, either direction
misconceptions_touched: {resolved, returned}
```

`SessionFinishHud` renders at most three lines — end-of-session is a low-energy moment.
Full diff in Log. Corrections always included when nonzero; a session that only regraded
downward still reports honestly.

### 4.9 Log / Review (tab 8, replaces the Errors placeholder)

The changelog of your knowledge. Two sections:

1. **Changelog** (spine): reverse-chronological — what was demonstrated, which
   predictions moved, what was corrected. Non-monotone events annotated, never smoothed.
   **Includes system-authored entries** for model events outside sessions: regrades
   applied by maintenance, and recalculations. An `algorithm_version` bump collapses to
   **one** entry ("recalibration: estimates recomputed — your evidence unchanged"), never
   a per-facet flood the learner appears to have caused.
2. **Working hypotheses** (standing state): what's shaky now (overconfident facets,
   fastest-decaying), and active misconception statements as cold `diagnosis` claims —
   this is where §2.3 re-asks surface (≤1 per visit), **each with its correction
   attached** (§4.7 rule) and a "repair this" action.

Every facet reference opens `FacetEvidenceDrawer` (currently an orphan; Log is its first
consumer, KnowledgeMapScreen its second). The drawer is the receipt (§5) — see the
exactness blocker there before wiring it everywhere.

**Empty state** (fresh vault): changelog suppressed; working hypotheses render alone with
one line on what appears after the first session. First impressions are where §1's trust
argument is won or lost.

### 4.10 Repair (a flow, not a tab)

No permanent Doctor tab: ten tabs already exist, a queue that is frequently empty doesn't
earn navigation, and "Doctor" both pathologizes learner error and collides with the
codebase's system-health doctor (`learnloop doctor`, `facet_doctor`). Repair launches as
a **detail flow** from Log's working hypotheses, Feedback's "repair this," and Today
cards. Tab 9 is freed.

The learner sees **one compact sequence**: compare the two ideas → open the source → try
a related item now → an unassisted retry gets scheduled. The four stages remain the
**recorded backend structure** — §7.2's telemetry depends on the stage boundaries even
though the learner never sees a pipeline:

1. **Diagnosis.** Intake per §3 (Repair queue only). Cases ranked by blueprint weight ×
   recurrence; each shows the §4.7 statement pair and mechanism.
2. **Prescription.** Exact canonical passages via a thin resolver composing
   `get_entity_provenance` with `build_span_view`. **Fetch spans for both `target_facet`
   and `confused_with_facet`** (both persisted, migration 047) — a misconception is a
   confusion between two things; reading only the target often fails to dissolve it.
   Treatment medium varies by mechanism (§3 table): worked examples/contrast items for
   procedure/selection errors, not re-reading. Reading writes a `source_exposure_event`
   with context `remediation`, keyed to the misconception id — recorded as exposure, not
   proof of reading.
3. **Treatment.** One tap into a primed attempt. This is a **parallel intake path** to
   `start_primed_retry`, not a parameter tweak: the existing handler keys everything off
   `attempt_id`; the reusable core is the sibling picker (already prefers
   `need.target_facets`).
4. **Follow-up.** A scheduled **cold retry** — delayed (next session ≥1 day), unprimed,
   unassisted. Required by existing epistemics: mastery already refuses to advance the
   cold anchor on primed evidence, so without it, remediation can never convert to
   Demonstrated credit.

**Backend model (§6.6) — cold_retry is not a follow-up string.** Current follow-ups are
action strings on `attempt_surprise` consumed by the scheduler as soon as any later
attempt exists; "≥1 day later" is *inexpressible* in that storage. Two tables:

- `remediation_episodes`: case (misconception/diagnosis ref), passages shown, primed
  attempt, cold attempt, state. This is §7.2's telemetry given a primary key.
- `followup_tasks`: kind (`cold_retry` first), case/source identity, `not_before`,
  expiry, status, selected item, consumed attempt.

Status chips come from **misconception transition events** (§6.2), including
**"returned"** — the current update path wipes `resolved_at` on reactivation
(`repositories.py`: "any reactivation clears it"), so relapse is historically
unrecoverable from state alone. Relapse rendered, not hidden.

Cold retry generalizes beyond repair: any assisted evidence channel — `hinted` /
`scaffolded` / `answer_exposed` (`capability_mapping.ASSISTED_CHANNELS`; `primed` is an
orthogonal flag, not a channel) — may schedule one. Assisted→cold conversion is the
Demonstrated lane's growth engine.

### 4.11 Coverage (three-bucket bar)

Per source set, facet counts in three buckets with **explicit precedence** (pooled or
embedded evidence can demonstrate a facet that has no local practice supply, so buckets
must not be computed independently): demonstrated (from any evidence) ≻ assessed-but-not
≻ **no-practice-supply** (`attempts_to_certify = None` + source_coverage's
teaching-without-assessment classes). Rendered with the existing `SegmentBar` — a treemap
earns its complexity at dozens of leaves; three buckets don't. The third bucket is
visually distinct, labeled as the system's debt, and **actionable**: "create/review
practice items" → generation/review flow. Placement: Library (per-source) + the §4.2
content-gap link. Small rollup service over `source_coverage` + goal report.

### 4.12 Track record — two views, not one

One tap from the forecast hero. **Exam calibration and forecast performance are different
things and get separate sections:**

1. **Answer calibration** (from `exam_calibration.py`): pooled Brier + sample count,
   plain-language until a minimum N ("23 predictions so far — too few for a curve").
   No per-bin Brier and no 10-bin curve at this data volume; a confident curve through
   three samples is the dishonesty this surface exists to prevent. The reliability curve
   appears only past minimum N, sparse bins grayed and excluded.
   Beside it, the **duel** (§4.6): learner Brier vs. model Brier on matched attempts.
2. **Forecast track record** (from the §6.3 ledger): per forecast kind — issued,
   resolved, censored, unobservable; accuracy on the resolved subset only. The pace
   sentence and decay line accumulate separate records.

Badly calibrated is displayed as plainly as well calibrated; the learner deserves to know
what to discount.

### 4.13 Accessibility

Charts and status encodings carry text equivalents (the two-lane hero has a one-sentence
text summary); all claim responses are keyboard-reachable; state is never encoded by
color alone (the amber-mono aesthetic makes this easy to violate) — patterns, labels, or
glyphs accompany color; screen-reader summaries for the hero, queue reasons, and session
diff.

## 5. The receipt

### 5.1 Scope

Receipts attach to **consequential model-derived claims only**: Ready, Demonstrated,
forecasts, misconception diagnoses, schedule selections. Ordinary counts, dates, and
session totals do not get derivation drawers — "every number everywhere" was an unbounded
plumbing commitment.

For a covered number: its derivation. "Ready 0.82 — 3 direct observations (2 unassisted),
1 pooled from {parent facet}, decayed 11 days," plus cross-links. Rendered by
`FacetEvidenceDrawer` + the evidence scrubber: each observation a tick (direct / pooled /
assisted; corrections marked), tap-through to the attempt.

### 5.2 The exactness blocker

**The trust anchor cannot be approximate while claiming exactness.** Today the timeline
service documents its magnitude as an "upper-ish bound" (per-group caps and the
attempt-wide ceiling are not reproduced — `facet_evidence_timeline.py` design notes)
while the UI copy says "exact fold over the immutable ledger" (`KnowledgeModel.tsx:372`).
That discrepancy is a Track-0 copy fix; the structural fix is §6.5: one **shared
authoritative contribution calculator** (the KM2 canonical projection math) used by both
the projection and the timeline, including caps, correlation rules, and corrections.

Phasing: ship the **Demonstrated drawer** first (exact after §6.5), with Log as first
consumer; Ready derivation (pooling, decay factors, version segments) is a separate
backend phase. The sidecar endpoint today returns only the Demonstrated series and
cross-links — the full §5.1 payload does not exist yet, and no sequencing may call it
"mostly assembly."

### 5.3 Generation rule

Receipt facts are **template-rendered, deterministically, from the ledger.** Launch ships
template-only: no generative smoothing, no validation machinery. (Reserved for later,
only if templates prove unreadable: generative connective prose under verbatim-copy
validation with raw-template fallback — the receipt is the one place a hallucinated token
is unrecoverable.)

## 6. Backend deltas

**Track 0 — bug fixes, immediately and independently of everything below:**

- Goal-scoped, qualifying pace numerator (`compute_goal_pace` currently counts every
  vault attempt; `attempt_count_for_learning_objects` shows the scoped shape).
- `KnowledgeModel.tsx:372` copy fix: the drawer must not claim "exact fold" over an
  upper-ish bound.
- `session_attempt_counts` switches from the time-window join to
  `practice_attempts.session_id` (column exists since migration 010, unused) —
  overlapping/abandoned sessions corrupt the diff otherwise.

**Ordered by dependency:**

1. **Claim contract** (§2.2): `hypothesis_events` with presentation/response linkage,
   claim versioning, producer versions, `visible_at`, suppression, visit_id; the §2.4
   dispatcher; the §2.5 privacy boundary (opt-in export, inspect, delete).
2. **Misconception registry deltas**: transition events table (so `returned` is
   historically recoverable — reactivation currently wipes `resolved_at`); authored
   `correction_statement` (provenance-backed) written at promotion time; the §3 intake
   gate (durable row required for Repair).
3. **Forecast ledger**: forecasts are **issued idempotently** — one row per goal / kind /
   as-of snapshot / material input change, never per render; presentations reference the
   forecast id. Frozen per row: input snapshot hash, algorithm + resolution-rule
   versions, horizon, exact target metric, model coverage. Status: `resolved` |
   `censored` | `unobservable`. **Resolution uses reality only**: cold outcomes and exam
   evidence. A do-nothing forecast is **censored** when the learner practiced the scoped
   facets in the interval — grading it against post-intervention state systematically
   punishes exactly the learners who follow the plan. Comparing a projection to a later
   model estimate is *projection drift*, reported as such, never as forecast accuracy.
4. **Decay-projection series** on the goal report/series: per-day projected mean to the
   due date + model-coverage counts (estimated vs. held-flat facets), from the
   `goal_projection.py` retention-ratio machinery. `GoalSeriesPointDto` has no FSRS data
   today; §4.1 is blocked on this. The same helper feeds §4.4 and §4.5.
5. **Shared receipt calculator** (§5.2): one authoritative contribution function for
   projection and timeline.
6. **Remediation model** (§4.10): `remediation_episodes` + `followup_tasks`
   (`cold_retry` first kind, `not_before`/expiry/status/consumed-attempt) — the current
   follow-up storage (action strings on `attempt_surprise`) cannot express a delayed
   task. Plus the misconception→span resolver (compose `get_entity_provenance` +
   `build_span_view`; no new data) and the `remediation` exposure context
   (migration-052 CHECK extension).
7. **Coverage rollup** with bucket precedence (§4.11).
8. **Duel storage** (§4.6): pre-reveal `answer_confidence` capture on ordinary attempts +
   the model's frozen prediction per attempt; mapping to probabilities at consumption.
9. **Read-side additions**: server-computed dominant scheduler reason on serialized queue
   items (ranking logic exists for plain-English output); minimum-N gating in
   calibration views.
10. **Frontend wiring**: two-lane hero; typed claim shell + dispatcher; FacetEvidenceDrawer
    consumers; Feedback card hierarchy; Log/Review tab + empty states; Repair flow;
    coverage bar CTA.

## 7. What the telemetry is

### 7.1 Feedback signals
Every claim response is a signal: (system claim, claim version, learner response,
hot/cold, presentation context). **Signals, not labels** — a learner's "too low" is
another prediction, a schedule dispute is a preference, a diagnosis denial is self-report.
Raw signals are preserved; interpretation is stratified at analysis time.

### 7.2 Longitudinal intervention–outcome data
Repair episodes emit complete trajectories: misconception → prescribed spans exposed
(exposure ≠ proof of reading) → primed outcome → cold outcome → resolved/returned. This
is **longitudinal intervention-outcome data, not natural experiments** — remediation is
self-selected and uncontrolled. It is still the only honest path toward ever drawing the
"if you follow the plan" line, and it is the strongest data this system will collect.

### 7.3 Graded forecasts
Every issued forecast eventually resolves, censors, or is marked unobservable (§6.3).
Track records accrue from issuance day one — they cannot be backfilled — even though the
grading and display ship later. A ledger that only writes and never resolves is the
fabricated-precision failure mode wearing a schema.

## 8. Sequencing — parallel tracks, not a serial gate

**Track 0** (now): the three bug fixes. None depends on anything below.

1. **Contracts**: claim/presentation/response schema + privacy boundary + dispatcher;
   misconception transition events + authored corrections + intake gate. Trustable data
   before surfaces that expose it.
2. **Receipt + Log/Review**: shared calculator, exact Demonstrated drawer, changelog
   spine (needs only Track 0's session join + transition events — starts in parallel
   with the calculator work).
3. **Feedback vertical slice**: typed misconception card (§4.7 copy, authored
   correction, request-review path) **+ the duel** (§4.6 — in launch scope: it is a
   selector move plus one storage delta, and it seeds §4.12's matched-attempt data from
   day one).
4. **Sit-down**: two-lane hero (after §6.4), qualified pace sentence, forecast issuance.
5. **Reason column + overconfidence drill-down**: kept early deliberately — every live
   session accrues `schedule_choice` signal against the decision-inert scheduler
   weights; data the weights are not currently earning.
6. **Repair**: episodes + tasks + resolver + cold_retry + three-way intake.
7. **Ambient**: coverage bar, welcome-back, fresh-vault fallback, track-record views
   (calibration view gated on minimum N).
