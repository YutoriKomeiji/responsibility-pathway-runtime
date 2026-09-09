# Claim Boundary Promotion（主張境界の昇格）

RPRでは、公開上の主張をevidence-governed stateとして扱います。現在のnon-claimを自動的に永久免責とはみなしません。

RPRは次を分離します。

1. 必要Evidenceが揃いreviewされれば前進できる **evidence-limited boundary**
2. runtime単体では越えるべきでない **permanent responsibility boundary**

## Current Evidence Boundary

RPR `0.1.0a6`は現在の公開Public Alphaです。公開済みsurfaceには、bounded Responsibility Routing、route visibility、runtime/persistence/restart/reconciliation、MCP、packaging、browser/Pyodide、bounded Windows field evidence、bounded formal-evidence surfaceが含まれます。これらが支えるのは、現行product documentationで明示された公開済みalpha claimまでです。

`0.1.0a6`の公開は、production / enterprise readiness、あらゆる組織経路の自動妥当化、法的/compliance Authority、universal exactly-once、implementation-wide formal conformanceを意味しません。今後のsource変更も、別途validationとpromotionが完了するまではreleased claimになりません。

## Promotion Criteria

| 現在の境界 | 境界を前進させるEvidence |
|---|---|
| production / enterprise readiness未主張 | sustained workload / soak evidence、対応deployment profile、supervisor/restart/upgrade/rollback evidence、operational monitoring/SLO evidence、review済みsecurity control |
| customer environment validationが限定的 | proxy/TLS/identity/credential/network/OS/container/MCP client profileごとの再現可能なfield evidence |
| Responsibility Routingは文書化されたPublic Alpha contract内でのみrelease済み | 宣言済みreceiver/delegation profileに対するより広いintegration evidence、route-level operational evidence、claim/test traceability、exact-head package/CI evidence、拡張claimに対する明示的promotion review |
| broad exactly-once未主張 | 対象system側のtransaction/idempotency contractと、主張対象integration profileに対する独立かつ権威あるreadback |
| ledgerはtamper-evidentまで | 独立検証可能なsigning/attestation、external immutabilityまたはtimestamping、主張する場合のkey/trust governance |
| implementation-wide formal conformance未主張 | model-to-runtime refinement/conformance relationと、主張対象runtime surfaceの再現可能Evidence |

Promotionは明示的に行い、経過時間、version番号、source availability、subset testのGREENだけから推定しません。

## Permanent Responsibility Boundaries

- RPR単体は法的・組織的・実行上のAuthorityを生成しません。
- Responsibility Routingは、receiverがcapable、selected、notified、またはEvidenceを受領しただけでAuthorityを生成しません。
- Human Returnはbounded Responsibility Routeであり、すべてのfail-closed conditionのgeneric fallbackではありません。
- Unresolved/invalid routeは、receiver eligibilityとAuthorityが確立されるまでneutral holdのままが正しい場合があります。
- Credential、identity provider、network、external system、business decisionそのものの正しさを生成しません。
- transport/MCP responseだけを重大なexternal effectの証明にしません。
- Route selectionやsuccessful transferだけでResidual Ownerを暗黙置換しません。
- 最終legal/institutional accountabilityは、周囲のsystemにおける責任主体である人間・制度に残ります。
- 必要contractを持たない任意remote systemにuniversal exactly-onceを約束しません。
- abstract state modelへのformal proofだけでPython runtime全体、Responsibility Routingのreceiver eligibility/delegation semantics、deployment全体を証明済みと扱いません。

これらは未完成機能ではなく責任境界です。

## Evidence Owner / Promotion State

RPR engineeringは宣言したruntime / route mechanism Evidenceを担当します。Integrator/operatorは環境固有のidentity、receiver eligibility、delegation source-of-truth、credential、network、bypass prevention、monitoring、権威あるreadback Evidenceを担当します。法務、認証、deployment、operational authorizationは資格・権限を持つ人間／制度が担当します。

可能な範囲でEvidence依存境界は `evidence_collecting` / `review_ready` / `promoted`、恒久境界は `permanently_out_of_scope` を使用します。
