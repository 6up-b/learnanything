// Reader workbench RW7a: the Guide's "your path" card (spec §10.1; UX §4.11,
// Moment 0, W1). Shown only while the prompt contract carries readingPaths;
// absent, the Guide is today's (the goal card). Display only.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReadingPathChoice, ReadingPathDepth, ReadingPathDto, ReadingPathExerciseDto, ReadingPathSectionDto } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill } from "../../components/term";
import { errorMessage } from "../../errors";
import {
  READING_PATH_COPY as COPY,
  READING_PATH_POLL_MS,
  READING_PATH_REFRESH_MS,
  depthSourceLine,
  exercisesWorthTrying,
  offeredChoice,
  pathHeading,
  reasonIsModels,
  shouldPoll,
} from "./readingPath";
import { MeaningLabel } from "./voices";

const LINK = {
  background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer",
  fontFamily: FONT_MONO, fontSize: 10, textDecoration: "underline",
} as const;

export interface ReadingPathCardProps {
  extractionId: string;
  /** Moves the page to a section (ordinary reading navigation). */
  onJump: (spanId: string) => void;
  /** "Try it": the exercise in the workbench through the usual import, the
   *  book open; null when the workbench is off (the book is offered instead). */
  onTryExercise: ((exercise: ReadingPathExerciseDto) => void) | null;
  onError: (message: string) => void;
  /** Bumped by Orient's "what matters here?": the card scrolls into view. */
  focusToken?: number;
  /** What the path depends on, as the Reader sees it (readingPathRefreshKey):
   *  when it changes the mounted card reads the path again (Codex review F3). */
  refreshKey?: string;
}

export function ReadingPathCard({ extractionId, onJump, onTryExercise, onError, focusToken = 0, refreshKey = "" }: ReadingPathCardProps) {
  const [path, setPath] = useState<ReadingPathDto | null>(null);
  const [choosing, setChoosing] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const shown = useRef(extractionId);
  const cardRef = useRef<HTMLDivElement | null>(null);

  const read = useCallback(async (params: { retry?: boolean } = {}) => {
    const asked = extractionId;
    try {
      const result = await api.readerReadingPath({ extractionId: asked, ...params });
      if (shown.current === asked) setPath(result);
    } catch (error) {
      if (shown.current === asked) onError(errorMessage(error, "Couldn't load your reading path."));
    }
  }, [extractionId, onError]);

  useEffect(() => {
    shown.current = extractionId;
    setPath(null);
    setChoosing(false);
    setOpen(null);
    void read();
  }, [extractionId, read]);

  // A judgment runs in the background: read the path again, paced, until it lands.
  useEffect(() => {
    if (!shouldPoll(path)) return undefined;
    const timer = window.setTimeout(() => void read(), READING_PATH_POLL_MS);
    return () => window.clearTimeout(timer);
  }, [path, read]);

  useEffect(() => {
    if (focusToken > 0) cardRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [focusToken]);

  // The learner read on, answered or came back to the Guide while the card
  // stayed mounted: read the path again (the server rejudges only when its
  // state changed; "next" follows progress at once). Paced, so the Reader's
  // progress save lands first and a burst of changes is one read.
  const refreshedFor = useRef(refreshKey);
  useEffect(() => {
    if (refreshedFor.current === refreshKey) return undefined;
    refreshedFor.current = refreshKey;
    const timer = window.setTimeout(() => void read(), READING_PATH_REFRESH_MS);
    return () => window.clearTimeout(timer);
  }, [refreshKey, read]);

  const chooseDepth = async (depth: ReadingPathDepth) => {
    setBusy(true);
    try {
      const result = await api.readerReadingPathSetDepth({ extractionId, depth });
      if (shown.current === extractionId) {
        setPath(result);
        setChoosing(false);
      }
    } catch (error) {
      onError(errorMessage(error, "Couldn't save how deep you want to go."));
    } finally {
      setBusy(false);
    }
  };

  const choose = async (section: ReadingPathSectionDto, choice: ReadingPathChoice) => {
    if (!path?.depth) return;
    setBusy(true);
    try {
      const result = await api.readerReadingPathOverride({ extractionId, depth: path.depth, sectionId: section.sectionId, choice });
      if (shown.current === extractionId) setPath(result);
    } catch (error) {
      onError(errorMessage(error, "Couldn't save that choice."));
    } finally {
      setBusy(false);
    }
  };

  if (path === null || path.status === "no_sections") return null;
  if (path.status === "withheld") {
    return (
      <div data-reading-path="withheld">
        <Card style={{ marginBottom: 10 }}>
          <Faint style={{ fontSize: 10 }}>{path.message}</Faint>
        </Card>
      </div>
    );
  }

  const askDepth = path.status === "ask_depth" || choosing;
  const exercises = exercisesWorthTrying(path);
  return (
    <div ref={cardRef} data-reading-path={path.status}>
      <Card style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 10, background: COLOR.washCyan }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>{COPY.heading}</Faint>
          {path.depth && !askDepth ? (
            <>
              <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>{pathHeading(path)}</span>
              <button type="button" style={LINK} onClick={() => setChoosing(true)}>{COPY.change}</button>
            </>
          ) : null}
        </div>
        {askDepth ? (
          <div role="group" aria-label={COPY.ask} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{COPY.ask}</span>
            {path.depths.map((depth) => (
              <button
                key={depth.id}
                type="button"
                disabled={busy}
                aria-pressed={path.depth === depth.id}
                onClick={() => void chooseDepth(depth.id)}
                style={{ ...LINK, fontSize: 11, textAlign: "left", textDecoration: path.depth === depth.id ? "underline" : "none" }}
              >
                {depth.label} <span style={{ color: COLOR.textDim }}>· {depth.means}</span>
              </button>
            ))}
            <Faint style={{ fontSize: 10 }}>{COPY.askNote}</Faint>
          </div>
        ) : (
          <>
            {depthSourceLine(path) ? <MeaningLabel>{depthSourceLine(path)}</MeaningLabel> : null}
            {path.goalLine ? <Faint style={{ fontSize: 10 }}>{path.goalLine}</Faint> : null}
            {path.next ? (
              <span data-reading-path-next="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                {path.next.text}
              </span>
            ) : null}
            {path.status === "judging" || path.status === "pending" ? (
              <Faint style={{ fontSize: 10 }}>{path.sections.length ? COPY.updating : COPY.judging}</Faint>
            ) : null}
            {path.status === "failed" ? (
              <Faint style={{ fontSize: 10 }}>
                {path.message}{" "}
                {path.reason === "capped" || path.reason === "models_off" || path.reason === "unrouted" || path.reason === "unpriced" ? null : (
                  <button type="button" style={LINK} onClick={() => void read({ retry: true })}>{COPY.tryAgain}</button>
                )}
              </Faint>
            ) : null}
            {path.sections.map((section) => (
              <SectionRow
                key={section.sectionId}
                section={section}
                open={open === section.sectionId}
                busy={busy}
                onToggle={() => setOpen((current) => (current === section.sectionId ? null : section.sectionId))}
                onJump={() => onJump(section.startSpanId)}
                onChoose={(choice) => void choose(section, choice)}
              />
            ))}
            {exercises.length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Faint style={{ fontSize: 10 }}>{COPY.exercise}</Faint>
                {exercises.map((section) => (
                  <span key={section.sectionId} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                    {section.exercise!.label}{" "}
                    {onTryExercise ? (
                      <button type="button" style={LINK} onClick={() => onTryExercise(section.exercise!)}>{COPY.tryIt}</button>
                    ) : (
                      <button type="button" style={LINK} onClick={() => onJump(section.exercise!.spanIds[0] ?? section.startSpanId)}>
                        {COPY.openInBook}
                      </button>
                    )}
                  </span>
                ))}
              </div>
            ) : null}
          </>
        )}
      </Card>
    </div>
  );
}

