import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  FindPracticeResultDto,
  PracticeRequestDto,
  SourcePassageDto,
  SourceToolRequestDto,
  SourceToolRunDto
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill } from "./term";

/** Canonical sources (spec_source_practice_and_probes_v1 §6.2, §10.3): the
 *  offers under a tutor answer. Everything here PROPOSES: a practice pick goes
 *  through the plan's own pick path, a textbook exercise through its import
 *  (whose answer key is checked before it counts), and passages are the
 *  learner's own books, labelled source-authored. Nothing is served from here. */

export interface SourceOffersAnswer {
  eventId: string;
  practiceRequest?: PracticeRequestDto | null;
  toolRequests?: SourceToolRequestDto[];
}

interface PracticeOffer {
  key: string;
  reason: string;
  proposalId: string | null;
  items: Array<{ practiceItemId: string; prompt: string; detail: string | null }>;
  exercises: Array<{ key: string; extractionId: string; spanIds: string[]; label: string; statement: string }>;
}

const MAX_SHOWN = 3;

function message(error: unknown): string {
  return (error as CommandError)?.message ?? String(error);
}

function clip(text: string, limit = 220): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length <= limit ? flat : `${flat.slice(0, limit - 1)}…`;
}

function fromFindPractice(key: string, reason: string, result: FindPracticeResultDto): PracticeOffer {
  return {
    key,
    reason,
    proposalId: result.proposalId ?? null,
    items: result.items.slice(0, MAX_SHOWN).map((item) => ({
      practiceItemId: item.practiceItemId,
      prompt: item.prompt,
      detail: item.rationale
    })),
    exercises: (result.sourceExercises ?? []).slice(0, MAX_SHOWN).map((exercise) => ({
      key: exercise.key,
      extractionId: exercise.extractionId,
      spanIds: exercise.spanIds,
      label: exercise.labelLine,
      statement: exercise.statement
    }))
  };
}

function fromToolRun(request: SourceToolRequestDto, run: SourceToolRunDto): PracticeOffer {
  return {
    key: request.toolCallId,
    reason: request.reason ?? "Practice this",
    proposalId: run.result.proposalId ?? null,
    items: (run.result.items ?? []).slice(0, MAX_SHOWN).map((item) => ({
      practiceItemId: item.practiceItemId,
      prompt: item.prompt,
      detail: item.rationale
    })),
    exercises: (run.result.sourceExercises ?? []).slice(0, MAX_SHOWN).map((exercise) => {
      const [extractionId] = exercise.spanKeys[0]?.split(":") ?? [""];
      return {
        key: exercise.key,
        extractionId,
        spanIds: exercise.spanKeys.map((spanKey) => spanKey.slice(spanKey.indexOf(":") + 1)),
        label: exercise.sourceLabel ?? "From your book",
        statement: exercise.statement
      };
    })
  };
}

const offerBox = {
  border: `1px solid ${COLOR.border}`,
  borderRadius: 4,
  padding: "6px 8px",
  marginTop: 6,
  fontSize: 12
} as const;

const actionStyle = {
  cursor: "pointer",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  whiteSpace: "nowrap"
} as const;

