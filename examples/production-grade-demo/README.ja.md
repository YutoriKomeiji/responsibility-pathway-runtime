# 本番級デモ：統治された仕入先支払実行

> 現行RPR repository source向けの実行可能integration scenarioです。公開package baselineは`0.1.0a6`で、Responsibility Routingとread-only route visibilityはこの公開済みPublic Alphaに含まれます。Repository sourceには、後続のexact-head release promotionまでは公開packageに含まれない追加workが存在する場合があります。
>
> 成功だけを見せるsimulated walkthroughではありません。実RPR interfaceを使い、persistent state、configured Human Gate approval、external write ambiguity、independent readback、durable SQLite state上でのruntime recreation、reconciliation、duplicate-dispatch preventionを確認します。Payment providerだけは決定論的local integration fixtureです。

## Business scenario

Finance automation serviceが承認済みsupplier invoiceを受け取り、allow-listされたpayment APIへpayment instructionを提案します。Paymentは重大なexternal effectであり、callerがtimeoutしたという理由だけで繰り返してはいけません。

Host applicationは次を保持します。

- proposed actionとdeclared Authority
- operationと各execution attemptのidentity
- dispatchを許可するconfigured bounded Human Gate decision
- external requestとbounded response Evidence
- payment-status endpointからのindependent readback
- write結果が曖昧な場合の明示的unresolved state
- duplicate dispatchを起こさないrestart/recreation-safe recovery
- reconciliation、repair/resume boundary、Residual Owner

`Fail closed`は`send to a human`と同義ではありません。現行Responsibility Routingでは、unresolved effectをreconciliation holdへ保持できます。Human Returnはhuman-held Authorityが実際に必要な場合のbounded routeです。

## このデモが実際に実行するもの

現行demoは次を使用します。

- `ResponsibilityPathwayRuntime`
- persistent SQLite pathway / execution-attempt store
- authorized runtime transition
- allow-listed HTTP execution
- idempotency identityとduplicate-dispatch prevention
- `write_status_unknown` fail-closed handling
- completion前のindependent readback
- configured Human Gate approval
- 同じdurable store上での新しいruntime object再構築
- runtime-integrated reconciliation
- Evidence chain verification

External payment serviceはdeterministic localhost fixtureで置き換え、実financial systemへ接続せずauthorized completion、accept後timeout、readback unavailable、human rejectionを再現します。Fixtureはtest doubleですが、RPR runtime、persistence、transition、executor path、reconciliationはproduct codeです。

このcommand-line demo単体は、**OS process kill/restart boundaryを証明しません**。Process-level interruption/restart behaviorはrepository内の別test matrixで扱い、このdemoではdurable SQLite stateに対してruntime/store objectを再構築します。Runtime recreationをsubprocess restartと表現してはいけません。

## RoleとResponsibility boundary

| Role | Responsibility |
|---|---|
| Host finance application | Authentication、invoice validity、credential、network policy、payment-domain authorization、bypass prevention、receiver eligibility/delegation source-of-truth |
| Human approver | configured bounded Human Gateがhuman-held Authorityを必要とする場合のpayment authorization |
| RPR | Pathway state、execution-attempt continuity、Evidence retention、reconciliation/repair/resume boundary、configured route metadata |
| Payment API fixture | 再現可能なintegration test向けdeterministic external effect / readback behavior |
| Operator | Environment configuration、backup、diagnostics、incident handling、retained customer data |

RPRはinvoiceが法的に支払可能かを決めず、approverを認証せず、organizational Authorityを生成せず、任意remote systemに対するexactly-onceを保証しません。Evidence transferやreceiver capabilityもAuthorityを生成しません。

## Demonstration paths

### Path A — Authorized completion

1. Payment pathwayをregisterする。
2. Dispatch前のconfigured Human Gateへ入る。
3. Explicit approvalを記録する。
4. Stable idempotency identityで一度だけdispatchする。
5. Payment statusをindependentにreadbackする。
6. Readbackがintended paymentを確認した後だけcompleteする。

Expected result: verified readback付きcompleted pathway、external dispatchは1回。

### Path B — Remote acceptance後timeout

1. Fixtureがpaymentをacceptしexternal effectを記録する。
2. RPRがconclusive responseを受け取る前にconnectionが失敗する。
3. RPRはsuccessやsafe retryではなく`write_status_unknown`を記録する。
4. 同じSQLite store上で新しいruntimeを構築する。
5. Re-executionはredispatchせずpersisted unresolved attemptを返す。
6. Reconciliationがindependent status endpointをqueryする。
7. Verified observationが2回目のpayment dispatchなしでpathwayを閉じる。

Expected result: dispatch 1回、ambiguity可視、durable attempt continuity、明示的reconciliation Evidence。

### Path C — Readback unavailable

1. Dispatchがaccepted responseを受ける。
2. Independent readbackが利用できない。
3. Completionは`write_status_unknown`のままblockされる。
4. Runtime recreationでもblind redispatchしない。
5. 十分なEvidenceが得られるまでreconciliationはunresolvedのまま残る。

Expected result: acceptedをverified completionとして扱わない。

### Path D — Human rejection

1. Proposed paymentをregisterする。
2. Configured Human Gateへ入る。
3. ReasonとAuthority identityを伴うrejectionを記録する。
4. External dispatchが発生していないことを確認する。

Expected result: denied pathway、external effect 0件。

## 実際のrepository内容

現行public repositoryには次があります。

```text
examples/production-grade-demo/
├── README.md
├── README.ja.md
├── payment_service.py
├── run_demo.py
└── tests/
    └── test_demo_scenarios.py
```

現行実装に別個の`scenarios/`や`expected/`directoryはありません。Scenario selectionとassertionは`run_demo.py`と`tests/test_demo_scenarios.py`に実装されています。Documentationが存在しないartifactを示してはいけません。

Scriptはinstall/import可能なRPR package interfaceを呼び出し、demo内部でpathway state machineを再実装しません。

## 現在存在するautomated acceptance

`tests/test_demo_scenarios.py`は次を確認します。

- authorized completionが1 dispatchで完了しEvidenceがvalid
- timeout-after-acceptanceが`write_status_unknown`になり、runtime recreation後にreconcileし、dispatchは1回のまま
- readback unavailableがcompleteしない
- human rejectionでexternal effectが0件

Release-level clean-wheel install、full test、artifact reproducibility、formal check、browser/Pyodide verification、exact-head CIは別のproduct gateです。このdemo testだけから推論してはいけません。

## Qualityとclaim boundary

このdemoのpassは、tested environmentにおける宣言済みscenarioを検証します。Real payment systemのproduction readiness、financial regulatory compliance、credential security、universal exactly-once、organizational delegationの正当性、特定organizationへの適合性は示しません。

Real deploymentは、authenticated authorization source、receiver eligibility/delegation source-of-truth、credential isolation、network control、independent external readback、operational ownership、incident procedureを別途提供する必要があります。
