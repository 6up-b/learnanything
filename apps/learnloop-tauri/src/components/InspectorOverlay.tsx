// Global inspector — the GUI mirror of `learnloop show <id>`.
//
// Reworked to follow the handoff design (learnloop-handoff2/.../inspector.jsx):
// a centered `learnloop show` modal over a blurred backdrop, a kind-pill
// header with back-history, per-kind bodies (InspectorRows, FSRS stat grid,
// the component-by-component scheduler `why`, mastery posterior), and a footer
// key bar. Unlike the fixture handoff this is wired to the live `inspect_entity`
// command, so it also keeps the real-data sections the prototype omitted
// (prompt, hints, rubric, evidence, source refs).

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import { masteryTone } from "../app/algoConfig";
import type {
  AttemptInspectorDetail,
  InspectorEntity,
  InspectorSearchResult,
  LearningObjectDetail,
  MasteryDto,
  NoteInspectorDetail,
  ProbeEpisodeInspectorDetail,
  PracticeItemDetail,
  ErrorEventDto,
  CapabilityGridResult,
  ConceptInspectorDetail,
  ConceptReferenceDto,
  SchedulerComponents,
  SchedulerExplanationDto
} from "../api/dto";
import { BlockBar, COLOR, Dim, DisclosureHeader, Divider, Faint, FONT_MONO, HelpTooltip, Meta, modePillColor, Pill, SectionHeader, type PillColor } from "./term";
import { CapabilityGridView } from "./KnowledgeModel";
import { RungVariantActions } from "./CardControls";
import { ConceptAnimationSection } from "./ConceptAnimationSection";
import { RecipeTreeEditor } from "./recipeedit/RecipeTreeEditor";
import { MarkdownMath } from "../render/MarkdownMath";
import { CommandOverlayFrame, commandOverlayActionStyle, learnloopShowOverlayWidth } from "./CommandOverlayFrame";

// ── kind → header pill ──────────────────────────────────────────────────
const KIND_PILL: Record<string, { color: PillColor; label: string }> = {
  practice_item: { color: "cyan", label: "practice_item" },
  learning_object: { color: "purple", label: "learning_object" },
  concept: { color: "cyan", label: "concept" },
  attempt: { color: "amber", label: "attempt" },
  error_event: { color: "red", label: "error_event" },
  note: { color: "cyan", label: "note" },
  probe_episode: { color: "red", label: "probe_episode" }
};

function masteryColor(mastery: number): string {
  return masteryTone(mastery, COLOR);
}

