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
| `ink.save` | `{clientId, seq, owner: {blockId} \| {annotationId}, inkId, strokes: [{strokeId, points: [[x, y, t, pressure, tiltX, tiltY], ...]}], pointerMeta: {pointerType: pen\|mouse, devicePixelRatio?}}` | `{appliedSeq, inkId, results: [ok{duplicate} \| refused{code}]}` |
| `ink.list` | `{padId}` or `{sourceId}` | `{padId, sourceId, owners: [{ownerKind, ownerId, contentHash, devicePixelRatio, strokes: [{strokeId, inkId, points}], transcription: {transcriptionId, latexMd, confidenceLabel, contentHash, current, createdAt} \| null}]}` |
| `ink.transcribe` | `{inkId}` | `{jobId, status, done, result, error}` at once |
| `ink.transcribe_job` | `{jobId}` | the same, at once (never a wait) |
| `ink.transcribe_cancel` | `{jobId}` | the same |
| `pad.apply` op `erase_ink` | `{op: "erase_ink", blockId, strokeIds, eraseId?}` | `ok{eraseId}` or `refused{code}` |

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

1. **Plain ink on a source is not kept.** The backend's ink owners are a block or an annotation; a stroke the
   recognizer cannot place has neither, and making an annotation for it would be the guess the brief forbids. Its chip
   says "not kept". Options: a kind of annotation for free ink (a backend change), or a per-source scratch owner.
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
