// The one context menu (spec §9.1, §9.2): the header, up to four promoted rows in their own block (the cheap ones at
// once from passage.promoted, the judged ones from its job on the one poller, cancelled when the menu closes), then
// the fixed verbs for the object kind, then a pad's inserts. ↑↓ or j/k move, ↵ runs, esc closes, a verb's letter runs
// it, a press outside closes. The Append row opens its submenu of the desk's pads on hover (→ from the keys).
// Styled as the mockup measures it (desk.css `.desk-menu`).
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import type { MenuObjectInput, PassagePromotedDto, PromotedJobDto, PromotedRowDto, ProposalLabel } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import { screenLeavesKey } from "../../../app/keymap";
import { MENU_SIZES, placeMenu, placeSubmenu, promotedReason, shownPromoted, type MenuRow } from "./model";

/** The promoted rows' calls (passage.promoted and its job; proposal.label with proposalKind "promoted_row"). */
export interface PromotedApi {
  passagePromoted(input: MenuObjectInput): Promise<PassagePromotedDto>;
  passagePromotedJob(input: { jobId: string }): Promise<PromotedJobDto>;
  passagePromotedCancel(input: { jobId: string }): Promise<PromotedJobDto>;
  label(rowId: string, label: ProposalLabel): void;
}

export interface AppendTargets {
  pads: Array<{ padId: string; title: string }>;
  current: string | null;
  onPick: (padId: string | "+") => void;
}

export interface ContextMenuProps {
  header: string;
  /** The menu's name for assistive tech (the header line when absent). */
  label?: string;
  rows: MenuRow[];
  at: { x: number; y: number };
  /** The object as the server reads it, for its promoted rows (none for an object with no passage). */
  object?: MenuObjectInput | null;
  promoted?: PromotedApi | null;
  /** What runs a promoted row's action (open, What this knows, the carried question…); false when it could not. */
  onPromoted?: (row: PromotedRowDto, origin: MenuObjectInput | null) => boolean | void;
  /** The rows this menu shows now, for the verbs that read them (Open beside): told only while the menu is open on
   * its object, so a late answer for a closed menu never reaches another. */
  onRows?: (rows: PromotedRowDto[]) => void;
  poller?: Poller;
  /** The window the menu is about: the job's poll waits while it is paused. */
  owner?: string | null;
  append?: AppendTargets | null;
  /** Inserts' heading ("INSERT BELOW THIS LINE"). */
  insertHeading?: string;
  onClose: () => void;
  /** A dialog the menu hands over to (the practice sheet): shown in its place. */
  children?: ReactNode;
  /** Where its keys and presses are heard: a desk window's listener hub inside a window, the page's otherwise. */
  listen?: (target: "window", type: string, handler: (event: Event) => void, capture?: boolean) => () => void;
}

const PAGE_LISTEN = (target: "window", type: string, handler: (event: Event) => void, capture = false) => {
  window.addEventListener(type, handler, capture);
  return () => window.removeEventListener(type, handler, capture);
};

/** A menu's sheet or panel owns the focus while it is open (spec §5.4): it takes it when it opens (its first
 * field, else itself), escape closes it wherever the key lands, and the focus goes back to where it was. */
export function useSheetFocus(ref: { current: HTMLElement | null }, onEscape: () => void): void {
  const escape = useRef(onEscape);
  escape.current = onEscape;
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    const node = ref.current;
    if (node && !node.contains(document.activeElement)) {
      const field = node.querySelector<HTMLElement>("textarea, input, select");
      (field ?? node).focus();
    }
    const onKey = (event: KeyboardEvent) => {
      // A modal sheet: it owns escape wherever the focus is.
      if (screenLeavesKey(event, { modal: true }) || event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      escape.current();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      if (before && before.isConnected && before !== document.body) before.focus();
    };
  }, [ref]);
}

