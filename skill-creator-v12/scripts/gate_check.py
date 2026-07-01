#!/usr/bin/env python3
"""
Mechanical gate enforcement for skill-creator workflow.

Replaces manual verification steps with deterministic checks.
Exits 0 on pass, 1 on failure with actionable error message.

Usage:
  python scripts/gate_check.py <path> --gate preflight
  python scripts/gate_check.py <path> --gate feedback
  python scripts/gate_check.py <path> --gate stagnation
  python scripts/gate_check.py <path> --gate assertions

Gates:
  preflight    - Verify linter passes on a skill directory
  feedback     - Verify feedback.json exists in an iteration directory
  stagnation   - Check for stagnation/regression across iterations
  assertions   - Verify assertions_are_sufficient in grading results
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def check_preflight(skill_dir: str) -> bool:
    """GATE 1+2: Run linter on skill directory."""
    skill_path = Path(skill_dir)
    if not (skill_path / "SKILL.md").exists():
        print(f"ERROR: No SKILL.md found in {skill_dir}")
        return False

    # Find the linter script relative to this script
    scripts_dir = Path(__file__).parent
    linter = scripts_dir / "skill_lint.py"
    if not linter.exists():
        print(f"ERROR: Linter not found at {linter}")
        return False

    result = subprocess.run(
        [sys.executable, str(linter), skill_dir, "--json"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"GATE 1 FAILED: Linter found issues in {skill_dir}")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False

    # Parse JSON output to check for failures.
    # skill_lint.py --json outputs a plain list of dicts, each with
    # keys: category, label, passed (bool), message.
    try:
        lint_result = json.loads(result.stdout)
        if not isinstance(lint_result, list):
            # Defensive: if format changes, wrap in list
            lint_result = [lint_result]
        fails = [c for c in lint_result if not c.get("passed", True)]
        if fails:
            print(f"GATE 1 FAILED: {len(fails)} check(s) failed:")
            for f in fails:
                print(f"  - [{f.get('category', '?')}] {f.get('label', '?')}: {f.get('message', '?')}")
            return False
    except (json.JSONDecodeError, TypeError) as e:
        # If output is not valid JSON, treat as failure (don't silently pass)
        print(f"GATE 1 WARNING: Could not parse linter JSON output: {e}")
        print(f"Raw output: {result.stdout[:500]}")
        return False

    print("GATE 1+2 PASSED: Linter checks passed.")
    return True


def check_feedback(iteration_dir: str) -> bool:
    """GATE 3: Verify feedback.json exists and is valid."""
    feedback_path = Path(iteration_dir) / "feedback.json"

    if not feedback_path.exists():
        print(f"GATE 3 FAILED: No feedback.json found at {feedback_path}")
        print("The human has not reviewed yet. Generate the eval viewer")
        print("and wait for the user to submit their reviews.")
        return False

    try:
        with open(feedback_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"GATE 3 FAILED: feedback.json is invalid: {e}")
        return False

    status = data.get("status", "")
    reviews = data.get("reviews", [])

    if status != "complete":
        print(f"GATE 3 WARNING: feedback status is '{status}', not 'complete'.")

    non_empty = [r for r in reviews if r.get("feedback", "").strip()]
    print(f"GATE 3 PASSED: feedback.json found with {len(reviews)} reviews "
          f"({len(non_empty)} with comments).")
    return True


def check_stagnation(workspace_dir: str) -> bool:
    """GATE 4: Check for stagnation/regression.

    Returns False if stagnation_check.json is missing — this prevents
    silently skipping the gate by not generating the file.
    """
    stag_path = Path(workspace_dir) / "stagnation_check.json"

    if not stag_path.exists():
        print("GATE 4 FAILED: No stagnation_check.json found.")
        print("You must run the stagnation check before proceeding:")
        print("  python -m scripts.aggregate_benchmark "
              f"{workspace_dir}/iteration-N --check-stagnation")
        return False

    try:
        with open(stag_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"GATE 4 ERROR: stagnation_check.json invalid: {e}")
        return False

    pattern = data.get("pattern", "unknown")
    recommendation = data.get("recommendation", "unknown")
    best_rate = data.get("best_pass_rate", 0)
    iterations = data.get("iterations", [])
    current_rate = iterations[-1]["pass_rate"] if iterations else 0

    if pattern == "regressing":
        print(f"GATE 4 FAILED — REGRESSION: Current {current_rate:.0%} "
              f"vs best {best_rate:.0%}.")
        print("Action: Revert to best version before continuing.")
        return False
    elif pattern == "stagnating":
        print(f"GATE 4 WARNING — STAGNATION: Pass rate stuck near "
              f"{current_rate:.0%} for multiple iterations.")
        print("Action: Pivot approach or accept and ship.")
        return True  # Warning, not hard failure
    elif pattern == "oscillating":
        print(f"GATE 4 WARNING — OSCILLATION: Pass rate alternating. "
              f"Current {current_rate:.0%}, best {best_rate:.0%}.")
        print("Action: Add more diverse test cases instead of tweaking.")
        return True
    else:
        print(f"GATE 4 PASSED: Pattern is '{pattern}', "
              f"pass rate {current_rate:.0%}.")
        return True


def check_assertions(iteration_dir: str) -> bool:
    """GATE: Verify assertions_are_sufficient in grading results.

    Scans all grading.json files in the iteration directory. If any
    grading result has assertions_are_sufficient: false, the gate fails.
    This prevents proceeding to skill improvement when the eval assertions
    don't fully cover the test intent.
    """
    iter_path = Path(iteration_dir)
    if not iter_path.exists():
        print(f"ASSERTIONS GATE FAILED: Directory not found: {iteration_dir}")
        return False

    grading_files = list(iter_path.rglob("grading.json"))
    if not grading_files:
        print("ASSERTIONS GATE FAILED: No grading.json files found.")
        print("Run the grader agent first to produce grading results.")
        return False

    insufficient = []
    for gf in grading_files:
        try:
            with open(gf) as f:
                data = json.load(f)
            if not data.get("assertions_are_sufficient", True):
                rel_path = gf.relative_to(iter_path)
                insufficient.append(str(rel_path))
        except (json.JSONDecodeError, IOError) as e:
            print(f"ASSERTIONS GATE WARNING: Could not read {gf}: {e}")
            insufficient.append(f"{gf.name} (unreadable)")

    if insufficient:
        print(f"ASSERTIONS GATE FAILED: {len(insufficient)} grading(s) have "
              f"assertions_are_sufficient: false")
        for path in insufficient:
            print(f"  - {path}")
        print("Action: Add more assertions to cover the eval's intent before proceeding.")
        return False

    # Also validate grading field structure (text, passed, evidence)
    schema_errors = []
    for gf in grading_files:
        try:
            with open(gf) as f:
                data = json.load(f)
            for i, exp in enumerate(data.get("expectations", [])):
                missing = [k for k in ("text", "passed", "evidence") if k not in exp]
                if missing:
                    schema_errors.append(f"{gf.name}[{i}] missing: {', '.join(missing)}")
        except (json.JSONDecodeError, IOError):
            pass  # Already handled above

    if schema_errors:
        print(f"ASSERTIONS GATE WARNING: {len(schema_errors)} expectation(s) have "
              f"malformed fields (must have text, passed, evidence):")
        for err in schema_errors[:5]:
            print(f"  - {err}")
        return False

    print(f"ASSERTIONS GATE PASSED: {len(grading_files)} grading file(s), "
          f"all assertions sufficient, all fields valid.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Mechanical gate checks for skill-creator workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("path", help="Path to check (skill dir or workspace)")
    parser.add_argument("--gate", required=True,
                        choices=["preflight", "feedback", "stagnation", "assertions"],
                        help="Which gate to check")
    args = parser.parse_args()

    gates = {
        "preflight": check_preflight,
        "feedback": check_feedback,
        "stagnation": check_stagnation,
        "assertions": check_assertions,
    }

    success = gates[args.gate](args.path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
