<!--
Document Title: RPR クイックスタート
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# クイックスタート

RPRは[`MIT License`](../../LICENSE)に基づき、無保証で提供されます。まず使い捨て可能で影響のない環境で試験し、利用環境への適合性は利用者自身で判断してください。

## 試験の流れ

| 手順 | 実施内容 | 保存するEvidence |
|---:|---|---|
| 1 | [`release-manifest.json`](../../release-manifest.json)と配布物を照合 | File名、byte数、SHA-256 |
| 2 | 隔離したPython 3.11環境を作成 | Python・pip version |
| 3 | 検証済みwheelをinstall | Install log、dependency解決結果 |
| 4 | CLIを確認 | `rpr --help`の出力 |
| 5 | Synthetic dataでlocal pathwayを実行 | Pathway、attempt、readback、最終state |
| 6 | Restartまたは曖昧結果を試験 | 未解決effectが重複実行されない証拠 |

## 1. Release artifactを検証する

```bash
sha256sum responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
sha256sum responsibility_pathway_runtime-0.1.0a2.tar.gz
```

manifestとdigestまたはsizeが異なるartifactはinstallしないでください。

## 2. 隔離環境を作る

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
```

## 3. Command surfaceを確認する

```bash
rpr --help
python -m responsibility_pathway_runtime --help
```

## 4. 影響のないlocal rehearsalを行う

使い捨てdirectoryとsynthetic dataを使用し、pathwayとauthorityの登録、Human Gateへの到達、execution attemptの永続化、独立readback evidenceの関連付け、restart後の未解決state復元、repairまたはreconciliationへの遷移を確認します。

最初からproduction credential、customer data、不可逆action、独立readbackできないremote writeを使用しないでください。

## Environment記録

| 分類 | 記録項目 |
|---|---|
| Runtime | OS、architecture、Python・pip version |
| Artifact | 入手元、version、Freeze ID、digest |
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
