# RPR 技術FAQ・よくある疑問

このページでは、Responsibility Pathway Runtime（RPR）を初めて見た人が抱きやすい疑問に答えます。宣伝用FAQではなく、何ができるのか、どのEvidenceがあるのか、どこまでをclaimしないのかをセットで整理します。

## 結局、RPRは何ができるの？

RPRは、重要な外部操作の結果が分からなくなったとき、それを勝手に成功・失敗・再試行可能へ変えないためのruntimeです。

AI agentやautomationが外部へwriteをdispatchした直後に応答が失われても、未解決attempt、承認context、Evidence、recovery stateをrestart後まで保持できます。そのうえで、configured responsibility pathwayに従って、readback、reconciliation、repair、explicit resume、hold、bounded Human Returnのどこへ進むかを明示できます。

**Evidence:** persistent pathway / execution-attempt state、`write_status_unknown`、restart continuity、independent readback path、実行可能demo scenarioがPublic Alphaに含まれます。

**Boundary:** RPRは法的責任や組織上の責任を決めません。receiverにAuthorityを生成するものでもありません。

## 具体的にどんなときに必要？

次の3条件がそろうときに有効です。

1. 外部actionに実害や重要なside effectがある。
2. dispatch後に結果不明になる可能性がある。
3. 何が起きたか確認せずretryすると危険である。

例として、決済、メッセージ送信、deploy、record更新、outbound tool callなどがあります。timeoutやprocess crashが、external system側では処理済みの後に起きる場合が対象です。

**Boundary:** RPRはすべてのagent actionに必要ではありません。read-only、何度でも安全に繰り返せる処理、またはremote system側で十分強いexactly-once / reconciliation保証がある場合は、このlayerが不要なことがあります。

## TemporalやLangGraphなどのworkflow engineでよくない？

RPRはworkflow engineではなく、orchestration、scheduling、durable queue、retry、sagaを置き換えません。workflow engineはRPRのhostとして使えます。

RPRが扱うのはもっと狭いcontractです。authorization、attempt identity、uncertain external effect、readback、repair/resume boundary、Responsibility Routingを、外部結果が未解決な間も同じ経路で接続して保持します。

既存workflow toolingとapplication-specific state / policy codeを組み合わせれば同等動作を作ることはできます。RPRの目的は、そのresponsibility contractを各integrationが毎回作り直さなくてもよくすることです。

**Boundary:** workflow engine一般が不十分だというclaimではありません。

## それってidempotencyだけでよくない？

Idempotencyは重要で、RPRとも補完関係にあります。ただしidempotencyだけで、すべてのambiguous outcomeを扱えるわけではありません。

remote systemが同じkeyとsemanticsを正しく扱える場合、idempotency keyは重複effect防止に役立ちます。RPRはさらにexecution attempt、未解決effect、independent readback、recovery decision、responsibility routeをrestart後まで接続します。

**Boundary:** RPRはidempotencyを置き換えず、任意のremote systemに対してexactly-onceを保証しません。

## ただのstate machineでは？

RPRは明示的なstate transitionを使いますが、「stateがあること」自体を新規性としてclaimしていません。

価値はstateをまたいで保持するcontractにあります。proposal / authorization履歴、attempt identity、effect uncertainty、Evidence、readback requirement、repair/resume distinction、route visibility、Residual Owner、bounded next actionを接続して保持します。

**Boundary:**十分に設計されたapplication-specific state machineでも同等動作は実装できます。RPRはそれを再利用可能なreference runtime / contractとして提供します。

## Human Returnってhuman-in-the-loopの言い換え？

違います。Human ReturnはResponsibility Routeの一つに限定されます。

未解決actionは、reconciliation hold、neutral hold、明示的にdelegationされたeligible receiver route、stop/preserve stateなどに残る場合があります。RPRは「非自律なら全部人へ戻す」とは定義しません。

