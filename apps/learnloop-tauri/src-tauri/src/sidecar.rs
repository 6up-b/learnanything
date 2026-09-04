use crate::errors::CommandError;
use serde_json::{json, Value};
use std::ffi::OsString;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::mpsc::{Receiver, RecvTimeoutError};
use std::sync::{mpsc, Arc, Mutex};
use std::time::{Duration, Instant};

// Goal population may legitimately use the Codex SDK's 15-minute turn
// deadline. The 16-minute total adds a one-minute envelope for validation and
// persistence before treating the Python process as hung and replacing it.
const DEFAULT_RESPONSE_TIMEOUT_SECS: u64 = 16 * 60;
const DEFAULT_STARTUP_TIMEOUT_SECS: u64 = 15;
const SHUTDOWN_TIMEOUT_SECS: u64 = 2;

fn response_timeout() -> Duration {
    timeout_from_env(
        "LEARNLOOP_SIDECAR_TIMEOUT_SECS",
        DEFAULT_RESPONSE_TIMEOUT_SECS,
    )
}

fn startup_timeout() -> Duration {
    timeout_from_env(
        "LEARNLOOP_SIDECAR_STARTUP_TIMEOUT_SECS",
        DEFAULT_STARTUP_TIMEOUT_SECS,
    )
}

fn timeout_from_env(name: &str, default_secs: u64) -> Duration {
    std::env::var(name)
        .ok()
        .and_then(|raw| raw.parse::<u64>().ok())
        .filter(|secs| *secs > 0)
        .map(Duration::from_secs)
        .unwrap_or(Duration::from_secs(default_secs))
}

#[derive(Clone)]
pub struct SidecarManager {
    state: Arc<Mutex<SidecarState>>,
}

struct SidecarState {
    client: Option<SidecarClient>,
    vault_path: Option<PathBuf>,
}

struct SidecarClient {
    child: Child,
    stdin: ChildStdin,
    // Lines arrive via a dedicated reader thread so call() can time out instead
    // of blocking forever on a hung sidecar. The channel disconnects on EOF.
    responses: Receiver<std::io::Result<String>>,
    next_id: u64,
    launcher: String,
}

struct SidecarCommandSpec {
    program: OsString,
    args: Vec<OsString>,
    label: String,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(SidecarState {
                client: None,
                vault_path: None,
            })),
        }
    }

    pub fn initialize(&self, vault_path: Option<String>) -> Result<Value, CommandError> {
        let requested_vault = vault_path.map(PathBuf::from);
        let mut state = self
            .state
            .lock()
            .map_err(|_| CommandError::state_unavailable())?;
        // Reconnects after a timeout or broken pipe must preserve the selected
        // vault. Previously `call()` reinitialized with `None`, which silently
        // fell back to the fixture/default vault after dropping a dead client.
        let explicit_selection = requested_vault.is_some();
        let vault = resolve_vault_path(requested_vault, state.vault_path.clone());
        if state.client.is_none() || state.vault_path.as_ref() != Some(&vault) {
            // Never run two job managers against one vault while switching.
            // Keep the last successful path, though: if selection fails, the
            // next ordinary call can restore that vault in a fresh process.
            if let Some(mut previous) = state.client.take() {
                stop_client(&mut previous, true);
            }
            let mut candidate = SidecarClient::spawn()?;
            let initialized = match candidate.call(
                "initialize",
                json!({"vaultPath": vault, "clientVersion": env!("CARGO_PKG_VERSION")}),
            ) {
                Ok(value) => value,
                Err(error) => {
                    stop_client(&mut candidate, false);
                    return Err(error);
                }
            };
            state.client = Some(candidate);
            if explicit_selection {
                // A vault the user chose (header picker, new-vault wizard)
                // becomes the next launch's default; the fallbacks below only
                // apply until then.
                remember_vault(&vault);
            }
            state.vault_path = Some(vault);
            return Ok(initialized);
        }
        Ok(json!({"ok": true}))
    }

    /// The vault the sidecar is (or would be) initialized against. Used by the
    /// llpdf:// protocol to locate the vault's content-addressed originals
    /// store without a sidecar round-trip.
    pub fn resolved_vault_path(&self) -> PathBuf {
        let selected = self
            .state
            .lock()
            .ok()
            .and_then(|state| state.vault_path.clone());
        resolve_vault_path(None, selected)
    }

    pub fn select_vault(&self, vault_path: Option<String>) -> Result<Value, CommandError> {
        let initialized = self.initialize(vault_path)?;
        if let Some(vault) = initialized.get("vault") {
            return Ok(vault.clone());
        }
        self.call("load_vault", json!({}))
            .map(|snapshot| snapshot.get("vault").cloned().unwrap_or(Value::Null))
    }

    pub fn call(&self, method: &str, params: Value) -> Result<Value, CommandError> {
        {
            let needs_init = self
                .state
                .lock()
                .map_err(|_| CommandError::state_unavailable())?
                .client
                .is_none();
            if needs_init {
                drop(self.initialize(None)?);
            }
        }
        let mut state = self
            .state
            .lock()
            .map_err(|_| CommandError::state_unavailable())?;
        let client = state
            .client
            .as_mut()
            .ok_or_else(CommandError::state_unavailable)?;
        let result = client.call(method, params);
        // Transport/protocol failures leave no trustworthy request boundary.
        // Reap the process so the next command starts a clean client against
        // the same selected vault. Typed application errors keep it alive.
        if matches!(&result, Err(error) if error.invalidates_sidecar()) {
            if let Some(mut client) = state.client.take() {
                stop_client(&mut client, false);
            }
        }
        result
    }

    /// Run one call on a fresh sidecar initialized against the selected vault.
    ///
    /// Long-running CLI commands must not occupy the primary client's mutex:
    /// that client serves every interactive desktop request. The isolated
    /// process has its own stdin/stdout protocol and is always reaped after the
    /// call, whether the RPC succeeds, fails, or times out.
    pub fn call_isolated(&self, method: &str, params: Value) -> Result<Value, CommandError> {
        let vault = self.resolved_vault_path();
        let mut client = SidecarClient::spawn()?;
        let initialized = client.call(
            "initialize",
            json!({"vaultPath": vault, "clientVersion": env!("CARGO_PKG_VERSION")}),
        );
        if let Err(error) = initialized {
            stop_client(&mut client, !error.invalidates_sidecar());
            return Err(error);
        }

        let result = client.call(method, params);
        let graceful = !matches!(&result, Err(error) if error.invalidates_sidecar());
        stop_client(&mut client, graceful);
        result
    }
}

