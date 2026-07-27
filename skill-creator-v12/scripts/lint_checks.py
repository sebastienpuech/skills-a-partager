#!/usr/bin/env python3
"""Lint check functions for skill_lint.py."""

import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required by lint_checks.py. Install: pip install pyyaml")


def parse_frontmatter(content: str) -> dict | None:
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except Exception:
        return None


def count_lines(text: str) -> int:
    return len(text.strip().splitlines())


def check_skill_md_exists(skill_path: Path):
    p = skill_path / "SKILL.md"
    if p.exists():
        return True, "SKILL.md exists"
    return False, "SKILL.md not found"


def check_frontmatter(content: str):
    fm = parse_frontmatter(content)
    if fm is None:
        return False, "Missing or unparseable YAML frontmatter"
    missing = [k for k in ("name", "description") if k not in fm]
    if missing:
        return False, f"Frontmatter missing required fields: {', '.join(missing)}"
    return True, "Frontmatter OK"


def check_description_quality(content: str):
    fm = parse_frontmatter(content)
    if not fm:
        return False, "Cannot parse frontmatter"
    desc = str(fm.get("description", ""))
    issues = []
    if len(desc) < 80:
        issues.append(f"too short ({len(desc)} chars) — aim 100-300 with trigger phrases")
    trigger_keywords = ["use this skill", "trigger", "when the user", "whenever", "use when", "also trigger"]
    if not any(kw in desc.lower() for kw in trigger_keywords):
        issues.append("lacks trigger phrases (e.g. 'Use this skill whenever…')")
    if issues:
        return False, "; ".join(issues)
    return True, "Description OK"


def check_description_scope(content: str):
    fm = parse_frontmatter(content)
    if not fm:
        return True, "Cannot parse (skipping scope check)"
    body_match = re.match(r'^---\n.*?\n---\n(.*)', content, re.DOTALL)
    if not body_match:
        return True, "Cannot extract body (skipping)"
    desc, body = str(fm.get("description", "")).lower(), body_match.group(1).lower()
    action_words = re.findall(r'\b(convert|transform|generate|create|review|evaluate|clean|analyze|extract|merge|split|fill|format)\b', desc)
    missing = [w for w in set(action_words) if w not in body]
    if missing:
        return False, f"Description mentions {', '.join(missing)} not in body"
    return True, "Description-body alignment OK"


def check_line_count(content: str):
    n = count_lines(content)
    if n > 500:
        return False, f"Line count {n} > 500 limit"
    if n > 400:
        return True, f"Line count {n} approaching 500 (consider trimming)"
    return True, f"Line count {n} OK"


def check_script_sizes(skill_path: Path):
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return True, "No scripts/ dir"
    py_files = [f for f in scripts_dir.glob("*.py") if not f.name.startswith("__")]
    if not py_files:
        return True, "No Python files"
    oversized = [f"{f.name} ({count_lines(f.read_text(encoding="utf-8", errors="replace"))} lines)" for f in py_files if count_lines(f.read_text(encoding="utf-8", errors="replace")) > 300]
    if oversized:
        return False, f"Scripts > 300 lines: {', '.join(oversized)}"
    return True, f"All {len(py_files)} scripts within 300-line limit"


def check_context_budget(skill_path: Path, content: str):
    """Estimate startup context: SKILL.md + agents (always) + unconditional refs.
    Refs are conditional if SKILL.md uses "when/if/only" before the filename."""
    total = len(content)
    file_sizes = {"SKILL.md": len(content)}
    counted_refs = []
    skipped_refs = []

    agents_dir = skill_path / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.md"):
            size = len(f.read_text(encoding="utf-8", errors="replace"))
            file_sizes[f"agents/{f.name}"] = size
            total += size

    refs_dir = skill_path / "references"
    if refs_dir.exists():
        lower_content = content.lower()
        for f in refs_dir.iterdir():
            if not f.is_file():
                continue
            if f"`references/{f.name}`" not in content and f"`{f.name}`" not in content and f.name not in content:
                skipped_refs.append(f.name)
                continue
            escaped = re.escape(f.name)
            cond = [rf"(?:if|when|only)\b.*{escaped}", rf"{escaped}.*\b(?:if needed|as needed|only when|only if)",
                    rf"read only (?:when|if).*{escaped}"]
            if any(re.search(p, lower_content) for p in cond):
                skipped_refs.append(f.name)
                continue
            size = len(f.read_text(encoding="utf-8", errors="replace"))
            file_sizes[f"references/{f.name}"] = size
            counted_refs.append(f.name)
            total += size

    if total > 50_000:
        largest = sorted(file_sizes.items(), key=lambda x: -x[1])[:3]
        detail = ", ".join(f"{n} ({sz//1000}K)" for n, sz in largest)
        return False, f"Context {total//1000}K > 50K limit. Largest: {detail}"
    return True, f"Context {total//1000}K OK (agents: always, refs unconditional: {len(counted_refs)}, refs conditional/skipped: {len(skipped_refs)})"


def check_inline_data_blocks(skill_path: Path, content: str):
    issues = []
    for block in re.findall(r'```[\s\S]*?```', content):
        if count_lines(block) > 30:
            issues.append("Code block > 30 lines")
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.glob("*.py"):
            if f.name.startswith("__"):
                continue
            in_block, max_block = 0, 0
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if re.match(r'^["\'].*["\']:\s', stripped) or (re.match(r'^[\d"\'{(]', stripped) and stripped.endswith(',')):
                    in_block += 1
                    max_block = max(max_block, in_block)
                else:
                    in_block = 0
            if max_block > 25:
                issues.append(f"{f.name}: {max_block} lines inline data")
    if issues:
        return False, "; ".join(issues[:3])
    return True, "No large inline data blocks"