export function InspectorOverlay({
  entityId,
  onClose,
  onInspect,
  onError
}: {
  entityId: string | null;
  onClose: () => void;
  onInspect: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [query, setQuery] = useState(entityId ?? "");
  const [entity, setEntity] = useState<InspectorEntity | null>(null);
  const [childPracticeItemId, setChildPracticeItemId] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const loadedIdRef = useRef<string | null>(null);
  const backNavRef = useRef(false);

  // Navigate forward: route through the parent so `entityId` stays the source
  // of truth; the effect below does the fetch and history bookkeeping.
  function go(id: string) {
    const trimmed = id.trim();
    if (trimmed) onInspect(trimmed);
  }

  function back() {
    setHistory((h) => {
      if (!h.length) return h;
      backNavRef.current = true;
      onInspect(h[h.length - 1]);
      return h.slice(0, -1);
    });
  }

  useEffect(() => {
    setQuery(entityId ?? "");
    if (!entityId) {
      setEntity(null);
      setHistory([]);
      loadedIdRef.current = null;
      return;
    }
    const prev = loadedIdRef.current;
    if (backNavRef.current) {
      backNavRef.current = false;
    } else if (prev && prev !== entityId) {
      setHistory((h) => [...h, prev]);
    }
    void fetchEntity(entityId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId]);

  useEffect(() => {
    if (!entityId) return;
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      const isInput = tag === "input" || tag === "textarea";
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key === "Backspace" && !isInput && history.length > 0) {
        event.preventDefault();
        back();
        return;
      }
      if (isInput) return;
      if (event.key === "ArrowRight" && entity?.kind === "practice_item") {
        event.preventDefault();
        event.stopPropagation();
        go(entity.detail.learningObjectId);
      } else if (event.key === "ArrowLeft" && entity?.kind === "learning_object" && childPracticeItemId) {
        event.preventDefault();
        event.stopPropagation();
        go(childPracticeItemId);
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childPracticeItemId, entity, entityId, history.length]);

  async function fetchEntity(id: string) {
    try {
      const previous = entity;
      const result = await api.inspectEntity(id);
      if (result.kind === "practice_item") {
        setChildPracticeItemId(result.id);
      } else if (result.kind === "learning_object" && previous?.kind === "practice_item") {
        setChildPracticeItemId(previous.id);
      }
      setEntity(result);
      loadedIdRef.current = id;
    } catch (error) {
      onError((error as Error).message);
    }
  }

  if (!entityId) return null;

  const pill = entity && entity.kind in KIND_PILL ? KIND_PILL[entity.kind] : null;

  return (
    <CommandOverlayFrame
      command="show"
      context={entityId}
      badge={pill ? <Pill color={pill.color}>{pill.label}</Pill> : null}
      headerActions={history.length > 0 ? (
        <button type="button" onClick={back} style={commandOverlayActionStyle}>
          ← back · {history.length}
        </button>
      ) : null}
      footerKeys={(
        <>
          <span><span style={{ color: COLOR.text }}>esc</span> close</span>
          <span><span style={{ color: COLOR.text }}>backspace</span> back</span>
          {entity?.kind === "practice_item" ? <span><span style={{ color: COLOR.text }}>→</span> parent</span> : null}
          {entity?.kind === "learning_object" && childPracticeItemId ? (
            <span><span style={{ color: COLOR.text }}>←</span> child</span>
          ) : null}
        </>
      )}
      footerRight={(
        <span>
          CLI mirror · <Dim>learnloop show {entityId}</Dim>
        </span>
      )}
      onClose={onClose}
      ariaLabel={`Inspect ${entityId}`}
      width={learnloopShowOverlayWidth}
    >
        {/* ── search ── */}
        <div style={{ padding: "10px 16px", borderBottom: `1px solid ${COLOR.border}`, flexShrink: 0 }}>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="search by id — pi_… lo_… att_… ee_…"
            onKeyDown={(event) => {
              if (event.key === "Enter") go(query);
            }}
            style={searchInputStyle}
          />
        </div>

        {/* ── body ── */}
        <div style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
          {!entity ? (
            <div style={{ padding: 24, fontSize: 13 }}>
              <Faint>loading </Faint>
              <span style={{ color: COLOR.text, fontFamily: FONT_MONO }}>{entityId}</span>
              <Faint> …</Faint>
            </div>
          ) : (
            <InspectorEntityView
              entity={entity}
              childPracticeItemId={childPracticeItemId}
              onGo={go}
              onError={onError}
              onRefresh={() => {
                if (entityId) void fetchEntity(entityId);
              }}
            />
          )}
        </div>

    </CommandOverlayFrame>
  );
}

// ── entity dispatch ───────────────────────────────────────────────────────
function InspectorEntityView({
  entity,
  childPracticeItemId,
  onGo,
  onError,
  onRefresh
}: {
  entity: InspectorEntity;
  childPracticeItemId: string | null;
  onGo: (id: string) => void;
  onError: (message: string) => void;
  /** Re-fetch the currently shown entity (after a mutation like re-runging). */
  onRefresh: () => void;
}) {
  if (entity.kind === "not_found") {
    return <NotFoundBody id={entity.id} suggestions={entity.suggestions} onGo={onGo} />;
  }

  const title =
    entity.kind === "practice_item"
      ? entity.detail.learningObjectTitle
      : entity.kind === "learning_object"
        ? entity.detail.title
        : entity.kind === "concept"
          ? entity.detail.title
        : entity.kind === "error_event"
          ? entity.detail.errorTitle ?? entity.detail.errorType
          : entity.kind === "note"
            ? entity.detail.title
            : entity.kind === "probe_episode"
              ? `Diagnostic episode · ${entity.detail.learningObjectId}`
              : entity.id;

  return (
    <>
      <div style={{ padding: "14px 22px 8px", flexShrink: 0 }}>
        <div style={{ fontSize: 17, color: COLOR.text, fontWeight: 600, lineHeight: 1.35 }}>{title}</div>
        <div style={{ marginTop: 4 }}>
          <Meta>{entity.id}</Meta>
        </div>
      </div>
      <Divider />
      <div style={{ padding: "12px 22px 24px" }}>
        {entity.kind === "practice_item" ? (
          <PracticeItemBody detail={entity.detail} onGo={onGo} onError={onError} onRefresh={onRefresh} />
        ) : entity.kind === "learning_object" ? (
          <LearningObjectBody detail={entity.detail} childPracticeItemId={childPracticeItemId} onGo={onGo} />
        ) : entity.kind === "concept" ? (
          <ConceptBody detail={entity.detail} onGo={onGo} />
        ) : entity.kind === "error_event" ? (
          <ErrorEventBody detail={entity.detail} onGo={onGo} />
        ) : entity.kind === "note" ? (
          <NoteBody detail={entity.detail} onGo={onGo} />
        ) : entity.kind === "probe_episode" ? (
          <ProbeEpisodeBody detail={entity.detail} onGo={onGo} />
        ) : (
          <AttemptBody id={entity.id} detail={entity.detail} onGo={onGo} />
        )}
      </div>
    </>
  );
}

function ProbeEpisodeBody({ detail, onGo }: { detail: ProbeEpisodeInspectorDetail; onGo: (id: string) => void }) {
  return (
    <div>
      <InspectorRow label="learning_object"><IdLink id={detail.learningObjectId} onGo={onGo} /></InspectorRow>
      <InspectorRow label="status"><Pill color={detail.status === "complete" ? "green" : "red"}>{detail.status}</Pill></InspectorRow>
      <InspectorRow label="trigger"><Dim>{detail.trigger}</Dim></InspectorRow>
      <InspectorRow label="required_facets"><Dim>{detail.requiredFacets.join(" · ") || "none"}</Dim></InspectorRow>
      <InspectorRow label="observations"><Dim style={{ fontFamily: FONT_MONO }}>{detail.observations.filter((row) => row.eligibleForCompletion).length}/{detail.minimumIndependentObservations} qualifying · max {detail.maximumObservations}</Dim></InspectorRow>
      {detail.completionReason ? <InspectorRow label="completion_reason"><Dim>{detail.completionReason}</Dim></InspectorRow> : null}
      <SectionHeader>Posterior transitions</SectionHeader>
      {detail.observations.length ? detail.observations.map((row) => (
        <div key={row.attemptId} style={{ padding: "8px 0", borderBottom: `1px solid ${COLOR.border}`, fontSize: 12 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <IdLink id={row.attemptId} onGo={onGo} />
            <Pill color={row.eligibleForCompletion ? "green" : "slate"}>{row.eligibleForCompletion ? "qualifying" : "incidental"}</Pill>
            <span style={{ marginLeft: "auto", color: row.realizedInformationGain >= 0 ? COLOR.green : COLOR.red, fontFamily: FONT_MONO }}>
              ΔH {row.realizedInformationGain >= 0 ? "+" : ""}{row.realizedInformationGain.toFixed(3)}
            </span>
          </div>
          <div style={{ marginTop: 4 }}><Faint>entropy {row.entropyBefore.toFixed(3)} → {row.entropyAfter.toFixed(3)} · {relTime(row.createdAt)}</Faint></div>
          {row.contamination ? <div style={{ marginTop: 3, color: COLOR.amber }}>contaminated · {formatUnknown(row.contamination)}</div> : null}
        </div>
      )) : <Faint>no submitted observations yet</Faint>}
    </div>
  );
}

// ── practice_item ──────────────────────────────────────────────────────────
function PracticeItemBody({
  detail,
  onGo,
  onError,
  onRefresh
}: {
  detail: PracticeItemDetail;
  onGo: (id: string) => void;
  onError: (message: string) => void;
  onRefresh: () => void;
}) {
  const state = detail.state;
  const mastery = detail.mastery;
  return (
    <div>
      <InspectorRow label="learning_object">
        <IdLink id={detail.learningObjectId} onGo={onGo}>
          {detail.learningObjectTitle}
        </IdLink>
      </InspectorRow>
      <InspectorRow label="practice_mode">
        <Pill color={modePillColor(detail.practiceMode)}>{detail.practiceMode}</Pill>
        <span style={{ display: "inline-flex", gap: 12, marginLeft: 14 }}>
          <RungVariantActions practiceItemId={detail.id} onError={onError} onApplied={onRefresh} />
        </span>
      </InspectorRow>
      <InspectorRow label="subjects">{detail.subjects.length ? detail.subjects.join(" · ") : <Faint>none</Faint>}</InspectorRow>
      {detail.difficulty != null ? (
        <InspectorRow label="difficulty">
          <BlockBar value={detail.difficulty} width={10} />
          {"  "}
          <Dim style={{ fontFamily: FONT_MONO }}>{detail.difficulty.toFixed(2)}</Dim>
        </InspectorRow>
      ) : null}

      <SectionHeader>FSRS · practice_item_state</SectionHeader>
      {state ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          <Stat label="stability" value={state.stability != null ? `${state.stability.toFixed(1)}d` : "—"} />
          <Stat
            label="retrievability"
            value={state.retrievability != null ? state.retrievability.toFixed(2) : "—"}
            color={state.retrievability != null && state.retrievability < 0.5 ? COLOR.amber : COLOR.green}
          />
          <Stat label="last_attempt" value={relTime(state.lastAttemptAt)} />
          <Stat label="due_at" value={relTime(state.dueAt)} color={COLOR.amber} />
        </div>
      ) : (
        <Faint>no FSRS state yet — first-touch item</Faint>
      )}

      <SectionHeader>Why this is in the queue · scheduler_explanations</SectionHeader>
      {detail.scheduler ? <SchedulerWhy scheduler={detail.scheduler} /> : <Faint>no scheduler explanation available</Faint>}

      <SectionHeader>Mastery · learning_object_mastery</SectionHeader>
      {mastery ? (
        <MasteryPosteriorBar mastery={mastery} />
      ) : (
        <Faint>no evidence yet</Faint>
      )}

      <SectionHeader>Attempt history</SectionHeader>
      {detail.attempts.length ? (
        <div style={{ border: `1px solid ${COLOR.border}` }}>
          {detail.attempts.map((attempt, index) => (
            <div key={attempt.id} style={attemptRowStyle(index)}>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                <IdLink id={attempt.id} onGo={onGo} />
              </span>
              <span style={{ fontFamily: FONT_MONO, color: COLOR.amber, textAlign: "right" }}>
                {attempt.rubricScore == null ? "—" : `${attempt.rubricScore}/${attempt.maxPoints}`}
              </span>
              <Pill color={attemptTypePillColor(attempt.attemptType)}>{attempt.attemptType}</Pill>
              <span style={{ color: COLOR.textDim, fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {relTime(attempt.createdAt)}
                {attempt.errorType ? ` · ${attempt.errorType}` : ""}
                {attempt.hintsUsed ? ` · ${attempt.hintsUsed} hint${attempt.hintsUsed > 1 ? "s" : ""}` : ""}
              </span>
              {attempt.surpriseDirection && attempt.surpriseDirection !== "none" ? (
                <Pill color={attempt.surpriseDirection === "negative" ? "red" : "green"}>{attempt.surpriseDirection}</Pill>
              ) : (
                <span />
              )}
            </div>
          ))}
        </div>
      ) : (
        <Faint>no attempts yet — first-touch item</Faint>
      )}

      <SectionHeader>Prompt</SectionHeader>
      <div style={panelStyle}>
        <div className="markdown">
          <MarkdownMath value={detail.prompt} />
        </div>
      </div>

      <SectionHeader>Hints</SectionHeader>
      {detail.hints.length ? (
        <div style={{ display: "grid", border: `1px solid ${COLOR.border}` }}>
          {detail.hints.map((hint, index) => (
            <div
              key={index}
              style={{
                display: "grid",
                gridTemplateColumns: "58px minmax(0, 1fr)",
                gap: 10,
                padding: "8px 10px",
                fontSize: 12,
                color: COLOR.textDim,
                background: COLOR.bgInput,
                borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
                lineHeight: 1.5
              }}
            >
              <span style={{ color: COLOR.amber, fontFamily: FONT_MONO }}>hint {String(index + 1).padStart(2, "0")}</span>
              <span>{hint}</span>
            </div>
          ))}
        </div>
      ) : (
        <Faint>no hints configured</Faint>
      )}
      <div style={{ marginTop: 8, fontSize: 11 }}>
        <Faint>max useful hints</Faint> <Dim style={{ fontFamily: FONT_MONO }}>{detail.hintPolicy.maxUsefulHints}</Dim>
      </div>

      <SectionHeader>Answer · rubric</SectionHeader>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 6 }}>expected answer</div>
      <div style={{ ...panelStyle, whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontFamily: FONT_MONO, fontSize: 12 }}>
        {formatUnknown(detail.expectedAnswer)}
      </div>
      {detail.rubric ? (
        <div style={{ marginTop: 12, border: `1px solid ${COLOR.border}` }}>
          <div style={{ padding: "8px 12px", borderBottom: `1px solid ${COLOR.border}`, fontSize: 11, color: COLOR.textFaint }}>
            rubric · max {detail.rubric.maxPoints}
          </div>
          {detail.rubric.criteria.map((criterion, index) => (
            <div key={criterion.id} style={rubricRowStyle(index)}>
              <span style={{ color: COLOR.amber, fontFamily: FONT_MONO }}>+{criterion.points}</span>
              <span>
                <span style={{ color: COLOR.text }}>{criterion.id}</span>
                <span style={{ color: COLOR.textDim }}> — {criterion.description}</span>
              </span>
            </div>
          ))}
          {detail.rubric.fatalErrors.map((fatal) => (
            <div key={fatal.id} style={rubricRowStyle(1)}>
              <span style={{ color: COLOR.red, fontFamily: FONT_MONO }}>cap {fatal.maxGrade}</span>
              <span>
                <span style={{ color: COLOR.red }}>{fatal.id}</span>
                <span style={{ color: COLOR.textDim }}> — {fatal.description}</span>
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ marginTop: 8 }}>
          <Faint>no rubric configured</Faint>
        </div>
      )}

      <SectionHeader>Evidence</SectionHeader>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 6 }}>facets</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
        {detail.evidenceFacets.length ? (
          detail.evidenceFacets.map((facet) => (
            <Pill key={facet} color="slate">
              {facet}
            </Pill>
          ))
        ) : (
          <Faint>none</Faint>
        )}
      </div>
      {Object.entries(detail.evidenceWeights).map(([key, value]) => (
        <InspectorRow key={key} label={key}>
          <Dim style={{ fontFamily: FONT_MONO }}>{formatUnknown(value)}</Dim>
        </InspectorRow>
      ))}
      {detail.sourceRefs.length ? (
        <>
          <div style={{ fontSize: 11, color: COLOR.textFaint, margin: "12px 0 6px" }}>source refs</div>
          {detail.sourceRefs.map((ref, index) => (
            <InspectorRow key={`${ref.refId}:${index}`} label={ref.refId}>
              <Dim>{ref.locator ?? ref.path ?? ref.refType}</Dim>
            </InspectorRow>
          ))}
        </>
      ) : null}
    </div>
  );
}

// ── learning_object ──────────────────────────────────────────────────────
function LearningObjectBody({
  detail,
  childPracticeItemId,
  onGo
}: {
  detail: LearningObjectDetail;
  childPracticeItemId: string | null;
  onGo: (id: string) => void;
}) {
  return (
    <div>
      <InspectorRow label="concept">
        <IdLink id={detail.concept} onGo={onGo} />
      </InspectorRow>
      <InspectorRow label="knowledge_type">
        <Pill color="purple">{detail.knowledgeType}</Pill>
      </InspectorRow>
      <InspectorRow label="status">
        <Pill color={detail.status === "active" ? "green" : "slate"}>{detail.status}</Pill>
      </InspectorRow>
      {detail.difficultyPrior != null ? (
        <InspectorRow label="difficulty_prior">
          <BlockBar value={detail.difficultyPrior} width={10} />
          {"  "}
          <Dim style={{ fontFamily: FONT_MONO }}>{detail.difficultyPrior.toFixed(2)}</Dim>
        </InspectorRow>
      ) : null}
      {childPracticeItemId ? (
        <InspectorRow label="child_practice_item">
          <IdLink id={childPracticeItemId} onGo={onGo} /> <Faint>· ← to return</Faint>
        </InspectorRow>
      ) : null}

      {detail.summary ? (
        <>
          <SectionHeader>Summary</SectionHeader>
          <div style={panelStyle}>{detail.summary}</div>
        </>
      ) : null}

      <SectionHeader>Mastery · learning_object_mastery</SectionHeader>
      {detail.mastery ? (
        <MasteryPosteriorBar mastery={detail.mastery} showLastEvidence />
      ) : (
        <Faint>no evidence yet</Faint>
      )}

      <LearningObjectRelations
        subjects={detail.subjects}
        prerequisites={detail.prerequisiteConcepts ?? fallbackConceptRefs(detail.prerequisites)}
        confusables={detail.confusableConcepts ?? fallbackConceptRefs(detail.confusables)}
        tags={detail.tags}
        onGo={onGo}
      />

      <LoCapabilitySection loId={detail.id} />

      <RecipeTreeEditor loId={detail.id} blueprints={detail.blueprints} onGo={onGo} />
    </div>
  );
}

// ── concept ──────────────────────────────────────────────────────────────
function ConceptBody({ detail, onGo }: { detail: ConceptInspectorDetail; onGo: (id: string) => void }) {
  return (
    <div>
      <InspectorRow label="concept_type">
        <Pill color={detail.type === "misconception" ? "red" : detail.type === "procedure" ? "amber" : "cyan"}>
          {detail.type}
        </Pill>
      </InspectorRow>
      <InspectorRow label="aliases">
        {detail.aliases.length ? detail.aliases.join(" · ") : <Faint>none</Faint>}
      </InspectorRow>
      <InspectorRow label="tags">
        {detail.tags.length ? (
          <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
            {detail.tags.map((tag) => <Pill key={tag} color="slate">#{tag}</Pill>)}
          </span>
        ) : <Faint>none</Faint>}
      </InspectorRow>

      <SectionHeader>Description</SectionHeader>
      {detail.description ? <div style={panelStyle}>{detail.description}</div> : <Faint>no description configured</Faint>}

      <SectionHeader>Learning objects</SectionHeader>
      {detail.learningObjects.length ? (
        <div style={{ border: `1px solid ${COLOR.border}` }}>
          {detail.learningObjects.map((learningObject, index) => (
            <div
              key={learningObject.id}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1fr) auto auto",
                gap: 10,
                alignItems: "center",
                padding: "8px 12px",
                borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
                fontSize: 12
              }}
            >
              <IdLink id={learningObject.id} onGo={onGo}>{learningObject.title}</IdLink>
              <Pill color="slate">{learningObject.knowledgeType}</Pill>
              <Pill color={learningObject.status === "active" ? "green" : "slate"}>{learningObject.status}</Pill>
            </div>
          ))}
        </div>
      ) : <Faint>no learning objects currently teach or assess this concept</Faint>}

      <SectionHeader>Concept relations</SectionHeader>
      <div style={{ color: COLOR.textDim, fontSize: 11, lineHeight: 1.5, marginBottom: 8 }}>
        Prerequisite links express learning order. Confusable links identify plausible substitutions that should be distinguished through contrastive practice; they are not prerequisites.
      </div>
      {detail.relations.length ? (
        <div style={{ border: `1px solid ${COLOR.border}` }}>
          {detail.relations.map((relation, index) => {
            const presentation = conceptRelationPresentation(relation);
            return (
              <div
                key={relation.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "126px minmax(0, 1fr) 54px",
                  gap: 10,
                  alignItems: "baseline",
                  padding: "8px 12px",
                  borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
                  fontSize: 12
                }}
              >
                <span style={{ color: presentation.color, fontFamily: FONT_MONO }}>{presentation.label}</span>
                <span style={{ minWidth: 0 }}>
                  {relation.concept.conceptId ? (
                    <IdLink id={relation.concept.conceptId} onGo={onGo}>{relation.concept.title}</IdLink>
                  ) : (
                    <Dim>{relation.concept.title}</Dim>
                  )}
                  <span style={{ display: "block", marginTop: 3, color: COLOR.textFaint, fontSize: 11, lineHeight: 1.45 }}>
                    {relation.rationale ?? presentation.description}
                  </span>
                </span>
                <Dim style={{ fontFamily: FONT_MONO, textAlign: "right" }}>{relation.strength.toFixed(2)}</Dim>
              </div>
            );
          })}
        </div>
      ) : <Faint>no concept-graph relations configured</Faint>}

      <SectionHeader>Explainer animation</SectionHeader>
      <ConceptAnimationSection conceptId={detail.id} />
    </div>
  );
}

