// Reader workbench RW4e (spec §7.1, §7.9; UX §4.5): a library hit's role label.
// Ingest's role groups the passage ("definition", "worked example"); where the
// passage is ordinary prose and LearnLoop's model proposed a finer role, the
// label is that role with "model's label", so a proposal never reads as the
// book's own heading. Without a proposal the label is RW4a's (the group).
import type { LibraryHitDto } from "../../api/dto";

export const MODEL_LABEL = "model's label";

export function hitRoleLabel(hit: Pick<LibraryHitDto, "group" | "proposedRole">): string {
  const proposed = hit.proposedRole;
  if (proposed?.role) return `${proposed.role.replace(/_/g, " ")} (${proposed.label || MODEL_LABEL})`;
  return hit.group.toLowerCase();
}
