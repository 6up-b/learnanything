// Deliverable curriculum C0b (spec §5.1-§5.4; Codex review F4): making a deliverable from
// the learner's own words, and reviewing what those words resolved to.
//
// * DeliverableEntry: under the Guide's path card while no deliverable names this book:
//   "learning this for something?" opens the form (the learner's sentence, an optional
//   topic list, a deadline, whether it is an exam), and "your deliverables" lists the
//   ones made, each with its scope.
// * DeliverableScopePanel: one line per topic with the phrase of the learner's it answers;
//   the phrases not in the library yet with *add it* / *no* (a topic is created only on the
//   learner's yes); *not this…* and *add…* as text boxes (learner text over delete buttons);
//   the resolution's receipt on demand; "How deep for this?" while it is unanswered.
//
// Display only: the server resolves, validates and writes; this module words the result.
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { DeliverableScopeDto, ReadingPathDepth } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";

const LINK = {
  background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer",
  fontFamily: FONT_MONO, fontSize: 10, textDecoration: "underline",
} as const;
const INPUT = {
  fontFamily: FONT_MONO, fontSize: 10, background: "transparent", color: COLOR.text,
  border: `1px solid ${COLOR.borderStrong}`,
} as const;

/** RW7a's depths (the server's labels; the same three as the path card's). */
export const SCOPE_DEPTHS: Array<{ id: ReadingPathDepth; label: string }> = [
  { id: "get_the_idea", label: "get the idea" },
  { id: "learn_to_use_it", label: "learn to use it" },
  { id: "fluency", label: "fluency" },
];

export const SCOPE_COPY = {
  entry: "learning this for something? ▸",
  yours: (count: number) => (count === 1 ? "your deliverable ▸" : `your ${count} deliverables ▸`),
  sentence: "what you're learning this for, in your own words",
  sentencePlaceholder: "only what's on my midterm: ch 1–4, eigenvalues, no proofs",
  topics: "topics (optional: paste the course page's list)",
  deadline: "deadline (optional)",
  exam: "it's an exam",
  make: "make it ↵",
  cancel: "cancel",
  summary: (title: string, topics: number, missing: number) =>
    `For ${title}: ${topics === 1 ? "1 topic" : `${topics} topics`} from your books`
    + (missing ? ` · ${missing} not in your library yet` : ""),
  notInLibrary: "not in your library yet",
  addIt: "add it",
  no: "no",
  added: "added as a new topic",
  declined: "you said no",
  notThis: "not this…",
  notThisPlaceholder: "not Jordan form; we skipped it",
  add: "add…",
  addPlaceholder: "and the spectral theorem",
  send: "send ↵",
  receipt: "receipt",
  receiptLine: (origin: string, model: string, at: string) =>
    `${origin === "learner" ? "your decision" : `resolved by ${model}`} · ${at.slice(0, 10)}`,
  ask: "How deep for this?",
  nothingYet: "Nothing resolved yet: say what you need below.",
} as const;

/** "For your midterm: 14 topics from your books · 2 not in your library yet". */
export function scopeSummary(scope: DeliverableScopeDto): string {
  return SCOPE_COPY.summary(scope.title, scope.topics.length, scope.unmatched.filter((entry) => entry.status === "open").length);
}

/** A scope RPC's answer the learner should read (superseded, unavailable): its message, else null. */
export function scopeNotice(result: { status: string; message: string | null }): string | null {
  return result.status === "ready" || result.status === "fresh" ? null : (result.message ?? null);
}

export interface DeliverableScopePanelProps {
  scope: DeliverableScopeDto;
  onChanged: (scope: DeliverableScopeDto) => void;
  onError: (message: string) => void;
}