function conceptRelationPresentation(
  relation: ConceptInspectorDetail["relations"][number]
): { label: string; description: string; color: string } {
  if (relation.relationType === "confusable_with") {
    return { label: "confusable_with", description: "A nearby concept that a learner might plausibly substitute for this one.", color: COLOR.pink };
  }
  if (relation.relationType === "prerequisite") {
    return relation.direction === "incoming"
      ? { label: "prerequisite", description: "Expected before learning this concept.", color: COLOR.amber }
      : { label: "prerequisite_for", description: "This concept supports the neighboring concept.", color: COLOR.green };
  }
  if (relation.relationType === "part_of") {
    return relation.direction === "outgoing"
      ? { label: "part_of", description: "This concept is a component of the neighboring concept.", color: COLOR.cyan }
      : { label: "contains", description: "The neighboring concept is a component of this concept.", color: COLOR.cyan };
  }
  return { label: "related", description: "A related concept in the authored concept graph.", color: COLOR.textDim };
}

// KM3b §9.6: the capability grid (Demonstrated vs Ready per facet×capability)
// and blueprint recipe tree — the diagnostic drill-down that supersedes the
// per-LO facet radar. Fetched on demand (one tap from the Demonstrated surface).
function LoCapabilitySection({ loId }: { loId: string }) {
  const [open, setOpen] = useState(false);
  const [grid, setGrid] = useState<CapabilityGridResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || grid) return;
    let alive = true;
    api
      .getCapabilityGrid(loId)
      .then((result) => { if (alive) setGrid(result); })
      .catch((e) => { if (alive) setError(e?.message ?? "failed to load capability grid"); });
    return () => { alive = false; };
  }, [open, loId, grid]);

  return (
    <div>
      <DisclosureHeader
        open={open}
        onToggle={() => setOpen((v) => !v)}
        tooltip="Shows the facet–capability requirements for this learning object, the direct evidence and predicted recall for each requirement, the acceptable recipe paths, and the current bottleneck. This view is read-only."
      >
        Capability grid &amp; recipe tree
      </DisclosureHeader>
      {open && (
        <div>
          {error && <Faint>{error}</Faint>}
          {grid && <CapabilityGridView result={grid} />}
          {!grid && !error && <Faint>loading…</Faint>}
        </div>
      )}
    </div>
  );
}

