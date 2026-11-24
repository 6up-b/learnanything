// The pad's overlays: the pad menu (spec §9.2, its marimo row inserting a cell run in the pad's notebook),
// the arrange overlay (§10.2), and the sheets for submitting a block (§10.9) and making a line into practice.
import { useEffect, useMemo, useRef, useState } from "react";
import type { PadBlockDto, PadBlockKind, PadProvenance } from "../../../api/dto";
import type { MenuObjectInput } from "../../../api/dto";
import { screenLeavesKey } from "../../../app/keymap";
import { useListenerHub, useWindowLifecycle } from "../lifecycle";
import { ContextMenu, useSheetFocus } from "../menu/ContextMenu";
import { MARIMO_CELL_INSERT, MARIMO_CELL_ROW } from "../notebook/menuBridge";
import type { MenuRow } from "../menu/model";
import type { PadsHost } from "./host";
import { isLearnersWords, type PadState } from "./model";

export interface MenuRequest {
  padId: string;
  blockId: string | null;
  blockIds?: string[];
  text: string;
  x: number;
  y: number;
  /** Opened from a notebook frame (spec §11.3): the header's label ("the lesson", "your pad") and the insert row's
   * words; the text is the frame's selection, untrusted notebook text (only ever shown quoted, as text). */
  label?: string;
  insertLabel?: string;
  /** A notebook lesson's menu: its inserts go to the lesson's additions pad, never into the notebook. */
  lessonId?: string | null;
}

type InsertBlock = { kind: PadBlockKind; provenance: PadProvenance; bodyMd?: string; payload?: Record<string, unknown> };

interface Row {
  key: string;
  glyph: string;
  label: string;
  note?: string;
  disabled?: boolean;
  run?: () => void;
}

/** A source piece: the passage's own words as the source has them (whole, not a search label or the page's
 * rendered text), its title, page, section and time apart. A held-out passage is not copied, and says so. */
async function insertPiece(host: PadsHost, onInsert: (block: InsertBlock) => void, extractionId: string, spanId: string): Promise<void> {
  try {
    const content = await host.api.passageContent({ extractionId, fromSpanId: spanId, toSpanId: spanId });
    const span = content.spans.find((each) => each.spanId === spanId) ?? content.spans[0];
    if (content.withheld !== false || !span || span.withheld !== false || span.text === null) {
      host.toast("this passage is held out (exam material): it is not copied into a pad");
      return;
    }
    onInsert({
      kind: "source_piece", provenance: "source", bodyMd: span.text,
      payload: {
        source_id: content.sourceId, source_title: content.title ?? "the source", extraction_id: extractionId, span_id: span.spanId,
        page: span.page, section_label: span.sectionLabel, ...(span.t0 !== null ? { t: span.t0, t_end: span.t1 } : {}),
      },
    });
  } catch (error) {
    host.toast(`couldn't read that passage · ${messageOf(error)}`);
  }
}

/** A block's anchored passages (its links), for Teach me and the LO of a teach-back. */
function anchorsOf(state: PadState | null, blockId: string | null): Array<{ extractionId: string; spanId: string }> {
  if (!state || !blockId) return [];
  const block = state.blocks.find((each) => each.blockId === blockId);
  const fromLinks = state.anchors.filter((anchor) => anchor.blockId === blockId).map((anchor) => ({ extractionId: anchor.extractionId, spanId: anchor.spanId }));
  const p = (block?.payload ?? {}) as Record<string, unknown>;
  if (typeof p.extraction_id === "string" && typeof p.span_id === "string" && !fromLinks.some((each) => each.spanId === p.span_id)) {
    fromLinks.push({ extractionId: p.extraction_id, spanId: p.span_id });
  }
  return fromLinks;
}

/** The pad menu (spec §9.2) in the one context menu: the rows on the line's words, then the inserts, then muting
 * suggestions; its promoted rows come from passage.promoted for the line (its passages are its own links). */
