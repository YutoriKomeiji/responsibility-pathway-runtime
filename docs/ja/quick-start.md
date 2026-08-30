<!--
Document Title: RPR クイックスタート
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a5
Freeze ID: RPR-CF-2026-08-02-01
Header Language: Japanese
Body Language: Japanese
-->

# クイックスタート

RPRは[`MIT License`](../../LICENSE)に基づき、無保証で提供されます。まず使い捨て可能で影響のない環境で試験し、利用環境への適合性は利用者自身で判断してください。

GitHub Prerelease / sourceとPyPI packageは、Public Alpha `0.1.0a5` で揃っています。

- [PyPI 0.1.0a5](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a5/)
- [GitHub Prerelease v0.1.0a5](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a5)
- [実RPRブラウザデモ](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html)
- [公開リポジトリ](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

## 試験の流れ

| 手順 | 実施内容 | 保存する証拠 |
|---:|---|---|
| 1 | 公開版と取得元を記録 | PyPI URL、version、Repository URL、tag |
| 2 | 隔離したPython 3.11環境を作成 | Python・pip version |
| 3 | PyPIからversion固定で導入 | Install log、導入されたpackage version |
| 4 | CLIを確認 | `rpr --help` / `rpr-mcp --help` の出力 |
| 5 | Synthetic dataでlocal pathwayを実行 | Pathway、attempt、readback、最終state |
| 6 | Restartまたは曖昧結果を試験 | 未解決effectが重複実行されない証拠 |

## 1. 隔離環境を作り、PyPIから導入する

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility-pathway-runtime==0.1.0a5
```

導入されたversionとCLIを確認します。

```bash
python -m pip show responsibility-pathway-runtime
rpr --help
rpr-mcp --help
```

対応するGitHub `v0.1.0a5` prereleaseのsource確認や開発を行う場合は、公開リポジトリを別途取得します。

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
git checkout v0.1.0a5
python -m pip install -e .
```

Windows UTF-8 BOM修復は `0.1.0a5` に含まれ、再現された環境・入力経路について検証済みです。このevidenceは、すべてのWindows環境やcustomer environmentの一般保証を意味しません。

## 2. 影響のないローカル試験を行う

使い捨てdirectoryとsynthetic dataを使用し、pathwayとauthorityの登録、Human Gateへの到達、execution attemptの保存、独立readback evidenceの関連付け、restart後の未解決state復元、repairまたはreconciliationへの遷移を確認します。

最初からproduction credential、customer data、不可逆action、独立readbackできないremote writeを使用しないでください。

## 環境記録

| 分類 | 記録項目 |
|---|---|
| Runtime | OS、architecture、Python・pip version |
| Distribution | PyPI URL、導入version、GitHub tagまたはcommit |
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
