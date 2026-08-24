# P3 implementation spec: reading-first integration

**Status:** Draft v0.2, code-audited 2026-07-16; depth contract amended
2026-07-17; ownership-ledger consensus folded in 2026-07-17
**Parent:** `spec_new_improvements_v2.md` (P3 delivery phase and Layer 3)
**Depends on:** the existing source layer; integrates with P0–P2 when present
**Acceptance focus:** Journeys 1, 2, and 7

**Ownership claims** (pins ledger seed 2026-07-17,
`spec_ownership_ledger.md`; re-triaged 2026-07-18 against U-017@v3):
implements U-013@v2 reading-event kinds on the P0-owned `interaction_events`
envelope; extends the P2 reader-dialogue slice (U-033) with reading-mode
presentation and per-question interaction controls (§5.1, §5.4); defers
U-017@v3 (`ask_now` planner and automatic question density) to P4 shadow
work and U-036 (non-text renderers) past this phase.

P3 makes the source reader the front door. The learner can begin reading before
a whole study map exists; selections and personal text are saved immediately;
Ask, Practice, and Mark actions progressively request only the current source
neighborhood; and accepted captures unfold into visible learning plans without
turning every click into curriculum.

The immutable source bytes remain authoritative. Extraction IR is a versioned
derived representation. Marker markdown is a replaceable display view.
Reviewed facets/learning objects remain the canonical domain model. These
layers are deliberately not called interchangeable or “canonical.”

---

## 1. Outcome and boundaries

At P3 exit the learner can:

1. open an imported source directly into skim or anchor reading;
2. select exact text across one or more source blocks;
3. save a verbatim annotation locally before any external call;
4. Ask, Practice, or Mark through nine explicit presets;
5. continue reading while bounded inventory/synthesis runs in the background;
6. accept, edit, or reject proposed mappings/activities without a modal
   interruption;
7. see a capture become a visible two-clock unfolding arc;
8. choose whether that arc holds, suggests, or automatically advances inside a
   visible depth envelope, and pause/shrink it at any time;
9. edit/split/merge/spawn a card from the review moment;
10. take a later cold activity and receive the exact source neighborhood plus
   their annotation only after measurement closes.

### 1.1 Non-negotiable invariants

1. **Reader is useful before synthesis.** Opening, navigation, selection,
   annotation, and local capture never wait for an AI/model job.
2. **Local-first capture.** The exact selected quote and learner-authored text
   commit transactionally before enqueueing any background work.
3. **Blocks anchor meaning.** Annotations bind to source revision/block
   locators plus sub-block selectors. Markdown offsets are never authoritative.
4. **Views are replaceable.** Re-rendering marker markdown does not rewrite
   annotations, source objects, commitments, or evidence.
5. **Ambiguity is visible.** Failed or ambiguous re-anchoring becomes
   `needs_reanchor`; it is never silently attached to the nearest text.
6. **Reading is not evidence.** Dwell, skip, highlight, revisit, “already know,”
   and salience projections cannot enter mastery, posterior, or certification
   projectors.
7. **Capture is not automatic curriculum.** Annotations and explicit
   commitments materialize immediately. Facet/LO mappings, relationships, and
   synthesized activities remain proposals until the relevant review contract
   accepts them.
8. **Commit semantics stay distinct.** `test_me_later` means one delayed cold
   check; `help_me_remember` means ongoing attention; `connect_it` creates a
   learner-authored relationship proposal, never a canonical edge.
9. **Authorship is never laundered.** Author, learner, expert, and AI provenance
   remains attached and visible. An AI-rendered prompt cannot be presented as
   the source author's editorial intention.
10. **Cold means no source cue.** Source text, tutor exchanges, annotations,
    purpose text, and “why” are withheld from a cold administration. Opening
    them ends/contaminates cold status rather than blocking learner agency.
11. **Content edits append.** Annotation edits, reanchors, card edits,
    refactors, mappings, and source-object reconciliation append versions/events.
12. **No `content_events` misuse.** Learner interaction telemetry uses the
    typed `interaction_events` envelope (created by P0, U-013; P3 adds the
    reader event kinds); `content_events` remains the closed content-mutation
    audit stream.
13. **Automatic depth is visible pre-authorization.** Reader arcs may advance
    automatically only inside the active P1 DepthEnvelope along a reviewed,
    evidence-gated edge. The reader never infers authorization from dwell,
    highlights, questions, affect, or `wanted_more_depth`, and it never hides a
    reached milestone when the arc continues.

### 1.2 In scope

- marker-converted markdown + KaTeX reader with figure assets;
- immutable render versions and markdown↔source-block crosswalk;
- per-block extraction health and original-region fallback;
- annotations with exact sub-block anchors, verbatim content, reanchoring, and
  mapping proposals;
- Ask/Practice/Mark action palette and local-first capture receipt;
- demand-paged unit inventory/synthesis with idempotent jobs, caps, and visible
  usage;
- source objects and source-object relations/provenance;
- salience-only reading telemetry and typed interaction event envelope;
- learner-authored Q+A, non-blocking formulation coach, pinned surfaces, and
  in-review edit/refactor/merge/spawn;
- versioned unfolding arcs, depth presets, policy/envelope controls, automatic
  inside-envelope transitions, and tempered pretest primes;
- post-cold source/annotation restoration;
- batch “Build me a path” coexistence and additive migration.

### 1.3 Explicitly out of scope

- syntopic comparison UI, a separate incremental-reading queue, or eager
  whole-library synthesis;
