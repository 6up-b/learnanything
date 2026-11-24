// The client's pad model (spec §10.4, §10.5; RD0/RD4a's `pad.apply`): every op applied as the server applies
// it, so a pad shows a write at once and the outbox sends it after. Blocks order by their position key, then
// their id (the server's ORDER BY); an edit expects the block's head version and makes a new one (the
// client mints both the block ids and the version ids, so a run of edits chains before any reply).
import type { PadAnchorDto, PadBlockDto, PadBlockKind, PadDto, PadOpDto, PadProvenance, PadViewDto } from "../../../api/dto";

/** The kinds the learner edits in place (spec §10.4's "editable" column; the server's EDITABLE_KINDS). */
export const EDITABLE_KINDS: ReadonlySet<PadBlockKind> = new Set(["text", "note", "sketch", "cell", "ink", "check_cell"]);

export interface PadState {
  pad: PadDto;
  /** Standing blocks, in order. */
  blocks: PadBlockDto[];
  anchors: PadAnchorDto[];
}

export type Pads = Record<string, PadState>;

export class PadOpRefusal extends Error {
  constructor(readonly code: string, message: string) {
    super(message);
  }
}

export class PadOpConflict extends Error {
  constructor(readonly current: Record<string, unknown>) {
    super("stale head");
  }
}

export function fromPadView(view: PadViewDto): PadState {
  return { pad: { ...view.pad }, blocks: sortBlocks(view.blocks.map((block) => ({ ...block, submissions: [...(block.submissions ?? [])] }))), anchors: [...view.anchors] };
}

function sortBlocks(blocks: PadBlockDto[]): PadBlockDto[] {
  return [...blocks].sort((a, b) => (a.positionKey < b.positionKey ? -1 : a.positionKey > b.positionKey ? 1 : a.blockId < b.blockId ? -1 : a.blockId > b.blockId ? 1 : 0));
}

// -- position keys: fractional, so a block lands between two others without moving them -------------------

const DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

/** A key strictly between `a` and `b` (either may be null: before everything, after everything). Keys compare
 * as plain strings, as SQLite's BINARY collation compares them; a generated key never ends in the lowest digit,
 * so there is always room before it. */
export function keyBetween(a: string | null, b: string | null): string {
  if (a !== null && b !== null && a >= b) throw new Error(`no key between ${a} and ${b}`);
  return midpoint(a ?? "", b);
}

function midpoint(a: string, b: string | null): string {
  if (b !== null) {
    // A common prefix (a read as padded with the lowest digit) is kept.
    let n = 0;
    while ((a[n] ?? DIGITS[0]) === b[n]) n += 1;
    if (n > 0) {
      if (n >= b.length) throw new Error("no key between them");
      return b.slice(0, n) + midpoint(a.slice(n), b.slice(n));
    }
  }
  const low = a ? DIGITS.indexOf(a[0]) : 0;
  const high = b !== null ? DIGITS.indexOf(b[0]) : DIGITS.length;
  if (high - low > 1) return DIGITS[Math.round((low + high) / 2)];
  // Neighbouring digits: b's first digit alone sits between when b goes on; else extend a.
  if (b !== null && b.length > 1) return b.slice(0, 1);
  return DIGITS[low] + midpoint(a.slice(1), null);
}

/** The key for a block placed after `after` (null: at the start) in `blocks`. */
export function keyAfter(blocks: PadBlockDto[], after: string | null): string {
  if (after === null) return keyBetween(null, blocks[0]?.positionKey ?? null);
  const index = blocks.findIndex((block) => block.blockId === after);
  const here = blocks[index]?.positionKey ?? blocks[blocks.length - 1]?.positionKey ?? null;
  const next = index >= 0 ? blocks[index + 1]?.positionKey ?? null : null;
  return keyBetween(here, next);
}

// -- applying ops ------------------------------------------------------------------------------------------

function replace(pads: Pads, padId: string, state: PadState): Pads {
  return { ...pads, [padId]: state };
}

function requirePad(pads: Pads, padId: string): PadState {
  const state = pads[padId];
  if (!state) throw new PadOpRefusal("pad_not_found", "Couldn’t find this pad. Open it again.");
  return state;
}

function requireHead(state: PadState, blockId: string, expected: string): PadBlockDto {
  const block = state.blocks.find((each) => each.blockId === blockId);
  if (!block) throw new PadOpRefusal("block_not_found", "Couldn’t find this line. Reopen the pad and try again.");
  if (block.headVersionId !== expected) throw new PadOpConflict({ block_id: blockId, head_version_id: block.headVersionId });
  return block;
}

