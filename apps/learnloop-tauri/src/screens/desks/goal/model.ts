// The goal lens on the desks (spec §12.2-§12.5): pure helpers over goal.band and goal.lens. The backend
// computes every level (curriculum/goal_lens.py); this file only indexes, filters and words what it sent.
// Display of the real model: nothing here is evidence.
import type { GoalBandDto, GoalBandLoDto, GoalLensDto, GoalLensSectionDto } from "../../../api/dto";

export type LensLevel = GoalLensSectionDto["level"];

/** The why card's first line per level (spec §12.3's mark table, the mockup's words). */
export const LEVEL_LABEL: Record<LensLevel, string> = {
  core: "core for your goal",
  supporting: "supporting",
  later: "later",
  already_shown: "already shown",
  skippable: "skippable for now",
  partial: "partly mapped for this goal",
  unmapped: "not mapped for this goal yet",
};

/** The mark a level draws (§12.3): a solid bar, the same at 34 %, a dotted line, a short grey tick, or none. */
export type MarkKind = "core" | "sup" | "skip" | "later" | "shown" | "partial";

export function markKind(level: LensLevel): MarkKind | null {
  switch (level) {
    case "core": return "core";
    case "supporting": return "sup";
    case "skippable": return "skip";
    case "later": return "later";
    case "already_shown": return "shown";
    case "partial": return "partial";
    default: return null;
  }
}

/** One reading's lens, indexed by passage: every passage inherits its section's level (decision D1). */
export interface LensIndex {
  extractionId: string;
  bySpan: Map<string, GoalLensSectionDto>;
  /** A section's first passage in this reading: where its callout goes. */
  starts: Map<string, GoalLensSectionDto>;
  sections: GoalLensSectionDto[];
}

export function indexLens(lens: GoalLensDto | null | undefined): LensIndex | null {
  if (!lens) return null;
  const bySpan = new Map<string, GoalLensSectionDto>();
  const starts = new Map<string, GoalLensSectionDto>();
  for (const section of lens.levels) {
    for (const span of section.spanIds) bySpan.set(span, section);
    starts.set(section.startSpanId, section);
    // A section whose heading is not among its passages starts at its first passage.
    if (section.spanIds.length && !section.spanIds.includes(section.startSpanId)) starts.set(section.spanIds[0], section);
  }
  return { extractionId: lens.extractionId, bySpan, starts, sections: lens.levels };
}

/** The levels of the passages in view: one whole-reading goal.lens call is filtered here, so a scroll asks
 *  the sidecar nothing (spec §3.6: batched per reading, never per span). */
export function levelsInRange(index: LensIndex | null, spanIds: readonly string[]): GoalLensSectionDto[] {
  if (!index) return [];
  const seen = new Set<string>();
  const out: GoalLensSectionDto[] = [];
  for (const span of spanIds) {
    const section = index.bySpan.get(span);
    if (section && !seen.has(section.sectionId)) {
      seen.add(section.sectionId);
      out.push(section);
    }
  }
  return out;
}

/** Dimmed while dimming is on: skippable and later, unless the learner chose to read it anyway (the
 *  backend's `dim`). Dimmed text is never hidden. */
export function isDimmed(section: GoalLensSectionDto | undefined, dimOn: boolean): boolean {
  return Boolean(dimOn && section?.dim);
}

/** The deeper depth a "later" passage is kept at: the one after the chosen depth. */
export function deeperDepthLabel(band: GoalBandDto | null): string | null {
  const depths = band?.depths ?? [];
  const at = depths.findIndex((depth) => depth.id === band?.depth);
  return at >= 0 && at + 1 < depths.length ? depths[at + 1].label : null;
}

/** The why card's level line: "later · kept at learn to use it", "core for your goal". */
export function whyLevelLine(section: GoalLensSectionDto, band: GoalBandDto | null): string {
  if (section.level === "later") {
    const deeper = deeperDepthLabel(band);
    return deeper ? `later · kept at ${deeper}` : "later";
  }
  return LEVEL_LABEL[section.level];
}