def check_self_diagnosis(content: str):
    lower = content.lower()
    markers = ["self-diagnosis", "self diagnosis", "auto-diagnostic", "mandatory self-diagnosis"]
    if any(m in lower for m in markers):
        return True, "Self-diagnosis found"
    if "guardrails.md" in content:
        return True, "References guardrails.md"
    return False, "No self-diagnosis section"


def check_circuit_breakers(skill_path: Path):
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return True, "No scripts/"
    py_files = list(scripts_dir.glob("*.py"))
    if not py_files:
        return True, "No Python files"
    cb_patterns = [r"circuit.?breaker", r"QUARANTINE", r"flag.?rate", r"assert ", r"raise\s+ValueError", r"alerts\.append", r"if\s+.*>\s*0\.\d", r"if\s+len\(.*\)\s*[>=<]"]
    files_with_cb = sum(1 for f in py_files if not f.name.startswith("__") and any(re.search(p, f.read_text(encoding="utf-8", errors="replace")) for p in cb_patterns))
    if files_with_cb == 0:
        return False, "No circuit-breaker patterns in scripts"
    return True, f"{files_with_cb}/{len(py_files)} have circuit-breakers"


def check_circuit_breaker_quality(skill_path: Path):
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return True, "No scripts/"
    py_files = [f for f in scripts_dir.glob("*.py") if not f.name.startswith("__")]
    if not py_files:
        return True, "No Python files"
    domain_patterns = [r"flag.?rate", r"QUARANTINE", r"balance", r"debit.*credit|credit.*debit", r"row.?count", r"threshold", r"rate\s*>", r"rate\s*<", r"\.nunique\(\)", r"avg.*words|words.*avg", r"alerts\.append", r"mismatch", r"violation", r"inconsisten"]
    files_with_domain_cb = sum(1 for f in py_files if any(re.search(p, f.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE) for p in domain_patterns))
    if files_with_domain_cb == 0 and len(py_files) > 0:
        return False, "No domain-specific circuit-breakers found"
    return True, f"{files_with_domain_cb}/{len(py_files)} have domain-specific breakers"


def check_references_linked(skill_path: Path, content: str):
    refs_dir = skill_path / "references"
    if not refs_dir.exists():
        return True, "No references/"
    ref_files = [f.name for f in refs_dir.iterdir() if f.is_file()]
    if not ref_files:
        return True, "references/ empty"
    unlinked = [f for f in ref_files if f not in content]
    if unlinked:
        return False, f"Unlinked: {', '.join(unlinked)}"
    return True, f"All {len(ref_files)} refs linked"


def check_examples_structure(skill_path: Path, content: str):
    examples_dir = skill_path / "examples"
    if not examples_dir.exists():
        return True, "No examples/"
    issues = []
    index_file = examples_dir / "index.json"
    if not index_file.exists():
        issues.append("Missing index.json")
    else:
        try:
            data = json.loads(index_file.read_text(encoding="utf-8", errors="replace"))
            examples = data.get("examples", [])
            if not examples:
                issues.append("Empty examples array")
            else:
                for ex in examples:
                    for key in ("input", "output"):
                        fname = ex.get(key, "")
                        if fname and not (examples_dir / fname).exists():
                            issues.append(f"Missing {fname}")
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON: {e}")
    if "examples/" not in content and "index.json" not in content:
        issues.append("Not referenced in SKILL.md")
    total_size = sum(f.stat().st_size for f in examples_dir.rglob("*") if f.is_file())
    if total_size > 100_000:
        issues.append(f"Size {total_size//1000}K > 100K")
    if issues:
        return False, "; ".join(issues[:3])
    return True, "examples/ OK"


def check_agents_have_instructions(skill_path: Path):
    agents_dir = skill_path / "agents"
    if not agents_dir.exists():
        return True, "No agents/"
    agent_files = list(agents_dir.glob("*.md"))
    if not agent_files:
        return True, "No .md files"
    thin_agents = [f.name for f in agent_files if count_lines(f.read_text(encoding="utf-8", errors="replace")) < 10]
    if thin_agents:
        return False, f"Thin agents (< 10 lines): {', '.join(thin_agents)}"
    return True, f"All {len(agent_files)} agents OK"


def check_architecture_documented(content: str):
    markers = ["architecture a", "architecture b", "architecture c", "single agent", "multi-agent", "multi agent", "complexity score", "complexity scoring", "debate room", "expert panel", "refinement loop", "tournament"]
    if any(m in content.lower() for m in markers):
        return True, "Architecture documented"
    return True, "No explicit architecture (OK)"


def check_eval_schema(skill_path: Path):
    evals_dir = skill_path / "evals"
    if not evals_dir.exists():
        return True, "No evals/"
    evals_json = evals_dir / "evals.json"
    if not evals_json.exists():
        return True, "No evals.json"
    try:
        data = json.loads(evals_json.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    if "evals" not in data:
        return False, "Missing 'evals' key"
    evals = data["evals"]
    if not isinstance(evals, list):
        return False, "evals should be a list"
    for i, ev in enumerate(evals):
        if "prompt" not in ev:
            return False, f"eval[{i}] missing 'prompt'"
    return True, f"evals.json OK ({len(evals)} cases)"


def check_no_hardcoded_paths(content: str):
    patterns = [r"/Users/\w+", r"C:\\Users\\\w+", r"/home/\w+", r"/sessions/\w+"]
    found = []
    for p in patterns:
        matches = re.findall(p, content)
        if matches:
            found.extend(matches[:2])
    if found:
        return False, f"Hardcoded paths: {', '.join(found[:3])}"
    return True, "No hardcoded paths"
