// @vitest-environment jsdom
// The Compare window from the menu (spec §9.1 `=`): the passage it was opened on anchors the comparison.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const ctl = vi.hoisted(() => ({ enabled: true, scopeOn: true, ask: vi.fn(), askBox: vi.fn(async () => undefined), compareFrom: vi.fn(), close: vi.fn() }));
vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: () => ({ data: { readerEnabled: true }, error: null }) }));
vi.mock("../../reader/useLibraryAsk", () => ({ useLibraryAsk: () => ctl }));
vi.mock("../../reader/ReadingPathCard", () => ({ ReadingPathCard: () => null }));
vi.mock("../../reader/LibraryPane", () => ({
  LibraryPane: ({ compose, onAsk }: { compose: string | null; onAsk: (text: string) => void }) => (
    <button type="button" onClick={() => onAsk(compose ?? "")}>ask</button>
  ),
}));

import { LibraryPanel } from "./PanelWindow";

afterEach(() => {
  cleanup();
  ctl.ask.mockReset();
  ctl.compareFrom.mockReset();
});

describe("a Compare window", () => {
  it("opened from a passage runs the comparison anchored on it when the learner asks", () => {
    render(<LibraryPanel query="two ideas" anchor={{ extractionId: "ext1", spanIds: ["s1", "s2"], sourceId: "src1", revisionId: "rev1" }}
      onOpenHit={() => undefined} onClose={() => undefined} onError={() => undefined} />);
    fireEvent.click(screen.getByText("ask"));
    expect(ctl.compareFrom).toHaveBeenCalledWith({ door: "selection", question: "two ideas", extractionId: "ext1", anchorSpanIds: ["s1", "s2"],
      openSourceId: "src1", identity: { sourceId: "src1", revisionId: "rev1", extractionId: "ext1" } });
    expect(ctl.ask).not.toHaveBeenCalled();
  });

  // Review fix round (major 19): typed words are the ask box's, which reads named books first (the old library page's).
  it("opened bare asks across the library through the ask box", () => {
    render(<LibraryPanel query="two ideas" onOpenHit={() => undefined} onClose={() => undefined} onError={() => undefined} />);
    fireEvent.click(screen.getByText("ask"));
    expect(ctl.askBox).toHaveBeenCalledWith({ query: "two ideas", entry: "library_search", extractionId: null, spanIds: [], identity: null });
    expect(ctl.compareFrom).not.toHaveBeenCalled();
  });
});
