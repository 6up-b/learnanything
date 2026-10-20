// RW4d: syntopic reading, kept (spec §7.8; UX §4.5, §4.10, W10).
//
// Under a compare table (RW4a's, or the tutor's comparison in RW1c's offers)
// the three voices sit in visibly separate bands (W2, B 261):
//
//   § what each source says — the table above, each line quoting its source;
//   ◇ how LearnLoop reads the relations — each pair's relation, labelled as
//     LearnLoop's inference (AI-written), with its fine label;
//   › your take (optional) — the learner's own line on a pair or a claim.
//
// "keep comparison ⇄" stores proposals (the sidecar writes source objects and
// relations, never a concept edge, facet merge, prerequisite or LO change);
// "remove" supersedes them. Nothing is kept until the press. Without the
// Reader's `compareKeep` context (reader_compare.keep_enabled off) this
// renders nothing, so the table is RW4a's and the tutor's offer RW1c's.
// Nothing here takes focus, animates or opens a modal (G54).
import { useEffect, useState, type ComponentType } from "react";
import { api } from "../../api/client";
import type { CompareTableDto, KeptComparisonDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { useCompareKeep } from "./compareKeepContext";
import { LearnerVoice, MeaningLabel, ModelVoice } from "./voices";

export const KEEP_COPY = {
  inferred: "how LearnLoop reads the relations",
  inferredNote: "LearnLoop's inference (AI-written)",
  take: "your take (optional)",
  takeAbout: "about",
  takePlaceholder: "what you make of these passages, in your words",
  keep: "keep comparison ⇄",
  keeping: "keeping",
  kept: "kept ⇄",
  addTake: "add your take",
  remove: "remove",
  removed: "Removed. The proposals are kept as superseded, never deleted.",
  proposals: "kept as proposals · nothing changes your map until you review them",
  whereThisGoes: "ⓘ where this goes",
  whereLine: "Kept as your own note on these passages, in your voice. It isn't read for gaps — and never grades you.",
  reopening: "opening your comparison",
  close: "close",
  comparedOn: "you compared these on",
  reopen: "reopen ⇄",
} as const;

/** The sources spec's fine relation labels, in plain words (§3.4 item 15). */
export const FINE_LABELS: Record<string, string> = {
  equivalent: "the same claim",
  different_assumptions: "different assumptions",
  different_notation: "different notation",
  complementary: "complementary",
  disagreement: "they disagree",
  unclear: "unclear",
};

export function fineLabel(fine: string | null | undefined): string {
  return (fine && FINE_LABELS[fine]) || (fine ?? "").replace(/_/g, " ") || "related";
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

const linkStyle = {
  border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0,
  cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2,
} as const;
const quietStyle = { ...linkStyle, color: COLOR.textDim, fontSize: 10 } as const;
const headStyle = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.06em", color: COLOR.textDim, textTransform: "uppercase" as const };

interface RelationPair {
  key: string;
  titles: [string, string];
  relation: string | null;
  line: string | null;
}

/** Each pair's relation once (the table shows it under both rows). */
export function relationPairs(table: CompareTableDto): RelationPair[] {
  const seen = new Map<string, RelationPair>();
  for (const row of table.rows) {
    const title = row.sourceTitle ?? "a source";
    for (const cell of [...row.assumes, ...row.differs]) {
      const other = cell.otherSourceTitle ?? "a source";
      const titles = [title, other].sort() as [string, string];
      const key = `${titles.join("⇄")}|${cell.relation ?? ""}|${cell.line ?? ""}`;
      if (!seen.has(key)) seen.set(key, { key, titles, relation: cell.relation ?? null, line: cell.line });
    }
  }
  return [...seen.values()];
}

interface TakeTarget {
  value: string;
  label: string;
  keys: string[];
}

function takeTargets(table: CompareTableDto): TakeTarget[] {
  const rows = table.rows;
  const title = (index: number) => rows[index].sourceTitle ?? "a source";
  const pairs: TakeTarget[] = [];
  for (let i = 0; i < rows.length; i += 1) {
    for (let j = i + 1; j < rows.length; j += 1) {
      pairs.push({ value: `${rows[i].key}|${rows[j].key}`, label: `${title(i)} ⇄ ${title(j)}`, keys: [rows[i].key, rows[j].key] });
    }
  }
  const claims = rows.map((row, index) => ({ value: row.key, label: `${title(index)} only`, keys: [row.key] }));
  return [...pairs, ...claims];
}

export type KeepTarget = { askId: string } | { toolCallId: string; extractionId: string | null };

/** The relation band, the take band and keep / remove under a compare table. */
export function CompareKeep({ table, target }: { table: CompareTableDto; target: KeepTarget }) {
  const ctx = useCompareKeep();
  // A kept comparison can always be removed (and its take added to) while
  // keeping is on, whichever surface kept it; a new keep needs its surface's switch.
  const allowed = ctx ? ("askId" in target ? ctx.settings.library || Boolean(table.kept) : ctx.settings.tutor) : false;
  const [kept, setKept] = useState<KeptComparisonDto | null>(table.kept ?? null);
  const [take, setTake] = useState("");
  const targets = takeTargets(table);
  const [about, setAbout] = useState(targets[0]?.value ?? "");
  const [phase, setPhase] = useState<"idle" | "pending" | "failed" | "removed">("idle");
  const [failure, setFailure] = useState<string | null>(null);
  const [why, setWhy] = useState(false);
  useEffect(() => { setKept(table.kept ?? null); }, [table.kept, table.comparisonId]);
  if (!ctx || !allowed) return null;
  if (table.status !== "ok" || !table.comparisonId || table.rows.length < 2) return null;
  const pairs = relationPairs(table);

  const keep = async (withTake: boolean) => {
    const chosen = targets.find((entry) => entry.value === about) ?? targets[0];
    const text = take.trim();
    const takes = withTake && text && chosen ? [{ text, keys: chosen.keys }] : [];
    setPhase("pending");
    setFailure(null);
    try {
      const result = await api.readerLibraryCompareKeep({
        ...("askId" in target ? { askId: target.askId } : { toolCallId: target.toolCallId, extractionId: target.extractionId }),
        takes,
      });
      setKept(result.kept);
      setTake("");
      setPhase("idle");
      ctx.onChanged();
    } catch (error) {
      setPhase("failed");
      setFailure(errorMessage(error, "Couldn't keep this comparison. Nothing was saved; try again."));
    }
  };
  const remove = async () => {
    if (!kept) return;
    setPhase("pending");
    setFailure(null);
    try {
      await api.readerLibraryCompareRemove({ askId: kept.askId });
      setKept(null);
      setPhase("removed");
      ctx.onChanged();
    } catch (error) {
      setPhase("failed");
      setFailure(errorMessage(error, "Couldn't remove it; it is still kept."));
    }
  };

  return (
    <div data-compare-keep="" style={{ display: "flex", flexDirection: "column", gap: 10, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
      {pairs.length ? (
        <div data-compare-band="inferred" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={headStyle}>{KEEP_COPY.inferred}</span>
          {pairs.map((pair) => (
            <ModelVoice key={pair.key} note={KEEP_COPY.inferredNote}>
              <span>{pair.titles[0]} ⇄ {pair.titles[1]} · {fineLabel(pair.relation)}</span>
              {pair.line ? <span style={{ display: "block", color: COLOR.textDim, fontSize: 11 }}>{pair.line}</span> : null}
            </ModelVoice>
          ))}
        </div>
      ) : null}
      <div data-compare-band="take" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {kept?.takes.length ? kept.takes.map((entry) => (
          <LearnerVoice key={entry.id} label="your take">{entry.learnerText}</LearnerVoice>
        )) : null}
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={headStyle}><span aria-hidden="true">› </span>{KEEP_COPY.take}</span>
          <input
            value={take}
            onChange={(event) => setTake(event.target.value)}
            placeholder={KEEP_COPY.takePlaceholder}
            aria-label="your take on these passages"
            maxLength={1000}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 8px" }}
          />
        </label>
        <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
          {targets.length > 1 ? (
            <label style={{ display: "flex", gap: 6, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
              {KEEP_COPY.takeAbout}
              <select value={about} onChange={(event) => setAbout(event.target.value)} aria-label="your take is about"
                style={{ fontFamily: FONT_MONO, fontSize: 10, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }}>
                {targets.map((entry) => <option key={entry.value} value={entry.value}>{entry.label}</option>)}
              </select>
            </label>
          ) : null}
          <button type="button" style={quietStyle} aria-expanded={why} onClick={() => setWhy((value) => !value)}>{KEEP_COPY.whereThisGoes}</button>
        </div>
        {why ? <MeaningLabel>{KEEP_COPY.whereLine}</MeaningLabel> : null}
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        {kept ? (
          <>
            <span data-kept="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amber }}>{KEEP_COPY.kept}</span>
            <MeaningLabel>{KEEP_COPY.proposals}</MeaningLabel>
            {take.trim() ? (
              <button type="button" style={linkStyle} disabled={phase === "pending"} onClick={() => void keep(true)}>{KEEP_COPY.addTake}</button>
            ) : null}
            <button type="button" style={quietStyle} disabled={phase === "pending"} onClick={() => void remove()}>{KEEP_COPY.remove}</button>
          </>
        ) : (
          <button type="button" style={linkStyle} disabled={phase === "pending"} onClick={() => void keep(true)}>{KEEP_COPY.keep}</button>
        )}
        {phase === "pending" ? <MeaningLabel><span aria-hidden="true">◐</span> {KEEP_COPY.keeping}…</MeaningLabel> : null}
      </div>
      {phase === "removed" && !kept ? <MeaningLabel>{KEEP_COPY.removed}</MeaningLabel> : null}
      {phase === "failed" && failure ? <span role="status"><MeaningLabel>{failure}</MeaningLabel></span> : null}
    </div>
  );
}

/** A kept comparison's table again (from ⇄, or "you compared these on …"):
 *  rebuilt from the stored comparison, no model call. `Table` is RW4a's
 *  CompareTable (passed in, so this file does not import the answer). */
export function KeptComparisonView({
  askId,
  onClose,
  Table,
}: {
  askId: string;
  onClose: () => void;
  Table: ComponentType<{ table: CompareTableDto }>;
}) {
  const ctx = useCompareKeep();
  const [state, setState] = useState<{ phase: "pending" | "landed" | "failed"; table: CompareTableDto | null; failure: string | null }>(
    { phase: "pending", table: null, failure: null },
  );
  const openSourceId = ctx?.openSourceId ?? null;
  useEffect(() => {
    let cancelled = false;
    setState({ phase: "pending", table: null, failure: null });
    void api.readerLibraryCompareReopen({ askId, openSourceId })
      .then((table) => { if (!cancelled) setState({ phase: "landed", table, failure: null }); })
      .catch((error) => { if (!cancelled) setState({ phase: "failed", table: null, failure: errorMessage(error, "Couldn't open this comparison.") }); });
    return () => { cancelled = true; };
  }, [askId, openSourceId]);
  if (!ctx) return null;
  return (
    <div
      data-kept-comparison={askId}
      onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onClose(); } }}
      style={{ display: "flex", flexDirection: "column", gap: 8, border: `1px solid ${COLOR.border}`, padding: "8px 10px", margin: "6px 0" }}
    >
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <span style={headStyle}>a comparison you kept</span>
        <span style={{ flex: 1 }} />
        <button type="button" style={quietStyle} onClick={onClose}>{KEEP_COPY.close}</button>
      </div>
      {state.phase === "pending" ? <MeaningLabel><span aria-hidden="true">◐</span> {KEEP_COPY.reopening}…</MeaningLabel> : null}
      {state.phase === "failed" ? <MeaningLabel>{state.failure}</MeaningLabel> : null}
      {state.table ? (
        <>
          {state.table.query ? <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>“{state.table.query}”</span> : null}
          <Table table={state.table} />
          <CompareKeep table={state.table} target={{ askId }} />
        </>
      ) : null}
    </div>
  );
}
