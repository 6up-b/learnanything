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
import type {
  InspectorEntity,
  InspectorSearchResult,
  LearningObjectDetail,
  PracticeItemDetail,
  ErrorEventDto,
  SchedulerComponents,
  SchedulerExplanationDto
} from "../api/dto";
import { BlockBar, COLOR, Dim, Divider, Faint, FONT_MONO, Meta, Pill, SectionHeader, type PillColor } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

// ── kind → header pill ──────────────────────────────────────────────────
const KIND_PILL: Record<string, { color: PillColor; label: string }> = {
  practice_item: { color: "cyan", label: "practice_item" },
  learning_object: { color: "purple", label: "learning_object" },
  attempt: { color: "amber", label: "attempt" },
  error_event: { color: "red", label: "error_event" }
};

function modePillColor(mode: string): PillColor {
  return (
    {
      short_answer: "purple",
      explanation: "cyan",
      proof: "amber",
      worked_problem: "green",
      transfer: "pink",
      free_recall: "slate"
    } as Record<string, PillColor>
  )[mode] ?? "purple";
}

function masteryColor(mastery: number): string {
  return mastery > 0.6 ? COLOR.green : mastery > 0.35 ? COLOR.amber : COLOR.red;
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
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(event) => event.stopPropagation()}>
        {/* ── header ── */}
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ color: COLOR.text, fontSize: 13 }}>
            learnloop <span style={{ color: COLOR.amber }}>show</span>
          </span>
          <Faint>·</Faint>
          <span style={{ color: COLOR.amberLink, fontSize: 13, fontFamily: FONT_MONO }}>{entityId}</span>
          {pill ? <Pill color={pill.color}>{pill.label}</Pill> : null}
          <span style={{ flex: 1 }} />
          {history.length > 0 ? (
            <span onClick={back} style={{ color: COLOR.amberLink, fontSize: 12, cursor: "pointer" }}>
              ← back ({history.length})
            </span>
          ) : null}
          <span onClick={onClose} style={{ color: COLOR.textDim, cursor: "pointer", fontSize: 13, marginLeft: 6 }}>
            esc
          </span>
        </div>

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
            <InspectorEntityView entity={entity} childPracticeItemId={childPracticeItemId} onGo={go} />
          )}
        </div>

        {/* ── footer ── */}
        <div style={footerStyle}>
          <span><span style={{ color: COLOR.text }}>esc</span> close</span>
          <span><span style={{ color: COLOR.text }}>backspace</span> back</span>
          {entity?.kind === "practice_item" ? <span><span style={{ color: COLOR.text }}>→</span> parent</span> : null}
          {entity?.kind === "learning_object" && childPracticeItemId ? (
            <span><span style={{ color: COLOR.text }}>←</span> child</span>
          ) : null}
          <span style={{ flex: 1 }} />
          <span>
            CLI mirror · <Dim>learnloop show {entityId}</Dim>
          </span>
        </div>
      </div>
    </div>
  );
}

// ── entity dispatch ───────────────────────────────────────────────────────
function InspectorEntityView({
  entity,
  childPracticeItemId,
  onGo
}: {
  entity: InspectorEntity;
  childPracticeItemId: string | null;
  onGo: (id: string) => void;
}) {
  if (entity.kind === "not_found") {
    return <NotFoundBody id={entity.id} suggestions={entity.suggestions} onGo={onGo} />;
  }

  const title =
    entity.kind === "practice_item"
      ? entity.detail.learningObjectTitle
      : entity.kind === "learning_object"
        ? entity.detail.title
        : entity.kind === "error_event"
          ? entity.detail.errorTitle ?? entity.detail.errorType
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
          <PracticeItemBody detail={entity.detail} onGo={onGo} />
        ) : entity.kind === "learning_object" ? (
          <LearningObjectBody detail={entity.detail} childPracticeItemId={childPracticeItemId} onGo={onGo} />
        ) : entity.kind === "error_event" ? (
          <ErrorEventBody detail={entity.detail} onGo={onGo} />
        ) : (
          <AttemptBody id={entity.id} detail={entity.detail} />
        )}
      </div>
    </>
  );
}

