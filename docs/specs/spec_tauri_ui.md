# Tauri UI integration spec: delivering P0–P4 in the desktop app

**Status:** draft v0.1, 2026-07-17. Companion spec of record for the
*client-side* delivery of `spec_p0` … `spec_p4`: design-language contract,
per-phase screen/fixture inventory, RPC plumbing conventions, and the
`show`/`diff` replumbing. The phase specs own semantics; this spec owns
presentation and client plumbing. **It resolves the P3 delivery-surface
question: the delivery surface is `apps/learnloop-tauri` + the Python
sidecar** (the TUI remains a legacy surface; no new phase UI lands there).

**Ownership claims (ledger seed 2026-07-17):** implements U-030@v1
(design-language contract), U-031@v1 (per-phase screen + fixture inventory),
U-032@v1 (inspector/diff replumbing for the three-hash + lineage world).

All `file:line` references were verified against the working tree on
2026-07-17 (audit anchors, not durable references).

---

## 1. Design-language contract

### 1.1 The exemplars (read these before building any screen)

- **Screen body:** `IngestScreen.tsx` — the canonical direction (shipped
  single-screen v2). `TodayScreen.tsx` is consistent but carries legacy
  sprawl; where they differ, follow Ingest.
- **Overlay / inspector:** `components/CommandOverlayFrame.tsx` +
  `components/InspectorOverlay.tsx` — the `learnloop <command>` overlay form
  factor (backdrop, prompt header `❯ learnloop show <id>`, esc ×, footer
  keybar, history stack, `IdLink` graph navigation).
