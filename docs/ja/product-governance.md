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
3. 実装完了とみなす前に、影響を受ける製品surfaceをすべて特定する。
4. Pull Requestの正確なHEADに対してRPR CIを実行し、evidenceをreviewする。
5. 承認済み変更をRPR `main`へmergeする。
6. mainのreadbackを行い、必要なRelease Candidateは修復済みmain系譜から再構築する。
7. Issueをcloseまたは関連付けし、必要に応じてRPR Releaseへ含める。

Security脆弱性は公開Issueではなく、`SECURITY.md`に定める非公開報告経路を使用します。

## Cross-surface semantic driftの再発防止

RPRは複数surfaceからなる製品です。state、decision、route、authority境界、evidenceの意味、owner、external effect claim、release identityの変更は、source code以外にも影響します。

完了前に、該当する次のsurfaceを確認します。

- runtime sourceとserialization
- persistenceとrestart/recovery behavior
- unit / component test
- integration / product / system E2E test
- MCP、CLI、その他のpublic interface
- 英語・日本語の文書pair
- siteと実行可能demo
- claim / test / assurance / integration registry
- formal modelのscopeとnon-claim
- CI drift checkとrelease validation

Local testがGREENでも、これらのsurfaceが整合している証拠にはなりません。変更種別によって生じるstaleまたはmissing surfaceをCIが検出できない場合は、release promotion前に検査を追加します。

過去のRelease記録はhistorical recordとして保持します。Current-state検査のために過去の事実を書き換えず、active product documentとhistorical/release-specific recordを区別します。

## Responsibility Routingの境界

Human Returnは限定されたResponsibility Routeであり、fail-closed一般の意味ではありません。

Generic evaluator failure、不正route、利用不能receiver、未解決external effectから、人間destinationを自動生成してはなりません。Eligible receiverがまだ成立していない場合、neutral holdは正当な状態です。

Evidence transfer、capability、confidence、successful transport、recovered state、route selectionはAuthorityを生成しません。Routingは未解決residueとResidual Ownerを保持し、ownershipを変える場合は明示的かつ認可された再設計を必要とします。

## Release Candidateの整合性

Release Candidateのevidenceは、その正確なsource lineageにbindされます。Candidate freeze後にsource、文書、test、claim registry、CI controlが変わった場合、旧candidateをそのままpatchしてevidenceが有効なままと扱ってはなりません。修復済み`main`からfresh candidateを再構築し、exact-head validationを再実行し、新しいHuman Gate判断を取得します。

## Responsibility Pathway Programへのエスカレーション

通常の不具合修整と限定的な製品拡張は、RPR内で完結させます。

次のようなprogram-levelの理論または責任境界を変更する提案は、Responsibility Pathway Programへエスカレーションします。

- Responsibility RoutingまたはHuman Gateの意味
- RPD・RPE・RPR間の責任分離
- 正本pathway stateまたはtransitionの意味
- residual ownershipの意味
- assuranceまたは公開主張の境界

Program-levelの判断が採用された後も、実装はRPR Pull Requestへ戻します。製品codeの正本はRPRのままです。

## Carryback

RPRのRelease結果、evidence summary、design escalationの判断結果はResponsibility Pathway Programへcarrybackできます。ただしcarryback記録によって、Program repository内のsnapshotが製品正本へ戻ることはありません。
