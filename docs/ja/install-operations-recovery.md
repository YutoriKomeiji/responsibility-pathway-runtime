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

## Install

manifestと一致するwheelまたはsource distributionだけを隔離環境へinstallしてください。artifact、digest、Python version、dependency解決結果、install logをdeployment evidenceとして保存します。

## Configuration baseline

adapterを有効化する前に、state store、許可action、endpoint allow-list、subprocess command allow-list、timeout、retry policy、credential source、readback source、backup先、retention policy、責任を持つhuman ownerを記録します。

secretをrepository file、example、log、pathway record、Issueへ含めてはいけません。

## Operating sequence

1. 提案action、actor、authority、integration設定を検証する。
2. pathwayを登録またはloadする。
3. 現stateが要求transitionを許すことを確認する。
4. dispatch前にdurable execution attemptを1件作る。
5. bounded adapterからdispatchする。
6. 独立readbackを取得する。
7. 必要evidenceが一致した場合だけcompletedにする。
8. 一致しない場合は未解決stateを保持し、repair、resume、reconciliation、Human Gateへ進む。

## Restart

restart時は新規dispatchを許す前にpersistent pathwayとattemptをloadします。未解決attemptを暗黙に再送してはいけません。operation identity、dispatch evidence、最後のstate、readback result、必要な次判断を再構成します。

## Backupとrestore

persistent stateと関連evidenceを整合性が保たれる方法でbackupします。隔離先へrestoreして試験し、その後diagnosticsと未解決attemptのreconciliationを実施してからexternal actionを再開します。

## Ambiguous write recovery

adapterがwriteした可能性はあるが結果を確定できない場合：

- `write_status_unknown`を維持する。
- automatic redispatchを無効にする。
- stable operation identityで独立sourceをqueryする。
- resultとprovenanceをevidenceへ付ける。
- completed、failed、repair-required、Human Gateのいずれかへreconcileする。
- 判断とevidence trailを保持する。

## Removalとcustomer data

Python packageのuninstallでcustomer pathway dataを暗黙削除してはいけません。state store、backup location、retention owner、export format、削除承認、検証方法をpackage removalとは別に記録します。

## Operational stop conditions

configuration、authority、credential、persistence、readback、restore integrity、operation identityを確立できない場合はexternal executionを停止します。retryをreconciliationの代替にしないでください。