export function PadMenu({ request, host, windowId, state, muted, onClose, onInsert, onNote, onSubmit, onMute }: {
  request: MenuRequest;
  windowId: string;
  host: PadsHost;
  state: PadState | null;
  muted: boolean;
  onClose: () => void;
  onInsert: (block: InsertBlock) => void;
  /** Note in margin on a pad line: a note block attached under it (opened in the editor). */
  onNote: () => void;
  onSubmit: () => void;
  onMute: () => void;
}) {
  const block: PadBlockDto | null = state?.blocks.find((each) => each.blockId === request.blockId) ?? null;
  const blockIds = request.blockIds ?? (request.blockId ? [request.blockId] : []);
  const anchors = anchorsOf(state, request.blockId);
  const pieces = useMemo(() => host.sourcePieces(), [host]);
  const [practicing, setPracticing] = useState(false);
  // A line whose words are about exam or held-out material (its first answer says): nothing sends them on.
  const [withheld, setWithheld] = useState<boolean | null>(null);
  const hub = useListenerHub();
  const text = request.text.trim();
  const close = (then?: () => void) => () => {
    onClose();
    then?.();
  };
  // A press in another window makes it the active one: the menu goes with the focus.
  const lifecycle = useWindowLifecycle();
  useEffect(() => {
    if (lifecycle.state !== "active") onClose();
  }, [lifecycle.state, onClose]);
  const object: MenuObjectInput | null = request.blockId ? { objectKind: "pad_line", blockId: request.blockId, ...(blockIds.length > 1 ? { blockIds } : {}), windowId, ...(host.deskId ? { deskId: host.deskId } : {}) } : null;
  const allTextRows: Row[] = text ? [
    { key: "a", glyph: "?", label: "Ask about this", run: close(() => host.askAbout(text, { padId: request.padId, blockId: request.blockId, blockIds, anchor: anchors[0] ?? null })) },
    ...(request.blockId ? [{ key: "n", glyph: "›", label: "Note in margin", note: "a note attached under this line", run: close(onNote) }] : []),
    { key: "/", glyph: "⌕", label: "Find in my sources", run: close(() => host.openSearch(text, undefined, blockIds)) },
    // A line with no passage has no Show me (the figure is built for a passage).
    ...(host.showMe && anchors.length ? [{ key: "v", glyph: "◇", label: "Show me", note: "make a figure for this line", run: close(() => {
      host.toast("◇ Making a figure for this line…");
      // The finished figure goes to the window's waiting figures: written only while the pad is live.
      void host.showMe?.(text, anchors[0] ?? null, windowId, blockIds).then((figure) => {
        if (!figure) host.toast("No figure was made. Try another line.");
        else host.figures.push(windowId, { padId: request.padId, afterBlockId: request.blockId, blockIds, figureId: figure.figureId, line: figure.line });
      }, () => host.toast("Couldn’t make a figure for this line. Try another line."));
    }) }] : []),
    ...(anchors.length ? [{ key: "p", glyph: "✎", label: "Make it practice", note: "drafts an item from this line for your queue", run: () => setPracticing(true) }] : []),
    { key: "c", glyph: "◌", label: "Save for later", run: close(() => host.carry(text, { kind: "block", ref: request.blockId, blockIds, anchor: anchors[0] ?? null })) },
    // A lesson is on one reading: the line's passages in its first linked reading (span ids repeat across books).
    ...(anchors.length && host.teachMe ? [{ key: "t", glyph: "◎", label: "Teach me this", run: close(() => host.teachMe?.(anchors[0].extractionId,
      anchors.filter((each) => each.extractionId === anchors[0].extractionId).map((each) => each.spanId), blockIds)) }] : []),
    ...(block && isLearnersWords(block) ? [{ key: "s", glyph: "✓", label: "Submit this block as…", run: close(onSubmit) }] : []),
  ] : [];
  // On exam or held-out material the rows that would send the line's words on (the tutor, a search, a figure,
  // practice, a carried question, a lesson) are left out, as a protected passage is never copied into a pad.
  const textRows = withheld !== false ? allTextRows.filter((row) => row.key === "n") : allTextRows;
  const insertRows: Row[] = [
    // §9.2 gives this row the letter k, but an open menu's j/k move the selection (§5.4's matrix): moving
    // wins, so the row is chosen with ↑↓ ↵ (or alt+d from the pad) and shows no letter.
    { key: "sketch", glyph: "✎", label: "Sketch cell", note: "pen, line, arrow, box, text · yours", run: close(() => onInsert({ kind: "sketch", provenance: "learner", payload: { width: 480, height: 160, items: [] } })) },
    { ...MARIMO_CELL_ROW, run: close(() => onInsert(MARIMO_CELL_INSERT)) },
    ...pieces.map((piece, index): Row => ({
      key: index === 0 ? "i" : `piece-${index}`,
      glyph: piece.t !== undefined ? "▶" : "§",
      label: piece.label,
      run: close(() => void insertPiece(host, onInsert, piece.extractionId, piece.spanId)),
    })),
    { key: "o", glyph: "⌕", label: "a piece of another source…", run: close(() => host.openSearch("", (row) => {
      // A piece is a passage: a whole source (or a pad, a thread) is not one.
      const spanId = row.kind === "result" ? row.target?.spanId : undefined;
      if (row.kind !== "result" || !row.ref || (row.ref.kind !== "source" && row.ref.kind !== "video") || !spanId) {
        host.toast("choose a passage (or a moment of a video) to put a piece of it here");
        return;
      }
      void insertPiece(host, onInsert, row.ref.extractionId, spanId);
    })) },
  ];
  const tailRows: Row[] = [
    ...(request.blockId && host.menu ? [{ key: "knows", glyph: "i", label: "What this knows", run: close(() => host.menu?.knows({ objectKind: "pad_line", blockId: request.blockId as string, blockIds, windowId })) }] : []),
    ...(request.lessonId ? [] : [{ key: "u", glyph: "◇", label: muted ? "show LearnLoop's suggestions on this pad" : "mute LearnLoop's suggestions on this pad", run: close(onMute) }]),
  ];
  const toRow = (section: MenuRow["section"]) => (row: Row): MenuRow => ({
    id: row.key, glyph: row.glyph, label: row.label, note: row.note, disabled: row.disabled, run: row.run, section,
    ...(row.key.length === 1 ? { key: row.key } : {}),
    ...(row.key === "knows" ? { aid: true } : {}),
  });
  const rows: MenuRow[] = [...textRows.map(toRow("verb")), ...insertRows.map(toRow("insert")), ...tailRows.map(toRow("tail"))];
  return (
    <ContextMenu
      label="the pad menu"
      neutralHeader={request.label ?? "your pad"}
      header={withheld === null ? request.label ?? "your pad" : withheld ? `${request.label ?? "your pad"} · about exam or held-out material` : `${request.label ?? "your pad"} · “${(text || "this line").replace(/\s+/g, " ").slice(0, 46)}${text.length > 46 ? "…" : ""}”`}
      rows={rows}
      at={{ x: request.x, y: request.y }}
      object={object}
      promoted={host.menu?.promoted ?? null}
      onPromoted={host.menu?.onPromoted}
      onWithheld={setWithheld}
      poller={host.menu?.poller}
      owner={windowId}
      insertHeading={request.insertLabel ?? (request.blockId ? "insert below this line" : "insert at the end of this pad")}
      onClose={onClose}
      listen={(target, type, handler, capture) => hub.listen(target, type, handler, capture)}
    >
      {practicing && withheld === false && state && block ? <PracticeSheet host={host} blockIds={blockIds} text={text} anchors={anchors} onClose={onClose} /> : undefined}
    </ContextMenu>
  );
}

