# JSON Schemas — Input & Eval Data

Schemas for eval configuration and timing data. For grading, comparison,
benchmark, and analysis output schemas, see `references/grading-format.md`.

All schemas include `$schema_version: 1`. Scripts should warn on version mismatch.

---

## evals.json

Defines the evals for a skill. Located at `evals/evals.json`.

```json
{
  "$schema_version": 1,
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": ["The output includes X", "The skill used script Y"]
    }
  ]
}
```

Fields: `skill_name` (matches frontmatter), `evals[].id` (unique int),
`evals[].prompt` (task), `evals[].expected_output` (human-readable),
`evals[].files` (optional input paths), `evals[].expectations` (verifiable statements).

---

## eval_metadata.json

Per-test-case metadata. Located at `<workspace>/iteration-N/eval-<name>/eval_metadata.json`.

```json
{
  "$schema_version": 1,
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "is_trapped_test": false,
  "assertions": ["The output file is a valid .xlsx", "Row count matches input"]
}
```

Use `eval_name` as directory name (e.g. `eval-column-mapping-trap/`).
`is_trapped_test: true` for inputs designed to trigger guardrails.

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

Capture from task notification (`total_tokens`, `duration_ms`) — not persisted elsewhere.

```json
{
  "$schema_version": 1,
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Required: `total_tokens`, `duration_ms`, `total_duration_seconds`.
Optional: `executor_start/end/duration_seconds`, `grader_start/end/duration_seconds`.

---

## stagnation_check.json

GATE 4 output. Located at `<workspace>/stagnation_check.json`.

```json
{
  "$schema_version": 1,
  "iterations": [
    { "iteration": 1, "pass_rate": 0.65, "timestamp": "2026-01-15T10:30:00Z", "skill_snapshot": "SKILL.md.v1" }
  ],
  "best_iteration": 2,
  "best_pass_rate": 0.70,
  "pattern": "improving",
  "recommendation": "continue"
}
```

Patterns: `improving` (>2% gain), `stagnating` (<2% for 2+ iterations),
`regressing` (>5% drop), `oscillating` (sign changes, <5% net),
`first_iteration`, `no_data`.

Recommendations: `continue`, `pivot`, `revert_to_best`, `ship`.

---

## Migration Log

### Version 1 (initial)
- All schemas established with `$schema_version: 1`
