import { useEffect, useRef, useState } from "react";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import type { UnlistenFn } from "@tauri-apps/api/event";

const SOURCE_EXTENSIONS = [
  ".pdf", ".md", ".markdown", ".txt", ".html", ".htm", ".vtt", ".srt",
  ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".oga", ".opus", ".aac"
];

type Subscriber = {
  enabled: boolean;
  priority: number;
  onDrop: (paths: string[]) => void;
  onDragging: (dragging: boolean) => void;
};

const subscribers = new Map<symbol, Subscriber>();
let unlistenPromise: Promise<UnlistenFn> | null = null;

function activeSubscriber(): Subscriber | null {
  return [...subscribers.values()]
    .filter((subscriber) => subscriber.enabled)
    .sort((a, b) => b.priority - a.priority)[0] ?? null;
}

function setDragging(active: Subscriber | null, dragging: boolean) {
  for (const subscriber of subscribers.values()) {
    subscriber.onDragging(subscriber === active ? dragging : false);
  }
}

function ensureNativeListener() {
  if (unlistenPromise) return;
  unlistenPromise = getCurrentWebview().onDragDropEvent((event) => {
    const active = activeSubscriber();
    if (!active) return;
    if (event.payload.type === "enter" || event.payload.type === "over") {
      setDragging(active, true);
    } else if (event.payload.type === "leave") {
      setDragging(active, false);
    } else if (event.payload.type === "drop") {
      setDragging(active, false);
      const supported = event.payload.paths.filter(isSupportedSourceFile);
      if (supported.length > 0) active.onDrop(supported);
    }
  }).catch(() => () => {});
}

export function isSupportedSourceFile(path: string): boolean {
  const lower = path.toLowerCase();
  return SOURCE_EXTENSIONS.some((extension) => lower.endsWith(extension));
}

export function useSourceFileDrop({
  enabled = true,
  priority = 0,
  onDrop
}: {
  enabled?: boolean;
  priority?: number;
  onDrop: (paths: string[]) => void;
}): boolean {
  const [dragging, setDragging] = useState(false);
  const callbackRef = useRef(onDrop);
  callbackRef.current = onDrop;

  useEffect(() => {
    const id = Symbol("source-file-drop");
    subscribers.set(id, {
      enabled,
      priority,
      onDrop: (paths) => callbackRef.current(paths),
      onDragging: setDragging
    });
    ensureNativeListener();
    return () => {
      subscribers.delete(id);
      setDragging(false);
    };
  }, [enabled, priority]);

  return dragging;
}
