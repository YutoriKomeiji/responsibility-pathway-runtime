# Release version coherence

Status: active release rule

## Core rule

RPR prepares the **next release version before external publication**.

When a release candidate version `X` is selected, version-bearing active/current-facing surfaces move to `X` during release preparation. PyPI publication is the final distribution action for an already-coherent release identity; it is not the step that creates that identity.

```text
next_release_version
== pyproject version
== active documentation version
== package long-description version
== current site version
```

Publication state is separate from release identity.

Before publication, active surfaces may say `release candidate` / `not yet published`, but they must not keep the previous public version as their own active document identity.

## Required order

1. Select the next version `X`.
2. Move `pyproject.toml`, active README/docs/site surfaces, package long description, and every other version-bearing current surface to `X`.
3. Keep candidate/publication wording explicit: `X` is not yet published.
4. Run lifecycle, package metadata, public-export, formal-scope, bilingual documentation, and exact-head validation.
5. Inspect the built wheel/sdist metadata and rendered long description.
6. Obtain the Human Gate for the public release identity.
7. Create the exact tag / GitHub prerelease and read it back.
8. Publish the already-verified distribution to PyPI.
9. Read PyPI back independently.
10. Change only publication-state facts and wording after successful public readback.
11. Reconcile all current surfaces and preserve historical evidence unchanged.

## Fail-closed checks

Release preparation must fail if:

- `pyproject.toml` identifies `X` while an active version-bearing README/docs/site surface still identifies the previous version as its own current identity;
- the package long description does not identify `X`;
- candidate wording claims `X` is already published;
- a version-bearing assurance/evidence surface disagrees with `X`;
- exact-head artifacts cannot be tied to the validated source revision.

Historical release manifests, frozen evidence, changelog history, regression fixtures, and explicit statements such as “X preserves behavior from Y” are allowed to retain older version identifiers.

## Why this exists

RPR already added package long-description validation after an earlier stale-PyPI-description incident. RPOS later reproduced the same broader class of failure at another release boundary: package identity advanced while some current-facing version surfaces still reflected the previous public version.

The prevention rule is therefore broader than PyPI metadata validation:

**future release identity first; publication second.**

This file does not authorize a release. Tags, GitHub Releases, PyPI publication, and strong readiness claims remain Human-Gated.
