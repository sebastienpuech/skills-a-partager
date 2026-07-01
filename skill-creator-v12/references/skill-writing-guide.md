# Skill Writing Guide

Read this reference when writing or editing a SKILL.md. It covers skill anatomy, context budgets, bundling examples, writing patterns, style guidance, and pre-flight critique.

---

## Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    ├── examples/   - Input/output pairs for in-context learning (few-shot)
    └── assets/     - Files used in output (templates, icons, fonts)
```

## Progressive Disclosure & Context Budget

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

**Context budget per layer** — these are hard limits enforced by the linter. Exceeding them causes context window overflow and script truncation in the skills you create:

| Layer | Max size | What goes here |
|-------|----------|----------------|
| SKILL.md body | 500 lines / 25K chars | Orchestration flow, decision logic, guardrails |
| Each agent .md | 80 lines / 4K chars | Role prompt, output format, constraints |
| Each Python script | 300 lines / 12K chars | One focused task; import helpers for more |
| Each reference .md | 300 lines / 15K chars | Domain knowledge, loaded conditionally |
| **Total startup load** | **< 50K chars** | SKILL.md + agents + unconditionally loaded refs |

If a file exceeds its budget, **extract content to a lower layer** — never delete it:
- SKILL.md too long → move domain-specific rules to `references/`, load conditionally
- Script too long → split into `main.py` (< 150 lines) + helper modules it imports
- Reference too long → split by topic into multiple files

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on **when** to read them (conditional loading)
- For large reference files (>300 lines), include a table of contents
- **Read-on-demand pattern**: Don't load references unconditionally at startup. Instead, gate them with conditions in SKILL.md. Write "Read `references/<your-domain-rules>.md` when processing input files" not "First, read `references/<your-domain-rules>.md`". This way the reference is only loaded into context when actually needed, saving tokens on invocations that don't need it.

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

## Bundling Input/Output Examples (Few-Shot Learning)

When a skill performs a transformation, formatting, or any task where "show me what the output should look like" is worth more than 100 lines of rules, **bundle real input/output pairs in an `examples/` directory**. These are the most token-efficient way to communicate complex expectations to the agent: one good example teaches more than a page of instructions.

**When to bundle examples:**
- TRANSFORMATION skills where the mapping rules are complex or numerous (accounting, data formatting, protocol conversion)
- GENERATION skills where the desired style/format is hard to describe in words
- Any skill where the user provides reference pairs during creation ("here's what the input looks like, here's what the output should be")

**When NOT to bundle examples:**
- EVALUATION/ANALYSIS skills where each input is unique (a proposal review doesn't benefit from seeing a different proposal's review)
- Skills where the rules are simple enough to state in 10 lines of instructions
- When the examples would be larger than 50K chars total — at that point they defeat the purpose

**Directory structure:**

```
my-skill/
└── examples/
    ├── index.json          (metadata: what each pair demonstrates)
    ├── 01-input.xlsx       (or .csv, .json, .txt — real format)
    ├── 01-output.xlsx
    ├── 02-input.csv
    └── 02-output.csv
```

The `index.json` describes each pair so the agent can pick the most relevant one:

```json
{
  "examples": [
    {
      "id": "01",
      "description": "Standard case: 15 entries, single currency, all accounts mapped",
      "input": "01-input.xlsx",
      "output": "01-output.xlsx",
      "tags": ["standard", "single-currency"]
    },
    {
      "id": "02",
      "description": "Edge case: multi-currency with unmapped accounts",
      "input": "02-input.csv",
      "output": "02-output.csv",
      "tags": ["multi-currency", "edge-case", "unmapped"]
    }
  ]
}
```

**How the SKILL.md should reference examples:**

```markdown
## Before processing

1. Read `examples/index.json`
2. Compare the user's input with the example descriptions
3. Read the input AND output of the most similar example
4. Use this pair as your reference for the expected transformation
```

**Keep examples small and focused.** Each pair should demonstrate one pattern, not be a full production file. A 15-row extract is better than a 500-row complete file. If the user provides large reference files, extract a representative subset. The linter's context budget (CB-7) will catch examples that are too large.

**During skill creation**: when the user provides input/output pairs, ask: "Should I bundle these as examples in the skill so it can use them as reference on every future execution?" If yes, **spawn `agents/example-distiller.md`** with the raw examples — do not bundle them manually. The distiller will cluster them by distinct rule, select one representative per cluster, trim oversized files, write the `examples/` directory, and generate the SKILL.md snippet to paste. Only proceed to write the SKILL.md after the distiller has completed and the user has validated the taxonomy table.

## Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

## Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

**Gotchas section** — One of the highest-value things a skill can contain is a list of counter-intuitive facts or common pitfalls that the agent wouldn't discover on its own. If the domain has "traps" (e.g., an API that silently truncates, a file format that looks like CSV but uses semicolons, a field name that means something different than it sounds), put them in a `## Gotchas` section near the top. These save more runs than any amount of generic instruction.

**Checklists for multi-step workflows** — When a skill involves a sequence of steps with dependencies or validation gates between them, a numbered checklist helps the agent track progress and not skip steps. Especially useful for workflows where step N depends on step N-1 succeeding.

**Plan-Validate-Execute** — For skills that do batch or destructive operations (bulk file renames, database writes, mass transformations), instruct the agent to first produce a plan (a preview of what will change), validate it against a source of truth or sanity checks, then execute. This catches errors before they happen — complementary to circuit-breakers which catch them after.

## Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

**Add what the agent doesn't know, omit what it does.** Don't explain what a PDF is or how JSON works — the model already knows. Focus the skill's token budget on what's genuinely novel: domain conventions, counter-intuitive edge cases, company-specific formats, and the gotchas. Every line that restates common knowledge is a line that dilutes the signal.

**Match specificity to fragility.** Within a skill, not everything needs the same level of prescription. Give freedom where multiple approaches work fine (e.g., "choose an appropriate chart type"), be prescriptive where a specific sequence is fragile or error-prone (e.g., "you must call the validation endpoint before submitting"). The goal is guardrails on the cliffs, not fences on the meadow.

**Avoid these context-bloating anti-patterns** — they are the #1 cause of broken skills in production:

- **The encyclopedic SKILL.md**: Putting all domain rules, mappings, and examples inline in SKILL.md instead of using references/ and scripts/. The body should contain orchestration logic, not data. If you find yourself writing 50+ lines of rules or mappings, stop and extract them.
- **The monolith script**: One Python file that does everything (reading, transforming, validating, writing). When it exceeds 300 lines, it gets truncated when loaded into context and the skill breaks silently. Split into focused modules that import each other.
- **Hardcoded data in Python**: Dictionaries or lists of 25+ entries embedded in Python code (e.g., accounting mappings, validation rules, field definitions). These belong in a `config.json` or `rules.yaml` file that the script reads at runtime — this keeps the script lean and the data maintainable.
- **Unconditional reference loading**: Writing "First, read references/X.md" at the top of the skill causes X.md to be loaded every time, even when it's not needed. Use conditional gating: "When processing [condition], read references/X.md for the relevant rules."

These anti-patterns don't just waste tokens — they cause real failures. A 660-line script gets truncated mid-function when an agent reads it, producing syntax errors. A 450-line SKILL.md dilutes instructions so badly that the model ignores the ones at the bottom (lost-in-the-middle effect). The budget limits in the Progressive Disclosure section exist to prevent these failures.

## Pre-flight Critique

Before moving to test cases, stop and critique the SKILL.md you just wrote. This catches structural problems early — much cheaper than discovering them after running evals.

1. **Run the linter**: `python scripts/skill_lint.py <skill_directory>`. Fix any FAIL before proceeding. The linter checks frontmatter, description quality, line count, **script sizes (CB-5)**, **total context budget (CB-7)**, **inline data blocks (CB-8)**, guardrails presence, circuit-breakers, reference linking, and portability. Pay special attention to SIZE failures — they cause context truncation and broken skills in production.

2. **Token audit** — if the linter passes, do a quick manual check:
   - List all files the skill will Read during a typical execution. Sum their sizes. If total > 50K chars, refactor: move content to references with conditional loading, or externalize data to JSON files.
   - Check each Python script: any script > 200 lines should be reviewed for opportunities to split into modules or externalize data.
   - The rule is **extract, never delete**. Moving rules from SKILL.md to `references/rules.md` preserves all information while reducing what's loaded upfront.

3. **Self-critique the draft** — reread the SKILL.md as if you're a different agent seeing it for the first time. Ask yourself these 5 questions:
   - Would a wrong output slip past the self-diagnosis section? (If yes, tighten the domain-specific checks.)
   - Is there an ambiguous instruction that two reasonable agents would interpret differently? (If yes, add an example or clarify.)
   - Does the skill handle the "boring edge case" — empty input, single-row input, input in a different language? (If not, add a note.)
   - Are there instructions that contradict each other? (Read the whole file looking for inconsistencies.)
   - Would removing any section make the skill noticeably worse? (If not, that section is bloat — cut it.)

4. **Adversarial stress-test** (if subagents are available — otherwise do it inline) — spawn a short-lived "devil's advocate" subagent with this prompt:

   > You are a hostile QA tester. You receive a skill's SKILL.md. Your job: invent 3 realistic user prompts that would break this skill or produce wrong/incomplete output. Focus on: (a) inputs at the boundary of what the skill handles, (b) inputs that exploit ambiguous instructions, (c) inputs where the guardrails would fail to catch an error. For each, explain WHY the skill would fail and what instruction is missing or flawed. Output JSON: [{"prompt": "...", "expected_failure": "...", "missing_instruction": "..."}]

   Review the results. If a failure is plausible, fix the skill now — it's much cheaper than discovering it during eval runs. If all 3 attacks are things the skill already handles, your draft is solid. Add the most interesting adversarial prompts to the trapped test cases.

5. Fix what you found, then move on. Don't spend more than 5 minutes on this — it's a focused pass, not a formal review.

6. **Description-scope alignment check** — Reread the frontmatter description and compare it against the actual SKILL.md body:
   - Does the description cover ALL major workflows in the SKILL.md? If the skill handles CSV→JSON AND JSON→YAML, but the description only mentions CSV→JSON, the skill will be under-triggered.
   - Does the description EXCLUDE workflows NOT covered? If the description says "any data transformation" but the SKILL.md only handles accounting, the skill will be wrongly triggered on medical data and fail.
   - Generate 3 test prompts from the description alone. Would the skill handle them well? If not, either narrow the description or expand the skill.
   - Check for orphaned trigger phrases — keywords in the description that don't map to any actual capability in the SKILL.md.