fn stop_client(client: &mut SidecarClient, graceful: bool) {
    if graceful {
        let _ = client.call_with_timeout(
            "shutdown",
            json!({}),
            Duration::from_secs(SHUTDOWN_TIMEOUT_SECS),
        );
    }
    // `shutdown` responds before the Python server loop exits. Kill is a
    // harmless fallback if it has not exited yet and guarantees that the child
    // is reaped instead of becoming a zombie.
    client.terminate();
}

impl SidecarClient {
    fn spawn() -> Result<Self, CommandError> {
        let repo_root = repo_root();
        let mut attempts = Vec::new();
        for spec in sidecar_command_specs(&repo_root) {
            let label = spec.label.clone();
            match Self::launch(&repo_root, spec) {
                Ok(mut client) => {
                    match client.call_with_timeout("rpc.ping", json!({}), startup_timeout()) {
                        Ok(_) => return Ok(client),
                        Err(error) => {
                            attempts.push(json!({
                                "launcher": label,
                                "phase": "readiness_probe",
                                "code": error.code,
                                "diagnostic": error.details,
                            }));
                            client.terminate();
                        }
                    }
                }
                Err(diagnostic) => attempts.push(json!({
                    "launcher": label,
                    "phase": "spawn",
                    "diagnostic": diagnostic,
                })),
            }
        }
        Err(CommandError::unavailable(json!({
            "phase": "startup",
            "attempts": attempts,
        })))
    }

    fn launch(repo_root: &Path, spec: SidecarCommandSpec) -> Result<Self, String> {
        let mut command = Command::new(&spec.program);
        command
            .args(&spec.args)
            .current_dir(repo_root)
            .env("PYTHONPATH", python_path(repo_root))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command.spawn().map_err(|error| error.to_string())?;
        let stdin = match child.stdin.take() {
            Some(stdin) => stdin,
            None => {
                let _ = child.kill();
                let _ = child.wait();
                return Err("stdin pipe was unavailable".to_string());
            }
        };
        let stdout = match child.stdout.take() {
            Some(stdout) => stdout,
            None => {
                let _ = child.kill();
                let _ = child.wait();
                return Err("stdout pipe was unavailable".to_string());
            }
        };
        Ok(Self {
            child,
            stdin,
            responses: spawn_reader(stdout),
            next_id: 1,
            launcher: spec.label,
        })
    }

