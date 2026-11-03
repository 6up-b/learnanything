# Configurable mobile HTTPS port

The M1 host assumed it owned HTTPS port 443. On a shared Tailscale node that
port can already belong to another project, including one with Funnel enabled.
The mobile host now accepts `https_port` in machine-local `mobile.toml`, with
443 as the compatible default. The existing `port` remains the loopback backend
listener; no vault migration or algorithm-version change is involved.

```toml
hostname = "desktop.example-tailnet.ts.net"
port = 8765
https_port = 8445
```

M2a integration contract:

- `config.https_port`: external HTTPS port, an integer in 1–65535.
- `config.https_authority`: exact Host value, such as
  `desktop.example-tailnet.ts.net:8445`; port 443 is implicit.
- `config.base_url`: HTTPS origin and URL prefix, such as
  `https://desktop.example-tailnet.ts.net:8445`, with no trailing slash.
- `hostname` stays a bare lowercase `.ts.net` name. Use the properties above
  instead of rebuilding an origin from `hostname` or using the backend `port`.

Host/Origin validation stays exact. Pairing emits the configured URL. The
generated Flush Shortcut accepts the optional port, with no path, credentials
or other URL components. Doctor checks the configured HTTPS root route and
scans background, foreground and Service configurations for aliases to the
backend. Any extra web route or TCP forward to that backend still fails;
Funnel on the configured port or a backend alias still fails. Unrelated routes,
including Funnel on 443 when LearnLoop uses 8445, do not fail the check.

This patch changes no queue, grading or practice behavior and performs no
deployment, Serve, policy or vault edits. A1–A3 remain real-device checks.

Validation: **459 passed**, no skips, with the pinned mobile dependencies in a
temporary `uv --with` environment (the project's virtualenv lacks the mobile
extra). This covers `test_mobile_https`, `test_mobile_doctor`,
`test_mobile_host_auth`, `test_mobile_pairing`, `test_mobile_capture`,
`test_mobile_shortcuts`, `test_mobile_host_coexistence` and
`test_mobile_allowlist`. One upstream Starlette TestClient deprecation warning
was emitted. The suite includes real subprocess/WAL coexistence, default-443
compatibility, pairing and authenticated status on 8445, cross-origin rejection,
and background/foreground/Service backend aliases with and without Funnel.
The new same-host cross-port regression was rerun after its final refinement.
