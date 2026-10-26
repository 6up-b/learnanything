// Reader workbench: the Reader's working posture (spec §5.1 "the split"; UX
// S1, W5, W8, W15), split out of ReaderScreen before RW2b added the ladder
// (RW2a friction note 5). The book's cover while it is hidden, the
// resizable separator, and the workbench pane at the remembered width (or
// stacked below the 1,040 px breakpoint). The workbench itself (steps,
// checks, the help ladder) is the shared Workbench component the practice
// screen's "Work in steps" uses too.
import { useEffect, useState } from "react";
import type { PassageTarget, WorkbenchSessionDto } from "../../api/dto";
import { algoConfig } from "../../app/algoConfig";
import { AskOverlay } from "../../components/AskOverlay";
import { COLOR, FONT_MONO } from "../../components/term";
import { Workbench } from "../workbench/Workbench";
import { WORKBENCH_COPY } from "../workbench/stepModel";
import { MIN_WORKBENCH_WIDTH, SPLIT_STEP, clampSplitWidth } from "../workbench/splitWidth";
import type { ActiveWorkbench, ReaderWorkbench } from "./useReaderWorkbench";

/** The palette's ask while a problem is open (UX Phase 2 fix round 3). */
export const WORKING_ASK_WAITS = "Ask the tutor is beside the book. Leave for now (your steps are kept) and Ask opens.";

