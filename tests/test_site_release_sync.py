# Language: Python
# Purpose: Prevent public GitHub Pages release labels and demo wheel references from drifting from pyproject.toml.
# Boundary: Static consistency test only; it does not publish, tag, or alter runtime behavior.

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def current_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_public_pages_release_version_matches_package() -> None:
    version = current_version()
    expected_tag = f"v{version}"

    english = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    japanese = (ROOT / "site" / "ja.html").read_text(encoding="utf-8")
    demo = (ROOT / "site" / "demo.html").read_text(encoding="utf-8")
    demo_js = (ROOT / "site" / "demo.js").read_text(encoding="utf-8")

    assert f"Public Alpha · {version}" in english
    assert f"<dd>{version}</dd>" in english
    assert expected_tag in english
    assert f"responsibility-pathway-runtime=={version}" in english

    assert f"Public Alpha {version}" in japanese
    assert f"<dd>{version}</dd>" in japanese
    assert expected_tag in japanese
    assert f"responsibility-pathway-runtime=={version}" in japanese

    assert f"Public Alpha {version}" in demo
    assert f"responsibility_pathway_runtime-{version}-py3-none-any.whl" in demo_js
