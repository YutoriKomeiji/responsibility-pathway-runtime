<!-- language: en -->

# EU AI Act Article 50 transparency profile

RPR provides an optional, fail-closed integration profile for recording and enforcing transparency controls declared by an integrating organisation.

It does not determine legal scope, provide legal advice, certify compliance, sign the EU Code of Practice, or generate a conformity declaration.

The profile can require evidence for:

- disclosure that a person is interacting with AI;
- machine-readable marking of AI-generated or manipulated content;
- visible disclosure for deepfakes and proportionate disclosure for artistic or fictional content;
- visible disclosure for public-interest text unless human review/editorial control and a named editorial-responsibility owner are recorded;
- a Human Gate before publication or deployment.

Unknown territorial scope, actor role, content classification, or missing evidence remains blocked. A successful generation, upload, publication, or tool response is not transparency evidence.

Run the sample:

```bash
python examples/eu_article50_transparency.py
```

The reference legal basis is Article 50 of Regulation (EU) 2024/1689 and the European Commission guidance published in July 2026. Integrators must review current law, guidance, standards, market-surveillance expectations, and their own facts before relying on the profile.
