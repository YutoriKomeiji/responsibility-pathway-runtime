# Claim Boundary Promotion（主張境界の昇格）

RPRでは、公開上の主張をevidence-governed stateとして扱います。現在のnon-claimを自動的に永久免責とはみなしません。

RPRは次を分離します。

1. 必要evidenceが揃いreviewされれば前進できる **evidence-limited boundary**
2. runtime単体では越えるべきでない **permanent responsibility boundary**

## Current Evidence Boundary

RPR 0.1.0a4はPublic Alphaであり、runtime、persistence、restart/reconciliation、MCP、packaging、browser/Pyodide、限定的Windows evidence、bounded formal-evidence surfaceを公開しています。これらが支えるのは現在のalpha claimまでです。

## Promotion Criteria

| 現在の境界 | 境界を前進させるevidence |
|---|---|
| production / enterprise readiness未主張 | sustained workload / soak evidence、対応deployment profile、supervisor/restart/upgrade/rollback evidence、operational monitoring/SLO evidence、review済みsecurity control |
| customer environment validationが限定的 | proxy/TLS/identity/credential/network/OS/container/MCP client profileごとの再現可能なfield evidence |
| broad exactly-once未主張 | 対象system側のtransaction/idempotency contractと、主張対象integration profileに対する独立かつ権威あるreadback |
| ledgerはtamper-evidentまで | 独立検証可能なsigning/attestation、external immutabilityまたはtimestamping、主張する場合のkey/trust governance |
| implementation-wide formal conformance未主張 | model-to-runtime refinement/conformance relationと、主張対象runtime surfaceの再現可能evidence |

Promotionは明示的に行い、version番号や経過時間だけから推定しません。

## Permanent Responsibility Boundaries

- RPR単体は法的・組織的・実行上のauthorityを生成しません。
- credential、identity provider、network、external system、business decisionそのものの正しさを生成しません。
- transport/MCP responseだけを重大なexternal effectの証明にしません。
- 最終的なoperational / organizational responsibilityは責任主体である人間・制度に残ります。
- 必要contractを持たない任意remote systemにuniversal exactly-onceを約束しません。
- abstract modelへのformal proofだけでPython runtime全体やdeployment全体を証明済みと扱いません。

これらは未完成機能ではなく責任境界です。

## Evidence Owner / Promotion State

RPR engineeringは宣言したruntime evidenceを担当します。Integrator/operatorは環境固有のidentity、credential、network、bypass prevention、monitoring、権威あるreadback evidenceを担当します。法務、認証、deployment、operational authorizationは資格・権限を持つ人間／制度が担当します。

可能な範囲でevidence依存境界は `evidence_collecting` / `review_ready` / `promoted`、恒久境界は `permanently_out_of_scope` を使用します。
