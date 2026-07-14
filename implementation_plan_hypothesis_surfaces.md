# Implementation Plan: Hypothesis Surfaces (spec_hypothesis_surfaces.md v3)

Audience: an engineer who has **never seen this repository**. Read Part 1 before touching
anything. The normative contract is `spec_hypothesis_surfaces.md` (draft v3, 2026-07-14);
this plan tells you where everything lives, what order to build in, and which existing
behaviors will bite you. Companion background: `spec_knowledge_model.md` (§9.5 dual-axis,
§9.6 UI, §10 error taxonomy), `spec_misconception_diagnostics.md`,
`implementation_plan_km_ingestion_v2.md` Part 1 (fuller orientation; this one is
condensed).

---

## Part 1 — Orientation

### 1.1 What LearnLoop is

A local-first adaptive learning app. A user's data lives in a **vault**: a directory of
YAML/Markdown files (subjects, concepts, Learning Objects, Practice Items, rubrics,
goals) plus one SQLite database (`state.sqlite`) holding derived learner state and event
history. No server; AI features call a local Codex runtime through a typed client.

```
apps/learnloop-tauri/          React + TypeScript UI (terminal aesthetic, amber/mono), Tauri shell
  src/screens/*.tsx            one file per screen (TodayScreen, PracticeScreen, FeedbackScreen, ...)
  src/components/*.tsx         shared components (ui.tsx = primitives incl. the tab bar & SegmentBar)
  src/api/client.ts, dto.ts    typed RPC client + DTO definitions (camelCase)
  src-tauri/src/commands.rs    Rust proxy commands → Python sidecar

src/learnloop_sidecar/         JSON-RPC sidecar (Python)
  handlers/*.py                one module per feature area; thin: parse → service → serialize
                               methods declared with @method("name", InputModel)
  handlers/serializers.py      scheduled-item serialization (queue + components)

src/learnloop/                 the product (Python)
  services/*.py                ALL business logic (~60 modules)
  db/repositories.py           ALL SQL (one large module; no SQL anywhere else)
  vault/                       YAML loaders/models (ruamel.yaml, pydantic v2)
  cli.py                       Typer CLI; CLI and sidecar call the SAME services
  config.py                    embedded default TOML + pydantic models; per-vault learnloop.toml

migrations/NNN_*.sql           sequential SQLite migrations. 001–054 exist. THIS PLAN
                               PRE-ASSIGNS 055–058 (see packages). Run `ls migrations/`
                               before creating one — collisions with parallel work happen.
fixtures/                      small real vaults used by tests (linear_algebra, arxiv, law, ...)
tests/                         1,400+ pytest tests; deterministic, no network, FrozenClock
```

Verify everything with: `python -m pytest -q` (full suite), `npx tsc --noEmit` (in
`apps/learnloop-tauri`), `cargo check` (in `apps/learnloop-tauri/src-tauri`).

### 1.2 The wiring chain (memorize — every feature walks it)

A feature is not done when the service works. The full chain:

```
services/foo.py  →  db/repositories.py (if SQL)  →  learnloop_sidecar/handlers/foo.py (@method)
  →  src-tauri/src/commands.rs (Rust proxy + capability)  →  src/api/dto.ts + client.ts  →  screen
```

- New Rust commands require a **full app restart**, not a Vite reload. `client.ts`
  surfaces this as `stale_app_binary`. You will forget this once; budget for it.
- `versioned()` in the sidecar **camelizes payloads recursively**. Never re-attach a
  snake_case dict to a payload after calling it.
- CLI parity: substantial read models should also get a Typer command in `cli.py`
  (pattern: every service in the last release has one).

### 1.3 Invariants you must not break

1. **Evidence, not mastery.** No code writes belief state directly. All belief change
   flows through `apply_attempt` (`services/attempts.py`). Nothing in this spec grades or
   writes mastery — claim responses, forecasts, and remediation records are *side
   tables*. If you find yourself touching a belief row, stop.
2. **Replay determinism.** `rebuild_derived_state` must reproduce derived state
   byte-identically from event history. Time goes through `clock.py` (FrozenClock in
   tests). Anything algorithm-dependent is stamped `algorithm_version` (currently
   `mvp-0.7`). New tables in this plan are **outside replay** (presentation/response
   telemetry, forecasts, episodes) — keep them that way; replay must never read them.
