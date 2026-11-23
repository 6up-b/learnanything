// What a source window's pen layer needs from the desks (spec §10.10): pen mode and its switch, the client's one
// write sequence for ink, ids, the RPCs it calls and the central poller. DeskShell provides it; tests provide fakes.
import { createContext, useContext } from "react";
import type {
  InkListDto,
  InkTranscribeJobDto,
  ReaderAnnotationResultDto,
  ReaderCaptureInput,
  ReaderCaptureReceiptDto,
} from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import type { InkSaveBody } from "../outbox";
import type { InkCache } from "./inkCache";

export interface PenApi {
  readerCapture(input: ReaderCaptureInput): Promise<ReaderCaptureReceiptDto>;
  readerDeleteIntentAnnotation(input: { annotationId: string; reason?: string | null }): Promise<unknown>;
  readerEditAnnotation(input: { annotationId: string; learnerText?: string | null }): Promise<ReaderAnnotationResultDto>;
  readerSourceAnnotations(input: { sourceId: string; extractionId?: string | null }): Promise<{ annotations: unknown[] }>;
  inkList(input: { padId: string } | { sourceId: string }): Promise<InkListDto>;
  inkTranscribe(input: { inkId: string }): Promise<InkTranscribeJobDto>;
  inkTranscribeJob(input: { jobId: string }): Promise<InkTranscribeJobDto>;
  inkTranscribeCancel(input: { jobId: string }): Promise<InkTranscribeJobDto>;
}

export interface PenHost {
  /** Pen mode is on (alt+p, the ✎ chip, or a pen's first touch). */
  on: boolean;
  /** The mouse draws as a pen ("simulate pen", a testing aid). */
  simulate: boolean;
  setOn: (on: boolean) => void;
  /** Queue one ink save in the client's one write sequence (sent in order, retried, idempotent by ink id). */
  saveInk: (ink: InkSaveBody) => void;
  /** Every queued write acknowledged ("unsaved" when it cannot be sent now). */
  settled: () => Promise<"saved" | "unsaved">;
  mintId: (prefix: string) => string;
  api: PenApi;
  poller: Poller;
  /** Open the companion at the current selection (a lasso's "ask the tutor · c"). */
  askCompanion: () => void;
  /** The ink of the pads shown, and their lines' readings. */
  ink: InkCache;
}

export const PenHostContext = createContext<PenHost | null>(null);

export function usePenHost(): PenHost | null {
  return useContext(PenHostContext);
}
