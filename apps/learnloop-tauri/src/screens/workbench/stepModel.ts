// Reader workbench RW2a: the step list as the learner sees it (spec §5.1,
// §5.7; UX §5.1-5.3). The server keeps every version (an append-only ledger);
// the screen keeps one local list, keyed by each step's first row, and a write
// queue sends each change with its own idempotency key. Pure functions only.
import type { WorkbenchEntry, WorkbenchOrigin, WorkbenchStepDto, WorkbenchStepKind, WorkbenchStepVersionDto } from "../../api/dto";

/** Entries that open WITH the book (UX S7, D9; learnloop.reader.workbench). */
export const BOOK_OPEN_ENTRIES: ReadonlySet<WorkbenchEntry> = new Set<WorkbenchEntry>(["work_through", "resume", "path_exercise"]);

export function defaultBookVisible(entry: WorkbenchEntry, origin: WorkbenchOrigin): boolean {
  return origin === "reader" && BOOK_OPEN_ENTRIES.has(entry);
}

export interface LocalStep {
  /** Stable for the step's life on this screen (its chain id once saved). */
  key: string;
  /** The newest saved version's row id; null until its add lands. */
  serverId: string | null;
  /** RW2b: the step's stable id on the server (its first row), once saved:
   *  what checks and hints name. */
  chainId?: string | null;
  kind: WorkbenchStepKind;
  body: string;
  /** Deleted on this visit: shown as "deleted · undo" until the learner leaves. */
  deleted: boolean;
  versions: WorkbenchStepVersionDto[];
}

export function fromServer(steps: readonly WorkbenchStepDto[]): LocalStep[] {
  return [...steps]
    .sort((a, b) => a.ordinal - b.ordinal)
    .map((step) => ({ key: step.chainId, serverId: step.stepId, chainId: step.chainId, kind: step.kind, body: step.bodyMd, deleted: step.deleted, versions: step.versions }));
}

/** A new step right after `afterKey` (Enter at a step's end), or at the end. */
export function insertAfter(steps: readonly LocalStep[], afterKey: string | null, step: { key: string; kind: WorkbenchStepKind; body?: string }): LocalStep[] {
  const entry: LocalStep = { key: step.key, serverId: null, kind: step.kind, body: step.body ?? "", deleted: false, versions: [] };
  const index = afterKey === null ? -1 : steps.findIndex((existing) => existing.key === afterKey);
  if (index < 0) return [...steps, entry];
  return [...steps.slice(0, index + 1), entry, ...steps.slice(index + 1)];
}

export function updateLocal(steps: readonly LocalStep[], key: string, patch: Partial<LocalStep>): LocalStep[] {
  return steps.map((step) => (step.key === key ? { ...step, ...patch } : step));
}

export function deleteLocal(steps: readonly LocalStep[], key: string): LocalStep[] {
  return updateLocal(steps, key, { deleted: true });
}

export function restoreLocal(steps: readonly LocalStep[], key: string): LocalStep[] {
  return updateLocal(steps, key, { deleted: false });
}

export function liveSteps(steps: readonly LocalStep[]): LocalStep[] {
  return steps.filter((step) => !step.deleted);
}

/** RW2b: the step's id on the server (checks and hints name it), or null. */
export function stepChain(step: LocalStep): string | null {
  return step.chainId ?? (step.serverId !== null && step.key === step.serverId ? step.key : null);
}

/** "Exercise 5.14" when the stem names its exercise, else "this problem". */
export function problemTitle(stem: string): string {
  const match = /^\s*(Exercise|Problem|Question|Example)\s+([0-9]+(?:\.[0-9]+)*[a-z]?)/i.exec(stem);
  return match ? `${match[1][0].toUpperCase()}${match[1].slice(1).toLowerCase()} ${match[2]}` : "this problem";
}

export type SaveState = "saved" | "saving" | "retrying" | "offline" | "rejected";

/** The save line's state: "rejected" carries why the server refused a write. */
export interface SaveStatus {
  state: SaveState;
  savedAt: string | null;
  reason?: string | null;
}

/** Every fixed line the workbench shows. Never "error" (UX §5.3, U6). */
export const WORKBENCH_COPY = {
  savedJustNow: "saved · just now",
  retrying: "not saved yet — retrying · your text is safe in this window",
  offline: "sidecar unreachable — keeping your steps here; they'll save when it's back",
  rejected: "not saved — your text is still here; shorten or delete the step to save the rest",
  saving: "saving…",
  setup: "setting up checks and hints for this exercise…",
  waitsForSetup: "available once setup finishes",
  stuckPrompt: "Write what you can, or what's confusing you. Being stuck here is useful information.",
  bookOpen: "with the book open — practice beside the book (counts as one hint)",
  bookHidden: "without it — your own attempt; you can open it any time",
  bookHiddenCover: "The book is hidden so this can count as your own attempt.",
  bookHiddenHow: "Show it any time (Ctrl+Shift+B) — it'll count as one hint from then on.",
  abandoned: "abandoned · your steps are kept ·",
  kept: "Your steps are kept.",
  partsAsk: "This selection set up more than one problem. Which one are you working?",
  setupDidNotFinish: "Setup didn't finish.",
  leftKept: "kept — resume any time",
  // Round 4 F8: while Leave or "answer box instead" is under way.
  leaving: "leaving…",
  leavingPaused: "leaving… · editing is paused until your steps are checked",
} as const;

export function savedLabel(status: SaveStatus, nowMs: number = Date.now()): string {
  if (status.state === "rejected") return status.reason ? `not saved (${status.reason}) — your text is still here` : WORKBENCH_COPY.rejected;
  if (status.state === "retrying") return WORKBENCH_COPY.retrying;
  if (status.state === "offline") return WORKBENCH_COPY.offline;
  if (status.state === "saving") return WORKBENCH_COPY.saving;
  const at = status.savedAt ? Date.parse(status.savedAt) : Number.NaN;
  if (!Number.isFinite(at)) return "saved";
  const minutes = Math.floor((nowMs - at) / 60000);
  return minutes < 1 ? WORKBENCH_COPY.savedJustNow : `saved · ${minutes} min ago`;
}