3. **Migrations are append-only**, and SQLite `CHECK` constraints can't be altered in
   place — extending one means CREATE new → copy → drop → rename (see `migrations/002`
   for the pattern). This plan hits that twice (B6).
4. **Attempt results are frozen dataclasses** — extend via `dataclasses.replace`, not
   mutation.
5. **Deterministic core** (spec §1.5): every number/citation the learner sees is
   template-rendered from ledger or authored content. No LLM output at render time.

### 1.4 Domain glossary (enough to read the spec)

- **LO** (Learning Object): a study-map node; owns Practice Items.
- **Facet**: the atomic knowledge claim; canonical, shared across LOs (mvp-0.7).
  **Capability**: observation dimension (retrieval/schema/procedure/selection/transfer).
- **Demonstrated**: banked certification credit — direct, unassisted, capability-matched
  evidence only. **Ready**: pooled *prediction* of recall. Never blended (spec §1.1).
- **Evidence mass / certification credit**: per-attempt pseudo-mass allocated to facets;
  the math lives in `services/canonical_projection.py` + `services/capability_mapping.py`
  (`ASSISTED_CHANNELS = {hinted, scaffolded, answer_exposed}`; `primed` is a separate
  flag).
- **FSRS**: the forgetting model; per practice item (`stability`), *not* per facet. Facet
  decay is projected via supporting items (`services/goal_projection.py`).
- **Misconception registry**: durable rows (`active/resolving/resolved`) with statements
  and target/confused-with facets (migration 047); promotion discipline in
  `services/misconceptions.py`.
- **Claim surface**: spec §2 — a rendered system belief with class-typed response
  affordances. The spec's central primitive.

### 1.5 Verified current-state facts this plan is built on

Each was verified against the tree on 2026-07-14. They are the *reasons* for the shape of
the work packages — read them before arguing with a package.

| # | Fact | Where |
|---|------|-------|
| 1 | Pace numerator counts **every vault attempt** in 14d; denominator is goal-scoped. Live bug in shipped GoalBanner. | `services/goal_pace.py:58` (`daily_attempt_counts`); scoped primitive exists at `:80` |
| 2 | Drawer UI claims "exact fold over the immutable ledger"; the service documents an "upper-ish bound" (caps not reproduced). | `components/KnowledgeModel.tsx:372` vs `services/facet_evidence_timeline.py` design notes |
| 3 | `session_attempt_counts` joins by time window; `practice_attempts.session_id` exists (migration 010) but is unused. | `db/repositories.py:5834` |
| 4 | Follow-ups are action strings on `attempt_surprise`; the scheduler consumes them as soon as any later attempt exists. No `not_before`, no status. A "≥1 day later" cold retry is **inexpressible**. | `db/repositories.py` `_queued_followup_action`, `pending_followup_practice_items` |
| 5 | `update_misconception` **wipes `resolved_at` on reactivation** ("any reactivation clears it"), so relapse is historically unrecoverable from state. | `db/repositories.py:1332` |
| 6 | Migration 047 has `statement`/`statement_normalized`, **no correction column**. | `migrations/047_compositional_misconceptions.sql` |
| 7 | `GoalSeriesPointDto` has **no FSRS/decay data**; the chart linearly extrapolates the last ≤4 points (`linearFit()`). | `dto.ts:2110`, `GoalTrajectoryChart.tsx:19,87` |
| 8 | `goal_projection` **holds facets flat** when no FSRS info exists (documented deliberately). | `services/goal_projection.py` module docstring |
| 9 | Scheduler per-item `components` dict is already serialized to the frontend; there is **no dominant-reason field** (ranking helpers exist server-side). | `handlers/serializers.py:34,58,72`; `scheduler.py:641,960` |
| 10 | `exam_calibration` computes **pooled** Brier; bins carry means + count only. | `services/exam_calibration.py` |
| 11 | `exam_predictions` (migration 024) is a working frozen-prediction ledger graded by `exam_calibration` — the pattern B3 copies. | `services/exam_session.py` |
| 12 | `FacetEvidenceDrawer` is an orphan (defined, zero consumers, backend already wired). Tabs 8 ("errors") and 9 ("doctor") render a spinner placeholder. | `KnowledgeModel.tsx:322`; `ui.tsx:5-16`; `App.tsx:535` |
| 13 | `answer_confidence` 1–5 exists on `practice_attempts` (migration 031) with a selector in the probe banner. Two other confidence fields exist; do not add a fourth scale. | migration 031; PracticeScreen probe banner |
| 14 | FeedbackScreen renders `AttemptTraceView` then `UnresolvedCauseCard` ("consistent with N causes"). | `FeedbackScreen.tsx:1176-1191` |

