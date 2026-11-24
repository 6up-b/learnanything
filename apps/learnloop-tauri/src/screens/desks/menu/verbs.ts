// The source menu's verbs, each wired to its server entry (spec §9.1; the verb table in reader-rd5a.md): what each
// verb does with a passage, a cue, a highlight, a note or a window, through the few things the desks lend it.
import type {
  ContentRefDto,
  CorrespondentsDto,
  MenuObjectInput,
  PassageKnowsDto,
  PromotedRowDto,
  ReaderAuthorSectionQuestionDto,
  ReaderCaptureInput,
  ReaderCaptureReceiptDto,
  ReaderExerciseImportReceiptDto,
  ReaderImportExerciseInput,
} from "../../../api/dto";
import type { LessonEntry } from "../../LessonView";
import { QUOTING_VERBS, captureNodes, hasPassage, objectInput, verbsFor, type MenuObject, type MenuRow, type VerbId } from "./model";

/** The server entries the verbs call. */
export interface MenuApi {
  passageKnows(input: MenuObjectInput): Promise<PassageKnowsDto>;
  readerCorrespondents(input: { extractionId: string; sectionId: string; searchFallback?: boolean }): Promise<CorrespondentsDto>;
  /** The reading's identity for a capture (its revision and render view). */
  readingIdentity(extractionId: string): Promise<{ sourceId: string; revisionId: string; renderViewId: string | null }>;
  readerCapture(input: ReaderCaptureInput): Promise<ReaderCaptureReceiptDto>;
  readerImportExercise(input: ReaderImportExerciseInput): Promise<ReaderExerciseImportReceiptDto>;
  readerAuthorSectionQuestion(input: { extractionId: string; sectionId: string }): Promise<ReaderAuthorSectionQuestionDto>;
}

/** What the desks lend the verbs. */
export interface MenuContext {
  deskId: string | null;
  api: MenuApi;
  mintId: (prefix: string) => string;
  toast: (text: string) => void;
  /** The companion, anchored at the object, with its words as the chip. */
  ask: (object: MenuObject) => void;
  openSearch: (query: string) => void;
  openContent: (ref: ContentRefDto, options?: { spanId?: string | null; view?: Record<string, unknown> }) => void;
  carry: (text: string, origin: { kind: "selection" | "note"; ref?: string | null; anchor?: { extractionId: string; spanId: string } | null }) => Promise<void> | void;
  /** Append the object to a pad: the remembered target (null), another of the desk's pads, or a new one ("+"). */
  append: (object: MenuObject, padId: string | "+" | null) => void;
  /** A margin note's words, asked in a small sheet; resolves null when the learner leaves it. */
  askNote: (object: MenuObject) => Promise<string | null>;
  /** Make it practice on an exercise: its words, the import, and what it made (a sheet of the desks'). */
  reviewExercise: (object: MenuObject, anchor: { extractionId: string; spanId: string }) => void;
  /** "Draft this for your queue?": the confirmation before Make it practice drafts a section question. */
  confirm: (title: string, detail: string) => Promise<boolean>;
  /** Show me: the figure built for the passage (null when none is shown), polled under the window asked from. */
  showMe: (text: string, anchor: { extractionId: string; spanId: string }, ownerWindowId: string | null) => Promise<{ figureId: string; line: string } | null>;
  /** Where a figure asked for now will land: the running pad of the desk asked on (null: it has none). */
  figureDestination: () => string | null;
  /** The figure, landed in the pad named when it was asked for. */
  landFigure: (object: MenuObject, figure: { figureId: string; line: string }, padId: string | null) => void | Promise<void>;
  /** A Teacher lesson opened in the desk's stack (a tab of its own while its first turn runs; spec §11.1). */
  teachMe: (entry: LessonEntry) => void;
  /** The desks' own moves for a window (§5.2, §6.6). */
  windowMove: (kind: "new_desk" | "gather" | "share_slot" | "own_slot", windowId: string) => void;
  showKnows: (object: MenuObject) => void;
  /** The rows passage.promoted gave this object (Open beside takes the first correspondent among them). */
  promotedRows: () => PromotedRowDto[];
  /** Whether the object is exam or held-out material (resolves when its first answer says; false with no passage). */
  withheld: () => Promise<boolean>;
  /** Why the verbs that would reveal or send veiled material wait now (an inline check is open), or null. */
  heldReason?: () => string | null;
}

