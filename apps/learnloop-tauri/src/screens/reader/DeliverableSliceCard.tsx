// Deliverable curriculum C0b: the Guide's path card shows a deliverable's slice for the
// open book (spec §7.5) when a deliverable's path names it: its core, prerequisite and
// alternate sections here, labelled; "not needed for <deliverable>"; one line per topic
// whose primary is in another book; the learner's overrides (§7.3) and "Am I ready?"
// (§8.5). "this book alone" shows RW7a's own card. With curriculum.enabled off (the RPC
// refuses), the slot is RW7a's card exactly: today's Guide. With no deliverable naming this
// book, RW7a's card and, under it, the way to make a deliverable or review yours (§5;
// Codex review F4). Display only.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "../../api/client";
import type {
  DeliverableLineDto, DeliverablePathChoice, DeliverableReadyDto, DeliverableScopeDto, DeliverableSliceDto, ReadingPathDepth,
} from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill } from "../../components/term";
import { errorMessage, getCommandError } from "../../errors";
import {
  DELIVERABLE_COPY as COPY,
  DELIVERABLE_POLL_MS,
  offeredChoices,
  sectionMarker,
  sectionRef,
  shouldPollSlice,
  sliceHeading,
  sliceShown,
} from "./deliverableSlice";
import { DeliverableEntry, DeliverableScopePanel, scopeNotice } from "./DeliverableScope";
import { MeaningLabel } from "./voices";

const LINK = {
  background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer",
  fontFamily: FONT_MONO, fontSize: 10, textDecoration: "underline",
} as const;
const QUIET_CODES = new Set(["curriculum_disabled", "reader_disabled"]);
const NONE: DeliverableSliceDto = { extractionId: "", status: "none" };

export interface GuidePathSlotProps {
  extractionId: string;
  /** RW7a's card for this book (null when reading_paths is off). */
  readingPathCard: ReactNode | null;
  onJump: (spanId: string) => void;
  onError: (message: string) => void;
  /** What the path depends on, as the Reader sees it: a change reads the slice again. */
  refreshKey?: string;
}

/** The Guide's path slot: the deliverable's slice when one names this book, else RW7a's card. */
export function GuidePathSlot({ extractionId, readingPathCard, onJump, onError, refreshKey = "" }: GuidePathSlotProps) {
  const [slice, setSlice] = useState<DeliverableSliceDto | null>(null);
  const [alone, setAlone] = useState(false);
  const [refused, setRefused] = useState(false);
  const shown = useRef(extractionId);

  const read = useCallback(async (params: { retry?: boolean; judge?: boolean } = {}) => {
    const asked = extractionId;
    try {
      const result = await api.curriculumGuideSlice({ extractionId: asked, ...params });
      if (shown.current === asked) { setSlice(result); setRefused(false); }
    } catch (error) {
      if (shown.current !== asked) return;
      setSlice({ ...NONE, extractionId: asked });
      setRefused(true);
      // The switch off (or the Reader off) is today's Guide, silently; any other refusal
      // is reported, and the card stays RW7a's.
      const code = getCommandError(error)?.code;
      if (code && !QUIET_CODES.has(code)) onError(errorMessage(error, "Couldn't load your deliverable's path."));
    }
  }, [extractionId, onError]);

  useEffect(() => {
    shown.current = extractionId;
    setSlice(null);
    setAlone(false);
    void read();
  }, [extractionId, read]);

  useEffect(() => {
    if (!shouldPollSlice(slice)) return undefined;
    const timer = window.setTimeout(() => void read(), DELIVERABLE_POLL_MS);
    return () => window.clearTimeout(timer);
  }, [slice, read]);

  const refreshedFor = useRef(refreshKey);
  useEffect(() => {
    if (refreshedFor.current === refreshKey) return undefined;
    refreshedFor.current = refreshKey;
    const timer = window.setTimeout(() => void read(), DELIVERABLE_POLL_MS);
    return () => window.clearTimeout(timer);
  }, [refreshKey, read]);

  if (slice === null) return null;
  if (!sliceShown(slice)) {
    // Refused (the switch off): RW7a's card exactly. Otherwise RW7a's card, then the way to
    // make a deliverable or review yours (Codex review F4).
    if (refused) return <>{readingPathCard}</>;
    return (
      <>
        {readingPathCard}
        <DeliverableEntry onError={onError} onChanged={() => void read()} />
      </>
    );
  }
  if (alone && readingPathCard) {
    return (
      <div data-deliverable-slice="alone">
        <button type="button" style={{ ...LINK, marginBottom: 4 }} onClick={() => setAlone(false)}>{COPY.backToDeliverable}</button>
        {readingPathCard}
      </div>
    );
  }
  // Keyed by the deliverable (Codex re-review F17): when a correction makes the Guide pick
  // another deliverable for this book, the card starts fresh, so an open scope panel never
  // edits the previous one and its late answers land nowhere.
  return (
    <DeliverableSliceCard
      key={slice.goal?.id ?? ""}
      slice={slice}
      onJump={onJump}
      onError={onError}
      onReload={(params) => read(params)}
      onAlone={readingPathCard ? () => setAlone(true) : null}
    />
  );
}