// ── error_event ────────────────────────────────────────────────────────────
function ErrorEventBody({ detail, onGo }: { detail: ErrorEventDto; onGo: (id: string) => void }) {
  return (
    <div>
      <InspectorRow label="error_type">
        <Pill color="red">{detail.errorType}</Pill>
      </InspectorRow>
      <InspectorRow label="learning_object">
        <IdLink id={detail.learningObjectId} onGo={onGo} />
      </InspectorRow>
      {detail.attemptId ? (
        <InspectorRow label="attempt">
          <IdLink id={detail.attemptId} onGo={onGo} />
        </InspectorRow>
      ) : null}
      <InspectorRow label="status">
        <Pill color={detail.status === "active" ? "red" : "green"}>{detail.status}</Pill>
      </InspectorRow>
      <InspectorRow label="severity">
        <BlockBar value={detail.severity} width={8} color={COLOR.red} />
        {"  "}
        <Dim style={{ fontFamily: FONT_MONO }}>{detail.severity.toFixed(2)}</Dim>
      </InspectorRow>
      <InspectorRow label="is_misconception">
        {detail.isMisconception ? <Pill color="red">true</Pill> : <Dim>false</Dim>}
      </InspectorRow>
      <InspectorRow label="created">
        <Dim>{relTime(detail.createdAt)}</Dim>
      </InspectorRow>

      {detail.repairPlan && Object.keys(detail.repairPlan).length ? (
        <>
          <SectionHeader>Repair plan</SectionHeader>
          <div style={{ ...panelStyle, borderLeft: `3px solid ${COLOR.red}`, whiteSpace: "pre-wrap", fontSize: 12, fontFamily: FONT_MONO }}>
            {formatUnknown(detail.repairPlan)}
          </div>
        </>
      ) : null}
    </div>
  );
}