function PracticeSheet({ host, blockIds, text, anchors, onClose }: { host: PadsHost; blockIds: string[]; text: string; anchors: Array<{ extractionId: string; spanId: string }>; onClose: () => void }) {
  const [prompt, setPrompt] = useState(text);
  const [answer, setAnswer] = useState("");
  const [los, setLos] = useState<string[] | null>(null);
  const [lo, setLo] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  // One save at a time: a second press while the first is on its way would author a second item.
  const [saving, setSaving] = useState(false);
  // One key per sheet, sent with every save of it: a retry after a lost reply returns the same item.
  const [authoringKey] = useState(() => host.mintId("pi"));
  const node = useRef<HTMLDivElement | null>(null);
  useSheetFocus(node, onClose);
  useEffect(() => {
    let live = true;
    const first = anchors[0];
    if (!first) return;
    host.api.passageUnionRange({ extractionId: first.extractionId, fromSpanId: first.spanId, toSpanId: first.spanId }).then((union) => {
      if (!live) return;
      const ids = [...new Set(union.sections.flatMap((section) => section.learningObjects.map((each) => each.learningObjectId)))];
      setLos(ids);
      setLo(ids[0] ?? null);
    }, () => live && setLos([]));
    return () => {
      live = false;
    };
  }, [anchors, host]);
  return (
    <div ref={node} tabIndex={-1} className="desk-sheet" role="dialog" aria-label="make it practice">
      <div className="head">✎ make it practice · it joins your queue once you save it</div>
      <label>the question<textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} /></label>
      <label>what a right answer says<textarea value={answer} onChange={(event) => setAnswer(event.target.value)} /></label>
      {los === null ? <div className="note">◐ finding what this passage teaches…</div> : los.length === 0 ? <div className="note">No topic to show. Try again or choose another passage.</div> : (
        <div className="note">for {los.length === 1 ? "the idea this passage teaches" : <select aria-label="Choose a topic" value={lo ?? ""} onChange={(event) => setLo(event.target.value)}>{los.map((id, index) => <option key={id} value={id}>Topic {index + 1}</option>)}</select>}</div>
      )}
      {failure ? <div className="note err">{failure}</div> : null}
      <div className="acts">
        <button type="button" disabled={saving || !lo || !prompt.trim() || !answer.trim()} onClick={() => {
          if (!lo || saving) return;
          setSaving(true);
          setFailure(null);
          void host.api.authorPracticeItem({ blockIds, learningObjectId: lo, prompt: prompt.trim(), expectedAnswer: answer.trim(), clientIdempotencyKey: authoringKey }).then(() => {
            host.toast("added to your queue");
            onClose();
          }, (error: unknown) => {
            setSaving(false);
            setFailure(messageOf(error));
          });
        }}>{saving ? "saving…" : "save to my queue"}</button>
        <button type="button" onClick={onClose}>not now</button>
      </div>
    </div>
  );
}

