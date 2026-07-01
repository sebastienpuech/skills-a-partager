#!/usr/bin/env python3
"""Helper functions for aggregate_benchmark.py."""

import json, math
from pathlib import Path


def calculate_stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0
    return {"mean": round(mean, 4), "stddev": round(stddev, 4), "min": round(min(values), 4), "max": round(max(values), 4)}


def load_run_results(benchmark_dir: Path) -> dict:
    runs_dir = benchmark_dir / "runs"
    search_dir = runs_dir if runs_dir.exists() else (benchmark_dir if list(benchmark_dir.glob("eval-*")) else None)
    if not search_dir:
        print(f"No eval directories found in {benchmark_dir} or {benchmark_dir / 'runs'}")
        return {}

    results: dict[str, list] = {}
    for eval_idx, eval_dir in enumerate(sorted(search_dir.glob("eval-*"))):
        metadata_path = eval_dir / "eval_metadata.json"
        eval_id, eval_name = eval_idx, ""
        if metadata_path.exists():
            try:
                with open(metadata_path) as mf:
                    metadata = json.load(mf)
                    eval_id = metadata.get("eval_id", eval_idx)
                    eval_name = metadata.get("eval_name", eval_dir.name)
            except (json.JSONDecodeError, OSError):
                eval_id, eval_name = eval_idx, eval_dir.name
        else:
            try:
                eval_id = int(eval_dir.name.split("-")[1])
            except ValueError:
                eval_id = eval_idx
            eval_name = eval_dir.name

        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir() or not list(config_dir.glob("run-*")):
                continue
            config = config_dir.name
            if config not in results:
                results[config] = []

            for run_dir in sorted(config_dir.glob("run-*")):
                run_number = int(run_dir.name.split("-")[1])
                grading_file = run_dir / "grading.json"
                if not grading_file.exists():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue

                try:
                    with open(grading_file) as f:
                        grading = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON in {grading_file}: {e}")
                    continue

                result = {
                    "eval_id": eval_id,
                    "eval_name": eval_name,
                    "run_number": run_number,
                    "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                }

                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds", 0.0)
                timing_file = run_dir / "timing.json"
                if result["time_seconds"] == 0.0 and timing_file.exists():
                    try:
                        with open(timing_file) as tf:
                            timing_data = json.load(tf)
                        result["time_seconds"] = timing_data.get("total_duration_seconds", 0.0)
                        result["tokens"] = timing_data.get("total_tokens", 0)
                    except json.JSONDecodeError:
                        pass

                metrics = grading.get("execution_metrics", {})
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                if not result.get("tokens"):
                    result["tokens"] = metrics.get("output_chars", 0)
                result["errors"] = metrics.get("errors_encountered", 0)

                raw_expectations = grading.get("expectations", [])
                for exp in raw_expectations:
                    missing = [f for f in ("text", "passed", "evidence") if f not in exp]
                    if missing:
                        print(f"Warning: expectation in {grading_file} missing fields {missing}: {exp}")
                result["expectations"] = raw_expectations

                notes_summary = grading.get("user_notes_summary", {})
                notes = []
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes

                results[config].append(result)

    return results


def aggregate_results(results: dict) -> dict:
    run_summary = {}
    configs = list(results.keys())

    for config in configs:
        runs = results.get(config, [])
        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            }
            continue
        pass_rates = [r["pass_rate"] for r in runs]
        times = [r["time_seconds"] for r in runs]
        tokens = [r.get("tokens", 0) for r in runs]
        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens)
        }

    # Explicitly identify primary (with_skill) vs baseline (without_skill)
    # instead of relying on arbitrary sort order of directory names
    primary_key = next((c for c in configs if "with_skill" in c or "with-skill" in c), None)
    baseline_key = next((c for c in configs if "without_skill" in c or "baseline" in c or "no_skill" in c), None)
    if primary_key is None and baseline_key is None and len(configs) >= 2:
        primary_key, baseline_key = configs[0], configs[1]
    elif primary_key is None and len(configs) >= 1:
        primary_key = configs[0]

    if len(configs) >= 2 and primary_key and baseline_key:
        primary = run_summary.get(primary_key, {})
        baseline = run_summary.get(baseline_key, {})
    else:
        primary = run_summary.get(primary_key or (configs[0] if configs else ""), {})
        baseline = {}

    delta_pass_rate = primary.get("pass_rate", {}).get("mean", 0) - baseline.get("pass_rate", {}).get("mean", 0)
    delta_time = primary.get("time_seconds", {}).get("mean", 0) - baseline.get("time_seconds", {}).get("mean", 0)
    delta_tokens = primary.get("tokens", {}).get("mean", 0) - baseline.get("tokens", {}).get("mean", 0)

    run_summary["delta"] = {
        "pass_rate": f"{delta_pass_rate:+.2f}",
        "time_seconds": f"{delta_time:+.1f}",
        "tokens": f"{delta_tokens:+.0f}"
    }

    warnings = []
    if len(configs) >= 2 and primary_key and baseline_key:
        primary_runs = results.get(primary_key, [])
        baseline_runs = results.get(baseline_key, [])
        if not primary_runs:
            warnings.append(f"WARNING: No primary runs for '{primary_key}'.")
        if not baseline_runs:
            warnings.append(f"WARNING: No baseline runs for '{baseline_key}'.")
        if abs(delta_pass_rate) > 0.50:
            warnings.append(f"WARNING: Delta pass_rate {delta_pass_rate:+.2f} > 50%.")

    run_summary["warnings"] = warnings
    return run_summary


