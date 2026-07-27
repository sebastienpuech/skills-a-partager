"""Shared utilities for skill-creator scripts."""

import re
from pathlib import Path


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content).

    Uses yaml.safe_load for robust frontmatter parsing instead of manual
    line-by-line parsing. Falls back to regex extraction if PyYAML is
    unavailable (shouldn't happen, but defensive).
    """
    content = (skill_path / "SKILL.md").read_text()

    # Extract raw frontmatter block
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m:
        raise ValueError("SKILL.md missing frontmatter (no opening/closing ---)")

    frontmatter_raw = m.group(1)

    try:
        import yaml
        fm = yaml.safe_load(frontmatter_raw)
        if not isinstance(fm, dict):
            raise ValueError("Frontmatter is not a YAML mapping")
        name = str(fm.get("name", ""))
        description = str(fm.get("description", ""))
    except ImportError:
        # Fallback: simple regex extraction (no PyYAML available)
        name_match = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', frontmatter_raw, re.MULTILINE)
        name = name_match.group(1) if name_match else ""
        desc_match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', frontmatter_raw, re.MULTILINE)
        description = desc_match.group(1) if desc_match else ""

    return name, description, content
