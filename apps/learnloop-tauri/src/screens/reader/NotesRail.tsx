// The Reader rail's Notes tab (RW1a split of ReaderScreen; a move, not a
// redesign): capture and the palette, exercise import, "make your own
// practice", background requests, the commitment arc and the annotations.
import type { Dispatch, SetStateAction } from "react";
import type { ReaderArcDto, ReaderCoachLintDto, ReaderExerciseImportResult, ReaderRenderBlockDto } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Pill, SectionHeader } from "../../components/term";
import { PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import { authoredQuestionMessage, type AuthoredQuestionStatus } from "./authoredQuestion";
import { clip, selectionNodes, type MarginAnnotation, type ReaderSelection } from "./readerShared";
import { MeaningLabel, ModelVoice } from "./voices";
import { parseRequestError, parseRequestResult, type BackgroundRequest, type SynthesizedObject } from "./useReaderRequests";

// The three visible primitives / nine presets (§5.2). Only the three commit presets
// are P1 commit-class; Ask and Mark never create commitments (§15.2).
// Naming: the "request" group runs in the BACKGROUND (demand-paged synthesis,
// results land in this rail) — deliberately distinct from the ask tab, which
// answers immediately about the selected span.
export const PALETTE: Array<{ group: string; presets: Array<{ preset: string; label: string }> }> = [
  {
    group: "Request · answered in background",
    presets: [
      { preset: "ask", label: "research this" },
      { preset: "worked_example", label: "worked example" },
      { preset: "alt_explanation", label: "explain differently" },
      { preset: "why_matters", label: "why this matters" },
    ],
  },
  {
    group: "Remember later",
    presets: [
      { preset: "test_me_later", label: "test me later" },
      { preset: "help_me_remember", label: "help me remember" },
      { preset: "connect_it", label: "connect it" },
    ],
  },
  {
    group: "Mark",
    presets: [
      { preset: "mark_confusing", label: "mark confusing" },
      { preset: "not_worth_remembering", label: "not worth remembering" },
    ],
  },
];

export interface ExerciseImportState {
  batchId: string;
  status: string;
  quote: string;
  result: ReaderExerciseImportResult | null;
  error: string | null;
  /** The passages the exercise was selected from (RW2a's workbench anchor). */
  spanIds?: string[];
}

export interface NotesRailProps {
  visible: boolean;
  offline: boolean;
  busy: boolean;
  pdfSurfaceActive: boolean;
  activeSpan: string | null;
  activeBlock: ReaderRenderBlockDto | null;
  // capture
  selection: ReaderSelection | null;
  selectionActions: string[];
  editingCapture: boolean;
  setEditingCapture: Dispatch<SetStateAction<boolean>>;
  clearSelection: () => void;
  editCaptureText: (text: string) => void;
  resetCaptureText: () => void;
  note: string;
  setNote: Dispatch<SetStateAction<string>>;
  captureHighlight: () => void | Promise<void>;
  invokePreset: (preset: string) => void | Promise<void>;
  // exercise import
  importExercise: () => void | Promise<void>;
  exerciseImport: ExerciseImportState | null;
  setExerciseImport: Dispatch<SetStateAction<ExerciseImportState | null>>;
  exerciseImportActive: boolean;
  /** RW2a: "work through this" on the selection (absent while the workbench is off). */
  onWorkThrough?: () => void;
  /** RW2a: "work through this" on an imported exercise. */
  onWorkThroughItem?: (item: ReaderExerciseImportResult["items"][number]) => void;
  // make your own practice
  authoringOpen: boolean;
  setAuthoringOpen: Dispatch<SetStateAction<boolean>>;
  setAuthoringSpanId: Dispatch<SetStateAction<string | null>>;
  authoringQuote: string;
  setAuthoringQuote: Dispatch<SetStateAction<string>>;
  authoredQuestion: string;
  setAuthoredQuestion: Dispatch<SetStateAction<string>>;
  authoredAnswer: string;
  setAuthoredAnswer: Dispatch<SetStateAction<string>>;
  authoredCardId: string | null;
  setAuthoredCardId: Dispatch<SetStateAction<string | null>>;
  authoredStatus: AuthoredQuestionStatus | undefined;
  authoringBusy: boolean;
  saveOwnQuestion: () => void | Promise<void>;
  coach: ReaderCoachLintDto | null;
  setCoach: Dispatch<SetStateAction<ReaderCoachLintDto | null>>;
  runCoach: () => void | Promise<void>;
  // background requests
  requests: BackgroundRequest[];
  requestLoadError: string | null;
  refreshRequests: () => void | Promise<void>;
  synthesizedObjects: Map<string, SynthesizedObject>;
  openProposalIds: Set<string>;
  proposalCount: number;
  expandedRequests: Set<string>;
  setExpandedRequests: Dispatch<SetStateAction<Set<string>>>;
  retryRequest: (requestId: string) => void | Promise<void>;
  decideProposal: (proposalId: string, decision: "accept" | "reject") => void | Promise<void>;
  jumpToSpan: (spanId: string) => void;
  /** A request result's passage is an investigative jump (a detour while
   *  reader_inquiry is on). */
  peekPassage?: (spanId: string) => void;
  // commitment arc
  arc: ReaderArcDto | null;
  pauseArc: () => void | Promise<void>;
  setArcPolicy: (policy: string) => void | Promise<void>;
  // annotations
  annotations: MarginAnnotation[];
  jumpToAnnotation: (annotation: MarginAnnotation) => void;
  reanchorAnnotation: (annotationId: string) => void | Promise<void>;
  manualAnchorToSelection: (annotationId: string) => void | Promise<void>;
  reanchorNotes: Record<string, string>;
  editingAnnotationId: string | null;
  setEditingAnnotationId: Dispatch<SetStateAction<string | null>>;
  editingAnnotationText: string;
  setEditingAnnotationText: Dispatch<SetStateAction<string>>;
  saveAnnotationEdit: () => void | Promise<void>;
  deleteAnnotation: (annotationId: string) => void | Promise<void>;
  /** The selection touches material held out of LearnLoop's models (exam
   *  protection decides): the reason. Highlights, notes and marks stay; no
   *  action that would show it to a model is offered. */
  protectionMessage?: string | null;
}

/** The palette groups that send the selection to a model (background
 *  requests, remember-later synthesis); "Mark" stays local. */
const MODEL_GROUPS: ReadonlySet<string> = new Set(["Request · answered in background", "Remember later"]);

export function NotesRail(props: NotesRailProps) {
  const {
    visible, offline, busy, pdfSurfaceActive, activeSpan, activeBlock,
    selection, selectionActions, editingCapture, setEditingCapture, clearSelection,
    editCaptureText, resetCaptureText, note, setNote, captureHighlight, invokePreset,
    importExercise, exerciseImport, setExerciseImport, exerciseImportActive, onWorkThrough, onWorkThroughItem,
    authoringOpen, setAuthoringOpen, setAuthoringSpanId, authoringQuote, setAuthoringQuote,
    authoredQuestion, setAuthoredQuestion, authoredAnswer, setAuthoredAnswer,
    authoredCardId, setAuthoredCardId, authoredStatus, authoringBusy, saveOwnQuestion,
    coach, setCoach, runCoach,
    requests, requestLoadError, refreshRequests, synthesizedObjects, openProposalIds,
    proposalCount, expandedRequests, setExpandedRequests, retryRequest, decideProposal, jumpToSpan, peekPassage,
    arc, pauseArc, setArcPolicy,
    annotations, jumpToAnnotation, reanchorAnnotation, manualAnchorToSelection, reanchorNotes,
    editingAnnotationId, setEditingAnnotationId, editingAnnotationText, setEditingAnnotationText,
    saveAnnotationEdit, deleteAnnotation, protectionMessage = null,
  } = props;
  return (
    <div style={{ display: visible ? "block" : "none" }}>
      <SectionHeader style={{ marginTop: 0 }}>Capture</SectionHeader>
      {selection ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Faint style={{ fontSize: 11 }}>
                selected · {selection.nodes && selection.nodes.length > 1 ? `${selection.nodes.length} passages` : "1 passage"}
              </Faint>
              <button
                type="button"
                onClick={() => setEditingCapture((v) => !v)}
                style={{ marginLeft: "auto", border: 0, background: "transparent", color: editingCapture ? COLOR.amberLink : COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer" }}
              >
                {editingCapture ? "done" : "edit"}
              </button>
              <button type="button" onClick={clearSelection} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer" }}>clear</button>
            </div>
            {editingCapture ? (
              // OCR-mishap repair: the whole selection edits as ONE
              // combined passage (block fragments joined in reading
              // order); the edited text becomes the practice surface while
              // the anchors stay on the source blocks.
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <textarea
                  value={selection.editedText ?? selectionNodes(selection).map((n) => n.quote).join("\n\n")}
                  onChange={(e) => editCaptureText(e.target.value)}
                  autoFocus
                  style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${selection.editedText != null ? COLOR.amberLink : COLOR.border}`, color: COLOR.text, padding: 6, minHeight: 110, resize: "vertical" }}
                />
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <MeaningLabel>
                    fix any OCR mishaps — the edited passage becomes the practice surface; anchors stay on the source blocks.
                  </MeaningLabel>
                  {selection.editedText != null ? (
                    <button
                      type="button"
                      onClick={resetCaptureText}
                      style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                    >
                      reset
                    </button>
                  ) : null}
                </div>
              </div>
            ) : selection.editedText != null ? (
              <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                “{clip(selection.editedText.replace(/\s+/g, " ").trim(), 360)}”
                <Faint style={{ fontSize: 10, color: COLOR.amberLink }}> (edited)</Faint>
              </span>
            ) : selection.nodes && selection.nodes.length > 1 ? (
              // Per-block anchor preview: exactly what each capture will
              // ground to, so an over-wide sweep is visible before acting.
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {selection.nodes.map((node, index) => (
                  <span key={`${node.spanId}-${index}`} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                    <Faint style={{ fontSize: 10 }}>[{index + 1}]</Faint> “{clip(node.quote, 110)}”
                  </span>
                ))}
              </div>
            ) : (
              <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>“{clip(selection.quote, 360)}”</span>
            )}
            {selectionActions.length > 0 ? (
              <Faint style={{ fontSize: 10, color: COLOR.green }}>✓ saved · choose another action or select another passage</Faint>
            ) : null}
          </Card>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="your note (optional)…"
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 54, resize: "vertical" }}
          />
          <PrimaryButton onClick={() => captureHighlight()} disabled={busy || selectionActions.includes("highlight")}>
            {selectionActions.includes("highlight") ? "highlighted ✓" : "highlight"}
          </PrimaryButton>
          {protectionMessage ? (
            <span data-capture-protected="" style={{ color: COLOR.textFaint, fontSize: 11, lineHeight: 1.6 }}>
              {protectionMessage} You can still highlight it, mark it and keep notes.
            </span>
          ) : null}
          {!offline && !protectionMessage ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>EXERCISES</Faint>
              {onWorkThrough ? (
                <>
                  <PrimaryButton onClick={() => onWorkThrough()} disabled={busy}>work through this ▸</PrimaryButton>
                  <MeaningLabel>
                    opens beside the book now, in steps that save as you type; checks and hints are set up in the background.
                  </MeaningLabel>
                </>
              ) : null}
              <PrimaryButton
                onClick={() => void importExercise()}
                disabled={busy || exerciseImportActive || selectionActions.includes("exercise_import")}
              >
                {selectionActions.includes("exercise_import") ? "exercise queued ✓" : "add exercise to practice"}
              </PrimaryButton>
              <MeaningLabel>
                the exercise text stays verbatim — LearnLoop's model completes the answer, rubric, hints, and depth.
              </MeaningLabel>
            </div>
          ) : null}
          {PALETTE.filter((grp) => !protectionMessage || !MODEL_GROUPS.has(grp.group)).map((grp) => (
            <div key={grp.group} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>{grp.group.toUpperCase()}</Faint>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {grp.presets.map((p) => (
                  <SecondaryButton key={p.preset} onClick={() => invokePreset(p.preset)} disabled={busy || selectionActions.includes(p.preset)}>
                    {p.label}{selectionActions.includes(p.preset) ? " ✓" : ""}
                  </SecondaryButton>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Faint style={{ fontSize: 12 }}>
          {pdfSurfaceActive
            ? "drag to select · double-click a word, triple-click a passage · click a formula or table to take it whole · shift+arrows extend a selection · hold ctrl and drag boxes, release ctrl to take them together (best for exercises) · alt+drag for whole passages · right-click to tag."
            : "select text to capture it · hold ctrl and drag one or more boxes, release ctrl to capture their union."}
        </Faint>
      )}

      {exerciseImport ? (
        <>
          <SectionHeader>Exercise import</SectionHeader>
          <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {exerciseImportActive ? (
              <Faint style={{ fontSize: 11 }}>
                ◐ authoring practice from “{clip(exerciseImport.quote, 90)}” — keep reading, the cards land here.
              </Faint>
            ) : exerciseImport.status === "completed" && exerciseImport.result ? (
              <>
                {exerciseImport.result.items.map((item) => (
                  <div key={item.practiceItemId} style={{ display: "flex", flexDirection: "column", gap: 3, borderBottom: `1px solid ${COLOR.border}`, paddingBottom: 6 }}>
                    <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.green }}>
                      ✓ {item.title || clip(item.prompt, 80)}
                    </span>
                    <Faint style={{ fontSize: 10 }}>→ {item.learningObjectTitle}</Faint>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {item.capability ? (
                        <Pill color="purple">{item.capability.replace(/_/g, " ")}</Pill>
                      ) : (
                        <Pill color="slate">depth unclassified</Pill>
                      )}
                      {typeof item.taskFeatures.span === "string" ? (
                        <Pill color="cyan">{String(item.taskFeatures.span).replace(/_/g, " ")}</Pill>
                      ) : null}
                      {item.difficulty != null ? (
                        <Pill color="amber">difficulty {Math.round(item.difficulty * 100) / 100}</Pill>
                      ) : null}
                    </div>
                    <Faint style={{ fontSize: 10 }}>
                      verbatim from the source · {item.evidenceFacets.length} facet{item.evidenceFacets.length === 1 ? "" : "s"} · {item.hintCount} hint{item.hintCount === 1 ? "" : "s"} · scheduled as practice
                    </Faint>
                    {item.classificationReason ? (
                      <Faint style={{ fontSize: 10 }}>{item.classificationReason}</Faint>
                    ) : null}
                    {onWorkThroughItem ? (
                      <button
                        type="button"
                        onClick={() => onWorkThroughItem(item)}
                        style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                      >
                        work through this ▸
                      </button>
                    ) : null}
                  </div>
                ))}
                {exerciseImport.result.skipped.map((skip, index) => (
                  <Faint key={index} style={{ fontSize: 10 }}>
                    skipped{skip.title ? ` ${skip.title}` : ""}: {skip.reason}
                  </Faint>
                ))}
                {exerciseImport.result.warnings.slice(0, 4).map((warning, index) => (
                  <Faint key={index} style={{ fontSize: 10, color: COLOR.amberLink }}>⚠ {warning}</Faint>
                ))}
              </>
            ) : (
              <Faint style={{ fontSize: 11, color: COLOR.red }}>
                ✗ {exerciseImport.error || "the exercise import did not complete."}
              </Faint>
            )}
            {!exerciseImportActive ? (
              <button
                type="button"
                onClick={() => setExerciseImport(null)}
                style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
              >
                dismiss
              </button>
            ) : null}
          </Card>
        </>
      ) : null}

      {(selection || activeSpan || authoringOpen) ? (
        <>
          <SectionHeader>Make your own practice</SectionHeader>
          {!authoringOpen ? (
            <SecondaryButton onClick={() => {
              const spanId = selection?.spanId ?? activeSpan;
              setAuthoringSpanId(spanId);
              setAuthoringQuote(selection?.quote ?? activeBlock?.markdown.replace(/\s+/g, " ") ?? "");
              setAuthoringOpen(true);
              setAuthoredCardId(null);
              setCoach(null);
            }}>
              write my own question
            </SecondaryButton>
          ) : (
            <Card style={{ display: "flex", flexDirection: "column", gap: 8, background: COLOR.bgElev }}>
              {authoringQuote ? (
                <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint }}>From “{clip(authoringQuote, 120)}”</span>
              ) : null}
              <textarea
                value={authoredQuestion}
                disabled={authoredCardId !== null}
                onChange={(event) => setAuthoredQuestion(event.target.value)}
                placeholder="Write a question future-you should answer…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 64, resize: "vertical" }}
              />
              <textarea
                value={authoredAnswer}
                disabled={authoredCardId !== null}
                onChange={(event) => setAuthoredAnswer(event.target.value)}
                placeholder="Write the answer in your own words…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 72, resize: "vertical" }}
              />
              {authoredQuestion.trim() || authoredAnswer.trim() ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 4, borderTop: `1px solid ${COLOR.border}`, paddingTop: 6 }}>
                  <Faint style={{ fontSize: 10 }}>PREVIEW</Faint>
                  {authoredQuestion.trim() ? (
                    <div className="markdown" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                      <MarkdownMath value={authoredQuestion} />
                    </div>
                  ) : null}
                  {authoredAnswer.trim() ? (
                    <div className="markdown" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}>
                      <MarkdownMath value={authoredAnswer} />
                    </div>
                  ) : null}
                </div>
              ) : null}
              {authoredCardId ? (
                <>
                  <Faint style={{ fontSize: 11, color: authoredQuestionMessage(authoredStatus).scheduled ? COLOR.green : COLOR.textDim }}>
                    {authoredQuestionMessage(authoredStatus).text}
                  </Faint>
                  {!offline ? <SecondaryButton onClick={() => void runCoach()}>check the wording</SecondaryButton> : null}
                  {coach ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {coach.suggestions.length === 0 ? (
                        <Faint style={{ fontSize: 11 }}>The wording looks clear as written.</Faint>
                      ) : coach.suggestions.map((suggestion, index) => (
                        <Faint key={index} style={{ fontSize: 11 }}>• {suggestion.prompt}</Faint>
                      ))}
                      {coach.suggestions.length > 0 ? (
                        <Faint style={{ fontSize: 10 }}>Your saved wording stays unchanged. Use “write another” below to make a revised card.</Faint>
                      ) : null}
                    </div>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => {
                      setAuthoredQuestion("");
                      setAuthoredAnswer("");
                      setAuthoredCardId(null);
                      setCoach(null);
                    }}
                    style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                  >
                    write another
                  </button>
                </>
              ) : (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <PrimaryButton onClick={() => void saveOwnQuestion()} disabled={authoringBusy || !authoredQuestion.trim() || !authoredAnswer.trim()}>
                    save for practice
                  </PrimaryButton>
                  <SecondaryButton onClick={() => setAuthoringOpen(false)} disabled={authoringBusy}>cancel</SecondaryButton>
                </div>
              )}
            </Card>
          )}
        </>
      ) : null}

      {requestLoadError ? (
        <Card status="error" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          <div role="alert" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.red }}>
            Some Reader request data is unavailable.
          </div>
          <Faint style={{ fontSize: 10 }}>{requestLoadError}</Faint>
          <button
            type="button"
            onClick={() => void refreshRequests()}
            style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
          >
            retry request data
          </button>
        </Card>
      ) : null}

      {requests.length > 0 ? (
        <>
          <SectionHeader>Your requests</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {requests.map((request) => {
              const { sourceObjectId, proposalId } = parseRequestResult(request.resultJson);
              const requestError = parseRequestError(request.errorJson);
              const result = sourceObjectId ? synthesizedObjects.get(sourceObjectId) : undefined;
              const expanded = expandedRequests.has(request.id);
              const proposalOpen = proposalId !== null && openProposalIds.has(proposalId);
              return (
                <Card
                  key={request.id}
                  status={request.status === "complete" ? "done" : request.status === "failed" ? "error" : "running"}
                  style={{ display: "flex", flexDirection: "column", gap: 6 }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                    <Pill color={request.status === "complete" ? "green" : request.status === "failed" ? "pink" : request.status === "partial" ? "amber" : "slate"}>
                      {request.status === "complete" ? "ready" : request.status === "failed" ? "needs retry" : "working"}
                    </Pill>
                    <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                      {request.preset.replace(/_/g, " ")}
                    </span>
                    {request.status === "complete" && result ? (
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedRequests((ids) => {
                            const next = new Set(ids);
                            if (next.has(request.id)) next.delete(request.id);
                            else next.add(request.id);
                            return next;
                          })
                        }
                        style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                      >
                        {expanded ? "▾ hide" : "▸ view result"}
                      </button>
                    ) : request.status === "failed" ? (
                      <button
                        type="button"
                        onClick={() => void retryRequest(request.id)}
                        style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                      >
                        retry
                      </button>
                    ) : null}
                  </div>
                  {request.status === "failed" && requestError ? (
                    <Faint style={{ fontSize: 10, color: COLOR.red }}>{requestError}</Faint>
                  ) : null}
                  {expanded && result ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {result.contentMd ? (
                        <ModelVoice first>
                          <MarkdownMath value={result.contentMd} />
                        </ModelVoice>
                      ) : (
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>“{clip(result.exactText, 260)}”</span>
                      )}
                      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                        {result.spanId ? (
                          <button
                            type="button"
                            onClick={() => (peekPassage ?? jumpToSpan)(result.spanId!)}
                            style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                          >
                            show the passage
                          </button>
                        ) : null}
                        {proposalOpen && proposalId ? (
                          <>
                            <button
                              type="button"
                              onClick={() => void decideProposal(proposalId, "accept")}
                              disabled={busy}
                              style={{ border: 0, background: "transparent", color: COLOR.green, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                            >
                              keep it
                            </button>
                            <button
                              type="button"
                              onClick={() => void decideProposal(proposalId, "reject")}
                              disabled={busy}
                              style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                            >
                              dismiss
                            </button>
                          </>
                        ) : proposalId ? (
                          <Faint style={{ fontSize: 10, color: COLOR.green }}>✓ reviewed</Faint>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </Card>
              );
            })}
            {proposalCount > 0 ? <Faint style={{ fontSize: 10 }}>{proposalCount} idea{proposalCount === 1 ? " is" : "s are"} awaiting your review above.</Faint> : null}
          </div>
        </>
      ) : null}

      {arc ? (
        <>
          <SectionHeader>You’ll see this again</SectionHeader>
          <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
              {arc.paused
                ? "Paused. This passage will stay saved until you resume."
                : "Saved. LearnLoop will bring this idea back as short practice and adjust only from your answers."}
            </span>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <SecondaryButton onClick={pauseArc} disabled={arc.paused}>pause reminders</SecondaryButton>
              <SecondaryButton onClick={() => setArcPolicy("hold_at_target")}>keep it at this level</SecondaryButton>
              <SecondaryButton onClick={() => setArcPolicy("suggest_next")}>deepen when I’m ready</SecondaryButton>
            </div>
          </Card>
        </>
      ) : null}

      <SectionHeader>Annotations</SectionHeader>
      {annotations.length === 0 ? (
        <Faint style={{ fontSize: 12 }}>no annotations yet.</Faint>
      ) : (
        annotations.map((a, i) => (
          <Card
            key={a.annotationId ?? i}
            onClick={() => jumpToAnnotation(a)}
            style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 6, cursor: a.segments.length ? "pointer" : "default" }}
          >
            <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
              <Pill color="cyan">{a.kind}</Pill>
              {a.status === "needs_reanchor" ? <Pill color="amber">anchor needs review</Pill> : <Faint style={{ fontSize: 10 }}>{a.status}</Faint>}
              {a.placement?.state === "moved" ? (
                <span data-placement="moved" style={{ fontSize: 10, color: COLOR.amberLink }}>moved here when the book was read again</span>
              ) : a.placement?.state === "flagged" ? (
                <Pill color="amber">its words changed when the book was read again</Pill>
              ) : null}
            </div>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>“{clip(a.quote, 180)}”</span>
            {a.status === "needs_reanchor" && a.annotationId && !offline ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }} onClick={(e) => e.stopPropagation()}>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => void reanchorAnnotation(a.annotationId!)}
                    disabled={busy}
                    style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                  >
                    re-anchor to this version
                  </button>
                  {selection ? (
                    <button
                      type="button"
                      onClick={() => void manualAnchorToSelection(a.annotationId!)}
                      disabled={busy}
                      style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                    >
                      anchor to selection
                    </button>
                  ) : null}
                </div>
                {reanchorNotes[a.annotationId] ? (
                  <Faint style={{ fontSize: 10 }}>{reanchorNotes[a.annotationId]}</Faint>
                ) : null}
              </div>
            ) : null}
            {editingAnnotationId !== null && editingAnnotationId === a.annotationId ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }} onClick={(e) => e.stopPropagation()}>
                <textarea
                  autoFocus
                  value={editingAnnotationText}
                  onChange={(e) => setEditingAnnotationText(e.target.value)}
                  placeholder="your note…"
                  onKeyDown={(e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") void saveAnnotationEdit();
                    if (e.key === "Escape") setEditingAnnotationId(null);
                  }}
                  style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 54, resize: "vertical" }}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <PrimaryButton onClick={() => void saveAnnotationEdit()} disabled={busy}>save ↵</PrimaryButton>
                  <SecondaryButton onClick={() => setEditingAnnotationId(null)} disabled={busy}>cancel</SecondaryButton>
                </div>
              </div>
            ) : (
              <>
                {a.learnerText ? <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{a.learnerText}</span> : null}
                {a.annotationId && !offline ? (
                  <div style={{ display: "flex", gap: 10 }} onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingAnnotationId(a.annotationId);
                        setEditingAnnotationText(a.learnerText);
                      }}
                      disabled={busy}
                      style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                    >
                      {a.learnerText ? "edit note" : "add note"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void deleteAnnotation(a.annotationId!)}
                      disabled={busy}
                      style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                    >
                      delete
                    </button>
                  </div>
                ) : null}
              </>
            )}
          </Card>
        ))
      )}
    </div>
  );
}
