// Codex review of V4, F11: every media target §2.3 lifts reaches the host through the real Markdown pipeline (the
// desktop's MarkdownMath, whose URL filter empties an `asset:` or `llpdf:` target), as an image or as a link.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveCredential } from "../store/credential";
import { PhoneMarkdown } from "./PageImage";
import { withPhoneMedia } from "./readerModel";

const NAME = `sha256-${"ab".repeat(32)}`;
let asked: string[];

beforeEach(async () => {
  asked = [];
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    asked.push(String(input));
    return new Response(new Blob([new Uint8Array([137, 80, 78, 71])], { type: "image/png" }), { status: 200 });
  }));
  // jsdom has no blob URLs; this file's own worker gets them.
  Object.assign(URL, { createObjectURL: () => "blob:fake", revokeObjectURL: () => undefined });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("a prompt's media on the phone (§2.3)", () => {
  it("an asset:// image the eligibility admits is fetched from the host", async () => {
    render(<PhoneMarkdown value={`Read the graph.\n\n![graph](asset://localhost/vault/canonical-sources/raw/${NAME})`} />);
    await waitFor(() => expect(asked).toEqual([`/api/v1/assets/${NAME}`]));
    expect(await screen.findByRole("img", { name: "graph" })).toBeTruthy();
  });

  it("a vault-path image and an asset:// link are the same stored image", async () => {
    render(<PhoneMarkdown value={`![a](canonical-sources/raw/${NAME}) and [the figure](asset://localhost/vault/canonical-sources/raw/${NAME})`} />);
    await waitFor(() => expect(asked).toEqual([`/api/v1/assets/${NAME}`, `/api/v1/assets/${NAME}`]));
  });

  it("an llpdf: image is its page; an llpdf: link opens its page on demand", async () => {
    render(<PhoneMarkdown value={`![page two](llpdf://localhost/${NAME}#page=2)`} />);
    await waitFor(() => expect(asked).toHaveLength(1));
    expect(asked[0]).toMatch(new RegExp(`^/api/v1/reader/page/${NAME}/1\\?w=(720|1080)$`));
    cleanup();
    asked = [];
    render(<PhoneMarkdown value={`See [page 3](llpdf://localhost/${NAME}#page=3).`} />);
    expect(asked).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "page 3" }));
    await waitFor(() => expect(asked).toHaveLength(1));
    expect(asked[0]).toMatch(new RegExp(`^/api/v1/reader/page/${NAME}/2\\?w=`));
  });

  it("anything else is left as it was: a remote image is a link, an llpdf: link naming no stored file too", () => {
    expect(withPhoneMedia("![x](https://example.com/x.png) [p](llpdf://source/abc#page=3)"))
      .toBe("![x](https://example.com/x.png) [p](llpdf://source/abc#page=3)");
    expect(withPhoneMedia(`[ref]: asset://localhost/vault/canonical-sources/raw/${NAME}`)).toBe(`[ref]: #llasset/${NAME}`);
    render(<PhoneMarkdown value="![remote](https://example.com/x.png)" />);
    expect(asked).toEqual([]);
    expect(screen.getByRole("link", { name: "remote" })).toBeTruthy();
  });
});
