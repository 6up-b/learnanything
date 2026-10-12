// Daily-loop P2 auto-advance through the real client wrapper and the real
// query cache: only the Tauri transport is faked, so a mutation's cache
// invalidation (or its absence) is what the hook actually sees.
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { QueueInput, QueueSnapshot, ScheduledItemDto } from "../api/dto";
import { clear, invalidate } from "../api/queryCache";
import { TAG } from "../api/queryTags";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));

import { api } from "../api/client";
import { useNextQueueItem } from "./autoAdvance";

const INPUT: QueueInput = { sessionId: "s1", availableMinutes: 25, energy: null };

function queueWith(practiceItemId: string): QueueSnapshot {
  const item = {
    practiceItemId,
    schedulerCandidateId: `cand_${practiceItemId}`,
    learningObjectTitle: practiceItemId
  } as unknown as ScheduledItemDto;
  return {
    version: 1,
    generatedAt: "2026-10-12T12:00:00Z",
    sessionId: "s1",
    sections: [{ title: "due", items: [item] }],
    totalItems: 1
  } as unknown as QueueSnapshot;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

/** A fake sidecar: the queue head is server state that mutations change. */
let serverHead = "pi_a";
let queueReads = 0;
beforeEach(() => {
  serverHead = "pi_a";
  queueReads = 0;
  invoke.mockImplementation(async (command: string) => {
    if (command === "get_today_queue") {
      queueReads += 1;
      return queueWith(serverHead);
    }
    if (command === "trigger_followup") {
      // The forced diagnostic follow-up is queued ahead of everything else.
      serverHead = "pi_followup";
      return { attemptId: "att_1" };
    }
    throw new Error(`${command} not faked`);
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

it("resolves the head of a queue rebuilt after a forced follow-up (the real wrapper invalidates it)", async () => {
  const { result } = renderHook(() => useNextQueueItem(INPUT, true));
  await waitFor(() => expect(result.current.head?.practiceItemId).toBe("pi_a"));
  expect(queueReads).toBe(1);

  await act(async () => { await api.triggerFollowup("att_1"); });

  let next: ScheduledItemDto | null = null;
  await act(async () => { next = await result.current.resolve(); });
  expect(next!.practiceItemId).toBe("pi_followup");
  expect(queueReads).toBe(2);
});

it("never resolves a queue invalidated while it was being read: it waits for the rebuilt one", async () => {
  const stale = deferred<QueueSnapshot>();
  invoke.mockImplementation(async (command: string) => {
    if (command !== "get_today_queue") throw new Error(`${command} not faked`);
    queueReads += 1;
    return queueReads === 1 ? stale.promise : queueWith("pi_fresh");
  });
  const { result } = renderHook(() => useNextQueueItem(INPUT, true));
  await waitFor(() => expect(queueReads).toBe(1));

  // A mutation (or a vault-change notification) lands while the prefetch is in flight.
  act(() => invalidate({ tags: [TAG.queue] }));
  let next: ScheduledItemDto | null | undefined;
  const resolving = result.current.resolve().then((head) => { next = head; });
  await act(async () => { stale.resolve(queueWith("pi_stale")); await resolving; });

  expect(next?.practiceItemId).toBe("pi_fresh");
  expect(queueReads).toBe(2);
  await waitFor(() => expect(result.current.head?.practiceItemId).toBe("pi_fresh"));
});
