<!--
Document Title: RPR Japanese Writing Profile
Document Type: Public Product Documentation Standard
Status: Draft v0.3
Header Language: English
Body Language: Japanese
-->

# RPR 日本語ドキュメント執筆基準

この文書は、RPRの日本語README、製品ページ、デモUI、クイックスタート、統合ガイドに適用する執筆基準です。

日本語はB2B向けの自然な技術日本語とし、日本のIT・ビジネス文脈で定着している英語由来語は一般的なカタカナ表記を優先します。一方、RPR固有の責任・Authority・Evidence概念は、意味を変えないことを優先し、英語版とのsemantic parityを機械検査できる形で残します。

## 1. 読者が先に知りたいことを書く

RPRの内部構造より先に、利用者が解決したい問題と得られる結果を示します。

| 内部起点 | 利用者起点 |
|---|---|
| `write_status_unknown`を永続化する | APIが成功したか分からない状態を保存する |
| `reconciliation`を実行する | 外部システムの状態を読み直して結果を確かめる |
| execution attemptを保持する | いつ、何を、何回実行したかを残す |
| Human Gateを要求する | 明示的に人間の判断・Authorityが必要な場面だけ人間へ返す |
| Responsibility Routeを保持する | 未解決の仕事を、誰が・何のAuthorityで・どこまで引き受けられるかを失わない |

正式な状態名や型名は、日本語で意味を説明した後に示します。

## 2. 用語の基準表記

### カタカナを優先する一般技術語

- runtime → ランタイム
- package → パッケージ
- adapter → アダプター
- framework → フレームワーク
- proxy → プロキシ
- release → リリース
- deployment → デプロイ
- retry → リトライ
- security → セキュリティ
- support → サポート

### 英字を維持する標準略語・製品名

- AI
- API
- MCP
- HTTP
- JSON
- TLS
- GitHub
- Python
- SQLite
- PyPI
- Lean 4

### RPR固有語

| 実装語 | 日本語本文での基準表記 |
|---|---|
| Responsibility Pathway | 責任経路 |
| Responsibility Routing | 初出では「Responsibility Routing（責任の引受先を限定して保持する経路選択）」、以後はResponsibility Routing |
| Responsibility Route | Responsibility Route、または文脈が明確なら「責任Route」 |
| bounded Human Return | bounded Human Return。「人間へ返す」は必ず限定Routeであることを明示 |
| Human Gate | Human Gate。すべてのfail-closedのgeneric fallbackとして書かない |
| Authority | Authority。単なる能力・権限一般と混同しやすい場合は「宣言済みAuthority」と書く |
| receiver eligibility | receiver eligibility（受取先としての適格性） |
| delegation scope | delegation scope（委任範囲） |
| Residual Owner / residual owner | Residual Owner（未解決・残存影響のowner） |
| pathway | 責任経路 |
| runtime | ランタイム |
| execution attempt | 実行履歴。型名を示す場合は`execution attempt`を併記 |
| evidence chain | 証拠チェーン |
| Evidence | Evidence。Authorityを生成しないことが重要な文脈では英字を維持 |
| readback | 読み戻し、外部状態の再確認 |
| reconciliation | 照合。必要に応じて`reconciliation`を併記 |
| repair | 修復 |
| resume | 再開 |
| `write_status_unknown` | 結果不明（`write_status_unknown`） |
| `hold_for_reconciliation` | reconciliation待ちのhold（`hold_for_reconciliation`） |
| `bounded_human_return` | 限定Human Return（`bounded_human_return`） |
| `authority_inferred: false` | Authorityを推論していないことを示すmachine-readable marker。文字列を勝手に翻訳・省略しない |
| provider | 外部サービス |
| dispatch | 外部サービスへの実行要求。コード説明では`dispatch`を併記可 |

同じ概念を日本語、英語、カタカナで無秩序に切り替えません。

## 3. Responsibility Routingの書き方

次の区別を崩してはいけません。

- `fail closed` ≠ Human Gate
- Evidence transfer ≠ Authority transfer
- receiver capability ≠ receiver eligibility
- route selection ≠ Authority grant
- state recovery ≠ approval/resume Authority recovery
- Human Return = bounded Responsibility Route
- unresolved effect = successでもfailureでもない

Generic evaluator failure、invalid route、ineligible receiver、結果不明から「人間へ返す」を自動導出しません。Eligible receiverやAuthorityが成立していない場合は、neutral holdが正しいことがあります。

