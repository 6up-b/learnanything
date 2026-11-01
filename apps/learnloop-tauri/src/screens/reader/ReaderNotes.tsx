// Curriculum C2 (spec §10.2, §10.3; UX §3.4's third voice): the learner's own notes,
// linked to the passages and topics they discuss, always in the learner's voice (›):
//
// * NoteMark: › in the margin beside a passage with a linked note (the learner's own
//   mark, like ⇄: outside the cue budget, never counted by the density setting).
//   Pressing it opens the note(s) under the passage; Esc or *close* folds them.
// * PathLineNotes: "your note from 3 Oct" on a deliverable path line.
// * NotesTakeBand: Compare's *your take* band lists the notes linked to the compared
//   passages, each with *use as my take* (RW4d's own take, quoting the note).
// * NoteLinkPicker: *link one of your notes…* from the Reader's passage menu: tend's
//   notes for the passage's section, or a words-only search of the learner's own words.
//
// A model's link says "linked by LearnLoop's model"; one tap hides it (*hide*), and it
// stays hidden. Keeping it needs no tap. A Pocket Notes page says "handwritten ·
// transcribed by Pocket Notes". A note is never a source, never evidence and never
// grades anything. Nothing here opens, moves focus or animates unasked.
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../../api/client";
import type { NoteHitDto, NoteLinkDto, NoteMarksDto, NotesContractDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { useNotes, type NotesContextValue } from "./notesContext";
import { LearnerVoice, MeaningLabel } from "./voices";

export const NOTES_COPY = {
  fromYourNotes: "from your notes",
  yourNote: "your note",
  hide: "hide",
  hidden: "hidden · it stays hidden",
  undo: "undo",
  close: "close",
  useAsMyTake: "use as my take",
  linkNote: "link one of your notes…",
  linkHere: "link it here",
  linked: "linked",
  searchPlaceholder: "search your notes (words only)",
  searching: "looking in your notes…",
  nothingFound: "Nothing in your notes matched.",
  forSection: "your notes for this section",
  whereThisGoes: "ⓘ where this goes",
  whereLine: "Your note is shown beside the book in your own words. It is never a source, never used to write questions and never grades you.",
  truncated: "(shortened)",
} as const;

const linkStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
} as const;
const quietStyle = { ...linkStyle, color: COLOR.textDim } as const;
const headStyle = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.06em", color: COLOR.textDim, textTransform: "uppercase" as const };

/** "your note · Linear algebra › Eigen stuff · 3 Oct" */
export function noteLabel(link: NoteLinkDto): string {
  const where = [link.note.title, link.note.heading].filter(Boolean).join(" › ");
  return [NOTES_COPY.yourNote, where, link.note.dateLabel].filter(Boolean).join(" · ");
}

/** Hide one link (one tap), with undo; the server keeps the learner's word across re-judgments. */
function useDecide(onChanged: (() => void) | undefined) {
  const [hidden, setHidden] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<string | null>(null);
  const decide = async (link: NoteLinkDto, choice: "hide" | "keep") => {
    setFailure(null);
    try {
      if (choice === "hide") {
        const out = await api.notesDecide({ linkId: link.linkId, choice: "hide" });
        setHidden((current) => ({ ...current, [link.linkId]: out.linkId }));
      } else {
        const hiddenId = hidden[link.linkId];
        if (!hiddenId) return;
        await api.notesDecide({ linkId: hiddenId, choice: "keep" });
        setHidden((current) => {
          const next = { ...current };
          delete next[link.linkId];
          return next;
        });
      }
      onChanged?.();
    } catch (error) {
      setFailure(errorMessage(error, "Couldn't save that; nothing changed."));
    }
  };
  return { hidden, failure, decide };
}

/** One linked note, in the learner's voice. */
export function NoteCard({ link, isHidden, onHide, onUndo, extra }: {
  link: NoteLinkDto;
  isHidden?: boolean;
  onHide?: () => void;
  onUndo?: () => void;
  extra?: ReactNode;
}) {
  if (isHidden) {
    return (
      <span data-note-hidden={link.linkId} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <MeaningLabel>{NOTES_COPY.hidden}</MeaningLabel>
        {onUndo ? <button type="button" style={linkStyle} onClick={onUndo}>{NOTES_COPY.undo}</button> : null}
      </span>
    );
  }
  return (
    <div data-note-link={link.linkId} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <LearnerVoice label={noteLabel(link)}>
        <span style={{ whiteSpace: "pre-wrap" }}>{link.note.text}</span>
        {link.note.truncated ? <span style={{ color: COLOR.textDim }}> {NOTES_COPY.truncated}</span> : null}
      </LearnerVoice>
      <span style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap", paddingLeft: 10 }}>
        {link.note.originLabel ? <MeaningLabel>{link.note.originLabel}</MeaningLabel> : null}
        <MeaningLabel>{link.byLabel}</MeaningLabel>
        {link.howLine ? <MeaningLabel><span aria-hidden="true">◇ </span>{link.howLine}</MeaningLabel> : null}
        {onHide ? <button type="button" style={quietStyle} onClick={onHide}>{NOTES_COPY.hide}</button> : null}
        {extra}
      </span>
    </div>
  );
}

