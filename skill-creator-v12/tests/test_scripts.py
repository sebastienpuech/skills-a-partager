#!/usr/bin/env python3
"""
Automated test suite for skill-creator-v10 scripts.

Compatible with both pytest (`pytest tests/`) and direct execution (`python tests/test_scripts.py`).

Tests:
1. gate_check.py correctly parses skill_lint.py JSON output
2. skill_lint.py imports work and produce valid JSON
3. benchmark_helpers.py correctly identifies with_skill/without_skill configs
4. utils.py parses frontmatter correctly
5. quick_validate.py validates skill structure
6. package_skill.py excludes correct files
7. lint_checks individual check functions
8. SKILL.md v10 content integrity
9. gate_check.py stagnation gate behavior
10. Integration: gate_check → skill_lint → lint_checks end-to-end
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR.parent))


# ────────────────────────────────────────────
# Helper: create minimal valid skill dir
# ────────────────────────────────────────────

def _make_skill_dir(tmpdir, name="test-skill", extra_content="", self_diag=True):
    """Create a minimal valid skill directory for testing."""
    skill_dir = Path(tmpdir) / name
    skill_dir.mkdir(exist_ok=True)
    diag = "\nSelf-diagnosis: check outputs.\n" if self_diag else ""
    (skill_dir / "SKILL.md").write_text(f"""---
name: {name}
description: >
  Use this skill whenever the user wants to test something. Also trigger when user says test.
---

# {name}

Does testing.{diag}{extra_content}
""")
    return skill_dir


# ────────────────────────────────────────────
# 1. skill_lint.py JSON output format
# ────────────────────────────────────────────

def test_skill_lint_json_output_is_list_of_dicts_with_correct_keys():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = _make_skill_dir(tmpdir)
        from skill_lint import lint_skill
        results = lint_skill(skill_dir)

        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert len(results) > 0, "No results returned"

        for r in results:
            assert isinstance(r, dict), f"Expected dict, got {type(r)}"
            assert "category" in r, f"Missing 'category' key: {r}"
            assert "label" in r, f"Missing 'label' key: {r}"
            assert "passed" in r, f"Missing 'passed' key: {r}"
            assert "message" in r, f"Missing 'message' key: {r}"
            assert isinstance(r["passed"], bool), f"'passed' should be bool, got {type(r['passed'])}"


def test_skill_lint_json_cli_output_is_valid_json_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = _make_skill_dir(tmpdir)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "skill_lint.py"), str(skill_dir), "--json"],
            capture_output=True, text=True
        )
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, list), f"Expected list, got {type(parsed)}"


# ────────────────────────────────────────────
# 2. gate_check.py correctly parses lint output
# ────────────────────────────────────────────

def test_gate_check_parses_lint_json_list_format():
    """Verify the CRITICAL bug fix: gate_check must handle list output, not dict with 'checks' key."""
    lint_output = json.dumps([
        {"category": "STRUCTURE", "label": "SKILL.md exists", "passed": True, "message": "OK"},
        {"category": "SIZE", "label": "Line count", "passed": False, "message": "Too big"},
    ])
    parsed = json.loads(lint_output)
    assert isinstance(parsed, list), "Should be a list"
    fails = [c for c in parsed if not c.get("passed", True)]
    assert len(fails) == 1, f"Expected 1 failure, got {len(fails)}"
    assert fails[0]["label"] == "Line count"


def test_gate_check_does_not_silently_pass_on_json_decode_error():
    """Old bug: JSONDecodeError was caught and ignored, making GATE 1 dead code."""
    source = (SCRIPTS_DIR / "gate_check.py").read_text()
    # After the except (json.JSONDecodeError, TypeError) block, there must be a return False
    after_except = source.split("except (json.JSONDecodeError")[1].split("def ")[0]
    assert "return False" in after_except, \
        "JSONDecodeError handler should return False, not silently pass"


def test_gate_check_stagnation_returns_false_when_file_missing():
    """Gate 4 must NOT silently pass when stagnation_check.json is absent."""
    from gate_check import check_stagnation
    with tempfile.TemporaryDirectory() as tmpdir:
        result = check_stagnation(tmpdir)
        assert result is False, "check_stagnation should return False when file is missing"


def test_gate_check_assertions_gate_exists():
    """gate_check.py must have a gate for assertions_are_sufficient."""
    source = (SCRIPTS_DIR / "gate_check.py").read_text()
    assert "assertions" in source.lower(), "gate_check.py must have an assertions gate"
    assert "assertions_are_sufficient" in source, "gate_check.py must check assertions_are_sufficient field"


# ────────────────────────────────────────────
# 3. benchmark_helpers.py config detection
# ────────────────────────────────────────────

def test_benchmark_helpers_identifies_with_skill_as_primary():
    from benchmark_helpers import aggregate_results
    results = {
        "with_skill": [
            {"pass_rate": 0.9, "time_seconds": 10.0, "tokens": 500},
            {"pass_rate": 0.8, "time_seconds": 12.0, "tokens": 600},
        ],
        "without_skill": [
            {"pass_rate": 0.5, "time_seconds": 8.0, "tokens": 400},
            {"pass_rate": 0.6, "time_seconds": 9.0, "tokens": 450},
        ],
    }
    summary = aggregate_results(results)
    delta = summary["delta"]
    assert float(delta["pass_rate"]) > 0, f"Delta should be positive, got {delta['pass_rate']}"


def test_benchmark_helpers_no_well_skill_typo():
    source = (SCRIPTS_DIR / "benchmark_helpers.py").read_text()
    assert "well_skill" not in source, "Typo 'well_skill' still present!"


def test_benchmark_helpers_handles_hyphenated_config_name():
    from benchmark_helpers import aggregate_results
    results = {
        "with-skill": [
            {"pass_rate": 0.9, "time_seconds": 10.0, "tokens": 500},
        ],
        "without_skill": [
            {"pass_rate": 0.5, "time_seconds": 8.0, "tokens": 400},
        ],
    }
    summary = aggregate_results(results)
    delta = summary["delta"]
    assert float(delta["pass_rate"]) > 0, f"Delta should be positive, got {delta['pass_rate']}"


def test_benchmark_helpers_warnings_use_correct_keys():
    """Warnings must use primary_key/baseline_key, not arbitrary configs[0]/configs[1]."""
    from benchmark_helpers import aggregate_results
    # Use dict ordering where configs[0] != primary_key
    results = {
        "without_skill": [
            {"pass_rate": 0.5, "time_seconds": 8.0, "tokens": 400},
        ],
        "with_skill": [],  # Empty — should trigger warning about primary, not baseline
    }
    summary = aggregate_results(results)
    warnings = summary.get("warnings", [])
    # If there are warnings about empty runs, they should reference the correct config
    for w in warnings:
        if "No" in w and "runs" in w:
            assert "with_skill" in w, f"Warning should reference 'with_skill' (primary), got: {w}"


# ────────────────────────────────────────────
# 4. utils.py frontmatter parsing
# ────────────────────────────────────────────

def test_utils_parse_skill_md_extracts_name_and_description():
    from utils import parse_skill_md
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: >
  Does cool stuff.
---

# My Skill
Content here.
""")
        name, desc, content = parse_skill_md(skill_dir)
        assert name == "my-skill", f"Expected 'my-skill', got '{name}'"
        assert "cool stuff" in desc, f"Description missing 'cool stuff': '{desc}'"
        assert "# My Skill" in content


