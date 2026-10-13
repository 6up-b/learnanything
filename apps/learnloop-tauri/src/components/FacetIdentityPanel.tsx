import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { CommandError, FacetIdentityActionDto, FacetIdentitySummaryDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "./term";

// Facet identity (handoff §4): the merges and absorbs one synthesis or append
// run applied, and the rewords (facet versions) its proposal wrote when it
// applied, each with a one-tap undo. The job result is a snapshot: the
// panel re-reads the run's actions when it mounts (and after an undo), so an
// action undone elsewhere, or one whose proposal was applied later, shows
// its live state. A merge that rides on a proposal not applied yet says so
// instead of offering an undo it cannot perform.

const MAX_CLAIM = 110;

function short(text: string): string {
  return text.length > MAX_CLAIM ? `${text.slice(0, MAX_CLAIM - 1)}…` : text;
}

function verb(action: FacetIdentityActionDto): string {
  if (action.action === "absorb") return action.absorbAs === "precondition" ? "absorbed as a precondition" : "absorbed as an example";
  return action.scope === "attach" ? "matched an existing facet" : "merged";
}

// Facet identity locks were removed (owner, 2026-10-12): an action never
// refuses because a facet carries evidence. It says what it did with it.
export function evidenceLabel(action: FacetIdentityActionDto): string | null {
  const evidenced = action.evidencedFacets ?? [];
  if (action.action === "reword") {
    return evidenced.length
      ? "the facet keeps its evidence, graded against the old wording, which is kept"
      : "the old wording is kept";
  }
  if (!evidenced.length) return null;
  return evidenced.length === 1
    ? "re-keys one facet's recorded evidence to the survivor"
    : `re-keys ${evidenced.length} facets' recorded evidence to the survivor`;
}

function describeLine(action: FacetIdentityActionDto) {
  if (action.action === "reword" && action.reworded) {
    const { from, to, fromVersion, toVersion } = action.reworded;
    return (
      <>
        {short(from)} <Faint>reworded (v{fromVersion ?? "?"} → v{toVersion ?? "?"}) to</Faint> {short(to)}
      </>
    );
  }
  return (
    <>
      {action.retired.map((facet) => short(facet.claim)).join("; ")}{" "}
      <Faint>{verb(action)} into</Faint> {short(action.survivor.claim)}
    </>
  );
}

function skippedNote(summary: FacetIdentitySummaryDto): string | null {
  if (summary.status === "judge_unavailable") return "duplicate check skipped: the judge was unavailable";
  if (summary.status === "judge_failed" || summary.status === "error") return "duplicate check failed; facets were kept as written";
  if (summary.status === "over_budget") return "duplicate check stopped at its spend cap; some facets were not checked";
  if (summary.status === "partial") return "duplicate check finished part of the facets";
  return null;
}

function stateLabel(action: FacetIdentityActionDto): string | null {
  if (action.status === "undone") return "undone";
  if (action.status === "abandoned") return "not applied";
  if (action.status === "applying" || action.status === "undoing") return "interrupted";
  if (action.undoable) return null;
  if (action.note) return "no undo";
  if (action.status === "proposed") return "applies with the proposal";
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
  const mounted = useRef(true);
  const runId = summary.runId ?? summary.actions?.[0]?.runId ?? null;
  const note = skippedNote(summary);

  const refresh = useCallback(async () => {
    if (!runId) return;
    try {
      const live = await api.listFacetIdentityActions(runId);
      if (mounted.current && live && Array.isArray(live.actions)) setActions(live.actions);
    } catch {
      // Keep the job's snapshot; the undo itself re-checks everything.
    }
  }, [runId]);

  useEffect(() => {
    mounted.current = true;
    void refresh();
    return () => {
      mounted.current = false;
    };
  }, [refresh]);

  if (!actions.length && !note) return null;

  async function undo(action: FacetIdentityActionDto) {
    if (busy) return;
    setBusy(action.id);
    try {
      const result = await api.undoFacetIdentityAction(action.id);
      const updated = result.action ?? { ...action, status: "undone" as const, undoable: false };
      setActions((current) => current.map((item) => (item.id === action.id ? updated : item)));
      await refresh();
    } catch (e) {
      onError((e as CommandError).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div style={{ marginTop: 12, border: `1px solid ${COLOR.border}`, padding: "9px 11px" }} data-testid="facet-identity">
      <div style={{ color: COLOR.cyan, fontFamily: FONT_MONO, fontSize: 11 }}>
        facet changes · {actions.length} {actions.length === 1 ? "change" : "changes"}
      </div>
      {note && <Faint style={{ display: "block", marginTop: 4, fontSize: 11 }}>{note}</Faint>}
      {actions.map((action) => {
        const state = stateLabel(action);
        const evidence = evidenceLabel(action);
        const details = [
          action.note,
          action.status === "applying" || action.status === "undoing" ? "finish it with learnloop doctor --fix-state" : null,
          evidence,
          action.contractNote,
          action.undoable && action.action !== "reword"
            ? "undo restores the facets; what grading recorded while they were merged stays with the survivor"
            : null,
          action.undoable && action.action === "reword" ? "undo restores the old wording" : null,
          action.rationale || null
        ].filter((part): part is string => Boolean(part));
        return (
          <div key={action.id} style={{ marginTop: 8, fontSize: 12, lineHeight: 1.5 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
              <span style={{ color: action.status === "undone" || action.status === "abandoned" ? COLOR.textFaint : COLOR.text, flex: 1, minWidth: 0 }}>
                {describeLine(action)}
              </span>
              {action.undoable && action.status === "applied" ? (
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => void undo(action)}
                  style={{ border: `1px solid ${COLOR.amber}`, background: "transparent", color: COLOR.amber, padding: "2px 8px", fontFamily: FONT_MONO, fontSize: 10, cursor: busy ? "default" : "pointer", opacity: busy && busy !== action.id ? 0.5 : 1 }}
                >
                  {busy === action.id ? "undoing…" : "undo"}
                </button>
              ) : state ? (
                <Faint style={{ fontFamily: FONT_MONO, fontSize: 10 }}>{state}</Faint>
              ) : null}
            </div>
            {details.length > 0 && (
              <Faint style={{ display: "block", fontSize: 10 }}>{details.join(" · ")}</Faint>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** The facet-identity block of a completed synthesis/append job, if any. */
export function facetIdentityOf(result: Record<string, unknown> | null | undefined): FacetIdentitySummaryDto | null {
  const block = result?.facetIdentity as FacetIdentitySummaryDto | null | undefined;
  return block && typeof block === "object" ? block : null;
}
