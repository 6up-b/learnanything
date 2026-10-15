// Synthetic PDFs for the selection tests (reader-pdf-selection): real PDF
// files, written here, parsed by the real pdf.js. No book's text is in them.
//
// Coordinates are top-left PDF points like the extraction's boxes: `y` is a
// line's baseline measured from the top of the page.

export interface PdfText {
  x: number;
  y: number;
  size: number;
  text: string;
}

export interface PdfPageSpec {
  width?: number;
  height?: number;
  /** Text drawn in this order (the content stream's order, which need not be
   *  reading order). */
  texts?: PdfText[];
  /** A full-page grey image and no text: a scanned page. */
  scanned?: boolean;
}

function escapePdf(text: string): string {
  return text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

/** A PDF with Helvetica text (and grey images for scanned pages). */
export function buildPdf(pages: readonly PdfPageSpec[]): Uint8Array {
  const objects: string[] = [];
  const add = (body: string) => {
    objects.push(body);
    return objects.length;
  };
  const font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>");
  const image = add(
    "<< /Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceGray /BitsPerComponent 8 /Length 4 >>\nstream\n °° \nendstream",
  );
  const contents = pages.map((page) => {
    const height = page.height ?? 792;
    const width = page.width ?? 612;
    const ops = page.scanned
      ? [`q ${width} 0 0 ${height} 0 0 cm /Im1 Do Q`]
      : (page.texts ?? []).map((t) => `BT /F1 ${t.size} Tf ${t.x} ${height - t.y} Td (${escapePdf(t.text)}) Tj ET`);
    const stream = ops.join("\n");
    return add(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  });
  const pagesId = objects.length + pages.length + 1;
  const kids = pages.map((page, index) =>
    add(
      `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${page.width ?? 612} ${page.height ?? 792}] ` +
        `/Resources << /Font << /F1 ${font} 0 R >> /XObject << /Im1 ${image} 0 R >> >> /Contents ${contents[index]} 0 R >>`,
    ),
  );
  const pagesObject = add(`<< /Type /Pages /Kids [${kids.map((kid) => `${kid} 0 R`).join(" ")}] /Count ${kids.length} >>`);
  if (pagesObject !== pagesId) throw new Error("page tree numbering");
  const catalog = add(`<< /Type /Catalog /Pages ${pagesObject} 0 R >>`);
  let out = "%PDF-1.4\n";
  const offsets: number[] = [];
  objects.forEach((body, index) => {
    offsets.push(out.length);
    out += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = out.length;
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  out += offsets.map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
  out += `trailer\n<< /Size ${objects.length + 1} /Root ${catalog} 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Uint8Array.from(out, (ch) => ch.charCodeAt(0) & 0xff);
}

export interface ParsedPage {
  /** Zero-based, as the extraction numbers pages. */
  page: number;
  items: Array<{ str: string; transform: number[]; width: number; height: number; hasEOL?: boolean }>;
  transform: number[];
  width: number;
  height: number;
}

/** Each page's text content and scale-1 viewport, read by the real pdf.js. */
export async function readPdf(bytes: Uint8Array): Promise<ParsedPage[]> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  const task = pdfjs.getDocument({ data: bytes.slice(), disableFontFace: true, verbosity: 0 });
  const doc = await task.promise;
  const out: ParsedPage[] = [];
  for (let number = 1; number <= doc.numPages; number++) {
    const page = await doc.getPage(number);
    const viewport = page.getViewport({ scale: 1 });
    const content = await page.getTextContent();
    out.push({
      page: number - 1,
      items: content.items.flatMap((item) => ("str" in item ? [{ str: item.str, transform: item.transform, width: item.width, height: item.height, hasEOL: item.hasEOL }] : [])),
      transform: viewport.transform,
      width: viewport.width,
      height: viewport.height,
    });
  }
  await task.destroy();
  return out;
}