def test_utils_parse_skill_md_raises_on_missing_frontmatter():
    from utils import parse_skill_md
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter\nJust content.")
        try:
            parse_skill_md(skill_dir)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected


# ────────────────────────────────────────────
# 5. quick_validate.py
# ────────────────────────────────────────────

def test_quick_validate_accepts_valid_skill():
    from quick_validate import validate_skill
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = _make_skill_dir(tmpdir, "valid-skill")
        valid, msg = validate_skill(skill_dir)
        assert valid, f"Should be valid: {msg}"


def test_quick_validate_rejects_missing_name():
    from quick_validate import validate_skill
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\ndescription: Missing name field.\n---\n# Bad")
        valid, msg = validate_skill(skill_dir)
        assert not valid, "Should be invalid"
        assert "name" in msg.lower()


def test_quick_validate_rejects_angle_brackets():
    from quick_validate import validate_skill
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: bad-skill\ndescription: Has <angle> brackets.\n---\n# Bad")
        valid, msg = validate_skill(skill_dir)
        assert not valid, "Should reject angle brackets"


# ────────────────────────────────────────────
# 6. package_skill.py exclusions
# ────────────────────────────────────────────

def test_package_skill_excludes_pycache_and_ds_store():
    from package_skill import should_exclude
    assert should_exclude(Path("my-skill/__pycache__/foo.pyc"))
    assert should_exclude(Path("my-skill/.DS_Store"))
    assert should_exclude(Path("my-skill/evals/test.json"))  # root-level evals excluded
    assert not should_exclude(Path("my-skill/SKILL.md"))
    assert not should_exclude(Path("my-skill/scripts/main.py"))


# ────────────────────────────────────────────
# 7. lint_checks individual checks
# ────────────────────────────────────────────

def test_lint_checks_frontmatter_detects_missing_fields():
    from lint_checks import check_frontmatter
    passed, msg = check_frontmatter("---\nfoo: bar\n---\n# Content")
    assert not passed, "Should fail on missing name/description"


def test_lint_checks_description_quality_detects_short():
    from lint_checks import check_description_quality
    passed, msg = check_description_quality("---\nname: x\ndescription: short\n---\n")
    assert not passed, "Should fail on short description"


def test_lint_checks_line_count_rejects_over_500():
    from lint_checks import check_line_count
    big_content = "\n".join(["line"] * 501)
    passed, msg = check_line_count(big_content)
    assert not passed, "Should reject >500 lines"


def test_lint_checks_hardcoded_paths():
    from lint_checks import check_no_hardcoded_paths
    passed, msg = check_no_hardcoded_paths("Read from /Users/john/file.txt")
    assert not passed


