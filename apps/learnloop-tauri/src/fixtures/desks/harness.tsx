// The desks' visual harness (spec §18.3): the real DeskShell and real windows over the synthetic
// workspace, in a browser page with no sidecar. desk-harness.html mounts it; vite.desks.config.mjs
// builds that page (its @tauri-apps/api/core answered by fakeCore.ts) and scripts/desk_harness/run.py
// drives it in headless Chromium.
import React, { useEffect, useState } from "react";
import type { LessonEntry } from "../../screens/LessonView";
import ReactDOM from "react-dom/client";
import { DeskShell, type DeskDebugHandle, type DeskOpenRequest } from "../../screens/desks/DeskShell";
import { setAlgoConfig } from "../../app/algoConfig";
import { DIRECT_HUB, WindowScope, type WindowState } from "../../screens/desks/lifecycle";
import { SourceWindow } from "../../screens/desks/windows/SourceWindow";
import { PadStackWindow } from "../../screens/desks/pads/PadStackWindow";
import { PadsHostContext, PendingFigures, type PadsHost } from "../../screens/desks/pads/host";
import { DeskStore } from "../../screens/desks/store";
import { REAL_TIMERS } from "../../screens/desks/keys/router";
import { fixtureCellsPad, fixtureMathPad } from "./pads";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "./sources";
import { FixtureDeskServer } from "./workspace";
import { NotebookBridgeContext, NotebookFrame, type NotebookBridgeHost } from "../../screens/desks/notebook/NotebookFrame";
import type { BridgeMessage } from "../../screens/desks/notebook/bridge";
import "../../styles/app.css";
import "../../styles/palettes.css";

const errors: string[] = [];
declare global {
  interface Window {
    __problemSubmitted?: string;
    __deskHarnessErrors?: string[];
    __deskDebug?: DeskDebugHandle;
    /** `?lesson=1`: ask the desks for a lesson as the app does while they are its place (RD9a). */
    __deskLessonAsk?: (entry: LessonEntry) => void;
    /** The Reader place left, as for a check's practice screen and its feedback: the desks unmount. */
    __deskAway?: () => void;
    /** Back to the Reader place with the app's way back: the desks mount again and open (or focus) a book at a passage. */
    __deskReturn?: (sourceId: string, spanId: string | null) => void;
  }
}
window.__deskHarnessErrors = errors;

const noop = () => undefined;

/** One window as a card in a given lifecycle state (`?preview=preview|active`): the harness checks
 * that a preview logs no reading activity while the same window, active, does. */
function PreviewCard({ state }: { state: WindowState }) {
  const { book } = FIXTURE_SOURCES;
  return (
    <div data-preview-card="" style={{ position: "fixed", left: 40, top: 40, width: 640, height: 480, display: "flex", background: "#1a1a1c" }}>
      <WindowScope lifecycle={{ windowId: "preview", state }} hub={DIRECT_HUB}>
        <SourceWindow
          content={{ kind: "source", sourceId: book.sourceId, extractionId: book.extractionId }}
          card={FIXTURE_LIBRARY[0]}
          libraryLoaded
          startSpan={null}
          railHost={null}
          onStatus={noop}
          onJumpReady={noop}
          onMediaReady={noop}
          onError={(message) => errors.push(message)}
        />
      </WindowScope>
    </div>
  );
}

/** The display-math fixture (`?latex=1`, spec §13.4 rule 5): the math pad in pad windows of three widths, so
 * one equation fits, is scaled, and scrolls; the harness measures every equation's ink against its nearest
 * clipping ancestor, and hovers a mark for the card. */
export const LATEX_WIDTHS = [640, 430, 300] as const;

