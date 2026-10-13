// Rewords waiting for the owner's one-tap confirm (owner, 2026-10-13).
//
// A model-proposed change to a facet's meaning with no textbook, lecture,
// paper, reference or alternate-explanation passage behind it is never written
// on its own: accepting its proposal holds it here, with the wording before and
// after and what it cited. "Confirm" applies it as the owner's own edit (an
// owner verdict, with an undo in the facet's history); "keep current wording"
// closes it. Exam material never reaches this list (it is refused), and an
// exam citation never shows its text. Shown in registry review and in the
// proposals inbox; no screen of its own.

import { useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { CommandError, FacetChangeSourceDto, FacetRewordConfirmDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, SectionHeader } from "./term";

const FIELD_LABEL: Record<string, string> = {
  kind: "kind",
  title: "title",
  claim: "claim",
  description: "definition",
  preconditions: "preconditions",
  postconditions: "postconditions",
  applicability: "applies when",
  non_goals: "not about",
  positive_examples: "examples",
  negative_examples: "non-examples"
};

const ROLE_LABEL: Record<string, string> = {
  primary_textbook: "textbook",
  lecture: "lecture",
  paper: "paper",
  reference: "reference",
  alternate_explanation: "alternate explanation",
  notes: "notes",
  problem_set: "problem set",
  exam: "exam"
};

export function fieldLabel(field: string): string {
  return FIELD_LABEL[field] ?? field.replace(/_/g, " ");
}

export function roleLabel(role: string): string {
  return ROLE_LABEL[role] ?? (role ? `${role.replace(/_/g, " ")} (unknown role)` : "unknown role");
}

/** A field's value as plain text: lists one per line, nothing as a dash. */
export function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.map((part) => valueText(part)).join("\n") : "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** One plain sentence on what the reword rests on. */
export function supportLine(confirm: FacetRewordConfirmDto): string {
  if (!confirm.sources.length) {
    return confirm.unresolved.length
      ? "None of its citations counts (they are outside the units you selected)."
      : "It cites no source.";
  }
  const roles = Array.from(new Set(confirm.sources.map((source) => roleLabel(source.role))));
  return `It cites only ${roles.join(", ")} material: no textbook, lecture, paper or reference passage.`;
}

function SourceLine({ source }: { source: FacetChangeSourceDto }) {
  return (
    <div style={{ fontSize: 11, lineHeight: 1.5, marginTop: 3 }}>
      <span style={{ fontFamily: FONT_MONO, color: COLOR.textDim }}>
        {roleLabel(source.role)} · {source.unitId || source.extractionId}
      </span>{" "}
      {source.assessmentOnly ? (
        <Faint>exam material: aligns assessment only, text hidden</Faint>
      ) : source.excerpt ? (
        <span style={{ color: COLOR.textDim }}>“{source.excerpt}”</span>
      ) : null}
    </div>
  );
}

function RewordConfirmCard({
  confirm,
  busy,
  onDecide
}: {
  confirm: FacetRewordConfirmDto;
  busy: boolean;
  onDecide: (decision: "confirm" | "keep") => void;
}) {
  const changed = confirm.fields.map(fieldLabel).join(", ");
  return (
    <div
      data-testid="reword-confirm"
      style={{ border: `1px solid ${COLOR.border}`, borderLeft: `3px solid ${COLOR.amber}`, padding: "10px 12px", background: COLOR.bgElev }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{confirm.facetId}</span>
        {confirm.title ? <Faint style={{ fontSize: 11 }}>{confirm.title}</Faint> : null}
        <Faint style={{ fontSize: 11, marginLeft: "auto" }}>new {changed} proposed</Faint>
      </div>
      {confirm.changes.map((change) => (
        <div key={change.field} style={{ marginTop: 8, fontSize: 12, lineHeight: 1.5 }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            {fieldLabel(change.field)}
          </div>
          <div style={wordingStyle}>
            <Faint>now: </Faint>
            <span style={{ color: COLOR.textDim }}>{valueText(change.before)}</span>
          </div>
          <div style={wordingStyle}>
            <Faint>new: </Faint>
            <span style={{ color: COLOR.text }}>{valueText(change.after)}</span>
          </div>
        </div>
      ))}
      <div style={{ marginTop: 8, fontSize: 12, color: COLOR.amber }}>{supportLine(confirm)}</div>
      {confirm.sources.map((source) => (
        <SourceLine key={`${source.extractionId}/${source.spanId}`} source={source} />
      ))}
      {confirm.unresolved.length ? (
        <Faint style={{ display: "block", fontSize: 10, marginTop: 3 }}>not counted: {confirm.unresolved.join("; ")}</Faint>
      ) : null}
      {confirm.interrupted ? (
        <Faint style={{ display: "block", fontSize: 10, marginTop: 3 }}>an earlier confirm did not finish ({confirm.interrupted}); nothing changed</Faint>
      ) : null}
      <div style={{ display: "flex", gap: 10, marginTop: 10, alignItems: "center" }}>
        <button type="button" disabled={busy} onClick={() => onDecide("confirm")} style={{ ...button, borderColor: COLOR.green, color: COLOR.green }}>
          confirm reword
        </button>
        <button type="button" disabled={busy} onClick={() => onDecide("keep")} style={button}>
          keep current wording
        </button>
        <Faint style={{ fontSize: 10 }}>a confirm can be undone from the facet's history</Faint>
      </div>
    </div>
  );
}

export function RewordConfirmList({
  confirms,
  onDecided,
  onError
}: {
  confirms: FacetRewordConfirmDto[];
  onDecided?: (confirm: FacetRewordConfirmDto, decision: "confirm" | "keep") => void;
  onError?: (message: string) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [decided, setDecided] = useState<Set<string>>(new Set());
  const visible = confirms.filter((confirm) => confirm.status === "pending" && !decided.has(confirm.actionId));
  if (!visible.length) return null;

  async function decide(confirm: FacetRewordConfirmDto, decision: "confirm" | "keep") {
    if (busy) return;
    setBusy(confirm.actionId);
    try {
      await api.decideFacetReword(confirm.actionId, decision);
      setDecided((current) => new Set(current).add(confirm.actionId));
      onDecided?.(confirm, decision);
    } catch (err) {
      onError?.((err as CommandError)?.message ?? String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div data-testid="reword-confirms" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <SectionHeader style={{ marginTop: 0 }}>Rewords waiting for your confirm</SectionHeader>
      <Faint style={{ fontSize: 12, lineHeight: 1.5 }}>
        A source update proposed new wording for {visible.length === 1 ? "this facet" : "these facets"} without a textbook,
        lecture, paper or reference passage behind it. Nothing has changed yet: confirm the new wording, or keep the current one.
      </Faint>
      {visible.map((confirm) => (
        <RewordConfirmCard
          key={confirm.actionId}
          confirm={confirm}
          busy={busy !== null}
          onDecide={(decision) => void decide(confirm, decision)}
        />
      ))}
    </div>
  );
}

const wordingStyle: CSSProperties = { whiteSpace: "pre-wrap", marginTop: 2 };

const button: CSSProperties = {
  padding: "4px 10px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: "transparent",
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 11,
  cursor: "pointer"
};