function withBlock(state: PadState, block: PadBlockDto): PadState {
  return { ...state, blocks: sortBlocks([...state.blocks.filter((each) => each.blockId !== block.blockId), block]) };
}

function keepBoth(pads: Pads, padId: string, state: PadState, op: Extract<PadOpDto, { op: "edit_block" }>, head: PadBlockDto | null, now: string): Pads {
  const keep = op.keepBoth as NonNullable<typeof op.keepBoth>;
  if (state.blocks.some((block) => block.blockId === keep.blockId)) throw new PadOpRefusal("block_exists", "This line may already be in the pad. Check the pad before trying again.");
  const kind = head?.kind ?? "text";
  if (!EDITABLE_KINDS.has(kind)) throw new PadOpRefusal("not_editable", "Add your own note below this line.");
  const kept: PadBlockDto = {
    blockId: keep.blockId,
    headVersionId: keep.versionId ?? `${keep.blockId}~${now}`,
    kind,
    bodyMd: op.bodyMd ?? head?.bodyMd ?? "",
    payload: { ...(op.payload ?? head?.payload ?? {}), conflict: { of_block_id: op.blockId, expected_head: op.expectedHead, server_head_version_id: head?.headVersionId ?? null, label: keep.label ?? "", at: now } },
    provenance: kind === "ink" ? "learner_correction" : head?.provenance ?? "learner",
    positionKey: keyAfter(state.blocks, head ? head.blockId : state.blocks[state.blocks.length - 1]?.blockId ?? null),
    day: head?.day ?? null,
    createdAt: now,
    updatedAt: now,
    submissions: [],
  };
  return replace(pads, padId, withBlock(state, kept));
}

