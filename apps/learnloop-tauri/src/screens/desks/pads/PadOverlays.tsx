// The pad's overlays: the pad menu (spec §9.2, all rows but marimo's, which says it arrives with notebooks),
// the arrange overlay (§10.2), and the sheets for submitting a block (§10.9) and making a line into practice.
import { useEffect, useMemo, useState } from "react";
import type { PadBlockDto, PadBlockKind, PadProvenance } from "../../../api/dto";
import type { PadsHost } from "./host";
import { isLearnersWords, type PadState } from "./model";

export interface MenuRequest {
  padId: string;
  blockId: string | null;
  text: string;
  x: number;
  y: number;
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

export function PadMenu({ request, host, state, muted, onClose, onInsert, onSubmit, onMute }: {
  request: MenuRequest;
  host: PadsHost;
  state: PadState | null;
  muted: boolean;
  onClose: () => void;
  onInsert: (block: InsertBlock) => void;
  onSubmit: () => void;
  onMute: () => void;
}) {
  const block: PadBlockDto | null = state?.blocks.find((each) => each.blockId === request.blockId) ?? null;
  const anchors = anchorsOf(state, request.blockId);
  const pieces = useMemo(() => host.sourcePieces(), [host]);
  const [practicing, setPracticing] = useState(false);
  const text = request.text.trim();
  const close = (then?: () => void) => () => {
    onClose();
    then?.();
  };
  const textRows: Row[] = text ? [
    { key: "a", glyph: "?", label: "Ask about this", run: close(() => host.askAbout(text)) },
    { key: "/", glyph: "⌕", label: "Find in my sources", run: close(() => host.openSearch(text)) },
    ...(host.showMe ? [{ key: "v", glyph: "◇", label: "Show me", note: "a figure lands below this line", run: close(() => {
      host.toast("◇ making a figure for this line · it lands below it when it's ready");
      void host.showMe?.(text, anchors[0] ?? null).then((figure) => {
        if (!figure) host.toast("no figure for this line · nothing was shown");
        else onInsert({ kind: "figure", provenance: "learnloop", bodyMd: figure.line, payload: { figure_id: figure.figureId } });
      }, () => host.toast("couldn't make a figure for this line"));
    }) }] : []),
    ...(anchors.length ? [{ key: "p", glyph: "✎", label: "Make it practice", note: "drafts an item from this line for your queue", run: () => setPracticing(true) }] : []),
    { key: "c", glyph: "◌", label: "Carry", run: close(() => host.carry(text, { kind: "block", ref: request.blockId, anchor: anchors[0] ?? null })) },
    ...(anchors.length && host.teachMe ? [{ key: "t", glyph: "◎", label: "Teach me this", run: close(() => host.teachMe?.(anchors[0].extractionId, anchors.map((each) => each.spanId))) }] : []),
    ...(block && isLearnersWords(block) ? [{ key: "s", glyph: "✓", label: "Submit this block as…", run: close(onSubmit) }] : []),
  ] : [];
  const insertRows: Row[] = [
    { key: "k", glyph: "✎", label: "Sketch cell", note: "pen, line, arrow, box, text · yours", run: close(() => onInsert({ kind: "sketch", provenance: "learner", payload: { width: 480, height: 160, items: [] } })) },
    { key: "m", glyph: "◆", label: "marimo cell · arrives with notebooks", disabled: true },
    ...pieces.map((piece, index): Row => ({
      key: index === 0 ? "i" : `piece-${index}`,
      glyph: piece.t !== undefined ? "▶" : "§",
      label: piece.label,
      run: close(() => onInsert({ kind: "source_piece", provenance: "source", bodyMd: piece.text, payload: { source_title: piece.sourceTitle, extraction_id: piece.extractionId, span_id: piece.spanId, ...(piece.t !== undefined ? { t: piece.t } : {}) } })),
    })),
    { key: "o", glyph: "⌕", label: "a piece of another source…", run: close(() => host.openSearch("", (row) => {
      if (row.kind !== "result" || !row.ref || (row.ref.kind !== "source" && row.ref.kind !== "video")) return;
      onInsert({ kind: "source_piece", provenance: "source", bodyMd: row.text, payload: { source_title: row.text.split(" · ")[0], extraction_id: row.ref.extractionId, span_id: row.target?.spanId ?? null } });
    })) },
  ];
  const rows = [...textRows, ...insertRows, { key: "u", glyph: "◇", label: muted ? "show LearnLoop's suggestions on this pad" : "mute LearnLoop's suggestions on this pad", run: close(onMute) }];
  const runnable = rows.filter((row) => !row.disabled);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (practicing) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      } else if (event.key === "ArrowDown" || event.key === "j") {
        event.preventDefault();
        setIndex((now) => Math.min(runnable.length - 1, now + 1));
      } else if (event.key === "ArrowUp" || event.key === "k") {
        event.preventDefault();
        setIndex((now) => Math.max(0, now - 1));
      } else if (event.key === "Enter") {
        event.preventDefault();
        runnable[index]?.run?.();
      } else {
        const row = runnable.find((each) => each.key === event.key);
        if (row) {
          event.preventDefault();
          row.run?.();
        }
      }
    };
    const onDown = (event: MouseEvent) => {
      if (!(event.target as Element).closest?.(".desk-padmenu, .desk-sheet")) onClose();
    };
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [index, onClose, practicing, runnable]);

  if (practicing && state && block) {
    return <PracticeSheet host={host} text={text} anchors={anchors} onClose={onClose} />;
  }
  const rowView = (row: Row) => {
    const selected = runnable[index] === row;
    return (
      <button key={row.key} type="button" className={`row${selected ? " sel" : ""}`} disabled={row.disabled} onClick={row.run} onMouseEnter={() => {
        const at = runnable.indexOf(row);
        if (at >= 0) setIndex(at);
      }}>
        <span className="g">{row.glyph}</span>
        <span className="l">{row.label}{row.note ? <span className="n"> · {row.note}</span> : null}</span>
        <span className="k">{row.key.length === 1 ? row.key : ""}</span>
      </button>
    );
  };
  return (
    <div className="desk-padmenu" role="menu" aria-label="the pad menu" style={{ left: Math.min(request.x, window.innerWidth - 340), top: Math.min(request.y, window.innerHeight - 420) }}>
      <div className="head">your pad · “{(text || "this line").slice(0, 46)}”</div>
      {textRows.map(rowView)}
      <div className="sep">{request.blockId ? "INSERT BELOW THIS LINE" : "INSERT AT THE END OF THIS PAD"}</div>
      {insertRows.map(rowView)}
      <div className="sep" />
      {rowView(rows[rows.length - 1])}
    </div>
  );
}

