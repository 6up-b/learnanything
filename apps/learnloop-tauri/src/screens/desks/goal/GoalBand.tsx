// The goal band (spec §12.2, §12.8): under the top bar, in five parts: the goal in the learner's words, its
// learning objects as dots in path order with the depth, where the focused window is reading, the next step for
// the goal, and the tools (dimming, the path). Every value is goal.band's; the band computes nothing.
import { Fragment, useState } from "react";
import type { GoalBandDto, GoalsListSnapshot, ReadingPathDepth } from "../../../api/dto";
import { countsLine, dotClasses, dotTitle, formatDay, goalLabel, nextLine } from "./model";

export interface HereView {
  where: string;
  lo: string | null;
  tag: string | null;
  loId: string | null;
}

/** A goal as the chooser names it: the server's protected label (the learner's words, a held topic's name masked);
 * until that is read, or when it could not be, a neutral name rather than the raw sentence. */
function choiceLabel(labels: Record<string, string> | null, goal: GoalsListSnapshot["goals"][number], index: number): string {
  return labels?.[goal.id] ?? `Goal ${index + 1} · set ${formatDay(goal.createdAt)}`;
}

export function GoalBand({ band, goals, labels = null, here, dimOn, onToggleDim, onPath, onDepth, onOpenLo, onNext, onChooseGoal, onMapIt }: {
  band: GoalBandDto;
  goals: GoalsListSnapshot["goals"] | null;
  labels?: Record<string, string> | null;
  here: HereView | null;
  dimOn: boolean;
  onToggleDim: () => void;
  onPath: () => void;
  onDepth: (depth: ReadingPathDepth) => void;
  onOpenLo: (learningObjectId: string) => void;
  onNext: () => void;
  onChooseGoal: (goalId: string | null) => void;
  onMapIt: () => void;
}) {
  const [choosing, setChoosing] = useState(false);
  const mapped = band.status !== "no_scope" && band.status !== "not_a_deliverable";
  const dots = band.learningObjects ?? [];
  const next = nextLine(band);
  const active = (goals ?? []).filter((goal) => goal.status === "active");
  return (
    <div className="desk-goalband goalband" role="region" aria-label="your goal" data-goal-status={band.status} data-check-region="the goal band">
      <div className="gb-goal">
        <div className="gb-lab">{goalLabel(band)} <span className="gb-prov">your words, {formatDay(band.goal.setAt)}</span></div>
        {/* The learner's sentence as the server gives it: a held topic's name is masked there, nothing else. */}
        <button type="button" className="gb-t" title="switch this desk's goal" aria-expanded={choosing} onClick={() => setChoosing((open) => !open)}>
          “{band.goal.sentence}”
        </button>
        {choosing ? (
          <div className="gb-choose" role="menu" aria-label="this desk's goal">
            {active.map((goal, index) => (
              <button key={goal.id} type="button" role="menuitem" aria-current={goal.id === band.goalId ? "true" : undefined}
                onClick={() => { setChoosing(false); onChooseGoal(goal.id); }}>
                {choiceLabel(labels, goal, index)}
              </button>
            ))}
            <button type="button" role="menuitem" onClick={() => { setChoosing(false); onChooseGoal(null); }}>no goal (the lens off)</button>
          </div>
        ) : null}
      </div>
      {!mapped ? (
        <div className="gb-path gb-unmapped">
          <div className="gb-lab">{band.status === "not_a_deliverable" ? "Choose one of your goals" : "Reading suggestions unavailable"}</div>
          <div className="gb-ht">
            {band.status === "not_a_deliverable"
              ? (band.message ?? "Choose a goal you set, or create one in Goals.")
              : <>Find reading in your library for this goal · <button type="button" className="gb-map" onClick={onMapIt}>Find reading</button></>}
          </div>
        </div>
      ) : (
        <div className="gb-path">
          <div className="gb-lab">{band.status === "ask_depth" ? "how deep for this?" : countsLine(band)} <span className="gb-prov">readiness from cold checks</span></div>
          <div className="gb-row">
            <div className="gb-stops">
              {dots.map((dot) => (
                <Fragment key={dot.learningObjectId}>
                  <button type="button" className={dotClasses(dot, here?.loId ?? null)} data-gstop={dot.learningObjectId} title={dotTitle(dot)}
                    aria-label={dotTitle(dot)} onClick={() => onOpenLo(dot.learningObjectId)} />
                  {/* No LO's name on the ◇, and no hover (spec §12.6.1). */}
                  {dot.check ? <span className={`gs chk ${dot.check === "due" ? "due" : "done"}`} title={dot.check === "due" ? "Cold check due" : "Cold check answered today"} aria-label={dot.check === "due" ? "Cold check due" : "Cold check answered today"} /> : null}
                </Fragment>
              ))}
              {(band.unmatched ?? []).map((phrase) => (
                <button key={`unm:${phrase.phrase}`} type="button" className="gs unm" title={`not in your library yet: “${phrase.phrase}” · open Path`} aria-label={`not in your library yet: ${phrase.phrase}`} onClick={onPath} />
              ))}
            </div>
            <div className="gb-depth" title="how deep for this? one depth per goal">
              {(band.depths ?? []).map((depth) => (
                <button key={depth.id} type="button" className={depth.id === band.depth ? "on" : undefined} aria-pressed={depth.id === band.depth} data-gdepth={depth.id}
                  onClick={() => onDepth(depth.id)}>
                  {depth.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      <div className="gb-here">
        <div className="gb-lab"><span className="gring" title="In view" /> In view</div>
        <div className="gb-ht" data-goal-here="" title={here ? undefined : "No passage in view"}>
          {!here ? "—" : here.lo
            ? <>{here.where} · <b>{here.lo}</b>{here.tag ? <span className="off"> · {here.tag}</span> : null}</>
            : <>{here.where}{here.tag ? <span className="off"> · {here.tag}</span> : null}</>}
        </div>
      </div>
      <div className="gb-next">
        <div className="gb-lab">next for the goal</div>
        {next.kind === "read" || next.kind === "none"
          ? <span className="gb-ht">{next.text}</span>
          : <button type="button" className="gb-nb" onClick={onNext}>{next.text}</button>}
      </div>
      <div className="gb-tools">
        <button type="button" className={`gb-dim${dimOn ? " on" : ""}`} aria-pressed={dimOn} data-gdim="" title="dim the passages you can skip for this goal (they stay readable)" onClick={onToggleDim}>
          <span className="lg"><i className="b core" /><i className="b sup" /><i className="b skip" /></span>{dimOn ? "dimmed" : "shown"}
        </button>
        <button type="button" className="gb-pth" data-gpath="" title="your path (p)" onClick={onPath}>path <kbd>p</kbd></button>
      </div>
    </div>
  );
}

/** No goal on this desk: no band, a quiet chip in the top bar (spec §12.8). */
export function GoalTopChip({ goals, labels = null, onChooseGoal }: { goals: GoalsListSnapshot["goals"] | null; labels?: Record<string, string> | null; onChooseGoal: (goalId: string) => void }) {
  const [open, setOpen] = useState(false);
  const active = (goals ?? []).filter((goal) => goal.status === "active");
  return (
    <span className="desk-goalchip">
      <button type="button" className="tb" aria-expanded={open} onClick={() => setOpen((now) => !now)}>◎ set a goal</button>
      {open ? (
        <span className="gb-choose" role="menu" aria-label="a goal for this desk">
          {active.length ? active.map((goal, index) => (
            <button key={goal.id} type="button" role="menuitem" onClick={() => { setOpen(false); onChooseGoal(goal.id); }}>{choiceLabel(labels, goal, index)}</button>
          )) : <span className="none">no active goal yet · set one in Goals</span>}
        </span>
      ) : null}
    </span>
  );
}
