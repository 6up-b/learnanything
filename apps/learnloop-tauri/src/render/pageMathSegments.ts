// RW5c §5.2: the equations the page shows for a block, as the page finds them. This is react-markdown's own pipeline
// (unified, remark-parse, MarkdownMath's remark plugins, remark-rehype under react-markdown's options) up to the tree
// rehype-katex walks, so a reference definition, a link title, a code span or an unreferenced footnote is simply not there.
// bookMathRender.test.ts holds it to the real MarkdownMath; the sidecar runs it bundled, never a second reader.
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";
import { normalizeWithPlaces, REMARK_PLUGINS } from "./markdownPipeline";

export type PageMathSegment = { latex: string; start: number; end: number; display: boolean };

type Hast = {
  type: string;
  tagName?: string;
  value?: string;
  properties?: { className?: unknown };
  position?: { start?: { offset?: number }; end?: { offset?: number } };
  children?: Hast[];
};

const PROCESSOR = unified().use(remarkParse).use(REMARK_PLUGINS).use(remarkRehype, { allowDangerousHtml: true });

function classes(node: Hast): unknown[] {
  const names = node.properties?.className;
  return Array.isArray(names) ? names : [];
}

function textOf(node: Hast): string {
  return node.type === "text" ? String(node.value ?? "") : (node.children ?? []).map(textOf).join("");
}

/** A UTF-16 place in ``text`` as the code points before it: the Python side's strings count those. */
function codePoints(text: string, place: number): number {
  let count = 0;
  for (let at = 0; at < place; at++) {
    const unit = text.charCodeAt(at);
    if (unit >= 0xd800 && unit <= 0xdbff && at + 1 < place) {
      const next = text.charCodeAt(at + 1);
      if (next >= 0xdc00 && next <= 0xdfff) at++;
    }
    count++;
  }
  return count;
}

export function pageMathSegments(value: string): PageMathSegment[] {
  const source = value || "";
  const { text, places } = normalizeWithPlaces(source);
  const tree = PROCESSOR.runSync(PROCESSOR.parse(text)) as unknown as Hast;
  const found: PageMathSegment[] = [];
  const visit = (node: Hast, holder: Hast | null, struck: boolean) => {
    if (node.type !== "element") {
      (node.children ?? []).forEach((child) => visit(child, node, struck));
      return;
    }
    const names = classes(node);
    const inline = names.includes("math-inline");
    const display = names.includes("math-display");
    if (node.tagName === "code" && (inline || display)) {
      // A displayed block's place is on its <pre>. A struck-through equation is shown, but no book states it.
      const located = node.position ?? holder?.position;
      const low = located?.start?.offset;
      const high = located?.end?.offset;
      if (!struck && typeof low === "number" && typeof high === "number") {
        const latex = textOf(node);
        const inside = text.indexOf(latex, low);
        const [from, to] = inside >= 0 && inside + latex.length <= high ? [inside, inside + latex.length] : [low, high];
        let begin = from;
        while (begin < to && places[begin] < 0) begin++;
        let end = to;
        while (end > begin && places[end - 1] < 0) end--;
        if (begin < end) {
          found.push({ latex, start: codePoints(source, places[begin]), end: codePoints(source, places[end - 1] + 1), display });
        }
      }
      return;
    }
    (node.children ?? []).forEach((child) => visit(child, node, struck || node.tagName === "del"));
  };
  visit(tree, null, false);
  return found;
}
