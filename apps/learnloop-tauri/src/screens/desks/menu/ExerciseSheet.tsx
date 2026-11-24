// Make it practice on an exercise (spec §9.1 `p`): the exercise's own words first, as the book has them, then the
// import; once it lands, the items it made, each with the edit and retire controls, said plainly to be in the queue
// already. The review follows the admission: holding drafts before they join the queue needs storage of its own (an
// owner option, recorded in reader-rd5b.md). Exam or held-out material is never shown here and never imported.
import { useEffect, useRef, useState } from "react";
import type { PassageContentDto, ReaderExerciseImportReceiptDto, ReaderExerciseImportStatusDto, ReaderExerciseImportedItem } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import { CardControls } from "../../../components/CardControls";
import { useSheetFocus } from "./ContextMenu";

const FINISHED = new Set(["completed", "failed", "cancelled"]);

function messageOf(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

export function ExerciseSheet({ readWords, startImport, readStatus, poller, owner, onClose, onError }: {
  /** The exercise's passages as the source has them (`passage.content`). */
  readWords: () => Promise<PassageContentDto>;
  startImport: () => Promise<ReaderExerciseImportReceiptDto>;
  readStatus: (batchId: string) => Promise<ReaderExerciseImportStatusDto>;
  poller: Poller;
  /** The window asked from: the import's poll waits while it is paused. */
  owner: string | null;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const [words, setWords] = useState<PassageContentDto | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [phase, setPhase] = useState<"review" | "importing" | "done" | "failed">("review");
  const [items, setItems] = useState<ReaderExerciseImportedItem[]>([]);
  const [skipped, setSkipped] = useState(0);
  const [retired, setRetired] = useState<Set<string>>(new Set());
  const node = useRef<HTMLDivElement | null>(null);
  const stop = useRef<() => void>(() => undefined);
  useSheetFocus(node, onClose);

  useEffect(() => {
    let live = true;
    readWords().then((read) => live && setWords(read), (error: unknown) => live && setFailure(messageOf(error)));
    return () => {
      live = false;
      stop.current();
    };
    // Read once, for the exercise it opened on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const begin = async () => {
    setPhase("importing");
    setFailure(null);
    try {
      const receipt = await startImport();
      stop.current = poller.register<ReaderExerciseImportStatusDto>({
        key: `exercise-import:${receipt.batchId}`,
        owner,
        request: () => readStatus(receipt.batchId),
        onResult: (status) => {
          if (!FINISHED.has(status.status)) return { done: false };
          if (status.status === "completed" && status.result) {
            setItems(status.result.items);
            setSkipped(status.result.skipped.length);
            setPhase("done");
          } else {
            setFailure(status.error?.message ?? status.message ?? "Couldn’t add the exercise. Close this and reopen it to try again.");
            setPhase("failed");
          }
          return { done: true };
        },
      });
    } catch (error) {
      setFailure(messageOf(error));
      setPhase("failed");
    }
  };

  const withheld = words !== null && (words.withheld !== false || words.spans.some((span) => span.withheld !== false));
  return (
    <div ref={node} tabIndex={-1} className="desk-sheet desk-exercise" role="dialog" aria-label="make it practice from this exercise">
      <div className="head">✎ make it practice · this exercise, as the book has it</div>
      {words === null && !failure ? <div className="note">◐ reading the exercise…</div> : null}
      {withheld ? <div className="note">this is exam or held-out material: it is not shown or made into practice from here</div> : null}
      {words && !withheld && phase === "review" ? (
        <>
          <div className="words" data-exercise-words="">
            {words.spans.map((span) => <p key={span.spanId}>{span.text}</p>)}
          </div>
          <div className="note">importing adds what it makes to your queue at once; you can edit or retire any of it there</div>
        </>
      ) : null}
      {phase === "importing" ? <div className="note">◐ importing the exercise…</div> : null}
      {phase === "done" ? (
        <>
          <div className="note">{items.length === 0 ? "No practice questions were added." : items.length === 1 ? "this is in your queue now · edit or retire it if it is wrong" : `these ${items.length} are in your queue now · edit or retire any that is wrong`}{skipped ? ` · ${skipped} part${skipped === 1 ? "" : "s"} could not be made` : ""}</div>
          {items.map((item) => (
            <div key={item.practiceItemId} className="item" data-imported-item={item.practiceItemId}>
              <div className="t">{retired.has(item.practiceItemId) ? `retired · ${item.title}` : item.title}</div>
              <div className="p">{item.prompt}</div>
              {retired.has(item.practiceItemId) ? null : (
                <CardControls practiceItemId={item.practiceItemId} prompt={item.prompt} expectedAnswer={null} onError={onError}
                  onRetired={() => setRetired((now) => new Set([...now, item.practiceItemId]))} />
              )}
            </div>
          ))}
        </>
      ) : null}
      {failure ? <div className="note err">{failure}</div> : null}
      <div className="acts">
        {phase === "review" && words && !withheld ? <button type="button" onClick={() => void begin()}>import it as practice</button> : null}
        <button type="button" onClick={onClose}>{phase === "done" ? "done" : phase === "failed" ? "close" : "not now"}</button>
      </div>
    </div>
  );
}
