// Adaptive difficulty AD1 fix round 4 (V4; spec §5.3 unknown timing,
// G-AD1-10): the first-hint marker of a restored draft whose earlier hint was
// never timed stays unknown; a fresh draft still records its first hint.
import { act, renderHook } from "@testing-library/react";
import { expect, it } from "vitest";
import { useFirstHintProgress } from "./useFirstHintProgress";

it("an earlier hint with no saved marker leaves the marker unknown at every later reveal", () => {
  const hook = renderHook(() => useFirstHintProgress({ enabled: true, restored: null, hintsBefore: true }));
  act(() => hook.result.current.mark("draft_started"));
  act(() => hook.result.current.mark("no_draft"));
  expect(hook.result.current.value).toBeNull();
});

it("a fresh draft still records no_draft or draft_started at its first hint", () => {
  const empty = renderHook(() => useFirstHintProgress({ enabled: true, hintsBefore: false }));
  act(() => empty.result.current.mark("no_draft"));
  expect(empty.result.current.value).toBe("no_draft");
  const begun = renderHook(() => useFirstHintProgress({ enabled: true }));
  act(() => begun.result.current.mark("draft_started"));
  expect(begun.result.current.value).toBe("draft_started");
});

it("a saved marker is kept whatever came before, and an untimed book after the first hint changes nothing", () => {
  const restored = renderHook(() => useFirstHintProgress({ enabled: true, restored: "no_draft", hintsBefore: true }));
  act(() => restored.result.current.mark("draft_started"));
  expect(restored.result.current.value).toBe("no_draft");
  const marked = renderHook(() => useFirstHintProgress({ enabled: true }));
  act(() => marked.result.current.mark("draft_started"));
  act(() => marked.result.current.noteUntimedHint?.());
  expect(marked.result.current.value).toBe("draft_started");
});

it("a book counted before any timed hint leaves the marker unknown", () => {
  const hook = renderHook(() => useFirstHintProgress({ enabled: true }));
  // On the old hook this method does not exist; the reveal is then recorded.
  act(() => hook.result.current.noteUntimedHint?.());
  act(() => hook.result.current.mark("no_draft"));
  expect(hook.result.current.value).toBeNull();
});
