// The desktop's kind table is generated from the backend's (SOURCE_KINDS), and
// every place that accepts a source file reads it: a drop and the file picker
// accepted .png but not .rst, a pasted path neither, while the classifier
// takes both.
import { describe, expect, it, vi } from "vitest";

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("@tauri-apps/api/webview", () => ({ getCurrentWebview: () => ({ onDragDropEvent: async () => () => {} }) }));

import { looksLikeSource } from "../app/useGlobalAdd";
import { isSupportedSourceFile } from "../components/useSourceFileDrop";
import { SOURCE_FILE_EXTENSIONS, SOURCE_KINDS, sourceKindRow } from "./sourceKinds";

describe("the generated kind table", () => {
  it("names the seven kinds the classifier returns", () => {
    expect(SOURCE_KINDS.map((kind) => kind.category)).toEqual([
      "web", "arxiv", "pdf", "youtube", "textfile", "audio", "image"
    ]);
    expect(sourceKindRow("image")?.label).toBe("image");
    expect(sourceKindRow("bogus")).toBeNull();
  });

  it.each([...SOURCE_FILE_EXTENSIONS])("lets a dropped or picked %s file in", (extension) => {
    expect(isSupportedSourceFile(`/home/me/books/name${extension.toUpperCase()}`)).toBe(true);
  });

  it.each([...SOURCE_FILE_EXTENSIONS])("takes a pasted %s path as a source", (extension) => {
    expect(looksLikeSource(`/home/me/books/name${extension}`)).toBe(true);
  });

  it("refuses a suffix no kind reads", () => {
    expect(isSupportedSourceFile("/home/me/books/name.docx")).toBe(false);
    expect(looksLikeSource("/home/me/books/name.docx")).toBe(false);
  });
});
