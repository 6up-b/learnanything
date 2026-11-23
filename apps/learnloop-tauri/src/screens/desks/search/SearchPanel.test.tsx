// Search in context (spec §9.3): one live search generation (a cleared query or a closed panel makes every
// older reply stale, and a stale reply registers no poll), and a meaning pass that says why it did not run or
// how it failed, per group, instead of "nothing found".
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SearchEverythingDto, SearchJobDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import type { Timers } from "../keys/router";
import { SearchPanel, type SearchApi } from "./SearchPanel";

class ManualTimers implements Timers {
  queue: Array<{ fn: () => void; id: number }> = [];
  private next = 1;
  set(fn: () => void): unknown {
    const id = this.next++;
    this.queue.push({ fn, id });
    return id;
  }
  clear(handle: unknown): void {
    this.queue = this.queue.filter((entry) => entry.id !== handle);
  }
  now(): number {
    return 0;
  }
  fire(): void {
    const due = this.queue;
    this.queue = [];
    for (const entry of due) entry.fn();
  }
}

const PASSAGE = { ref: { kind: "source", sourceId: "src1", extractionId: "ext1" }, target: { spanId: "s1" }, sourceId: "src1", sourceTitle: "A book", extractionId: "ext1", spanId: "s1", section: null, page: 3, snippet: "attention is a weighted average", byMeaning: false };

function words(query: string, meaning: SearchEverythingDto["meaning"]): SearchEverythingDto {
  return { version: 1, query, groups: [{ group: "passages", label: "passages and moments", basis: "words", status: "ok", rows: [PASSAGE as never], more: false }], meaning };
}

function setup() {
  const replies: Array<(value: SearchEverythingDto) => void> = [];
  let job: SearchJobDto = { version: 1, jobId: "j1", status: "running", done: false, groups: [], error: null };
  const api: SearchApi = {
    searchEverything: vi.fn(() => new Promise<SearchEverythingDto>((resolve) => replies.push(resolve))),
    searchJob: vi.fn(async () => job),
  };
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  const timers = new ManualTimers();
  const view = render(
    <SearchPanel api={api} poller={poller} timers={timers} deskId="d1" open={[]} deskTitle={() => "a desk"} reducedMotion onOpenRow={vi.fn()} onClose={vi.fn()} />,
  );
  const input = screen.getByLabelText(/search every source/) as HTMLInputElement;
  const type = (value: string) => {
    fireEvent.change(input, { target: { value } });
    act(() => timers.fire());
  };
  const settle = async () => {
    await act(async () => {
      for (let i = 0; i < 4; i += 1) await Promise.resolve();
    });
  };
  return { api, poller, view, replies, type, settle, setJob: (next: SearchJobDto) => { job = next; } };
}

afterEach(cleanup);

describe("one search generation", () => {
  it("a query cleared below two characters makes the older reply stale: it shows nothing", async () => {
    const { replies, type, settle } = setup();
    type("attention");
    expect(replies).toHaveLength(1);
    type("a");
    replies[0](words("attention", { status: "unavailable", jobId: null, unavailable: [] }));
    await settle();
    expect(document.querySelector("[data-search-row]")).toBeNull();
  });

  it("a panel closed before its reply registers no poll for the reply's meaning job", async () => {
    const { replies, type, settle, view, poller } = setup();
    type("attention");
    view.unmount();
    replies[0](words("attention", { status: "pending", jobId: "j1", groups: ["passages"], unavailable: [] }));
    await settle();
    expect(poller.size).toBe(0);
  });
});

describe("the meaning pass says why, per group", () => {
  it("groups with no meaning search say why even while another group's job runs", async () => {
    const { replies, type, settle } = setup();
    type("attention");
    replies[0](words("attention", { status: "pending", jobId: "j1", groups: ["passages"], unavailable: [{ group: "notes", reason: "notes are not indexed by meaning yet" }] }));
    await settle();
    expect(screen.getByText(/notes are not indexed by meaning yet/)).toBeTruthy();
  });

  it("a job that fails says so in its own words, not 'nothing found'", async () => {
    const { replies, type, settle, poller, setJob } = setup();
    type("attention");
    replies[0](words("attention", { status: "pending", jobId: "j1", groups: ["passages"], unavailable: [] }));
    await settle();
    setJob({ version: 1, jobId: "j1", status: "failed", done: true, groups: [], error: { code: "provider_unavailable", message: "the embedding service is not reachable", retryable: true } });
    await act(async () => {
      await poller.tick();
    });
    expect(screen.getByText(/the embedding service is not reachable/)).toBeTruthy();
  });

  it("a group the job could not search, or whose meaning search failed, says why under its name", async () => {
    const { replies, type, settle, poller, setJob } = setup();
    type("attention");
    replies[0](words("attention", { status: "pending", jobId: "j1", groups: ["passages", "notes"], unavailable: [] }));
    await settle();
    setJob({ version: 1, jobId: "j1", status: "done", done: true, error: null, groups: [
      { group: "passages", label: "passages and moments", basis: "meaning", status: "failed", reason: "the query could not be embedded", rows: [], more: false },
      { group: "notes", label: "your notes", basis: "meaning", status: "unavailable", reason: "no notes are indexed by meaning", rows: [], more: false },
    ], unavailable: [{ group: "pads", reason: "no meaning index of pad text" }] });
    await act(async () => {
      await poller.tick();
    });
    expect(screen.getByText(/the query could not be embedded/)).toBeTruthy();
    expect(screen.getByText(/no notes are indexed by meaning/)).toBeTruthy();
    expect(screen.getByText(/no meaning index of pad text/)).toBeTruthy();
  });
});
