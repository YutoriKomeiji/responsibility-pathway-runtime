# はじめてのRPR

RPR（Responsibility Pathway Runtime）は、AIエージェントや自動化処理の外部操作に、**止められる・確かめられる・人間へ戻せる責任経路**を組み込むためのPythonランタイムです。

> **責任経路は、責任者を並べた静的な線ではありません。**  
> 判断、権限、承認、実行、証拠、停止、復旧、残余責任を切断せずにつなぐ、動的で実行可能な経路です。

このガイドは、RPRを初めて見る方が次のことを理解できるように書かれています。

- RPRが何を解決するのか
- どこへ組み込むのか
- 最初に何を試せばよいか
- Human Gateやreadbackがなぜ必要なのか
- どこから先は利用側の責任なのか

---

## 1. RPRは何をするものですか

AIエージェントがファイルを書き換えたり、APIを呼び出したり、メッセージを送ったりするとき、単に「ツール呼び出しが成功した」だけでは十分ではありません。

たとえば、次の問題が起こります。

- 操作を承認した人が分からない
- 実行してよい範囲が曖昧
- 通信が切れ、書き込みが成功したか分からない
- 再試行で同じ処理を二重実行する
- 異常を検出しても止める権限がない
- 人間へ戻すべき状態なのに自動処理が続く
- 完了したという記録はあるが、外部システムを読み戻していない
- 失敗後の修復や残った影響の担当者がいない

RPRは、こうした外部操作を次の経路へ通します。

```text
提案された操作
      ↓
適用される要件と権限を確認
      ↓
allow / hold / human_gate / deny
      ↓
許可された場合だけ実行
      ↓
外部結果をreadbackで確認
      ↓
完了 / 結果不明 / 修復 / 人間へ返却
```

RPRは、AIに法的責任を負わせる仕組みではありません。AIが関与する行為の中で、**誰の権限で進み、何を証拠とし、どこで止まり、誰へ戻すか**を扱うための実行基盤です。

---

## 2. RPRが向いている場面

RPRは、AIエージェントだけでなく、外部作用を持つ自動化処理全般へ使えます。

- AIエージェントによるファイル更新
- APIを通じたデータ登録・変更
- メールや通知の送信
- CI/CDやリリース処理
- 長時間タスクの停止・再開
- RPAや業務ワークフロー
- Human-in-the-loopを含む承認処理
- 障害復旧や修復操作

特に、次のどれかがある場合に向いています。

- 外部システムを書き換える
- 人間の承認が必要
- 再試行や再起動が起こる
- 完了確認を残したい
- 失敗時に安全停止したい
- 後から責任経路を再構成したい

---

## 3. 最初の5分

> 現在の独立リポジトリはPrivate Alphaの製品化作業中です。以下の手順は、本体コードの移植完了後に利用できます。

### 必要な環境

- Python 3.11以上
- Git
- 仮想環境の利用を推奨

### インストール

リポジトリを取得し、開発モードでインストールします。

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

RPRをインストールします。

```bash
python -m pip install -e .
```

### サンプルを確認する

```bash
rpr check examples/file_update.json
```

このコマンドは、サンプル責任経路が実行可能な構造を持っているかを確認します。実際の外部変更を行うコマンドではありません。

---

## 4. RPRの基本用語

### Pathway

一つの操作について、所有者、承認者、実行者、停止権限、証拠、修復担当、残余責任者をつないだ責任経路です。

### Human Gate

自動処理を止め、人間または適切な組織へ判断を返す状態です。単なる通知ではなく、承認された状態遷移が行われるまで先へ進みません。

### Readback

外部作用が本当に起きたかを、実行結果とは別に確認することです。

例:

- 書き込んだファイルを読み直してSHA-256を比較する
- 作成したAPIリソースを再取得する
- 配信事業者の永続的な受付IDを確認する
- 別の監視経路で外部状態を照合する

### `write_status_unknown`

外部書き込みが成功したか失敗したか判断できない状態です。

