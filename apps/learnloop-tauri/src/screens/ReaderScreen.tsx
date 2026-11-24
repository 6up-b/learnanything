// The standalone Reader screen: the scoped source (screens/desks/source/ScopedSource.tsx) with the branches only this
// screen has (the list of books, the old header, the collapsed rail's handle and the key bar), as functions of the
// source's state. A source window mounts the same source without them. Step 2 of the Reader's retirement deletes this
// file with its standalone-only state.
import type { ComponentProps, ReactNode } from "react";
import { api } from "../api/client";
import { COLOR, Card, Dim, FONT_MONO, Faint, KeyBar, Meta, Pill, TermSelect } from "../components/term";
import { SecondaryButton } from "../components/goldenpath/shared";
import { youtubeVideoId } from "../components/sourceTail";
import { searchBasisLabel } from "./reader/searchBasis";
import { readerKeyBarKeys } from "./reader/readerKeys";
import { CompareKeepContext } from "./reader/compareKeepContext";
import { NotesContext } from "./reader/notesContext";
import { LibraryAnswer } from "./reader/LibraryAnswer";
import { clip, sectionWords } from "./reader/readerShared";
import { READER_MODE_OPTIONS, ScopedSource } from "./desks/source/ScopedSource";
import type { StandaloneCollapsedRail, StandaloneHeader, StandaloneKeyBar, StandaloneShell, StandaloneUnopened } from "./desks/source/types";

export function ReaderScreen(props: Omit<ComponentProps<typeof ScopedSource>, "standalone">) {
  return <ScopedSource {...props} standalone={STANDALONE} />;
}

