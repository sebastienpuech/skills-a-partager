#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_diagnosis.py - Circuit-breakers for mode-plan v3.3

Replaces v2.0 LLM-based self-diagnosis with binary Python assertions.
0 token, 100% reliable on these checks.

Usage:
    python3 self_diagnosis.py <project_dir> [--type=app|skill|doc] [--memory=...]

Exit codes:
    0 = all checks pass
    1 = at least one failure (details in stdout JSON)
    2 = usage error
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS_DIR.parent


def err(msg):
    print(json.dumps(msg, ensure_ascii=False), file=sys.stderr)


REQUIRED_FILES = ["spec_produit.md", "archi.md", "data_model.md"]
SESSIONS_FILE = "sessions_claude_code.md"

MIN_LINES = {
    "spec_produit.md": 80,
    "archi.md": 60,
    "data_model.md": 40,
    "sessions_claude_code.md": 30,
}

PLACEHOLDER_PATTERNS = [
    r"\[A COMPLETER\]",
    r"\[\xc0 COMPLETER\]",
    r"\[TODO\]",
    r"\[XXX\]",
    r"\[\.\.\.\]",
    r"\bTBD\b",
    r"\bFIXME\b",
    r"\bPLACEHOLDER\b",
]
# Add the accented version explicitly using unicode escape
PLACEHOLDER_PATTERNS.append("\\[À COMPLÉTER\\]")

VALID_RESET_VALUES = ["nouvelle fenêtre", "nouvelle fenetre", "/clear", "continuer"]


def check_files_exist(project_dir):
    """C1: required files exist."""
    fails = []
    for fname in REQUIRED_FILES:
        if not (project_dir / fname).is_file():
            fails.append("C1: missing required file " + fname)
    return fails


def check_min_lines(project_dir):
    """C2: each file exceeds min line threshold."""
    fails = []
    for fname, threshold in MIN_LINES.items():
        path = project_dir / fname
        if not path.is_file():
            continue
        n = sum(1 for _ in path.open(encoding="utf-8"))
        if n < threshold:
            fails.append(
                "C2: " + fname + " has " + str(n) + " lines, required >= "
                + str(threshold) + " (probable empty template)"
            )
    return fails


def check_no_placeholders(project_dir):
    """C3: no leftover placeholders from templates."""
    fails = []
    pattern = re.compile("|".join(PLACEHOLDER_PATTERNS))
    for fname in REQUIRED_FILES + [SESSIONS_FILE]:
        path = project_dir / fname
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        matches = pattern.findall(content)
        if matches:
            samples = list(set(matches))[:3]
            fails.append(
                "C3: " + fname + " contains " + str(len(matches))
                + " unfilled placeholders (samples: " + str(samples) + ")"
            )
    return fails


def check_skill_memory(project_dir, memory):
    """C4: if type=skill and memory!=aucune, required sections present."""
    if memory == "aucune":
        return []
    fails = []
    spec = project_dir / "spec_produit.md"
    if spec.is_file():
        content = spec.read_text(encoding="utf-8")
        if not re.search(r"##\s+Mémoire du skill", content, re.IGNORECASE):
            fails.append(
                "C4: type=skill with memory!=aucune but spec_produit.md "
                "lacks section '## Memoire du skill'"
            )
    archi = project_dir / "archi.md"
    if archi.is_file():
        content = archi.read_text(encoding="utf-8")
        keywords = ["interactions", "issues", "proposed_fixes"]
        missing = [k for k in keywords if k not in content.lower()]
        if missing:
            fails.append("C4: archi.md does not describe memory files: " + str(missing))
    return fails


def check_sessions_structure(project_dir):
    """C5: if sessions_cc.md exists, minimal structure present."""
    sessions_path = project_dir / SESSIONS_FILE
    if not sessions_path.is_file():
        return []
    content = sessions_path.read_text(encoding="utf-8")
    fails = []
    if not re.search(r"règle de fer", content, re.IGNORECASE):
        fails.append("C5: sessions_claude_code.md lacks 'regle de fer' header")
    sessions = re.findall(r"###\s+Session\s+\d+", content)
    if not sessions:
        fails.append("C5: sessions_claude_code.md has 0 sessions defined")
    elif len(sessions) > 30:
        fails.append(
            "C5: sessions_claude_code.md has " + str(len(sessions))
            + " sessions (>30 is suspicious, probable over-split)"
        )
    return fails


