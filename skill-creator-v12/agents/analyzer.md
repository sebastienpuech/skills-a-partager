# Analyzer Agent

Two modes: post-hoc comparison analysis, and benchmark pattern analysis.

---

## Mode 1: Post-hoc Comparison Analysis

After the blind comparator determines a winner, "unblind" and explain WHY.

### Inputs
- **winner**: "A" or "B"
- **winner_skill_path**, **loser_skill_path**: Paths to both skills
- **winner_transcript_path**, **loser_transcript_path**: Execution transcripts
- **comparison_result_path**: Blind comparator's output
- **output_path**: Where to save analysis

### Process
1. Read comparison result — note reasoning and scores
2. Read both skills — identify structural differences (clarity, scripts, examples, edge cases)
3. Read both transcripts — compare execution patterns, tool usage, error recovery
4. Score instruction following (1-10) for each — did the agent follow its skill?
5. Identify winner strengths and loser weaknesses with specific quotes
6. Generate prioritized improvement suggestions (high/medium/low)

### Output
Write `analysis.json`. Read `references/grading-format.md` for the schema.

---

## Mode 2: Benchmark Pattern Analysis

Review benchmark run results and surface patterns hidden by aggregates.

### Inputs
- **benchmark_data_path**: Path to benchmark.json with all run results
- **output_path**: Where to save notes (JSON array of strings)

### Process
1. Read benchmark data, note configurations and aggregates
2. Per-assertion patterns: always pass both? always fail both? skill-only pass? high variance?
3. Cross-eval patterns: certain types harder? surprising results?
4. Metrics patterns: time/token tradeoffs, outlier runs, high variance?
5. Write freeform observation notes grounded in data

### Output
JSON array of strings. Each note: specific observation + data reference.

### Rules (both modes)
- Be specific — quote from skills/transcripts, reference data
- Be actionable — concrete changes, not vague advice
- Focus on causation — did the weakness actually cause the worse output?
- Don't suggest skill improvements in benchmark mode — just report patterns
