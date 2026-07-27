use crate::sidecar::SidecarManager;
use notify::{recommended_watcher, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::Serialize;
use serde_json::json;
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender};
use std::time::Duration;
use tauri::{AppHandle, Emitter};

pub const VAULT_FILES_CHANGED_EVENT: &str = "learnloop://vault-files-changed";

/// Owns the desktop's native vault watch.
///
/// Python remains the domain-state owner. Rust only coalesces filesystem events
/// and hands relative paths to the sidecar's canonical refresh boundary.
#[derive(Clone)]
pub struct VaultWatcher {
    target_tx: Sender<PathBuf>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct VaultFilesChanged {
    root: String,
    changed_paths: Vec<String>,
    refresh: serde_json::Value,
}

impl VaultWatcher {
    pub fn start(app: AppHandle, sidecar: SidecarManager) -> Self {
        let (target_tx, target_rx) = mpsc::channel();
        std::thread::spawn(move || watch_loop(target_rx, app, sidecar));
        Self { target_tx }
    }

    pub fn watch(&self, root: PathBuf) {
        let root = std::fs::canonicalize(&root).unwrap_or(root);
        let _ = self.target_tx.send(root);
    }
}

fn watch_loop(target_rx: Receiver<PathBuf>, app: AppHandle, sidecar: SidecarManager) {
    let (event_tx, event_rx) = mpsc::channel();
    let mut watcher: Option<RecommendedWatcher> = None;
    let mut root: Option<PathBuf> = None;

    loop {
        if let Some(next_root) = newest_target(&target_rx, root.is_none()) {
            if root.as_ref() != Some(&next_root) {
                match install_watch(&next_root, event_tx.clone()) {
                    Ok(next_watcher) => {
                        watcher = Some(next_watcher);
                        root = Some(next_root);
                        // Events queued for the previous root must never be applied
                        // to the newly selected vault.
                        while event_rx.try_recv().is_ok() {}
                    }
                    Err(error) => {
                        // Never keep watching the previous vault after selection
                        // has moved to a target whose watch could not be installed.
                        watcher = None;
                        root = None;
                        emit_error(&app, &next_root, "vault_watch_failed", error.to_string());
                    }
                }
            }
        }

        if watcher.is_none() {
            continue;
        }
        let Some(active_root) = root.as_deref() else {
            continue;
        };
        let first = match event_rx.recv_timeout(Duration::from_millis(200)) {
            Ok(event) => event,
            Err(RecvTimeoutError::Timeout) => continue,
            Err(RecvTimeoutError::Disconnected) => break,
        };

        let mut paths = BTreeSet::new();
        let mut force_full_refresh = collect_paths(first, active_root, &mut paths);
        // Editors commonly truncate, replace, and rename in a burst. Wait for a
        // short quiet interval and send one refresh containing the whole write.
        loop {
            match event_rx.recv_timeout(Duration::from_millis(160)) {
                Ok(event) => {
                    force_full_refresh |= collect_paths(event, active_root, &mut paths);
                }
                Err(RecvTimeoutError::Timeout) => break,
                Err(RecvTimeoutError::Disconnected) => return,
            }
        }
        if force_full_refresh {
            // A backend rescan flag means its path list is incomplete. Sending
            // the vault config path deliberately selects Python's conservative
            // full-refresh arm.
            paths.insert(PathBuf::from("learnloop.toml"));
        }
        if paths.is_empty() {
            continue;
        }
        let relative: Vec<String> = paths.into_iter().map(|path| path_for_wire(&path)).collect();
        let refresh = match sidecar.call(
            "refresh_vault_files",
            json!({"paths": &relative, "vaultRoot": active_root}),
        ) {
            Ok(value) => value,
            Err(error) => json!({
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "retryable": error.retryable,
                    "details": error.details,
                }
            }),
        };
        let payload = VaultFilesChanged {
            root: active_root.to_string_lossy().into_owned(),
            changed_paths: relative,
            refresh,
        };
        let _ = app.emit(VAULT_FILES_CHANGED_EVENT, payload);
    }
}

fn newest_target(target_rx: &Receiver<PathBuf>, block: bool) -> Option<PathBuf> {
    let mut newest = if block {
        target_rx.recv().ok()
    } else {
        target_rx.try_recv().ok()
    };
    while let Ok(next) = target_rx.try_recv() {
        newest = Some(next);
    }
    newest
}

fn install_watch(
    root: &Path,
    event_tx: Sender<notify::Result<Event>>,
) -> notify::Result<RecommendedWatcher> {
    let mut watcher = recommended_watcher(event_tx)?;
    watcher.watch(root, RecursiveMode::Recursive)?;
    Ok(watcher)
}

