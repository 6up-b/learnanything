import { memo, useMemo, type ComponentProps } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { useMathMacros } from "./mathMacros";
import { normalizeMathDelimiters, REMARK_PLUGINS } from "./markdownPipeline";

// The normalization and the remark plugins live in markdownPipeline.ts, because the check behind "matches the book's
// equation (checked)" must find the equations this page finds.

// A display environment KaTeX draws (it refuses them in inline math). The web-page extraction keeps some of a
// page's display equations as bare environments, outside any $$, and remark-math leaves those as text.
const DISPLAY_ENVIRONMENT = /^(equation|align|gather|alignat)\*?$/;
// What a bare environment is looked for between: code (shown as written), an escaped dollar, and math already
// delimited (an environment inside it is that formula's own). Then a \begin{…}.
const AROUND_ENVIRONMENTS =
  /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`[^`\n]*`|\\\$|\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$[^$\n]+?\$)|\\begin\{([A-Za-z]+\*?)\}/g;

/** Each bare display environment, put in $$ on lines of its own, as the page's own \[ … \] are. One never
 *  closed, or one KaTeX cannot draw, is left as written. Only the page's drawing changes: the text stored and
 *  what the book-math check reads (markdownPipeline.ts, pageMathSegments.ts) are not this. */
function bareEnvironmentsAsDisplayMath(value: string): string {
  if (!value.includes("\\begin{")) return value;
  let out = "";
  let last = 0;
  AROUND_ENVIRONMENTS.lastIndex = 0;
  for (let match = AROUND_ENVIRONMENTS.exec(value); match; match = AROUND_ENVIRONMENTS.exec(value)) {
    const name = match[2];
    if (!name || !DISPLAY_ENVIRONMENT.test(name)) continue;
    const close = `\\end{${name}}`;
    const end = value.indexOf(close, match.index + match[0].length);
    if (end < 0) continue;
    const after = end + close.length;
    out += `${value.slice(last, match.index)}\n$$\n${value.slice(match.index, after)}\n$$\n`;
    last = after;
    AROUND_ENVIRONMENTS.lastIndex = after;
  }
  return last === 0 ? value : out + value.slice(last);
}

// Module-level plugin list: a fresh array per render defeats react-markdown's
// own memoisation, and the component is memoised because the markdown +
// KaTeX pipeline is the most expensive render in the app (used from dozens
// of call sites that re-render on unrelated state).
type MarkdownProps = ComponentProps<typeof ReactMarkdown>;
const REHYPE_PLUGINS: MarkdownProps["rehypePlugins"] = [rehypeKatex];

// `components`: the phone renders a remote image as a link (mobile spec §3.4, its CSP has none).
// `urlTransform`: the phone maps the destinations its host serves (mobile v2 §2.3); none is react-markdown's default.
// Keep both module-level constants, for the same reason as the plugin list. The desktop passes neither.
export const MarkdownMath = memo(function MarkdownMath({
  value,
  components,
  urlTransform
}: {
  value: string;
  components?: MarkdownProps["components"];
  urlTransform?: MarkdownProps["urlTransform"];
}) {
  // A source's own macros (mathMacros.tsx), when the screen shows its math. Without them the plugin list is the
  // module constant: rehype-katex with no options, the settings the book-math check reads equations under.
  // With them, a copy per value: KaTeX writes a formula's \gdef into the table it is given, and the source's
  // table must not carry one formula's definition into the next render.
  const macros = useMathMacros();
  const rehypePlugins = useMemo<MarkdownProps["rehypePlugins"]>(
    () => (macros ? [[rehypeKatex, { macros: { ...macros } }]] : REHYPE_PLUGINS),
    [macros, value]
  );
  return (
    <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={rehypePlugins} components={components}
      urlTransform={urlTransform}>
      {normalizeMathDelimiters(bareEnvironmentsAsDisplayMath(value || ""))}
    </ReactMarkdown>
  );
});
