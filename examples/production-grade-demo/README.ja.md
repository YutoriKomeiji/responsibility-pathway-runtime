# 本番級デモ：統治された仕入先支払実行

> Responsibility Pathway Runtime `0.1.0a2` Public Alpha向けシナリオ。
>
> これは玩具的なカウンター、承認ボタンだけのモック、成功だけを見せる疑似デモではありません。凍結候補に含まれる実RPR runtime interfaceを使い、永続状態、Human Gateへの帰還、外部writeの曖昧性、独立readback、再起動継続、修復、reconciliationを検証する実行可能な統合シナリオです。

## 業務シナリオ

財務自動化serviceが承認済みの仕入先請求書を受け取り、allow-listされた支払APIへ支払指図を提案します。支払は重大な外部作用であり、callerがtimeoutしたという理由だけで再実行してはなりません。

Host applicationは、次を保持します。

- 提案されたactionと宣言されたauthority
- operationと各execution attemptのidentity
- dispatchを許可したHuman Gate decision
- 外部requestと限定されたresponse evidence
- 支払状態endpointからの独立readback
- write結果が曖昧な場合の明示的な未解決状態
- 重複dispatchを起こさないrestart-safe recovery
- reconciliation、repair、resume、residual ownership

## 本番級デモと呼べる理由

このシナリオは、凍結候補のtestで扱われる同じ製品経路を使用します。

- 永続的pathway storeとexecution-attempt store
- 認可されたruntime transition
- allow-listされたHTTP execution
- idempotency identityとduplicate-dispatch prevention
- `write_status_unknown`によるfail-closed処理
- completion前の独立readback
- Human Gateへの帰還とresume
- 未解決execution中のprocess restart
- reconciliationと明示的repair decision
- operational diagnosticsと保持されたevidence

外部支払serviceは、実金融systemへ接続せずに、通常完了、remote rejection、受付後timeout、readback unavailable、restart条件を再現する決定論的local integration fixtureです。Fixtureは統合test doubleですが、RPR runtime、persistence、state transition、executor path、diagnostics、recovery behaviorは実製品codeを使用します。

## 役割と責任境界

| Role | Responsibility |
|---|---|
| Host finance application | 認証、請求書の妥当性、credential、network policy、支払domain authorization、bypass防止 |
| Human approver | 最終的な支払認可と例外的reconciliation decision |
| RPR | Pathway state、execution-attempt continuity、evidence retention、stop／repair／resume boundary |
| Payment API fixture | 再現可能な統合testのための決定論的external effectとreadback behavior |
| Operator | 環境設定、backup、diagnostics、incident handling、保持されたcustomer data |

RPRは、請求書が法的に支払可能かを判断せず、承認者を認証せず、credentialを保護せず、任意のremote systemに対する普遍的exactly-once behaviorを保証しません。

## デモ経路

### Path A — 認可された完了

1. 支払pathwayを登録する。
2. Dispatch前にHuman Gateへ戻す。
3. 明示的なapprovalを記録する。
4. 安定したidempotency identityで一度だけdispatchする。
5. 支払状態を独立にreadbackする。
6. Readbackが意図した支払を確認した後にのみcompleteとする。
7. 保持されたpathway、attempt、authority、evidence recordを出力する。

期待結果：readback evidenceを持つcompleted pathwayと、1回だけのexternal dispatch。

### Path B — Remote受付後のtimeout

1. Fixtureが支払を受け付け、external effectを永続化する。
2. RPRが確定responseを受け取る前にconnectionが失敗する。
3. RPRは成功または安全なretryではなく、`write_status_unknown`を記録する。
4. Processを終了し、再起動する。
5. RPRが未解決attemptを復元し、blind redispatchを防ぐ。
6. Reconciliationが独立status endpointを照会する。
7. Operatorがreconciliation outcomeを記録し、明示的authority decisionの下でresumeまたはrepairする。

期待結果：支払重複なし、曖昧性の可視化、attempt continuityの保持、明示的resolution evidence。

### Path C — Readback unavailable

1. Dispatchがaccepted responseを受け取る。
2. 独立readbackが利用できない。
3. Completionをblockしたままにする。
4. Diagnosticsが未解決pathwayと必要なoperator actionを表示する。
5. 後のreadbackまたは承認済みrepair routeで状態を解決する。

期待結果：acceptedをverified completionとして扱わない。

### Path D — Human rejection

1. 提案された支払を登録する。
2. Human Gateへ戻す。
3. 理由とauthority identityを伴うrejectionを記録する。
4. External dispatchが発生していないことを確認する。

期待結果：external effectが0件のterminatedまたはheld pathway。

## 必須デモpackage

公開repository exportには次を含めます。

```text
examples/production-grade-demo/
├── README.md
├── README.ja.md
├── payment_service.py
├── run_demo.py
├── scenarios/
│   ├── authorized-completion.json
│   ├── timeout-after-acceptance.json
│   ├── readback-unavailable.json
│   └── human-rejection.json
├── expected/
│   ├── authorized-completion.json
│   ├── timeout-after-acceptance.json
│   ├── readback-unavailable.json
│   └── human-rejection.json
└── tests/
    └── test_demo_scenarios.py
```

Scriptは出荷されたRPR packageを呼び出し、デモ内部でpathway state machineを再実装してはなりません。

## 受入基準

次のすべてがclean environmentで通過した場合にのみ、デモをrelease eligibleとします。

- RPP source treeではなく凍結wheelからinstallする
- localhost以外へのnetwork accessなしで動作する
- 明示的state directoryがない限りtemporary directoryを使う
- 決定論的なmachine-readable resultを生成する
- timeout-after-acceptance scenarioでdispatchが1回だけであることを証明する
- 実subprocess restartを通過する
- product diagnostics経路で未解決workを表示する
- 実credential、endpoint、personal data、internal repository linkを含まない
- retained stateとevidenceをexpected outputと比較するautomated testを持つ
- product behaviorと決定論的external fixtureを明確に区別する

## 品質と主張境界

このデモの通過は、試験環境における宣言済みscenarioだけを検証します。実支払systemのproduction readiness、金融規制適合、credential security、普遍的exactly-once delivery、特定組織への適合性を立証しません。

実配備では、認証されたauthorization source、credential isolation、network control、独立external readback、operational ownership、incident procedureを別途用意する必要があります。
