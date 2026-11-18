// Stands in for @tauri-apps/api/core: `invoke` goes to the walk bridge, which
// does for each command what src-tauri/src/commands.rs does.
import { BRIDGE, post } from "./bridge";

export type InvokeArgs = Record<string, unknown>;

export async function invoke<T>(cmd: string, args: InvokeArgs = {}): Promise<T> {
  return post<T>("/invoke", { command: cmd, args });
}

/** Tauri maps `<protocol>://localhost/<name>` to a Rust handler (llpdf, llmedia);
 * the bridge serves the same store files under one path per protocol. */
export function convertFileSrc(filePath: string, protocol = "asset"): string {
  return `${BRIDGE}/protocol/${encodeURIComponent(protocol)}/${encodeURIComponent(filePath)}`;
}
