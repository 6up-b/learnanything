// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5.2, §7.7, §8.5, §10 2.2): one
// screen for the owner's instruments. A left list of tools, each under a
// plain title with its old name in small type and its own count; on the
// right, the tool's screen exactly as it was.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { UnderTheHoodScreen } from "./UnderTheHoodScreen";

afterEach(cleanup);

describe("UnderTheHoodScreen", () => {
  it("lists the tools by plain title, the old name small beside each, with counts", () => {
    render(
      <UnderTheHoodScreen tool="ingest" onSelectTool={() => undefined} counts={{ proposals: 41, maintain: 3 }}>
        <div data-testid="tool-body">ingest screen</div>
      </UnderTheHoodScreen>
    );
    const list = screen.getByRole("navigation", { name: "Under the hood" });
    const rows = within(list).getAllByRole("button");
    expect(rows.map((row) => row.getAttribute("aria-label"))).toEqual([
      "Imports & builds",
      "Study-map changes, 41 waiting",
      "Subjects & topics",
      "Concept graph editor",
      "Analyst views",
      "Mistake history",
      "Calibration",
      "System health, 3 waiting",
      "Data",
      "Files",
      "Inspector",
      "Spend & AI routes"
    ]);
    expect(rows[0].getAttribute("aria-current")).toBe("page");
  });

  it("titles the open tool plainly, with what it was called in small type, over the screen unchanged", () => {
    render(
      <UnderTheHoodScreen tool="proposals" onSelectTool={() => undefined} counts={{}}>
        <div data-testid="tool-body">proposals screen</div>
      </UnderTheHoodScreen>
    );
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.textContent).toBe("Study-map changes");
    expect(screen.getByText("was Proposals")).toBeTruthy();
    expect(screen.getByTestId("tool-body").textContent).toBe("proposals screen");
  });

  it("selects a tool", () => {
    const onSelectTool = vi.fn();
    render(
      <UnderTheHoodScreen tool="ingest" onSelectTool={onSelectTool} counts={{}}>
        <div />
      </UnderTheHoodScreen>
    );
    fireEvent.click(screen.getByRole("button", { name: "System health" }));
    expect(onSelectTool).toHaveBeenCalledWith("maintain");
  });
});
