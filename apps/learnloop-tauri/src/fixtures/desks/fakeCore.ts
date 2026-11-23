// Stands in for @tauri-apps/api/core in the desks' visual harness (vite.desks.config.mjs): every call
// is answered from the synthetic workspace, and recorded, so the harness can read what each window
// asked for (reading activity above all). Nothing leaves the page.
import type { DeskApplyInput, DeskStateDto, PadViewDto } from "../../api/dto";
import { FIXTURE_INK_PAD, fixtureInkOwners, fixtureInkPad, fixturePads } from "./pads";
import { FIXTURE_GUIDES, FIXTURE_LIBRARY, FIXTURE_VIEWS, FIXTURE_WATCH } from "./sources";
import { FixtureDeskServer, fixtureDeskState } from "./workspace";
import { FixtureCompanion } from "./companion";
import { FixtureGoal } from "./goal";
import { FIXTURE_LESSON_ID, FixtureLessons, fixtureAdditionsPad } from "./lessons";
import { FixtureVideo } from "./video";

export type InvokeArgs = Record<string, unknown>;

export interface HarnessCall {
  command: string;
  input: Record<string, unknown>;
  at: number;
}

/** The harness's `?lesson=1` page: a finished Teacher lesson in the softmax desk's stack (RD9a), with its additions. */
const LESSON_PAGE = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("lesson") === "1";

/** The harness's workspace: the fixture's, with every desk's running pad in a stack (as the desks ensure it), so a
 * first visit to a desk changes no layout under the overview's transitions. */
function harnessDeskState(): DeskStateDto {
  const state = fixtureDeskState();
  const extra: Record<string, string> = { fx_desk_attention: "fx_pad_running_attention", fx_desk_backprop: "fx_pad_running_backprop" };
  for (const desk of state.desks) {
    const padId = extra[desk.deskId];
    if (!padId) continue;
    desk.slots.push({ slot: desk.slots.length, windows: [{ windowId: `fx_w_pads_${desk.deskId}`, pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId }] }] as never });
    state.runningPadIds.push(padId);
  }
  if (LESSON_PAGE) {
    const stack = state.desks.find((desk) => desk.deskId === "fx_desk_softmax")?.slots.flatMap((slot) => slot.windows).find((window) => window.windowId === "fx_w_pads");
    stack?.stack?.push({ kind: "lesson", lessonId: FIXTURE_LESSON_ID });
  }
  // `?inkpad=1`: the handwritten pad joins the softmax desk's stack (pen and ink, RD8a).
  if (INK_PAD_SHOWN) {
    for (const slot of state.desks[0].slots) {
      for (const window of slot.windows as Array<{ windowId: string; stack?: Array<{ kind: string; padId: string }> }>) {
        if (window.windowId === "fx_w_pads") window.stack?.push({ kind: "pad", padId: FIXTURE_INK_PAD });
      }
    }
  }
  return state;
}

const INK_PAD_SHOWN = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("inkpad") === "1";

function harnessPads(): PadViewDto[] {
  const at = "2026-11-23T09:00:00Z";
  const empty = (padId: string, deskId: string): PadViewDto => ({ version: 1, pad: { padId, kind: "running", title: "running", kept: false, homeDeskId: deskId, workbenchSessionId: null, lessonId: null, version: 1, createdAt: at, updatedAt: at }, blocks: [], anchors: [] });
  return [...fixturePads(), fixtureInkPad(), empty("fx_pad_running_attention", "fx_desk_attention"), empty("fx_pad_running_backprop", "fx_desk_backprop"),
    ...(LESSON_PAGE ? [fixtureAdditionsPad()] : [])];
}

const server = new FixtureDeskServer(harnessDeskState(), harnessPads());
const companion = new FixtureCompanion();
const goal = new FixtureGoal();
const lessons = new FixtureLessons();
// `?video=1`: the video's chapters already suggested, the second accepted (RD10), as the reference shows them.
const videoFixture = new FixtureVideo(typeof window !== "undefined" && new URLSearchParams(window.location.search).get("video") === "1");
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
    __deskHarness?: { calls: HarnessCall[]; server: FixtureDeskServer; companion: FixtureCompanion; goal: FixtureGoal; lessons: FixtureLessons; video: FixtureVideo };
  }
}
window.__deskHarness = { calls, server, companion, goal, lessons, video: videoFixture };

function viewFor(id: string) {
  return FIXTURE_VIEWS[id] ?? Object.values(FIXTURE_VIEWS).find((view) => view.extractionId === id) ?? null;
}

const CONTRACT = {
  version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
  answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
  exposureOnCommit: "none", inquiryEnabled: true, readingPaths: { enabled: true, depths: [] },
  // `?intent=1`: the Reader's intent box over a selection is on (its key claim against the desks' shortcuts).
  ...(typeof window !== "undefined" && new URLSearchParams(window.location.search).get("intent") === "1"
    ? { intent: {
      palette: [{ group: "understand", label: "understand", intention: "understand", actions: [
        { id: "ask", group: "understand", intention: "understand", label: "Ask", effect: { kind: "ask", answerMode: "answer_directly" }, model: true },
      ] }],
      notesPalette: [], speculative: false, speculateAfterMs: 0, timeoutSeconds: 30,
    } }
    : {}),
};

