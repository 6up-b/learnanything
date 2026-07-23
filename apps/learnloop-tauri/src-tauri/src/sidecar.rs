use crate::errors::CommandError;
use serde_json::{json, Value};
use std::ffi::OsString;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::mpsc::{Receiver, RecvTimeoutError};
use std::sync::{mpsc, Arc, Mutex};
use std::time::{Duration, Instant};

// Longest legitimate sidecar call is AI grading (backend request timeout 180s);
// anything slower means the Python process is hung and the client is replaced.
const DEFAULT_RESPONSE_TIMEOUT_SECS: u64 = 240;
pub const TIMEOUT_ERROR_CODE: &str = "sidecar_timeout";

fn response_timeout() -> Duration {
    std::env::var("LEARNLOOP_SIDECAR_TIMEOUT_SECS")
        .ok()
        .and_then(|raw| raw.parse::<u64>().ok())
        .filter(|secs| *secs > 0)
        .map(Duration::from_secs)
        .unwrap_or(Duration::from_secs(DEFAULT_RESPONSE_TIMEOUT_SECS))
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
        let vault = vault_path
            .map(PathBuf::from)
            .or_else(|| std::env::var("LEARNLOOP_VAULT").ok().map(PathBuf::from))
            .unwrap_or_else(default_vault_path);
        let mut state = self
            .state
            .lock()
            .map_err(|_| CommandError::internal("Sidecar lock was poisoned."))?;
        if state.client.is_none() || state.vault_path.as_ref() != Some(&vault) {
            if let Some(mut client) = state.client.take() {
                let _ = client.call("shutdown", json!({}));
            }
            state.client = Some(SidecarClient::spawn()?);
            state.vault_path = Some(vault.clone());
            return state.client.as_mut().expect("client initialized").call(
                "initialize",
                json!({"vaultPath": vault, "clientVersion": env!("CARGO_PKG_VERSION")}),
            );
        }
        Ok(json!({"ok": true}))
    }

    /// The vault the sidecar is (or would be) initialized against. Used by the
    /// llpdf:// protocol to locate the vault's content-addressed originals
    /// store without a sidecar round-trip.
    pub fn resolved_vault_path(&self) -> PathBuf {
        self.state
            .lock()
            .ok()
            .and_then(|state| state.vault_path.clone())
            .or_else(|| std::env::var("LEARNLOOP_VAULT").ok().map(PathBuf::from))
            .unwrap_or_else(default_vault_path)
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
                .map_err(|_| CommandError::internal("Sidecar lock was poisoned."))?
                .client
                .is_none();
            if needs_init {
                drop(self.initialize(None)?);
            }
        }
        let mut state = self
            .state
            .lock()
            .map_err(|_| CommandError::internal("Sidecar lock was poisoned."))?;
        let client = state
            .client
            .as_mut()
            .ok_or_else(|| CommandError::internal("Sidecar was not initialized."))?;
        let result = client.call(method, params);
        // A timed-out sidecar is presumed hung: kill it and drop the client so the
        // next call respawns a fresh process against the same vault.
        if matches!(&result, Err(err) if err.code == TIMEOUT_ERROR_CODE) {
            if let Some(mut client) = state.client.take() {
                let _ = client.child.kill();
                let _ = client.child.wait();
            }
        }
        result
    }
}

impl SidecarClient {
    fn spawn() -> Result<Self, CommandError> {
        let repo_root = repo_root();
        let mut spawn_errors = Vec::new();
        for spec in sidecar_command_specs(&repo_root) {
            let mut command = Command::new(&spec.program);
            command
                .args(&spec.args)
                .current_dir(&repo_root)
                .env("PYTHONPATH", python_path(&repo_root))
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::inherit());
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                command.creation_flags(0x08000000);
            }
            match command.spawn() {
                Ok(mut child) => {
                    let stdin = child
                        .stdin
                        .take()
                        .ok_or_else(|| CommandError::internal("Sidecar stdin was unavailable."))?;
                    let stdout = child
                        .stdout
                        .take()
                        .ok_or_else(|| CommandError::internal("Sidecar stdout was unavailable."))?;
                    return Ok(Self {
                        child,
                        stdin,
                        responses: spawn_reader(stdout),
                        next_id: 1,
                        launcher: spec.label,
                    });
                }
                Err(err) => spawn_errors.push(format!("{}: {err}", spec.label)),
            }
        }
        Err(CommandError::internal(format!(
            "Failed to spawn Python sidecar. Tried: {}",
            spawn_errors.join("; ")
        )))
    }

    fn call(&mut self, method: &str, params: Value) -> Result<Value, CommandError> {
        let id = self.next_id;
        self.next_id += 1;
        let request = json!({"jsonrpc": "2.0", "id": id, "method": method, "params": params});
        writeln!(self.stdin, "{request}").map_err(|err| {
            CommandError::internal(format!("Failed to write sidecar request: {err}"))
        })?;
        self.stdin.flush().map_err(|err| {
            CommandError::internal(format!("Failed to flush sidecar request: {err}"))
        })?;
        let deadline = Instant::now() + response_timeout();
        loop {
            let remaining = deadline.saturating_duration_since(Instant::now());
            let line = match self.responses.recv_timeout(remaining) {
                Ok(Ok(line)) => line,
                Ok(Err(err)) => {
                    return Err(CommandError::internal(format!(
                        "Failed to read sidecar response: {err}"
                    )))
                }
                Err(RecvTimeoutError::Timeout) => {
                    return Err(CommandError::timeout(format!(
                        "Sidecar did not respond to {method} within {}s. launcher={}",
                        response_timeout().as_secs(),
                        self.launcher
                    )))
                }
                Err(RecvTimeoutError::Disconnected) => {
                    let status = self.child.try_wait().ok().flatten();
                    return Err(CommandError::internal(format!(
                        "Sidecar exited before responding. launcher={} status={status:?}",
                        self.launcher
                    )));
                }
            };
            let response: Value = serde_json::from_str(line.trim())
                .map_err(|err| CommandError::internal(format!("Invalid sidecar JSON: {err}")))?;
            if response.get("id").and_then(Value::as_u64) != Some(id) {
                continue;
            }
            if let Some(error) = response.get("error") {
                return Err(CommandError::from_rpc(error));
            }
            return Ok(response.get("result").cloned().unwrap_or(Value::Null));
        }
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
        specs.push(python_spec(active.into_os_string(), "active env (VIRTUAL_ENV/CONDA_PREFIX)"));
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

fn default_vault_path() -> PathBuf {
    // Dev default: the tracked linear-algebra fixture vault (real SVD content).
    // Override with the LEARNLOOP_VAULT env var to point at another vault.
    let fixture = repo_root().join("fixtures").join("linear_algebra");
    if fixture.join("learnloop.toml").exists() {
        fixture
    } else {
        repo_root()
    }
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
