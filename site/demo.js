/*
Language: JavaScript
Purpose: Load the CI-built RPR wheel into Pyodide and drive the real runtime demo scenario.
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
  const dispatchCount = document.getElementById("dispatch-count");
  const evidenceStatus = document.getElementById("evidence-status");
  const summary = document.getElementById("summary");
  const output = document.getElementById("output");

  const WHEEL_URL = "./assets/responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl";
  const WHEEL_PATH = "/tmp/responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl";

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
      summary.innerHTML = `<h3>実行失敗</h3><p><code>${payload.error_type}</code>: ${payload.error}</p>`;
      return;
    }
    const result = latestResult(payload);
    if (!result) return;
    const state = result.state || result.state_before || "unknown";
    const count = result.dispatch_count ?? result.provider?.dispatch_count ?? 0;
    const valid = result.evidence_valid;
    currentState.textContent = state;
    dispatchCount.textContent = String(count);
    evidenceStatus.textContent = valid === true ? "検証済み" : (valid === false ? "不正" : "未検証");
    document.documentElement.dataset.demoState = state;
    document.documentElement.dataset.dispatchCount = String(count);
    document.documentElement.dataset.evidenceValid = String(valid === true);
    summary.innerHTML = `
      <h3><code>${state}</code></h3>
      <p>実RPR packageが返した状態です。dispatch回数は<strong>${count}</strong>、証拠チェーンは<strong>${valid === true ? "valid" : "未確定"}</strong>です。</p>
      ${result.duplicate_dispatch_prevented === true ? "<p><strong>再起動後も二重dispatchは発生していません。</strong></p>" : ""}
    `;
  }

  async function invoke(functionName) {
    if (!ready) throw new Error("RPR runtime is not loaded");
    report("python-scenario", functionName);
    const quoted = JSON.stringify(functionName);
    const raw = await pyodide.runPythonAsync(`run_json(${quoted})`);
    const payload = JSON.parse(raw);
    updateView(payload);
    return payload;
  }

  async function loadRuntime() {
    loadButton.disabled = true;
    pythonStatus.textContent = "Pyodide取得中";
    packageStatus.textContent = "待機中";
    report("pyodide-loading", "初回は数十MBを取得する場合があります");
    try {
      pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/" });
      const pythonVersion = pyodide.runPython("import sys; sys.version.split()[0]");
      pythonStatus.textContent = `Python ${pythonVersion}`;
      report("python-packages-loading", "micropip + sqlite3");
      await pyodide.loadPackage(["micropip", "sqlite3"]);

      packageStatus.textContent = "wheelを取得中";
      report("wheel-fetch", WHEEL_URL);
      const wheelResponse = await fetch(WHEEL_URL, { cache: "no-store" });
      if (!wheelResponse.ok) {
        throw new Error(`wheel fetch failed: HTTP ${wheelResponse.status}`);
      }
      const wheelBytes = new Uint8Array(await wheelResponse.arrayBuffer());
      if (wheelBytes.byteLength < 1024) {
        throw new Error(`wheel response is unexpectedly small: ${wheelBytes.byteLength} bytes`);
      }
      pyodide.FS.mkdirTree("/tmp");
      pyodide.FS.writeFile(WHEEL_PATH, wheelBytes);
      report("wheel-fs-ready", `${wheelBytes.byteLength} bytes`);

      packageStatus.textContent = "wheelをインストール中";
      report("wheel-install", WHEEL_PATH);
      await pyodide.runPythonAsync(`
import micropip
await micropip.install("emfs:${WHEEL_PATH}")
`);

      report("scenario-fetch", "./demo_scenario.py");
      const scenarioResponse = await fetch("./demo_scenario.py", { cache: "no-store" });
      if (!scenarioResponse.ok) throw new Error(`demo_scenario.py fetch failed: HTTP ${scenarioResponse.status}`);
      const scenarioSource = await scenarioResponse.text();
      await pyodide.runPythonAsync(scenarioSource);

      const version = pyodide.runPython(`
import importlib.metadata
importlib.metadata.version("responsibility-pathway-runtime")
`);
      packageStatus.textContent = `RPR ${version}`;
      ready = true;
      setControls(true);
      loadButton.textContent = "実RPR起動済み";
      document.documentElement.dataset.runtimeReady = "true";
      report("runtime-ready", `RPR ${version}`);
      await invoke("reset_demo");
    } catch (error) {
      console.error("[rpr-demo] startup failed", error);
      pythonStatus.textContent = "起動失敗";
      packageStatus.textContent = "未読込";
      output.textContent = `${error.name}: ${error.message}\n${error.stack || ""}`;
      summary.innerHTML = "<h3>起動できませんでした</h3><p>ブラウザのWebAssembly、CDN接続、メモリ制限、Content Security Policyなどを確認してください。</p>";
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
