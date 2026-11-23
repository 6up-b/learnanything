// The synthetic workspace's desks (spec §18.3), arranged like the mockup's: a first desk of a book with
// a video, a paper, its guide and path panels and a pad stack; a second desk on attention; a third
// with a ranged window on the same book. And a small in-memory server that applies `desk.apply` as
// the sidecar does (versions checked per op, conflicts with the current head), for the harness.
import type { DeskApplyDto, DeskApplyInput, DeskOpDto, DeskStateDto, WriteOpResultDto } from "../../api/dto";
import { OpRefusal, applyDeskOp, deskById, fromDeskState, type Workspace } from "../../screens/desks/model/workspace";
import { FIXTURE_SOURCES } from "./sources";

const { book, paper, video, video2 } = FIXTURE_SOURCES;

export function fixtureDeskState(): DeskStateDto {
  return {
    version: 1,
    runningPadIds: [],
    serverSeq: [],
    desks: [
      {
        deskId: "fx_desk_softmax", title: "softmax and cross-entropy", position: "a", focusWindowId: "fx_w_book", goalId: null,
        companion: { dock: "br", shown: false }, version: 1,
        slots: [
          { slot: 0, windows: [{ windowId: "fx_w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } }] },
          { slot: 1, windows: [{ windowId: "fx_w_video", pane: 0, kind: "video", active: true, view: {}, content: { kind: "video", sourceId: video.sourceId, extractionId: video.extractionId } }] },
          { slot: 2, windows: [{ windowId: "fx_w_paper", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" } }] },
          { slot: 3, windows: [{ windowId: "fx_w_guide", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "guide", extractionId: book.extractionId } }] },
          { slot: 4, windows: [{ windowId: "fx_w_path", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "path", extractionId: book.extractionId } }] },
          { slot: 5, windows: [{ windowId: "fx_w_pads", pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId: "fx_pad_running" }, { kind: "pad", padId: "fx_pad_deriving" }] }] },
        ],
      },
      {
        deskId: "fx_desk_attention", title: "attention", position: "b", focusWindowId: "fx_w_video2", goalId: null,
        companion: { dock: "br", shown: false }, version: 1,
        slots: [
          { slot: 0, windows: [{ windowId: "fx_w_video2", pane: 0, kind: "video", active: true, view: {}, content: { kind: "video", sourceId: video2.sourceId, extractionId: video2.extractionId } }] },
          { slot: 1, windows: [{ windowId: "fx_w_paper2", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" } }] },
        ],
      },
      {
        deskId: "fx_desk_backprop", title: "backprop", position: "c", focusWindowId: "fx_w_book_range", goalId: null,
        companion: { dock: "br", shown: false }, version: 1,
        slots: [
          { slot: 0, windows: [{ windowId: "fx_w_book_range", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render", range: { fromSpanId: `${book.extractionId}_s4_h`, toSpanId: `${book.extractionId}_s5_3` } } }] },
        ],
      },
    ],
  };
}

/** The workspace back as `desk.state` sends it. */
export function toDeskState(ws: Workspace, serverSeq: DeskStateDto["serverSeq"]): DeskStateDto {
  return {
    version: 1,
    runningPadIds: [],
    serverSeq,
    desks: ws.desks.map((desk) => ({
      deskId: desk.deskId, title: desk.title, position: desk.position, focusWindowId: desk.focusWindowId, goalId: desk.goalId,
      companion: { ...desk.companion }, version: desk.version,
      slots: desk.slots.map((ids, slot) => ({
        slot,
        windows: ids.map((id, pane) => {
          const window = ws.windows[id];
          return {
            windowId: id, pane, kind: window.kind, active: window.active, view: window.view,
            ...(window.stack ? { stack: window.stack } : { content: window.content ?? undefined }),
          };
        }),
      })),
    })),
  };
}

/** A small server for the harness: per client, batches in order; per op, the named desk's version checked. */
export class FixtureDeskServer {
  private ws: Workspace;
  private seqs = new Map<string, number>();
  readonly batches: DeskApplyInput[] = [];

  constructor(state: DeskStateDto = fixtureDeskState()) {
    this.ws = fromDeskState(state);
  }

  state(): DeskStateDto {
    return toDeskState(this.ws, [...this.seqs.entries()].map(([clientId, seq]) => ({ clientId, seq })));
  }

  apply(input: DeskApplyInput): DeskApplyDto {
    const last = this.seqs.get(input.clientId) ?? 0;
    if (input.seq !== last + 1) throw { code: "seq_gap", message: `expected ${last + 1}`, retryable: false };
    this.batches.push(input);
    const results: WriteOpResultDto[] = [];
    const touched = new Set<string>();
    for (const op of input.ops) {
      const conflict = this.stale(op);
      if (conflict) {
        results.push({ status: "conflict", current: conflict });
        continue;
      }
      try {
        this.ws = applyDeskOp(this.ws, op);
        touched.add(op.deskId);
        if (op.op === "move_to_desk") touched.add(op.toDeskId);
        results.push({ status: "ok" });
      } catch (error) {
        if (error instanceof OpRefusal) results.push({ status: "refused", code: error.code, message: error.message });
        else throw error;
      }
    }
    this.seqs.set(input.clientId, input.seq);
    return {
      version: 1,
      appliedSeq: input.seq,
      results,
      versions: [...touched].filter((id) => deskById(this.ws, id)).map((id) => ({ deskId: id, version: deskById(this.ws, id)!.version })),
    };
  }

  private stale(op: DeskOpDto): Record<string, unknown> | null {
    if (op.op === "create_desk") return null;
    const desk = deskById(this.ws, op.deskId);
    if (!desk) return null;
    if (op.expectedVersion !== desk.version) return { deskId: desk.deskId, version: desk.version };
    if (op.op === "move_to_desk") {
      const to = deskById(this.ws, op.toDeskId);
      if (to && op.toExpectedVersion !== to.version) return { deskId: to.deskId, version: to.version };
    }
    return null;
  }
}