function LatexFixture() {
  const host = React.useMemo<PadsHost>(() => {
    const server = new FixtureDeskServer();
    server.pads.fx_pad_math = fixtureMathPad();
    const store = new DeskStore("latex", {
      state: async () => server.state(),
      apply: async (input) => server.apply(input),
      applyPad: async (input) => server.applyPad(input),
      padGet: async ({ padId }) => server.padGet(padId),
    }, REAL_TIMERS);
    const nothing = async () => ({}) as never;
    return {
      store, deskId: "fx_desk_softmax", mintId: (prefix) => `${prefix}_${Math.random().toString(36).slice(2)}`, today: () => "2026-11-23",
      api: { padProposals: async ({ padId }) => ({ version: 1, padId, proposals: [] }) as never, proposalLabel: nothing, padSubmitBlock: nothing, carriedCarry: nothing,
        requestTeachBack: nothing, passageUnionRange: nothing, authorPracticeItem: nothing, workbenchOpenProblems: async () => ({ problems: [] }),
        submitTeachBackTurn: nothing, getSession: nothing, passageContent: nothing },
      practiceSessionId: null, openPassage: noop, openSearch: noop, askAbout: noop, toast: noop, setView: noop, sourcePieces: () => [], register: noop, carry: noop,
      figures: new PendingFigures(), addToStack: noop,
    };
  }, []);
  return (
    <PadsHostContext.Provider value={host}>
      <div className="desk-shell" data-latex-fixture="" style={{ position: "fixed", inset: 0, display: "flex", gap: 16, padding: 16, background: "#0e0e10", alignItems: "stretch" }}>
        {LATEX_WIDTHS.map((width) => (
          <div key={width} data-latex-column={width} style={{ width, display: "flex", flexDirection: "column", minHeight: 0 }}>
            <WindowScope lifecycle={{ windowId: `latex-${width}`, state: "active" }} hub={DIRECT_HUB}>
              <PadStackWindow windowId={`latex-${width}`} stack={[{ kind: "pad", padId: "fx_pad_math" }]} view={{}} />
            </WindowScope>
          </div>
        ))}
      </div>
    </PadsHostContext.Provider>
  );
}

/** The pad cells fixture (`?padcells=1`, spec §11.5): a pad window holding the harness script's cells, run in a
 * real sandboxed session through the script's bridge (`window.__nbRpc`); `window.__padCellsMove()` moves the pad's
 * window to the other side of the page (it remounts, as a desk switch does). */
function PadCellsFixture() {
  const [side, setSide] = React.useState<"left" | "right">("left");
  React.useEffect(() => {
    window.__padCellsMove = () => setSide((now) => (now === "left" ? "right" : "left"));
  }, []);
  const host = React.useMemo<PadsHost>(() => {
    const server = new FixtureDeskServer();
    server.pads.fx_pad_cells = fixtureCellsPad(window.__notebookHarness?.padCells ?? []);
    const store = new DeskStore("padcells", {
      state: async () => server.state(),
      apply: async (input) => server.apply(input),
      applyPad: async (input) => server.applyPad(input),
      padGet: async ({ padId }) => server.padGet(padId),
    }, REAL_TIMERS);
    const nothing = async () => ({}) as never;
    window.__padCellsServer = server;
    return {
      store, deskId: "fx_desk_softmax", mintId: (prefix) => `${prefix}_${Math.random().toString(36).slice(2)}`, today: () => "2026-11-23",
      api: { padProposals: async ({ padId }) => ({ version: 1, padId, proposals: [] }) as never, proposalLabel: nothing, padSubmitBlock: nothing, carriedCarry: nothing,
        requestTeachBack: nothing, passageUnionRange: nothing, authorPracticeItem: nothing, workbenchOpenProblems: async () => ({ problems: [] }),
        submitTeachBackTurn: nothing, getSession: nothing, passageContent: nothing },
      practiceSessionId: null, openPassage: noop, openSearch: noop, askAbout: noop, toast: noop, setView: noop, sourcePieces: () => [], register: noop, carry: noop,
      figures: new PendingFigures(), addToStack: noop,
    };
  }, []);
  return (
    <PadsHostContext.Provider value={host}>
      <div className="desk-shell" data-padcells-fixture="" style={{ position: "fixed", inset: 0, display: "flex", gap: 16, padding: 16, background: "#0e0e10",
        justifyContent: side === "left" ? "flex-start" : "flex-end" }}>
        <div key={side} data-padcells-side={side} style={{ width: 560, display: "flex", flexDirection: "column", minHeight: 0 }}>
          <WindowScope lifecycle={{ windowId: `padcells-${side}`, state: "active" }} hub={DIRECT_HUB}>
            <PadStackWindow windowId={`padcells-${side}`} stack={[{ kind: "pad", padId: "fx_pad_cells" }]} view={{}} />
          </WindowScope>
        </div>
      </div>
    </PadsHostContext.Provider>
  );
}

declare global {
  interface Window {
    __padCellsMove?: () => void;
    __padCellsServer?: FixtureDeskServer;
    __notebookMessages?: BridgeMessage[];
    __notebookPause?: (paused: boolean) => void;
  }
}

/** The notebook fixture (`?notebook=1`, spec §11.2): a lesson's notebook frame where the mockup's Teacher lesson
 * state (`#tabs=distance,pad=3`, 1440 × 900) draws it, a pad window's paper round it, and a bridge host that
 * records every message it is handed (the frame has already refused the rest). `?nbstate=` forces a state;
 * `?nbpreview=1` shows the window as an overview card; `window.__notebookPause(true)` moves it offscreen. */
