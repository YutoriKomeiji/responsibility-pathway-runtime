<!--
Document Title: RPR 検証・Release・UAT
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 検証、release note、既知制約、UAT

## Release identity

| 項目 | 値 |
|---|---|
| Version | `0.1.0a6` |
| Channel | PyPI・GitHub Prereleaseで公開中のPublic Alpha |
| Tag | `v0.1.0a6` |
| Release commit | `9f71a34f5d7eb0e25359ccf31d0c6d85570203d8` |
| Publish workflow | `34087946734` — success |
| Final rehearsal profile | Linux / Python 3.11、加えてBOM修整のbounded Windows field evidence |
| License | [`MIT License`](../../LICENSE) |

Repository sourceには次release向けworkが含まれる場合があります。`main`に存在するだけではpackage releaseへ昇格しません。次releaseにはfresh candidate、exact-head validation、明示的Human Gate approvalが必要です。

## 公開済み`0.1.0a6` Evidenceが示す範囲

Published evidence setは、pathway transition、persistent state、execution-attempt continuity、configured Human Gate・repair route、Responsibility Routing、対応adapter path、fault injection、restart、backup/restore、diagnostics、removal、package installation、reproducible artifactを対象とします。

MCPについては、確認環境内のLocal subprocess / stdio経路、JSON-RPC framing、Server / Tool Binding、read-only MCP inspection、read-only route visibility、Fault Injection、結果不明の保持、Restart後の継続、Duplicate Dispatch防止を対象とします。Remote MCPやHosted MCP Service全般の互換性を示すものではありません。

| Evidence statement | 示すこと | 示さないこと |
|---|---|---|
| Testがpassした | 記録された環境・条件で対象caseがpassした | すべての環境・integrationでpassすること |
| Buildがreproducible | 試験したbuild processで一致artifactを生成した | 欠陥や脆弱性が存在しないこと |
| Pathwayがcompletedになった | そのcaseで必要Evidenceが一致した | Remote systemが普遍的なexactly-once semanticsを持つこと |
| Local MCP Testがpassした | 記録されたsubprocess / stdio caseが定義済みcheckを満たした | すべてのMCP Server、Transport、Tool、Remote Serviceが互換であること |
| UAT reportがpassした | 報告構成が定義済みcheckを満たした | 一般的な本番適合性、認証、保証 |

Verification documentationは観測結果と試験結果を記録するものです。MIT Licenseを変更せず、warranty、support obligation、certification、legal assuranceを追加しません。

## `0.1.0a6`に含まれるResponsibility Routing検証

Release-level Evidenceには次が含まれます。

- route serializationとlegacy compatibility
- receiver eligibility validation
- generic fail-closed conditionからfalse human escalationを起こさないこと
- `REQUIRES_REEVALUATION` hold behavior
- Evidence、capability、route selection、transport successからAuthorityを推論しないこと
- Residual Owner preservation
- persistence/runtime recreation後のroute visibility
- ambiguous write -> `hold_for_reconciliation` visibility
- duplicate dispatchなしのreconciliation
- read-only MCP route visibilityと`authority_inferred: false`
- English / Japanese browser/demo assertion
- claim/test registry bindingとexact-head CI

Release candidateは公開前に、standalone suite 477件、production-grade demo、clean wheel installとCLI check、Lean / JSON / Python parity、reproducible artifact verification、EN/JA browser/Pyodide E2Eを通過しました。

## 公開artifact Evidence

| Artifact | SHA256 |
|---|---|
| `responsibility_pathway_runtime-0.1.0a6-py3-none-any.whl` | `3db42d6d1289e2a1f1a20afc8d181a7bc433dcbb8e7ea87416415192a6ca6cb2` |
| `responsibility_pathway_runtime-0.1.0a6.tar.gz` | `0690b9ea23831ea5dc24578accecb68fccc7a0737bbf71facdd09be629f0874f` |

PyPIはTrusted Publishing経路で両artifactを受理し、public readbackで`0.1.0a6` pageとfile metadataを確認しました。公開時にdigital attestationも生成されています。

## Known limitations

| 分類 | 現在の境界 |
|---|---|
| Customer environment | 事前検証されていない |
| Platform | bounded field case以外のWindows、macOS、追加Linux、container、別Python profileにはfield evidenceが必要 |
| MCP | Local subprocess / stdio、local read-only inspection、read-only route visibilityは検証済み。Remote MCP、Hosted Service、企業Identity、Service固有readbackはintegration固有testが必要 |
| Responsibility Routing | bounded route metadata/visibilityは公開済み。receiver eligibilityとorganizational delegation source-of-truthはintegrator-owned |
| Enterprise integration | Proxy、TLS、identity、credential、remote serviceにはintegration固有testが必要 |
| Remote effect | 任意systemに対するexactly-onceを保証しない |
| Legal / security | Legal interpretation、organizational Authority生成、security certificationを提供しない |
| Formal Evidence | Leanが検証するのはselected state-transition invariantであり、receiver eligibilityやResponsibility Routing delegation semantics全体ではない |
| Compatibility | Alpha interfaceとmigration behaviorは変更される場合がある |
| MCP Server role | 公開済み`0.1.0a6`はread-only `rpr-mcp`と`rpr.get_route_visibility`を含み、mutating pathway operationは公開しない。 |

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

Expected / actual behavior、reproduction step、sanitized log、environment、RPR version、release/tag identity、artifact digest、adapter、readback source、必要ならroute classification / receiver eligibility、real external effectの有無を記録します。

MCPでは、Transport、Server実装とVersion、Protocol Version、Tool Name、Schema Digest、認証構成、障害時にDispatchを否定できたかも記録します。

各結果は`pass`、`fail`、`blocked`、`not applicable`、`not executed`のいずれかに分類します。Blockedや未実行caseをpassing Evidenceへ変換してはいけません。

## Release promotion gate

Tag、GitHub Release、binary publication、claim promotion、release declarationは、正確なcandidate HEADがsource、unit、component、integration、system/E2E、persistence/restart、package-install、formal-scope、secret/internal-reference、bilingual documentation、manifest/digest、claim/evidence checkを通過し、指定されたhuman approvalを得た後に実施します。

Frozen candidateがvalidation後に変わった場合、旧Evidenceを持ち越さず、`main`からfresh candidateを再構築します。
