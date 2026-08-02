/*
Language: JavaScript
Purpose: Static explanatory simulator for the published RPR state machine.
Boundary: No network calls, persistence, credentials, analytics, or runtime execution.
*/
(() => {
  "use strict";

  const transitions = {
    proposed: ["awaiting_approval", "approved", "denied"],
    awaiting_approval: ["approved", "denied", "human_gate"],
    approved: ["running", "held", "aborted"],
    running: ["completed", "stopped", "partially_completed", "write_status_unknown", "repair_required"],
    held: ["human_gate", "approved", "aborted"],
    human_gate: ["approved", "denied", "aborted"],
    stopped: ["repair_required", "aborted"],
    partially_completed: ["repair_required"],
    write_status_unknown: ["completed", "repair_required"],
    repair_required: ["ready_to_resume", "aborted"],
    ready_to_resume: ["running", "aborted"],
    completed: [],
    denied: [],
    aborted: []
  };

  const labels = {
    proposed: "操作が提案されました。まだ外部作用は始まっていません。",
    awaiting_approval: "承認待ちです。誰が、何を承認するかを確定する必要があります。",
    approved: "承認済みですが、まだ実行前です。前提が変わっていないか確認できます。",
    running: "外部作用を実行中です。dispatchの成功だけでは完了証拠になりません。",
    held: "実行前または継続前に保留しました。Human Gateまたは再評価へ進みます。",
    human_gate: "人間の判断が必要です。自動処理はこの状態を迂回できません。",
    stopped: "継続を停止しました。再開ではなく、まず修復または中止を判断します。",
    partially_completed: "一部だけ完了しました。通常実行を繰り返さず、修復経路へ進みます。",
    write_status_unknown: "書き込み結果が不明です。推測で成功・失敗へ閉じず、独立確認が必要です。",
    repair_required: "修復が必要です。通常実行とは別の担当者・権限・証拠を使います。",
    ready_to_resume: "再開条件が揃いました。ただし、再開可能と完了は別です。",
    completed: "独立した証拠を含む完了状態です。終端状態なので後続遷移はありません。",
    denied: "実行は拒否されました。外部作用を開始しない終端状態です。",
    aborted: "経路を中止しました。終端状態なので再利用しません。"
  };

  const currentState = document.getElementById("current-state");
  const effectStatus = document.getElementById("effect-status");
  const evidenceStatus = document.getElementById("evidence-status");
  const humanStatus = document.getElementById("human-status");
  const pathway = document.getElementById("pathway");
  const buttons = document.getElementById("transition-buttons");
  const explanation = document.getElementById("explanation");
  const reset = document.getElementById("reset");

  let state = "proposed";
  let history = [state];

  function statusFor(next) {
    const effectStarted = ["running", "stopped", "partially_completed", "write_status_unknown", "repair_required", "ready_to_resume", "completed"].includes(next);
    effectStatus.textContent = effectStarted ? (next === "completed" ? "確認済み" : "開始または可能性あり") : "未開始";
    evidenceStatus.textContent = next === "completed" ? "独立確認あり" : (next === "write_status_unknown" ? "不足・照合待ち" : "未確定");
    humanStatus.textContent = next === "human_gate" ? "判断待ち" : (["held", "repair_required"].includes(next) ? "必要になる可能性" : "未要求");
  }

  function render() {
    currentState.textContent = state;
    statusFor(state);
    pathway.innerHTML = "";
    history.forEach((item) => {
      const node = document.createElement("div");
      node.textContent = item;
      if (item === state) node.classList.add("accent");
      pathway.appendChild(node);
    });

    buttons.innerHTML = "";
    const allowed = transitions[state];
    if (allowed.length === 0) {
      const terminal = document.createElement("article");
      terminal.className = "card";
      terminal.innerHTML = "<h3>終端状態</h3><p>この状態から許可された後続遷移はありません。最初から試す場合はリセットしてください。</p>";
      buttons.appendChild(terminal);
    } else {
      allowed.forEach((next) => {
        const card = document.createElement("article");
        card.className = "card";
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button secondary";
        button.textContent = next;
        button.addEventListener("click", () => {
          state = next;
          history.push(next);
          render();
        });
        const text = document.createElement("p");
        text.textContent = labels[next];
        card.append(button, text);
        buttons.appendChild(card);
      });
    }

    explanation.innerHTML = `<h3><code>${state}</code></h3><p>${labels[state]}</p>`;
  }

  reset.addEventListener("click", () => {
    state = "proposed";
    history = [state];
    render();
  });

  render();
})();
