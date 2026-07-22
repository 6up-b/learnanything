// P3 reader render-view offline fixture (spec_tauri_ui §4/§5, U-031).
//
// Every new screen must render offline from a fixture state with no jobs / no AI.
// ReaderScreen fetches `reader.render_view` from the sidecar; when the sidecar is
// unavailable (or the reader is owner-disabled) it renders this deterministic
// marker-markdown chapter instead. Shape matches ReaderRenderViewDto verbatim.

import type { ReaderRenderViewDto } from "../api/dto";

export const readerRenderViewFixture: ReaderRenderViewDto = {
  renderViewId: "rv_fixture_symmetric",
  extractionId: "ext_symmetric",
  revisionId: "rev_symmetric",
  sourceId: "src_symmetric",
  renderer: "marker_markdown",
  rendererVersion: "1",
  contentHash: "sha256:fixture",
  status: "ready",
  layers: {
    source_bytes: "authoritative immutable artifact",
    source_revision: "immutable identity/version of those bytes",
    extraction_ir: "versioned derived representation; may contain errors",
    render_view: "replaceable marker-markdown/KaTeX presentation",
    source_object: "per-source reviewed/proposed semantic object",
    canonical_domain: "reviewed cross-source facets/LOs/blueprints",
  },
  blocks: [
    {
      displayNodeId: "node-span_symmetric_intro",
      spanId: "span_symmetric_intro",
      blockType: "Section",
      markdown: "## Symmetric matrices and variance",
      sanitized: false,
      katexNodes: [],
      assets: [],
      health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
    },
    {
      displayNodeId: "node-span_symmetric_prose",
      spanId: "span_symmetric_prose",
      blockType: "Text",
      markdown:
        "A real symmetric matrix $A = A^\\top$ admits an orthonormal eigenbasis. When choosing a decomposition for a variance problem, the **spectral decomposition** is preferred over a general SVD because the eigenvalues are the variances along principal axes.",
      sanitized: false,
      katexNodes: [],
      assets: [],
      health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
    },
    {
      displayNodeId: "node-span_spectral_worked",
      spanId: "span_spectral_worked",
      blockType: "Text",
      markdown:
        "Worked example: for $A = \\begin{bmatrix} 2 & 1 \\\\ 1 & 2 \\end{bmatrix}$, the eigenvalues $3$ and $1$ are the variances along the eigenvectors $(1,1)/\\sqrt2$ and $(1,-1)/\\sqrt2$.",
      sanitized: false,
      katexNodes: [],
      assets: [],
      health: { status: "suspect", recommendedView: "crop_adjacent", reasonFlags: ["equation_low_confidence"] },
    },
  ],
};
