# Language: Python
# Purpose: Demonstrate bounded Article 50 transparency decisions.
# Boundary: Examples are integration aids, not legal advice or compliance certification.

from dataclasses import asdict
import json

from rpr.eu_ai_act_article50 import (
    ActorRole,
    Article50Assessment,
    ContentContext,
    ContentModality,
    SystemFunction,
    TerritorialScope,
    evaluate_article50,
)


LEGAL_BASIS = "EU-AI-ACT-ARTICLE-50-2026-08-02"


def show(name: str, record: Article50Assessment) -> None:
    decision = evaluate_article50(record)
    print(json.dumps({"case": name, "decision": asdict(decision)}, ensure_ascii=False, indent=2))


def main() -> None:
    show(
        "eu_chatbot_with_disclosure",
        Article50Assessment(
            assessment_id="case-chatbot",
            assessed_at="2026-08-04T16:30:00+09:00",
            legal_basis_version=LEGAL_BASIS,
            territorial_scope=TerritorialScope.EU_IN_SCOPE,
            actor_role=ActorRole.PROVIDER,
            system_function=SystemFunction.INTERACTIVE_AI,
            interaction_disclosure_present=True,
            responsible_owner="product-owner",
        ),
    )

    show(
        "deepfake_video_missing_label",
        Article50Assessment(
            assessment_id="case-deepfake",
            assessed_at="2026-08-04T16:30:00+09:00",
            legal_basis_version=LEGAL_BASIS,
            territorial_scope=TerritorialScope.EU_IN_SCOPE,
            actor_role=ActorRole.BOTH,
            system_function=SystemFunction.GENERATIVE_CONTENT,
            content_modality=ContentModality.VIDEO,
            content_context=ContentContext.DEEPFAKE,
            machine_readable_mark_present=True,
            visible_label_present=False,
            responsible_owner="media-owner",
        ),
    )

    show(
        "public_interest_text_with_editorial_control",
        Article50Assessment(
            assessment_id="case-reviewed-text",
            assessed_at="2026-08-04T16:30:00+09:00",
            legal_basis_version=LEGAL_BASIS,
            territorial_scope=TerritorialScope.EU_IN_SCOPE,
            actor_role=ActorRole.DEPLOYER,
            system_function=SystemFunction.GENERATIVE_CONTENT,
            content_modality=ContentModality.TEXT,
            content_context=ContentContext.PUBLIC_INTEREST_TEXT,
            human_review_completed=True,
            editorial_responsibility_owner="Akihisa Ono",
            responsible_owner="Akihisa Ono",
        ),
    )

    show(
        "unresolved_eu_scope",
        Article50Assessment(
            assessment_id="case-unresolved",
            assessed_at="2026-08-04T16:30:00+09:00",
            legal_basis_version=LEGAL_BASIS,
            territorial_scope=TerritorialScope.UNRESOLVED,
            actor_role=ActorRole.UNRESOLVED,
            system_function=SystemFunction.UNRESOLVED,
            content_modality=ContentModality.UNRESOLVED,
            content_context=ContentContext.UNRESOLVED,
            residual_uncertainty="EU availability and deployer role require legal classification",
            responsible_owner="legal-owner",
        ),
    )


if __name__ == "__main__":
    main()
