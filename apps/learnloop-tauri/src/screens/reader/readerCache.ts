import { getOrFetch, type QueryKey, type QueryTag } from "../../api/queryCache";
import { readerTag } from "../../api/queryTags";

// Per-source reads the Reader opens imperatively (render view, guide plan,
// progress, PDF/watch manifests, ask history, annotations) go through the
// query cache with a freshness window instead of a hook: openSource is a
// sequence with side effects, not a render-time subscription. Reader mutation
// wrappers invalidate the `reader:<sourceId>` tag, so a re-read after a
// mutation always fetches; within the window a re-open (returning to this
// tab) is served from memory.
export const READER_CACHE_MS = 10 * 60_000;

export interface SourceReadOptions {
  /** Learner or vault state the read depends on besides its source. */
  readonly tags?: readonly QueryTag[];
  /** Fetch even when the cached result is still fresh. */
  readonly force?: boolean;
}

export function cachedSourceRead<T>(
  sourceId: string,
  key: QueryKey,
  fetcher: () => Promise<T>,
  options: SourceReadOptions = {}
): Promise<T> {
  return getOrFetch(key, fetcher, {
    tags: [readerTag(sourceId), ...(options.tags ?? [])],
    staleAfterMs: READER_CACHE_MS,
    force: options.force
  });
}
