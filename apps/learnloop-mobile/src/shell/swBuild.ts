// The service worker's cache is keyed by the build (mobile v2 §5.2, §6.1). `public/sw.js` names a
// placeholder; the build writes the hash of the built `index.html` into its copy. The shell names
// every hashed asset, so any change to the app changes the hash: the browser sees a new worker,
// and its `activate` drops the previous build's cache. The test suite runs the source with "dev".
export const BUILD_MARKER = 'const BUILD = "dev";';

export function stampServiceWorker(source: string, buildHash: string): string {
  if (!/^[0-9a-f]{8,64}$/.test(buildHash)) throw new Error(`Not a build hash: ${buildHash}`);
  const at = source.indexOf(BUILD_MARKER);
  if (at < 0 || source.indexOf(BUILD_MARKER, at + 1) >= 0) throw new Error("sw.js must name its build placeholder exactly once.");
  return source.replace(BUILD_MARKER, `const BUILD = "${buildHash}";`);
}
