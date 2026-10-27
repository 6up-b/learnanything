// Reader CA3: compare from anywhere (ux_reader_compare_ask_v1 §4.2-§4.4, X1, X2; K12, K16).
//
// * `ScopeLine`, the routed line: "→ comparing · your passage · [Axler ×]
//   [Strang ×] + add a book · on: eigenvalues · change". The chips are visible
//   so "change" is honest, never to ask for a confirmation: the comparison has
//   started already. A name the library doesn't have reads "“Hoffman” isn't in
//   your library"; nothing is guessed. No chip, no line, no number of books.
// * `AddBook`: "+ add a book" opens a short picker of the library's books
//   (type-ahead; ↵ adds the first match; Esc closes).
// * `CompareScopeView`: a comparison with no library answer (the selection
//   verb, the ask box's comparison, the tutor's offer): the routed line, the
//   table at once (today's comparison view; CA4 redraws it by point), the
//   refine box (`/`: other books change the chips, a view becomes a requested
//   perspective), "previous ▸" (the earlier table, never paid for twice), the
//   tutor about this comparison (Ctrl+↵) and "practice this".
//
// Nothing here takes focus unasked, animates or counts things to read (G54-G58).
// The refine box and the picker take the cursor only on the learner's own key.
import { useEffect, useRef, useState, type ComponentType, type KeyboardEvent as ReactKeyboardEvent } from "react";
import type { CompareTableDto, LibraryBookDto, ProposedItemDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import { CompareKeep } from "./CompareKeep";
import { ModelActionState } from "./ModelActionState";
import { LIBRARY_COPY, SCOPE_COPY, type LibraryAskController, type ScopeChips } from "./useLibraryAsk";
import { MeaningLabel, ModelVoice } from "./voices";

const linkStyle = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
} as const;

const chipStyle = {
  display: "inline-flex",
  alignItems: "baseline",
  gap: 4,
  border: `1px solid ${COLOR.border}`,
  padding: "0 6px",
  fontFamily: FONT_MONO,
  fontSize: 11,
  color: COLOR.text,
} as const;

const headStyle = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim, textTransform: "uppercase" as const };

/** The books the line shows: the chosen ones, else (every book with a match)
 *  the books the comparison found, without the anchor's own (it is "your passage"). */
export function shownBooks(chips: ScopeChips, table: CompareTableDto | null): LibraryBookDto[] {
  if (chips.books.length) return chips.books;
  const books: LibraryBookDto[] = [];
  for (const row of table?.rows ?? []) {
    if (!row.sourceId || (chips.anchored && row.isOpenSource)) continue;
    if (!books.some((book) => book.sourceId === row.sourceId)) books.push({ sourceId: row.sourceId, title: row.sourceTitle ?? row.sourceId });
  }
  return books;
}

