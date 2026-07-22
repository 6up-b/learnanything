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

export function MarkdownMath({ value }: { value: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
      {normalizeMathDelimiters(value || "")}
    </ReactMarkdown>
  );
}
