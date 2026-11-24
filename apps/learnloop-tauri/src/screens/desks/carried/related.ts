// Carried questions resurfacing beside a related passage (spec §10.12; RD10). RD4 shows a carried question's quiet ◌
// beside the passage it was carried from. A question also comes back beside the passages that treat the same thing in
// the other open readings: its passage's section (the union read), that section's judged correspondents
// (`reader.correspondents`, no search, no model call), each landing on its section's first passage. Never a nudge:
// the same quiet ◌, logged `surfaced` once per question as before. Read once per question per session.
import type { CarriedQuestionDto, CorrespondentsDto, PassageUnionDto, PassageUnionInput } from "../../../api/dto";

export interface RelatedApi {
  passageUnionRange(input: PassageUnionInput): Promise<PassageUnionDto>;
  correspondents(input: { extractionId: string; sectionId: string; searchFallback: boolean }): Promise<CorrespondentsDto>;
}

interface Place {
  extractionId: string;
  spanId: string;
}

function anchorOf(question: CarriedQuestionDto): Place | null {
  const anchor = question.anchor as { extraction_id?: unknown; span_id?: unknown } | null;
  return anchor && typeof anchor.extraction_id === "string" && typeof anchor.span_id === "string"
    ? { extractionId: anchor.extraction_id, spanId: anchor.span_id } : null;
}

export class CarriedRelated {
  private places = new Map<string, Place[]>();
  private asking = new Set<string>();
  private listeners = new Set<() => void>();
  private version = 0;

  constructor(private readonly api: RelatedApi) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  private emit(): void {
    this.version += 1;
    for (const listener of this.listeners) listener();
  }

  private resolve(question: CarriedQuestionDto, anchor: Place): void {
    this.asking.add(question.carriedId);
    const done = (places: Place[]) => {
      this.places.set(question.carriedId, places);
      this.emit();
    };
    void Promise.resolve()
      .then(() => this.api.passageUnionRange({ extractionId: anchor.extractionId, fromSpanId: anchor.spanId, toSpanId: anchor.spanId }))
      .then((union) => {
        const sectionId = union.spans.find((span) => span.spanId === anchor.spanId)?.sectionId ?? union.spans[0]?.sectionId ?? null;
        if (!sectionId) return done([]);
        return this.api.correspondents({ extractionId: anchor.extractionId, sectionId, searchFallback: false }).then((view) => {
          const places: Place[] = [];
          for (const group of view.status === "judged" ? view.learningObjects : []) {
            for (const source of group.sources) {
              for (const section of source.sections) {
                if (section.jump.spanId && section.extractionId !== anchor.extractionId
                  && !places.some((place) => place.extractionId === section.extractionId && place.spanId === section.jump.spanId)) {
                  places.push({ extractionId: section.extractionId, spanId: section.jump.spanId });
                }
              }
            }
          }
          done(places);
        });
      })
      .catch(() => done([]));
  }

  /** The still-carried questions to show beside related passages in the open readings: each as a copy whose anchor
   * names the related passage (`related: true`), so the margin marks place it there. */
  beside(questions: readonly CarriedQuestionDto[], openExtractions: readonly string[]): CarriedQuestionDto[] {
    const open = new Set(openExtractions);
    const out: CarriedQuestionDto[] = [];
    for (const question of questions) {
      const anchor = anchorOf(question);
      if (!question.carried || !anchor) continue;
      const places = this.places.get(question.carriedId);
      if (!places) {
        // Only a question whose passage has another reading open beside it is worth reading for.
        if (!this.asking.has(question.carriedId) && [...open].some((extractionId) => extractionId !== anchor.extractionId)) this.resolve(question, anchor);
        continue;
      }
      for (const place of places) {
        if (open.has(place.extractionId)) out.push({ ...question, anchor: { extraction_id: place.extractionId, span_id: place.spanId, related: true } });
      }
    }
    return out;
  }
}

/** Every still-carried question, through the list's pages (the shelf reads only its first). */
export async function allCarried(list: (cursor?: string) => Promise<{ carried: CarriedQuestionDto[]; cursor?: string | null }>): Promise<CarriedQuestionDto[]> {
  const out: CarriedQuestionDto[] = [];
  const seen = new Set<string>();
  let cursor: string | undefined;
  for (;;) {
    const page = await list(cursor);
    for (const question of page.carried) if (!seen.has(question.carriedId)) { seen.add(question.carriedId); out.push(question); }
    if (!page.cursor || page.cursor === cursor) return out;
    cursor = page.cursor;
  }
}
