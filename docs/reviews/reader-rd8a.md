# Reader workbench v2, RD8a: pen and ink, the backend half

The backend half of stage RD8a of `docs/specs/spec_reader_workbench_v2.md` (§3.4, §10.4, §10.10, §10.11, §15, §16's
RD8a row). Branch `reader/rd8a-ink-backend`, from origin/main `ba7884c102` (migration head 266, latest tag mvp-0.68).
The owner moved pen mode ahead of RD7 on Nov 23, so nothing here depends on inline checks. The frontend half (pen input,
the recognizer on sources, ink pads, barrel erase, palm rejection, the editable transcription) follows on the contract
in `client.ts`/`dto.ts`.

**What it delivers.** Migration 267 (`ink_strokes` RAW_LEDGER, `ink_transcriptions` RECEIPT); `ink.save` through the
write protocol and the `erase_ink` pad op; `ink.list` (a pad's or a source's ink); `ink.transcribe` /
`ink.transcribe_job` / `ink.transcribe_cancel` (a polled, cancellable, vault-scoped job); a deterministic server-side
renderer; the `ink_transcription` paid route; emission of readings as transcribed learner text through RD4a's
contract; Rust passthroughs and typed `client.ts`/`dto.ts`. No UI component, no kill switch, no algorithm tag, nothing on
the phone, no live model call (fakes only).

**Stopped, as the brief says to:** the help ladder for ink in problem pads (§5 below) needs more than the existing hint
path with a new surface value.

## 1. What landed, per spec item

