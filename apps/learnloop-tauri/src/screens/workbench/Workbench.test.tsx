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
// The window's close request (review F8): the handler is kept so a test can fire it.
const windowApi = vi.hoisted(() => ({
  closeHandlers: [] as Array<(event: { preventDefault: () => void }) => Promise<void>>,
  destroy: vi.fn(),
}));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({
  onCloseRequested: async (handler: (event: { preventDefault: () => void }) => Promise<void>) => {
    windowApi.closeHandlers.push(handler);
    return () => { windowApi.closeHandlers = windowApi.closeHandlers.filter((candidate) => candidate !== handler); };
  },
  destroy: windowApi.destroy,
}) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
// The editor's own behaviour is tested in LiveMarkdownEditor.test.tsx; here a
// textarea stands in, reporting the same key information.
vi.mock("../../render/LiveMarkdownEditor", async () => {
  const React = await import("react");
  return {
    LiveMarkdownEditor: (p: {
      value: string; onChange: (value: string) => void; placeholder?: string; ariaLabel?: string; focusSignal?: number;
      readOnly?: boolean;
      onKeyDown?: (event: React.KeyboardEvent<HTMLTextAreaElement>, info: { atEnd: boolean; empty: boolean }) => void;
    }) => {
      const ref = React.useRef<HTMLTextAreaElement | null>(null);
      React.useEffect(() => { if (p.focusSignal) ref.current?.focus(); }, [p.focusSignal]);
      return (
        <textarea
          ref={ref} aria-label={p.ariaLabel} placeholder={p.placeholder} value={p.value} readOnly={p.readOnly}
          // A change to a read-only box is still reported (round 4 F8), so a
          // test sees the workbench itself refuse it, not only the editor.
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


// -- review fixes (docs/reviews/reader-rw2a-codex-review.md) ------------------------------------

const SAVED_STEPS = [
  { stepId: "a", chainId: "a", ordinal: 1, kind: "step" as const, bodyMd: "one", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  { stepId: "b", chainId: "b", ordinal: 2, kind: "step" as const, bodyMd: "two", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
];

function stepRow(input: { stepId?: string; op: string; kind?: string }, bodyMd: string) {
  return {
    version: 1, savedAt: "x", record: RECORD_OPEN,
    step: { stepId: `${input.stepId ?? "new"}_v`, chainId: input.stepId ?? "new", ordinal: 1, kind: input.kind ?? "step",
            bodyMd, deleted: input.op === "delete", createdAt: "x", editedAt: "x", versions: [] },
  };
}

it("F5: a write retried after its response was lost resends what it sent, and newer text saves under a new key", async () => {
  // The server: each key commits once; a replayed key answers what it committed.
  const committed = new Map<string, string>();
  let head = "one";
  let lose = true;
  api.workbenchSaveStep.mockImplementation(async (input: { clientIdempotencyKey: string; op: string; stepId?: string; bodyMd?: string }) => {
    if (!committed.has(input.clientIdempotencyKey)) {
      committed.set(input.clientIdempotencyKey, input.bodyMd ?? head);
      head = input.bodyMd ?? head;
      if (lose) {
        lose = false;
        throw { code: "database_locked", message: "the response was lost" };
      }
    }
    return stepRow(input, committed.get(input.clientIdempotencyKey)!);
  });
  render(<Workbench {...props({ initial: session({ steps: [SAVED_STEPS[0]] }) })} />);
  await typeStep(1, "first edit");
  expect(await screen.findByText("not saved yet — retrying · your text is safe in this window", undefined, { timeout: 3000 })).toBeTruthy();
  // During the backoff the learner keeps typing.
  fireEvent.change(stepBox(1), { target: { value: "newer edit" } });
  await waitFor(() => expect(head).toBe("newer edit"), { timeout: 6000 });
  const calls = api.workbenchSaveStep.mock.calls.map((call) => call[0]);
  expect(calls[1].clientIdempotencyKey).toBe(calls[0].clientIdempotencyKey);
  expect(calls[1].bodyMd).toBe("first edit");
  expect(calls[2].bodyMd).toBe("newer edit");
  expect(calls[2].clientIdempotencyKey).not.toBe(calls[0].clientIdempotencyKey);
  expect(await screen.findByText("saved · just now", undefined, { timeout: 3000 })).toBeTruthy();
  expect(stepBox(1).value).toBe("newer edit");
}, 12000);

it("F6: a write the server refuses stays not saved, and Submit sends nothing until it is fixed", async () => {
  const onError = vi.fn();
  api.workbenchSaveStep.mockRejectedValueOnce({ code: "validation_error", message: "This step is too long to save." });
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "att_1" }, session: session({ status: "submitted", attemptId: "att_1" }), practiceSession: null });
  render(<Workbench {...props({ onError })} />);
  await typeStep(1, "x".repeat(50));
  expect(await screen.findByText(/^not saved \(This step is too long to save\.\)/, undefined, { timeout: 3000 })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /^submit/ }));
  expect(await screen.findByText(/A step isn't saved \(This step is too long to save\.\), so nothing was submitted/)).toBeTruthy();
  expect(api.workbenchSubmit).not.toHaveBeenCalled();
  expect(stepBox(1).value).toBe("x".repeat(50));
  // Shortened, it saves, and Submit goes.
  fireEvent.change(stepBox(1), { target: { value: "short" } });
  expect(await screen.findByText("saved · just now", undefined, { timeout: 3000 })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalledTimes(1));
});

it("F3: hiding the book within the save's debounce saves the step written with it shown first", async () => {
  const order: string[] = [];
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string }) => {
    order.push(`save:${input.bodyMd}`);
    await new Promise((resolve) => setTimeout(resolve, 50));
    return stepRow(input, input.bodyMd ?? "");
  });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => {
    order.push(`book:${input.visible}`);
    return { session: session({ sourceVisible: input.visible, sourceShownAt: "x" }) };
  });
  const onSession = vi.fn();
  render(<Workbench {...props({ onSession })} />);
  await typeStep(1, "written beside the book");
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "B", ctrlKey: true, shiftKey: true });
  // The Reader covers the book at once...
  expect(onSession).toHaveBeenCalledWith(expect.objectContaining({ sourceVisible: false }));
  // ...and the server hears the step before the book's change.
  await waitFor(() => expect(order).toEqual(["save:written beside the book", "book:false"]), { timeout: 3000 });
});

