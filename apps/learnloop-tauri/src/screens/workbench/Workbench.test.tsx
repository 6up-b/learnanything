// RW2a's workbench on its own (spec §5.1; UX §5.1-5.3, §5.9, §5.10, W5, W8):
// the header, the verbatim problem in the source's voice, the book line before
// step 1, steps saved as typed through a write queue (idempotency keys, a
// retry that keeps the text, an offline sidecar that keeps the steps), Enter
// for a new step, I'm stuck, delete with undo, the book's one key, the submit
// record line and Ctrl+Enter through the ordinary submit, waiting for an
// import to bind, Leave for now (Esc twice) and Abandon in the ⋯ menu. Nothing
// a save or a poll returns moves focus.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { Workbench } from "./Workbench";
import type { WorkbenchSessionDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(),
  workbenchReopen: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
  workbenchSubmit: vi.fn(), workbenchGet: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
// The editor's own behaviour is tested in LiveMarkdownEditor.test.tsx; here a
// textarea stands in, reporting the same key information.
vi.mock("../../render/LiveMarkdownEditor", async () => {
  const React = await import("react");
  return {
    LiveMarkdownEditor: (p: {
      value: string; onChange: (value: string) => void; placeholder?: string; ariaLabel?: string; focusSignal?: number;
      onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>, info: { atEnd: boolean; empty: boolean }) => void;
    }) => {
      const ref = React.useRef<HTMLTextAreaElement | null>(null);
      React.useEffect(() => { if (p.focusSignal) ref.current?.focus(); }, [p.focusSignal]);
      return (
        <textarea
          ref={ref} aria-label={p.ariaLabel} placeholder={p.placeholder} value={p.value}
          onChange={(event) => p.onChange(event.target.value)}
          onKeyDown={(event) => {
            const box = event.currentTarget;
            p.onKeyDown?.(event, { atEnd: box.selectionStart === box.value.length && box.selectionEnd === box.value.length, empty: box.value.trim() === "" });
          }}
        />
      );
    },
  };
});

const RECORD_OPEN = {
  bookCounted: true, bookVisible: true, hints: 1, questionHints: 0, ownAttempt: false,
  line: "book open · 1 hint → practice with help ◌ (not yet checked on your own)",
  footer: "book open = 1 hint · help used: none", stuckNote: null,
};

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_514", stemMd: "Exercise 5.14 Let X be Uniform(-1, 0) with probability p. Find the CDF of X.",
    importStatus: "none", importError: null, origin: "reader", entry: "work_through", parentSessionId: null,
    extractionId: "ext1", spanIds: ["b2"], sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null,
    practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "2026-10-17T09:00:00Z",
    updatedAt: "2026-10-17T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null,
    record: { ...RECORD_OPEN, bookCounted: false, hints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none" },
    parts: null, sourceId: "src1", ...overrides,
  };
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return {
    initial: session(), layout: "split", practiceSessionId: "ps1",
    onSession: vi.fn(), onLeave: vi.fn(), onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(),
    ...overrides,
  };
}

let saved = 0;
beforeEach(() => {
  vi.resetAllMocks();
  saved = 0;
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string; kind?: string; stepId?: string }) => {
    saved += 1;
    return {
      version: 1, savedAt: "2026-10-17T09:00:05Z", record: RECORD_OPEN,
      step: { stepId: `row_${saved}`, chainId: input.stepId ?? `row_${saved}`, ordinal: saved, kind: input.kind ?? "step",
              bodyMd: input.bodyMd ?? "", deleted: input.op === "delete", createdAt: "x", editedAt: "x", versions: [] },
    };
  });
  api.workbenchLeave.mockImplementation(async () => ({ session: session() }));
  api.workbenchAbandon.mockImplementation(async () => ({ session: session({ status: "abandoned", closedAt: "2026-10-17T09:10:00Z" }) }));
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => ({ session: session({ sourceVisible: input.visible }) }));
});
afterEach(cleanup);

function stepBox(index: number): HTMLTextAreaElement {
  return screen.getByRole("textbox", { name: `Step ${index}` }) as HTMLTextAreaElement;
}

async function typeStep(index: number, text: string) {
  const box = stepBox(index);
  fireEvent.focus(box);
  fireEvent.change(box, { target: { value: text } });
}

