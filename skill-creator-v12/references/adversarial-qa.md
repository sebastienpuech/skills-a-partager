# Adversarial Quality Assurance Module

This module is for skills that produce EVALUATIVE outputs (reviews, assessments,
analyses with claims about what is present/absent in a source document).
It runs AFTER the main output is produced, BEFORE delivery to the user.

## When to Use This Module

Use this module when the skill you're building:
- Produces review comments about a document
- Makes claims about what a document does or doesn't contain
- Evaluates compliance against criteria
- Flags issues or gaps in source material

Do NOT use for: pure transformations, content generation, or data cleaning
(those skills use circuit-breakers and self-diagnosis instead).

## Why This Exists

The dominant failure mode for any agent evaluating a document is the
false negative: claiming an element is absent/insufficient when it IS
present in the source. A single false negative destroys the credibility
of the entire deliverable. This module exists to eliminate them.

---

## Architecture

```
Step 1: Main skill output (the CRITIC's work) -> deliverable
Step 2: Spawn DEFENDER agent -> defense.json
Step 3: Deterministic resolution script -> resolutions.json
Step 4: Apply corrections to deliverable
Step 5: Quality report
```

## Step 2: Defender Agent

Spawn a sub-agent using `agents/defender.md` as the system prompt.

The Defender checks two types of claims:

1. **Absence claims** (default): "the document doesn't mention X", "X is absent", "X is insufficient" — the Defender searches exhaustively for synonyms and alternative formulations to verify or contest these.

2. **Accuracy claims** (optional, via Step 2b below): "covers 90% of risks", "thorough analysis" — quantitative or qualitative judgments that require independent verification against source data.

