// Reader RW5d P2: the pinned engine in Node, for the vitest files (never imported by the app).
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { SketchEngineHost } from "./sketchEngine";

// A copy (a Node Buffer's slice is a view: a test that tampers must never change the shared bytes).
export const ENGINE_BYTES: Uint8Array = new Uint8Array(readFileSync(join(__dirname, "sketch-engine.wasm")));

export const nodeDigest = async (bytes: Uint8Array): Promise<string> => createHash("sha256").update(bytes).digest("hex");

export function newHost(): Promise<SketchEngineHost> {
  return SketchEngineHost.create(ENGINE_BYTES, { digest: nodeDigest });
}
