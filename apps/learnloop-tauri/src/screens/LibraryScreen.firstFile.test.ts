// UX Phase 2, a finding Phase 1's usability round 1 deferred here (m8,
// docs/reviews/ux-phase1.md): "Notes & files opens previewing vault.lock".
// The tree lists directories first and then files by name, so the first file
// of a vault is a machine file: vault.lock, state.sqlite, a WAL file. In the
// simple shell the first selection is the first note a person wrote (a
// Markdown file), else the first file that isn't a lock or a database. The
// classic shell keeps the first file.
import { describe, expect, it } from "vitest";
import type { VaultTreeNode } from "../api/dto";
import { initialFilePath, learnerTree } from "./LibraryScreen";

const file = (path: string, kind = "text"): VaultTreeNode => ({ type: "file", name: path.split("/").pop() ?? path, path, kind });
const dir = (path: string, children: VaultTreeNode[]): VaultTreeNode => ({ type: "dir", name: path.split("/").pop() ?? path, path, children });

const tree: VaultTreeNode[] = [
  dir(".learnloop", [file(".learnloop/vault.lock"), file(".learnloop/state.sqlite", "sqlite")]),
  dir("notes", [file("notes/lu-decomposition.md", "markdown")]),
  file("learnloop.toml"),
  file("state.sqlite", "sqlite"),
  file("state.sqlite-wal", "binary"),
  file("vault.lock")
];

describe("the first file Notes & files previews", () => {
  it("is the first note in the simple shell", () => {
    expect(initialFilePath(tree, "simple")).toBe("notes/lu-decomposition.md");
  });

  it("skips locks and databases when there is no note", () => {
    expect(initialFilePath([file("vault.lock"), file("state.sqlite", "sqlite"), file("learnloop.toml")], "simple")).toBe("learnloop.toml");
    expect(initialFilePath([file("vault.lock"), file("state.sqlite", "sqlite")], "simple")).toBeNull();
  });

  it("is the first file in the classic shell, as before", () => {
    expect(initialFilePath(tree, "classic")).toBe(".learnloop/vault.lock");
  });
});

// Codex review F1 (spec Q18): in the simple shell the learner's file tree
// does not list the library's database; Under the hood → Data reaches it,
// read-only by default. Classic keeps the tree as it was.
describe("the database leaves the learner's file tree", () => {
  const paths = (nodes: VaultTreeNode[]): string[] =>
    nodes.flatMap((node) => (node.type === "dir" ? [node.path, ...paths(node.children ?? [])] : [node.path]));

  it("drops database files and their journals in the simple shell", () => {
    const shown = paths(learnerTree(tree, "simple"));
    expect(shown).not.toContain("state.sqlite");
    expect(shown).not.toContain("state.sqlite-wal");
    expect(shown).not.toContain(".learnloop/state.sqlite");
    expect(shown).toContain("notes/lu-decomposition.md");
    expect(shown).toContain("learnloop.toml");
    expect(shown).toContain(".learnloop/vault.lock");
  });

  it("keeps the tree exactly in the classic shell", () => {
    expect(learnerTree(tree, "classic")).toBe(tree);
  });
});
