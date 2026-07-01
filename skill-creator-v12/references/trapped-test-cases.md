# Trapped Test Cases: Design Guide

Trapped test cases are inputs designed to trigger the skill's guardrails. They verify that circuit-breakers and self-diagnosis actually work. A trapped test that passes cleanly (without any alert) means the guardrail is dead code.

## Design Principles

1. **The trap must be realistic.** Don't create absurd inputs that would never occur in production. The best traps are plausible edge cases that a real user might encounter.
2. **One trap per guardrail.** Each trapped test should target a specific circuit-breaker or self-diagnosis check. Don't try to trigger everything at once.
3. **The trap should be subtle enough to fool the skill, but obvious enough that a human reviewer would catch it.** If the trap is too easy, it doesn't test the guardrail. If it's too hard, even a correct guardrail might miss it.
4. **Document what SHOULD happen.** In the eval_metadata.json, set `"is_trapped_test": true` and describe the expected guardrail behavior in the assertions (e.g., "Output should contain a QUARANTINE alert").

## Templates by Task Type

### TRANSFORMATION Skills

**Trap 1: Column mapping error**
Create an input where a column has a misleading name. Example: a column named "interviewer" that actually contains long survey response text. The circuit-breaker should fire because average word count per cell > 5.

**Trap 2: Extreme flag rate**
Create an input where 70%+ of records would be flagged by the rules. The circuit-breaker should fire because flag_rate > 0.60 (the standard threshold from guardrails.md). Make sure the trap exceeds the threshold with margin — e.g., 70-80% flag rate when the threshold is 60%.

**Trap 3: Data loss**
Create an input with a specific row count, then modify the skill's input to cause some rows to be silently dropped (e.g., special characters in a key field). The circuit-breaker should detect output_rows < input_rows * 0.95.

**Trap 4: Balance violation (accounting)**
Create an input where one transaction has mismatched amounts. The debit/credit balance circuit-breaker should catch it.

### EVALUATION Skills

**Trap 1: False negative bait**
Include something in the source document that the skill is supposed to check for, but phrase it using synonyms or place it in an unexpected section (e.g., governance information buried in a footnote). The adversarial QA should catch and correct any "missing" claim.

**Trap 2: Over-commenting**
Provide a well-written document that has few real issues. If the skill produces > 30 comments, the circuit-breaker should fire for suspicious volume.

**Trap 3: Single-section bias**
Provide a document where Section 3 has obvious issues but other sections are subtle. If > 50% of comments target Section 3, the self-diagnosis should flag unbalanced coverage.

### GENERATION Skills

**Trap 1: Generic output test**
Provide two very different briefs and check if the skill produces meaningfully different outputs. If the outputs are >70% similar (by edit distance or structural overlap), the anti-mediocrity check should flag it.

**Trap 2: Missing requirements**
Provide a brief with 5 specific requirements. Intentionally make one requirement easy to overlook (buried in a long sentence). The critique phase should catch the omission.

### ANALYSIS Skills

**Trap 1: Obvious anomaly buried in data**
Include one dramatic outlier in a dataset (10x the mean). If the analysis doesn't mention it, the coverage check should flag missed dimensions.

**Trap 2: Contradictory conclusion**
Provide data where the overall trend contradicts the most visible subgroup. The contrarian step should surface this.

## How to Verify Trapped Tests

After running a trapped test, check for these in the output or transcript:
1. **Explicit alert text** — "QUARANTINE", "WARNING", "ALERT", "CRITICAL"
2. **Self-diagnosis flags** — "Detected problem", "Suspicious result", "Proportionality check failed"
3. **Modified behavior** — The skill offered to re-execute, warned the user, or refused to deliver

If NONE of these appear, the guardrail failed. Diagnose: was the trap too weak, the threshold too high, or the guardrail pattern wrong?
