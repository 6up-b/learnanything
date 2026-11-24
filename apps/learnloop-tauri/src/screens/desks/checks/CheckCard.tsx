// The inline cold check's markup on the desks (spec §12.6.1, §12.6.4-§12.6.6; RD7's frontend half): the closed marker
// before the host passage (no question, no LO title, no provenance, no purpose: no cues), the open card (inline at the
// host passage when its reading is on this desk, else centred near the top), and the answered card with the reply's
// reason in plain words. Every word about what an answer counts as comes from the server's reply.
import { useSyncExternalStore, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { MarkdownMath } from "../../../render/MarkdownMath";
import type { ReaderLens } from "../source/types";
import { FitMath } from "../fitMath";
import type { CheckDesk, DueCheck, OpenCheck } from "./controller";
import { PRIMED_BY_NOTE_WORDS, REASON_WORDS, answeredHead, groupsLine, lookedLine, type CheckReason } from "./model";

/** "◇ a check is due before this page · on your own" with "check now" and "later" (folded: a quiet line). */
export function CheckMarker({ checks, desk, onCheckNow }: { checks: DueCheck[]; desk: CheckDesk; onCheckNow: (commitmentId: string) => void }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const check = checks[0];
  if (!check) return null;
  const held = desk.holding();
  if (desk.deferred(check.commitmentId)) {
    return (
      <div className="ck-later" data-check-marker={check.commitmentId} data-check-folded="">
        <span className="g">◇</span> a cold check is due before this page{" "}
        <button type="button" className="lnk" disabled={held} title={held ? "another cold check is open" : undefined} onClick={() => onCheckNow(check.commitmentId)}>check now</button>
      </div>
    );
  }
  return (
    <div className="callout gq ck-closed" data-check-marker={check.commitmentId}>
      <span className="lab">◇ a cold check is due before this page · on your own</span>
      <div className="gqr">
        <span className="faint">whatever states the answer is veiled in place while you answer, then comes back</span>
        <button type="button" className="act" onClick={() => desk.defer(check.commitmentId)}>later</button>
        <button type="button" className="act pri" disabled={held} title={held ? "another cold check is open" : undefined} onClick={() => onCheckNow(check.commitmentId)}>check now</button>
      </div>
      {held && desk.open()?.card.commitmentId !== check.commitmentId ? <div className="ck-note">another check is open · answer it or say not now first</div> : null}
    </div>
  );
}

function question(open: OpenCheck): string {
  const prompt = open.card.prompt as { prompt?: unknown };
  return typeof prompt.prompt === "string" ? prompt.prompt : "";
}

function feedback(open: OpenCheck): string {
  const reply = open.reply as { feedbackMd?: unknown } | null;
  return reply && typeof reply.feedbackMd === "string" ? reply.feedbackMd : "";
}

function answerKeys(desk: CheckDesk) {
  return (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    // The answer's keys are the learner's: the desks' own keys never fire from here.
    event.stopPropagation();
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void desk.submit();
    }
  };
}

/** The card's reason line after the answer. */
function ReasonLine({ open }: { open: OpenCheck }) {
  const reason = (open.reply?.reason ?? null) as CheckReason | null;
  if (!reason) return null;
  const byNote = reason === "primed" && open.reply?.primedBy === "unmeasured_note";
  return <div className="ck-reason" data-check-reason={reason} {...(byNote ? { "data-check-primed-by": "unmeasured_note" } : {})}>{byNote ? PRIMED_BY_NOTE_WORDS : REASON_WORDS[reason]}</div>;
}

/** The open (or answered) card at the host passage: the goal lens's own callout, opened. */
export function CheckCardInline({ desk }: { desk: CheckDesk }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const open = desk.open();
  if (!open) return null;
  const veiled = open.veiled;
  const looked = lookedLine(open.looked, open.coldNow);
  if (open.phase === "answered") {
    const cold = Boolean(open.reply?.cold);
    return (
      <div className="callout gq done" data-check-card="inline" data-check-phase="answered">
        <span className="lab">◇ a cold check</span>
        <div className="gqq"><FitMath><MarkdownMath value={question(open)} /></FitMath></div>
        <div className="gqy"><span className="who">{answeredHead(cold)}</span>{open.answer}</div>
        <ReasonLine open={open} />
        {feedback(open) ? <div className="gqf"><span className="who">◇ feedback</span><FitMath><MarkdownMath value={feedback(open)} /></FitMath></div> : null}
        <div className="gqv"><b>{veiled.length} {veiled.length === 1 ? "thing was" : "things were"} veiled while you answered</b>{veiled.length ? <> · {groupsLine(veiled)}</> : null} · <span className="faint">back now</span></div>
        <div className="gqr"><span className="faint" /><button type="button" className="act" onClick={() => desk.close()}>close</button></div>
      </div>
    );
  }
  return (
    <div className="callout gq open" data-check-card="inline" data-check-phase={open.phase}>
      <span className="lab">◇ a cold check · now</span>
      <div className="gqq"><FitMath><MarkdownMath value={question(open)} /></FitMath></div>
      <textarea className="gqa" aria-label="your answer" spellCheck={false} value={open.answer} disabled={open.phase !== "open"}
        onChange={(event) => desk.setAnswer(event.target.value)} onKeyDown={answerKeys(desk)} autoFocus />
      <div className="gqv"><b>veiled while you answer</b> · {groupsLine(desk.veils()) || "nothing on screen"}</div>
      {looked ? <div className="ck-looked">{looked}</div> : null}
      {open.error ? <div className="ck-note" role="alert">{open.error}</div> : null}
      <div className="gqr">
        <span className="faint">nothing moves · only an on-your-own answer settles this check</span>
        <button type="button" className="act" onClick={() => void desk.abandon()}>not now</button>
        <button type="button" className="act pri" disabled={open.phase !== "open" || !open.answer.trim()} onClick={() => void desk.submit()}>answer ↵</button>
      </div>
    </div>
  );
}

