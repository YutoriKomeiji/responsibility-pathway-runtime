<!--
Document Title: RPR MCP Integration Japanese Guide
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: Japanese
-->

# MCP統合

Responsibility Pathway Runtime（RPR）は、統合ApplicationからMCP Serverへ送るTool Callを責任経路の中で管理できます。公開済みPublic Alpha `0.1.0a6`には、local read-only `rpr-mcp` inspection serverとread-only Responsibility Routing visibilityが含まれます。

> **公開Releaseの境界:** PyPI `0.1.0a6`はoutbound MCP Callを統治し、local read-only RPR MCP inspection serverと`rpr.get_route_visibility`を含みます。変更系RPR MCP Toolは含みません。

## 公開済み`0.1.0a6`でできること

公開済みのoutbound MCP経路には次が実装されています。

- Local subprocessの起動とstdio transport
- MCP JSON-RPC sessionとframing
- Protocol Version、Server Identity、Server Capability、Tool Name、Tool Schemaのbinding
- `tools/call`前のadmission check
- Execution attemptの継続とEvidence保持
- 送信前に確実に失敗した場合と、送信後かもしれない失敗の分離
- 不明なTool Callを`write_status_unknown`として保持
- 変更を伴うToolについて、完了前に独立readbackを要求できる構造
- Restart後も未解決Callを黙って再送しないreconciliation経路
- `authority_inferred: false`を伴うread-only Responsibility Routing visibility

公開済み`rpr-mcp`のread-only toolは次です。

- `rpr.get_status`
- `rpr.list_pathways`
- `rpr.get_pathway`
- `rpr.get_route_visibility`
- `rpr.get_evidence`
- `rpr.list_unresolved`

## outbound MCP Tool Callを通る責任経路

```text
Host ApplicationまたはAgent
  -> MCP Tool Callの提案
  -> Actor、declared Authority、Pathway State、Responsibility Routing
  -> 許可されたMCP ServerとToolのbinding
  -> 設定されたTransportでtools/call
  -> Tool Result
  -> 必要な場合は独立readback
  -> completed | write_status_unknown | repair | reconcile | bounded human gate | hold
```

JSON-RPCの成功応答は、MCP Serverが結果を返したEvidenceです。しかし、それだけで外部の変更が正しく成立したEvidenceにはなりません。変更を伴うToolでは、統合側が独立かつ権威あるreadback sourceを用意する必要があります。

## 結果が分からないとき

RPRは次のように扱いを分けます。

| 観測できたこと | RPRでの扱い |
|---|---|
| Callが送信前に拒否されたと確認できる | `dispatch_state: not_sent`を伴う失敗 |
| 送信された可能性があるが、確かな結果がない | `write_status_unknown` |
| Dispatch後かもしれないTransport Error | `write_status_unknown` |
| MCP Serverが明示的なTool Errorを返した | Tool Resultを保持した失敗 |
| 成功応答はあるが、必須readbackを取得できない | `write_status_unknown` |
| 独立readbackで外部作用を確認できた | Readback Evidenceを伴う成功 |

Client Processが再起動した、またはTransportがtimeoutしたという理由だけで、未解決Callを再送してはいけません。また、結果が不明というだけで自動的にHuman Gateへ変換してはいけません。Responsibility Routingは、reconciliation holdや、明示的にeligibleかつauthorizedな別routeへ未解決effectを保持できます。

## Responsibility Routing visibility

公開済み`0.1.0a6`には次のread-only toolが含まれます。

- `rpr.get_route_visibility`

`rpr.get_route_visibility(pathway_id)`は、current state、限定的なcompatibility route、保存済みdeclared route、Human Return point、Residual Owner、`authority_inferred: false`を返します。

このToolはreceiverを選択せず、Authorityを付与せず、承認・実行・reconciliation・resume・state mutationも行いません。Receiver capability、Evidence transfer、successful transport、route selectionはAuthorityを生成しません。

## Read-only serverの起動

```bash
python -m pip install responsibility-pathway-runtime==0.1.0a6
rpr-mcp --database ./rpr.sqlite3
```

未公開repository sourceを試す場合:

```bash
python -m pip install -e .
rpr-mcp --database ./rpr.sqlite3
```

Serverは既存SQLite Fileを`mode=ro`で開きます。承認、実行、状態遷移、reconciliation、修復、再開、Authority grantを行うMCP Toolは持ちません。Status応答にはDatabaseのFilesystem Pathを含めません。

Local MCP Client設定例:

```json
{
  "command": "rpr-mcp",
  "args": ["--database", "/absolute/path/to/rpr.sqlite3"]
}
```

> **信頼境界:** Read-onlyでも情報が非機密になるわけではありません。Pathway Definition、Route Metadata、保持Evidenceには運用情報が含まれる場合があります。Databaseを読むOS権限を既に持つ、信頼されたLocal MCP Clientだけで使ってください。認証、認可、Tenant分離、Redaction Gatewayの代替ではありません。

## 検証済み範囲と未検証範囲

公開済みPublic Alphaの検証は、確認環境内のoutbound Local MCP subprocess / stdio経路、read-only MCP inspection、Responsibility Routing visibility、Fault Injection、Restart後の継続、Duplicate Dispatch防止を対象とします。

Route visibilityのEvidenceには次が含まれます。

- Responsibility Routing inspectionがstateを変更しないこと
- persisted declared routeのreadback
- narrow state-to-route compatibility mapping
- `authority_inferred: false`
- invalid receiverとAuthority non-propagation
- malformed requestとmissing pathway ID

次は環境ごとの評価が必要です。

- Remote MCP TransportとHosted MCP Service
- 企業Proxy、TLS、Identity、Credential構成
- Service固有のTool Semanticsと権威あるreadback source
- 検証済みProfile以外のWindows、macOS、Container、Python環境
- Productionの認証、認可、Tenant分離、Bypass防止、監視、Incident Owner、Deployment適合性

## 統合側が担うこと

RPRは、任意のMCP Server、Client、route receiverが信頼できる／authorizedであると自動判定しません。統合Applicationと運用者は次を設計・運用します。

- MCP Peerの選定と認証
- receiver eligibilityとdelegation source-of-truth
- Credential、Database File、環境変数の保護
- Process、Network、Filesystem、Tool Permissionの制限
- outboundのどのToolにbounded Human Gateを要求するか
- 重要な外部作用を確認する独立readback
- Repair、Reconciliation、Resume、Residual Owner
- RPRを通らない別経路の実行を防ぐこと
- 信頼されていないMCP ClientからPathway、Route、Evidenceを読ませないこと

## MCP mutationとしてまだ提供していないもの

公開済み`0.1.0a6`は、変更を伴うRPR MCP操作を公開しません。`rpr.request_human_gate`、`rpr.approve`、`rpr.execute`、`rpr.reconcile`、`rpr.resume`などは現在のcapabilityではありません。

関連文書:

- [製品範囲と構成](product-scope-architecture.md)
- [Responsibility Routing migration](responsibility-routing-migration.md)
- [セキュリティ・統合・API境界](security-integration-api.md)
- [検証・Release・既知制約・UAT](verification-release-uat.md)
