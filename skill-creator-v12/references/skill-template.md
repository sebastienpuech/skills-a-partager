# Skill Template

Use this skeleton as your starting point when writing a new SKILL.md.
Replace all `[PLACEHOLDERS]` with actual content. Delete comments after filling in.

---

```markdown
---
name: [skill-name]
description: >
  [Max 1024 chars. Use imperative phrasing: "Use this skill when..."
  Include: what it does + specific trigger phrases + implicit cases.
  Be slightly "pushy" to combat under-triggering.]
---

# [Skill Name]

[1-2 sentences: what this skill does and why it exists.]

## Gotchas

[Counter-intuitive facts, common pitfalls, things the agent wouldn't
discover on its own. This section has the highest value-per-token ratio
of anything in the skill. 3-5 bullet points.]

- [Gotcha 1: e.g., "The API silently truncates responses over 4K chars"]
- [Gotcha 2: e.g., "Column 'montant' can be negative for credit notes"]
- [Gotcha 3]

## Workflow

[Numbered steps. Be prescriptive where fragile, flexible where tolerant.]

1. [Step 1: Read/validate input]
   - Read `references/[domain-rules].md` when processing [condition]
2. [Step 2: Main processing]
3. [Step 3: Generate output]
4. [Step 4: Validate output]

[If TRANSFORMATION/GENERATION skill with examples:]
### Before processing: Load reference example
1. Read `examples/index.json`
2. Find the cluster matching the current input
3. Read the selected input/output pair
4. Use as concrete reference for the expected transformation

## Mandatory self-diagnosis

Before delivering the output, run these checks.
Never rationalize a suspicious result — diagnose it.

### Universal checks

1. **Proportionality**: is the output proportionate to the input?
   - A 5-page doc generating 200 comments → suspect
   - A 300-row dataset flagged at 100% → suspect
   - An empty or abnormally small output → suspect

2. **Uniformity**: is there an extreme or uniform result?
   - Everything flagged / nothing flagged → suspect
   - All scores identical → suspect
   - One error type > 50% of findings → suspect

3. **Plausibility**: pick 3 random results — would a domain expert
   find them sensible?

### Domain-specific checks

- [ ] [Check 1: e.g., "Total debit = total credit"]
- [ ] [Check 2: e.g., "Output row count ≥ 95% of input row count"]
- [ ] [Check 3: e.g., "Every comment cites a specific passage"]
- [ ] [Check 4: e.g., "At least 2 positive points identified"]

### What to do if a check fails

1. Do NOT deliver the output as-is
2. Explain the problem: "I detected [issue]. This probably indicates [diagnosis]."
3. Offer to fix and re-execute
4. If the fix is simple, apply it directly
```

---

## Architecture variants

**For Architecture B** (score 4-6), add between Workflow and Self-diagnosis:

```markdown
## Internal critique

STOP. You are no longer the producer. You are an external auditor
seeing this output for the first time.

| Question | Action if NO |
|----------|-------------|
| Does the output answer the original request? | Identify what's missing |
| Is the data internally consistent? | Verify totals, cross-refs |
| Would a domain expert validate this? | Identify weak points |
| Are there manifestly absurd results? | Diagnose the bug |
```

**For Architecture C** (score 7+), add an `agents/` directory and reference
the pattern from `references/architecture-decision.md`.
