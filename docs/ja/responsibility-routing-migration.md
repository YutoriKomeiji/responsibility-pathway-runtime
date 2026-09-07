# Responsibility Routing 互換実装ベースライン

Status: source preview上で実装済みの互換ベースライン。現在PyPIで公開中の版は`0.1.0a5`であり、この文書自体は新しいリリースを公開しません。

## 目的

Responsibility Pathway Runtime（RPR）は、承認、実行、外部作用の結果不明、照合、修復、再開まで責任経路を永続的に保持します。初期Public AlphaではHuman Gateと`human_return_point`を前面に置いていました。Responsibility Routingでは、Human Returnを有効な一つの限定Routeとして残しつつ、責任の移送先をより一般化します。

互換方針はadditiveです。既存state、永続化、Authority field、旧serializationを維持しながら、Authorityを暗黙に生成しないRoute semanticsを追加します。

## 中核ルール

責任を伴う遷移が有効なのは、次のholderが正当なAuthorityの範囲で行動でき、未解決residueを失わないために必要な情報をRouteが保持する場合だけです。

Evidence transferはAuthority transferではありません。Receiverの能力、model confidence、agent consensus、tool成功、Route表示、checkpoint回復、handoff receiptだけではdelegationは拡張されません。

## 実装済みのRoute vocabulary

`ResponsibilityRouteClass`には現在、次があります。

- `CONTINUE_AUTONOMOUSLY`
- `AI_RESOLVE_WITHIN_DELEGATION`
- `HOLD_FOR_RECONCILIATION`
- `BOUNDED_HUMAN_RETURN`
- `STOP_AND_PRESERVE_RESIDUE`

これらはsource modelには存在しますが、全classをruntime dispatchが自動選択するという意味ではありません。最初の互換cycleでは、既存RPR semanticsから根拠を持って確定できるstateだけを自動分類します。

## 実装済みのRoute record

`ResponsibilityRoute`は次を保持できます。

- route class
- source holder
- destination
- receiver eligibility
- Authority class
- delegation scope
- unresolved payload / residue
- allowed next actions
- closure condition
- reevaluation condition
- Residual Owner
- optional expiry

このrecordは`PathwayDefinition`へadditiveに付加されます。Route未指定時は旧serialized definition shapeを維持します。Optional routeは既存definition JSON内に保存するため、SQLite schema version 1も変更しません。

Route typeは現在top-levelの`rpr` Python exportへ昇格していません。外部向けに文書化しているsource-preview inspection contractは、後述の独立したread-only MCP toolです。

## 実装済みの互換mapping

自動mappingは現時点で次の2つだけです。

- `PathwayState.HUMAN_GATE` -> `bounded_human_return`
- `PathwayState.WRITE_STATUS_UNKNOWN` -> `hold_for_reconciliation`

それ以外のstateは、Routing semanticsを明示設計・reviewするまで未分類です。Route classが存在するという理由だけで、completed、repair-ready、runningなどを勝手に新しいRouteへ変換しません。

## Human Returnは有効だが限定Route

### `PathwayDefinition.human_return_point`

分類: `NARROW_BUT_VALID`。

具体的なHuman Returnが必要な場合には引き続き有効です。一方、非Human Routeすべての必須条件としては扱いません。

### `PathwayState.HUMAN_GATE`

分類: `NARROW_BUT_VALID`。

人間が保持する判断またはAuthority boundaryが実際に必要な場合に有効です。設定不正、RPE利用不可、不適格receiver、結果不明の外部作用の一般fallbackではありません。

### `RuntimeDecision.HUMAN_GATE`

分類: `NARROW_BUT_VALID`。

Approval authorityと具体的なreturn pointを持つhigh-impact actionなどは引き続きHuman Gateを要求できます。一般的なfail-closed条件は、有効なHuman Gateが別途成立しない限り`HOLD`します。

### `InspectionResult.human_return_available`

