// Which blocks the Reader displays, in one file (readerBlockPolicy.json), because two readers must agree on it: the page
// (ReaderScreen) and the check behind "matches the book's equation (checked)" (source_render_views.py reads the same JSON).
//
// furniture: real extraction data the page drops: running heads repeat every page and the book's own ToC interleaves mid-prose.
// markdown: the types known to reach MarkdownMath. The page shows a type it has never met; the check reads only these.
// plainTextSourceUri: a source that opens on the watch surface, whose transcript is plain text and never reaches MarkdownMath.
import policy from "./readerBlockPolicy.json";

const FURNITURE: ReadonlySet<string> = new Set(policy.furniture);

export function readerDisplaysBlock(blockType: string | null | undefined): boolean {
  return !FURNITURE.has(blockType ?? "");
}
