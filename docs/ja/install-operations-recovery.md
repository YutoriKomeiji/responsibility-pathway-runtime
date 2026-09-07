<!--
Document Title: RPR 導入・運用・復旧
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# 導入・運用・復旧

この文書は、公開済み`0.1.0a6`と現行repository source境界における推奨integration / operation手順を示します。Hosted service、managed operation、support SLA、保証を提供するものではありません。RPRは[`MIT License`](../../LICENSE)に基づいて提供されます。

## Deployment baseline

| 分類 | Integration側で決定・保存するもの |
|---|---|
| Artifact | 検証済みwheelまたはsource distribution、digest、入手元 |
| Runtime | Python version、dependency解決結果、隔離環境 |
| Persistence | State store、access control、backup、retention |
| Authority | 許可action、authorized actor、delegation source-of-truth、configured bounded Human Gate owner |
| Responsibility Routing | receiver eligibility、route scope、unresolved payload、allowed next actions、closure/reevaluation condition、Residual Owner |
| Execution | Adapter allow-list、timeout、cancellation、retry policy |
| Credential | 外部Secret sourceとleast-privilege scope |
| Evidence | 独立readback sourceとmatching rule |
| Recovery | Repair、reconciliation、resume、incident owner |

Secretをrepository file、example、log、pathway record、diagnostic bundle、Issueへ含めないでください。

## Operating sequence

| 順序 | Operation | 完了条件 |
|---:|---|---|
| 1 | Proposed action、actor、declared Authority、route eligibility、設定を検証 | 必須宣言が揃っている |
| 2 | Pathwayを登録またはload | Persistent stateを利用できる |
| 3 | Requested transitionとrouteを確認 | Current state、actor、receiver条件が許可されている |
| 4 | Durable execution attemptを作成 | Dispatch前にattempt identityが保存される |
| 5 | Bounded adapterからdispatch | Dispatch Evidenceが保持される |
| 6 | Independent readbackを取得 | External sourceをqueryする |
| 7 | Evidenceをreconcile | Required Evidenceと一致するか、未解決effectを保持する |
| 8 | Complete、repair、resume、hold、reconcile、または明示的configured bounded Human Gateへ進む | StateとResponsibility Routeが整合している |

## Restartとambiguous write

| 状況 | 必要な処理 |
|---|---|
| Process restart | New dispatch前にpathwayとattemptをloadする |
| Unresolved attempt | 暗黙に再dispatchしない |
| Write済みの可能性があるが結果不明 | `write_status_unknown`を保持する |
| Readback可能 | Stable operation identityでqueryしprovenanceを保持する |
| Readback不可または不確定 | reconciliation hold、または明示的にeligibleかつauthorizedなResponsibility Routeへ保持する |
| Receiver eligibilityまたはAuthority不明 | Holdする。Human receiverを推測しない |

Retryをreconciliationの代替にしてはいけません。`Fail closed`は`Human Gate`と同義ではありません。

Evidence transfer、receiver capability、successful transport、recovered state、route selectionはAuthorityを生成しません。

## Backupとrestore

Persistent stateと関連Evidenceを整合性が保たれる方法でbackupします。隔離環境へrestoreして試験し、diagnostics、route-relevant material stateの再確認、未解決attemptのreconciliationを行ってからexternal actionを再開します。Stateのrestoreだけでapprovalやresume Authorityが復元されたとは扱いません。

## Removalとretained data

Python packageのuninstallとpathway dataの削除は別のoperationです。

| 対象 | Removal前の記録 |
|---|---|
| Package | Install済みversionとuninstall結果 |
| State | Storeとbackup location |
| Retention | Owner、期間、export format |
| Deletion | Approver、method、verification Evidence |

## Operational stop conditions

Configuration、Authority、receiver eligibility、credential、persistence、readback、restore integrity、stable operation identity、Residual Ownerを確立できない場合はexternal executionを停止します。利用環境でRPRを採用・継続利用する判断は、統合する組織と運用者が行います。
