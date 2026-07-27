#!/usr/bin/env python3
"""Validate defender.md output (defense.json) schema.

Usage:
    python scripts/validate_defender.py <path/to/defense.json>
"""

import json
import sys
from pathlib import Path


def validate_defender_output(defense_path: str) -> bool:
    """Validate defender agent output schema.

    Checks that defense.json has required fields:
    defenses[], accuracy_checks[], statistics{}.
    """
    path = Path(defense_path)
    if not path.exists():
        print(f"DEFENDER VALIDATION: No defense.json at {defense_path}")
        return False

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"DEFENDER VALIDATION FAILED: Invalid JSON: {e}")
        return False

    errors = []
    for key in ("defenses", "accuracy_checks", "statistics"):
        if key not in data:
            errors.append(f"Missing top-level key: '{key}'")

    defenses = data.get("defenses", [])
    if not isinstance(defenses, list):
        errors.append("'defenses' must be a list")
    else:
        required = {"claim_id", "claim_text", "verdict"}
        for i, d in enumerate(defenses):
            missing = required - set(d.keys())
            if missing:
                errors.append(f"defenses[{i}] missing: {', '.join(missing)}")
            verdict = d.get("verdict", "")
            if verdict not in ("CONTESTED", "CONFIRMED", ""):
                errors.append(f"defenses[{i}] invalid verdict: '{verdict}'")

    stats = data.get("statistics", {})
    if isinstance(stats, dict):
        if "total_claims_checked" not in stats:
            errors.append("statistics missing 'total_claims_checked'")
    else:
        errors.append("'statistics' must be a dict")

    if errors:
        print(f"DEFENDER VALIDATION FAILED: {len(errors)} error(s):")
        for e in errors[:5]:
            print(f"  - {e}")
        return False

    print(f"DEFENDER VALIDATION PASSED: {len(defenses)} defenses, "
          f"{len(data.get('accuracy_checks', []))} accuracy checks.")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_defender.py <path/to/defense.json>")
        sys.exit(1)
    success = validate_defender_output(sys.argv[1])
    sys.exit(0 if success else 1)