    fn call(&mut self, method: &str, params: Value) -> Result<Value, CommandError> {
        self.call_with_timeout(method, params, response_timeout())
    }

    fn call_with_timeout(
        &mut self,
        method: &str,
        params: Value,
        timeout: Duration,
    ) -> Result<Value, CommandError> {
        let id = self.next_id;
        self.next_id += 1;
        let request = json!({"jsonrpc": "2.0", "id": id, "method": method, "params": params});
        writeln!(self.stdin, "{request}").map_err(|err| {
            CommandError::outcome_unknown(json!({
                "phase": "write_request",
                "method": method,
                "launcher": self.launcher,
                "diagnostic": err.to_string(),
                "outcome": "unknown",
            }))
        })?;
        self.stdin.flush().map_err(|err| {
            CommandError::outcome_unknown(json!({
                "phase": "flush_request",
                "method": method,
                "launcher": self.launcher,
                "diagnostic": err.to_string(),
                "outcome": "unknown",
            }))
        })?;
        let deadline = Instant::now() + timeout;
        let remaining = deadline.saturating_duration_since(Instant::now());
        let line = match self.responses.recv_timeout(remaining) {
            Ok(Ok(line)) => line,
            Ok(Err(err)) => {
                return Err(CommandError::outcome_unknown(json!({
                    "phase": "read_response",
                    "method": method,
                    "launcher": self.launcher,
                    "diagnostic": err.to_string(),
                    "outcome": "unknown",
                })))
            }
            Err(RecvTimeoutError::Timeout) => {
                return Err(CommandError::timeout(json!({
                    "method": method,
                    "timeoutSeconds": timeout.as_secs(),
                    "launcher": self.launcher,
                    "outcome": "unknown",
                })))
            }
            Err(RecvTimeoutError::Disconnected) => {
                let status = self.child.try_wait().ok().flatten();
                return Err(CommandError::outcome_unknown(json!({
                    "phase": "await_response",
                    "method": method,
                    "launcher": self.launcher,
                    "exitStatus": format!("{status:?}"),
                    "outcome": "unknown",
                })));
            }
        };
        parse_response(&line, id, method, &self.launcher)
    }