function NoteList({ links, ctx }: { links: NoteLinkDto[]; ctx: NotesContextValue | null }) {
  const { hidden, failure, decide } = useDecide(ctx?.onChanged);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {links.map((link) => (
        <NoteCard key={link.linkId} link={link} isHidden={Boolean(hidden[link.linkId])}
          onHide={() => void decide(link, "hide")} onUndo={() => void decide(link, "keep")} />
      ))}
      {failure ? <span role="status"><MeaningLabel>{failure}</MeaningLabel></span> : null}
    </div>
  );
}

// ── the › margin mark ──────────────────────────────────────────────────────

export type NoteMark = NoteMarksDto["marks"][number];

export function NoteMarkButton({ mark, surface = "text", below = false }: { mark: NoteMark; surface?: "text" | "pdf"; below?: boolean }) {
  const ctx = useNotes();
  const [open, setOpen] = useState(false);
  const onPage = surface === "pdf";
  const count = mark.notes.length;
  const label = count > 1 ? `${count} of your notes on this passage: ${open ? "close them" : "open them"}`
    : `your note${mark.notes[0]?.note.dateLabel ? ` from ${mark.notes[0].note.dateLabel}` : ""}: ${open ? "close it" : "open it"}`;
  const body = open ? (
    <div data-note-mark-panel={mark.spanId} onClick={(event) => event.stopPropagation()}
      style={onPage
        ? { position: "absolute", left: 24, top: 0, width: 480, maxHeight: "60vh", overflowY: "auto", zIndex: 30, background: COLOR.bg, border: `1px solid ${COLOR.border}`, padding: "4px 8px" }
        : { margin: "4px 0 8px", display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <span style={headStyle}><span aria-hidden="true">› </span>{NOTES_COPY.fromYourNotes}</span>
        <span style={{ flex: 1 }} />
        <button type="button" style={quietStyle} onClick={() => setOpen(false)}>{NOTES_COPY.close}</button>
      </span>
      <NoteList links={mark.notes} ctx={ctx} />
    </div>
  ) : null;
  const button = (
    <button type="button" data-note-mark={mark.spanId} aria-expanded={open} aria-label={label}
      title={count > 1 ? `${count} of your notes` : NOTES_COPY.yourNote}
      onClick={(event) => { event.stopPropagation(); setOpen((value) => !value); }}
      onKeyDown={(event) => { if (event.key === "Escape" && open) { event.stopPropagation(); setOpen(false); } }}
      style={onPage
        ? { width: 20, height: 20, padding: 0, border: `1px solid ${COLOR.border}`, background: COLOR.bg, color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12, lineHeight: "18px", cursor: "pointer" }
        : { position: "absolute", left: -22, top: 36, border: 0, background: "transparent", color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 13, padding: 0, cursor: "pointer" }}>
      ›
    </button>
  );
  if (onPage) {
    return (
      <span data-note-slot={mark.spanId} style={{ position: "absolute", left: 0, top: below ? 44 : 0, zIndex: open ? 30 : 4 }}
        onMouseDown={(event) => event.stopPropagation()} onMouseUp={(event) => event.stopPropagation()}>
        {button}
        {body}
      </span>
    );
  }
  return (<>{button}{body}</>);
}

const NO_MARKS: ReadonlyMap<string, NoteMark> = new Map();

/** The › marks of the open reading (off: none, nothing read). */
export function useNoteMarks({ settings, extractionId, offline }: {
  settings: NotesContractDto | null | undefined;
  extractionId: string | null;
  offline: boolean;
}) {
  const enabled = Boolean(settings?.enabled);
  const [marks, setMarks] = useState<ReadonlyMap<string, NoteMark>>(NO_MARKS);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!enabled || !extractionId || offline) {
      setMarks(NO_MARKS);
      return;
    }
    let cancelled = false;
    void api.notesMarks({ extractionId })
      .then((result) => { if (!cancelled) setMarks(new Map(result.marks.map((mark) => [mark.spanId, mark] as const))); })
      // Marks are a convenience: an unreadable list shows none, quietly.
      .catch(() => { if (!cancelled) setMarks(NO_MARKS); });
    return () => { cancelled = true; };
  }, [enabled, extractionId, offline, revision]);
  const onChanged = useCallback(() => setRevision((value) => value + 1), []);
  const settingsKey = settings ? JSON.stringify(settings) : "";
  const context = useMemo<NotesContextValue | null>(
    // eslint-disable-next-line react-hooks/exhaustive-deps
    () => (settings?.enabled ? { settings, onChanged, revision } : null), [settingsKey, onChanged, revision],
  );
  return { enabled, marks, context };
}

