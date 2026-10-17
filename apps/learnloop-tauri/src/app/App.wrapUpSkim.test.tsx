// RW6a Codex review round 2, F9 (docs/reviews/reader-rw6a-codex-review.md):
// the App shell itself, not a hook in isolation. Leaving the Reader for the
// library arms the one wrap-up line there; leaving it while skimming (the
// Reader reports skim through onSkimmingChange) arms nothing. The Reader, the
// library and the offer are stubs; the App's tab wiring is the real one.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

const stubs = vi.hoisted(() => ({ skim: false }));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));

vi.mock("../api/client", () => {
  const snapshot = {
    vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 1, practiceItems: 1 }, algorithmVersion: "mvp-0.27" },
    health: { ai: { ready: false, settingsReady: false, manualGrading: false, activeProvider: null }, codex: { ready: false } },
    config: { recap: { enabled: true, wrapUpEnabled: true } },
    activeSession: null,
    streak: null,
  };
  // Every other call stays pending: nothing else in the shell matters here.
  const api = new Proxy({ loadVault: vi.fn(async () => snapshot) } as Record<string, unknown>, {
    get: (target, name: string) => (name in target ? target[name] : () => new Promise(() => undefined)),
  });
  return { api };
});

vi.mock("../screens/ReaderScreen", async () => {
  const React = await import("react");
  return {
    ReaderScreen: ({ onSkimmingChange }: { onSkimmingChange?: (muted: boolean) => void }) => {
      React.useEffect(() => { onSkimmingChange?.(stubs.skim); }, [onSkimmingChange]);
      return <div data-testid="reader-stub">reader</div>;
    },
  };
});

vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: () => <div data-testid="library-stub">library</div> }));

vi.mock("../screens/reader/WrapUpOffer", () => ({
  WrapUpOffer: ({ armed }: { armed: boolean }) => <div data-testid="wrap-up-offer">{armed ? "armed" : "idle"}</div>,
}));

import { App } from "./App";

beforeEach(() => {
  stubs.skim = false;
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null, setItem: (key: string, value: string) => { store.set(key, value); },
    removeItem: (key: string) => { store.delete(key); }, clear: () => store.clear(),
  });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function leaveTheReaderForTheLibrary(): Promise<void> {
  render(<App />);
  await screen.findByRole("button", { name: /Reader/ });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Reader/ })); });
  await screen.findByTestId("reader-stub");
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Library/ })); });
  await screen.findByTestId("library-stub");
}

it("F9: leaving the Reader for the library offers the wrap-up there", async () => {
  await leaveTheReaderForTheLibrary();
  expect(screen.getByTestId("wrap-up-offer").textContent).toBe("armed");
});

it("F9: leaving the Reader while skimming offers no wrap-up where the learner lands", async () => {
  stubs.skim = true;
  await leaveTheReaderForTheLibrary();
  expect(screen.queryByTestId("wrap-up-offer")).toBeNull();
});