def detect_stagnation(workspace_dir: Path) -> dict:
    iterations = []
    for iter_dir in sorted(workspace_dir.glob("iteration-*")):
        benchmark_file = iter_dir / "benchmark.json"
        if not benchmark_file.exists():
            continue
        try:
            with open(benchmark_file) as f:
                bm = json.load(f)
            configs = [k for k in bm.get("run_summary", {}) if k != "delta" and k != "warnings"]
            # Prefer with_skill config for stagnation detection
            primary = next((c for c in configs if "with_skill" in c or "with-skill" in c), configs[0] if configs else None)
            if primary:
                pass_rate = bm["run_summary"][primary].get("pass_rate", {}).get("mean", 0.0)
            else:
                pass_rate = 0.0
            iter_num = int(iter_dir.name.split("-")[1])
            iterations.append({
                "iteration": iter_num,
                "pass_rate": round(pass_rate, 4),
                "timestamp": bm.get("metadata", {}).get("timestamp", ""),
                "skill_snapshot": f"SKILL.md.v{iter_num}"
            })
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    if not iterations:
        return {"$schema_version": 1, "pattern": "no_data", "recommendation": "continue", "iterations": []}

    if len(iterations) == 1:
        return {
            "$schema_version": 1,
            "iterations": iterations,
            "best_iteration": iterations[0]["iteration"],
            "best_pass_rate": iterations[0]["pass_rate"],
            "current_pass_rate": iterations[0]["pass_rate"],
            "pattern": "first_iteration",
            "recommendation": "continue",
            "note": "Only 1 iteration available."
        }

    best = max(iterations, key=lambda x: x["pass_rate"])
    current = iterations[-1]
    pattern, recommendation = "improving", "continue"

    if len(iterations) >= 2:
        prev = iterations[-2]
        delta = current["pass_rate"] - prev["pass_rate"]
        deltas = [iterations[i]["pass_rate"] - iterations[i-1]["pass_rate"] for i in range(1, len(iterations))]
        recent_deltas = deltas[-4:] if len(deltas) >= 4 else deltas

        if delta < -0.05:
            pattern, recommendation = "regressing", "revert_to_best"
        elif len(recent_deltas) >= 2 and all(abs(d) < 0.02 for d in recent_deltas):
            pattern, recommendation = "stagnating", "pivot"
        elif len(recent_deltas) >= 3:
            sign_changes = sum(1 for i in range(len(recent_deltas) - 1) if recent_deltas[i] * recent_deltas[i + 1] < 0)
            net_change = abs(current["pass_rate"] - iterations[-min(4, len(iterations))]["pass_rate"])
            if sign_changes >= 2 and net_change < 0.05:
                pattern, recommendation = "oscillating", "pivot"
            elif delta > 0.02:
                pattern, recommendation = "improving", "continue"
        elif delta > 0.02:
            pattern, recommendation = "improving", "continue"

    if current["pass_rate"] < best["pass_rate"] - 0.05 and pattern != "improving":
        recommendation = "revert_to_best"
    if current["pass_rate"] > 0.95:
        recommendation = "ship"

    return {
        "$schema_version": 1,
        "iterations": iterations,
        "best_iteration": best["iteration"],
        "best_pass_rate": best["pass_rate"],
        "current_pass_rate": current["pass_rate"],
        "pattern": pattern,
        "recommendation": recommendation
    }