it("F3: a failing save holds the book's change behind it, so the assistance is never lost", async () => {
  const order: string[] = [];
  api.workbenchSaveStep.mockRejectedValueOnce({ code: "database_locked", message: "locked" })
    .mockImplementation(async (input: { op: string; bodyMd?: string }) => {
      order.push(`save:${input.bodyMd}`);
      return stepRow(input, input.bodyMd ?? "");
    });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => {
    order.push(`book:${input.visible}`);
    return { session: session({ sourceVisible: input.visible }) };
  });
  render(<Workbench {...props()} />);
  await typeStep(1, "beside the book");
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "B", ctrlKey: true, shiftKey: true });
  await waitFor(() => expect(order).toEqual(["save:beside the book", "book:false"]), { timeout: 5000 });
}, 8000);

it("F7: Abandon waits for every queued save before setting the problem aside", async () => {
  const order: string[] = [];
  let releaseFirst!: () => void;
  api.workbenchSaveStep.mockImplementationOnce((input: { op: string; stepId?: string; bodyMd?: string }) => new Promise((resolve) => {
    order.push(`save:${input.stepId}`);
    releaseFirst = () => resolve(stepRow(input, input.bodyMd ?? ""));
  })).mockImplementation(async (input: { op: string; stepId?: string; bodyMd?: string }) => {
    order.push(`save:${input.stepId}`);
    return stepRow(input, input.bodyMd ?? "");
  });
  api.workbenchAbandon.mockImplementation(async () => {
    order.push("abandon");
    return { session: session({ status: "abandoned" }) };
  });
  const onAbandoned = vi.fn();
  render(<Workbench {...props({ onAbandoned, initial: session({ steps: SAVED_STEPS }) })} />);
  await typeStep(1, "one, revised");
  await typeStep(2, "two, revised");
  fireEvent.click(screen.getByRole("button", { name: "more actions" }));
  fireEvent.click(screen.getByRole("menuitem", { name: "Abandon this problem" }));
  await waitFor(() => expect(order).toEqual(["save:a"]));
  await act(async () => releaseFirst());
  await waitFor(() => expect(order).toEqual(["save:a", "save:b", "abandon"]));
  await waitFor(() => expect(onAbandoned).toHaveBeenCalled());
});