- browser extension, OS share sheet, voice, or VOD capture;
- learned salience/taste models or reading-behavior mastery inference;
- automatic canonical facet/LO creation from clicks;
- an AI gate on learner-authored cards;
- whole-document collaborative annotation or social sharing;
- P4 controller promotion/open-world expansion, though P3 emits the typed
  learner hypothesis seeds P4 consumes;
- unbounded, cross-source/commitment, or outside-envelope automatic depth
  escalation;
- active-learning artifacts as a fully supported source class; their source
  contract is reserved here for a post-MVP successor;
- planner-driven automatic reading-question insertion (U-017@v3: the
  `ask_now` planner and any density policy such as §8b.6's ~1 per 1000–1500
  words) — deferred to P4 shadow work. In scope by contrast: presenting the
  owner-placed P2 dialogue questions (U-033) under reading-mode gating with
  per-question controls; pretest-as-prime (§10.3) is unaffected and remains
  in scope.

---

## 2. Verified code-truth ledger

| Area | Verified reality | P3 consequence |
|---|---|---|
| Source identity | Migration 032 already models artifact → immutable revision → extraction run → units/blocks/assets with hashes and geometry. | Extend this chain; do not invent document identity inside the reader. |
| Block stability | `DocumentBlock.span_id` is stable only within an extraction and cross-run identity is recovered by reanchoring (`ingest/ir.py:32-52`). | Annotation anchors pin revision/extraction + block and use explicit cross-run anchor versions. |
| Reanchoring | `reanchor_spans` uses exact hash, section/page/geometry, and neighbors; unresolved/tied candidates become `needs_reanchor` (`ingest/reanchor.py:1-8,40-70,83-99`). | Reuse its deterministic first pass, then add sub-block quote/context resolution and manual review events. |
| Health | IR exposes only per-page `PageHealth` plus aggregate flags (`ingest/ir.py:117-151`). | Add per-block health and fallback decisions; do not infer equation/figure safety from a page-wide flag alone. |
| Existing viewer | `build_span_view` returns text, geometry, neighbors, optional local PDF page render, and records a source exposure (`span_view.py:69-172`). | Reuse source resolution/exposure and region geometry; expand from read-only span viewer to versioned reader view. |
| Viewer fallback | Current local PDF renderer returns a whole page and otherwise falls back to labeled PDF text (`span_view.py:110-115,175-200`). | Add block-region crop fallback for suspect blocks while retaining “view whole original.” |
| Exposure schema | `source_exposure_events.context` is a closed CHECK and records one viewed block (`migrations/049_source_exposure_events.sql:8-25`, later rebuilt for more contexts). | Add reader/restoration contexts through a deliberate migration and keep source exposure distinct from activity familiarity. |
| Inventory | Unit inventory is already deterministic, sharded by block/section, cached by schema/prompt/model, span-cited, and produces candidates only (`source_unit_inventory.py:1-29`). | Demand-page existing unit work and preserve candidate/review semantics. |
| Synthesis | Source-set synthesis already shards and caches `synthesis_shard_results`; ingest batches have durable priority. | Add reader request keys/priorities and proposal routing rather than a parallel job engine. |
| Quick add | Current quick add imports a source selection then enqueues inventory→bootstrap synthesis after one confirmation (`quick_add.py:1-22,320+`). | Keep batch “Build me a path”; add a capture/commit transport that does not pretend the existing quick-add flow already models annotations. |
| Interaction log | `content_events` has closed event/entity CHECKs for content mutation (`migrations/036_content_events_entity_types.sql:10-38`). | Create `interaction_events`; do not repeatedly rebuild `content_events` for reader telemetry. |
| Annotations | No durable source-annotation model exists; only passive source exposure exists. | P3 owns the first annotation/version/anchor/event schema. |
| Product surface | Current TUI exposes practice/today flows, not a marker markdown reader with selection/action palette. | Reader UX and RPCs are new, while source/attempt services remain reusable. |

---

## 3. Rendering contract

### 3.1 Authority layers

Every reader response and debug receipt states the layer explicitly:

```text
source bytes        authoritative immutable artifact
source revision     immutable identity/version of those bytes
extraction IR       versioned derived representation; may contain errors
render view         replaceable marker-markdown/KaTeX presentation
source object       per-source reviewed/proposed semantic object
canonical domain    reviewed cross-source facets/LOs/blueprints
```

No display renderer may write directly to canonical-domain tables.

### 3.2 Render versions

Create immutable `source_render_views` with:

- source/revision/extraction ids;
- renderer (`marker_markdown`) and exact renderer/model/config/schema versions;
- markdown/content hash and asset manifest hash;
- status, health summary, creation/completion timestamps;
- predecessor view and reason;
- retained output reference or chunk storage;
- canonical request/result hashes for idempotency.

Create `source_render_block_crosswalk` with:

- render-view id and display node/chunk id;
- source extraction/span id;
- display start/end offsets for highlighting only;
- source-block content hash and ordinal;
- asset/KaTeX node relationships;
- crosswalk status and reason.

Display offsets are disposable. Selection is immediately translated through
the crosswalk into source-block anchor segments before persistence. If that
translation is ambiguous, save the raw selection/capture and mark the anchor
`needs_reanchor`; never discard learner text.

### 3.3 KaTeX and assets

Marker markdown renders math through KaTeX with source text preserved in the
view payload. Extracted figures use immutable asset ids/content hashes. Missing
assets, unsupported TeX, unsafe HTML, or render failure produce a visible
fallback, never a blank or silently altered expression.

