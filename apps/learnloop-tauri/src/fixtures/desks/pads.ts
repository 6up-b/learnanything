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
