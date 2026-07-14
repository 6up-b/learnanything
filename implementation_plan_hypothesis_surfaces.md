# Implementation Plan: Hypothesis Surfaces (spec_hypothesis_surfaces.md v3)

Audience: an engineer who has **never seen this repository**. Read Part 1 before touching
anything. The normative contract is `spec_hypothesis_surfaces.md` (draft v3, 2026-07-14);
this plan tells you where everything lives, what order to build in, and which existing
behaviors will bite you. Companion background: `spec_knowledge_model.md` (§9.5 dual-axis,
§9.6 UI, §10 error taxonomy), `spec_misconception_diagnostics.md`,
`implementation_plan_km_ingestion_v2.md` Part 1 (fuller orientation; this one is
condensed).

---

## Implementation status — 2026-07-14 (final)

All backend packages, their focused acceptance tests, and the Tauri React UI/UX
packages (F1–F7) are implemented. Treat the package descriptions below as the
normative acceptance contract; the notes column records residual gaps.

| Package | State | Notes |
|---|---|---|
| Track 0 | **done** | Overlapping-session attribution test added (`tests/test_session_attempt_attribution.py`); drawer copy restored to exact language after the B5 invariant passed. |
| B1 | **done** | Dispatcher unit matrix added (`tests/test_hypothesis_claim_dispatcher.py`): hot-slot reservation, cooldown, debounce, changed-version re-presentation, ≤1 cold re-ask/visit, suppression. |
| B2 | **done** | Transition/reactivation ("returned" derivable) and all-three-intake-route tests added (`tests/test_misconception_transitions_intake.py`). |
| B3 | **done** | Idempotency, censoring, and past-horizon pace-resolution tests added (`tests/test_forecast_ledger.py`). |
| B4 | **done** | Monotone/held-flat/golden/zero-coverage tests added (`tests/test_goal_decay_projection.py`); F4 renders the fields. |
| B5 | **done** (phases 1+2) | The all-fixture invariant test (`tests/test_receipt_exactness.py`) exposed a real divergence in `facet_evidence_timeline.py` (intra-attempt repeat discounting, zero-credit group marking, per-epoch folding); fixed to replicate canonical-projection marking semantics exactly — worst residual diff 5.5e-17. Phase 2 shipped: `itemize_observation_contributions` (float-identical to the cap path) gives every timeline point a per-observation derivation (channel, raw vs capped credit, binding rule), and `facet_ready_derivation` folds the persisted canonical recall slices for the §5.1 Ready line; the drawer renders the derivation line, a keyboard-reachable evidence scrubber with tap-through detail, and honest `notes` for ingredients not derivable from ledger state (no FSRS decay factor in the grid Ready quantity; no facet→parent pooling in production; single algorithm_version). `tests/test_receipt_derivation.py` asserts itemization sums exactly to banked credit on every fixture. |
| B6 | **done** | FrozenClock delay / consume-once / unassisted-enforcement / end-to-end episode tests added (`tests/test_remediation_cold_retry.py`); F6 UI built. |
| B7 | **done** | Overlap/sum tests added (`tests/test_coverage_rollup.py`); Library renders the bar. |
| B8 | **done** | Post-reveal rejection + duel exclusion tests added (`tests/test_answer_calibration_duel.py`); Practice selector finalized (pre-reveal lock, caret + focus marking, clear affordance). |
| B9 | **done** | Consumed by F5 (policy claims) and F7 (track record). |
| F1 | **done** | `replaceAll` → ES2020-safe `.replace(/_/g, " ")`; typecheck clean. Viewport-exposure behavior is IntersectionObserver-based; there is no frontend test runner in this repo, so off-screen non-exposure remains manual-smoke scope. |
| F2 | **done** | Tab 8 is now "Review" (`ReviewScreen.tsx`): changelog spine with annotated non-monotone events, working hypotheses as cold diagnosis claims (correction always attached), repair launch, `FacetEvidenceDrawer` wired here and in Knowledge Map, fresh-vault empty state. System-authored entries shipped: `learner_review_feed.py` emits `regrade` entries for out-of-session grading epochs (old→new, direction; in-session regrades stay inside the session entry's corrections count — clean partition) and exactly ONE `recalibration` entry per algorithm_version transition from `derived_state_rebuilds` (`tests/test_learner_review_system_entries.py`). |
| F3 | **done** | §4.7 statement-pair card strictly replaces `UnresolvedCauseCard`, hot diagnosis claim via `ClaimSurface`, "repair this" wired through App to the repair flow, regrade `ledger_fact` card with request-review. `FeedbackBundle` now carries a persisted `regrade` marker (old/new score, direction, regradedAt), so out-of-session regrades render the ledger card on fresh load; the transient in-screen receipt takes precedence so a regrade never renders twice. |
| F4 | **done** | `GoalTrajectoryChart` rewritten as two time-aligned lanes (`linearFit` deleted from the tree); model-coverage caption; zero-coverage suppression; §4.2 pace sentence with `pace_kind` labeling and edge states; planning override logged via claims; `TrackRecordView` with the two never-merged sections. `GoalReportSummaryDto.activeForecasts` now carries the open issued-forecast ids per kind (read-only lookup — rendering never issues), and the planning-override claim references the issued pace forecast row, falling back to a labeled goal-scoped ref only when none is open. |
| F5 | **done** | Focused queue row's dominant reason wrapped as a `schedule_choice` claim (suppression-aware); new `overconfidence.py` read model (ready × blueprint weight, evidence-mass gate, config `[hypothesis].overconfidence_min_evidence_mass`) + Today list + `start_overconfidence_probe` with `origin='overconfidence_list'`. Migration 059 adds a durable `origin` column on `probe_episodes` (the `target_decision_json` side-channel is removed); origin survives target selection, legacy rows stay NULL, and the table remains outside replay. |
| F6 | **done** | Doctor tab removed; `RepairScreen.tsx` overlay drives the full episode lifecycle (statement pair → side-by-side spans for both facets → primed attempt handoff → cold-retry confirmation) launched from Review and Feedback. |
| F7 | **done** | Library three-bucket coverage bar (debt bucket glyph+label+CTA via propose-only `create_study_map`); `SessionFinishHud` ≤3-line learning diff (up/down never netted, corrections forced when nonzero); welcome-back `ReentryPanel` (new `reentry_summary.py` + RPC, survival-first, streak never mentioned); no-goal decay-pressure list and fresh-vault three-action fallback (new `decay_pressure.py` + RPC). |

New read-model RPCs added during F5/F7: `get_overconfidence_list`,
`start_overconfidence_probe`, `get_reentry_summary`, `get_decay_pressure` (full
service → repository → sidecar → Rust → DTO/client chain, plus Typer CLI parity).
New config knobs under `[hypothesis]`: `overconfidence_min_evidence_mass`,
`reentry_gap_days`, `decay_pressure_target_recall`, `decay_pressure_horizon_days`.

Validation at this checkpoint:

- `pytest -q`: full suite green including 50+ new acceptance tests.
- `npx tsc --noEmit`: clean.
- `cargo check`: passed (new proxy commands registered; a full app restart is
  required before the new RPCs are callable from the UI).
- `python -m compileall -q src`: passed. `git diff --check`: passed.
- `grep -rn linearFit apps/learnloop-tauri/src`: no matches.

Important naming guard: `services/review_log.py` is the existing FSRS fitting
reconstruction API (`ReviewObservation`, `ReviewLog`, `reconstruct_review_log`). It is
restored with no Git diff and its 10 fitting/reconstruction tests pass. The learner-facing
Review feed is deliberately separate in `services/learner_review_feed.py`; never merge
or rename it over the FSRS module.

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

migrations/NNN_*.sql           sequential SQLite migrations. 055–059 now implement this
                               plan. Run `ls migrations/` before creating another one —
                               collisions with parallel work happen.
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
- `services/review_log.py` means **FSRS fitting input**, not the learner-visible Review
  tab. The learner-facing read model lives in `services/learner_review_feed.py`.

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

### 1.5 Verified baseline facts and their current disposition

Each baseline fact was verified before implementation on 2026-07-14. They explain the
shape of the work packages, but several are now deliberately superseded. The final
column is authoritative for the current tree.

| # | Baseline fact | Where | Current disposition |
|---|---|---|---|
| 1 | Pace numerator counted **every vault attempt** in 14d; denominator was goal-scoped. | `services/goal_pace.py`, `db/repositories.py` | **Fixed:** goal-scoped, qualification-compatible, and clipped to goal age; `pace_kind='qualifying'`. |
| 2 | Drawer claimed exactness while the timeline omitted grouped caps. | `KnowledgeModel.tsx`, `facet_evidence_timeline.py` | **Backend fixed:** timeline uses the shared cap calculator. Temporary upper-bound UI copy is now stale and must be updated after the fixture invariant test. |
| 3 | `session_attempt_counts` joined only by time window despite `session_id`. | `db/repositories.py` | **Fixed:** session id first, time fallback only for legacy NULL rows. |
| 4 | Legacy follow-ups could not express delayed cold retry. | repository/scheduler follow-up paths | **Extended:** migration 058 adds structured delayed tasks; legacy action strings remain for old rows. |
| 5 | Reactivation erased durable relapse history. | `update_misconception` | **Compensated:** transition events make `returned` derivable even though current-state timestamps still reset. |
| 6 | Registry rows had no authored correction. | migrations 047 and 056 | **Extended:** nullable correction + provenance span ids; legacy rows correctly remain NULL. |
| 7 | Series DTO lacked decay data and the chart fabricated `linearFit`. | goal series DTO/chart | **Backend fixed, UI pending:** projection fields exist; `linearFit` is still present and must be removed in F4. |
| 8 | Facets without FSRS data were held flat. | `goal_projection.py` | **Preserved and disclosed:** DTOs now distinguish `decay_estimated` and `held_flat`. |
| 9 | Scheduler exposed components but no canonical dominant reason. | scheduler/serializers | **Fixed:** server computes and serializes `dominant_reason`; Today currently displays it. |
| 10 | Calibration had pooled Brier without launch-safe gating/duel. | `exam_calibration.py` | **Extended:** minimum-N gate, matched learner/model duel, and answer-calibration RPC. |
| 11 | `exam_predictions` supplied the frozen-ledger pattern. | `exam_session.py` | **Preserved:** B3 follows this pattern in migration 057. |
| 12 | Drawer was orphaned; Errors/Doctor tabs were placeholders. | KnowledgeModel/ui/App | **Still true:** F2/F6 remain. |
| 13 | Stored 1–5 answer confidence existed only in probe UX. | migration 031/PracticeScreen | **Extended:** ordinary attempt selector and submission wiring exist; no fourth scale added. |
| 14 | Feedback always followed trace with unresolved causes. | FeedbackScreen | **Backend prepared, UI pending:** correction-backed `matchedMisconception` is serialized, but hierarchy/rendering is still F3. |

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

The backend dependency spine has landed. For the remaining UI work, F2's changelog spine
does not wait for B5's phase-2 receipt detail, but drawer exactness copy should wait for
the B5 all-fixture invariant.

---

## Part 2 — Backend packages

Applied migration assignments: **055** (B1), **056** (B2), **057** (B3), **058** (B6), **059** (durable probe origin, F5).
Migration 058 rebuilds the existing `source_exposure_events.context` CHECK and creates
the new follow-up table with its own closed CHECK values. Do not renumber these now that
they exist.

### Track 0 — bug fixes (days; no new schema)

**Status: implemented.** Goal pace and session attribution are live and the updated
pace/series assertions pass. The drawer copy was made conservative before B5; after B5's
fixture exactness test lands, remove its now-stale “upper bound” qualifier.

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

**Status: implemented and wired.** Migration, config, repository/service, CLI, sidecar,
Rust, and TS contracts exist. `tests/test_hypothesis_surface_wiring.py` covers the
presentation→response linkage and camelized RPC round trip. Add the dispatcher policy
unit matrix listed in the status table before calling the acceptance block complete.

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

**Status: implemented and wired.** Correction-backed matches are exposed to Feedback
and Review, and repair intake has its own service. Focused transition and intake tests
remain.

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

**Status: implemented and wired.** Session start resolves then issues material
forecasts; maintenance resolves due rows; the forecast track-record RPC reaches the TS
client. Add the three focused acceptance tests below.

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

**Status: implemented and wired.** Goal report/series payloads now carry current Ready,
Demonstrated counts, do-nothing projections, and model coverage; payload cache version is
3. F4 and projection-specific golden tests remain.

Extend `services/goal_projection.py` / `goal_series.py`: per-day projected mean recall
from today to due date (reuse the retention-ratio machinery + `fsrs.forgetting_curve`),
plus coverage counts `{decay_estimated: n, held_flat: m}` (fact 8). Thread through
`handlers/goals.py` and `GoalSeriesPointDto`/report DTO.
*Pitfall*: the goal series sidecar cache keys on a payload version — **bump
`_SERIES_PAYLOAD_VERSION`** or stale cached series will miss the new fields.
*Acceptance*: projection is monotone non-increasing for decay-only facets; held-flat
facets excluded from the curve but counted; golden test on a fixture vault.

### B5 — Shared receipt calculator (no new table; spec §5.2)

**Status: core implementation present; acceptance incomplete.** Canonical projection and
the timeline share `services/receipt_contributions.py`, and repository-derived timeline
events are marked authoritative. Do not restore exact UI copy until the all-fixture
banked-credit invariant passes. Phase 2 remains separate work.

Extract the authoritative per-observation contribution math (caps, correlation-group
budgets, attempt ceiling, corrections) from `services/canonical_projection.py` into a
pure shared function; make `services/facet_evidence_timeline.py` fold with it.
*Acceptance*: **the timeline's final value equals the banked ledger credit exactly** on
every fixture vault (this is the test that retires fact 2); from-scratch == incremental
fold stays byte-identical. Phase 2 (separate, after F2 ships): extend the timeline
handler payload with per-observation derivation + Ready derivation for the full §5.1
receipt — the current endpoint returns only the Demonstrated series + cross-links.

### B6 — Remediation model (migration 058 + CHECK rebuild; spec §4.10)

**Status: implemented and wired.** The RPC lifecycle is covered by a sidecar contract
round trip. Time-delay, consume-once, assistance enforcement, and full episode tests are
still required before the acceptance block is complete.

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

**Status: implemented and wired.** `get_source_coverage` includes the rollup and the TS
DTO models all three buckets. Add the overlap/sum tests and F7 Library surface.

`services/coverage_rollup.py` over `source_coverage` + goal report. Bucket **precedence**
(demonstrated ≻ assessed ≻ no-supply) computed in one pass — pooled/embedded evidence
can demonstrate a facet with no local supply, so buckets must not be computed
independently. *Acceptance*: buckets are mutually exclusive and sum to the facet count;
the overlap case (demonstrated via pooled evidence + `attempts_to_certify = None`) lands
in `demonstrated`.

### B8 — Duel storage (spec §4.6; column check first)

**Status: partially complete.** No new confidence scale or attempt prediction column was
needed: ordinary attempts reuse `answer_confidence`, while the model prediction is
joined from the served scheduler candidate. The calibration read model computes both
Briers, and Practice already submits the optional selector. Add the negative/exclusion
tests and finish F3/F7 presentation.

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

**Status: implemented and wired.** Dominant reason is server-owned, the calibration
payload declares its minimum-N gate, and `get_answer_calibration` exposes pooled and
duel records through Tauri/TS.

Dominant scheduler reason: compute server-side next to the existing plain-English
ranking (`scheduler.py`), emit as `dominant_reason` in `handlers/serializers.py` (fact
9). Calibration report: minimum-N gating field so the frontend can render
plain-language counts below threshold; no per-bin Brier.

### B10 — Boundary completion added during implementation

**Status: implemented.** This is documentation of work discovered while preparing the
frontend boundary; it is not a new normative feature package.

- `services/learner_review_feed.py` owns the learner-facing changelog and working
  hypotheses. `services/review_log.py` remains exclusively the FSRS fitting
  reconstruction module.
- `services/session_learning_diff.py` and `end_session` now expose
  `facets_demonstrated`, separate prediction movement counts, corrections, and
  misconception `resolved`/`returned` counts. The same read model feeds session entries
  in Review.
- `handlers/review.py`, `handlers/remediation.py`, `handlers/claims.py`, goals/exams
  handlers, Rust proxy commands, and `dto.ts`/`client.ts` complete the non-visual chain.
- `tests/test_hypothesis_surface_wiring.py` covers claim linkage, Review/remediation,
  both track-record endpoints, and the session-end payload.

---

## Part 3 — Frontend packages

All in `apps/learnloop-tauri/src`. Every package ends with `npx tsc --noEmit` clean and
a full-app-restart sanity run (§1.2). Terminal aesthetic: match `ui.tsx` primitives
(Pill, Dim, Faint, Card, SegmentBar); amber is the accent; **never encode state by color
alone** (spec §4.13) — pair with glyphs/labels.

### F1 — Claim shell + dispatcher client (needs B1)

**Status: partial.** The component and boundary exist, but no product surface consumes
the shell yet. Replace the unsupported `String.replaceAll` usage (or raise the TS lib
target deliberately), restore a clean typecheck, and add viewport-exposure tests before
integration.

`components/ClaimSurface.tsx`: one shell (claim text, provenance line, receipt link,
response area), response vocabularies switched by `claim_class` per spec §2.1. Suppressed
claims render the plain-text variant. `visible_at` via IntersectionObserver — report
exposure, not render (spec §2.2). Keyboard-reachable responses. Mint `visit_id` per
tab-visit outside practice sessions. dto/client additions for the three B1 RPCs.
*Acceptance*: a claim scrolled off-screen never logs a presentation; responses land with
the right `presentation_id`.

### F2 — Log/Review tab (needs Track 0, B2; drawer-everywhere needs B5)

**Status: not started in the UI.** The backend feed and DTO/client method provide the
session spine and correction-backed active hypotheses. System-authored regrade and
single-entry recalibration events are not yet modeled. `ReviewScreen.tsx` does not
exist; tab 8 is still “Errors”; the drawer remains orphaned.

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

**Status: partial.** Ordinary answer confidence is captured and Feedback receives a
typed `matchedMisconception` only for active/resolving rows with authored corrections.
Feedback still renders the old unresolved-cause hierarchy and has no hot claim or repair
launch.

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

**Status: not started in the UI.** Backend fields are ready, but
`GoalTrajectoryChart.tsx` still contains `linearFit()` and the old blended trajectory.

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

**Status: partial.** Today renders `dominantReason`. It is not yet a `schedule_choice`
claim, and the weighted/minimum-evidence overconfidence read model, list, and
origin-tagged probe route do not exist.

TodayScreen queue gains the reason column from `dominant_reason`; each is a
`schedule_choice` claim (F1) with the structured reason follow-up (§2.1). Overconfidence
drill-down anchored on the session-narrative line (spec §4.3), probes launched with
`origin='overconfidence_list'`. This is deliberately early in sequencing: it accrues the
schedule-choice signal the decision-inert scheduler weights need.

### F6 — Repair flow (needs B6; no new tab)

**Status: not started in the UI.** `RepairScreen.tsx` does not exist and the Doctor tab
is still present. The start→prescribe→treatment→get RPC lifecycle is ready.

A detail view (not a tab — tab 9 is freed; remove the "doctor" entry from `ui.tsx`),
launched from ReviewScreen working hypotheses, Feedback's "repair this," and Today
cards. One compact sequence: statement pair → side-by-side spans via `OpenInSource`
(both facets; the MaintenanceScreen already does side-by-side spans — copy that
pattern) → "try one now" (primed attempt via B6 intake) → confirmation that an
unassisted retry is scheduled ("tomorrow or later"). Status chips from transition
events, including **returned**.
*Acceptance*: full episode drives B6 end-to-end from the UI on a fixture vault.

### F7 — Ambient surfaces (needs B3, B4, B7; each independent)

**Status: not started in the UI.** The shared read models for answer calibration,
forecast records, coverage, goal projection, and session diffs have DTO/client coverage.
Before implementing welcome-back and no-goal decay pressure, verify those endpoints can
support historical survival and threshold-crossing copy; add a deterministic backend
read model if they cannot rather than deriving a confident claim from incomplete client
data.

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
- **Migration hygiene**: numbers 055–059 are assigned above; verify against
  `ls migrations/` at start; rebuild CHECKs off the *current* schema, not the original
  migration (older migrations may have already rebuilt the table).
- **Config**: new knobs go in `config.py` embedded defaults under `[hypothesis]`
  (budget, cooldown) and `[forecasts]` (resolution windows); per-vault override via
  `learnloop.toml`.
- **Original order of delivery** (spec §8): Track 0 → {B1+B2 ∥ B5} → F2 →
  {B8, F1} → F3 → {B3+B4} → F4 → B9+F5 → B6 → F6 → B7 + F7.
- **Continuation order from this checkpoint**: fix the F1 typecheck blocker and add its
  exposure tests → F2 Review/drawer → F3 Feedback hierarchy → F4 two-lane hero → finish
  F5 policy claims/overconfidence → F6 Repair flow → F7 ambient surfaces/session diff →
  focused backend acceptance tests listed in the status table → full pytest/tsc/cargo
  and a restarted-app smoke test.
- **When in doubt about product behavior**, the spec wins; where the spec cites a file
  and the file has drifted, re-verify before building — every §1.5 fact carries its
  location for exactly that purpose.