it("F7: Abandon with a save still retrying sets nothing aside and says the steps are not saved yet", async () => {
  const onError = vi.fn();
  api.workbenchSaveStep.mockRejectedValue({ code: "database_locked", message: "locked" });
  render(<Workbench {...props({ onError, initial: session({ steps: SAVED_STEPS }) })} />);
  await typeStep(1, "one, revised");
  expect(await screen.findByText("not saved yet — retrying · your text is safe in this window", undefined, { timeout: 3000 })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "more actions" }));
  fireEvent.click(screen.getByRole("menuitem", { name: "Abandon this problem" }));
  await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.stringContaining("not saved yet, so this problem was not set aside")));
  expect(api.workbenchAbandon).not.toHaveBeenCalled();
});

it("F8: a vault switch freezes the steps and saves them against their own vault before it selects the next", async () => {
  const { selectWithDraftFlush } = await import("../../app/vaultTransition");
  const order: string[] = [];
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string }) => {
    order.push(`save:${input.bodyMd}`);
    return stepRow(input, input.bodyMd ?? "");
  });
  const view = render(<Workbench {...props()} />);
  await typeStep(1, "typed just before the switch");
  await act(async () => {
    await selectWithDraftFlush(async () => {
      order.push("select");
      // Frozen: typing during the switch changes nothing.
      fireEvent.change(stepBox(1), { target: { value: "typed during the switch" } });
    });
  });
  expect(order).toEqual(["save:typed just before the switch", "select"]);
  expect(stepBox(1).value).toBe("typed just before the switch");
  // Unmounted after the switch: nothing is sent to the next vault.
  view.unmount();
  await new Promise((resolve) => setTimeout(resolve, 700));
  expect(order).toEqual(["save:typed just before the switch", "select"]);
});

it("F8: a vault switch with steps that cannot be saved does not happen, and editing resumes", async () => {
  const { selectWithDraftFlush } = await import("../../app/vaultTransition");
  api.workbenchSaveStep.mockRejectedValue({ code: "database_locked", message: "locked" });
  render(<Workbench {...props()} />);
  await typeStep(1, "not yet saved");
  const select = vi.fn();
  let refused: unknown = null;
  await act(async () => {
    await selectWithDraftFlush(select).catch((error: unknown) => { refused = error; });
  });
  expect(select).not.toHaveBeenCalled();
  expect(refused).toMatchObject({ code: "not_saved" });
  fireEvent.change(stepBox(1), { target: { value: "still editable" } });
  expect(stepBox(1).value).toBe("still editable");
});

