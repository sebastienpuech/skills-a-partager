# Improvement Guide

## Improvement checklist

Before editing the SKILL.md, work through these questions in order. They
prevent the most common mistakes — overfitting, prompt bloat, cargo-culting.

1. **Generalize, don't overfit.** Would this change help with a prompt you
   haven't seen, or only this test case? If only this test case, reframe
   with a broader principle or structural change.

2. **Cut before adding.** Read the transcripts. If the skill makes the model
   waste time on unproductive steps, remove those first. A leaner prompt
   that doesn't mislead beats a longer one with more rules on top.

3. **Explain the why.** Transmit understanding, not commands. When the model
   understands *why* something matters, it generalizes better than from rote
   instructions. If you catch yourself writing ALWAYS or NEVER in caps,
   reframe as reasoning.

4. **Deduplicate across test runs.** If all subagents independently wrote
   similar helper scripts, bundle the script once in `scripts/`. Read
   `references/script-design.md` for agent-friendly script design.

5. **Draft, then re-read.** Write your revision, then look at it fresh
   before committing. Get into the user's head — what do they need?

6. **Refresh the evals.** Have requirements changed? Are assertions still
   aligned with what the skill produces? If the skill now outputs YAML but
   assertions check for JSON, fix the assertions.

## The iteration loop

1. Apply improvements
2. Rerun all test cases into `iteration-<N+1>/`, including baselines
3. Launch viewer with `--previous-workspace` pointing at previous iteration
4. **GATE 3**: wait for human review → verify `feedback.json` exists
5. Read feedback
6. **GATE 4**: run stagnation/regression check (see below)
7. If `assertions_are_sufficient` is false in any grading.json, fix first
8. Improve and repeat

## GATE 4 — Stagnation and Regression Check

Run after each iteration: `python -m scripts.aggregate_benchmark <workspace>/iteration-N --check-stagnation`

| Pattern | Action |
|---------|--------|
| **Regression** (drop >5%) | Revert to best version. Ask user: "Latest changes made things worse. Reverting to version N (X% pass rate). Try a different approach?" |
| **Stagnation** (<2% change over 3 iterations) | Stop current approach. Pivot diagnosis: stuck assertions? wrong architecture? wrong task type? Present options: different architecture, rethink approach, or accept and ship. |
| **Oscillation** (alternating up/down, 3+ iterations) | Likely overfitting to specific test cases. Add more diverse tests instead of tweaking. |
| **Steady improvement** (>2% each iteration) | Continue normally. |

**Version tracking**: snapshot SKILL.md before each improvement (`cp SKILL.md SKILL.md.vN`).
Track which iteration had the highest pass_rate. Offer rollback if current is worse.

Keep going until: user is happy, feedback is all empty, or no meaningful progress.
