# Surface別SupportとMaturity

RPRはrepository全体を一律にexperimentalとせず、surfaceごとにmaturityを区別します。

| Surface | 現在のposture | Notes |
|---|---|---|
| Core Python/SQLite pathway runtime | Supported | 文書化されたcontract内の限定的な実integrationを対象とします。 |
| Pathway persistence / restart continuity | Supported | Repository testとpublic scenarioで確認します。 |
| Responsibility Routing / bounded Human Gate / repair / resume / reconciliation | Supported Public Alpha | 公開済み`0.1.0a6` packageに、文書化されたalpha contractの範囲で含まれます。route visibilityもreleased surfaceです。 |
| Local-fileとbounded outbound path | Supported reference | Integration固有のauthority/network controlと組み合わせて利用します。 |
| Governed outbound MCP subprocess path | Supported reference | Reference integrationです。peer identityとdeployment controlはintegrator-ownedです。 |
| Read-only `rpr-mcp` inspection server | Supported reference | Local trusted client向けinspection surfaceです。公開済み`0.1.0a6` surfaceにはread-only route visibilityが含まれます。 |
| Article 50 transparency profile | Preview / bounded profile | Structured profileであり、法的分類やcompliance certificationではありません。 |
| Customer-equivalent proxy/TLS/identity profile | Field evidence collecting | 実環境reportを受け付けますが、universal readinessは主張しません。 |
| Remote production MCP transport | Not included | 将来のbounded workです。 |
| 任意systemに対するuniversal exactly-once | Unsupported as a universal claim | Target側contractとauthoritative readbackが必要です。 |
| Legal/organizational Authorityの生成 | Unsupported | RPRは宣言済みAuthorityを保持しますが、生成しません。 |

## Responsibility Routingのmaturity境界

公開済み`0.1.0a6` Public AlphaのResponsibility Routingは、bounded Human Returnをneutral hold、reconciliation hold、明示的delegation内のeligible receiver、stop/preserve outcomeから区別します。Route recordはreceiver eligibility、delegation scope、unresolved payload、allowed next actions、closure/reevaluation condition、Residual Ownerを保持します。

ただし、あらゆるorganizational routeをRPRが自動的に妥当化するわけではありません。Receiver eligibilityとAuthorityはintegration boundaryから与える必要があります。Evidence transfer、capability、successful transport、route selectionはAuthorityを生成しません。

現行Lean layerが証明するのは限定されたstate-transition invariantです。Responsibility Routingのreceiver eligibilityやdelegation semanticsを形式証明したものではありません。

## Vocabulary

- **Supported** — 文書化された境界内で通常利用を想定し、defectを受け付けて修整します。
- **Supported Public Alpha** — 文書化されたalpha claim boundaryの範囲で公開済みalpha packageに含まれます。stable release前なのでinterface/semanticsは進化する可能性があります。
- **Supported reference** — 利用可能なreference implementationであり、deployment hardeningの一部はintegrator-ownedです。
- **Preview** — early useとfeedback向けで、interface/semanticsが進化する可能性があります。
- **Field evidence collecting** — 実装済みですが、より広い環境evidenceを収集中です。
- **Not included** — 現行project surfaceでは提供していません。
- **Unsupported** — 意図的に約束しない、またはruntimeが生成すべきでないAuthorityです。

`Not guaranteed`は自動的に`forbidden`を意味しません。
