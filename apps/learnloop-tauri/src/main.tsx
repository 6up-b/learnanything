import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import "./styles/app.css";
import "./styles/palettes.css";

// Apply the persisted palette before first paint so there is no default-theme
// flash. The Settings screen updates both the attribute and localStorage.
const storedPalette = localStorage.getItem("learnloop.palette");
if (storedPalette) {
  document.documentElement.dataset.palette = storedPalette;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

