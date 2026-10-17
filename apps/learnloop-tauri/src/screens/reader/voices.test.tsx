// G55: three voices with glyph, rule, label and spoken prefix; evidence and
// check markers; meaning-bearing copy on --dim. Plus two lints over the Reader's
// component sources: model text renders through ModelVoice, and meaning-bearing
// labels never use <Faint>.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { CheckMarker, EvidenceMarker, LearnerVoice, MeaningLabel, ModelVoice, SourceVoice } from "./voices";

afterEach(cleanup);

// The Reader's component sources, read raw for the two lints below.
const READER_SOURCES: Record<string, string> = import.meta.glob(
  ["../ReaderScreen.tsx", "./*.tsx", "!./*.test.tsx"],
  { query: "?raw", import: "default", eager: true },
);

it("each voice has its glyph (hidden from screen readers), label and spoken prefix", () => {
  const { container } = render(
    <>
      <SourceVoice source="Probability" locator="§5.4 p.212">verbatim</SourceVoice>
      <ModelVoice first>explanation</ModelVoice>
      <LearnerVoice>my words</LearnerVoice>
    </>,
  );
  const voices = Array.from(container.querySelectorAll("[data-voice]")).map((node) => node.getAttribute("data-voice"));
  expect(voices).toEqual(["source", "model", "learner"]);
  expect(screen.getByText("From the book, §5.4 p.212:")).toBeTruthy();
  expect(screen.getByText("LearnLoop's model:")).toBeTruthy();
  expect(screen.getByText("You wrote:")).toBeTruthy();
  for (const glyph of ["§", "◇", "›"]) {
    const node = screen.getByText(glyph);
    expect(node.getAttribute("aria-hidden")).toBe("true");
  }
  expect(container.textContent).toContain("LearnLoop's model");
  // The rules differ by style as well as colour, so greyscale keeps them apart.
  const rules = Array.from(container.querySelectorAll<HTMLElement>("[data-voice]")).map((node) => node.style.borderLeft);
  expect(rules[0]).toContain("solid");
  expect(rules[1]).toContain("dotted");
  expect(rules[2]).toContain("2px solid");
});

it("the evidence markers are the well's discrete glyphs, never a percentage", () => {
  const { container } = render(
    <>
      <EvidenceMarker status="untested" />
      <EvidenceMarker status="with_help" />
      <EvidenceMarker status="demonstrated" />
    </>,
  );
  expect(container.textContent).toContain("○");
  expect(container.textContent).toContain("◌");
  expect(container.textContent).toContain("●");
  expect(container.textContent).not.toMatch(/%/);
  expect(screen.getByLabelText("worked with help · a check on your own is pending")).toBeTruthy();
});

it("check markers say what checked them, and a model's reading is never 'checked'", () => {
  render(<><CheckMarker status="checked" /><CheckMarker status="model_reading" /><CheckMarker status="not_checked" /></>);
  expect(screen.getByLabelText("model's reading").textContent).not.toContain("✓");
  expect(screen.getByLabelText("checked").textContent).toContain("✓");
});

it("meaning-bearing labels use --dim", () => {
  render(<MeaningLabel>not checked</MeaningLabel>);
  expect((screen.getByText("not checked") as HTMLElement).style.color).toBe("var(--dim)");
});

it("lint: model text in the Reader renders through ModelVoice", () => {
  // The model-written fields the Reader shows: Ask answers, quick checks'
  // questions and intended answers, and background request results.
  const modelFields = /value=\{(?:exchange\.answerMd|question\.expectedAnswer|question\.expectedAnswerMd|question\.questionMd|result\.contentMd)\b/;
  const offenders: string[] = [];
  expect(Object.keys(READER_SOURCES).length).toBeGreaterThan(5);
  for (const [file, source] of Object.entries(READER_SOURCES)) {
    const lines = source.split("\n");
    lines.forEach((line, index) => {
      if (!modelFields.test(line)) return;
      const before = lines.slice(Math.max(0, index - 3), index).join("\n");
      // RW1b: an expected answer that is the book's own lines (answer_basis =
      // "source", found in the passage in code) renders through SourceVoice,
      // and only on that branch.
      const bookBranch = before.includes("<SourceVoice") && lines.slice(Math.max(0, index - 4), index).join("\n").includes("fromBook ?");
      if (!before.includes("<ModelVoice") && !bookBranch) offenders.push(`${file}:${index + 1}`);
    });
  }
  expect(offenders).toEqual([]);
});

it("lint: meaning-bearing labels never use <Faint> (about 3.5:1 on the default background)", () => {
  const meaning = /(model's reading|model's guess|not checked|never a grade|counts as one hint|not a test|self-check|AI-written|AI completes)/;
  const offenders: string[] = [];
  for (const [file, source] of Object.entries(READER_SOURCES)) {
    const faint = /<Faint\b[^>]*>([\s\S]*?)<\/Faint>/g;
    for (let match = faint.exec(source); match; match = faint.exec(source)) {
      if (meaning.test(match[1])) offenders.push(`${file}: ${match[1].trim().slice(0, 60)}`);
    }
  }
  expect(offenders).toEqual([]);
});
