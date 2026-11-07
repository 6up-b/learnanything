// Codex review of V4, F11: every media target §2.3 lifts reaches the host through the real Markdown pipeline (the
// desktop's MarkdownMath, whose URL filter empties an `asset:` or `llpdf:` target), as an image or as a link.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveCredential } from "../store/credential";
import { PhoneMarkdown } from "./PageImage";
import { phoneUrlTransform } from "./readerModel";

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
    expect(phoneUrlTransform("https://example.com/x.png")).toBe("https://example.com/x.png");
    // An llpdf: link naming no stored file gets the renderer's own filter (an unknown scheme is emptied).
    expect(phoneUrlTransform("llpdf://source/abc#page=3")).toBe("");
    expect(phoneUrlTransform(`asset://localhost/vault/canonical-sources/raw/${NAME}`)).toBe(`#llasset/${NAME}`);
    render(<PhoneMarkdown value="![remote](https://example.com/x.png)" />);
    expect(asked).toEqual([]);
    expect(screen.getByRole("link", { name: "remote" })).toBeTruthy();
  });

  // Codex re-review F15: only parsed link and image destinations change; a literal example stays the book's text.
  it("a media link written inside inline code is shown as written and fetches nothing", () => {
    const literal = `![graph](asset://localhost/vault/canonical-sources/raw/${NAME})`;
    const { container } = render(<PhoneMarkdown value={`Write it as \`${literal}\` in a note.`} />);
    expect(container.querySelector("code")?.textContent).toBe(literal);
    expect(container.textContent).not.toContain("#llasset/");
    expect(asked).toEqual([]);
  });

  it("a fenced code example keeps its page link, reference definition and autolink as written", () => {
    const body = [
      `![p](llpdf://localhost/${NAME}#page=2)`,
      `[r]: asset://localhost/vault/canonical-sources/raw/${NAME}`,
      `<llpdf://localhost/${NAME}#page=3>`
    ].join("\n");
    const { container } = render(<PhoneMarkdown value={"```md\n" + body + "\n```"} />);
    expect(container.querySelector("pre code")?.textContent).toBe(body + "\n");
    expect(container.textContent).not.toMatch(/#ll(page|asset)\//);
    expect(asked).toEqual([]);
  });

  it("outside code a reference-style image and an autolinked page still open from the host", async () => {
    render(<PhoneMarkdown value={`![fig][r]\n\n[r]: asset://localhost/vault/canonical-sources/raw/${NAME}`} />);
    await waitFor(() => expect(asked).toEqual([`/api/v1/assets/${NAME}`]));
    cleanup();
    asked = [];
    render(<PhoneMarkdown value={`See <llpdf://localhost/${NAME}#page=3>.`} />);
    fireEvent.click(screen.getByRole("button"));
    await waitFor(() => expect(asked).toHaveLength(1));
    expect(asked[0]).toMatch(new RegExp(`^/api/v1/reader/page/${NAME}/2\\?w=`));
  });
});
