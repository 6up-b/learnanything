// The source menu's verbs, each wired to its server entry (spec §9.1; the verb table in reader-rd5a.md): what each
// verb does with a passage, a cue, a highlight, a note or a window, through the few things the desks lend it.
import type {
  ContentRefDto,
  CorrespondentsDto,
  LessonTurnInput,
  LessonViewDto,
  MenuObjectInput,
  PassageKnowsDto,
  PromotedRowDto,
  ReaderAuthorSectionQuestionDto,
  ReaderCaptureInput,
  ReaderCaptureReceiptDto,
  ReaderExerciseImportReceiptDto,
  ReaderImportExerciseInput,
} from "../../../api/dto";
import { objectInput, verbsFor, type MenuObject, type MenuRow, type VerbId } from "./model";

/** The server entries the verbs call. */
export interface MenuApi {
  passageKnows(input: MenuObjectInput): Promise<PassageKnowsDto>;
  readerCorrespondents(input: { extractionId: string; sectionId: string; searchFallback?: boolean }): Promise<CorrespondentsDto>;
  /** The reading's identity for a capture (its revision and render view). */
  readingIdentity(extractionId: string): Promise<{ sourceId: string; revisionId: string; renderViewId: string | null }>;
  readerCapture(input: ReaderCaptureInput): Promise<ReaderCaptureReceiptDto>;
  readerImportExercise(input: ReaderImportExerciseInput): Promise<ReaderExerciseImportReceiptDto>;
  readerAuthorSectionQuestion(input: { extractionId: string; sectionId: string }): Promise<ReaderAuthorSectionQuestionDto>;
  lessonTurn(input: LessonTurnInput): Promise<LessonViewDto>;
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
  /** "Draft this for your queue?": the review before Make it practice adds anything. */
  confirm: (title: string, detail: string) => Promise<boolean>;
  /** Show me: the figure built for the passage (null when none is shown), polled under the window asked from. */
  showMe: (text: string, anchor: { extractionId: string; spanId: string }, ownerWindowId: string | null) => Promise<{ figureId: string; line: string } | null>;
  /** The figure, landed where the desks keep figures (the running pad). */
  landFigure: (object: MenuObject, figure: { figureId: string; line: string }) => void;
  /** The desks' own moves for a window (§5.2, §6.6). */
  windowMove: (kind: "new_desk" | "gather" | "share_slot" | "own_slot", windowId: string) => void;
  showKnows: (object: MenuObject) => void;
  /** The rows passage.promoted gave this object (Open beside takes the first correspondent among them). */
  promotedRows: () => PromotedRowDto[];
}

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
        await ctx.api.readerCapture({
          sourceId: who.sourceId, revisionId: who.revisionId, extractionId: anchor.extractionId, renderViewId: who.renderViewId,
          action: "annotate", clientIdempotencyKey: ctx.mintId("note"), learnerText: note,
          rawSelection: { extractionId: anchor.extractionId, nodes: (object.spanIds?.length ? object.spanIds : [anchor.spanId]).map((spanId) => ({ spanId, ...(object.selection ? { quote: object.selection } : {}) })) },
        });
        ctx.toast("noted in the margin");
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
      case "compare":
        // The Compare window, on the selection's words (it asks across the library when the learner confirms there).
        ctx.openContent({ kind: "compare", query: words.slice(0, 200) });
        return;
      case "show_me": {
        if (!anchor) return;
        ctx.toast("◇ making a figure for this passage · it lands in your running pad when it's ready");
        // The Reader's figure build, polled under the window asked from (a paused window's poll waits).
        const figure = await ctx.showMe(words.slice(0, 300), anchor, object.windowId);
        if (!figure) {
          ctx.toast("no figure for this passage · nothing was shown");
          return;
        }
        ctx.landFigure(object, figure);
        return;
      }
      case "make_practice": {
        if (!anchor) return;
        const { sectionId, role } = await sectionOf(object, ctx);
        if (role === "exercise") {
          if (!(await ctx.confirm("✎ make it practice · import this exercise", "it joins your queue as the book has it, with its parts and its solution kept apart"))) return;
          const who = await ctx.api.readingIdentity(anchor.extractionId);
          await ctx.api.readerImportExercise({
            sourceId: who.sourceId, revisionId: who.revisionId, extractionId: anchor.extractionId, renderViewId: who.renderViewId, clientIdempotencyKey: ctx.mintId("import"),
            rawSelection: { extractionId: anchor.extractionId, nodes: (object.spanIds?.length ? object.spanIds : [anchor.spanId]).map((spanId) => ({ spanId })) },
          });
          ctx.toast("importing the exercise · it joins your queue when it is ready");
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
      case "teach_me": {
        const lesson = await ctx.api.lessonTurn(anchor
          ? { action: "open", entry: "reader_selection", selection: { extractionId: anchor.extractionId, spanIds: object.spanIds?.length ? object.spanIds : [anchor.spanId] } }
          : { action: "open", entry: "new_topic", goalText: words.slice(0, 200) });
        ctx.openContent({ kind: "lesson", lessonId: lesson.lessonId });
        return;
      }
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
export function sourceMenuRows(object: MenuObject, ctx: MenuContext, appendTarget: string): MenuRow[] {
  return verbsFor(object.kind).map((verb) => ({
    id: verb.id,
    glyph: verb.glyph,
    label: verb.id === "append" ? `Append to “${appendTarget}”  ▸` : verb.label,
    key: verb.key,
    section: "verb" as const,
    aid: verb.id === "knows",
    submenu: verb.id === "append",
    run: () => void runVerb(verb.id, object, ctx),
  }));
}
