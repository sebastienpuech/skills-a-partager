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
- **`skill-creator-v12`**: 29 tests on its scripts (`skill-creator-v12/tests/test_scripts.py`).

## What this copy is not

- A working copy, extracted from my private skills repository: the history is kept, but the
  personal usage log and cache files were removed, and references to my professional or personal
  repositories were replaced with generic mentions.
- Not a tool ready to install on your machine: some scripts assume my environment (paths,
  scheduled tasks). What you can read here is the method and the way it is measured.