def check_critic_output(project_dir):
    """C6: if .mode-plan/verdict.json exists, parses correctly."""
    verdict_path = project_dir / ".mode-plan" / "verdict.json"
    if not verdict_path.is_file():
        return []
    try:
        data = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return ["C6: verdict.json fails to parse: " + str(e)]
    fails = []
    required_keys = {"verdicts", "statistiques", "verdict_global"}
    missing = required_keys - data.keys()
    if missing:
        fails.append("C6: verdict.json missing keys: " + str(missing))
    return fails


def check_patches_appended(project_dir):
    """C7: if verdict requires patches, files have a ## Patches strategiques section."""
    verdict_path = project_dir / ".mode-plan" / "verdict.json"
    if not verdict_path.is_file():
        return []
    try:
        data = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if data.get("verdict_global") not in {"patch_required", "major_revision"}:
        return []
    fails = []
    found = False
    for fname in REQUIRED_FILES:
        path = project_dir / fname
        if not path.is_file():
            continue
        if re.search(r"##\s+Patches\s+stratégiques\s+v\d+\.\d+",
                     path.read_text(encoding="utf-8")):
            found = True
            break
    if not found:
        confirmed = sum(1 for v in data.get("verdicts", [])
                        if v.get("verdict") in ("CONFIRMÉE", "CONFIRMEE"))
        if confirmed > 0:
            fails.append(
                "C7: verdict has " + str(confirmed) + " confirmed patches but no "
                "file has a '## Patches strategiques vX.Y' section"
            )
    return fails


def check_regle_de_fer_in_sessions(project_dir):
    """C8: each session prompt includes the 'regle de fer' bloc."""
    sessions_path = project_dir / SESSIONS_FILE
    if not sessions_path.is_file():
        return []
    content = sessions_path.read_text(encoding="utf-8")
    sessions = re.split(r"(?=###\s+Session\s+\d+)", content)
    fails = []
    for sess in sessions[1:]:
        prompt_match = re.search(r"\*\*Prompt\*\*\s*:?\s*```([\s\S]+?)```", sess)
        if prompt_match:
            prompt_body = prompt_match.group(1)
            if "règle de fer" not in prompt_body.lower():
                header = re.match(r"###\s+(Session\s+\d+[^\n]*)", sess)
                name = header.group(1) if header else "unknown"
                fails.append(
                    "C8: " + name.strip() + " prompt lacks 'regle de fer' bloc"
                )
    return fails[:5]


def check_reset_contexte_per_session(project_dir):
    """C9 (v3.1): each session has a valid 'Reset contexte' field."""
    sessions_path = project_dir / SESSIONS_FILE
    if not sessions_path.is_file():
        return []
    content = sessions_path.read_text(encoding="utf-8")
    sessions = re.split(r"(?=###\s+Session\s+\d+)", content)
    fails = []
    for sess in sessions[1:]:
        header_match = re.match(r"###\s+(Session\s+\d+[^\n]*)", sess)
        name = header_match.group(1).strip() if header_match else "unknown"
        reset_match = re.search(
            r"\*\*Reset\s+contexte\*\*\s*:\s*[`*]?([^`*\n(]+?)[`*]?\s*(?:\(|$)",
            sess,
            re.IGNORECASE | re.MULTILINE,
        )
        if not reset_match:
            fails.append(
                "C9: " + name + " lacks 'Reset contexte' field (v3.1+ requires it). "
                "Add one of: 'nouvelle fenetre', '/clear', 'continuer'."
            )
            continue
        value = reset_match.group(1).strip().lower()
        if not any(v.lower() in value for v in VALID_RESET_VALUES):
            fails.append(
                "C9: " + name + " 'Reset contexte' value '" + value
                + "' not in {nouvelle fenetre, /clear, continuer}"
            )
    return fails[:5]


