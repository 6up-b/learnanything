// Reader CA5: the salience-only records of a corresponding section peeked or
// opened (ux_reader_compare_ask_v1 §6.5 Records; CA5a's deferred events), from
// either list: CA5's judged "also in your books" or CA5a's unchecked hits.
// Ids and kinds only, never a title or the learner's words.
import type { CorrespondentSectionDto } from "../../api/dto";
import { logReaderAction } from "./activity";

export type CorrespondentAct = "corresponding_section_peeked" | "corresponding_section_opened";

export function logCorrespondentAct(
  event: CorrespondentAct,
  extractionId: string,
  sectionId: string | null,
  hit: Pick<CorrespondentSectionDto, "sourceId" | "extractionId" | "sectionId" | "jump" | "by">,
  via: "also_list" | "find_list",
): void {
  logReaderAction(event, {
    extraction_id: extractionId, section_id: sectionId, target_source_id: hit.sourceId,
    target_extraction_id: hit.extractionId, target_section_id: hit.sectionId, target_span_id: hit.jump.spanId,
    by: hit.by === "search" ? "search" : "judged", via,
  });
}
