# Designing Scripts for Agentic Use

When a skill bundles scripts in `scripts/`, those scripts will be run by an
agent in a non-interactive shell. A few design choices make scripts dramatically
easier for agents to use — and dramatically harder to misuse.

Read this reference when you're about to bundle a script into a skill.

## Hard requirements

**No interactive prompts.** Agents cannot respond to TTY prompts, password
dialogs, or confirmation menus. A script that blocks on input will hang
indefinitely. Accept all input via command-line flags, environment variables,
or stdin.

```
# Bad: hangs waiting for input
$ python scripts/deploy.py
Target environment: _

# Good: clear error with guidance
$ python scripts/deploy.py
Error: --env is required. Options: development, staging, production.
Usage: python scripts/deploy.py --env staging --tag v1.2.3
```

## Interface discovery: --help

`--help` output is the primary way an agent learns your script's interface.
Include a brief description, available flags, and usage examples:

```
Usage: scripts/process.py [OPTIONS] INPUT_FILE

Process input data and produce a summary report.

Options:
  --format FORMAT   Output format: json, csv, table (default: json)
  --output FILE     Write output to FILE instead of stdout
  --verbose         Print progress to stderr

Examples:
  scripts/process.py data.csv
  scripts/process.py --format csv --output report.csv data.csv
```

Keep it concise — the output enters the agent's context window.

## Error messages

When an agent gets an error, the message directly shapes its next attempt.
Say what went wrong, what was expected, and what to try:

```
Error: --format must be one of: json, csv, table. Received: "xml"
```

Not just: `Error: invalid input`

## Structured output

Prefer JSON or CSV over free-form text. Structured formats can be consumed
by both the agent and standard tools (jq, cut, awk).

Separate data from diagnostics: structured data to **stdout**, progress
messages and warnings to **stderr**.

## Idempotency

Agents may retry commands. Design for it:
- "Create if not exists" rather than "create and fail on duplicate"
- Overwrite-safe operations where possible
- Clear messaging when a no-op occurs ("already exists, skipping")

## Dry-run support

For destructive or stateful operations, a `--dry-run` flag lets the agent
preview what will happen before committing. This pairs well with the
Plan-Validate-Execute pattern described in SKILL.md.

## Exit codes

Use distinct exit codes for different failure types and document them in
`--help`:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Input file not found or unreadable |
| 3 | Processing error (partial results may exist) |
| 10 | Circuit-breaker triggered (output is suspect) |

## Script size limit: 300 lines max

This is a hard limit enforced by the linter (CB-5). Scripts over 300 lines
get truncated when agents read them into context, causing syntax errors and
silent failures. The agent doesn't even know the script is broken — it just
sees garbled code and improvises badly.

**When a script exceeds 300 lines, split it:**

```
scripts/
├── main.py          (<150 lines — orchestration, CLI, I/O)
├── rules.py         (domain logic, validation)
├── transform.py     (data transformation)
└── utils.py         (shared helpers)
```

The SKILL.md only mentions `main.py` — the agent runs it, and Python's import
system loads the rest without consuming context tokens. The helpers exist as
implementation details that never enter the LLM's context window.

## Externalize data, don't embed it

Large dictionaries, mappings, lookup tables, and rule sets must live in
external files (JSON, YAML, CSV), not as Python literals. The linter flags
scripts with 25+ consecutive lines of data entries (CB-8).

```python
# Bad: 200 lines of hardcoded mappings bloating the script
ACCOUNT_MAP = {
    "601100": {"ohada": "601", "label": "Achats marchandises"},
    "602200": {"ohada": "602", "label": "Achats matières"},
    # ... 198 more lines
}

# Good: data lives in a config file, script stays lean
import json
with open(Path(__file__).parent / "account_map.json") as f:
    ACCOUNT_MAP = json.load(f)
```

Put config files alongside the scripts in `scripts/` or in `assets/`.
This keeps scripts focused on logic and makes the data easy to review,
update, and reuse across multiple scripts.

## Predictable output size

Many agent harnesses truncate tool output beyond 10-30K characters. If your
script might produce large output:
- Default to a summary or reasonable limit
- Support `--offset` and `--limit` for pagination
- Support `--output <file>` to write to a file instead of stdout

## Dependency management

Prefer self-contained scripts with inline dependency declarations:

**Python (PEP 723 + uv):**
```python
# /// script
# dependencies = [
#   "beautifulsoup4>=4.12,<5",
# ]
# ///
```
Run with: `uv run scripts/extract.py`

Pin versions for reproducibility. State runtime prerequisites in your SKILL.md
or in the `compatibility` frontmatter field.
