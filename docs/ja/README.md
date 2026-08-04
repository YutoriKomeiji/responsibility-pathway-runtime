<!--
Document Title: RPR Japanese Product Entrance
Document Type: Public Product Documentation Index
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: Japanese
-->

# Responsibility Pathway Runtime 日本語ドキュメント

Responsibility Pathway Runtime（RPR）は、外部操作を伴う処理に、責任経路、実行履歴、外部状態の独立確認、修復、再開、照合、Human Gateを組み込むための、MITライセンスのPythonランタイムです。

Public Alpha `0.1.0a2` は、PyPIとGitHub Prereleaseで公開しています。公開リポジトリ、製品ページ、ブラウザ内で実際のRPRを動かすデモも利用できます。

- [PyPIパッケージ](https://pypi.org/project/responsibility-pathway-runtime/)
- [GitHub Prerelease](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a2)
- [日本語製品ページ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/ja.html)
- [実RPRブラウザデモ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html)
- [公開リポジトリ](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

本ソフトウェアは[`MIT License`](../../LICENSE)の条件で提供されます。同ライセンスには無保証および責任制限が含まれます。この文書は、確認済みの挙動と統合時の役割分担を説明するものであり、保証、認証、適合証明、運用代行、特定用途への適合約束を追加するものではありません。

## 最初に読むもの

| 文書 | 内容 |
|---|---|
| [クイックスタート](quick-start.md) | PyPIから導入し、影響のないローカル試験を行う |
| [製品範囲と構成](product-scope-architecture.md) | RPRが提供する機能と製品境界 |
| [MCP統合](mcp-integration.md) | 現在のMCP Tool Call経路、証拠要件、対応境界を確認する |
| [導入・運用・復旧](install-operations-recovery.md) | 導入、停止、復旧、削除の運用手順 |
| [セキュリティ・統合・API境界](security-integration-api.md) | 信頼境界と統合側の責務 |
| [検証・Release・既知制約・UAT](verification-release-uat.md) | 検証根拠、制約、受入試験 |
| [日本語ドキュメント執筆基準](writing-standard.md) | 日本語本文、製品ページ、デモUIの表記と審査基準 |
| [English product documentation](../en/README.md) | 英語版ドキュメント |

## 現在のMCP対応境界

RPR `0.1.0a2`は、統合ApplicationからMCP Serverへ送るTool Callを責任経路で管理できます。Local subprocess / stdio transport、ServerとToolのbinding、結果不明のfail-closed処理、独立readbackを扱います。ただし、RPR自身のPathway操作をMCP Toolとして公開する「RPR MCP Server」は、まだ提供していません。

## 製品と統合の役割分担

| RPRが提供するもの | 統合Application・運用者が提供するもの |
|---|---|
| Pathway stateと許可された遷移 | 認証とDomain固有の認可 |
| Execution attemptの継続性 | Credential隔離とNetwork制御 |
| Evidence保持とreadback workflow | 独立かつ権威あるreadback source |
| Human Gate、repair、resume、reconciliation | 承認規則、Bypass防止、運用責任者 |
| 試験済みadapterと障害state処理 | Deployment判断、監視、最終的な外部行為 |

最終リハーサルはLinux / Python 3.11で実施されています。他のOS、Python環境、Proxy、TLS、企業Identity、Credential Store、Remote MCP、Framework統合には、その環境固有の試験が必要です。

Field Testの結果は、報告された構成についてのEvidenceです。一般的な本番適合性、安全性、法令適合、認証、任意の遠隔Systemに対するexactly-once保証を意味しません。

## 問い合わせ先

| 内容 | 経路 |
|---|---|
| 製品・統合に関する質問 | [`SUPPORT.md`](../../SUPPORT.md) |
| Security報告 | [`SECURITY.md`](../../SECURITY.md) |
| Contribution | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| License条件 | [`LICENSE`](../../LICENSE) |