function messageOf(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) return String((error as { message: unknown }).message);
  return String(error);
}

export function ArrangeOverlay({ pads, split, onCancel, onConfirm }: {
  pads: Array<{ padId: string; title: string; line?: string }>;
  split: { pads: string[] } | null;
  onCancel: () => void;
  onConfirm: (shown: string[]) => void;
}) {
  const [order, setOrder] = useState(pads.map((pad) => pad.padId));
  const [shown, setShown] = useState<Set<string>>(new Set(split?.pads ?? pads.slice(0, 2).map((pad) => pad.padId)));
  const [index, setIndex] = useState(0);
  const [again, setAgain] = useState(split === null);
  const hub = useListenerHub();
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // A modal overlay: it owns the keyboard while it is open, but never a chord.
      if (screenLeavesKey(event, { modal: true }) || event.altKey || event.ctrlKey || event.metaKey) return;
      if (!again) {
        if (event.key === "Enter") {
          event.preventDefault();
          onConfirm([]);
        } else if (event.key === "a") {
          event.preventDefault();
          setAgain(true);
        } else if (event.key === "Escape") onCancel();
        return;
      }
      const id = order[index];
      if (event.key === "ArrowDown") setIndex((now) => Math.min(order.length - 1, now + 1));
      else if (event.key === "ArrowUp") setIndex((now) => Math.max(0, now - 1));
      else if (event.key === "k" && index > 0) {
        setOrder((now) => {
          const next = [...now];
          [next[index - 1], next[index]] = [next[index], next[index - 1]];
          return next;
        });
        setIndex(index - 1);
      } else if (event.key === "j" && index < order.length - 1) {
        setOrder((now) => {
          const next = [...now];
          [next[index + 1], next[index]] = [next[index], next[index + 1]];
          return next;
        });
        setIndex(index + 1);
      } else if (event.key === " ") {
        setShown((now) => {
          const next = new Set(now);
          if (next.has(id)) next.delete(id);
          else if (next.size < 3) next.add(id);
          return next;
        });
      } else if (event.key === "=") {
        // Equal heights is what a fresh split has; nothing to keep here.
      } else if (event.key === "Enter") onConfirm(order.filter((padId) => shown.has(padId)));
      else if (event.key === "Escape") onCancel();
      else return;
      event.preventDefault();
    };
    return hub.listen("window", "keydown", onKey);
  }, [again, hub, index, onCancel, onConfirm, order, shown]);
  const titles = new Map(pads.map((pad) => [pad.padId, pad.title]));
  const lines = new Map(pads.map((pad) => [pad.padId, pad.line ?? ""]));
  if (!again) {
    return (
      <div className="desk-arrange" role="dialog" aria-label="arrange pads">
        <div className="head">ARRANGE · pads above and below each other</div>
        <button type="button" className="row" onClick={() => onConfirm([])}>↵ back to one at a time</button>
        <button type="button" className="row" onClick={() => setAgain(true)}>a · arrange again</button>
      </div>
    );
  }
  return (
    <div className="desk-arrange" role="dialog" aria-label="arrange pads">
      <div className="head">ARRANGE · pads above and below each other</div>
      {order.map((padId, i) => (
        <button key={padId} type="button" className={`row${i === index ? " sel" : ""}`} onClick={() => {
          setIndex(i);
          setShown((now) => {
            const next = new Set(now);
            if (next.has(padId)) next.delete(padId);
            else if (next.size < 3) next.add(padId);
            return next;
          });
        }}>
          <span className="dot" title={shown.has(padId) ? "Pad shown" : "Pad hidden"}>{shown.has(padId) ? "●" : "○"}</span>
          <span className="txt"><span className="t">{titles.get(padId)}</span>{lines.get(padId) ? <span className="ln">{lines.get(padId)}</span> : null}</span>
        </button>
      ))}
      <div className="foot">↑↓ (Up/Down arrows) to choose · K above · J below · Space to show · = (Equals) for equal heights · ↵ (Enter) to confirm · Esc to cancel</div>
    </div>
  );
}

