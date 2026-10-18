// The comparing posture's content (reader workbench RW4a; spec §7.3; UX §4.5,
// W9, W10): a library answer, sources first. The header says how the passages
// were found and that the notes are LearnLoop's model's; each passage is a §
// excerpt with its locator and, when ready, one ◇ line on what it contributes
// (peek · pin · open); prerequisites and applications from the concept graph
// sit under their own subheads. Pinned passages can be compared (a table with
// one row per source, each cell quoting its own source, no consensus) or put
// to the tutor ("answers only from these N passages"). "Practice this
// question" lists proposals; picking one is a learner pick the plan serves.
// Nothing here takes focus, animates or opens a modal (G54).
import { useState, type KeyboardEvent as ReactKeyboardEvent } from "react";
import type { CompareTableDto, LibraryHitDto, LibraryNoteDto, ProposedItemDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import { ModelActionState } from "./ModelActionState";
import { LIBRARY_COPY, type LibraryAskController } from "./useLibraryAsk";
import { EvidenceMarker, MeaningLabel, ModelVoice, SourceVoice } from "./voices";

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

const headStyle = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim, textTransform: "uppercase" as const };

function locator(hit: LibraryHitDto): string {
  return [hit.group.toLowerCase(), hit.section, hit.page !== null ? `p.${hit.page}` : null].filter(Boolean).join(" · ");
}

function clip(text: string, limit = 420): string {
  const flat = text.split(/\s+/).join(" ").trim();
  return flat.length <= limit ? flat : `${flat.slice(0, limit - 1).trimEnd()}…`;
}

