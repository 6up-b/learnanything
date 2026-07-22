import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { CommandError, RetirementReason } from "../api/dto";
import { RETIREMENT_REASONS } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "./term";

// Learner card controls (Andy: "readers control the prompts they collect"):
// reword, split ("this wants to be two questions"), retire — immediately, in
// place, no review gate. Mounted wherever a card is being looked at:
// PracticeScreen (prompt-only — the expected answer must not leak pre-attempt)
// and FeedbackScreen (full controls; the answer is already revealed).

const REASON_LABEL: Record<RetirementReason, string> = {
  too_easy: "too easy",
  ambiguous: "ambiguous",
  missing_context: "missing context",
  duplicate_surface: "feels like a duplicate",
  wrong_granularity: "wrong granularity",
  no_longer_relevant: "no longer relevant",
  bad_underlying_explanation: "the explanation it rests on is bad",
  superseded_by_better_activity: "superseded by a better activity",
  should_be_reference_not_memorized: "should be reference, not memorized",
  dont_care_enough_to_retain: "don't care enough to retain",
  knew_prompt_not_concept: "I knew the prompt, not the concept"
};

type Panel = "reword" | "split" | "retire" | null;

// Learner-initiated re-runging: mint an easier/harder sibling one depth
// waypoint away. The request itself is evidence (a discounted self-report on
// the source card), written before the variant is authored. Reused by
// CardControls (Practice/Feedback), the InspectorOverlay, and GoldenPath.
export function RungVariantActions({
  practiceItemId,
  disabled = false,
  onError,
  onApplied
}: {
  practiceItemId: string;
  disabled?: boolean;
  onError: (message: string) => void;
  /** Called when the variant lands in the vault (caller refreshes its view). */
  onApplied?: (createdPracticeItemId: string | null) => void;
}) {
  const [pending, setPending] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    },
    []
  );

  const request = async (direction: "easier" | "harder") => {
    if (busy || pending !== null || disabled) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await api.requestRungVariant({ practiceItemId, direction });
      setPending(`authoring an ${direction} variant (${result.sourceWaypoint} → ${result.targetWaypoint})…`);
      const requestId = result.requestId;
      pollRef.current = window.setInterval(async () => {
        try {
          const { request: row } = await api.getRungVariantStatus({ requestId });
          if (row.status === "pending" || row.status === "generating") return;
          if (pollRef.current !== null) window.clearInterval(pollRef.current);
          pollRef.current = null;
          setPending(null);
          if (row.status === "applied") {
            setNotice(`${direction} variant added — it will be served next`);
            onApplied?.(row.createdPracticeItemId);
          } else if (row.status === "review_required") {
            setNotice("variant needs review — see the Proposals screen");
          } else {
            onError(row.failureReason ?? "variant authoring failed");
          }
        } catch {
          /* poll again next tick; terminal errors surface via failureReason */
        }
      }, 2000);
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  if (pending !== null) {
    return <Faint style={{ fontSize: 11 }}>◐ {pending}</Faint>;
  }
  const inactive = busy || disabled;
  const linkStyle = {
    fontFamily: FONT_MONO,
    fontSize: 11,
    color: inactive ? COLOR.textFaint : COLOR.amberLink,
    textDecoration: "underline",
    textUnderlineOffset: 2,
    cursor: inactive ? "default" : "pointer",
    whiteSpace: "nowrap"
  } as const;
  return (
    <>
      <span
        onClick={() => void request("easier")}
        title="mint an easier sibling one depth waypoint down — also tells the model this card is above your current level"
        style={linkStyle}
      >
        ↓ easier
      </span>
      <span
        onClick={() => void request("harder")}
        title="mint a harder sibling one depth waypoint up — also tells the model this card is below your current level"
        style={linkStyle}
      >
        ↑ harder
      </span>
      {notice ? <Faint style={{ fontSize: 11 }}>{notice}</Faint> : null}
    </>
  );
}