/** The verbs that would reveal veiled material or send it to a model while an inline check is open (spec §12.6.4):
 * each waits until the check is answered, its row disabled with the reason (the record lists the call per verb). */
export const CHECK_HELD_VERBS: readonly VerbId[] = ["ask", "find", "compare", "show_me", "make_practice", "teach_me", "knows", "open_beside"];

function errorText(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

function anchorOf(object: MenuObject): { extractionId: string; spanId: string } | null {
  return object.extractionId && object.spanId ? { extractionId: object.extractionId, spanId: object.spanId } : null;
}

/** A promoted row's action as a place to open (Open beside's first choice, and a promoted row's run). */
export function promotedRef(row: PromotedRowDto): { ref: ContentRefDto; spanId: string | null } | null {
  const ref = row.action.ref as Record<string, unknown> | undefined;
  if (row.action.verb !== "open" || !ref || typeof ref.kind !== "string") return null;
  const camel: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(ref)) camel[key.replace(/_([a-z])/g, (_m, c: string) => c.toUpperCase())] = value;
  const target = row.action.target ?? {};
  if (typeof target.t === "number" && camel.kind === "video") camel.t = target.t;
  return { ref: camel as unknown as ContentRefDto, spanId: target.spanId ?? null };
}

/** The section a passage sits in, from What this knows' read. */
async function sectionOf(object: MenuObject, ctx: MenuContext): Promise<{ sectionId: string | null; role: string | null }> {
  const knows = await ctx.api.passageKnows(objectInput(object, ctx.deskId));
  const place = knows.places.find((each) => each.spanId === object.spanId) ?? knows.places[0];
  return { sectionId: place?.knows.sectionId ?? null, role: place?.role ?? null };
}

