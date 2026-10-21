// UX Phase 2 (docs/specs/ux_learnloop_v1.md §7.9, §10 2.3): the notice system
// that replaces Phase 1's stopgap. Errors and notices are two kinds; a notice
// can name what resolves it and leaves once that happens; nothing but errors
// shows while the Reader has a book open, and the held notices arrive at the
// next destination.
import { describe, expect, it } from "vitest";
import {
  NOTICE_TTL_MS,
  addNotice,
  dismissNotice,
  expireNotices,
  markShown,
  resolveNotices,
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

  it("keeps at most three at once, dropping the oldest", () => {
    let list = empty;
    for (const text of ["a", "b", "c", "d"]) list = addNotice(list, { kind: "notice", text });
    expect(list.map((notice) => notice.text)).toEqual(["b", "c", "d"]);
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

  it("marks only the ids it is given, once", () => {
    let list = addNotice(addNotice(empty, { kind: "notice", text: "a" }), { kind: "notice", text: "b" });
    list = markShown(list, [list[0].id], 5);
    list = markShown(list, [list[0].id], 9);
    expect(list.map((notice) => notice.shownAt)).toEqual([5, null]);
  });
});
