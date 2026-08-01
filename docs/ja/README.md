<!--
Document Title: RPR Japanese Product Entrance
Document Type: Public Product Documentation Index
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: Japanese
-->

# Responsibility Pathway Runtime 日本語入口

Responsibility Pathway Runtime（RPR）は、外部作用を伴う処理の前後に、責任経路・実行試行・独立readback・修復・再開・照合・Human Gateを保持するためのPythonランタイムです。

> **Public Alpha — 0.1.0a2**  
> Freeze ID: `RPR-CF-2026-08-01-02`  
> 最終リハーサル環境: Linux / Python 3.11

RPRは、法的責任を自動判定するエンジン、認証基盤、Secret Manager、万能な本番Gateway、任意の遠隔システムに対するexactly-once保証ではありません。また、現時点であらゆる顧客環境に対する本番準備完了を主張しません。

## 最初に読むもの

- [English product documentation](../en/README.md)
- [Quick Start](../en/quick-start.md)
- [製品範囲と構成](../en/product-scope-architecture.md)
- [導入・運用・復旧](../en/install-operations-recovery.md)
- [セキュリティ・統合・API境界](../en/security-integration-api.md)
- [検証・Release・既知制約・UAT](../en/verification-release-uat.md)

英語文書が現行のPrimary Product Documentationです。この日本語入口は、マスターおよび日本語利用者が判断できるよう、製品位置づけ・非主張・利用経路を示します。

## 検証済み範囲

凍結候補では、pathway lifecycle、永続state、execution attempt、Human Gate、repair・resume・reconciliation、local file、allow-listed HTTP、durable outbound message、MCP subprocess、曖昧writeのfail-closed処理、restart、backup/restore、diagnostics、removal、配布物のclean installおよび再現可能buildが、ローカルで実行可能な範囲として検証されています。

この検証は、未実行のOS、Python環境、Proxy、TLS、企業Identity、Credential、Remote MCP、個別Service、Framework統合へ自動的には拡張されません。

## 利用者へお願いするField Test

公開後は、次の再現可能な結果をGitHub Issuesで募集します。

- Windows、macOS、追加Linux、Container、別Python環境
- Proxy、TLS、企業Identity、Credential連携
- Remote MCP、個別Service、Framework、Agent、RPA、Batch統合
- Install、Upgrade、運用、Backup/Restore、Removal
- 不具合、分かりにくい状態、文書不足、未対応前提

報告された結果は、その環境に関するField Evidenceです。普遍的な本番準備完了や安全性を意味しません。

## 責任境界

認証、Credential隔離、Network制御、Domain固有の認可、Bypass防止、独立readback、Deployment承認、最終的な外部行為は、統合するApplicationとHuman Authorityが担います。

脆弱性の可能性がある内容は公開Issueへ投稿せず、[`SECURITY.md`](../../SECURITY.md)の非公開経路を使用してください。
