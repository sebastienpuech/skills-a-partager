#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_evals.py - Run the golden cases in evals/evals.json against scripts/

Each case spec:
  - script: name of the script in scripts/ to run
  - fixture_dir: relative path under evals/ (copied to a temp dir before run)
  - args: extra argv passed after the fixture path
  - expected:
      exit_code: int
      json_match: dict of "path.to.key": value to match in stdout JSON
      json_path_min: dict of "path": min value
      failure_includes_substring: substring required in any failures[]
      side_effect_file: file name expected to be created in fixture dir
      side_effect_json_match: dict to match in the side_effect_file's JSON

Usage:
    python3 scripts/run_evals.py [--evals=evals/evals.json] [--verbose]
"""

from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def get_nested(obj, dotted_path):
    """Traverse obj by dotted path. Supports '.length' suffix for arrays."""
    parts = dotted_path.split(".")
    cur = obj
    for p in parts:
        if p == "length" and isinstance(cur, list):
            return len(cur)
        if isinstance(cur, dict):
            if p not in cur:
                return ("__MISSING__", dotted_path)
            cur = cur[p]
        elif isinstance(cur, list):
            try:
                cur = cur[int(p)]
            except (ValueError, IndexError):
                return ("__MISSING__", dotted_path)
        else:
            return ("__MISSING__", dotted_path)
    return cur


def check_expected(case_id, expected, exit_code, stdout, side_effect_dir):
    """Return list of failure strings for this case. Empty list = pass."""
    fails = []

    # 1. exit code
    if "exit_code" in expected:
        if exit_code != expected["exit_code"]:
            fails.append(
                f"exit_code: expected {expected['exit_code']}, got {exit_code}"
            )

    # 2. parse stdout as JSON
    stdout_json = None
    try:
        stdout_json = json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        pass

    # 3. json_match
    if "json_match" in expected:
        if stdout_json is None:
            fails.append("json_match: stdout is not valid JSON")
        else:
            for path, want in expected["json_match"].items():
                got = get_nested(stdout_json, path)
                if isinstance(got, tuple) and got[0] == "__MISSING__":
                    fails.append(f"json_match: path '{path}' missing")
                elif got != want:
                    fails.append(f"json_match: '{path}' expected {want!r}, got {got!r}")

    # 4. json_path_min
    if "json_path_min" in expected and stdout_json is not None:
        for path, min_val in expected["json_path_min"].items():
            got = get_nested(stdout_json, path)
            if isinstance(got, tuple) and got[0] == "__MISSING__":
                fails.append(f"json_path_min: path '{path}' missing")
            elif not isinstance(got, (int, float)) or got < min_val:
                fails.append(
                    f"json_path_min: '{path}' expected >= {min_val}, got {got!r}"
                )

    # 5. failure_includes_substring
    if "failure_includes_substring" in expected:
        substr = expected["failure_includes_substring"]
        failures = (stdout_json or {}).get("failures", []) if stdout_json else []
        if not any(substr in f for f in failures):
            fails.append(
                f"failure_includes_substring: no failure contains '{substr}'"
            )

    # 6. side_effect_file
    if "side_effect_file" in expected:
        side_path = side_effect_dir / expected["side_effect_file"]
        if not side_path.is_file():
            fails.append(f"side_effect_file: {expected['side_effect_file']} not created")
        elif "side_effect_json_match" in expected:
            try:
                side_json = json.loads(side_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                fails.append(f"side_effect_file: not valid JSON ({e})")
                return fails
            for path, want in expected["side_effect_json_match"].items():
                got = get_nested(side_json, path)
                if isinstance(got, tuple) and got[0] == "__MISSING__":
                    fails.append(f"side_effect_json_match: path '{path}' missing")
                elif got != want:
                    fails.append(
                        f"side_effect_json_match: '{path}' expected {want!r}, got {got!r}"
                    )

    return fails


def run_case(case, evals_dir, scripts_dir, verbose=False):
    case_id = case["id"]
    fixture_src = evals_dir / case["fixture_dir"]
    if not fixture_src.is_dir():
        return (case_id, ["fixture_dir not found: " + str(fixture_src)])

    # Copy fixture to temp dir so side effects don't pollute the repo
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "workdir"
        shutil.copytree(fixture_src, tmp_path)

        script_path = scripts_dir / case["script"]
        cmd = ["python3", str(script_path), str(tmp_path)] + case.get("args", [])

        if verbose:
            print(f"  cmd: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            return (case_id, ["TIMEOUT after 30s"])

        fails = check_expected(
            case_id, case["expected"],
            result.returncode, result.stdout, tmp_path
        )
        if verbose and fails:
            print(f"  stdout: {result.stdout[:300]}")
            print(f"  stderr: {result.stderr[:300]}")
        return (case_id, fails)


def main():
    ap = argparse.ArgumentParser(description="Run mode-plan eval cases")
    ap.add_argument("--evals", type=Path, default=None,
                    help="Path to evals.json (default: <repo>/evals/evals.json)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    # Resolve paths
    scripts_dir = Path(__file__).resolve().parent
    repo_dir = scripts_dir.parent
    evals_file = args.evals or (repo_dir / "evals" / "evals.json")
    evals_dir = evals_file.parent

    if not evals_file.is_file():
        print(json.dumps({"error": "evals.json not found at " + str(evals_file)}),
              file=sys.stderr)
        return 2

    spec = json.loads(evals_file.read_text(encoding="utf-8"))
    cases = spec.get("cases", [])

    print(f"Running {len(cases)} eval cases against scripts in {scripts_dir}")
    print("=" * 70)

    results = []
    for case in cases:
        case_id, fails = run_case(case, evals_dir, scripts_dir, args.verbose)
        status = "PASS" if not fails else "FAIL"
        results.append({"id": case_id, "status": status, "failures": fails})
        marker = "ok" if status == "PASS" else "XX"
        print(f"  [{marker}] {case_id}")
        for f in fails:
            print(f"         -> {f}")

    print("=" * 70)
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = len(results) - n_pass
    print(f"Summary: {n_pass}/{len(results)} passed, {n_fail} failed")

    report = {
        "total": len(results),
        "passed": n_pass,
        "failed": n_fail,
        "results": results,
    }
    # Write report to evals/last_run.json for CI consumption
    (evals_dir / "last_run.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
