// Search in context (spec §9.3): `/`, the shelf's "/ switch", the Find verb, the pad menu's insert mode.
// Words come back at once from `search.everything`; the meaning pass runs as a job, polled through the one
// poller, and merges in with a quiet tag; a group that cannot be searched says why. ↑↓ choose, ↵ opens
// beside the focus (or inserts, in insert mode), tab shows a group's other rows, esc closes. The rofi
// animation: the backdrop fades in, the panel pops from 85 %, the selection block glides between rows, and
// closing is a quick fade with a slight shrink; reduced motion removes all of it.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { SearchEverythingDto, SearchEverythingInput, SearchGroupDto, SearchJobDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import type { Timers } from "../keys/router";
import { meaningNote, selectableRows, shownGroups, type OpenWindow, type SearchRow } from "./model";

export interface SearchApi {
  searchEverything(input: SearchEverythingInput): Promise<SearchEverythingDto>;
  searchJob(input: { jobId: string }): Promise<SearchJobDto>;
}

/** Words are searched this long after the last keystroke, so typing sends one search, not one per key. */
export const SEARCH_DEBOUNCE_MS = 120;
/** The close animation's length (spec §4.3). */
export const SEARCH_CLOSE_MS = 140;

export interface SearchPanelProps {
  api: SearchApi;
  poller: Poller;
  timers: Timers;
  deskId: string | null;
  open: OpenWindow[];
  deskTitle: (deskId: string | null) => string;
  initialQuery?: string;
  /** Insert mode (the pad menu's "a piece of another source…"): ↵ inserts the row instead of opening it. */
  insert?: ((row: SearchRow) => void) | null;
  reducedMotion: boolean;
  onOpenRow: (row: SearchRow) => void;
  onClose: () => void;
}