def test_lint_checks_self_diagnosis():
    from lint_checks import check_self_diagnosis
    passed, _ = check_self_diagnosis("## Self-diagnosis\nCheck outputs.")
    assert passed
    passed2, _ = check_self_diagnosis("No guardrails here.")
    assert not passed2


def test_lint_checks_yaml_import_is_top_level():
    """yaml must be imported at module level, not inside a function."""
    source = (SCRIPTS_DIR / "lint_checks.py").read_text()
    # Check that 'import yaml' appears before the first 'def '
    import_pos = source.find("import yaml")
    first_def = source.find("\ndef ")
    assert import_pos < first_def, \
        f"'import yaml' at position {import_pos} should come before first function def at {first_def}"


# ────────────────────────────────────────────
# 8. SKILL.md v10 content checks
# ────────────────────────────────────────────

def test_skill_md_contains_critical_guardrails_inline():
    import re
    skill_md = (SCRIPTS_DIR.parent / "SKILL.md").read_text()
    checks = [
        ("with_skill", "Directory naming convention"),
        ("without_skill", "Directory naming convention"),
        ("assertions_are_sufficient", "assertions_are_sufficient gate"),
        ("Baseline validation", "Baseline validation section"),
        ("Idempoten", "Idempotency reminder"),
        ("adversarial", "Adversarial QA mention"),
        ("text.*passed.*evidence", "Grading field names"),
        ("EVALUATION.*mandatory|mandatory.*EVALUATION", "Adversarial QA mandatory for EVALUATION"),
        ("debug", "Debug section"),
    ]
    for pattern, label in checks:
        assert re.search(pattern, skill_md, re.IGNORECASE), \
            f"SKILL.md missing critical guardrail: {label} (pattern: {pattern})"


def test_skill_md_says_v12():
    skill_md = (SCRIPTS_DIR.parent / "SKILL.md").read_text()
    assert "skill-creator-v12" in skill_md, "Name should be skill-creator-v12"
    assert "# Skill Creator v12" in skill_md, "Title should say v12"
    assert "v1 through v11" in skill_md, "Should mention superseding v1-v11"


def test_skill_md_has_guardrails_by_task_type_inline():
    """v7 regression: SKILL.md must have at least a summary of guardrails per task type."""
    skill_md = (SCRIPTS_DIR.parent / "SKILL.md").read_text().lower()
    for task_type in ["evaluation", "transformation", "generation", "analysis"]:
        assert task_type in skill_md, f"SKILL.md missing task type '{task_type}'"


def test_skill_md_has_gate3_enforcement_reminder():
    """v7 regression: must remind to run gate_check before modifying skill."""
    skill_md = (SCRIPTS_DIR.parent / "SKILL.md").read_text()
    assert "feedback.json" in skill_md, "Must mention feedback.json"
    assert "gate_check" in skill_md, "Must mention gate_check.py for enforcement"


# ────────────────────────────────────────────
# 9. run_eval.py / run_loop.py claude CLI check
# ────────────────────────────────────────────

def test_run_eval_checks_for_claude_cli():
    """run_eval.py should verify claude CLI is available before trying to use it."""
    source = (SCRIPTS_DIR / "run_eval.py").read_text()
    assert "shutil.which" in source or "which" in source or "claude" in source.split("def ")[0], \
        "run_eval.py should check for claude CLI availability"


# ────────────────────────────────────────────
# 10. Integration: end-to-end lint on itself
# ────────────────────────────────────────────

def test_skill_lint_runs_on_v10_itself_without_crashes():
    skill_dir = SCRIPTS_DIR.parent
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "skill_lint.py"), str(skill_dir), "--json"],
        capture_output=True, text=True,
        cwd=str(SCRIPTS_DIR)
    )
    assert result.returncode is not None, "Process should complete"
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, list), f"Expected list, got {type(parsed)}"
    for r in parsed:
        assert "passed" in r, f"Result missing 'passed': {r}"


def test_gate_check_preflight_passes_on_v10():
    """End-to-end: gate_check preflight must pass on skill-creator-v10 itself."""
    skill_dir = str(SCRIPTS_DIR.parent)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "gate_check.py"), skill_dir, "--gate", "preflight"],
        capture_output=True, text=True,
        cwd=str(SCRIPTS_DIR)
    )
    assert result.returncode == 0, f"gate_check preflight failed: {result.stdout}\n{result.stderr}"


# ────────────────────────────────────────────
# Runner: compatible with both pytest and direct execution
# ────────────────────────────────────────────

if __name__ == "__main__":
    passed = 0
    failed = 0
    errors = []

    # Collect all test_* functions defined in this module
    test_functions = [
        (name, obj) for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]

    for name, fn in test_functions:
        try:
            fn()
            passed += 1
            print(f"  [PASS] {name}")
        except AssertionError as e:
            failed += 1
            errors.append(f"{name}: {e}")
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            failed += 1
            errors.append(f"{name}: CRASHED: {e}")
            print(f"  [FAIL] {name}: CRASHED: {e}")

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed out of {total} tests")
    print(f"{'='*60}")

    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")

    sys.exit(1 if failed > 0 else 0)