/** One op on one pad, as the server applies it. `now` stamps what the server would stamp. */
export function applyPadOp(pads: Pads, padId: string, op: PadOpDto, now: string): Pads {
  if (op.op === "create_pad") {
    if (pads[padId]) throw new PadOpConflict({ pad_id: padId, version: pads[padId].pad.version });
    return replace(pads, padId, {
      pad: { padId, kind: op.kind, title: op.title ?? "", kept: false, homeDeskId: op.homeDeskId ?? null, workbenchSessionId: op.workbenchSessionId ?? null, lessonId: op.lessonId ?? null, version: 1, createdAt: now, updatedAt: now },
      blocks: [],
      anchors: [],
    });
  }
  const state = requirePad(pads, padId);
  switch (op.op) {
    case "set_title":
    case "keep":
    case "unkeep": {
      if (op.expectedVersion !== state.pad.version) throw new PadOpConflict({ pad_id: padId, version: state.pad.version });
      const pad = { ...state.pad, version: state.pad.version + 1, updatedAt: now, ...(op.op === "set_title" ? { title: op.title } : { kept: op.op === "keep" }) };
      return replace(pads, padId, { ...state, pad });
    }
    case "insert_block": {
      if (Object.values(pads).some((each) => each.blocks.some((block) => block.blockId === op.blockId))) {
        throw new PadOpConflict({ block_id: op.blockId });
      }
      const block: PadBlockDto = {
        blockId: op.blockId, headVersionId: op.versionId ?? op.blockId, kind: op.kind, bodyMd: op.bodyMd ?? "", payload: op.payload ?? {},
        provenance: op.provenance, positionKey: op.positionKey, day: op.day ?? null, createdAt: now, updatedAt: now, submissions: [],
      };
      return replace(pads, padId, withBlock({ ...state, pad: { ...state.pad, updatedAt: now } }, block));
    }
    case "edit_block": {
      const current = state.blocks.find((block) => block.blockId === op.blockId);
      // Typed over a version that is no longer the head (another device's edit, or the block removed there): the
      // head stays, and these words land as a block of their own right after it, marked as the conflict they are.
      if (op.keepBoth && (!current || current.headVersionId !== op.expectedHead)) return keepBoth(pads, padId, state, op, current ?? null, now);
      const head = requireHead(state, op.blockId, op.expectedHead);
      if (!EDITABLE_KINDS.has(head.kind)) throw new PadOpRefusal("not_editable", "Add your own note below this line.");
      const next: PadBlockDto = {
        ...head, headVersionId: op.versionId ?? `${head.blockId}~${now}`, updatedAt: now,
        ...(op.bodyMd !== undefined ? { bodyMd: op.bodyMd } : {}),
        ...(op.payload !== undefined ? { payload: op.payload } : {}),
        ...(head.kind === "ink" ? { provenance: "learner_correction" as PadProvenance } : {}),
        // A new version is no longer the submitted one: its tag reads "an earlier version".
        submissions: head.submissions.map((submission) => ({ ...submission, current: false })),
      };
      return replace(pads, padId, withBlock(state, next));
    }
    case "remove_block": {
      requireHead(state, op.blockId, op.expectedHead);
      return replace(pads, padId, { ...state, blocks: state.blocks.filter((block) => block.blockId !== op.blockId), anchors: state.anchors.filter((anchor) => anchor.blockId !== op.blockId) });
    }
    case "move_block": {
      const head = requireHead(state, op.blockId, op.expectedHead);
      return replace(pads, padId, withBlock(state, { ...head, positionKey: op.positionKey, headVersionId: op.versionId ?? head.headVersionId, updatedAt: now }));
    }
    case "lift_out": {
      const head = requireHead(state, op.blockId, op.expectedHead);
      if (pads[op.newPadId]) throw new PadOpRefusal("pad_exists", "This pad may already exist. Check the window list before trying again.");
      const lifted: PadBlockDto = { ...head, blockId: op.newBlockId, headVersionId: op.newVersionId ?? op.newBlockId, positionKey: op.positionKey ?? "a0", createdAt: now, updatedAt: now, submissions: [] };
      const stub: PadBlockDto = {
        ...head, kind: "lifted", bodyMd: "", provenance: "learnloop", headVersionId: op.stubVersionId ?? `${head.blockId}~${now}`, updatedAt: now,
        payload: { lifted_to_pad_id: op.newPadId, lifted_block_id: op.newBlockId },
      };
      const created: PadState = {
        pad: { padId: op.newPadId, kind: "named", title: op.title ?? "", kept: false, homeDeskId: state.pad.homeDeskId, workbenchSessionId: null, lessonId: null, version: 1, createdAt: now, updatedAt: now },
        blocks: [lifted],
        anchors: [],
      };
      return { ...replace(pads, padId, withBlock(state, stub)), [op.newPadId]: created };
    }
    case "link_anchor":
    case "unlink_anchor": {
      if (!state.blocks.some((block) => block.blockId === op.blockId)) throw new PadOpRefusal("block_not_found", "Couldn’t find this line. Reopen the pad and try again.");
      const current = anchorHead(state, op.blockId, op.extractionId, op.spanId);
      if (current !== op.expectedAnchorHead) throw new PadOpConflict({ block_id: op.blockId, anchor_head: current });
      const others = state.anchors.filter((anchor) => !(anchor.blockId === op.blockId && anchor.extractionId === op.extractionId && anchor.spanId === op.spanId));
      if (op.op === "unlink_anchor") {
        if (others.length === state.anchors.length) throw new PadOpRefusal("not_linked", "This line has no link to that passage. Choose another line.");
        return replace(pads, padId, { ...state, anchors: others });
      }
      const anchor: PadAnchorDto = { eventId: op.eventId ?? `${op.blockId}:${op.spanId}:${now}`, blockId: op.blockId, extractionId: op.extractionId, spanId: op.spanId, anchor: op.anchor ?? {}, annotationId: op.annotationId ?? null, createdAt: now };
      return replace(pads, padId, { ...state, anchors: [...others, anchor] });
    }
    case "erase_ink": {
      // The strokes live outside the pad model (inkList); here only the pad's change time moves, as on the server.
      const block = state.blocks.find((each) => each.blockId === op.blockId);
      if (!block) throw new PadOpRefusal("block_not_found", "Couldn’t find this line. Reopen the pad and try again.");
      if (block.kind !== "ink") throw new PadOpRefusal("not_an_ink_block", "Open a handwriting pad to write with the pen.");
      if (op.versionId && block.provenance === "ink_transcription") {
        // Every stroke erased: LearnLoop's reading of them goes with them, as on the server (a blank version).
        const { ink_transcription: _gone, ...payload } = block.payload;
        const next: PadBlockDto = { ...block, headVersionId: op.versionId, bodyMd: "", payload, updatedAt: now,
          submissions: block.submissions.map((submission) => ({ ...submission, current: false })) };
        return replace(pads, padId, { ...withBlock(state, next), pad: { ...state.pad, updatedAt: now } });
      }
      return replace(pads, padId, { ...state, pad: { ...state.pad, updatedAt: now } });
    }
  }
}

