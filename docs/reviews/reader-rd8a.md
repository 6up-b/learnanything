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

**The job.** `polled_jobs` on a thread the context owns; one registry per vault root, so a poll from another vault
answers `job_not_found`, and a vault switch interrupts a running job (its next request is refused). A second ask for
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
settings' judgment routes gain `ink_transcription` and its disclosure), `identity_pins_helpers.py` (site RD8a: the
strokes hash, the prompt, the result schema; three new pins, none moved), `model.test.ts` (the pad model's
`erase_ink`).
