// RO0 rows 4 and 5 (spec_router_objective_v1 §4): a batched event keeps when it happened, and a visit names who sent it.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const send = vi.hoisted(() => vi.fn().mockResolvedValue({ recorded: 1 }));

vi.mock("../../api/client", () => ({ api: { readerLogActivity: send } }));

import {
  flushReaderActivity,
  logReaderActivity,
  setNextReaderVisitInitiator,
  setReaderActivityEnabled,
  takeReaderVisitInitiator,
} from "./activity";

describe("the Reader's activity", () => {
  beforeEach(() => {
    send.mockClear();
    setReaderActivityEnabled(true);
  });
  afterEach(() => setReaderActivityEnabled(false));

  it("stamps each event when it happened, not when the batch went", () => {
    logReaderActivity({ kind: "reader_selection", payload: { visit_id: "v1" } });
    flushReaderActivity();
    const [event] = send.mock.calls[0][0].events;
    expect(Number.isNaN(Date.parse(event.occurred_at))).toBe(false);
  });

  it("names the plan once, for the next visit only; every other visit is the learner's", () => {
    expect(takeReaderVisitInitiator()).toBe("learner");
    setNextReaderVisitInitiator("plan");
    expect(takeReaderVisitInitiator()).toBe("plan");
    expect(takeReaderVisitInitiator()).toBe("learner");
  });
});
