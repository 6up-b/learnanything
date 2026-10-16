// Types for the few Node built-ins the vitest lints read (the app ships no
// @types/node; vitest runs in Node, where these exist at runtime). The Reader
// lints read CSS this way because vitest turns CSS imports into empty modules.
declare module "node:fs" {
  export function readFileSync(path: string, encoding: "utf8"): string;
  export function writeFileSync(path: string, data: string, encoding: "utf8"): void;
}
declare module "node:path" {
  export function join(...parts: string[]): string;
}
declare const __dirname: string;
/** The PDF selection contract test rewrites its fixture on request. */
declare const process: { env: Record<string, string | undefined> };
