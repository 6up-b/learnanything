// Registry review (§5.7): facet-contract cards for a subject with claim /
// conditions / examples / non-goals / error signatures / repairs, identifiability
// warnings from synthesis generation-needs, lock chips, and pre-lock merge/coarsen
// actions that create REVIEW proposals (never auto-merge).

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { FacetContractCardDto, IdentifiabilityWarningDto, SubjectRegistryDto } from "../api/dto";
import { ProvenancePanel } from "../components/ProvenancePanel";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader, TermSelect } from "../components/term";

export function RegistryReviewScreen({
  subjectId,
  subjects,
  onSelectSubject,
  onOpenSource
}: {
  subjectId: string | null;
  subjects: { id: string; title: string }[];
  onSelectSubject: (id: string) => void;
  onOpenSource?: (extractionId: string, spanId: string, entityType: string, entityId: string) => void;
}) {
  const [registry, setRegistry] = useState<SubjectRegistryDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!subjectId) {
      setRegistry(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .getSubjectRegistry(subjectId)
      .then((res) => {
        if (!cancelled) {
          setRegistry(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [subjectId]);

  useEffect(() => {
    const cleanup = load();
    return cleanup;
  }, [load]);

  const proposeMerge = async (retiredFacetId: string, survivingFacetId: string, needId?: string | null) => {
    if (!subjectId) return;
    setError(null);
    try {
      await api.proposeFacetMerge({ subjectId, retiredFacetId, survivingFacetId, needId: needId ?? null });
      setNotice("Merge review item created → review in Proposals.");
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const facetOptions = useMemo(() => (registry?.facets ?? []).map((f) => f.facetId), [registry]);

  return (
    <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
        <SectionHeader style={{ marginTop: 0 }}>Registry review</SectionHeader>
        <TermSelect
          value={subjectId ?? ""}
          options={subjects.map((s) => ({ value: s.id, label: s.title }))}
          onChange={onSelectSubject}
          placeholder="— pick a subject —"
          width={240}
        />
        {registry ? <Faint>{registry.facetCount} facets · {registry.lockedCount} locked</Faint> : null}
      </div>

      {!subjectId ? <Faint>Pick a subject to review its facet registry.</Faint> : null}
      {loading ? <Faint>loading registry…</Faint> : null}
      {error ? <div style={{ color: COLOR.red, fontSize: 12 }}>{error}</div> : null}
      {notice ? <div style={{ color: COLOR.green, fontSize: 12 }}>{notice}</div> : null}

      {registry && registry.identifiabilityWarnings.length ? (
        <div>
          <SectionHeader style={{ marginTop: 0 }}>Identifiability warnings</SectionHeader>
          {registry.identifiabilityWarnings.map((w, i) => (
            <WarningRow key={w.id ?? i} warning={w} onCoarsen={() => void proposeMerge(w.facetIds[1], w.facetIds[0], w.id)} />
          ))}
        </div>
      ) : null}

      {registry ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {registry.facets.map((card) => (
            <FacetCard key={card.facetId} card={card} facetOptions={facetOptions} onMerge={(survivor) => void proposeMerge(card.facetId, survivor)} onOpenSource={onOpenSource} />
          ))}
          {registry.facets.length === 0 ? <Faint>No facets in this subject's registry yet.</Faint> : null}
        </div>
      ) : null}
    </div>
  );
}

function WarningRow({ warning, onCoarsen }: { warning: IdentifiabilityWarningDto; onCoarsen: () => void }) {
  const canCoarsen = warning.kind === "coarsen_distinction" && warning.facetIds.length === 2;
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.amber}`, padding: "10px 14px", marginTop: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Pill color={warning.kind === "coarsen_distinction" ? "amber" : "cyan"}>{warning.kind}</Pill>
        <span style={{ fontSize: 12, color: COLOR.text }}>{warning.targetKey}</span>
        <Faint style={{ fontSize: 11 }}>missing: {warning.missingCapability}</Faint>
        {canCoarsen ? (
          <button style={{ ...smallBtn, marginLeft: "auto" }} onClick={onCoarsen}>
            propose coarsening merge
          </button>
        ) : null}
      </div>
      {warning.detail ? <div style={{ fontSize: 12, color: COLOR.textDim, marginTop: 4 }}>{warning.detail}</div> : null}
    </div>
  );
}

function FacetCard({ card, facetOptions, onMerge, onOpenSource }: { card: FacetContractCardDto; facetOptions: string[]; onMerge: (survivor: string) => void; onOpenSource?: (extractionId: string, spanId: string, entityType: string, entityId: string) => void }) {
  const [showProvenance, setShowProvenance] = useState(false);
  const [mergeOpen, setMergeOpen] = useState(false);
  const others = facetOptions.filter((id) => id !== card.facetId);
  const [survivor, setSurvivor] = useState(others[0] ?? "");

  const accent = card.status === "reviewed" ? COLOR.greenSoft : card.status === "proposed" ? COLOR.amber : COLOR.textFaint;
  const lockDetail = card.lockReasons[0]?.detail;

  return (
    <div style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${accent}`, background: COLOR.bgElev, padding: "12px 16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 13, color: COLOR.text, fontFamily: FONT_MONO }}>{card.title ?? card.facetId}</span>
        <Faint style={{ fontSize: 11 }}>{card.facetId}</Faint>
        {card.kind ? <Pill color="slate">{card.kind}</Pill> : null}
        <Pill color={card.status === "reviewed" ? "green" : card.status === "proposed" ? "amber" : "slate"}>{card.status}</Pill>
        {card.locked ? <Pill color="red">locked</Pill> : <Pill color="green">pre-lock</Pill>}
      </div>
      {card.locked && lockDetail ? <Faint style={{ fontSize: 11, display: "block", marginTop: 4 }}>lock: {lockDetail}</Faint> : null}

      {card.claim ? <div style={{ fontSize: 13, color: COLOR.text, marginTop: 8, lineHeight: 1.6 }}>{card.claim}</div> : null}

      <ListBlock label="preconditions" items={card.conditions.preconditions} />
      <ListBlock label="postconditions" items={card.conditions.postconditions} />
      <ListBlock label="applicability" items={card.conditions.applicability} />
      <ListBlock label="examples (+)" items={card.examples.positive} />
      <ListBlock label="examples (−)" items={card.examples.negative} />
      <ListBlock label="non-goals" items={card.nonGoals} />
      <ListBlock label="error signatures" items={card.errorSignatures} />
      <ListBlock label="repairs" items={card.instructionalRepairs} />

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
        <span style={{ cursor: "pointer", color: COLOR.amberLink, fontSize: 12 }} onClick={() => setShowProvenance((v) => !v)}>
          {showProvenance ? "hide provenance" : "provenance"}
        </span>
        <button
          style={{ ...smallBtn, opacity: card.canMerge ? 1 : 0.4, cursor: card.canMerge ? "pointer" : "default" }}
          disabled={!card.canMerge}
          title={card.canMerge ? "" : lockDetail ?? "facet identity locked"}
          onClick={() => setMergeOpen((v) => !v)}
        >
          propose merge
        </button>
        {mergeOpen && card.canMerge ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
            <Faint style={{ fontSize: 11 }}>into</Faint>
            <TermSelect value={survivor} options={others} onChange={setSurvivor} width={200} />
            <button
              style={{ ...smallBtn, opacity: survivor ? 1 : 0.4 }}
              disabled={!survivor}
              onClick={() => {
                onMerge(survivor);
                setMergeOpen(false);
              }}
            >
              create review item
            </button>
          </span>
        ) : null}
      </div>

      {showProvenance ? (
        <div style={{ marginTop: 12 }}>
          <ProvenancePanel
            entityType="facet"
            entityId={card.facetId}
            onClose={() => setShowProvenance(false)}
            onOpenSource={onOpenSource ? (extractionId, spanId) => onOpenSource(extractionId, spanId, "facet", card.facetId) : undefined}
          />
        </div>
      ) : null}
    </div>
  );
}

function ListBlock({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 10, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: FONT_MONO }}>{label}</div>
      {items.map((item, i) => (
        <div key={i} style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
          · {item}
        </div>
      ))}
    </div>
  );
}

const smallBtn: CSSProperties = {
  padding: "4px 10px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: "transparent",
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 11,
  cursor: "pointer"
};
