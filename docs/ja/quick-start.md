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

## 1. Release artifactを検証する

ファイル名、byte数、SHA-256 digestを[`release-manifest.json`](../../release-manifest.json)と照合します。

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

## 4. 影響のないlocal rehearsalから始める

使い捨てdirectoryとsynthetic dataを使用し、host applicationが次を実行できることを確認します。

1. pathwayと宣言済みauthorityを登録する。
2. Human Gateを迂回せず到達する。
3. execution attemptを作成し永続化する。
4. 独立readback evidenceを関連付ける。
5. 未解決effectを再送せずrestart後に再開する。
6. completionを確定できない場合にrepairまたはreconciliationを公開する。

最初からproduction credential、customer data、不可逆action、独立readbackできないremote writeを使用しないでください。

## 5. Environmentを記録する

最低限、OSとarchitecture、Python/pip version、install元とartifact digest、RPR versionとFreeze ID、host framework、network/proxy/TLS/identity/credential構成、実行command、期待結果、実結果、secret除去済みlogを保存します。

## 6. Field evidenceを報告する

再現可能な成功・失敗試験はenvironment-report Issue formへ、product defectはbug formへ、framework/service要望はintegration formへ、脆弱性は`SECURITY.md`のprivate routeへ報告します。

## 停止条件

authorityがない、独立readback sourceが使えない、credential露出の可能性がある、external effectが曖昧、pathwayを復元できない、または次のactionが明示的な人間承認なしに不可逆となる場合はrehearsalを停止してください。
