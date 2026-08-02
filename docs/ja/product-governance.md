<!--
Document Title: RPR Product Governance Japanese
Document Type: Public Product Operations Policy
Status: Active
Header Language: English
Body Language: Japanese
-->

# RPR製品運用方針

## 製品実装の正本

`YutoriKomeiji/responsibility-pathway-runtime`を、RPR製品実装の唯一の正本とします。

次の対象はRPRで管理します。

- ランタイムsourceとtests
- package metadataとRelease artifact
- 公開仕様と製品文書
- 英語・日本語の製品page
- CI、Issue Forms、Security Policy、Changelog、Release記録
- 利用者からのIssueと実装修整Pull Request

製品修整を、別repositoryの準備snapshotだけへ適用してはなりません。

## 通常の変更経路

利用者の指摘や不具合は、次の経路で処理します。

1. RPR Issueを作成またはtriageする。
2. RPR上でbranchとPull Requestを作成する。
3. RPR CIとreview evidenceを確認する。
4. 承認済み変更をRPR `main`へmergeする。
5. Issueをcloseまたは関連付けし、必要に応じてRPR Releaseへ含める。

Security脆弱性は公開Issueではなく、`SECURITY.md`に定める非公開報告経路を使用します。

## Responsibility Pathway Programへのエスカレーション

通常の不具合修整と限定的な製品拡張は、RPR内で完結させます。

次のようなprogram-levelの理論または責任境界を変更する提案は、Responsibility Pathway Programへエスカレーションします。

- Human Gateの意味
- RPD・RPE・RPR間の責任分離
- 正本pathway stateまたはtransitionの意味
- residual ownershipの意味
- assuranceまたは公開主張の境界

Program-levelの判断が採用された後も、実装はRPR Pull Requestへ戻します。製品codeの正本はRPRのままです。

## Carryback

RPRのRelease結果、evidence summary、design escalationの判断結果はResponsibility Pathway Programへcarrybackできます。ただしcarryback記録によって、Program repository内のsnapshotが製品正本へ戻ることはありません。