function SectionRow({
  section, open, busy, onToggle, onJump, onChoose,
}: {
  section: ReadingPathSectionDto;
  open: boolean;
  busy: boolean;
  onToggle: () => void;
  onJump: () => void;
  onChoose: (choice: ReadingPathChoice) => void;
}) {
  const offered = offeredChoice(section);
  return (
    <div data-reading-path-section={section.sectionId} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <Pill color={section.effectiveLabel === "core" || section.effectiveLabel === "prerequisite" ? "cyan" : "slate"} style={{ fontSize: 10 }}>
          {section.chip}
        </Pill>
        <button
          type="button"
          onClick={onJump}
          style={{ background: "none", border: "none", padding: 0, cursor: "pointer", color: COLOR.text, fontFamily: FONT_MONO, fontSize: 11, textAlign: "left", textDecoration: section.effectiveLabel === "skipped" ? "line-through" : "none" }}
        >
          {section.title}
        </button>
        <button type="button" style={LINK} aria-expanded={open} onClick={onToggle}>{COPY.why} {open ? "▾" : "▸"}</button>
      </div>
      {open ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 2, paddingLeft: 8, borderLeft: reasonIsModels(section) ? `1px dotted ${COLOR.purplePill}` : `1px solid ${COLOR.borderStrong}` }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }}>
            {reasonIsModels(section) ? "◇ " : ""}{section.reason}
          </span>
          {reasonIsModels(section) ? <MeaningLabel>{COPY.modelsReading}</MeaningLabel> : null}
          <span style={{ display: "flex", gap: 8 }}>
            {section.override ? (
              <>
                <MeaningLabel>{section.override === "skip" ? COPY.skipping : COPY.readingAnyway}</MeaningLabel>
                <button type="button" style={LINK} disabled={busy} onClick={() => onChoose("none")}>{COPY.undo}</button>
              </>
            ) : offered ? (
              <button type="button" style={LINK} disabled={busy} onClick={() => onChoose(offered)}>
                {offered === "skip" ? COPY.skip : COPY.readAnyway}
              </button>
            ) : null}
          </span>
        </div>
      ) : null}
    </div>
  );
}
