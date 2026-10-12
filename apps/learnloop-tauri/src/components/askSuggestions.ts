import type { SuggestedLearningObjectDto } from "../api/dto";

/** Slice 2 T6 (spec §9): a reader span without a provenance-linked learning
 *  object gets a labelled nearest-LO suggestion. The label says what it is, a
 *  suggestion and not a source link, so the learner never mistakes it for one. */
export function suggestionLine(suggestions: SuggestedLearningObjectDto[] | undefined): string | null {
  const titles = (suggestions ?? []).map((entry) => entry.title).filter((title) => title && title.trim());
  if (titles.length === 0) return null;
  const noun = titles.length === 1 ? "learning object" : "learning objects";
  return `Nearest ${noun} (a suggestion, not a source link): ${titles.join(" · ")}`;
}