it("F8: closing the window waits for the steps to save before it goes", async () => {
  windowApi.closeHandlers = [];
  let release!: () => void;
  api.workbenchSaveStep.mockImplementation((input: { op: string; bodyMd?: string }) => new Promise((resolve) => {
    release = () => resolve(stepRow(input, input.bodyMd ?? ""));
  }));
  render(<Workbench {...props()} />);
  await waitFor(() => expect(windowApi.closeHandlers.length).toBeGreaterThan(0));
  await typeStep(1, "typed just before closing");
  const closing = windowApi.closeHandlers[windowApi.closeHandlers.length - 1]({ preventDefault: vi.fn() });
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledWith(expect.objectContaining({ bodyMd: "typed just before closing" })));
  expect(windowApi.destroy).not.toHaveBeenCalled();
  await act(async () => { release(); await closing; });
  expect(windowApi.destroy).toHaveBeenCalledTimes(1);
});

it("F9: a bound problem shows the item's whole presentation, the required method's instruction included", () => {
  render(<Workbench {...props({ initial: session({ presentation: { practiceItemId: "pi_514", blocks: [
    { kind: "prompt", markdown: "Find the CDF of X.", label: null },
    { kind: "required_method_instruction", markdown: "Use the law of total probability in your answer.", label: null },
  ] } }) })} />);
  const problem = screen.getByTestId("workbench-presentation");
  expect(problem.textContent).toContain("Find the CDF of X.");
  expect(problem.textContent).toContain("Use the law of total probability in your answer.");
  expect(screen.queryByText(/Let X be Uniform/)).toBeNull();
});

it("re-review F3: a refused step holds hiding the book, so its corrected text is saved with the book shown", async () => {
  // A previous test's closed workbench may still be retrying its own text.
  const seen: string[] = [];
  const mine = () => seen.filter((entry) => entry === "refused" || entry === "save:shortened" || entry.startsWith("book:"));
  const order = { push: (entry: string) => seen.push(entry) };
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string }) => {
    if ((input.bodyMd ?? "").length > 20_000) {
      order.push("refused");
      throw { code: "validation_error", message: "This step is too long to save." };
    }
    order.push(`save:${input.bodyMd}`);
    return stepRow(input, input.bodyMd ?? "");
  });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => {
    order.push(`book:${input.visible}`);
    return { session: session({ sourceVisible: input.visible, sourceShownAt: "x" }) };
  });
  const onSession = vi.fn();
  render(<Workbench {...props({ onSession })} />);
  await typeStep(1, "x".repeat(20_001));
  expect(await screen.findByText(/^not saved \(This step is too long to save\.\)/, undefined, { timeout: 3000 })).toBeTruthy();
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "B", ctrlKey: true, shiftKey: true });
  // The Reader covers the book at once, but the server keeps it shown...
  expect(onSession).toHaveBeenCalledWith(expect.objectContaining({ sourceVisible: false }));
  await new Promise((resolve) => setTimeout(resolve, 100));
  expect(mine()).toEqual(["refused"]);
  // ...until the step written beside it is saved, beside it.
  fireEvent.change(stepBox(1), { target: { value: "shortened" } });
  await waitFor(() => expect(mine()).toEqual(["refused", "save:shortened", "book:false"]), { timeout: 3000 });
  expect(await screen.findByText("saved · just now", undefined, { timeout: 3000 })).toBeTruthy();
});

it("re-review F3: showing the book never waits behind a refused step", async () => {
  const order: string[] = [];
  api.workbenchSaveStep.mockImplementation(async () => {
    order.push("refused");
    throw { code: "validation_error", message: "This step is too long to save." };
  });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => {
    order.push(`book:${input.visible}`);
    return { session: session({ sourceVisible: input.visible }) };
  });
  render(<Workbench {...props({ initial: session({ sourceVisible: false }) })} />);
  await typeStep(1, "x".repeat(20_001));
  await waitFor(() => expect(order).toEqual(["refused"]), { timeout: 3000 });
  fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "B", ctrlKey: true, shiftKey: true });
  await waitFor(() => expect(order).toContain("book:true"), { timeout: 3000 });
});

