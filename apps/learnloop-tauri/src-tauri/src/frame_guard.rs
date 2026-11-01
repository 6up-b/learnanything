//! Reader RW5d P2, the sketch compartment: defense in depth in the shell
//! (spec_reader_show_me_figures_v1 §9.4, §9b.5 "the shell's command handlers
//! also refuse an invoke whose requesting frame URL isn't the app's own
//! document").
//!
//! The boundary is in WebKit: the sketch engine runs in a Worker created from a
//! blob inside a sandboxed, opaque-origin frame whose CSP has
//! `connect-src 'none'`, so its requests never leave the webview. This module
//! is the second line, and it is narrower than one would like, because of what
//! Tauri 2.11 exposes (recorded in docs/reviews/reader-rw5d-p2-sketch-compartment.md):
//!
//! - There is no hook *before* Tauri's `ipc:` protocol handler or its invoke
//!   dispatcher (`Webview::on_message`). Registering our own `ipc` scheme would
//!   pre-empt Tauri's, but that means re-implementing Tauri's IPC protocol; not
//!   proportionate.
//! - The app's own invoke handler is reachable, after Tauri's invoke-key and
//!   ACL checks and before any LearnLoop command runs: `refusal_reason` below
//!   refuses there. It covers LearnLoop's commands, not the core or plugin ones
//!   (`plugin:…`), which Tauri dispatches without passing through it.
//! - That check reads what WebKit reports (Origin, Referer), which identifies
//!   a frame only coarsely: Fetch lets a context omit its Referer (refused:
//!   the app's document always sends one) or replace it with any same-origin
//!   URL (not detectable here). The document itself is authenticated by
//!   Tauri's invoke key, which only the main frame's init script holds, in a
//!   closure (Codex review F1, docs/reviews/reader-rw5d-p2-sketch-compartment-codex-review.md).
//! - The WebKit script-message path (`window.webkit.messageHandlers.ipc`) is
//!   exposed to every frame, and wry forwards each message with the TOP
//!   document's URL, so no handler can tell a frame from the app. On Linux the
//!   app sends every invoke over the `ipc:` custom protocol and uses that path
//!   only as a fallback, so the shell unregisters it (main.rs).
//! - The header refusals are transport-aware, by platform. Tauri falls back to
//!   that script-message path when a custom-protocol fetch fails, and on the
//!   fallback it builds the invoke's headers from the message's own
//!   `options.headers`, which LearnLoop's `invoke(command, args)` leaves empty:
//!   a legitimate top-document call arrives with no Origin and no Referer. On
//!   Linux the fallback is unregistered, so every invoke the app makes comes over
//!   the custom protocol with both headers, and a missing one is refused. On
//!   Windows and macOS the fallback stays registered, so only a header that is
//!   present and names a frame or a foreign origin is refused there; an absent
//!   header passes (orchestrator scoped verify, Sol job 20261101-153827-RFAdme).

use tauri::http::HeaderMap;
use tauri::Url;

/// The app's own origins, serialized as an Origin header carries them:
/// `tauri://localhost` (Linux, macOS), `http(s)://tauri.localhost` (Windows,
/// Android) and the loopback dev server (`devUrl`, `http://localhost:1420`).
/// None for anything else.
fn app_origin(url: &Url) -> Option<String> {
    let host = url.host_str()?;
    let known = match url.scheme() {
        "tauri" => host == "localhost",
        "http" | "https" => {
            host == "tauri.localhost"
                || (url.scheme() == "http" && matches!(host, "localhost" | "127.0.0.1" | "[::1]"))
        }
        _ => false,
    };
    if !known || !url.username().is_empty() || url.password().is_some() {
        return None;
    }
    Some(match url.port() {
        Some(port) => format!("{}://{}:{}", url.scheme(), host, port),
        None => format!("{}://{}", url.scheme(), host),
    })
}

/// Which header rules apply: whether Tauri's script-message IPC fallback can
/// deliver a legitimate invoke without Origin and Referer (see the module
/// comment). A parameter, not only a `cfg`, so both branches are tested on any
/// machine.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Platform {
    /// The fallback is unregistered (main.rs): every app invoke carries both
    /// headers, so a missing one is refused.
    Linux,
    /// Windows and macOS: the fallback stays registered and carries no headers
    /// of its own, so an absent header passes and only a present one that
    /// names a frame or a foreign origin is refused.
    FallbackRegistered,
}