// ── note ───────────────────────────────────────────────────────────────────
function NoteBody({ detail, onGo }: { detail: NoteInspectorDetail; onGo: (id: string) => void }) {
  return (
    <div>
      <InspectorRow label="note_id">
        <Dim style={{ fontFamily: FONT_MONO }}>{detail.id}</Dim>
      </InspectorRow>
      {detail.requestedId !== detail.id ? (
        <InspectorRow label="source_ref">
          <Dim style={{ fontFamily: FONT_MONO }}>{detail.requestedId}</Dim>
        </InspectorRow>
      ) : null}
      <InspectorRow label="source_type">
        <Pill color={detail.sourceType === "canonical_source" ? "amber" : "cyan"}>{detail.sourceType}</Pill>
      </InspectorRow>
      {detail.locator ? (
        <InspectorRow label="locator">
          <Dim style={{ fontFamily: FONT_MONO }}>{detail.locator}</Dim>
        </InspectorRow>
      ) : null}
      {detail.path ? (
        <InspectorRow label="path">
          <Dim style={{ fontFamily: FONT_MONO }}>{detail.path}</Dim>
        </InspectorRow>
      ) : null}
      {detail.subjects.length ? (
        <InspectorRow label="subjects">
          <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
            {detail.subjects.map((subject) => (
              <Pill key={subject} color="slate">{subject}</Pill>
            ))}
          </span>
        </InspectorRow>
      ) : null}
      {detail.relatedLos.length ? (
        <InspectorRow label="related_los">
          <span style={{ display: "inline-flex", gap: 8, flexWrap: "wrap" }}>
            {detail.relatedLos.map((id) => (
              <IdLink key={id} id={id} onGo={onGo} />
            ))}
          </span>
        </InspectorRow>
      ) : null}
      {detail.relatedConcepts.length ? (
        <InspectorRow label="related_concepts">
          <span style={{ display: "inline-flex", gap: 8, flexWrap: "wrap" }}>
            {detail.relatedConcepts.map((id) => (
              <IdLink key={id} id={id} onGo={onGo} />
            ))}
          </span>
        </InspectorRow>
      ) : null}
      {detail.canonicalSource ? (
        <InspectorRow label="canonical">
          <Dim style={{ fontFamily: FONT_MONO, overflowWrap: "anywhere" }}>{JSON.stringify(detail.canonicalSource)}</Dim>
        </InspectorRow>
      ) : null}

      <SectionHeader>Body</SectionHeader>
      <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgElev, padding: "10px 12px", fontSize: 13 }}>
        <MarkdownMath value={detail.body} />
      </div>
    </div>
  );
}

