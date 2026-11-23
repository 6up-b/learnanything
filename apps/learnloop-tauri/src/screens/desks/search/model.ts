// Search in context, the pure half (spec §9.3): the groups in their order with the client's own "open on this
// desk" first, the meaning job's rows merged into their groups with a quiet "by meaning" tag, at most three
// rows a group until it is expanded (an attention limit), each row's line and its "where", and the rows the
// keys move through.
import type {
  ContentRefDto,
  SearchEverythingDto,
  SearchExchangeRowDto,
  SearchGroupDto,
  SearchNoteRowDto,
  SearchPadRowDto,
  SearchPassageRowDto,
  SearchRowBase,
  SearchScope,
  SearchSourceRowDto,
  SearchThreadRowDto,
} from "../../../api/dto";

/** Rows shown per group before `tab` expands it (spec §9.3: an attention limit). */
export const ROWS_PER_GROUP = 3;

export const GROUP_ORDER: readonly SearchScope[] = ["sources", "passages", "notes", "pads", "threads", "exchanges"];

/** What the panel's client side knows: the windows on this desk. */
export interface OpenWindow {
  windowId: string;
  title: string;
}

export type SearchRow =
  | { kind: "open"; key: string; text: string; where: string; windowId: string }
  | { kind: "result"; key: string; group: SearchScope; text: string; where: string; byMeaning: boolean; ref: ContentRefDto | null;
      target: SearchRowBase["target"]; raw: SearchGroupDto["rows"][number] };

export interface ShownGroup {
  id: SearchScope | "open";
  label: string;
  rows: SearchRow[];
  /** Rows beyond the three shown (tab shows them). */
  hidden: number;
  /** The group could not be searched: why (never "nothing found"). */
  off: string | null;
  /** The meaning pass is still running for this group. */
  pending: boolean;
}

function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function clip(text: string, length = 140): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > length ? `${flat.slice(0, length - 1)}…` : flat;
}

/** One result's line and its "where", as the mockup's rows read. */
export function describeRow(group: SearchScope, raw: SearchGroupDto["rows"][number], deskTitle: (deskId: string | null) => string): { text: string; where: string; byMeaning: boolean } {
  switch (group) {
    case "sources": {
      const row = raw as SearchSourceRowDto;
      const kind = row.ref?.kind === "video" ? "video" : "source";
      return { text: row.title, where: row.onThisDesk ? `${kind} · on this desk` : row.openOnDeskIds.length ? `${kind} · open` : kind, byMeaning: false };
    }
    case "passages": {
      const row = raw as SearchPassageRowDto;
      const at = row.ref?.kind === "video" && typeof row.target?.t === "number" ? ` ▶ ${clock(row.target.t)}` : row.page ? ` p.${row.page}` : "";
      return { text: `${row.sourceTitle}${at} · ${clip(row.snippet)}`, where: row.ref?.kind === "video" ? "moment" : "passage", byMeaning: row.byMeaning };
    }
    case "notes": {
      const row = raw as SearchNoteRowDto;
      if (row.noteKind === "note") return { text: clip(row.snippet || row.title), where: `› your note${row.capturedOn ? ` · ${shortDate(row.capturedOn)}` : ""}`, byMeaning: row.byMeaning };
      return { text: clip(row.snippet), where: `› your words · ${shortDate(row.createdAt)}`, byMeaning: false };
    }
    case "pads": {
      const row = raw as SearchPadRowDto;
      return { text: `${row.padTitle} · ${clip(row.snippet, 100)}`, where: row.handwriting ? "your handwriting" : "yours", byMeaning: false };
    }
    case "threads": {
      const row = raw as SearchThreadRowDto;
      return { text: clip(row.questionMd), where: `thread · ${shortDate(row.createdAt)}`, byMeaning: false };
    }
    case "exchanges": {
      const row = raw as SearchExchangeRowDto;
      return { text: `› ${clip(row.questionMd)}`, where: `${shortDate(row.createdAt)} · ${deskTitle(row.deskId)}`, byMeaning: false };
    }
  }
}

