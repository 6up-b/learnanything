// Reader RW5d P2: one engine, two hosts (spec_reader_show_me_figures_v1 G-SM9, G-SM11, G-SM13).
//
// The parity corpus holds the text the sidecar's wasmtime runner returned
// for each read; the desktop's engine host (the same bytes under V8's
// WebAssembly) must return the same text, byte for byte. The hostile corpus
// gets the same outcome here as in the sidecar. A tampered engine is refused.
import { describe, expect, it } from "vitest";
import parity from "./sketchParityCorpus.json";
// Read as text and JSON.parse'd: a JSON module import would turn the polluted
// case's "__proto__" key into a prototype (a JSON.parse keeps it an own key).
import hostileText from "./sketchHostileCorpus.json?raw";
import { ENGINE_SHA256, sha256Hex, SKETCH_FUEL_PER_CALL, SKETCH_MEMORY_BYTES, SKETCH_SERIALIZE_TICKS, SketchEngineHost, SketchRunError } from "./sketchEngine";
import { ENGINE_BYTES, newHost, nodeDigest } from "./engineForTests";

type Call = { op: "init" | "step" | "view" | "probes"; params: Record<string, number>; seed?: number; dt?: number; index?: number; count?: number; expect?: string };
const hostile = JSON.parse(hostileText) as { cases: Array<{ name: string; code: string; call?: string; calls?: Call[]; expect: { status: string; result?: unknown } }> };

describe("the pinned engine", () => {
  it("hashes to the pin the sidecar uses", async () => {
    expect(await nodeDigest(ENGINE_BYTES)).toBe(ENGINE_SHA256);
    expect(parity.engine_sha256).toBe(ENGINE_SHA256);
  });

  it("checks the pin in plain TypeScript where Web Crypto is missing", () => {
    expect(sha256Hex(ENGINE_BYTES)).toBe(ENGINE_SHA256);
    expect(sha256Hex(new TextEncoder().encode("abc"))).toBe("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    expect(sha256Hex(new Uint8Array(0))).toBe("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  });

  it("reports the caps compiled into it", async () => {
    const host = await newHost();
    const limits = host.limits();
    expect(limits.memory_bytes).toBe(SKETCH_MEMORY_BYTES);
    expect(limits.ticks_per_call).toBe(SKETCH_FUEL_PER_CALL);
    expect(limits.serialize_ticks).toBe(SKETCH_SERIALIZE_TICKS);
  });

  it("refuses an engine whose digest is not the pin (G-SM13)", async () => {
    const tampered = new Uint8Array(ENGINE_BYTES);
    tampered[tampered.length - 1] ^= 1;
    await expect(SketchEngineHost.create(tampered, { digest: nodeDigest })).rejects.toThrow(/not the pinned/);
  });
});

describe("the parity corpus (G-SM9)", () => {
  for (const testCase of parity.cases) {
    it(`returns the sidecar's text for ${testCase.name}`, async () => {
      const host = await newHost();
      host.load(testCase.code);
      let reads = 0;
      for (const call of testCase.calls as Call[]) {
        if (call.op === "init") host.init(call.params, call.seed ?? 1);
        else if (call.op === "step") host.step(call.params, call.dt ?? 0, call.index ?? 0, call.count ?? 1);
        else {
          const text = call.op === "view" ? host.viewText(call.params, call.index ?? 0) : host.probesText(call.params, call.index ?? 0);
          expect(text).toBe(call.expect);
          reads += 1;
        }
      }
      expect(reads).toBeGreaterThan(0);
    });
  }
});

describe("the hostile corpus (G-SM11)", () => {
  for (const testCase of hostile.cases) {
    it(`${testCase.name}: ${testCase.expect.status}`, async () => {
      const host = await newHost();
      let outcome: { status: string; result?: unknown };
      try {
        host.load(testCase.code);
        let result: unknown = null;
        if (testCase.calls) {
          // A sequence (fix round 4: every init a fresh start; reads within one run).
          for (const call of testCase.calls) {
            if (call.op === "init") host.init(call.params, call.seed ?? 1);
            else if (call.op === "step") host.step(call.params, call.dt ?? 0, call.index ?? 0, call.count ?? 1);
            else result = call.op === "view" ? host.view(call.params, call.index ?? 0) : host.probes(call.params, call.index ?? 0);
          }
        } else {
          host.init({}, 1);
          result = testCase.call === "probes" ? host.probes({}, 0) : host.view({}, 0);
        }
        outcome = { status: "ok", result };
      } catch (caught) {
        outcome = { status: caught instanceof SketchRunError ? caught.kind : "thrown" };
      }
      expect(outcome.status).toBe(testCase.expect.status);
      if ("result" in testCase.expect) expect(outcome.result).toEqual(testCase.expect.result);
    });
  }

  it("parses a polluted result as plain data in this realm", async () => {
    const host = await newHost();
    host.load("function init(){return 1} function view(){return {}} function probes(){ return JSON.parse('{\"__proto__\": {\"isAdmin\": true}}'); }");
    host.init({}, 1);
    const probes = host.probes({}, 0) as Record<string, unknown>;
    expect(({} as Record<string, unknown>).isAdmin).toBeUndefined();
    expect(Object.getPrototypeOf(probes)).toBe(Object.prototype);
  });
});
