/*
Language: JavaScript
Purpose: English UI controller for the browser-hosted RPR runtime demo.
Boundary: The external provider is simulated in Python; no credentials or user data are transmitted.
*/
(() => {
  "use strict";

  const loadButton = document.getElementById("load-runtime");
  const runAllButton = document.getElementById("run-all");
  const resetButton = document.getElementById("reset");
  const stepButtons = Array.from(document.querySelectorAll(".demo-step"));
  const pythonStatus = document.getElementById("python-status");
  const packageStatus = document.getElementById("package-status");
  const currentState = document.getElementById("current-state");
  const routeStatus = document.getElementById("route-status");
  const dispatchCount = document.getElementById("dispatch-count");
  const evidenceStatus = document.getElementById("evidence-status");
  const summary = document.getElementById("summary");
  const output = document.getElementById("output");

  const WHEEL_MANIFEST_URL = "./assets/wheel.sha256";

  let pyodide = null;
  let ready = false;

  function report(stage, detail = "") {
    const message = detail ? `${stage}: ${detail}` : stage;
    console.log(`[rpr-demo] ${message}`);
    output.textContent = message;
    document.documentElement.dataset.demoStage = stage;
  }

  function setControls(enabled) {
    runAllButton.disabled = !enabled;
    resetButton.disabled = !enabled;
    stepButtons.forEach((button) => { button.disabled = !enabled; });
  }

  function latestResult(payload) {
    if (!payload || !payload.result) return null;
    if (payload.result.reconciled) return payload.result.reconciled;
    return payload.result;
  }

  function updateView(payload) {
    output.textContent = JSON.stringify(payload, null, 2);
    document.documentElement.dataset.demoOk = String(payload.ok === true);
    if (!payload.ok) {
      summary.innerHTML = `<h3>Execution failed</h3><p><code>${payload.error_type}</code>: ${payload.error}</p>`;
      return;
    }
    const result = latestResult(payload);
    if (!result) return;
    const state = result.state || result.state_before || "unknown";
    const route = result.route_visibility?.compatibility_route ?? "none";
    const authorityInferred = result.route_visibility?.authority_inferred;
    const count = result.dispatch_count ?? result.provider?.dispatch_count ?? 0;
    const valid = result.evidence_valid;
    currentState.textContent = state;
    routeStatus.textContent = route;
    dispatchCount.textContent = String(count);
    evidenceStatus.textContent = valid === true ? "verified" : (valid === false ? "invalid" : "not verified");
    document.documentElement.dataset.demoState = state;
    document.documentElement.dataset.route = route;
    document.documentElement.dataset.dispatchCount = String(count);
    document.documentElement.dataset.evidenceValid = String(valid === true);
    summary.innerHTML = `
      <h3>Current state: <code>${state}</code></h3>
      <p>Responsibility Route: <strong><code>${route}</code></strong>${authorityInferred === false ? " (this view does not create Authority)" : ""}</p>
      <p>The external provider has been dispatched <strong>${count} time${count === 1 ? "" : "s"}</strong>. The evidence chain is <strong>${valid === true ? "verified" : "not yet verified"}</strong>.</p>
      ${result.duplicate_dispatch_prevented === true ? "<p><strong>The operation was not re-dispatched after restart.</strong></p>" : ""}
    `;
  }

  async function resolveWheelLocation() {
    const response = await fetch(WHEEL_MANIFEST_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Failed to fetch wheel manifest: HTTP ${response.status}`);
    const manifest = (await response.text()).trim();
    const match = manifest.match(/\b(responsibility_pathway_runtime-[0-9A-Za-z.+-]+-py3-none-any\.whl)\b/);
    if (!match) throw new Error(`Could not parse wheel manifest: ${manifest}`);
    const filename = match[1];
    return {
      url: `./assets/${filename}`,
      path: `/tmp/${filename}`,
    };
  }

  async function invoke(functionName) {
    if (!ready) throw new Error("RPR is not loaded yet");
    report("Running scenario", functionName);
    const quoted = JSON.stringify(functionName);
    const raw = await pyodide.runPythonAsync(`run_json(${quoted})`);
    const payload = JSON.parse(raw);
    updateView(payload);
    return payload;
  }

  async function loadRuntime() {
    loadButton.disabled = true;
    pythonStatus.textContent = "loading Pyodide";
    packageStatus.textContent = "waiting";
    report("Preparing Python runtime", "the first load may download tens of MB");
    try {
      pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/" });
      const pythonVersion = pyodide.runPython("import sys; sys.version.split()[0]");
      pythonStatus.textContent = `Python ${pythonVersion}`;
      report("Preparing Python packages", "micropip + sqlite3");
      await pyodide.loadPackage(["micropip", "sqlite3"]);

      const wheel = await resolveWheelLocation();
      packageStatus.textContent = "fetching RPR wheel";
      report("Fetching RPR wheel", wheel.url);
      const wheelResponse = await fetch(wheel.url, { cache: "no-store" });
      if (!wheelResponse.ok) throw new Error(`Failed to fetch wheel: HTTP ${wheelResponse.status}`);
      const wheelBytes = new Uint8Array(await wheelResponse.arrayBuffer());
      if (wheelBytes.byteLength < 1024) throw new Error(`Fetched wheel is unexpectedly small: ${wheelBytes.byteLength} bytes`);
      pyodide.FS.mkdirTree("/tmp");
      pyodide.FS.writeFile(wheel.path, wheelBytes);
      report("Placed RPR wheel", `${wheelBytes.byteLength} bytes`);

      packageStatus.textContent = "installing RPR";
      report("Installing RPR", wheel.path);
      await pyodide.runPythonAsync(`
import micropip
await micropip.install("emfs:${wheel.path}")
`);

      report("Loading demo scenario", "./demo_scenario.py");
      const scenarioResponse = await fetch("./demo_scenario.py", { cache: "no-store" });
      if (!scenarioResponse.ok) throw new Error(`Failed to fetch demo scenario: HTTP ${scenarioResponse.status}`);
      const scenarioSource = await scenarioResponse.text();
      await pyodide.runPythonAsync(scenarioSource);

      const version = pyodide.runPython(`
import importlib.metadata
importlib.metadata.version("responsibility-pathway-runtime")
`);
      packageStatus.textContent = `RPR ${version}`;
      ready = true;
      setControls(true);
      loadButton.textContent = "RPR loaded";
      document.documentElement.dataset.runtimeReady = "true";
      report("RPR loaded", `RPR ${version}`);
      await invoke("reset_demo");
    } catch (error) {
      console.error("[rpr-demo] startup failed", error);
      pythonStatus.textContent = "startup failed";
      packageStatus.textContent = "not loaded";
      output.textContent = `${error.name}: ${error.message}\n${error.stack || ""}`;
      summary.innerHTML = "<h3>RPR could not be loaded</h3><p>Check WebAssembly support, CDN access, browser memory limits, and Content Security Policy.</p>";
      document.documentElement.dataset.runtimeReady = "false";
      document.documentElement.dataset.demoError = `${error.name}: ${error.message}`;
      loadButton.disabled = false;
    }
  }

  loadButton.addEventListener("click", loadRuntime);
  runAllButton.addEventListener("click", () => invoke("run_full_demo"));
  resetButton.addEventListener("click", () => invoke("reset_demo"));
  stepButtons.forEach((button) => {
    button.addEventListener("click", () => invoke(button.dataset.function));
  });

  setControls(false);
})();