// ── practice_item ──────────────────────────────────────────────────────────
function PracticeItemBody({ detail, onGo }: { detail: PracticeItemDetail; onGo: (id: string) => void }) {
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
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 12 }}>
          <BlockBar value={mastery.mean} width={14} color={masteryColor(mastery.mean)} />
          <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{mastery.mean.toFixed(2)}</span>
          <Faint>±{Math.sqrt(mastery.variance).toFixed(2)}</Faint>
          <span style={{ flex: 1 }} />
          <Faint>evidence</Faint>
          <Dim style={{ fontFamily: FONT_MONO }}>{mastery.evidenceCount}</Dim>
        </div>
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
        <div style={{ display: 'grid', gap: 6 }}>
            {detail.hints.map((h, i) =>
          <div key={i} style={{
            padding: '8px 10px', fontSize: 12, color: COLOR.textDim,
            borderLeft: `2px solid ${COLOR.border}`, lineHeight: 1.5
          }}>
                <Faint>hint {i + 1}</Faint>{' '}{h}
              </div>
          )}
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
        <Dim style={{ fontFamily: FONT_MONO }}>{detail.concept}</Dim>
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
        <InspectorRow label="child practice_item">
          <IdLink id={childPracticeItemId} onGo={onGo} /> <Faint>· ← to return</Faint>
        </InspectorRow>
      ) : null}

      {detail.summary ? (
        <>
          <SectionHeader>Summary</SectionHeader>
          <div style={{ fontSize: 13, color: COLOR.text, lineHeight: 1.6 }}>{detail.summary}</div>
        </>
      ) : null}

      <SectionHeader>Mastery posterior</SectionHeader>
      {detail.mastery ? (
        <div>
          <div style={{ fontSize: 24, fontFamily: FONT_MONO, color: masteryColor(detail.mastery.mean) }}>
            {detail.mastery.mean.toFixed(2)}
          </div>
          <div>
            <Faint>±{Math.sqrt(detail.mastery.variance).toFixed(2)} (logit-space Kalman)</Faint>
          </div>
          <div style={{ marginTop: 6, fontSize: 11 }}>
            <Faint>evidence_count</Faint> <Dim style={{ fontFamily: FONT_MONO }}>{detail.mastery.evidenceCount}</Dim>
            {"   "}
            <Faint>last</Faint> <Dim>{relTime(detail.mastery.lastEvidenceAt)}</Dim>
          </div>
        </div>
      ) : (
        <Faint>no evidence yet</Faint>
      )}

      <PillList label="Subjects" items={detail.subjects} />
      <PillList label="Prerequisites" items={detail.prerequisites} onGo={onGo} color="amber" />
      <PillList label="Confusables" items={detail.confusables} onGo={onGo} color="pink" />
      <PillList label="Tags" items={detail.tags} color="slate" />
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

// ── attempt (untyped detail) ────────────────────────────────────────────────
function AttemptBody({ id, detail }: { id: string; detail: unknown }) {
  const rows = detail && typeof detail === "object" ? Object.entries(detail as Record<string, unknown>) : [];
  return (
    <div>
      <InspectorRow label="attempt_id">
        <Dim style={{ fontFamily: FONT_MONO }}>{id}</Dim>
      </InspectorRow>
      {rows.length ? (
        rows.map(([key, value]) => (
          <InspectorRow key={key} label={key}>
            <span style={{ overflowWrap: "anywhere", fontFamily: FONT_MONO, fontSize: 12 }}>{formatUnknown(value)}</span>
          </InspectorRow>
        ))
      ) : (
        <div style={{ marginTop: 8 }}>
          <Faint>no structured attempt detail available</Faint>
        </div>
      )}
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
  { key: "activeGoal", label: "active_goal", color: COLOR.green },
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
            style={{ display: "grid", gridTemplateColumns: "200px 1fr 64px", gap: 12, alignItems: "center", padding: "5px 0" }}
          >
            <div style={{ fontSize: 12, color: row.color, fontFamily: FONT_MONO }}>{row.label}</div>
            <div style={{ height: 18, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, position: "relative" }}>
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
            borderLeft: `3px solid ${COLOR.cyan}`,
            fontSize: 12,
            lineHeight: 1.6,
            color: COLOR.text
          }}
        >
          <div style={{ color: COLOR.cyan, fontWeight: 600, marginBottom: 3 }}>plain english</div>
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
        <span>
          <Faint>expected_information_gain</Faint>{" "}
          <Dim style={{ fontFamily: FONT_MONO }}>{scheduler.expectedInformationGain.toFixed(3)}</Dim>
        </span>
      </div>
    </div>
  );
}

// ── small helpers ────────────────────────────────────────────────────────
function InspectorRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: 12, padding: "4px 0", alignItems: "baseline", fontSize: 12 }}>
      <span style={{ color: COLOR.textFaint, fontFamily: FONT_MONO }}>{label}</span>
      <span style={{ color: COLOR.text }}>{children}</span>
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

function PillList({
  label,
  items,
  onGo,
  color = "cyan"
}: {
  label: string;
  items: string[];
  onGo?: (id: string) => void;
  color?: PillColor;
}) {
  if (!items.length) return null;
  return (
    <>
      <SectionHeader>{`${label} (${items.length})`}</SectionHeader>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {items.map((item) =>
          onGo ? (
            <IdLink key={item} id={item} onGo={onGo}>
              <Pill color={color}>{item}</Pill>
            </IdLink>
          ) : (
            <Pill key={item} color={color}>
              {item}
            </Pill>
          )
        )}
      </div>
    </>
  );
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
const backdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 200,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "6vh 5vw",
  backdropFilter: "blur(2px)"
};

const modalStyle: CSSProperties = {
  width: "min(960px, 100%)",
  maxHeight: "88vh",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const headerStyle: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexShrink: 0
};

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

const footerStyle: CSSProperties = {
  borderTop: `1px solid ${COLOR.border}`,
  padding: "6px 14px",
  fontSize: 11,
  color: COLOR.textDim,
  display: "flex",
  gap: 18,
  flexShrink: 0,
  alignItems: "center"
};

const panelStyle: CSSProperties = {
  padding: "12px 14px",
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.border}`,
  fontSize: 13,
  lineHeight: 1.6,
  color: COLOR.text
};
