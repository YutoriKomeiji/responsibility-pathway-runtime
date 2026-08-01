<!--
Document Title: RPR 製品範囲とarchitecture
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# 製品範囲とarchitecture

## Product role

Responsibility Pathway Runtime（RPR）は、host applicationのdecision logicと重大なexternal actionの間に置かれます。提案actionから、宣言authority、pathway state、execution attempt、独立readback、repairまたはreconciliation、Human Gateへの返却までを再構成可能な経路として保持します。

```text
host application
  -> proposed action + actor + authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | human gate
  -> evidence retained for reconstruction
```

## Frozen alpha capability groups

`RPR-CF-2026-08-01-02`候補には次が含まれます。

- pathway lifecycleとauthorized transition
- persistent pathwayとexecution-attempt continuity
- Human Gate、repair、resume、reconciliation境界
- local-file、allow-listed HTTP、durable outbound-message、MCP subprocess経路
- fail-closedなambiguous-write処理
- freeze rehearsalで試験したcrash/restartとduplicate-dispatch protection
- backup、restore、diagnostics、removal、customer-data retention手順
- reproducible artifactによるwheel/source-distribution install

## Stateとevidenceの原則

- writeを試みたことはcompletionではない。
- completionにはhost integrationが定義したevidence class、通常は独立readbackが必要。
- remote result不明は`write_status_unknown`のまま保持し、successへ書き換えない。
- restartは未解決attemptを保持し、暗黙再送しない。
- repairとreconciliationは隠れたexception handlingではなく明示pathway stateである。
- human approvalはdecision evidenceであり、remote effect発生の証明ではない。

## Adapter boundary

adapterはbounded execution pathを提供しますが、business authorization、credential、network trust、service semantics、十分なreadback定義は所有しません。host integrationは、許可action、承認者、credential isolation、bypass prevention、effectを証明する独立source、曖昧stateの停止・repair・human return条件を定義する必要があります。

## Optional RPE integration

Responsibility Pathway Engineering（RPE）はexternal gate decisionを提供できます。RPRはRPE不在、malformed output、unsupported version、inapplicable resultを可視化し、integration contractに従ってfail closedに扱います。RPEはactionを実行せず、RPRのexecution evidenceを置き換えません。

## Non-claims

RPRはlegal-responsibility engine、policy author、identity provider、secret manager、production gateway、universal transaction coordinator、certification、任意remote systemでのexactly-once guaranteeではありません。このalpha candidateはuniversal production readyとは宣言されていません。
