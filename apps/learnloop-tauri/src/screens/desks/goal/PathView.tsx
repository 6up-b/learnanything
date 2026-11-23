// The path view (spec §12.5): `p`, the band's "path" or a dashed dot opens it over the desk. Left, the goal,
// what it resolved to, the phrases not in the library, the depths with the size of each, "am I ready?" and the
// margin legend; right, one row per LO in path order with its primary section, another way ("use this one
// instead", stored), its cold check, the exercise worth trying, and at the end what isn't needed ("read it
// anyway", stored). Clicks open beside on the goal's desk. Everything shown is goal.band's and goal.lens's.
import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from "react";
import type { DeliverableSectionDto, GoalBandDto, GoalBandLoDto, GoalLensSectionDto, ReadingPathDepth } from "../../../api/dto";
import { formatDay, goalLabel } from "./model";

export interface NotNeeded {
  extractionId: string;
  book: string;
  section: GoalLensSectionDto;
}

type Line = NonNullable<GoalBandDto["path"]>["lines"][number];

function readiness(dot: GoalBandLoDto): string {
  if (dot.readiness === "demonstrated") return "demonstrated";
  if (dot.readiness === "likely") return "likely · LearnLoop's prediction";
  return "untested";
}

function paceLine(band: GoalBandDto): string {
  const pace = band.pace;
  if (!band.goal.dueAt) {
    return pace ? `No deadline, so no pace target; you've averaged ${pace.attemptsPerDay} attempts a day over 14 days.` : "No deadline, so no pace target.";
  }
  if (!pace || pace.neededPerDay === null) return `Due ${formatDay(band.goal.dueAt)}.`;
  return `Due ${formatDay(band.goal.dueAt)}: about ${pace.neededPerDay} attempts a day needed; you've averaged ${pace.attemptsPerDay}.`;
}

/** "change: type what's missing or not needed": a press opens a line for the learner's words, which go to the goal as
 *  a correction of its scope (curriculum.set_scope); without a way to send them, the line is not offered. */
function ScopeCorrection({ onCorrect }: { onCorrect?: (text: string) => void }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  if (!onCorrect) return null;
  if (!open) {
    return <> · <button type="button" className="faint gp-change" data-gp-change="" onClick={() => setOpen(true)}>change: type what's missing or not needed</button></>;
  }
  return (
    <> · <input
      className="gp-change-in" data-gp-change="" autoFocus value={text} aria-label="what's missing or not needed"
      placeholder="what's missing, or not needed"
      onChange={(event) => setText(event.target.value)}
      onKeyDown={(event) => {
        // Its keys are the learner's words: the path's own p and esc do not close the path from here.
        event.stopPropagation();
        if (event.key === "Escape") { setOpen(false); setText(""); }
        if (event.key === "Enter" && text.trim()) { onCorrect(text.trim()); setOpen(false); setText(""); }
      }} /></>
  );
}