### 1.6 Dependency spine

```
Track 0 (bug fixes — start immediately, independent of everything)
   │
B1 claim contract ──────────────┬→ F1 claim shell ─┬→ F3 Feedback slice + duel (needs B2, B8)
B2 registry deltas ─────────────┤                  │
B3 forecast ledger ─────────────┼→ F4 two-lane hero + pace (needs B4)
B4 decay-projection series ─────┤
B5 shared receipt calculator ───┼→ F2 Log/Review + drawer (changelog spine needs only Track 0 + B2)
B6 remediation model ───────────┼→ F6 Repair flow
B7 coverage rollup ─────────────┼→ F7 ambient surfaces
B8 duel storage ────────────────┤
B9 read-side additions ─────────┴→ F5 reason column (small; ship early — spec §8.5)
```

Parallel tracks, not a serial gate: Track 0, B1–B2, and B5 can run concurrently. F2's
changelog spine does not wait for B5 — only drawer-everywhere wiring does.

---

## Part 2 — Backend packages

Migration pre-assignments: **055** (B1), **056** (B2), **057** (B3), **058** (B6). B6
additionally rebuilds two CHECK constraints. Check `ls migrations/` first; renumber all
downstream references if taken.

### Track 0 — bug fixes (days; no new schema)

1. **Goal-scoped qualifying pace.** `compute_goal_pace` numerator must count only
   attempts on the goal's scope LOs (add a windowed variant of
   `attempt_count_for_learning_objects` to `repositories.py`), clip the window to days
   the goal existed, and (second step) apply qualification semantics matching the
   denominator (unassisted / certification-capable — reuse `ASSISTED_CHANNELS`). Until
   qualification lands, the DTO gains `pace_kind: "activity" | "qualifying"` so the UI
   can label honestly (spec §4.2).
   *Acceptance*: test where heavy practice on an out-of-scope LO leaves `on_pace`
   unchanged; existing `goal_pace` tests updated, full suite green.
2. **Drawer copy fix.** `KnowledgeModel.tsx:372`: replace "exact fold…" with honest copy
   ("evidence shape is exact; magnitude is an upper bound until §B5 lands").
3. **Session join fix.** `session_attempt_counts` (`repositories.py:5834`) switches to
   `WHERE session_id = ?` with a time-window fallback only for legacy rows (session_id
   NULL). *Acceptance*: test with two overlapping sessions attributing attempts
   correctly.

### B1 — Claim contract (migration 055; spec §2)

**New**: `migrations/055_hypothesis_events.sql` exactly per spec §2.2 (append-only; both
event and presentation rows live here, `presentation_id` self-referential for
responses). `services/hypothesis_claims.py`: `present_claims(...)` (dispatcher: budget 2,
one slot reserved for `temperature='hot'`, per-claim cooldown from config
`[hypothesis].session_card_budget` / `claim_cooldown_days`, priority order per §2.4,
returns which claims get affordances vs. suppressed + `suppression_reason`),
`record_response(presentation_id, payload)`, debounce by
`(claim_ref, claim_version, surface, session_id|visit_id)`.
**Sidecar**: `handlers/claims.py` — `present_claims`, `respond_claim`,
`dismiss_claim`. `visible_at` is supplied by the frontend (F1) at viewport exposure,
patched onto the presentation row.
**Privacy** (§2.5): CLI `learnloop claims export|purge` + sidecar equivalents; no
network anywhere.
*Pitfalls*: replay must never read this table; `visit_id` is minted by the frontend for
Today/Log browsing outside practice sessions — don't reuse `session_id`.
*Acceptance*: unit tests for budget/reservation/cooldown/debounce; sidecar contract test
(`tests/test_sidecar_contract.py` pattern); a changed `claim_version` re-presents within
one session.

### B2 — Misconception registry deltas (migration 056; spec §3, §4.7, §4.10)