fn collect_paths(event: notify::Result<Event>, root: &Path, paths: &mut BTreeSet<PathBuf>) -> bool {
    let Ok(event) = event else {
        // Backend overflow/error means the event path set is no longer
        // trustworthy. Recover through the same conservative full refresh used
        // by an explicit rescan flag.
        return true;
    };
    if event.need_rescan() {
        return true;
    }
    // Reads performed by Python's refresh must not recursively trigger another
    // refresh. Only filesystem mutations cross the language boundary.
    if !matches!(
        event.kind,
        EventKind::Create(_) | EventKind::Modify(_) | EventKind::Remove(_)
    ) {
        return false;
    }
    let mut force_full_refresh = false;
    for path in event.paths {
        let Ok(relative) = path.strip_prefix(root) else {
            continue;
        };
        if is_ignored_relative_path(relative) {
            continue;
        }
        if is_watchable_relative_path(relative) {
            paths.insert(relative.to_path_buf());
        } else if relative.extension().is_none() {
            // Recursive backends can report only the containing directory for
            // a directory rename/removal. Its full contents may have changed.
            force_full_refresh = true;
        }
    }
    force_full_refresh
}

fn is_ignored_relative_path(relative: &Path) -> bool {
    if relative.iter().any(|part| {
        matches!(
            part.to_str(),
            Some(".git" | "target" | "__pycache__" | ".pytest_cache")
        )
    }) || relative.starts_with("canonical-sources/raw")
        || relative.starts_with("media/animations")
    {
        return true;
    }
    false
}

fn is_watchable_relative_path(relative: &Path) -> bool {
    if is_ignored_relative_path(relative) {
        return false;
    }
    matches!(
        relative
            .extension()
            .and_then(|extension| extension.to_str()),
        Some("yaml" | "yml" | "md" | "toml" | "json")
    )
}

fn emit_error(app: &AppHandle, root: &Path, code: &str, message: String) {
    let payload = VaultFilesChanged {
        root: root.to_string_lossy().into_owned(),
        changed_paths: Vec::new(),
        refresh: json!({"error": {"code": code, "message": message}}),
    };
    let _ = app.emit(VAULT_FILES_CHANGED_EVENT, payload);
}

fn path_for_wire(path: &Path) -> String {
    path.components()
        .map(|component| component.as_os_str().to_string_lossy())
        .collect::<Vec<_>>()
        .join("/")
}

#[cfg(test)]
mod tests {
    use super::*;
    use notify::event::{AccessKind, AccessMode, ModifyKind};

    #[test]
    fn watcher_accepts_domain_files_and_excludes_runtime_artifacts() {
        assert!(is_watchable_relative_path(Path::new(
            "subjects/s/practice-items/a.yaml"
        )));
        assert!(is_watchable_relative_path(Path::new("learnloop.toml")));
        assert!(!is_watchable_relative_path(Path::new("state.sqlite")));
        assert!(!is_watchable_relative_path(Path::new(
            "canonical-sources/raw/sha256-a.json"
        )));
        assert!(!is_watchable_relative_path(Path::new(
            "subjects/.pytest_cache/a.json"
        )));
    }

    #[test]
    fn wire_paths_are_platform_neutral() {
        assert_eq!(
            path_for_wire(Path::new("subjects/s/practice-items/a.yaml")),
            "subjects/s/practice-items/a.yaml"
        );
    }

    #[test]
    fn read_access_does_not_trigger_a_refresh_loop() {
        let root = Path::new("/vault");
        let file = root.join("subjects/s/practice-items/a.yaml");
        let mut paths = BTreeSet::new();

        collect_paths(
            Ok(
                Event::new(EventKind::Access(AccessKind::Open(AccessMode::Read)))
                    .add_path(file.clone()),
            ),
            root,
            &mut paths,
        );
        assert!(paths.is_empty());

        collect_paths(
            Ok(Event::new(EventKind::Modify(ModifyKind::Any)).add_path(file)),
            root,
            &mut paths,
        );
        assert_eq!(
            paths,
            BTreeSet::from([PathBuf::from("subjects/s/practice-items/a.yaml")])
        );
    }

    #[test]
    fn a_domain_directory_mutation_forces_a_full_refresh() {
        let root = Path::new("/vault");
        let mut paths = BTreeSet::new();
        let force_full = collect_paths(
            Ok(
                Event::new(EventKind::Remove(notify::event::RemoveKind::Folder))
                    .add_path(root.join("subjects/linear-algebra")),
            ),
            root,
            &mut paths,
        );

        assert!(force_full);
        assert!(paths.is_empty());
    }
}
