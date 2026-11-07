// §5.4: what the Reader keeps is what was opened plus one ahead; a new mark on the desktop (the reading's
// protection changed) drops everything kept of that reading, its page images included; a 401 drops it all.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveCredential } from "../store/credential";
import { clearDisplayCache, getSection, PAGE_CACHE } from "../store/displayCache";
import { loadSection } from "./readerCache";

const reply = (heldOut: string[]) => ({
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c", status: "ok", layers: {}, blocks: [{ displayNodeId: "n1", spanId: "b1", markdown: "text" }],
  protection: { withheld: false, heldOutSpanIds: heldOut, message: heldOut.length ? "held" : null }
});

let deleted: string[];

beforeEach(async () => {
  deleted = [];
  vi.stubGlobal("caches", { delete: async (name: string) => { deleted.push(name); return true; } });
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

afterEach(() => vi.unstubAllGlobals());

function host(heldOut: string[]) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ ok: true, result: reply(heldOut) }), { status: 200 })));
}

describe("the Reader's display cache (§3.2, §5.4)", () => {
  it("keeps an opened section and reads it back with the desktop away", async () => {
    host([]);
    await loadSection("ext1", "u1");
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("offline"); }));
    const loaded = await loadSection("ext1", "u1");
    expect(loaded.stale).toBe(true);
    expect(loaded.section.blocks[0].markdown).toBe("text");
  });

  it("a changed protection drops the reading's sections and every page image", async () => {
    host([]);
    await loadSection("ext1", "u1");
    await loadSection("ext1", "u2");
    host(["b9"]);
    await loadSection("ext1", "u1");
    expect(deleted).toContain(PAGE_CACHE);
    await expect(getSection({ extractionId: "ext1", revision: "rv1", sectionId: "u2" })).resolves.toBeNull();
  });

  it("revocation clears the sections and the page images", async () => {
    host([]);
    await loadSection("ext1", "u1");
    await clearDisplayCache();
    expect(deleted).toContain(PAGE_CACHE);
    await expect(getSection({ extractionId: "ext1", revision: "rv1", sectionId: "u1" })).resolves.toBeNull();
  });
});