Source text is untrusted content. It is escaped/sanitized for display and
delimited as data in model prompts. Script execution, external embeds, and
arbitrary local-file references are disallowed by the reader renderer.

### 3.4 Per-block extraction health

Extend `DocumentBlock`/storage through an additive versioned health artifact,
not an in-place claim that old IR had block quality. Create immutable
`source_block_health` keyed by extraction/span + analyzer version with:

```text
ok | suspect | failed | unknown
```

and reason flags including:

```text
equation_low_confidence
figure_missing_or_misaligned
reading_order_suspect
ocr_character_anomaly
table_structure_lost
text_density_anomaly
geometry_missing
manual_flag
```

Each result stores signal provenance, confidence/status, page-health inputs,
and recommended view. Decision thresholds are registered P0-style decision
parameters.

Reader behavior:

- `ok`: render derived markdown with “view original” available;
- `suspect` with geometry: show derived content plus the original PDF region
  crop adjacent/toggleable;
- `failed` with geometry: default to the original region crop and label the
  extracted text as unreliable;
- no geometry: show a visible warning and original-source link; never imply a
  verified transcription.

The crop is derived on demand from the pinned revision bytes and exact block
geometry. It is not a new authoritative artifact and does not replace the
source hash.

---

## 4. Annotation contract

### 4.1 Stable identity and append-only versions

Create:

- stable `source_annotations`;
- immutable `source_annotation_versions` for learner content/type;
- immutable `source_annotation_anchor_versions` plus ordered anchor segments;
- `source_annotation_events` for create/edit/reanchor/map/disposition/delete-
  intent transitions;
- a rebuildable annotation-head projection.

Deletion is a tombstone/disposition event. Historical versions remain for
audit, restoration, and any already-created commitment/activity provenance.

### 4.2 Anchor shape

An anchor version pins source id, revision id, extraction id, render-view id
used at capture, and one or more ordered segments. Each segment stores:

- block locator/span id and block content hash;
- Unicode code-point start/end offsets against **source-block text**;
- exact selected quote;
- bounded prefix/suffix context;
- page geometry or derived sub-block geometry when available;
- section path and neighboring-block hashes;
- selection text hash;
- capture/reanchor algorithm version and confidence.

Anchor status is:

```text
exact | reanchored | needs_reanchor | orphaned | manually_anchored
```

A multi-block selection stores multiple segments; it is never flattened into a
markdown byte range. Exact quote, prefix/suffix, and learner content are
preserved even when the anchor becomes orphaned.

### 4.3 Annotation content

Launch types:

```text
highlight
question
confusion
interpretation
disposition
```

A version contains verbatim learner text, optional
`what_i_think_is_going_on`, privacy/locality flags, and authorship provenance.
The hypothesis field is a bounded-trust **seed**, not a diagnosis, error label,
or evidence of inability.

Canonical facet/LO/source-object links are separate mapping proposals and never
replace the annotation's wording. Display may show accepted links beside it.

### 4.4 Reanchoring algorithm

On a new render of the same extraction, only rebuild the crosswalk; source
anchors do not change. On a new extraction/revision:

1. reuse existing deterministic block reanchor aliases;
2. within the candidate block, require a unique exact quote match when
   possible;
3. disambiguate duplicates with prefix/suffix, relative offset, geometry, and
   neighboring segments;
4. if source text changed, compute a bounded candidate and confidence but never
   auto-accept an ambiguous match;
5. append an anchor successor with `reanchored` or `needs_reanchor` status;
6. permit an explicit manual anchor event.

Automatic reanchor never changes annotation content or canonical mappings.

---

## 5. Reader modes and action palette

### 5.1 Modes

- **skim:** navigate quickly; enqueue cheap current-unit inventory; surface
  terms/claims/figures and learner questions without forcing prompts;
- **anchor:** full selection, Ask/Practice/Mark, authoring, annotations, and
  source-object context for one section;
- **incremental:** mark valuable/confusing spans for maintenance-feed
  resurfacing; each revisit offers refine, commit, or release. This is not a
  second scheduler/reading queue.

Mode changes append interaction events and influence proposal priority only.
They never alter evidence eligibility.

Modes also gate the owner-placed reader-dialogue questions (U-033, P2 §7.6):
**skim** never presents them (targets are collected for later); **anchor**
presents them at their placed boundaries; **incremental** presents at most
the pretest prime on revisit. Every presented question carries per-question
controls — `skip`, `too_easy`, `too_intrusive`, `ask_me_differently`,
`don't_bring_this_back`, `I don't understand the question` — all
interaction-policy signals, never ability evidence.
`I don't understand the question` routes to source restoration or
instruction, never to a lapse.

### 5.2 Three visible primitives, nine presets

The UI shows three actions:

**Ask**

1. ask a question;
2. request a worked example;
3. request an alternative explanation;
4. ask why this matters.

**Practice / Commit**

5. `test_me_later`;
6. `help_me_remember`;
7. `connect_it`.

**Mark / Disposition**

8. `mark_confusing`;
9. `not_worth_remembering`.

Every action creates/updates an annotation. Only the three commit presets are
P1 commit-class actions. Ask never silently creates a commitment. Mark never
does. `not_worth_remembering` suppresses proposals for this learner and never
deletes a source object/assertion.

`connect_it` records the learner's proposed source/canonical relationship and
creates/extends a commitment whose target is that relationship. It cannot apply
a concept edge.

### 5.3 Local-first capture transaction

