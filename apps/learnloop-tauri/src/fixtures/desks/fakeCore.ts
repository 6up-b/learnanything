// Stands in for @tauri-apps/api/core in the desks' visual harness (vite.desks.config.mjs): every call
// is answered from the synthetic workspace, and recorded, so the harness can read what each window
// asked for (reading activity above all). Nothing leaves the page.
import type { DeskApplyInput } from "../../api/dto";
import { FIXTURE_GUIDES, FIXTURE_LIBRARY, FIXTURE_VIEWS, FIXTURE_WATCH } from "./sources";
import { FixtureDeskServer } from "./workspace";
import { FixtureCompanion } from "./companion";

export type InvokeArgs = Record<string, unknown>;

export interface HarnessCall {
  command: string;
  input: Record<string, unknown>;
  at: number;
}

const server = new FixtureDeskServer();
const companion = new FixtureCompanion();
const calls: HarnessCall[] = [];

declare global {
  interface Window {
    __deskHarness?: { calls: HarnessCall[]; server: FixtureDeskServer; companion: FixtureCompanion };
  }
}
window.__deskHarness = { calls, server, companion };

function viewFor(id: string) {
  return FIXTURE_VIEWS[id] ?? Object.values(FIXTURE_VIEWS).find((view) => view.extractionId === id) ?? null;
}

const CONTRACT = {
  version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
  answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
  exposureOnCommit: "none", inquiryEnabled: true, readingPaths: { enabled: true, depths: [] },
};

function answer(command: string, input: Record<string, unknown>): unknown {
  switch (command) {
    case "desk_state":
      return server.state();
    case "desk_apply":
      return server.apply(input as unknown as DeskApplyInput);
    case "get_source_library":
      return { version: 1, sources: FIXTURE_LIBRARY };
    case "reader_prompt_contract":
      return CONTRACT;
    case "reader_render_view": {
      const view = viewFor(String(input.extractionId));
      if (!view) throw { code: "not_found", message: "no such reading in the fixture", retryable: false };
      return view;
    }
    case "reader_guide_plan": {
      const guide = FIXTURE_GUIDES[String(input.extractionId)];
      const view = viewFor(String(input.extractionId));
      return guide ?? { sourceId: view?.sourceId ?? "", extractionId: String(input.extractionId), personalized: false, selectionBasis: "fixture", goalContext: null, sections: [] };
    }
    case "reader_get_progress":
      return { extractionId: String(input.extractionId), sections: [] };
    case "reader_pdf_view":
      return { available: false };
    case "reader_watch_plan": {
      const plan = FIXTURE_WATCH[String(input.sourceId)];
      if (!plan) throw { code: "not_found", message: "no video", retryable: false };
      return plan;
    }
    case "reader_source_annotations":
      return { annotations: [] };
    case "reader_ask_history":
      return { exchanges: [] };
    case "reader_drain_outbox":
      return { drained: [], failed: [] };
    case "reader_log_activity":
      return { recorded: Array.isArray(input.events) ? input.events.length : 0 };
    case "reader_note_reading_progress":
    case "reader_mark_section_progress":
      return null;
    case "reader_reading_path":
      return { extractionId: String(input.extractionId), status: "ask_depth", depth: null, depths: [], goal: null, sections: [], next: null };
    case "curriculum_guide_slice":
      // The fixture vault has curriculum off: the Guide shows its reading-path card, as a vault without it does.
      throw { code: "curriculum_disabled", message: "curriculum is off in the fixture", retryable: false };
    case "companion_ask":
      return companion.ask(input as unknown as Parameters<FixtureCompanion["ask"]>[0]);
    case "companion_ask_job":
      return companion.read(String(input.requestId));
    case "companion_ask_cancel":
      return companion.cancel(String(input.requestId));
    case "companion_history":
      return companion.history(input as { query?: string });
    case "search_everything":
      return companion.search(input as { query: string });
    case "search_job":
      return companion.searchJob(String(input.jobId));
    default:
      throw { code: "not_in_fixture", message: `${command} is not part of the desks' fixture`, retryable: false };
  }
}

export async function invoke<T>(command: string, args: InvokeArgs = {}): Promise<T> {
  const input = (args.input as Record<string, unknown> | undefined) ?? args;
  calls.push({ command, input: JSON.parse(JSON.stringify(input ?? {})), at: Date.now() });
  return answer(command, input) as T;
}

export function convertFileSrc(filePath: string, protocol = "asset"): string {
  return `fixture://${protocol}/${encodeURIComponent(filePath)}`;
}
