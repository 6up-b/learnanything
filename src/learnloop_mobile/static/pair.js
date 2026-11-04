"use strict";
let secret = new URLSearchParams(location.hash.slice(1)).get("s");
history.replaceState(null, "", "/pair");
document.getElementById("pair").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.target.querySelector("button");
  button.disabled = true;
  const message = document.getElementById("message");
  try {
    const payload = {device_label: document.getElementById("label").value};
    if (secret) payload.secret = secret;
    else payload.code = document.getElementById("code").value.trim();
    const response = await fetch("/pair", {
      method: "POST", headers: {"Content-Type": "application/json"},
      credentials: "omit", cache: "no-store", body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error("Pairing failed. Run pair again on the desktop.");
    secret = null;
    document.getElementById("code").value = "";
    document.getElementById("token").value = result.token;
    document.getElementById("token-label").hidden = false;
    message.textContent = "Paired. Keep this token private; it is shown only once.";
    if (result.scope === "app") {
      // The app reads its token from this fragment, which never reaches a server or a log.
      const fragment = new URLSearchParams({token: result.token, device: result.device_id});
      document.getElementById("open-app-link").href = "/app/#" + fragment.toString();
      document.getElementById("open-app").hidden = false;
    }
  } catch (_) {
    message.textContent = "Pairing failed. Run pair again on the desktop.";
    button.disabled = false;
  }
});
