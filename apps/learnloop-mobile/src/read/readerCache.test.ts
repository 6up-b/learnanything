// §5.4: what the Reader keeps is what was opened plus one ahead; a new mark on the desktop (the reading's
// protection changed) drops everything kept of that reading, its page images included; a 401 drops it all.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveCredential } from "../store/credential";
import { clearDisplayCache, getSection, PAGE_CACHE } from "../store/displayCache";
import { cachedGuide, cachedSection, loadGuide, loadSection } from "./readerCache";

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

  it("a reading the host now withholds whole leaves nothing on the phone to reopen offline (Codex review F2)", async () => {
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
      const method = JSON.parse(String(init?.body)).method;
      const result = method === "reader.guide_plan"
        ? { version: 1, extractionId: "ext1", sections: [{ id: "u1", label: "1 Vectors", spanIds: ["b1"] }], cues: [] }
        : reply([]);
      return new Response(JSON.stringify({ ok: true, result }), { status: 200 });
    }));
    await loadSection("ext1", "u1");
    await loadGuide("ext1");
    await expect(cachedGuide("ext1")).resolves.toMatchObject({ guide: { extractionId: "ext1" } });
    const refused = () => new Response(JSON.stringify({ ok: false, error: { code: "held_out_material", message: "held out", retryable: false, details: {} } }), { status: 409 });
    vi.stubGlobal("fetch", vi.fn(async () => refused()));
    await expect(loadSection("ext1", "u1")).rejects.toMatchObject({ code: "held_out_material" });
    expect(deleted).toContain(PAGE_CACHE);
    await expect(cachedSection("ext1", "u1")).resolves.toBeNull();
    // The guide's refusal drops its copy too.
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
      const method = JSON.parse(String(init?.body)).method;
      return method === "reader.guide_plan" ? refused() : new Response(JSON.stringify({ ok: true, result: reply([]) }), { status: 200 });
    }));
    await loadSection("ext1", "u1");
    await expect(loadGuide("ext1")).rejects.toMatchObject({ code: "held_out_material" });
    await expect(cachedGuide("ext1")).resolves.toEqual({ guide: null, progress: null });
    await expect(cachedSection("ext1", "u1")).resolves.toBeNull();
    // Then with the desktop away, nothing of it opens (the guide's copy is gone too, above; one offline try here,
    // as the client's retries back off for seconds).
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("offline"); }));
    await expect(loadSection("ext1", "u1")).rejects.toMatchObject({ code: "desktop_offline" });
  });

  it("revocation clears the sections and the page images", async () => {
    host([]);
    await loadSection("ext1", "u1");
    await clearDisplayCache();
    expect(deleted).toContain(PAGE_CACHE);
    await expect(getSection({ extractionId: "ext1", revision: "rv1", sectionId: "u1" })).resolves.toBeNull();
  });
});
