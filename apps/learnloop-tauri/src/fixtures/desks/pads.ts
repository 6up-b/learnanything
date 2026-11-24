// The synthetic workspace's pads (spec §18.3): a running pad over two days and a named pad with a derivation,
// in the fixture's stack. Project-authored text only; the quotes quote the fixture's own self-written book.
import type { PadAnchorDto, PadBlockDto, PadViewDto } from "../../api/dto";
import { FIXTURE_SOURCES } from "./sources";

const { book, video } = FIXTURE_SOURCES;
const T = "2026-11-22T09:00:00Z";
const T2 = "2026-11-23T09:00:00Z";

function block(over: Partial<PadBlockDto> & Pick<PadBlockDto, "blockId" | "kind" | "provenance" | "positionKey">): PadBlockDto {
  return { headVersionId: `${over.blockId}_v1`, bodyMd: "", payload: {}, day: null, createdAt: T, updatedAt: T, submissions: [], ...over };
}

export const FIXTURE_PAD_IDS = { running: "fx_pad_running", deriving: "fx_pad_deriving" } as const;

export function fixturePads(): PadViewDto[] {
  const runningBlocks: PadBlockDto[] = [
    block({ blockId: "fx_b_r1", kind: "text", provenance: "learner", positionKey: "a", day: "2026-11-22", bodyMd: "softmax keeps the winner and the runners-up in proportion, not just the winner" }),
    block({ blockId: "fx_b_r2", kind: "source_quote", provenance: "source", positionKey: "b", day: "2026-11-22",
      bodyMd: "The largest score gets the largest weight, but every class keeps some.",
      payload: { source_title: "Softmax, a short book", page: 1, extraction_id: book.extractionId, span_id: `${book.extractionId}_s1_3` } }),
    block({ blockId: "fx_b_r3", kind: "tutor_quote", provenance: "tutor", positionKey: "c", day: "2026-11-22",
      bodyMd: "Adding a constant to every score multiplies the top and the bottom by the same factor, so the weights do not move.",
      payload: { asked_on: "2026-11-22" } }),
    block({ blockId: "fx_b_r4", kind: "text", provenance: "learner", positionKey: "d", day: "2026-11-23", createdAt: T2, updatedAt: T2,
      bodyMd: "check: the gradient of the loss is $p - \\mathbb{1}_y$, and it matches finite differences",
      submissions: [{ submissionId: "fx_sub1", versionId: "fx_b_r4_v1", as: "teach_back", practiceItemId: "fx_item_tb", attemptId: null, teachBackId: "fx_tb1", createdAt: T2, current: true }] }),
    block({ blockId: "fx_b_r5", kind: "figure", provenance: "learnloop", positionKey: "e", day: "2026-11-23", createdAt: T2, updatedAt: T2,
      bodyMd: "softmax of (1, 2, 1) at T = 0.5: 0.11 · 0.79 · 0.11", payload: { label: "temperature", figure_id: "fx_fig1" } }),
    block({ blockId: "fx_b_r6", kind: "source_quote", provenance: "source", positionKey: "f", day: "2026-11-23", createdAt: T2, updatedAt: T2,
      bodyMd: "Divide by a half and the winner pulls ahead.",
      payload: { source_title: "Softmax by hand", t: 72, extraction_id: video.extractionId, span_id: `${video.extractionId}_c4` } }),
    block({ blockId: "fx_b_r7", kind: "text", provenance: "learner", positionKey: "g", day: "2026-11-23", createdAt: T2, updatedAt: T2,
      bodyMd: "is dividing by the square root of the length the same move as a temperature?" }),
  ];
  const anchors: PadAnchorDto[] = [
    { eventId: "fx_an1", blockId: "fx_b_r2", extractionId: book.extractionId, spanId: `${book.extractionId}_s1_3`, anchor: {}, annotationId: null, createdAt: T },
  ];
  const derivingBlocks: PadBlockDto[] = [
    block({ blockId: "fx_b_d1", kind: "text", provenance: "learner", positionKey: "a", bodyMd: "the loss for the right class $y$:" }),
    block({ blockId: "fx_b_d2", kind: "text", provenance: "learner", positionKey: "b",
      bodyMd: "$$\\frac{\\partial L}{\\partial z_k} = \\frac{\\partial}{\\partial z_k}\\left(-z_y + \\log \\sum_{j=1}^{K} e^{z_j}\\right) = -[k = y] + \\frac{e^{z_k}}{\\sum_{j} e^{z_j}} = p_k - [k = y]$$" }),
    block({ blockId: "fx_b_d3", kind: "sketch", provenance: "learner", positionKey: "c", payload: { width: 480, height: 160, items: [{ type: "box", x: 40, y: 40, w: 120, h: 60 }, { type: "arrow", x1: 160, y1: 70, x2: 300, y2: 70 }, { type: "text", x: 310, y: 76, text: "p − one-hot" }] } }),
  ];
  return [
    { version: 1, pad: { padId: FIXTURE_PAD_IDS.running, kind: "running", title: "running", kept: false, homeDeskId: "fx_desk_softmax", workbenchSessionId: null, lessonId: null, version: 1, createdAt: T, updatedAt: T2 }, blocks: runningBlocks, anchors },
    { version: 1, pad: { padId: FIXTURE_PAD_IDS.deriving, kind: "named", title: "deriving ∂L/∂z", kept: true, homeDeskId: "fx_desk_softmax", workbenchSessionId: null, lessonId: null, version: 2, createdAt: T, updatedAt: T }, blocks: derivingBlocks, anchors: [] },
  ];
}