it("re-review F8: closing with a step that cannot be saved keeps the window open once, then closes on a second request", async () => {
  windowApi.closeHandlers = [];
  const onError = vi.fn();
  api.workbenchSaveStep.mockRejectedValue({ code: "validation_error", message: "This step is too long to save." });
  render(<Workbench {...props({ onError })} />);
  await waitFor(() => expect(windowApi.closeHandlers.length).toBeGreaterThan(0));
  await typeStep(1, "x".repeat(50));
  expect(await screen.findByText(/^not saved \(This step is too long to save\.\)/, undefined, { timeout: 3000 })).toBeTruthy();
  const handler = windowApi.closeHandlers[windowApi.closeHandlers.length - 1];
  await act(async () => { await handler({ preventDefault: vi.fn() }); });
  expect(windowApi.destroy).not.toHaveBeenCalled();
  expect(onError).toHaveBeenCalledWith(expect.stringContaining("Close it again to close anyway"));
  expect(stepBox(1).value).toBe("x".repeat(50));
  await act(async () => { await handler({ preventDefault: vi.fn() }); });
  expect(windowApi.destroy).toHaveBeenCalledTimes(1);
});

// Final verification F8: Leave for now waits for the steps like Abandon and
// closing the window do, so leaving first never strips their protection.
it("final F8: Leave with a refused step stays, says why, and keeps the vault switch and close held; a second Leave leaves and says the text was discarded", async () => {
  const { selectWithDraftFlush } = await import("../../app/vaultTransition");
  windowApi.closeHandlers = [];
  const onLeave = vi.fn();
  const onError = vi.fn();
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string }) => {
    if ((input.bodyMd ?? "").length > 20_000) throw { code: "validation_error", message: "This step is too long to save." };
    return stepRow(input, input.bodyMd ?? "");
  });
  render(<Workbench {...props({ onLeave, onError })} />);
  await waitFor(() => expect(windowApi.closeHandlers.length).toBeGreaterThan(0));
  await typeStep(1, "x".repeat(20_001));
  expect(await screen.findByText(/^not saved \(This step is too long to save\.\)/, undefined, { timeout: 3000 })).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /leave for now/ })); });
  // It stays, and says why in plain words.
  expect(onLeave).not.toHaveBeenCalled();
  expect(await screen.findByText(/This step is too long to save\.\), so you're still here/)).toBeTruthy();
  expect(stepBox(1).value).toBe("x".repeat(20_001));
  // Still mounted, so a vault switch and the window's close stay held.
  const select = vi.fn();
  let refused: unknown = null;
  await act(async () => { await selectWithDraftFlush(select).catch((error: unknown) => { refused = error; }); });
  expect(select).not.toHaveBeenCalled();
  expect(refused).toMatchObject({ code: "not_saved" });
  expect(windowApi.closeHandlers.length).toBeGreaterThan(0);
  // A second Leave leaves anyway, and the discarded text is said, never silent.
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /leave for now/ })); });
  await waitFor(() => expect(onLeave).toHaveBeenCalledTimes(1));
  expect(onError).toHaveBeenCalledWith(expect.stringContaining("its unsaved text was discarded"));
  expect(api.workbenchLeave).toHaveBeenCalledWith({ sessionId: "wb1" });
});

it("final F8: answer box instead waits for the steps the same way", async () => {
  const onAnswerBox = vi.fn();
  api.workbenchSaveStep.mockRejectedValue({ code: "validation_error", message: "This step is too long to save." });
  render(<Workbench {...props({ layout: "full", onAnswerBox, initial: session({ origin: "practice", sourceVisible: false }) })} />);
  await typeStep(1, "x".repeat(20_001));
  expect(await screen.findByText(/^not saved \(This step is too long to save\.\)/, undefined, { timeout: 3000 })).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "answer box instead" })); });
  expect(onAnswerBox).not.toHaveBeenCalled();
  expect(await screen.findByText(/so you're still here/)).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "answer box instead" })); });
  await waitFor(() => expect(onAnswerBox).toHaveBeenCalledTimes(1));
});

