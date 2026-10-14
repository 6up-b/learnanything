// Method-explicit items (round 3): the instruction is a block the sidecar
// renders from the item's required method, shown after the statement.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ItemPresentation } from "./ItemPresentation";

vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <p>{value}</p> }));

afterEach(() => {
  cleanup();
});

describe("ItemPresentation", () => {
  it("shows a required method's instruction as its own block after the statement", () => {
    render(
      <ItemPresentation
        presentation={{
          practiceItemId: "pi_det",
          blocks: [
            {
              kind: "prompt",
              markdown: 'The previous exercise said: "Use cofactor expansion in your answer." Compute det(B).',
              label: null
            },
            { kind: "required_method_instruction", markdown: "Use cofactor expansion in your answer.", label: null }
          ]
        }}
      />
    );
    const paragraphs = screen.getAllByText(/cofactor expansion/).map((node) => node.textContent);
    expect(paragraphs).toEqual([
      'The previous exercise said: "Use cofactor expansion in your answer." Compute det(B).',
      "Use cofactor expansion in your answer."
    ]);
  });
});