**Schema**: `misconception_transition_events` (id, misconception_id, from_status,
to_status, at, source — so "returned" is derivable forever) + `correction_statement`
TEXT NULL and `correction_source_span_ids_json` on `misconceptions`.
**Write paths**: `repositories.update_misconception` and
`services/misconceptions.resolve_or_reactivate_by_posterior` emit a transition row on
every status change (fact 5: `resolved_at` wipe stays, the event log compensates).
**Authoring**: the promotion path in `services/misconceptions.py` authors
`correction_statement` (provenance-backed, from target-facet canonical content) at
promotion time via the existing proposal/review machinery — never at render time.
Existing rows: backfill `correction_statement = NULL`; the F3 card **does not render**
statement-pair copy for rows without one (falls back to the unresolved-cause card).
**Intake gate**: new `services/remediation_intake.py` — `classify_intake(...) →
'repair' | 'diagnose' | 'read_first'` per spec §3 (repair requires a durable
active/resolving row; a lone `is_misconception=true` mechanism event is promotion
evidence, not a case).
*Acceptance*: reactivation test asserting `returned` is derivable from events; intake
unit tests for all three routes incl. the one-off-error negative case.

### B3 — Forecast ledger (migration 057; spec §6.3)

Copy the shape of `exam_predictions` (fact 11). Table `forecasts`: id, goal_id, kind
(`decay|pace|plan`), issued_at, as_of input snapshot hash, algorithm + resolution-rule
versions, horizon, target metric, predicted value, model-coverage json, status
(`open|resolved|censored|unobservable`), resolved value/at.
`services/forecast_ledger.py`: `issue_forecast(...)` idempotent on (goal, kind,
input-snapshot hash); `resolve_due_forecasts(...)` called from session start and the
maintenance feed — **censor** when scoped facets received practice in the interval;
resolve only against cold outcomes/exam evidence; comparisons against later model
estimates are stored as `projection_drift`, a separate field, never accuracy.
Presentations (B1) reference `forecast_id` in `claim_ref`.
*Acceptance*: idempotency test (same snapshot → one row); censoring test (practice in
interval → censored, not wrong); pace forecast resolves on first session past horizon.

### B4 — Decay-projection series (no new table; spec §4.1)

Extend `services/goal_projection.py` / `goal_series.py`: per-day projected mean recall
from today to due date (reuse the retention-ratio machinery + `fsrs.forgetting_curve`),
plus coverage counts `{decay_estimated: n, held_flat: m}` (fact 8). Thread through
`handlers/goals.py` and `GoalSeriesPointDto`/report DTO.
*Pitfall*: the goal series sidecar cache keys on a payload version — **bump
`_SERIES_PAYLOAD_VERSION`** or stale cached series will miss the new fields.
*Acceptance*: projection is monotone non-increasing for decay-only facets; held-flat
facets excluded from the curve but counted; golden test on a fixture vault.

### B5 — Shared receipt calculator (no new table; spec §5.2)

Extract the authoritative per-observation contribution math (caps, correlation-group
budgets, attempt ceiling, corrections) from `services/canonical_projection.py` into a
pure shared function; make `services/facet_evidence_timeline.py` fold with it.
*Acceptance*: **the timeline's final value equals the banked ledger credit exactly** on
every fixture vault (this is the test that retires fact 2); from-scratch == incremental
fold stays byte-identical. Phase 2 (separate, after F2 ships): extend the timeline
handler payload with per-observation derivation + Ready derivation for the full §5.1
receipt — the current endpoint returns only the Demonstrated series + cross-links.

### B6 — Remediation model (migration 058 + 2 CHECK rebuilds; spec §4.10)

**Schema**: `remediation_episodes` (id, case ref = misconception_id | diagnosis ref,
state, passages_shown_json, primed_attempt_id, cold_attempt_id, timestamps);
`followup_tasks` (id, kind — `cold_retry` first —, case/source identity, `not_before`,
expires_at, status `pending|served|consumed|expired`, selected_item_id,
consumed_attempt_id).
**CHECK rebuilds** (invariant 3, migration-002 dance): `source_exposure_events.context`
gains `remediation`; any CHECK on followup-bearing tables you touch.
**Services**: `services/remediation.py` — episode lifecycle; span prescription via
`get_entity_provenance` ∘ `build_span_view` for **both** target and confused-with facets
(migration 047 has both ids); treatment entry as a **parallel intake path** beside
`start_primed_retry` (`handlers/feedback.py` keys everything off `attempt_id`; reuse the
sibling picker, which already prefers `need.target_facets`); `cold_retry` scheduling
into `followup_tasks`.
**Scheduler**: consume `followup_tasks` where `status='pending' AND not_before <= now`
(new branch beside the legacy action-string path, which stays for old rows); mark
`consumed` when the attempt lands, linking `consumed_attempt_id`.
*Acceptance*: a cold retry scheduled today is **not schedulable** until tomorrow
(FrozenClock test); consumed exactly once; unassisted+unprimed enforced on the served
attempt; episode rows link prescription→primed→cold end-to-end (this is spec §7.2's
telemetry).

