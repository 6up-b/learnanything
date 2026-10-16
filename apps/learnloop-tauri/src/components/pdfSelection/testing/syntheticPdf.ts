// Synthetic PDFs for the selection tests (reader-pdf-selection): real PDF
// files, written here, parsed by the real pdf.js. No book's text is in them.
//
// Coordinates are top-left PDF points like the extraction's boxes: `y` is a
// line's baseline measured from the top of the page.

/** The fonts a synthetic page draws with: three of the standard 14 (no
 *  file: pdf.js uses its own metrics for them, the widths every PDF reader
 *  uses), and a Type3 font whose widths are nothing like any of them ("a" 900
 *  units, "b" 100, a space 250), as an embedded font's need not be. */
export type PdfFont = "Helvetica" | "Courier" | "Times-Roman" | "Type3";

const FONT_KEYS: Record<PdfFont, string> = { Helvetica: "F1", Courier: "F2", "Times-Roman": "F3", Type3: "F4" };

export interface PdfText {
  x: number;
  y: number;
  size: number;
  text: string;
  /** Helvetica unless said. */
  font?: PdfFont;
}

export interface PdfPageSpec {
  width?: number;
  height?: number;
  /** Text drawn in this order (the content stream's order, which need not be
   *  reading order). */
  texts?: PdfText[];
  /** A full-page grey image and no text: a scanned page. */
  scanned?: boolean;
  /** Content-stream operators drawn after `texts`, as written (PDF space:
   *  the origin at the bottom left). Fonts by `fontKey`; the form XObject
   *  /Fm1 draws "Form" in Courier 10 at its own origin, through its
   *  /Matrix [1 0 0 1 300 100]. */
  raw?: string[];
}

/** The resource name a raw content stream uses for a font. */
export function fontKey(font: PdfFont): string {
  return FONT_KEYS[font];
}

function escapePdf(text: string): string {
  return text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

/** A PDF with text in the fonts above (and grey images for scanned pages). */
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
  const courier = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>");
  const times = add("<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>");
  const blank = "0 0 0 0 0 0 d1";
  const glyph = add(`<< /Length ${blank.length} >>\nstream\n${blank}\nendstream`);
  const type3 = add(
    `<< /Type /Font /Subtype /Type3 /FontBBox [0 0 1000 1000] /FontMatrix [0.001 0 0 0.001 0 0] ` +
      `/CharProcs << /space ${glyph} 0 R /a ${glyph} 0 R /b ${glyph} 0 R >> ` +
      `/Encoding << /Type /Encoding /Differences [32 /space 97 /a /b] >> /FirstChar 32 /LastChar 98 ` +
      `/Widths [250 ${Array(64).fill(0).join(" ")} 900 100] /Resources << >> >>`,
  );
  const formStream = "BT /F2 10 Tf 0 0 Td (Form) Tj ET";
  const form = add(
    `<< /Type /XObject /Subtype /Form /BBox [0 0 200 50] /Matrix [1 0 0 1 300 100] ` +
      `/Resources << /Font << /F2 ${courier} 0 R >> >> /Length ${formStream.length} >>\nstream\n${formStream}\nendstream`,
  );
  const contents = pages.map((page) => {
    const height = page.height ?? 792;
    const width = page.width ?? 612;
    const ops = page.scanned
      ? [`q ${width} 0 0 ${height} 0 0 cm /Im1 Do Q`]
      : (page.texts ?? []).map(
          (t) => `BT /${FONT_KEYS[t.font ?? "Helvetica"]} ${t.size} Tf ${t.x} ${height - t.y} Td (${escapePdf(t.text)}) Tj ET`,
        );
    ops.push(...(page.raw ?? []));
    const stream = ops.join("\n");
    return add(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  });
  const pagesId = objects.length + pages.length + 1;
  const kids = pages.map((page, index) =>
    add(
      `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${page.width ?? 612} ${page.height ?? 792}] ` +
        `/Resources << /Font << /F1 ${font} 0 R /F2 ${courier} 0 R /F3 ${times} 0 R /F4 ${type3} 0 R >> ` +
        `/XObject << /Im1 ${image} 0 R /Fm1 ${form} 0 R >> >> /Contents ${contents[index]} 0 R >>`,
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
  items: Array<{ str: string; transform: number[]; width: number; height: number; hasEOL?: boolean; fontName?: string }>;
  /** Each font's fallback family, as pdf.js's text content says it. */
  styles: Record<string, { fontFamily: string }>;
  transform: number[];
  width: number;
  height: number;
}

/** A page as pdf.js reads it for drawing: its operator list (glyphs with
 *  their own widths) and its fonts, by loaded name. */
export interface PaintedPage {
  page: number;
  opList: { fnArray: number[]; argsArray: unknown[] };
  fonts: Map<string, { fontMatrix?: number[]; isType3Font?: boolean; vertical?: boolean; bbox?: number[] }>;
  transform: number[];
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
      items: content.items.flatMap((item) =>
        "str" in item
          ? [{ str: item.str, transform: item.transform, width: item.width, height: item.height, hasEOL: item.hasEOL, fontName: item.fontName }]
          : [],
      ),
      styles: Object.fromEntries(Object.entries(content.styles).map(([name, style]) => [name, { fontFamily: style.fontFamily }])),
      transform: viewport.transform,
      width: viewport.width,
      height: viewport.height,
    });
  }
  await task.destroy();
  return out;
}

/** Each page's operator list and fonts, read by the real pdf.js as it reads
 *  them to draw (annotations left out), with pdf.js's operator ids. */
export async function paintPdf(bytes: Uint8Array): Promise<{ pages: PaintedPage[]; ops: Record<string, number> }> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  const task = pdfjs.getDocument({ data: bytes.slice(), disableFontFace: true, verbosity: 0 });
  const doc = await task.promise;
  const pages: PaintedPage[] = [];
  for (let number = 1; number <= doc.numPages; number++) {
    const page = await doc.getPage(number);
    const opList = await page.getOperatorList({ annotationMode: pdfjs.AnnotationMode.DISABLE });
    const fonts: PaintedPage["fonts"] = new Map();
    opList.fnArray.forEach((fn, index) => {
      if (fn !== pdfjs.OPS.setFont) return;
      const name = String((opList.argsArray[index] as unknown[])[0]);
      const font = page.commonObjs.get(name) as { fontMatrix?: number[]; isType3Font?: boolean; vertical?: boolean; bbox?: number[] };
      fonts.set(name, { fontMatrix: font.fontMatrix, isType3Font: font.isType3Font, vertical: font.vertical, bbox: font.bbox });
    });
    pages.push({
      page: number - 1,
      opList: { fnArray: [...opList.fnArray], argsArray: [...opList.argsArray] },
      fonts,
      transform: page.getViewport({ scale: 1 }).transform,
    });
  }
  await task.destroy();
  return { pages, ops: { ...pdfjs.OPS } };
}