**Boundary:** receiver eligibilityとorganizational Authorityはintegration側の責任です。

## 本当にもう1 layer必要？

常に必要ではありません。

read-only、安価にreversible、実際のremote semanticsでもfully idempotent、またはprior resultを確認せず繰り返しても安全なら、RPRは過剰なことがあります。

RPRが強く効くのは、duplicate execution、approval contextの欠落、restart discontinuity、誤ったescalationがmaterialな損失につながる場合です。

## その境界を埋めると、実際どこまで効果がある？

RPRはagent safetyやreliabilityを何％改善する、という一般claimをしていません。

効果はもっと狭く、testableです。ambiguous write後のblind retry、unknown stateのsuccess/failureへのsilent conversion、restartによる未解決state喪失、approvalとexecution historyの分断、本来不要なgeneric Human Returnなど、特定failure pathを明示化・除去することが対象です。

評価指標としては、duplicate dispatchを防げた件数、未解決effect保持率、restart recovery成功率、required readbackなしでcompletionした件数、unnecessary Human Return頻度などが使えます。

**Boundary:** synthetic/local resultは、そのscenarioとenvironmentのEvidenceです。universal production readinessのclaimには昇格しません。

## 入れて生まれる最大の驚きは？

直感に反する可能性は、責任境界を厳密にすることで、人間への不要なescalationが増えるのではなく減ることです。

`write_status_unknown`、reconciliation hold、neutral hold、bounded Human Returnを区別できれば、「安全のため全部人へ戻す」必要がなくなり、本当に人間の判断やAuthorityが必要な場面までmachine-processableな状態を維持できます。

**Boundary:** RPRはautomation rateが一般に上昇するとはclaimしていません。architectural claimは、Human Returnをuniversal fail-closed destinationにしない設計が可能になる、という範囲です。

## モデルが賢くなったら不要にならない？

RPRが扱うのは、external system、transport、process lifetime、authorization、responsibility stateの不確実性です。model reasoningが向上しても、network failure、ambiguous remote write、process crash、organizational Authority boundaryは消えません。

より強いmodelがconfigured routeの提案を改善する可能性はありますが、capabilityはAuthorityを生成せず、必要なreadbackなしのEvidenceはexternal effectの証明にはなりません。

## 実際に試せる？

はい。

- PyPI Public Alpha: `responsibility-pathway-runtime==0.1.0a6`
- CLI: `rpr`, `rpr-mcp`
- project siteのlive browser demo
- repository内のexecutable scenarios / tests

live browser demoはcurrent repository sourceからCI buildしたwheelを動かすため、PyPI `0.1.0a6`公開後のdevelopment changeを含む場合があります。公開artifactそのものを確認したい場合は、PyPI `0.1.0a6`またはtag `v0.1.0a6`を使用してください。

## Formal verificationはどこまで？

selected Lean 4 assetsは、encoded definition / assumptionのもとでbounded state-transition invariantを確認します。

**Boundary:** RPR全体、external system、receiver eligibility、delegation semantics、法的責任、production correctnessをformal verifyしたという意味ではありません。Lean kernel acceptanceはformal model上のtheoremに関するEvidenceであり、real-world validityやAuthorityを自動的に証明しません。

## 誰が使ってるの？

RPRはPublic Alphaで、再現可能なfield testingとintegration feedbackを募集している段階です。広範なproduction adoptionについては、公開Evidenceがない限りclaimしません。

## 次にどこを見ればいい？

- [`README.md`](../../README.md) — product overview / current public surface
- [`quick-start.md`](quick-start.md) — installation / rehearsal flow
- [`product-scope-architecture.md`](product-scope-architecture.md) — product / architecture boundary
- [`support-maturity.md`](support-maturity.md) — maturity by surface
- [`verification-release-uat.md`](verification-release-uat.md) — verification / release evidence
- [`claim-boundary-promotion.md`](claim-boundary-promotion.md) — claim promotion rule