export function ContextMenu({ header, label, rows, at, object = null, promoted = null, onPromoted, onRows, poller, owner = null, append = null, insertHeading, onClose, children, listen = PAGE_LISTEN }: ContextMenuProps) {
  const [cheap, setCheap] = useState<PromotedRowDto[]>([]);
  const [judgedPending, setJudgedPending] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [index, setIndex] = useState(0);
  const [submenuOpen, setSubmenuOpen] = useState(false);
  // The submenu's own selection (its pads, then "a new pad"): its keys move it while it is open.
  const [subIndex, setSubIndex] = useState(0);
  const [place, setPlace] = useState<{ left: number; top: number }>({ left: at.x + 2, top: at.y + 2 });
  const [subPlace, setSubPlace] = useState<{ left: number; top: number } | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const appendRef = useRef<HTMLButtonElement | null>(null);
  // Closing the menu gives the focus back to where it was (the passage's window, the pad's editor).
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    return () => {
      if (before && before.isConnected && before !== document.body) before.focus();
    };
  }, []);

  // The promoted rows: the cheap ones at once; the job's rows replace them when it is done. The job is cancelled
  // when the menu closes before it is (a newer menu on the desk supersedes it on the server too).
  const objectKey = object ? JSON.stringify(object) : "";
  // The calls are read through a ref: a parent's new object for the same calls must not restart the request (and
  // cancel the judged job) while the menu stays open on the same object.
  const promotedNow = useRef(promoted);
  promotedNow.current = promoted;
  const onRowsNow = useRef(onRows);
  onRowsNow.current = onRows;
  const hasPromoted = promoted !== null;
  useEffect(() => {
    const promoted = promotedNow.current;
    if (!object || !promoted) return;
    let live = true;
    let jobId: string | null = null;
    let finished = false;
    let stop: (() => void) | null = null;
    void promoted.passagePromoted(object).then((found) => {
      if (!live) {
        // Closed before the first answer came: its judged job is cancelled now (nothing else knows its id).
        if (found.pendingJob) void promoted.passagePromotedCancel({ jobId: found.pendingJob.jobId }).catch(() => undefined);
        return;
      }
      setCheap(found.rows);
      onRowsNow.current?.(found.rows);
      if (found.pendingJob && poller) {
        jobId = found.pendingJob.jobId;
        setJudgedPending(true);
        stop = poller.register<PromotedJobDto>({
          key: `promoted-job:${jobId}`,
          owner,
          request: () => (promotedNow.current ?? promoted).passagePromotedJob({ jobId: jobId as string }),
          onResult: (job) => {
            if (!live) return { done: true };
            if (job.done) {
              finished = true;
              setJudgedPending(false);
              if (job.status === "done") {
                setCheap(job.rows);
                onRowsNow.current?.(job.rows);
              }
            }
            return { done: job.done };
          },
          onError: () => {
            if (live) setJudgedPending(false);
          },
        });
      }
    }, () => undefined);
    return () => {
      live = false;
      stop?.();
      if (jobId && !finished) void promoted.passagePromotedCancel({ jobId }).catch(() => undefined);
    };
    // objectKey stands for the object.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [objectKey, hasPromoted, poller, owner]);

  const promotedRows: MenuRow[] = shownPromoted(cheap, dismissed).map((row) => ({
    id: `promoted:${row.rowId}`, glyph: row.glyph, label: row.label, note: promotedReason(row), section: "promoted", promoted: row,
    run: () => {
      onClose();
      // Labelled opened only when its action ran (a row that could not open stays unlabelled).
      if (onPromoted?.(row, object) !== false) promoted?.label(row.rowId, "opened");
    },
  }));
  const all = [...promotedRows, ...rows];
  const runnable = all.filter((row) => !row.disabled);

  // Placed at the pointer, then moved in to fit once its size is known (and again when rows arrive).
  useLayoutEffect(() => {
    const menu = menuRef.current;
    if (!menu) return;
    const box = menu.getBoundingClientRect();
    setPlace(placeMenu(at, { w: box.width || MENU_SIZES.width, h: box.height }, { w: window.innerWidth, h: window.innerHeight }));
  }, [at, all.length, judgedPending, children !== undefined]);

  const openSubmenu = () => {
    const row = appendRef.current?.getBoundingClientRect();
    if (!row) return;
    setSubPlace(placeSubmenu({ right: row.right, top: row.top }, MENU_SIZES.submenuWidth, { w: window.innerWidth }));
    if (!submenuOpen) setSubIndex(Math.max(0, append?.pads.findIndex((pad) => pad.padId === append.current) ?? 0));
    setSubmenuOpen(true);
  };

  const dismiss = (row: PromotedRowDto, label: "dismiss" | "not_this") => {
    promoted?.label(row.rowId, label);
    setDismissed((now) => new Set([...now, row.rowId]));
  };

  useEffect(() => {
    if (children) return;
    const onKey = (event: KeyboardEvent) => {
      // A modal menu: it owns the keyboard while it is open, never a chord.
      if (screenLeavesKey(event, { modal: true }) || event.altKey || event.ctrlKey || event.metaKey) return;
      const current = runnable[Math.min(index, runnable.length - 1)];
      if (submenuOpen && append) {
        // The Append submenu owns the keys while open: its rows move and run; left or escape go back to the menu.
        const count = append.pads.length + 1;
        if (event.key === "ArrowDown" || event.key === "j" || (event.key === "Tab" && !event.shiftKey)) setSubIndex((now) => (now + 1) % count);
        else if (event.key === "ArrowUp" || event.key === "k" || (event.key === "Tab" && event.shiftKey)) setSubIndex((now) => (now - 1 + count) % count);
        else if (event.key === "Enter") append.onPick(subIndex < append.pads.length ? append.pads[subIndex].padId : "+");
        else if (event.key === "Escape" || event.key === "ArrowLeft") setSubmenuOpen(false);
        else return;
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      if (event.key === "Escape") {
        if (submenuOpen) setSubmenuOpen(false);
        else onClose();
      } else if (event.key === "ArrowDown" || event.key === "j") setIndex((now) => Math.min(runnable.length - 1, now + 1));
      else if (event.key === "ArrowUp" || event.key === "k") setIndex((now) => Math.max(0, now - 1));
      else if (event.key === "ArrowRight" && current?.submenu) openSubmenu();
      else if (event.key === "Enter") {
        if (current?.submenu) openSubmenu();
        else current?.run?.();
      } else {
        const row = runnable.find((each) => each.key === event.key);
        if (!row) return;
        if (row.submenu) openSubmenu();
        else row.run?.();
      }
      event.preventDefault();
      event.stopPropagation();
    };
    const onDown = (event: MouseEvent) => {
      if (!(event.target as Element).closest?.(".desk-menu")) onClose();
    };
    const offs = [listen("window", "keydown", onKey as (event: Event) => void), listen("window", "mousedown", onDown as (event: Event) => void, true)];
    return () => offs.forEach((off) => off());
  });

  if (children) return <>{children}</>;

  const rowView = (row: MenuRow) => {
    const at = runnable.indexOf(row);
    const selected = at >= 0 && at === Math.min(index, runnable.length - 1);
    return (
      <button
        key={row.id}
        ref={row.submenu ? appendRef : undefined}
        type="button"
        role="menuitem"
        data-menu-row={row.id}
        className={`mi${selected ? " sel" : ""}${row.aid ? " aid" : ""}${row.submenu ? " hassub" : ""}`}
        disabled={row.disabled}
        onMouseEnter={() => {
          if (at >= 0) setIndex(at);
          if (row.submenu) openSubmenu();
          else setSubmenuOpen(false);
        }}
        onClick={() => (row.submenu ? openSubmenu() : row.run?.())}
      >
        <span className="g">{row.glyph}</span>
        <span className="t">
          {row.label}
          {row.note ? <span className="why">{row.note}</span> : null}
        </span>
        {row.promoted ? (
          <span className="k pl">
            <span role="button" tabIndex={-1} className="lb" title="wrong: don't suggest this here" onClick={(event) => { event.stopPropagation(); dismiss(row.promoted as PromotedRowDto, "not_this"); }}>not this</span>
            <span role="button" tabIndex={-1} className="lb" title="not now" aria-label="dismiss" onClick={(event) => { event.stopPropagation(); dismiss(row.promoted as PromotedRowDto, "dismiss"); }}>×</span>
          </span>
        ) : <span className="k">{row.key ?? ""}</span>}
      </button>
    );
  };

  const verbs = rows.filter((row) => row.section === "verb");
  const inserts = rows.filter((row) => row.section === "insert");
  const tail = rows.filter((row) => row.section === "tail");
  return (
    <>
      <div ref={menuRef} className="desk-menu" role="menu" aria-label={label ?? header} style={{ left: place.left, top: place.top }}>
        <div className="mh">{header}</div>
        {promotedRows.length || judgedPending ? (
          <div className="pro" data-menu-promoted="">
            {promotedRows.map(rowView)}
            {judgedPending ? <div className="pending">◐ looking for more · the four most useful show</div> : null}
          </div>
        ) : null}
        {verbs.filter((row) => !row.aid).map(rowView)}
        {inserts.length ? <div className="mh sub">{insertHeading ?? "insert below this line"}</div> : null}
        {inserts.map(rowView)}
        {tail.length || verbs.some((row) => row.aid) ? <div className="sep" /> : null}
        {verbs.filter((row) => row.aid).map(rowView)}
        {tail.map(rowView)}
      </div>
      {submenuOpen && append && subPlace ? (
        <div className="desk-menu submenu" role="menu" aria-label="append to" style={{ left: subPlace.left, top: subPlace.top }}>
          <div className="mh">append to</div>
          {append.pads.map((pad, padIndex) => (
            <button key={pad.padId} type="button" role="menuitem" className={`mi${padIndex === subIndex ? " sel" : ""}`} onMouseEnter={() => setSubIndex(padIndex)} onClick={() => append.onPick(pad.padId)}>
              <span className="g">{pad.padId === append.current ? "✓" : ""}</span>
              <span className="t">{pad.title}</span>
              <span className="k" />
            </button>
          ))}
          <div className="sep" />
          <button type="button" role="menuitem" className={`mi${subIndex === append.pads.length ? " sel" : ""}`} onMouseEnter={() => setSubIndex(append.pads.length)} onClick={() => append.onPick("+")}>
            <span className="g">+</span>
            <span className="t">a new pad</span>
            <span className="k">alt+n</span>
          </button>
        </div>
      ) : null}
    </>
  );
}
