// Lightweight line-based syntax highlighters for the Library viewer, ported from
// the handoff design (learnloop-handoff2/screens/library.jsx). Not a full parser —
// just enough coloring to read YAML/Markdown comfortably in the dark palette.

import type { ReactNode } from "react";
import { COLOR } from "./term";

const PROSE_KEYS = new Set([
  "description",
  "expected_answer",
  "prompt",
  "quote",
  "summary",
  "title"
]);

const ID_KEYS = new Set([
  "concept",
  "id",
  "learning_object_id",
  "path",
  "practice_mode",
  "ref_id",
  "ref_type",
  "status"
]);

const DATE_KEYS = new Set(["created_at", "updated_at"]);

type YamlContinuation = {
  indent: number;
  color: string;
};

export function highlightYaml(src: string): ReactNode[] {
  let continuation: YamlContinuation | null = null;

  return src.split("\n").map((line, index) => {
    const key = `y${index}`;
    const indent = line.match(/^(\s*)/)?.[0] ?? "";
    const indentWidth = indent.length;
    const rest = line.slice(indent.length);

    if (!rest) {
      continuation = null;
      return (
        <span key={key}>
          {"\n"}
        </span>
      );
    }

    if (line.trim().startsWith("#")) {
      continuation = null;
      return (
        <span key={key} style={{ color: COLOR.textFaint }}>
          {line}
          {"\n"}
        </span>
      );
    }

    const listKeyMatch = rest.match(/^- ([A-Za-z0-9_-]+):\s?(.*)$/);
    if (listKeyMatch) {
      const [, field, value] = listKeyMatch;
      continuation = nextContinuation(indentWidth, field, value);
      return (
        <span key={key}>
          {renderIndent(indent)}
          <span style={{ color: COLOR.amber }}>- </span>
          {renderYamlPair(field, value)}
          {"\n"}
        </span>
      );
    }

    if (rest.startsWith("- ")) {
      const value = rest.slice(2);
      continuation = value ? { indent: indentWidth, color: scalarColor(value) } : null;
      return (
        <span key={key}>
          {renderIndent(indent)}
          <span style={{ color: COLOR.amber }}>- </span>
          <span style={{ color: scalarColor(value) }}>{value}</span>
          {"\n"}
        </span>
      );
    }

    const match = rest.match(/^([A-Za-z0-9_-]+):\s?(.*)$/);
    if (match) {
      const [, field, value] = match;
      continuation = nextContinuation(indentWidth, field, value);
      return (
        <span key={key}>
          {renderIndent(indent)}
          {renderYamlPair(field, value)}
          {"\n"}
        </span>
      );
    }

    if (continuation && indentWidth > continuation.indent) {
      return (
        <span key={key}>
          {renderIndent(indent)}
          <span style={{ color: continuation.color }}>{rest}</span>
          {"\n"}
        </span>
      );
    }

    continuation = null;

    return (
      <span key={key}>
        {line}
        {"\n"}
      </span>
    );
  });
}

function renderYamlPair(field: string, value: string): ReactNode {
  return (
    <>
      <span style={{ color: COLOR.cyan }}>{field}</span>
      <span style={{ color: COLOR.textFaint }}>:</span>
      {value ? (
        <>
          <span> </span>
          {renderYamlScalar(field, value)}
        </>
      ) : null}
    </>
  );
}

function renderYamlScalar(field: string, value: string): ReactNode {
  const block = value.match(/^([|>])([+-])?$/);
  if (block) {
    return <span style={{ color: COLOR.pink }}>{value}</span>;
  }

  const color = scalarColor(value, field);
  const commentIndex = value.indexOf(" #");
  if (commentIndex > 0) {
    return (
      <>
        <span style={{ color }}>{value.slice(0, commentIndex)}</span>
        <span style={{ color: COLOR.textFaint }}>{value.slice(commentIndex)}</span>
      </>
    );
  }

  return <span style={{ color }}>{value}</span>;
}