export function SourceOffers({
  answer,
  sessionId,
  onExplainWithWork,
  onToast
}: {
  answer: SourceOffersAnswer;
  sessionId?: string;
  onExplainWithWork?: (spanKey: string) => void;
  onToast: (message: string) => void;
}) {
  const [practice, setPractice] = useState<PracticeOffer[]>([]);
  const [passages, setPassages] = useState<Array<{ request: SourceToolRequestDto; run: SourceToolRunDto }>>([]);
  const [opened, setOpened] = useState<Set<string>>(new Set());
  const [comparisons, setComparisons] = useState<Record<string, SourceToolRunDto | "loading" | string>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const impressed = useRef<Set<string>>(new Set());

  const toolRequests = answer.toolRequests ?? [];
  const compareRequests = toolRequests.filter((request) => request.tool === "compare_sources");

  useEffect(() => {
    let cancelled = false;
    const practiceRequests = toolRequests.filter((request) => request.tool === "find_practice");
    const sourceRequests = toolRequests.filter((request) => request.tool === "find_sources");
    // Eager runs: practice and passages load as the offer is shown.
    for (const request of practiceRequests) {
      api
        .runSourceTool(request.toolCallId)
        .then((run) => {
          if (!cancelled) setPractice((prev) => [...prev, fromToolRun(request, run)]);
        })
        .catch((error) => !cancelled && setErrors((prev) => [...prev, message(error)]));
    }
    if (practiceRequests.length === 0 && answer.practiceRequest) {
      const offer = answer.practiceRequest;
      api
        .findPractice({ ...offer.request, caller: offer.caller })
        .then((result) => {
          if (!cancelled) setPractice([fromFindPractice(answer.eventId, "Practice this", result)]);
        })
        .catch((error) => !cancelled && setErrors((prev) => [...prev, message(error)]));
    }
    for (const request of sourceRequests) {
      api
        .runSourceTool(request.toolCallId)
        .then((run) => {
          if (!cancelled && (run.result.passages ?? []).length > 0) setPassages((prev) => [...prev, { request, run }]);
        })
        .catch((error) => !cancelled && setErrors((prev) => [...prev, message(error)]));
    }
    return () => {
      cancelled = true;
    };
    // The answer is immutable once shown; run its offers once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer.eventId]);

  // Displayed is not unseen (§6.5): record what the strip rendered.
  useEffect(() => {
    for (const offer of practice) {
      if (!offer.proposalId || impressed.current.has(offer.proposalId)) continue;
      const keys = [
        ...offer.items.map((item) => ({ kind: "item" as const, practiceItemId: item.practiceItemId })),
        ...offer.exercises.map((exercise) => ({
          kind: "source_exercise" as const,
          extractionId: exercise.extractionId,
          spanIds: exercise.spanIds
        }))
      ];
      if (keys.length === 0) continue;
      impressed.current.add(offer.proposalId);
      void api
        .recordProposalImpressions({ proposalId: offer.proposalId, surface: "tutor_strip", keys, sessionId })
        .catch(() => undefined);
    }
  }, [practice, sessionId]);

  async function pickItem(offer: PracticeOffer, practiceItemId: string) {
    try {
      await api.planLearnerPick(practiceItemId, sessionId ?? null, null, offer.proposalId);
      setPicked((prev) => new Set(prev).add(practiceItemId));
      onToast("Added to today's practice.");
    } catch (error) {
      onToast(message(error));
    }
  }

  async function importExercise(offer: PracticeOffer, exercise: PracticeOffer["exercises"][number]) {
    if (!offer.proposalId) return;
    try {
      await api.importSourceExercise({
        proposalId: offer.proposalId,
        extractionId: exercise.extractionId,
        spanIds: exercise.spanIds,
        sessionId: sessionId ?? null
      });
      setPicked((prev) => new Set(prev).add(exercise.key));
      onToast("Bringing this exercise into your practice; its answer key is being checked.");
    } catch (error) {
      onToast(message(error));
    }
  }

  function openPassages(toolCallId: string, shown: SourcePassageDto[]) {
    setOpened((prev) => new Set(prev).add(toolCallId));
    void api
      .recordSourceOfferShown({ toolCallId, spanKeys: shown.map((passage) => passage.spanKey), sessionId })
      .catch(() => undefined);
  }

  async function compare(request: SourceToolRequestDto) {
    setComparisons((prev) => ({ ...prev, [request.toolCallId]: "loading" }));
    try {
      const run = await api.runSourceTool(request.toolCallId);
      setComparisons((prev) => ({ ...prev, [request.toolCallId]: run }));
      if ((run.result.sources ?? []).length > 0) {
        void api.recordSourceOfferShown({ toolCallId: request.toolCallId, sessionId }).catch(() => undefined);
      }
    } catch (error) {
      setComparisons((prev) => ({ ...prev, [request.toolCallId]: message(error) }));
    }
  }

  const visiblePractice = practice.filter((offer) => offer.items.length + offer.exercises.length > 0);
  if (visiblePractice.length === 0 && passages.length === 0 && compareRequests.length === 0 && errors.length === 0) {
    return null;
  }

  return (
    <div data-testid="source-offers" style={{ marginTop: 8 }}>
      {visiblePractice.map((offer) => (
        <div key={offer.key} style={offerBox} data-testid="practice-offer">
          <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
            <Pill color="amber">practice this</Pill>
            <span style={{ color: COLOR.text }}>{offer.reason}</span>
          </div>
          {offer.items.map((item) => (
            <div key={item.practiceItemId} style={{ display: "flex", gap: 8, alignItems: "baseline", marginTop: 3 }}>
              <span style={{ flex: 1, minWidth: 0, color: COLOR.text }}>{clip(item.prompt)}</span>
              {picked.has(item.practiceItemId) ? (
                <Faint>added</Faint>
              ) : (
                <span style={actionStyle} onClick={() => void pickItem(offer, item.practiceItemId)}>
                  ❯ practise
                </span>
              )}
            </div>
          ))}
          {offer.exercises.map((exercise) => (
            <div key={exercise.key} style={{ marginTop: 4 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                <span style={{ flex: 1, minWidth: 0, color: COLOR.text }}>{clip(exercise.statement)}</span>
                {picked.has(exercise.key) ? (
                  <Faint>importing</Faint>
                ) : (
                  <span style={actionStyle} onClick={() => void importExercise(offer, exercise)}>
                    ❯ practise from your book
                  </span>
                )}
              </div>
              <Faint style={{ fontSize: 10 }}>{exercise.label}</Faint>
            </div>
          ))}
        </div>
      ))}
      {passages.map(({ request, run }) => {
        const shown = run.result.passages ?? [];
        const isOpen = opened.has(request.toolCallId);
        return (
          <div key={request.toolCallId} style={offerBox} data-testid="passage-offer">
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <Pill color="cyan">from your books</Pill>
              <span style={{ flex: 1, color: COLOR.text }}>{request.reason ?? "Passages from your sources"}</span>
              {!isOpen ? (
                <span style={actionStyle} onClick={() => openPassages(request.toolCallId, shown)}>
                  ❯ read {shown.length}
                </span>
              ) : null}
            </div>
            {isOpen
              ? shown.map((passage) => (
                  <div key={passage.spanKey} style={{ marginTop: 6 }}>
                    <Faint style={{ fontSize: 10 }}>
                      {[passage.sourceTitle, passage.section, passage.page != null ? `p. ${passage.page}` : null]
                        .filter(Boolean)
                        .join(" · ")}{" "}
                      · {passage.label}
                    </Faint>
                    <div style={{ color: COLOR.text, whiteSpace: "pre-wrap" }}>{passage.text}</div>
                    {onExplainWithWork ? (
                      <span style={actionStyle} onClick={() => onExplainWithWork(passage.spanKey)}>
                        ❯ explain this with my work
                      </span>
                    ) : null}
                  </div>
                ))
              : null}
          </div>
        );
      })}
      {compareRequests.map((request) => {
        const state = comparisons[request.toolCallId];
        return (
          <div key={request.toolCallId} style={offerBox} data-testid="compare-offer">
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <Pill color="purple">compare</Pill>
              <span style={{ flex: 1, color: COLOR.text }}>{request.reason ?? "How do your books treat this?"}</span>
              {state === undefined ? (
                <span style={actionStyle} onClick={() => void compare(request)}>
                  ❯ how do your books treat this?
                </span>
              ) : null}
            </div>
            {state === "loading" ? <Faint>reading your sources …</Faint> : null}
            {typeof state === "string" && state !== "loading" ? <Faint>couldn't compare: {state}</Faint> : null}
            {state && typeof state !== "string" ? (
              <div style={{ marginTop: 4 }}>
                {(state.result.sources ?? []).map((source) => (
                  <div key={source.ref} style={{ marginTop: 4 }}>
                    <Faint style={{ fontSize: 10 }}>
                      {source.sourceTitle ?? source.sourceId}
                      {source.page != null ? ` · p. ${source.page}` : ""} · {source.label}
                    </Faint>
                    {(source.contributions ?? []).map((line, index) => (
                      <div key={index} style={{ color: COLOR.text }}>
                        {line.contribution} <Faint>“{line.quote}”</Faint>
                      </div>
                    ))}
                  </div>
                ))}
                {(state.result.sources ?? []).length === 0 ? (
                  <Faint>Your sources don't give enough to compare ({state.result.status}).</Faint>
                ) : (
                  <Faint style={{ fontSize: 10 }}>{state.result.labels?.comparison ?? "LearnLoop's comparison"}</Faint>
                )}
              </div>
            ) : null}
          </div>
        );
      })}
      {errors.length > 0 ? (
        <Faint style={{ fontSize: 10 }}>Some offers couldn't load: {errors[0]}</Faint>
      ) : null}
    </div>
  );
}
