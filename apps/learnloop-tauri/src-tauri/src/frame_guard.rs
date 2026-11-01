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

/// Why an invoke is refused, or None when its Origin is one of the app's and
/// its Referer is the app's own top document on that origin.
///
/// This is a filter on what WebKit reports, not authentication: Fetch lets a
/// context omit its Referer (`referrer: ""`, refused here because the app's
/// document always sends one) or name any same-origin URL instead (which this
/// layer can't tell from the document). What authenticates the document is
/// Tauri's invoke key, held only in a closure of the main frame's init script;
/// no Worker or frame has it (docs/reviews/reader-rw5d-g-sm14-probe.md).
pub fn refusal(origin: Option<&str>, referer: Option<&str>) -> Option<&'static str> {
    let Some(origin) = origin.map(str::trim) else {
        return Some("the request has no Origin");
    };
    // An opaque origin: a sandboxed frame (the sketch compartment) or a data: document.
    if origin.eq_ignore_ascii_case("null") {
        return Some("the request came from an opaque-origin frame");
    }
    let Some(origin) = Url::parse(origin).ok().as_ref().and_then(app_origin) else {
        return Some("the request's Origin is not the app's");
    };
    // The app's document always sends one (every app call in both G-SM14 runs).
    let Some(referer) = referer.map(str::trim).filter(|value| !value.is_empty()) else {
        return Some("the request has no Referer, which the app's document always sends");
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
    if app_origin(&url).as_deref() != Some(origin.as_str()) {
        return Some("the request's Referer is not on its Origin");
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

/// `refusal` for an invoke's request headers. Page script can't set Origin or
/// Referer as headers, but Fetch lets it omit the Referer or replace it with a
/// same-origin URL (see `refusal`).
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
            (
                Some("https://tauri.localhost"),
                Some("https://tauri.localhost/index.html"),
            ),
            (
                Some("http://127.0.0.1:1420"),
                Some("http://127.0.0.1:1420/"),
            ),
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
            assert!(refusal(origin, referer).is_some(), "{origin:?} {referer:?}");
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
            refusal(Some("tauri://localhost"), Some("tauri://localhost/")),
            None
        );
    }

    #[test]
    fn reads_the_request_headers() {
        let mut headers = HeaderMap::new();
        assert!(refusal_reason(&headers).is_some());
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
