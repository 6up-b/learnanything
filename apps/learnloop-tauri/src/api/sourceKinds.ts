// GENERATED from learnloop.ingest.source_kinds.SOURCE_KINDS by `python tests/test_source_kinds.py --write`.
// Edit the table, never this file: tests/test_source_kinds.py fails when they differ.

export const SOURCE_KINDS = [
  {"category": "web", "label": "web page", "noun": "article", "extensions": [".html", ".htm"], "urlExtensions": []},
  {"category": "arxiv", "label": "arXiv paper", "noun": "paper", "extensions": [], "urlExtensions": []},
  {"category": "pdf", "label": "PDF", "noun": "PDF", "extensions": [".pdf"], "urlExtensions": [".pdf"]},
  {"category": "youtube", "label": "YouTube transcript", "noun": "video", "extensions": [], "urlExtensions": []},
  {"category": "textfile", "label": "local file", "noun": "book", "extensions": [".md", ".markdown", ".mdown", ".txt", ".text", ".rst", ".vtt", ".srt"], "urlExtensions": []},
  {"category": "audio", "label": "audio file", "noun": "recording", "extensions": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".oga", ".opus", ".aac"], "urlExtensions": []},
  {"category": "image", "label": "image", "noun": "image", "extensions": [".png", ".jpg", ".jpeg"], "urlExtensions": [".png", ".jpg", ".jpeg"]}
] as const;

export type SourceCategory = (typeof SOURCE_KINDS)[number]["category"];

export type SourceKindRow = (typeof SOURCE_KINDS)[number];

/** Every local file suffix the classifier reads as some kind (lower case, with the dot). */
export const SOURCE_FILE_EXTENSIONS: readonly string[] = SOURCE_KINDS.flatMap((kind) => kind.extensions);

export function sourceKindRow(category: string | null | undefined): SourceKindRow | null {
  return SOURCE_KINDS.find((kind) => kind.category === category) ?? null;
}