/** The newest standing link event between a block and a passage, as the client knows it (null: none). */
export function anchorHead(state: PadState, blockId: string, extractionId: string, spanId: string): string | null {
  const found = state.anchors.filter((anchor) => anchor.blockId === blockId && anchor.extractionId === extractionId && anchor.spanId === spanId);
  return found.length ? found[found.length - 1].eventId : null;
}

/** One queued op re-applied on newer pads (after a conflict): the heads it expects stamped from them. Throws
 * PadOpRefusal when it no longer applies there. An edit of a block another device changed meanwhile lands as a
 * newer version on top (the other version stays in the block's history). */
/** Where a queued edit's words went when the server kept both: the version the client made (the edit's
 * versionId) → the block and version its words landed in. A later edit typed on top goes on there. */
export type KeptBothRedirects = Map<string, { blockId: string; versionId: string }>;

/** One queued op re-applied on newer pads (after a conflict, or a reconcile): the server's head is kept. An edit
 * typed over an older head keeps its expected head and lands as its own block (keepBoth); a stale remove, move or
 * lift is refused (never retried onto newer words); versions and anchor heads are stamped from the newer pads. */
export function restampPadOp(pads: Pads, padId: string, op: PadOpDto, now: string, redirects?: KeptBothRedirects): { pads: Pads; op: PadOpDto } {
  const state = pads[padId];
  let stamped: PadOpDto = op;
  if (state) {
    if (op.op === "set_title" || op.op === "keep" || op.op === "unkeep") stamped = { ...op, expectedVersion: state.pad.version };
    if (op.op === "edit_block") {
      const moved = redirects?.get(op.expectedHead);
      // Typed on after an edit whose words were kept apart: it goes on in the block they landed in.
      if (moved) stamped = { ...op, blockId: moved.blockId, expectedHead: moved.versionId, keepBoth: op.keepBoth };
      const target = stamped as Extract<PadOpDto, { op: "edit_block" }>;
      const head = state.blocks.find((block) => block.blockId === target.blockId);
      if ((!head || head.headVersionId !== target.expectedHead) && !target.keepBoth) throw new PadOpRefusal("stale", "This line changed in another window. Check the latest text before trying again.");
      if (head && head.headVersionId !== target.expectedHead && target.keepBoth && target.versionId) {
        redirects?.set(target.versionId, { blockId: target.keepBoth.blockId, versionId: target.keepBoth.versionId ?? target.keepBoth.blockId });
      } else if (!head && target.keepBoth && target.versionId) {
        redirects?.set(target.versionId, { blockId: target.keepBoth.blockId, versionId: target.keepBoth.versionId ?? target.keepBoth.blockId });
      }
    }
    if (op.op === "remove_block" || op.op === "move_block" || op.op === "lift_out") {
      const head = state.blocks.find((block) => block.blockId === op.blockId);
      if (!head) throw new PadOpRefusal("block_not_found", "This line was removed. Choose another line.");
      if (head.headVersionId !== op.expectedHead) throw new PadOpRefusal("stale", "This line changed in another window. Check the latest text before trying again.");
    }
    if (op.op === "link_anchor" || op.op === "unlink_anchor") stamped = { ...op, expectedAnchorHead: anchorHead(state, op.blockId, op.extractionId, op.spanId) };
  }
  try {
    return { pads: applyPadOp(pads, padId, stamped, now), op: stamped };
  } catch (error) {
    if (error instanceof PadOpConflict) throw new PadOpRefusal("conflict", "This pad changed. Check the latest text and try again.");
    throw error;
  }
}

/** Whether a block's words are the learner's own (what may be submitted and what is emitted: §10.9, §10.11). */
export function isLearnersWords(block: PadBlockDto): boolean {
  if (block.kind === "text" || block.kind === "note") return block.provenance === "learner";
  if (block.kind === "ink") return block.provenance === "ink_transcription" || block.provenance === "learner_correction";
  return block.kind === "check_cell";
}

/** The first line of a block's words, for tab labels and the drain. */
export function firstLine(text: string): string {
  return text.split("\n").map((line) => line.trim()).find(Boolean) ?? "";
}

/** A line as plain words for a one-line label: math delimiters, emphasis, heading and quote marks dropped
 * (a tab cannot typeset, and "$y$" reads as noise). */
export function plainLine(text: string): string {
  return firstLine(text).replace(/\$+/g, "").replace(/[*_`]+/g, "").replace(/^(#+|>)\s*/, "").replace(/\\([a-zA-Z]+)/g, "$1").trim();
}
