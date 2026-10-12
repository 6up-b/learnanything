import { useState } from "react";
import { api } from "../api/client";
import type { CommandError, FacetIdentityActionDto, FacetIdentitySummaryDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "./term";

// Facet identity (handoff §4): the merges and absorbs one synthesis or append
// run applied, each with a one-tap undo. A merge that rides on a proposal not
// applied yet says so instead of offering an undo it cannot perform.

const MAX_CLAIM = 110;

function short(text: string): string {
  return text.length > MAX_CLAIM ? `${text.slice(0, MAX_CLAIM - 1)}…` : text;
}

function verb(action: FacetIdentityActionDto): string {
  if (action.action === "absorb") return action.absorbAs === "precondition" ? "absorbed as a precondition" : "absorbed as an example";
  return action.scope === "attach" ? "matched an existing facet" : "merged";
}

function skippedNote(summary: FacetIdentitySummaryDto): string | null {
  if (summary.status === "judge_unavailable") return "duplicate check skipped: the judge was unavailable";
  if (summary.status === "judge_failed" || summary.status === "error") return "duplicate check failed; facets were kept as written";
  if (summary.status === "over_budget") return "duplicate check stopped at its spend cap; some facets were not checked";
  if (summary.status === "partial") return "duplicate check finished part of the facets";
  return null;
}

export function FacetIdentityPanel({
  summary,
  onError
}: {
  summary: FacetIdentitySummaryDto;
  onError: (message: string) => void;
}) {
  const [actions, setActions] = useState<FacetIdentityActionDto[]>(summary.actions ?? []);
  const [busy, setBusy] = useState<string | null>(null);
  const note = skippedNote(summary);
  if (!actions.length && !note) return null;

  async function undo(action: FacetIdentityActionDto) {
    if (busy) return;
    setBusy(action.id);
    try {
      const result = await api.undoFacetIdentityAction(action.id);
      const updated = result.action ?? { ...action, status: "undone" as const, undoable: false };
      setActions((current) => current.map((item) => (item.id === action.id ? updated : item)));
    } catch (e) {
      onError((e as CommandError).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div style={{ marginTop: 12, border: `1px solid ${COLOR.border}`, padding: "9px 11px" }} data-testid="facet-identity">
      <div style={{ color: COLOR.cyan, fontFamily: FONT_MONO, fontSize: 11 }}>
        duplicate facets · {actions.length} {actions.length === 1 ? "change" : "changes"}
      </div>
      {note && <Faint style={{ display: "block", marginTop: 4, fontSize: 11 }}>{note}</Faint>}
      {actions.map((action) => (
        <div key={action.id} style={{ marginTop: 8, fontSize: 12, lineHeight: 1.5 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <span style={{ color: action.status === "undone" ? COLOR.textFaint : COLOR.text, flex: 1, minWidth: 0 }}>
              {action.retired.map((facet) => short(facet.claim)).join("; ")}{" "}
              <Faint>{verb(action)} into</Faint> {short(action.survivor.claim)}
            </span>
            {action.status === "undone" ? (
              <Faint style={{ fontFamily: FONT_MONO, fontSize: 10 }}>undone</Faint>
            ) : action.undoable ? (
              <button
                type="button"
                disabled={busy !== null}
                onClick={() => void undo(action)}
                style={{ border: `1px solid ${COLOR.amber}`, background: "transparent", color: COLOR.amber, padding: "2px 8px", fontFamily: FONT_MONO, fontSize: 10, cursor: busy ? "default" : "pointer", opacity: busy && busy !== action.id ? 0.5 : 1 }}
              >
                {busy === action.id ? "undoing…" : "undo"}
              </button>
            ) : action.note ? (
              <Faint style={{ fontFamily: FONT_MONO, fontSize: 10 }}>no undo</Faint>
            ) : (
              <Faint style={{ fontFamily: FONT_MONO, fontSize: 10 }}>applies with the proposal</Faint>
            )}
          </div>
          {(action.rationale || action.locked || action.note) && (
            <Faint style={{ display: "block", fontSize: 10 }}>
              {action.note ? `${action.note} · ` : ""}
              {action.locked ? "facet had practice history; undo restores it · " : ""}
              {action.rationale}
            </Faint>
          )}
        </div>
      ))}
    </div>
  );
}

/** The facet-identity block of a completed synthesis/append job, if any. */
export function facetIdentityOf(result: Record<string, unknown> | null | undefined): FacetIdentitySummaryDto | null {
  const block = result?.facetIdentity as FacetIdentitySummaryDto | null | undefined;
  return block && typeof block === "object" ? block : null;
}