export function SearchPanel({ api, poller, timers, deskId, open, deskTitle, initialQuery = "", insert = null, reducedMotion, onOpenRow, onClose }: SearchPanelProps) {
  const [query, setQuery] = useState(initialQuery);
  const [words, setWords] = useState<SearchEverythingDto | null>(null);
  const [meaning, setMeaning] = useState<SearchGroupDto[]>([]);
  const [meaningPending, setMeaningPending] = useState(false);
  // The meaning job's own account: the groups it had no search for, and how it failed when it did.
  const [meaningUnavailable, setMeaningUnavailable] = useState<Array<{ group: string; reason: string }>>([]);
  const [meaningFailure, setMeaningFailure] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState(0);
  const [closing, setClosing] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const searchSeq = useRef(0);
  const stopMeaning = useRef<(() => void) | null>(null);

  useEffect(() => {
    inputRef.current?.focus({ preventScroll: true });
  }, []);

  // The words, once typing pauses. One live generation: every query change (a cleared one too) and the
  // panel's closing make any older answer stale, and a stale answer neither shows nor starts a poll.
  useEffect(() => {
    const trimmed = query.trim();
    const seq = ++searchSeq.current;
    stopMeaning.current?.();
    stopMeaning.current = null;
    setMeaning([]);
    setMeaningPending(false);
    setMeaningUnavailable([]);
    setMeaningFailure(null);
    if (trimmed.replace(/\s+/g, " ").length < 2) {
      setWords(null);
      setFailure(null);
      return () => {
        searchSeq.current += 1;
      };
    }
    const handle = timers.set(() => {
      void api.searchEverything({ query: trimmed.slice(0, 200), deskId }).then(
        (found) => {
          if (seq !== searchSeq.current) return;
          setWords(found);
          setFailure(null);
          setSelected(0);
          if (found.meaning.status === "pending" && found.meaning.jobId) {
            const jobId = found.meaning.jobId;
            setMeaningPending(true);
            stopMeaning.current = poller.register<SearchJobDto>({
              key: `search-job:${jobId}`,
              request: () => api.searchJob({ jobId }),
              onResult: (job) => {
                if (seq !== searchSeq.current) return { done: true };
                if (job.done) {
                  setMeaningPending(false);
                  setMeaning(job.groups);
                  setMeaningUnavailable(job.unavailable ?? []);
                  if (job.status !== "done") setMeaningFailure(job.error?.message ?? (job.status === "expired" ? "it finished while the panel was away" : "it stopped"));
                }
                return { done: job.done };
              },
              onError: (error: unknown) => {
                if (seq !== searchSeq.current) return;
                setMeaningPending(false);
                setMeaningFailure(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error));
              },
            });
          }
        },
        (error: unknown) => {
          if (seq !== searchSeq.current) return;
          setWords(null);
          setFailure(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error));
        },
      );
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      timers.clear(handle);
      searchSeq.current += 1;
    };
  }, [query, deskId, api, poller, timers]);
  useEffect(() => () => stopMeaning.current?.(), []);

  const groups = useMemo(
    () => shownGroups({ query, open, words, meaning, meaningPending, expanded, deskTitle }),
    [query, open, words, meaning, meaningPending, expanded, deskTitle],
  );
  const rows = useMemo(() => selectableRows(groups), [groups]);
  const current = rows[Math.min(selected, rows.length - 1)] ?? null;

  // The selection block glides to the selected row (its top is animated, not jumped).
  const rowEls = useRef(new Map<string, HTMLElement>());
  const listRef = useRef<HTMLDivElement | null>(null);
  const [block, setBlock] = useState<{ top: number; height: number } | null>(null);
  useLayoutEffect(() => {
    const element = current ? rowEls.current.get(current.key) : null;
    if (!element) {
      setBlock(null);
      return;
    }
    setBlock({ top: element.offsetTop, height: element.offsetHeight });
    element.scrollIntoView?.({ block: "nearest" });
  }, [current, groups]);

  const close = () => {
    if (closing) return;
    if (reducedMotion) {
      onClose();
      return;
    }
    setClosing(true);
    timers.set(onClose, SEARCH_CLOSE_MS);
  };

  const choose = (row: SearchRow | null) => {
    if (!row) return;
    if (insert && row.kind === "result") insert(row);
    else onOpenRow(row);
    close();
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSelected((index) => Math.min(rows.length - 1, index + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setSelected((index) => Math.max(0, index - 1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(current);
    } else if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      close();
    } else if (event.key === "Tab") {
      event.preventDefault();
      const group = groups.find((each) => each.rows.some((row) => row.key === current?.key)) ?? groups.find((each) => each.hidden > 0);
      if (group) setExpanded((now) => new Set([...now, group.id]));
    }
  };

  const note = meaningNote(words, meaningUnavailable);
  const motion = reducedMotion ? " still" : "";
  return (
    <div className={`desk-search-backdrop${closing ? " closing" : ""}${motion}`} data-desk-search="" onMouseDown={(event) => {
      if (event.target === event.currentTarget) close();
    }}>
      <div className={`desk-search${closing ? " closing" : ""}${motion}`} role="dialog" aria-label="search in context" onKeyDown={onKeyDown}>
        <div className="desk-search-in">
          <span className="g">⌕</span>
          <input
            ref={inputRef}
            value={query}
            placeholder="search every source, note, pad, thread and past exchange"
            aria-label="search every source, note, pad, thread and past exchange"
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <div className="desk-search-list" ref={listRef}>
          {block ? <div className="desk-search-sel" style={{ top: block.top, height: block.height }} /> : null}
          {groups.map((group) => (
            <div key={group.id} className="desk-search-group" data-search-group={group.id}>
              <div className="grp">{group.label}{group.pending ? <span className="pending"> · by meaning…</span> : null}</div>
              {group.off ? <div className="off">{group.off}</div> : null}
              {group.rows.map((row) => (
                <div
                  key={row.key}
                  ref={(node) => {
                    if (node) rowEls.current.set(row.key, node);
                    else rowEls.current.delete(row.key);
                  }}
                  className={`r${current?.key === row.key ? " sel" : ""}`}
                  data-search-row={row.key}
                  onMouseMove={() => {
                    const index = rows.findIndex((each) => each.key === row.key);
                    if (index >= 0 && index !== selected) setSelected(index);
                  }}
                  onClick={() => choose(row)}
                >
                  <span className="t">{row.text}</span>
                  <span className="w">{row.kind === "result" && row.byMeaning ? "· by meaning " : ""}{row.where}</span>
                </div>
              ))}
              {group.hidden > 0 ? <div className="more">tab · {group.hidden} more</div> : null}
            </div>
          ))}
          {failure ? <div className="off">couldn't search just now · {failure}</div> : null}
          {meaningFailure ? <div className="off" data-meaning-failure="">by meaning: couldn't finish · {meaningFailure}</div> : null}
          {query.trim().length >= 2 && words && groups.length === 0 ? <div className="off">nothing found for “{query.trim()}”</div> : null}
        </div>
        <div className="desk-search-foot">
          <span>↑↓ choose · ↵ {insert ? "insert it here" : "open beside the focus, or scroll to it if open"} · tab more · esc close · words now, meaning later</span>
          {note ? <span className="why">{note}</span> : null}
        </div>
      </div>
    </div>
  );
}
