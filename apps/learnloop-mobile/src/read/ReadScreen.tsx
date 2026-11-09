// The Read place (mobile v2 §4.2, stage V4): the books the phone's Reader opens, the one last read first
// (*Continue reading*, which lands where the shared reading history says), then the book. Read only: adding a
// book and its administration are the desktop's (J15; V7 adds *Add a link* through capture).
import { useEffect, useState } from "react";
import type { CommandError } from "@desktop/api/dto";
import { phone, type PhoneBookDto } from "../api/phone";
import { getLatest, putLatest } from "../store/displayCache";
import { readPlaces, type LocalPlace } from "./readerCache";
import type { ReaderTarget } from "./ReaderScreen";

export function ReadScreen({ onOpen, onError }: { onOpen: (target: ReaderTarget) => void; onError: (error: unknown) => void }) {
  const [books, setBooks] = useState<PhoneBookDto[] | null>(null);
  const [stale, setStale] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [places] = useState<LocalPlace[]>(() => readPlaces());

  useEffect(() => {
    let cancelled = false;
    phone.library().then(
      (library) => {
        if (cancelled) return;
        setBooks(library.sources);
        void putLatest("library", library.sources).catch(() => undefined);
      },
      async (error: CommandError) => {
        if (cancelled) return;
        const cached = await getLatest<PhoneBookDto[]>("library").catch(() => null);
        if (cancelled) return;
        if (cached) {
          setBooks(cached);
          setStale(true);
          return;
        }
        if (error?.code === "phone_reader_off") setProblem("Reading is on the desktop for now.");
        else if (error?.code === "desktop_offline") setProblem("Your books open here when the desktop is reachable.");
        else {
          setProblem("Your books couldn't be listed.");
          onError(error);
        }
      }
    );
    return () => {
      cancelled = true;
    };
    // Once per visit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const remembered = places[0] ?? null;
  // The book's reading now (a book read again has a new one), when the list knows it.
  const last = remembered
    ? { ...remembered, extractionId: books?.find((book) => book.sourceId === remembered.sourceId)?.extractionId ?? remembered.extractionId }
    : null;
  return (
    <div className="screen">
      <h1>Read</h1>
      {stale ? <p className="dim" role="status">The list on this phone; the desktop isn't reachable.</p> : null}
      {last ? (
        <div className="actions">
          <button className="primary block" type="button"
            onClick={() => onOpen({ extractionId: last.extractionId, sourceId: last.sourceId, title: last.title })}>
            Continue reading {last.title}
          </button>
        </div>
      ) : null}
      {problem ? <p className="dim" role="status">{problem}</p> : null}
      {books === null && !problem ? <p className="dim" role="status">Reading your books…</p> : null}
      {books && books.length === 0 ? <p className="dim">No book is ready to read yet. Add one on the desktop.</p> : null}
      {books && books.length ? (
        <ul className="list" aria-label="Your books">
          {books.map((book) => (
            <li key={book.sourceId}>
              <button type="button" onClick={() => onOpen({ extractionId: book.extractionId, sourceId: book.sourceId, title: book.title })}>
                <span>{book.title}</span>
                {book.subjectTitle ? <span className="dim"> · {book.subjectTitle}</span> : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
