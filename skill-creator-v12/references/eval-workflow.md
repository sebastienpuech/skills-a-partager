# Eval Workflow: Running and Evaluating Test Cases

This is one continuous sequence — don't stop partway through.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory.
Organize by iteration (`iteration-1/`, `iteration-2/`) and test case (`eval-<name>/`).

## Step 1: Spawn all runs in the same turn

For each test case, spawn two subagents simultaneously:

**With-skill run:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any>
- Save outputs to: <workspace>/iteration-<N>/eval-<name>/with_skill/outputs/
```

**Baseline run** (same prompt, no skill or old skill):
- Creating a new skill → no skill at all, save to `without_skill/outputs/`
- Improving an existing skill → old version snapshot, save to `old_skill/outputs/`

Write `eval_metadata.json` for each test case (see `references/schemas.md`).
Use descriptive directory names (`eval-column-mapping-trap/` not `eval-0/`).

**Idempotency**: each run uses its own output directory. No shared temp files.

**Baseline validation**: after all runs complete, verify BOTH configurations
produced outputs. Re-run failed baselines before proceeding to grading.

## Step 2: Draft assertions while runs execute

Don't wait — use this time to draft quantitative assertions. Good assertions
are objectively verifiable and have descriptive names that read clearly in
the benchmark viewer.

Update `eval_metadata.json` and `evals/evals.json` with the assertions.

## Step 3: Capture timing data

When each subagent completes, the notification contains `total_tokens` and
`duration_ms`. Save immediately to `timing.json` — this data isn't persisted
elsewhere. See `references/schemas.md` for the schema.

## Step 4: Grade, aggregate, and launch the viewer

### 4a. Grade each run

Spawn a grader subagent using `agents/grader.md`. The grader reads
`references/grading-format.md` for the exact JSON schema.

Key: if the grader flags non-discriminating assertions in `eval_feedback`,
address them before the next iteration. If `assertions_are_sufficient` is
false, you cannot proceed to skill improvement.

For programmatically checkable assertions, write and run a script instead
of eyeballing it.

### 4b. Verify trapped test cases

For trapped tests (`is_trapped_test: true`): the output or transcript must
contain guardrail evidence (QUARANTINE, WARNING, ALERT, CRITICAL, or modified
behavior). A trapped test that passes cleanly = critical failure → fix the
guardrail before continuing.

### 4c. Aggregate into benchmark

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

Produces `benchmark.json` and `benchmark.md`. See `references/grading-format.md`
for the benchmark.json schema the viewer expects.

### 4d. Analyst pass

Read benchmark data and surface patterns: non-discriminating assertions,
high-variance evals (>30% stddev), time/token tradeoffs. For high-variance
evals, act on them: simplify, run more samples, mark unreliable, or
investigate root cause.

### 4e. Launch the viewer

```bash
python -m eval-viewer.generate_review \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json
```

For iteration 2+: add `--previous-workspace <workspace>/iteration-<N-1>`.
In Cowork/headless: add `--static <output_path>` for standalone HTML.

Tell the user: "I've opened the results — 'Outputs' tab for qualitative
review, 'Benchmark' tab for quantitative comparison. Come back when done."

### What the user sees

- **Outputs tab**: prompt, rendered output files, previous output (iteration 2+),
  formal grades (collapsed), feedback textbox, previous feedback (iteration 2+)
- **Benchmark tab**: pass rates, timing, tokens per configuration, analyst notes
- Navigation: prev/next or arrow keys. "Submit All Reviews" saves `feedback.json`.

## Step 5: Read the feedback

Read `feedback.json`. Focus on test cases with specific complaints — empty
feedback means it was fine. Kill the viewer server when done.

---

## GATE 3 enforcement

Before revising the skill, verify `feedback.json` exists:
```bash
python scripts/gate_check.py <workspace>/iteration-N --gate feedback
```

### Chat-based feedback collection

When the viewer's file-download flow creates friction (Cowork static viewer,
remote sessions, or users who find the round-trip confusing), collect feedback
directly in conversation and write `feedback.json` yourself.

**Procedure:**

1. Present the static viewer link so the user can see the outputs.
2. For each test case, ask: "How does test N look? Anything to fix or improve?"
   Keep it conversational — don't overwhelm with all test cases at once.
3. If the user says "looks good" or similar, record an empty feedback string
   for that test case (same meaning as in the viewer).
4. Once all test cases are covered, write `feedback.json` to the iteration
   directory using the standard schema:

```json
{
  "$schema_version": 1,
  "reviews": [
    {"run_id": "eval-name-with_skill", "feedback": "user's comment or empty", "timestamp": "ISO8601"}
  ],
  "status": "complete",
  "source": "chat"
}
```

5. Run the gate check as usual — `feedback.json` written from chat passes
   the same gate as one downloaded from the viewer.

The `source: "chat"` field is optional metadata to distinguish how the
feedback was collected. The gate check ignores it.
