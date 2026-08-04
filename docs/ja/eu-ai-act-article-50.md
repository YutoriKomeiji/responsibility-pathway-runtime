<!-- language: ja -->

# EU AI Act Article 50 透明性プロファイル

RPRは、連携組織が宣言した透明性controlを記録し、fail-closedで強制するための任意integration profileを提供します。

RPRは、法的適用範囲の決定、法律助言、適合認証、EU Code of Practiceへの署名、適合宣言の作成を行いません。

このprofileでは、次の証拠を要求できます。

- 人がAIと対話していることの告知
- AI生成・加工contentのmachine-readable marking
- deepfakeの明示表示、および芸術・創作・風刺・fiction等における適切で比例的な表示
- 公共的関心事項を扱うtextについて、人間review／editorial controlと編集責任者が記録されない場合の明示表示
- 公開またはdeployment前のHuman Gate

法域、actor role、content分類が不明な場合、または必要証拠が欠ける場合はblockedのままです。生成、upload、公開、tool callの成功応答だけでは透明性証拠になりません。

sample実行:

```bash
python examples/eu_article50_transparency.py
```

参照法源はRegulation (EU) 2024/1689 Article 50、および2026年7月に公表されたEuropean Commission guidanceです。integratorは、このprofileへ依存する前に、最新法令、guideline、standard、market-surveillance要件、自組織の事実関係を確認する必要があります。
