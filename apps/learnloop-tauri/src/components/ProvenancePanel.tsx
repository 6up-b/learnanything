import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { EntityProvenance, EntitySourceLink } from "../api/dto";
import { COLOR, Dim, Faint, FONT_MONO, Pill, type PillColor } from "./term";

// Minimal read-only provenance panel (source-lineage milestone). Shows an
// entity's semantic sources (with the semantic authority marked), its assessment
// alignment sources (distinctly labelled — NOT semantic authority), any recorded
// conflicts / notation mappings, and where the entity was introduced. The full
// span-peek / Open-in-source viewer is a later milestone.

// Relation → chip label + color. First matching rule wins; unrecognized
// relations fall back to a neutral slate chip echoing the raw relation.
const RELATION_RULES: Array<[RegExp, { label: string; color: PillColor }]> = [
  [/authorit/i, { label: "authority", color: "green" }],
  [/semantic|defines|derives|grounds|support/i, { label: "semantic", color: "cyan" }],
  [/assess|align|exam|calibrat/i, { label: "assessment", color: "amber" }],
  [/notation/i, { label: "notation", color: "pink" }]
];

function relationChip(relation: string | null): { label: string; color: PillColor } {
  const raw = relation ?? "";
  for (const [pattern, chip] of RELATION_RULES) {
    if (pattern.test(raw)) return chip;
  }
  return { label: raw || "source", color: "slate" };
}

function truncate(value: string, max = 12): string {
  return value.length > max ? `${value.slice(0, max)}…` : value;
}

// Canonical block_span_v1 is `span:<extraction>/<span>`; keep accepting the
// pre-v2 malformed `span:<span>` shape during permanent back-compat.
function spanFromLocator(locator: string | null): string | null {
  if (!locator) return null;
  const match = /^span:(?:[^/]+\/)?(.+)$/.exec(locator.trim());
  return match ? match[1] : null;
}

function SourceRow({
  link,
  isAuthority,
  overrideChip,
  onOpenSource
}: {
  link: EntitySourceLink;
  isAuthority?: boolean;
  overrideChip?: { label: string; color: PillColor };
  onOpenSource?: (extractionId: string, spanId: string) => void;
}) {
  const chip = overrideChip ?? relationChip(link.relation);
  const spanId = spanFromLocator(link.locator);
  const canOpen = Boolean(onOpenSource && link.extractionId && spanId);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        flexWrap: "wrap",
        borderTop: `1px solid ${COLOR.border}`,
        paddingTop: 6,
        fontSize: 12,
        fontFamily: FONT_MONO
      }}
    >
      <Pill color={chip.color}>{chip.label}</Pill>
      {isAuthority ? <Pill color="green">authority</Pill> : null}
      {link.stale ? <Pill color="red">stale</Pill> : null}
      {link.locator ? (
        <span style={{ color: COLOR.text }}>{link.locator}</span>
      ) : (
        <Faint>no locator</Faint>
      )}
      {link.sourceId ? (
        <Faint style={{ marginLeft: "auto" }}>{truncate(link.sourceId, 18)}</Faint>
      ) : null}
      {canOpen ? (
        <span
          onClick={() => onOpenSource!(link.extractionId as string, spanId as string)}
          title="Open in source"
          style={{
            marginLeft: link.sourceId ? 8 : "auto",
            color: COLOR.amberLink,
            cursor: "pointer",
            fontFamily: FONT_MONO,
            fontSize: 11
          }}
        >
          open ↗
        </span>
      ) : null}
    </div>
  );
}

function Section({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>{title}</span>
        {count != null ? <Faint style={{ fontSize: 11 }}>{count}</Faint> : null}
      </div>
      {children}
    </div>
  );
}

