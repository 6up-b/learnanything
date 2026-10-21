// UX Phase 2 fix round 4 (whole-stage verify 20261021-134216-8mdDfN item 2):
// classic is base by construction. These replay base's (c80c54cbb) error
// reporting in the classic shell: each screen reports ONE aggregated error,
// `onError(loadError.message)`, where loadError is the first failing feed in
// base's precedence (Library: tree ?? proposals ?? source sets; Knowledge map:
// map ?? history ?? decay). A later failure of a lower feed adds nothing; a
// failure of a higher feed is reported. The simple shell reports each feed.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { clear } from "../api/queryCache";
import { setAlgoConfig } from "../app/algoConfig";

const api = vi.hoisted(() => ({}) as Record<string, Mock>);
vi.mock("../api/client", () => ({ api }));

import { KnowledgeMapView } from "./KnowledgeMapScreen";
import { LibraryScreen } from "./LibraryScreen";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const failure = (message: string) => ({ code: "sidecar_timeout", message, retryable: true });

const SNAPSHOT = {
  version: 1,
  points: [],
  counts: { items: 0, learningObjects: 0, concepts: 0, facets: 0 },
  stress: 0,
  facetField: { points: [], graphNodes: [], edges: [], layoutVersion: "v1", stress: 0, layoutValid: true, layoutWarning: null, nextGap: null },
  itemTextNeighbors: {}
};

beforeEach(() => {
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = () => undefined;
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
  setAlgoConfig({});
});

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

function libraryFeeds() {
  const tree = deferred<unknown>();
  const proposals = deferred<unknown>();
  const sets = deferred<unknown>();
  api.getVaultTree = vi.fn(() => tree.promise);
  api.getProposals = vi.fn(() => proposals.promise);
  api.listSourceSets = vi.fn(() => sets.promise);
  return { tree, proposals, sets };
}

describe("classic: Library → Notes & files reports as base did", () => {
  beforeEach(() => setAlgoConfig({ ui: { shell: "classic" } }));

  it("tree fails, then proposals: one error, the tree's (base keeps A)", async () => {
    const feeds = libraryFeeds();
    const onError = vi.fn();
    render(<LibraryScreen onError={onError} onInspect={vi.fn()} />);
    await act(async () => feeds.tree.reject(failure("A: the tree failed.")));
    await flush();
    await act(async () => feeds.proposals.reject(failure("B: proposals failed.")));
    await flush();
    expect(onError.mock.calls).toEqual([["A: the tree failed."]]);
  });

  it("proposals fail, then the tree: both, the tree's last (tree precedence)", async () => {
    const feeds = libraryFeeds();
    const onError = vi.fn();
    render(<LibraryScreen onError={onError} onInspect={vi.fn()} />);
    await act(async () => feeds.proposals.reject(failure("B: proposals failed.")));
    await flush();
    await act(async () => feeds.sets.reject(failure("C: source sets failed.")));
    await flush();
    await act(async () => feeds.tree.reject(failure("A: the tree failed.")));
    await flush();
    expect(onError.mock.calls).toEqual([["B: proposals failed."], ["A: the tree failed."]]);
  });
});

describe("classic: the knowledge map reports as base did", () => {
  beforeEach(() => setAlgoConfig({ ui: { shell: "classic" } }));

  function mapFeeds() {
    const history = deferred<unknown>();
    const decay = deferred<unknown>();
    api.getKnowledgeMap = vi.fn(async () => SNAPSHOT);
    api.getKnowledgeMapHistory = vi.fn(() => history.promise);
    api.getDecayPressure = vi.fn(() => decay.promise);
    return { history, decay };
  }

  async function view(mode: "strata" | "well" | "terrain") {
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: mode }));
    });
    await flush();
  }

  it("history fails, then decay: one error, the history's", async () => {
    const feeds = mapFeeds();
    const onError = vi.fn();
    render(<KnowledgeMapView onInspect={vi.fn()} onError={onError} />);
    await screen.findByRole("button", { name: "strata" });
    await view("strata");
    await act(async () => feeds.history.reject(failure("B: history failed.")));
    await flush();
    await view("well");
    await act(async () => feeds.decay.reject(failure("C: decay failed.")));
    await flush();
    expect(onError.mock.calls).toEqual([["B: history failed."]]);
  });

  it("decay fails, then history: both, the history's last (history precedence)", async () => {
    const feeds = mapFeeds();
    const onError = vi.fn();
    render(<KnowledgeMapView onInspect={vi.fn()} onError={onError} />);
    await screen.findByRole("button", { name: "well" });
    await view("well");
    await act(async () => feeds.decay.reject(failure("C: decay failed.")));
    await flush();
    await view("strata");
    await act(async () => feeds.history.reject(failure("B: history failed.")));
    await flush();
    expect(onError.mock.calls).toEqual([["C: decay failed."], ["B: history failed."]]);
  });
});

describe("simple: each failing feed is its own error", () => {
  it("Library: the tree and the proposals each report, with a source and a retry", async () => {
    setAlgoConfig({});
    const feeds = libraryFeeds();
    const onError = vi.fn();
    render(<LibraryScreen onError={onError} onInspect={vi.fn()} />);
    await act(async () => feeds.tree.reject(failure("A: the tree failed.")));
    await act(async () => feeds.proposals.reject(failure("B: proposals failed.")));
    await waitFor(() => expect(onError).toHaveBeenCalledTimes(2));
    const sources = onError.mock.calls.map((call) => (call[1] as { source?: string }).source);
    expect(new Set(sources).size).toBe(2);
    expect(onError.mock.calls.every((call) => typeof (call[1] as { retry?: unknown }).retry === "function")).toBe(true);
  });
});
