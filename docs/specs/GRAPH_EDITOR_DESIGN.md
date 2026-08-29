# Graph / Knowledge-Map Editor — implementation design

Working design for user-editable relations in the Tauri app. Read together with
`spec_knowledge_model.md` (§3.4 locks, §8 three graphs, §9.6 UI, §12 mutation
contract). This file is the single source of truth for cross-agent contracts:
method names, param/DTO shapes, and file ownership. Follow existing repo
conventions everywhere (handlers use `@method` + `ParamsModel` + `versioned`,
DTOs camelCase via `dto.to_camel`, frontend uses `api.*` in
`apps/learnloop-tauri/src/api/client.ts`).

## Non-negotiable principles

1. **One write path.** Every user edit compiles to proposal items in the
   existing proposals machinery (`services/proposals.py`, `services/patches.py`,
   proposals inbox screen). No handler writes vault YAML directly.
2. **Locks are visible before the gesture.** `curriculum_locks.can_apply` /
   `identity_locks` drive padlock UI; a locked action shows reasons and offers
   "queue a restructure request", never a fake apply.
3. **Layer honesty.** Semantic edges (relations.yaml) affect navigation + map
   geometry only; recipes/blueprints govern readiness. Every edge-editing
   surface carries a caption stating this and links to the recipe editor.
4. **Determinism.** Preview endpoints are pure reads; byte-identical on
   identical input.

## New/extended sidecar methods

### Write path (owner: backend agent B1)

- `propose_graph_edits` — params:
  `{ rationale: str, edits: [ { item_type: "concept_edge"|"learning_object"|"task_blueprint"|"concept", operation: "create"|"update"|"delete", payload: dict, target_entity_id: str|None } ] }`.
  Creates ONE proposal batch (provider `"user"`, purpose `"graph_editor"`,
  summary = rationale) with one proposal item per edit, validated exactly like
  Codex-authored items (reuse `persist_authoring_proposal` /
  `AuthoringProposal` machinery or the closest reusable seam — do not fork
  validation logic). Returns `{ batch_id, items: [...] }` + refreshed proposals
  payload shape. Items land pending in the inbox; the UI routes there.
- `queue_restructure_request` — params
  `{ facet_ids: [str], requested_operation: "merge"|"split", rationale: str }`.
  Durable record for locked-facet restructure intent (spec §17 machinery does
  not exist yet — this only queues intent). Reuse the most fitting existing
  durable queue (generation-needs table is the expected fit, kind
  `restructure_request`; inspect first) and surface it in the maintenance feed.
  Returns the created record.
- Direction-resolution maintenance notices: extend
  `services/maintenance_feed.py` with an `ambiguous_edge_direction` notice
  kind. Heuristics (keep modest): (a) prerequisite cycles, (b) A→B and B→A
  prerequisite pairs, (c) `proposed`-status prerequisite edges. Each notice
  carries evidence to inform direction: attempt-ordering stats per concept pair
  (success rate on B-items before vs after first success on A-items — derive
  from existing attempt history queries; add a repository helper if needed) and
  the edge's provenance/rationale if present. New method
  `resolve_edge_direction` — params
  `{ edge_id: str, resolution: "keep"|"flip"|"retype_related"|"retire", rationale: str }` —
  compiles to a `concept_edge` proposal item via the same service used by
  `propose_graph_edits` and resolves the notice.

B1 owns changes to `src/learnloop/db/repositories.py` this wave. New handler
file: `src/learnloop_sidecar/handlers/graph_edit.py`. Service:
`src/learnloop/services/graph_edit_proposals.py`. Tests:
`tests/test_graph_edit_proposals.py`.

### Read/preview path (owner: backend agent B2)

- Extend `get_knowledge_map`'s `facet_field` points with
  `locked: bool` and `lock_sources: [str]` (distinct `LockReason.source`
  values), computed via `curriculum_locks.identity_locks` (one call, not per
  point).
- `get_facet_detail` — params `{ facet_id }`. Returns:
  `{ facet: {id, title, kind, claim, preconditions, positive_examples, negative_examples, non_goals, error_signatures, aliases, status}, lock: {locked, reasons: [{source, detail}]}, membership: [{learning_object_id, lo_title, blueprint_id, recipe_id, capability, modality, role}], evidence: {ready, ready_ghost, evidence_mass, capability_ledger: [{capability, direct_positive_mass, direct_negative_mass, certification_credit, demonstrated}]}, shared_with: [learning_object_ids...] }`.
  Pure read composing existing services (`facet_evidence_timeline`,
  capability ledger reads, `_facet_field`-style membership walk, `can_apply`).
- `list_facets` — lightweight `{ facets: [{id, title, kind, status, locked}] }`
  for autocomplete pickers.
- `preview_knowledge_map` — params
  `{ added_edges: [{source, target, relation_type}], removed_edge_ids: [str] }`.
  Recomputes the item-map MDS (`get_knowledge_map` pipeline) against the
  hypothetical semantic edge set. Returns `{ points: [{id, x, y}], stress }`
  plus `baseline: {points, stress}` so the UI can draw displacement without a
  second call. Refactor `get_knowledge_map` internals into a shared pure
  function rather than duplicating.