function clock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function rowKey(group: SearchScope, raw: SearchGroupDto["rows"][number], index: number): string {
  const r = raw as unknown as Record<string, unknown>;
  const id = r.spanId ?? r.blockId ?? r.noteKey ?? r.gapId ?? r.questionEventId ?? r.sourceId ?? index;
  return `${group}:${String(r.extractionId ?? "")}:${String(id)}`;
}

/** The groups to show: open on this desk (client side), then each server group in order, the meaning job's
 * rows merged after the words' with their tag; three rows each unless expanded. */
export function shownGroups(input: {
  query: string;
  open: OpenWindow[];
  words: SearchEverythingDto | null;
  meaning: SearchGroupDto[];
  meaningPending: boolean;
  expanded: ReadonlySet<string>;
  deskTitle: (deskId: string | null) => string;
}): ShownGroup[] {
  const out: ShownGroup[] = [];
  const q = input.query.trim().toLowerCase();
  const openRows: SearchRow[] = input.open
    .filter((window) => !q || window.title.toLowerCase().includes(q))
    .map((window) => ({ kind: "open", key: `open:${window.windowId}`, text: window.title, where: "open on this desk", windowId: window.windowId }));
  if (openRows.length) out.push(limit({ id: "open", label: "open on this desk", rows: openRows, hidden: 0, off: null, pending: false }, input.expanded));
  if (!input.words) return out;
  const pendingGroups = new Set(input.meaningPending ? input.words.meaning.groups ?? [] : []);
  for (const id of GROUP_ORDER) {
    const words = input.words.groups.find((group) => group.group === id);
    const meaning = input.meaning.find((group) => group.group === id);
    const rows: SearchRow[] = [];
    const seen = new Set<string>();
    for (const group of [words, meaning]) {
      if (!group || group.status !== "ok") continue;
      group.rows.forEach((raw, index) => {
        const key = rowKey(id, raw, index);
        if (seen.has(key)) return;
        seen.add(key);
        const described = describeRow(id, raw, input.deskTitle);
        rows.push({ kind: "result", key, group: id, ...described, byMeaning: described.byMeaning || group.basis === "meaning", ref: raw.ref, target: raw.target, raw });
      });
    }
    // Not searched by words, or by meaning (unavailable, or failed): said under the group's name, never
    // "nothing found".
    const off = words && words.status !== "ok"
      ? words.reason ?? "not available"
      : meaning && meaning.status !== "ok"
        ? `by meaning: ${meaning.reason ?? (meaning.status === "failed" ? "the search failed" : "not available")}`
        : null;
    if (rows.length === 0 && !off && !pendingGroups.has(id)) continue;
    out.push(limit({ id, label: words?.label ?? meaning?.label ?? id, rows, hidden: 0, off, pending: pendingGroups.has(id) }, input.expanded));
  }
  return out;
}

function limit(group: ShownGroup, expanded: ReadonlySet<string>): ShownGroup {
  if (expanded.has(group.id) || group.rows.length <= ROWS_PER_GROUP) return group;
  return { ...group, rows: group.rows.slice(0, ROWS_PER_GROUP), hidden: group.rows.length - ROWS_PER_GROUP };
}

/** The rows the arrow keys move through, in display order. */
export function selectableRows(groups: ShownGroup[]): SearchRow[] {
  return groups.flatMap((group) => group.rows);
}

/** Why some groups have no meaning pass, said once under the results (each group's own reason), whether or not
 * another group's meaning job runs; the job's own list joins the start's. */
export function meaningNote(words: SearchEverythingDto | null, fromJob: ReadonlyArray<{ group: string; reason: string }> = []): string | null {
  if (!words) return null;
  const reasons = [...new Set([...words.meaning.unavailable, ...fromJob].map((entry) => entry.reason))];
  return reasons.length ? `by meaning: ${reasons.join(" · ")}` : null;
}
