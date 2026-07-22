import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommandError, QuestionQueueRowDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader, type PillColor } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

// The outstanding-question queue (spec_andymatusnotes: "a queue of outstanding
// questions"). Renders on Today so open questions stay ambiently visible in the
// loop. answerStatus tracks whether the tutor answered; resolution is the
// learner's own "am I done with this?" — an answered question can stay open.

const CONTEXT_PILL: Record<string, PillColor> = {
  library: "cyan",
  practice: "amber",
  feedback: "green",
  reader: "purple"
};

export function QuestionQueuePanel({ onError }: { onError: (message: string) => void }) {
  const [rows, setRows] = useState<QuestionQueueRowDto[] | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api
      .listQuestionQueue()
      .then((snap) => setRows(snap.questions))
      .catch(() => setRows(null)); // queue is ambient — never block Today on it
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const resolve = useCallback(
    async (id: string, resolution: "resolved" | "dismissed") => {
      setBusyId(id);
      try {
        await api.resolveQuestionEvent(id, resolution);
        setRows((prev) => (prev ?? []).filter((r) => r.id !== id));
        if (expandedId === id) setExpandedId(null);
      } catch (error) {
        onError((error as CommandError).message);
      } finally {
        setBusyId(null);
      }
    },
    [expandedId, onError]
  );

  const promote = useCallback(
    async (row: QuestionQueueRowDto) => {
      setBusyId(row.id);
      try {
        const promotion = await api.promoteTutorQuestion(row.id, "practice");
        setRows((prev) => (prev ?? []).map((r) => (r.id === row.id ? { ...r, promotion } : r)));
      } catch (error) {
        onError((error as CommandError).message);
      } finally {
        setBusyId(null);
      }
    },
    [onError]
  );

  if (!rows || rows.length === 0) return null;

  return (
    <div style={{ padding: "0 16px 12px" }}>
      <SectionHeader>
        Open questions <Faint style={{ fontSize: 11 }}>({rows.length})</Faint>
      </SectionHeader>
      <Faint style={{ fontSize: 11, display: "block", marginBottom: 6 }}>
        questions you raised that are still yours — an answered question stays here until you decide it is settled.
      </Faint>
      {rows.map((row) => {
        const expanded = expandedId === row.id;
        const busy = busyId === row.id;
        return (
          <div
            key={row.id}
            style={{
              border: `1px solid ${COLOR.border}`,
              borderLeft: `3px solid ${COLOR.purplePill}`,
              marginBottom: 6,
              padding: "8px 10px",
              display: "flex",
              flexDirection: "column",
              gap: 6,
              background: COLOR.bgElev
            }}
          >
            <div
              onClick={() => setExpandedId(expanded ? null : row.id)}
              style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}
            >
              <Pill color={CONTEXT_PILL[row.context] ?? "slate"}>{row.context}</Pill>
              {row.answerStatus !== "answered" ? <Pill color="amber">{row.answerStatus}</Pill> : null}
              <span
                style={{
                  flex: 1,
                  minWidth: 0,
                  overflow: expanded ? "visible" : "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: expanded ? "normal" : "nowrap",
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  color: COLOR.text
                }}
              >
                {expanded ? <MarkdownMath value={row.questionMd} /> : row.questionMd}
              </span>
              <Faint style={{ fontSize: 10, flexShrink: 0 }}>{row.createdAt.slice(0, 10)}</Faint>
            </div>
            {expanded ? (
              <>
                {row.answerMd ? (
                  <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, borderTop: `1px solid ${COLOR.border}`, paddingTop: 6 }}>
                    <MarkdownMath value={row.answerMd} />
                  </div>
                ) : (
                  <Faint style={{ fontSize: 11 }}>no tutor answer recorded.</Faint>
                )}
                <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                  <QueueAction label="✓ resolved" disabled={busy} onClick={() => void resolve(row.id, "resolved")} />
                  <QueueAction label="dismiss" disabled={busy} onClick={() => void resolve(row.id, "dismissed")} />
                  {row.promotion ? (
                    <Pill color="green">
                      {row.promotion.route === "existing_item"
                        ? `scheduled: ${row.promotion.existingPracticeItemId ?? "?"}`
                        : row.promotion.createdPracticeItemId
                          ? `added: ${row.promotion.createdPracticeItemId}`
                          : row.promotion.route.replace(/_/g, " ")}
                    </Pill>
                  ) : (
                    <QueueAction label="→ practice this" disabled={busy} onClick={() => void promote(row)} />
                  )}
                </div>
              </>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function QueueAction({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return (
    <span
      onClick={disabled ? undefined : onClick}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 11,
        color: disabled ? COLOR.textFaint : COLOR.amberLink,
        textDecoration: "underline",
        textUnderlineOffset: 2,
        cursor: disabled ? "default" : "pointer"
      }}
    >
      {label}
    </span>
  );
}