/** A submission in flight, frozen at its first try: a retry (its reply was lost, the sidecar was away) resends the
 * very same request (id, version, target), so the server's idempotency holds and nothing is recorded twice. A new
 * request is made only for a new submission: after this one is recorded, or once the block's words have changed. */
interface FrozenSubmission {
  submissionId: string;
  versionId: string;
  as: "attempt" | "teach_back";
  practiceItemId: string;
}

const FROZEN = new WeakMap<object, Map<string, FrozenSubmission>>();

function frozenFor(store: object): Map<string, FrozenSubmission> {
  let map = FROZEN.get(store);
  if (!map) {
    map = new Map();
    FROZEN.set(store, map);
  }
  return map;
}

/** A teach-back's open question, from the entry point's reply or from the session's checkpoint. */
interface TeachBackTurn {
  practiceItemId: string;
  questionMd: string;
}

type StoredTeachBackState = { practice_item_id?: string; practiceItemId?: string; turns?: Array<{ role?: string; content_md?: string; contentMd?: string }> };

/** The pending follow-up question of a teach-back's stored state (keys as stored), if its last turn is the tutor's. */
export function stateQuestion(state: StoredTeachBackState | null | undefined, practiceItemId: string): string | null {
  if (!state) return null;
  const item = state.practice_item_id ?? state.practiceItemId;
  if (item !== undefined && item !== practiceItemId) return null;
  const last = state.turns?.[state.turns.length - 1];
  return last && last.role === "ai" ? last.content_md ?? last.contentMd ?? null : null;
}

