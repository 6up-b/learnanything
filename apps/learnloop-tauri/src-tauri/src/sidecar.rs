use crate::errors::CommandError;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};

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
    stdout: BufReader<ChildStdout>,
    next_id: u64,
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
        if state.vault_path.as_ref() != Some(&vault) {
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
        client.call(method, params)
    }
}

impl SidecarClient {
    fn spawn() -> Result<Self, CommandError> {
        let repo_root = repo_root();
        let mut command = Command::new("python");
        command
            .arg("-m")
            .arg("learnloop_sidecar")
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
        let mut child = command.spawn().map_err(|err| {
            CommandError::internal(format!("Failed to spawn Python sidecar: {err}"))
        })?;
        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| CommandError::internal("Sidecar stdin was unavailable."))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| CommandError::internal("Sidecar stdout was unavailable."))?;
        Ok(Self {
            child,
            stdin,
            stdout: BufReader::new(stdout),
            next_id: 1,
        })
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
        loop {
            let mut line = String::new();
            let bytes = self.stdout.read_line(&mut line).map_err(|err| {
                CommandError::internal(format!("Failed to read sidecar response: {err}"))
            })?;
            if bytes == 0 {
                let status = self.child.try_wait().ok().flatten();
                return Err(CommandError::internal(format!(
                    "Sidecar exited before responding. status={status:?}"
                )));
            }
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
