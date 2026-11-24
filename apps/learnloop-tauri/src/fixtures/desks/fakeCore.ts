// Stands in for @tauri-apps/api/core in the desks' visual harness (vite.desks.config.mjs): every call
// is answered from the synthetic workspace, and recorded, so the harness can read what each window
// asked for (reading activity above all). Nothing leaves the page.
import type { DeskApplyInput, DeskStateDto, LessonViewDto, PadViewDto } from "../../api/dto";
import { FIXTURE_INK_PAD, fixtureInkPad, fixturePads } from "./pads";
import { FIXTURE_GUIDES, FIXTURE_LIBRARY, FIXTURE_SOURCES, FIXTURE_VIEWS, FIXTURE_WATCH } from "./sources";
import { FixtureDeskServer, fixtureDeskState } from "./workspace";
import { FixtureCompanion } from "./companion";
import { FixtureGoal } from "./goal";
import { FIXTURE_LESSON_ID, FixtureLessons, fixtureAdditionsPad } from "./lessons";
import { FixtureVideo } from "./video";
import { fixtureFigure } from "./figures";
import { FixtureWorkbench } from "./workbench";

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
  // `?inkpad=1`: the handwritten pad joins the softmax desk's stack (pen and ink, RD8a).
  if (INK_PAD_SHOWN) {
    for (const slot of state.desks[0].slots) {
      for (const window of slot.windows as Array<{ windowId: string; stack?: Array<{ kind: string; padId: string }> }>) {
        if (window.windowId === "fx_w_pads") window.stack?.push({ kind: "pad", padId: FIXTURE_INK_PAD });
      }
    }
  }
  if (LESSON_PAGE) {
    const stack = state.desks.find((desk) => desk.deskId === "fx_desk_softmax")?.slots.flatMap((slot) => slot.windows).find((window) => window.windowId === "fx_w_pads");
    stack?.stack?.push({ kind: "lesson", lessonId: FIXTURE_LESSON_ID });
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

const PAIRS = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("pairs") === "1";

/** Side by side's fixture (`?pairs=1`): the book's section n (n = 1…6) is treated by the paper's section ((n-1) % 3 + 1),
 *  a judged correspondent opening at that section's first passage. */
function pairCorrespondents(input: { extractionId: string; sectionId: string }) {
  const { book, paper } = FIXTURE_SOURCES;
  const n = input.extractionId === book.extractionId ? Number(/_s(\d+)$/.exec(input.sectionId)?.[1] ?? NaN) : NaN;
  if (!Number.isFinite(n)) return { extractionId: input.extractionId, sectionId: input.sectionId, status: "none", learningObjects: [], search: null, checkableLearningObjectIds: [] };
  const section = `${paper.extractionId}_p${((n - 1) % 3) + 1}`;
  const view = FIXTURE_VIEWS[paper.sourceId];
  const first = view?.blocks.find((block) => block.spanId?.startsWith(`${section}_`))?.spanId ?? null;
  return {
    extractionId: input.extractionId, sectionId: input.sectionId, status: "judged", search: null, checkableLearningObjectIds: [],
    learningObjects: [{ learningObjectId: `lo_pair_${n}`, title: "a shared idea", sources: [{ sourceId: paper.sourceId, sourceTitle: "Attention as averaging (a note)", sections: [{
      extractionId: paper.extractionId, sectionId: section, title: `§${((n - 1) % 3) + 1}`, sourceId: paper.sourceId, sourceTitle: "Attention as averaging (a note)",
      read: false, jump: { extractionId: paper.extractionId, sectionId: section, spanId: first }, treatment: "develops", by: "judge" }] }] }],
  };
}

const CONTRACT = {
  version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
  answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
  exposureOnCommit: "none", inquiryEnabled: true, readingPaths: { enabled: true, depths: [] },
  // `?intent=1`: the Reader's intent box over a selection is on (its key claim against the desks' shortcuts).
  // `?problem=1` (RW2 on a problem pad, spec §15.2): the box also offers "work through this".
  ...(typeof window !== "undefined" && ["intent", "problem"].some((key) => new URLSearchParams(window.location.search).get(key) === "1")
    ? { intent: {
      palette: [{ group: "understand", label: "understand", intention: "understand", actions: [
        { id: "ask", group: "understand", intention: "understand", label: "Ask", effect: { kind: "ask", answerMode: "answer_directly" }, model: true },
      ] }, ...(new URLSearchParams(window.location.search).get("problem") === "1" ? [{ group: "apply", label: "Apply", intention: "apply", actions: [
        { id: "work_through", group: "apply", intention: "apply", label: "work through this", effect: { kind: "work_through" }, model: true },
      ] }] : [])],
      notesPalette: [], speculative: false, speculateAfterMs: 0, timeoutSeconds: 30,
    } }
    : {}),
  // `?pairs=1`: side by side is on (the book's sections each have a judged correspondent in the paper, below).
  ...(PAIRS ? { sideBySide: { enabled: true } } : {}),
};

// The context menu's promoted rows: a cheap row per passage (the learner's own question there, so rows differ by
// passage) and a judged job that adds a correspondent found by search, unchecked, on its second read.
/** RW2's workbench, faked for the problem pad's harness run. */
const workbench = new FixtureWorkbench();
if (typeof window !== "undefined") (window as unknown as { __fixtureWorkbench?: FixtureWorkbench }).__fixtureWorkbench = workbench;

const promotedJobs = new Map<string, { rows: Array<Record<string, unknown>>; reads: number; cancelled: boolean }>();
let promotedJobCount = 0;

function cheapRows(input: Record<string, unknown>): Array<Record<string, unknown>> {
  const spanId = typeof input.spanId === "string" ? input.spanId : null;
  if (!spanId) return [];
  return [{ rowId: `row_q_${spanId}`, kind: "question", glyph: "?", label: `your question on ${spanId}`, reason: "you asked the tutor about this passage",
    action: { verb: "open", ref: { kind: "thread", rootExchangeId: `q_${spanId}` } }, learnerAt: "2026-11-22T10:00:00Z", checked: true, judgeRank: 0, basis: "union", extra: {} }];
}

function emptyUnion(spanId: string): Record<string, unknown> {
  return { spanId, sectionId: null, annotations: [], padBlocks: [], exchanges: [], adjustments: [], gaps: [], passageLinks: [], figures: [], checksDue: [], notes: [],
    authoredQuestions: [], carried: [], exposure: { timesShown: 1, lastShownAt: null, withheld: false } };
}
/** The pen's writes in this page (RD8a): annotations made by recognized marks and the ink saved with them. */
const pen: { annotations: Array<{ sourceId: string; annotation: { id: string }; version: { annotationType: string; learnerText: string }; [placed: string]: unknown }>; inks: Record<string, unknown>[] } = { annotations: [], inks: [] };

function answer(command: string, input: Record<string, unknown>): unknown {
  const fromWorkbench = workbench.answer(command, input);
  if (fromWorkbench !== undefined) return fromWorkbench;
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
      // `?checks=1`: the book's first section has a question placed before it (project-authored).
      if (guide && typeof window !== "undefined" && new URLSearchParams(window.location.search).get("checks") === "1") {
        return { ...guide, sections: guide.sections.map((section, index) => (index === 0 && guide.extractionId === FIXTURE_SOURCES.book.extractionId ? {
          ...section, question: { placement: "owner_reviewed", practiceItemId: "fx_pi_weights", prompt: "Before you read: what should weights from scores add up to?",
            reason: "a question placed before this section", readingPhase: "before_section", placementEventId: "fx_pe_1", learningObjectId: "fx_lo_1" },
        } : section)) };
      }
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
      // Placed on the open reading as the sidecar places it: the selection's nodes, here.
      const nodes = ((input.rawSelection as { nodes?: Array<{ spanId: string; quote?: string; start?: number; end?: number }> } | undefined)?.nodes ?? []);
      const segments = nodes.map((node) => ({ spanId: node.spanId, codepointStart: node.start ?? 0, codepointEnd: node.end ?? 0, exactQuote: node.quote ?? "" }));
      pen.annotations.push({
        sourceId: String(input.sourceId), annotation: { id: annotationId },
        version: { annotationType: input.action === "highlight" ? "highlight" : input.action === "annotate" ? "interpretation" : String(input.action), learnerText: String(input.learnerText ?? "") },
        ...(segments.length ? {
          anchor: { status: "exact", extractionId: String(input.extractionId) },
          segments: segments.map((segment) => ({ spanId: segment.spanId, exactQuote: segment.exactQuote, geometryJson: null })),
          placement: { state: "here", flagSpanId: null, segments },
        } : {}),
      });
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
      return { version: 1, padId: input.padId ?? null, sourceId: input.sourceId ?? null, owners: input.padId ? server.inkFor(String(input.padId)) : [] };
    case "ink_transcribe":
      return { version: 1, jobId: null, status: "failed", done: true, result: null,
        error: { code: "unavailable", message: "Handwriting can't be read yet: text recognition (GLM-OCR) isn't set up.", retryable: true, details: null } };
    case "reader_ask_history":
      return { exchanges: [] };
    case "reader_drain_outbox":
      return { drained: [], failed: [] };
    // Show me (spec §13.1): a figure build answered at its first read, with the fixture figure.
    case "figure_request":
      return { jobId: "fx_figure_job", kind: "figure_build", askId: null, state: "pending", result: null, anchor: input.anchor ?? null };
    case "reader_figure_job":
      return { jobId: String(input.jobId), kind: "figure_build", askId: null, state: "done", result: { figure: fixtureFigure(`${FIXTURE_SOURCES.book.extractionId}_s1_1`), reused: false } };
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
    case "passage_promoted": {
      const rows = cheapRows(input);
      const jobId = typeof input.spanId === "string" ? `pj_${++promotedJobCount}` : null;
      if (jobId) promotedJobs.set(jobId, { rows, reads: 0, cancelled: false });
      return { version: 1, objectKey: JSON.stringify(input), rows, cap: 4, pendingJob: jobId ? { jobId } : null, paid: false };
    }
    case "passage_promoted_job": {
      const job = promotedJobs.get(String(input.jobId));
      if (!job) return { version: 1, jobId: input.jobId, status: "expired", done: true, rows: [], error: null };
      if (job.cancelled) return { version: 1, jobId: input.jobId, status: "cancelled", done: true, rows: [], error: null };
      job.reads += 1;
      if (job.reads < 2) return { version: 1, jobId: input.jobId, status: "running", done: false, rows: [], error: null };
      const paper = FIXTURE_SOURCES.paper;
      return { version: 1, jobId: input.jobId, status: "done", done: true, error: null, rows: [...job.rows, {
        rowId: `row_elsewhere_${input.jobId}`, kind: "correspondent", glyph: "§", label: "the same step in another source", reason: "treats the same step",
        action: { verb: "open", ref: { kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" }, target: {} },
        learnerAt: null, checked: false, judgeRank: 1, basis: "judged", extra: {},
      }] };
    }
    case "passage_promoted_cancel": {
      const job = promotedJobs.get(String(input.jobId));
      if (job) job.cancelled = true;
      return { version: 1, jobId: input.jobId, status: "cancelled", done: true, rows: [], error: null };
    }
    case "passage_knows": {
      const spanId = typeof input.spanId === "string" ? input.spanId : null;
      const extractionId = typeof input.extractionId === "string" ? input.extractionId : null;
      return { version: 1, objectKey: JSON.stringify(input), sourceIds: [], places: spanId && extractionId ? [{ extractionId, spanId, role: null, knows: emptyUnion(spanId) }] : [] };
    }
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
    case "notebook_open":
    case "notebook_status":
    case "notebook_run_cells":
    case "notebook_release":
      // The harness script answers these from a real sandboxed session when it exposes its bridge.
      if (window.__nbRpc) return window.__nbRpc(command, input);
      return notebookSession(command, input);
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
      return notebookLesson(lessons.view(input as { lessonId: string }));
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
      return PAIRS ? pairCorrespondents(input as never) : videoFixture.correspondents(input as never);
    // `?recap=1`: the book's last session, its recap card and its Wrap up (project-authored).
    case "reader_recap":
    case "reader_recap_event":
    case "reader_wrap_up":
      if (typeof window === "undefined" || new URLSearchParams(window.location.search).get("recap") !== "1") {
        throw { code: "not_in_fixture", message: `${command} is not part of the desks' fixture`, retryable: false };
      }
      return recapAnswer(command, input);
    default:
      throw { code: "not_in_fixture", message: `${command} is not part of the desks' fixture`, retryable: false };
  }
}

function recapAnswer(command: string, input: Record<string, unknown>): unknown {
  const extractionId = String(input.extractionId ?? "");
  if (command === "reader_recap_event") return { version: 1, eventId: `fx_recap_${String(input.event)}`, event: input.event };
  const ours = extractionId === FIXTURE_SOURCES.book.extractionId;
  const session = { sessionId: "fx_session", extractionId, visitIds: ["fx_visit"], startedAt: "2026-11-22T20:00:00Z", endedAt: "2026-11-22T20:40:00Z", minutes: 40 };
  const open = [{ rootExchangeId: "fx_root1", questionEventId: "fx_q1", questionMd: "does the constant always cancel?", spanId: `${extractionId}_s1_4`, anchorSpanIds: [`${extractionId}_s1_4`], openedAt: "2026-11-22T20:05:00Z" }];
  if (command === "reader_recap") {
    return { version: 1, dismissed: false, recap: ours ? {
      recapVersion: "fixture", extractionId, session, continueAt: { sectionId: `${extractionId}_s2`, label: "2 Why the exponential" },
      stillOpen: open, unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
    } : null };
  }
  return {
    version: 1, wrapUpVersion: "fixture", available: ours, extractionId, session: ours ? session : null, resolved: [],
    stillOpen: ours ? [{ rootExchangeId: "fx_root1", questionMd: "does the constant always cancel?", spanIds: [`${extractionId}_s1_4`], actions: [
      { action: "resolve", rpc: "reader.set_inquiry_status", params: { resolution: "resolved", trigger: "chip" } }, { action: "keep_open" },
    ] }] : [],
    worthReinforcing: [],
  };
}

/** The notebook fixture (`?notebook=1`): a real sandboxed session the harness script started (its frame URL in
 * `window.__notebookHarness`), or a forced state (`?nbstate=`) for the frame's honest states. */
declare global {
  interface Window {
    __notebookHarness?: { frameUrl: string; sessionId: string; padCells?: Array<{ blockId: string; code: string }> };
    __nbRpc?: (command: string, input: Record<string, unknown>) => Promise<unknown>;
  }
}

/** `?nblesson=open|review`: the fixture lesson's medium is a notebook (spec §11.2), open (its commit points
 * release) or finished (its review); the harness script serves the notebook from a real sandboxed session. */
function notebookLesson(view: LessonViewDto): LessonViewDto {
  const mode = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("nblesson");
  if (mode !== "open" && mode !== "review") return view;
  return { ...view, medium: "notebook", notebookPath: `notebooks/lessons/${view.lessonId}.py`, closed: mode === "review",
    closeReason: mode === "review" ? view.closeReason ?? "learner_stop" : null };
}

function notebookSession(command: string, input: Record<string, unknown>) {
  const forced = new URLSearchParams(window.location.search).get("nbstate");
  const real = window.__notebookHarness;
  if (forced === "unavailable" || (!real && !forced)) {
    throw { code: "notebook_runtime_unavailable", message: "Notebooks can't run here: bubblewrap (bwrap) is not installed; notebooks run only inside it.", retryable: false };
  }
  const state = forced && forced !== "ready" ? forced : "ready";
  return {
    version: 1, sessionId: real?.sessionId ?? "nbs_fixture", owner: (input.owner as string) ?? "lesson:fx", state,
    stopReason: state === "stopped" ? "idle" : null, error: state === "failed" ? "the notebook server stopped 4 times; it was not started again" : null,
    restarts: state === "restarting" ? 1 : 0, framesAttached: 0, cells: [], startSeconds: [0.4],
    frameUrl: real?.frameUrl ?? "http://127.0.0.1:9/s/none/", memoryBytes: null, command,
  };
}

export async function invoke<T>(command: string, args: InvokeArgs = {}): Promise<T> {
  const input = (args.input as Record<string, unknown> | undefined) ?? args;
  calls.push({ command, input: JSON.parse(JSON.stringify(input ?? {})), at: Date.now() });
  return answer(command, input) as T;
}

export function convertFileSrc(filePath: string, protocol = "asset"): string {
  return `fixture://${protocol}/${encodeURIComponent(filePath)}`;
}
