import "fake-indexeddb/auto";
import { IDBFactory } from "fake-indexeddb";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";
import { resetTimingForTests } from "../api/http";
import { resetConnectionForTests } from "../shell/connection";
import { resetCredentialForTests } from "../store/credential";
import { resetDbForTests } from "../store/db";

// Node's own `localStorage` global can shadow jsdom's with nothing behind it.
if (typeof globalThis.localStorage?.clear !== "function") {
  const values = new Map<string, string>();
  const storage = {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, String(value)),
    removeItem: (key: string) => void values.delete(key),
    clear: () => values.clear(),
    key: (index: number) => [...values.keys()][index] ?? null,
    get length() {
      return values.size;
    }
  };
  Object.defineProperty(globalThis, "localStorage", { value: storage, configurable: true });
}

beforeEach(() => {
  // A fresh device for every test.
  globalThis.indexedDB = new IDBFactory();
  resetDbForTests();
  resetCredentialForTests();
  resetConnectionForTests();
  resetTimingForTests();
  localStorage.clear();
  // A fresh app opens on Today: the fragment one test left would open another place.
  window.history.replaceState(null, "", "/app/");
  delete document.documentElement.dataset.theme;
});

afterEach(() => cleanup());
