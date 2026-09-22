# Two Claude Code skills: `mode-plan` and `skill-creator-v12`

*(Version française : [README.fr.md](README.fr.md))*

Two skills I built and use every day, shared here with their dated history (July to September
2026). I am not a developer: Claude Code writes the code; I design, validate and measure. This
repository is private and shared by invitation. The skills themselves are written in French.

## What is inside

| Folder | What the skill does | Where to start |
|---|---|---|
| `mode-plan/` | Before any complex project, forces a plan in 4 files (product spec, architecture, data model, work sessions), has it attacked by 4 critics in parallel, then a defender and a judge, and generates self-contained work prompts | `mode-plan/SKILL.md`, then `mode-plan/docs/plan-v4/journal.md` |
| `skill-creator-v12/` | Creates, improves and tests other skills: scoping, guardrails, adversarial review, evaluations against a baseline version | `skill-creator-v12/SKILL.md` |

## What is unusual in `mode-plan`

Four mechanisms, each born from a plan that failed. None of them appears in the planning skills
of `superpowers` (`brainstorming`, `writing-plans`, version 6.2.0, checked on 22 September 2026).

| Mechanism | What it does | Why it exists | Where |
|---|---|---|---|
| **Brief anchoring** | Before any debate, every claim of fact in the brief ("X is not installed", "the file does not exist") is checked by a command, never from memory | A full run (4 critics × 3 rounds, 45 confirmed critiques, 433k tokens, 57 minutes) planned work that was already deployed, because nobody checked the brief's premises | `SKILL.md`, step 1.6 |
| **Adversarial debate room** | 4 critics in parallel, then a defender, then a judge; merging and convergence are done by script, not by a model | A plan is judged against its objections, not against its author's confidence | `SKILL.md`, phase 3 |
| **Verified citations** | The defender and the judge quote the plan; a script checks that every quoted passage really exists, with no model in the loop | Nothing checked that their quotes were real | `SKILL.md`, step 3.4bis |
| **The plan that ends** | Every plan carries a global stop condition: an acceptance recipe frozen on real cases, read by someone other than its producer, plus frozen decisions and a rule for surprises | 7 successive plans reached all their milestones, and the project never ended | `SKILL.md`, step 2.4ter |

The final plan also goes through 16 automatic checks (C1 to C16, `scripts/self_diagnosis.py`),
and the skill reads the index of past lessons before writing. These are design differences, not
a measured win: no head-to-head comparison of plan quality against another tool has been run.

## What is measured, and where to check it

Every number points to the file that contains it.

- **`mode-plan` is checked by scripts, not by the impression it leaves.** From the journal
  (`mode-plan/docs/plan-v4/journal.md`): `run_evals` 19 of 19, replay of the adversarial debate
  6 of 6.
- **An option is only wired in if its gain clears a threshold set in advance.** Generating several
  candidates ("best-of-N"): mean score 0.45 without, 0.5625 with, on 8 cases chosen before the
  measurement; gain threshold 0.03. It stays opt-in. Same journal.
- **The skill was audited against itself, and the audit caught it out.** Report of 3 July 2026
  (`mode-plan/docs/audit-2026-07-03-skill-reviewer-v2/rapport.md`): the framing holds, but one
  verifier went green if the folder of held-out cases was simply deleted. For a skill whose thesis
  is "trust comes from the verifiers", that is the defect that matters most: it is written down,
  not hidden.
- **The evaluation cases are published with their verdicts**, rejected plans included
  (`mode-plan/evals/ensemble/`).
- **An option that did not earn its place was rejected, and the rejection kept.** An ensemble of
  verifiers, tried on 29 July 2026 on 8 live cases: 0.875 without, 0.875 with, a gain of zero
  against a threshold of 0.03. Rejected by a human decision, switched off.
- **`skill-creator-v12`**: 29 tests on its scripts (`skill-creator-v12/tests/test_scripts.py`).

## What does not work

`mode-plan` has a weekly self-improvement loop. It runs, logs, and has never improved anything:
11 passes from 2 July to 20 September 2026, none of them committed a change, and its capability
score has stayed frozen at 0.6667 since 28 July. It works as a weekly health check; as an
improvement engine, it has not delivered. That log is part of my private working files and is
not included in this copy.

## What this copy is not

- A working copy, extracted from my private skills repository: the history is kept, but the
  personal usage log and cache files were removed, and references to my professional or personal
  repositories were replaced with generic mentions.
- Not a tool ready to install on your machine: some scripts assume my environment (paths,
  scheduled tasks). What you can read here is the method and the way it is measured.
