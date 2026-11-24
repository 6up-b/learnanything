// The whole app in jsdom with the real desks (spec §21.1's proofs from the app's side): App mounted as it is, the
// Reader place on the desks (its only surface), every desk and pad read and written through
// the app's api client to a fake sidecar, the books and their readings answered by the desks' fixture (fakeCore.ts,
// through realDesk.tsx), and the app's own reads (the vault, Today) answered here. A command no one answers stays
// pending, as a slow sidecar's would. A test file routes `@tauri-apps/api/core` to realDesk.tsx exactly as a
// real-desk test does, and stubs the screens it does not exercise.
import type { DeskStateDto, PadViewDto } from "../../api/dto";
import { answers, memoryStorage, resetSidecar, unknownCommands } from "./realDesk";
import { fixturePads } from "./pads";
import { FixtureDeskServer, fixtureDeskState } from "./workspace";

let vaults = 0;

export interface AppSidecar {
  /** The desks and pads the app reads and writes. */
  server: FixtureDeskServer;
  /** The machine's local storage. */
  storage: Storage;
  /** The vault's root, as the app's snapshot names it. */
  root: string;
}

/** The fake sidecar for one app: a vault (``config`` as its snapshot carries it), an empty Today, and the desks. */
export function appSidecar(options: { state?: DeskStateDto; pads?: PadViewDto[]; config?: Record<string, unknown>;
  session?: Record<string, unknown> | null } = {}): AppSidecar {
  resetSidecar();
  unknownCommands.pending = true;
  // A vault of its own per app: the desks keep a vault's store, open requests and pairs while the app runs.
  const root = `/fixture-vault-${++vaults}`;
  const server = new FixtureDeskServer(options.state ?? fixtureDeskState(), options.pads ?? fixturePads());
  answers.set("desk_state", () => server.state());
  // This app's desks are this vault's client: an earlier app's desk store (kept per vault while the module lives, as
  // the app keeps it) may still be sending its outbox, and its writes are not this vault's.
  const clientId = `client_app_${vaults}`;
  const mine = (input: Record<string, unknown>) => input.clientId === undefined || input.clientId === clientId;
  answers.set("desk_apply", (input) => (mine(input) ? server.apply(input as never) : new Promise(() => undefined)));
  answers.set("pad_get", (input) => server.padGet(String(input.padId)));
  answers.set("pad_apply", (input) => (mine(input) ? server.applyPad(input as never) : new Promise(() => undefined)));
  answers.set("load_vault", () => ({
    version: 1,
    vault: { root, subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "fixture" },
    health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
    config: options.config ?? {},
    activeSession: options.session ?? null,
    streak: { current: 1, activeToday: false, longest: 1 },
  }));
  answers.set("get_daily_plan", () => ({ version: 1, enabled: false, headlineEnabled: false, localDate: "2026-11-23", plan: null,
    streak: { current: 1, activeToday: false, longest: 1 } }));
  answers.set("get_start_summary", () => ({ version: 1, rememberedMinutes: 15, minutesSource: "last_session", minutesPresets: [10, 15, 25],
    minuteChoices: [10, 15, 25], streak: { current: 1, activeToday: false, longest: 1 } }));
  answers.set("get_today_queue", () => ({ version: 1, generatedAt: "2026-11-23T09:00:00Z", sessionId: null, sections: [], totalItems: 0 }));
  answers.set("get_today_headline", () => ({ version: 1, enabled: false }));
  answers.set("list_question_queue", () => ({ version: 1, questions: [], openCount: 0 }));
  answers.set("workbench_open_problems", () => ({ version: 1, problems: [] }));
  answers.set("get_inbox_summary", () => ({ count: 0, newCount: 0, captures: [], deletePending: [], deletePendingCount: 0, pinnedVault: null,
    vaultMismatch: false, enabled: true }));
  answers.set("get_review_counts", () => ({ version: 1, pendingProposals: 0, openConflicts: 0 }));
  const storage = memoryStorage();
  storage.setItem(`learnloop.desks.client.${root}`, clientId);
  return { server, storage, root };
}