**Key insight:** A single false negative (claiming something is missing when it's present) destroys the credibility of the entire output. This step is mandatory for EVALUATION skills with >3 verifiable claims.

Save output to `<run-dir>/defense.json`.

## Step 3: Resolution (deterministic script)

Run a Python script that aligns each deliverable claim with the defense:

```python
import json

def resolve(deliverable_claims, defense):
    resolutions = []

    # Handle absence claims (from Step 2)
    for d in defense.get("defenses", []):
        if d["verdict"] == "CONTESTED" and d["evidence"]["found"]:
            if d["evidence"]["completeness"] == "COMPLETE":
                action = "DELETE"  # complete false negative
            else:  # PARTIAL
                action = "REWRITE"  # acknowledge what exists, specify what's missing
        else:
            action = "KEEP"
        resolutions.append({
            "claim_id": d["claim_id"],
            "action": action,
            "evidence": d.get("evidence"),
            "argument": d.get("argument")
        })

    # Handle accuracy checks (from Step 2b)
    for ac in defense.get("accuracy_checks", []):
        if ac["verdict"] == "INACCURATE":
            resolutions.append({
                "claim_id": ac["claim_id"],
                "action": "REWRITE",
                "evidence": {"found": True, "location": ac.get("evidence_location", ""), "passage": ac.get("actual_finding", ""), "completeness": "PARTIAL"},
                "argument": f"Claim is inaccurate: {ac.get('actual_finding', '')}"
            })
        else:
            resolutions.append({
                "claim_id": ac["claim_id"],
                "action": "KEEP",
                "evidence": None,
                "argument": "Accuracy verified"
            })

    stats = {
        "total": len(resolutions),
        "keep": sum(1 for r in resolutions if r["action"] == "KEEP"),
        "rewrite": sum(1 for r in resolutions if r["action"] == "REWRITE"),
        "delete": sum(1 for r in resolutions if r["action"] == "DELETE"),
    }

    # Circuit-breaker
    alerts = []
    fn_rate = (stats["rewrite"] + stats["delete"]) / max(stats["total"], 1)
    if fn_rate == 0 and stats["total"] > 5:
        alerts.append(
            "WARNING: 0% false negatives on " + str(stats["total"]) +
            " claims. Statistically improbable. The defense may have been too lax."
        )
    if stats["delete"] / max(stats["total"], 1) > 0.50:
        alerts.append(
            "CRITICAL: >50% of claims to delete. The initial deliverable is "
            "fundamentally unreliable. Consider regenerating."
        )

    return {"resolutions": resolutions, "statistics": stats, "alerts": alerts}
```

Save to `<run-dir>/resolutions.json`.

## Step 4: Apply Corrections

For each resolution:

- **KEEP**: no change
- **REWRITE**: modify the comment/passage to acknowledge what IS present
  in the source document, then specify what's still missing.
  Format: "The document addresses [topic] in [location] by mentioning
  [found elements]. However, it does not provide: (a) [gap 1],
  (b) [gap 2]."
- **DELETE**: remove the comment/passage from the deliverable

## Step 5: Quality Report

Add at the end of the deliverable (or present to the user):

```
## Adversarial QA
- Claims verified: [total]
- Validated as-is: [keep] ([%])
- Rewritten (info partially present): [rewrite] ([%])
- Deleted (false negatives): [delete] ([%])
- False negative rate: [fn_rate]%
```

## Step 2b: Accuracy Defender (for quantitative/qualitative claims)

The standard Defender (Step 2) checks PRESENCE — whether something exists in the source document. But many evaluation outputs also make ACCURACY claims: "the budget covers 90% of costs", "the risk section is thorough", "implementation is feasible". These need a different verification.

**When to use:** When the deliverable contains claims with numbers, percentages, qualitative judgments ("thorough", "insufficient", "comprehensive"), or comparative statements ("better than", "exceeds").

Spawn an additional sub-agent with this prompt:

```
You are an ACCURACY AUDITOR. Your sole objective: verify that quantitative and qualitative claims in the deliverable are supported by the source data.

For EACH claim that contains a number, percentage, rating, or qualitative judgment:

1. Identify the specific claim and its magnitude/assessment
2. Find the relevant data in the source document
3. Independently calculate/assess the value
4. Compare your assessment with the claim
5. If they match (within 10% for numbers): mark as ACCURATE
6. If they diverge: mark as INACCURATE with your calculation and the correct value
7. If the source data is insufficient to verify: mark as UNVERIFIABLE

You are not the advocate — you are the auditor. Report what the data shows, regardless of whether it supports the deliverable.

## Output JSON
{
  "accuracy_checks": [
    {
      "claim_id": "identifier",
      "claim_text": "the budget covers 90% of costs",
      "claim_type": "quantitative|qualitative",
      "source_data": "description of what the source shows",
      "auditor_assessment": "ACCURATE|INACCURATE|UNVERIFIABLE",
      "correct_value": "85% based on line-item analysis",
      "evidence": "Section 4.2, Table 3 shows total budget of X vs total costs of Y"
    }
  ],
  "statistics": {
    "total_checked": 0,
    "accurate": 0,
    "inaccurate": 0,
    "unverifiable": 0
  }
}
```

**Resolution for accuracy issues:** Apply the same resolution logic as Step 3:
- ACCURATE → KEEP
- INACCURATE → REWRITE with the correct value
- UNVERIFIABLE → REWRITE to note that the claim could not be verified from available data

**Update the Quality Report** (Step 5) to include accuracy stats alongside presence stats.

---

## Bypass Conditions

The adversarial phase can be bypassed ONLY if:
- The user explicitly asks for a quick/draft output
- The deliverable contains fewer than 3 verifiable claims
- The skill is a PURE TRANSFORMATION type and all Python circuit-breakers
  (debit==credit, row_count, etc.) pass

In all other cases, this phase is mandatory.

## Adaptation by Skill Type

| Deliverable type | What the Defender checks |
|-----------------|-------------------------|
| Review / evaluation | Absence claims ("doesn't mention X") |
| Analysis report | Conclusions vs source data |
| Content generation | Cited facts vs provided sources |
| Data cleaning / flags | Flags vs raw data (10% sample) |
| Accounting transformation | Debit/credit balance + sample of 5 operations |

For PURE TRANSFORMATION skills (accounting, formatting) where there are no
absence claims, replace the Defender with a Sample Verifier that manually
re-executes 5 operations and compares with the skill's output.