Before any model/job call, one local transaction:

1. resolves or records the raw selection and render view;
2. appends annotation/version/anchor rows;
3. appends the typed interaction event;
4. creates/extends a commitment only for a commit action;
5. creates a durable background request/outbox row;
6. returns a capture receipt and visible provisional arc preview.

The response target is local-only latency. A worker outage may leave the
request pending, but the annotation/commitment is already safe and editable.

Client retries use an explicit idempotency key and produce one annotation
version, one interaction event, and one job request.

### 5.4 Ask integration

Ask reuses the existing tutor-QA service with exact selected segments and a
bounded neighboring window. Persist:

- learner question/preset and annotation id;
- exact context manifest sent;
- answer and validated citations;
- provider/model/prompt/schema provenance;
- relation to the source revision and optional commitment;
- learner follow-up/correction events.

The exchange is learner/AI-authored source material, not author-authored
content. It is hidden during cold activities and may become a source object or
commitment target only through explicit capture/review.

Ask runs in the `reader` tutor context (U-033, P2 §7.6) with the
per-ask answer-mode choice (`answer_directly` / `help_me_reason` /
`ask_me_first`); P3 adds annotation linkage and **inquiry-thread
projection**: exchanges on the same annotation/target project into a durable
thread with status `open` / `partially_resolved` / `resolved` / `deferred` /
`no_longer_relevant`. A later failure, question, or contradiction may reopen
or branch a thread — one plausible answer never permanently settles the
question, and thread resolution claims nothing about the underlying
capability.

### 5.5 Practice/commit integration

- `test_me_later` creates/extends a commitment with disposition
  `one_check_pending` and one delayed cold administration contract;
- `help_me_remember` creates/extends an ongoing commitment and proposes a
  P1 pattern/arc appropriate to the selected content and chosen depth. The
  capture UI asks the learner to choose `hold_at_target`, `suggest_next`, or
  `auto_within_envelope` and previews the resulting envelope before its single
  confirmation;
- `connect_it` preserves both endpoints and learner explanation, proposes a
  typed relation, and creates/extends a relationship commitment; its chosen
  depth policy/envelope/disposition determines whether it schedules an activity.

No card is created until target, purpose, and ActivityContract are sufficiently
specified. A capture may remain a useful annotation/commitment while proposals
are pending or rejected.

### 5.6 Mark/disposition integration

`mark_confusing` creates a question/confusion annotation and optional
hypothesis seed. It raises proposal/Ask priority and can request a cautious
measure-mode prior later; it never lowers a learner-state estimate.

`not_worth_remembering` writes a learner disposition for the annotation/source
target. It suppresses future generation/maintenance suggestions at that scope
unless explicitly reversed. It does not alter source-object truth or another
commitment with a narrower explicit target.

---

## 6. Demand-paged synthesis

### 6.1 Two first-class entry paths

- **Build me a path:** existing source-set scope, inventory, and batch
  synthesis remain unchanged.
- **I'm reading:** enqueue only the current block neighborhood/unit and actions
  that need semantic work. Results accumulate as proposals and never interrupt
  reading with mandatory review.

Both use the same inventory/synthesis caches and proposal schemas. Reader work
must not duplicate a result already built by batch flow.

### 6.2 Durable idempotency key

Create `reader_background_requests` keyed by the canonical hash of:

```text
source revision
block span or deterministic window
reader action/preset
inventory schema + profile
synthesis/output schema
prompt + provider + model version
relevant config/policy hash
```

The key includes the revision—not a mutable “current source”—and exact model
contract. Same request reuses the standing/completed result; a material version
change creates a successor request.

States are `queued`, `running`, `complete`, `partial`, `failed`, `cancelled`,
or `obsolete`. Cancelling a job never cancels/deletes the local capture.

### 6.3 Neighborhood and budgets

Resolve the smallest sufficient window:

- exact selected blocks;
- enclosing section heading;
- bounded adjacent blocks needed for references/equations;
- cited figure/table assets;
- no unrelated chapter content.

Visible request metadata includes selected scope, estimated/actual input/output
tokens, provider/model, reason, cache hit, cap remaining, and status. Exceeding
a cap keeps the capture and offers local/manual handling; it never silently
expands scope or sends the whole source.

Reader requests receive interactive priority above bulk jobs but are bounded so
rapid scrolling cannot starve an explicitly running batch. Deduplicate/cancel
obsolete prefetch as the reading neighborhood changes.

### 6.4 Proposal behavior

Background results may propose:

- source objects and relations;
- mappings to existing facets/LOs;
- genuinely new facet/LO proposals when existing objects cannot represent the
  target;
- P1 families/cards/surfaces for an explicit commitment;
- annotation tags or a starter authoring template.

Nothing is silently applied while reading. Existing safe auto-apply behavior
from unrelated batch ingest does not apply to reader-triggered canonical
changes. Proposals queue for exception review and may be accepted later from a
non-modal inbox or the relevant annotation/card.

---

## 7. Source objects and mappings

### 7.1 Source-object layer

Create stable `source_objects`, immutable `source_object_versions`, citations,
and review events. Types:

```text
claim
definition
procedure
worked_example
problem
proof_move
motif_or_passage
artifact
```

Every version is per source revision and span-cited. It stores authorial role,
salience proposal, exact text/structured content, authorship provenance, model
provenance when rendered, and status:

```text
proposed | reviewed | rejected | superseded
```

Inventory output begins `proposed`. An explicit learner-authored capture may be
durable immediately as learner content but still has a proposed canonical
mapping. A source object is not a cross-source truth claim.

