/**
 * Parsed pdf.js documents, kept across Reader unmounts.
 *
 * Leaving the Reader tab used to destroy the parsed document, its page text
 * (Ctrl+F) cache and every rendered page; coming back re-fetched the bytes
 * over llpdf:// and re-parsed them. Documents are content-addressed by their
 * URL, so a cached entry can only go stale when the vault changes — the app
 * calls clearPdfDocuments() on a vault switch.
 *
 * Memory is bounded by MAX_DOCS (least recently used first). The pdf.js
 * worker holds the parsed document and its page caches; a scanned textbook
 * can be a few hundred MB there, so this is a small number on purpose.
 */
import * as pdfjs from "pdfjs-dist";
import type { PDFDocumentLoadingTask, PDFDocumentProxy } from "pdfjs-dist";

const MAX_DOCS = 3;

export interface CachedPdfDocument {
  readonly doc: PDFDocumentProxy;
  /** Lower-cased page text by zero-based page index, filled lazily by find. */
  readonly pageTexts: Map<number, string>;
}

interface Entry extends CachedPdfDocument {
  /** pdf.js frees the worker-side document through the loading task. */
  readonly task: PDFDocumentLoadingTask;
  lastUsed: number;
}

const documents = new Map<string, Entry>();
const loading = new Map<string, Promise<CachedPdfDocument>>();

function evictBeyondLimit(): void {
  if (documents.size <= MAX_DOCS) return;
  const stale = [...documents.entries()].sort((a, b) => a[1].lastUsed - b[1].lastUsed);
  for (const [url, entry] of stale) {
    if (documents.size <= MAX_DOCS) break;
    documents.delete(url);
    void entry.task.destroy();
  }
}

async function load(fileUrl: string): Promise<CachedPdfDocument> {
  const response = await fetch(fileUrl);
  if (!response.ok) throw new Error(`originals store returned ${response.status}`);
  const data = new Uint8Array(await response.arrayBuffer());
  const task = pdfjs.getDocument({ data });
  const doc = await task.promise;
  const entry: Entry = { doc, task, pageTexts: new Map(), lastUsed: Date.now() };
  documents.set(fileUrl, entry);
  evictBeyondLimit();
  return entry;
}

/** Resolve the parsed document for a URL, sharing an in-flight load and reusing a cached one. */
export function acquirePdfDocument(fileUrl: string): Promise<CachedPdfDocument> {
  const cached = documents.get(fileUrl);
  if (cached) {
    cached.lastUsed = Date.now();
    return Promise.resolve(cached);
  }
  const inFlight = loading.get(fileUrl);
  if (inFlight) return inFlight;
  const promise = load(fileUrl).finally(() => {
    if (loading.get(fileUrl) === promise) loading.delete(fileUrl);
  });
  loading.set(fileUrl, promise);
  return promise;
}

/** Destroy every cached document (vault switch). */
export function clearPdfDocuments(): void {
  for (const entry of documents.values()) void entry.task.destroy();
  documents.clear();
  loading.clear();
}
