// The desks in jsdom with their real bodies (spec §21.1's proofs): DeskShell with no pane stand-in, so a
// source window is the real SourceWindow and the Reader's source pane inside it, every read and write going
// through the app's api client to a fake sidecar. The fake answers from the harness's synthetic workspace
// (fakeCore.ts) unless a test answers a command itself. A test file routes `@tauri-apps/api/core` here:
//
//   vi.mock("@tauri-apps/api/core", () => ({
//     invoke: async (command: string, args?: unknown) => (await import("../../fixtures/desks/realDesk")).core.invoke(command, args as never),
//     convertFileSrc: (path: string) => path,
//   }));
//
// (each call imports this module when it is made: a factory that imported it would wait on the client, which
// imports the mocked module, which waits on the factory).
import { act, render } from "@testing-library/react";
import type { DeskStateDto, PadViewDto } from "../../api/dto";
import { Poller } from "../../api/poller";
import { clear as clearQueryCache } from "../../api/queryCache";
import { DeskShell, LIVE_DESK_TRANSPORT, type DeskShellProps, type DeskTransport } from "../../screens/desks/DeskShell";
import { convertFileSrc as fixtureFileSrc, invoke as fixtureInvoke } from "./fakeCore";
import { fixturePads } from "./pads";
import { FixtureDeskServer, fixtureDeskState } from "./workspace";

export type Answer = (input: Record<string, unknown>) => unknown;

/** Every command the desks sent, in order, with its input. */
export const sent: Array<{ command: string; input: Record<string, unknown> }> = [];
/** A test's own answers, by command (cleared by `resetSidecar`). */
export const answers = new Map<string, Answer>();

/** The whole app mounted over the desks' fixture (realApp.tsx): a command neither the test nor the fixture answers
 *  stays pending, as a slow sidecar's would, instead of failing every screen the app shows around the desks. */
export const unknownCommands = { pending: false };

async function invoke<T>(command: string, args: { input?: Record<string, unknown> } = {}): Promise<T> {
  const input = args.input ?? {};
  sent.push({ command, input });
  const own = answers.get(command);
  if (own) return (await own(input)) as T;
  try {
    return await fixtureInvoke<T>(command, args as Record<string, unknown>);
  } catch (error) {
    if (unknownCommands.pending && (error as { code?: string } | null)?.code === "not_in_fixture") return new Promise<T>(() => undefined);
    throw error;
  }
}

/** What `@tauri-apps/api/core` resolves to in a test file that mounts the real desks. */
export const core = { invoke, convertFileSrc: fixtureFileSrc };

export function resetSidecar(): void {
  sent.length = 0;
  answers.clear();
  unknownCommands.pending = false;
  // The app's cached reads (contracts, guide plans, readings) outlive a render: each test starts with none.
  clearQueryCache();
}

/** The inputs of every call of one command. */
export function inputsOf(command: string): Array<Record<string, unknown>> {
  return sent.filter((call) => call.command === command).map((call) => call.input);
}

/** A workspace of one desk holding the given windows (one per slot), for a test that needs fewer windows. */
export function oneDesk(windows: DeskStateDto["desks"][number]["slots"][number]["windows"][]): DeskStateDto {
  const state = fixtureDeskState();
  const first = state.desks[0];
  return { ...state, desks: [{ ...first, focusWindowId: windows[0]?.[0]?.windowId ?? null, slots: windows.map((each, slot) => ({ slot, windows: each })) }] };
}

/** A Storage in memory (jsdom's own may be missing under node's): the desks remember the current desk in it. */
export function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => void values.delete(key),
    setItem: (key: string, value: string) => void values.set(key, String(value)),
  };
}

let mounted = 0;

/** Mounts the desks over a fresh fixture server (its own desks and pads), with a poller the test ticks. */
export function mountRealDesk(options: { state?: DeskStateDto; pads?: PadViewDto[]; props?: Partial<DeskShellProps> } = {}) {
  const server = new FixtureDeskServer(options.state ?? fixtureDeskState(), options.pads ?? fixturePads());
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  const onError = (message: string) => errors.push(message);
  const errors: string[] = [];
  const vaultKey = `real-desk-${++mounted}`;
  // The library and readings come through the client as in the app; the desks and pads are this server's.
  const transport: DeskTransport = {
    ...LIVE_DESK_TRANSPORT,
    state: async () => server.state(),
    apply: async (input: Parameters<FixtureDeskServer["apply"]>[0]) => server.apply(input),
    applyPad: async (input: Parameters<FixtureDeskServer["applyPad"]>[0]) => server.applyPad(input),
    padGet: async ({ padId }: { padId: string }) => server.padGet(padId),
  };
  const ui = (props: Partial<DeskShellProps> = {}) => (
    <DeskShell vaultKey={vaultKey} onError={onError} transport={transport} poller={poller} initialViewport={{ width: 1600, height: 960 }} {...options.props} {...props} />
  );
  const view = render(ui());
  /** The desks rendered again by their parent, with these props changed (as the app does). */
  const rerender = (props: Partial<DeskShellProps>) => view.rerender(ui(props));
  return { server, poller, errors, view, rerender };
}

/** Lets the desks' and the Reader's reads land (fake timers advanced a little at a time). */
export async function settleDesk(ms = 0, rounds = 8, advance: (ms: number) => Promise<unknown> | unknown = () => undefined): Promise<void> {
  for (let i = 0; i < rounds; i += 1) {
    await act(async () => {
      await advance(i === 0 ? ms : 20);
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}