function PracticeSheet({ host, text, anchors, onClose }: { host: PadsHost; text: string; anchors: Array<{ extractionId: string; spanId: string }>; onClose: () => void }) {
  const [prompt, setPrompt] = useState(text);
  const [answer, setAnswer] = useState("");
  const [los, setLos] = useState<string[] | null>(null);
  const [lo, setLo] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
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
    <div className="desk-sheet" role="dialog" aria-label="make it practice">
      <div className="head">✎ make it practice · it joins your queue once you save it</div>
      <label>the question<textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} /></label>
      <label>what a right answer says<textarea value={answer} onChange={(event) => setAnswer(event.target.value)} /></label>
      {los === null ? <div className="note">◐ finding what this passage teaches…</div> : los.length === 0 ? <div className="note">this passage is tied to nothing to practise yet</div> : (
        <div className="note">for {los.length === 1 ? "the idea this passage teaches" : <select value={lo ?? ""} onChange={(event) => setLo(event.target.value)}>{los.map((id) => <option key={id} value={id}>{id}</option>)}</select>}</div>
      )}
      {failure ? <div className="note err">{failure}</div> : null}
      <div className="acts">
        <button type="button" disabled={!lo || !prompt.trim() || !answer.trim()} onClick={() => {
          if (!lo) return;
          void host.api.authorPracticeItem({ learningObjectId: lo, prompt: prompt.trim(), expectedAnswer: answer.trim() }).then(() => {
            host.toast("added to your queue");
            onClose();
          }, (error: unknown) => setFailure(messageOf(error)));
        }}>save to my queue</button>
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
  pads: Array<{ padId: string; title: string }>;
  split: { pads: string[] } | null;
  onCancel: () => void;
  onConfirm: (shown: string[]) => void;
}) {
  const [order, setOrder] = useState(pads.map((pad) => pad.padId));
  const [shown, setShown] = useState<Set<string>>(new Set(split?.pads ?? pads.slice(0, 2).map((pad) => pad.padId)));
  const [index, setIndex] = useState(0);
  const [again, setAgain] = useState(split === null);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
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
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [again, index, onCancel, onConfirm, order, shown]);
  const titles = new Map(pads.map((pad) => [pad.padId, pad.title]));
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
          {shown.has(padId) ? "●" : "○"} {titles.get(padId)}
        </button>
      ))}
      <div className="foot">↑↓ choose · k above · j below · space show · = equal · ↵ confirm · esc cancel</div>
    </div>
  );
}

