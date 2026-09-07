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
const pendingFetches = new Set<AbortController>();
const pendingTasks = new Set<PDFDocumentLoadingTask>();
const destruction = new WeakMap<PDFDocumentLoadingTask, Promise<void>>();

function destroyTask(task: PDFDocumentLoadingTask): Promise<void> {
  const existing = destruction.get(task);
  if (existing) return existing;
  // Cleanup must not mask a parse error or reject an unobserved eviction.
  const promise = Promise.resolve().then(() => task.destroy()).catch(() => undefined);
  destruction.set(task, promise);
  return promise;
}
// Bumped by clearPdfDocuments(): a load that started before a clear must not
// install its (previous-vault) document afterwards.
let generation = 0;

function evictBeyondLimit(): void {
  if (documents.size <= MAX_DOCS) return;
  const stale = [...documents.entries()].sort((a, b) => a[1].lastUsed - b[1].lastUsed);
  for (const [url, entry] of stale) {
    if (documents.size <= MAX_DOCS) break;
    documents.delete(url);
    void destroyTask(entry.task);
  }
}

async function load(fileUrl: string): Promise<CachedPdfDocument> {
  const startedIn = generation;
  const controller = new AbortController();
  pendingFetches.add(controller);
  let data: Uint8Array;
  let pdfjs: typeof import("pdfjs-dist");
  try {
    const [response, module] = await Promise.all([fetch(fileUrl, { signal: controller.signal }), import("pdfjs-dist")]);
    if (!response.ok) throw new Error(`originals store returned ${response.status}`);
    data = new Uint8Array(await response.arrayBuffer());
    pdfjs = module;
  } finally {
    pendingFetches.delete(controller);
  }
  if (startedIn !== generation) throw new Error("PDF document cache was cleared while loading");
  const task = pdfjs.getDocument({ data });
  pendingTasks.add(task);
  let doc: PDFDocumentProxy;
  try {
    doc = await task.promise;
  } catch (error) {
    await destroyTask(task);
    throw error;
  } finally {
    pendingTasks.delete(task);
  }
  const entry: Entry = { doc, task, pageTexts: new Map(), lastUsed: Date.now() };
  const existing = documents.get(fileUrl);
  if (startedIn !== generation || existing) {
    // Cleared mid-load, or a concurrent load already installed this URL: the
    // worker-side document would otherwise leak with nothing referencing it.
    void destroyTask(task);
    if (existing && startedIn === generation) return existing;
    throw new Error("PDF document cache was cleared while loading");
  }
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
  generation += 1;
  for (const controller of pendingFetches) controller.abort();
  pendingFetches.clear();
  for (const task of pendingTasks) void destroyTask(task);
  pendingTasks.clear();
  for (const entry of documents.values()) void destroyTask(entry.task);
  documents.clear();
  loading.clear();
}
