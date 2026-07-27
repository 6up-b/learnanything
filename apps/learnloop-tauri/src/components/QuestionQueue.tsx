import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommandError, QuestionQueueRowDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader, type PillColor } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";
import { notifyQueueChanged, subscribeQueueChanged } from "../queueEvents";
import type { AskTarget } from "./AskOverlay";
import { OpenInSource } from "./OpenInSource";

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

interface SourceLaunch {
  extractionId: string;
  spanId: string;
  questionEventId: string;
  primedItemId: string | null;
}

export function QuestionQueuePanel({
  onContinueDialogue,
  onOpenPrimedPractice,
  onError
}: {
  onContinueDialogue: (target: AskTarget) => void;
  onOpenPrimedPractice: (practiceItemId: string) => void;
  onError: (message: string) => void;
}) {
  const [rows, setRows] = useState<QuestionQueueRowDto[] | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [selectedTargetById, setSelectedTargetById] = useState<Record<string, string>>({});
  const [sourceLaunch, setSourceLaunch] = useState<SourceLaunch | null>(null);

  const refresh = useCallback(() => {
    api
      .listQuestionQueue()
      .then((snap) => setRows(snap.questions))
      .catch(() => setRows(null)); // queue is ambient — never block Today on it
  }, []);

  useEffect(() => {
    refresh();
    return subscribeQueueChanged(refresh);
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
      const targetId =
        selectedTargetById[row.id] ??
        (row.promotionTargetIds.length === 1 ? row.promotionTargetIds[0] : undefined);
      if (row.context === "reader" && !targetId) {
        onError(
          row.promotionTargetIds.length > 1
            ? "Choose which learning object this reader question should practice."
            : "This reader span is not mapped to a learning object yet."
        );
        return;
      }
      setBusyId(row.id);
      try {
        const result = await api.promoteTutorQuestion(
          row.id,
          "practice",
          targetId ? { learningObjectId: targetId } : undefined
        );
        setRows((prev) =>
          (prev ?? []).map((r) =>
            r.id === row.id
              ? {
                  ...r,
                  promotion: result.promotion,
                  promotionRequest: result.request
                }
              : r
          )
        );
        notifyQueueChanged();
      } catch (error) {
        onError((error as CommandError).message);
      } finally {
        setBusyId(null);
      }
    },
    [onError, selectedTargetById]
  );

  if (!rows || rows.length === 0) return null;

  return (
    <>
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
          const dialogueTarget = targetForDialogue(row);
          const primedItemId = readyPracticeItemId(row);
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
                  {dialogueTarget ? (
                    <QueueAction
                      label="↳ continue dialogue"
                      disabled={busy}
                      onClick={() => onContinueDialogue(dialogueTarget)}
                    />
                  ) : null}
                  {row.sourceCitation ? (
                    <QueueAction
                      label="open canonical source"
                      disabled={busy}
                      onClick={() =>
                        setSourceLaunch({
                          extractionId: row.sourceCitation!.extractionId,
                          spanId: row.sourceCitation!.spanId,
                          questionEventId: row.id,
                          primedItemId: null
                        })
                      }
                    />
                  ) : null}
                  {row.sourceCitation && primedItemId ? (
                    <QueueAction
                      label="review → primed attempt"
                      disabled={busy}
                      onClick={() =>
                        setSourceLaunch({
                          extractionId: row.sourceCitation!.extractionId,
                          spanId: row.sourceCitation!.spanId,
                          questionEventId: row.id,
                          primedItemId
                        })
                      }
                    />
                  ) : null}
                  <QueueAction label="✓ resolved" disabled={busy} onClick={() => void resolve(row.id, "resolved")} />
                  <QueueAction label="dismiss" disabled={busy} onClick={() => void resolve(row.id, "dismissed")} />
                  {row.promotionRequest?.status === "failed" ? (
                    <>
                      <Pill color="red">
                        failed: {row.promotionRequest.errorMessage ?? row.promotionRequest.errorCode ?? "unknown error"}
                      </Pill>
                      {row.promotionRequest.retryable ? (
                        <QueueAction label="↻ retry" disabled={busy} onClick={() => void promote(row)} />
                      ) : null}
                    </>
                  ) : row.promotion ? (
                    <Pill color="green">
                      {row.promotion.route === "existing_item"
                        ? `ready: ${row.promotion.existingPracticeItemId ?? "?"}`
                        : row.promotion.route === "review_required"
                          ? `awaiting review${row.promotion.proposedPatchId ? `: ${row.promotion.proposedPatchId}` : ""}`
                          : row.promotion.createdPracticeItemId
                            ? `ready: ${row.promotion.createdPracticeItemId}`
                            : row.promotion.route.replace(/_/g, " ")}
                    </Pill>
                  ) : row.promotionRequest ? (
                    <Pill color="amber">
                      {row.promotionRequest.stage === "review"
                        ? "awaiting review"
                        : `authoring: ${row.promotionRequest.stage}`}
                    </Pill>
                  ) : (
                    <>
                      {row.context === "reader" && row.promotionTargetIds.length > 1 ? (
                        <select
                          value={selectedTargetById[row.id] ?? ""}
                          onChange={(event) =>
                            setSelectedTargetById((current) => ({
                              ...current,
                              [row.id]: event.target.value
                            }))
                          }
                          style={{
                            background: COLOR.bg,
                            color: COLOR.text,
                            border: `1px solid ${COLOR.border}`,
                            fontFamily: FONT_MONO,
                            fontSize: 10,
                            maxWidth: 260
                          }}
                        >
                          <option value="">choose learning object…</option>
                          {row.promotionTargetIds.map((id) => (
                            <option key={id} value={id}>{id}</option>
                          ))}
                        </select>
                      ) : null}
                      <QueueAction
                        label="→ practice this"
                        disabled={
                          busy ||
                          (row.context === "reader" &&
                            (row.promotionTargetIds.length === 0 ||
                              (row.promotionTargetIds.length > 1 && !selectedTargetById[row.id])))
                        }
                        onClick={() => void promote(row)}
                      />
                    </>
                  )}
                </div>
              </>
            ) : null}
            </div>
          );
        })}
      </div>
      {sourceLaunch ? (
        <OpenInSource
          extractionId={sourceLaunch.extractionId}
          spanId={sourceLaunch.spanId}
          context="open_question"
          entityType="question_event"
          entityId={sourceLaunch.questionEventId}
          onClose={() => {
            const primedItemId = sourceLaunch.primedItemId;
            setSourceLaunch(null);
            if (primedItemId) onOpenPrimedPractice(primedItemId);
          }}
        />
      ) : null}
    </>
  );
}

function targetForDialogue(row: QuestionQueueRowDto): AskTarget | null {
  if (row.context === "reader") {
    if (!row.noteId || !row.sourceCitation) return null;
    return {
      context: "reader",
      noteId: row.noteId,
      extractionId: row.sourceCitation.extractionId,
      spanId: row.sourceCitation.spanId
    };
  }
  if (row.context === "feedback") {
    if (!row.attemptId) return null;
    return {
      context: "feedback",
      attemptId: row.attemptId,
      practiceItemId: row.practiceItemId ?? undefined
    };
  }
  if (row.context === "practice") {
    if (!row.practiceItemId) return null;
    return {
      context: "practice",
      practiceItemId: row.practiceItemId,
      sessionId: row.sessionId ?? undefined
    };
  }
  if (!row.noteId) return null;
  return { context: "library", noteId: row.noteId };
}

function readyPracticeItemId(row: QuestionQueueRowDto): string | null {
  return (
    row.promotion?.existingPracticeItemId ??
    row.promotion?.createdPracticeItemId ??
    row.practiceItemId
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
