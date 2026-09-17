# Release version coherence

Status: active release rule

## 基本ルール

RPRでは、**外部公開より先に次のrelease versionを完成させます**。

release candidate `X` を選んだ時点で、versionを持つactive / current-facing surfaceはrelease準備中に `X` へ揃えます。PyPI publishは、すでに整合・検証済みのrelease identityを配布する最後の操作であり、version identityを作る操作ではありません。

```text
next_release_version
== pyproject version
== active documentation version
== package long-description version
== current site version
```

publication stateとrelease identityは別です。

公開前は `release candidate` / `未公開` と明記しますが、前公開versionをactive document自身のversionとして残しません。

## 必須順序

1. 次version `X` を決める。
2. `pyproject.toml`、active README/docs/site、package long description、その他versionを持つcurrent surfaceを `X` へ揃える。
3. `X` は未公開candidateであることを明示する。
4. lifecycle、package metadata、public export、formal scope、日英document、exact-head validationを実行する。
5. buildされたwheel/sdistのmetadataとrendered long descriptionを確認する。
6. public release identityへのHuman Gateを得る。
7. exact tag / GitHub prereleaseを作成しreadbackする。
8. 検証済みdistributionをPyPIへpublishする。
9. PyPIを独立readbackする。
10. 公開成功後に変更するのはpublication-stateの事実と文言だけにする。
11. current surfaceを再照合し、historical evidenceは書き換えない。

## Fail-closed

次の場合、release準備を失敗扱いにします。

- `pyproject.toml` が `X` なのに、active README/docs/siteが前versionを自身のcurrent identityとして持つ
- package long descriptionが `X` と一致しない
- candidate文書が `X` を公開済みと主張する
- versionを持つassurance/evidence surfaceが `X` と一致しない
- exact-head artifactを検証済みsource revisionへ結び付けられない

historical release manifest、frozen evidence、CHANGELOG履歴、regression fixture、「XはYのbehaviorを維持する」のような明示的な履歴説明は旧versionを保持して構いません。

## 背景

RPRでは以前、PyPI Long Descriptionに旧versionの記述が残る問題を受けてpackage metadata validationを追加しました。その後RPOSでも、package identityだけが先に進み、current-facing version surfaceの一部が前公開versionを保持する同系統の問題が再発しました。

したがって対策はPyPI metadataだけでは不十分です。

**未来versionを先に揃える。公開は最後。**

この文書はrelease authorizationを生成しません。Tag、GitHub Release、PyPI publication、強いreadiness claimは引き続きHuman Gate対象です。
