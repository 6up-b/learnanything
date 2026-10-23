// UX Phase 2: the shell (docs/specs/ux_learnloop_v1.md §5, §7.7, §10 2.1–2.5).
//
// The four places a learner goes (Today, Library, Reader, Progress) over the
// shell's existing tabs, the Under-the-hood tools, the per-machine memory of
// the last place, and the kill switch `[ui] shell` ("simple" by default,
// "classic" keeps the ten-tab shell exactly; Q17).
//
// Display and navigation only: nothing here is read by grading, scheduling,
// evidence, projections or replay. The tabs stay the shell's state; a place
// is a view over them, so every existing `setTab("ingest")` keeps working and
// lands under the hood in the simple shell.
import type { TopTab } from "../components/ui";
import { SHOW_GOLDEN_PATH } from "../components/ui";
import { algoConfig } from "./algoConfig";

export type ShellMode = "simple" | "classic";

/** The shell the sidecar named (the default is simple; only "classic" turns it off). */
export function shellMode(): ShellMode {
  return algoConfig().shell;
}

/** Whether the simple shell is on: the one predicate the screens that carry a
 *  Phase 2 fix read, so "classic" leaves them as they were. */
export function simpleShell(): boolean {
  return shellMode() !== "classic";
}

// ── Places ──────────────────────────────────────────────────────────────

export type Place = "today" | "library" | "reader" | "progress";

export const PLACES: ReadonlyArray<{ id: Place; label: string; key: string }> = [
  { id: "today", label: "Today", key: "1" },
  { id: "library", label: "Library", key: "2" },
  { id: "reader", label: "Reader", key: "3" },
  { id: "progress", label: "Progress", key: "4" }
];

const UNDER_THE_HOOD_TABS: ReadonlySet<TopTab> = new Set<TopTab>(["ingest", "proposals", "registry", "maintain", "underhood", "golden"]);

/** The place a tab belongs to; the demoted tabs are under the hood. */
export function placeOfTab(tab: TopTab): Place | "underhood" | null {
  if (tab === "start" || tab === "today") return "today";
  if (tab === "library") return "library";
  if (tab === "reader") return "reader";
  if (tab === "graph") return "progress";
  if (UNDER_THE_HOOD_TABS.has(tab)) return "underhood";
  return null;
}

/** Where a place opens. Today is Start while no session is open (its Begin
 *  starts one) and Today once one is; Phase 3 merges the two. Progress is
 *  today's Graph screen, unchanged until Phase 5 reshapes it. */
export function tabForPlace(place: Place, hasSession: boolean): TopTab {
  if (place === "today") return hasSession ? "today" : "start";
  if (place === "progress") return "graph";
  return place;
}

// ── Under the hood (§5.2) ───────────────────────────────────────────────

export type UthToolId =
  | "ingest"
  | "proposals"
  | "registry"
  | "graph-editor"
  | "analyst"
  | "mistakes"
  | "calibration"
  | "maintain"
  | "data"
  | "files"
  | "inspector"
  | "golden"
  | "spend";

export interface UthTool {
  id: UthToolId;
  /** The plain title. */
  title: string;
  /** What it was called, in small type, for the owner's muscle memory. */
  was: string;
  /** Extra words the palette matches (old names, CLI words). */
  keywords: string[];
  /** Golden Path stays hidden unless SHOW_GOLDEN_PATH (visibleUthTools). */
  hidden?: boolean;
}