| Spec item | Where |
|---|---|
| §15.1 `ink_strokes` (and a reading's receipt) | `migrations/267_reader_workbench_ink.sql`; roles in `db/table_roles.py`; SQL in `db/stores/ink_strokes.py` |
| `ink.save`, `erase_ink`, the reads | `pads/ink.py`; the op's model and dispatch in `pads/blocks.py` (additive: one op class, one union member, one branch) |
| Strokes to an image | `pads/ink_render.py` |
| `ink.transcribe` and its route | `pads/ink_transcribe.py`; route task in `ai/routing.py`, `ai.routing.ink_transcription` in `config/schema.py`, its disclosure in `ai/disclosures.py`, its price in `ai/plan_fallback.py`, the shared envelope in `workbench/check.py` |
| The RPCs | `learnloop_sidecar/handlers/ink.py` |
| Rust, typed client | `src-tauri/src/commands.rs`, `main.rs` (five commands); `src/api/client.ts`, `src/api/dto.ts`; `erase_ink` in the pad model's optimistic apply (`screens/desks/pads/model.ts`, which must stay exhaustive) |
| Fences | `learnloop.db.stores.ink_strokes` joins the four workbench v2 contracts that list the pad stores (`pyproject.toml`) |
| Desktop only | `tests/test_mobile_allowlist.py` (`READER_RD8A_RPCS`, pinned to `INK_RPCS`) |

Pad files touched (RD4's fix round edits the same area): `src/learnloop/pads/blocks.py` only, additively. Not touched:
`handlers/pads.py`, `pads/emission.py`, `pads/submission.py`.

## 2. The RPCs

Every params model is `extra="forbid"` (nested models too) and every reply `versioned`.

| Method | Input | Reply |
|---|---|---|
| `ink.save` | `{clientId, seq, owner: {blockId} \| {annotationId} \| {extractionId}, inkId, strokes: [{strokeId, points: [[x, y, t, pressure, tiltX, tiltY], ...]}], pointerMeta: {pointerType: pen\|mouse, devicePixelRatio?}}` | `{appliedSeq, inkId, results: [ok{duplicate} \| refused{code}]}` |
| `ink.list` | `{padId}` or `{sourceId}` | `{padId, sourceId, owners: [{ownerKind, ownerId, contentHash, devicePixelRatio, strokes: [{strokeId, inkId, points}], transcription: {transcriptionId, latexMd, confidenceLabel, contentHash, current, createdAt} \| null}]}` |
| `ink.transcribe` | `{inkId}` | `{jobId, status, done, result, error}` at once |
| `ink.transcribe_job` | `{jobId}` | the same, at once (never a wait) |
| `ink.transcribe_cancel` | `{jobId}` | the same |
| `ink.erase` | `{clientId, seq, owner: {annotationId} \| {extractionId}, eraseId, strokeIds}` | `{appliedSeq, eraseId, results: [ok{duplicate} \| refused{code}]}` |
| `pad.apply` op `erase_ink` | `{op: "erase_ink", blockId, strokeIds, eraseId?}` | `ok{eraseId}` or `refused{code}` |

**Ink on a source's page** (owner kind `source`, added to migration 267 before it landed anywhere; the owner id is the
reading's extraction id): what the learner draws on a source that becomes no mark. `ink.save` takes it (the reading
must exist: `reading_not_found`; the receipt filed under no pad, as an annotation's ink); `ink.list {sourceId}` returns
it after the annotations' ink, one owner per reading of the source; `ink.erase` tombstones its strokes (also an
annotation's; a block's ink stays `pad.apply`'s `erase_ink`: `erase_in_the_pad`), idempotent by `eraseId`. **It is the
learner's marks, never learner text:** `ink.transcribe` refuses it (`not_read`), `ink_transcriptions`' `owner_kind`
CHECK has no `source`, and nothing emits it (it is in no block); it becomes words only if the learner makes it a note.
Pinned by `tests/test_reader_rd8a_transcribe.py::test_ink_on_a_page_is_never_read_nor_learner_text` and the migration's
constraint test.

**`ink.save` and the write protocol.** One save is one batch in the client's one sequence with `desk.apply` and
`pad.apply` (spec §3.5: one outbox): a gap is `seq_gap`, a repeated `seq` returns the stored reply, the same `seq` with
other strokes is `seq_reused`. The receipt is a pad-channel receipt (`pad_op_receipts`, no new receipt table), filed
under the owning block's pad, `''` for a margin note's ink. `inkId` and `strokeId` are client-minted: a resent `inkId`
with the same owner and strokes is `ok{duplicate: true}`, with anything else `ink_id_reused`; a `strokeId` already
saved for the owner is `stroke_exists`. The owner must be a standing ink block of an unarchived pad
(`block_not_found`, `block_removed`, `not_an_ink_block`, `pad_archived`) or an existing annotation
(`annotation_not_found`). Touch is refused by the params (`pointerType` is `pen` or `mouse`, spec "touch never
draws").

**Storage.** Lossless: the points as sent, `zlib` over their canonical JSON (`encoding = 'zlib-json-v1'`), with
`content_hash` (sha256 of that JSON). Nothing is quantized or thinned: a precision or a thinning tolerance would be a
constant nobody chose. Values are checked finite, pressure in 0..1 and tilts in -90..90 (the Pointer Events ranges).

**Standing strokes.** An owner's ink is every save's strokes in write order (`rowid`; the table refuses deletes)
without the strokes an erase row names. `content_hash` of the standing strokes (`ink.strokes_hash`) keys a reading.

**`ink.list`.** For a pad: its standing ink blocks with ink, in block order. For a source: its listed annotations
(`annotations_for_source`, so a deleted note's ink is not listed) with ink.

## 3. Transcription: route, consent, storage

**Rendering** (`pads/ink_render.py`): the standing strokes drawn with the spec's pen (§4.2: `#2b4fa8`, 2.2 px) on the
paper they were drawn on (pad `#fdfdfc`, source `#f7f5f0`), at the finest device pixel ratio the owner's saves report
(default one device pixel per CSS pixel), cropped to the strokes with one pen width of margin (so a round end is not
cut), round joins and ends, a one-point stroke a dot, no antialiasing, PNG without timestamps: the same strokes give
the same bytes (a test pins the digest of a fixed synthetic input under the locked Pillow). Bounds come from existing
limits: Pillow's own `Image.MAX_IMAGE_PIXELS` for the canvas and the transport's `MAX_IMAGE_BYTES` for the file
(`ink_too_large` past either).

**The route.** A new paid role, `ink_transcription` (`ai.routing.ink_transcription`; empty: `ai.active_provider`, the
ChatGPT plan), planned and resolved by `practice_index.paid.plan_route` / `resolve_client` like every paid role:

- a ready plan serves first;
- **OpenRouter only after the learner's OK, enforced server-side**: with the plan unavailable, the route reports
  unavailable and makes the "Use OpenRouter instead" offer; only the learner's grant (`plan_fallback`) plans it onto
  OpenRouter, and every request is admitted against the one OK to use AI (`model_use.admit` in `model_call`). The
  generic `tests/test_plan_first_transport_paid_roles.py` runs over every `AITask`, `ink_transcription` included
  (resolves to the plan and asks before OpenRouter; a grant routes to OpenRouter priced as metered; a ready plan
  first). The offer relays through the poll that finds the job finished (`plan_fallback.relay_job_offer`), as the
  companion's;
- the image is refused before anything is sent when the resolved model cannot read images (`cannot_read_images`);
- metered: held to `workbench.price_per_million` (unset: `unpriced`, and no OpenRouter offer) and the workbench's daily
  envelope, which now counts these calls with the step checks' (`ENVELOPE_OWNER_KINDS`), the step check's runaway
  bounds (`CALL_CAPS`), `LEARNLOOP_WORKBENCH_MODELS=off` honoured;
- an isolated turn: the image and the instructions, nothing else (no vault, files, tools or learner history).

**The prompt** (`ink_transcription.v1`): fixed instructions (write out exactly what is written as Markdown with LaTeX,
keep the learner's notation and mistakes, never correct or explain, empty when there is no writing) and, last, the
image's media type and sha256. Naming the digest follows `PaidCalls.call`'s documented rule ("a caller with images
names their digests in the prompt"), so a paid checkpoint never answers another image. Result schema
`InkTranscriptionV1 {latex_md}`.

**Kept once.** `ink_transcriptions` holds one reading per owner and standing strokes (UNIQUE `(owner_kind, owner_id,
content_hash)`): `ink.transcribe` on strokes already read answers at once with `done` and no job, sending and
spending nothing, whatever model is routed now; a race between two jobs keeps the first row. The row names its task,
provider, model and prompt version.

**`confidence_label`.** `may_be_wrong` for every model reading, `nothing_read` when it read no writing. The spec gives
no vocabulary; its own words are "transcription may be wrong · fix it", no calibrated confidence exists, and a graded
label over a model's self-report would be a made-up threshold. Options for a graded label are in §6.

**Into the block.** A block owner's reading becomes the block's next version: `body_md` the reading, provenance
`ink_transcription`, `payload.ink_transcription = {transcription_id, content_hash, confidence_label}` (the rest of the
payload kept), `client_id = 'learnloop:ink_transcription'`. Not written when the block stands removed
(`block_removed`) or its head is the learner's correction (`kept_your_correction`): the learner's words are never
overwritten, and the reading is returned for the client to offer. The learner's edit of an ink block is a version of
provenance `learner_correction` (`pads.blocks`, RD0). A margin note's reading is kept and returned, never written into
the annotation: the note's text is the annotation's own, written by the client through the annotation's edit.

**The job.** `polled_jobs` on a thread the context owns; the shared polled-jobs registry keyed by vault (RD3's fix round), so a poll from
another vault answers `job_not_found`, and a vault switch interrupts a running job (its next request is refused). A second ask for
the same owner and strokes while a job runs joins it; after a failure or a cancel a new ask starts a new job.
Cancelling refuses the next physical model request before it is sent; a request already sent finishes and its reading
is kept (the poll still reads `cancelled`). Failures as the poll says them: `cannot_read_images`, `models_off`,
`unrouted`, `unpriced`, `capped`, `unavailable`, `provider_unavailable` (after the retry cap), `ink_too_large`,
`waiting_for_ok`, `cancelled`, `interrupted`. Request-time errors: `ink_not_found`, `block_removed`,
`annotation_not_found`, `nothing_to_read` (every stroke erased).

## 4. Emission and persisted meaning

A reading written into its block is committed learner text: the handler settles it through `pads.emission`
(`settle_blocks`, then proposals), as `pad.apply` does after a batch. RD4a's contract already emits `ink` blocks of
provenance `ink_transcription` or `learner_correction` with `transcribed: true` in the frozen snapshot; a correction
supersedes the gap read from the reading, a removal retracts it, quoted text and the fences are unchanged, and the
gap's passages follow the block's links (live equals rebuild). Tested through the reading path.

**Persisted meaning: none** (the playbook's step 1, "decide whether the change alters persisted meaning"). Which ink
words are learner text, and what they may do, was decided by mvp-0.68 (`pads.emission.EMITTED` names the two ink
provenances); this step writes rows that rule already covers and changes no rule. No vault holds an ink row before
migration 267, so no existing row is read differently, and no tag, upgrade row or effective default moves. §15.3's
RD8a row says the same.

## 5. The help ladder: stopped, with what it needs

The brief: "the existing hint path with the new surface value only (no new assistance context); if the spec's ladder
needs more than that, stop and report". It does:

1. **Readers of `surface = 'workbench'`.** About 25 places give workbench help its meaning by that literal: the hint
   window fold that marks a later attempt assisted after worked help (`db/stores/help_assists.py` 414-471), the
   session fold, diagnosis traces (`diagnosis/split/workbench_trace.py`), field workbench signals, help outcomes, gap
   sources, the reports, the bridge and route-example writers. Rows with `surface = 'workbench_ink'` would be missed
   by all of them; in particular worked ink help (rungs 4-5) would not make a later submission assisted, which is an
   honesty defect. Admitting the new value in each is a change to evidence-adjacent readers, not a surface value.
2. **The work text.** The workbench ladder's context (`hints.workbench.WorkbenchHintContext`) is built from the RW2
   session's `workbench_steps`, not from pad blocks. Ink reaches it only if the transcription is written into the
   session's steps, or the context reads pad blocks (a context change, which the bounds forbid). "Labelled as a
   transcription" is a prompt change in the hint writer and the check (an identity pin).
3. **The `◇` marker** beside the first step that doesn't hold needs the workbench check over the transcription's
   lines, which again needs them as steps.
4. **`help_assists.surface` CHECK** (a table rebuild in the 250 pattern) is left out with the ladder: a value nothing
   writes, at the cost of a rebuild and every earlier migration's upgrade-diff edits.

Options for the owner: (a) the ladder writes an ink line's transcription into the problem pad's RW2 session as a step
(through the workbench's step writer, labelled in the step's payload) and asks with `surface = 'workbench'`, adding no
surface value (the spec's `workbench_ink` dropped; ink help then folds, checks and reports exactly as typed steps,
with no label telling the model it is handwriting); (b) the spec's `workbench_ink`, with every `surface = 'workbench'`
reader widened to a named set in one place and the hint writer's context told the work is a transcription (a
persisted-meaning decision and a pinned prompt change); (c) wait for RD8b's freeform context and serve problem pads
through it too.

## 6. Judgment calls and open questions

1. **No vision-capable plan route exists today.** The ChatGPT plan's transport (`ai/providers/chatgpt_plan.py`)
   declares no `image_input`; a local image reaches a model today only through an OpenAI-compatible chat profile whose
   `input_modalities` list `"image"` (`openai_chat.py`; the figure author sends a crop that way and drops it on the
   plan, `figures/routes.FigureRoute.reads_images`). So on the default route every reading is refused honestly
   (`cannot_read_images`, nothing sent), and because the plan is ready, no OpenRouter offer is made either. Options:
   (a) teach the plan provider `input_image` content parts (a transport change, unverified without one live probe the
   owner runs; it also turns crops on for the figure author on the plan unless that route opts out); (b) the owner
   routes `ai.routing.ink_transcription` to an OpenRouter profile with `"image"` in `input_modalities` and sets
   `workbench.price_per_million` (config only; metered); (c) a plan-capability refusal that also makes the OpenRouter
   offer (a `plan_fallback` change); (d) the Pocket Notes OCR route of decision D8.
2. **A second table, `ink_transcriptions`** (§15.1 names only `ink_strokes`): readings must survive a restart for "no
   spend on a retry of the same strokes" (the polled job is in memory), and a margin note's reading has no block to
   live in.
3. **The receipt channel**: ink batches are pad-channel receipts in `pad_op_receipts`, so the client's one sequence
   needs no new receipt table and `workspace_batches` is unchanged.
4. **Erase as `pad.apply`'s `erase_ink`** (spec §3.4 lists it there): block ink only; a margin note's ink goes with its
   annotation (deleting the note hides it from `ink.list`).
5. **A reading reads the owner's standing strokes**, not only the named save's: a line flushed in several saves is
   read whole. `ink.transcribe {inkId}` keeps the spec's input.
6. **Resolution**: the finest device pixel ratio of the owner's saves.
7. **The learner's correction is never overwritten** by a later reading, even of new strokes (`kept_your_correction`;
   the client offers the new reading, and adopting it is the learner's edit). The alternative overwrote their words.
8. **A server-written version moves the block's head** while the client may hold an older one: its next `edit_block`
   then conflicts and §3.5 keeps both texts. The reply's `headVersionId` lets the client move its head first.
9. **The route shares the workbench's price, envelope, caps and models switch** rather than adding config of its own;
   one new config key (`ai.routing.ink_transcription`, `exclude_if` at its default so whole-config hashes keep their
   bytes).

## 7. What the frontend half needs

- Save strokes through the outbox with `inkSave` (one `seq` sequence with desk and pad batches), minting `inkId` per
  flush and `strokeId` per stroke; points in CSS pixels of the surface drawn on (the pad's ink layer, or the source's
  scroller for a margin note), `devicePixelRatio` from the window.
- Create an ink line as `insert_block` `{kind: "ink", provenance: "ink_transcription", bodyMd: ""}`, then save its ink;
  a margin note as an `interpretation` annotation (existing capture path), then save its ink with `{annotationId}`.
- Barrel erase: `padApply` `erase_ink` with the stroke ids passed over (block ink only).
- Read ink with `inkList({padId})` / `inkList({sourceId})`; `transcription.current` false means the strokes changed
  since the reading (ask again).
- Ask for a reading with `inkTranscribe({inkId})` after a line settles; poll `inkTranscribeJob` through the central
  poller; `inkTranscribeCancel` on leaving. Show `latexMd` as "read as …" labelled "transcription may be wrong · fix
  it"; `nothing_read` as nothing read. On `applied`, move the block's head to `headVersionId`; on
  `kept_your_correction`, offer the new reading beside the learner's words. A fix is `edit_block` (provenance becomes
  `learner_correction`, "you corrected the transcription").
- For a margin note, write the reading into the annotation through its edit if the learner accepts it.
- Errors to word: `cannot_read_images` (and the setup it needs, §6.1), `waiting_for_ok`, the fallback offer, `capped`,
  `unpriced`, `ink_too_large`.

## 8. What waits for RD7 and RD8b

- **RD7**: `#pen=veil` (ink veiled during an open check like typed text), ink inside a check, and "a block written
  during an open administration is emitted only after it closes" for ink as for text.
- **RD8b**: freeform ink help (the hint service's freeform assistance context, the judged line check, the ladder on
  freewrite pads); until then a freewrite line's menu offers "ask about this line" through the companion.
- **The problem-pad ladder** (§5): an owner decision first.
- Not in RD8a's backend: the recognizer's thresholds on sources, palm rejection and pen-mode toggles are frontend; the
  Pocket Notes comparison (D8) needs the owner's handwriting.

## 9. Tests, fail-first, commands

See the step's report for the command log. New: `tests/test_reader_rd8a_migration.py`, `test_reader_rd8a_ink.py`,
`test_reader_rd8a_render.py`, `test_reader_rd8a_transcribe.py`, `test_reader_rd8a_rpcs.py`; helpers
`tests/ink_helpers.py`, `tests/reader_rd8a_migration_helpers.py`. Edited: the earlier migrations' upgrade diffs (admit
`RD8A_ADDED_OBJECTS`), `test_mobile_allowlist.py` (the five RPCs pinned desktop-only), `test_judge_routes.py` (the
settings' judgment routes gain `ink_transcription` and its disclosure), `test_architecture.py` (the new SQL owner
`db/stores/ink_strokes.py`), `identity_pins_helpers.py` (site RD8a: the
strokes hash, the prompt, the result schema; three new pins, none moved), `model.test.ts` (the pad model's
`erase_ink`).

## 10. The frontend, part 1: pen on sources and the input layer

Branch `reader/rd8a-pen-ui`, from the backend's tip with its status commit, with RD3's fix round
(`reader/rd3-fix-frontend`) and RD4's (`reader/rd4-fix-frontend`, which carries the visual reference tool) merged in.
Part 2 (ink pads, ink blocks in `pads/*`, the pad's editable transcription) waits for the coordinator's word. The
help ladder (`#pen=ladder`, `#pen=rung2`) and `#pen=veil` are out (owner decisions and RD7).

**Where the code lives.** `screens/desks/pen/` alone: `recognizer.ts` (the rules, pure), `input.ts` (which pointers
draw, pure), `geometry.ts` (the page's probes, ranges and boxes), `PenLayer.tsx` (the ink layer, marks, chips, the
margin note), `host.ts` and `live.ts` (what the layer reaches), `pen.css`. Mount points, small and additive:
`ReaderScreen.tsx` hands its text surface (`windowed.onPenSurface`: the scroller, the reading's identity, and its
per-block selection model for any range, `nodesForRange`, which the selection now uses too); `SourceWindow.tsx`
mounts the layer; `DeskShell.tsx` holds pen mode (`alt+p`, the ✎ chip, "simulate pen", the footer's pen hints) and
provides `PenHostContext`; `keys/router.ts` takes `alt+p` (its `later` mark removed); `outbox.ts` and `store.ts` carry
an `ink` batch in the one sequence. No file in `pads/*` changed.

### 10.1 What each stroke becomes

| Stroke (spec §10.10's geometry, the mockup's recognizer for the rest) | Persisted | Shown |
|---|---|---|
| closed loop: ends within 30 px, w > 30, h > 16 | nothing (the words inside become the DOM selection: `c` asks the companion about them) | the words under a `#cfe0fa` box, the chip "circle → selection · ask the tutor · c" |
| in the margin (beyond 4 px past the text column, the first passage wider than 100 px), h > 40, w < 26 | a highlight on every paragraph spanned (each overlapping it by more than 6 px at both ends), anchored whole | the paragraphs on `#fff6d0` with the mockup's −10/+6 px spread |
| any other margin stroke | an interpretation annotation beside the passage it overlaps (else the nearest), its ink saved with it | the note box "› your note · handwritten", its transcription (below) |
| flat (h < 22) and wide (w > 40), through the middle of a line (the line 9 px above holds the middle between 30 % from its top and 25 % from its bottom) | a disposition annotation, "I disagree / doesn't make sense" | a 1.5 px `#a83a2b` line-through |
| flat and wide, under a line (the line 10 px above its middle) | a highlight snapped to the words between the stroke's ends (2 px in) | the words on `#fff0b8` |
| anything else, or a mark with no words or paragraph to attach to | nothing | plain ink, its chip saying "… not kept" |

Each mark's chip reads "X → Y · undo · ✕" at the mockup's place beside the stroke (moved in from the window's edge,
under the stroke when it would cover the words); undo files the annotation's delete intent and removes the mark and
its ink; the barrel button erasing a mark's ink does the same (a source's ink belongs to its annotation, and the
server erases block ink only). The strokes are saved with their annotation through `ink.save`, after the capture
returns the annotation id. Ink already saved is drawn again on reopening (`ink.list` with `reader.source_annotations`
for each owner's kind), its marks found again by the same geometry on today's layout.

**The margin note's transcription.** Once the note's ink is acknowledged (`store.settled()`), `ink.transcribe`; a job
is polled through the central poller under the window's id (so a paused window does not poll). On today's default
route the reading is refused (`cannot_read_images`): the note says "handwriting can't be read yet · your ink is kept"
and the learner may type the words. A reading, when a route can read images, fills the field labelled "transcribed ·
may be wrong · fix it" and is never stored as the learner's words until they keep it (↵) or change it: only then is
it written (`reader.edit_annotation`), so a model's reading is never laundered into the learner's text.

**Input** (`input.ts`). A pen draws (its first touch turns pen mode on and already draws); touch never draws, nor
does a second pointer during a stroke; the mouse draws only with "simulate pen" on and pen mode on; button 2 or 5, or
the eraser end (buttons bit 32), erases; every coalesced sample is kept with x, y, the time since the stroke began,
pressure (a mouse's 0 is the Pointer Events 0.5) and tilt, clamped to the Pointer Events ranges. A stroke of 3 points
or fewer is a tap. A paused window (offscreen, hidden, a preview) refuses input, drops a stroke under way and saves
nothing (guarded at down, move and up).

### 10.2 The mockup comparison (the shared reference, stage `rd8`)

The reference's pen captures had no marks: in headless Chromium the mockup's pen deep links scroll their passage off
screen before drawing. The private capture script gained the pen regions (the mockup's `svg.ink path.stroke.*`,
`mark.penhl`, `.p.penpara`, `mark.ctxsel`, `.recog …`, `.inknote …`, `#bPen`, `#bSimPen`, `#keys .penk`) and, for a pen
link that drew nothing on screen, runs the mockup's own recognizer (`window.penDemo`) on a paragraph that is, with its
own stroke shapes; the five pen links were captured again (`arxiv_v2`, both viewports; strike at the laptop size
still drew nothing). `visual_reference.py --stage rd8` puts the harness in each state by `alt+p` and one synthetic pen
stroke (pointer events with `pointerType: "pen"`, pressure and tilt) of the mockup's shapes on the fixture book, and
compares; it now also measures `cursor` (compared on the text under pen mode only) and an SVG's `stroke-width`
(exactly).

| Region | Measured (harness = mockup unless noted) |
|---|---|
| strokes | `#2b4fa8`, 2.2 px; opacity .35 underline, .55 bracket, .5 lasso, .85 note; strike `#a83a2b` at .6 |
| underline / bracket / lasso marks | `#fff0b8` (radius 1 px), `#fff6d0`, `#cfe0fa` |
| chip | `#181818` on `#3a3a3a`, radius 12 px, padding 3/10, JetBrains Mono 10.5 px `#d8d8e0`; undo `#f0b878`, ✕ `#8b8b9d`, "ask the tutor · c" `#9fc2ff` |
| note | 220 px, `#f7f5f0e6`, 2 px `#2b4fa8` left edge, padding 2/0/2/8; "›" line `#2b4fa8` 10 px; words Literata 13 px italic `#2a2825`; label `#8b8578` 9.5 px |
| top-bar chip (on) | `#9fc2ff` on `#121a26`, `#3b5b8a` border, radius 3 px, padding 4/8; **12 px, mockup 11.5 px** |
| footer pen hint | `#9fc2ff`, JetBrains Mono 11 px |
| cursor over text in pen mode | `crosshair` |

Tolerance: colours, type and stroke widths exact; geometry 2 px (the tool's, from §4.3). Every remaining difference
is explained: the chip's 12 px is the desks' top-bar chips' size (VR-9, RD1's); the marks' 19 px height against 24 px
follows the book prose's 13 px against 16.5 px (VR-4, RD1's); the note's label wraps to two lines because its words
are the refusal's, not the mockup's mock OCR line; the note has a chip in the app and none in the mockup (the spec:
"each recognition shows a chip"). Token rows are VR-1's (interface type, the coordinator's decision: JetBrains Mono).
Screenshots and measurements stay in the private reference directory.

### 10.3 Judgment calls

1. **Plain ink on a source stays on the page** (as decided after part 2): a stroke the recognizer cannot place, or a
   mark with no words or paragraph to attach to, is saved for the reading it was drawn on (owner kind `source`), its
   chip reading "… · kept on the page · undo · ✕"; it is redrawn when the source reopens (only that reading's), and the
   barrel erases it stroke by stroke (`ink.erase` in the write sequence; its undo erases all its strokes). It is never
   read or emitted. It never becomes a mark: making an annotation for it would be a guess.
2. **The bracket's and the note's anchors are whole passages** (`start 0, end 1_000_000`, as the Reader anchors a
   block); the note goes beside the passage it overlaps, else the nearest one.
3. **Marks are drawn as boxes under the words** (the scroller isolated, the layer at z-index −1), not by wrapping the
   words in `<mark>` as the mockup does: React owns that text, and foreign nodes inside it break reconciliation.
4. **The lasso's words become the DOM selection** (so `c` and the companion read them as any selection), with the
   native selection's paint hidden while the lasso's box shows.
5. **The eraser's reach is the pen's own width** (2.2 px either side of a stroke).
6. **Ink is kept to a hundredth of a pixel** in the scroller's coordinates (the layer's rounding of computed floats;
   every sample kept).
7. **Saved ink is redrawn in the scroller's coordinates**; a reflow (another window width, another font size) moves
   the text under it. Re-anchoring ink to words is not in the spec.
8. **"Simulate pen" is built** (the mockup's, hidden below 1400 px as there) as the brief's mouse fallback for testing.

### 10.4 What waits

Part 2 (ink pads and blocks, the pad transcription, `kept_your_correction`, the refusal on a pad), the ladder and
`#pen=veil`. The real tablet (pressure and palm behaviour on the owner's device) is unverified: the harness's pen is
synthetic.

## 11. The frontend, part 2: ink pads, ink lines and their transcriptions

After RD4's fix round was final (merged again at its tip, which also fixed the DeskShell test's union fake).

**What it delivers** (`screens/desks/pen/inkCache.ts`, `pen/InkLine.tsx`; mount points in `pads/PadStackWindow.tsx`;
`DeskStore.refreshPad`):

- **A handwritten pad** (`kind: ink`, `#pen=pad`): its tab reads "handwritten · today"; under the tab the bar "✎ by hand
  · dotted · hide transcription"; each ink line sits on its own rule (`#dfe6f2`, the mockup's), or the paper becomes a
  dot grid. A new pad made while pen mode is on is a handwritten one ("Scratchpad · ✎ by hand").
- **Ink lines** (`ink` blocks) in any pad: the line's surface draws its strokes in the pen's colour and takes the pen
  (touch never draws; a paused window draws nothing; the barrel's erasing is `erase_ink`). The pad's last row takes the
  pen too: a stroke there inserts a new ink block, then saves its ink (one write sequence: the block's batch, then the
  ink's). A click on that row still starts a typed line.
- **The transcription**, under each line: "read as <the reading>" with "may be wrong · fix it" for LearnLoop's reading
  (provenance `ink_transcription`), "yours … you corrected the transcription · fix it" for the learner's words
  (`learner_correction`). Fixing it is `edit_block`, a new version the server makes the learner's correction.
- **Reading** (`ink.transcribe`): a line is read once the learner starts writing on another line, or asks ("read it");
  never on every stroke. Its job is polled through the central poller under the window's id (so a paused window does
  not poll), "reading your handwriting… · cancel" while it runs, cancelled when its window closes. A reading written
  into the block reads the pad again (`refreshPad`, once the outbox is acknowledged), so the client's head is the
  server's and the learner's next fix does not conflict.
- **Outcomes said as they are**: `cannot_read_images` (today's default route): "handwriting can't be read yet · your ink
  is kept · type what you wrote"; `kept_your_correction`: "your words stand · LearnLoop now reads: … (may be wrong) · use
  it", and using it is the learner's edit; `nothing_read`: "nothing read · write it here"; a failure: "not read (…) ·
  your ink is kept · read it again".

**The mockup comparison** (`--stage rd8`, state `pen=pad`; the harness shows a fixture handwritten pad, synthetic
strokes and project-written transcriptions, with `?inkpad=1`; the private capture gained the pad's regions and the
link was captured again). Exact: the bar (`#7a766e` 10.5 px mono, its buttons `#2b4fa8`), the gutter's ✎ (`#2b4fa8`
10 px at .6), the transcription line (11 px mono `#7a766e`, "read as" 9.5 px `#a09a8e`, the reading `#3b3832` 12 px),
the last row's hint (`#9a968e` 11 px). Explained: the paper's colour is compared through the mockup's gradient
shorthand (both are `#fdfdfc` with `#dfe6f2` rules); the pad paper's and tab's border colours and the window head
(RD4's pads and VR-2, RD1's); the top-bar chip's 12 px (VR-9). Not compared: the mockup's ink is handwriting-font
text (`#233f8f`, "mock ink"); the desks draw the learner's strokes (`#2b4fa8` at .85, the pen token).

**Judgment calls.** (1) A line is read when the next one starts or on request, not after an idle time (a number found
nowhere), and not per stroke (spent and thrown away). (2) The learner's correction is never replaced by a later reading
(the backend's rule); the newer reading is offered beside it. (3) The last row's hint names what happens ("each line is
read once you start the next"): the mockup's "LearnLoop marks only the gutter (◇)" describes the help ladder, which is
not built. (4) Rules are drawn per line, not as one paper background: lines grow with their strokes and readings, and a
paper-wide rule would cross them.

**Plain ink on a source (part 1's judgment call 1): done as option (a).** Migration 267 (landed nowhere) amended in
place: `ink_strokes.owner_kind` admits `'source'`; the fixture rebuilt from the tracked 266 copy (its own commit, its
README section updated). The backend (§2) and the frontend (§10.3 item 1) keep it, redraw it and erase it; it is never
read or emitted.

**What waits.** The help ladder and its ◇ marker (`#pen=ladder`, `#pen=rung2`), `#pen=veil`; the real tablet.

## 12. Fix round, both halves (the adversarial review, 2026-11-23)

Branch `reader/rd8fix`, cut from the second workbench batch (migration head 268). The
review found no blocker, fourteen major and three minor findings. Each was checked against this branch's code first;
every one held. They were taken in the order of harm the orchestrator set. Ledger rows RD8a-2 to RD8a-19
(`docs/reviews/refactor-bug-ledger.md`); RD8a-18 is a bug this round found while writing a test.

| # | Verdict | What changed |
|---|---|---|
| 2 | **fixed** (RD8a-2) | A reading becomes the block's words only while its hash is the standing strokes' hash, checked inside its transaction (`pads.ink.reading_decision`, the one rule for the apply, a cached answer and `ink.list`); a stale one is kept (never paid for again) and answered `applied: false, reason: "strokes_changed"`. Client: each line counts its local changes; a reading that started at another count, or that the server set aside, leaves the line unread |
| 3 | **fixed** (RD8a-3) | `erase_ink` that leaves no standing stroke, on a block whose head is an automatic transcription, writes a blank successor without the reading's payload key (client-minted `versionId`, mirrored by the client's pad model), so emission supersedes what was read from it. A learner correction is never touched. Judgment call: a partial erase leaves the words until the line is read again (its reading names the strokes it read, and `ink.list` says it is no longer current) |
| 4 | **fixed** (RD8a-4) | A mark taken back while its annotation is being made is remembered; once made, the annotation is deleted and its ink never saved. A failed delete puts the mark back saying so; undo retries |
| 10 | **fixed** (RD8a-5) | Saved marks are drawn from the annotation's anchor (placement on the open reading, else its segments; nothing painted where it is flagged, elsewhere or needs re-anchoring), the words found by their quote in the passage's text (`geometry.rangeOfQuote`). The kind is the annotation's; a bracket is told from an underline by its ink's shape, which no layout changes. The ink stays where it was written while that still marks the same words or passage, else it is moved beside them (the recognizer's own offsets: a strike through the middle, an underline `underlineAbove` below the line, a bracket and a note to their passage's top) |
| 5 | **fixed** (RD8a-6) | The note's editor is dirty once typed into; a reading arriving then is offered beside the draft ("LearnLoop reads: … (may be wrong) · use it") |
| 8 | **fixed** (RD8a-7) | A cancelled job keeps its strokes reserved until its thread ends; a retry's job waits for it, then answers from the kept reading |
| 12 | **fixed** (RD8a-8) | Ink lines: an attempt number per line, checked after every await; a late start of a stale attempt is cancelled and never polled. Margin notes: the job id is kept; undo and the window's close stop the poll and cancel the job; a late start after either is cancelled |
| 9 | **fixed** (RD8a-9) | `_after_reading` gets the job's `live`: facts still go to the reading's vault; the worker is woken only while the job's epoch is open |
| 11 | **fixed, by the orchestrator's default** (RD8a-19) | First stopped with options (neither the spec nor the mockup gives a grouping rule); the orchestrator chose option (a), grouping by place, which the owner may change (below) |
| 6 | **fixed** (RD8a-10) | `lift_out` of an ink block saves its standing strokes again for the lifted block (same ids and points, so the same hash, ink id `<new block>:lifted`) and copies the reading of exactly those strokes; the client moves the line at once and reads the new pad once the lift is answered |
| 13 | **fixed** (RD8a-11) | The store counts each pad's local changes; a pad read whose pad changed since it started is dropped |
| 14 | **fixed** (RD8a-12) | After an erase is answered, and each time a pad is shown, the ink cache reads the pad's ink again, keeping strokes written here and not yet acknowledged on top |
| 7 | **wording corrected** (RD8a-13) | "your ink isn't sent yet · it is kept while LearnLoop stays open". A durable outbox is the RD-spike's storage choice (RD1 §5 of its record), so it is an owner question, not built here |
| 1 | **fixed** (RD8a-14) | Migration 269 (its own commit; first numbered 270, renumbered so no gap lands, inline checks taking 270): the replacing-INSERT guard refuses an insert meeting either key. 267 is on main and was not amended |
| 15 | **fixed** (RD8a-15) | Underlines and strikes take whole words |
| 16 | **fixed** (RD8a-16) | Cached answers and `ink.list` carry `applied` and `reason`; the offer is rebuilt on load |
| 17 | **fixed** (RD8a-17) | `InkSurface` drops the stroke under way when it pauses |

**Grouping margin strokes into one note (finding 11): option (a), the orchestrator's default; the owner may change
it.** Neither the spec (§10.10's table: "other margin strokes → handwritten note") nor the mockup's recognizer
(`st_16.js`, one note box per stroke, its demo one synthetic scribble) gives a rule, so this round first stopped with
three options; the orchestrator chose (a):
- (a) **By place (built):** a pen stroke in the margin beside the same passage as the open note joins it when it
  overlaps that note's strokes' box grown by one rendered text line. The line is read from the page (the passage's
  computed line height, else the height of its first line box as laid out), never a number. A stroke elsewhere (beside
  another passage, or beyond that reach), any stroke that is not a margin note, ↵ outside a text field, words typed
  into the note, leaving pen mode, pausing or closing the window ends the note. It is then kept as one annotation
  holding all its strokes and read once; nothing is saved or read per stroke. While open, undo takes the last stroke
  back and the whole note with its only one (nothing was saved); the barrel takes the strokes it passes over. Once a
  note has ended, undo takes the whole note back, as before. Tests (`pen/PenLayer.test.tsx`, "a handwritten margin
  note"): the two-stroke "x", ending by a far or a non-margin stroke, and undo while open fail on the stroke-per-note
  code; "two notes beside different passages stay two" and "leaving pen mode ends the open note" pass on it too (they
  guard against grouping too much and against an open note being lost). The note tests written before now end their
  note with ↵ before they look for its annotation and reading. The rd8 visual stage went from 4 findings to 3
  (`pen=note` lost its geometry finding: the open note's box shows its short label until the note ends); no state got
  worse.
- (b) **By an explicit end:** margin strokes beside one passage gather until ↵, "done", or a stroke that is not a
  margin stroke. Not built.
- (c) **By a pause:** a time gap the owner picks (or a learned per-writer pause distribution later). Not built.

**Persisted meaning.** No tag, no new table or column. Existing rows keep their meaning. What changes is future
writes: a stale reading no longer becomes a block version (2); an erase that leaves no stroke appends a blank version
of an automatic transcription (3), which emission settles as any edit; a lift of an ink block appends strokes and a
reading receipt for the lifted block (6). The replay of existing `ink_strokes` and `ink_transcriptions` rows is
unchanged; pad versions are a raw ledger, not replayed from ops.

**Migration 269** (`269_ink_transcriptions_guard.sql`): drops and recreates one trigger; nothing else changes. The
fixture was upgraded in place from the tracked 268 (README section). The upgrade tests that compared the applied list
with `range(N, head + 1)` read the migrations from N on instead (`tests/helpers.py migrations_from`), the files present
rather than a range (they broke while this round numbered its migration 270 past a held 269). This changes test
infrastructure, not an assertion about behaviour: each test still checks that exactly the files from N on are applied,
in order. A gap now fails loudly in one place instead: `tests/test_migrations.py::
test_the_migration_files_are_contiguous_from_the_oldest_to_the_head` (fail-first: it fails with the file at 270). Git
holds no file at 13 old numbers (38, 39, 42, 43, 46, 60, 67, 127-129, 135-137), skipped by merges landed long before;
the test lists them as `SKIPPED_BEFORE_THIS_CHECK` (a judgment call: "contiguous from the oldest" is otherwise false
today) and nothing may be added to that set.

**Contract changes** (`src/api/dto.ts`): `erase_ink` gains `versionId?`; `InkOwnerViewDto.transcription` gains
`applied` and `reason`; `InkReadingDto.reason` may be `strokes_changed`. The server's `EraseInk` op gains
`version_id`. No new RPC.

**Assertions changed.** `PenLayer.test.tsx`'s underline test pinned the half-word substring (`TEXTS[0].slice(5, 24)`,
finding 15's bug); it now expects "quick brown fox jumps". The saved-ink test's fake listing gained the anchors a
real listing has. `test_reader_rd8a_migration.py` compares the 267 upgrade with the head as 267 left it (269's trigger
undone on a copy), and its UNIQUE probe now meets 269's guard first (`append-only`). The fake desk server answers
`ink.list` from the ink it was sent, without erased strokes, as the server does (`FixtureDeskServer.inkFor`).

**Not verified here.** The anchored restore on a real layout (jsdom has none: its tests stub the geometry); the
moved-ink offsets are the recognizer's own, checked by the stubbed test. When the client and the server disagree on
whether an erase left no stroke (another device's strokes), the server writes its own version and the client's head
stays stale until the next pad read; the next edit then lands as a kept-both block.

## Owner copies (the orchestrator, 2026-11-23)

Migration 267 was applied to backup-API copies of the owner's three vaults (the floor set, upgraded to mvp-0.68 by
`learnloop upgrade`), in a gitignored directory, deleted afterwards. On every copy: the upgrade exited 0,
`integrity_check` is ok, `foreign_key_check` is empty, the migration head is 267, and `ink_strokes` and
`ink_transcriptions` hold no rows. No live vault was opened.
