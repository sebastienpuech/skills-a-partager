# Architecture Decision Guide

This reference helps you choose the right architecture when designing a new skill.
Read this BEFORE writing the SKILL.md.

## Step 1: Classify the Task

| Type | Description | Dominant Failure Mode |
|------|-------------|----------------------|
| TRANSFORMATION | Structured input -> structured output | Mapping errors, miscalibrated thresholds |
| EVALUATION | Input -> judgment / comments / score | False negatives, confirmation bias |
| GENERATION | Brief -> created content | Satisficing mediocrity, genericness |
| ANALYSIS | Data -> insights / patterns | Selection bias, missing angles |

## Step 2: Score Complexity

Two separate scores determine the architecture. Score them independently.

### 2a. Conceptual complexity (determines single vs multi-agent)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Cost of error | 0-3 | 0=negligible, 1=annoying, 2=costly, 3=critical (millions $) |
| Subjectivity | 0-2 | 0=mechanically verifiable, 2=pure judgment |
| Non-expert users | 0-2 | 0=experts who will verify, 2=non-experts who trust blindly |
| Edge cases | 0-1 | 0=well-constrained domain, 1=varied and frequent edge cases |
| Frequency | 0-1 | 0=occasional, 1=regular (>10x/month) |

**Max: 9 points**

### 2b. Input volume (determines chunking and context strategy)

| Input volume | Level | Impact |
|-------------|-------|--------|
| < 5 pages / < 10K chars | SMALL | No special handling needed |
| 5-30 pages / 10-60K chars | MEDIUM | Fits in context but needs focused reading |
| 30-80 pages / 60-160K chars | LARGE | Risk of lost-in-the-middle — requires sectioned reading strategy |
| > 80 pages / > 160K chars | VERY LARGE | Cannot fit in one pass — requires chunking or multi-pass strategy |

Input volume is scored separately because it drives a different kind of
architecture decision than conceptual complexity. A simple TRANSFORMATION
skill (score 3) processing 100-page documents still needs a multi-pass
strategy even though it doesn't need multi-agent debate. Conversely, a
high-stakes EVALUATION skill (score 8) on a 2-page document doesn't need
chunking at all.

## Step 3: Choose Architecture

**Based on conceptual complexity score:**

| Score | Architecture | What to build |
|-------|-------------|---------------|
| 0-3 | A: Single agent + self-diagnosis | Just SKILL.md with self-diagnosis section at the end |
| 4-6 | B: Single agent + internal critique | SKILL.md in 2 phases (execution + critique before delivery) |
| 7+ | C: Multi-agent | agents/ directory with roles + synthesizer (see Step 4 for pattern) |

**Overlay with input volume — regardless of conceptual score:**

| Volume | Additional requirement |
|--------|----------------------|
| SMALL | No additional handling |
| MEDIUM | Instruct the agent to read documents section by section, not all at once. Add a "completeness check" to self-diagnosis: did I process all sections? |
| LARGE | Add a **sectioned reading strategy** to the SKILL.md: list sections to process, read each one, accumulate findings, synthesize at the end. This is NOT multi-agent — it's a single agent working in passes. Add lost-in-the-middle mitigation: "After processing all sections, re-read the introduction and conclusion to check for information you may have missed in the middle." |
| VERY LARGE | **Mandatory chunking pipeline**: a Python script splits the input into chunks, the agent processes each chunk independently, then a synthesis step merges findings. For Architecture A/B, this means adding a script. For Architecture C, one agent can be the "chunker/merger." Also add a circuit-breaker: if the agent's output references fewer than 60% of the input sections, flag as potentially incomplete. |

## Step 4: Choose Pattern (if conceptual score >= 7)

```
EVALUATION task?
+-- Risk of false negatives -> Pattern 1 (Debate Room)
+-- Need iterative correction -> Pattern 2 (Refinement Loop)
+-- Both -> Pattern 6 (Combo: Debate Room + Refinement Loop)

ANALYSIS task?
+-- Multiple independent dimensions -> Pattern 3 (Expert Panel)
+-- Single dimension, need depth -> Pattern 2 (Refinement Loop)

GENERATION task?
+-- Writing quality is critical -> Pattern 5 (Tournament)
+-- Incremental improvement -> Pattern 2 (Refinement Loop)

TRANSFORMATION task?
+-- Complex rules + high cost of error -> Pattern 3 (Expert Panel)
    with roles: TRANSFORMER + VALIDATOR + SPOT-CHECKER
+-- Multi-format output -> Pattern 2 (Refinement Loop)
    with validation script between iterations
+-- Simple rules but large volume -> Architecture B + chunking
    (don't over-engineer with multi-agent when a validation script suffices)
```

## Step 4b: Guardrails by Task Type

Each task type has different dominant failure modes and needs different
guardrails. Don't apply EVALUATION guardrails to TRANSFORMATION skills.

| Task type | Mandatory guardrails | Optional (if high complexity) |
|-----------|---------------------|------------------------------|
| TRANSFORMATION | Circuit-breakers in scripts (row count, totals, format). Spot-check: re-execute 3-5 random operations and compare. | Sample Verifier agent (re-processes 10% of input independently) |
| EVALUATION | Adversarial QA (Defender agent). Every "missing" claim must be searched exhaustively. | Debate Room pattern, blind comparison |
| GENERATION | Critique phase: check against brief requirements. Anti-mediocrity check: "is this output generic or specifically tailored?" | Tournament pattern, style diversity |
| ANALYSIS | Multi-angle coverage check: "which dimensions did I NOT analyze?" Selection bias check: "am I over-representing certain data points?" | Expert Panel with different analytical lenses |

## Step 5: Checklist Before Writing the SKILL.md