function HitBlock({
  hit,
  note,
  notesPhase,
  pinned,
  onPeek,
  onPin,
  onOpen,
}: {
  hit: LibraryHitDto;
  note: LibraryNoteDto | undefined;
  notesPhase: string;
  pinned: boolean;
  onPeek: () => void;
  onPin: () => void;
  onOpen: (() => void) | null;
}) {
  const modelRole = note?.roles?.length && hit.role !== note.roles[0] ? note.roles[0].replace(/_/g, " ") : null;
  return (
    <div
      data-library-hit={hit.key}
      tabIndex={0}
      aria-label={`${hit.sourceTitle ?? "a source"}, ${locator(hit)}${pinned ? ", pinned" : ""}`}
      style={{ display: "flex", flexDirection: "column", gap: 4, opacity: note?.verdict === "unrelated" ? 0.75 : 1 }}
    >
      <SourceVoice source={hit.sourceTitle} locator={locator(hit)}>
        <span style={{ fontSize: 12 }}>{clip(hit.text)}</span>
      </SourceVoice>
      {note?.line ? (
        <ModelVoice note={modelRole ? `${modelRole} (${LIBRARY_COPY.modelsLabel})` : null}>
          <MarkdownMath value={note.line} />
        </ModelVoice>
      ) : notesPhase === "pending" ? (
        <MeaningLabel style={{ fontSize: 10 }}><span aria-hidden="true">◐</span> {LIBRARY_COPY.noting}…</MeaningLabel>
      ) : null}
      {note?.speaksTo ? (
        <MeaningLabel style={{ fontSize: 11 }}>
          <span aria-hidden="true">◌ </span>{LIBRARY_COPY.speaksTo} {clip(note.speaksTo.statement, 120)} (model's reading)
        </MeaningLabel>
      ) : null}
      <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
        <button type="button" onClick={onPeek} style={linkStyle} aria-label={`peek at ${hit.sourceTitle ?? "this passage"}`}>peek</button>
        <button type="button" onClick={onPin} style={linkStyle} aria-pressed={pinned}>{pinned ? "pinned ✓" : "pin"}</button>
        {onOpen ? <button type="button" onClick={onOpen} style={linkStyle}>open</button> : null}
      </div>
    </div>
  );
}

function CompareCells({ cells }: { cells: CompareTableDto["rows"][number]["contributes"] }) {
  if (!cells.length) return <MeaningLabel style={{ fontSize: 11 }}>—</MeaningLabel>;
  return (
    <>
      {cells.map((cell, index) => (
        <ModelVoice key={index}>
          <span>{cell.line}</span>
          {cell.quote ? <span style={{ display: "block", color: COLOR.textDim, fontSize: 11 }}>§ “{cell.quote}”</span> : null}
        </ModelVoice>
      ))}
    </>
  );
}

/** W10, display only (RW4d adds keep): one row per source; differences kept. */
export function CompareTable({ table }: { table: CompareTableDto }) {
  return (
    <div data-compare-table="" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <span style={headStyle}>compare · {table.rows.length} sources · {table.header}</span>
      {table.status === "too_few_sources" ? (
        <MeaningLabel style={{ fontSize: 11 }}>These passages come from one source; pin one from another book to compare.</MeaningLabel>
      ) : null}
      <div role="table" aria-label="how your sources treat this" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {table.rows.map((row) => (
          <div role="row" key={row.key} style={{ display: "flex", flexDirection: "column", gap: 6, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
            <span role="rowheader" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
              § {row.isOpenSource ? "your passage · " : ""}{row.sourceTitle ?? "a source"}{row.page !== null ? ` · p.${row.page}` : ""}
            </span>
            {([["contributes", row.contributes], ["assumes", row.assumes], ["differs from the others", row.differs]] as const).map(([label, cells]) => (
              <div role="cell" key={label} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span style={{ ...headStyle, letterSpacing: "0.06em" }}>{label}</span>
                <CompareCells cells={cells} />
              </div>
            ))}
          </div>
        ))}
      </div>
      {table.alsoDiscussedIn.length ? (
        <MeaningLabel style={{ fontSize: 11 }}>
          also discussed in: {table.alsoDiscussedIn.map((entry) => String(entry.sourceTitle ?? entry.sourceId ?? "a source")).join(", ")}
        </MeaningLabel>
      ) : null}
      {table.droppedPins.length ? (
        <MeaningLabel style={{ fontSize: 11 }}>
          left out: {table.droppedPins.map((pin) => String(pin.reason ?? "not available")).join("; ")}
        </MeaningLabel>
      ) : null}
    </div>
  );
}

export function LibraryAnswer({
  ctl,
  onOpenHit,
  onPracticePick,
  onClose,
}: {
  ctl: LibraryAskController;
  /** Open a hit in the left pane (a crumb: Alt+← comes back). */
  onOpenHit: ((hit: LibraryHitDto) => void) | null;
  /** A learner pick of a practice proposal (the plan serves it). */
  onPracticePick: ((item: ProposedItemDto, proposalId: string | null) => void) | null;
  onClose: () => void;
}) {
  const [question, setQuestion] = useState("");
  const state = ctl.state;
  if (!state) return null;
  const ask = state.ask.value;
  const notes = new Map((state.notes.value?.notes ?? []).map((note) => [note.key, note]));
  const notesPhase = state.notes.phase;
  const hits = new Map((ask?.hits ?? []).map((hit) => [hit.key, hit]));
  const order = state.notes.value?.order ?? [];
  const ordered = (keys: string[]) => (order.length ? [...keys].sort((a, b) => {
    const left = order.indexOf(a);
    const right = order.indexOf(b);
    return (left < 0 ? 999 : left) - (right < 0 ? 999 : right);
  }) : keys);
  const block = (key: string) => {
    const hit = hits.get(key);
    if (!hit) return null;
    return (
      <HitBlock
        key={key}
        hit={hit}
        note={notes.get(key)}
        notesPhase={notesPhase}
        pinned={state.pinned.includes(key)}
        onPeek={() => void ctl.peek(key)}
        onPin={() => ctl.togglePin(key)}
        onOpen={onOpenHit ? () => onOpenHit(hit) : null}
      />
    );
  };
  const prerequisites = ask?.expansions.find((expansion) => expansion.expansion === "prerequisites");
  // The comparing keys (UX §3.5), only while focus is inside the answer (never
  // on the reading surface): ↑ ↓ move between passages · Space peek · p pin ·
  // o open · c compare pinned · Ctrl+↵ ask the tutor about pinned.
  const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("input, textarea, select")) {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && state.pinned.length) {
        event.preventDefault();
        void ctl.askTutor(question);
      }
      return;
    }
    const items = Array.from(event.currentTarget.querySelectorAll<HTMLElement>("[data-library-hit]"));
    const current = target.closest<HTMLElement>("[data-library-hit]");
    const key = current?.getAttribute("data-library-hit") ?? null;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (!items.length) return;
      event.preventDefault();
      const at = current ? items.indexOf(current) : -1;
      const next = items[(at + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length];
      next.focus({ preventScroll: false });
      return;
    }
    if (event.ctrlKey || event.metaKey || event.altKey) {
      if (event.key === "Enter" && state.pinned.length) {
        event.preventDefault();
        void ctl.askTutor(question);
      }
      return;
    }
    if (key && event.key === " ") {
      event.preventDefault();
      void ctl.peek(key);
    } else if (key && event.key === "p") {
      event.preventDefault();
      ctl.togglePin(key);
    } else if (key && event.key === "o" && onOpenHit) {
      const hit = hits.get(key);
      if (hit) {
        event.preventDefault();
        onOpenHit(hit);
      }
    } else if (event.key === "c" && ctl.canCompare) {
      event.preventDefault();
      void ctl.compare();
    }
  };
  return (
    <section aria-label="ask your library" data-library-answer="" onKeyDown={onKeyDown} style={{ display: "flex", flexDirection: "column", gap: 12, padding: "16px 18px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        <span style={headStyle}>{LIBRARY_COPY.title}</span>
        <span style={{ flex: 1 }} />
        <button
          type="button"
          onClick={() => ctl.setPersonalized(!state.personalized)}
          aria-pressed={state.personalized}
          title={LIBRARY_COPY.personalizedWhy}
          style={{ ...linkStyle, textDecoration: "none", fontSize: 11 }}
        >
          {state.personalized ? LIBRARY_COPY.personalizedOn : LIBRARY_COPY.personalizedOff}
        </button>
        <button type="button" onClick={onClose} style={linkStyle}>{LIBRARY_COPY.close}</button>
      </div>
      <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>“{state.request.query}”</span>
      <ModelActionState
        phase={state.ask.phase}
        verb={LIBRARY_COPY.searching}
        failure={state.ask.failure ?? undefined}
        kept="Your question is kept."
        onRetry={ctl.retry}
        onCancel={onClose}
      >
        {ask ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <MeaningLabel style={{ fontSize: 11 }}>
              {ask.sourceCount} source{ask.sourceCount === 1 ? "" : "s"} · {ask.passageCount} passage{ask.passageCount === 1 ? "" : "s"} · {LIBRARY_COPY.found(ask.basis)} · {LIBRARY_COPY.notesBy}
            </MeaningLabel>
            {notesPhase !== "landed" && notesPhase !== "pending" && notesPhase !== "idle" ? (
              <ModelActionState
                phase={notesPhase}
                verb={LIBRARY_COPY.noting}
                failure={state.notes.failure ?? "Couldn't write the notes."}
                kept="The passages are here."
                capRoute="library notes"
                capAmount={state.notes.value?.reason?.match(/\$[0-9.]+/)?.[0]}
                fallback="Reading the passages"
                onRetry={ctl.retryNotes}
              />
            ) : null}
            {ask.hits.length === 0 ? <MeaningLabel style={{ fontSize: 12 }}>{LIBRARY_COPY.nothing}</MeaningLabel> : null}
            {prerequisites && ask.entry === "what_do_i_need_first" ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={headStyle}>{LIBRARY_COPY.prerequisitesTitle}</span>
                {prerequisites.learningObjects.length === 0 ? (
                  <MeaningLabel style={{ fontSize: 11 }}>Nothing is recorded as coming before this yet.</MeaningLabel>
                ) : prerequisites.learningObjects.map((lo) => (
                  <div key={lo.learningObjectId} style={{ display: "flex", gap: 8, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 12 }}>
                    <span style={{ color: COLOR.text }}>{lo.title}</span>
                    {lo.demonstrated ? <EvidenceMarker status="demonstrated" /> : <MeaningLabel style={{ fontSize: 11 }}>{LIBRARY_COPY.notShown}</MeaningLabel>}
                    {lo.keys.length === 0 ? <MeaningLabel style={{ fontSize: 11 }}>· no passage in your books yet</MeaningLabel> : null}
                  </div>
                ))}
              </div>
            ) : null}
            {ask.groups.sources.map((source) => (
              <div key={source.sourceId ?? source.sourceTitle ?? "source"} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <span style={{ ...headStyle, borderBottom: `1px solid ${COLOR.border}`, paddingBottom: 2 }}>{source.sourceTitle ?? "a source"}</span>
                {source.groups.map((group) => (
                  <div key={group.group} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {ordered(group.keys).map(block)}
                  </div>
                ))}
              </div>
            ))}
            {ask.groups.expansions.map((expansion) => (
              <div key={expansion.expansion} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <span style={{ ...headStyle, borderBottom: `1px solid ${COLOR.border}`, paddingBottom: 2 }}>
                  {expansion.label === "Prerequisite" ? "Prerequisites" : expansion.label === "Application" ? "Applications" : expansion.label} · from your concept map
                </span>
                {ordered(expansion.keys).map(block)}
              </div>
            ))}
            {state.peek ? (
              <div data-library-peek="" style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", gap: 8 }}>
                  <span style={headStyle}>peek</span>
                  <span style={{ flex: 1 }} />
                  <button type="button" onClick={ctl.closePeek} style={linkStyle}>close peek</button>
                </div>
                {state.peek.view ? (
                  <SourceVoice source={hits.get(state.peek.key)?.sourceTitle} locator={state.peek.view.page !== null ? `p.${state.peek.view.page}` : null}>
                    {[...state.peek.view.previousSpans.map((span) => span.text), state.peek.view.text, ...state.peek.view.nextSpans.map((span) => span.text)].map((text, index) => (
                      <p key={index} style={{ margin: "0 0 6px", fontWeight: index === state.peek!.view!.previousSpans.length ? 600 : 400 }}>{clip(text, 700)}</p>
                    ))}
                  </SourceVoice>
                ) : (
                  <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> opening the passage…</MeaningLabel>
                )}
              </div>
            ) : null}
            {ask.hits.length > 0 ? (
              <div style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 10, display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline" }}>
                  {ctl.settings?.compare ? (
                    ctl.canCompare ? (
                      <button type="button" onClick={() => void ctl.compare()} style={linkStyle}>{LIBRARY_COPY.compare} ({state.pinned.length})</button>
                    ) : (
                      <MeaningLabel style={{ fontSize: 10 }}>{LIBRARY_COPY.compareNeeds}</MeaningLabel>
                    )
                  ) : null}
                  <button type="button" onClick={() => void ctl.practice()} style={linkStyle}>{LIBRARY_COPY.practice} ▸</button>
                </div>
                <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>↑↓ move · space peek · p pin · o open · c compare pinned · ctrl+↵ ask the tutor about pinned</span>
                {state.compare.phase !== "idle" ? (
                  <ModelActionState
                    phase={state.compare.phase}
                    verb={LIBRARY_COPY.comparing}
                    failure={state.compare.failure ?? undefined}
                    kept="Your pins are kept."
                    capRoute="comparison"
                    fallback="Reading the passages"
                    onRetry={() => void ctl.compare()}
                  >
                    {state.compare.value ? <CompareTable table={state.compare.value} /> : null}
                  </ModelActionState>
                ) : null}
                {state.pinned.length > 0 ? (
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      void ctl.askTutor(question);
                    }}
                    style={{ display: "flex", flexDirection: "column", gap: 6 }}
                  >
                    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <span style={headStyle}>{LIBRARY_COPY.askTutor} ({state.pinned.length})</span>
                      <input
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        placeholder={LIBRARY_COPY.tutorPlaceholder}
                        aria-label="your question for the tutor"
                        style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 8px" }}
                      />
                    </label>
                    <MeaningLabel style={{ fontSize: 10 }}>
                      answers only from {state.pinned.length === 1 ? "this passage" : `these ${state.pinned.length} passages`} · ↵ ask
                    </MeaningLabel>
                  </form>
                ) : null}
                {state.tutor.phase !== "idle" ? (
                  <ModelActionState
                    phase={state.tutor.phase}
                    verb={LIBRARY_COPY.tutorWriting}
                    failure={state.tutor.failure ?? undefined}
                    kept="Your question is kept."
                    capRoute="tutor"
                    onRetry={() => void ctl.askTutor(question)}
                  >
                    {state.tutor.value ? (
                      <ModelVoice first note={state.tutor.value.label}>
                        <MarkdownMath value={state.tutor.value.answerMd ?? ""} />
                        {state.tutor.value.citations.length ? (
                          <span style={{ display: "block", color: COLOR.textDim, fontSize: 11 }}>
                            cites: {state.tutor.value.citations.map((citation) => citation.label).join(" · ")}
                          </span>
                        ) : null}
                      </ModelVoice>
                    ) : null}
                  </ModelActionState>
                ) : null}
                {state.practice.phase !== "idle" ? (
                  <ModelActionState
                    phase={state.practice.phase}
                    verb={LIBRARY_COPY.practiceLooking}
                    failure={state.practice.failure ?? undefined}
                    onRetry={() => void ctl.practice()}
                  >
                    {state.practice.value && state.practice.value.items.length ? (
                      <ul aria-label="practice for this question" style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 6 }}>
                        {state.practice.value.items.map((item) => (
                          <li key={item.practiceItemId} style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                            {clip(item.prompt, 160)}
                            {item.learningObjectTitle ? <span style={{ color: COLOR.textDim }}> · {item.learningObjectTitle}</span> : null}
                            {onPracticePick ? (
                              <>
                                {" "}
                                <button type="button" onClick={() => onPracticePick(item, state.practice.value?.proposalId ?? null)} style={linkStyle}>
                                  practice this ▸
                                </button>
                              </>
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
          </div>
        ) : null}
      </ModelActionState>
    </section>
  );
}
