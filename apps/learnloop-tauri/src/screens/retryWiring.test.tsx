// UX Phase 2 fix round 3 (whole-stage verify 20261021-130232-Uk06Al, item 1):
// every screen that wires a read's failure to the shell's Try again hands over
// a self-contained retry. For each feed of each such screen, in each view
// that reads it, the retry issues the failed request again after the view
// changed and after the screen unmounted, rejects while the request fails,
// and resolves RETRY_RAN only once it ran and succeeded.
//
// Round 2 bound the hook's `refetch`. That resolved without a request once
// the view that enabled the query had changed (Strata's history after
// switching to Terrain, Well's decay pressure), so the shell dropped the error
// as if the retry had worked.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { clear } from "../api/queryCache";
import { expectRetryIssuesRequest, reportFor } from "../fixtures/retryRequests";

const TIMEOUT = { code: "sidecar_timeout", message: "The read timed out.", retryable: true };

const control = vi.hoisted(() => ({ failing: new Set<string>() }));

function failingUnless<T>(name: string, value: T) {
  return vi.fn(async () => {
    if (control.failing.has(name)) throw { ...TIMEOUT };
    return value;
  });
}

const SNAPSHOT = {
  version: 1,
  points: [],
  counts: { items: 0, learningObjects: 0, concepts: 0, facets: 0 },
  stress: 0,
  facetField: { points: [], graphNodes: [], edges: [], layoutVersion: "v1", stress: 0, layoutValid: true, layoutWarning: null, nextGap: null },
  itemTextNeighbors: {}
};

const api = vi.hoisted(() => ({}) as Record<string, Mock>);
vi.mock("../api/client", () => ({ api }));

import { KnowledgeMapView } from "./KnowledgeMapScreen";
import { LibraryScreen } from "./LibraryScreen";

beforeEach(() => {
  control.failing = new Set();
  api.getKnowledgeMap = failingUnless("map", SNAPSHOT);
  api.getKnowledgeMapHistory = failingUnless("history", { version: 1, attempts: [], learningObjects: [] });
  api.getDecayPressure = failingUnless("decay", { version: 1, pressure: null });
  api.getVaultTree = failingUnless("tree", { version: 1, root: "/vault", tree: [] });
  api.getProposals = failingUnless("proposals", { version: 1, batches: [] });
  api.listSourceSets = failingUnless("sets", { version: 1, sourceSets: [] });
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = () => undefined;
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
});

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function mountMap() {
  const onError = vi.fn();
  const view = render(<KnowledgeMapView onInspect={vi.fn()} onError={onError} />);
  await screen.findByRole("button", { name: "strata" });
  return { onError, view };
}

async function switchTo(mode: "terrain" | "well" | "strata") {
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: mode }));
  });
  await flush();
}

describe("Analyst views (KnowledgeMapView)", () => {
  it("Terrain: the map's retry reads the map again after the screen unmounted", async () => {
    control.failing.add("map");
    const onError = vi.fn();
    const { unmount } = render(<KnowledgeMapView onInspect={vi.fn()} onError={onError} />);
    await waitFor(() => expect(onError).toHaveBeenCalled());
    unmount();
    const report = reportFor(onError, TIMEOUT.message);
    await expectRetryIssuesRequest(report, api.getKnowledgeMap, "fails");
    control.failing.delete("map");
    await expectRetryIssuesRequest(report, api.getKnowledgeMap, "succeeds");
  });

  it("Strata: the history's retry reads it again after switching to Terrain (the verify's case)", async () => {
    control.failing.add("history");
    const { onError } = await mountMap();
    await switchTo("strata");
    await waitFor(() => expect(onError).toHaveBeenCalled());
    await switchTo("terrain");
    const report = reportFor(onError, TIMEOUT.message);
    await expectRetryIssuesRequest(report, api.getKnowledgeMapHistory, "fails");
    control.failing.delete("history");
    await expectRetryIssuesRequest(report, api.getKnowledgeMapHistory, "succeeds");
  });

  it("Well: the decay pressure's retry reads it again after switching away and unmounting", async () => {
    control.failing.add("decay");
    const { onError, view } = await mountMap();
    await switchTo("well");
    await waitFor(() => expect(onError).toHaveBeenCalled());
    await switchTo("terrain");
    view.unmount();
    const report = reportFor(onError, TIMEOUT.message);
    await expectRetryIssuesRequest(report, api.getDecayPressure, "fails");
    control.failing.delete("decay");
    await expectRetryIssuesRequest(report, api.getDecayPressure, "succeeds");
  });

  it("gives each feed its own identity", async () => {
    control.failing.add("history");
    control.failing.add("decay");
    const { onError } = await mountMap();
    await switchTo("strata");
    await switchTo("well");
    await waitFor(() => expect(onError.mock.calls.length).toBeGreaterThanOrEqual(2));
    const sources = new Set(onError.mock.calls.map((call) => (call[1] as { source?: string })?.source));
    expect(sources.size).toBeGreaterThanOrEqual(2);
  });
});

describe("Files (LibraryScreen)", () => {
  it.each([
    ["tree", "getVaultTree"],
    ["proposals", "getProposals"],
    ["sets", "listSourceSets"]
  ])("the %s read's retry reads it again after the screen unmounted", async (feed, request) => {
    control.failing.add(feed);
    const onError = vi.fn();
    const { unmount } = render(<LibraryScreen onError={onError} onInspect={vi.fn()} />);
    await waitFor(() => expect(onError).toHaveBeenCalled());
    unmount();
    const report = reportFor(onError, TIMEOUT.message);
    await expectRetryIssuesRequest(report, api[request], "fails");
    control.failing.delete(feed);
    await expectRetryIssuesRequest(report, api[request], "succeeds");
  });
});

// The screens above are every screen that hands the shell a read's retry:
// each goes through `useReportQueryError`. A new one must be added here.
it("covers every screen that wires a read's failure to Try again", () => {
  const src = join(__dirname, "..");
  const files: string[] = [];
  const walk = (dir: string, rel: string) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      const relPath = rel ? `${rel}/${name}` : name;
      if (statSync(path).isDirectory()) walk(path, relPath);
      else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name)) files.push(relPath);
    }
  };
  walk(src, "");
  const wiring = files.filter((file) => {
    const text = readFileSync(join(src, file), "utf8");
    return /useReportQueryError\(|retryReport\(\)/.test(text) && file !== "api/useCachedQuery.ts";
  });
  // UX Phase 3 landing: Today's full list (TodayPlace, fix round 1 F6) uses
  // the query's self-contained `retryReport()` for its own in-place Try again;
  // it hands no retry to the shell. Its tests (TodayPlace.test.tsx, "fix
  // round 1, F6") check that Try again reads the list again, after a failed
  // first read and after a failed refresh.
  expect(wiring.sort()).toEqual(["screens/KnowledgeMapScreen.tsx", "screens/LibraryScreen.tsx", "screens/today/TodayPlace.tsx"]);
  // Nothing hands the shell a retry built from a hook's refetch.
  const fromRefetch = files.filter((file) => /retry:\s*\(\)\s*=>\s*(?:void\s+)?\w*\.?refetch\(/.test(readFileSync(join(src, file), "utf8")));
  expect(fromRefetch).toEqual([]);
});