    fn terminate(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

impl Drop for SidecarClient {
    fn drop(&mut self) {
        self.terminate();
    }
}

fn parse_response(
    line: &str,
    expected_id: u64,
    method: &str,
    launcher: &str,
) -> Result<Value, CommandError> {
    let response: Value = serde_json::from_str(line.trim()).map_err(|err| {
        CommandError::protocol(json!({
            "phase": "decode_response",
            "method": method,
            "launcher": launcher,
            "diagnostic": err.to_string(),
        }))
    })?;
    if response.get("jsonrpc").and_then(Value::as_str) != Some("2.0")
        || response.get("id").and_then(Value::as_u64) != Some(expected_id)
    {
        return Err(CommandError::protocol(json!({
            "phase": "validate_response_envelope",
            "method": method,
            "expectedId": expected_id,
            "receivedId": response.get("id"),
        })));
    }
    match (response.get("result"), response.get("error")) {
        (Some(result), None) => Ok(result.clone()),
        (None, Some(error)) => Err(CommandError::from_rpc(error)),
        _ => Err(CommandError::protocol(json!({
            "phase": "validate_response_payload",
            "method": method,
        }))),
    }
}

fn spawn_reader(stdout: ChildStdout) -> Receiver<std::io::Result<String>> {
    let (tx, rx) = mpsc::channel();
    std::thread::spawn(move || {
        let mut reader = BufReader::new(stdout);
        loop {
            let mut line = String::new();
            match reader.read_line(&mut line) {
                Ok(0) => break,
                Ok(_) => {
                    if tx.send(Ok(line)).is_err() {
                        break;
                    }
                }
                Err(err) => {
                    let _ = tx.send(Err(err));
                    break;
                }
            }
        }
    });
    rx
}

fn sidecar_command_specs(repo_root: &Path) -> Vec<SidecarCommandSpec> {
    let mut specs = Vec::new();
    if let Some(python) = std::env::var_os("LEARNLOOP_PYTHON") {
        specs.push(python_spec(python, "LEARNLOOP_PYTHON"));
    }

    // Prefer the environment the app was launched from (an activated
    // conda/virtualenv) over the repo-local .venv, so the sidecar — and thus
    // sys.executable and manim — matches the user's active Python environment.
    if let Some(active) = active_env_python() {
        specs.push(python_spec(
            active.into_os_string(),
            "active env (VIRTUAL_ENV/CONDA_PREFIX)",
        ));
    }

    #[cfg(not(windows))]
    if repo_root.join("uv.lock").exists() {
        specs.push(uv_spec());
    }

    if let Some(venv_python) = venv_python(repo_root) {
        specs.push(python_spec(venv_python.into_os_string(), ".venv python"));
    }

    #[cfg(windows)]
    {
        specs.push(python_spec(OsString::from("python"), "python"));
        if repo_root.join("uv.lock").exists() {
            specs.push(uv_spec());
        }
    }

    #[cfg(not(windows))]
    {
        specs.push(python_spec(OsString::from("python3"), "python3"));
        specs.push(python_spec(OsString::from("python"), "python"));
    }

    specs
}

fn python_spec(program: OsString, label: &str) -> SidecarCommandSpec {
    SidecarCommandSpec {
        program,
        args: vec![OsString::from("-m"), OsString::from("learnloop_sidecar")],
        label: label.to_string(),
    }
}

fn uv_spec() -> SidecarCommandSpec {
    SidecarCommandSpec {
        program: OsString::from("uv"),
        args: vec![
            OsString::from("run"),
            OsString::from("python"),
            OsString::from("-m"),
            OsString::from("learnloop_sidecar"),
        ],
        label: "uv run python".to_string(),
    }
}

fn venv_python(repo_root: &Path) -> Option<PathBuf> {
    let candidate = if cfg!(windows) {
        repo_root.join(".venv").join("Scripts").join("python.exe")
    } else {
        repo_root.join(".venv").join("bin").join("python")
    };
    candidate.exists().then_some(candidate)
}

/// The interpreter of the currently-activated virtualenv or conda environment,
/// if one is active and its python exists. Checks `VIRTUAL_ENV` first, then
/// `CONDA_PREFIX`. On Windows a venv keeps python under `Scripts/`, while a
/// conda prefix keeps `python.exe` at the prefix root — both are probed.
fn active_env_python() -> Option<PathBuf> {
    for var in ["VIRTUAL_ENV", "CONDA_PREFIX"] {
        if let Some(base) = std::env::var_os(var) {
            let base = PathBuf::from(base);
            let candidate = if cfg!(windows) {
                let scripts = base.join("Scripts").join("python.exe");
                if scripts.exists() {
                    return Some(scripts);
                }
                base.join("python.exe")
            } else {
                base.join("bin").join("python")
            };
            if candidate.exists() {
                return Some(candidate);
            }
        }
    }
    None
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .canonicalize()
        .unwrap_or_else(|_| Path::new(env!("CARGO_MANIFEST_DIR")).join("../../.."))
}

fn is_vault(path: &Path) -> bool {
    path.join("learnloop.toml").is_file()
}

/// The machine-global LearnLoop config directory, resolved the way
/// `learnloop.config.loader` does it: `LEARNLOOP_CONFIG_DIR`, else
/// `$XDG_CONFIG_HOME/learnloop`, else `~/.config/learnloop`.
fn config_dir() -> Option<PathBuf> {
    if let Some(dir) = std::env::var_os("LEARNLOOP_CONFIG_DIR") {
        return Some(PathBuf::from(dir));
    }
    if let Some(xdg) = std::env::var_os("XDG_CONFIG_HOME") {
        return Some(PathBuf::from(xdg).join("learnloop"));
    }
    std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(|home| PathBuf::from(home).join(".config").join("learnloop"))
}

fn last_vault_file() -> Option<PathBuf> {
    config_dir().map(|dir| dir.join("last_vault"))
}

/// The vault recorded by the last explicit selection, if it is still a vault.
fn remembered_vault_from(file: &Path) -> Option<PathBuf> {
    let raw = std::fs::read_to_string(file).ok()?;
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return None;
    }
    let path = PathBuf::from(trimmed);
    is_vault(&path).then_some(path)
}

fn remember_vault(vault: &Path) {
    let Some(file) = last_vault_file() else {
        return;
    };
    if let Some(parent) = file.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    // Best effort: an unwritable config dir must not fail vault selection.
    let _ = std::fs::write(&file, format!("{}\n", vault.display()));
}

/// The first (sorted) vault under `<root>/fixtures-local/`, the gitignored
/// home for per-developer vaults.
fn local_dev_vault_in(root: &Path) -> Option<PathBuf> {
    let entries = std::fs::read_dir(root.join("fixtures-local")).ok()?;
    let mut vaults: Vec<PathBuf> = entries
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| is_vault(path))
        .collect();
    vaults.sort();
    vaults.into_iter().next()
}

