const MAX_IT = 28;

type JuliaFrameRequest = {
  id: number;
  cols: number;
  rows: number;
  cr: number;
  ci: number;
  reSpan: number;
  imSpan: number;
};

type JuliaFrameResponse = {
  id: number;
  cols: number;
  rows: number;
  iterations: Uint8Array;
};

let cachedCols = 0;
let cachedRows = 0;
let cachedReSpan = 0;
let cachedImSpan = 0;
let realCoordinates = new Float64Array(0);
let imaginaryCoordinates = new Float64Array(0);

function prepareCoordinates(cols: number, rows: number, reSpan: number, imSpan: number): void {
  if (
    cols === cachedCols &&
    rows === cachedRows &&
    reSpan === cachedReSpan &&
    imSpan === cachedImSpan
  ) {
    return;
  }

  cachedCols = cols;
  cachedRows = rows;
  cachedReSpan = reSpan;
  cachedImSpan = imSpan;
  realCoordinates = new Float64Array(cols);
  imaginaryCoordinates = new Float64Array(rows);

  const realStep = reSpan / Math.max(1, cols - 1);
  const imaginaryStep = imSpan / Math.max(1, rows - 1);
  let value = -reSpan * 0.5;
  for (let x = 0; x < cols; x++, value += realStep) realCoordinates[x] = value;
  value = -imSpan * 0.5;
  for (let y = 0; y < rows; y++, value += imaginaryStep) imaginaryCoordinates[y] = value;
}

function computeFrame(request: JuliaFrameRequest): Uint8Array {
  const { cols, rows, cr, ci, reSpan, imSpan } = request;
  prepareCoordinates(cols, rows, reSpan, imSpan);
  const result = new Uint8Array(cols * rows);
  let offset = 0;

  for (let y = 0; y < rows; y++) {
    const initialZi = imaginaryCoordinates[y];
    for (let x = 0; x < cols; x++) {
      let zr = realCoordinates[x];
      let zi = initialZi;
      let zr2 = zr * zr;
      let zi2 = zi * zi;
      let iteration = 0;

      while (iteration < MAX_IT && zr2 + zi2 <= 4) {
        zi = (zr + zr) * zi + ci;
        zr = zr2 - zi2 + cr;
        zr2 = zr * zr;
        zi2 = zi * zi;
        iteration++;
      }
      result[offset++] = iteration;
    }
  }

  return result;
}

self.onmessage = (event: MessageEvent<JuliaFrameRequest>) => {
  const request = event.data;
  const iterations = computeFrame(request);
  const response: JuliaFrameResponse = {
    id: request.id,
    cols: request.cols,
    rows: request.rows,
    iterations
  };
  self.postMessage(response, { transfer: [iterations.buffer] });
};

export {};