def check_harness_coverage(project_dir):
    """C10 (v3.3, gated by --harness=on): plan files carry the harness sections."""
    fails = []
    spec = project_dir / "spec_produit.md"
    if spec.is_file():
        c = spec.read_text(encoding="utf-8").lower()
        has_anchor = (
            "harnais" in c
            or ("golden set" in c and "assertion" in c)
            or "signal de succès" in c
            or "signal de succes" in c
        )
        if not has_anchor:
            fails.append(
                "C10: spec_produit.md lacks a success-signal / harness section "
                "(H1: golden set + assertions). See references/harnais.md."
            )
    archi = project_dir / "archi.md"
    if archi.is_file():
        c = archi.read_text(encoding="utf-8").lower()
        has_layer = ("harnais" in c) or (
            ("vérif" in c or "verif" in c)
            and ("garde-fou" in c or "garde fou" in c or "budget" in c
                 or "observabilit" in c)
        )
        if not has_layer:
            fails.append(
                "C10: archi.md lacks a harness layer (H2/H6: verification + "
                "guardrails/budget/observability). See references/harnais.md."
            )
    return fails


def check_autoimprove_loop(project_dir):
    """C11 (v3.5, gated by --autoimprove=on, skill only): the plan specifies the
    self-improvement loop (signal + memory + engine + trigger). Lenient: anchors.

    Cf. references/harnais.md (boucle d'auto-amélioration) + spec_produit.md §11.
    """
    fails = []
    spec = project_dir / "spec_produit.md"
    if spec.is_file():
        c = spec.read_text(encoding="utf-8").lower()
        has_loop = (
            "auto-amélioration" in c
            or "auto-amelioration" in c
            or "skill-auto-improver" in c
            or ("boucle" in c and "amélior" in c)
            or ("boucle" in c and "amelior" in c)
        )
        if not has_loop:
            fails.append(
                "C11: spec_produit.md (skill) lacks a self-improvement loop section "
                "(skill-auto-improver: signal + memory + engine + trigger). "
                "See references/harnais.md + spec_produit.md §11."
            )
    return fails


def check_handoff_spec(project_dir):
    """C12 (v3.6, gated by --handoff=on): a repo-resident agent spec was generated
    (CLAUDE.md or AGENTS.md) so the plan lives in the repo, not pasted.

    Cf. references/handoff-cc.md (Phase 4.3bis).
    """
    fails = []
    has = (project_dir / "CLAUDE.md").is_file() or (project_dir / "AGENTS.md").is_file()
    if not has:
        fails.append(
            "C12: no repo handoff spec (CLAUDE.md or AGENTS.md) in the plan folder. "
            "mode-plan v3.6 must generate one (Phase 4.3bis) so the plan is "
            "repo-resident, not pasted. See references/handoff-cc.md."
        )
    return fails


def check_selfeval(project_dir):
    """C13 (v4.0, gated by --selfeval=on): le self-golden-set du SKILL existe et
    tourne, et le grader-of-graders passe. Porte sur le skill lui-même (SKILL_ROOT),
    pas sur project_dir. Cf. archi §5.
    """
    fails = []
    selfeval_dir = SKILL_ROOT / "evals" / "selfeval"
    if not selfeval_dir.is_dir() or not any(selfeval_dir.glob("S*/expected.json")):
        return ["C13: evals/selfeval/ absent ou vide (self-golden-set manquant). "
                "Voir mode-plan v4.0 Session 1."]
    # sys.executable (jamais 'python3') pour robustesse Windows.
    se = SCRIPTS_DIR / "self_eval_debate.py"
    me = SCRIPTS_DIR / "_meta_eval.py"
    try:
        r1 = subprocess.run([sys.executable, str(se), "--replay"],
                            capture_output=True, text=True, encoding="utf-8")
        if r1.returncode != 0:
            fails.append(f"C13: self_eval_debate.py --replay a échoué (exit {r1.returncode})")
        r2 = subprocess.run([sys.executable, str(me)],
                            capture_output=True, text=True, encoding="utf-8")
        if r2.returncode != 0:
            fails.append(f"C13: _meta_eval.py (grader-of-graders) a échoué (exit {r2.returncode})")
    except OSError as e:
        fails.append(f"C13: impossible de lancer le self-golden-set: {e}")
    return fails


