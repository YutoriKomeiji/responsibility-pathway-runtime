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
      summary.innerHTML = `<h3>実行できませんでした</h3><p><code>${payload.error_type}</code>: ${payload.error}</p>`;
      return;
    }
    const result = latestResult(payload);
    if (!result) return;
    const state = result.state || result.state_before || "unknown";
    const count = result.dispatch_count ?? result.provider?.dispatch_count ?? 0;
    const valid = result.evidence_valid;
    currentState.textContent = state;
    dispatchCount.textContent = String(count);
    evidenceStatus.textContent = valid === true ? "検証済み" : (valid === false ? "不整合" : "未検証");
    document.documentElement.dataset.demoState = state;
    document.documentElement.dataset.dispatchCount = String(count);
    document.documentElement.dataset.evidenceValid = String(valid === true);
    summary.innerHTML = `
      <h3>現在の状態: <code>${state}</code></h3>
      <p>外部サービスへの実行は<strong>${count}回</strong>です。証拠チェーンは<strong>${valid === true ? "検証済み" : "未確定"}</strong>です。</p>
      ${result.duplicate_dispatch_prevented === true ? "<p><strong>再起動後も同じ操作を再送していません。</strong></p>" : ""}
    `;
  }

  async function resolveWheelLocation() {
    const response = await fetch(WHEEL_MANIFEST_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`wheel manifestの取得に失敗しました: HTTP ${response.status}`);
    const manifest = (await response.text()).trim();
    const match = manifest.match(/\b(responsibility_pathway_runtime-[0-9A-Za-z.+-]+-py3-none-any\.whl)\b/);
    if (!match) throw new Error(`wheel manifestを解析できません: ${manifest}`);
    const filename = match[1];
    return {
      url: `./assets/${filename}`,
      path: `/tmp/${filename}`,
    };
  }

  async function invoke(functionName) {
    if (!ready) throw new Error("RPRがまだ読み込まれていません");
    report("シナリオを実行中", functionName);
    const quoted = JSON.stringify(functionName);
    const raw = await pyodide.runPythonAsync(`run_json(${quoted})`);
    const payload = JSON.parse(raw);
    updateView(payload);
    return payload;
  }

  async function loadRuntime() {
    loadButton.disabled = true;
    pythonStatus.textContent = "Pyodideを取得中";
    packageStatus.textContent = "待機中";
    report("Python環境を準備中", "初回は数十MBを取得する場合があります");
    try {
      pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/" });
      const pythonVersion = pyodide.runPython("import sys; sys.version.split()[0]");
      pythonStatus.textContent = `Python ${pythonVersion}`;
      report("Python packageを準備中", "micropip + sqlite3");
      await pyodide.loadPackage(["micropip", "sqlite3"]);

      const wheel = await resolveWheelLocation();
      packageStatus.textContent = "RPR wheelを取得中";
      report("RPR wheelを取得中", wheel.url);
      const wheelResponse = await fetch(wheel.url, { cache: "no-store" });
      if (!wheelResponse.ok) throw new Error(`wheelの取得に失敗しました: HTTP ${wheelResponse.status}`);
      const wheelBytes = new Uint8Array(await wheelResponse.arrayBuffer());
      if (wheelBytes.byteLength < 1024) throw new Error(`取得したwheelが小さすぎます: ${wheelBytes.byteLength} bytes`);
      pyodide.FS.mkdirTree("/tmp");
      pyodide.FS.writeFile(wheel.path, wheelBytes);
      report("RPR wheelを配置しました", `${wheelBytes.byteLength} bytes`);

      packageStatus.textContent = "RPRをインストール中";
      report("RPRをインストール中", wheel.path);
      await pyodide.runPythonAsync(`
import micropip
await micropip.install("emfs:${wheel.path}")
`);

      report("デモシナリオを読み込み中", "./demo_scenario.py");
      const scenarioResponse = await fetch("./demo_scenario.py", { cache: "no-store" });
      if (!scenarioResponse.ok) throw new Error(`デモシナリオの取得に失敗しました: HTTP ${scenarioResponse.status}`);
      const scenarioSource = await scenarioResponse.text();
      await pyodide.runPythonAsync(scenarioSource);

      const version = pyodide.runPython(`
import importlib.metadata
importlib.metadata.version("responsibility-pathway-runtime")
`);
      packageStatus.textContent = `RPR ${version}`;
      ready = true;
      setControls(true);
      loadButton.textContent = "RPR読込済み";
      document.documentElement.dataset.runtimeReady = "true";
      report("RPRを読み込みました", `RPR ${version}`);
      await invoke("reset_demo");
    } catch (error) {
      console.error("[rpr-demo] startup failed", error);
      pythonStatus.textContent = "準備失敗";
      packageStatus.textContent = "未読込";
      output.textContent = `${error.name}: ${error.message}\n${error.stack || ""}`;
      summary.innerHTML = "<h3>RPRを読み込めませんでした</h3><p>WebAssemblyへの対応、CDNへの接続、ブラウザのメモリ制限、Content Security Policyを確認してください。</p>";
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