/** The pen's writes in this page (RD8a): annotations made by recognized marks and the ink saved with them. */
const pen: { annotations: Array<{ sourceId: string; annotation: { id: string }; version: { annotationType: string; learnerText: string } }>; inks: Record<string, unknown>[] } = { annotations: [], inks: [] };

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
      return { annotations: pen.annotations.filter((head) => head.sourceId === String(input.sourceId)).map(({ sourceId: _source, ...head }) => head) };
    // Pen and ink (RD8a): a recognized mark's annotation, its ink, and a reading refused as the default route
    // refuses it today (the plan's transport reads no images).
    case "reader_capture": {
      const annotationId = `fx_ann_${pen.annotations.length + 1}`;
      pen.annotations.push({ sourceId: String(input.sourceId), annotation: { id: annotationId }, version: { annotationType: input.action === "highlight" ? "highlight" : String(input.action), learnerText: String(input.learnerText ?? "") } });
      return { annotationId, outboxId: `fx_out_${annotationId}`, interactionEventId: `fx_ev_${annotationId}`, anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "captured" };
    }
    case "reader_delete_intent_annotation":
      pen.annotations = pen.annotations.filter((head) => head.annotation.id !== String(input.annotationId));
      return { eventId: `fx_del_${String(input.annotationId)}` };
    case "reader_edit_annotation":
      return { annotationId: String(input.annotationId), status: "exact" };
    case "ink_save":
      pen.inks.push(input);
      return server.applyInk(input as unknown as { clientId: string; seq: number; inkId: string });
    case "ink_erase": {
      const applied = server.applyInk({ clientId: String(input.clientId), seq: Number(input.seq), inkId: String(input.eraseId) });
      return { version: 1, appliedSeq: applied.appliedSeq, eraseId: String(input.eraseId), results: applied.results };
    }
    case "ink_list":
      return { version: 1, padId: input.padId ?? null, sourceId: input.sourceId ?? null, owners: input.padId === FIXTURE_INK_PAD ? fixtureInkOwners() : [] };
    case "ink_transcribe":
      return { version: 1, jobId: null, status: "failed", done: true, result: null,
        error: { code: "cannot_read_images", message: "The model routed to read handwriting cannot read images, so nothing was sent.", retryable: false, details: null } };
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
    case "passage_union_range": {
      // The pads' links on the reading's passages (every passage of the reading: the fixture's books are short).
      const extractionId = String(input.extractionId);
      const bySpan = new Map<string, Array<Record<string, unknown>>>();
      for (const pad of Object.values(server.pads)) {
        for (const anchor of pad.anchors) {
          if (anchor.extractionId !== extractionId) continue;
          const block = pad.blocks.find((each) => each.blockId === anchor.blockId);
          bySpan.set(anchor.spanId, [...(bySpan.get(anchor.spanId) ?? []), { blockId: anchor.blockId, padId: pad.pad.padId, kind: block?.kind ?? "text", provenance: block?.provenance ?? "learner", eventId: anchor.eventId, annotationId: anchor.annotationId, alias: "exact" }]);
        }
      }
      // A one-passage read names its passage's section (a carried question's, RD10), as the book's span ids say it.
      if (input.fromSpanId && input.fromSpanId === input.toSpanId && !bySpan.has(String(input.fromSpanId))) bySpan.set(String(input.fromSpanId), []);
      const sectionOf = (spanId: string) => /_(s\d+)_\d+$/.exec(spanId)?.[1] ?? null;
      return { version: 1, extractionId, sections: [], spans: [...bySpan.entries()].map(([spanId, padBlocks]) => ({ spanId, sectionId: sectionOf(spanId), annotations: [], padBlocks, exchanges: [], adjustments: [] })) };
    }
    case "passage_content": {
      // A passage of the fixture's books as the source has it (the render's block for the span).
      const extractionId = String(input.extractionId);
      const view = viewFor(extractionId);
      const spanId = String(input.fromSpanId ?? "");
      const block = view?.blocks.find((each) => each.spanId === spanId);
      return { version: 1, extractionId, sourceId: view?.sourceId ?? null, title: view ? FIXTURE_LIBRARY.find((card) => card.sourceId === view.sourceId)?.title ?? null : null, withheld: false,
        spans: block ? [{ spanId, text: block.markdown, page: 1, t0: null, t1: null, sectionId: null, sectionLabel: null, withheld: false }] : [] };
    }
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
    // The goal lens (RD6): one goal over the book and the note; the desks' default goal is its primary.
    case "goals_list":
      // The goal lens is the harness's `?goal=1` page; without it the desks have no goal, as before.
      return typeof window !== "undefined" && new URLSearchParams(window.location.search).get("goal") === "1" ? goal.goals() : { version: 1, goals: [] };
    case "goal_band":
      return goal.band();
    case "goal_lens":
      return goal.lens(String(input.extractionId));
    case "goal_section_choice":
      return goal.sectionChoice(input as never);
    case "curriculum_path":
      return goal.band().path;
    case "curriculum_set_depth":
      return goal.setDepth(input.depth as never);
    case "curriculum_path_override":
      return goal.override(input as never);
    case "curriculum_set_scope":
    case "curriculum_scope_decide":
      return { status: "ready", created: null, scope: null };
    // Teacher lessons (RD9a): a finished lesson replayed by lesson.view; an opening makes a new one after a wait.
    case "lesson_turn":
      return lessons.turn(input as never);
    case "lesson_view":
      return lessons.view(input as { lessonId: string });
    case "lesson_list":
      return lessons.list(input as { lessonIds?: string[] });
    case "lesson_activity":
      return { recorded: 0, enabled: false };
    // Follow-along and the suggested chapters (RD10).
    case "reader_follow_along":
      return videoFixture.follow(input as never);
    case "chapters_list":
      return videoFixture.list(input as never);
    case "chapters_suggest":
      return videoFixture.suggest(input as never);
    case "chapters_job":
      return videoFixture.job(input as never);
    case "chapters_cancel":
      return videoFixture.cancel(input as never);
    case "chapters_decide":
      return videoFixture.decide(input as never);
    case "reader_correspondents":
      return videoFixture.correspondents(input as never);
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