// Review F15: the submit names its surface's serve as one pair, or none.
it("final F15: a submit with no serve of its own names none, so the server answers the pair the problem kept", async () => {
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "att_1" }, session: session({ status: "submitted" }), practiceSession: null });
  const onSubmitted = vi.fn();
  render(<Workbench {...props({ onSubmitted, initial: session({ steps: [SAVED_STEPS[0]] }) })} />);
  fireEvent.click(screen.getByRole("button", { name: /^submit/ }));
  await waitFor(() => expect(onSubmitted).toHaveBeenCalled());
  const sent = api.workbenchSubmit.mock.calls[0][0];
  expect("schedulerCandidateId" in sent || "planPresentationId" in sent).toBe(false);
});

// Round 4 F8 (Codex's reproduction): saved work, Leave pressed and its
// response delayed, 20,001 characters typed meanwhile (a step the server
// refuses for good), then the response arrives. The departure froze the
// steps, so nothing typed then was accepted, and what leaves is what is saved.
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

async function rest(ms = 800) {
  await act(async () => { await new Promise((done) => setTimeout(done, ms)); });
}

function refusesLongSteps() {
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string; stepId?: string; kind?: string }) => {
    if ((input.bodyMd ?? "").length > 20_000) throw { code: "validation_error", message: "This step is too long to save." };
    return stepRow(input, input.bodyMd ?? "");
  });
}

async function departWhileTyping(button: RegExp | string, then: ReturnType<typeof vi.fn>, onError: ReturnType<typeof vi.fn>) {
  const pending = deferred<{ session: WorkbenchSessionDto }>();
  api.workbenchLeave.mockReturnValue(pending.promise);
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: button })); });
  await waitFor(() => expect(api.workbenchLeave).toHaveBeenCalledTimes(1));
  // Under way: the steps are read-only and say so.
  expect(stepBox(1).readOnly).toBe(true);
  expect(screen.getByText(/leaving… · editing is paused/)).toBeTruthy();
  const writes = api.workbenchSaveStep.mock.calls.length;
  await typeStep(1, "x".repeat(20_001));
  await rest();
  expect(api.workbenchSaveStep.mock.calls.length).toBe(writes);
  expect(stepBox(1).value).toBe("one");
  await act(async () => { pending.resolve({ session: session() }); });
  await waitFor(() => expect(then).toHaveBeenCalledTimes(1));
  // Nothing was refused or discarded: the steps left exactly as saved.
  expect(onError).not.toHaveBeenCalled();
  expect(screen.queryByText(/not saved/)).toBeNull();
}

it("round 4 F8: Leave freezes the steps while it is under way, so text typed then is never refused and unmounted unseen", async () => {
  refusesLongSteps();
  const onLeave = vi.fn();
  const onError = vi.fn();
  render(<Workbench {...props({ onLeave, onError, initial: session({ steps: [SAVED_STEPS[0]] }) })} />);
  await departWhileTyping(/leave for now/, onLeave, onError);
});

it("round 4 F8: answer box instead freezes the steps the same way", async () => {
  refusesLongSteps();
  const onAnswerBox = vi.fn();
  const onError = vi.fn();
  render(<Workbench {...props({ layout: "full", onAnswerBox, onError, initial: session({ origin: "practice", sourceVisible: false, steps: [SAVED_STEPS[0]] }) })} />);
  await departWhileTyping("answer box instead", onAnswerBox, onError);
});

