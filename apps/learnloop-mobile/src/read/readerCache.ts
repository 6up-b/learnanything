// The Reader's display cache (mobile v2 §3.2, §5.4): a section the learner opened, and the next one, kept so it
// reads with no signal. Never authoritative: every open re-reads the host when it can. What the host withholds is
// never in it (the host never sends it), and when a reading's protection changes (a mark made on the desktop)
// everything cached of that reading goes, its page images included.
import type { ReaderGuidePlanDto, ReaderProgressListDto } from "@desktop/api/dto";
import { phone, type PhoneSectionDto } from "../api/phone";
import { dropExtraction, getLatest, getSection, purgePageImages, putLatest, putSection } from "../store/displayCache";
import { protectionKey } from "./readerModel";

interface ReadingMeta {
  readonly revision: string;
  readonly protection: string;
}

const metaName = (extractionId: string) => `reader:${extractionId}`;
const guideName = (extractionId: string) => `guide:${extractionId}`;
const progressName = (extractionId: string) => `progress:${extractionId}`;

/** The copy of a section kept last time, or null (§4.5: a screen with cached data shows it at once). */
export async function cachedSection(extractionId: string, sectionId: string): Promise<PhoneSectionDto | null> {
  const meta = await getLatest<ReadingMeta>(metaName(extractionId)).catch(() => null);
  return meta ? getSection<PhoneSectionDto>({ extractionId, revision: meta.revision, sectionId }).catch(() => null) : null;
}

/** A section from the host, kept; or, the host away, the copy kept last time (`stale`). */
export async function loadSection(extractionId: string, sectionId: string): Promise<{ section: PhoneSectionDto; stale: boolean }> {
  try {
    const section = await phone.section(extractionId, sectionId);
    await keep(extractionId, sectionId, section);
    return { section, stale: false };
  } catch (error) {
    if ((error as { code?: string }).code !== "desktop_offline") throw error;
    const meta = await getLatest<ReadingMeta>(metaName(extractionId));
    const cached = meta ? await getSection<PhoneSectionDto>({ extractionId, revision: meta.revision, sectionId }) : null;
    if (!cached) throw error;
    return { section: cached, stale: true };
  }
}

/** §3.2's prefetch: the next section, into the cache only. A failure is nothing (it loads when opened). */
export async function prefetchSection(extractionId: string, sectionId: string): Promise<void> {
  try {
    await keep(extractionId, sectionId, await phone.section(extractionId, sectionId));
  } catch {
    /* the section loads when it is opened */
  }
}

async function keep(extractionId: string, sectionId: string, section: PhoneSectionDto): Promise<void> {
  const revision = section.renderViewId || section.contentHash || "r";
  const key = protectionKey(section.protection);
  const meta = await getLatest<ReadingMeta>(metaName(extractionId));
  if (meta && (meta.protection !== key || meta.revision !== revision)) {
    // A new mark or a new reading: nothing cached of it stays, and no page image either.
    await dropExtraction(extractionId);
    if (meta.protection !== key) await purgePageImages();
  }
  await putLatest(metaName(extractionId), { revision, protection: key } satisfies ReadingMeta);
  await putSection({ extractionId, revision, sectionId }, section);
}

/** The section list and the reading history as last read here, or null (shown at once, then refreshed). */
export async function cachedGuide(extractionId: string): Promise<{ guide: ReaderGuidePlanDto | null; progress: ReaderProgressListDto | null }> {
  const [guide, progress] = await Promise.all([
    getLatest<ReaderGuidePlanDto>(guideName(extractionId)).catch(() => null),
    getLatest<ReaderProgressListDto>(progressName(extractionId)).catch(() => null)
  ]);
  return { guide, progress };
}

/** The guide plan (the section list) and the reading history, from the host or, away from it, as last read. */
export async function loadGuide(extractionId: string): Promise<{ guide: ReaderGuidePlanDto; stale: boolean }> {
  try {
    const guide = await phone.guidePlan(extractionId);
    await putLatest(guideName(extractionId), guide);
    return { guide, stale: false };
  } catch (error) {
    if ((error as { code?: string }).code !== "desktop_offline") throw error;
    const guide = await getLatest<ReaderGuidePlanDto>(guideName(extractionId));
    if (!guide) throw error;
    return { guide, stale: true };
  }
}

export async function loadProgress(extractionId: string): Promise<ReaderProgressListDto | null> {
  try {
    const progress = await phone.readerProgress(extractionId);
    await putLatest(progressName(extractionId), progress);
    return progress;
  } catch {
    return getLatest<ReaderProgressListDto>(progressName(extractionId));
  }
}

/** This phone's own last place in a book (each device keeps its own scroll, §5.6), by its reading. */
export interface LocalPlace {
  readonly extractionId: string;
  readonly sectionId: string;
  readonly spanId: string | null;
  readonly title: string;
  readonly sourceId: string | null;
}

const PLACE_KEY = "learnloop.phone.reader.places";

export function readPlaces(): LocalPlace[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(PLACE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((one) => one && typeof one.extractionId === "string").slice(0, 5) : [];
  } catch {
    return [];
  }
}

export function rememberPlace(place: LocalPlace): void {
  try {
    const rest = readPlaces().filter((one) => one.sourceId ? one.sourceId !== place.sourceId : one.extractionId !== place.extractionId);
    localStorage.setItem(PLACE_KEY, JSON.stringify([place, ...rest].slice(0, 5)));
  } catch {
    /* a denied write never stops reading */
  }
}

export function forgetPlaces(): void {
  try {
    localStorage.removeItem(PLACE_KEY);
  } catch {
    /* nothing to forget */
  }
}