// ── attempt ─────────────────────────────────────────────────────────────────
// Structured mirror of the CLI's `learnloop show <attempt>` layout: identity
// rows, a score stat grid, the learner answer, per-criterion grading evidence
// with ✓/✗ verdicts, tutor feedback + repair suggestions, surprise, and error
// attributions — instead of the old raw key/value dump.
function AttemptBody({ id, detail, onGo }: { id: string; detail: AttemptInspectorDetail; onGo: (id: string) => void }) {
  const feedback = detail.feedback ?? null;
  const surprise = feedback?.surprise ?? null;
  const evidence = feedback?.criterionEvidence ?? [];
  const attributions = feedback?.errorAttributions ?? [];
  const repairs = feedback?.repairSuggestions ?? [];
  return (
    <div>
      <InspectorRow label="attempt_id">
        <Dim style={{ fontFamily: FONT_MONO }}>{id}</Dim>
      </InspectorRow>
      <InspectorRow label="practice_item">
        <IdLink id={detail.practiceItemId} onGo={onGo} />
      </InspectorRow>
      <InspectorRow label="learning_object">
        <IdLink id={detail.learningObjectId} onGo={onGo}>
          {feedback?.learningObjectTitle ?? detail.learningObjectId}
        </IdLink>
      </InspectorRow>
      {detail.concept ? <InspectorRow label="concept">{detail.concept}</InspectorRow> : null}
      <InspectorRow label="mode">
        <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
          {detail.practiceMode ? <Pill color={modePillColor(detail.practiceMode)}>{detail.practiceMode}</Pill> : null}
          {detail.attemptType ? <Pill color="slate">{detail.attemptType}</Pill> : null}
        </span>
      </InspectorRow>
      <InspectorRow label="created">
        {relTime(detail.createdAt)} <Meta>{detail.createdAt}</Meta>
      </InspectorRow>

      <SectionHeader>Score</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <Stat
          label="rubric"
          value={detail.rubricScore == null ? "—" : feedback ? `${detail.rubricScore}/${feedback.maxPoints}` : `${detail.rubricScore}`}
          color={
            detail.rubricScore != null && feedback
              ? masteryColor(detail.rubricScore / Math.max(1, feedback.maxPoints))
              : undefined
          }
        />
        <Stat
          label="correctness"
          value={detail.correctness == null ? "—" : detail.correctness.toFixed(2)}
          color={detail.correctness == null ? undefined : masteryColor(detail.correctness)}
        />
        <Stat label="grader_conf" value={detail.graderConfidence == null ? "—" : detail.graderConfidence.toFixed(2)} />
        <Stat label="hints" value={detail.hintsUsed ?? 0} color={detail.hintsUsed ? COLOR.amber : undefined} />
      </div>
      {detail.errorType ? (
        <div style={{ marginTop: 8, display: "flex", gap: 6, alignItems: "center" }}>
          <Pill color="red">{detail.errorType}</Pill>
          {detail.manualReview ? <Pill color="amber">manual review</Pill> : null}
        </div>
      ) : null}

      {detail.learnerAnswerMd ? (
        <>
          <SectionHeader>Learner answer</SectionHeader>
          <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgElev, padding: "10px 12px", fontSize: 13 }}>
            <MarkdownMath value={detail.learnerAnswerMd} />
          </div>
        </>
      ) : null}

      {evidence.length ? (
        <>
          <SectionHeader>Grading evidence</SectionHeader>
          <div style={{ display: "grid", gap: 8 }}>
            {evidence.map((row) => {
              const earned = row.pointsAwarded > 0;
              return (
                <div
                  key={row.criterionId}
                  style={{
                    borderLeft: `3px solid ${earned ? COLOR.green : COLOR.red}`,
                    background: COLOR.bgElev,
                    padding: "8px 12px",
                    fontSize: 12
                  }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
                    <span style={{ color: earned ? COLOR.green : COLOR.red, fontFamily: FONT_MONO }}>{earned ? "✓" : "✗"}</span>
                    <span style={{ color: COLOR.cyan, fontFamily: FONT_MONO, overflowWrap: "anywhere" }}>{row.criterionId}</span>
                    <span style={{ color: earned ? COLOR.green : COLOR.red, fontFamily: FONT_MONO }}>
                      {row.pointsAwarded}/{row.pointsPossible}
                    </span>
                  </div>
                  {row.criterionDescription ? (
                    <div style={{ marginTop: 3, color: COLOR.textDim }}>{row.criterionDescription}</div>
                  ) : null}
                  {row.evidence ? <div style={{ marginTop: 4, color: COLOR.text, lineHeight: 1.5 }}>{row.evidence}</div> : null}
                  {row.notes ? <div style={{ marginTop: 3, color: COLOR.textFaint, lineHeight: 1.5 }}>{row.notes}</div> : null}
                </div>
              );
            })}
          </div>
        </>
      ) : null}

      {feedback?.feedbackMd || repairs.length || (feedback?.fatalErrors.length ?? 0) ? (
        <>
          <SectionHeader>Feedback{feedback?.gradingSource ? ` · graded by ${feedback.gradingSource}` : ""}</SectionHeader>
          {feedback?.fatalErrors.length ? (
            <div style={{ marginBottom: 6, color: COLOR.red, fontSize: 12 }}>
              fatal errors: {feedback.fatalErrors.join(", ")}
            </div>
          ) : null}
          {feedback?.feedbackMd ? (
            <div style={{ fontSize: 13, lineHeight: 1.55 }}>
              <MarkdownMath value={feedback.feedbackMd} />
            </div>
          ) : null}
          {repairs.map((repair, index) => (
            <div key={index} style={{ marginTop: 8, borderTop: `1px solid ${COLOR.border}`, paddingTop: 6, fontSize: 12 }}>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                <span style={{ color: COLOR.amber }}>→ {repair.practiceMode}</span>
                {(repair.targetEvidenceFamilies ?? []).map((facet) => (
                  <Pill key={facet} color="cyan">
                    {facet}
                  </Pill>
                ))}
              </div>
              {repair.rationale ? <div style={{ marginTop: 4, color: COLOR.textDim, lineHeight: 1.5 }}>{repair.rationale}</div> : null}
            </div>
          ))}
        </>
      ) : null}

      {surprise && (surprise.predictiveSurprise != null || surprise.bayesianSurprise != null) ? (
        <>
          <SectionHeader>Surprise</SectionHeader>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            <Stat
              label="predictive"
              value={surprise.predictiveSurprise == null ? "—" : surprise.predictiveSurprise.toFixed(3)}
            />
            <Stat label="bayesian" value={surprise.bayesianSurprise == null ? "—" : surprise.bayesianSurprise.toFixed(3)} />
            <Stat
              label="direction"
              value={surprise.surpriseDirection ?? "—"}
              color={surprise.surpriseDirection === "negative" ? COLOR.red : surprise.surpriseDirection === "positive" ? COLOR.green : undefined}
            />
          </div>
        </>
      ) : null}

      {attributions.length ? (
        <>
          <SectionHeader>Error attributions</SectionHeader>
          <div style={{ display: "grid", gap: 6 }}>
            {attributions.map((ea) => (
              <div key={ea.id} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", fontSize: 12 }}>
                <IdLink id={ea.id} onGo={onGo}>
                  <span style={{ color: COLOR.red }}>{ea.errorTitle ?? ea.errorType}</span>
                </IdLink>
                {ea.isMisconception ? <Pill color="red">misconception</Pill> : null}
                <Pill color={ea.status === "active" ? "amber" : "slate"}>{ea.status}</Pill>
                <Dim style={{ fontFamily: FONT_MONO }}>sev {ea.severity.toFixed(2)}</Dim>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

// ── not_found / search results ──────────────────────────────────────────────
function NotFoundBody({
  id,
  suggestions,
  onGo
}: {
  id: string;
  suggestions: InspectorSearchResult[];
  onGo: (id: string) => void;
}) {
  return (
    <div style={{ padding: "16px 22px 24px" }}>
      <SectionHeader style={{ marginTop: 0 }}>Search results</SectionHeader>
      <div style={{ fontSize: 13, color: COLOR.text, marginBottom: 12 }}>
        no exact match for <span style={{ fontFamily: FONT_MONO, color: COLOR.amberLink }}>{id}</span>
      </div>
      {suggestions.length ? (
        <div style={{ border: `1px solid ${COLOR.border}` }}>
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.kind}:${suggestion.id}`}
              onClick={() => onGo(suggestion.id)}
              style={{
                padding: "10px 12px",
                cursor: "pointer",
                borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 10
              }}
            >
              <span>
                <span style={{ display: "block", color: COLOR.text, fontWeight: 600 }}>{suggestion.title}</span>
                <span style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO }}>
                  {suggestion.id}
                  {suggestion.subtitle ? ` · ${suggestion.subtitle}` : ""}
                </span>
              </span>
              <Pill color={KIND_PILL[suggestion.kind]?.color ?? "slate"}>{suggestion.kind}</Pill>
            </div>
          ))}
        </div>
      ) : (
        <Faint>no fuzzy matches</Faint>
      )}
    </div>
  );
}

// ── component-by-component scheduler `why` ──────────────────────────────────
const WHY_ROWS: Array<{ key: keyof SchedulerComponents; label: string; color: string }> = [
  { key: "forgettingRisk", label: "forgetting_risk", color: COLOR.amber },
  { key: "goalFrontier", label: "goal_frontier", color: COLOR.green },
  { key: "recentError", label: "recent_error", color: COLOR.red },
  { key: "probeEig", label: "probe_eig", color: COLOR.pink },
  { key: "interventionFollowup", label: "intervention_followup", color: COLOR.green }
];

function SchedulerWhy({ scheduler }: { scheduler: SchedulerExplanationDto }) {
  const comps = scheduler.components;
  const normalizedComps = {
    ...comps,
    interventionFollowup: (comps.interventionFollowup ?? 0) + (comps.negativeSurpriseFollowup ?? 0)
  };
  const rows = WHY_ROWS.filter((row) => normalizedComps[row.key] != null);
  const maxVal = Math.max(0.001, ...rows.map((row) => normalizedComps[row.key] ?? 0));
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ color: COLOR.text, fontWeight: 600, fontSize: 13 }}>priority = Σ wᵢ · componentᵢ</span>
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: 8 }}>
          <Faint>priority</Faint>
          <span style={{ color: COLOR.amber, fontWeight: 700, fontSize: 18, fontFamily: FONT_MONO }}>
            {scheduler.priority.toFixed(2)}
          </span>
        </span>
      </div>

      {rows.map((row) => {
        const value = normalizedComps[row.key] ?? 0;
        const pct = (value / maxVal) * 100;
        return (
          <div
            key={row.key}
            style={{ display: "grid", gridTemplateColumns: "180px 1fr 64px", gap: 12, alignItems: "center", padding: "5px 0" }}
          >
            <div style={{ fontSize: 12, color: row.color, fontFamily: FONT_MONO }}>{row.label}</div>
            <div style={{ height: 8, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, position: "relative" }}>
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${pct}%`, background: row.color, opacity: 0.85 }} />
            </div>
            <div style={{ fontSize: 12, color: row.color, textAlign: "right", fontFamily: FONT_MONO }}>{value.toFixed(3)}</div>
          </div>
        );
      })}

      {scheduler.plainEnglish.length ? (
        <div
          style={{
            marginTop: 14,
            padding: "10px 12px",
            background: COLOR.bgElev,
            border: `1px solid ${COLOR.border}`,
            borderLeft: `2px solid ${COLOR.cyan}`,
            fontSize: 12,
            lineHeight: 1.6,
            color: COLOR.text
          }}
        >
          <div style={{ color: COLOR.cyan, fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>
            plain english
          </div>
          {scheduler.plainEnglish.join(" ")}
        </div>
      ) : null}

      <div style={{ marginTop: 10, display: "flex", gap: 16, flexWrap: "wrap", fontSize: 11 }}>
        {scheduler.readinessFactor != null ? (
          <span>
            <Faint>readiness_factor</Faint> <Dim style={{ fontFamily: FONT_MONO }}>{scheduler.readinessFactor.toFixed(2)}</Dim>
          </span>
        ) : null}
        <span>
          <Faint>selected_mode</Faint> <Dim style={{ fontFamily: FONT_MONO }}>{scheduler.selectedMode}</Dim>
        </span>
        <span title="diagnostic expected information gain: entropy reduction over a locked hypothesis set — only defined while a diagnostic probe episode is in progress">
          <Faint>diagnostic_eig</Faint>{" "}
          {scheduler.expectedInformationGain > 0 ? (
            <Dim style={{ fontFamily: FONT_MONO }}>{scheduler.expectedInformationGain.toFixed(3)}</Dim>
          ) : (
            <Faint style={{ fontFamily: FONT_MONO }}>— (no active diagnostic)</Faint>
          )}
        </span>
        {comps.practiceInformation != null ? (
          <span title="display only, never a selection input: Fisher information of one ordinary attempt about this LO's mastery latent (a²·p·(1−p) × evidence mass). Peaks when the item sits on your boundary; near-zero far above or below your level.">
            <Faint>practice_information (display only)</Faint>{" "}
            <Dim style={{ fontFamily: FONT_MONO }}>{comps.practiceInformation.toFixed(3)}</Dim>
          </span>
        ) : null}
      </div>
    </div>
  );
}

// ── small helpers ────────────────────────────────────────────────────────
function MasteryPosteriorBar({ mastery, showLastEvidence = false }: { mastery: MasteryDto; showLastEvidence?: boolean }) {
  const mean = Math.max(0, Math.min(1, mastery.mean));
  const fallbackSd = Math.sqrt(Math.max(0, mastery.variance));
  const lower = Math.max(0, Math.min(mean, mastery.plausibleLower ?? mean - fallbackSd));
  const upper = Math.min(1, Math.max(mean, mastery.plausibleUpper ?? mean + fallbackSd));
  const mass = mastery.plausibleMass ?? 0.8;
  const tone = masteryColor(mean);
  const intervalLabel = `${Math.round(mass * 100)}% plausible range · ${lower.toFixed(2)}–${upper.toFixed(2)}; likely mastery ${mean.toFixed(2)}`;

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 12, flexWrap: "wrap", fontSize: 12 }}>
      <div
        role="img"
        aria-label={intervalLabel}
        title={intervalLabel}
        style={{ display: "inline-grid", gap: 3, flex: "0 0 auto", fontFamily: FONT_MONO }}
      >
        <span aria-hidden><BlockBar value={mean} width={14} color={tone} /></span>
        <span aria-hidden style={{ position: "relative", display: "block", width: "14ch", height: 8 }}>
          <span
            style={{
              position: "absolute",
              top: 3,
              left: `${lower * 100}%`,
              width: `${Math.max(0, upper - lower) * 100}%`,
              borderTop: `1px solid ${COLOR.textFaint}`
            }}
          >
            <span style={{ position: "absolute", left: 0, top: -4, height: 7, borderLeft: `1px solid ${COLOR.textFaint}` }} />
            <span style={{ position: "absolute", right: 0, top: -4, height: 7, borderRight: `1px solid ${COLOR.textFaint}` }} />
          </span>
        </span>
      </div>
      <span style={{ minWidth: 34, color: COLOR.text, fontFamily: FONT_MONO }}>{mean.toFixed(2)}</span>
      <Faint style={{ fontFamily: FONT_MONO }}>±{fallbackSd.toFixed(2)}</Faint>
      <span style={{ marginLeft: "auto", display: "inline-flex", gap: 7, alignItems: "baseline", flexWrap: "wrap" }}>
        <Faint>evidence</Faint>
        <Dim style={{ fontFamily: FONT_MONO }}>{mastery.evidenceCount}</Dim>
        {showLastEvidence ? (
          <>
            <Faint>last</Faint>
            <Dim style={{ fontFamily: FONT_MONO }}>{relTime(mastery.lastEvidenceAt)}</Dim>
          </>
        ) : null}
      </span>
    </div>
  );
}