function unopened({ render, opening, openingTitle, library, shelf, sidecarDown, enabled, librarySearch, setLibrarySearch, setSearchDeep, libraryCtl, searchBusy, searchResults, notesCtl, keptCtl, openSource, onCheckMe, pickLibraryPagePractice, exerciseProps, figureOffersOn, makeExplorable, searchError, contract, openFixture }: StandaloneUnopened): ReactNode {
  if (!render && opening && openingTitle) {
    return (
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>READER</span>
            <Meta>{openingTitle}</Meta>
          </div>
          <Faint style={{ fontSize: 12 }}>◐ Opening {openingTitle}…</Faint>
        </div>
      </div>
    );
  }

  // ── Source picker: the Reader's front door is the real library ──
  if (!render) {
    // Every book is listed and openable; one still being prepared opens on its
    // original (UX Phase 1) instead of hiding behind "still getting ready".
    const readySources = library ?? [];
    // The one shelf, when the shell provides it (spec K5): search stays here.
    const useShelf = Boolean(shelf) && !sidecarDown;
    return (
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>
              {useShelf ? "READER" : "READER · LIBRARY"}
            </span>
            {sidecarDown ? <Pill color="amber">offline</Pill> : null}
          </div>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
            {useShelf ? "Pick a book to read, or search them all." : "Pick up where you left off, or open something new."}
          </span>
        </div>
        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: useShelf ? "18px 0 0" : "18px 32px", display: "flex", flexDirection: "column", gap: 10, maxWidth: useShelf ? undefined : 720 }}>
          {enabled && !sidecarDown ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: useShelf ? "0 32px" : undefined, maxWidth: 720 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  value={librarySearch}
                  onChange={(e) => {
                    setLibrarySearch(e.target.value);
                    setSearchDeep(false);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      setLibrarySearch("");
                      setSearchDeep(false);
                    }
                    // RW4a: Shift+Enter asks your library (sources first); off, it is Enter.
                    if (e.key === "Enter" && e.shiftKey && libraryCtl.enabled && librarySearch.trim()) {
                      e.preventDefault();
                      // CA3: with compare from anywhere on, the ask box first reads named books.
                      void libraryCtl.askBox({ query: librarySearch.trim(), entry: "library_search", extractionId: null, spanIds: [], identity: null });
                      return;
                    }
                    if (e.key === "Enter") setSearchDeep(true);
                  }}
                  placeholder="search all sources…"
                  style={{ fontFamily: FONT_MONO, fontSize: 12, width: 280, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 10px" }}
                />
                {searchBusy ? <Faint style={{ fontSize: 11 }}>◐ searching…</Faint> : searchResults ? (
                  <Faint style={{ fontSize: 11 }}>
                    {searchResults.hits.length} hit{searchResults.hits.length === 1 ? "" : "s"} across {searchResults.searchedSources} source{searchResults.searchedSources === 1 ? "" : "s"}
                    {searchBasisLabel(searchResults)}
                  </Faint>
                ) : null}
              </div>
              {libraryCtl.enabled ? <Faint style={{ fontSize: 10 }}>↵ search by meaning · ⇧↵ ask your library</Faint> : null}
              {libraryCtl.open ? (
                // RW4d: keep and reopen work on the library page too (Codex review F3);
                // curriculum C2: so do the notes' your-take band (C2 Codex review F10).
                <NotesContext.Provider value={notesCtl.context}>
                <CompareKeepContext.Provider value={keptCtl.context}>
                <Card style={{ padding: 0 }}>
                  <LibraryAnswer
                    ctl={libraryCtl}
                    onOpenHit={(hit) => {
                      const card = (library ?? []).find((candidate) => candidate.sourceId === hit.sourceId);
                      if (card && opening === null) void openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
                    }}
                    onPracticePick={onCheckMe ? pickLibraryPagePractice : null}
                    onClose={libraryCtl.close}
                    exercises={exerciseProps}
                    onMakeExplorable={figureOffersOn ? (hit, offerRef) => makeExplorable(hit, "library", offerRef) : null}
                    onReword={libraryCtl.scopeOn ? (words) => { libraryCtl.close(); setLibrarySearch(words); } : null}
                  />
                </Card>
                </CompareKeepContext.Provider>
                </NotesContext.Provider>
              ) : null}
              {searchError ? (
                <div role="alert" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.red }}>
                  {searchError} Edit the search to retry.
                </div>
              ) : null}
              {searchResults && searchResults.hits.length > 0 ? (
                <div className="ll-scroll" style={{ maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
                  {searchResults.hits.map((hit) => {
                    const card = (library ?? []).find((c) => c.sourceId === hit.sourceId);
                    return (
                      <Card
                        key={`${hit.extractionId}/${hit.spanId}`}
                        onClick={() => {
                          if (card && opening === null) {
                            const receiptId = searchResults.retrievalReceiptId;
                            if (receiptId) {
                              // Local contextual retrieval P1: the open is a relevance signal (never blocks the open).
                              void api.readerRetrievalOpen({ receiptId, extractionId: hit.extractionId, spanId: hit.spanId }).catch(() => undefined);
                            }
                            void openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
                          }
                        }}
                        style={{ display: "flex", flexDirection: "column", gap: 4, cursor: card ? "pointer" : "default" }}
                      >
                        <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
                          <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink }}>{clip(hit.sourceTitle, 60)}</span>
                          {hit.section ? <Faint style={{ fontSize: 10 }}>· {clip(hit.section, 50)}</Faint> : null}
                          {hit.page !== null ? <Faint style={{ fontSize: 10 }}>· p.{hit.page}</Faint> : null}
                        </div>
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, lineHeight: 1.5 }}>{hit.snippet}</span>
                      </Card>
                    );
                  })}
                </div>
              ) : searchResults && !searchBusy ? (
                <Faint style={{ fontSize: 11 }}>no matches — this searches the text of every book that is ready.</Faint>
              ) : null}
            </div>
          ) : null}
          {contract !== null && !enabled && !sidecarDown ? (
            <Card style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", gap: 6 }}>
              <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
                the reader is disabled in this vault's config (new vaults have it on by default). Set <Dim>tutor_qa.reader_enabled = true</Dim>
                in learnloop.toml to read and annotate real sources; the demo chapter below works without it.
              </Faint>
            </Card>
          ) : null}
          {useShelf ? (
            shelf
          ) : library === null ? (
            <Faint style={{ fontSize: 12 }}>◐ loading source library…</Faint>
          ) : readySources.length === 0 ? (
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              {sidecarDown
                ? "the sidecar is unreachable — only the offline demo chapter is available."
                : "Nothing to read yet. Add a book, paper or video from the Library."}
            </Faint>
          ) : (
            readySources.map((card) => {
              const cardOpenable = enabled && card.readerEnabled !== false;
              const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null;
              return (
                <Card
                  key={card.sourceId}
                  onClick={() => {
                    if (cardOpenable && opening === null) void openSource(card);
                  }}
                  style={{ display: "flex", flexDirection: "column", gap: 4, cursor: cardOpenable ? "pointer" : "default", opacity: cardOpenable ? 1 : 0.55 }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }} title={card.title}>
                      {card.title}
                    </span>
                    {card.readerEnabled === false ? (
                      <Pill color="slate">reader off · set at ingest</Pill>
                    ) : (
                      <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2 }}>
                        {opening === card.sourceId ? "opening…" : isVideo ? "watch →" : "read →"}
                      </span>
                    )}
                  </div>
                  <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
                    {card.readiness === "ready" ? `${card.unitCount} sections` : card.statusLine?.text ?? "Getting this ready"}
                  </Faint>
                </Card>
              );
            })
          )}
          {/* The demo chapter is for when LearnLoop's background service is
              down, not a book on the main path (spec §7.3; usability round 1). */}
          {sidecarDown ? (
            <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10 }}>
              <SecondaryButton onClick={openFixture}>open demo chapter (fixture)</SecondaryButton>
              <Faint style={{ fontSize: 11 }}>offline demo — captures are not persisted.</Faint>
            </div>
          ) : null}
        </div>
        <KeyBar keys={[{ key: "click", label: "open source" }]} right={{ key: "^p", label: "palette" }} />
      </div>
    );
  }
  return null;
}