export function PathView({ band, here, notNeeded, onClose, onDepth, onOpen, onUseInstead, onReadAnyway, onAddPhrase, onCorrect, lessonRow }: {
  band: GoalBandDto;
  here: string | null;
  notNeeded: NotNeeded[];
  onClose: () => void;
  onDepth: (depth: ReadingPathDepth) => void;
  onOpen: (section: { extractionId: string; sourceId?: string; startSpanId: string | null }) => void;
  onUseInstead: (learningObjectId: string, section: DeliverableSectionDto) => void;
  onReadAnyway: (extractionId: string, sectionId: string, on: boolean) => void;
  onAddPhrase: (phrase: string) => void;
  /** The learner's correction of the goal's scope, in their words (absent: no change line). */
  onCorrect?: (text: string) => void;
  /** The Teacher lesson on an LO, if one exists (opens its window): the desks' lesson windows render it. */
  lessonRow?: (learningObjectId: string) => ReactNode;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => { ref.current?.focus({ preventScroll: true }); }, []);
  const lines = new Map<string, Line>((band.path?.lines ?? []).map((line) => [line.learningObjectId, line]));
  const dots = band.learningObjects ?? [];
  const needed = dots.filter((dot) => dot.kind === "needed").length;
  const prerequisites = dots.filter((dot) => dot.kind === "prerequisite").length;
  const depthLabel = band.depths?.find((depth) => depth.id === band.depth)?.label ?? "";
  const onKeyDown = (event: ReactKeyboardEvent) => {
    // Its keys are its own while it is open (a menu scope): esc or p closes it.
    if (event.key === "Escape" || (event.key === "p" && !event.altKey && !event.ctrlKey && !event.metaKey)) {
      event.preventDefault();
      event.stopPropagation();
      onClose();
    }
  };
  return (
    <div ref={ref} className="ovl gpath desk-gpath" role="dialog" aria-label="your path" tabIndex={-1} onKeyDown={onKeyDown} data-goal-path="">
      <div className="gp-l">
        <div className="gb-lab">{goalLabel(band)} <span className="gb-prov">your words, {formatDay(band.goal.setAt)}</span></div>
        <h3>“{band.goal.sentence}”</h3>
        <div className="gp-scope">resolved to <b>{needed} learning object{needed === 1 ? "" : "s"}</b>, plus {prerequisites} prerequisite{prerequisites === 1 ? "" : "s"} you haven't shown yet<ScopeCorrection onCorrect={onCorrect} /></div>
        {(band.unmatched ?? []).map((phrase) => (
          <div key={phrase.phrase} className="gp-unm">
            “<i>{phrase.phrase}</i>” isn't in your library yet{phrase.proposedTitle ? <> → {phrase.proposedTitle}</> : null}
            <button type="button" className="act" onClick={() => onAddPhrase(phrase.phrase)}>add it</button>
          </div>
        ))}
        <div className="gp-depth">
          <div className="gb-lab">how deep for this? · one depth per goal</div>
          {(band.depths ?? []).map((depth) => (
            <button key={depth.id} type="button" className={`gp-d${depth.id === band.depth ? " on" : ""}`} aria-pressed={depth.id === band.depth} onClick={() => onDepth(depth.id)}>
              <b>{depth.label}</b>
              {depth.sections !== null ? <span className="len"> · {depth.sections} section{depth.sections === 1 ? "" : "s"} · {depth.minutes} min</span> : null}
              <span className="t">{depth.means}</span>
            </button>
          ))}
        </div>
        <div className="gp-ready">
          <div className="gb-lab">am I ready?</div>
          Only delayed cold checks answer that. Reading raises LearnLoop's prediction, never a certification.
          <span className="faint">{paceLine(band)}</span>
        </div>
        <div className="gp-key">
          <div className="gb-lab">in the margins · from section coverage</div>
          <div><i className="b core" />core · the primary section of a goal LO</div>
          <div><i className="b sup" />supporting · a prerequisite, another way, or an example</div>
          <div><i className="b skip" />skippable · no LO your goal needs; dimmed, still readable</div>
          <div className="faint">later · needed only deeper · already shown · its LO is demonstrated</div>
        </div>
      </div>
      <div className="gp-r-wrap">
        <div className="gp-gh">your path · prerequisites before what assumes them · {depthLabel}</div>
        {dots.map((dot, index) => {
          const line = lines.get(dot.learningObjectId);
          const later = dot.kind === "later";
          return (
            <div key={dot.learningObjectId} className={`gp-lo${later ? " later" : ""}${here === dot.learningObjectId ? " here" : ""}`} data-gp-lo={dot.learningObjectId}>
              <div className="gp-h">
                <span className={`gp-n rd-${dot.readiness}${dot.kind === "prerequisite" ? " pre" : ""}`} />
                <span className="gp-ord">{index + 1}</span>
                <span className="gp-ti">{dot.title ?? "a topic with a cold check due"}</span>
                <span className={`gp-tag ${later ? "later" : dot.kind === "needed" ? "core" : "prerequisite"}`}>{later ? "later" : dot.kind === "needed" ? "core" : "prerequisite"}</span>
                {here === dot.learningObjectId ? <span className="gp-tag here">you are reading here</span> : null}
                <span className="grow" />
                <span className={`gp-rd rd-${dot.readiness}`}>{readiness(dot)}</span>
              </div>
              {line ? (
                <button type="button" className="gp-prim" onClick={() => onOpen({ extractionId: line.section.extractionId, sourceId: line.section.sourceId, startSpanId: line.section.startSpanId })}>
                  <span className="g">§</span>
                  <span className="gp-src">{line.section.book}</span>
                  <span className="gp-at">{line.section.title}</span>
                  <span className="gp-why">{line.section.treatmentWords}{line.reason ? ` · ${line.reason}` : ""}</span>
                  <span className="gp-st">{line.section.read ? "read" : "not read"}{line.override ? ` · you chose ${line.override.replace("_", " ")}` : ""}</span>
                </button>
              ) : dot.primary ? (
                <button type="button" className="gp-prim" onClick={() => onOpen({ extractionId: dot.primary!.extractionId, startSpanId: dot.primary!.startSpanId })}>
                  <span className="g">§</span>
                  <span className="gp-src">{dot.primary.book}</span>
                  <span className="gp-at">{dot.primary.title}</span>
                  <span className="gp-why">{later ? "needed only at a deeper depth" : "not on the path yet"}</span>
                  <span className="gp-st" />
                </button>
              ) : null}
              {(line?.alternates ?? []).map((alternate) => (
                <div key={`${alternate.extractionId}/${alternate.sectionId}`} className="gp-alt" role="group">
                  <button type="button" className="gp-alt-open" onClick={() => onOpen({ extractionId: alternate.extractionId, sourceId: alternate.sourceId, startSpanId: alternate.startSpanId })}>
                    <span className="g">§</span>
                    <span className="gp-src">another way · {alternate.book}</span>
                    <span className="gp-at">{alternate.title}</span>
                    <span className="gp-why">{alternate.difference || alternate.treatmentWords}</span>
                  </button>
                  {alternate.canUseInstead ? (
                    <button type="button" className="gp-st gp-use" onClick={() => onUseInstead(dot.learningObjectId, alternate)}>use this one instead</button>
                  ) : <span className="gp-st" />}
                </div>
              ))}
              {dot.check ? (
                <div className={`gp-chk${dot.check === "answered" ? " done" : ""}`}>
                  <span className="g">◇</span>
                  <span className="gp-src">cold check</span>
                  <span className="gp-at">{dot.check === "due" ? "due today" : "answered today"}</span>
                  <span className="gp-why">{dot.check === "due" ? "answer it in Today, on your own" : "answered on your own"}</span>
                  <span className="gp-st" />
                </div>
              ) : null}
              {line?.exercise ? (
                <button type="button" className="gp-alt" onClick={() => onOpen({ extractionId: line.exercise!.extractionId, startSpanId: line.exercise!.spanIds[0] ?? null })}>
                  <span className="g">§</span>
                  <span className="gp-src">exercise worth trying</span>
                  <span className="gp-at">{line.exercise.label}</span>
                  <span className="gp-why">picked from the primary section's book</span>
                  <span className="gp-st" />
                </button>
              ) : null}
              {lessonRow ? lessonRow(dot.learningObjectId) : null}
            </div>
          );
        })}
        <div className="gp-grp skipg">
          <div className="gp-gh">┊ not needed for your goal · read it anyway</div>
          {notNeeded.length === 0 ? <div className="gp-s"><span className="g" /><span className="gp-why">nothing in the readings on your desk</span></div> : null}
          {notNeeded.map((entry) => (
            <div key={`${entry.extractionId}/${entry.section.sectionId}`} className="gp-s" data-gp-skip={entry.section.sectionId}>
              <span className="g">§</span>
              <span className="gp-src">{entry.book}</span>
              <span className="gp-at">{entry.section.title}</span>
              <span className="gp-why">
                {entry.section.reasonMd}
                <button type="button" className="gp-anyway" onClick={() => onReadAnyway(entry.extractionId, entry.section.sectionId, entry.section.choice !== "read_anyway")}>
                  {entry.section.choice === "read_anyway" ? "dim it again" : "read it anyway"}
                </button>
              </span>
            </div>
          ))}
        </div>
      </div>
      <button type="button" className="gp-close" aria-label="close your path" onClick={onClose}>esc</button>
    </div>
  );
}