it("shows the problem verbatim in the book's voice, the book line before step 1, and the record line", () => {
  render(<Workbench {...props()} />);
  const header = screen.getByTestId("workbench-header");
  expect(header.textContent).toContain("WORKING · Exercise 5.14 · from the book, verbatim");
  expect(screen.getByText(/Let X be Uniform/).closest("[data-voice]")?.getAttribute("data-voice")).toBe("source");
  const choice = screen.getByRole("radiogroup", { name: "the book while you work" });
  expect(within(choice).getByRole("radio", { name: /with the book open/ }).getAttribute("aria-checked")).toBe("true");
  expect(choice.textContent).toContain("counts as one hint");
  expect(choice.textContent).toContain("your own attempt; you can open it any time");
  expect(screen.getByTestId("workbench-record").textContent).toBe("your own attempt");
});

it("saves a step as it is typed, with an idempotency key, and edits supersede it", async () => {
  render(<Workbench {...props()} />);
  await typeStep(1, "F_X(x) = p F_Y(x) + (1 - p) F_Z(x)");
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(1), { timeout: 3000 });
  const add = api.workbenchSaveStep.mock.calls[0][0];
  expect(add).toMatchObject({ sessionId: "wb1", op: "add", kind: "step", bodyMd: "F_X(x) = p F_Y(x) + (1 - p) F_Z(x)" });
  expect(typeof add.clientIdempotencyKey).toBe("string");
  expect(await screen.findByText("saved · just now", undefined, { timeout: 3000 })).toBeTruthy();
  // The first step accepted the book choice: the line is gone, the record says so.
  expect(screen.queryByRole("radiogroup", { name: "the book while you work" })).toBeNull();
  expect(screen.getByTestId("workbench-record").textContent).toBe(RECORD_OPEN.line);
  fireEvent.change(stepBox(1), { target: { value: "F_X(x) = p F_Y(x) + (1-p) F_Z(x)" } });
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(2), { timeout: 3000 });
  expect(api.workbenchSaveStep.mock.calls[1][0]).toMatchObject({ op: "edit", stepId: "row_1" });
  expect(api.workbenchSaveStep.mock.calls[1][0].clientIdempotencyKey).not.toBe(add.clientIdempotencyKey);
});

it("a failing write keeps the text, says so without 'error', and retries with the same key until it lands", async () => {
  api.workbenchSaveStep.mockRejectedValueOnce({ code: "database_locked", message: "locked" });
  render(<Workbench {...props()} />);
  await typeStep(1, "my first move");
  expect(await screen.findByText("not saved yet — retrying · your text is safe in this window", undefined, { timeout: 3000 })).toBeTruthy();
  expect(stepBox(1).value).toBe("my first move");
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(2), { timeout: 4000 });
  const [first, second] = api.workbenchSaveStep.mock.calls.map((call) => call[0]);
  expect(second.clientIdempotencyKey).toBe(first.clientIdempotencyKey);
  expect(await screen.findByText("saved · just now", undefined, { timeout: 3000 })).toBeTruthy();
});

it("with the sidecar down the steps stay in the window", async () => {
  api.workbenchSaveStep.mockRejectedValue({ code: "sidecar_unavailable", message: "down" });
  render(<Workbench {...props()} />);
  await typeStep(1, "kept here");
  expect(await screen.findByText("sidecar unreachable — keeping your steps here; they'll save when it's back", undefined, { timeout: 3000 })).toBeTruthy();
  expect(stepBox(1).value).toBe("kept here");
});

it("Enter at a step's end starts the next step, and Shift+Enter stays in the step", async () => {
  render(<Workbench {...props()} />);
  await typeStep(1, "one");
  const box = stepBox(1);
  box.setSelectionRange(3, 3);
  fireEvent.keyDown(box, { key: "Enter", shiftKey: true });
  expect(screen.queryByRole("textbox", { name: "Step 2" })).toBeNull();
  fireEvent.keyDown(box, { key: "Enter" });
  const next = await screen.findByRole("textbox", { name: "Step 2" });
  await waitFor(() => expect(document.activeElement).toBe(next));
});

