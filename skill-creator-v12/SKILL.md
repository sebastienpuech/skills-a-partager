---
name: skill-creator-v12
description: >
  Create, improve, debug, and rigorously test skills with built-in architecture guidance, guardrails, and adversarial QA.
  Use this skill whenever the user wants to create a skill from scratch, edit or optimize an existing skill, turn
  a workflow into a reusable skill, run evals with baseline comparison, benchmark skill performance, do blind A/B
  comparison between skill versions, or optimize a skill's description for better triggering. Also trigger when
  the user says "make this a skill", "automate this as a skill", "package this workflow", or asks to test, evaluate,
  debug, fix, or improve an existing skill. Trigger when the user says "my skill doesn't work", "this skill is broken",
  or "help me debug my skill". This is the latest version — always prefer this over skill-creator v1 through v11.
---

# Skill Creator v12

Create new skills, iterate on them with eval-driven feedback, and ship.

## High-level flow

```
1. Capture intent (interview the user)
2. Architecture decision (classify, score, choose A/B/C)
   └─ If score 0-2 + SMALL volume → fast-path (skip to step 6)
3. Write SKILL.md draft (with guardrails built in)
4. GATE 1: linter must pass  |  GATE 2: pre-flight critique
5. Run test cases (with-skill + baseline, including trapped tests)
6. GATE 3: generate eval viewer → human reviews → read feedback
7. Improve skill based on feedback
8. GATE 4: stagnation/regression check
9. Repeat 5-8 until satisfied
10. Optimize description → package → deliver
```

Your job: figure out where the user is in this flow and help them progress.
Maybe they want to create from scratch, maybe they have a draft, maybe their
skill is broken and they need debugging help. Be flexible.

## Communicating with the user

Adapt your vocabulary to the user's level. Context cues matter — if someone
says "I just want a simple skill to rename files", don't talk about adversarial
QA. Terms like "evaluation" and "benchmark" are fine for most users; for "JSON"
and "assertion", check that the user is comfortable before using them freely.

---

## Fast-path for simple skills

When complexity ≤ 2 AND volume is SMALL:

1. Capture intent (same questions)
2. Confirm fast-path: "This is straightforward — I'll draft it, run a quick test, and iterate."
3. Write SKILL.md with Architecture A + Template A self-diagnosis + ≥1 circuit-breaker
   - Record: `# Created via: fast-path (complexity ≤2, SMALL volume)`
4. Run 1-2 test prompts directly — no baseline, no viewer
5. Escalation check after each test. Switch to full flow if:
   - User reveals >3 unanticipated edge cases
   - Any test needs >1 revision cycle
   - Output quality varies between similar inputs
6. Iterate in conversation

---

## Creating a skill

### Capture Intent

Extract from conversation history first (tools used, corrections made, I/O formats).
Then fill gaps:

1. What should this skill enable Claude to do?
2. When should it trigger? (phrases, contexts)
3. Expected output format?
4. Should we set up test cases? (suggest based on skill type — objective outputs benefit, subjective may not)
5. Scope check: one skill or several?

### Interview and Research

Ask about edge cases, formats, examples, success criteria, dependencies.
Ask for existing docs, runbooks, scripts, past failures.
Ask explicitly for input/output pairs (candidates for `examples/` directory).
Check available MCPs for research.

### Architecture Decision

Read `references/architecture-decision.md` for the full guide.

1. Classify task type: TRANSFORMATION | EVALUATION | GENERATION | ANALYSIS
2. Score conceptual complexity (0-9) and input volume (SMALL/MEDIUM/LARGE/VERY LARGE)
3. Choose architecture:
   - 0-3 → A (single agent + self-diagnosis). If also SMALL → offer fast-path
   - 4-6 → B (single agent + internal critique phase)
   - 7+  → C (multi-agent, choose pattern from architecture-decision.md)
4. Overlay volume strategy (sectioned reading for LARGE, chunking for VERY LARGE)
5. Choose guardrails matched to task type (see Step 4b in architecture-decision.md)

Present the decision to the user before proceeding.

### Guardrails Integration

When writing guardrails, read `references/guardrails.md` for templates and examples.

Every skill gets at minimum:
- Template A self-diagnosis (end of SKILL.md)
- ≥2 domain-specific circuit-breakers in Python scripts
- 4-5 domain-specific checks

Architecture B/C additionally get internal critique (Template B) or multi-agent critique.

Guardrails vary by task type (summary — details in `references/architecture-decision.md` Step 4b):
- **EVALUATION** skills (judge/grade): adversarial QA via `agents/defender.md` is **mandatory**. If building an EVALUATION skill, read `references/adversarial-qa.md`. Validate defender output schema.
- **TRANSFORMATION** skills (convert/clean): need mechanical verification (input count = output count, checksums, round-trip tests).
- **GENERATION** skills (create/write): need anti-mediocrity checks (output must differ from generic template, check specificity score).
- **ANALYSIS** skills (analyze/review): need coverage checks (all sections addressed, no silent skips).

Weave guardrails into the workflow naturally — self-diagnosis at the end, circuit-breakers inside scripts, critique phase between execution and delivery.