### B7 — Coverage rollup (no new table; spec §4.11)

`services/coverage_rollup.py` over `source_coverage` + goal report. Bucket **precedence**
(demonstrated ≻ assessed ≻ no-supply) computed in one pass — pooled/embedded evidence
can demonstrate a facet with no local supply, so buckets must not be computed
independently. *Acceptance*: buckets are mutually exclusive and sum to the facet count;
the overlap case (demonstrated via pooled evidence + `attempts_to_certify = None`) lands
in `demonstrated`.

### B8 — Duel storage (spec §4.6; column check first)

Pre-reveal capture on **ordinary** attempts: the `answer_confidence` column exists
(migration 031) — this package is (a) accepting it on the ordinary submit path, valid
only when recorded pre-reveal (the draft flow already carries it for probes), and (b)
freezing the **model's** prediction per served attempt. **Check
`scheduler_training_logs` (migration 010) first** — if serve-time predicted recall is
already logged there, reference it; only add a `model_predicted_correctness` column on
`practice_attempts` if not. Probability mapping {1→.10, 2→.30, 3→.50, 4→.70, 5→.90}
lives in the track-record read model only — stored values stay 1–5.
*Acceptance*: post-reveal taps rejected; duel comparison excludes assisted/primed
attempts and attempts missing either side's prediction.

### B9 — Read-side additions (small; spec §4.3, §4.12)

Dominant scheduler reason: compute server-side next to the existing plain-English
ranking (`scheduler.py`), emit as `dominant_reason` in `handlers/serializers.py` (fact
9). Calibration report: minimum-N gating field so the frontend can render
plain-language counts below threshold; no per-bin Brier.

---

## Part 3 — Frontend packages

All in `apps/learnloop-tauri/src`. Every package ends with `npx tsc --noEmit` clean and
a full-app-restart sanity run (§1.2). Terminal aesthetic: match `ui.tsx` primitives
(Pill, Dim, Faint, Card, SegmentBar); amber is the accent; **never encode state by color
alone** (spec §4.13) — pair with glyphs/labels.

### F1 — Claim shell + dispatcher client (needs B1)

`components/ClaimSurface.tsx`: one shell (claim text, provenance line, receipt link,
response area), response vocabularies switched by `claim_class` per spec §2.1. Suppressed
claims render the plain-text variant. `visible_at` via IntersectionObserver — report
exposure, not render (spec §2.2). Keyboard-reachable responses. Mint `visit_id` per
tab-visit outside practice sessions. dto/client additions for the three B1 RPCs.
*Acceptance*: a claim scrolled off-screen never logs a presentation; responses land with
the right `presentation_id`.

### F2 — Log/Review tab (needs Track 0, B2; drawer-everywhere needs B5)

Repurpose tab 8: `ui.tsx` label "errors" → "Review" (id can stay), route in `App.tsx`
replaces the `EmptyPlaceholder` fallthrough. `screens/ReviewScreen.tsx`: changelog spine
(one entry per session from the B-side diff; **system-authored entries** for
out-of-session regrades/recalcs; an `algorithm_version` bump renders as ONE
"recalibration — your evidence unchanged" entry, never a per-facet flood) + working
hypotheses (cold `diagnosis` claims, ≤1 re-ask per visit, **correction always attached**
— §4.7's rule applies here too). Wire `FacetEvidenceDrawer` (fact 12: orphan, backend
already live) here and in `KnowledgeMapScreen`. Empty state per spec §4.9.
*Acceptance*: fresh-vault empty state renders; every facet reference opens the drawer.

### F3 — Feedback slice + duel (needs B1, B2, B8)

