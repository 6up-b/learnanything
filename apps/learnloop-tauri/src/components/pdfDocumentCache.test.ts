import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import { acquirePdfDocument, clearPdfDocuments } from "./pdfDocumentCache";

const { getDocument } = vi.hoisted(() => ({ getDocument: vi.fn() }));
vi.mock("pdfjs-dist", () => ({ getDocument }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
const response = () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) });

beforeEach(() => {
  getDocument.mockReset();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response()));
});
afterEach(() => { clearPdfDocuments(); vi.unstubAllGlobals(); });

describe("PDF worker ownership", () => {
  it("destroys a failed parse and permits a fresh request", async () => {
    const parsing = deferred<object>();
    const task = { promise: parsing.promise, destroy: vi.fn().mockRejectedValue(new Error("worker gone")) };
    getDocument.mockReturnValueOnce(task);
    const failed = expect(acquirePdfDocument("bad.pdf")).rejects.toThrow("parse failed");
    await waitFor(() => expect(getDocument).toHaveBeenCalledOnce());
    parsing.reject(new Error("parse failed"));
    await failed;
    expect(task.destroy).toHaveBeenCalledOnce();
    const doc = { numPages: 2 };
    getDocument.mockReturnValueOnce({ promise: Promise.resolve(doc), destroy: vi.fn() });
    expect((await acquirePdfDocument("bad.pdf")).doc).toBe(doc);
  });

  it("clears an old worker without removing a fresh in-flight request for the same URL", async () => {
    const old = deferred<object>();
    const fresh = deferred<object>();
    const oldTask = { promise: old.promise, destroy: vi.fn() };
    getDocument.mockReturnValueOnce(oldTask).mockReturnValueOnce({ promise: fresh.promise, destroy: vi.fn() });
    const oldResult = acquirePdfDocument("shared.pdf");
    const rejected = expect(oldResult).rejects.toThrow("cleared");
    await waitFor(() => expect(getDocument).toHaveBeenCalledTimes(1));
    clearPdfDocuments();
    const freshResult = acquirePdfDocument("shared.pdf");
    await waitFor(() => expect(getDocument).toHaveBeenCalledTimes(2));
    old.resolve({ oldVault: true });
    await rejected;
    expect(acquirePdfDocument("shared.pdf")).toBe(freshResult);
    const doc = { newVault: true };
    fresh.resolve(doc);
    expect((await freshResult).doc).toBe(doc);
    expect(oldTask.destroy).toHaveBeenCalledOnce();
  });

  it("aborts an in-flight fetch on vault change even if the fetch resolves late", async () => {
    const pending = deferred<ReturnType<typeof response>>();
    const fetcher = vi.fn().mockReturnValue(pending.promise);
    vi.stubGlobal("fetch", fetcher);
    const rejected = expect(acquirePdfDocument("old.pdf")).rejects.toThrow("cleared");
    clearPdfDocuments();
    expect(fetcher.mock.calls[0][1].signal.aborted).toBe(true);
    pending.resolve(response());
    await rejected;
    expect(getDocument).not.toHaveBeenCalled();
  });
});