export function CardControls({
  practiceItemId,
  prompt,
  expectedAnswer,
  onError,
  onChanged,
  onRetired
}: {
  practiceItemId: string;
  prompt: string;
  /** Pass null while the answer must stay hidden (pre-attempt) — disables
   *  answer editing and split. */
  expectedAnswer: string | null;
  onError: (message: string) => void;
  /** Called after a successful reword (caller refreshes its item). */
  onChanged?: () => void;
  /** Called after a successful retire or split (caller navigates/refreshes). */
  onRetired?: (createdIds?: string[]) => void;
}) {
  const [panel, setPanel] = useState<Panel>(null);
  const [busy, setBusy] = useState(false);
  const [promptDraft, setPromptDraft] = useState(prompt);
  const [answerDraft, setAnswerDraft] = useState(expectedAnswer ?? "");
  const [parts, setParts] = useState<Array<{ prompt: string; expectedAnswer: string }>>([
    { prompt, expectedAnswer: expectedAnswer ?? "" },
    { prompt: "", expectedAnswer: "" }
  ]);
  const [reason, setReason] = useState<RetirementReason>("knew_prompt_not_concept");
  const [note, setNote] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    try {
      await fn();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const reword = () =>
    run(async () => {
      const input: { practiceItemId: string; prompt?: string; expectedAnswer?: string } = { practiceItemId };
      if (promptDraft.trim() && promptDraft.trim() !== prompt) input.prompt = promptDraft.trim();
      if (expectedAnswer !== null && answerDraft.trim() && answerDraft.trim() !== expectedAnswer)
        input.expectedAnswer = answerDraft.trim();
      if (!input.prompt && !input.expectedAnswer) {
        setNotice("nothing changed");
        return;
      }
      await api.editPracticeItem(input);
      setNotice("saved — the card is yours");
      setPanel(null);
      onChanged?.();
    });

  const split = () =>
    run(async () => {
      const result = await api.splitPracticeItem({
        practiceItemId,
        parts: parts.map((p) => ({ prompt: p.prompt.trim(), expectedAnswer: p.expectedAnswer.trim() }))
      });
      setNotice(`split into ${result.created.length} cards; this one retired`);
      setPanel(null);
      onRetired?.(result.created);
    });

  const retire = () =>
    run(async () => {
      await api.retirePracticeItem({ practiceItemId, reason, note: note.trim() || undefined });
      setNotice("retired — history kept, never served again");
      setPanel(null);
      onRetired?.();
    });


  const link = (label: string, target: Panel) => (
    <span
      key={label}
      onClick={() => {
        setNotice(null);
        setPanel(panel === target ? null : target);
      }}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 11,
        color: panel === target ? COLOR.amber : COLOR.textFaint,
        textDecoration: "underline",
        textUnderlineOffset: 2,
        cursor: "pointer"
      }}
    >
      {label}
    </span>
  );

  const textarea = (value: string, set: (v: string) => void, placeholder: string, rows = 2) => (
    <textarea
      value={value}
      onChange={(e) => set(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 12,
        background: COLOR.bgInput,
        border: `1px solid ${COLOR.border}`,
        color: COLOR.text,
        padding: 6,
        resize: "vertical",
        width: "100%"
      }}
    />
  );

  const action = (label: string, onClick: () => void) => (
    <span
      onClick={busy ? undefined : onClick}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 11,
        color: busy ? COLOR.textFaint : COLOR.amberLink,
        textDecoration: "underline",
        textUnderlineOffset: 2,
        cursor: busy ? "default" : "pointer"
      }}
    >
      {busy ? "…" : label}
    </span>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 6 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>THIS CARD:</Faint>
        {link("reword", "reword")}
        {expectedAnswer !== null ? link("split in two", "split") : null}
        {link("retire", "retire")}
        <RungVariantActions
          practiceItemId={practiceItemId}
          disabled={busy}
          onError={onError}
          onApplied={() => onChanged?.()}
        />
        {notice ? <Faint style={{ fontSize: 11 }}>{notice}</Faint> : null}
      </div>

      {panel === "reword" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, border: `1px solid ${COLOR.border}`, padding: 8 }}>
          {textarea(promptDraft, setPromptDraft, "prompt…", 3)}
          {expectedAnswer !== null
            ? textarea(answerDraft, setAnswerDraft, "expected answer…", 3)
            : <Faint style={{ fontSize: 10 }}>the expected answer stays hidden until you answer — edit it from feedback.</Faint>}
          <div style={{ display: "flex", gap: 12 }}>{action("save", () => void reword())}</div>
        </div>
      ) : null}

      {panel === "split" && expectedAnswer !== null ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, border: `1px solid ${COLOR.border}`, padding: 8 }}>
          <Faint style={{ fontSize: 11 }}>the original retires (history kept); each part becomes its own card.</Faint>
          {parts.map((part, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <Faint style={{ fontSize: 10 }}>part {i + 1}</Faint>
              {textarea(part.prompt, (v) => setParts((p) => p.map((x, j) => (j === i ? { ...x, prompt: v } : x))), "prompt…")}
              {textarea(part.expectedAnswer, (v) => setParts((p) => p.map((x, j) => (j === i ? { ...x, expectedAnswer: v } : x))), "expected answer…")}
            </div>
          ))}
          <div style={{ display: "flex", gap: 12 }}>
            {action("split", () => {
              if (parts.some((p) => !p.prompt.trim() || !p.expectedAnswer.trim())) {
                onError("every part needs a prompt and an expected answer.");
                return;
              }
              void split();
            })}
            {action("+ part", () => setParts((p) => [...p, { prompt: "", expectedAnswer: "" }]))}
          </div>
        </div>
      ) : null}

      {panel === "retire" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, border: `1px solid ${COLOR.border}`, padding: 8 }}>
          <Faint style={{ fontSize: 11 }}>nothing is deleted — attempts and evidence stay; it is just never served again.</Faint>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value as RetirementReason)}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}`, padding: 4 }}
          >
            {RETIREMENT_REASONS.map((r) => (
              <option key={r} value={r}>{REASON_LABEL[r]}</option>
            ))}
          </select>
          {textarea(note, setNote, "optional note…", 2)}
          <div style={{ display: "flex", gap: 12 }}>{action("retire this card", () => void retire())}</div>
        </div>
      ) : null}
    </div>
  );
}