// ── "your note from 3 Oct" on a path line ─────────────────────────────────

export function PathLineNotes({ notes }: { notes: NoteLinkDto[] }) {
  const ctx = useNotes();
  const [open, setOpen] = useState(false);
  if (!notes.length) return null;
  const first = notes[0];
  return (
    <div data-path-line-notes="" style={{ display: "flex", flexDirection: "column", gap: 3, paddingLeft: 8 }}>
      <button type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}
        style={{ ...linkStyle, color: COLOR.textDim, textDecoration: "none", textAlign: "left" }}>
        <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>
        {first.line}{notes.length > 1 ? ` (+${notes.length - 1})` : ""} {open ? "▾" : "▸"}
      </button>
      {open ? <NoteList links={notes} ctx={ctx} /> : null}
    </div>
  );
}

/** The notes of one deliverable's path, by topic (and the background linking started once a day). */
export function usePathNotes(goalId: string | null, ready: boolean) {
  const ctx = useNotes();
  const [byLo, setByLo] = useState<ReadonlyMap<string, NoteLinkDto[]>>(new Map());
  const enabled = Boolean(ctx?.settings.enabled) && Boolean(goalId) && ready;
  const revision = ctx?.revision ?? 0;
  useEffect(() => {
    if (!enabled || !goalId) { setByLo(new Map()); return undefined; }
    let cancelled = false;
    void api.notesPath({ goalId })
      .then((out) => { if (!cancelled) setByLo(new Map(out.lines.map((line) => [line.learningObjectId, line.notes] as const))); })
      // Notes are a convenience on the path: unreadable, none show.
      .catch(() => { if (!cancelled) setByLo(new Map()); });
    return () => { cancelled = true; };
  }, [enabled, goalId, revision]);
  return byLo;
}

// ── Compare's your-take band ───────────────────────────────────────────────

/** The compared passages, from a table's row keys ("<extraction>:<span>"). */
export function passagesOfKeys(keys: string[]): Array<{ extractionId: string; spanId: string }> {
  const out: Array<{ extractionId: string; spanId: string }> = [];
  for (const key of keys) {
    const at = key.indexOf(":");
    if (at > 0 && at < key.length - 1) out.push({ extractionId: key.slice(0, at), spanId: key.slice(at + 1) });
  }
  return out;
}

export function NotesTakeBand({ keys, onUse, busy = false }: { keys: string[]; onUse: (text: string) => void; busy?: boolean }) {
  const ctx = useNotes();
  const [notes, setNotes] = useState<NoteLinkDto[]>([]);
  const [used, setUsed] = useState<string[]>([]);
  const passages = useMemo(() => passagesOfKeys(keys), [keys.join("|")]); // eslint-disable-line react-hooks/exhaustive-deps
  const enabled = Boolean(ctx?.settings.enabled) && passages.length > 0;
  const revision = ctx?.revision ?? 0;
  useEffect(() => {
    if (!enabled) { setNotes([]); return undefined; }
    let cancelled = false;
    void api.notesPassages({ passages })
      .then((out) => { if (!cancelled) setNotes(out.notes); })
      .catch(() => { if (!cancelled) setNotes([]); });
    return () => { cancelled = true; };
  }, [enabled, passages, revision]);
  if (!enabled || !notes.length) return null;
  return (
    <div data-compare-band="notes" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={headStyle}><span aria-hidden="true">› </span>{NOTES_COPY.fromYourNotes}</span>
      {notes.map((link) => (
        <NoteCard key={link.linkId} link={link} extra={
          used.includes(link.linkId) ? <MeaningLabel>✓</MeaningLabel> : (
            <button type="button" style={linkStyle} disabled={busy || !link.takeText}
              onClick={() => { if (link.takeText) { onUse(link.takeText); setUsed((value) => [...value, link.linkId]); } }}>
              {NOTES_COPY.useAsMyTake}
            </button>
          )} />
      ))}
    </div>
  );
}

