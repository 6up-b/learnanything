use serde::Serialize;
use serde_json::{json, Value};

pub const SIDECAR_TIMEOUT_CODE: &str = "sidecar_timeout";
pub const SIDECAR_UNAVAILABLE_CODE: &str = "sidecar_unavailable";
pub const SIDECAR_PROTOCOL_CODE: &str = "sidecar_protocol_error";
pub const VAULT_CHANGED_CODE: &str = "vault_changed";
pub const GRADING_PROVIDER_RESET_CODE: &str = "grading_provider_reset";

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CommandError {
    pub code: String,
    pub message: String,
    pub retryable: bool,
    pub details: Option<Value>,
}

impl CommandError {
    pub fn task_failed(diagnostic: impl Into<String>) -> Self {
        Self {
            code: "internal".to_string(),
            message:
                "LearnLoop could not complete its background task. Restart the app and try again."
                    .to_string(),
            retryable: false,
            details: Some(json!({"diagnostic": diagnostic.into()})),
        }
    }

    pub fn state_unavailable() -> Self {
        Self {
            code: "internal".to_string(),
            message:
                "LearnLoop's local service state is unavailable. Restart the app and try again."
                    .to_string(),
            retryable: false,
            details: None,
        }
    }

    pub fn unavailable(details: Value) -> Self {
        Self {
            code: SIDECAR_UNAVAILABLE_CODE.to_string(),
            message: "LearnLoop's local service is unavailable. Retry the action; if it keeps failing, restart the app."
                .to_string(),
            retryable: true,
            details: Some(details),
        }
    }

    pub fn outcome_unknown(mut details: Value) -> Self {
        if let Some(details) = details.as_object_mut() {
            details
                .entry("outcome")
                .or_insert_with(|| Value::String("unknown".to_string()));
        }
        Self {
            code: SIDECAR_UNAVAILABLE_CODE.to_string(),
            message: "LearnLoop lost contact with its local service and could not confirm whether this action completed. Check the current state before trying it again."
                .to_string(),
            retryable: false,
            details: Some(details),
        }
    }

    pub fn protocol(mut details: Value) -> Self {
        if let Some(details) = details.as_object_mut() {
            details
                .entry("outcome")
                .or_insert_with(|| Value::String("unknown".to_string()));
        }
        Self {
            code: SIDECAR_PROTOCOL_CODE.to_string(),
            message: "LearnLoop received an invalid response and could not confirm whether this action completed. Check the current state before trying it again."
                .to_string(),
            retryable: false,
            details: Some(details),
        }
    }

    pub fn timeout(details: Value) -> Self {
        Self {
            code: SIDECAR_TIMEOUT_CODE.to_string(),
            message: "The local learning service took too long to respond, so LearnLoop could not confirm whether this action completed. Check the current state before trying it again."
                .to_string(),
            retryable: false,
            details: Some(details),
        }
    }

    /// A command issued against one vault selection reached the sidecar after
    /// the learner selected another vault.
    pub fn vault_changed(message: &str, details: Value) -> Self {
        Self {
            code: VAULT_CHANGED_CODE.to_string(),
            message: message.to_string(),
            retryable: false,
            details: Some(details),
        }
    }

    /// A replacement sidecar refused the learner's grading-provider choice, so
    /// the choice was dropped and grading uses the vault's configured provider.
    /// The replacement sidecar itself is healthy, so the action can be retried.
    pub fn grading_provider_reset(provider: &str, cause: CommandError) -> Self {
        Self {
            code: GRADING_PROVIDER_RESET_CODE.to_string(),
            message: format!(
                "LearnLoop restarted its local service but could not restore the grading provider \"{provider}\" ({}). Grading now uses the vault's configured provider. Retry the action.",
                cause.message
            ),
            retryable: true,
            details: Some(json!({
                "provider": provider,
                "cause": {"code": cause.code, "message": cause.message, "details": cause.details},
            })),
        }
    }

    pub fn from_rpc(error: &Value) -> Self {
        if !error.is_object()
            || !error.get("code").is_some_and(Value::is_i64)
            || !error.get("message").is_some_and(Value::is_string)
        {
            return Self::protocol(json!({"phase": "decode_error_response"}));
        }
        let data = error.get("data").and_then(Value::as_object);
        Self {
            code: data
                .and_then(|data| data.get("code"))
                .and_then(Value::as_str)
                .unwrap_or("internal")
                .to_string(),
            message: error
                .get("message")
                .and_then(Value::as_str)
                .unwrap_or("Sidecar command failed.")
                .to_string(),
            retryable: data
                .and_then(|data| data.get("retryable"))
                .and_then(Value::as_bool)
                .unwrap_or(false),
            details: data.and_then(|data| data.get("details")).cloned(),
        }
    }

    pub fn invalidates_sidecar(&self) -> bool {
        matches!(
            self.code.as_str(),
            "internal" | SIDECAR_TIMEOUT_CODE | SIDECAR_UNAVAILABLE_CODE | SIDECAR_PROTOCOL_CODE
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn malformed_rpc_errors_are_protocol_failures() {
        let error = CommandError::from_rpc(&json!({"message": "missing numeric code"}));

        assert_eq!(error.code, SIDECAR_PROTOCOL_CODE);
        assert!(error.invalidates_sidecar());
    }

    #[test]
    fn application_errors_preserve_the_typed_contract() {
        let error = CommandError::from_rpc(&json!({
            "code": -32001,
            "message": "Try later.",
            "data": {
                "code": "provider_unavailable",
                "retryable": true,
                "details": {"provider": "codex"}
            }
        }));

        assert_eq!(error.code, "provider_unavailable");
        assert_eq!(error.message, "Try later.");
        assert!(error.retryable);
        assert!(!error.invalidates_sidecar());
    }

    #[test]
    fn unknown_commit_failures_are_not_safe_to_retry() {
        let error = CommandError::from_rpc(&json!({
            "code": -32603,
            "message": "Outcome unknown.",
            "data": {"code": "internal", "retryable": false}
        }));

        assert!(!error.retryable);
        assert!(error.invalidates_sidecar());

        let disconnected = CommandError::outcome_unknown(json!({"phase": "await_response"}));
        assert!(!disconnected.retryable);
        assert_eq!(
            disconnected.details.unwrap()["outcome"],
            Value::String("unknown".to_string())
        );
    }
}