/** The display-math fixture (spec §13.4 rule 5): tall and wide equations in every kind of pad block, for the
 * real-webview test that no equation is clipped. Project-authored math, as display blocks ($$ on lines of
 * their own, the form the editor, the tutor and the Reader's display brackets all come to). */
const TEX = {
  fractionOfSums: "\\frac{\\sum_{i=1}^{n} \\sum_{j=1}^{m} a_{ij}\\, e^{z_{ij}}}{\\sum_{k=1}^{K} \\frac{e^{z_k}}{1 + \\sum_{l} e^{z_l}}}",
  aligned: "\\begin{aligned} \\frac{\\partial L}{\\partial z_k} &= \\frac{\\partial}{\\partial z_k}\\Bigl(-z_y + \\log \\sum_{j} e^{z_j}\\Bigr) \\\\ &= -[k = y] + \\frac{e^{z_k}}{\\sum_{j} e^{z_j}} \\\\ &= p_k - [k = y] \\end{aligned}",
  matrix: "J = \\begin{pmatrix} p_1(1 - p_1) & -p_1 p_2 & \\cdots & -p_1 p_K \\\\ -p_2 p_1 & p_2(1 - p_2) & \\cdots & -p_2 p_K \\\\ \\vdots & \\vdots & \\ddots & \\vdots \\\\ -p_K p_1 & -p_K p_2 & \\cdots & p_K(1 - p_K) \\end{pmatrix}",
  tallParens: "\\left( \\frac{\\displaystyle \\sum_{j=1}^{K} e^{z_j / T}}{\\displaystyle \\prod_{k=1}^{K} \\left( 1 + \\frac{1}{e^{z_k}} \\right)} \\right)^{\\frac{1}{2}}",
  // Fits a wide column, is scaled in a middle one, and scrolls in a narrow one.
  wide: "p_k = \\frac{e^{z_k / T}}{e^{z_1 / T} + e^{z_2 / T} + e^{z_3 / T} + e^{z_4 / T} + e^{z_5 / T}} \\quad\\text{and}\\quad \\log p_k = \\frac{z_k}{T} - \\log \\sum_{j} e^{z_j / T}",
} as const;

const display = (tex: string) => `\n\n$$\n${tex}\n$$\n\n`;

export const FIXTURE_MATH = {
  fractionOfSums: display(TEX.fractionOfSums),
  aligned: display(TEX.aligned),
  matrix: display(TEX.matrix),
  tallParens: display(TEX.tallParens),
  wide: display(TEX.wide),
} as const;

export function fixtureMathPad(): PadViewDto {
  const m = FIXTURE_MATH;
  const at = (n: number) => String.fromCharCode(97 + n);
  const blocks: PadBlockDto[] = [
    block({ blockId: "fx_m_text1", kind: "text", provenance: "learner", positionKey: at(0), day: "2026-11-23", bodyMd: `a fraction of sums:${m.fractionOfSums}` }),
    block({ blockId: "fx_m_text2", kind: "text", provenance: "learner", positionKey: at(1), day: "2026-11-23", bodyMd: m.aligned.trim() }),
    block({ blockId: "fx_m_quote", kind: "source_quote", provenance: "source", positionKey: at(2), day: "2026-11-23", bodyMd: `the Jacobian:${m.matrix}it is symmetric.`,
      payload: { source_title: "Softmax, a short book", page: 2, extraction_id: book.extractionId, span_id: `${book.extractionId}_s2_1` } }),
    block({ blockId: "fx_m_tutor", kind: "tutor_quote", provenance: "tutor", positionKey: at(3), day: "2026-11-23", bodyMd: `with a temperature:${m.tallParens}`, payload: { asked_on: "2026-11-23" } }),
    block({ blockId: "fx_m_check", kind: "check_cell", provenance: "tutor", positionKey: at(4), day: "2026-11-23", bodyMd: m.aligned.trim(),
      payload: { practice_item_id: "fx_item_check", prompt_md: `derive it:${m.fractionOfSums}` } }),
    block({ blockId: "fx_m_wide", kind: "text", provenance: "learner", positionKey: at(5), day: "2026-11-23", bodyMd: m.wide.trim() }),
  ];
  return { version: 1, pad: { padId: "fx_pad_math", kind: "running", title: "math", kept: false, homeDeskId: "fx_desk_softmax", workbenchSessionId: null, lessonId: null, version: 1, createdAt: T2, updatedAt: T2 }, blocks, anchors: [] };
}

