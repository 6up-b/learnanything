// The desks' visual harness (spec §18.3): the real DeskShell and real windows over the synthetic
// workspace, in a browser page with no sidecar. desk-harness.html mounts it; vite.desks.config.mjs
// builds that page (its @tauri-apps/api/core answered by fakeCore.ts) and scripts/desk_harness/run.py
// drives it in headless Chromium.
import React, { useEffect, useState } from "react";
import type { LessonEntry } from "../../screens/LessonView";
import ReactDOM from "react-dom/client";
import { DeskShell, type DeskDebugHandle } from "../../screens/desks/DeskShell";
import { DIRECT_HUB, WindowScope, type WindowState } from "../../screens/desks/lifecycle";
import { SourceWindow } from "../../screens/desks/windows/SourceWindow";
import { PadStackWindow } from "../../screens/desks/pads/PadStackWindow";
import { PadsHostContext, PendingFigures, type PadsHost } from "../../screens/desks/pads/host";
import { DeskStore } from "../../screens/desks/store";
import { REAL_TIMERS } from "../../screens/desks/keys/router";
import { fixtureMathPad } from "./pads";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "./sources";
import { FixtureDeskServer } from "./workspace";
import "../../styles/app.css";
import "../../styles/palettes.css";

const errors: string[] = [];
declare global {
  interface Window {
    __deskHarnessErrors?: string[];
    __deskDebug?: DeskDebugHandle;
    /** `?lesson=1`: ask the desks for a lesson as the app does while they are its place (RD9a). */
    __deskLessonAsk?: (entry: LessonEntry) => void;
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

export function Harness({ search = window.location.search }: { search?: string }) {
  const params = new URLSearchParams(search);
  const preview = params.get("preview");
  if (preview === "preview" || preview === "active") return <PreviewCard state={preview} />;
  if (params.get("latex") === "1") return <LatexFixture />;
  return <HarnessShell lessonsOn={params.get("lesson") === "1"} />;
}

function HarnessShell({ lessonsOn }: { lessonsOn: boolean }) {
  // The app's way in while the desks are its place: each ask once, by its seq.
  const [request, setRequest] = useState<{ seq: number; entry: LessonEntry } | null>(null);
  useEffect(() => {
    if (!lessonsOn) return;
    window.__deskLessonAsk = (entry) => setRequest((now) => ({ seq: (now?.seq ?? 0) + 1, entry }));
  }, [lessonsOn]);
  return (
    <div style={{ position: "fixed", inset: 0, display: "flex" }}>
      <DeskShell
        vaultKey="desk-fixture"
        // `?lesson=1`: lessons are on (the Reader's Teach me opens a lesson window; RD9a).
        {...(lessonsOn ? { reader: { onTeachMe: () => undefined }, lessons: { request } } : {})}
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
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <Harness />
    </React.StrictMode>,
  );
}
