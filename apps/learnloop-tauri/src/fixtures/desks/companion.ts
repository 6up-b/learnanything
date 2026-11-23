// The desks' fixture companion and search (spec §18.3): `companion.ask` as a polled job answered by a fake
// tutor the harness can hold open (to time edits and hover while an answer generates), `companion.history`
// and `search.everything` / `search.job` over the synthetic workspace. Project-authored text only.
import type {
  CompanionAskInput,
  CompanionAskJobDto,
  CompanionExchangeDto,
  CompanionHistoryDto,
  SearchEverythingDto,
  SearchGroupDto,
  SearchJobDto,
} from "../../api/dto";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES, FIXTURE_VIEWS } from "./sources";

interface FakeJob {
  input: CompanionAskInput;
  startedAt: number;
  status: CompanionAskJobDto["status"];
  questionEventId: string | null;
}

/** The fake tutor: answers a question this long after it is asked, unless held. */
export const FAKE_ANSWER_MS = 600;

export class FixtureCompanion {
  /** While true, every job stays running (the harness's "fake tutor held open"). */
  held = false;
  private jobs = new Map<string, FakeJob>();
  private searches = new Map<string, { query: string; at: number }>();
  private answered: CompanionExchangeDto[] = [];
  private counter = 0;

  constructor(private readonly now: () => number = Date.now) {}

  ask(input: CompanionAskInput): CompanionAskJobDto {
    const known = this.jobs.get(input.requestId);
    if (known) return this.read(input.requestId);
    this.jobs.set(input.requestId, { input, startedAt: this.now(), status: "running", questionEventId: null });
    return this.read(input.requestId);
  }

  read(requestId: string): CompanionAskJobDto {
    const job = this.jobs.get(requestId);
    if (!job) throw { code: "job_not_found", message: "LearnLoop restarted since it was asked; if it finished, it is in your history.", retryable: false };
    if (job.status === "running" && !this.held && this.now() - job.startedAt >= FAKE_ANSWER_MS) {
      job.status = "done";
      job.questionEventId = `fx_q_${++this.counter}`;
      this.answered.unshift({
        questionEventId: job.questionEventId,
        questionMd: job.input.question,
        answerFirstSentence: "A synthetic answer from the fixture's tutor.",
        answerStatus: "answered",
        context: "reader",
        surface: job.input.surface,
        where: "on a desk",
        origin: "live",
        goalId: null,
        padBlockIds: [],
        anchor: { extractionId: job.input.extractionId, spanId: job.input.spanId, quality: "exact_selection" },
        createdAt: new Date(this.now()).toISOString(),
      });
    }
    const done = job.status === "done" || job.status === "cancelled";
    const answerMd = `A synthetic answer from the fixture's tutor to “${job.input.question}”. The weights come from the scores' differences, so the passage's claim holds.`;
    return {
      version: 1,
      requestId,
      status: job.status,
      done,
      partialMd: job.status === "done" ? answerMd : "",
      citations: job.status === "done" ? [{ extractionId: job.input.extractionId, spanId: job.input.spanId, label: "the passage asked about" }] : [],
      streamedPieces: job.status === "running" ? Math.floor((this.now() - job.startedAt) / 200) : 0,
      questionEventId: job.questionEventId,
      kept: false,
      answer: job.status === "done"
        ? ({
          eventId: `fx_ev_${requestId}`,
          readerAnswerEventId: `fx_ans_${requestId}`,
          answerMd,
          answerMode: "answer_directly",
          citations: [{ extractionId: job.input.extractionId, spanId: job.input.spanId, label: "the passage asked about" }],
          manifest: {},
          warmedSurfaceIds: [],
          burnedSurfaceIds: [],
          hintEquivalent: false,
          remaining: null,
        } as CompanionAskJobDto["answer"])
        : null,
      error: null,
    };
  }

  cancel(requestId: string): CompanionAskJobDto {
    const job = this.jobs.get(requestId);
    if (job && job.status === "running") job.status = "cancelled";
    return this.read(requestId);
  }

  history(input: { query?: string }): CompanionHistoryDto {
    const earlier: CompanionExchangeDto[] = [
      {
        questionMd: "why does adding a constant to every score change nothing?",
        answerFirstSentence: "Because the factor it adds cancels between the top and the bottom.",
        questionEventId: "fx_q_old1", answerStatus: "answered", context: "reader", surface: "reader", where: "in the Reader",
        origin: "backfill", goalId: null, padBlockIds: [],
        anchor: { extractionId: FIXTURE_SOURCES.book.extractionId, spanId: `${FIXTURE_SOURCES.book.extractionId}_s1_4`, quality: "exact_selection" },
        createdAt: "2026-11-14T10:00:00Z",
      },
    ];
    const all = [...this.answered, ...earlier];
    const q = input.query?.toLowerCase().trim();
    const rows = q ? all.filter((exchange) => exchange.questionMd.toLowerCase().includes(q) || exchange.answerFirstSentence.toLowerCase().includes(q)) : all;
    const days = new Map<string, CompanionExchangeDto[]>();
    for (const row of rows) {
      const date = row.createdAt.slice(0, 10);
      days.set(date, [...(days.get(date) ?? []), row]);
    }
    return {
      version: 1,
      days: [...days.entries()].map(([date, exchanges]) => ({ date, desks: [{ deskId: exchanges[0].origin === "live" ? "fx_desk_softmax" : null, exchanges }] })),
      cursor: null,
    };
  }

