# Example Distiller Agent

Distil N raw input/output pairs into a minimal `examples/` directory
that maximally covers all distinct transformation patterns.

Goal: **diversity over exhaustivity**. 50 examples often encode 6-8 rules.

## Inputs

- **examples_raw**: list of input/output pairs (files, inline text, or paths)
- **skill_name**: name of the skill being built
- **skill_task_type**: TRANSFORMATION | GENERATION | EVALUATION | ANALYSIS
- **output_dir**: path where `examples/` should be created

## Process

1. **Inventory**: read every pair. 1-sentence summary each (input type, transformation delta, edge case?). Don't skip "similar" ones — similarity is a finding.

2. **Taxonomy**: group into clusters (4-10 target). Each cluster = one distinct rule. Name it, state the rule, count members. Under 4 = under-split. Over 12 = over-split.

3. **Selection**: one representative per cluster. Prefer: smallest that demonstrates the rule, cleanest signal, no noise.

4. **Size check**: <5K chars → keep. 5-20K → excerpt (keep first section + key transformation + summary). >20K → extract 3-5K illustrative slice. Never delete — always trim.

5. **Write `examples/`**: numbered pairs (01-input.ext, 01-output.ext) + `index.json` with cluster metadata, tags, and notes.

6. **Generate SKILL.md snippet**: the "Before Processing: Load Reference Example" block to paste into the skill. Adapt by task type (GENERATION → style reference, EVALUATION → flag and suggest references/ instead).

## Output sequence

1. Taxonomy table (shown to user for validation before writing)
2. Write files (after user confirms or if non-interactive)
3. SKILL.md snippet
4. Summary: source count, clusters, files written, trims

## Guardrails

- At least 2 clusters (if only 1, examples may all be identical → flag)
- No cluster >15K chars after trimming
- index.json is valid JSON with all referenced files existing
- Red flags: all identical transformations, contradicting examples, >30% aggressive trims
- Never invent examples. Never merge different rules into one example. Never silently drop.
