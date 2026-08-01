<!--
Document Title: RPR 検証・Release・UAT
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# 検証、release note、既知制約、UAT

## Release identity

- Version: `0.1.0a2`
- Channel: public alpha
- Freeze ID: `RPR-CF-2026-08-01-02`
- Canonical product commit: `release-manifest.json`に記録
- Final rehearsal profile: Linux / Python 3.11

## Verified locally executable scope

freeze candidateでは、pathway transition、persistent state、execution-attempt continuity、Human Gate/repair route、local file、allow-listed HTTP、durable outbound-message、MCP subprocess execution、fault injection、restart behavior、backup/restore、diagnostics、removal、package installation、reproducible artifactに関するevidenceを保持しています。

この記述はfreeze evidence setに限定されます。すべてのenvironment、remote system、credential arrangement、framework、operating conditionを実行したという主張ではありません。

## Known limitations and non-claims

- customer environmentは事前検証されていません。
- Windows、macOS、追加Linux distribution、container、別Python profileにはfield evidenceが必要です。
- enterprise proxy、TLS、identity、credential、remote MCPにはintegration固有testが必要です。
- 任意remote systemでexactly-once effectを保証しません。
- legal interpretation、production authorization、security certification、universal deployment fitnessを提供しません。
- alpha interfaceとmigration behaviorはstable release前に変更される場合があります。

## Minimum UAT plan

最初はsyntheticまたはnon-consequential actionを使います。

1. environment、artifact digest、configuration、responsible ownerを記録する。
2. unauthorized transitionがfail closedになることを確認する。
3. required Human Gateを迂回できないことを確認する。
4. independent readback付き成功dispatchを実行する。
5. ambiguous resultを注入またはsimulateし、false completionがないことを確認する。
6. unresolved attemptを持ったままrestartし、duplicate dispatchがないことを確認する。
7. repairまたはreconciliationをdocumented end stateまで実行する。
8. state storeを隔離環境でbackup/restoreする。
9. diagnosticsを実行し、出力にsecretがないことを確認する。
10. packageをremoveし、retained customer dataが宣言policyに従うことを確認する。

## Reporting result

expected/actual behavior、reproduction steps、sanitized log、environment、RPR version、Freeze ID、artifact digest、adapter type、readback source、real external effectの有無を含めます。

結果はpass、fail、blocked、not applicable、not executedのいずれかに分類します。blockedやnot-executedをpassing evidenceへ変換してはいけません。

## Release promotion gate

public repository更新、tag、GitHub Release、binary upload、publicationは、準備exportがsecret、internal file/link、license、manifest、digest、documentation、claim/evidence auditを通過し、明示的human approvalを受けた後だけ実施します。
