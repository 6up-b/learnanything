use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CommandError {
    pub code: String,
    pub message: String,
    pub retryable: bool,
    pub details: Option<Value>,
}

impl CommandError {
    pub fn internal(message: impl Into<String>) -> Self {
        Self {
            code: "internal".to_string(),
            message: message.into(),
            retryable: false,
            details: None,
        }
    }

    pub fn from_rpc(error: &Value) -> Self {
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
}
