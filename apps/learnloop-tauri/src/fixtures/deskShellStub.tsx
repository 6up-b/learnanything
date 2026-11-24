// A stand-in for the desks (the Reader place) in the app's tests about the shell around them: what the app asks of the
// desks (its open request, the companion's ask count, the workbench's resume, the reader's hand-offs) is shown on the
// stand-in's element, and the desks' reports to the app (the book being read, skimming, an error) are made as the
// real desks make them. The real desks in the app are proven in app/App.desks.test.tsx (fixtures/desks/realApp.tsx).
//
// Use: vi.mock("../screens/desks/DeskShell", async () => ({ DeskShell: (await import("../fixtures/deskShellStub")).DeskShellStub }));
import { useEffect } from "react";
import type { DeskShellProps } from "../screens/desks/DeskShell";

export const deskStub: {
  /** Every render's props, in order. */
  props: DeskShellProps[];
  /** The titles the stand-in reports for the books it opens (the real desks read them from the library). */
  titles: Record<string, string>;
  /** Reported as the window's skimming once mounted, when set. */
  skim: boolean | undefined;
  /** Reported through onError once mounted, when set. */
  error: string | null;
  /** Reported as the book being read once mounted, when set: a book window the desks kept from before (their own
   *  layout), open without any request from the app. */
  restored: { sourceId: string; title: string } | null;
  /** The requests already done and the book the stand-in has open, as the real desks keep them for the app's run (a
   *  remount neither redoes a request nor forgets a closed book). */
  done: number;
  reading: { sourceId: string; title: string } | null | undefined;
} = { props: [], titles: {}, skim: undefined, error: null, restored: null, done: -1, reading: undefined };

export function resetDeskStub(): void {
  deskStub.props.length = 0;
  deskStub.titles = {};
  deskStub.skim = undefined;
  deskStub.error = null;
  deskStub.restored = null;
  deskStub.done = -1;
  deskStub.reading = undefined;
}

export function lastDeskProps(): DeskShellProps {
  const last = deskStub.props[deskStub.props.length - 1];
  if (!last) throw new Error("the desks were never shown");
  return last;
}

export function DeskShellStub(props: DeskShellProps) {
  deskStub.props.push(props);
  const request = props.openRequest ?? null;
  const { onReadingChange, onSkimmingChange, onError } = props;
  useEffect(() => {
    // The desks open (or focus) the book asked for, once per request, which becomes the book being read; shown again,
    // they report the book they have open (a closed one stays closed).
    if (request?.sourceId && request.seq > deskStub.done) {
      deskStub.done = request.seq;
      deskStub.reading = { sourceId: request.sourceId, title: deskStub.titles[request.sourceId] ?? "" };
    }
    if (deskStub.reading !== undefined) onReadingChange?.(deskStub.reading);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [request?.seq, request?.sourceId]);
  useEffect(() => {
    if (deskStub.restored && !request?.sourceId && deskStub.reading === undefined) {
      deskStub.reading = deskStub.restored;
      onReadingChange?.(deskStub.restored);
    }
    if (deskStub.skim !== undefined) onSkimmingChange?.(deskStub.skim);
    if (deskStub.error) onError(deskStub.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const resume = props.reader?.workbench?.resumeProblem ?? null;
  return (
    <div
      data-testid="reader-stub"
      data-source={request?.sourceId ?? "shelf"}
      data-span={request?.spanId ?? ""}
      data-reading={request?.reading ?? ""}
      data-phrase={request?.phrase ?? ""}
      data-seq={request ? String(request.seq) : ""}
      data-ask-request={props.askRequest ?? 0}
      data-resume={resume?.sessionId ?? ""}
      data-resume-reading={resume?.extractionId ?? ""}
    >
      reader
      {/* Closing the last book window on the desks: no book is being read. */}
      <button type="button" onClick={() => { deskStub.reading = null; onReadingChange?.(null); }}>close book</button>
    </div>
  );
}