- `preview_blueprint_readiness` — params
  `{ learning_object_id, blueprints: <edited blueprints payload, same shape as LO YAML> }`.
  Returns `{ current: {readiness, bottleneck}, proposed: {readiness, bottleneck}, identifiability_warnings: [str], affected_goals: [{goal_id, title}] }`.
  Compose `capability_grid.lo_blueprint_readiness` (against a hypothetical LO —
  build an in-memory copy; never mutate the loaded vault) and
  `services/identifiability.py` scoped to the LO neighborhood.

B2 must NOT modify `db/repositories.py` (B1 owns it this wave) — compose
existing repository methods. New handler code goes in
`src/learnloop_sidecar/handlers/knowledge_model.py` or a new
`handlers/facet_detail.py`. Tests: `tests/test_graph_editor_reads.py`.

## API layer (owner: agent A, after B1+B2)

Add DTO types (`apps/learnloop-tauri/src/api/dto.ts`) and client methods
(`apps/learnloop-tauri/src/api/client.ts`) for all six methods above plus the
extended facet-field fields, following the existing camelCase/versioned
conventions exactly. No screen changes.

## Frontend (owners: F1, F2, F3 — do not edit client.ts/dto.ts except
append-only additions if a contract gap is discovered; note any such gap in
your final report)

### F1 — GraphScreen edit mode (owns `apps/learnloop-tauri/src/screens/GraphScreen.tsx` + new components under `src/components/graphedit/`)

- `edit` toggle beside the map/knowledge toggle. In edit mode:
  click source node → click target node → relation-type picker (reuse
  `RELATION_STYLE` colors) creates a pending edge. Click an existing edge →
  popover: flip direction / retype / retire. Esc cancels.
- Pending edits render as dashed ghost edges (and struck-through for retire)
  with a "N pending edits" strip: rationale input (required) + "file edits" →
  `api.proposeGraphEdits` → success toast linking to the Proposals screen,
  pending overlay cleared.
- Honesty caption in the picker/popover: "prerequisite edges order the
  curriculum and shape the map; they never change readiness — edit the LO
  recipe to change requirements", with an inspect link to the LO.
- Syllabus column (collapsible right-side list in edit mode): concepts in
  derived topological order (prerequisite depth, ties alphabetical). Dragging a
  concept earlier/later computes the minimal prerequisite edge
  additions/flips needed and stages them as pending edits; refuse (with a
  message) drags that would create a cycle.
- Geometry preview: when pending edits touch semantic edges, a "preview
  geometry" button calls `api.previewKnowledgeMap` and renders an overlay on
  the knowledge-map view (or an inline mini-view): baseline points, arrows to
  new positions, old→new stress readout.

### F2 — Locks, facet inspector, merge flow (owns `KnowledgeMapScreen.tsx`, `KnowledgeTerrainView.tsx`, new `src/components/FacetInspector.tsx`)

- Padlock ring / lock glyph on locked facet points in the knowledge field
  (from the new `locked` field); legend entry explaining the grace window
  ("unlocked facets can still be merged/split cheaply").
- FacetInspector panel (opened from a field point, reachable via existing
  `onInspect` plumbing): contract, lock chip with verbatim reasons,
  membership list (LO/recipe/capability/modality) with inspect links,
  capability ledger mini-grid, "shared with" cross-links.
- Merge flow: "merge into…" button → facet autocomplete (`api.listFacets`) →
  side-by-side contract comparison (claim, examples, error signatures) →
  survivor selection → rationale → `api.proposeFacetMerge` (method exists:
  `propose_facet_merge`) → route to review. If either facet is locked, the
  button instead opens lock reasons + "queue restructure request" →
  `api.queueRestructureRequest`.

### F3 — Recipe tree editor + direction cards (owns LO detail in `InspectorOverlay.tsx` / its LO detail component, `MaintenanceScreen.tsx`)

- Editable recipe tree on LO detail: blueprints → recipes → components
  (facet + capability + all_of/any_of + modality + integration slot). Edits:
  add component (facet autocomplete via `api.listFacets`, capability picker),
  remove, move all_of↔any_of, set modality, set/clear integration. All edits
  are local state until "file as proposal".
- Blast-radius panel beside the tree: debounced `api.previewBlueprintReadiness`
  — current vs proposed readiness, bottleneck change, identifiability
  warnings, affected goals.
- "File as proposal" → `api.proposeGraphEdits` with a `learning_object` update
  payload (full edited LO), rationale required.
- MaintenanceScreen: render `ambiguous_edge_direction` notices as cards:
  the concept pair, the three-way choice (keep / flip / merely related) plus
  retire, the attempt-ordering evidence, edge provenance; resolving calls
  `api.resolveEdgeDirection` and refreshes the feed.

## Verification

Backend: `pytest tests/test_graph_edit_proposals.py tests/test_graph_editor_reads.py`
plus the existing suites touched (`tests/test_sidecar_contract.py` must pass —
new methods need contract registration if that suite enumerates methods).
Frontend: `npm run build` (tsc) in `apps/learnloop-tauri` must pass.
