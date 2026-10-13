// The contract every model-backed Reader action follows (reader workbench W14;
// UX §4.0; gate G56): seven states, rendered the same way at the action's
// landing place. Reading, selecting and typing continue through all of them;
// nothing here moves focus, animates or opens a modal.
//
//   pending      ◐ <verb>… (· usually about N s, only when measured) · cancel
//   landed       the result, with its voice
//   failed       what failed, what is kept · try again
//   unreachable  "Couldn't reach LearnLoop's model. <kept> · try again"
//   offline      the sidecar is down: say so, the source still reads
//   capped       "Today's <route> budget (<amount>) is used. <fallback> still works."
//   off          the kill switch is off: nothing at all (no disabled ghost)
import type { ReactNode } from "react";
import { COLOR, FONT_MONO } from "../../components/term";
import { getCommandError } from "../../errors";
import { MeaningLabel } from "./voices";

export type ModelActionPhase = "idle" | "pending" | "landed" | "failed" | "unreachable" | "offline" | "capped" | "off";

export interface ModelActionStateProps {
  phase: ModelActionPhase;
  /** The present-participle verb for pending ("writing", "looking in your books"). */
  verb: string;
  /** A measured p50 for the route, in seconds; omitted unless the report has one. */
  usuallySeconds?: number | null;
  /** What failed, for the failed line ("Couldn't write a quick check."). */
  failure?: string;
  /** What the learner keeps when it fails ("Your question is kept."). */
  kept?: string;
  /** Capped: the route's name and its daily cap, and what still works. */
  capRoute?: string;
  capAmount?: string;
  fallback?: string;
  onCancel?: () => void;
  onRetry?: () => void;
  /** The landed result (rendered only in the landed phase). */
  children?: ReactNode;
}

const linkStyle = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
} as const;

/** Map a rejected model call to its state: the sidecar down, the model
 *  unreachable, a spend or count cap, or an ordinary failure. */
export function phaseForError(error: unknown): ModelActionPhase {
  const command = getCommandError(error);
  const code = command?.code ?? "";
  if (code === "sidecar_unavailable" || code === "sidecar_timeout" || code === "sidecar_protocol_error") return "offline";
  if (code === "provider_unavailable" || code === "provider_timeout") return "unreachable";
  if (code === "question_limit_reached" || code.includes("budget") || code.includes("cap")) return "capped";
  return "failed";
}

export function ModelActionState({
  phase,
  verb,
  usuallySeconds,
  failure,
  kept,
  capRoute,
  capAmount,
  fallback,
  onCancel,
  onRetry,
  children,
}: ModelActionStateProps) {
  if (phase === "off" || phase === "idle") return null;
  if (phase === "landed") return <div data-model-state="landed">{children}</div>;
  const retry = onRetry ? (
    <>
      {" · "}
      <button type="button" onClick={onRetry} style={linkStyle}>try again ↵</button>
    </>
  ) : null;
  let body: ReactNode;
  if (phase === "pending") {
    body = (
      <>
        <span aria-hidden="true">◐</span> {verb}…
        {typeof usuallySeconds === "number" && usuallySeconds > 0 ? ` · usually about ${Math.round(usuallySeconds)} s` : null}
        {onCancel ? (
          <>
            {" · "}
            <button type="button" onClick={onCancel} style={linkStyle}>cancel</button>
          </>
        ) : null}
      </>
    );
  } else if (phase === "unreachable") {
    body = <>Couldn't reach LearnLoop's model.{kept ? ` ${kept}` : ""}{retry}</>;
  } else if (phase === "offline") {
    body = <>LearnLoop's background service isn't responding. The source still reads.{retry}</>;
  } else if (phase === "capped") {
    body = (
      <>
        Today's {capRoute ?? "model"} budget{capAmount ? ` (${capAmount})` : ""} is used.
        {fallback ? ` ${fallback} still works.` : ""}
      </>
    );
  } else {
    body = <>{failure ?? "Couldn't finish that."}{kept ? ` ${kept}` : ""}{retry}</>;
  }
  return (
    <div data-model-state={phase} role="status" aria-live="polite">
      <MeaningLabel style={{ fontSize: 11 }}>{body}</MeaningLabel>
    </div>
  );
}