In `FeedbackScreen.tsx`: when the graded error matches a registry row **with an authored
correction**, the §4.7 statement-pair card *replaces* `UnresolvedCauseCard` (fact 14 —
never both); "repair this" action; hot `diagnosis` claim via F1. Regrade events render
the `ledger_fact` variant with request-review. In `PracticeScreen.tsx`: move/reuse the
existing `answer_confidence` selector for ordinary attempts, shown after the answer
draft is non-empty and locked at submit (pre-reveal), skippable.
*Acceptance*: rows without `correction_statement` fall back to the unresolved-cause
card; card hierarchy never shows two diagnoses; duel tap absent → attempt submits
normally.

### F4 — Two-lane hero + pace (needs B3, B4)

Rewrite `GoalTrajectoryChart.tsx` → two time-aligned lanes (spec §4.1): Demonstrated
step lane (counts, corrections visible), Ready lane (history + dotted do-nothing decay
from B4 + target line — target renders **only** in this lane). **Delete `linearFit()`**
and its forecast line. Model-coverage caption ("decay estimated from 8 of 12 facets…").
Pace sentence per §4.2 with edge states and the `pace_kind` label from Track 0;
planning-override response ("my usual {n} study days/week") recomputes the sentence
client-side from DTO fields and logs the scenario as a forecast response.
*Acceptance*: no rendered projection when B4 reports zero decay-estimated facets;
`linearFit` gone from the tree.

### F5 — Reason column + overconfidence list (needs B9; ship early)

TodayScreen queue gains the reason column from `dominant_reason`; each is a
`schedule_choice` claim (F1) with the structured reason follow-up (§2.1). Overconfidence
drill-down anchored on the session-narrative line (spec §4.3), probes launched with
`origin='overconfidence_list'`. This is deliberately early in sequencing: it accrues the
schedule-choice signal the decision-inert scheduler weights need.

### F6 — Repair flow (needs B6; no new tab)

A detail view (not a tab — tab 9 is freed; remove the "doctor" entry from `ui.tsx`),
launched from ReviewScreen working hypotheses, Feedback's "repair this," and Today
cards. One compact sequence: statement pair → side-by-side spans via `OpenInSource`
(both facets; the MaintenanceScreen already does side-by-side spans — copy that
pattern) → "try one now" (primed attempt via B6 intake) → confirmation that an
unassisted retry is scheduled ("tomorrow or later"). Status chips from transition
events, including **returned**.
*Acceptance*: full episode drives B6 end-to-end from the UI on a fixture vault.

### F7 — Ambient surfaces (needs B3, B4, B7; each independent)

- **Coverage bar** (Library, per source set): `SegmentBar`, three buckets, debt bucket
  visually distinct + "create/review practice items" CTA.
- **Welcome-back panel** (Today, >7 days): survival-first ordering per spec §4.4;
  never mentions the streak.
- **No-goal/fresh-vault fallbacks** (spec §4.5): decay-pressure list with
  "crosses target in ~N days" (insufficient-history facets excluded from confident
  copy); fresh vault → read-first / set a goal / short diagnostic.
- **Track record** (from forecast hero): two sections (answer calibration with
  minimum-N gating + duel Briers; forecast ledger record with
  resolved/censored/unobservable counts). No 10-bin curve below minimum N.

---

## Part 4 — Cross-cutting practices

- **Tests**: pytest, deterministic, FrozenClock, no network. Sidecar surface changes get
  contract tests (`tests/test_sidecar_contract.py` pattern). Fixture vaults under
  `fixtures/` — don't invent synthetic schemas when a fixture exists. Full suite +
  `tsc` + `cargo check` before every merge.
- **Git**: commit locally; **do not push to any remote without explicit approval** (the
  repo owner has previously forbidden pushing; copyrighted PDFs under `new_textbooks/`
  are gitignored and must never enter history).
- **Migration hygiene**: numbers 055–058 are assigned above; verify against
  `ls migrations/` at start; rebuild CHECKs off the *current* schema, not the original
  migration (older migrations may have already rebuilt the table).
- **Config**: new knobs go in `config.py` embedded defaults under `[hypothesis]`
  (budget, cooldown) and `[forecasts]` (resolution windows); per-vault override via
  `learnloop.toml`.
- **Order of delivery** (spec §8): Track 0 → {B1+B2 ∥ B5} → F2 → {B8, F1} → F3 →
  {B3+B4} → F4 → B9+F5 → B6 → F6 → B7 + F7. F5 may float earlier whenever B9 is done.
- **When in doubt about product behavior**, the spec wins; where the spec cites a file
  and the file has drifted, re-verify before building — every §1.5 fact carries its
  location for exactly that purpose.