function NotebookFixture({ search }: { search: string }) {
  const params = new URLSearchParams(search);
  const [paused, setPaused] = React.useState(false);
  React.useEffect(() => {
    window.__notebookPause = setPaused;
  }, []);
  const state: WindowState = params.get("nbpreview") === "1" ? "preview" : paused ? "offscreen" : "active";
  const host = React.useMemo<NotebookBridgeHost>(() => {
    const messages: BridgeMessage[] = [];
    window.__notebookMessages = messages;
    return { onMessage: (message) => messages.push(message) };
  }, []);
  return (
    <div className="desk-shell" data-notebook-fixture="" style={{ position: "fixed", inset: 0, background: "#0a0a0b" }}>
      <div data-desk-window="" style={{ position: "absolute", left: 838, top: 46, width: 558, height: 820, background: "#1a1a1c", border: "1px solid #6b5534", boxSizing: "border-box" }}>
        <div className="desk-pane-head" style={{ height: 32, boxSizing: "border-box" }}>
          <span>›</span><span>Scratchpads</span>
        </div>
        <div data-notebook-paper="" style={{ position: "absolute", left: 7, top: 125, width: 542, height: 647, background: "#fdfdfc", border: "1px solid #2a2825", boxSizing: "border-box" }}>
          <NotebookBridgeContext.Provider value={host}>
            <WindowScope lifecycle={{ windowId: "fx_w_lesson", state }} hub={DIRECT_HUB}>
              <NotebookFrame owner="lesson:fx_lesson" path="notebooks/lesson.py" title="A slope you can see" style={{ position: "absolute", left: 0, top: 105, right: 0, bottom: 0, height: "auto" }} />
            </WindowScope>
          </NotebookBridgeContext.Provider>
        </div>
      </div>
    </div>
  );
}

export function Harness({ search = window.location.search }: { search?: string }) {
  const params = new URLSearchParams(search);
  const preview = params.get("preview");
  if (preview === "preview" || preview === "active") return <PreviewCard state={preview} />;
  if (params.get("latex") === "1") return <LatexFixture />;
  if (params.get("notebook") === "1") return <NotebookFixture search={search} />;
  if (params.get("padcells") === "1") return <PadCellsFixture />;
  return <HarnessShell lessonsOn={params.get("lesson") === "1"} problemOn={params.get("problem") === "1"} />;
}

function HarnessShell({ lessonsOn, problemOn }: { lessonsOn: boolean; problemOn: boolean }) {
  // `?problem=1` (RW2 on a problem pad, spec §15.2): the workbench and its help are on, and a submit's hand-off to
  // feedback is noted where the harness script reads it.
  if (problemOn) setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30, help: { enabled: true } }, hints: { adaptiveEnabled: true } });
  // The app's way in while the desks are its place: each ask once, by its seq.
  const [request, setRequest] = useState<{ seq: number; entry: LessonEntry } | null>(null);
  useEffect(() => {
    if (!lessonsOn) return;
    window.__deskLessonAsk = (entry) => setRequest((now) => ({ seq: (now?.seq ?? 0) + 1, entry }));
  }, [lessonsOn]);
  // The app's round trip away from the desks and back (a check or a problem, its feedback, "back to the book").
  const [shown, setShown] = useState(true);
  const [openRequest, setOpenRequest] = useState<DeskOpenRequest | null>(null);
  useEffect(() => {
    window.__deskAway = () => setShown(false);
    window.__deskReturn = (sourceId, spanId) => {
      setOpenRequest((now) => ({ seq: (now?.seq ?? 0) + 1, sourceId, spanId, reading: null }));
      setShown(true);
    };
  }, []);
  if (!shown) return <div data-desks-away="" style={{ position: "fixed", inset: 0, background: "#111" }} />;
  return (
    <div style={{ position: "fixed", inset: 0, display: "flex" }}>
      <DeskShell
        openRequest={openRequest}
        vaultKey="desk-fixture"
        // `?lesson=1`: lessons are on (the Reader's Teach me opens a lesson window; RD9a).
        {...(lessonsOn ? { reader: { onTeachMe: () => undefined }, lessons: { request } } : {})}
        {...(problemOn ? { reader: { workbench: { practiceSessionId: null, onSubmitted: (result) => { window.__problemSubmitted = result.attempt.attemptId; } } } } : {})}
        onError={(message) => errors.push(message)}
        onLeave={() => errors.push("left for the old Reader")}
        onDebugHandle={(handle) => {
          window.__deskDebug = handle;
        }}
      />
    </div>
  );
}

export function mountHarness(root: HTMLElement): void {
  // `?recap=1`: the recap card and Wrap up are on (RW6a's switches), with the fixture's last session on the book.
  if (new URLSearchParams(window.location.search).get("recap") === "1") setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <Harness />
    </React.StrictMode>,
  );
}
