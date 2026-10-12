"""Shared M1 capture domain. Importing this package never attaches or migrates."""

from .devices import (
    authenticate_device,
    create_pairing,
    exchange_pairing,
    list_devices,
    revoke_device,
    touch_device,
)
from .errors import CaptureError
from .inbox import (
    capture_media_preview,
    create_capture,
    dismiss_capture,
    get_capture,
    get_inbox_summary,
    list_captures,
    purge_capture,
    report_orphan_originals,
    route_capture,
    sanitize_image,
    validate_url,
)
from .maintenance import log_request, pinned_vault_info, prune_request_log

__all__ = [
    "CaptureError", "authenticate_device", "create_pairing", "exchange_pairing",
    "list_devices", "revoke_device", "touch_device", "capture_media_preview", "create_capture",
    "dismiss_capture",
    "get_capture", "get_inbox_summary", "list_captures", "purge_capture",
    "report_orphan_originals", "route_capture", "sanitize_image", "validate_url",
    "log_request", "pinned_vault_info", "prune_request_log",
]