it("I'm stuck (Ctrl+D) adds a stuck step in the learner's voice with its prompt", async () => {
  render(<Workbench {...props()} />);
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "d", ctrlKey: true });
  const stuck = await screen.findByRole("textbox", { name: "Step 1 (stuck)" });
  expect(stuck.getAttribute("placeholder")).toBe("Write what you can, or what's confusing you. Being stuck here is useful information.");
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledWith(expect.objectContaining({ op: "add", kind: "stuck" })), { timeout: 3000 });
});

it("the empty stuck submit says what it records before it is sent", () => {
  render(<Workbench {...props({ initial: session({ record: { ...session().record, stuckNote: "Submitting now records 'stuck' — that's fine" } }) })} />);
  expect(screen.getByText("Submitting now records 'stuck' — that's fine")).toBeTruthy();
});

it("Ctrl+Backspace in an empty step deletes it with an undo", async () => {
  render(<Workbench {...props({ initial: session({ steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "one", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
    { stepId: "b", chainId: "b", ordinal: 2, kind: "step", bodyMd: "", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }) })} />);
  fireEvent.keyDown(stepBox(2), { key: "Backspace", ctrlKey: true });
  expect(await screen.findByText("step 2 deleted ·")).toBeTruthy();
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledWith(expect.objectContaining({ op: "delete", stepId: "b" })), { timeout: 3000 });
  fireEvent.click(screen.getByRole("button", { name: "undo" }));
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledWith(expect.objectContaining({ op: "restore" })), { timeout: 3000 });
  expect(screen.getByRole("textbox", { name: "Step 2" })).toBeTruthy();
});

it("Ctrl+Shift+B hides and shows the book, and tells the Reader", async () => {
  const onSession = vi.fn();
  render(<Workbench {...props({ onSession })} />);
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "B", ctrlKey: true, shiftKey: true });
  await waitFor(() => expect(api.workbenchSetBook).toHaveBeenCalledWith({ sessionId: "wb1", visible: false }));
  await waitFor(() => expect(onSession).toHaveBeenCalledWith(expect.objectContaining({ sourceVisible: false })));
});

it("Ctrl+Enter saves what is pending, then submits through the ordinary path", async () => {
  const pending: Array<() => void> = [];
  api.workbenchSaveStep.mockImplementationOnce((input: { bodyMd: string }) => new Promise((resolve) => {
    pending.push(() => resolve({ savedAt: "x", record: RECORD_OPEN, step: { stepId: "row_1", chainId: "row_1", ordinal: 1, kind: "step", bodyMd: input.bodyMd, deleted: false, createdAt: "x", editedAt: "x", versions: [] } }));
  }));
  const result = { version: 1, attempt: { attemptId: "att_1" }, session: session({ status: "submitted", attemptId: "att_1" }), practiceSession: { sessionId: "ps1" } };
  api.workbenchSubmit.mockResolvedValue(result);
  const onSubmitted = vi.fn();
  render(<Workbench {...props({ onSubmitted, schedulerCandidateId: "cand", planPresentationId: "pres" })} />);
  await typeStep(1, "A = U Sigma V^T");
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(1), { timeout: 3000 });
  expect(api.workbenchSubmit).not.toHaveBeenCalled();
  await act(async () => pending[0]());
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalledTimes(1));
  expect(api.workbenchSubmit.mock.calls[0][0]).toMatchObject({
    sessionId: "wb1", practiceSessionId: "ps1", schedulerCandidateId: "cand", planPresentationId: "pres",
  });
  await waitFor(() => expect(onSubmitted).toHaveBeenCalledWith(result));
});

it("a refused submit keeps the steps and says why", async () => {
  api.workbenchSubmit.mockRejectedValue({ code: "validation_error", message: "a cold retry must be unassisted and unprimed" });
  render(<Workbench {...props({ initial: session({ steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "one", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }) })} />);
  fireEvent.click(screen.getByRole("button", { name: /^submit/ }));
  expect(await screen.findByText(/a cold retry must be unassisted and unprimed/)).toBeTruthy();
  expect(screen.getByText(/Your steps are kept/)).toBeTruthy();
  expect(stepBox(1).value).toBe("one");
});

