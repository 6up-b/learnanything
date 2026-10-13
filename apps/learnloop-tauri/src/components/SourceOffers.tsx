import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  DailyPlanDto,
  FindPracticeResultDto,
  PracticeRequestDto,
  SourceExerciseImportDto,
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
/** How often a queued textbook import is checked, and for how long before the
 *  learner is offered "check again" (authoring plus the key's time-boxed check). */
const IMPORT_POLL_MS = 1500;
const IMPORT_FOLLOW_MS = 6 * 60 * 1000;
const IMPORT_DONE = new Set(["written", "rejected", "failed"]);

/** Where a picked offer stands. `added`: the plan serves it; `open`: the plan
 *  is off, so the open list serves it when the learner opens it; the rest
 *  follow a textbook exercise's import. */
type PickState =
  | { state: "picking" }
  | { state: "added"; note?: string }
  | { state: "open"; practiceItemId: string; note?: string }
  | { state: "importing"; importId?: string }
  | { state: "slow"; importId: string }
  | { state: "failed"; reason: string };

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
  onOpenPractice,
  onToast,
  importPollMs = IMPORT_POLL_MS
}: {
  answer: SourceOffersAnswer;
  sessionId?: string;
  onExplainWithWork?: (spanKey: string) => void;
  /** The open-list path (DL0's open), used when the daily plan is off. */
  onOpenPractice?: (practiceItemId: string) => void;
  onToast: (message: string) => void;
  importPollMs?: number;
}) {
  const [practice, setPractice] = useState<PracticeOffer[]>([]);
  const [passages, setPassages] = useState<Array<{ request: SourceToolRequestDto; run: SourceToolRunDto }>>([]);
  const [opened, setOpened] = useState<Set<string>>(new Set());
  const [comparisons, setComparisons] = useState<Record<string, SourceToolRunDto | "loading" | string>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [picks, setPicks] = useState<Record<string, PickState>>({});
  const impressed = useRef<Set<string>>(new Set());
  const unmounted = useRef(false);

  useEffect(() => {
    unmounted.current = false;
    return () => {
      unmounted.current = true;
    };
  }, []);

  function setPick(key: string, state: PickState) {
    if (!unmounted.current) setPicks((prev) => ({ ...prev, [key]: state }));
  }

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

  /** After the serving path answered: the plan serves the item (`added`), or,
   *  with the plan off, the open list does when the learner opens it. */
  function delivered(key: string, result: DailyPlanDto, practiceItemId: string, note?: string) {
    if (result.enabled) {
      setPick(key, { state: "added", note });
      onToast(note ? `Added to today's practice. ${note}` : "Added to today's practice.");
      return;
    }
    setPick(key, { state: "open", practiceItemId, note });
    onToast(
      onOpenPractice
        ? "Your daily plan is off: open it from here when you're ready."
        : "Your daily plan is off: open it from your practice list."
    );
  }

  async function pickItem(offer: PracticeOffer, practiceItemId: string) {
    setPick(practiceItemId, { state: "picking" });
    try {
      const result = await api.planLearnerPick(practiceItemId, sessionId ?? null, null, offer.proposalId);
      delivered(practiceItemId, result, practiceItemId);
    } catch (error) {
      setPick(practiceItemId, { state: "failed", reason: message(error) });
      onToast(message(error));
    }
  }

  async function followImport(importId: string): Promise<SourceExerciseImportDto | null> {
    const started = Date.now();
    for (;;) {
      const current = await api.getSourceExerciseImport(importId);
      if (IMPORT_DONE.has(current.status)) return current;
      if (unmounted.current || Date.now() - started > IMPORT_FOLLOW_MS) return null;
      await new Promise((resolve) => setTimeout(resolve, importPollMs));
    }
  }

  async function deliverImport(offer: PracticeOffer, key: string, importId: string) {
    setPick(key, { state: "importing", importId });
    const done = await followImport(importId);
    if (done === null) {
      setPick(key, { state: "slow", importId });
      return;
    }
    if (done.status !== "written" || !done.practiceItemId) {
      const reason = done.reason ?? (done.status === "rejected" ? "it didn't pass its checks" : "the import failed");
      setPick(key, { state: "failed", reason });
      onToast(`Couldn't bring this exercise into your practice: ${reason}`);
      return;
    }
    const note = done.keyLabel ? `Answer key: ${done.keyLabel}.` : undefined;
    const result = await api.planLearnerPick(done.practiceItemId, sessionId ?? null, null, offer.proposalId, importId);
    delivered(key, result, done.practiceItemId, note);
  }

  async function importExercise(offer: PracticeOffer, exercise: PracticeOffer["exercises"][number]) {
    if (!offer.proposalId) return;
    setPick(exercise.key, { state: "importing" });
    try {
      const queued = await api.importSourceExercise({
        proposalId: offer.proposalId,
        extractionId: exercise.extractionId,
        spanIds: exercise.spanIds,
        sessionId: sessionId ?? null
      });
      onToast("Bringing this exercise into your practice; its answer key is being checked.");
      await deliverImport(offer, exercise.key, queued.importId);
    } catch (error) {
      setPick(exercise.key, { state: "failed", reason: message(error) });
      onToast(message(error));
    }
  }

  async function checkAgain(offer: PracticeOffer, key: string, importId: string) {
    try {
      await deliverImport(offer, key, importId);
    } catch (error) {
      setPick(key, { state: "failed", reason: message(error) });
      onToast(message(error));
    }
  }

  function pickStatus(offer: PracticeOffer, key: string, action: string, onPick: () => void) {
    const pick = picks[key];
    if (!pick) {
      return (
        <span style={actionStyle} onClick={onPick}>
          {action}
        </span>
      );
    }
    switch (pick.state) {
      case "picking":
        return <Faint>adding …</Faint>;
      case "added":
        return <Faint>added</Faint>;
      case "open":
        return onOpenPractice ? (
          <span style={actionStyle} onClick={() => onOpenPractice(pick.practiceItemId)}>
            ❯ open
          </span>
        ) : (
          <Faint>in your practice list</Faint>
        );
      case "importing":
        return <Faint>importing, checking its answer key …</Faint>;
      case "slow":
        return (
          <span style={actionStyle} onClick={() => void checkAgain(offer, key, pick.importId)}>
            ❯ still checking: check again
          </span>
        );
      case "failed":
        return (
          <span style={{ display: "inline-flex", gap: 6 }}>
            <Faint>couldn't add: {pick.reason}</Faint>
            <span style={actionStyle} onClick={onPick}>
              ❯ try again
            </span>
          </span>
        );
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
              {pickStatus(offer, item.practiceItemId, "❯ practise", () => void pickItem(offer, item.practiceItemId))}
            </div>
          ))}
          {offer.exercises.map((exercise) => (
            <div key={exercise.key} style={{ marginTop: 4 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                <span style={{ flex: 1, minWidth: 0, color: COLOR.text }}>{clip(exercise.statement)}</span>
                {pickStatus(offer, exercise.key, "❯ practise from your book", () => void importExercise(offer, exercise))}
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
