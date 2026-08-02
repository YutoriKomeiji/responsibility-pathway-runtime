<!--
Document Title: RPR クイックスタート
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# クイックスタート

RPRは[`MIT License`](../../LICENSE)に基づき、無保証で提供されます。まず使い捨て可能で影響のない環境で試験し、利用環境への適合性は利用者自身で判断してください。

現在は公開リポジトリと実動ブラウザデモを利用できます。最終tag、GitHub Release、package registryへの配布はまだ行っていません。

- [実RPRブラウザデモ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html)
- [公開リポジトリ](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

## 試験の流れ

| 手順 | 実施内容 | 保存する証拠 |
|---:|---|---|
| 1 | 公開リポジトリの取得元とcommitを記録 | Repository URL、commit SHA |
| 2 | 隔離したPython 3.11環境を作成 | Python・pip version |
| 3 | 公開ソースをeditable install | Install log、dependency解決結果 |
| 4 | CLIを確認 | `rpr --help`の出力 |
| 5 | Synthetic dataでlocal pathwayを実行 | Pathway、attempt、readback、最終state |
| 6 | Restartまたは曖昧結果を試験 | 未解決effectが重複実行されない証拠 |

## 1. 公開ソースを取得する

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
git rev-parse HEAD
```

特定の検証済み候補を確認する場合は、Freeze IDとartifact evidenceを[`release-evidence/replacement-freeze-2026-08-02.json`](../../release-evidence/replacement-freeze-2026-08-02.json)で確認してください。記録されたwheelとsdistは候補artifactであり、現時点では一般配布物ではありません。

## 2. 隔離環境を作る

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## 3. コマンドを確認する

```bash
rpr --help
python -m responsibility_pathway_runtime --help
```

## 4. 影響のないローカル試験を行う

使い捨てdirectoryとsynthetic dataを使用し、pathwayとauthorityの登録、Human Gateへの到達、execution attemptの保存、独立readback evidenceの関連付け、restart後の未解決state復元、repairまたはreconciliationへの遷移を確認します。

最初からproduction credential、customer data、不可逆action、独立readbackできないremote writeを使用しないでください。

## 環境記録

| 分類 | 記録項目 |
|---|---|
| Runtime | OS、architecture、Python・pip version |
| Source | Repository URL、commit SHA、Freeze ID |
| Integration | Host framework、adapter、network、proxy、TLS、identity、credential |
| Test | 実行command、期待結果、実結果 |
| Evidence | Secret除去済みlog、readback source、最終pathway state |

## 報告経路

| 内容 | 経路 |
|---|---|
| 再現可能な環境試験結果 | Environment-report Issue form |
| Product defect | Bug Issue form |
| Framework・Service要望 | Integration Issue form |
| 脆弱性の可能性 | [`SECURITY.md`](../../SECURITY.md)の非公開経路 |

## 停止条件

authorityがない、独立readback sourceが利用できない、credential露出の可能性がある、external effectが曖昧、pathwayを復元できない、または次のactionが明示的な人間承認なしに不可逆となる場合は試験を停止してください。
