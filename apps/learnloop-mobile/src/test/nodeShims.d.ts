// Types for the few Node built-ins the phone's contract and lint tests use (the app ships no
// @types/node; vitest runs in Node, where these exist). The desktop keeps the same kind of shim
// (`apps/learnloop-tauri/src/testNodeShims.d.ts`).
declare module "node:fs" {
  export function existsSync(path: string): boolean;
  export function mkdirSync(path: string, options: { recursive: true }): void;
  export function readFileSync(path: string, encoding: "utf8"): string;
  export function readdirSync(path: string): string[];
  export function statSync(path: string): { isDirectory(): boolean; isFile(): boolean };
  export function writeFileSync(path: string, data: string): void;
}
declare module "node:path" {
  export function dirname(path: string): string;
  export function join(...parts: string[]): string;
  export function resolve(...parts: string[]): string;
  export function relative(from: string, to: string): string;
}
declare module "node:url" {
  export function fileURLToPath(url: string | URL): string;
}
declare const process: { env: Record<string, string | undefined> };