export function AddBook({ library, chosen, onAdd }: {
  library: LibraryBookDto[];
  chosen: string[];
  onAdd: (book: LibraryBookDto) => void;
}) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    // The learner pressed "+ add a book": the picker takes the cursor.
    if (open) inputRef.current?.focus({ preventScroll: true });
  }, [open]);
  const words = text.trim().toLowerCase();
  const matches = library
    .filter((book) => !chosen.includes(book.sourceId))
    .filter((book) => !words || book.title.toLowerCase().includes(words))
    .slice(0, 6);
  if (!open) {
    return (
      <button type="button" style={linkStyle} onClick={() => setOpen(true)} disabled={library.length === 0}>
        {SCOPE_COPY.addBook}
      </button>
    );
  }
  const add = (book: LibraryBookDto | undefined) => {
    if (!book) return;
    onAdd(book);
    setText("");
    setOpen(false);
  };
  return (
    <span style={{ display: "inline-flex", flexDirection: "column", gap: 2 }}>
      <input
        ref={inputRef}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            add(matches[0]);
          } else if (event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            setOpen(false);
          }
        }}
        placeholder={SCOPE_COPY.addPlaceholder}
        aria-label="add a book to compare"
        role="combobox"
        aria-expanded={matches.length > 0}
        aria-controls="compare-add-book"
        style={{ fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "2px 6px", width: 220 }}
      />
      {matches.length ? (
        <ul id="compare-add-book" role="listbox" aria-label="books in your library" style={{ margin: 0, padding: 0, listStyle: "none" }}>
          {matches.map((book) => (
            <li key={book.sourceId} role="option" aria-selected={book === matches[0]}>
              <button type="button" style={{ ...linkStyle, textDecoration: "none", fontSize: 11 }} onClick={() => add(book)}>
                {book.title}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </span>
  );
}

export function ScopeLine({ chips, table, library, onBooks, onReword }: {
  chips: ScopeChips;
  table: CompareTableDto | null;
  library: LibraryBookDto[];
  onBooks: (books: LibraryBookDto[]) => void;
  onReword: (() => void) | null;
}) {
  const books = shownBooks(chips, table);
  const chosen = books.map((book) => book.sourceId);
  // "+ add a book" offers the books the comparison could read (with the anchor's own left out).
  const anchorSource = chips.anchored ? table?.rows.find((row) => row.isOpenSource)?.sourceId ?? null : null;
  const offer = library.filter((book) => book.sourceId !== anchorSource);
  return (
    <div data-scope-line="" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
        <span aria-hidden="true">→</span>
        <span>{SCOPE_COPY.comparing}</span>
        {chips.anchored ? <span style={chipStyle}>{SCOPE_COPY.yourPassage}</span> : null}
        {books.length === 0 && !table ? <span>· {SCOPE_COPY.allBooks}</span> : null}
        {books.map((book) => (
          <span key={book.sourceId} data-scope-chip={book.sourceId} style={chipStyle}>
            {book.title}
            <button
              type="button"
              aria-label={SCOPE_COPY.remove(book.title)}
              onClick={() => onBooks(books.filter((other) => other.sourceId !== book.sourceId))}
              style={{ ...linkStyle, textDecoration: "none", fontSize: 11 }}
            >
              ×
            </button>
          </span>
        ))}
        <AddBook library={offer} chosen={chosen} onAdd={(book) => onBooks([...books, book])} />
        {chips.topic ? <span>· {SCOPE_COPY.on} {chips.topic}</span> : null}
        {onReword ? <button type="button" style={linkStyle} onClick={onReword}>{SCOPE_COPY.change}</button> : null}
      </span>
      {chips.unmatched ? (
        <MeaningLabel style={{ fontSize: 11 }}>{SCOPE_COPY.notInLibrary(chips.unmatched)}</MeaningLabel>
      ) : null}
    </div>
  );
}

/** The refine box (`/`), shown on the learner's key; it takes the cursor then. */
export function RefineBox({ ctl, open, onClose }: { ctl: LibraryAskController; open: boolean; onClose: () => void }) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (open) inputRef.current?.focus({ preventScroll: true });
  }, [open]);
  const refine = ctl.state?.refine;
  return (
    <div data-refine="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {open ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (!text.trim()) return;
            void ctl.refine(text);
            setText("");
            onClose();
          }}
        >
          <input
            ref={inputRef}
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                onClose();
              }
            }}
            placeholder={SCOPE_COPY.refine}
            aria-label="refine this comparison"
            style={{ width: "100%", boxSizing: "border-box", fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "4px 8px" }}
          />
        </form>
      ) : null}
      {refine?.phase === "pending" ? <ModelActionState phase="pending" verb={SCOPE_COPY.refining} /> : null}
      {refine?.phase === "failed" && refine.failure ? <MeaningLabel style={{ fontSize: 11 }}>{refine.failure}</MeaningLabel> : null}
    </div>
  );
}

