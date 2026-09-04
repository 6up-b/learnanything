import { memo, type ComponentProps } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

// remark-math only recognizes $…$ / $$…$$, but model-generated prose (tutor
// answers, open questions) routinely uses \(…\) / \[…\] — which plain markdown
// then mangles by swallowing the backslashes. Rewrite those delimiters to the
// dollar forms before parsing, leaving code fences and inline code untouched.
const CODE_SEGMENT = /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`[^`\n]*`)/g;

function rewriteDelimiters(text: string): string {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, body: string) => `\n$$\n${body.trim()}\n$$\n`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, body: string) => `$${body.trim()}$`);
}

export function normalizeMathDelimiters(value: string): string {
  return value
    .split(CODE_SEGMENT)
    .map((segment, i) => (i % 2 === 1 ? segment : rewriteDelimiters(segment)))
    .join("");
}

// Module-level plugin lists: a fresh array per render defeats react-markdown's
// own memoisation, and the component is memoised because the markdown +
// KaTeX pipeline is the most expensive render in the app (used from dozens
// of call sites that re-render on unrelated state).
type MarkdownProps = ComponentProps<typeof ReactMarkdown>;
const REMARK_PLUGINS: MarkdownProps["remarkPlugins"] = [remarkGfm, remarkMath];
const REHYPE_PLUGINS: MarkdownProps["rehypePlugins"] = [rehypeKatex];

export const MarkdownMath = memo(function MarkdownMath({ value }: { value: string }) {
  return (
    <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
      {normalizeMathDelimiters(value || "")}
    </ReactMarkdown>
  );
});
