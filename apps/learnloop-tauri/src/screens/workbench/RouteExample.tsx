// Reader workbench RW2c: what helps this learner, in the workbench (spec
// §5.10; UX §5.6). Two things land under a hint, beside the learner's step:
//
// - "A worked example that takes your route: Book A §3.4 · compare it with
//   your step 4", looked for in the background after a level-3+ hint (the
//   sources spec's worked_example intent, under the item's assisted-practice
//   policy) and on "Show me a similar example". The passage opens in the
//   book; no passage text is shown here.
// - "another passage ▸" under a bridge or an example whose logged draw kept
//   other verified passages: the next one, with no search and no call (a
//   learner pick).
//
// Everything is absent while its switch is off (workbench.examples_enabled,
// .passage_draw_enabled: the app config carries a key only while it is on),
// so the workbench is then exactly RW2b's. Nothing here moves focus,
// animates or opens a dialog (W12).
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { PassageTarget, WorkbenchExampleViewDto, WorkbenchHelpJobDto, WorkbenchHelpStateDto } from "../../api/dto";
import { quietLine, quietLink } from "../../components/PlainParts";
import { MeaningLabel } from "../reader/voices";
import { errorMessage } from "../../errors";
import type { BridgeState } from "./useWorkbenchHelp";

export const EXAMPLE_COPY = {
  looking: "looking for a worked example that takes your route…",
  none: "no worked example in your books fits this step yet",
  showMe: "show me a similar example",
  another: "another passage ▸",
  noOther: "There is no other passage to show here.",
} as const;

export interface ExampleState {
  status: "pending" | "ready" | "none";
  view?: WorkbenchExampleViewDto;
  message?: string;
}

const FIRST_POLL_MS = 350;
const MAX_POLL_MS = 1500;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function viewOf(result: NonNullable<WorkbenchHelpJobDto["result"]>, hintAssistId: string | null): WorkbenchExampleViewDto | null {
  if (result.status !== "ready" || !result.shown || !result.assistId || !result.line) return null;
  return {
    assistId: result.assistId, line: result.line, spanId: result.spanId ?? null, extractionId: result.extractionId ?? null,
    ...(result.sourceId ? { sourceId: result.sourceId } : {}),
    label: result.label ?? null, verdict: result.verdict ?? null, trigger: result.trigger ?? null,
    aboutStepId: result.aboutStepId ?? null, hintAssistId,
    ...(result.alternatives ? { alternatives: result.alternatives, drawAssistId: result.assistId } : {}),
  };
}

export interface RouteExamples {
  /** Either RW2c switch on: the workbench wires the hook in. */
  active: boolean;
  /** workbench.passage_draw_enabled: "another passage" is offered. */
  passageDraw: boolean;
  /** "Show me a similar example" can run here (examples on, S3 present, a Reader problem). */
  available: boolean;
  underHint: Record<string, ExampleState>;
  standalone: ExampleState[];
  showMePending: boolean;
  notice: string | null;
  followExample: (hintAssistId: string, jobId: string) => void;
  restore: (state: WorkbenchHelpStateDto) => void;
  showMe: (focusedStepId: string | null) => Promise<void>;
  /** The bridge to draw under a hint: the learner's last pick, else RW2b's. */
  bridgeFor: (hintAssistId: string, bridge: BridgeState | undefined) => BridgeState | undefined;
  anotherBridge: (hintAssistId: string, bridge: BridgeState) => Promise<void>;
  anotherExample: (key: { hintAssistId: string } | { index: number }, view: WorkbenchExampleViewDto) => Promise<void>;
}

