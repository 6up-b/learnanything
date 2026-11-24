// "What this knows" (spec §9.1 `i`): the union read of the object's passages as one panel, grouped, each row with its
// anchor quality (an alias that needs re-anchoring said so), each item openable where it has a place to open. A due
// check shows that one is due and nothing of it (§12.6.1).
import { useEffect, useRef, useState } from "react";
import { useSheetFocus } from "./ContextMenu";
import type { MenuObjectInput, PassageKnowsDto, PassageUnionSpanDto } from "../../../api/dto";

export interface KnowsActions {
  openThread: (questionEventId: string) => void;
  openPadBlock: (padId: string, blockId: string) => void;
  openPassage: (extractionId: string, spanId: string) => void;
}

function quality(alias: string): string {
  return alias === "needs_reanchor" ? " · from an earlier version of this source; the link may open nearby" : "";
}

function day(at: string | null | undefined): string {
  if (!at) return "";
  const date = new Date(at);
  return Number.isNaN(date.getTime()) ? "" : ` · ${date.toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`;
}

/** A note linked beside the passage (the learner's own, from their notes): its line and title. */
interface LinkedNote {
  linkId?: string;
  line?: string;
  note?: { title?: string; text?: string };
}

export function knowsGroups(place: PassageUnionSpanDto, actions: KnowsActions, at?: { extractionId: string; spanId: string }): Array<{ title: string; rows: Array<{ text: string; open?: () => void }> }> {
  // What lives on the passage itself (a highlight, a figure, a written question) opens the passage, where it shows.
  const openHere = at ? () => actions.openPassage(at.extractionId, at.spanId) : undefined;
  const groups: Array<{ title: string; rows: Array<{ text: string; open?: () => void }> }> = [
    { title: "your questions in the companion", rows: place.exchanges.map((each) => ({ text: `? ${each.questionMd} · ${each.quality.replace(/_/g, " ")}${quality(each.alias)}${day(each.createdAt)}`, open: () => actions.openThread(each.questionEventId) })) },
    { title: "questions that changed what LearnLoop inferred", rows: place.adjustments.map((each) => ({ text: "? a question of yours here changed how LearnLoop read your words", open: () => actions.openThread(each.questionEventId) })) },
    { title: "your pads", rows: place.padBlocks.map((each) => ({ text: `› a ${each.kind.replace(/_/g, " ")} line${quality(each.alias)}${day(each.createdAt)}`, open: () => actions.openPadBlock(each.padId, each.liftedFromBlockId ? each.blockId : each.blockId) })) },
    { title: "your highlights and notes", rows: place.annotations.map((each) => ({ text: `› ${each.type}${each.learnerText ? ` · ${each.learnerText}` : ""}${day(each.createdAt)}`, open: openHere })) },
    { title: "your notes linked here", rows: (place.notes as LinkedNote[]).map((each) => ({ text: `› ${each.line || each.note?.title || "a note of yours"}${each.note?.text ? ` · ${each.note.text.slice(0, 80)}` : ""}` })) },
    { title: "what LearnLoop read in your words", rows: place.gaps.map((each) => ({ text: `◇ a ${each.kind.replace(/_/g, " ")} (${each.sourceKind.replace(/_/g, " ")}) · ${each.quality.replace(/_/g, " ")}${quality(each.alias)}${day(each.createdAt)}` })) },
    { title: "carried", rows: place.carried.map((each) => ({ text: `◌ ${each.text}${day(each.since)}` })) },
    { title: "linked passages", rows: place.passageLinks.map((each) => ({ text: `§ ${each.relation.replace(/_/g, " ")}${each.quote ? ` · “${each.quote.slice(0, 80)}”` : ""}${quality(each.alias)}` })) },
    { title: "figures", rows: place.figures.map((each) => ({ text: `◇ a figure · ${each.verification.replace(/_/g, " ")}${day(each.createdAt)}`, open: openHere })) },
    { title: "questions written for this passage", rows: place.authoredQuestions.map((each) => ({ text: `? ${each.questionMd} · ${each.status}`, open: openHere })) },
    { title: "cold checks", rows: place.checksDue.length ? [{ text: "a cold check is due before this passage (nothing of it shows until it opens)" }] : [] },
  ];
  return groups.filter((group) => group.rows.length);
}

export function KnowsPanel({ object, load, actions, onClose }: {
  object: MenuObjectInput;
  load: (object: MenuObjectInput) => Promise<PassageKnowsDto>;
  actions: KnowsActions;
  onClose: () => void;
}) {
  const [found, setFound] = useState<PassageKnowsDto | null>(null);
  const panel = useRef<HTMLDivElement | null>(null);
  useSheetFocus(panel, onClose);
  const [failure, setFailure] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    load(object).then((read) => live && setFound(read), (error: unknown) => live && setFailure(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error)));
    return () => {
      live = false;
    };
    // Read once for the object it opened on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div ref={panel} tabIndex={-1} className="desk-sheet desk-knows" role="dialog" aria-label="passage details">
      <div className="head">i · passage details · your notes, questions, related passages and figures tied to this passage</div>
      {failure ? <div className="note err">{failure}</div> : null}
      {found === null && !failure ? <div className="note">◐ reading it…</div> : null}
      {found?.places.length === 0 ? <div className="note">nothing here yet</div> : null}
      {found?.places.map((place) => {
        const groups = knowsGroups(place.knows, actions, { extractionId: place.extractionId, spanId: place.spanId });
        return (
          <div key={`${place.extractionId}:${place.spanId}`} className="place" data-knows-place={place.spanId}>
            <button type="button" className="ph" onClick={() => actions.openPassage(place.extractionId, place.spanId)}>
              § the passage{place.role ? ` · ${place.role}` : ""} · shown {place.knows.exposure.timesShown} time{place.knows.exposure.timesShown === 1 ? "" : "s"}
            </button>
            {groups.length === 0 ? <div className="note">nothing held about it yet</div> : groups.map((group) => (
              <div key={group.title} className="grp">
                <div className="gt">{group.title}</div>
                {group.rows.map((row, index) => row.open
                  ? <button key={index} type="button" className="row" onClick={row.open}>{row.text}</button>
                  : <div key={index} className="row">{row.text}</div>)}
              </div>
            ))}
          </div>
        );
      })}
      <div className="acts"><button type="button" onClick={onClose}>close</button></div>
    </div>
  );
}