function InspectorRow({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: 12, padding: "4px 0", alignItems: "baseline", fontSize: 12 }}>
      {/* min-width:0 + overflow-wrap keep long unbreakable ids (source refs)
          inside their grid track instead of overlapping the value column */}
      <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO, minWidth: 0, overflowWrap: "anywhere" }}>{label}</span>
      <span style={{ color: COLOR.text, minWidth: 0, overflowWrap: "anywhere" }}>{children}</span>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: ReactNode; color?: string }) {
  return (
    <div style={{ padding: "8px 10px", border: `1px solid ${COLOR.border}`, background: COLOR.bgElev }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint }}>{label}</div>
      <div style={{ fontSize: 14, color: color ?? COLOR.text, fontFamily: FONT_MONO, marginTop: 2 }}>{value}</div>
    </div>
  );
}

function LearningObjectRelations({
  subjects,
  prerequisites,
  confusables,
  tags,
  onGo
}: {
  subjects: string[];
  prerequisites: ConceptReferenceDto[];
  confusables: ConceptReferenceDto[];
  tags: string[];
  onGo: (id: string) => void;
}) {
  return (
    <>
      <SectionHeader>Relationships · classification</SectionHeader>
      <InspectorRow label="subjects">
        {subjects.length ? subjects.join(" · ") : <Faint>none</Faint>}
      </InspectorRow>
      <InspectorRow
        label={(
          <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            prerequisite concepts
            <HelpTooltip label="What are prerequisite concepts?">
              Concepts expected before this learning object. They express learning order and can affect readiness and upstream evidence propagation.
            </HelpTooltip>
          </span>
        )}
      >
        <ConceptReferenceLinks items={prerequisites} onGo={onGo} />
      </InspectorRow>
      <InspectorRow
        label={(
          <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            confusable concepts
            <HelpTooltip label="What are confusable concepts?">
              Nearby concepts a learner might plausibly substitute for the target. The list combines authored curriculum relationships with repeated learner-observed diagnostic evidence; observed entries require multiple qualifying observations and posterior lift. They are alternatives to distinguish, not prerequisites.
            </HelpTooltip>
          </span>
        )}
      >
        <ConceptReferenceLinks items={confusables} onGo={onGo} />
      </InspectorRow>
      <InspectorRow label="tags">
        {tags.length ? (
          <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap" }}>
            {tags.map((tag) => <Pill key={tag} color="slate">#{tag}</Pill>)}
          </span>
        ) : <Faint>none</Faint>}
      </InspectorRow>
    </>
  );
}

function ConceptReferenceLinks({ items, onGo }: {
  items: ConceptReferenceDto[];
  onGo: (id: string) => void;
}) {
  if (!items.length) return <Faint>none</Faint>;
  return <span style={{ display: "inline-flex", gap: 10, flexWrap: "wrap" }}>
    {items.map((item) => item.resolved && item.conceptId ? (
      <span key={`${item.reference}:${item.conceptId}`} title={`concept · ${item.conceptId}`}>
        <IdLink id={item.conceptId} onGo={onGo}>{item.title}</IdLink>
        {item.source?.includes("learner_observed") && item.probability != null ? (
          <Pill color="pink" style={{ marginLeft: 6, fontSize: 10 }}>
            observed {Math.round(item.probability * 100)}% · {item.evidenceCount ?? 0} probes
          </Pill>
        ) : null}
      </span>
    ) : (
      <span
        key={item.reference}
        title="No unique concept registry match; this legacy reference cannot be opened yet."
        style={{ color: COLOR.textDim, borderBottom: `1px dotted ${COLOR.textFaint}` }}
      >
        {item.title} <Faint>· unresolved</Faint>
      </span>
    ))}
  </span>;
}

function fallbackConceptRefs(values: string[]): ConceptReferenceDto[] {
  return values.map((value) => ({ reference: value, conceptId: value, title: value, resolved: true }));
}

function IdLink({ id, onGo, children }: { id: string; onGo: (id: string) => void; children?: ReactNode }) {
  return (
    <span
      role="button"
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onGo(id);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          onGo(id);
        }
      }}
      style={{
        color: COLOR.amberLink,
        textDecoration: "underline",
        textDecorationStyle: "dotted",
        textUnderlineOffset: "2px",
        cursor: "pointer",
        fontFamily: FONT_MONO
      }}
    >
      {children ?? id}
    </span>
  );
}

