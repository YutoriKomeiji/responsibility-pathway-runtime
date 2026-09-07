<!--
Document Title: RPR 製品範囲とarchitecture
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 製品範囲とarchitecture

## Product role

Responsibility Pathway Runtime（RPR）は、host applicationのdecision logicと重大なexternal actionの間に配置するMITライセンスのsoftware componentです。提案actionからdeclared Authority、execution attempt、Evidence、reconciliation / repair / resume、Responsibility Routingまでを再構成可能な経路として保持します。Human Returnはbounded routeの一つであり、すべてのfail-closed conditionのgeneric destinationではありません。

```text
host application
  -> proposed action + actor + declared Authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | hold | bounded human gate
  -> responsibility route + evidence retained for reconstruction
```

## Capability map

| Capability | RPRが提供するもの | RPRの外に残るもの |
|---|---|---|
| Pathway lifecycle | State modelと許可transition | Business policyの作成 |
| Execution continuity | 永続operationとattempt | Remote systemのtransaction保証 |
| Evidence | Evidence保持、provenance、readback workflow | 権威あるexternal evidence source |
| Responsibility Routing | Route metadata、eligibility state、bounded next actions、closure/reevaluation condition、Residual Owner | receiver eligibilityの正本、organizational delegationの正当性、最終legal/institutional accountability |
| Human control | 明示的にconfiguredなHuman Gate、repair、resume、reconciliation state | Authorized decision makerの選定と本人性確認 |
| Adapter | Local file、HTTP、message、outbound MCPのbounded path | Network trust、credential、service固有semantics |
| Recovery | Ambiguous write保持とrestart continuity | Incident staffingと運用ownership |

## Architecture上のMCP位置づけ

RPRはClient側からoutbound MCP Callを統治できます。Host ApplicationがMCP Tool Callを提案し、RPRがActor、declared Authority、Pathway State、Server / Tool Binding、Execution Attempt、関連route metadataを保持したうえで、許可されたTransportが`tools/call`を実行します。

```text
Host ApplicationまたはAgent
  -> RPRのPathway、Authority、Route確認
  -> 許可されたMCP Server / Tool Binding
  -> Local subprocessとstdio transport
  -> tools/call result
  -> 必要な場合は独立readback
  -> complete | write_status_unknown | repair | reconcile | bounded human gate | hold
```

公開済み`0.1.0a6`にはlocal read-only `rpr-mcp` inspection serverと`rpr.get_route_visibility`が含まれます。Remote MCP Service、Hosted Transport、企業Identity、Service固有readbackは環境ごとの評価が必要です。

## State、route、Evidenceの原則

| 原則 | 必要な挙動 |
|---|---|
| Attemptはcompletionではない | Dispatch済みwriteだけで完了扱いしない |
| Evidenceでcompletionを閉じる | Integrationが定義したEvidence classを要求する |
| UnknownはUnknownのまま保持 | Reconciliationなしに`write_status_unknown`をsuccessへ変更しない |
| Restartはretryではない | 未解決attemptを復元して暗黙再送しない |
| Recoveryを明示する | Repairとreconciliationをhidden exception handlingにしない |
| Approvalはeffect証明ではない | Human approvalはdecision Evidenceでありremote resultの証明ではない |
| MCP応答はeffect証明ではない | 重要なexternal effectでは、`tools/call`成功応答だけでauthoritative readbackを置き換えない |
| Fail-closedは自動的にHuman Gateではない | Invalid route、unavailable evaluator、unknown receiverではneutral holdが必要な場合がある |
| Evidence transferはAuthority transferではない | capability、route selection、transport success、recovered stateはAuthorityを生成しない |
| Residueはownerを保持する | Routingはunresolved payloadとResidual Ownerを保持し、ownership変更には明示的かつ認可された再設計を要求する |

## Integration boundary

Host applicationは、許可action、authentication / authorization、receiver eligibility、delegation source-of-truth、credential隔離、bypass防止、MCP Serverの選定、Tool Permission、独立readback、data handling、deployment承認、運用ownershipを定義します。RPRは宣言された責任経路を保持・強制するmechanismを提供しますが、個別deploymentの法令適合、安全性、特定用途への適合性を判定しません。

## Optional RPE integration

Responsibility Pathway Engineering（RPE）はexternal gate decisionを提供できます。RPEはactionを実行せず、RPRのexecution Evidenceを置き換えません。RPE不在、malformed output、unsupported version、inapplicable resultは、implicit permissionやinvented human destinationへ変換せずfail closedで扱います。一方、明示的にconfiguredされたhigh-impact Human Gateが自身のAuthority条件から必要な場合、そのbounded Human Gateは維持されます。

## Published releaseの境界

現在の公開済みpackageは`0.1.0a6`です。Repository sourceには次package承認前のworkが含まれる場合があります。Sourceが存在するだけでは、package contract、release Evidence、support maturityは昇格しません。

次releaseには、`main`から再構築したfresh candidate、exact-head test / document / claim validation、明示的Human Gate approvalが必要です。

## Licenseと非主張

RPRは[`MIT License`](../../LICENSE)の条件で提供され、無保証です。

RPRはlegal-responsibility engine、policy author、identity provider、secret manager、production gateway、MCP trust oracle、certification、universal transaction coordinator、任意remote systemに対するexactly-once保証ではありません。選択されたLean modelが証明するのはbounded state-transition invariantであり、Responsibility Routingのreceiver eligibilityやdelegation semantics全体ではありません。Public Alphaは、すべての環境や用途への適合を表明するものではありません。
