// The ink cache's readings against what the server holds: a reading of strokes that changed meanwhile leaves the
// line unread, a reading stopped before its start answered is stopped on the server too, a reading kept beside the
// learner's correction is offered again after a reload, an erase the server refused shows the strokes it still
// holds, a lifted line takes its strokes along, and unsent ink is said to be kept only while the app is open.
import { describe, expect, it, vi } from "vitest";
import type { InkOwnerViewDto, InkReadingDto, InkStrokeDto, InkTranscribeJobDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { InkCache, type InkCacheApi } from "./inkCache";

const stroke = (strokeId: string): InkStrokeDto => ({ strokeId, points: [[1, 2, 0, 0.5, 0, 0], [3, 4, 8, 0.5, 0, 0]] });

function reading(over: Partial<InkReadingDto> = {}): InkReadingDto {
  return { transcriptionId: "it_1", ownerKind: "block", ownerId: "b1", contentHash: "h1", latexMd: "$x$", confidenceLabel: "may_be_wrong",
    model: "m", createdAt: "t", applied: true, reason: null, headVersionId: "v2", ...over };
}

function owner(strokeIds: string[], transcription: InkOwnerViewDto["transcription"] = null): InkOwnerViewDto {
  return { ownerKind: "block", ownerId: "b1", contentHash: strokeIds.join(","), devicePixelRatio: 1,
    strokes: strokeIds.map((id) => ({ ...stroke(id), inkId: `ink_${id}` })), transcription };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function setup(api: Partial<InkCacheApi> = {}, settled: () => Promise<"saved" | "unsaved"> = async () => "saved") {
  const full: InkCacheApi = {
    inkList: vi.fn(async () => ({ owners: [] })),
    inkTranscribe: vi.fn(),
    inkTranscribeJob: vi.fn(),
    inkTranscribeCancel: vi.fn(async ({ jobId }: { jobId: string }) => ({ version: 1, jobId, status: "cancelled" as const, done: false, result: null, error: null })),
    ...api,
  };
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  const refreshPad = vi.fn(async () => undefined);
  const cache = new InkCache({ api: full, poller, settled, refreshPad });
  return { cache, api: full, poller, refreshPad };
}

describe("the ink cache's readings", () => {
  it("a reading of strokes written to meanwhile leaves the line unread", async () => {
    const answer = deferred<InkTranscribeJobDto>();
    const { cache } = setup({ inkTranscribe: vi.fn(() => answer.promise) });
    cache.addStrokes("p", "b1", "ink_1", [stroke("s1")]);
    const read = cache.read("p", "b1", null);
    await Promise.resolve();
    cache.addStrokes("p", "b1", "ink_2", [stroke("s2")]);
    answer.resolve({ version: 1, jobId: null, status: "done", done: true, result: reading(), error: null });
    await read;
    expect(cache.pad("p").lines.b1.unread).toBe(true);
    expect(cache.pad("p").readings.b1.status).toBe("read");
  });

  it("a reading the server set aside (its strokes changed on another device) leaves the line unread", async () => {
    const { cache } = setup({ inkTranscribe: vi.fn(async () => ({ version: 1, jobId: null, status: "done" as const, done: true, result: reading({ applied: false, reason: "strokes_changed" }), error: null })) });
    cache.addStrokes("p", "b1", "ink_1", [stroke("s1")]);
    await cache.read("p", "b1", null);
    expect(cache.pad("p").lines.b1.unread).toBe(true);
  });

  it("a reading cancelled before its start answered is cancelled on the server and never polled", async () => {
    const answer = deferred<InkTranscribeJobDto>();
    const { cache, api, poller } = setup({ inkTranscribe: vi.fn(() => answer.promise) });
    cache.addStrokes("p", "b1", "ink_1", [stroke("s1")]);
    const read = cache.read("p", "b1", null);
    await Promise.resolve();
    cache.cancel("p", "b1");
    answer.resolve({ version: 1, jobId: "job_late", status: "running", done: false, result: null, error: null });
    await read;
    expect(api.inkTranscribeCancel).toHaveBeenCalledWith({ jobId: "job_late" });
    expect(poller.size).toBe(0);
    expect(cache.pad("p").readings.b1.status).toBe("cancelled");
  });

  it("unsent ink is said to be kept while the app stays open, not on this device", async () => {
    const { cache } = setup({}, async () => "unsaved");
    cache.addStrokes("p", "b1", "ink_1", [stroke("s1")]);
    await cache.read("p", "b1", null);
    expect(cache.pad("p").readings.b1.message).toBe("your ink isn't sent yet · it is kept while LearnLoop stays open");
  });
});

describe("the ink cache against the server's ink", () => {
  it("a reading kept beside the learner's correction is offered again after a reload", async () => {
    const { cache } = setup({ inkList: vi.fn(async () => ({ owners: [owner(["s1"], { transcriptionId: "it_9", latexMd: "$y$", confidenceLabel: "may_be_wrong",
      contentHash: "s1", current: true, createdAt: "t", applied: false, reason: "kept_your_correction" })] })) });
    await cache.load("p");
    expect(cache.pad("p").readings.b1).toMatchObject({ status: "kept_yours", result: { latexMd: "$y$", reason: "kept_your_correction", applied: false } });
  });

  it("an erase the server refused shows the strokes it still holds once the erase is answered", async () => {
    const held = [owner(["s1", "s2"])];
    const { cache, api } = setup({ inkList: vi.fn(async () => ({ owners: held })) });
    await cache.load("p");
    cache.erase("p", "b1", ["s1", "s2"]);
    expect(cache.pad("p").lines.b1.strokes).toEqual([]);
    held.splice(0, 1, owner(["s2"])); // s1 was erased elsewhere first: the whole erase was refused, s2 stands
    await cache.reconcile("p");
    expect(api.inkList).toHaveBeenCalledTimes(2);
    expect(cache.pad("p").lines.b1.strokes.map((s) => s.strokeId)).toEqual(["s2"]);
  });

  it("a forced read keeps the strokes written here that the server has not acknowledged", async () => {
    const answer = deferred<"saved" | "unsaved">();
    const { cache } = setup({ inkList: vi.fn(async () => ({ owners: [owner(["s1"])] })) }, () => answer.promise);
    await cache.load("p");
    cache.addStrokes("p", "b1", "ink_new", [stroke("s9")]);
    await cache.load("p", true);
    expect(cache.pad("p").lines.b1.strokes.map((s) => s.strokeId)).toEqual(["s1", "s9"]);
  });

  it("a lifted line takes its strokes and reading to its new pad, then reads that pad from the server", async () => {
    const { cache, api } = setup({ inkList: vi.fn(async ({ padId }: { padId: string }) => ({ owners: padId === "p" ? [owner(["s1"])] : [{ ...owner(["s1"]), ownerId: "b9" }] })) });
    await cache.load("p");
    cache.lifted("p", "b1", "p2", "b9");
    expect(cache.pad("p2").lines.b9.strokes.map((s) => s.strokeId)).toEqual(["s1"]);
    await vi.waitFor(() => expect(api.inkList).toHaveBeenCalledWith({ padId: "p2" }));
  });
});