### 7.2 Relations

Create versioned `source_object_relations` with:

```text
supports
contradicts
refines
alternate_definition
unresolved
learner_connects
```

Relations name authorship and review status. `learner_connects` preserves the
learner's wording and remains a proposal unless reviewed into another relation.
This schema supplies future syntopic data without shipping syntopic UI.

### 7.3 Canonical mapping proposals

Mappings from source object/annotation to facet, LO, blueprint, or commitment
target are append-only proposals with confidence/status/rationale/provenance.
Accepting a mapping does not overwrite the source object. Rejecting one does
not suppress alternative mappings or delete the annotation.

New canonical objects require the existing proposal/gate/review path. The
reader cannot create a transcript-shaped graph merely because content was
visible or highlighted.

---

## 8. Reading signals and interaction events

### 8.1 Typed envelope

The append-only `interaction_events` envelope is created by P0 (U-013), which
already logs attempt durations and retirement reasons; P3 adds the reader
event kinds below. If P3 arrives first, create the envelope to the P0
contract. The envelope carries:

- id, occurred/received time, actor, client/session/visit ids;
- event type and payload schema version;
- source/revision/render/locator/annotation/commitment/activity refs;
- canonical payload JSON/hash and client idempotency key;
- privacy/locality and consent context;
- producer/app/policy versions;
- optional supersedes/correction event id.

Launch reader event types include open/close, mode change, span visible,
selection, highlight, annotation edit, action invoked, capture acknowledged,
job queued/completed, proposal accepted/edited/rejected, source restored,
authoring coach response, affect/disposition actions, depth policy/envelope
confirmed or changed, milestone reached, automatic edge committed/blocked, and
automatic depth paused.

Corrections append; raw event timestamps are not rewritten. High-value domain
tables remain authoritative for their own contracts; the envelope is the
cross-journey corpus/telemetry stream, not a replacement for administrations,
observations, annotations, or commitments.

### 8.2 Signal aggregation

Do not log high-frequency timer ticks. Clients emit bounded visibility segments
with foreground state and end reason. A versioned salience projector derives:

- highlight/question/revisit counts;
- bounded dwell estimates;
- skip/skim and explicit-interest signals;
- proposal priority and depth suggestions.

The evidence ingestion API rejects every event/signal with authority class
`salience_only`. There is no numeric conversion path from dwell/highlight to
correctness, mastery, capability evidence, diagnosis, or certification.

“I already know this” creates a low-authority learner claim usable to prioritize
a cheap cold check; it does not mark the target demonstrated.

---

## 9. Learner authoring and in-review maintenance

### 9.1 Q+A flow

From an optional annotation/span, the learner writes the question **and**
answer. This content persists before AI assistance. LearnLoop may propose:

- existing facet/LO/source-object mapping or a new-object proposal;
- capability, task features, pattern/family attachment;
- rubric/evidence weights and fingerprint memberships;
- source citations and sibling/duplicate warnings.

One confirmation creates a learner-authored P1 card and pinned surface under an
explicit commitment. The learner's exact surface remains preserved. A family
may later mint non-learner-authored siblings for transfer.

### 9.2 Formulation coach

The coach is a non-blocking scale:

- novice: questions about atomic target, useful discrimination, common shallow
  response, and desired retention;
- middle: a starter prompt/template the learner must adapt/complete;
- expert: freeform plus post-hoc lint for ambiguity, duplicate fingerprint,
  granularity, missing context, and rubric mismatch.

Lint never prevents acceptance. It records suggestions and the learner's
accept/edit/dismiss response for future corpus analysis, not a learned live
policy.

### 9.3 Fluid maintenance

From the review/feedback screen the learner can:

```text
edit wording
split one card into many
merge many cards into one
spawn a sibling/new angle
retire card/family
change commitment depth policy/envelope/disposition
```

These actions use P1 lineage classification. Already-administered versions
remain immutable. Split/merge never combines scheduling/certification blindly;
new lineages receive explicit evidence-informed priors only. A cosmetic edit
may retain card state when the classifier proves it surface-preserving.

Learner-authored “exhaust” is expected. Retirement UX frames culling as the
understanding/collection evolving and preserves all evidence/intent history.

---

## 10. Unfolding arcs and primes

### 10.1 Versioned arc program

Create stable `commitment_arcs`, immutable `commitment_arc_versions`, and
append-only `commitment_arc_events`. An arc version references P1 patterns and
declares conditional transitions such as:

```text
comprehend -> complete -> retrieve -> discriminate -> integrate -> transfer
-> revisit from a new perspective
```

It is a program/state machine, not a precomputed set of due dates. Arc state is
a projection over:

- **memory time:** card/readiness decay and due constraints;
- **arc time:** intended stage and evidence-gated progress.

The arc never hard-gates continued reading. It schedules learning attention
inside the learner's commitment/burden contract.

Arc versions pin the P1 depth-policy/envelope version and map each arc stage to
a reviewed depth-milestone edge. The arc projector may record an achieved stage
and request one P1 automatic transition; it cannot create an edge, widen an
envelope, or transfer scheduling state across a card fork.

### 10.2 Visible promise and depth

Immediately after a commit, show a provisional plan such as “cold check in two
days; explain from memory next week; apply later,” with the explicit caveat
that evidence and burden may adapt it. The four P1 depth presets parameterize
arc stages and budget; they do not create item-by-item approval fatigue. Beside
the plan show:

