// Places and stacks (mobile v2 §4.2): four tabs, a stack of screens in each, and the current view
// mirrored in the URL fragment so a reload or a cold start opens the same tab. No router library.
//
// A fragment never brings back a screen whose opening writes something: a question's opening is
// its serve, and a feedback's opening is recorded. Those come back from the host's checkpoint and
// a pending submit, as M2a built it, so a reload never serves a question twice (see App.tsx).

export type Tab = "today" | "read" | "capture" | "progress";

export interface TabSpec {
  readonly tab: Tab;
  /** What the bar shows. */
  readonly label: string;
  /** What VoiceOver reads, and a test finds. */
  readonly name: string;
  /** The screen's title, announced when it opens. */
  readonly title: string;
}

/** Today · Read · + · Progress, the + centred because capture is the phone's most-used verb. */
export const TABS: readonly TabSpec[] = [
  { tab: "today", label: "Today", name: "Today", title: "Today" },
  { tab: "read", label: "Read", name: "Read", title: "Read" },
  { tab: "capture", label: "+", name: "Capture", title: "Capture" },
  { tab: "progress", label: "Progress", name: "Progress", title: "Progress" }
];

const TAB_NAMES = new Set<string>(TABS.map((spec) => spec.tab));

/** `#/read/<extraction>/<section>` → `{ tab: "read", path: [extraction, section] }`. Anything else is Today. */
export function parseFragment(hash: string): { tab: Tab; path: string[] } {
  const parts = hash.replace(/^#\/?/, "").split("/").filter(Boolean).map((part) => {
    try {
      return decodeURIComponent(part);
    } catch {
      return part;
    }
  });
  const [head, ...path] = parts;
  if (head && TAB_NAMES.has(head)) return { tab: head as Tab, path };
  return { tab: "today", path: [] };
}

export function fragmentFor(tab: Tab, path: readonly string[] = []): string {
  return `#/${[tab, ...path].map((part) => encodeURIComponent(part)).join("/")}`;
}

/** Mirror the view without adding history: the app has no browser chrome to go back with. */
export function writeFragment(tab: Tab, path: readonly string[] = [], location: Pick<Location, "pathname" | "search" | "hash"> = window.location): void {
  const next = fragmentFor(tab, path);
  if (location.hash === next) return;
  window.history.replaceState(window.history.state, "", `${location.pathname}${location.search}${next}`);
}

/** A stack of screens in one tab. Its root never pops. */
export interface Stack<R> {
  readonly routes: readonly [R, ...R[]];
}

export function stackOf<R>(root: R): Stack<R> {
  return { routes: [root] };
}

export function push<R>(stack: Stack<R>, route: R): Stack<R> {
  return { routes: [...stack.routes, route] };
}

export function pop<R>(stack: Stack<R>): Stack<R> {
  if (stack.routes.length === 1) return stack;
  return { routes: stack.routes.slice(0, -1) as unknown as [R, ...R[]] };
}

export function top<R>(stack: Stack<R>): R {
  return stack.routes[stack.routes.length - 1];
}