/// The platform this shell was built for.
pub const PLATFORM: Platform = if cfg!(target_os = "linux") {
    Platform::Linux
} else {
    Platform::FallbackRegistered
};

/// Why an invoke is refused, or None when its Origin is one of the app's and
/// its Referer is the app's own top document on that origin. On
/// `Platform::FallbackRegistered` an absent (or empty) Origin or Referer is not
/// a reason: the script-message fallback sends neither for the app's own calls.
///
/// This is a filter on what WebKit reports, not authentication: Fetch lets a
/// context omit its Referer (`referrer: ""`, refused on Linux because the app's
/// document always sends one there) or name any same-origin URL instead (which
/// this layer can't tell from the document), and on the fallback the headers are
/// whatever the message names. What authenticates the document is Tauri's
/// invoke key, held only in a closure of the main frame's init script; no
/// Worker or frame has it (docs/reviews/reader-rw5d-g-sm14-probe.md).
pub fn refusal_on(
    platform: Platform,
    origin: Option<&str>,
    referer: Option<&str>,
) -> Option<&'static str> {
    let strict = platform == Platform::Linux;
    let origin = match origin.map(str::trim) {
        None => None,
        Some("") if !strict => None,
        Some(value) => Some(value),
    };
    let app = match origin {
        None if strict => return Some("the request has no Origin"),
        None => None,
        // An opaque origin: a sandboxed frame (the sketch compartment) or a data: document.
        Some(value) if value.eq_ignore_ascii_case("null") => {
            return Some("the request came from an opaque-origin frame");
        }
        Some(value) => match Url::parse(value).ok().as_ref().and_then(app_origin) {
            Some(app) => Some(app),
            None => return Some("the request's Origin is not the app's"),
        },
    };
    let Some(referer) = referer.map(str::trim).filter(|value| !value.is_empty()) else {
        // The app's document always sends one over the custom protocol (every
        // app call in both G-SM14 runs); the fallback sends none.
        return strict
            .then_some("the request has no Referer, which the app's document always sends");
    };
    let Ok(url) = Url::parse(referer) else {
        return Some("the request's Referer is not a URL");
    };
    match url.scheme() {
        // Blob workers and frames, srcdoc documents.
        "blob" | "data" | "about" | "filesystem" | "javascript" => {
            return Some("the request came from a worker or a frame, not the app's document");
        }
        _ => {}
    }
    let referer_origin = app_origin(&url);
    match &app {
        Some(app) if referer_origin.as_deref() != Some(app.as_str()) => {
            return Some("the request's Referer is not on its Origin");
        }
        None if referer_origin.is_none() => return Some("the request's Referer is not the app's"),
        _ => {}
    }
    // The app's document is "/" or "/index.html" (and any extension-less route);
    // a URL-loaded Worker's script (`/assets/…js`) or another HTML page (the
    // sketch frame) is not.
    let last = url.path().rsplit('/').next().unwrap_or("");
    if !last.is_empty() && last != "index.html" && last.contains('.') {
        return Some("the request came from a worker or a frame, not the app's document");
    }
    None
}

fn header<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    headers.get(name).and_then(|value| value.to_str().ok())
}

/// `refusal_on` for an invoke's request headers, on this build's platform.
/// Page script can't set Origin or Referer as custom-protocol headers, but
/// Fetch lets it omit the Referer or replace it with a same-origin URL, and on
/// the script-message fallback the headers are the message's own (see
/// `refusal_on`).
pub fn refusal_reason(headers: &HeaderMap) -> Option<&'static str> {
    refusal_reason_on(PLATFORM, headers)
}

