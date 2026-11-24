// Every kind of desk window has a decision on what an open inline check shows of it (`WINDOW_VEIL_DECISIONS`): a new
// kind added to the DTO, the desks' glyphs or the shell's window switch without one fails here (and the type refuses
// the table), so no window reaches the learner during a check because nobody thought of it. A kind without a
// decision is held whole anyway (`passagesCanShow`); the test makes the decision explicit.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { WINDOW_VEIL_DECISIONS, passagesCanShow } from "./model";

const SRC = join(__dirname, "..", "..", "..");

/** The window kinds the DTO declares: each `kind: "<name>"` of `ContentRefDto`, and `pad_stack`. */
function dtoKinds(): string[] {
  const dto = readFileSync(join(SRC, "api", "dto.ts"), "utf8");
  const union = dto.slice(dto.indexOf("export type ContentRefDto ="), dto.indexOf("export type PadStackEntryDto"));
  const kinds = [...union.matchAll(/kind: "([a-z_]+)"/g)].map((match) => match[1]);
  const window = dto.slice(dto.indexOf("export type DeskWindowKind ="), dto.indexOf("export interface DeskWindowDto"));
  kinds.push(...[...window.matchAll(/\| "([a-z_]+)"/g)].map((match) => match[1]));
  return [...new Set(kinds)];
}

/** The kinds the desks give a glyph (`KIND_GLYPH`), read from the shell's source (the shell itself needs a browser). */
function glyphKinds(): string[] {
  const shell = readFileSync(join(SRC, "screens", "desks", "DeskShell.tsx"), "utf8");
  const start = shell.indexOf("export const KIND_GLYPH");
  const table = shell.slice(start, shell.indexOf("};", start));
  return [...table.matchAll(/^\s+([a-z_]+):/gm)].map((match) => match[1]);
}

/** The content kinds the shell's window switch renders (`case "<kind>":` in the pane body). */
function shellKinds(): string[] {
  const shell = readFileSync(join(SRC, "screens", "desks", "DeskShell.tsx"), "utf8");
  const start = shell.indexOf("const paneBody = (window: DeskWindow");
  const body = shell.slice(start, shell.indexOf("\n  };\n", start));
  return [...new Set([...body.matchAll(/case "([a-z_]+)":/g)].map((match) => match[1]))];
}

describe("every window kind has a veil decision", () => {
  it("the DTO's window kinds", () => {
    const kinds = dtoKinds();
    expect(kinds.length).toBeGreaterThan(5);
    expect(kinds.filter((kind) => !(kind in WINDOW_VEIL_DECISIONS))).toEqual([]);
  });

  it("the desks' glyphs and the shell's window switch", () => {
    const glyphs = glyphKinds();
    expect(glyphs.length).toBeGreaterThan(5);
    expect(glyphs.filter((kind) => !(kind in WINDOW_VEIL_DECISIONS))).toEqual([]);
    const rendered = shellKinds();
    expect(rendered.length).toBeGreaterThan(3);
    expect(rendered.filter((kind) => !(kind in WINDOW_VEIL_DECISIONS))).toEqual([]);
  });

  it("only a source's or a video's own text can show; any other kind, or one with no decision, is held whole", () => {
    expect(Object.entries(WINDOW_VEIL_DECISIONS).filter(([, decision]) => decision === "passages").map(([kind]) => kind).sort()).toEqual(["source", "video"]);
    expect(passagesCanShow("a_kind_added_tomorrow")).toBe(false);
  });
});
