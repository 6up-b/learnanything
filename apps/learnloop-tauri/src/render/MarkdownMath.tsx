import { memo, type ComponentProps } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { normalizeMathDelimiters, REMARK_PLUGINS } from "./markdownPipeline";

// The normalization and the remark plugins live in markdownPipeline.ts, because the check behind "matches the book's
// equation (checked)" must find the equations this page finds.

// Module-level plugin list: a fresh array per render defeats react-markdown's
// own memoisation, and the component is memoised because the markdown +
// KaTeX pipeline is the most expensive render in the app (used from dozens
// of call sites that re-render on unrelated state).
type MarkdownProps = ComponentProps<typeof ReactMarkdown>;
const REHYPE_PLUGINS: MarkdownProps["rehypePlugins"] = [rehypeKatex];

export const MarkdownMath = memo(function MarkdownMath({ value }: { value: string }) {
  return (
    <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
      {normalizeMathDelimiters(value || "")}
    </ReactMarkdown>
  );
});