/** Run one verb on one object. */
export async function runVerb(id: VerbId, object: MenuObject, ctx: MenuContext): Promise<void> {
  const anchor = anchorOf(object);
  const words = (object.selection || object.text).trim();
  try {
    const held = CHECK_HELD_VERBS.includes(id) ? ctx.heldReason?.() ?? null : null;
    if (held) {
      ctx.toast(`this waits · ${held}`);
      return;
    }
    // A verb that would quote or send the words waits for the object's protection: exam or held-out material is
    // never sent anywhere from the menu (a key pressed before the menu's first answer waits for it too).
    if (QUOTING_VERBS.includes(id) && await ctx.withheld()) {
      ctx.toast("this is exam or held-out material: its words are not sent anywhere from here");
      return;
    }
    switch (id) {
      case "ask":
        ctx.ask(object);
        return;
      case "find":
        ctx.openSearch(words.slice(0, 200));
        return;
      case "carry":
        await ctx.carry(words.slice(0, 400), { kind: object.kind === "note" ? "note" : "selection", ref: object.annotationId ?? null, anchor });
        return;
      case "append":
        ctx.append(object, null);
        return;
      case "note": {
        if (!anchor) return;
        const note = await ctx.askNote(object);
        if (!note) return;
        const who = await ctx.api.readingIdentity(anchor.extractionId);
        const receipt = await ctx.api.readerCapture({
          sourceId: who.sourceId, revisionId: who.revisionId, extractionId: anchor.extractionId, renderViewId: who.renderViewId,
          action: "annotate", clientIdempotencyKey: ctx.mintId("note"), learnerText: note,
          rawSelection: { extractionId: anchor.extractionId, nodes: captureNodes(object) },
        });
        // Where it landed is the capture's own answer: a note that could not be placed says so.
        ctx.toast(receipt.anchorStatus === "needs_reanchor" ? "noted, but its place in the passage needs re-anchoring" : "noted in the margin");
        return;
      }
      case "open_beside": {
        // The passage's best correspondent: the first promoted row that opens one; else the section's correspondents.
        const row = ctx.promotedRows().find((each) => ["correspondent", "next_step", "elsewhere"].includes(each.kind));
        const place = row ? promotedRef(row) : null;
        if (place) {
          ctx.openContent(place.ref, { spanId: place.spanId });
          return;
        }
        if (!anchor) return;
        const { sectionId } = await sectionOf(object, ctx);
        if (!sectionId) {
          ctx.toast("nothing found that treats this passage elsewhere yet");
          return;
        }
        const found = await ctx.api.readerCorrespondents({ extractionId: anchor.extractionId, sectionId, searchFallback: true });
        const section = found.learningObjects.flatMap((lo) => lo.sources.flatMap((source) => source.sections))[0]
          ?? found.search?.sources.flatMap((source) => source.sections)[0];
        if (!section) {
          ctx.toast("nothing found that treats this passage elsewhere yet");
          return;
        }
        ctx.openContent({ kind: "source", sourceId: section.sourceId, extractionId: section.jump.extractionId }, { spanId: section.jump.spanId });
        if (found.status === "unchecked") ctx.toast("found by search, not checked");
        return;
      }
      case "compare": {
        // The Compare window, on the selection's words and anchored on its passages: asking there runs the
        // comparison from those passages (the selection's door), once the learner confirms the question.
        if (!anchor) {
          ctx.openContent({ kind: "compare", query: words.slice(0, 200) });
          return;
        }
        const who = await ctx.api.readingIdentity(anchor.extractionId);
        ctx.openContent({ kind: "compare", query: words.slice(0, 200) }, { view: { compareAnchor: {
          extractionId: anchor.extractionId, spanIds: object.spanIds?.length ? object.spanIds : [anchor.spanId], sourceId: who.sourceId, revisionId: who.revisionId,
        } } });
        return;
      }
      case "show_me": {
        if (!anchor) return;
        // Where it lands is decided now: the running pad of this desk, even if another desk is shown when it is ready.
        const destination = ctx.figureDestination();
        ctx.toast("◇ making a figure for this passage · it lands in your running pad when it's ready");
        // The Reader's figure build, polled under the window asked from (a paused window's poll waits).
        const figure = await ctx.showMe(words.slice(0, 300), anchor, object.windowId);
        if (!figure) {
          ctx.toast("no figure for this passage · nothing was shown");
          return;
        }
        await ctx.landFigure(object, figure, destination);
        return;
      }
      case "make_practice": {
        if (!anchor) return;
        const { sectionId, role } = await sectionOf(object, ctx);
        if (role === "exercise") {
          // The exercise's own words first, then the import, then what it made with edit and retire (the sheet).
          ctx.reviewExercise(object, anchor);
          return;
        }
        if (!sectionId) {
          ctx.toast("this passage sits in no section to write a question for");
          return;
        }
        if (!(await ctx.confirm("✎ make it practice · a question for this section", "LearnLoop drafts a question from this section; it shows in the section to answer or keep when it is ready"))) return;
        const drafted = await ctx.api.readerAuthorSectionQuestion({ extractionId: anchor.extractionId, sectionId });
        ctx.toast(drafted.status === "exists" ? "this section already has a question waiting" : "drafting a question for this section");
        return;
      }
      case "teach_me":
        // The lesson opens as a tab of the desk's stack (RD9a's opening: the tab shows while its first turn runs).
        ctx.teachMe(anchor
          ? { kind: "open", entry: "reader_selection", selection: { extractionId: anchor.extractionId, spanIds: object.spanIds?.length ? object.spanIds : [anchor.spanId] } }
          : { kind: "open", entry: "new_topic", title: words.slice(0, 200) });
        return;
      case "new_desk":
      case "gather":
      case "share_slot":
      case "own_slot":
        if (object.windowId) ctx.windowMove(id, object.windowId);
        return;
      case "knows":
        ctx.showKnows(object);
        return;
      case "submit":
        return;
    }
  } catch (error) {
    ctx.toast(`couldn't do that just now · ${errorText(error)}`);
  }
}

/** The menu's verb rows for a source object (a passage, cue, highlight, note or window), in their fixed order. */
export function sourceMenuRows(object: MenuObject, ctx: MenuContext, appendTarget: string, withheld = false): MenuRow[] {
  // What this knows reads a passage: a window with none in view (a panel, a thread) offers only its moves; on exam or
  // held-out material the verbs that would quote or send its words are left out.
  const held = ctx.heldReason?.() ?? null;
  return verbsFor(object.kind).filter((verb) => (verb.id !== "knows" || hasPassage(object)) && !(withheld && QUOTING_VERBS.includes(verb.id))).map((verb) => ({
    id: verb.id,
    glyph: verb.glyph,
    label: verb.id === "append" ? `Append to “${appendTarget}”  ▸` : verb.label,
    key: verb.key,
    section: "verb" as const,
    ...(held && CHECK_HELD_VERBS.includes(verb.id) ? { disabled: true, note: held } : {}),
    aid: verb.id === "knows",
    submenu: verb.id === "append",
    run: () => void runVerb(verb.id, object, ctx),
  }));
}