/** "For <goal>:" — the goal's own short words (its title, else its sentence). */
export function goalShort(band: GoalBandDto | null): string {
  const title = band?.goal.title?.trim();
  return title || band?.goal.sentence || "your goal";
}

/** "◎ YOUR GOAL · QUEST · NO DEADLINE" (kind shown, never stored; spec §12.1). */
export function goalLabel(band: GoalBandDto): string {
  const due = band.goal.dueAt ? `due ${formatDay(band.goal.dueAt)}` : "no deadline";
  return `◎ your goal · ${band.goal.kind} · ${due}`;
}

export function formatDay(stamp: string): string {
  const parsed = new Date(stamp);
  if (Number.isNaN(parsed.getTime())) return stamp;
  return parsed.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

/** "N learning objects · a likely · b untested" (the counts are the LOs within the chosen depth). */
export function countsLine(band: GoalBandDto): string {
  const counts = band.counts;
  if (!counts) return "";
  const parts = [
    counts.demonstrated ? `${counts.demonstrated} demonstrated` : null,
    counts.likely ? `${counts.likely} likely` : null,
    counts.untested ? `${counts.untested} untested` : null,
  ].filter(Boolean);
  const n = counts.learningObjects;
  return [`${n} learning object${n === 1 ? "" : "s"}`, ...parts].join(" · ");
}

/** "Next for the goal": due checks, the next unread primary, or "nothing due · the path is read". */
export function nextLine(band: GoalBandDto): { text: string; kind: "checks" | "section" | "read" | "none" } {
  const next = band.next;
  if (!next || next.kind === "none") return { text: "nothing on the path yet", kind: "none" };
  if (next.kind === "checks") return { text: `◇ ${next.count} cold check${next.count === 1 ? "" : "s"} due today`, kind: "checks" };
  if (next.kind === "section") return { text: `§ ${next.section.book} ${next.section.title}`, kind: "section" };
  return { text: "nothing due · the path is read", kind: "read" };
}

/** "You are reading": the focused window's passage mapped through the lens (spec §12.2 part 3). */
export function hereLine(index: LensIndex | null, readingSpan: string | null, where: string | null,
                         band: GoalBandDto | null): { where: string; lo: string | null; tag: string | null; loId: string | null } | null {
  if (!index || !readingSpan) return null;
  const section = index.bySpan.get(readingSpan);
  const place = where || section?.title || "";
  if (!section) return { where: place, lo: null, tag: null, loId: null };
  if (section.level === "skippable") return { where: place, lo: null, tag: "not needed for your goal", loId: null };
  if (section.level === "unmapped") return { where: place, lo: null, tag: "not mapped for this goal yet", loId: null };
  // A section treating an LO whose check is due names nothing: not the window's own place words (the book's heading
  // may be the LO's name), only the server's neutral title (D15).
  if (section.held) return { where: section.title, lo: null, tag: "a cold check is due here", loId: null };
  const lo = section.learningObjects.find((entry) => entry.learningObjectId === section.determiningLoId);
  const dot = band?.learningObjects?.find((each) => each.learningObjectId === section.determiningLoId);
  const tag = section.level === "later" ? "later"
    : section.level === "already_shown" ? "already shown"
    : section.reasonKey === "alternate" ? "another way"
    : lo?.kind === "prerequisite" ? "prerequisite"
    : section.level === "partial" ? "partly mapped" : null;
  return { where: place, lo: truncate(lo?.title ?? dot?.title ?? null, 44), tag, loId: section.determiningLoId };
}

/** A section-start callout (spec §12.4) for a section the path places: core or prerequisite or another way.
 *  The words are the path's own reason for the section (goal.lens's `reasonMd`); none for the rest. */
export interface Callout {
  label: string;
  body: string;
  held: boolean;
}

export function calloutFor(section: GoalLensSectionDto): Callout | null {
  if (section.mapping !== "mapped") return null;
  const lo = section.learningObjects.find((entry) => entry.learningObjectId === section.determiningLoId);
  if (section.held) return { label: "for your goal", body: section.reasonMd, held: true };
  if (!lo) return null;
  const quoted = lo.title ? `“${lo.title}”` : "this topic";
  if (section.reasonKey === "primary") {
    return { label: "for your goal · core", body: `${section.reasonMd} Primary on your path for ${quoted}.`, held: false };
  }
  if (section.reasonKey === "prerequisite") {
    return { label: "for your goal · prerequisite", body: `${section.reasonMd} Primary on your path for ${quoted}, which your goal builds on.`, held: false };
  }
  if (section.reasonKey === "alternate") {
    return { label: "for your goal · another way", body: `Another way for ${quoted}: ${section.reasonMd}`, held: false };
  }
  return null;
}

/** The band's dots: the rotated ◇ follows an LO with a due check (filled once answered). */
export function dotClasses(dot: GoalBandLoDto, here: string | null): string {
  // A later LO is a prerequisite the deeper depths reach: a small dot too, dimmed.
  return ["gs", `rd-${dot.readiness}`, dot.kind !== "needed" ? "pre" : "", dot.beyondDepth ? "later" : "",
    here && here === dot.learningObjectId ? "here" : ""].filter(Boolean).join(" ");
}

/** A dot's hover title; a held LO's name is not shown (spec §12.6.1). */
export function dotTitle(dot: GoalBandLoDto): string {
  if (dot.held) return "a cold check is due on this topic";
  return [dot.title, dot.kind === "later" ? "later" : dot.kind, dot.readiness].filter(Boolean).join(" · ");
}

export function readOrNot(read: boolean): string {
  return read ? "read" : "not read";
}

/** The band's reading line keeps an LO's title to a glance (44 characters, as the reference does). */
export function truncate(text: string | null, limit: number): string | null {
  if (text === null || text.length <= limit) return text;
  return `${text.slice(0, limit - 1).trimEnd()}…`;
}

/** A shelf row through the lens (§12.3: shelf rows carry the bar at their right edge, a line on what the source is
 *  for, and the path's ranges on the minimap). */
export interface ShelfGoal {
  mark: MarkKind | null;
  line: string;
  ranges: Array<[number, number]>;
}

export function shelfGoal(index: LensIndex | null): ShelfGoal | null {
  if (!index) return null;
  const sections = index.sections;
  if (!sections.length || sections.every((section) => section.mapping === "unmapped")) {
    return { mark: null, line: "not mapped for this goal yet", ranges: [] };
  }
  const total = sections.reduce((sum, section) => sum + section.spanIds.length, 0) || 1;
  const ranges: Array<[number, number]> = [];
  let at = 0;
  for (const section of sections) {
    const from = at / total;
    at += section.spanIds.length;
    if (section.mapping === "mapped" && (section.level === "core" || section.level === "supporting")) {
      const last = ranges[ranges.length - 1];
      if (last && Math.abs(last[1] - from) < 1e-9) last[1] = at / total;
      else ranges.push([from, at / total]);
    }
  }
  const primaries = new Set(sections.filter((section) => section.reasonKey === "primary" && section.determiningLoId).map((section) => section.determiningLoId));
  if (primaries.size) return { mark: "core", line: `primary for ${primaries.size} of your LO${primaries.size === 1 ? "" : "s"}`, ranges };
  if (sections.some((section) => section.reasonKey === "prerequisite")) return { mark: "sup", line: "background your goal builds on", ranges };
  if (sections.some((section) => section.reasonKey === "alternate")) return { mark: "sup", line: "another way", ranges };
  if (sections.some((section) => section.level === "supporting" || section.level === "core")) return { mark: "sup", line: "supporting your goal", ranges };
  if (sections.some((section) => section.level === "later")) return { mark: "later", line: "needed only deeper", ranges };
  if (sections.some((section) => section.level === "already_shown")) return { mark: "shown", line: "already shown", ranges };
  if (sections.some((section) => section.level === "partial")) return { mark: "partial", line: "partly mapped for this goal", ranges };
  return { mark: "skip", line: "not needed for your goal", ranges };
}