function attemptTypePillColor(attemptType: string): PillColor {
  return (
    {
      independent_attempt: "slate",
      hinted_attempt: "amber",
      dont_know: "red",
      diagnostic_probe: "pink",
      guided_walkthrough: "cyan",
      reconstruction_after_walkthrough: "cyan",
      skip: "slate",
      self_report: "purple"
    } as Record<string, PillColor>
  )[attemptType] ?? "slate";
}

function attemptRowStyle(index: number): CSSProperties {
  return {
    display: "grid",
    gridTemplateColumns: "minmax(0, 1.3fr) 64px auto minmax(0, 1.5fr) auto",
    gap: 10,
    padding: "8px 12px",
    alignItems: "center",
    borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
    fontSize: 12
  };
}

function rubricRowStyle(index: number): CSSProperties {
  return {
    display: "grid",
    gridTemplateColumns: "60px 1fr",
    gap: 10,
    padding: "8px 12px",
    borderTop: index > 0 ? `1px solid ${COLOR.border}` : "none",
    fontSize: 12,
    alignItems: "baseline"
  };
}

function relTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const diff = Date.now() - then;
  const abs = Math.abs(diff);
  const minute = 60_000;
  const hour = 3_600_000;
  const day = 86_400_000;
  if (abs < minute) return "just now";
  const label = abs < hour ? `${Math.round(abs / minute)}m` : abs < day ? `${Math.round(abs / hour)}h` : `${Math.round(abs / day)}d`;
  return diff >= 0 ? `${label} ago` : `in ${label}`;
}

function formatUnknown(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(3);
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

// ── layout styles ──────────────────────────────────────────────────────────
const searchInputStyle: CSSProperties = {
  width: "100%",
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.borderFocus}`,
  padding: "8px 12px",
  fontSize: 13,
  fontFamily: FONT_MONO,
  outline: "none"
};

const panelStyle: CSSProperties = {
  padding: "12px 14px",
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.border}`,
  fontSize: 13,
  lineHeight: 1.6,
  color: COLOR.text
};
