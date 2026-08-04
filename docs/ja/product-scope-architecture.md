<!--
Document Title: RPR 製品範囲とarchitecture
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 製品範囲とarchitecture

## Product role

Responsibility Pathway Runtime（RPR）は、host applicationのdecision logicと重大なexternal actionの間に配置するMITライセンスのsoftware componentです。提案actionからauthority、execution attempt、evidence、repairまたはreconciliation、Human Gateへの返却までを再構成可能な経路として保持します。

```text
host application
  -> proposed action + actor + authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | human gate
  -> evidence retained for reconstruction
```

## Capability map

| Capability | RPRが提供するもの | RPRの外に残るもの |
|---|---|---|
| Pathway lifecycle | State modelと許可transition | Business policyの作成 |
| Execution continuity | 永続operationとattempt | Remote systemのtransaction保証 |
| Evidence | Evidence保持、provenance、readback workflow | 権威ある外部evidence source |
| Human control | Human Gate、repair、resume、reconciliation state | Authorized decision makerの選定と本人性確認 |
| Adapter | Local file、HTTP、message、outbound MCPのbounded path | Network trust、credential、service固有semantics |
| Recovery | Ambiguous write保持とrestart continuity | Incident staffingと運用ownership |

## Architecture上のMCP位置づけ

RPRは現在、MCP統合のClient側で動きます。Host ApplicationがMCP Tool Callを提案し、RPRがActor、Authority、Pathway State、Server / Tool Binding、Execution Attemptを保持したうえで、許可されたTransportが`tools/call`を実行します。

```text
Host ApplicationまたはAgent
  -> RPRのPathwayとAuthority確認
  -> 許可されたMCP Server / Tool Binding
  -> Local subprocessとstdio transport
  -> tools/call result
  -> 必要な場合は独立readback
  -> complete | write_status_unknown | repair | reconcile | human gate
```

現在のReleaseは、RPR自身をMCP Serverとして公開しません。Remote MCP Service、Hosted Transport、企業Identity、Service固有readbackは、環境ごとの評価が必要です。

## Stateとevidenceの原則

| 原則 | 必要な挙動 |
|---|---|
| Attemptはcompletionではない | Dispatch済みwriteだけで完了扱いしない |
| Evidenceでcompletionを閉じる | Integrationが定義したevidence classを要求する |
| UnknownはUnknownのまま保持 | Reconciliationなしに`write_status_unknown`をsuccessへ変更しない |
| Restartはretryではない | 未解決attemptを復元して暗黙再送しない |
| Recoveryを明示する | Repairとreconciliationをhidden exception handlingにしない |
| Approvalはeffect証明ではない | Human approvalはdecision evidenceでありremote resultの証明ではない |
| MCP応答はeffect証明ではない | 重要な外部作用では、`tools/call`成功応答だけで権威あるreadbackを置き換えない |

## Integration boundary

Host applicationは、許可action、authorization、credential隔離、bypass防止、MCP Serverの選定、Tool Permission、独立readback、data handling、deployment承認、運用ownershipを定義します。RPRは宣言された責任経路を保持・強制するmechanismを提供しますが、個別deploymentの法令適合、安全性、特定用途への適合性を判定しません。

## Optional RPE integration

Responsibility Pathway Engineering（RPE）はexternal gate decisionを提供できます。RPEはactionを実行せず、RPRのexecution evidenceを置き換えません。RPE不在、malformed output、unsupported version、inapplicable resultは可視化し、integration contractに従って扱います。

## Licenseと非主張

RPRは[`MIT License`](../../LICENSE)の条件で提供され、無保証です。

RPRはlegal-responsibility engine、policy author、identity provider、secret manager、production gateway、MCP trust oracle、certification、universal transaction coordinator、任意remote systemに対するexactly-once保証ではありません。Public Alphaは、すべての環境や用途への適合を表明するものではありません。