export function ReaderWorkingPosture({
  wbCtl,
  active,
  stacked,
  bookHidden,
  sourceShown,
  practiceSessionId,
  onLeave,
  onAbandoned,
  onPeekPassage,
  onError,
  askWaiting = null,
}: {
  wbCtl: ReaderWorkbench;
  active: ActiveWorkbench;
  stacked: boolean;
  bookHidden: boolean;
  sourceShown: boolean;
  practiceSessionId: string | null;
  /** Leave and Abandon carry the generation the workbench was shown in (R5). */
  onLeave: (session: WorkbenchSessionDto, generation: number) => void;
  onAbandoned: (session: WorkbenchSessionDto, generation: number) => void;
  /** RW2b: "compare with the book" peeks its passage in the source pane. */
  /** RW2c review F1: ``target`` names the passage's book when the workbench knows it. */
  onPeekPassage: (spanId: string, target?: PassageTarget) => void;
  onError: (message: string) => void;
  /** UX Phase 2 fix round 3: the palette asked for the tutor while this
   *  problem is open. Ask sits beside the book, which this posture hides, so
   *  a line says how to get there; leaving is the learner's call. */
  askWaiting?: { onDismiss: () => void } | null;
}) {
  // Reader CA2 (§7.1, §7.6): asking about a step no longer means leaving the
  // problem. With the panel on and the problem bound to an item in a practice
  // session, Ask opens inline under the focused step; the palette's Ask opens
  // it too, instead of the "leave for now" line.
  const itemId = active.session.practiceItemId;
  const inlineAsk = algoConfig().ask !== null && itemId !== null && practiceSessionId !== null && !active.readOnly;
  const [askSignal, setAskSignal] = useState(0);
  const [workMd, setWorkMd] = useState("");
  useEffect(() => {
    if (!askWaiting || !inlineAsk) return;
    setAskSignal((value) => value + 1);
    askWaiting.onDismiss();
  }, [askWaiting, inlineAsk]);
  return (
    <>
      {bookHidden && sourceShown ? (
        // W8: the book hidden so this can be the learner's own attempt.
        <div
          data-testid="workbench-book-cover"
          style={{
            position: "absolute", zIndex: 20, background: COLOR.bg, display: "flex", alignItems: "center",
            justifyContent: "center", padding: 32, textAlign: "center",
            ...(stacked ? { left: 0, right: 0, bottom: 0, top: "50%" } : { left: 0, top: 0, bottom: 0, width: `calc(100% - ${wbCtl.width + 6}px)` }),
          }}
        >
          <div style={{ maxWidth: 360, fontFamily: FONT_MONO, fontSize: 12, lineHeight: 1.7, color: COLOR.textDim }}>
            <p style={{ margin: 0 }}>{WORKBENCH_COPY.bookHiddenCover}</p>
            <p style={{ margin: "10px 0 0" }}>{WORKBENCH_COPY.bookHiddenHow}</p>
          </div>
        </div>
      ) : null}
      {!stacked ? (
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="resize the workbench"
          aria-valuemin={MIN_WORKBENCH_WIDTH}
          aria-valuemax={clampSplitWidth(Number.MAX_SAFE_INTEGER, window.innerWidth)}
          aria-valuenow={wbCtl.width}
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
              event.preventDefault();
              // The workbench is on the right: dragging the edge left widens it.
              wbCtl.resizeBy(event.key === "ArrowLeft" ? SPLIT_STEP : -SPLIT_STEP);
            }
          }}
          onMouseDown={(event) => {
            event.preventDefault();
            const startX = event.clientX;
            const startWidth = wbCtl.width;
            const onMove = (move: MouseEvent) => wbCtl.setWidth(startWidth + (startX - move.clientX));
            const onUp = () => {
              window.removeEventListener("mousemove", onMove);
              window.removeEventListener("mouseup", onUp);
            };
            window.addEventListener("mousemove", onMove);
            window.addEventListener("mouseup", onUp);
          }}
          style={{ width: 6, flexShrink: 0, cursor: "col-resize", borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg }}
        />
      ) : null}
      <div
        data-workbench-pane=""
        data-layout={stacked ? "stacked" : "split"}
        className="ll-scroll"
        style={{
          width: stacked ? "100%" : wbCtl.width, flexShrink: 0, minHeight: 0, overflowY: "auto",
          ...(stacked ? { flex: sourceShown ? "0 0 50%" : "1 1 auto" } : { height: "100%" }),
        }}
      >
        {askWaiting && !inlineAsk ? (
          <div
            role="status"
            data-testid="workbench-ask-waiting"
            style={{ display: "flex", gap: 10, alignItems: "baseline", margin: "10px 14px 0", padding: "8px 10px", border: `1px solid ${COLOR.border}`, fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}
          >
            <span style={{ flex: 1 }}>{WORKING_ASK_WAITS}</span>
            <button type="button" aria-label="Dismiss" onClick={askWaiting.onDismiss} style={{ border: 0, background: "transparent", color: COLOR.textDim, cursor: "pointer", fontFamily: FONT_MONO }}>
              ×
            </button>
          </div>
        ) : null}
        <Workbench
          key={active.session.sessionId}
          initial={active.session}
          serverSession={active.session}
          layout={stacked ? "stacked" : "split"}
          readOnly={active.readOnly}
          autoFocus={active.autoFocus}
          practiceSessionId={practiceSessionId}
          schedulerCandidateId={active.schedulerCandidateId}
          planPresentationId={active.planPresentationId}
          // R5: the workbench's own callbacks carry the generation it was
          // shown in, so a late one after Leave or a book change is dropped.
          onSession={(next) => wbCtl.update(next, active.generation)}
          onLeave={(session) => onLeave(session, active.generation)}
          onAbandoned={(session) => onAbandoned(session, active.generation)}
          onSubmitted={(result) => wbCtl.submitted(result, active.generation)}
          onShowInBook={() => wbCtl.setSheetOpen(!wbCtl.sheetOpen)}
          onPeekPassage={onPeekPassage}
          onError={onError}
          {...(inlineAsk && itemId !== null && practiceSessionId !== null ? {
            askSignal,
            onWorkChange: setWorkMd,
            renderAsk: ({ stepNumber, stepsCount, onClose }: { stepNumber: number | null; stepsCount: number; onClose: () => void }) => (
              <AskOverlay
                variant="inline"
                target={{
                  context: "practice",
                  practiceItemId: itemId,
                  sessionId: practiceSessionId,
                  // The open problem is one attempt until it is submitted:
                  // resuming it is not a reattempt (§7.3), so its key is the session's.
                  submissionId: `workbench:${active.session.sessionId}`,
                  workbenchSessionId: active.session.sessionId,
                  ...(stepNumber !== null ? { aboutStep: stepNumber } : {}),
                  stepsCount,
                  workMd,
                  readDraft: () => workMd,
                  attemptProgress: workMd.trim() ? "draft_started" : "no_draft"
                }}
                onClose={onClose}
                onToast={onError}
              />
            )
          } : {})}
        />
      </div>
    </>
  );
}
