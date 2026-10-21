// UX Phase 2, Codex review of ux-phase2-shell F3: a failed knowledge-map read
// reached the shell as a bare sentence, so a retryable failure (a sidecar
// timeout) left the error with no Try again over a "loading" screen. The view
// now hands the shell the error itself and a retry that reads again.
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  getKnowledgeMap: vi.fn(async () => {
    throw { code: "sidecar_timeout", message: "The knowledge map timed out.", retryable: true };
  }),
  getKnowledgeMapHistory: vi.fn(async () => ({})),
  getDecayPressure: vi.fn(async () => ({ pressure: null }))
}));
vi.mock("../api/client", () => ({ api }));

import { KnowledgeMapView } from "./KnowledgeMapScreen";

afterEach(cleanup);

describe("KnowledgeMapView's load failure", () => {
  it("reports the error with a retry that reads the map again", async () => {
    const onError = vi.fn();
    render(<KnowledgeMapView onInspect={vi.fn()} onError={onError} />);
    await waitFor(() => expect(onError).toHaveBeenCalled());
    const [message, report] = onError.mock.calls[0] as [
      string,
      { error?: unknown; retry?: (() => unknown) | null; source?: string | null } | undefined
    ];
    expect(message).toBe("The knowledge map timed out.");
    expect(report?.error).toMatchObject({ code: "sidecar_timeout", retryable: true });
    expect(report?.source).toBe("knowledge-map:get_knowledge_map");
    expect(typeof report?.retry).toBe("function");
    const before = api.getKnowledgeMap.mock.calls.length;
    // Fix round 2: the retry hands back the read itself, so the shell sees a
    // second failure and reports it, mounted or not.
    await act(async () => {
      await expect(Promise.resolve(report?.retry?.())).rejects.toMatchObject({ code: "sidecar_timeout" });
    });
    expect(api.getKnowledgeMap.mock.calls.length).toBe(before + 1);
  });
});