function renderIndent(indent: string): ReactNode {
  return indent ? <span style={{ color: COLOR.borderStrong }}>{indent}</span> : null;
}

function nextContinuation(indent: number, field: string, value: string): YamlContinuation | null {
  if (/^[|>][+-]?$/.test(value)) {
    return { indent, color: COLOR.greenSoft };
  }
  if (!value || isCompactScalar(value)) return null;
  return { indent, color: scalarColor(value, field) };
}

function isCompactScalar(value: string): boolean {
  const trimmed = value.trim();
  return (
    trimmed === "{}" ||
    trimmed === "[]" ||
    /^['"].*['"]$/.test(trimmed) ||
    /^(true|false|null|~)$/i.test(trimmed) ||
    /^-?\d+(\.\d+)?$/.test(trimmed) ||
    /^\[.*\]$/.test(trimmed) ||
    /^\{.*\}$/.test(trimmed)
  );
}

function scalarColor(value: string, field?: string): string {
  const trimmed = value.trim();
  if (!trimmed || trimmed === "{}" || trimmed === "[]") return COLOR.textFaint;
  if (field && DATE_KEYS.has(field)) return COLOR.yellow;
  if (/^(true|false)$/i.test(trimmed)) return COLOR.pink;
  if (/^(null|~)$/i.test(trimmed)) return COLOR.textFaint;
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return COLOR.amber;
  if (field && PROSE_KEYS.has(field)) return COLOR.green;
  if (field && ID_KEYS.has(field)) return COLOR.amberLink;
  if (/^['"].*['"]$/.test(trimmed)) return COLOR.greenSoft;
  if (/^\[.*\]$/.test(trimmed) || /^\{.*\}$/.test(trimmed)) return COLOR.textDim;
  return COLOR.greenSoft;
}

export function highlightMarkdown(src: string): ReactNode[] {
  return src.split("\n").map((line, index) => {
    const key = `m${index}`;
    if (line.startsWith("---")) {
      return (
        <span key={key} style={{ color: COLOR.textFaint }}>
          {line}
          {"\n"}
        </span>
      );
    }
    if (line.startsWith("# ")) {
      return (
        <span key={key} style={{ color: COLOR.amber, fontWeight: 700 }}>
          {line}
          {"\n"}
        </span>
      );
    }
    if (line.startsWith("## ")) {
      return (
        <span key={key} style={{ color: COLOR.amberLink, fontWeight: 600 }}>
          {line}
          {"\n"}
        </span>
      );
    }
    if (line.startsWith("> ")) {
      return (
        <span key={key} style={{ color: COLOR.cyan, fontStyle: "italic" }}>
          {line}
          {"\n"}
        </span>
      );
    }
    if (line.startsWith("    ")) {
      return (
        <span key={key} style={{ color: COLOR.green }}>
          {line}
          {"\n"}
        </span>
      );
    }
    // Inline `code` and **bold**.
    const parts = line.split(/(`[^`]+`|\*\*[^*]+\*\*)/);
    return (
      <span key={key}>
        {parts.map((part, partIndex) => {
          if (part.startsWith("`") && part.endsWith("`")) {
            return (
              <span key={partIndex} style={{ color: COLOR.green, background: COLOR.bgElev, padding: "0 4px" }}>
                {part.slice(1, -1)}
              </span>
            );
          }
          if (part.startsWith("**") && part.endsWith("**")) {
            return (
              <span key={partIndex} style={{ color: COLOR.amber, fontWeight: 700 }}>
                {part.slice(2, -2)}
              </span>
            );
          }
          return <span key={partIndex}>{part}</span>;
        })}
        {"\n"}
      </span>
    );
  });
}

export function highlightFor(kind: string | undefined, body: string): ReactNode[] {
  if (kind === "md") return highlightMarkdown(body);
  if (kind === "yaml") return highlightYaml(body);
  // toml/json/text fall back to YAML-ish key coloring, which reads fine for them.
  return highlightYaml(body);
}
