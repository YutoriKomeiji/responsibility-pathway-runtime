<!--
Document Title: RPR Security・Integration・API境界
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: Japanese
Body Language: Japanese
-->

# Security、integration、API境界

## Security model

RPRはcontrolとevidenceのcomponentであり、完全なsecurity perimeterではありません。authenticated user/service、least-privilege credential、network policy、endpoint allow-list、保護されたpersistence、log redaction、software supply-chain control、operational monitoringを提供するhost architecture内へ配置します。

## Trust boundaries

次を別々のtrust domainとして扱います。

- humanまたはinstitutional authority
- host application
- RPR state/evidence store
- adapter process
- credential/secret store
- remote system
- independent readback source
- optional RPE decision service

あるdomainのresultを、別domainが所有するevidenceへ暗黙代入してはいけません。特にadapter return valueは自動的に独立readbackにはなりません。

## Integration contract

各integrationは次を定義します。

- accepted action/actor schema
- authorityとHuman Gate要件
- stable operation/idempotency identity
- permitted state transition
- dispatch timeout/cancellation behavior
- authoritative readback sourceとmatching rule
- ambiguous-write handling
- repair、resume、reconciliation owner
- data classification、retention、deletion rule
- observabilityとincident route

## API stability

`0.1.0a2`はpublic alphaです。integratorはversionをpinし、upgrade前にserialized state、CLI behavior、adapter configuration、migration procedureを検証してください。alpha releaseではsafetyまたはevidence semanticsを守るため非互換修正が入る場合があります。

## Credentials

RPRのdocumentationとexampleはplaceholderを使用します。credentialは外部secret mechanismから供給し、許可operationの最小範囲へ制限します。pathway evidence、exception message、diagnostic bundle、public Issue、release artifactへsecretを入れてはいけません。

## Bypass prevention

同じ重大operationに対し、pathway controlを迂回する第二execution pathをhost applicationが公開してはいけません。direct adapter invocation、alternate endpoint、debug mode、restart pathがrequired admission/evidence handlingを暗黙迂回しないことをtestで示してください。

## Vulnerability reporting

exploit可能なsecurity detailをpublic Issueへ投稿しないでください。[`SECURITY.md`](../../SECURITY.md)のprivate reporting routeを使用します。
