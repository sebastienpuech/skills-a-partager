# Guardrails: Self-Diagnosis and Circuit-Breakers

Every skill, REGARDLESS of complexity score, must include at minimum
the self-diagnosis (Template A). Circuit-breakers in code are a free
bonus in terms of tokens.

The problem we're solving: an agent that produces an absurd result
doesn't question it. It rationalizes ("this reflects the high sensitivity
of the rules" instead of "100% flagged = the rule is broken").
Guardrails force doubt.

---

## Circuit-Breakers (in code, 0 tokens)

Circuit-breakers are Python code or conditions in scripts that refuse
to produce a manifestly absurd result.

### Universal Circuit-Breakers

```python
def circuit_breaker_check(results, total_input, context):
    alerts = []

    # CB-1: Disproportionate output
    if hasattr(results, 'flag_rate') and results.flag_rate > 0.60:
        alerts.append({
            "type": "QUARANTINE",
            "message": f"Flag rate {results.flag_rate:.0%} > 60%. "
                       "Probable mapping/threshold error. "
                       "Review configuration before trusting results."
        })

    # CB-2: Empty output
    if hasattr(results, 'count') and results.count == 0:
        alerts.append({
            "type": "ALERT",
            "message": "Zero results produced. "
                       "The skill likely failed to process the input."
        })

    # CB-3: Output smaller than input
    if hasattr(results, 'row_count'):
        if results.row_count < total_input * 0.95:
            alerts.append({
                "type": "ALERT",
                "message": f"Output has {results.row_count} rows vs "
                           f"{total_input} input. Data loss detected."
            })

    # CB-4: Suspicious uniformity
    if hasattr(results, 'categories'):
        max_pct = max(results.categories.values()) / sum(results.categories.values())
        if max_pct > 0.80:
            alerts.append({
                "type": "WARNING",
                "message": f"One category represents {max_pct:.0%} of results. "
                           "Output may lack discrimination."
            })

    return alerts
```

### Circuit-Breakers by Skill Type

**Data cleaning / transformation**:
```python
# After column mapping
def validate_column_mapping(df, mapping):
    alerts = []
    for role, col_name in mapping.items():
        if col_name is None:
            continue
        sample = df[col_name].dropna().head(10).tolist()
        sample_str = [str(v) for v in sample]

        if role == 'interviewer':
            avg_words = sum(len(s.split()) for s in sample_str) / max(len(sample_str), 1)
            if avg_words > 5:
                alerts.append(
                    f"Column '{col_name}' mapped as interviewer but contains "
                    f"long text (avg {avg_words:.0f} words). Sample: {sample_str[:3]}. "
                    f"Probably wrong column."
                )

        if role == 'respondent_id':
            unique_rate = df[col_name].nunique() / max(len(df[col_name].dropna()), 1)
            if unique_rate < 0.40:
                alerts.append(
                    f"Column '{col_name}' mapped as respondent_id but only "
                    f"{unique_rate:.0%} unique values. Not a unique identifier."
                )

    return alerts

# After each rule
def per_rule_circuit_breaker(rule_id, flag_count, total_records):
    rate = flag_count / max(total_records, 1)
    if rate > 0.60:
        return {
            "status": "QUARANTINED",
            "rule": rule_id,
            "rate": rate,
            "message": f"Rule {rule_id} flagged {rate:.0%} of records - "
                       "quarantined. Likely column mapping or threshold error."
        }
    return {"status": "APPLIED"}
```

**Document review / evaluation**:
```python
def validate_review_output(comments):
    alerts = []

    if len(comments) == 0:
        alerts.append("CRITICAL: Zero comments produced. Review likely failed.")
    elif len(comments) > 50:
        alerts.append(f"WARNING: {len(comments)} comments is likely noise.")
    elif len(comments) < 5:
        alerts.append(f"WARNING: Only {len(comments)} comments - possibly superficial.")

    no_citation = [c for c in comments if not c.get('passage_cited')]
    if no_citation:
        alerts.append(
            f"{len(no_citation)} comments have no source citation - "
            "these are unverifiable and should be removed or substantiated."
        )

    sections = [c.get('section', 'unknown') for c in comments]
    from collections import Counter
    top_section, top_count = Counter(sections).most_common(1)[0]
    if top_count / len(comments) > 0.50:
        alerts.append(
            f"{top_count}/{len(comments)} comments target section {top_section}. "
            "Review may be unbalanced."
        )

    return alerts
```

### Circuit-Breaker Quality Requirements

Having circuit-breakers is necessary but not sufficient. The linter checks for their PRESENCE, but YOU must ensure their QUALITY. A circuit-breaker must be **domain-specific** — not just a generic sanity check.