export const UTH_TOOLS: ReadonlyArray<UthTool> = [
  { id: "ingest", title: "Imports & builds", was: "Ingest", keywords: ["ingest", "import", "build", "outline", "collections", "exam seeding"] },
  { id: "proposals", title: "Study-map changes", was: "Proposals", keywords: ["proposals", "accept", "reject", "inbox"] },
  { id: "registry", title: "Subjects & topics", was: "Registry", keywords: ["registry", "subjects"] },
  { id: "graph-editor", title: "Concept graph editor", was: "Graph · edit", keywords: ["graph", "edit", "edges", "prerequisites"] },
  { id: "analyst", title: "Analyst views", was: "Graph · knowledge field", keywords: ["terrain", "strata", "well", "facets", "knowledge field"] },
  { id: "mistakes", title: "Mistake history", was: "Review · learnloop diff", keywords: ["review", "diff", "errors", "misconceptions"] },
  { id: "calibration", title: "Calibration", was: "calibrate", keywords: ["calibrate", "calibration", "probe"] },
  { id: "maintain", title: "System health", was: "Maintain", keywords: ["maintain", "health", "conflicts", "adjudicate", "backfill"] },
  { id: "data", title: "Data", was: "SQLite browser", keywords: ["sqlite", "database", "state.sqlite", "sql"] },
  { id: "files", title: "Files", was: "Library · Notes & files", keywords: ["files", "vault tree", "payload", "notes"] },
  { id: "inspector", title: "Inspector", was: "learnloop show", keywords: ["show", "inspect", "id"] },
  { id: "golden", title: "Golden path", was: "Golden Path", keywords: ["golden"], hidden: true },
  { id: "spend", title: "Spend & AI routes", was: "Settings · AI", keywords: ["spend", "routes", "ai status", "caps", "providers"] }
];

/** The tools the list shows: Golden Path only while SHOW_GOLDEN_PATH. Read at
 *  call time (ui.tsx and this module import each other). */
export function visibleUthTools(): UthTool[] {
  return UTH_TOOLS.filter((tool) => !tool.hidden || (tool.id === "golden" && SHOW_GOLDEN_PATH));
}

/** The tools that are the old tabs themselves: shown under the hood by tab. */
const TAB_TOOLS: ReadonlySet<UthToolId> = new Set<UthToolId>(["ingest", "proposals", "registry", "maintain", "golden"]);

export function isTabTool(tool: UthToolId): tool is "ingest" | "proposals" | "registry" | "maintain" | "golden" {
  return TAB_TOOLS.has(tool);
}

export function uthTool(id: UthToolId): UthTool {
  return UTH_TOOLS.find((tool) => tool.id === id) ?? UTH_TOOLS[0];
}

/** The tool a tab shows under the hood: an old tab is its own tool, the
 *  Under-the-hood tab shows the last one picked. */
export function uthToolOfTab(tab: TopTab, current: UthToolId): UthToolId {
  if (tab === "ingest" || tab === "proposals" || tab === "registry" || tab === "maintain" || tab === "golden") return tab;
  return current;
}

// ── Remember the last place (per machine, best effort) ─────────────────

const PLACE_KEY = "learnloop.place";
const TOOL_KEY = "learnloop.underhood.tool";
const BOOK_KEY_PREFIX = "learnloop.reader.book:";

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* storage may be blocked; the app opens on Today then */
  }
}

export function rememberPlace(place: Place | "underhood"): void {
  write(PLACE_KEY, place);
}

export function rememberedPlace(): Place | "underhood" | null {
  const value = read(PLACE_KEY);
  return value === "today" || value === "library" || value === "reader" || value === "progress" || value === "underhood" ? value : null;
}

export function rememberTool(tool: UthToolId): void {
  write(TOOL_KEY, tool);
}

export function rememberedTool(): UthToolId {
  const value = read(TOOL_KEY);
  const tool = visibleUthTools().find((candidate) => candidate.id === value);
  return tool?.id ?? "ingest";
}

/** The book open in the Reader, per library (a source id). */
export function rememberBook(vaultRoot: string, sourceId: string | null): void {
  write(BOOK_KEY_PREFIX + vaultRoot, sourceId ?? "");
}

export function rememberedBook(vaultRoot: string): string | null {
  const value = read(BOOK_KEY_PREFIX + vaultRoot);
  return value ? value : null;
}
