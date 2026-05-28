import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { COLOR, FONT_MONO } from "../components/term";
import { MarkdownMath } from "./MarkdownMath";

// Single-pane "live preview" markdown editor (Obsidian/Typora model): every block
// renders with KaTeX/markdown except the block the caret is in, which shows its raw
// source in a textarea. Moving off a block re-renders it. There is no source|preview
// split — you type directly into the rendered document.
//
// Editing is offset-based: when a block goes active we freeze the text *before* and
// *after* it, edit the slice in between, and re-emit `before + draft + after`. That
// keeps everything outside the block byte-for-byte intact and lets you add blank
// lines mid-block without the textarea reshuffling under the caret.

interface Block {
  start: number;
  end: number;
  text: string;
  frontmatter?: boolean;
}

// Split a document into renderable blocks (separated by blank lines), keeping
// fenced code (``` / ~~~) and display-math ($$) fences whole, and treating a leading
// YAML frontmatter section as its own (raw-rendered) block.
function splitBlocks(value: string): Block[] {
  const blocks: Block[] = [];
  let scanFrom = 0;

  if (value.startsWith("---")) {
    const close = value.indexOf("\n---", 3);
    if (close !== -1) {
      const afterClose = value.indexOf("\n", close + 1);
      const fmEnd = afterClose === -1 ? value.length : afterClose;
      blocks.push({ start: 0, end: fmEnd, text: value.slice(0, fmEnd), frontmatter: true });
      scanFrom = fmEnd;
    }
  }

  const lines = value.slice(scanFrom).split("\n");
  let cursor = scanFrom;
  let blockStart = -1;
  let blockEnd = -1;
  let fence: "fence" | "math" | null = null;

  const flush = () => {
    if (blockStart !== -1) {
      blocks.push({ start: blockStart, end: blockEnd, text: value.slice(blockStart, blockEnd) });
      blockStart = -1;
    }
  };

  for (const line of lines) {
    const lineStart = cursor;
    const lineEnd = cursor + line.length;
    const trimmed = line.trim();
    const isFence = trimmed.startsWith("```") || trimmed.startsWith("~~~");
    const isMath = trimmed === "$$";

    if (fence) {
      blockEnd = lineEnd;
      if ((fence === "fence" && isFence) || (fence === "math" && isMath)) fence = null;
    } else if (trimmed === "") {
      flush();
    } else {
      if (blockStart === -1) blockStart = lineStart;
      blockEnd = lineEnd;
      if (isFence) fence = "fence";
      else if (isMath) fence = "math";
    }
    cursor = lineEnd + 1; // account for the consumed "\n"
  }
  flush();
  return blocks;
}

const SCROLL_STYLE = { flex: 1, overflow: "auto", minHeight: 0 } as const;

export function LiveMarkdownEditor({
  value,
  onChange,
  placeholder = "type markdown — math renders as you move off a block"
}: {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
}) {
  // While a block is active we hold the frozen text on either side of it.
  const [editing, setEditing] = useState<{ before: string; after: string } | null>(null);
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  const blocks = useMemo(() => splitBlocks(value), [value]);

  // The active slice currently lives between `before` and `after` in `value`.
  const aStart = editing ? editing.before.length : -1;
  const aEnd = editing ? value.length - editing.after.length : -1;
  const draft = editing ? value.slice(aStart, aEnd) : "";

  function startEdit(block: Block) {
    setEditing({ before: value.slice(0, block.start), after: value.slice(block.end) });
  }

  function startEditEmpty() {
    setEditing({ before: "", after: "" });
  }

  function onDraftChange(next: string) {
    if (!editing) return;
    onChange(editing.before + next + editing.after);
  }

  // Focus + caret-to-end whenever a block goes active.
  useLayoutEffect(() => {
    if (editing && taRef.current) {
      const node = taRef.current;
      node.focus();
      const end = node.value.length;
      node.setSelectionRange(end, end);
    }
  }, [editing !== null]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-size the active textarea to its content.
  useEffect(() => {
    const node = taRef.current;
    if (node) {
      node.style.height = "auto";
      node.style.height = `${node.scrollHeight}px`;
    }
  }, [draft, editing !== null]); // eslint-disable-line react-hooks/exhaustive-deps

  function renderBlock(block: Block) {
    return (
      <div
        key={`b${block.start}`}
        onMouseDown={(event) => {
          event.preventDefault();
          startEdit(block);
        }}
        style={{ cursor: "text", padding: "2px 0" }}
      >
        {block.frontmatter ? (
          <pre style={frontmatterStyle}>{block.text}</pre>
        ) : (
          <div className="markdown" style={{ color: COLOR.text }}>
            <MarkdownMath value={block.text} />
          </div>
        )}
      </div>
    );
  }

  const textarea = (
    <textarea
      ref={taRef}
      value={draft}
      onChange={(event) => onDraftChange(event.target.value)}
      onBlur={() => setEditing(null)}
      spellCheck={false}
      rows={1}
      style={{
        display: "block",
        width: "100%",
        resize: "none",
        border: `1px solid ${COLOR.borderStrong}`,
        outline: "none",
        background: COLOR.bgInput,
        color: COLOR.text,
        fontFamily: FONT_MONO,
        fontSize: 12.5,
        lineHeight: 1.65,
        padding: "6px 10px",
        margin: "2px 0",
        boxSizing: "border-box",
        overflow: "hidden"
      }}
    />
  );

  let body;
  if (!editing) {
    body =
      blocks.length === 0 ? (
        <div onMouseDown={(e) => { e.preventDefault(); startEditEmpty(); }} style={{ cursor: "text", color: COLOR.textFaint, fontStyle: "italic" }}>
          {placeholder}
        </div>
      ) : (
        blocks.map(renderBlock)
      );
  } else {
    const beforeBlocks = blocks.filter((block) => block.end <= aStart);
    const afterBlocks = blocks.filter((block) => block.start >= aEnd);
    body = (
      <>
        {beforeBlocks.map(renderBlock)}
        {textarea}
        {afterBlocks.map(renderBlock)}
      </>
    );
  }

  return (
    <div className="ll-scroll" style={SCROLL_STYLE}>
      <div style={{ padding: "12px 18px", fontSize: 13, lineHeight: 1.65 }}>{body}</div>
    </div>
  );
}

const frontmatterStyle = {
  margin: 0,
  padding: "8px 10px",
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.border}`,
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 11.5,
  lineHeight: 1.6,
  whiteSpace: "pre-wrap" as const,
  overflowWrap: "anywhere" as const
};