```text
policy: hold | suggest | auto within this envelope
current milestone and previously reached milestones
envelope summary: capability / transfer / span / representation / scaffold
next reviewed edge, evidence gate, expected burden, and fresh-proof requirement
pause, reduce envelope, change policy, or stop
```

With `auto_within_envelope`, satisfying an exit gate may activate one displayed
edge without another prompt. The activation remains a normal P0/P1 successor
transaction: material cards fork, prior milestone success stays visible, and a
new terminal-support reserve is required when applicable. The UI says “next
stage activated”, never “your previous goal was too easy.”

`wanted_more_depth` prioritizes/evaluates the displayed edge when it is already
inside the active envelope. If it would cross the envelope, it opens an editable
commitment/envelope successor proposal and requires confirmation. The affect
signal alone has no authorization or learner-state authority.

### 10.3 Pretest as prime

A learner question from section N may be offered before section N+1 as an
opt-in prime. If answered:

- administration context records immediate source proximity and priming;
- evidence is heavily tempered/no cold credit according to the P1 pattern;
- the result may adjust low-authority priors but cannot satisfy delayed
  certification;
- source and annotation remain hidden until response/give-up.

The same interaction may help encoding and measurement, but its dual-use
context is explicit rather than laundered as cold proof.

---

## 11. Restoration contract

After a cold administration is submitted and its measurement segment closes:

1. resolve criterion/facet/card provenance to source blocks;
2. resolve relevant annotation heads and anchor statuses;
3. show exact learner wording alongside source text, never merged into it;
4. show tutor/source-object provenance labels;
5. record source restoration/exposure and instructional context;
6. allow edit/commit/Ask without changing the closed observation.

If an annotation needs reanchor, show its quote/context in an “anchor needs
review” panel rather than attaching it to uncertain text. If the source block
is unhealthy, use §3.4 fallback.

Opening restoration material before response appends a contamination/feedback
exposure event and changes eligibility. The learner is never trapped in a cold
task to protect a metric.

---

## 12. Service and product interfaces

Required service boundaries:

- resolve/create immutable render view and block crosswalk;
- calculate/read block health and render original-region fallback;
- translate selection to source anchor, append annotation/content/anchor
  successor, manually reanchor, and inspect history;
- capture Ask/Practice/Mark locally and enqueue outbox work atomically;
- resolve/dedupe/execute reader background request on existing ingest/synthesis
  workers;
- author/review/link source objects and mapping/relationship proposals;
- aggregate salience signals while rejecting evidence use;
- create learner-authored pinned card and run non-blocking lint;
- edit/split/merge/spawn via P1 lineage services;
- create/project/advance an unfolding arc and request one P1-authorized depth
  edge after a qualifying milestone;
- restore source/annotation after a closed administration.

The delivery surface for this contract is the Tauri desktop app + Python
sidecar; screen inventory, design-language rules, and fixture strategy are
owned by `spec_tauri_ui.md` (U-031).

Minimum reader RPC/UI contract:

- open source at revision/unit/span and select skim/anchor/incremental mode;
- page/scroll current neighborhood without requiring synthesis;
- create/edit/delete-intent/reanchor an annotation;
- invoke each action preset and receive immediate local receipt;
- inspect/cancel/retry background work and token/cap usage;
- review accumulated proposals without losing reading position;
- author Q+A with optional coach and one confirmation;
- inspect visible arc, reached/current/next milestones and envelope, then change
  policy/depth/disposition or pause automatic progression;
- open original region/source from every block;
- return from cold review into exact source/annotation context.

Reader state (position, mode, open annotation/editor) persists per
source revision and client, but is UX state—not source truth or evidence.

---

## 13. Migration, coexistence, and failure behavior

### 13.1 Additive migration

1. Add render views/crosswalk and create one marker view per actively opened
   extraction lazily, not through an eager whole-library migration.
2. Add block-health rows as `unknown` until analyzed; preserve page health.
3. Add annotation/version/anchor/event tables with no fabricated historical
   highlights.
4. Add source objects/relations/mapping proposals; import existing span-cited
   inventory claims/problems as `proposed` with original provenance.
5. Register reader event kinds on the P0-owned typed interaction envelope
   (U-013); do not copy content mutations into it as if they were learner
   interactions.
6. Extend source-exposure contexts through a table migration while preserving
   every historical row/id.
7. Add reader request links to existing ingest batches/shard cache.
8. Add arc/authoring projections and P1 adapters when P1 is installed.

### 13.2 Coexistence

- existing batch source-set/quick-add flows remain first-class;
- existing read-only `span_view` callers continue to work and record exposure;
- P2 restoration may consume P3 annotations immediately after P3 lands;
- without P1, annotations and local captures still work; commit actions may
  adapt to a legacy fixed PracticeItem only behind an explicit compatibility
  mode and later upgrade losslessly;
- reader-triggered proposals never change an in-flight P2 goal contract,
  diagnostic episode, or assessment reserve.

### 13.3 Failure behavior

- marker unavailable/fails -> readable original/text fallback, capture still
  available where block locators resolve;
- render/crosswalk mismatch -> save raw selection + text as `needs_reanchor`;
- block health suspect -> original region visible/default per §3.4;
- local transaction failure -> return no acknowledgement and enqueue no job;
- job/model failure -> retain capture/commitment, show retry/manual option;
- cap exceeded -> retain capture, no silent scope expansion;
- source revision changes -> keep old anchor/version and append reanchor result;
- ambiguous reanchor -> `needs_reanchor`, never guessed attachment;
- missing P1 pattern/family -> commitment remains active with `authoring_needed`;
- stale/outside envelope or missing reviewed next edge -> preserve reached arc
  milestone, show a proposal/block reason, and do not auto-activate;
