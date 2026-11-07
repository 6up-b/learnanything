// The phone Reader's pure parts (mobile v2 §3): what a section's state is, where reading resumes, how a page's
// image is named, and how a prompt's page and image links become the host's content-addressed URLs (§2.3).
// Nothing here talks to the host.
import type { ReaderGuideSectionDto, ReaderProgressListDto, ReaderProtectionDto } from "@desktop/api/dto";
import { resumeSpanFromHistory } from "@desktop/screens/reader/readingPosition";

/** §3.3: the widths the host renders a page at (`learnloop_mobile.media.PAGE_WIDTHS`); the phone asks for the one
 *  that fills its column at the screen's density, never another, so the URLs (and the cache) stay few. */
export const PAGE_WIDTHS = [720, 1080] as const;

export function pageWidthFor(cssWidth: number, devicePixelRatio: number): number {
  const wanted = Math.ceil(Math.max(cssWidth, 1) * Math.max(devicePixelRatio || 1, 1));
  return PAGE_WIDTHS.find((width) => width >= wanted) ?? PAGE_WIDTHS[PAGE_WIDTHS.length - 1];
}

/** `ref` is a reading (an extraction id) or a stored file (`sha256-<hex>`); `page` is zero-based. */
export function pagePath(ref: string, page: number, width: number): string {
  return `/api/v1/reader/page/${encodeURIComponent(ref)}/${page}?w=${width}`;
}

export function assetPath(name: string): string {
  return `/api/v1/assets/${encodeURIComponent(name)}`;
}

export type SectionState = "read" | "started" | "unread";

export function sectionState(sectionId: string, progress: ReaderProgressListDto | null): SectionState {
  const row = progress?.sections.find((one) => one.sectionId === sectionId);
  if (!row) return "unread";
  if (row.completedAt) return "read";
  return row.spansSeen > 0 || row.revealedAt ? "started" : "unread";
}

/** *Continue reading* (§3.1): the shared place, from the host's reading history, so a place read on the desktop
 *  opens on the phone and the reverse (the desktop's own fallback, `resumeSpanFromHistory`). */
export function resumeSection(sections: readonly ReaderGuideSectionDto[], progress: ReaderProgressListDto | null): string | null {
  if (!sections.length) return null;
  const span = progress ? resumeSpanFromHistory(sections, progress.sections) : null;
  if (span) return sections.find((section) => section.spanIds.includes(span))?.id ?? sections[0].id;
  return sections[0].id;
}

export function nextSectionId(sections: readonly ReaderGuideSectionDto[], sectionId: string): string | null {
  const index = sections.findIndex((section) => section.id === sectionId);
  return index >= 0 && index + 1 < sections.length ? sections[index + 1].id : null;
}

/** What a reading's protection is, as one string: when it changes, the phone drops what it cached of that reading
 *  (its sections and its page images), so a mark made on the desktop reaches the phone's caches too. */
export function protectionKey(protection: ReaderProtectionDto | null | undefined): string {
  if (!protection) return "none";
  return JSON.stringify({ withheld: Boolean(protection.withheld), held: [...(protection.heldOutSpanIds ?? [])].sort() });
}

/** The desktop's rule (`groundingProtected`): a selection touching what the reading holds out offers no Ask. */
export function selectionProtected(protection: ReaderProtectionDto | null | undefined, spanIds: readonly string[]): boolean {
  if (!protection) return false;
  if (protection.withheld) return true;
  const held = new Set(protection.heldOutSpanIds ?? []);
  return spanIds.some((span) => held.has(span));
}

const STORE_NAME = /sha256-[0-9a-f]{64}/;
const LLPDF_TARGET = /\(\s*<?(llpdf:[^)\s>]+)>?\s*\)|<(llpdf:[^>\s]+)>/gi;

/** `llpdf://…/sha256-<hex>[#page=N]` as the store name and its zero-based page, or null (§2.3). */
export function llpdfPage(target: string): { name: string; page: number } | null {
  const match = /^llpdf:(?:\/\/[^/#?]*)?\/?(?:[^#?]*\/)?(sha256-[0-9a-f]{64})(?:#page=([1-9][0-9]{0,4}))?$/i.exec(target.trim());
  if (!match) return null;
  return { name: match[1].toLowerCase(), page: Number(match[2] ?? "1") - 1 };
}

/** A link or image target's store name, when it ends in one. */
export function storeNameOf(target: string | undefined | null): string | null {
  if (!target) return null;
  const bare = target.split("#", 1)[0].split("?", 1)[0];
  const tail = bare.split(/[/:]/).pop() ?? "";
  return STORE_NAME.test(tail) && tail.length === 71 ? tail : null;
}

/** The fragment a page link becomes (react-markdown keeps fragments; it drops an unknown scheme). */
export const PAGE_LINK = "#llpage/";

/** A prompt's `llpdf:` page links, rewritten so they survive the renderer and open the host's page image. */
export function withPageLinks(markdown: string): string {
  return markdown.replace(LLPDF_TARGET, (whole, inParens?: string, angled?: string) => {
    const target = inParens ?? angled ?? "";
    const page = llpdfPage(target);
    if (!page) return whole;
    const link = `${PAGE_LINK}${page.name}/${page.page}`;
    return inParens ? `(${link})` : `<${link}>`;
  });
}

export function pageLinkTarget(href: string | undefined | null): { name: string; page: number } | null {
  if (!href || !href.startsWith(PAGE_LINK)) return null;
  const [name, page] = href.slice(PAGE_LINK.length).split("/");
  return STORE_NAME.test(name ?? "") && /^[0-9]+$/.test(page ?? "") ? { name, page: Number(page) } : null;
}
