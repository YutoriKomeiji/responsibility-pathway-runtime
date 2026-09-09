<!--
Document Title: RPR Japanese Writing Profile
Document Type: Repository Authoring Control
Lifecycle: AUTHORING_CONTROL
Status: Draft v0.4
Header Language: English
Body Language: Japanese
-->

# RPR 日本語ドキュメント執筆基準

この文書はrepository authoring controlであり、利用者向けcurrent product documentationではありません。日本語README、製品ページ、デモUI、クイックスタート、統合ガイドを作成・修正するときの表記・claim境界に適用します。

## 読者起点

内部構造より先に、利用者が困ることと得られる結果を書く。

- `write_status_unknown`を永続化する → APIが成功したか分からない状態を保存する
- `reconciliation`を実行する → 外部systemの状態を読み直して結果を確かめる
- execution attemptを保持する → いつ・何を・何回実行したかを残す
- Human Gateを要求する → 明示的に人間の判断・Authorityが必要な場面だけ人間へ返す
- Responsibility Routeを保持する → 未解決の仕事を誰が・何のAuthorityで・どこまで引き受けられるか失わない

## 用語

一般技術語は日本で定着しているカタカナを優先する。AI / API / MCP / HTTP / JSON / TLS / GitHub / Python / SQLite / PyPI / Lean 4は英字を維持する。

RPR固有語は意味境界を優先する。

- Responsibility Pathway → 責任経路
- Responsibility Routing → 初出で短い日本語説明を添え、以後はResponsibility Routing
- bounded Human Return → bounded Human Return。generic fail-closedと同義にしない
- Authority → 必要なら「宣言済みAuthority」として能力・権限一般と分離
- receiver eligibility → receiver eligibility（受取先としての適格性）
- delegation scope → delegation scope（委任範囲）
- Residual Owner → Residual Owner（未解決・残存影響のowner）
- `write_status_unknown` → 結果不明（`write_status_unknown`）
- `hold_for_reconciliation` → reconciliation待ちのhold
- `bounded_human_return` → 限定Human Return
- `authority_inferred: false` → machine-readable markerのため翻訳・省略しない

## Responsibility Routingで崩してはいけない区別

- `fail closed` != Human Gate
- Evidence transfer != Authority transfer
- receiver capability != receiver eligibility
- route selection != Authority grant
- state recovery != approval/resume Authority recovery
- Human Return = bounded Responsibility Route
- unresolved effect = successでもfailureでもない

Generic evaluator failure、invalid route、ineligible receiver、結果不明から人間destinationを自動導出しない。成立したreceiver eligibility / Authority / bounded next-decision scopeがなければneutral holdが正しい場合がある。

## 公開版とsource preview

公開package、repository `main`、unreleased source、release candidateを同一視しない。

Current-facing文書でversionを示す場合は、固定した過去versionの例を再利用せず、`product-status.json`とfresh release readbackに照合する。Repository sourceに後続変更があっても、exact-head validationとHuman Gateを通過したreleaseまではpublished package contractへ昇格させない。

Historical release recordは後続versionへ合わせて書き換えない。過去の「current」「pending」「source preview」はhistorical lifecycle surfaceへ保持し、active docsから分離する。

## 実物・Evidence・claim

「検証済み」「実動」「再現可能」「二重実行を防ぐ」「安全」「本番対応」「保証」「Authorityを保持する」「Responsibility Routingを検証した」は、対象・条件・Evidenceを同じ節で示せる場合だけ使う。

Browser demo等で実runtimeを使う場合も、模擬したexternal serviceと実物のruntime/persistence/reconciliationを分離して書く。

## Version transition時のauthoring check

- [ ] `product-status.json`のcurrent published versionとactive docsが一致する
- [ ] active docsに旧versionを「current/published」とする文が残っていない
- [ ] source previewとreleased packageを混同していない
- [ ] transition/migration文書にexit/retire条件がある
- [ ] release-specific candidate/audit recordをactive docs indexへ残していない
- [ ] 日英で機能・制約・Evidence・semantic anchorが一致する
- [ ] `fail closed`を自動的にHuman Gateへ変換していない
- [ ] `authority_inferred: false`等のmachine-readable contractを変更していない
- [ ] 実物、模擬、未確認を分けた
- [ ] current-facing linkがhistorical/retired surfaceを通常導線として案内していない

このauthoring control自体は製品claimやrelease Authorityを生成しない。