/** The same, from a session checkpoint's current answer (an older sidecar's only record of it). */
export function pendingTeachBackQuestion(currentAnswer: string | null | undefined, practiceItemId: string): string | null {
  if (!currentAnswer) return null;
  try {
    const envelope = JSON.parse(currentAnswer) as { mode?: string; state?: StoredTeachBackState };
    return envelope.mode === "teach_back" ? stateQuestion(envelope.state, practiceItemId) : null;
  } catch {
    return null;
  }
}

/** "Submit this block as…" (spec §10.9): my answer to the problem pad's item or the check cell's, or a teach-back
 * of the idea of a passage the block is linked to. Only the learner's own words; the server refuses quoted text.
 * A teach-back that asks a follow-up goes on here, turn by turn, until it is graded. */
export function SubmitSheet({ host, state, blockId, onClose }: { host: PadsHost; state: PadState | null; blockId: string; onClose: () => void }) {
  const block = state?.blocks.find((each) => each.blockId === blockId) ?? null;
  const [answerItem, setAnswerItem] = useState<string | null>(null);
  const [los, setLos] = useState<string[]>([]);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [turn, setTurn] = useState<TeachBackTurn | null>(null);
  const [reply, setReply] = useState("");
  const anchors = anchorsOf(state, blockId);
  useEffect(() => {
    let live = true;
    if (!state || !block) return;
    const p = block.payload as Record<string, unknown>;
    if (block.kind === "check_cell" && typeof p.practice_item_id === "string") setAnswerItem(p.practice_item_id);
    else if (state.pad.kind === "problem" && state.pad.workbenchSessionId) {
      void host.api.workbenchOpenProblems().then((out) => {
        const found = out.problems.find((problem) => problem.sessionId === state.pad.workbenchSessionId);
        if (live) setAnswerItem(found?.practiceItemId ?? null);
      }, () => undefined);
    }
    const first = anchors[0];
    if (first) {
      void host.api.passageUnionRange({ extractionId: first.extractionId, fromSpanId: first.spanId, toSpanId: first.spanId }).then((union) => {
        if (live) setLos([...new Set(union.sections.flatMap((section) => section.learningObjects.map((each) => each.learningObjectId)))]);
      }, () => undefined);
    }
    return () => {
      live = false;
    };
    // Read once for the block the sheet opened on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blockId]);
  if (!state || !block) return null;
  const padId = state.pad.padId;

  const submit = async (as: "attempt" | "teach_back", key: string, item: () => Promise<string>) => {
    const sessionId = host.practiceSessionId;
    if (!sessionId) {
      setFailure("Open Practice to start a session, then return to this pad.");
      return;
    }
    setBusy(true);
    setFailure(null);
    const frozen = frozenFor(host.store);
    const slot = `${padId}|${blockId}|${as}|${key}`;
    try {
      // The block's words must be saved before they are submitted (the server freezes that version).
      await host.store.flush();
      const current = host.store.pads[padId]?.blocks.find((each) => each.blockId === blockId) ?? block;
      let request = frozen.get(slot);
      if (!request || request.versionId !== current.headVersionId) {
        // A new submission (first try, or new words): its target is asked for once and kept with it.
        request = { submissionId: host.mintId("sub"), versionId: current.headVersionId, as, practiceItemId: await item() };
        frozen.set(slot, request);
      }
      const answered = await host.api.padSubmitBlock({
        submissionId: request.submissionId, blockId, versionId: request.versionId, as, target: { sessionId, practiceItemId: request.practiceItemId },
      });
      frozen.delete(slot);
      host.store.noteSubmission(padId, blockId, { submissionId: answered.submissionId, versionId: answered.versionId, as: answered.as, practiceItemId: answered.practiceItemId, attemptId: answered.attemptId, teachBackId: answered.teachBackId, createdAt: new Date().toISOString(), current: true });
      if (as === "teach_back") {
        const entry = answered.entry as { done?: boolean; questionMd?: string } | null;
        let question: string | null = entry && entry.done === false ? entry.questionMd ?? null : null;
        // Recorded before (its reply was lost): the conversation the submission reserved says whether it goes on.
        if (!question && answered.teachBack?.status === "ongoing") question = stateQuestion(answered.teachBack.state as StoredTeachBackState | null, answered.practiceItemId);
        // An older sidecar without it: the session's checkpoint.
        if (!question && !entry && answered.duplicate && answered.teachBack === undefined) {
          const session = await host.api.getSession(sessionId).catch(() => null);
          question = pendingTeachBackQuestion(session?.checkpoint?.currentAnswer, answered.practiceItemId);
        }
        if (question) {
          setTurn({ practiceItemId: answered.practiceItemId, questionMd: question });
          return;
        }
      }
      host.toast(as === "attempt" ? "submitted as your answer" : "submitted as a teach-back");
      onClose();
    } catch (error) {
      setFailure(messageOf(error));
    } finally {
      setBusy(false);
    }
  };

  const answerTurn = async (finish: boolean) => {
    const sessionId = host.practiceSessionId;
    if (!turn || !sessionId) return;
    setBusy(true);
    setFailure(null);
    try {
      const next = await host.api.submitTeachBackTurn({ sessionId, practiceItemId: turn.practiceItemId, answerMd: reply.trim(), ...(finish ? { finish: true } : {}) });
      setReply("");
      if (next.done === false) {
        setTurn({ practiceItemId: turn.practiceItemId, questionMd: next.questionMd });
        return;
      }
      host.toast("teach-back finished · it is graded as any teach-back");
      onClose();
    } catch (error) {
      // The conversation stays in the session; the answer typed stays here to send again.
      setFailure(messageOf(error));
    } finally {
      setBusy(false);
    }
  };

  if (turn) {
    return (
      <div className="desk-sheet" role="dialog" aria-label="submit this block">
        <div className="head">◎ teach-back · the tutor asks, as a student would</div>
        <div className="note q">{turn.questionMd}</div>
        <label>your answer<textarea aria-label="your answer" value={reply} onChange={(event) => setReply(event.target.value)} /></label>
        {failure ? <div className="note err">{failure} Your draft is still here. Select Answer to try again.</div> : null}
        <div className="acts">
          <button type="button" disabled={busy || !reply.trim()} onClick={() => void answerTurn(false)}>answer</button>
          <button type="button" disabled={busy} onClick={() => void answerTurn(true)}>finish now</button>
          <button type="button" onClick={onClose}>later</button>
        </div>
      </div>
    );
  }
  return (
    <div className="desk-sheet" role="dialog" aria-label="submit this block">
      <div className="head">✓ submit this block as… · only your own words count</div>
      {answerItem ? <button type="button" className="row" disabled={busy} onClick={() => void submit("attempt", answerItem, async () => answerItem)}>my answer to {state.pad.kind === "problem" ? "this problem" : "this check"}</button> : null}
      {los.map((lo, index) => (
        <button key={lo} type="button" className="row" disabled={busy} onClick={() => void submit("teach_back", lo, async () => (await host.api.requestTeachBack({ learningObjectId: lo })).practiceItemId)}>a teach-back of the idea this passage teaches{los.length > 1 ? ` · Topic ${index + 1}` : ""}</button>
      ))}
      {!answerItem && los.length === 0 ? <div className="note">Copy a passage into this pad, or open the pad for the question you’re answering.</div> : null}
      {failure ? <div className="note err">{failure}</div> : null}
      <div className="acts"><button type="button" onClick={onClose}>not now</button></div>
    </div>
  );
}
