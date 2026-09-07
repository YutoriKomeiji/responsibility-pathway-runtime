<!--
Document Title: RPR 検証・Release・UAT
Document Type: Public Product Guide
Status: Public Alpha with Post-Release Source Preview
Version: 0.1.0a5
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 検証、release note、既知制約、UAT

## Release identity

| 項目 | 値 |
|---|---|
| Version | `0.1.0a5` |
| Channel | PyPI・GitHub Prereleaseで公開中のPublic Alpha |
| Tag | `v0.1.0a5` |
| Freeze ID | `RPR-CF-2026-08-02-01` |
| Product commit | `release-manifest.json`に記録 |
| Final rehearsal profile | Linux / Python 3.11、加えてBOM修整のbounded Windows field evidence |
| License | [`MIT License`](../../LICENSE) |

Repository sourceにはpost-`0.1.0a5` Responsibility Routing workが含まれる場合があります。`main`に存在するだけではpackage releaseへ昇格しません。次releaseにはfresh candidate、exact-head validation、明示的Human Gate approvalが必要です。

## 公開済み`0.1.0a5` Evidenceが示す範囲

Published evidence setは、pathway transition、persistent state、execution-attempt continuity、configured Human Gate・repair route、対応adapter path、fault injection、restart、backup/restore、diagnostics、removal、package installation、reproducible artifactを対象とします。

MCPについては、確認環境内のLocal subprocess / stdio経路、JSON-RPC framing、Server / Tool Binding、read-only MCP inspection、Fault Injection、結果不明の保持、Restart後の継続、Duplicate Dispatch防止を対象とします。Remote MCPやHosted MCP Service全般の互換性を示すものではありません。

| Evidence statement | 示すこと | 示さないこと |
|---|---|---|
| Testがpassした | 記録された環境・条件で対象caseがpassした | すべての環境・integrationでpassすること |
| Buildがreproducible | 試験したbuild processで一致artifactを生成した | 欠陥や脆弱性が存在しないこと |
| Pathwayがcompletedになった | そのcaseで必要Evidenceが一致した | Remote systemが普遍的なexactly-once semanticsを持つこと |
| Local MCP Testがpassした | 記録されたsubprocess / stdio caseが定義済みcheckを満たした | すべてのMCP Server、Transport、Tool、Remote Serviceが互換であること |
| UAT reportがpassした | 報告構成が定義済みcheckを満たした | 一般的な本番適合性、認証、保証 |

Verification documentationは観測結果と試験結果を記録するものです。MIT Licenseを変更せず、warranty、support obligation、certification、legal assuranceを追加しません。

## Post-`0.1.0a5` Responsibility Routing verification target

現行source-previewのRouting workは、release promotion前にunit testだけでなく製品品質全体で検証します。

必要Evidenceには次を含みます。

- route serializationとlegacy compatibility
- receiver eligibility validation
- generic fail-closed conditionからfalse human escalationを起こさないこと
- `REQUIRES_REEVALUATION` hold behavior
- Evidence、capability、route selection、transport successからAuthorityを推論しないこと
- Residual Owner preservation
- persistence/restart後のroute visibility
- ambiguous write -> `hold_for_reconciliation` visibility
- duplicate dispatchなしのreconciliation
- read-only MCP route visibilityと`authority_inferred: false`
- English / Japanese browser/demo assertion
- claim/test registry bindingとexact-head CI

Unit suiteがGREENなだけでは不十分です。

## Known limitations

