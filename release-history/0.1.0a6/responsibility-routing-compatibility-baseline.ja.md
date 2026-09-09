# Historical record — Responsibility Routing 互換実装ベースライン

Lifecycle: `HISTORICAL`

この文書は、Responsibility RoutingがPublic Alpha `0.1.0a6`へ移行する過程で使われた日本語互換ベースラインを保存する履歴記録です。以下に残る「現在」「公開中」「source preview」等の表現は、当時の状態を示すものであり、現在の製品状態を示しません。現在状態は`product-status.json`と`docs/ja/README.md`を参照してください。

---

## 当時の互換設計要点

- Human Returnは有効だがbounded Responsibility Routeとして扱う。
- `PathwayState.HUMAN_GATE` -> `bounded_human_return`。
- `PathwayState.WRITE_STATUS_UNKNOWN` -> `hold_for_reconciliation`。
- Evidence transfer、receiver capability、route selection、transport success、recovered stateはAuthorityを生成しない。
- Optional routeは既存definition JSON内へadditiveに保存し、SQLite schema version 1を変更しない。
- Route typeは当時top-level `rpr` Python exportへ昇格せず、read-only MCP `rpr.get_route_visibility`を外部inspection surfaceとした。
- Invalid/ineligible route、RPE利用不可、結果不明からHuman Gateを自動生成しない。成立条件がなければneutral `HOLD`が有効。
- `write_status_unknown`はsuccess/failure/blind retry/forced Human Returnへ変換せず、独立readback/reconciliationに残す。
- Residual Ownerは別途認可されたownership変更なしにroute selectionで置換しない。
- Lean 4は選択されたstate-transition invariantのみを対象とし、receiver eligibility/delegation semantics全体の形式証明を意味しない。

## 履歴上の注意

元の日本語文書は`0.1.0a5`を公開中、Responsibility Routingをsource previewとして記述していた時点の文面を含んでいた。`0.1.0a6`公開後もactive docsに残ったことがDAN-104のpost-release reconciliation設計を起動する一因になった。この履歴記録はその事実を保持しつつ、current-facing guidanceから分離するためのもの。
