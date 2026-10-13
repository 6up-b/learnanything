import { useState } from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ReaderAskBranches, type ReaderExchange } from "./ReaderAskBranches";

vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
afterEach(cleanup);
const exchange = (id: string, parentExchangeId: string | null = null): ReaderExchange => ({
  id, parentExchangeId, extractionId: "ext", spanId: "passage", selectionSpanIds: ["passage", "next"],
  selectionQuoteMd: "Selected exact words", question: `Question ${id}`, answerMd: `Answer ${id}`,
  answerMode: "answer_directly", createdAt: null, citations: [{ extractionId: "ext", spanId: "next", label: "Second passage" }],
});
const follow = vi.fn();
const jump = vi.fn();
function Harness({ exchanges, query = "" }: { exchanges: ReaderExchange[]; query?: string }) {
  const [collapsed, setCollapsed] = useState(new Set<string>());
  return <ReaderAskBranches exchanges={exchanges} query={query} collapsedIds={collapsed} busy={false}
    onFollowUp={follow} onShowPassage={jump} onToggle={(id) => setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    })} />;
}

it("renders siblings under their parent, supports deep follow-ups and collapses the subtree", () => {
  render(<Harness exchanges={[exchange("leaf", "left"), exchange("right", "root"), exchange("left", "root"), exchange("root")]} />);
  const siblings = screen.getByRole("list", { name: "Follow-ups to Question root" });
  expect(within(siblings).getByText("Answer right")).toBeTruthy();
  const left = screen.getByRole("list", { name: "Follow-ups to Question left" });
  expect(within(left).getByText("Answer leaf")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /▾ Question root/ }));
  expect(screen.queryByText("Answer leaf")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /▸ Question root/ }));
  expect(screen.getByText("Answer leaf")).toBeTruthy();
});

it("preserves the exact exchange/selection for follow-up and navigates anchors and validated citations", () => {
  const root = exchange("root");
  render(<Harness exchanges={[root]} />);
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  expect(follow).toHaveBeenCalledWith(root);
  fireEvent.click(screen.getByRole("button", { name: "show passage" }));
  expect(jump).toHaveBeenLastCalledWith("passage");
  fireEvent.click(screen.getByRole("button", { name: "source: Second passage" }));
  expect(jump).toHaveBeenLastCalledWith("next");
});

it("search reveals matching descendants with ancestors while excluding unrelated siblings", () => {
  const { rerender } = render(<Harness exchanges={[exchange("leaf", "root"), exchange("sibling", "root"), exchange("root")]} />);
  fireEvent.click(screen.getByRole("button", { name: /▾ Question root/ }));
  rerender(<Harness query="Answer leaf" exchanges={[exchange("leaf", "root"), exchange("sibling", "root"), exchange("root")]} />);
  expect(screen.getByText("Answer root")).toBeTruthy();
  expect(screen.getByText("Answer leaf")).toBeTruthy();
  expect(screen.queryByText("Answer sibling")).toBeNull();
});

it("keeps legacy roots, missing-parent exchanges, and corrupt cycles readable", () => {
  render(<Harness exchanges={[exchange("legacy"), exchange("orphan", "absent"), exchange("a", "b"), exchange("b", "a")]} />);
  for (const id of ["legacy", "orphan", "a", "b"]) expect(screen.getByText(`Answer ${id}`)).toBeTruthy();
});

it("restores the hierarchy from saved exchanges after remounting", () => {
  const saved = JSON.parse(JSON.stringify([exchange("child", "root"), exchange("root")]));
  const first = render(<Harness exchanges={saved} />);
  first.unmount();
  render(<Harness exchanges={saved} />);
  expect(within(screen.getByRole("list", { name: "Follow-ups to Question root" })).getByText("Answer child")).toBeTruthy();
});