it("round 4 F8: a departure held by a refusal gives editing back with the first-press message, and a fixed step then leaves", async () => {
  const save = deferred<never>();
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string; stepId?: string; kind?: string }) => {
    if ((input.bodyMd ?? "").length > 20_000) return save.promise;
    return stepRow(input, input.bodyMd ?? "");
  });
  const onLeave = vi.fn();
  render(<Workbench {...props({ onLeave, initial: session({ steps: [SAVED_STEPS[0]] }) })} />);
  await typeStep(1, "x".repeat(20_001));
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /leave for now/ })); });
  // The long write is still in flight: the departure waits, read-only.
  expect(stepBox(1).readOnly).toBe(true);
  expect(screen.getByRole("button", { name: "leaving…" })).toBeTruthy();
  // A second press while it is under way is the same departure.
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "leaving…" })); });
  await act(async () => { save.reject({ code: "validation_error", message: "This step is too long to save." }); });
  expect(await screen.findByText(/This step is too long to save\.\), so you're still here/)).toBeTruthy();
  expect(onLeave).not.toHaveBeenCalled();
  expect(api.workbenchLeave).not.toHaveBeenCalled();
  // Editing is back: the learner shortens the step, it saves, and Leave goes.
  expect(stepBox(1).readOnly).toBe(false);
  await typeStep(1, "shorter");
  await rest();
  expect(await screen.findByText(/^saved/)).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /leave for now/ })); });
  await waitFor(() => expect(onLeave).toHaveBeenCalledTimes(1));
});

// RW4b, Codex review F3: a picked textbook exercise the server found exposed
// at the pick (or again at admission) says why, and that it is practice beside
// the book; unexposed, nothing is added.
it("RW4b: a picked exercise seen since it was offered says why, and that it is practice beside the book", () => {
  const exposure = { exposed: true, reasons: ["source_exposed"], label: "you've recently seen this page or its solution", note: null,
    offeredAs: "practice" as const, exposureRuleVersion: "reading_exposure_v1" };
  const pick = { proposalId: "pp_1", exposure, exposureChecked: "admission" as const, admitted: true, due: false };
  render(<Workbench {...props({ initial: session({ exercisePick: pick }) })} />);
  expect(screen.getByTestId("workbench-exercise-exposure").textContent)
    .toBe("you've recently seen this page or its solution · practice beside the book, not a check on your own");
  cleanup();
  render(<Workbench {...props({ initial: session({ exercisePick: { ...pick, exposure: { ...exposure, exposed: false, reasons: [], label: null, offeredAs: "check_on_your_own" as const } } }) })} />);
  expect(screen.queryByTestId("workbench-exercise-exposure")).toBeNull();
});

// RW4b fix round 4, R6 (Codex final verify F3): the exercise was picked
// unexposed; while it imported the learner read its passage; the admission
// corrects the exposure. The mounted workbench (same problem, same key) shows
// the correction, and keeps the step being typed and its write.
it("R6 (verify F3): the admission's exposure correction reaches the mounted workbench, keeping the unsaved step", async () => {
  const unexposed = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own" as const,
    exposureRuleVersion: "reading_exposure_v1" };
  const pick = { proposalId: "pp_1", exposure: unexposed, exposureChecked: "selection" as const, admitted: false, due: true };
  const first = session({ sourceVisible: false, exercisePick: pick });
  const onSession = vi.fn();
  const view = render(<Workbench {...props({ initial: first, serverSession: first, onSession })} />);
  expect(screen.queryByTestId("workbench-exercise-exposure")).toBeNull();
  await typeStep(1, "3x = 15, so");
  const corrected = session({
    sourceVisible: false, schedulerCandidateId: "cand_admit",
    exercisePick: { ...pick, admitted: true, due: false, exposureChecked: "admission",
      exposure: { exposed: true, reasons: ["source_exposed"], label: "you've recently seen this page or its solution", note: null,
        offeredAs: "practice" as const, exposureRuleVersion: "reading_exposure_v1" } },
  });
  view.rerender(<Workbench {...props({ initial: first, serverSession: corrected, onSession })} />);
  expect(screen.getByTestId("workbench-exercise-exposure").textContent)
    .toBe("you've recently seen this page or its solution · practice beside the book, not a check on your own");
  expect(stepBox(1).value).toBe("3x = 15, so");
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledWith(expect.objectContaining({ bodyMd: "3x = 15, so" })));
});