/** "Submit this block as…" (spec §10.9): my answer to the problem pad's item or the check cell's, or a teach-back
 * of the idea of a passage the block is linked to. Only the learner's own words; the server refuses quoted text. */
export function SubmitSheet({ host, state, blockId, onClose }: { host: PadsHost; state: PadState | null; blockId: string; onClose: () => void }) {
  const block = state?.blocks.find((each) => each.blockId === blockId) ?? null;
  const [answerItem, setAnswerItem] = useState<string | null>(null);
  const [los, setLos] = useState<string[]>([]);
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
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
  const submit = async (as: "attempt" | "teach_back", item: () => Promise<string>) => {
    const sessionId = host.practiceSessionId;
    if (!sessionId) {
      setFailure("start a practice session first: a submission is recorded in it, as any attempt is");
      return;
    }
    setBusy(true);
    try {
      // The block's words must be saved before they are submitted (the server freezes that version).
      await host.store.flush();
      const current = host.store.pads[state.pad.padId]?.blocks.find((each) => each.blockId === blockId) ?? block;
      const practiceItemId = await item();
      const reply = await host.api.padSubmitBlock({ submissionId: host.mintId("sub"), blockId, versionId: current.headVersionId, as, target: { sessionId, practiceItemId } });
      host.store.noteSubmission(state.pad.padId, blockId, { submissionId: reply.submissionId, versionId: reply.versionId, as: reply.as, practiceItemId: reply.practiceItemId, attemptId: reply.attemptId, teachBackId: reply.teachBackId, createdAt: new Date().toISOString(), current: true });
      host.toast(as === "attempt" ? "submitted as your answer" : "submitted as a teach-back");
      onClose();
    } catch (error) {
      setFailure(messageOf(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="desk-sheet" role="dialog" aria-label="submit this block">
      <div className="head">✓ submit this block as… · only your own words count</div>
      {answerItem ? <button type="button" className="row" disabled={busy} onClick={() => void submit("attempt", async () => answerItem)}>my answer to {state.pad.kind === "problem" ? "this problem" : "this check"}</button> : null}
      {los.map((lo) => (
        <button key={lo} type="button" className="row" disabled={busy} onClick={() => void submit("teach_back", async () => (await host.api.requestTeachBack({ learningObjectId: lo })).practiceItemId)}>a teach-back of the idea this passage teaches{los.length > 1 ? ` (${lo})` : ""}</button>
      ))}
      {!answerItem && los.length === 0 ? <div className="note">nothing to submit this to yet: link the block to a passage (append it from a source), or write it in a problem pad</div> : null}
      {failure ? <div className="note err">{failure}</div> : null}
      <div className="acts"><button type="button" onClick={onClose}>not now</button></div>
    </div>
  );
}