- proposal rejected -> preserve annotation/commitment and rejection rationale;
- AI answer has invalid citations -> store failed result for audit, do not
  present it as grounded;
- opening source during cold work -> record contamination and switch to
  instructional/restoration context;
- interaction telemetry unavailable -> core domain write succeeds through a
  durable outbox or fails atomically when the event is part of the capture
  receipt; never acknowledge a capture that can vanish.

---

## 14. Implementation order

1. Add render-view/crosswalk contracts and marker markdown/KaTeX reader with
   safe fallbacks.
2. Add per-block health analysis and original-region rendering.
3. Add annotation/version/anchor/event storage plus deterministic/manual
   reanchoring.
4. Add reader event kinds to the P0-owned `interaction_events` envelope
   (U-013) and the atomic local-first capture/outbox service.
5. Ship the three-action/nine-preset palette with Ask integration.
6. Add reader background request keys, priority/caps, and reuse of inventory/
   synthesis caches.
7. Add source objects, relations, and exception-review mapping proposals.
8. Add commit integration, learner Q+A, pinned surfaces, coach lint, and fluid
   P1 maintenance actions.
9. Add unfolding arcs, visible depth policy/envelope controls, one-edge automatic
   transition adapter, primes, and salience-only projection.
10. Add post-cold restoration and Journey 1/2/7 acceptance suites.

The local-first capture/annotation path must pass crash tests before any model
button is exposed in the reader.

---

## 15. Test and acceptance contract

### 15.1 Render and anchors

- bytes/revision hash remains unchanged by extraction/render upgrades;
- a marker re-render changes only render/crosswalk versions, not source anchors;
- single- and multi-block selections round-trip exact source text;
- duplicate quote matches use context or become `needs_reanchor`;
- changed/removed blocks never silently steal annotations;
- manual reanchor appends a successor and preserves old anchor;
- every healthy/suspect/failed block exposes the required original affordance;
- suspect equation/figure defaults to the correct region fallback;
- unsafe source HTML/scripts cannot execute.

### 15.2 Capture and actions

- kill the worker/process after local commit but before enqueue delivery: the
  annotation/commitment/request survives and resumes once;
- retry the same client key: no duplicate annotation version, interaction
  event, commitment, or job;
- Ask and Mark never create commitments;
- all three commit presets use distinct semantics;
- `connect_it` cannot create a canonical edge;
- `not_worth_remembering` suppresses proposals but deletes no source object;
- learner text remains byte-for-byte/verbatim through AI results and mapping.

### 15.3 Demand paging

- opening a source/scrolling works with all model workers disabled;
- one action sends only its deterministic neighborhood and asset manifest;
- identical request contracts hit cache across reader/batch paths;
- model/schema/revision changes create new request identity;
- rapid navigation dedupes/obsoletes prefetch without starving active work;
- caps and actual token usage are visible;
- no reader result silently applies a canonical/family change.

### 15.4 Reading-signal firewall

Attempt to feed every reading event and salience projection into mastery,
probe, readiness, and certification APIs; each must reject or assign zero
evidence by type. Highlights/dwell may reorder proposals only. “Already know”
may schedule a cold check but cannot mark a cell demonstrated.

### 15.5 Authoring and maintenance

- Q+A persists before coach/model work and confirms once;
- coach suggestions are dismissible and never block acceptance;
- learner-authored surface is pinned and provenance-labeled;
- an AI sibling never impersonates learner/source authorship;
- cosmetic edit retains state only through P1 classifier;
- material edit/split/merge/spawn creates proper lineage and no blind
  stability/certification transfer;
- retirement preserves commitment/evidence and reader provenance.

### 15.6 Cold restoration

- cold administration hides source, annotations, tutor exchanges, and purpose;
- opening them early appends contamination and removes cold eligibility;
- after close, exact cited blocks and annotation heads restore;
- orphaned annotation shows quote/context without false attachment;
- restoration records source exposure and cannot mutate the observation.

### 15.6.1 Arc and depth authorization

- a capture shows policy, envelope, current/reached milestone, next reviewed
  edge, evidence gate, burden, and pause/stop controls;
- `hold_at_target` and `suggest_next` never activate an edge automatically;
- `auto_within_envelope` can request exactly one reviewed inside-envelope edge
  after qualifying evidence, and material successor cards fork without FSRS or
  certification inheritance;
- the prior milestone stays visibly reached after progression;
- `wanted_more_depth`, dwell, highlight, question, and affect events cannot
  widen an envelope; outside-envelope growth requires a confirmed successor;
- pausing/shrinking the envelope before the next administration prevents that
  uncommitted transition and leaves the capture/arc intact.

### 15.7 Journey 2: quick insight capture

From an already imported chapter:

1. select a passage and write an interpretation;
2. choose `help_me_remember`;
3. receive durable acknowledgement and visible arc immediately;
4. continue reading while one bounded proposal job runs;
5. accept/edit 1–2 activities with no more than one confirmation;
6. receive a delayed cold retrieval;
7. after submission, restore exact source + personal annotation;
8. complete the capture flow in under one minute of learner administration,
   excluding reading/thinking/model wait.

### 15.8 Journey 1: reading-first first session

A new learner imports/opens one source, begins reading without building the
whole path, makes one Ask and one commit, sees transparent background status,
and leaves with a durable annotation/commitment/arc. No mastery or diagnosis is
claimed from reading behavior.

