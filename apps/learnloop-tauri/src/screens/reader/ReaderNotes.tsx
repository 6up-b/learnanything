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
// Curriculum C5 (spec §10.2, UX §4.10): with the learner's opt-in (the contract's
// `gaps`, Settings), every notes surface also says *where this goes*: a linked note may be
// read for gaps in their understanding, which only steers what to suggest. Without the
// opt-in nothing here changes.
//
// A model's link says "linked by LearnLoop's model"; one tap hides it (*hide*), and it
// stays hidden. Keeping it needs no tap. A Pocket Notes page says "handwritten ·
// transcribed by Pocket Notes". A note is never a source, never evidence and never
// grades anything. Nothing here opens, moves focus or animates unasked.
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "../../api/client";
import type { NoteHitDto, NoteLinkDto, NoteMarksDto, NotesContractDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { useNotes, type HiddenNote, type NotesContextValue } from "./notesContext";
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
  gapsLine: "You let your linked notes steer suggestions (Settings): LearnLoop's model on your ChatGPT plan reads a note you linked for gaps in your understanding. It only ever steers what to suggest, never grades you, and a note you hide is never read.",
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

/** UI refresh cadence while the background linking runs or waits for the plan or tend
 *  (Codex review F4). `keep`: how often a screen asks again, never a model parameter. */
export const NOTES_POLL_MS = { running: 3_000, waiting: 60_000 } as const;

/** Keep the cards of links hidden this session that a refresh no longer lists, where they
 *  were (Codex review F5: *undo* must survive the refresh a hide starts). */
export function retainHidden(previous: readonly NoteLinkDto[], next: readonly NoteLinkDto[],
  hidden: ReadonlyMap<string, HiddenNote>): NoteLinkDto[] {
  const listed = new Set(next.map((link) => link.linkId));
  const out = [...next];
  previous.forEach((link, index) => {
    if (hidden.has(link.linkId) && !listed.has(link.linkId)) out.splice(Math.min(index, out.length), 0, link);
  });
  return out;
}

/** Hide one link (one tap), with undo; the server keeps the learner's word across
 *  re-judgments, the context keeps the hidden card on screen until undone. */
function useDecide(ctx: NotesContextValue | null) {
  const [local, setLocal] = useState<Record<string, string>>({});
  const [failure, setFailure] = useState<string | null>(null);
  const hiddenId = (link: NoteLinkDto) => (ctx ? ctx.hidden.get(link.linkId)?.hiddenId : local[link.linkId]);
  const decide = async (link: NoteLinkDto, choice: "hide" | "keep") => {
    setFailure(null);
    try {
      if (choice === "hide") {
        const out = await api.notesDecide({ linkId: link.linkId, choice: "hide" });
        if (ctx) ctx.remember(link, out.linkId);
        else setLocal((current) => ({ ...current, [link.linkId]: out.linkId }));
      } else {
        const id = hiddenId(link);
        if (!id) return;
        await api.notesDecide({ linkId: id, choice: "keep" });
        if (ctx) ctx.forget(link.linkId);
        else setLocal((current) => {
          const next = { ...current };
          delete next[link.linkId];
          return next;
        });
      }
      ctx?.onChanged();
    } catch (error) {
      setFailure(errorMessage(error, "Couldn't save that; nothing changed."));
    }
  };
  return { isHidden: (link: NoteLinkDto) => Boolean(hiddenId(link)), failure, decide };
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

/** *ⓘ where this goes* (UX §4.10). `always`: the picker's own disclosure (C2), shown
 *  whatever the opt-in says; otherwise only with the opt-in on (curriculum C5), so the
 *  notes surfaces are today's exactly without it. */
export function NotesWhereThisGoes({ ctx, always = false }: { ctx: NotesContextValue | null; always?: boolean }) {
  const [why, setWhy] = useState(false);
  const gaps = Boolean(ctx?.settings.gaps);
  if (!always && !gaps) return null;
  return (
    <>
      <button type="button" data-notes-where={always ? undefined : ""} style={{ ...quietStyle, alignSelf: "flex-start" }} aria-expanded={why}
        onClick={() => setWhy((value) => !value)}>
        {NOTES_COPY.whereThisGoes}
      </button>
      {why ? <MeaningLabel>{NOTES_COPY.whereLine}</MeaningLabel> : null}
      {why && gaps ? <MeaningLabel>{NOTES_COPY.gapsLine}</MeaningLabel> : null}
    </>
  );
}

function NoteList({ links, ctx }: { links: NoteLinkDto[]; ctx: NotesContextValue | null }) {
  const { isHidden, failure, decide } = useDecide(ctx);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {links.map((link) => (
        <NoteCard key={link.linkId} link={link} isHidden={isHidden(link)}
          onHide={() => void decide(link, "hide")} onUndo={() => void decide(link, "keep")} />
      ))}
      {failure ? <span role="status"><MeaningLabel>{failure}</MeaningLabel></span> : null}
      <NotesWhereThisGoes ctx={ctx} />
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
const NO_HIDDEN: ReadonlyMap<string, HiddenNote> = new Map();

/** A reading's marks as read now, with the cards hidden this session kept in place (F5):
 *  a passage whose last note was hidden keeps its › and the hidden card's *undo*. */
export function mergeMarks(previous: ReadonlyMap<string, NoteMark>, next: readonly NoteMark[],
  hidden: ReadonlyMap<string, HiddenNote>): Map<string, NoteMark> {
  const out = new Map(next.map((mark) => [mark.spanId, mark] as const));
  if (hidden.size === 0) return out;
  for (const [spanId, mark] of previous) {
    const merged = retainHidden(mark.notes, out.get(spanId)?.notes ?? [], hidden);
    if (merged.length) out.set(spanId, { ...mark, notes: merged });
  }
  return out;
}

/** The › marks of the open reading (off: none, nothing read), and the notes context. */
export function useNoteMarks({ settings, extractionId, offline }: {
  settings: NotesContractDto | null | undefined;
  extractionId: string | null;
  offline: boolean;
}) {
  const enabled = Boolean(settings?.enabled);
  const [marks, setMarks] = useState<ReadonlyMap<string, NoteMark>>(NO_MARKS);
  const [revision, setRevision] = useState(0);
  const [hidden, setHidden] = useState<ReadonlyMap<string, HiddenNote>>(NO_HIDDEN);
  const hiddenRef = useRef(hidden);
  hiddenRef.current = hidden;
  const marksFor = useRef<string | null>(null);
  useEffect(() => {
    if (!enabled || !extractionId || offline) {
      setMarks(NO_MARKS);
      marksFor.current = null;
      return;
    }
    let cancelled = false;
    void api.notesMarks({ extractionId })
      .then((result) => {
        if (cancelled) return;
        // Another reading's marks never carry over (its hidden cards stay with it).
        const same = marksFor.current === extractionId;
        marksFor.current = extractionId;
        setMarks((previous) => mergeMarks(same ? previous : NO_MARKS, result.marks, hiddenRef.current));
      })
      // Marks are a convenience: an unreadable list shows none, quietly.
      .catch(() => { if (!cancelled) setMarks(NO_MARKS); });
    return () => { cancelled = true; };
  }, [enabled, extractionId, offline, revision]);
  const onChanged = useCallback(() => setRevision((value) => value + 1), []);
  const remember = useCallback((link: NoteLinkDto, hiddenId: string) => {
    setHidden((current) => new Map(current).set(link.linkId, { link, hiddenId }));
  }, []);
  const forget = useCallback((linkId: string) => {
    setHidden((current) => {
      if (!current.has(linkId)) return current;
      const next = new Map(current);
      next.delete(linkId);
      return next;
    });
  }, []);
  const settingsKey = settings ? JSON.stringify(settings) : "";
  const context = useMemo<NotesContextValue | null>(
    () => (settings?.enabled ? { settings, onChanged, revision, hidden, remember, forget } : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [settingsKey, onChanged, revision, hidden, remember, forget],
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

/** The notes of one deliverable's path, by topic (and the background linking started once
 *  a day). While that linking runs (or waits for the plan or tend) the path is read again
 *  (Codex review F4: `NOTES_POLL_MS`); when it finishes, every surface reads its notes
 *  again (the reading's › marks too). */
export function usePathNotes(goalId: string | null, ready: boolean) {
  const ctx = useNotes();
  const [byLo, setByLo] = useState<ReadonlyMap<string, NoteLinkDto[]>>(new Map());
  const [tick, setTick] = useState(0);
  const enabled = Boolean(ctx?.settings.enabled) && Boolean(goalId) && ready;
  const revision = ctx?.revision ?? 0;
  const ctxRef = useRef(ctx);
  ctxRef.current = ctx;
  const linking = useRef<{ goalId: string | null; state: string | null }>({ goalId: null, state: null });
  useEffect(() => {
    if (!enabled || !goalId) { setByLo(new Map()); linking.current = { goalId: null, state: null }; return undefined; }
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    void api.notesPath({ goalId })
      .then((out) => {
        if (cancelled) return;
        const hidden = ctxRef.current?.hidden ?? NO_HIDDEN;
        const same = linking.current.goalId === goalId;
        const before = same ? linking.current.state : null;
        linking.current = { goalId, state: out.linking ?? null };
        setByLo((previous) => {
          const next = new Map(out.lines.map((line) => [line.learningObjectId, line.notes] as const));
          if (same) {
            for (const [lo, list] of previous) {
              const merged = retainHidden(list, next.get(lo) ?? [], hidden);
              if (merged.length) next.set(lo, merged);
            }
          }
          return next;
        });
        if ((before === "running" || before === "waiting") && out.linking === "done") ctxRef.current?.onChanged();
        const wait = out.linking === "running" ? NOTES_POLL_MS.running : out.linking === "waiting" ? NOTES_POLL_MS.waiting : null;
        if (wait !== null) timer = setTimeout(() => { if (!cancelled) setTick((value) => value + 1); }, wait);
      })
      // Notes are a convenience on the path: unreadable, none show.
      .catch(() => { if (!cancelled) setByLo(new Map()); });
    return () => { cancelled = true; if (timer !== undefined) clearTimeout(timer); };
  }, [enabled, goalId, revision, tick]);
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

/** What *use as my take* did: kept as a take, put in the take's draft (kept with the
 *  comparison), or failed (nothing saved: the action stays to try again). */
export type NoteTakeOutcome = "kept" | "drafted" | "failed";

export function NotesTakeBand({ keys, onUse, busy = false }: {
  keys: string[];
  onUse: (text: string) => Promise<NoteTakeOutcome>;
  busy?: boolean;
}) {
  const ctx = useNotes();
  const [notes, setNotes] = useState<NoteLinkDto[]>([]);
  const [used, setUsed] = useState<string[]>([]);
  const [using, setUsing] = useState<string | null>(null);
  const keysKey = keys.join("|");
  const passages = useMemo(() => passagesOfKeys(keys), [keysKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const enabled = Boolean(ctx?.settings.enabled) && passages.length > 0;
  const revision = ctx?.revision ?? 0;
  // Another comparison: nothing of it was used yet (Codex review F11).
  useEffect(() => { setUsed([]); setUsing(null); }, [keysKey]);
  const use = async (link: NoteLinkDto) => {
    if (!link.takeText || using) return;
    setUsing(link.linkId);
    try {
      // Marked used only once the take is kept (Codex review F11); a failure keeps the action.
      if ((await onUse(link.takeText)) === "kept") setUsed((value) => [...value, link.linkId]);
    } finally {
      setUsing(null);
    }
  };
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
            <button type="button" style={linkStyle} disabled={busy || Boolean(using) || !link.takeText}
              onClick={() => void use(link)}>
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

  const on = ctx !== null;
  useEffect(() => { if (on) void search(""); }, [search, on]);

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
      <NotesWhereThisGoes ctx={ctx} always />
    </div>
  );
}
