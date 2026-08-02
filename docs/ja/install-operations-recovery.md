<!--
Document Title: RPR 導入・運用・復旧
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# 導入・運用・復旧

この文書は推奨される統合・運用手順を示します。Hosted service、managed operation、support SLA、保証を提供するものではありません。RPRは[`MIT License`](../../LICENSE)に基づいて提供されます。

## Deployment baseline

| 分類 | Integration側で決定・保存するもの |
|---|---|
| Artifact | 検証済みwheelまたはsource distribution、digest、入手元 |
| Runtime | Python version、dependency解決結果、隔離環境 |
| Persistence | State store、access control、backup、retention |
| Authority | 許可action、authorized actor、Human Gate owner |
| Execution | Adapter allow-list、timeout、cancellation、retry policy |
| Credential | 外部Secret sourceとleast-privilege scope |
| Evidence | 独立readback sourceとmatching rule |
| Recovery | Repair、reconciliation、resume、incident owner |

Secretをrepository file、example、log、pathway record、diagnostic bundle、Issueへ含めないでください。

## Operating sequence

| 順序 | Operation | 完了条件 |
|---:|---|---|
| 1 | Proposed action、actor、authority、設定を検証 | 必須宣言が揃っている |
| 2 | Pathwayを登録またはload | Persistent stateを利用できる |
| 3 | Requested transitionを確認 | Current stateとactorが許可されている |
| 4 | Durable execution attemptを作成 | Dispatch前にattempt identityが保存される |
| 5 | Bounded adapterからdispatch | Dispatch evidenceが保持される |
| 6 | Independent readbackを取得 | External sourceをqueryする |
| 7 | Evidenceを照合 | Expected effectと一致する |
| 8 | Completeまたは停止 | Completed、repair、resume、reconciliation、Human Gateへ進む |

## Restartとambiguous write

| 状況 | 必要な処理 |
|---|---|
| Process restart | New dispatch前にpathwayとattemptをloadする |
| Unresolved attempt | 暗黙に再dispatchしない |
| Write済みの可能性があるが結果不明 | `write_status_unknown`を保持する |
| Readback可能 | Stable operation identityでqueryしprovenanceを保持する |
| Readback不可または不確定 | 停止してreconciliationまたはHuman Gateへ返す |

Retryをreconciliationの代替にしてはいけません。

## Backupとrestore

Persistent stateと関連evidenceを整合性が保たれる方法でbackupします。隔離環境へrestoreして試験し、diagnosticsと未解決attemptのreconciliationを行ってからexternal actionを再開します。

## Removalとretained data

Python packageのuninstallとpathway dataの削除は別のoperationです。

| 対象 | Removal前の記録 |
|---|---|
| Package | Install済みversionとuninstall結果 |
| State | Storeとbackup location |
| Retention | Owner、期間、export format |
| Deletion | Approver、method、verification evidence |

## Operational stop conditions

Configuration、authority、credential、persistence、readback、restore integrity、stable operation identityを確立できない場合はexternal executionを停止します。利用環境でRPRを採用・継続利用する判断は、統合する組織と運用者が行います。
