<!--
Document Title: RPR MCP Integration Japanese Guide
Document Type: Public Product Guide
Status: Public Alpha and Unreleased Source Preview
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: Japanese
-->

# MCP統合

Responsibility Pathway Runtime（RPR）は、統合ApplicationからMCP Serverへ送るTool Callを、責任経路の中で管理できます。公開済みPublic Alpha `0.1.0a2`では、RPRはMCP Serverの手前に置くClient側の実行・証拠レイヤーとして動きます。

> **公開Releaseの境界:** PyPI `0.1.0a2`はMCP Serverへの呼び出しを統治します。RPR自身のPathway操作をMCP Toolとして公開する機能は含みません。

## `0.1.0a2`で現在できること

公開済みのoutbound MCP経路には、次が実装されています。

- Local subprocessの起動とstdio transport
- MCP JSON-RPC sessionとframing
- Protocol Version、Server Identity、Server Capability、Tool Name、Tool Schemaのbinding
- `tools/call`前のadmission check
- Execution attemptの継続とEvidence保持
- 送信前に確実に失敗した場合と、送信後かもしれない失敗の分離
- 不明なTool Callを`write_status_unknown`として閉じずに保持
- 変更を伴うToolについて、完了前に独立readbackを要求できる構造
- Restart後も未解決Callを黙って再送しないreconciliation経路

## outbound MCP Tool Callを通る責任経路

```text
Host ApplicationまたはAgent
  -> MCP Tool Callの提案
  -> Actor、Authority、Human Gate、Pathway State
  -> 許可されたMCP ServerとToolのbinding
  -> 設定されたTransportでtools/call
  -> Tool Result
  -> 必要な場合は独立readback
  -> completed | write_status_unknown | repair | reconcile | human gate
```

JSON-RPCの成功応答は、MCP Serverが結果を返した証拠です。しかし、それだけで外部の変更が正しく成立した証拠にはなりません。変更を伴うToolでは、統合側が独立かつ権威あるreadback sourceを用意する必要があります。

## 結果が分からないとき

RPRは、次のように扱いを分けます。

| 観測できたこと | RPRでの扱い |
|---|---|
| Callが送信前に拒否されたと確認できる | `dispatch_state: not_sent`を伴う失敗 |
| 送信された可能性があるが、確かな結果がない | `write_status_unknown` |
| Dispatch後かもしれないTransport Error | `write_status_unknown` |
| MCP Serverが明示的なTool Errorを返した | Tool Resultを保持した失敗 |
| 成功応答はあるが、必須readbackを取得できない | `write_status_unknown` |
| 独立readbackで外部作用を確認できた | Readback Evidenceを伴う成功 |

Client Processが再起動した、またはTransportがtimeoutしたという理由だけで、未解決Callを再送してはいけません。

## 未公開の読み取り専用RPR MCP Server Preview

現在のSource Treeには、既存のRPR SQLite Pathway Storeを参照するPhase 1の読み取り専用stdio MCP Serverがあります。このSource Previewは、**公開済みPyPI `0.1.0a2`には含まれておらず**、新しいPackage Releaseとしてもまだ昇格していません。

Editable installしたSourceから起動します。

```bash
python -m pip install -e .
rpr-mcp --database ./rpr.sqlite3
```

Previewが公開するToolは次の5つだけです。

- `rpr.get_status`
- `rpr.list_pathways`
- `rpr.get_pathway`
- `rpr.get_evidence`
- `rpr.list_unresolved`

Serverは既存SQLite Fileを`mode=ro`で開きます。承認、実行、状態遷移、照合、修復、再開を行うMCP Toolは持ちません。Status応答にはDatabaseのFilesystem Pathを含めません。

Local MCP Client設定例:

```json
{
  "command": "rpr-mcp",
  "args": ["--database", "/absolute/path/to/rpr.sqlite3"]
}
```

> **信頼境界:** 読み取り専用でも、情報が非機密になるわけではありません。Pathway Definitionと保持Evidenceには運用情報が含まれる場合があります。Databaseを読むOS権限を既に持つ、信頼されたLocal MCP Clientだけで使ってください。認証、認可、Tenant分離、Redaction Gatewayの代替ではありません。

## 検証済み範囲と未検証範囲

公開済みPublic Alphaの検証は、確認環境内のoutbound Local MCP subprocess / stdio経路、Fault Injection、Restart後の継続、Duplicate Dispatch防止を対象とします。

読み取り専用Server Previewでは、次のTestを追加しています。

- SQLiteをread-onlyで開き、write statementを拒否すること
- MCP initialize、`tools/list`、`tools/call`
- 空、一覧、個別、Evidence、未解決Pathwayの結果
- malformed JSON-RPCと不正Argument
- structured Tool Errorと存在しないPathway ID
- stdoutにJSON-RPC Message以外を出さないこと
- 存在しないDatabaseと非RPR Databaseの拒否

次は環境ごとの評価が必要です。

- Remote MCP TransportとHosted MCP Service
- 企業Proxy、TLS、Identity、Credential構成
- Service固有のTool Semanticsと権威あるreadback source
- 検証済みProfile以外のWindows、macOS、Container、Python環境
- Productionの認証、認可、Tenant分離、Bypass防止、監視、Incident Owner、Deployment適合性

## 統合側が担うこと

RPRは、任意のMCP ServerやClientが信頼できると自動判定しません。統合Applicationと運用者は、次を設計・運用します。

- MCP Peerの選定と認証
- Credential、Database File、環境変数の保護
- Process、Network、Filesystem、Tool Permissionの制限
- outboundのどのToolにHuman Gateを要求するか
- 重要な外部作用を確認する独立readback
- Repair、Reconciliation、Resume、Residual Owner
- RPRを通らない別経路の実行を防ぐこと
- 信頼されていないMCP ClientからPathwayやEvidenceを読ませないこと

## まだ提供していないもの

Source Previewは、変更を伴うRPR操作を公開しません。`rpr.request_human_gate`、`rpr.approve`、`rpr.execute`、`rpr.reconcile`、`rpr.resume`などは将来の設計候補であり、現在の機能ではありません。

関連文書:

- [製品範囲と構成](product-scope-architecture.md)
- [セキュリティ・統合・API境界](security-integration-api.md)
- [検証・Release・既知制約・UAT](verification-release-uat.md)