export function DeliverableScopePanel({ scope, onChanged, onError }: DeliverableScopePanelProps) {
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [receipt, setReceipt] = useState(false);
  const [notThis, setNotThis] = useState("");
  const [add, setAdd] = useState("");

  const send = async (kind: "correction" | "text", text: string, clear: () => void) => {
    setBusy(true);
    try {
      const out = await api.curriculumSetScope({ goalId: scope.goalId, kind, text });
      setNotice(scopeNotice(out));
      clear();
      onChanged(out.scope);
    } catch (error) {
      onError(errorMessage(error, "Couldn't send that."));
    } finally {
      setBusy(false);
    }
  };

  const decide = async (phrase: string, decision: "create" | "decline") => {
    setBusy(true);
    try {
      const out = await api.curriculumScopeDecide({ goalId: scope.goalId, phrase, decision });
      setNotice(null);
      onChanged(out.scope);
    } catch (error) {
      onError(errorMessage(error, "Couldn't save that."));
    } finally {
      setBusy(false);
    }
  };

  const setDepth = async (depth: ReadingPathDepth) => {
    setBusy(true);
    try {
      await api.curriculumSetDepth({ goalId: scope.goalId, depth });
      onChanged(await api.curriculumScope({ goalId: scope.goalId }));
    } catch (error) {
      onError(errorMessage(error, "Couldn't save how deep you want to go."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-deliverable-scope={scope.goalId} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
        {scope.resolution ? scopeSummary(scope) : SCOPE_COPY.nothingYet}
      </span>
      {scope.topics.map((topic) => (
        <span key={topic.learningObjectId} data-deliverable-topic={topic.learningObjectId}
          style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
          {topic.title}{topic.phrase ? <span style={{ color: COLOR.textFaint }}> · “{topic.phrase}”</span> : null}
        </span>
      ))}
      {scope.unmatched.map((entry) => (
        <span key={entry.phrase} data-deliverable-unmatched={entry.status}
          style={{ display: "flex", gap: 6, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
          <span>{entry.proposedTitle}? <span style={{ color: COLOR.textFaint }}>{SCOPE_COPY.notInLibrary} · “{entry.phrase}”</span></span>
          {entry.status === "open" ? (
            <>
              <button type="button" style={LINK} disabled={busy} title={entry.proposedStatement}
                onClick={() => void decide(entry.phrase, "create")}>{SCOPE_COPY.addIt}</button>
              <button type="button" style={LINK} disabled={busy} onClick={() => void decide(entry.phrase, "decline")}>{SCOPE_COPY.no}</button>
            </>
          ) : (
            <span style={{ color: COLOR.textFaint }}>{entry.status === "created" ? SCOPE_COPY.added : SCOPE_COPY.declined}</span>
          )}
        </span>
      ))}
      {notice ? <Faint style={{ fontSize: 10 }}>{notice}</Faint> : null}
      <TextBox label={SCOPE_COPY.notThis} placeholder={SCOPE_COPY.notThisPlaceholder} value={notThis} busy={busy}
        onChange={setNotThis} onSend={() => void send("correction", notThis.trim(), () => setNotThis(""))} />
      <TextBox label={SCOPE_COPY.add} placeholder={SCOPE_COPY.addPlaceholder} value={add} busy={busy}
        onChange={setAdd} onSend={() => void send("text", add.trim(), () => setAdd(""))} />
      {scope.resolution && !scope.depth ? (
        <div role="group" aria-label={SCOPE_COPY.ask} style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "baseline" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }}>{SCOPE_COPY.ask}</span>
          {SCOPE_DEPTHS.map((depth) => (
            <button key={depth.id} type="button" style={LINK} disabled={busy} onClick={() => void setDepth(depth.id)}>{depth.label}</button>
          ))}
        </div>
      ) : null}
      {scope.resolution ? (
        <span>
          <button type="button" style={LINK} aria-expanded={receipt} onClick={() => setReceipt((value) => !value)}>
            {SCOPE_COPY.receipt} {receipt ? "▾" : "▸"}
          </button>
          {receipt ? (
            <Faint style={{ fontSize: 10 }}>
              {" "}{SCOPE_COPY.receiptLine(scope.resolution.origin, scope.resolution.model, scope.resolution.createdAt)}
            </Faint>
          ) : null}
        </span>
      ) : null}
    </div>
  );
}

function TextBox({ label, placeholder, value, busy, onChange, onSend }: {
  label: string; placeholder: string; value: string; busy: boolean; onChange: (value: string) => void; onSend: () => void;
}) {
  return (
    <form style={{ display: "flex", gap: 6, alignItems: "baseline" }} onSubmit={(event) => {
      event.preventDefault();
      if (value.trim()) onSend();
    }}>
      <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>{label}</span>
      <input aria-label={label} placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)}
        style={{ ...INPUT, flex: 1 }} />
      <button type="submit" style={LINK} disabled={busy || !value.trim()}>{SCOPE_COPY.send}</button>
    </form>
  );
}

export interface DeliverableEntryProps {
  onError: (message: string) => void;
  /** A deliverable was made or its scope changed: the Guide reads its slice again. */
  onChanged: () => void;
}

/** Under the Guide's path card while no deliverable names this book: make one, or review yours. */
export function DeliverableEntry({ onError, onChanged }: DeliverableEntryProps) {
  const [mode, setMode] = useState<"closed" | "form" | "list">("closed");
  const [busy, setBusy] = useState(false);
  const [sentence, setSentence] = useState("");
  const [topics, setTopics] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [exam, setExam] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [scopes, setScopes] = useState<DeliverableScopeDto[]>([]);

  const load = useCallback(async () => {
    try {
      const out = await api.curriculumDeliverables();
      setScopes(out.deliverables ?? []);
    } catch {
      setScopes([]);  // listed only when it can be read; making one still works
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const replace = (scope: DeliverableScopeDto) => {
    setScopes((current) => {
      const others = current.filter((entry) => entry.goalId !== scope.goalId);
      return [scope, ...others];
    });
    onChanged();
  };

  const make = async () => {
    setBusy(true);
    try {
      const created = await api.curriculumCreateDeliverable({ sentence: sentence.trim(), dueAt: dueAt || null, exam });
      let scope = created.scope;
      let message = scopeNotice(created);
      if (topics.trim()) {
        const listed = await api.curriculumSetScope({ goalId: created.goalId, kind: "topic_list", text: topics.trim() });
        scope = listed.scope;
        message = scopeNotice(listed);
      }
      setNotice(message);
      setSentence(""); setTopics(""); setDueAt(""); setExam(false);
      setMode("list");
      replace(scope);
    } catch (error) {
      onError(errorMessage(error, "Couldn't make that deliverable."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-deliverable-entry={mode} style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
      <span style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" style={LINK} aria-expanded={mode === "form"}
          onClick={() => setMode((value) => (value === "form" ? "closed" : "form"))}>{SCOPE_COPY.entry}</button>
        {scopes.length ? (
          <button type="button" style={LINK} aria-expanded={mode === "list"}
            onClick={() => setMode((value) => (value === "list" ? "closed" : "list"))}>{SCOPE_COPY.yours(scopes.length)}</button>
        ) : null}
      </span>
      {mode === "form" ? (
        <Card style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <form style={{ display: "flex", flexDirection: "column", gap: 4 }} onSubmit={(event) => {
            event.preventDefault();
            if (sentence.trim()) void make();
          }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 2, fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
              {SCOPE_COPY.sentence}
              <textarea aria-label={SCOPE_COPY.sentence} placeholder={SCOPE_COPY.sentencePlaceholder} rows={2} value={sentence}
                onChange={(event) => setSentence(event.target.value)} style={INPUT} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 2, fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
              {SCOPE_COPY.topics}
              <textarea aria-label={SCOPE_COPY.topics} rows={3} value={topics} onChange={(event) => setTopics(event.target.value)} style={INPUT} />
            </label>
            <span style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
              <label>{SCOPE_COPY.deadline}{" "}
                <input aria-label={SCOPE_COPY.deadline} type="date" value={dueAt} onChange={(event) => setDueAt(event.target.value)} style={INPUT} />
              </label>
              <label>
                <input aria-label={SCOPE_COPY.exam} type="checkbox" checked={exam} onChange={(event) => setExam(event.target.checked)} />
                {" "}{SCOPE_COPY.exam}
              </label>
            </span>
            <span style={{ display: "flex", gap: 10 }}>
              <button type="submit" style={LINK} disabled={busy || !sentence.trim()}>{SCOPE_COPY.make}</button>
              <button type="button" style={LINK} onClick={() => setMode("closed")}>{SCOPE_COPY.cancel}</button>
            </span>
          </form>
        </Card>
      ) : null}
      {mode === "list" ? (
        <Card style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {notice ? <Faint style={{ fontSize: 10 }}>{notice}</Faint> : null}
          {scopes.map((scope) => (
            <DeliverableScopePanel key={scope.goalId} scope={scope} onError={onError} onChanged={replace} />
          ))}
        </Card>
      ) : null}
    </div>
  );
}
