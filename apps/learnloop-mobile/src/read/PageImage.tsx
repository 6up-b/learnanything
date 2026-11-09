// The original page, on demand (mobile v2 §3.3; owner decision D4: no PDF.js on the phone). The host renders it
// (pypdfium2), names it by its content, and the service worker keeps it (`public/sw.js`), so a page opened once
// reads offline too. An image needs the bearer token, so it is fetched and shown from a blob URL (the CSP's
// `img-src blob:`).
import { useEffect, useState, type ComponentProps } from "react";
import type ReactMarkdown from "react-markdown";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { getImage } from "../api/http";
import { assetLinkTarget, assetPath, pagePath, pageLinkTarget, pageWidthFor, phoneUrlTransform, storeNameOf } from "./readerModel";

type Components = NonNullable<ComponentProps<typeof ReactMarkdown>["components"]>;

function useBlobUrl(path: string | null): { url: string | null; failed: string | null } {
  const [state, setState] = useState<{ path: string | null; url: string | null; failed: string | null }>({ path: null, url: null, failed: null });
  useEffect(() => {
    if (!path) return undefined;
    let cancelled = false;
    let made: string | null = null;
    getImage(path).then(
      (blob) => {
        if (cancelled) return;
        made = URL.createObjectURL(blob);
        setState({ path, url: made, failed: null });
      },
      (error: { code?: string; message?: string }) => {
        if (cancelled) return;
        const line = error?.code === "held_out_material"
          ? "This page is held out for your exam, so it isn't shown here."
          : error?.code === "desktop_offline"
            ? "The page isn't on this phone yet. It opens when the desktop is reachable."
            : "The page isn't available.";
        setState({ path, url: null, failed: line });
      }
    );
    return () => {
      cancelled = true;
      if (made) URL.revokeObjectURL(made);
    };
  }, [path]);
  return state.path === path ? state : { url: null, failed: null };
}

function columnWidth(): number {
  if (typeof window === "undefined") return PAGE_DEFAULT_CSS;
  return Math.min(window.innerWidth || PAGE_DEFAULT_CSS, 720);
}
const PAGE_DEFAULT_CSS = 360;

/** One page of a reading or of a stored file, as printed. `alt` is the block's text where it reads well (§4.7). */
export function PageImage({ ref_, page, alt, inline = false }: { ref_: string; page: number; alt?: string | null; inline?: boolean }) {
  const width = pageWidthFor(columnWidth(), typeof window === "undefined" ? 1 : window.devicePixelRatio);
  const { url, failed } = useBlobUrl(pagePath(ref_, page, width));
  // Inside a prompt's paragraph (an image or a page link) the line is a span, never a paragraph in a paragraph.
  const Line = inline ? "span" : "p";
  if (failed) return <Line className="dim" role="status">{failed}</Line>;
  if (!url) return <Line className="dim" role="status">Opening the page…</Line>;
  return <img className="page-image" src={url} alt={alt?.trim() || `page ${page + 1}, as printed`} />;
}

export function StoredImage({ name, alt }: { name: string; alt?: string | null }) {
  const { url, failed } = useBlobUrl(assetPath(name));
  if (failed) return <span className="dim">{failed}</span>;
  if (!url) return <span className="dim">{alt || "image"}</span>;
  return <img className="stored-image" src={url} alt={alt || "image"} />;
}

/** A page link in a prompt (`llpdf:`, mapped by `phoneUrlTransform`): its page opens under it, on demand. */
function PageLink({ name, page, children }: { name: string; page: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="page-link">
      <button className="link" type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {children || `page ${page + 1}`}
      </button>
      {open ? <PageImage ref_={name} page={page} inline /> : null}
    </span>
  );
}

/**
 * Mobile v2 §2.3: how a prompt's images and links render on the phone. A stored image (its target ends in the
 * originals store's `sha256-<hex>` name) and a page link render from the host; a remote image stays the link it
 * is (the CSP has no remote images, M2a §3.4). The targets arrive as the phone's own fragments
 * (`phoneUrlTransform`, in place of react-markdown's URL filter, which empties an `asset:` or `llpdf:` one; Codex
 * review F11; on parsed destinations only, so code keeps its text, re-review F15), so render prompts through
 * `PhoneMarkdown`.
 */
export const PhoneMedia: Components = {
  img: ({ src, alt }) => {
    const target = typeof src === "string" ? src : null;
    const page = pageLinkTarget(target);
    if (page) return <PageImage ref_={page.name} page={page.page} alt={alt} inline />;
    const name = assetLinkTarget(target) ?? storeNameOf(target);
    if (name) return <StoredImage name={name} alt={alt} />;
    return <a href={target ?? undefined} rel="noreferrer noopener" target="_blank">{alt || "image"}</a>;
  },
  a: ({ href, children }) => {
    const page = pageLinkTarget(href);
    if (page) return <PageLink name={page.name} page={page.page}>{children}</PageLink>;
    const name = assetLinkTarget(href) ?? storeNameOf(href);
    if (name) return <StoredImage name={name} alt={typeof children === "string" ? children : null} />;
    return <a href={href} rel="noreferrer noopener" target="_blank">{children}</a>;
  }
};

/** A prompt, a book's text or an answer as the phone renders it: the desktop's `MarkdownMath` (KaTeX), with its
 *  page links and stored images served by the host (§2.3). */
export function PhoneMarkdown({ value }: { value: string }) {
  return <MarkdownMath value={value || ""} components={PhoneMedia} urlTransform={phoneUrlTransform} />;
}
