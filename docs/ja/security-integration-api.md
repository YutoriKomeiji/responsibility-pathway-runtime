<!--
Document Title: RPR Security・Integration・API境界
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# Security、integration、API境界

RPRはMITライセンスのcontrol・evidence componentであり、完全なsecurity perimeter、managed security service、security certificationではありません。Projectはmechanismと試験結果を公開し、その周囲のsecurity architectureとdeployment判断はintegratorが担います。

## Trust boundaries

| Domain | 他のDomainから暗黙に推定してはいけないもの |
|---|---|
| Human / institutional authority | Host applicationが示すidentityやauthorization |
| Host application | RPR stateやremote effectの正しさ |
| RPR state / evidence store | Adapterやexternal serviceの信頼性 |
| Adapter process | Independent readbackやbusiness authorization |
| Credential store | 特定business actionの実行許可 |
| Remote system | Callbackやlocal execution resultの正しさ |
| Independent readback source | Proposed actionやpolicyの妥当性 |
| Optional RPE service | Execution successやcompletion evidence |

Adapter return valueは、自動的に独立readbackにはなりません。

## Integration contract

| 項目 | Integrationが定義するもの |
|---|---|
| Action surface | Accepted action・actor schema |
| Authority | AuthorizationとHuman Gate要件 |
| Identity | Stable operation・idempotency identity |
| State | Permitted transitionとfailure handling |
| Dispatch | Timeout、cancellation、retry behavior |
| Evidence | Authoritative readback sourceとmatching rule |
| Ambiguity | `write_status_unknown`、repair、reconciliation handling |
| Ownership | Repair、resume、incident、residual-effect owner |
| Data | Classification、retention、export、deletion rule |
| Observability | Monitoring、alerting、incident route |

## Host security controls

RPRは、authenticated user/service、least-privilege credential、network policy、endpoint・command allow-list、protected persistence、log redaction、supply-chain control、monitoring、bypass preventionを備えたhost architecture内へ配置します。

Host applicationは、同じ重大operationに対してpathway admissionやevidence handlingを迂回するparallel execution pathを公開してはいけません。

## API stability

`0.1.0a2`はPublic Alphaです。Versionをpinし、serialized state、CLI behavior、adapter configuration、migration procedureをupgrade前に検証してください。Stable release前には非互換修正が入る場合があります。

## Credentialsと脆弱性報告

Documentationとexampleにはplaceholderを使用し、credentialは外部secret mechanismから供給してください。Evidence、exception、diagnostic bundle、Issue、release artifactへsecretを含めてはいけません。

Exploit可能性のある内容は公開Issueへ投稿せず、[`SECURITY.md`](../../SECURITY.md)の非公開経路を使用してください。

## License boundary

[`MIT License`](../../LICENSE)は、その条件に従った利用・変更・再配布を許可し、softwareを無保証で提供します。この文書はsecurity warranty、certification、indemnity、特定integrationの安全性や本番適合性の保証を追加するものではありません。