RPRは、この状態を成功にも失敗にも推測しません。独立した観測や人間の判断によって照合されるまで停止します。

### Idempotency

同じ操作が再試行されても、二重実行を防ぐための考え方です。RPRはoperation ID、attempt ID、idempotency keyと実行内容の対応を保持します。

### Residual Owner

ロールバックできない影響や、処理終了後にも残る問題を継続して管理する主体です。

---

## 5. 最小の導入契約

RPRを実行ゲートとして利用する環境には、少なくとも次の5点が必要です。

1. 外部操作を構造化データとして表せる
2. 外部へ送る前にRPRを必ず通せる
3. pathway、operation、attempt、idempotencyの識別子を保持できる
4. 独立したreadbackまたはreconciliationを実装できる
5. Human Gateで停止し、勝手に続行しない

モデル、LLM、オーケストレーションフレームワークは交換できます。この5点が、RPRとの最小契約です。

---

## 6. どこへ組み込めばよいですか

RPRは、**外部作用が起きる直前**へ置きます。

```text
LLM / Planner / Agent Framework
              ↓
      提案されたTool Call
              ↓
             RPR
              ↓
     実際のFile / API / Mail
```

ツール実行後のcallbackだけでは、実行ゲートになりません。観測には使えますが、危険な操作を事前に止められないためです。

### 小規模なPythonアプリ

Pythonライブラリとして、ツール呼び出し直前に組み込みます。

### Function Calling型エージェント

書き込みを行う各ツールをRPRの境界でラップします。

### Graph型ワークフロー

変更ノードの前にRPRノードを置き、`human_gate`、repair、reconciliationへ明示的に分岐させます。

### 複数言語・複数サービス

アプリケーション所有のAPIまたはsidecarとしてRPR境界を置けます。ただし現在のAlphaは、Production Gatewayそのものを提供していません。

---

## 7. 典型的な状態の流れ

通常経路:

```text
proposed
  → awaiting_approval
  → approved
  → running
  → completed
```

停止・復旧経路:

```text
running
  → write_status_unknown
  → repair_required
  → ready_to_resume
```

部分完了:

```text
running
  → partially_completed
  → repair_required
```

人間へ返す経路:

```text
held
  → human_gate
```

RPRでは、失敗経路も例外処理ではなく、正式な状態として扱います。

---

## 8. 最初に試すべき安全なユースケース

最初からメール送信、課金、公開リポジトリ変更、本番データ更新へ使わないでください。

推奨する最初の対象は、次の条件を満たすものです。

- 単一の操作
- 狭い範囲
- ローカル環境
- 可逆
- readbackが簡単
- 人間が結果を確認できる

例:

> 専用のテストディレクトリ内で、一つのテキストファイルを更新し、内容とSHA-256を読み戻して確認する。

このテストで、少なくとも次を確認します。

- 承認なしでは実行されない
- 許可されていない状態遷移が拒否される
- 同じattemptの再実行が二重書き込みにならない
- readbackが失敗した場合に完了扱いされない
- Human Gateから自動で抜けない
- 再起動後もattemptが復元される

---

## 9. RPRとRPEの違い

RPE（Responsibility Pathway Engineering）は、承認されたRequirement Packを用いて、提案された操作を次の判定へ振り分けます。

```text
allow / hold / human_gate / deny
```

RPRは、その判定を受けた後の実行経路を扱います。

```text
RPD: 責任経路を設計する
  ↓
RPE: 実行前に要件を評価する
  ↓
RPR: 状態、実行、証拠、readback、復旧を維持する
```

RPRはRPEを置き換えず、RPEのポリシー意味論を複製しません。

---

## 10. Lean 4は何を証明しますか

RPRはPythonで動作します。状態遷移モデルはJSON、Python、Lean 4の間で整合確認され、選択された不変条件がLean 4で機械検査されます。

検査対象の例:

