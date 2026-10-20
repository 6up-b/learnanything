// Daily-loop DL2: where "Back to where you studied this" opens (Reader §9.3
// item 9). The Reader at the check's first anchor span in its source; the
// source must still be in the library. Opening at an inquiry branch is RW6b's
// (its provenance names the branch; this opens the passage).
import type { IntentRestorationDto, SourceLibraryCard } from "../api/dto";

export function readerTargetForRestoration(
  restoration: IntentRestorationDto,
  library: SourceLibraryCard[] | null | undefined
): { card: SourceLibraryCard; spanId: string | null } | null {
  if (!restoration.sourceId) return null;
  const card = (library ?? []).find((entry) => entry.sourceId === restoration.sourceId);
  return card ? { card, spanId: restoration.anchorSpanIds[0] ?? null } : null;
}
