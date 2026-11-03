import "fake-indexeddb/auto";
import { IDBFactory } from "fake-indexeddb";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";
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
  localStorage.clear();
});

afterEach(() => cleanup());