export function ProvenancePanel({
  entityType,
  entityId,
  onClose,
  onOpenSource
}: {
  entityType: string;
  entityId: string;
  onClose?: () => void;
  onOpenSource?: (extractionId: string, spanId: string) => void;
}) {
  const [provenance, setProvenance] = useState<EntityProvenance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setProvenance(null);
    api
      .getEntityProvenance(entityType, entityId)
      .then((result) => {
        if (!cancelled) setProvenance(result);
      })
      .catch((err) => {
        if (!cancelled) setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [entityType, entityId]);

  const authorityId = provenance?.semanticAuthority?.id ?? null;

  return (
    <div
      style={{
        width: 380,
        maxHeight: "70vh",
        overflowY: "auto",
        background: COLOR.bgElev,
        border: `1px solid ${COLOR.borderStrong}`,
        borderRadius: 3,
        padding: "12px 16px",
        fontFamily: FONT_MONO,
        color: COLOR.text
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 13, color: COLOR.amber }}>provenance</span>
        <Faint style={{ fontSize: 11 }}>{entityType}</Faint>
        <span style={{ flex: 1 }} />
        {onClose ? (
          <span
            onClick={onClose}
            title="close"
            style={{ cursor: "pointer", color: COLOR.textDim, fontSize: 13 }}
          >
            ✕
          </span>
        ) : null}
      </div>
      <Faint style={{ fontSize: 11 }}>{entityId}</Faint>

      {loading ? (
        <div style={{ marginTop: 12, fontSize: 12, color: COLOR.textFaint }}>loading…</div>
      ) : error ? (
        <div style={{ marginTop: 12, fontSize: 12, color: COLOR.red }}>{error}</div>
      ) : !provenance || !provenance.hasProvenance ? (
        <div style={{ marginTop: 12, fontSize: 12, color: COLOR.textFaint }}>
          <Dim>no recorded provenance</Dim> — this entity has no linked sources yet.
        </div>
      ) : (
        <>
          <Section title="Semantic sources" count={provenance.semanticSources.length}>
            {provenance.semanticSources.length > 0 ? (
              <div style={{ display: "grid", gap: 6 }}>
                {provenance.semanticSources.map((link) => (
                  <SourceRow key={link.id} link={link} isAuthority={link.id === authorityId} onOpenSource={onOpenSource} />
                ))}
              </div>
            ) : (
              <Faint style={{ fontSize: 12 }}>none</Faint>
            )}
          </Section>

          <Section title="Assessment alignment" count={provenance.assessmentAlignmentSources.length}>
            <Faint style={{ fontSize: 11 }}>not semantic authority — alignment evidence only</Faint>
            {provenance.assessmentAlignmentSources.length > 0 ? (
              <div style={{ display: "grid", gap: 6, marginTop: 6 }}>
                {provenance.assessmentAlignmentSources.map((link) => (
                  <SourceRow
                    key={link.id}
                    link={link}
                    overrideChip={{ label: "assessment", color: "amber" }}
                    onOpenSource={onOpenSource}
                  />
                ))}
              </div>
            ) : (
              <div style={{ marginTop: 6 }}>
                <Faint style={{ fontSize: 12 }}>none</Faint>
              </div>
            )}
          </Section>

          {provenance.conflicts.length > 0 ? (
            <Section title="Conflicts" count={provenance.conflicts.length}>
              <div style={{ display: "grid", gap: 6 }}>
                {provenance.conflicts.map((conflict) => (
                  <div
                    key={conflict.id}
                    style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 6, fontSize: 12 }}
                  >
                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                      <Pill color="red">conflict</Pill>
                      {conflict.status ? <Faint style={{ fontSize: 11 }}>{conflict.status}</Faint> : null}
                    </div>
                    {conflict.statement ? (
                      <div style={{ marginTop: 3, color: COLOR.text }}>{conflict.statement}</div>
                    ) : null}
                  </div>
                ))}
              </div>
            </Section>
          ) : null}

          {provenance.notationMappings.length > 0 ? (
            <Section title="Notation" count={provenance.notationMappings.length}>
              <div style={{ display: "grid", gap: 6 }}>
                {provenance.notationMappings.map((mapping) => (
                  <div
                    key={mapping.id}
                    style={{
                      borderTop: `1px solid ${COLOR.border}`,
                      paddingTop: 6,
                      fontSize: 12,
                      display: "flex",
                      gap: 8,
                      alignItems: "center",
                      flexWrap: "wrap"
                    }}
                  >
                    <Pill color="pink">notation</Pill>
                    <span style={{ color: COLOR.text }}>{mapping.canonicalNotation ?? "—"}</span>
                    <Faint>↔</Faint>
                    <span style={{ color: COLOR.textDim }}>{mapping.alternateNotation ?? "—"}</span>
                    {mapping.context ? <Faint style={{ fontSize: 11 }}>{mapping.context}</Faint> : null}
                  </div>
                ))}
              </div>
            </Section>
          ) : null}

          {provenance.introducedBy?.manifestHash ? (
            <div style={{ marginTop: 14, fontSize: 11, color: COLOR.textDim }}>
              <Faint>introduced by</Faint>{" "}
              <span title={provenance.introducedBy.manifestHash}>
                manifest {truncate(provenance.introducedBy.manifestHash, 10)}
              </span>
              {provenance.introducedBy.mode ? <Faint> · {provenance.introducedBy.mode}</Faint> : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