- **Non-monotone state vocabulary:** `screens/ReviewScreen.tsx` — glyph +
  label + color, never color alone (`EventBadge`, ReviewScreen.tsx:63-70);
  honest recalibration copy ("Estimates recomputed; your underlying evidence
  did not change").
- **Bespoke data-viz:** `screens/KnowledgeWellView.tsx` — one continuous
  quantity per visual channel; discrete facts get discrete markers (filled
  bead vs hollow ring); **never blend two axes onto one continuous scale**.
  Not a template for ordinary screens, but its channel discipline governs
  every new visualization (boundary view included).

### 1.2 The two styling systems (architectural fact)

There are two parallel systems: CSS classes in `styles/app.css` and inline
primitives in `components/term.tsx` (`COLOR`, `FONT_MONO`, `SectionHeader`,
`Pill`, `BlockBar`, `KeyBar`, `Meta/Dim/Faint`, `DisclosureHeader`,
`HelpTooltip`). `components/ui.tsx` re-exports colliding names backed by CSS.
**Screen bodies use `term.tsx` exclusively** (as TodayScreen.tsx:18 and
IngestScreen.tsx:5 do); the CSS-class system serves only the shell/nav
(`ui.tsx:204-234`) and the command palette. Do not mix.

### 1.3 The fifteen rules for any new screen

1. Mono font only (`FONT_MONO`: JetBrains Mono ramp, app.css:3); re-assert on
   numeric/data spans. No proportional type, ever.
2. Import tokens from `term.tsx` (`COLOR`, `FONT_MONO`); style bodies inline
   or with `term.tsx` primitives — not `app.css` classes, not `ui.tsx`'s
   CSS-backed twins.
3. Screen skeleton: flex column `flex:1, minHeight:0` → hero (`flexShrink:0`,
   `borderBottom`, pad ~22px 32px) → scroll region (`className="ll-scroll"`,
   `flex:1`, `overflowY:auto`) → `<KeyBar>` footer.
4. Screen title is an uppercase eyebrow: 11px, `letterSpacing:0.18em`,
   `COLOR.textFaint`, followed by a 13px `textDim` description. No `<h1>`.
5. Section breaks use `<SectionHeader>` (14px amber underlined, Title Case);
   everything else is lowercase.
6. Cards: `1px solid COLOR.border`, `borderRadius:2`, `padding:14px 18px`,
   transparent bg; state via `borderLeft: 3px solid <semantic>` (cyan
   running, green done, red error, amber attention).
7. Corners square; 2px radius maximum (cards, pills).
8. Semantic palette exactly: amber=primary/focus/selected, green=success/
   ready, cyan=running, red=error/destructive, pink=probe/diagnostic,
   purple=default/blocked. `Pill` for tags; `STATUS_PILL`/`STATUS_COLOR`
   maps (IngestActivity.tsx:19-37) for job status.
9. Primary action = amber on `#241d12` with `1px solid COLOR.amber`, ending
   `↵` (confirm) or `→` (next). Secondary = `textDim` on transparent.
10. Progress idioms are semantic: `<AsciiLoadingBar>` (cyan `[··=>··]`) for
    indeterminate work; `<BlockBar>` (`▓░`) for a known 0–1 value; the
    `✓ → ◐ → ·` checkpoint ladder for multi-phase pipelines;
    `<EmptyPlaceholder>` for loading states.
11. Border semantics: dashed = help/empty/informational; solid = content;
    solid + 3px left color = status.
12. Numeric/data/id text mono and colored by meaning (`Meta` for ids, `Faint`
    for metadata, `Dim` for secondary).
13. Page never scrolls; scroll only inside `ll-scroll`/`library-tree` regions
    (square scrollbar, amber on `:active`).
14. Microcopy lowercase, terse, imperative; "…" for in-progress, "→" next,
    "↵" confirm, "×" dismiss; keep the glyph vocabulary (`❯ ▸ ◆ ✓ ✕ ◐ ▓░`).
15. Real `<button>` or `EntityLink` (role/tabIndex/keyboard) — never bare
    `<span onClick>`; screen-level keydown for j/k/enter/esc/hotkeys,
    advertised in the `KeyBar`.

### 1.4 Known debt (fix opportunistically, not blockers)

- Wash backgrounds are untokenized raw hex (`#241d12` amber, `#10212a` cyan,
  `#241315` red, `#101d22` cyan-banner) copied dozens of times. **First new
  screen promotes them into `term.tsx` as `COLOR.washAmber` etc.**
- `Card` is copied in three places (ui.tsx, IngestScreen, IngestActivity).
  **Promote one `Card` into `term.tsx`** and migrate on touch.
- `<span onClick>` accessibility gaps in older code — do not propagate.
- Dead CSS twins (`.hero`, `.card`, `.queue-row`…) in app.css are not wired
  to the screens; don't edit them expecting screen changes.

### 1.5 New shared components this program requires

| Component | Purpose | Consumers |
|---|---|---|
| `CalibrationBadge` | visible `heuristic` / `simulation_validated` / `live_calibrated` label on every claim (umbrella §1; P0 §6) — a `Pill` variant with fixed slate/cyan/green mapping | feedback, diagnostics, review, why-panels |
| `AffectTap` | one optional touch, six typed signals (P0 §4.6); never required, never interrupts; renders as a collapsed `▸ how did that feel` disclosure | PracticeScreen, FeedbackScreen, DiagnosticReviewScreen, golden-path run |
| `Card` (promoted) + wash tokens | end the triplication | everything |
| `useBatchPoll` hook | formalize the self-rescheduling `setTimeout` poll (1500ms active / 5000ms idle, cancelled-flag guard — IngestActivity.tsx:130-144) | all long-running flows |
| `DepthEnvelopeCard` | render a depth preset + envelope preview + burden budget; confirm `↵` | capture flows (P3), atomic confirmation (P2), depth invitations |
| `WhyPanel` body pattern | headline value over per-component bars + plain-english callout (generalize `SchedulerWhy`, InspectorOverlay.tsx:1029-1101) | why-this-activity, why-this-diagnosis, why-this-block |
| `DispositionPicker` | the four reading-question dispositions (U-033: `comprehension_only` / `check_once_later` / `keep_developing` / `reference_only`) as a one-row inline choice; walking past = `comprehension_only`, never an obligation | P2 reading view, P3 reader (Ask keep-flow, §5.6 marks) |

---

## 2. Plumbing conventions (how every new feature lands)

### 2.1 The five-layer RPC chain (no codegen; budget for it)

pydantic `ParamsModel` + `@method` handler in
`learnloop_sidecar/handlers/<area>.py` (module **must** be imported in
`handlers/__init__.py`) → `#[tauri::command]` in `commands.rs` →
`generate_handler![]` in `main.rs` → `api` method in `client.ts` → camelCase
types in `dto.ts`. Full recipe with patterns: see the architecture notes in
§7 of `spec_implementation_plan.md` reading order. Restart the dev app after
Rust changes (`stale_app_binary`, client.ts:166-172).

### 2.2 Long-running flows

Poll-only — the sidecar has no push channel (`server.py` NDJSON
request/response; `"streaming": "coarse"`). New long-running flows model as
**durable batches** of `JobSpec`s with `depends_on` (pattern
`ingest_jobs.py:273-316`), polled via a batch-view RPC, `waiting_for_input`
for human-in-the-loop pauses, `_reload_applied_batches` if vault content is
applied. **Gap owned by P2:** the queue's job-type vocabulary is hard-coded
to ingest/synthesis types (`ingest_jobs.py:27-32`); the golden-path run adds
its own run table + job vocabulary (P2 §4's event-sourced state machine is
the server-side truth; the UI only polls and renders).

### 2.3 Navigation

Flat `tab` enum (`navTabs`, ui.tsx:5-14) + `renderBody()` branches
(App.tsx:406-588); overlays are nullable-id state rendered after
`TerminalFrame` (App.tsx:606-698); full-screen guided experiences use the
**body pre-emption** pattern (exam/calibration, App.tsx:412-428). New
inspector-style surfaces are `CommandOverlayFrame` consumers with their own
`command` identity, composing through `onInspect(id)` so everything remains
one navigable graph.

---

## 3. Per-phase UI inventory

Screens ship with their phase; each phase's acceptance journeys are exercised
through these surfaces. "Overlay" = CommandOverlayFrame consumer.

### P0 — measurement correctness

| Surface | Kind | Notes |
|---|---|---|
| Adjudication queue | overlay, `command="adjudicate"` | serves the calibration stream (P0 §4.7): stratum-sampled attempts, confirm/correct grade, correction reasons; inclusion probability logged server-side, not shown. Also the vehicle for the retrospective bootstrap session — build early, it unblocks P0.2 |
| AffectTap capture | shared component | wired into PracticeScreen + FeedbackScreen; capture only (semantics land P2) |
| Retire-with-reason | dialog from InspectorOverlay practice-item body + MaintenanceScreen | reason taxonomy (P0 §3.7); shows evidence surviving (facet evidence retained, instrument retired) |
| CalibrationBadge | shared component | appears wherever a posterior/readiness/diagnosis claim renders |
| Inspector identity rows | InspectorOverlay change | three hashes replace the single contract id (see §4) |

Fixtures: `fixtures/linear_algebra` (default dev vault) + a planted-misgrade
fixture state for adjudication-UI development.

### P1 — shared substrate (mostly invisible; inspector is the UI)

| Surface | Kind | Notes |
|---|---|---|
| New inspector kinds | InspectorOverlay + `handlers/inspector.py` | `commitment`, `activity_family`, `activity_card` (+version), `activity_surface`, `activity_administration` — each: `KIND_PILL` entry, Body component, resolver branch. Card body gets a lineage section with **fork-break rendering** (certification never crosses a fork) |
| Diff replumbing pt. 1 | ReviewScreen | new changelog kinds + `EventBadge` glyphs for card forks/version bumps; copy: "new memory trace — prior evidence not inherited" |
| `adopt_legacy_item` | affordance in LibraryScreen/MaintenanceScreen | explicit adoption of legacy-unowned items into commitments |

Fixtures: `fixtures/linear_algebra_mvp0.7` through the P1 migration; a
post-cutover fixture with a card that has both a surface-preserving edit and
a fork in its lineage (exercises the inspector + diff rendering).

### P2 — narrow golden path (the major UI phase)

| Surface | Kind | Notes |
|---|---|---|
| Exemplar selection | extension of source/library views | pick end-of-chapter exercises; multiple exercises = target distribution |
| Chapter reading view | **ReaderScreen slice 0** — new tab, deliberately minimal | U-033 (P2 §7.6): read-only marker markdown/KaTeX over block-level span views. **Build it as the first slice of the P3 ReaderScreen** (same component, no annotation store, no palette, no capture outbox) so P3 extends rather than replaces it |
| Reader Ask box | popover/side panel in reading view | span-grounded Ask in the `reader` tutor context; per-ask answer-mode toggle (`answer directly` / `help me reason` / `ask me first`, default direct); exchange history per span; hidden during cold attempts |
| Boundary question card | inline card at owner-placed section boundaries | instructional administration render (source stays visible); always skippable (`skip` advertised in KeyBar, logged as policy signal); ends in `DispositionPicker` |
| Owner question placement | blueprint-review checklist row | placing/editing boundary questions is part of the existing blueprint review surface, not a new screen |
| Atomic confirmation | dialog (QuickAddDialog composition pattern, incl. consent/token checkpoint) | goal contract v1 + commitment + `DepthEnvelopeCard` preset + assessment reservation, one `↵` |
| Golden-path run | **body pre-emption screen** (exam/calibration precedent) | renders the P2 §4 server-side state machine via `useBatchPoll`; the run's stage strip is the `✓ → ◐ → ·` checkpoint ladder; per-stage surfaces reuse PracticeScreen/FeedbackScreen idioms |
| Triage decision aid | panel within run flow | deterministic route: stated plainly; provisional distribution: alternatives listed, glyph+label+color, override affordance; overrides logged as anchors (U-027) |
| Why-this-diagnosis | overlay, `command="why"` | `WhyPanel` pattern: locked hypothesis set, probes used, per-response evidence contributions, surviving alternatives, grader assumptions + CalibrationBadge |
| Boundary view | GraphScreen sub-view or run-end panel | capability cells demonstrated/developing/untested/weak/contested; **relationship-not-deficit framing** (lead with what deepened, directions not deficiencies); well-view channel discipline applies |
| Depth invitation | card at run end / TodayScreen | `suggest_next` render: edge, envelope delta, evidence, burden; one-tap `↵` confirm; never auto-fires (U-018) |
| Owner review surfaces | `waiting_for_input` cards in IngestActivity style + RegistryReviewScreen patterns | blueprint review checklist, surface-pool admission, edge review |

Backend UI-plumbing: run-status RPC over the P2 run table; new job
vocabulary (§2.2 gap).

Fixtures: the P2 chapter fixture vault, **seeded at each major run state**
(post-baseline, mid-ladder, awaiting-assessment, post-assessment) so every
screen state renders deterministically without live jobs — use
`bind(background=False)` + `drain_foreground()` to fast-forward
deterministically; add a dev command that snapshots a run at state X. The
chapter fixture also seeds owner-placed boundary questions and one persisted
Ask exchange so the reading view, disposition picker, and exposure-warming
paths render offline.

### P3 — reader integration

| Surface | Kind | Notes |
|---|---|---|
| ReaderScreen | extends the P2 slice-0 tab | adds to the P2 reading view: block-anchored selection; per-block health flags with "view original" PDF-crop fallback; skim/anchor/incremental mode switch (modes gate boundary questions, P3 §5.1); per-question controls on presented questions |
| Action palette | selection popover in reader | three primitives (Ask / Practice / Mark) with the nine presets beneath; immediate local capture receipt (outbox ack) before any AI call |
| Annotation margin | reader region | annotations + reanchor status (`needs_reanchor` review affordance) |
| Capture arc moment | inline card after commit-class capture | the visible unfolding arc ("this idea will unfold over two weeks") + `DepthEnvelopeCard` preset; the emotional promise at capture |
| Proposal exception review | ProposalsScreen extension | demand-paged synthesis proposals, reviewed without losing reading position |
| Outbox/request status | reader footer + IngestActivity | background work, caps, token use visible (silent caps are lies) |
| In-review maintenance | PracticeScreen/FeedbackScreen verbs | edit wording / split / merge / spawn without leaving the session (P1 lineage services) |
| Restoration view | post-cold-attempt panel | source neighborhood + learner annotations + originating tutor exchange, hidden during the cold attempt |

Backend greenfield (P3 spec §12 owns semantics): annotation store, render
views + crosswalk, request engine. The reader is the largest single UI
build in the program; slice per the plan (render+capture+annotations first).

Fixtures: a source-with-annotations vault; a re-extraction fixture (same
source, bumped marker version) to exercise reanchoring UI.

### P4 — controller and scale

| Surface | Kind | Notes |
|---|---|---|
| Why-this-block/activity | overlay, `command="why"` | feasible set first (constraints that filtered, in order), scores within it — constraints and scores visually distinct (keystone B); CalibrationBadge on every number |
| Attention-block framing | TodayScreen hero | current block = commitment neighborhood + intent + 5–15 min budget; "one item is a completed session" for the three-minute entry |
| Experiment consent | settings/first-run dialog | randomization-layer opt-in with plain description; logged propensities disclosed in why-panels |
| Contest flow (Journey 8) | action in why-this-diagnosis overlay | "propose another explanation" → bounded-trust candidate → discriminating probe → revised diagnosis |
| Hiatus re-entry | StartScreen variant | no red backlog count; goal triage; retained/recoverable/weak groups; 7-day plan (builds on ReviewScreen's `reentry-summary` kinship) |

### Cross-phase: `show`/`diff` replumbing (U-032, timed with P0.4/P1)

From the code audit of `InspectorOverlay.tsx` / `ReviewScreen.tsx` /
`handlers/serializers.py` / `assessment_contracts.py`:

1. **Three-hash identity.** `practice_item_detail`'s single
   `assessment_contract_version_id` (from the monolithic `contract_hash`,
   assessment_contracts.py:169-197) becomes three DTO keys → three
   `InspectorRow`s: `card_contract_hash`, `surface_hash`,
   `administration_snapshot_hash`.
2. **New entity kinds** (P1 table above) in the three hardcoded sites:
   `KIND_PILL`, the Body dispatch, the `inspect_entity` resolver.
3. **Lineage navigation.** `IdLink` + history stack generalize to lineage
   edges (`minor_successor | semantic_fork | split_from | merged_from`);
   fork edges render as a visual break in the chain.
4. **Lineage-aware diff.** ReviewScreen changelog gains fork/version-bump
   entry kinds with the honest-copy pattern; movement attribution moves from
   facet-only to card-lineage-aware.
5. **Administration context on attempts.** AttemptBody resolves and links
   the administration snapshot (assistance, tools, feedback, grader-model
   pins) — "why this grade" becomes inspectable.
6. **Compatibility seam.** Gate on the existing `algorithm_version` check
   (serializers.py:103-106) to render legacy id and new hashes side by side
   during dual-write; the CLI `content_events` provenance hash is orthogonal
   and unchanged.

---

## 4. Fixture strategy

Fixture vaults **are** the mock layer — there is no separate stub layer, and
that stays true. Deterministic UI = `LEARNLOOP_VAULT` pointed at a seeded
vault (Rust default: `fixtures/linear_algebra`, sidecar.rs:311-320). The
program adds:

- per-phase seeded vaults as listed above (misgrade, post-cutover lineage,
  P2 run states, annotated source, re-extraction pair);
- a dev fast-forward command that drains jobs synchronously
  (`bind(background=False)`) and snapshots a run at a named state;
- every new screen must render fully from a fixture state with no live jobs
  and no AI providers configured — this is a per-screen acceptance item.

## 5. Acceptance (per new surface)

1. Follows the §1.3 fifteen-rule contract (reviewed against the exemplars).
2. Keyboard-walkable end-to-end; keys advertised in `KeyBar`; esc semantics
   correct under nested overlays (suppress-parent pattern).
3. Renders from its fixture state offline (no jobs, no AI).
4. Non-monotone state uses glyph+label+color; every model-derived claim
   carries a `CalibrationBadge`.
5. Long-running work uses `useBatchPoll` + the correct progress idiom.
6. New RPCs traverse all five layers with camelCase DTO parity; `stale_*`
   drift detectors still fire correctly.

## 6. Change log

- **2026-07-18** — v0.2. Reader-dialogue fold (umbrella change (q), U-033):
  P2 inventory gains the chapter reading view (defined as ReaderScreen
  slice 0 so P3 extends it), reader Ask box with answer-mode toggle,
  boundary question card, and owner question placement (blueprint-review
  row); `DispositionPicker` added to shared components; P2 chapter fixture
  seeds boundary questions + one Ask exchange. U-031 inventory extension
  (editorial).
- **2026-07-17** — v0.1. Created from the three-agent design/architecture/
  inspector audit (TodayScreen + IngestScreen + app.css + term.tsx;
  App.tsx + client/dto + sidecar handlers + ingest_jobs; InspectorOverlay +
  CommandOverlayFrame + ReviewScreen plumbing). Resolves the P3
  delivery-surface question (Tauri + sidecar). Registers U-030/U-031/U-032.
