// The desks harness's stand-in for the sidecar answers as the sidecar does where the harness relies on
// it: desk.state and desk.apply with batches in order and versions checked per op, the Reader's reads
// from the synthetic workspace, every call recorded, and anything else refused by name.
import { describe, expect, it } from "vitest";
import type { DeskApplyDto, DeskStateDto } from "../../api/dto";
import { invoke } from "./fakeCore";
import { FIXTURE_SOURCES } from "./sources";

describe("the harness's fake sidecar", () => {
  it("serves the fixture's desks and applies a batch, checking each op's version", async () => {
    const state = await invoke<DeskStateDto>("desk_state", { input: {} });
    expect(state.desks.map((desk) => desk.title)).toEqual(["softmax and cross-entropy", "attention", "backprop"]);
    const reply = await invoke<DeskApplyDto>("desk_apply", {
      input: {
        clientId: "c", seq: 1, ops: [
          { op: "set_focus", deskId: "fx_desk_softmax", windowId: "fx_w_video", expectedVersion: 1 },
          { op: "set_focus", deskId: "fx_desk_softmax", windowId: "fx_w_paper", expectedVersion: 1 },
        ],
      },
    });
    expect(reply.results.map((result) => result.status)).toEqual(["ok", "conflict"]);
    await expect(invoke("desk_apply", { input: { clientId: "c", seq: 3, ops: [] } })).rejects.toMatchObject({ code: "seq_gap" });
  });

  it("answers the Reader's reads from the synthetic workspace and records them", async () => {
    const view = await invoke<{ extractionId: string; blocks: unknown[] }>("reader_render_view", { input: { extractionId: FIXTURE_SOURCES.book.sourceId } });
    expect(view.extractionId).toBe(FIXTURE_SOURCES.book.extractionId);
    expect(view.blocks.length).toBeGreaterThan(10);
    await invoke("reader_log_activity", { input: { events: [{ kind: "reader_view_opened" }] } });
    const calls = window.__deskHarness?.calls ?? [];
    expect(calls.some((call) => call.command === "reader_log_activity")).toBe(true);
  });

  it("refuses what the fixture does not hold, by name", async () => {
    await expect(invoke("reader_ask", { input: {} })).rejects.toMatchObject({ code: "not_in_fixture" });
    await expect(invoke("curriculum_guide_slice", { input: {} })).rejects.toMatchObject({ code: "curriculum_disabled" });
  });
});
