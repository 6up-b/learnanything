// UX Phase 2 (docs/specs/ux_learnloop_v1.md §7.9, §10 2.3): the notice system
// that replaces Phase 1's stopgap. Errors and notices are two kinds; a notice
// can name what resolves it and leaves once that happens; nothing but errors
// shows while the Reader has a book open, and the held notices arrive at the
// next destination.
import { describe, expect, it } from "vitest";
import { RETRY_RAN } from "../errors";
import {
  NOTICE_TTL_MS,
  addNotice,
  dismissNotice,
  expireNotices,
  markShown,
  resolveNotices,
  restartHidden,
  sessionNotice,
  visibleNotices,
  type ShellNotice
} from "./notices";

const empty: ShellNotice[] = [];

describe("the notice list", () => {
  it("keeps errors and notices apart, newest last", () => {
    let list = addNotice(empty, { kind: "notice", text: "grading → codex" });
    list = addNotice(list, { kind: "error", text: "Could not open the reader." });
    expect(list.map((notice) => [notice.kind, notice.text])).toEqual([
      ["notice", "grading → codex"],
      ["error", "Could not open the reader."]
    ]);
    expect(list.every((notice) => notice.shownAt === null)).toBe(true);
  });

  it("shows one copy of a repeated message, as fresh", () => {
    let list = addNotice(empty, { kind: "notice", text: "Saved." });
    list = markShown(list, list.map((notice) => notice.id), 1000);
    list = addNotice(list, { kind: "notice", text: "Saved." });
    expect(list).toHaveLength(1);
    expect(list[0].shownAt).toBeNull();
  });

  it("shows at most three at once; the fourth waits its turn instead of being dropped", () => {
    let list = empty;
    for (const text of ["a", "b", "c", "d"]) list = addNotice(list, { kind: "notice", text });
    expect(list.map((notice) => notice.text)).toEqual(["a", "b", "c", "d"]);
    expect(visibleNotices(list, false).map((notice) => notice.text)).toEqual(["a", "b", "c"]);
    list = dismissNotice(list, list[0].id);
    expect(visibleNotices(list, false).map((notice) => notice.text)).toEqual(["b", "c", "d"]);
  });

  // Codex review F2: an error with Try again, then three notices, lost the
  // error and its retry.
  it("keeps an unresolved error and its retry through any number of notices", () => {
    const retry = async () => RETRY_RAN;
    let list = addNotice(empty, { kind: "error", text: "Could not open the reader.", retry, source: "shell:open-reader" });
    for (const text of ["a", "b", "c", "d", "e"]) list = addNotice(list, { kind: "notice", text });
    const error = list.find((notice) => notice.kind === "error");
    expect(error?.retry).toBe(retry);
    const shown = visibleNotices(list, false);
    expect(shown).toHaveLength(3);
    expect(shown[0].text).toBe("Could not open the reader.");
  });

  it("delivers every notice held while reading, not only the last three", () => {
    let list = empty;
    for (const text of ["a", "b", "c", "d"]) list = addNotice(list, { kind: "notice", text });
    expect(visibleNotices(list, true)).toEqual([]);
    const delivered: string[] = [];
    for (let turn = 0; turn < 4 && list.length > 0; turn += 1) {
      const shown = visibleNotices(list, false);
      delivered.push(...shown.map((notice) => notice.text).filter((text) => !delivered.includes(text)));
      list = dismissNotice(list, shown[0].id);
    }
    expect(delivered).toEqual(["a", "b", "c", "d"]);
  });

  it("dismisses by id", () => {
    const list = addNotice(addNotice(empty, { kind: "notice", text: "a" }), { kind: "error", text: "b" });
    expect(dismissNotice(list, list[0].id).map((notice) => notice.text)).toEqual(["b"]);
  });
});

describe("a notice is true only until it is resolved", () => {
  it("drops every session-first notice once a session begins, held or shown", () => {
    let list = addNotice(empty, sessionNotice("practice"));
    list = addNotice(list, sessionNotice("checkMe"));
    list = addNotice(list, { kind: "notice", text: "Already in your library — opened where you left off." });
    list = addNotice(list, { kind: "error", text: "Could not open the check." });
    expect(resolveNotices(list, "session").map((notice) => notice.text)).toEqual([
      "Already in your library — opened where you left off.",
      "Could not open the check."
    ]);
  });

  it("marks session-first notices as notices, not errors", () => {
    expect(sessionNotice("plan")).toMatchObject({ kind: "notice", resolvedBy: "session" });
  });
});