// ── link one of your notes… (from the Reader's passage menu) ──────────────

export function NoteLinkPicker({ extractionId, spanId, onClose, onError }: {
  extractionId: string;
  spanId: string;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const ctx = useNotes();
  const [query, setQuery] = useState("");
  const [asked, setAsked] = useState<string | null>(null);
  const [hits, setHits] = useState<NoteHitDto[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [linked, setLinked] = useState<string[]>([]);
  const [why, setWhy] = useState(false);

  const search = useCallback(async (words: string) => {
    setBusy(true);
    try {
      const out = await api.notesSearch(words ? { query: words } : { extractionId, spanId });
      setAsked(out.query);
      setHits(out.hits);
    } catch (error) {
      onError(errorMessage(error, "Couldn't look in your notes just now."));
      setHits([]);
    } finally {
      setBusy(false);
    }
  }, [extractionId, spanId, onError]);

  useEffect(() => { void search(""); }, [search]);

  const link = async (hit: NoteHitDto) => {
    setBusy(true);
    try {
      await api.notesLink({
        note: { path: hit.path, line: hit.line, headingPath: hit.headingPath, title: hit.title, contentHash: hit.contentHash, mtime: hit.mtime },
        extractionId, spanId,
      });
      setLinked((value) => [...value, hit.noteKey]);
      ctx?.onChanged();
    } catch (error) {
      onError(errorMessage(error, "Couldn't link that note."));
    } finally {
      setBusy(false);
    }
  };

  if (!ctx) return null;
  return (
    <div data-note-picker={spanId} role="dialog" aria-label={NOTES_COPY.linkNote}
      onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onClose(); } }}
      style={{ display: "flex", flexDirection: "column", gap: 6, border: `1px solid ${COLOR.borderStrong}`, background: COLOR.bg, padding: "8px 10px", fontFamily: FONT_MONO }}>
      <span style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <span style={headStyle}><span aria-hidden="true">› </span>{NOTES_COPY.linkNote}</span>
        <span style={{ flex: 1 }} />
        <button type="button" style={quietStyle} onClick={onClose}>{NOTES_COPY.close}</button>
      </span>
      <form style={{ display: "flex", gap: 6 }} onSubmit={(event) => { event.preventDefault(); void search(query.trim()); }}>
        <input aria-label={NOTES_COPY.searchPlaceholder} placeholder={NOTES_COPY.searchPlaceholder} value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ flex: 1, fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}`, padding: "3px 6px" }} />
        <button type="submit" style={linkStyle} disabled={busy}>↵</button>
      </form>
      {busy && hits === null ? <MeaningLabel><span aria-hidden="true">◐</span> {NOTES_COPY.searching}</MeaningLabel> : null}
      {hits !== null && !query.trim() && asked ? <MeaningLabel>{NOTES_COPY.forSection}: {asked}</MeaningLabel> : null}
      {hits !== null && hits.length === 0 ? <MeaningLabel>{NOTES_COPY.nothingFound}</MeaningLabel> : null}
      {(hits ?? []).map((hit) => (
        <div key={hit.noteKey} data-note-hit={hit.noteKey} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span style={{ fontSize: 11, color: COLOR.text }}>
            <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>
            {[hit.title, hit.heading].filter(Boolean).join(" › ")}
          </span>
          {hit.snippet ? <span style={{ fontSize: 10, color: COLOR.textDim }}>{hit.snippet}</span> : null}
          <span style={{ display: "flex", gap: 8 }}>
            {hit.origin === "pocket_notes" ? <MeaningLabel>{ctx.settings.pocketNotesLabel}</MeaningLabel> : null}
            {linked.includes(hit.noteKey) ? <MeaningLabel>{NOTES_COPY.linked} ✓</MeaningLabel> : (
              <button type="button" style={linkStyle} disabled={busy} onClick={() => void link(hit)}>{NOTES_COPY.linkHere}</button>
            )}
          </span>
        </div>
      ))}
      <button type="button" style={{ ...quietStyle, alignSelf: "flex-start" }} aria-expanded={why} onClick={() => setWhy((value) => !value)}>
        {NOTES_COPY.whereThisGoes}
      </button>
      {why ? <MeaningLabel>{NOTES_COPY.whereLine}</MeaningLabel> : null}
    </div>
  );
}
