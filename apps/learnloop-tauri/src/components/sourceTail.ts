// Readable-tail helpers shared by the source library sidebar and the ingest
// activity stack. Source titles are raw URIs/paths; we show the last meaningful
// segment and let CSS ellipsize the rest. YouTube watch URLs are special-cased:
// the naive query-strip + last-path-segment yields "watch" (the video id lives
// in the ?v= query), so we extract the id explicitly → "youtube · <id>".

// Extract a YouTube video id from a watch/embed/shorts/live/youtu.be URL, or
// null if the string is not a recognizable YouTube URL.
export function youtubeVideoId(source: string): string | null {
  const s = (source || "").trim();
  if (!/(^|\/\/)([\w-]+\.)?(youtube\.com|youtu\.be)\//i.test(s)) return null;
  try {
    const url = new URL(s);
    const host = url.hostname.toLowerCase();
    if (host === "youtu.be" || host.endsWith(".youtu.be")) {
      const id = url.pathname.split("/").filter(Boolean)[0];
      return id || null;
    }
    const v = url.searchParams.get("v");
    if (v) return v;
    // /embed/<id>, /shorts/<id>, /live/<id>, /v/<id>
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && /^(embed|shorts|live|v)$/i.test(parts[0])) return parts[1];
    return null;
  } catch {
    return null;
  }
}

// Turn a source URI/path/title into a compact readable tail. YouTube URLs render
// as "youtube · <id>"; everything else keeps its last path segment (query and
// fragment stripped). Returns the input unchanged when there is no useful tail.
export function readableSourceTail(source: string): string {
  const vid = youtubeVideoId(source);
  if (vid) return `youtube · ${vid}`;
  const trimmed = source.replace(/[/\\]+$/, "");
  const withoutQuery = trimmed.split(/[?#]/)[0];
  const tail = withoutQuery.split(/[/\\]/).filter(Boolean).pop();
  return tail || source;
}
