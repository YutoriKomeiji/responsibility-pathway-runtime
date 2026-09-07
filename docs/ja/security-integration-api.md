<!--
Document Title: RPR Security・Integration・API境界
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a5
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# Security、integration、API境界

RPRはMITライセンスのcontrol・evidence componentであり、完全なsecurity perimeter、managed security service、security certificationではありません。Projectはmechanismと試験結果を公開し、その周囲のsecurity architectureとdeployment判断はintegratorが担います。

## Trust boundaries

| Domain | 他のDomainから暗黙に推定してはいけないもの |
|---|---|
| Human / institutional Authority | Host applicationが示すidentityやauthorization |
| Receiver capability | Receiver eligibilityやdelegated Authority |
| Evidence transfer | Authority transferやownership transfer |
| Host application | RPR stateやremote effectの正しさ |
| RPR state / evidence store | Adapterやexternal serviceの信頼性 |
| Adapter process | Independent readbackやbusiness authorization |
| Credential store | 特定business actionの実行許可 |
| Remote system | Callbackやlocal execution resultの正しさ |
| Independent readback source | Proposed actionやpolicyの妥当性 |
| Optional RPE service | Execution success、completion Evidence、または自動的に妥当なhuman destination |

Adapter return valueは自動的に独立readbackにはなりません。Successful transportやroute selectionもAuthorityではありません。

## Integration contract

| 項目 | Integrationが定義するもの |
|---|---|
| Action surface | Accepted action・actor schema |
| Authority | Authorization、delegation source-of-truth、bounded Human Gate要件 |
| Responsibility Routing | Receiver eligibility、route class、unresolved payload、bounded next actions、closure/reevaluation condition、Residual Owner |
| Identity | Stable operation・idempotency identity |
| State | Permitted transitionとfailure handling |
| Dispatch | Timeout、cancellation、retry behavior |
| Evidence | Authoritative readback sourceとmatching rule |
| Ambiguity | `write_status_unknown`、hold、repair、reconciliation handling |
| Ownership | Repair、resume、incident、residual-effect owner |
| Data | Classification、retention、export、deletion rule |
| Observability | Monitoring、alerting、incident route |

## Fail-closed routing rule

`Fail closed`は`send to a human`を意味しません。

Missing evaluator、malformed contract、invalid route、ineligible receiver、unresolved external effectからhuman destinationを推論してはいけません。Eligible receiverと必要Authorityが確立されるまでneutral holdが正しい場合があります。

明示的にconfiguredされたbounded Human Gateが必要な場合、Human Returnは正当なrouteとして維持されます。Evidence transfer、receiver capability、confidence、tool success、successful transport、recovered state、route selectionはAuthorityを生成しません。

## Host security controls

RPRは、authenticated user/service、least-privilege credential、network policy、endpoint・command allow-list、protected persistence、log redaction、supply-chain control、monitoring、bypass preventionを備えたhost architecture内へ配置します。

Host applicationは、同じ重大operationに対してpathway admission、route eligibility、Authority check、Evidence handlingを迂回するparallel execution pathを公開してはいけません。

## API stability

`0.1.0a5`は現在の公開Public Alphaです。Versionをpinし、serialized state、CLI behavior、adapter configuration、migration procedureをupgrade前に検証してください。Repository sourceには`0.1.0a5`公開後のResponsibility Routing workが含まれる場合があり、fresh candidateの再構築・検証・承認までは公開packageのcontractではありません。Stable release前には非互換修正が入る場合があります。

## Credentialsと脆弱性報告

Documentationとexampleにはplaceholderを使用し、credentialは外部secret mechanismから供給してください。Evidence、exception、diagnostic bundle、Issue、release artifactへsecretを含めてはいけません。

Exploit可能性のある内容は公開Issueへ投稿せず、[`SECURITY.md`](../../SECURITY.md)の非公開経路を使用してください。

## License boundary

[`MIT License`](../../LICENSE)は、その条件に従った利用・変更・再配布を許可し、softwareを無保証で提供します。この文書はsecurity warranty、certification、indemnity、特定integrationの安全性や本番適合性の保証を追加するものではありません。