export function useRouteExamples(options: { sessionId: string; examples: boolean; passageDraw: boolean }): RouteExamples {
  const { sessionId, examples, passageDraw } = options;
  const [available, setAvailable] = useState(false);
  const [underHint, setUnderHint] = useState<Record<string, ExampleState>>({});
  const [standalone, setStandalone] = useState<ExampleState[]>([]);
  const [overrides, setOverrides] = useState<Record<string, BridgeState>>({});
  const [showMePending, setShowMePending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const poll = useCallback(async (started: WorkbenchHelpJobDto): Promise<WorkbenchHelpJobDto> => {
    let job = started;
    let wait = FIRST_POLL_MS;
    while (job.jobId && job.state === "pending" && alive.current) {
      await sleep(wait);
      if (!alive.current) break;
      wait = Math.min(MAX_POLL_MS, Math.round(wait * 1.5));
      job = await api.workbenchHelpJob(job.jobId);
    }
    return job;
  }, []);

  const followExample = useCallback((hintAssistId: string, jobId: string) => {
    if (!examples) return;
    setUnderHint((current) => ({ ...current, [hintAssistId]: { status: "pending" } }));
    void (async () => {
      try {
        const job = await poll(await api.workbenchHelpJob(jobId));
        if (!alive.current) return;
        const view = job.result ? viewOf(job.result, hintAssistId) : null;
        // Under a hint, "nothing fits" stays quiet: the hint is the help.
        setUnderHint((current) => {
          const next = { ...current };
          if (view) next[hintAssistId] = { status: "ready", view };
          else delete next[hintAssistId];
          return next;
        });
      } catch {
        if (alive.current) setUnderHint((current) => {
          const next = { ...current };
          delete next[hintAssistId];
          return next;
        });
      }
    })();
  }, [examples, poll]);

  const restore = useCallback((state: WorkbenchHelpStateDto) => {
    if (!examples) return;
    setAvailable(state.examplesAvailable === true);
    const restored: Record<string, ExampleState> = {};
    for (const hint of state.hints) {
      if (hint.example) restored[hint.assistId] = { status: "ready", view: hint.example };
    }
    setUnderHint(restored);
    setStandalone((state.examples ?? []).map((view) => ({ status: "ready" as const, view })));
  }, [examples]);

  const showMe = useCallback(async (focusedStepId: string | null) => {
    if (!examples || showMePending) return;
    setNotice(null);
    setShowMePending(true);
    try {
      const job = await poll(await api.workbenchShowExample({ sessionId, focusedStepId }));
      if (!alive.current) return;
      const result = job.result;
      const view = result ? viewOf(result, null) : null;
      if (view) setStandalone((current) => [...current, { status: "ready", view }]);
      else if (result?.status === "none") setStandalone((current) => [...current, { status: "none", message: result.line ?? EXAMPLE_COPY.none }]);
      else setNotice(result?.message ?? "Couldn't look for a worked example just now.");
    } catch (error) {
      if (alive.current) setNotice(`Couldn't look for a worked example just now (${errorMessage(error)}).`);
    } finally {
      if (alive.current) setShowMePending(false);
    }
  }, [examples, poll, sessionId, showMePending]);

  const bridgeFor = useCallback((hintAssistId: string, bridge: BridgeState | undefined) => (
    passageDraw && overrides[hintAssistId] ? overrides[hintAssistId] : bridge
  ), [overrides, passageDraw]);

  const anotherBridge = useCallback(async (hintAssistId: string, bridge: BridgeState) => {
    if (!passageDraw || !bridge.assistId) return;
    try {
      const picked = await api.workbenchAnotherPassage({ sessionId, assistId: bridge.assistId });
      if (!alive.current) return;
      const view = picked.passage;
      setOverrides((current) => ({
        ...current,
        [hintAssistId]: { status: "ready", line: view.line, spanId: view.spanId, extractionId: view.extractionId,
          ...(view.sourceId ? { sourceId: view.sourceId } : {}),
          assistId: view.assistId, alternatives: view.alternatives ?? bridge.alternatives },
      }));
    } catch {
      if (alive.current) setNotice(EXAMPLE_COPY.noOther);
    }
  }, [passageDraw, sessionId]);

  const anotherExample = useCallback(async (key: { hintAssistId: string } | { index: number }, view: WorkbenchExampleViewDto) => {
    if (!passageDraw) return;
    try {
      const picked = await api.workbenchAnotherPassage({ sessionId, assistId: view.assistId });
      if (!alive.current) return;
      const next: ExampleState = { status: "ready", view: { ...picked.passage, alternatives: picked.passage.alternatives ?? view.alternatives } };
      if ("hintAssistId" in key) setUnderHint((current) => ({ ...current, [key.hintAssistId]: next }));
      else setStandalone((current) => current.map((entry, index) => (index === key.index ? next : entry)));
    } catch {
      if (alive.current) setNotice(EXAMPLE_COPY.noOther);
    }
  }, [passageDraw, sessionId]);

  return {
    active: examples || passageDraw, passageDraw, available: examples && available, underHint, standalone, showMePending, notice,
    followExample, restore, showMe, bridgeFor, anotherBridge, anotherExample,
  };
}

/** The example's passage, where it is: its reading and book (review F1: an
 *  example from another book opens that book, never the one open now). */
function targetOf(view: WorkbenchExampleViewDto): PassageTarget {
  return { extractionId: view.extractionId ?? null, sourceId: view.sourceId ?? null };
}

function ExampleLine({ state, onPeek, onAnother }: {
  state: ExampleState;
  onPeek?: (spanId: string, target?: PassageTarget) => void;
  onAnother?: () => void;
}) {
  if (state.status === "pending") {
    return <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {EXAMPLE_COPY.looking}</MeaningLabel>;
  }
  if (state.status === "none" || !state.view) {
    return <MeaningLabel style={{ fontSize: 11 }}>{state.message ?? EXAMPLE_COPY.none}</MeaningLabel>;
  }
  const view = state.view;
  return (
    <span style={{ ...quietLine, fontSize: 11, display: "inline-flex", gap: 6, flexWrap: "wrap", alignItems: "baseline" }}>
      <button type="button" data-testid="workbench-route-example" data-verdict={view.verdict ?? undefined}
        style={{ ...quietLink, fontSize: 11 }} onClick={() => (view.spanId && onPeek ? onPeek(view.spanId, targetOf(view)) : undefined)}>
        {view.line}
      </button>
      {view.alternatives && onAnother ? (
        <button type="button" data-testid="workbench-another-passage" style={{ ...quietLink, fontSize: 11 }} onClick={onAnother}>
          {EXAMPLE_COPY.another}
        </button>
      ) : null}
    </span>
  );
}

/** Under a hint, after RW2b's bridge line: "another passage" for the bridge,
 *  and the worked example in the learner's route. */
export function PassageExtras({ hintAssistId, bridge, rw2c, onPeek }: {
  hintAssistId: string;
  bridge: BridgeState | undefined;
  rw2c: RouteExamples;
  onPeek?: (spanId: string, target?: PassageTarget) => void;
}) {
  const example = rw2c.underHint[hintAssistId];
  const anotherBridge = rw2c.passageDraw && bridge?.status === "ready" && bridge.alternatives ? bridge : null;
  if (!anotherBridge && !example) return null;
  return (
    <div data-testid="workbench-passage-extras" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {anotherBridge ? (
        <button type="button" data-testid="workbench-another-bridge" style={{ ...quietLink, fontSize: 11, alignSelf: "flex-start" }}
          onClick={() => void rw2c.anotherBridge(hintAssistId, anotherBridge)}>
          {EXAMPLE_COPY.another}
        </button>
      ) : null}
      {example ? (
        <ExampleLine state={example} onPeek={onPeek}
          onAnother={example.view && rw2c.passageDraw ? () => void rw2c.anotherExample({ hintAssistId }, example.view as WorkbenchExampleViewDto) : undefined} />
      ) : null}
    </div>
  );
}

/** "Show me a similar example" on the step in focus, and its results. */
export function ShowMeExample({ rw2c, focusedStepId, disabled, onPeek }: {
  rw2c: RouteExamples;
  focusedStepId: string | null;
  disabled: boolean;
  onPeek?: (spanId: string, target?: PassageTarget) => void;
}) {
  if (!rw2c.available) return null;
  return (
    <div data-testid="workbench-show-example" style={{ display: "flex", flexDirection: "column", gap: 2, marginLeft: 36 }}>
      {rw2c.standalone.map((state, index) => (
        <ExampleLine key={state.view?.assistId ?? `none-${index}`} state={state} onPeek={onPeek}
          onAnother={state.view && rw2c.passageDraw ? () => void rw2c.anotherExample({ index }, state.view as WorkbenchExampleViewDto) : undefined} />
      ))}
      {rw2c.showMePending ? <ExampleLine state={{ status: "pending" }} /> : null}
      {rw2c.notice ? <div role="status" aria-live="polite"><MeaningLabel style={{ fontSize: 11 }}>{rw2c.notice}</MeaningLabel></div> : null}
      <button type="button" style={{ ...quietLink, fontSize: 10, alignSelf: "flex-start" }} aria-disabled={disabled || rw2c.showMePending}
        onClick={() => { if (!disabled) void rw2c.showMe(focusedStepId); }}>
        {EXAMPLE_COPY.showMe}
      </button>
    </div>
  );
}
