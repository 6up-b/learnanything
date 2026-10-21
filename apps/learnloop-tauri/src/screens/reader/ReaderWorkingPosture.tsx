// Reader workbench: the Reader's working posture (spec §5.1 "the split"; UX
// S1, W5, W8, W15), split out of ReaderScreen before RW2b added the ladder
// (RW2a friction note 5). The book's cover while it is hidden, the
// resizable separator, and the workbench pane at the remembered width (or
// stacked below the 1,040 px breakpoint). The workbench itself (steps,
// checks, the help ladder) is the shared Workbench component the practice
// screen's "Work in steps" uses too.
import type { PassageTarget, WorkbenchSessionDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { Workbench } from "../workbench/Workbench";
import { WORKBENCH_COPY } from "../workbench/stepModel";
import { MIN_WORKBENCH_WIDTH, SPLIT_STEP, clampSplitWidth } from "../workbench/splitWidth";
import type { ActiveWorkbench, ReaderWorkbench } from "./useReaderWorkbench";

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
}) {
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
        />
      </div>
    </>
  );
}