// ── a handwritten pad (pen and ink, RD8a): three ink lines with synthetic strokes (project-made curves, no one's
// handwriting); the first read by LearnLoop, the second corrected by the learner, the third not read yet.
export const FIXTURE_INK_PAD = "fx_pad_hand";

/** A synthetic line of "writing": short wavy strokes along a 52 px rule, `words` of them. */
function inkStrokes(line: string, words: number): Array<{ strokeId: string; inkId: string; points: Array<[number, number, number, number, number, number]> }> {
  return Array.from({ length: words }, (_unused, w) => {
    const points: Array<[number, number, number, number, number, number]> = [];
    for (let i = 0; i <= 14; i += 1) {
      const x = 12 + w * 64 + i * 3.6;
      const y = 30 + Math.sin(i * 0.9 + w) * 9 + (i % 5 === 0 ? -4 : 0);
      points.push([Math.round(x * 10) / 10, Math.round(y * 10) / 10, i * 8, 0.5, 0, 0]);
    }
    return { strokeId: `${line}_s${w}`, inkId: `${line}_ink`, points };
  });
}

export function fixtureInkPad(): PadViewDto {
  const at = (n: number) => String.fromCharCode(97 + n);
  const reading = (id: string, hash: string) => ({ ink_transcription: { transcription_id: id, content_hash: hash, confidence_label: "may_be_wrong" } });
  const blocks: PadBlockDto[] = [
    block({ blockId: "fx_b_h1", kind: "ink", provenance: "ink_transcription", positionKey: at(0), bodyMd: "$L = -\\ln p_y$", payload: reading("fx_it_1", "fx_h1"), createdAt: T2, updatedAt: T2 }),
    block({ blockId: "fx_b_h2", kind: "ink", provenance: "learner_correction", positionKey: at(1), bodyMd: "$\\partial L / \\partial z_k = p_k - [k = y]$", payload: reading("fx_it_2", "fx_h2"), createdAt: T2, updatedAt: T2 }),
    block({ blockId: "fx_b_h3", kind: "ink", provenance: "ink_transcription", positionKey: at(2), bodyMd: "", createdAt: T2, updatedAt: T2 }),
  ];
  return { version: 1, pad: { padId: FIXTURE_INK_PAD, kind: "ink", title: "Scratchpad · ✎ by hand", kept: false, homeDeskId: "fx_desk_softmax", workbenchSessionId: null, lessonId: null, version: 1, createdAt: T2, updatedAt: T2 }, blocks, anchors: [] };
}

/** `ink.list` for the handwritten pad: each line's strokes, its hash and its reading. */
export function fixtureInkOwners(): import("../../api/dto").InkOwnerViewDto[] {
  const owner = (blockId: string, hash: string, words: number, transcription: { id: string; latexMd: string } | null) => ({
    ownerKind: "block" as const, ownerId: blockId, contentHash: hash, devicePixelRatio: 1, strokes: inkStrokes(blockId, words),
    transcription: transcription ? { transcriptionId: transcription.id, latexMd: transcription.latexMd, confidenceLabel: "may_be_wrong" as const, contentHash: hash, current: true, createdAt: T2 } : null,
  });
  return [
    owner("fx_b_h1", "fx_h1", 4, { id: "fx_it_1", latexMd: "$L = -\\ln p_y$" }),
    owner("fx_b_h2", "fx_h2", 6, { id: "fx_it_2", latexMd: "$\\partial L / \\partial z_k = p_k + [k = y]$" }),
    owner("fx_b_h3", "fx_h3", 3, null),
  ];
}

/** The notebook harness's pad (`?padcells=1`): a line of the learner's, then the cells the harness script names
 * (it runs the same cells in a real sandboxed session), in order. */
export function fixtureCellsPad(cells: Array<{ blockId: string; code: string; provenance?: PadBlockDto["provenance"] }>): PadViewDto {
  const at = (n: number) => String.fromCharCode(98 + n);
  const blocks: PadBlockDto[] = [
    block({ blockId: "fx_c_text", kind: "text", provenance: "learner", positionKey: "a", day: "2026-11-23", bodyMd: "softmax at a temperature, as cells I can run" }),
    ...cells.map((cell, index) => block({ blockId: cell.blockId, kind: "cell", provenance: cell.provenance ?? "learner", positionKey: at(index), day: "2026-11-23", bodyMd: cell.code })),
  ];
  return { version: 1, pad: { padId: "fx_pad_cells", kind: "named", title: "marimo cells", kept: false, homeDeskId: "fx_desk_softmax", workbenchSessionId: null, lessonId: null, version: 1, createdAt: T2, updatedAt: T2 }, blocks, anchors: [] };
}