/// `refusal_reason` with the platform as a parameter (tests run both).
pub fn refusal_reason_on(platform: Platform, headers: &HeaderMap) -> Option<&'static str> {
    for name in ["origin", "referer"] {
        if let Some(value) = headers.get(name) {
            if value.to_str().is_err() {
                return Some("the request's Origin or Referer is not text");
            }
        }
    }
    refusal_on(
        platform,
        header(headers, "origin"),
        header(headers, "referer"),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use tauri::http::HeaderValue;

    #[test]
    fn the_apps_own_document_passes() {
        for (origin, referer) in [
            (Some("tauri://localhost"), Some("tauri://localhost")),
            (Some("tauri://localhost"), Some("tauri://localhost/")),
            (
                Some("tauri://localhost"),
                Some("tauri://localhost/index.html"),
            ),
            (
                Some("http://tauri.localhost"),
                Some("http://tauri.localhost/"),
            ),
            (
                Some("http://localhost:1420"),
                Some("http://localhost:1420/"),
            ),
            (
                Some("tauri://localhost"),
                Some("tauri://localhost/reader/route"),
            ),
            (
                Some("https://tauri.localhost"),
                Some("https://tauri.localhost/index.html"),
            ),
            (
                Some("http://127.0.0.1:1420"),
                Some("http://127.0.0.1:1420/"),
            ),
        ] {
            assert_eq!(
                refusal_on(Platform::Linux, origin, referer),
                None,
                "{origin:?} {referer:?}"
            );
        }
    }

    #[test]
    fn frames_and_workers_are_refused() {
        // Every Referer the G-SM14 probe saw from a Worker, and the compartment's own.
        for (origin, referer) in [
            (Some("null"), Some("tauri://localhost/")),
            (Some("null"), None),
            (Some("NULL "), None),
            (
                Some("tauri://localhost"),
                Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js"),
            ),
            (
                Some("tauri://localhost"),
                Some("blob:tauri://localhost/475eccc0-0dbe-45be-8fd9-29b96144c0d1"),
            ),
            (
                Some("null"),
                Some("blob:null/bd98b893-5790-4e74-b773-57e669cf2440"),
            ),
            (
                Some("tauri://localhost"),
                Some("tauri://localhost/sketch-frame.html"),
            ),
            (Some("tauri://localhost"), Some("about:srcdoc")),
            (Some("tauri://localhost"), Some("data:text/html,x")),
            (Some("tauri://localhost"), Some("not a url")),
        ] {
            assert!(
                refusal_on(Platform::Linux, origin, referer).is_some(),
                "{origin:?} {referer:?}"
            );
        }
    }

    #[test]
    fn omitted_headers_and_unexpected_origins_are_refused() {
        // Codex F1: a Worker's `fetch(url, {referrer: ""})` omits the Referer
        // while keeping the app's Origin; the app's own document always sends
        // both (G-SM14 runs: 23 of 23 and every app call, `tauri://localhost`).
        for (origin, referer) in [
            (Some("tauri://localhost"), None),
            (Some("tauri://localhost"), Some("")),
            (None, Some("tauri://localhost/")),
            (None, None),
            (Some(""), Some("tauri://localhost/")),
            // Not one of the app's origins.
            (Some("https://example.com"), Some("https://example.com/")),
            (
                Some("http://localhost.example.com"),
                Some("http://localhost.example.com/"),
            ),
            (Some("file://"), Some("file:///index.html")),
            (Some("ipc://localhost"), Some("ipc://localhost/")),
            // Origin and Referer disagree.
            (Some("tauri://localhost"), Some("http://tauri.localhost/")),
            (
                Some("http://localhost:1420"),
                Some("http://localhost:1421/"),
            ),
        ] {
            assert!(
                refusal_on(Platform::Linux, origin, referer).is_some(),
                "{origin:?} {referer:?}"
            );
        }
    }

    #[test]
    fn a_replaced_same_origin_referrer_is_not_this_layers_to_catch() {
        // Fetch lets a same-origin context name any same-origin URL as its
        // referrer, so a Worker holding the invoke key could pass as the app's
        // document here. What this layer can't tell apart, Tauri's invoke key
        // does: it lives in a closure of the main frame's init script only
        // (tauri 2.11.2 manager/webview.rs `main_frame_script`), no Worker or
        // frame has it (G-SM14: absent, every keyless invoke refused at
        // `on_message`), so a Worker that has it was handed it by a compromised
        // document, which could run the command itself. Pinned so the gap stays
        // written down.
        assert_eq!(
            refusal_on(
                Platform::Linux,
                Some("tauri://localhost"),
                Some("tauri://localhost/")
            ),
            None
        );
    }

    #[test]
    fn reads_the_request_headers() {
        let linux = |headers: &HeaderMap| refusal_reason_on(Platform::Linux, headers);
        let mut headers = HeaderMap::new();
        assert!(linux(&headers).is_some());
        headers.insert("origin", HeaderValue::from_static("tauri://localhost"));
        headers.insert("referer", HeaderValue::from_static("tauri://localhost"));
        assert_eq!(linux(&headers), None);
        headers.insert("origin", HeaderValue::from_static("null"));
        assert!(linux(&headers).is_some());
        headers.insert("origin", HeaderValue::from_static("tauri://localhost"));
        headers.insert(
            "referer",
            HeaderValue::from_bytes(b"tauri://localhost/\xff").unwrap(),
        );
        assert!(linux(&headers).is_some());
    }

    #[test]
    fn linux_refuses_absent_headers() {
        // Linux unregisters the script-message fallback (main.rs), so the app's
        // every invoke comes over the custom protocol carrying both headers.
        for (origin, referer) in [
            (None, None),
            (Some("tauri://localhost"), None),
            (None, Some("tauri://localhost/")),
            (Some(""), Some("")),
        ] {
            assert!(
                refusal_on(Platform::Linux, origin, referer).is_some(),
                "{origin:?} {referer:?}"
            );
        }
        assert!(refusal_reason_on(Platform::Linux, &HeaderMap::new()).is_some());
    }

    #[test]
    fn with_the_fallback_registered_absent_headers_pass() {
        // Sol scoped verify (20261101-153827-RFAdme): on Windows and macOS
        // Tauri 2.11.2 falls back to `window.ipc.postMessage` when the
        // custom-protocol fetch fails and builds the invoke's headers from the
        // message's `options.headers`; LearnLoop's `invoke(command, args)`
        // supplies none, so a legitimate top-document call has neither header.
        let other = Platform::FallbackRegistered;
        for (origin, referer) in [
            (None, None),
            (Some(""), None),
            (None, Some("")),
            (Some(" "), Some(" ")),
            // A present header that is the app's own still passes.
            (Some("tauri://localhost"), None),
            (None, Some("tauri://localhost/")),
            (None, Some("http://tauri.localhost/index.html")),
            (
                Some("http://tauri.localhost"),
                Some("http://tauri.localhost/"),
            ),
        ] {
            assert_eq!(
                refusal_on(other, origin, referer),
                None,
                "{origin:?} {referer:?}"
            );
        }
        // The fallback's request, as Tauri builds it: an empty header map.
        assert_eq!(refusal_reason_on(other, &HeaderMap::new()), None);
    }

    #[test]
    fn with_the_fallback_registered_an_explicit_frame_or_foreign_origin_is_refused() {
        let other = Platform::FallbackRegistered;
        for (origin, referer) in [
            // An explicit opaque origin, with or without a Referer.
            (Some("null"), None),
            (Some("NULL "), Some("tauri://localhost/")),
            // A foreign origin.
            (Some("https://example.com"), None),
            (Some("https://example.com"), Some("https://example.com/")),
            (Some("ipc://localhost"), None),
            (Some("not a url"), None),
            // A Referer, when present, that names a worker, a frame or a foreign page.
            (
                None,
                Some("blob:tauri://localhost/475eccc0-0dbe-45be-8fd9-29b96144c0d1"),
            ),
            (None, Some("about:srcdoc")),
            (None, Some("data:text/html,x")),
            (None, Some("tauri://localhost/sketch-frame.html")),
            (
                None,
                Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js"),
            ),
            (None, Some("https://example.com/")),
            (None, Some("not a url")),
            // Both present and disagreeing.
            (Some("tauri://localhost"), Some("http://tauri.localhost/")),
        ] {
            assert!(
                refusal_on(other, origin, referer).is_some(),
                "{origin:?} {referer:?}"
            );
        }
        let mut headers = HeaderMap::new();
        headers.insert("origin", HeaderValue::from_static("null"));
        assert!(refusal_reason_on(other, &headers).is_some());
        let mut headers = HeaderMap::new();
        headers.insert("origin", HeaderValue::from_bytes(b"tauri://\xff").unwrap());
        assert!(refusal_reason_on(other, &headers).is_some());
    }

    #[test]
    fn this_build_uses_its_platforms_rules() {
        assert_eq!(
            PLATFORM == Platform::Linux,
            cfg!(target_os = "linux"),
            "the header rules follow the build target"
        );
    }
}
