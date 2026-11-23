// The desks' visual harness (spec §18.3): the real DeskShell and real windows over the synthetic
// workspace, in a browser page with no sidecar. desk-harness.html mounts it; vite.desks.config.mjs
// builds that page (its @tauri-apps/api/core answered by fakeCore.ts) and scripts/desk_harness/run.py
// drives it in headless Chromium.
import React from "react";
import ReactDOM from "react-dom/client";
import { DeskShell } from "../../screens/desks/DeskShell";
import { DIRECT_HUB, WindowScope, type WindowState } from "../../screens/desks/lifecycle";
import { SourceWindow } from "../../screens/desks/windows/SourceWindow";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "./sources";
import "../../styles/app.css";
import "../../styles/palettes.css";

const errors: string[] = [];
declare global {
  interface Window {
    __deskHarnessErrors?: string[];
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

export function Harness({ search = window.location.search }: { search?: string }) {
  const preview = new URLSearchParams(search).get("preview");
  if (preview === "preview" || preview === "active") return <PreviewCard state={preview} />;
  return (
    <div style={{ position: "fixed", inset: 0, display: "flex" }}>
      <DeskShell vaultKey="desk-fixture" onError={(message) => errors.push(message)} onLeave={() => errors.push("left for the old Reader")} />
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
