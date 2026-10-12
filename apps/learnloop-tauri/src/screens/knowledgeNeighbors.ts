import type { KnowledgeItemTextNeighbors, KnowledgeMapPoint } from "../api/dto";

// Honest label for an item's neighbour list on the knowledge map (Slice 2 T7,
// display only): say which ranking chose it, and never imply that similar
// wording means the same skill (Slice 2 R2).
export function neighborCaption(
  point: Pick<KnowledgeMapPoint, "neighborBasis">,
  itemText: KnowledgeItemTextNeighbors | undefined
): string {
  const coverage = itemText ? `${itemText.embedded}/${itemText.stems} items embedded` : null;
  // A replacement `embedding.model` ranks nothing until its re-embed catches up.
  const pending = itemText?.enabled && itemText.pendingModel
    ? ` · ${itemText.pendingModel.modelId}: ${itemText.pendingModel.embedded}/${itemText.stems} re-embedded, used once complete`
    : "";
  if (point.neighborBasis === "item_text") {
    const source = itemText ? `stored ${itemText.modelId} vectors, ${coverage}` : "stored vectors";
    return `by similar wording · ${source} · not a same-skill match${pending}`;
  }
  if (itemText?.enabled && itemText.embedded > 0) {
    return `by shared facets + concept graph · wording vectors: ${coverage}${pending}`;
  }
  return "by shared facets + concept graph";
}