function header({ onOpenLibrary, backToLibrary, onOpenDesks, sourceTitle, offline, progress, pdfView, setSurface, surface, mode, changeMode, currentGuideSection, readingProgress, setSectionPromptsEnabled, sectionPromptsEnabled, boundaryChecksAvailable }: StandaloneHeader): ReactNode {
  return (
      <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>READER</span>
          <button
            type="button"
            onClick={onOpenLibrary ?? backToLibrary}
            style={{ background: "none", border: "none", padding: 0, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
          >
            ← Library
          </button>
          {onOpenDesks ? (
            <button
              type="button"
              onClick={onOpenDesks}
              title="the Reader's new workbench: desks of windows side by side"
              style={{ background: "none", border: "none", padding: 0, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
            >
              desks ▸
            </button>
          ) : null}
          <Meta>{sourceTitle ?? "Untitled source"}</Meta>
          {offline ? <Pill color="amber">offline demo</Pill> : null}
          {progress.placeApproximate && !offline ? (
            // Re-read safety: the saved place (or the search hit's passage)
            // was on an earlier reading whose words changed there.
            <Faint style={{ fontSize: 11 }}>
              {progress.placeApproximate === "found"
                ? "This book was read again: you're near the passage you found."
                : "This book was read again: you're near where you left off."}
            </Faint>
          ) : null}
          {pdfView && !offline ? (
            <span
              onClick={() => setSurface((s) => (s === "pdf" ? "text" : "pdf"))}
              style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
            >
              {surface === "pdf" ? "extracted text →" : "original pdf →"}
            </span>
          ) : null}
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <Faint style={{ fontSize: 11 }}>I want to</Faint>
            <TermSelect value={mode} options={READER_MODE_OPTIONS} onChange={changeMode} width={150} />
          </div>
        </div>
        <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
          {offline
            ? "offline demo — captures live only in this window and are not persisted."
            : "Select a passage to ask about it, mark it, or make your own practice."}
        </span>
        {!offline ? (
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <Faint style={{ fontSize: 11, flexShrink: 0 }}>
              {currentGuideSection ? sectionWords(currentGuideSection.label) : "reading"}
            </Faint>
            <div style={{ height: 3, flex: 1, maxWidth: 280, background: COLOR.border, overflow: "hidden" }} aria-label={`${Math.round(readingProgress * 100)}% through the book`}>
              <div style={{ height: "100%", width: `${Math.max(2, readingProgress * 100)}%`, background: COLOR.amber }} />
            </div>
            <Faint style={{ fontSize: 10 }}>{Math.round(readingProgress * 100)}%</Faint>
            <button
              type="button"
              onClick={() => setSectionPromptsEnabled((value) => !value)}
              aria-pressed={sectionPromptsEnabled}
              disabled={mode !== "anchor"}
              style={{ marginLeft: "auto", border: 0, background: "transparent", color: boundaryChecksAvailable ? COLOR.amberLink : COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 11, cursor: mode === "anchor" ? "pointer" : "default", padding: 0 }}
            >
              {mode !== "anchor" ? "quick checks while reading closely" : sectionPromptsEnabled ? "quick checks on" : "quick checks off"}
            </button>
          </div>
        ) : null}
      </div>
      );
}

function collapsedRail({ windowed, inquiry, railCollapsed, sbsPanes, working, comparing, sbsRailOverlay, setSbsRailOverlay, setRailCollapsed }: StandaloneCollapsedRail): ReactNode {
  return !windowed && ((inquiry && railCollapsed) || sbsPanes) && !working && !comparing && !sbsRailOverlay ? (
          <button
            type="button"
            onClick={() => (sbsPanes ? setSbsRailOverlay(true) : setRailCollapsed(false))}
            aria-label={"expand the rail (\\)"}
            title={"expand the rail (\\)"}
            style={{ width: 28, flexShrink: 0, border: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
          >
            ◂
          </button>
        ) : null;
}

function keyBar({ windowed, pdfSurfaceActive, inquiry, cueCtl, recapCtl, working, alsoOn, alsoAvailable, alsoHidden, comparing }: StandaloneKeyBar): ReactNode {
  return windowed ? null : <KeyBar
        keys={[
          // In plain words (UX Phase 1 re-test #9).
          ...readerKeyBarKeys(pdfSurfaceActive),
          // RW1a's Reader-wide keys (UX §3.5).
          ...(inquiry
            ? [
                { key: "alt+←", label: "back" },
                { key: "[ ]", label: "tabs" },
                { key: "\\", label: "rail" },
              ]
            : []),
          // RW3a: the margin marks, when any is drawn (UX §3.5).
          ...(cueCtl.placement.shown.length > 0 ? [{ key: "alt+↓", label: "next mark" }] : []),
          // RW6a: once the session has something to wrap up (UX W1).
          ...(recapCtl.wrapUpOffered && !working ? [{ key: "w", label: "wrap up" }] : []),
          // Reader CA5: while the Guide has its "also in your books" line.
          ...(inquiry && alsoOn && alsoAvailable && !alsoHidden && !working && !comparing ? [{ key: "x", label: "also in your books" }] : []),
        ]}
        right={{ key: "^p", label: "palette" }}
      />;
}

const STANDALONE: StandaloneShell = { unopened, header, collapsedRail, keyBar };