it("opens at once before the import binds: steps work, Submit waits and says so, and the binding lands quietly", async () => {
  const pendingSession = session({ practiceItemId: null, importStatus: "pending" });
  api.workbenchRefreshImport.mockResolvedValueOnce({ session: pendingSession })
    .mockResolvedValue({ session: session({ importStatus: "bound" }) });
  render(<Workbench {...props({ initial: pendingSession })} />);
  expect(screen.getByText("setting up checks and hints for this exercise…", { exact: false })).toBeTruthy();
  const submit = screen.getByRole("button", { name: /submit/ });
  expect(submit.textContent).toContain("available once setup finishes");
  fireEvent.click(submit);
  expect(api.workbenchSubmit).not.toHaveBeenCalled();
  await typeStep(1, "my first move");
  const before = document.activeElement;
  await waitFor(() => expect(api.workbenchRefreshImport).toHaveBeenCalledTimes(2), { timeout: 6000 });
  await waitFor(() => expect(screen.getByRole("button", { name: /^submit/ }).textContent).not.toContain("available once setup finishes"));
  expect(document.activeElement).toBe(before);
}, 10000);

it("a failed setup keeps the steps and offers try again; a multi-part one asks which part", async () => {
  api.workbenchRetryImport.mockResolvedValue({ session: session({ practiceItemId: null, importStatus: "pending" }) });
  api.workbenchRefreshImport.mockResolvedValue({ session: session({ practiceItemId: null, importStatus: "pending" }) });
  const { unmount } = render(<Workbench {...props({ initial: session({ practiceItemId: null, importStatus: "failed", importError: "the model timed out" }) })} />);
  expect(screen.getByText(/the model timed out/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await waitFor(() => expect(api.workbenchRetryImport).toHaveBeenCalledWith({ sessionId: "wb1" }));
  unmount();
  api.workbenchBind.mockResolvedValue({ session: session({ practiceItemId: "pi_b", importStatus: "bound" }) });
  render(<Workbench {...props({ initial: session({ practiceItemId: null, importStatus: "pending", parts: [
    { practiceItemId: "pi_a", title: "part (a)", prompt: "a" }, { practiceItemId: "pi_b", title: "part (b)", prompt: "b" },
  ] }) })} />);
  fireEvent.click(screen.getByRole("button", { name: "part (b)" }));
  await waitFor(() => expect(api.workbenchBind).toHaveBeenCalledWith({ sessionId: "wb1", practiceItemId: "pi_b" }));
});

it("Esc leaves the editor, a second Esc is Leave for now, which keeps the problem open", async () => {
  const onLeave = vi.fn();
  render(<Workbench {...props({ onLeave })} />);
  await typeStep(1, "one");
  fireEvent.keyDown(stepBox(1), { key: "Escape" });
  expect(onLeave).not.toHaveBeenCalled();
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "Escape" });
  await waitFor(() => expect(api.workbenchLeave).toHaveBeenCalledWith({ sessionId: "wb1" }));
  await waitFor(() => expect(onLeave).toHaveBeenCalled());
  expect(api.workbenchAbandon).not.toHaveBeenCalled();
});

it("Abandon lives in the ⋯ menu, never on the main row, and asks no confirmation", async () => {
  const onAbandoned = vi.fn();
  render(<Workbench {...props({ onAbandoned })} />);
  const actions = screen.getByRole("group", { name: "workbench actions" });
  expect(within(actions).queryByRole("button", { name: /abandon/i })).toBeNull();
  expect(within(actions).getByRole("button", { name: /I'm stuck/ })).toBeTruthy();
  expect(within(actions).getByRole("button", { name: /leave for now/ })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "more actions" }));
  fireEvent.click(screen.getByRole("menuitem", { name: "Abandon this problem" }));
  await waitFor(() => expect(api.workbenchAbandon).toHaveBeenCalledWith({ sessionId: "wb1" }));
  await waitFor(() => expect(onAbandoned).toHaveBeenCalledWith(expect.objectContaining({ status: "abandoned" })));
  expect(document.querySelector("[role=dialog]")).toBeNull();
});

it("a submitted problem shows read-only with its steps and what it recorded", () => {
  render(<Workbench {...props({ readOnly: true, initial: session({ status: "submitted", attemptId: "att_1", record: RECORD_OPEN, steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "A = U Sigma V^T", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }) })} />);
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.getByText("A = U Sigma V^T")).toBeTruthy();
  expect(screen.getByTestId("workbench-header").textContent).toContain("SUBMITTED");
  expect(screen.getByText(RECORD_OPEN.footer)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /^submit/ })).toBeNull();
});