- 許可されていない状態遷移が起きない
- Human Gateが無断で解除されない
- `write_status_unknown`から直接`completed`へ進まない
- 必須条件を満たさず完了扱いにならない

Lean 4があることだけで、次のものが証明されるわけではありません。

- Python実装全体の完全な正しさ
- 外部APIやネットワークの挙動
- 法的適合性
- 運用判断の妥当性
- AIモデルの真実性や安全性
- システム全体のProduction Readiness

RPRは、形式証明を宣伝用バッジではなく、**何を確認し、何を確認していないかを分けるための実装資産**として扱います。

---

## 11. RPRだけでは提供しないもの

RPRは、次のものを自動的には提供しません。

- Identity Provider
- OS Sandbox
- Network Isolation
- Credential Vault
- あらゆる制度を解釈する万能Policy Engine
- 任意の外部システムでのexactly-once保証
- 法令準拠や認証の自動判定
- 入力されたRequirement Packや人間判断の正しさ
- RPRを迂回する経路への防御

利用側は、認証、認可、ネットワーク、秘密情報、監視、バックアップ、個人情報、可用性を含む運用設計を別途行う必要があります。

---

## 12. 本番導入前のチェックリスト

外部作用を有効にする前に確認してください。

- すべての対象操作がRPRを通る
- RPRを迂回できるCredentialやNetwork Routeがない
- Principalが信頼されたホスト側で認証されている
- Idempotencyの単位と有効範囲が定義されている
- 外部作用ごとに独立readbackがある
- 永続Storeにbackup、restore、retention、migration手順がある
- Evidenceへ不要な秘密情報や個人情報を保存しない
- Human Gateの担当者とEscalation先が決まっている
- `write_status_unknown`のreconciliation手順を試験済み
- 公開・高影響操作には明示的な承認ルールがある
- completed、held、unknown、repair_requiredを監視上で区別できる

---

## 13. 推奨する導入順序

1. 一つの可逆で限定された操作から始める
2. 独立readbackを実装する
3. attemptを永続化し、再起動試験を行う
4. Human Gateとrepair routeを追加する
5. 直接実行できる迂回経路を閉じる
6. 証拠をレビューしてから対象ツールを増やす
7. clean installと障害復旧をRelease Candidate環境で試す
8. 対応範囲と非対応範囲を公開前に明記する

> **小さく正しく統治された実行面は、広く見えるだけで迂回可能な統治面より安全です。**

---

## 14. 困ったときの見方

### 操作が進まない

`reason_code`、不足しているevidence、現在のstate、Human Return先を確認してください。RPRは安全側で停止するため、情報不足や所有者不明を暗黙の`allow`へ変換しません。

### 通信エラー後に再試行できない

外部書き込みが成功している可能性があります。先にreadbackまたはreconciliationを行い、`write_status_unknown`を解消してください。

### Human Gateから抜けない

認可された主体による明示的な状態遷移が必要です。単にUIで「確認済み」と表示するだけでは解除されません。

### 完了にならない

executorの戻り値だけでなく、外部作用のreadback evidenceが必要です。

### Leanが通るので安全ですか

Leanが確認するのは、形式化された定義と前提の範囲です。実装、外部環境、運用を含む全体安全性は別に検証してください。

---

## 15. 次に読むもの

- [`README.md`](../README.md) — RPRの製品概要
- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — 責務とTrust Boundary
- [`docs/using-rpr.md`](using-rpr.md) — 技術者向け統合ガイド
- `docs/responsibility-pathway-minimum-test.md` — 最小運用試験
- `docs/formal-methods-integrity.md` — Lean 4の証明範囲
- `docs/threat-model.md` — 脅威モデル
- `SECURITY.md` — セキュリティ報告

一部の文書は、本体コードとともに独立リポジトリへ移植予定です。

---

## License

RPRはMIT Licenseです。

利用、改変、組込み、再配布、商用利用ができます。MIT License本文と著作権表示を保持してください。

**使ってください。試してください。壊して確かめてください。改善を共有してください。**