def check_c14_llm_limits(project_dir, type_projet):
    """C14 (v4.1, gated by --llmlimits=on): si type=skill/agent, spec_produit.md doit
    avoir une section 'Limites LLM' (§12bis) avec au moins une limite LMx nommée (H9).
    On ne peut pas dépasser un plafond du domaine qu'on n'a pas nommé.
    """
    if type_projet not in ("skill", "agent"):
        return []  # ne concerne que skill/agent
    spec = project_dir / "spec_produit.md"
    if not spec.is_file():
        return ["C14: spec_produit.md manquant"]
    txt = spec.read_text(encoding="utf-8").lower()
    has_section = ("limites llm" in txt) or ("12bis" in txt)
    if not has_section:
        return ["C14: type=skill/agent mais spec_produit.md n'a pas de section "
                "'Limites LLM pour ce skill' (§12bis) — lance diagnostic-plafonds"]
    if not re.search(r"\blm\d+\b", txt):
        return ["C14: section §12bis présente mais vide (aucune limite LMx nommée)"]
    return []


def run_all_checks(project_dir, type_, memory, harness="off", autoimprove="off",
                   handoff="off", selfeval="off", llmlimits="off"):
    """Run all circuit-breakers, return structured report."""
    all_fails = []
    all_fails.extend(check_files_exist(project_dir))
    all_fails.extend(check_min_lines(project_dir))
    all_fails.extend(check_no_placeholders(project_dir))
    if type_ == "skill":
        all_fails.extend(check_skill_memory(project_dir, memory))
    all_fails.extend(check_sessions_structure(project_dir))
    all_fails.extend(check_critic_output(project_dir))
    all_fails.extend(check_patches_appended(project_dir))
    all_fails.extend(check_regle_de_fer_in_sessions(project_dir))
    all_fails.extend(check_reset_contexte_per_session(project_dir))

    checks_run = 9
    if harness == "on":
        all_fails.extend(check_harness_coverage(project_dir))
        checks_run += 1
    if type_ == "skill" and autoimprove == "on":
        all_fails.extend(check_autoimprove_loop(project_dir))
        checks_run += 1
    if handoff == "on":
        all_fails.extend(check_handoff_spec(project_dir))
        checks_run += 1
    if selfeval == "on":
        all_fails.extend(check_selfeval(project_dir))
        checks_run += 1
    if llmlimits == "on":
        all_fails.extend(check_c14_llm_limits(project_dir, type_))
        checks_run += 1

    return {
        "project": str(project_dir),
        "checks_run": checks_run,
        "failures": all_fails,
        "status": "PASS" if not all_fails else "FAIL",
    }


def main():
    ap = argparse.ArgumentParser(description="Circuit-breakers for mode-plan v3.1")
    ap.add_argument("project_dir", type=Path)
    ap.add_argument("--type", choices=["app", "skill", "doc"], default="app")
    ap.add_argument(
        "--memory", choices=["complet", "issues_only", "aucune"], default="aucune"
    )
    ap.add_argument(
        "--harness", choices=["on", "off"], default="off",
        help="v3.3: also run C10 harness-coverage check (default off -> 9 checks)"
    )
    ap.add_argument(
        "--autoimprove", choices=["on", "off"], default="off",
        help="v3.5: if type=skill, also run C11 self-improvement-loop check"
    )
    ap.add_argument(
        "--handoff", choices=["on", "off"], default="off",
        help="v3.6: also run C12 repo-handoff-spec check (CLAUDE.md/AGENTS.md)"
    )
    ap.add_argument(
        "--selfeval", choices=["on", "off"], default="off",
        help="v4.0: also run C13 self-golden-set check (replay + grader-of-graders)"
    )
    ap.add_argument(
        "--llmlimits", choices=["on", "off"], default="off",
        help="v4.1: if type=skill/agent, require the domain LLM-limits section (§12bis, C14)"
    )
    args = ap.parse_args()

    if not args.project_dir.is_dir():
        err({"error": "project_dir not a directory: " + str(args.project_dir)})
        return 2

    report = run_all_checks(args.project_dir, args.type, args.memory, args.harness,
                            args.autoimprove, args.handoff, args.selfeval, args.llmlimits)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