### Write the SKILL.md

When writing the SKILL.md, read `references/skill-writing-guide.md` for the full style guide and anti-patterns.
When starting from scratch, use `references/skill-template.md` as your starting skeleton.

Key rules:
- SKILL.md < 500 lines / < 25K chars — orchestration only, not data
- Conditional loading for references ("Read X when doing Y")
- For TRANSFORMATION/GENERATION skills, ask for I/O pairs → bundle in `examples/` via `agents/example-distiller.md`
- Explain the "why" — the model generalizes from reasoning better than from rules
- Avoid monolith scripts (>300 lines), hardcoded data in Python, encyclopedic SKILL.md
- When bundling scripts, read `references/script-design.md`

### Pre-flight Critique

Two gates before testing — do not proceed if either fails.

**GATE 1 — Linter.** Run `python scripts/skill_lint.py <skill_directory>`. Fix all FAILs.

**GATE 2 — Pre-flight.** Follow the checklist in `references/skill-writing-guide.md` ("Pre-flight Critique"): token audit, self-critique (5 questions), optionally adversarial stress-test.

You can also run the mechanical gate check: `python scripts/gate_check.py <skill_directory> --gate preflight`

### Test Cases

Write 2-3 realistic test prompts + 1-2 trapped tests (inputs designed to trigger guardrails).
Save to `evals/evals.json` — see `references/schemas.md` for the schema.

---

## Running and evaluating test cases

When running evals, read `references/eval-workflow.md` for the full step-by-step procedure.

Summary: spawn with-skill + baseline runs in parallel → draft assertions while runs execute → grade each run → verify trapped tests triggered alerts → aggregate into benchmark → analyst pass → launch eval viewer → wait for human feedback.

### Critical eval rules (do NOT skip these)

**Directory naming convention**: Use `with_skill` and `without_skill` (or `old_skill`) as configuration directory names. The benchmark aggregator and eval viewer depend on these exact names to identify which is the primary vs baseline configuration. Other names will cause incorrect delta calculations.

**Grading field names**: Every expectation object in `grading.json` MUST have exactly these 3 fields: `text` (string — the assertion), `passed` (boolean), `evidence` (string — quote from output). Missing or renamed fields cause silent failures in the viewer and aggregator.

**`assertions_are_sufficient` gate**: After grading, the grader agent sets `assertions_are_sufficient: true/false`. If `false`, it means the assertions don't fully cover the eval's intent — you MUST add more assertions before proceeding. Do not skip this check. Enforce mechanically: `python scripts/gate_check.py <workspace>/iteration-N --gate assertions`. The gate also validates that every expectation has the 3 required fields (`text`, `passed`, `evidence`).

**Baseline validation (mandatory)**: Always run baseline (without_skill) alongside with_skill. Verify BOTH configurations have at least one successful run before proceeding to grading. A skill that scores 80% is only valuable if the baseline scores lower. If baseline ≈ with_skill, the skill adds no value — fix it before iterating.

**Idempotency**: Re-running the same eval should produce the same result (within statistical noise from `runs_per_query`). If results vary wildly between identical runs, the skill has a non-determinism problem — fix it before iterating. Each run must use its own output directory — do not rely on shared temp files or global state between parallel runs.

**Adversarial QA**: For EVALUATION skills (skills that judge or grade), adversarial QA via `agents/defender.md` is **mandatory**, not optional. EVALUATION skills that pass without adversarial testing are likely brittle.

### Practical steps

- For each run, save timing data from task notifications to `timing.json` immediately
- Use `python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>` to aggregate
- Launch viewer: `python -m eval-viewer.generate_review <workspace>/iteration-N --skill-name <name> --benchmark <path>`
  - In Cowork: add `--static <output_path>` (no browser available)
  - For iteration 2+: add `--previous-workspace <previous>`

**GATE 3 — Human review.** Generate the viewer, let the user review, then verify `feedback.json` exists BEFORE making any changes to the skill. This is a hard gate — do NOT modify the SKILL.md until the human has reviewed and feedback.json is present. Enforce: `python scripts/gate_check.py <workspace>/iteration-N --gate feedback`. Also run the assertions gate: `python scripts/gate_check.py <workspace>/iteration-N --gate assertions`.

**Chat-based feedback (Cowork / no browser):** If the user can't easily return a `feedback.json` file (e.g., static viewer in Cowork), collect feedback in chat instead. For each test case, ask the user what they think. Then write `feedback.json` yourself from their responses — same schema, same gate. See `references/eval-workflow.md` "Chat-based feedback collection" for the procedure.

---

## Improving the skill

When improving the skill, read `references/improvement-guide.md` for the full improvement checklist and iteration loop.

