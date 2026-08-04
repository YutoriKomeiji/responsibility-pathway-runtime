<!--
Document Title: RPR 検証・Release・UAT
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 検証、release note、既知制約、UAT

## Release identity

| 項目 | 値 |
|---|---|
| Version | `0.1.0a2` |
| Channel | PyPI・GitHub Prereleaseで公開中のPublic Alpha |
| Tag | `v0.1.0a2` |
| Freeze ID | `RPR-CF-2026-08-02-01` |
| Product commit | `release-manifest.json`に記録 |
| Final rehearsal profile | Linux / Python 3.11 |
| License | [`MIT License`](../../LICENSE) |

## Retained evidenceが示す範囲

Frozen evidence setは、pathway transition、persistent state、execution-attempt continuity、Human Gate・repair route、対応adapter path、fault injection、restart、backup/restore、diagnostics、removal、package installation、reproducible artifactを対象とします。

MCPについては、確認環境内のLocal subprocess / stdio経路、JSON-RPC framing、Server / Tool Binding、Fault Injection、結果不明の保持、Restart後の継続、Duplicate Dispatch防止を対象とします。Remote MCPやHosted MCP Service全般の互換性を示すものではありません。

| Evidence statement | 示すこと | 示さないこと |
|---|---|---|
| Testがpassした | 記録された環境・条件で対象caseがpassした | すべての環境・integrationでpassすること |
| Buildがreproducible | 試験したbuild processで一致artifactを生成した | 欠陥や脆弱性が存在しないこと |
| Pathwayがcompletedになった | そのcaseで必要evidenceが一致した | Remote systemが普遍的なexactly-once semanticsを持つこと |
| Local MCP Testがpassした | 記録されたsubprocess / stdio caseが定義済みcheckを満たした | すべてのMCP Server、Transport、Tool、Remote Serviceが互換であること |
| UAT reportがpassした | 報告構成が定義済みcheckを満たした | 一般的な本番適合性、認証、保証 |

Verification documentationは観測結果と試験結果を記録するものです。MIT Licenseを変更せず、warranty、support obligation、certification、legal assuranceを追加しません。

## Known limitations

| 分類 | 現在の境界 |
|---|---|
| Customer environment | 事前検証されていない |
| Platform | Windows、macOS、追加Linux、container、別Python profileにはfield evidenceが必要 |
| MCP | Local subprocess / stdioは検証済み。Remote MCP、Hosted Service、企業Identity、Service固有readbackはintegration固有testが必要 |
| Enterprise integration | Proxy、TLS、identity、credential、remote serviceにはintegration固有testが必要 |
| Remote effect | 任意systemに対するexactly-onceを保証しない |
| Legal / security | Legal interpretation、production authorization、security certificationを提供しない |
| Compatibility | Alpha interfaceとmigration behaviorは変更される場合がある |
| MCP Server role | RPR `0.1.0a2`は、自身のPathway操作をMCP Toolとして公開しない |

## Minimum UAT plan

最初はsyntheticまたはnon-consequential actionを使用します。

| 手順 | Acceptance check |
|---:|---|
| 1 | Environment、artifact digest、configuration、responsible ownerを記録する |
| 2 | Unauthorized transitionがfail closedになる |
| 3 | Required Human Gateを迂回できない |
| 4 | Independent readback付きdispatchが1件完了する |
| 5 | Ambiguous resultがfalse completionにならない |
| 6 | Restart後にunresolved dispatchが重複しない |
| 7 | Repairまたはreconciliationがdocumented end stateへ到達する |
| 8 | State backup/restoreが隔離環境で成功する |
| 9 | Diagnostic outputにsecretが含まれない |
| 10 | Package removal後のdataが宣言policyどおり保持または削除される |

MCP統合では、次も確認します。

| 手順 | MCP Acceptance check |
|---:|---|
| M1 | Dispatch前にProtocol Version、Server Identity、Capability、Tool Name、Tool Schemaがbindingされる |
| M2 | Pre-dispatch rejectionと、送信済みかもしれない結果不明を区別できる |
| M3 | Transport timeoutや不明結果が自動retryではなく`write_status_unknown`になる |
| M4 | 重要なToolではcompletion前に権威ある独立readbackを要求する |
| M5 | Restart後に未解決attemptを復元し、`tools/call`を黙って再送しない |
| M6 | Remote / Hosted MCPの主張を、実際に試験した環境だけへ限定する |

## Reporting result

Expected / actual behavior、reproduction step、sanitized log、environment、RPR version、Freeze ID、artifact digest、adapter、readback source、real external effectの有無を記録します。

MCPでは、Transport、Server実装とVersion、Protocol Version、Tool Name、Schema Digest、認証構成、障害時にDispatchを否定できたかも記録します。

各結果は`pass`、`fail`、`blocked`、`not applicable`、`not executed`のいずれかに分類します。Blockedや未実行caseをpassing evidenceへ変換してはいけません。

## Release promotion gate

Repository visibility変更、tag、GitHub Release、binary publication、release declarationは、準備exportが対象となるsecret、internal reference、license、manifest、digest、documentation、claim/evidence checkを通過し、指定されたhuman approvalを得た後に実施します。