describe("held while reading, delivered at the destination", () => {
  it("shows errors but holds notices while the Reader has a book open", () => {
    let list = addNotice(empty, { kind: "notice", text: "grading → codex" });
    list = addNotice(list, { kind: "error", text: "Could not load this." });
    expect(visibleNotices(list, true).map((notice) => notice.text)).toEqual(["Could not load this."]);
    expect(visibleNotices(list, false).map((notice) => notice.text)).toEqual(["grading → codex", "Could not load this."]);
  });

  it("does not age a held notice: its time starts when it is first shown", () => {
    let list = addNotice(empty, { kind: "notice", text: "grading → codex" });
    // Ten minutes in the Reader: never shown, so never expired.
    expect(expireNotices(list, 10 * 60_000)).toHaveLength(1);
    list = markShown(list, list.map((notice) => notice.id), 10 * 60_000);
    expect(expireNotices(list, 10 * 60_000 + NOTICE_TTL_MS - 1)).toHaveLength(1);
    expect(expireNotices(list, 10 * 60_000 + NOTICE_TTL_MS)).toHaveLength(0);
  });

  it("never expires an error by itself", () => {
    let list = addNotice(empty, { kind: "error", text: "Could not save." });
    list = markShown(list, list.map((notice) => notice.id), 0);
    expect(expireNotices(list, 60 * 60_000)).toHaveLength(1);
  });

  // Codex review F7: a notice shown, then held, came back already expired.
  it("restarts a notice's time when it leaves the screen unexpired", () => {
    let list = addNotice(empty, { kind: "notice", text: "a" });
    list = addNotice(list, { kind: "error", text: "e" });
    list = markShown(list, list.map((notice) => notice.id), 1000);
    const errorShownAt = list[1].shownAt;
    // Held in the Reader: only the error is on screen.
    list = restartHidden(list, [list[1].id]);
    expect(list[0].shownAt).toBeNull();
    expect(list[1].shownAt).toBe(errorShownAt);
    // Still on screen: unchanged, and the same list.
    expect(restartHidden(list, list.map((notice) => notice.id))).toBe(list);
  });

  it("marks only the ids it is given, once", () => {
    let list = addNotice(addNotice(empty, { kind: "notice", text: "a" }), { kind: "notice", text: "b" });
    list = markShown(list, [list[0].id], 5);
    list = markShown(list, [list[0].id], 9);
    expect(list.map((notice) => notice.shownAt)).toEqual([5, null]);
  });
});

// Fix round 3 (whole-stage verify 20261021-130232-Uk06Al items 1-2): an
// error's identity is its source; errors are never de-duplicated by text.
describe("error identity (fix round 3)", () => {
  const retry = async () => RETRY_RAN;

  it("keeps two errors with the same sentence from two sources, each with its retry", () => {
    let list = addNotice(empty, { kind: "error", text: "The engine is not responding.", retry, source: "query:map" });
    list = addNotice(list, { kind: "error", text: "The engine is not responding.", retry, source: "query:tree" });
    expect(list.map((notice) => notice.source)).toEqual(["query:map", "query:tree"]);
    expect(list.every((notice) => notice.retry === retry)).toBe(true);
  });

  it("replaces an error only with a new error of the same source, even when its sentence changed", () => {
    let list = addNotice(empty, { kind: "error", text: "Timed out.", retry, source: "query:map" });
    list = addNotice(list, { kind: "error", text: "Still busy.", retry, source: "query:map" });
    expect(list.map((notice) => notice.text)).toEqual(["Still busy."]);
  });

  it("never merges errors by their text alone", () => {
    let list = addNotice(empty, { kind: "error", text: "Could not save." });
    list = addNotice(list, { kind: "error", text: "Could not save." });
    expect(list).toHaveLength(2);
    // Plain notices still show once.
    list = addNotice(addNotice(list, { kind: "notice", text: "Saved." }), { kind: "notice", text: "Saved." });
    expect(list.filter((notice) => notice.kind === "notice")).toHaveLength(1);
  });

  it("offers no retry without a source to identify it by", () => {
    const list = addNotice(empty, { kind: "error", text: "Timed out.", retry, source: "" } as never);
    expect(list[0].retry).toBeNull();
  });
});
