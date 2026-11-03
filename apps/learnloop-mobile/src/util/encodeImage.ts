// §4.4: the server rejects HEIC, so the app re-encodes through a canvas, which also bakes in the
// orientation. An edge of 4096 is a `keep` bound: well past what a handwritten page needs, and it
// keeps an upload under the host's 20 MB cap on a 48 MP camera.
const MAX_EDGE = 4096;
const JPEG_QUALITY = 0.88;

export async function encodeImageToJpeg(file: Blob): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_EDGE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext("2d");
  if (!context) throw new Error("This browser can't prepare the image.");
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("This browser can't prepare the image."))), "image/jpeg", JPEG_QUALITY);
  });
}
