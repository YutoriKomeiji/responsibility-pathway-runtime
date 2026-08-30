<!--
Document Title: RPR Japanese Product Entrance
Document Type: Public Product Documentation Index
Status: Public Alpha
Version: split-state: GitHub 0.1.0a5 / PyPI 0.1.0a4
Freeze ID: RPR-CF-2026-08-04-04
Header Language: English
Body Language: Japanese
-->

# Responsibility Pathway Runtime 日本語ドキュメント

Responsibility Pathway Runtime（RPR）は、外部操作を伴う処理に、責任経路、実行履歴、外部状態の独立確認、修復、再開、照合、Human Gateを組み込むための、MITライセンスのPythonランタイムです。

現在の配布状態は一時的に分かれています。GitHub Prerelease / sourceは `0.1.0a5`、独立readback済みのPyPI packageは `0.1.0a4` です。PyPI `0.1.0a5` は、実際の公開readbackが取れるまで公開済みとして扱いません。

- [PyPI 0.1.0a4（現在のreadback済みpackage）](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a4/)
- [GitHub Prerelease v0.1.0a5](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a5)
- [日本語製品ページ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/ja.html)
- [実RPRブラウザデモ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html)
- [公開リポジトリ](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

本ソフトウェアは[`MIT License`](../../LICENSE)の条件で提供されます。同ライセンスには無保証および責任制限が含まれます。ただし、RPRの公開上の境界はすべてを永久的な免責事項として扱うのではなく、**evidenceが揃えば昇格できる境界**と、**runtime単体では越えない恒久責任境界**に分けます。詳細は[Claim Boundary Promotion](claim-boundary-promotion.md)を参照してください。

## 最初に読むもの

| 文書 | 内容 |
|---|---|
| [クイックスタート](quick-start.md) | 現在readback済みのPyPI版を導入し、影響のないローカル試験を行う |
| [製品範囲と構成](product-scope-architecture.md) | RPRが提供する機能と製品境界 |
| [Claim Boundary Promotion](claim-boundary-promotion.md) | 現在のevidence boundary、昇格条件、恒久責任境界を確認する |
| [MCP統合](mcp-integration.md) | 現在のMCP Tool Call経路、証拠要件、対応境界を確認する |
| [導入・運用・復旧](install-operations-recovery.md) | 導入、停止、復旧、削除の運用手順 |
| [セキュリティ・統合・API境界](security-integration-api.md) | 信頼境界と統合側の責務 |
| [検証・Release・既知制約・UAT](verification-release-uat.md) | 検証根拠、制約、受入試験 |
| [日本語ドキュメント執筆基準](writing-standard.md) | 日本語本文、製品ページ、デモUIの表記と審査基準 |
| [English product documentation](../en/README.md) | 英語版ドキュメント |

## 現在のMCP対応境界

現在のRPR public lineは、統合ApplicationからMCP Serverへ送るTool Callを責任経路で管理できます。Local subprocess / stdio transport、ServerとToolのbinding、結果不明のfail-closed処理、独立readbackを扱います。

readback済みのPyPI `0.1.0a4` packageには `rpr-mcp` という**local stdio / read-only inspection server**も含まれます。対象protocolはstable `2025-11-25`で、公開toolは `rpr.get_status`、`rpr.list_pathways`、`rpr.get_pathway`、`rpr.get_evidence`、`rpr.list_unresolved` に限定されます。Approval、execution、transition、reconciliation、repair、resumeなどのmutating toolは提供しません。Remote MCP transportも現時点ではclaimしません。

GitHub `v0.1.0a5` はこれらの境界を維持したうえで、Windows実機で再現したUTF-8 BOM入力互換性修正を追加しています。ただし、その修正をPyPI `0.1.0a5` の配布結果として扱うのはPyPI公開readback後です。

## 製品と統合の役割分担

| RPRが提供するもの | 統合Application・運用者が提供するもの |
|---|---|
| Pathway stateと許可された遷移 | 認証とDomain固有の認可 |
| Execution attemptの継続性 | Credential隔離とNetwork制御 |
| Evidence保持とreadback workflow | 独立かつ権威あるreadback source |
| Human Gate、repair、resume、reconciliation | 承認規則、Bypass防止、運用責任者 |
| 試験済みadapterと障害state処理 | Deployment判断、監視、最終的な外部行為 |

現在の公開evidenceは、すべてのcustomer environmentを代表するものではありません。Windows field evidenceは再現されたBOM-bearing input pathの範囲に限られます。Proxy、TLS、企業Identity、Credential Store、Remote MCP、Framework統合、long-duration operation、production supervisorなどは、主張対象profileごとの再現可能な検証が必要です。

Field Testの結果は、報告された構成についてのEvidenceです。一般的な本番適合性、安全性、法令適合、認証、任意の遠隔Systemに対するexactly-once保証を意味しません。これらのうちevidence依存の境界は、[Claim Boundary Promotion](claim-boundary-promotion.md)に記載した条件を満たしreviewされた場合にのみ前進します。

## 問い合わせ先

| 内容 | 経路 |
|---|---|
| 製品・統合に関する質問 | [`SUPPORT.md`](../../SUPPORT.md) |
| Security報告 | [`SECURITY.md`](../../SECURITY.md) |
| Contribution | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| License条件 | [`LICENSE`](../../LICENSE) |
