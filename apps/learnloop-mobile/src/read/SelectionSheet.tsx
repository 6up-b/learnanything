// The selection sheet (mobile v2 §3.5): on release of a selection in the text, Ask, Save and Copy, from the
// bottom, never over the selection. Ask is the desktop's `reader.ask` on the selected passages' spans, as a
// job (D2: the desktop's routes and budgets); its answer opens here, in the three voices (§ the book, ◇ the
// model, › you). Nothing about protection is decided here: a selection on what the reading holds out offers no
// Ask (the desktop's rule), and the host refuses it anyway, as it refuses an Ask during a check on your own.
import { useRef, useState } from "react";
import type { CommandError, ReaderAnswerDto } from "@desktop/api/dto";
import { phone, type PhoneSectionDto } from "../api/phone";
import { Sheet } from "../shell/Sheet";
import { newUlid } from "../util/ulid";
import { PhoneMarkdown } from "./PageImage";

export interface PhoneSelection {
  readonly spanIds: string[];
  readonly quote: string;
}

type Intent = "explain" | "alternative" | "remediate";

interface Turn {
  readonly question: string;
  readonly answer: ReaderAnswerDto | null;
  readonly intent: Intent;
}

/** A `keep` bound on the quote the sheet shows and sends: the desktop's own selection quote length. */
const QUOTE_LIMIT = 2000;

function refusalLine(error: unknown): string {
  const command = error as CommandError | undefined;
  switch (command?.code) {
    case "cold_check_open":
    case "held_out_material":
    case "question_limit_reached":
      return command.message;
    case "provider_unavailable":
      return "Ask isn't available right now. Try again in a moment.";
    case "desktop_offline":
      return "The desktop isn't reachable. Ask works when it is.";
    default:
      return "That didn't work. Try again.";
  }
}

export function SelectionSheet({
  selection,
  section,
  askOff,
  protectionMessage,
  onClose,
  onError
}: {
  selection: PhoneSelection;
  section: PhoneSectionDto;
  /** The selection touches what the reading holds out: no Ask is offered. */
  askOff: boolean;
  protectionMessage: string | null;
  onClose: () => void;
  onError: (error: unknown) => void;
}) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [thinking, setThinking] = useState(false);
  const [line, setLine] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const closed = useRef(false);
  const quote = selection.quote.slice(0, QUOTE_LIMIT);

  async function ask(intent: Intent, text: string) {
    const asked = text.trim() || (intent === "alternative" ? "Explain it another way." : intent === "remediate" ? "That didn't help." : "");
    if (!asked || thinking) return;
    setThinking(true);
    setLine(null);
    const parent = [...turns].reverse().find((turn) => turn.answer)?.answer ?? null;
    try {
      const answer = await phone.ask({
        extractionId: section.extractionId, spanId: selection.spanIds[0], selectionSpanIds: selection.spanIds,
        selectionQuote: quote, question: asked, retrievalIntent: intent,
        ...(intent !== "explain" && parent?.readerAnswerEventId ? { parentExchangeId: parent.readerAnswerEventId } : {})
      }, newUlid(), { isCancelled: () => closed.current });
      setTurns((list) => [...list, { question: asked, answer, intent }]);
      setQuestion("");
    } catch (error) {
      if ((error as CommandError)?.code !== "cancelled") setLine(refusalLine(error));
    } finally {
      setThinking(false);
    }
  }

  async function save() {
    try {
      await phone.save({
        sourceId: section.sourceId, revisionId: section.revisionId, extractionId: section.extractionId,
        clientIdempotencyKey: newUlid(), renderViewId: section.renderViewId,
        rawSelection: { nodes: selection.spanIds.map((spanId, index) => ({ spanId, quote: index === 0 ? quote : "" })) }
      });
      setSaved(true);
    } catch (error) {
      setLine(refusalLine(error));
      onError(error);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard?.writeText(quote);
      setLine("Copied.");
    } catch {
      setLine("Copying isn't allowed here.");
    }
  }

  const answered = turns.some((turn) => turn.answer);
  return (
    <Sheet title="Selected passage" onClose={() => { closed.current = true; onClose(); }}>
      <blockquote className="voice-book"><span aria-hidden="true">§ </span>{quote}</blockquote>
      {turns.map((turn, index) => (
        <div key={index} className="turn">
          <p className="voice-you"><span aria-hidden="true">› </span>{turn.question}</p>
          {turn.answer ? (
            <div className="voice-model markdown"><span aria-hidden="true">◇ </span><PhoneMarkdown value={turn.answer.answerMd} /></div>
          ) : null}
        </div>
      ))}
      {thinking ? <p className="dim" role="status">Thinking…</p> : null}
      {line ? <p className="dim" role="status">{line}</p> : null}
      {askOff ? (
        <p className="dim">{protectionMessage ?? "This passage is held out of LearnLoop's models."}</p>
      ) : (
        <>
          <label htmlFor="ask-question">Your question</label>
          <textarea id="ask-question" rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} />
          <div className="chips" aria-label="Ask">
            <button className="primary" type="button" disabled={thinking || !question.trim()} onClick={() => void ask("explain", question)}>Ask</button>
            {answered ? (
              <>
                <button className="plain" type="button" disabled={thinking} onClick={() => void ask("alternative", question)}>Another way</button>
                <button className="plain" type="button" disabled={thinking} onClick={() => void ask("remediate", question)}>That didn't help</button>
              </>
            ) : null}
          </div>
        </>
      )}
      <div className="row">
        <button className="plain" type="button" disabled={saved} onClick={() => void save()}>{saved ? "Saved" : "Save"}</button>
        <button className="plain" type="button" onClick={() => void copy()}>Copy</button>
      </div>
    </Sheet>
  );
}