### 15.9 Journey 7: tutor exchange to durable knowledge

Ask from a span, receive a citation-valid answer, add the learner's own Q+A or
interpretation, explicitly commit it, accept a pinned activity, and later
review it cold with the tutor exchange hidden. Afterward, restore the exchange
with AI/source/learner provenance clearly distinguished.

### 15.10 Replay and operations

- annotation/arc/salience heads rebuild after cache corruption;
- render and background requests are idempotent on repeated migration/run;
- interaction-event corrections append and projections select the active head;
- a 100k-event reader corpus query remains bounded by indexed source/session/
  event-type paths;
- reader stays navigable during ingest/model outage;
- no migration alters legacy source/revision/block ids or content-event rows.

---

## 16. Launch defaults and explicit assumptions

- Marker markdown + KaTeX is the only P3 rich reader view; original-region
  fallback is mandatory, not a second full reader implementation.
- Block health begins conservative/heuristic and is visible. Unknown health is
  not “healthy.”
- Capture channels are in-app selection, paste, and command palette only.
- Incremental reading uses the maintenance feed and P1 arcs; it does not create
  a new due queue.
- Reader `test_me_later` defaults to `hold_at_target`; ordinary ongoing captures
  default to `suggest_next`. A reader may explicitly choose
  `auto_within_envelope`, while P2 end-of-chapter commitments may arrive with its
  already confirmed recommended envelope.
- Automatic arcs commit at most one reviewed edge per transition and reproject
  before another. The reader never expands the envelope on the learner's behalf.
- Proposed source objects/mappings accumulate for exception review; none are
  silently applied while reading.
- Reading signals are salience-only forever unless a future spec introduces a
  separately validated measurement interaction. This spec grants no such path.
- P3 may run without the P2 golden path, but when P0/P1/P2 are present it uses
  their commitments, administrations, exposure, lineage, and restoration pins
  rather than compatibility substitutes.

---

## 17. Change log

- **2026-07-21** — **P3 code landed (slices 1–3).** Migrations 088–095:
  render views + crosswalk (088), per-block health (089), annotations + anchor
  versions/segments (090), `interaction_events` reader envelope + capture outbox
  (091), source-exposure reader/restoration contexts (092), demand-paged
  `reader_background_requests` (093), source objects/relations/mapping proposals
  (094), and **`commitment_arcs` + `_arc_versions` + `_arc_events` (095)**.
  Services: `source_render_views`, `block_health`, `annotations`,
  `reader_capture`, `salience_firewall`, `reader_requests`, `source_objects`,
  and — new in slice 3 — `commitment_arcs` (arc program composed with P1
  commitments/depth; at-most-one reviewed inside-envelope transition via
  `depth_transition.commit_one_edge`; never creates an edge or widens an
  envelope), `reader_authoring` (Q+A persists before AI → learner-authored P1
  card + pinned surface under an explicit commitment; non-blocking coach; fluid
  maintenance via P1 lineage), and `reader_restoration` (post-cold restoration
  composing the P2 `golden_path_restoration` seam; learner wording alongside
  source; `needs_reanchor`/orphaned → review panel; salience-only events). The
  salience projector v1 (`salience_firewall.salience_projection_v1`) emits
  `salience_only` outputs feeding proposal-priority / depth-suggestion ONLY.
  Five-layer RPC (`reader.*` sidecar handlers, Tauri passthroughs, TS client,
  ReaderScreen arc/coach affordances). Acceptance: Journeys 1/2/7, salience
  firewall (parametrized over the reader kind vocabulary + projector),
  annotation survival across re-extraction, and replay determinism — all green.
  **Adopted defaults** (pending owner confirmation, per the P3 design memo §A.3):
  reader `test_me_later` → `hold_at_target`, ordinary ongoing → `suggest_next`
  (§16); the three salience depth-suggestion weights registered structural
  (salience-only, no measurement authority). **Deferrals unchanged:** U-017@v3
  (`ask_now` planner + automatic density) and U-036 (non-text renderers) are NOT
  in P3; live `auto_within_envelope` activation stays behind the U-018 gate
  (`depth_transition.LIVE_ACTIVATION_ENABLED = False`).
- **2026-07-20** — **F2: "I already know this" cold-check claim deferred.** The
  §8.2 low-authority *already-know* claim (prioritizes a cheap cold check; never
  marks the target demonstrated) is NOT implemented in P3. There is no
  `already_know` event kind or projector branch, so the `already_know_claim`
  output of `salience_firewall.salience_projection_v1` was permanently empty and
  has been removed (along with its `SALIENCE_PROJECTIONS` entry). It will return
  when the cold-check **proposal** path is built — still `salience_only`, never
  evidence. All other §8.2 salience outputs are unchanged.

### 2026-07-20 — Reader opens real library sources (fixture demoted to labeled demo)

- `reader.render_view` resolves ANY ref (extraction / revision / source-artifact
  id) via `resolve_extraction_id`, so the library can open a source directly.
- Desktop ReaderScreen front door is now a picker over ready library sources;
  the symmetric-decomposition fixture is reachable only as an explicitly labeled
  "offline demo", its hard-coded boundary question renders only there, and the
  offline capture copy no longer claims durability. Per-source panel state resets
  on source switch.
- The `tutor_qa.reader_enabled` opt-in gate (L8) is unchanged and now surfaced
  honestly in the picker instead of being masked by a silent fixture fallback.
