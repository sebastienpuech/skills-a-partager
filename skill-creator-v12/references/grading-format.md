# Grading & Analysis JSON Formats

All schemas include `$schema_version: 1`. Scripts should check this field.

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "$schema_version": 1,
  "assertions_are_sufficient": true,
  "expectations": [
    {
      "text": "The output includes X",
      "passed": true,
      "evidence": "Found in transcript Step 3: '...'",
      "trap_triggered": true
    }
  ],
  "summary": { "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67 },
  "execution_metrics": { "tool_calls": {"Read": 5, "Bash": 8}, "total_tool_calls": 15, "errors_encountered": 0, "output_chars": 12450 },
  "timing": { "executor_duration_seconds": 165.0, "total_duration_seconds": 191.0 },
  "claims": [
    { "claim": "The form has 12 fields", "type": "factual", "verified": true, "evidence": "Counted in field_info.json" }
  ],
  "user_notes_summary": { "uncertainties": [], "needs_review": [], "workarounds": [] },
  "eval_feedback": {
    "suggestions": [{ "assertion": "...", "reason": "A wrong output would also pass" }],
    "overall": "Assertions check presence but not correctness."
  }
}
```

Key fields: `expectations[].text/passed/evidence` (viewer depends on these exact names). `trap_triggered` only for trapped tests. `assertions_are_sufficient` gates the iteration loop.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A provides...",
  "rubric": {
    "A": { "content": {"correctness": 5, "completeness": 5, "accuracy": 4}, "structure": {"organization": 4, "formatting": 5, "usability": 4}, "content_score": 4.7, "structure_score": 4.3, "overall_score": 9.0 },
    "B": { "content": {"correctness": 3, "completeness": 2, "accuracy": 3}, "structure": {"organization": 3, "formatting": 2, "usability": 3}, "content_score": 2.7, "structure_score": 2.7, "overall_score": 5.4 }
  },
  "output_quality": { "A": { "score": 9, "strengths": [], "weaknesses": [] }, "B": { "score": 5, "strengths": [], "weaknesses": [] } },
  "expectation_results": { "A": { "passed": 4, "total": 5, "pass_rate": 0.80 }, "B": { "passed": 3, "total": 5, "pass_rate": 0.60 } }
}
```

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`.

```json
{
  "comparison_summary": { "winner": "A", "winner_skill": "path/to/skill", "comparator_reasoning": "..." },
  "winner_strengths": ["..."],
  "loser_weaknesses": ["..."],
  "instruction_following": { "winner": { "score": 9, "issues": [] }, "loser": { "score": 6, "issues": [] } },
  "improvement_suggestions": [{ "priority": "high", "category": "instructions", "suggestion": "...", "expected_impact": "..." }],
  "transcript_insights": { "winner_execution_pattern": "...", "loser_execution_pattern": "..." }
}
```

Categories: `instructions`, `tools`, `examples`, `error_handling`, `structure`, `references`.
Priority: `high` (would change outcome), `medium` (improves quality), `low` (nice to have).

---

## benchmark.json

Output from Benchmark mode. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "$schema_version": 1,
  "metadata": { "skill_name": "pdf", "timestamp": "2026-01-15T10:30:00Z", "evals_run": [1, 2, 3], "runs_per_configuration": 3 },
  "runs": [
    {
      "eval_id": 1, "eval_name": "Ocean", "configuration": "with_skill", "run_number": 1,
      "result": { "pass_rate": 0.85, "passed": 6, "total": 7, "time_seconds": 42.5, "tokens": 3800, "errors": 0 },
      "expectations": [{"text": "...", "passed": true, "evidence": "..."}]
    }
  ],
  "run_summary": {
    "with_skill": { "pass_rate": {"mean": 0.85, "stddev": 0.05}, "time_seconds": {"mean": 45.0, "stddev": 12.0}, "tokens": {"mean": 3800, "stddev": 400} },
    "without_skill": { "pass_rate": {"mean": 0.35, "stddev": 0.08} },
    "delta": { "pass_rate": "+0.50" }
  },
  "notes": ["..."]
}
```

The viewer reads `configuration` (must be `"with_skill"` or `"without_skill"`), `result.pass_rate` (nested, not top-level). Using wrong field names = empty viewer.

---

## feedback.json

User feedback from eval viewer. Located at `<workspace>/iteration-N/feedback.json`.

```json
{
  "$schema_version": 1,
  "reviews": [{ "run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "2026-01-15T10:45:00Z" }],
  "status": "complete"
}
```

Empty feedback string = user thought it was fine.

---

## history.json

Version tracking in Improve mode. Located at workspace root.

```json
{
  "$schema_version": 1,
  "started_at": "2026-01-15T10:30:00Z",
  "skill_name": "pdf",
  "current_best": "v2",
  "iterations": [
    { "version": "v0", "parent": null, "expectation_pass_rate": 0.65, "grading_result": "baseline", "is_current_best": false },
    { "version": "v2", "parent": "v1", "expectation_pass_rate": 0.85, "grading_result": "won", "is_current_best": true }
  ]
}
```

---

## metrics.json

Output from executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {"Read": 5, "Write": 2, "Bash": 8},
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf"],
  "errors_encountered": 0,
  "output_chars": 12450
}
```