export interface DeliverableSliceCardProps {
  slice: DeliverableSliceDto;
  onJump: (spanId: string) => void;
  onError: (message: string) => void;
  onReload: (params?: { retry?: boolean; judge?: boolean }) => Promise<void> | void;
  /** "this book alone": RW7a's own card (null when it is off). */
  onAlone: (() => void) | null;
}

export function DeliverableSliceCard({ slice, onJump, onError, onReload, onAlone }: DeliverableSliceCardProps) {
  const [busy, setBusy] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [notNeededOpen, setNotNeededOpen] = useState(false);
  const [ready, setReady] = useState<DeliverableReadyDto | null>(null);
  const [scope, setScope] = useState<DeliverableScopeDto | null>(null);
  const [scopeOpen, setScopeOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const goalId = slice.goal?.id ?? "";

  const act = async (work: () => Promise<unknown>, failure: string, reload: { judge: boolean } = { judge: false }) => {
    setBusy(true);
    try {
      await work();
      await onReload(reload);
    } catch (error) {
      onError(errorMessage(error, failure));
    } finally {
      setBusy(false);
    }
  };

  const toggleScope = async () => {
    if (scopeOpen) { setScopeOpen(false); return; }
    try {
      setScope(await api.curriculumScope({ goalId }));
      setScopeOpen(true);
    } catch (error) {
      onError(errorMessage(error, "Couldn't load what this deliverable covers."));
    }
  };

  // A scope change asks for the judgment it owes (Codex review F9): the slice reads with
  // judge on, so a topic added since is placed and polled until its path is current.
  const scopeChanged = (next: DeliverableScopeDto) => {
    setScope(next);
    void onReload({ judge: true });
  };

  const chooseDepth = (depth: ReadingPathDepth) => act(async () => {
    await api.curriculumSetDepth({ goalId, depth });
    setChoosing(false);
    await onReload();
  }, "Couldn't save how deep you want to go.");

  const choose = (line: DeliverableLineDto, choice: DeliverablePathChoice, ref?: string) => act(
    () => api.curriculumPathOverride({ goalId, learningObjectId: line.learningObjectId, choice, ...(ref ? { sectionRef: ref } : {}) }),
    "Couldn't save that choice.");

  const notWhatINeed = (line: DeliverableLineDto, text: string) => act(async () => {
    const out = await api.curriculumSetScope({ goalId, kind: "correction", text,
      context: { via: "path_line", learning_object_id: line.learningObjectId } });
    // Superseded or unavailable: its message, read by the learner (never a silent no-op).
    setNotice(scopeNotice(out));
    // Words that match no topic yet wait for the learner's add it / no: the scope opens on them.
    if (scopeOpen || (out.scope?.unmatched ?? []).some((entry) => entry.status === "open")) {
      setScope(out.scope);
      setScopeOpen(true);
    }
  }, "Couldn't send that.", { judge: true });

  const amIReady = async () => {
    setBusy(true);
    try {
      const out = await api.curriculumReadyCheck({ goalId });
      setReady(out.readiness);
    } catch (error) {
      onError(errorMessage(error, "Couldn't check how ready you are."));
    } finally {
      setBusy(false);
    }
  };

  if (slice.status === "withheld") {
    return (
      <div data-deliverable-slice="withheld">
        <Card style={{ marginBottom: 10 }}><Faint style={{ fontSize: 10 }}>{slice.message}</Faint></Card>
      </div>
    );
  }
  const askDepth = slice.status === "ask_depth" || choosing;
  const lines = slice.lines ?? [];
  const notNeeded = slice.notNeeded ?? [];
  return (
    <div data-deliverable-slice={slice.status}>
      <Card style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 10, background: COLOR.washCyan }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>{COPY.heading}</Faint>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>{sliceHeading(slice)}</span>
          {slice.depth && !askDepth ? <button type="button" style={LINK} onClick={() => setChoosing(true)}>{COPY.change}</button> : null}
          {goalId ? (
            <button type="button" style={LINK} aria-expanded={scopeOpen} onClick={() => void toggleScope()}>
              {COPY.scope} {scopeOpen ? "▾" : "▸"}
            </button>
          ) : null}
          {onAlone ? <button type="button" style={LINK} onClick={onAlone}>{COPY.thisBookAlone}</button> : null}
        </div>
        {scopeOpen && scope ? <DeliverableScopePanel scope={scope} onError={onError} onChanged={scopeChanged} /> : null}
        {notice ? <Faint style={{ fontSize: 10 }}>{notice}</Faint> : null}
        {askDepth ? (
          <div role="group" aria-label={COPY.ask} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{COPY.ask}</span>
            {(slice.depths ?? []).map((depth) => (
              <button key={depth.id} type="button" disabled={busy} aria-pressed={slice.depth === depth.id}
                onClick={() => void chooseDepth(depth.id)}
                style={{ ...LINK, fontSize: 11, textAlign: "left", textDecoration: slice.depth === depth.id ? "underline" : "none" }}>
                {depth.label} <span style={{ color: COLOR.textDim }}>· {depth.means}</span>
              </button>
            ))}
            <Faint style={{ fontSize: 10 }}>{COPY.askNote}</Faint>
          </div>
        ) : (
          <>
            {slice.covering ? <Faint style={{ fontSize: 10 }}>{COPY.covering}</Faint> : null}
            {!slice.covering && (slice.status === "judging" || slice.status === "pending") ? (
              <Faint style={{ fontSize: 10 }}>{lines.length ? COPY.updating : COPY.judging}</Faint>
            ) : null}
            {slice.status === "failed" ? (
              <Faint style={{ fontSize: 10 }}>
                {slice.message}{" "}
                {["capped", "models_off", "unrouted", "unpriced"].includes(slice.reason ?? "") ? null : (
                  <button type="button" style={LINK} onClick={() => void onReload({ retry: true })}>{COPY.tryAgain}</button>
                )}
              </Faint>
            ) : null}
            {lines.map((line) => (
              <LineRow key={`${line.learningObjectId}:${line.section.sectionId}`} line={line} busy={busy}
                open={open === line.learningObjectId}
                onToggle={() => setOpen((current) => (current === line.learningObjectId ? null : line.learningObjectId))}
                onJump={() => onJump(line.section.startSpanId)}
                onChoose={(choice, ref) => void choose(line, choice, ref)}
                onNotWhatINeed={(text) => void notWhatINeed(line, text)} />
            ))}
            {(slice.elsewhere ?? []).map((entry) => (
              <span key={`else:${entry.learningObjectId}`} data-deliverable-elsewhere={entry.learningObjectId}
                style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
                {COPY.onPathIn(entry.title, entry.section.book, sectionMarker(entry.section.title))}
              </span>
            ))}
            {(slice.uncovered ?? []).length ? (
              <span data-deliverable-uncovered="" style={{ fontSize: 10, color: COLOR.textFaint }}>
                {COPY.notInBooks} {(slice.uncovered ?? []).map((entry) => entry.title).join(", ")}
              </span>
            ) : null}
            {notNeeded.length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <button type="button" style={{ ...LINK, textAlign: "left" }} aria-expanded={notNeededOpen}
                  onClick={() => setNotNeededOpen((value) => !value)}>
                  {COPY.notNeededToggle(notNeeded.length)} {notNeededOpen ? "▾" : "▸"}
                </button>
                {notNeededOpen ? notNeeded.map((entry) => (
                  <span key={entry.sectionId} data-deliverable-not-needed={entry.sectionId} style={{ display: "flex", gap: 6 }}>
                    <button type="button" onClick={() => onJump(entry.startSpanId)}
                      style={{ background: "none", border: "none", padding: 0, cursor: "pointer", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10, textAlign: "left" }}>
                      {entry.title}
                    </button>
                    <MeaningLabel>{slice.notNeededLabel}</MeaningLabel>
                  </span>
                )) : null}
              </div>
            ) : null}
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <button type="button" style={{ ...LINK, fontSize: 11, textAlign: "left" }} disabled={busy || !goalId}
                onClick={() => void amIReady()}>{COPY.ready}</button>
              {ready ? <ReadyLines ready={ready} /> : null}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

function LineRow({ line, busy, open, onToggle, onJump, onChoose, onNotWhatINeed }: {
  line: DeliverableLineDto;
  busy: boolean;
  open: boolean;
  onToggle: () => void;
  onJump: () => void;
  onChoose: (choice: DeliverablePathChoice, ref?: string) => void;
  onNotWhatINeed: (text: string) => void;
}) {
  const [text, setText] = useState("");
  const offered = offeredChoices(line);
  const onPath = line.effectiveLabel === "core" || line.effectiveLabel === "prerequisite";
  const crossed = line.effectiveLabel === "skipped" || line.effectiveLabel === "check_pending";
  return (
    <div data-deliverable-line={line.learningObjectId} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <Pill color={onPath ? "cyan" : "slate"} style={{ fontSize: 10 }}>{line.chip}</Pill>
        <button type="button" onClick={onJump}
          style={{ background: "none", border: "none", padding: 0, cursor: "pointer", color: COLOR.text, fontFamily: FONT_MONO, fontSize: 11, textAlign: "left", textDecoration: crossed ? "line-through" : "none" }}>
          {sectionMarker(line.section.title)}
        </button>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>· {line.title}</span>
        <button type="button" style={LINK} aria-expanded={open} onClick={onToggle}>{COPY.why} {open ? "▾" : "▸"}</button>
      </div>
      {line.elsewhere ? (
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim, paddingLeft: 8 }}>
          {COPY.onPathIn(line.title, line.elsewhere.book, sectionMarker(line.elsewhere.title))}
        </span>
      ) : null}
      {open ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 3, paddingLeft: 8, borderLeft: line.reasonBy === "model" ? `1px dotted ${COLOR.purplePill}` : `1px solid ${COLOR.borderStrong}` }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }}>{line.reasonBy === "model" ? "◇ " : ""}{line.reason}</span>
          {line.reasonBy === "model" ? <MeaningLabel>{COPY.modelsReading}</MeaningLabel> : null}
          {line.alternates.map((alternate) => (
            <span key={sectionRef(alternate)} data-deliverable-alternate={sectionRef(alternate)} style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
                {COPY.anotherWay} {alternate.book} {sectionMarker(alternate.title)}{alternate.difference ? `, ${alternate.difference}` : ""}
              </span>
              {alternate.canUseInstead === false ? null : (
                <button type="button" style={LINK} disabled={busy} onClick={() => onChoose("use_instead", sectionRef(alternate))}>{COPY.useInstead}</button>
              )}
            </span>
          ))}
          <span style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {line.override ? (
              <>
                <MeaningLabel>
                  {line.override === "skip" ? COPY.skipping : line.override === "check_later" ? COPY.checkWaiting
                    : line.override === "use_instead" ? COPY.usingInstead : COPY.readingAnyway}
                </MeaningLabel>
                <button type="button" style={LINK} disabled={busy} onClick={() => onChoose("none")}>{COPY.undo}</button>
              </>
            ) : offered.map((choice) => (
              <button key={choice} type="button" style={LINK} disabled={busy} onClick={() => onChoose(choice)}>
                {choice === "skip" ? COPY.skip : choice === "check_later" ? COPY.checkLater : COPY.readAnyway}
              </button>
            ))}
          </span>
          <form style={{ display: "flex", gap: 6 }} onSubmit={(event) => {
            event.preventDefault();
            if (text.trim()) { onNotWhatINeed(text.trim()); setText(""); }
          }}>
            <input aria-label={COPY.notWhatINeed} placeholder={COPY.notWhatINeedPlaceholder} value={text}
              onChange={(event) => setText(event.target.value)}
              style={{ flex: 1, fontFamily: FONT_MONO, fontSize: 10, background: "transparent", color: COLOR.text, border: `1px solid ${COLOR.borderStrong}` }} />
            <button type="submit" style={LINK} disabled={busy || !text.trim()}>{COPY.send}</button>
          </form>
        </div>
      ) : null}
    </div>
  );
}

function ReadyLines({ ready }: { ready: DeliverableReadyDto }) {
  return (
    <div data-deliverable-ready="" style={{ display: "flex", flexDirection: "column", gap: 2, paddingLeft: 8 }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }}>{ready.summary}</span>
      {ready.lines.map((line) => (
        <span key={line.learningObjectId} data-deliverable-ready-line={line.state}
          style={{ fontFamily: FONT_MONO, fontSize: 10, color: line.state === "demonstrated" ? COLOR.text : COLOR.textDim }}>
          {line.title}: {line.line}
          {line.checks.length ? ` · check on ${line.checks.map((check) => check.dueHint ?? "soon").join(", ")}` : ""}
        </span>
      ))}
      <Faint style={{ fontSize: 10 }}>{COPY.readyNote}</Faint>
    </div>
  );
}
