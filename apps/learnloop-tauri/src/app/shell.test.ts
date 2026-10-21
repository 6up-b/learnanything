// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5.1, §10 2.1/2.5): the four
// places over the shell's tabs, Under the hood's tools, remembering the last
// place, and the kill switch read from the app snapshot.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setAlgoConfig } from "./algoConfig";
import {
  PLACES,
  UTH_TOOLS,
  cachedShell,
  placeOfTab,
  rememberBook,
  rememberPlace,
  rememberTool,
  rememberedBook,
  rememberedPlace,
  rememberedTool,
  shellMode,
  tabForPlace,
  uthToolOfTab
} from "./shell";

function stubStorage(): Map<string, string> {
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear()
  });
  return store;
}

beforeEach(() => {
  stubStorage();
});
afterEach(() => {
  vi.unstubAllGlobals();
  setAlgoConfig({});
});

describe("the switch", () => {
  it("defaults to the simple shell; only 'classic' turns it off", () => {
    setAlgoConfig({});
    expect(shellMode()).toBe("simple");
    setAlgoConfig({ ui: { shell: "fancy" } });
    expect(shellMode()).toBe("simple");
    setAlgoConfig({ ui: { shell: "classic" } });
    expect(shellMode()).toBe("classic");
  });

  it("remembers the last shell for the moment before the library loads", () => {
    setAlgoConfig({ ui: { shell: "classic" } });
    expect(cachedShell()).toBe("classic");
    setAlgoConfig({ ui: { shell: "simple" } });
    expect(cachedShell()).toBe("simple");
  });

  it("falls back to simple when storage throws", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      }
    });
    expect(cachedShell()).toBe("simple");
    expect(() => setAlgoConfig({ ui: { shell: "classic" } })).not.toThrow();
  });
});

describe("places over tabs", () => {
  it("names the four places in order, with Alt+1…4", () => {
    expect(PLACES.map((place) => [place.label, place.key])).toEqual([
      ["Today", "1"],
      ["Library", "2"],
      ["Reader", "3"],
      ["Progress", "4"]
    ]);
  });

  it("puts Start and Today under Today, Graph under Progress, the demoted tabs under the hood", () => {
    expect(placeOfTab("start")).toBe("today");
    expect(placeOfTab("today")).toBe("today");
    expect(placeOfTab("library")).toBe("library");
    expect(placeOfTab("reader")).toBe("reader");
    expect(placeOfTab("graph")).toBe("progress");
    for (const tab of ["ingest", "proposals", "registry", "maintain", "underhood", "golden"] as const) {
      expect(placeOfTab(tab)).toBe("underhood");
    }
  });

  it("opens Today on Start while no session is open, on Today once one is", () => {
    expect(tabForPlace("today", false)).toBe("start");
    expect(tabForPlace("today", true)).toBe("today");
    expect(tabForPlace("progress", false)).toBe("graph");
    expect(tabForPlace("library", true)).toBe("library");
    expect(tabForPlace("reader", true)).toBe("reader");
  });
});

describe("Under the hood", () => {
  it("lists every §5.2 tool under a plain title with its old name", () => {
    const visible = UTH_TOOLS.filter((tool) => !tool.hidden);
    expect(visible.map((tool) => [tool.title, tool.was])).toEqual([
      ["Imports & builds", "Ingest"],
      ["Study-map changes", "Proposals"],
      ["Subjects & topics", "Registry"],
      ["Concept graph editor", "Graph · edit"],
      ["Analyst views", "Graph · knowledge field"],
      ["Mistake history", "Review · learnloop diff"],
      ["Calibration", "calibrate"],
      ["System health", "Maintain"],
      ["Data", "SQLite browser"],
      ["Files", "Library · Notes & files"],
      ["Inspector", "learnloop show"],
      ["Spend & AI routes", "Settings · AI"]
    ]);
  });

  it("maps the old tabs to their tools", () => {
    expect(uthToolOfTab("ingest", "files")).toBe("ingest");
    expect(uthToolOfTab("proposals", "files")).toBe("proposals");
    expect(uthToolOfTab("registry", "files")).toBe("registry");
    expect(uthToolOfTab("maintain", "files")).toBe("maintain");
    expect(uthToolOfTab("underhood", "data")).toBe("data");
  });
});

describe("remember the last place", () => {
  it("round-trips the place, the tool and the open book (per library)", () => {
    expect(rememberedPlace()).toBeNull();
    rememberPlace("progress");
    expect(rememberedPlace()).toBe("progress");
    rememberPlace("underhood");
    expect(rememberedPlace()).toBe("underhood");
    rememberTool("data");
    expect(rememberedTool()).toBe("data");
    rememberBook("/vault/a", "src_1");
    expect(rememberedBook("/vault/a")).toBe("src_1");
    expect(rememberedBook("/vault/b")).toBeNull();
  });

  it("ignores junk and survives a storage that throws", () => {
    localStorage.setItem("learnloop.place", "nowhere");
    localStorage.setItem("learnloop.underhood.tool", "nothing");
    expect(rememberedPlace()).toBeNull();
    expect(rememberedTool()).toBe("ingest");
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      }
    });
    expect(() => rememberPlace("library")).not.toThrow();
    expect(rememberedPlace()).toBeNull();
    expect(rememberedBook("/vault/a")).toBeNull();
  });
});
