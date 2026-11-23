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
// One carried question beside the book's third passage (project-authored).
const carried: Array<{ carriedId: string; text: string; carried: boolean; version: number; state: string; anchor: unknown; since: string }> = [
  { carriedId: "fx_carried1", text: "does the temperature trick work for any base?", originKind: "typed", originRef: null,
    anchor: { extraction_id: "fx_ext_softmax", span_id: "fx_ext_softmax_s1_3" }, deskId: "fx_desk_softmax", since: "2026-11-21T10:00:00Z",
    state: "carried", carried: true, version: 1, updatedAt: "2026-11-21T10:00:00Z" } as never,
];

/** The fixture's one proposal: beside the running pad's first block, a passage on the same idea. */
function fixtureProposals(padId: string) {
  if (padId !== "fx_pad_running") return { version: 1, padId, proposals: [] };
  return { version: 1, padId, proposals: [{
    proposalId: "fx_prop1", blockId: "fx_b_r1", blockVersionId: server.padGet(padId).blocks.find((block) => block.blockId === "fx_b_r1")?.headVersionId ?? "",
    foundBy: "passage_link", target: { content: { kind: "source", source_id: "fx_src_softmax", extraction_id: "fx_ext_softmax" }, target: { span_id: "fx_ext_softmax_s2_1" } },
    reasonMd: "Softmax, a short book p.2 takes this to the next step", quote: "The exponential is chosen because differences in scores become ratios of weights.",
    judgmentRef: null, createdAt: "2026-11-23T09:00:00Z", current: true, labels: [], shown: true,
  }] };
}

/** Today's pads on a desk, as pad.drain reads them. */
function fixtureDrain(deskId: string) {
  const pads = Object.values(server.pads).filter((pad) => pad.pad.homeDeskId === deskId);
  return { version: 1, deskId, day: new Date().toISOString().slice(0, 10), pads: pads.map((pad) => {
    const words = pad.blocks.map((block) => block.bodyMd.trim()).filter(Boolean);
    const last = words[words.length - 1] ?? "";
    return { padId: pad.pad.padId, kind: pad.pad.kind, title: pad.pad.title, kept: pad.pad.kept, version: pad.pad.version, firstLine: words[0] ?? "", lastLine: last, carryCandidate: last.endsWith("?") ? last : null, updatedAt: pad.pad.updatedAt };
  }) };
}
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
    case "pad_get":
      return server.padGet(String(input.padId));
    case "pad_apply":
      return server.applyPad(input as unknown as Parameters<FixtureDeskServer["applyPad"]>[0]);
    case "pad_proposals":
      return fixtureProposals(String(input.padId));
    case "proposal_label":
      return { version: 1, labelId: input.labelId, applied: true, at: new Date().toISOString() };
    case "pad_drain":
      return fixtureDrain(String(input.deskId));
    case "carried_list":
      return { version: 1, carried: carried.filter((question) => question.carried), shelfLimit: 3, cursor: null };
    case "carried_carry": {
      const question = { carriedId: String(input.carriedId), text: String(input.text), originKind: input.originKind, originRef: input.originRef ?? null,
        anchor: input.anchor ? { extraction_id: (input.anchor as { extractionId: string }).extractionId, span_id: (input.anchor as { spanId: string }).spanId } : null,
        deskId: input.deskId ?? null, since: new Date().toISOString(), state: "carried", carried: true, version: 1, updatedAt: new Date().toISOString() };
      carried.push(question as never);
      return { version: 1, carried: question, created: true };
    }
    case "carried_mark": {
      const question = carried.find((each) => each.carriedId === input.carriedId);
      if (question && input.event !== "surfaced" && input.event !== "ignored") {
        Object.assign(question, { state: input.event, carried: input.event === "not_now", version: question.version + 1 });
      }
      return { version: 1, carried: question, applied: true, conflict: false };
    }
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