```
[ ] Task type identified
[ ] Dominant failure mode identified
[ ] Conceptual complexity score calculated (0-9)
[ ] Input volume assessed (SMALL/MEDIUM/LARGE/VERY LARGE)
[ ] Architecture chosen (A / B / C + pattern)
[ ] Guardrails selected from Step 4b table (matched to task type)
[ ] Domain-specific self-diagnosis checks drafted (minimum 4)
[ ] Circuit-breakers identified (minimum 2)
[ ] If LARGE/VERY LARGE input: chunking or sectioned reading strategy designed
[ ] If Architecture C: agent roles defined with strong personas
[ ] Trapped test cases prepared (minimum 2 — inputs that should trigger circuit-breakers)
```

---

## Pattern Summaries

For full multi-agent pattern templates, see the `orchestration-patterns` skill
(separate skill, not part of this package).

### Pattern 1: Debate Room
Parallel spawn of CRITIC + DEFENDER, then deterministic alignment script,
then JUDGE who verifies against the source document. Best for evaluation
tasks where false negatives are the main risk.

### Pattern 2: Refinement Loop
Iterative loop: PRODUCER -> CRITIC (with convergence score) -> check
convergence -> if not converged, PRODUCER receives output + feedback ->
next iteration. Max 3-4 iterations. Exit on score >= 8, plateau, or
max iterations.

### Pattern 3: Expert Panel
Parallel spawn of 2-4 domain EXPERTS, each covering a different angle.
Then a SYNTHESIS agent that integrates (not concatenates) findings,
identifies convergences, contradictions, and cross-cutting gaps.

### Pattern 4: Red Team / Blue Team
BLUE TEAM produces output -> RED TEAM attacks it ("find everything an
adversary would use to reject this") -> BLUE TEAM 2nd instance corrects.
More aggressive than Debate Room. For outputs facing hostile evaluators.

### Pattern 5: Tournament
3-5 agents produce outputs from the same brief with different style
directives. BLIND EVALUATOR ranks them without knowing which agent
produced which. MERGER takes the best elements from top outputs.

### Pattern 6: Combo (Debate Room + Refinement Loop)
The most powerful. Iterative Debate Room: each iteration runs
CRITIC + DEFENDER -> alignment -> JUDGE -> REVISER. Loop until
convergence. For high-stakes evaluation tasks.

---

## Key Design Principles for Multi-Agent Skills

**Context isolation**: Each subagent only knows what its spawn prompt
gives it. Write intermediate outputs as JSON to the filesystem and pass
paths, not contents, in the prompt.

**Strong role prompts**: Adversarial patterns work because personas are
strong. If the critic is too polite, the pattern collapses. Use directive
personas ("you have rejected 70% of proposals", "you spent 18 months on
this project").

**Strict JSON format**: All agents produce JSON with identical fields and
cross-referencing IDs. Without this, the synthesis agent can't align
arguments.

**Deterministic scripts**: Everything mechanical (alignment, convergence
calculation, counting, format validation) goes in Python scripts, not
LLM calls. More reliable, faster, saves tokens.

## Failure Modes and Recovery for Multi-Agent Patterns

Every multi-agent pattern can fail partially. Design for graceful degradation, not all-or-nothing.

| Pattern | Failure Mode | Recovery Strategy |
|---------|-------------|-------------------|
| Debate Room | Defender agent crashes or returns malformed JSON | Synthesizer proceeds with Critic output only, but flags: "Adversarial check was not completed — results may contain uncaught false negatives" |
| Expert Panel | One expert produces no output or times out | Synthesizer integrates remaining experts, notes which dimension is missing: "Analysis of [topic] is absent due to agent failure — manual review recommended" |
| Tournament | Fewer than 3 candidates produced | Reduce to blind comparison (2) or skip tournament and use the best available output with a quality caveat |
| Refinement Loop | Convergence score never reaches threshold | Hard stop after max iterations (3-4). Deliver best iteration so far with note: "Did not converge after N iterations. Best score was X at iteration M." |
| Combo (Debate + Refinement) | Debate phase fails in one iteration | Skip adversarial check for that iteration only, continue loop. Flag the skip. |

**General rules for all multi-agent skills:**
1. **Timeout**: If an agent hasn't completed after 2x expected duration, proceed without it. Never block indefinitely.
2. **Malformed output**: If an agent's JSON is unparseable, retry once. If still malformed, treat as agent failure.
3. **Cascading failure**: If more than half of parallel agents fail, abort the pattern and fall back to single-agent execution. Notify the user.
4. **Always flag**: Any degraded execution must be clearly flagged in the output. Silent partial results are worse than explicit failures.

### Error Handling and Timeouts

When spawning parallel agents, always plan for partial failure:

**Timeout pattern:**
```
Spawn agents A, B, C in parallel with expected completion < 2 minutes.
Wait for all results with timeout = 4 minutes (2x expected).
If agent X hasn't completed after timeout:
  - Log: "Agent X timed out after 4 minutes"
  - Proceed with results from completed agents
  - Flag in output: "Analysis dimension [X's role] is missing due to timeout"
```

**Degraded input handling for synthesizer:**
```
You receive inputs from N agents. Some may be missing or malformed.
Before synthesizing:
1. Count received inputs: {received}/{expected}
2. If any input is empty or invalid JSON, note which agent failed
3. Produce the best output from available inputs
4. Add a "Coverage" section listing:
   - Dimensions covered: [list from successful agents]
   - Dimensions missing: [list from failed agents]
   - Recommendation: "Re-run [failed agent] to complete the analysis"
```

**Recovery strategy:**
If more than 50% of agents fail, do not attempt synthesis. Instead,
report the failure to the user and suggest re-running with fewer agents
or a simpler architecture.
