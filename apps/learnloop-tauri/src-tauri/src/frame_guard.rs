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
//! - The WebKit script-message path (`window.webkit.messageHandlers.ipc`) is
//!   exposed to every frame, and wry forwards each message with the TOP
//!   document's URL, so no handler can tell a frame from the app. On Linux the
//!   app sends every invoke over the `ipc:` custom protocol and uses that path
//!   only as a fallback, so the shell unregisters it (main.rs).

use tauri::http::HeaderMap;
use tauri::Url;

/// Why an invoke is refused, or None when its Origin and Referer are the app's
/// own top document's (or absent).
pub fn refusal(origin: Option<&str>, referer: Option<&str>) -> Option<&'static str> {
    if let Some(origin) = origin {
        // An opaque origin: a sandboxed frame (the sketch compartment) or a data: document.
        if origin.trim().eq_ignore_ascii_case("null") {
            return Some("the request came from an opaque-origin frame");
        }
    }
    let Some(referer) = referer else {
        return None;
    };
    let Ok(url) = Url::parse(referer.trim()) else {
        return Some("the request's Referer is not a URL");
    };
    match url.scheme() {
        // Blob workers and frames, srcdoc documents.
        "blob" | "data" | "about" | "filesystem" | "javascript" => {
            return Some("the request came from a worker or a frame, not the app's document");
        }
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

/// `refusal` for an invoke's request headers (the custom protocol carries the
/// webview's own Origin and Referer, which page script cannot set).
pub fn refusal_reason(headers: &HeaderMap) -> Option<&'static str> {
    if let Some(value) = headers.get("referer") {
        if value.to_str().is_err() {
            return Some("the request's Referer is not a URL");
        }
    }
    refusal(header(headers, "origin"), header(headers, "referer"))
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
            (Some("tauri://localhost"), None),
            (None, None),
        ] {
            assert_eq!(refusal(origin, referer), None, "{origin:?} {referer:?}");
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
            assert!(refusal(origin, referer).is_some(), "{origin:?} {referer:?}");
        }
    }

    #[test]
    fn reads_the_request_headers() {
        let mut headers = HeaderMap::new();
        assert_eq!(refusal_reason(&headers), None);
        headers.insert("origin", HeaderValue::from_static("tauri://localhost"));
        headers.insert("referer", HeaderValue::from_static("tauri://localhost"));
        assert_eq!(refusal_reason(&headers), None);
        headers.insert("origin", HeaderValue::from_static("null"));
        assert!(refusal_reason(&headers).is_some());
        headers.insert("origin", HeaderValue::from_static("tauri://localhost"));
        headers.insert(
            "referer",
            HeaderValue::from_bytes(b"tauri://localhost/\xff").unwrap(),
        );
        assert!(refusal_reason(&headers).is_some());
    }
}
