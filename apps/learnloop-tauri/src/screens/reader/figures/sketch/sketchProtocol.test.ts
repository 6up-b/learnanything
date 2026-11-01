// Reader RW5d P2, fix round 4 (the independent sandbox review, finding 3): the
// Worker's narrow protocol is validated at runtime on both sides.
//
// The Worker refuses an unknown operation, a malformed argument or an
// out-of-bounds count before the engine is touched (it never falls back to a
// read); the client refuses a reply whose shape is not the one its request
// expects. The hostile corpus's worker_messages are the shared cases.
import { describe, expect, it } from "vitest";
import hostileText from "./sketchHostileCorpus.json?raw";
import { newHost } from "./engineForTests";
import { sceneDigest, SketchRunError } from "./sketchEngine";
import { answerRequest, parseWorkerRequest, SKETCH_MAX_OUTPUT_CHARS, SKETCH_MAX_SOURCE_BYTES } from "./sketchProtocol";
import { portRunner, type WorkerRequest, type WorkerResponse } from "./sketchRunner";

const corpus = JSON.parse(hostileText) as { worker_messages: Array<{ name: string; message: unknown; expect: "accepted" | "refused" }> };

describe("the Worker's requests", () => {
  for (const testCase of corpus.worker_messages) {
    it(`${testCase.name}: ${testCase.expect}`, () => {
      expect(parseWorkerRequest(testCase.message).ok).toBe(testCase.expect === "accepted");
    });
  }

  it("refuses a program longer than the source cap, counted in UTF-8 bytes", () => {
    const long = "é".repeat(SKETCH_MAX_SOURCE_BYTES / 2 + 1);
    expect(parseWorkerRequest({ id: 1, op: "load", args: [long] }).ok).toBe(false);
    expect(parseWorkerRequest({ id: 1, op: "load", args: ["x".repeat(SKETCH_MAX_SOURCE_BYTES)] }).ok).toBe(true);
  });

  it("answers an unknown operation with a refusal, never a read", async () => {
    const host = await newHost();
    let asked = 0;
    const get = () => { asked += 1; return Promise.resolve(host); };
    const reply = await answerRequest(get, { id: 4, op: "probe", args: [{}, 0] });
    expect(reply).toEqual({ id: 4, ok: false, error: { kind: "input", message: expect.stringContaining("unknown operation") } });
    const unroutable = await answerRequest(get, { op: "read", args: [{}, 0] });
    expect(unroutable.ok).toBe(false);
    expect(unroutable.id).toBe(0);
    expect(asked).toBe(0);  // the engine was never reached
  });

  it("answers a read with the scene, the probes and the digest of the text the engine wrote", async () => {
    const host = await newHost();
    const get = () => Promise.resolve(host);
    const code = "function init(p){return p.k} function view(s){return {viewport:{x:[0,1],y:[0,1]},elements:[]}} function probes(s){return {k:s}}";
    expect((await answerRequest(get, { id: 1, op: "load", args: [code] })).ok).toBe(true);
    expect(await answerRequest(get, { id: 2, op: "init", args: [{ k: 3 }, 1] })).toEqual({ id: 2, ok: true, result: null });
    const reply = await answerRequest(get, { id: 3, op: "read", args: [{ k: 3 }, 0] });
    expect(reply.ok).toBe(true);
    // The engine's own text crosses the channel (the sketch compartment): the client bounds and parses it.
    const result = (reply as { result: { sceneText: string; probesText: string; digest: string } }).result;
    expect(Object.keys(result).sort()).toEqual(["digest", "probesText", "sceneText"]);
    expect(JSON.parse(result.probesText)).toEqual({ k: 3 });
    expect(result.digest).toBe(sceneDigest(result.sceneText, result.probesText));
  });
});

/** A Worker-like port whose replies the test writes. */
function fakePort() {
  const sent: WorkerRequest[] = [];
  const port = {
    onmessage: null as ((event: { data: WorkerResponse }) => void) | null,
    postMessage(message: WorkerRequest) { sent.push(message); },
    terminate() { /* nothing to stop */ },
    reply(data: unknown) { port.onmessage?.({ data: data as WorkerResponse }); },
  };
  return { port, sent };
}

describe("the client's replies", () => {
  it("refuses a read reply without the digest the protocol requires", async () => {
    const { port, sent } = fakePort();
    const runner = portRunner(port);
    const pending = runner.read({}, 0);
    port.reply({ id: sent[0].id, ok: true, result: { sceneText: "{}", probesText: "{}" } });
    await expect(pending).rejects.toThrow(/malformed/);
  });

  it("refuses a read reply carrying objects instead of the engine's text, or text that is not JSON", async () => {
    for (const result of [
      { scene: {}, probes: {}, digest: "a".repeat(32) },
      { sceneText: {}, probesText: "{}", digest: "a".repeat(32) },
      { sceneText: "{", probesText: "{}", digest: "a".repeat(32) },
      { sceneText: "{}", probesText: "{}", digest: "a".repeat(32), extra: "x" },
    ]) {
      const { port, sent } = fakePort();
      const pending = portRunner(port).read({}, 0);
      port.reply({ id: sent[0].id, ok: true, result });
      await expect(pending).rejects.toThrow(/malformed/);
    }
  });

  it("refuses an oversize read before parsing it", async () => {
    const { port, sent } = fakePort();
    const pending = portRunner(port).read({}, 0);
    port.reply({ id: sent[0].id, ok: true, result: { sceneText: `"${"x".repeat(SKETCH_MAX_OUTPUT_CHARS)}"`, probesText: "{}", digest: "a".repeat(32) } });
    await expect(pending).rejects.toThrow(/malformed/);
  });

  it("refuses an init reply that carries a result", async () => {
    const { port, sent } = fakePort();
    const runner = portRunner(port);
    const pending = runner.init({}, 1);
    port.reply({ id: sent[0].id, ok: true, result: { leaked: true } });
    await expect(pending).rejects.toBeInstanceOf(SketchRunError);
  });

  it("refuses a load reply that is not the entry points", async () => {
    const { port, sent } = fakePort();
    const runner = portRunner(port);
    const pending = runner.load("x");
    port.reply({ id: sent[0].id, ok: true, result: { init: "yes" } });
    await expect(pending).rejects.toThrow(/malformed/);
  });

  it("names an unknown error kind as an error and keeps a bounded message", async () => {
    const { port, sent } = fakePort();
    const runner = portRunner(port);
    const pending = runner.step({}, 1, 0, 1);
    port.reply({ id: sent[0].id, ok: false, error: { kind: "<script>", message: "m".repeat(10_000) } });
    const caught = await pending.catch((error: unknown) => error);
    expect(caught).toBeInstanceOf(SketchRunError);
    expect((caught as SketchRunError).kind).toBe("error");
    expect((caught as SketchRunError).message.length).toBeLessThanOrEqual(600);
  });

  it("ignores a reply to no request, and one that is not an object", async () => {
    const { port, sent } = fakePort();
    const runner = portRunner(port);
    const pending = runner.read({}, 0);
    port.reply({ id: 999, ok: true, result: { sceneText: "{}", probesText: "{}", digest: "0".repeat(32) } });
    port.reply("not a reply");
    port.reply(null);
    port.reply({ id: sent[0].id, ok: true, result: { sceneText: '{"viewport":1}', probesText: "{}", digest: "a".repeat(32) } });
    await expect(pending).resolves.toEqual({ scene: { viewport: 1 }, probes: {}, digest: "a".repeat(32) });
  });
});