/** A comparison with no library answer: the whole comparing pane (CA3). */
export function CompareScopeView({ ctl, onClose, onReword, onPracticePick, Table }: {
  ctl: LibraryAskController;
  onClose: () => void;
  /** "change": reopen the ask box with the words kept (absent: no ask box here). */
  onReword: ((words: string) => void) | null;
  onPracticePick: ((item: ProposedItemDto, proposalId: string | null) => void) | null;
  Table: ComponentType<{ table: CompareTableDto }>;
}) {
  const [refineOpen, setRefineOpen] = useState(false);
  const [showPrevious, setShowPrevious] = useState(false);
  const [question, setQuestion] = useState("");
  const state = ctl.state;
  if (!state?.chips) return null;
  const table = state.compare.value;
  const previous = state.previous ?? [];
  const earlier = previous[previous.length - 1] ?? null;
  const reword = onReword && state.chips.words !== null ? () => {
    const words = ctl.reword();
    if (words !== null) onReword(words);
  } : null;
  const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    const typing = Boolean(target.closest("input, textarea, select"));
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && table) {
      event.preventDefault();
      void ctl.askTutor(question);
      return;
    }
    if (typing || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === "/" && table) {
      event.preventDefault();
      setRefineOpen(true);
    }
  };
  return (
    <section aria-label="compare your books" data-compare-scope="" onKeyDown={onKeyDown} tabIndex={-1}
      style={{ display: "flex", flexDirection: "column", gap: 12, padding: "16px 18px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <span style={headStyle}>{SCOPE_COPY.title}</span>
        <span style={{ flex: 1 }} />
        <button type="button" onClick={onClose} style={linkStyle}>{LIBRARY_COPY.close}</button>
      </div>
      <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>“{state.request.query}”</span>
      <ScopeLine chips={state.chips} table={table} library={state.library ?? []} onBooks={ctl.setBooks} onReword={reword} />
      <ModelActionState
        phase={state.compare.phase}
        verb={SCOPE_COPY.pending}
        failure={state.compare.failure ?? undefined}
        kept="Your question and the books are kept."
        capRoute="comparison"
        fallback="Reading the passages"
        onCancel={ctl.cancelCompare}
        onRetry={ctl.retryCompare}
      >
        {showPrevious && earlier ? (
          <div data-previous-comparison="" aria-label={SCOPE_COPY.previousLabel} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <button type="button" style={linkStyle} onClick={() => setShowPrevious(false)}>{SCOPE_COPY.hidePrevious}</button>
            <Table table={earlier} />
          </div>
        ) : table ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Table table={table} />
            {ctl.keep ? <CompareKeep table={table} target={{ askId: table.askId }} /> : null}
          </div>
        ) : null}
      </ModelActionState>
      {table ? (
        <div style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
          <RefineBox ctl={ctl} open={refineOpen} onClose={() => setRefineOpen(false)} />
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline" }}>
            {!refineOpen ? <button type="button" style={linkStyle} onClick={() => setRefineOpen(true)}>/ refine</button> : null}
            {earlier && !showPrevious ? <button type="button" style={linkStyle} onClick={() => setShowPrevious(true)}>{SCOPE_COPY.previous}</button> : null}
            <button type="button" onClick={() => void ctl.practice()} style={linkStyle}>{LIBRARY_COPY.practice} ▸</button>
          </div>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={headStyle}>{SCOPE_COPY.askTutor}</span>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={LIBRARY_COPY.tutorPlaceholder}
              aria-label="your question for the tutor about this comparison"
              style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 8px" }}
            />
          </label>
          <MeaningLabel style={{ fontSize: 10 }}>{SCOPE_COPY.askTutorNote} · ctrl+↵ ask · {SCOPE_COPY.refineKeys}</MeaningLabel>
          {state.tutor.phase !== "idle" ? (
            <ModelActionState
              phase={state.tutor.phase}
              verb={LIBRARY_COPY.tutorWriting}
              failure={state.tutor.failure ?? undefined}
              kept="Your question is kept."
              capRoute="tutor"
              onCancel={ctl.cancelTutor}
              onRetry={() => void ctl.askTutor(question)}
            >
              {state.tutor.value ? (
                <ModelVoice first note={state.tutor.value.label}>
                  <MarkdownMath value={state.tutor.value.answerMd ?? ""} />
                </ModelVoice>
              ) : null}
            </ModelActionState>
          ) : null}
          {state.practice.phase !== "idle" ? (
            <ModelActionState phase={state.practice.phase} verb={LIBRARY_COPY.practiceLooking}
              failure={state.practice.failure ?? undefined} onRetry={() => void ctl.practice()}>
              {state.practice.value?.items.length ? (
                <ul aria-label="practice for this question" style={{ margin: 0, paddingLeft: 16 }}>
                  {state.practice.value.items.map((item) => (
                    <li key={item.practiceItemId} style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                      {item.prompt}{" "}
                      {onPracticePick ? (
                        <button type="button" style={linkStyle} onClick={() => onPracticePick(item, state.practice.value?.proposalId ?? null)}>
                          practice this ▸
                        </button>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <MeaningLabel style={{ fontSize: 11 }}>{LIBRARY_COPY.practiceNothing}</MeaningLabel>
              )}
            </ModelActionState>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