## 4. README・製品ページ・デモ

最初の画面は、次の順を基本にします。

1. 何が困るのか
2. RPRがどう扱うのか
3. 今使える範囲
4. 公開済みpackageとsource previewの違い
5. 最短の試し方
6. 既知の制約
7. 詳細な設計・検証情報

### 見出し

| 避ける | 推奨 |
|---|---|
| LIVE EXECUTION | 実際のRPRで復旧まで試す |
| Pathway登録 | 実行前の責任経路を登録する |
| Runtime再生成と照合 | 再起動して結果を確認する |
| 曖昧writeを発生 | 結果不明を発生させる |
| 人間に返す | 必要なAuthorityを持つbounded Human Returnへ返す |

### ボタン

- RPRを読み込む
- 責任経路を登録する
- 結果不明を発生させる
- 再起動して結果を確認する
- 最初からやり直す

### 実物と模擬

> RPRのPythonパッケージ、SQLite、実行履歴、証拠チェーン、照合処理、Responsibility Routing visibilityはブラウザ内で実際に動作します。
>
> 外部の決済サービスだけを、安全に試せるテスト用処理へ置き換えています。

## 5. 公開済みreleaseとsource previewを混同しない

公開済みpackage、repository `main`、未release source preview、release candidateを同一視しません。

例:

> 公開済み`0.1.0a5`にはread-only `rpr-mcp`が含まれます。現行post-`0.1.0a5` sourceは`rpr.get_route_visibility`を追加していますが、これは次releaseのexact-head validationとHuman Gate前のsource previewです。

過去releaseの事実を現在状態へ合わせて書き換えません。Active documentでは現在のpublished versionとsource-preview境界を明示します。

## 6. リスク・制約の書き方

「アルファだから使わないで」ではなく、条件と不足機能を具体的に書きます。

例:

> ローカルのMCP stdio経路は現在の公開版で利用できます。リモートMCP、企業認証、資格情報管理、本番プロキシ構成はRPR単体では提供しないため、統合環境側で準備してください。

`not guaranteed`と`forbidden`を混同しません。

## 7. GitHubドキュメント

手順文書は次の順で書きます。

1. この手順で何ができるか
2. 前提条件
3. 実行するコマンド
4. 確認する結果
5. 失敗した場合の確認先
6. 対象外と制約

コマンド、パス、状態名、route class、machine-readable marker、ハッシュ、バージョン、Freeze IDは英語版と一致させます。

## 8. 主張と証拠

次の語は、対象・条件・Evidenceを同じ節に示せる場合だけ使用します。

- 検証済み
- 実動
- 再現可能
- 二重実行を防ぐ
- 安全
- 本番対応
- 保証
- Authorityを保持する
- Responsibility Routingを検証した

例:

> ブラウザデモでは、CIで生成したRPR wheelをPyodideへ読み込みます。SQLiteへ結果不明状態を保存し、新しいランタイムから読み戻して、再送せずに照合を完了するところまでChromium E2Eで確認します。Route visibilityでは`bounded_human_return`、`hold_for_reconciliation`、`authority_inferred: false`もassertします。

この確認は、一般的な本番安全性、法令適合、任意の外部サービスでのexactly-once、receiver eligibilityの正しさ、organizational Authorityの正当性を意味しません。

## 9. 最終確認

- [ ] 冒頭に利用者の困りごと、目的、得られる結果がある
- [ ] 日本で一般的な技術語を不要に英語表記していない
- [ ] AI/API/MCPなど標準略語を不自然にカタカナ化していない
- [ ] 名詞を重ねすぎていない
- [ ] 技術語を日本語で説明してから実装語へ接続した
- [ ] Responsibility Routing / bounded Human Return / Authority / receiver eligibilityの区別が維持されている
- [ ] `fail closed`を自動的にHuman Gateと書いていない
- [ ] `authority_inferred: false`などmachine-readable contractを翻訳・省略していない
- [ ] 実物、模擬、未確認を分けた
- [ ] 公開済みreleaseとsource previewを分けた
- [ ] コード識別子、コマンド、URL、バージョン、Freeze IDが正しい
- [ ] MIT Licenseの無保証を弱める表現がない
- [ ] 英語版と機能、制約、手順、Evidence、semantic anchorが一致する
