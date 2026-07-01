#!/usr/bin/env python3
"""
Skill Linter — deep structural validation for skills.

Goes beyond quick_validate.py to verify the skill follows architecture guidelines.

Usage:
    python skill_lint.py <skill_directory>
    python skill_lint.py <skill_directory> --json   # machine-readable output
"""

import sys
import json
from pathlib import Path
import inspect

# Robust import: works both as `python scripts/skill_lint.py` (bare import)
# and as `python -m scripts.skill_lint` (package import).
try:
    from scripts.lint_checks import (
        check_skill_md_exists, check_frontmatter, check_description_quality,
        check_description_scope, check_line_count, check_script_sizes,
        check_context_budget, check_inline_data_blocks, check_self_diagnosis,
        check_circuit_breakers, check_circuit_breaker_quality,
        check_references_linked, check_examples_structure,
        check_agents_have_instructions, check_architecture_documented,
        check_eval_schema, check_no_hardcoded_paths,
    )
except ImportError:
    from lint_checks import (
        check_skill_md_exists, check_frontmatter, check_description_quality,
        check_description_scope, check_line_count, check_script_sizes,
        check_context_budget, check_inline_data_blocks, check_self_diagnosis,
        check_circuit_breakers, check_circuit_breaker_quality,
        check_references_linked, check_examples_structure,
        check_agents_have_instructions, check_architecture_documented,
        check_eval_schema, check_no_hardcoded_paths,
    )

ALL_CHECKS = [
    ("STRUCTURE", "SKILL.md exists", check_skill_md_exists),
    ("FRONTMATTER", "Valid frontmatter", check_frontmatter),
    ("DESCRIPTION", "Description quality", check_description_quality),
    ("DESCRIPTION", "Description-scope alignment", check_description_scope),
    ("SIZE", "Line count", check_line_count),
    ("SIZE", "Script sizes (CB-5)", check_script_sizes),
    ("SIZE", "Context budget (CB-7)", check_context_budget),
    ("SIZE", "Inline data blocks (CB-8)", check_inline_data_blocks),
    ("GUARDRAILS", "Self-diagnosis present", check_self_diagnosis),
    ("GUARDRAILS", "Circuit-breakers in scripts", check_circuit_breakers),
    ("GUARDRAILS", "Circuit-breaker quality", check_circuit_breaker_quality),
    ("REFERENCES", "References linked", check_references_linked),
    ("EXAMPLES", "Examples structure", check_examples_structure),
    ("AGENTS", "Agent instructions", check_agents_have_instructions),
    ("ARCHITECTURE", "Architecture documented", check_architecture_documented),
    ("EVALS", "Eval schema", check_eval_schema),
    ("PORTABILITY", "No hardcoded paths", check_no_hardcoded_paths),
]


def lint_skill(skill_path: Path) -> list[dict]:
    results = []
    content = ""
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()

    for category, label, check_fn in ALL_CHECKS:
        try:
            params = inspect.signature(check_fn).parameters
            param_names = list(params.keys())

            if param_names == ["skill_path"]:
                passed, msg = check_fn(skill_path)
            elif param_names == ["content"]:
                passed, msg = check_fn(content)
            elif param_names == ["skill_path", "content"]:
                passed, msg = check_fn(skill_path, content)
            else:
                passed, msg = False, f"Unknown check signature: {param_names}"
        except Exception as e:
            passed, msg = False, f"Check crashed: {e}"

        results.append({
            "category": category,
            "label": label,
            "passed": passed,
            "message": msg,
        })

    return results


def print_results(results: list[dict], as_json: bool = False):
    if as_json:
        print(json.dumps(results, indent=2))
        return

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  Skill Lint Results: {passed}/{total} checks passed")
    print(f"{'='*60}\n")

    for r in results:
        icon = "PASS" if r["passed"] else "FAIL"
        print(f"  [{icon}] [{r['category']}] {r['label']}")
        print(f"         {r['message']}")
        print()

    if passed == total:
        print("  All checks passed!")
    else:
        failed = [r for r in results if not r["passed"]]
        print(f"  {len(failed)} issue(s) to address.")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skill_lint.py <skill_directory> [--json]")
        sys.exit(1)

    skill_dir = Path(sys.argv[1])
    as_json = "--json" in sys.argv

    if not skill_dir.is_dir():
        print(f"Error: {skill_dir} is not a directory")
        sys.exit(1)

    results = lint_skill(skill_dir)
    print_results(results, as_json)

    all_passed = all(r["passed"] for r in results)
    sys.exit(0 if all_passed else 1)
