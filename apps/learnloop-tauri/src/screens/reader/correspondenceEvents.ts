// Reader CA5: the salience-only records of a corresponding section peeked or
// opened (ux_reader_compare_ask_v1 §6.5 Records; CA5a's deferred events), from
// either list: CA5's judged "also in your books" or CA5a's unchecked hits,
// and (Reader CA6) side by side's narrow-window peek, so every record of the
// two events has the same payload keys. Ids and kinds only, never a title or
// the learner's words.
import type { CorrespondentSectionDto, ReaderActivityEvent } from "../../api/dto";
import { logReaderAction } from "./activity";

export type CorrespondentAct = "corresponding_section_peeked" | "corresponding_section_opened";

/** The hit's ids (a list line, or side by side's pane target, whose `by` is already "judged" | "search"). */
export interface CorrespondentActTarget {
  sourceId: string;
  extractionId: string;
  sectionId: string;
  jump: { spanId: string | null };
  by: CorrespondentSectionDto["by"] | "judged";
}

export function logCorrespondentAct(
  event: CorrespondentAct,
  extractionId: string,
  sectionId: string | null,
  hit: CorrespondentActTarget,
  via: "also_list" | "find_list" | "peek" | "key",
  // CA6's side-by-side sheet adds the visit's ids and the open book's (never other keys).
  extra: ReaderActivityEvent["payload"] = {},
): void {
  logReaderAction(event, {
    ...extra,
    extraction_id: extractionId, section_id: sectionId, target_source_id: hit.sourceId,
    target_extraction_id: hit.extractionId, target_section_id: hit.sectionId, target_span_id: hit.jump.spanId,
    by: hit.by === "search" ? "search" : "judged", via,
  });
}