Summary: generalize (don't overfit) → cut before adding → explain the why → deduplicate across runs → draft then re-read → refresh evals.

**GATE 4 — Stagnation check.** After each iteration: `python -m scripts.aggregate_benchmark <workspace>/iteration-N --check-stagnation`. If regression → revert. If stagnation → pivot. If oscillation → more diverse tests.

Run: `python scripts/gate_check.py <workspace> --gate stagnation`

---

## Debugging a broken skill

When the user says "my skill doesn't work", "this skill is broken", or asks to debug/fix a skill:

1. **Reproduce**: Ask for the exact input that fails. Run it once to see the actual output.
2. **Triage**: Categorize the failure — wrong output, crash, partial output, inconsistent results, or "it works but poorly".
3. **Linter first**: Run `python scripts/skill_lint.py <skill_directory>` to check structural issues.
4. **Common failure patterns**:
   - Skill triggers on wrong inputs → fix description triggers and scope check
   - Output format wrong → check examples/ and output format instructions in SKILL.md
   - Missing context → check if references are loaded conditionally when they should be unconditional
   - Inconsistent results → check for non-determinism (missing examples, vague instructions, no self-diagnosis)
   - Script crashes → check imports, edge cases, missing dependencies
5. **Targeted fix**: Fix the specific issue, re-run the failing input, verify it passes.
6. **Regression check**: If the skill has evals, re-run them to make sure the fix didn't break other cases.

Do NOT start the full create-from-scratch flow for a debug request. Fix surgically.

---

## Advanced: Blind comparison

For rigorous A/B comparison between two skill versions. Read `agents/comparator.md` and `agents/analyzer.md`. Optional — most users won't need it.

---

## Description Optimization

After the skill is working, offer to optimize triggering. When optimizing, read `references/description-optimization.md` for the full workflow.

---

## Package and Present

If `present_files` tool is available:
```bash
python -m scripts.package_skill <path/to/skill-folder>
```
Then present the `.skill` file to the user.

---

## Environment-Specific Adaptations

When adapting for a specific environment, read `references/environment-adaptations.md` for full details.

**CLI dependency**: Several scripts (`run_eval.py`, `run_loop.py`, `improve_description.py`) invoke `claude -p` as a subprocess. They check for the CLI at startup and fail with a clear error if it's missing. If the user is on Claude.ai or Cowork without CLI access, you must run tests manually in conversation instead of using these scripts.

**Cowork**: subagents work, use `--static` for viewer, feedback downloads as file, description optimization works via `claude -p`. Editing installed skills: copy to `/tmp/`, edit there, package from copy.

**Claude.ai**: no subagents, no `claude -p` — run tests sequentially in conversation, skip baselines and blind comparison. Present results directly. Skip description optimization (requires CLI).

---

## Reference files

**Agents** (spawn as subagent prompts):
- `agents/grader.md` — Evaluate assertions against outputs. Reads `references/grading-format.md` for JSON schema.
- `agents/comparator.md` — Blind A/B comparison. Reads `references/grading-format.md` for JSON schema.
- `agents/analyzer.md` — Post-hoc analysis of why one version won + benchmark pattern analysis
- `agents/defender.md` — Adversarial Defender for EVALUATION skills
- `agents/example-distiller.md` — Distils I/O pairs into minimal `examples/` directory. Spawn when user provides examples.

**Scripts**:
- `scripts/skill_lint.py` — Structural linter. Run on every draft. Checks description, guardrails, sizes, context budget, portability. Use `--json` for machine-readable output.
- `scripts/quick_validate.py` — Lightweight frontmatter-only validation.
- `scripts/gate_check.py` — Mechanical gate enforcement (preflight, feedback, stagnation, assertions). Replaces manual checks. The assertions gate validates `assertions_are_sufficient` and grading field schema.

**References** (only load when needed — conditional on the current step):
- `references/schemas.md` — Read only when creating/validating evals.json, eval_metadata.json, timing.json, stagnation_check.json.
- `references/grading-format.md` — Read only when grading or analyzing runs (JSON formats for grading.json, comparison.json, etc.).
- `references/architecture-decision.md` — Read only when choosing architecture (task classification, scoring, pattern selection).
- `references/guardrails.md` — Read only when writing guardrails (self-diagnosis templates, circuit-breaker examples).
- `references/adversarial-qa.md` — Read only when building EVALUATION skills (mandatory adversarial QA).
- `references/script-design.md` — Read only when bundling scripts into a skill.
- `references/environment-adaptations.md` — Read only when adapting for Claude.ai or Cowork.
- `references/skill-writing-guide.md` — Read only when writing the SKILL.md (anatomy, budgets, style, anti-patterns, pre-flight).
- `references/skill-template.md` — Read only when starting a new SKILL.md from scratch (skeleton template).
- `references/description-optimization.md` — Read only when optimizing skill description/triggering.
- `references/trapped-test-cases.md` — Read only when writing trapped test cases.
- `references/eval-workflow.md` — Read only when running and evaluating test cases.
- `references/improvement-guide.md` — Read only when improving an existing skill after eval feedback.

**Multi-agent error handling**: When building Architecture C skills, every synthesizer must handle degraded inputs. See `references/architecture-decision.md` for the error handling pattern.

---

Please add steps to your TodoList to track progress. Include gates explicitly (GATE 1: linter, GATE 2: pre-flight, GATE 3: human review, GATE 4: stagnation check).
