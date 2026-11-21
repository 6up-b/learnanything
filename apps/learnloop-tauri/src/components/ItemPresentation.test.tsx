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

  // UX-76 (the live walk partread-3): an error hunt whose prompt already holds the work showed it again under "The
  // work to check" ("the worked solution was printed twice").
  const WORK = "Since $A(1,0) = (3,0) = 3(1,0)$ and $(1,0) \\neq 0$,\nthe vector $(1,0)$ is an eigenvector with eigenvalue $3$.";
  it("an error hunt whose prompt already holds the work shows it once: the block under it is not repeated", () => {
    render(
      <ItemPresentation
        presentation={{
          practiceItemId: "pi_hunt",
          blocks: [
            // The same work, with its line breaks and spaces laid out differently.
            { kind: "prompt", markdown: `Check this justification.\n\nSubmitted work:\n\n${WORK.replace("\n", "  \n   ")}`, label: null },
            { kind: "error_hunt_worked_solution", markdown: WORK, label: "The work to check" }
          ]
        }}
      />
    );
    expect(screen.getAllByText(/is an eigenvector with eigenvalue/)).toHaveLength(1);
    expect(screen.queryByText("The work to check")).toBeNull();
  });

  it("an error hunt whose prompt does not hold the work keeps the work under its label", () => {
    render(
      <ItemPresentation
        presentation={{
          practiceItemId: "pi_hunt",
          blocks: [
            { kind: "prompt", markdown: "Check the work below. Is it right?", label: null },
            { kind: "error_hunt_worked_solution", markdown: WORK, label: "The work to check" }
          ]
        }}
      />
    );
    expect(screen.getAllByText(/is an eigenvector with eigenvalue/)).toHaveLength(1);
    expect(screen.getByText("The work to check")).toBeTruthy();
  });

  it("a laddered stem's shared setup is never left out, even when the prompt repeats it", () => {
    render(
      <ItemPresentation
        presentation={{
          practiceItemId: "pi_part",
          blocks: [
            { kind: "laddered_stem_stimulus", markdown: "A is symmetric.", label: "Shared setup · part 2 of 3" },
            { kind: "prompt", markdown: "A is symmetric. Show its eigenvectors are orthogonal.", label: null }
          ]
        }}
      />
    );
    expect(screen.getByText("Shared setup · part 2 of 3")).toBeTruthy();
    expect(screen.getByText("A is symmetric.")).toBeTruthy();
  });
});