分類: `NARROW_BUT_VALID`。

旧Human Return surfaceの有無だけを示します。一般的なRoute availabilityやReturnabilityとして解釈してはいけません。

## Receiver eligibilityとFalse Escalation

Active routeのreceiverが`INELIGIBLE`、Route payload不正、Residual Owner不一致、bounded action不足の場合、そのRouteはinvalidとしてdefinition修復までholdします。`REQUIRES_REEVALUATION`もeligibilityを再評価するまでholdします。

これらの条件からHuman Gateを自動生成しません。Receiver eligibility、Authority、context、bounded next-decision scopeが成立していない状態で、人間を指定するだけでは安全なreturnになりません。

## RPE利用不可・contract failure

RPE利用不可、adapter failure、contract mismatchはfail-closedのままですが、それだけでは人間が正しいreceiverだとは証明できません。中立的な結果は`HOLD`です。

一方、local pathway inspectionがhigh-impact actionなどについて有効なHuman Gateを独立に要求している場合、decision結合ではより厳しいHuman Gateが維持されます。

## Authorityとownership

`approval_authority`、`stop_authority`、`resume_authority`など既存の明示Authority fieldは有効です。`decision_owner`、`evidence_owner`、`repair_owner`、`residual_owner`など既存owner fieldも有効です。

Responsibility Routingは、Route destination、receiver capability、evidence、visibilityからexecution/reconciliation Authorityを付与しません。また、別途認可されたownership変更がない限り、RouteはpathwayのResidual Ownerを保持します。

## 外部作用の結果不明

`write_status_unknown`は引き続き第一級の未解決stateです。Route visibilityでは`hold_for_reconciliation`として表示し、success、failure、blind retry、強制Human Returnへ変換しません。

独立readback / reconciliationが外部作用を分類します。Repair完了だけでresume Authorityが生まれることもありません。

## Read-only Route visibility

Source previewのlocal read-only MCP serverには`rpr.get_route_visibility(pathway_id)`があります。結果には次を含められます。

- current state
- 根拠がある場合のcompatibility route
- 保存済みdeclared route
- Human Return point
- Residual Owner
- `authority_inferred: false`

このToolは承認、実行、照合、修復、再開、receiver選択、state mutationを行えません。

## 設計で扱うfailure class

- **False Autonomy** — delegation、Authority、eligibility、unresolved residueの条件が別Routeを要求するのに自律実行を継続する。
- **Proxy Return** — 必要なAuthority/eligibilityを持たないAI/systemへ送り、安全にreturnしたように見せる。
- **False Escalation** — 別componentの失敗だけを理由に、Human Returnが有効か確認せず人へ送る。
- **Nominal Human Return** — 人間の名前や通知はあるが、Authority、context、eligibility、bounded next-decision scopeが不足する。

## 検証レイヤ

互換sliceは複数レイヤで確認します。

- unit: Route serialization、旧positional/wire互換、Route validation、Authority non-propagation、compatibility mapping
- component: SQLite persistenceとRoute visibility
- MCP integration: 独立read-only Route toolとdatabase byte invariance
- runtime/product: fail-closed RPE fallback、high-impact Human Gate維持、ambiguous write、restart、reconciliation、duplicate-dispatch prevention
- browser/Pyodide: Routeを表示するlive demo
- CI: package build、clean install、構造/日英検証、reproducibility、formal state-model check

Lean 4で現在検証しているのは選択されたpathway state-machine invariantです。Route metadata、receiver eligibility、Responsibility Routing selection semantics自体は、まだLeanで形式証明していません。

## 互換・release boundary

このmigrationではHuman Gateや`human_return_point`を破壊的renameせず、SQLite schema version 1を変更せず、mutating MCP toolを追加せず、AIが法的・制度的accountabilityを負うという主張もしません。

Source integrationとbinary publicationは別です。別途release promotionを承認し、readbackを完了するまで、公開packageは`0.1.0a5`のままです。