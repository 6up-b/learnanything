// RW2b fix round 9 (docs/reviews/reader-rw2b-h3-codex-review.md): symbolic checks
// are off by default, and the workbench never shows a "✓" / "≠" symbolic label
// unless the server says the check decided the verdict.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { VerdictCell } from "./CheckColumn";
import { claimLine, verdictMark } from "./helpModel";
import type { CheckStepVerdictDto } from "../../api/dto";

afterEach(cleanup);

function verdict(method: string, verdictValue: string, mark: string, label: string): CheckStepVerdictDto {
  return { chainId: "c1", number: 1, verdict: verdictValue, method, mark, label, reason: "", dependsOn: [],
    assumption: "", first: false, editedSinceCheck: false, deletedSinceCheck: false } as CheckStepVerdictDto;
}

it("a model's-reading verdict never shows a checked mark, whatever marker arrives", () => {
  expect(verdictMark(verdict("model", "valid", "✓", "checked"))).toEqual(
    { mark: "≈", label: "model's reading, not checked" });
  expect(verdictMark(verdict("model", "questionable", "≠", "checked")).mark).toBe("?");
  expect(verdictMark(verdict("model", "unchecked", "·", "model's reading, not checked")).mark).toBe("·");
  // A verdict the check decided keeps its marker, only with the switch on.
  expect(verdictMark(verdict("checked", "valid", "✓", "checked"), true)).toEqual({ mark: "✓", label: "checked" });
  // Fix round 11: a missing switch refuses it too.
  expect(verdictMark(verdict("checked", "valid", "✓", "checked")).mark).toBe("≈");
});

it("the verdict cell renders the guarded marker", () => {
  render(<VerdictCell verdict={verdict("model", "valid", "✓", "checked")} />);
  expect(screen.getByTestId("workbench-verdict").textContent).toBe("≈ model's reading, not checked");
});

it("a claim is shown with ✓ only when the check decided it", () => {
  expect(claimLine({ statement: "x = 1", status: "model", label: "model's reading, not checked" }))
    .toBe("≈ x = 1 — model's reading, not checked");
  expect(claimLine({ statement: "x = 1", status: "failed", label: "doesn't hold" })).toBe("≈ x = 1 — doesn't hold");
  expect(claimLine({ statement: "x = 1", status: "checked", label: "checked" }, true)).toBe("✓ x = 1 — checked");
  expect(claimLine({ statement: "x = 1", status: "checked", label: "checked" })).toBe(
    "≈ x = 1 — model's reading, not checked");
});

// RW2b fix round 10: the server sends the switch; off, even a stored checked
// verdict or claim never shows ✓ or ≠.
it("with the switch off, a stored checked verdict or claim reads as the model's", () => {
  expect(verdictMark(verdict("checked", "valid", "✓", "checked"), false)).toEqual(
    { mark: "≈", label: "model's reading, not checked" });
  expect(verdictMark(verdict("checked", "questionable", "≠", "checked"), false).mark).toBe("?");
  expect(claimLine({ statement: "x = 1", status: "checked", label: "checked" }, false))
    .toBe("≈ x = 1 — model's reading, not checked");
  render(<VerdictCell verdict={verdict("checked_numerically", "valid", "✓", "checked numerically")}
    symbolicEnabled={false} />);
  expect(screen.getByTestId("workbench-verdict").textContent).toBe("≈ model's reading, not checked");
});