/** The card centred near the top, when the host passage is not on this desk (or after a restart). */
export function CheckCardOverlay({ desk }: { desk: CheckDesk }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const open = desk.open();
  if (!open) return null;
  const veiled = open.veiled;
  const looked = lookedLine(open.looked, open.coldNow);
  return (
    <div className="ovl coldcheck" role="dialog" aria-label="a cold check" data-check-card="overlay" data-check-phase={open.phase}>
      <div className="cch"><span>◇ LearnLoop</span><span className="grow" /><span>{open.phase === "answered" ? "a cold check · answered" : "a cold check"}</span></div>
      <div className="ccq"><FitMath><MarkdownMath value={question(open)} /></FitMath></div>
      <div className="cca">
        {open.phase === "answered" ? (
          <div className="ccf">
            <div className="ccfh">◇ feedback · {open.reply?.cold ? "on your own" : "counts as practice"}</div>
            <div className="gqy"><span className="who">{answeredHead(Boolean(open.reply?.cold))}</span>{open.answer}</div>
            <ReasonLine open={open} />
            {feedback(open) ? <FitMath><MarkdownMath value={feedback(open)} /></FitMath> : null}
            <div className="ccv"><b>{veiled.length} {veiled.length === 1 ? "thing was" : "things were"} hidden while you answered</b>
              {[...new Set(veiled.map((ref) => ref.group))].map((group) => <div key={group}>· {group}</div>)}
              <div className="faint">they are back now</div></div>
            <div className="ccb"><span className="faint" /><button type="button" className="act" onClick={() => desk.close()}>close</button></div>
          </div>
        ) : (
          <>
            <textarea aria-label="your answer" spellCheck={false} value={open.answer} disabled={open.phase !== "open"}
              onChange={(event) => desk.setAnswer(event.target.value)} onKeyDown={answerKeys(desk)} autoFocus />
            <div className="ccv ck-groups">veiled while you answer · {groupsLine(desk.veils()) || "nothing on screen"}</div>
            {looked ? <div className="ck-looked">{looked}</div> : null}
            {open.error ? <div className="ck-note" role="alert">{open.error}</div> : null}
            <div className="ccb">
              <span className="faint">nothing moves · only an on-your-own answer settles this check</span>
              <button type="button" className="act" onClick={() => void desk.abandon()}>not now</button>
              <button type="button" className="act pri" disabled={open.phase !== "open" || !open.answer.trim()} onClick={() => void desk.submit()}>answer ↵</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/** The check's part of a source window's lens: the closed marker before each due check's host passage, or the open
 *  card there. One composed lens per window, made again only when its base or the checks change. */
export class CheckLenses {
  private made = new Map<string, { base: ReaderLens | null; extractionId: string; version: number; lens: ReaderLens | null }>();

  lensFor(windowId: string, extractionId: string, base: ReaderLens | null, desk: CheckDesk, onCheckNow: (commitmentId: string) => void): ReaderLens | null {
    const version = desk.getVersion();
    const known = this.made.get(windowId);
    if (known && known.base === base && known.extractionId === extractionId && known.version === version) return known.lens;
    const lens: ReaderLens = {
      ...(base ?? {}),
      before: (spanId: string) => {
        const own = base?.before?.(spanId) ?? null;
        const open = desk.open();
        const here = Boolean(open && open.host?.extractionId === extractionId && open.host?.spanId === spanId);
        const due = desk.dueAt(extractionId, spanId).filter((check) => check.commitmentId !== open?.card.commitmentId);
        if (!here && !due.length) return own;
        return <>{own}{here ? <CheckCardInline desk={desk} /> : <CheckMarker checks={due} desk={desk} onCheckNow={onCheckNow} />}</>;
      },
    };
    this.made.set(windowId, { base, extractionId, version, lens });
    return lens;
  }
}
