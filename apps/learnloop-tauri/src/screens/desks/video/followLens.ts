// Follow-along's mark on a book window (spec §7.5; RD10): the followed passage in cyan, laid over whatever lens the
// window already has (the goal lens). One composed lens per window, made again only when either part changes, so the
// Reader re-renders only for a new passage.
import type { ReaderLens } from "../../ReaderScreen";

export class FollowLenses {
  private made = new Map<string, { base: ReaderLens | null; spanId: string | null; lens: ReaderLens | null }>();

  lensFor(windowId: string, base: ReaderLens | null, spanId: string | null): ReaderLens | null {
    const known = this.made.get(windowId);
    if (known && known.base === base && known.spanId === spanId) return known.lens;
    const lens = spanId === null ? base : {
      ...(base ?? {}),
      className: (span: string, state: { annotated: boolean; active: boolean }) => {
        const own = base?.className?.(span, state);
        return span === spanId ? `${own ? `${own} ` : ""}followed` : own;
      },
    };
    this.made.set(windowId, { base, spanId, lens });
    return lens;
  }
}