fn default_vault_path() -> PathBuf {
    // Dev default order: a personal vault under fixtures-local/, then the
    // tracked linear-algebra fixture. The fixture is the last resort on
    // purpose — opening a vault writes to it (state.sqlite, learner profile),
    // and the tracked one shows up dirty in `git status` every launch.
    let root = repo_root();
    if let Some(local) = local_dev_vault_in(&root) {
        return local;
    }
    let fixture = root.join("fixtures").join("linear_algebra");
    if is_vault(&fixture) {
        fixture
    } else {
        root
    }
}

fn resolve_vault_path(requested: Option<PathBuf>, selected: Option<PathBuf>) -> PathBuf {
    requested
        .or(selected)
        .or_else(|| std::env::var("LEARNLOOP_VAULT").ok().map(PathBuf::from))
        .or_else(|| last_vault_file().and_then(|file| remembered_vault_from(&file)))
        .unwrap_or_else(default_vault_path)
}

fn python_path(repo_root: &Path) -> String {
    let src = repo_root.join("src");
    let mut paths = vec![src];
    if let Some(existing) = std::env::var_os("PYTHONPATH") {
        paths.extend(std::env::split_paths(&existing));
    }
    std::env::join_paths(paths)
        .map(|value| value.to_string_lossy().to_string())
        .unwrap_or_else(|_| repo_root.join("src").display().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::errors::SIDECAR_PROTOCOL_CODE;

    fn scratch_dir(label: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "learnloop-sidecar-{label}-{}-{:?}",
            std::process::id(),
            std::thread::current().id()
        ));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("scratch dir");
        dir
    }

    fn make_vault(path: &Path) {
        std::fs::create_dir_all(path).expect("vault dir");
        std::fs::write(path.join("learnloop.toml"), "").expect("vault marker");
    }

    #[test]
    fn remembered_vault_must_still_be_a_vault() {
        let dir = scratch_dir("remembered");
        let file = dir.join("last_vault");
        let vault = dir.join("mine");

        assert_eq!(remembered_vault_from(&file), None, "missing file");
        std::fs::write(&file, "\n").unwrap();
        assert_eq!(remembered_vault_from(&file), None, "blank file");
        std::fs::write(&file, format!("{}\n", vault.display())).unwrap();
        assert_eq!(remembered_vault_from(&file), None, "path is not a vault yet");
        make_vault(&vault);
        assert_eq!(remembered_vault_from(&file), Some(vault));
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn local_dev_vault_is_the_first_sorted_vault_under_fixtures_local() {
        let root = scratch_dir("local");
        assert_eq!(local_dev_vault_in(&root), None, "no fixtures-local yet");
        let local = root.join("fixtures-local");
        std::fs::create_dir_all(local.join("notes")).unwrap(); // not a vault
        assert_eq!(local_dev_vault_in(&root), None, "non-vault dirs are ignored");
        make_vault(&local.join("zeta"));
        make_vault(&local.join("alpha"));
        assert_eq!(local_dev_vault_in(&root), Some(local.join("alpha")));
        let _ = std::fs::remove_dir_all(&root);
    }

    #[test]
    fn reconnect_keeps_the_selected_vault() {
        let selected = PathBuf::from("/selected/vault");

        assert_eq!(resolve_vault_path(None, Some(selected.clone())), selected);
        assert_eq!(
            resolve_vault_path(
                Some(PathBuf::from("/explicit/vault")),
                Some(PathBuf::from("/selected/vault")),
            ),
            PathBuf::from("/explicit/vault")
        );
    }

    #[test]
    fn response_parser_requires_a_complete_matching_envelope() {
        assert_eq!(
            parse_response(
                r#"{"jsonrpc":"2.0","id":4,"result":null}"#,
                4,
                "load_vault",
                "test",
            )
            .expect("valid response"),
            Value::Null
        );

        for invalid in [
            r#"{"jsonrpc":"2.0","id":5,"result":{}}"#,
            r#"{"jsonrpc":"2.0","id":4}"#,
            r#"{"jsonrpc":"2.0","id":4,"result":{},"error":{}}"#,
            "not-json",
        ] {
            let error = parse_response(invalid, 4, "load_vault", "test")
                .expect_err("malformed response must fail");
            assert_eq!(error.code, SIDECAR_PROTOCOL_CODE);
            assert!(!error.retryable);
            assert!(error.invalidates_sidecar());
        }
    }
}