| 分類 | 現在の境界 |
|---|---|
| Customer environment | 事前検証されていない |
| Platform | bounded field case以外のWindows、macOS、追加Linux、container、別Python profileにはfield evidenceが必要 |
| MCP | Local subprocess / stdioとlocal read-only inspectionは検証済み。Remote MCP、Hosted Service、企業Identity、Service固有readbackはintegration固有testが必要 |
| Responsibility Routing | 現行sourceはbounded route metadata/visibilityを実装。receiver eligibilityとorganizational delegation source-of-truthはintegrator-owned。release-level routing assuranceはfresh exact-head validation待ち |
| Enterprise integration | Proxy、TLS、identity、credential、remote serviceにはintegration固有testが必要 |
| Remote effect | 任意systemに対するexactly-onceを保証しない |
| Legal / security | Legal interpretation、organizational Authority生成、security certificationを提供しない |
| Formal Evidence | Leanが検証するのはselected state-transition invariantであり、receiver eligibilityやResponsibility Routing delegation semantics全体ではない |
| Compatibility | Alpha interfaceとmigration behaviorは変更される場合がある |
| MCP Server role | 公開済み`0.1.0a5`はread-only `rpr-mcp`を含み、mutating pathway operationは公開しない。現行sourceは`rpr.get_route_visibility`をpreviewする。 |

## Minimum UAT plan

最初はsyntheticまたはnon-consequential actionを使用します。

| 手順 | Acceptance check |
|---:|---|
| 1 | Environment、artifact digest、configuration、responsible ownerを記録する |
| 2 | Unauthorized transitionがfail closedになる |
| 3 | Required configured Human Gateを迂回できない |
| 4 | Generic evaluator/route failureがhuman destinationを自動生成しない |
| 5 | 使用するResponsibility Routeのreceiver eligibilityとdelegation scopeが明示されている |
| 6 | Independent readback付きdispatchが1件完了する |
| 7 | Ambiguous resultがfalse completionにならない |
| 8 | Restart後にunresolved dispatchが重複しない |
| 9 | `write_status_unknown`がAuthorityを推論せずreconciliation holdを可視化する |
| 10 | RepairまたはreconciliationがResidual Ownerを保持してdocumented end stateへ到達する |
| 11 | State backup/restoreが隔離環境で成功し、route-relevant material stateがreevaluateされる |
| 12 | Diagnostic outputにsecretが含まれない |
| 13 | Package removal後のdataが宣言policyどおり保持または削除される |

MCP統合では次も確認します。

| 手順 | MCP Acceptance check |
|---:|---|
| M1 | Dispatch前にProtocol Version、Server Identity、Capability、Tool Name、Tool Schemaがbindingされる |
| M2 | Pre-dispatch rejectionと、送信済みかもしれない結果不明を区別できる |
| M3 | Transport timeoutや不明結果が自動retryではなく`write_status_unknown`になる |
| M4 | 重要なToolではcompletion前に権威ある独立readbackを要求する |
| M5 | Restart後に未解決attemptを復元し、`tools/call`を黙って再送しない |
| M6 | Read-only route visibilityがapprove、execute、reconcile、resume、Authority grantを行えない |
| M7 | Remote / Hosted MCPの主張を、実際に試験した環境だけへ限定する |

## Reporting result

Expected / actual behavior、reproduction step、sanitized log、environment、RPR version、Freeze ID、artifact digest、adapter、readback source、必要ならroute classification / receiver eligibility、real external effectの有無を記録します。

MCPでは、Transport、Server実装とVersion、Protocol Version、Tool Name、Schema Digest、認証構成、障害時にDispatchを否定できたかも記録します。

各結果は`pass`、`fail`、`blocked`、`not applicable`、`not executed`のいずれかに分類します。Blockedや未実行caseをpassing Evidenceへ変換してはいけません。

## Release promotion gate

Tag、GitHub Release、binary publication、claim promotion、release declarationは、正確なcandidate HEADがsource、unit、component、integration、system/E2E、persistence/restart、package-install、formal-scope、secret/internal-reference、bilingual documentation、manifest/digest、claim/evidence checkを通過し、指定されたhuman approvalを得た後に実施します。

Frozen candidateがvalidation後に変わった場合、旧Evidenceを持ち越さず、修復済み`main`からfresh candidateを再構築します。