**Bad circuit-breakers** (technically pass the linter but provide no safety):
```python
# These are too generic to catch domain errors:
if len(output) > 0:  # passes on any non-empty output
    pass
assert result is not None  # passes on any result
if output_file.exists():  # passes if file was created, even if empty/wrong
    pass
```

**Good circuit-breakers** (catch domain-specific errors):
```python
# These check domain-invariant properties:
if total_debit != total_credit:  # accounting: balance must hold
    alerts.append("Debit/credit mismatch")
if flag_rate > 0.60:  # data cleaning: too many flags = bad rule
    alerts.append("Excessive flag rate")
if len(comments) > 0 and all(c.get('section') == comments[0].get('section') for c in comments):
    alerts.append("All comments target one section — review is unbalanced")
```

**Minimum requirement:** Each script must have at least 2 circuit-breakers that check properties SPECIFIC to the skill's domain. Generic checks (file exists, non-empty, non-null) don't count toward this minimum.

---

## Self-Diagnosis Templates

### Template A: Minimal Self-Diagnosis (EVERY skill)

Copy-paste at the end of every SKILL.md you create:

```markdown
## Mandatory self-diagnosis

Before delivering the output, run these checks.
NEVER rationalize a suspicious result - diagnose it.

### Universal checks

1. **Proportionality**: is the output proportionate to the input?
   - A 5-page document generating 200 comments -> suspect
   - A 300-row dataset flagged at 100% -> suspect
   - An empty or abnormally small output file -> suspect

2. **Uniformity**: is there an extreme or uniform result?
   - Everything flagged / nothing flagged -> suspect
   - All scores are identical -> suspect
   - A single error type represents >50% of findings -> suspect

3. **Plausibility**: are 3 concrete examples from the output plausible?
   - Reread 3 random results
   - Ask yourself: would a domain expert find this sensible?
   - If an "interviewer" is named "Very willing during the survey",
     that's a mapping bug, not a result

### Domain-specific checks

[REPLACE WITH 4-5 CHECKS SPECIFIC TO THIS SKILL'S DOMAIN]

### What to do if a check fails

1. DO NOT deliver the output as-is
2. Explain the detected problem to the user:
   "I detected a problem with the output: [description].
   This probably indicates [diagnosis]. I recommend [action]."
3. Offer to fix and re-execute
4. If the fix is simple, apply it directly
```

### Template B: Internal Critique (score 4-6)

Add this phase between execution and delivery:

```markdown
## Phase 2: Internal critique

STOP. You are no longer the producer. You are an external auditor seeing
this output for the first time. You have NO reason to defend it.

### Perspective shift

Reread the output with the intention of FINDING PROBLEMS:

| Question | Action if NO |
|----------|-------------|
| Does the output answer the original request? | Identify what's missing |
| Is the data internally consistent? | Verify totals, cross-refs |
| Would a domain expert validate this? | Identify weak points |
| Are there manifestly absurd results? | Diagnose the bug |
| Is the output better than an "average output"? | Identify what to improve |

### If corrections are needed

1. Fix it
2. Save the corrected version
3. Reread the corrected version with the same critical eyes
4. Deliver the corrected version with a changelog
```

---

## Domain-Specific Check Examples

### Data cleaning / transformation skill
```markdown
### Domain-specific checks
- [ ] No rule flags >60% of the dataset
- [ ] The interviewer column contains person names (not sentences or comments)
- [ ] At least 30% of the dataset is "clean"
- [ ] Average flag count per record is <5
- [ ] Output row count >= input row count
- [ ] First 5 rows of output contain actual data
```

### Document review / evaluation skill
```markdown
### Domain-specific checks
- [ ] Every comment cites an exact passage (section + page)
- [ ] No claim "the document doesn't mention X" without checking
      ALL sections and annexes
- [ ] At least 2 positive points identified
- [ ] Between 8 and 30 total comments
- [ ] Comments cover at least 5 different sections
```

### Generation / writing skill
```markdown
### Domain-specific checks
- [ ] The text references concrete elements from the input
- [ ] No generic filler paragraphs
- [ ] Tone is consistent throughout
- [ ] Length is within expected range (+/-20%)
- [ ] An expert reader wouldn't immediately identify it as AI-generated
```

### Data analysis skill
```markdown
### Domain-specific checks
- [ ] At least 3 analysis angles covered
- [ ] Each insight is supported by specific data
- [ ] Recommendations are actionable (not "further investigation needed")
- [ ] Analysis limitations are explicitly mentioned
- [ ] Conclusions don't contradict the presented data
```

### Accounting transformation skill
```markdown
### Domain-specific checks
- [ ] Total debit = total credit in output file
- [ ] Output row count = N x input row count (N = 2 to 4 for double-entry)
- [ ] No unknown accounts (all codes exist in the OHADA chart)
- [ ] Amounts are identical between input and output (no loss)
- [ ] A sample of 5 operations, manually verified, is correct
```