  search(input: { query: string; deskId?: string | null }): SearchEverythingDto {
    const q = input.query.toLowerCase().trim();
    const sources = FIXTURE_LIBRARY.filter((card) => card.title.toLowerCase().includes(q)).map((card) => ({
      ref: { kind: "source" as const, sourceId: card.sourceId, extractionId: FIXTURE_VIEWS[card.sourceId]?.extractionId ?? card.sourceId },
      target: null,
      sourceId: card.sourceId,
      extractionId: FIXTURE_VIEWS[card.sourceId]?.extractionId ?? null,
      title: card.title,
      readerEnabled: true,
      openOnDeskIds: [],
      onThisDesk: false,
    }));
    const passages = this.passages((text) => text.toLowerCase().includes(q), false);
    const jobId = `fx_search_${++this.counter}`;
    this.searches.set(jobId, { query: q, at: this.now() });
    const groups: SearchGroupDto[] = [
      { group: "sources", label: "sources in your library", basis: "words", status: "ok", rows: sources, more: false },
      { group: "passages", label: "passages and moments", basis: "words", status: "ok", rows: passages.slice(0, 12), more: passages.length > 12 },
      { group: "notes", label: "your notes and highlights", basis: "words", status: "off", reason: "your notes are off in this fixture", rows: [], more: false },
      { group: "pads", label: "your pads", basis: "words", status: "ok", rows: [], more: false },
      { group: "threads", label: "threads", basis: "words", status: "ok", rows: [], more: false },
      {
        group: "exchanges", label: "past companion exchanges", basis: "words", status: "ok", more: false,
        rows: this.history({ query: q }).days.flatMap((day) => day.desks.flatMap((desk) => desk.exchanges)).map((exchange) => ({
          ref: exchange.anchor ? { kind: "source" as const, sourceId: FIXTURE_SOURCES.book.sourceId, extractionId: exchange.anchor.extractionId } : null,
          target: exchange.anchor ? { spanId: exchange.anchor.spanId } : null,
          questionEventId: exchange.questionEventId, questionMd: exchange.questionMd, answerFirstSentence: exchange.answerFirstSentence,
          surface: exchange.surface, where: exchange.where, origin: exchange.origin, createdAt: exchange.createdAt, deskId: null,
        })),
      },
    ];
    return {
      version: 1,
      query: input.query,
      groups,
      meaning: { status: "pending", jobId, groups: ["passages"], unavailable: [{ group: "pads", reason: "no meaning index of pad text" }, { group: "threads", reason: "no meaning index of exchanges" }] },
    };
  }

  searchJob(jobId: string): SearchJobDto {
    const search = this.searches.get(jobId);
    if (!search) throw { code: "job_not_found", message: "no such search", retryable: false };
    const done = this.now() - search.at >= 300;
    // A stand-in for the meaning pass: passages of the attention note the words did not find.
    const rows = done
      ? this.passages((text) => !text.toLowerCase().includes(search.query), true).filter((row) => row.extractionId === FIXTURE_SOURCES.paper.extractionId).slice(0, 2)
      : [];
    return {
      version: 1, jobId, status: done ? "done" : "running", done, error: null,
      groups: done ? [{ group: "passages", label: "passages and moments", basis: "meaning", status: "ok", rows, more: false }] : [],
    };
  }

  private passages(match: (text: string) => boolean, byMeaning: boolean) {
    return Object.values(FIXTURE_VIEWS).flatMap((view) => {
      const card = FIXTURE_LIBRARY.find((entry) => entry.sourceId === view.sourceId);
      const video = view.extractionId === FIXTURE_SOURCES.video.extractionId || view.extractionId === FIXTURE_SOURCES.video2.extractionId;
      return view.blocks.filter((block) => block.blockType === "Text" && match(block.markdown)).map((block) => ({
        ref: video ? { kind: "video" as const, sourceId: view.sourceId, extractionId: view.extractionId } : { kind: "source" as const, sourceId: view.sourceId, extractionId: view.extractionId },
        target: { spanId: block.spanId ?? "" },
        sourceId: view.sourceId, sourceTitle: card?.title ?? view.sourceId, extractionId: view.extractionId, spanId: block.spanId ?? "",
        section: null, page: null, snippet: block.markdown.replace(/\$\$[^$]*\$\$/g, "…").replace(/\$[^$]*\$/g, "…"), byMeaning,
      }));
    });
  }
}
