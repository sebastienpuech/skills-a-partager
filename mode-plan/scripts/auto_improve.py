#!/usr/bin/env python3
"""auto_improve.py — moteur de la boucle d'auto-amélioration V1 (spec §11, archi §4bis).

Harnais déterministe autour du `skill-auto-improver` : mesure les 3 métriques du
**gate d'adoption d'un patch** et tranche COMMIT / REVERT. Le moteur LLM
(`skill-auto-improver`) lit `_mode-plan-meta/issues.md` + le self-golden-set, propose
un patch d'un prompt d'agent ou d'un script ; CE script fournit la mesure et le gate.

Gate d'adoption d'un patch (spec §11, sanctuarisé) :
    COMMIT ssi  capability↑ (strict)  ET  regression == 1.0  ET  holdout == 1.0
    sinon REVERT.

- **Déclencheur = MANUEL en V1** (on lance ce script à la main). Forme-cible : une
  tâche planifiée hebdo (documentée dans le SKILL.md / la doctrine, non câblée en V1).
- **Sécurité** : en `--dry-run` (défaut) le script NE TOUCHE JAMAIS git. Sans candidat
  qui améliore, la décision est NO_COMMIT — c'est le comportement d'une passe à sec.
- **Anti-gaming** : le hold-out (`evals/selfeval/_holdout/`) est tenu hors optimisation ;
  regression_holdout < 100 % → revert (HARN-004). `expected.json` en lecture seule (ARCH-006).

Usage :
  python auto_improve.py            # passe à sec : mesure + gate, ne commit rien
  python auto_improve.py --dry-run  # idem (défaut explicite)
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
SELFEVAL_DIR = SKILL_ROOT / "evals" / "selfeval"
HOLDOUT_DIR = SELFEVAL_DIR / "_holdout"
META_DIR = SKILL_ROOT / "_mode-plan-meta"
PROPOSED_FIXES = META_DIR / "proposed_fixes.md"

PROGRESSIVE_DISCLOSURE_MAX_LINES = 500  # SKILL.md doit rester chargeable (context engineering)
_FULL_EPS = 1e-9  # tolérance flottante pour "score == 1.0" (audit #4)


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    # sys.executable (jamais 'python3') pour robustesse Windows.
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def _score_capability(dir_: Path) -> float:
    proc = _run([sys.executable, str(SCRIPTS_DIR / "self_eval_debate.py"),
                 "--replay", "--dir", str(dir_)])
    try:
        report = json.loads(proc.stdout)
        return float(report.get("score_capability", 0.0))
    except (json.JSONDecodeError, ValueError):
        return 0.0


def _regression_rate() -> float:
    proc = _run([sys.executable, str(SCRIPTS_DIR / "run_evals.py")])
    m = re.search(r"Summary:\s*(\d+)\s*/\s*(\d+)\s*passed", proc.stdout + proc.stderr)
    if not m:
        return 0.0
    passed, total = int(m.group(1)), int(m.group(2))
    return round(passed / total, 4) if total else 0.0


def measure() -> dict:
    """Les 3 métriques du gate."""
    return {
        "capability": _score_capability(SELFEVAL_DIR),
        "regression": _regression_rate(),
        "holdout": _score_capability(HOLDOUT_DIR) if HOLDOUT_DIR.is_dir() else 1.0,
    }


def gate(baseline: dict, candidate: dict) -> tuple[bool, str]:
    """COMMIT ssi capability↑ strict ET regression==1.0 ET holdout==1.0 (spec §11)."""
    if candidate["capability"] <= baseline["capability"]:
        return False, (f"capability {candidate['capability']} <= baseline "
                       f"{baseline['capability']} (pas d'amélioration) -> NO_COMMIT")
    # Audit #4 : tolérance flottante. Les scores sont des ratios passed/total (1.0 exact
    # quand plein), mais un grader pourrait émettre 0.9999998 -> faux REVERT. Un vrai
    # échec de cas vaut >= 1/total (>> 1e-9), donc l'epsilon ne masque aucune régression.
    if candidate["regression"] < 1.0 - _FULL_EPS:
        return False, f"regression {candidate['regression']} < 1.0 -> REVERT"
    if candidate["holdout"] < 1.0 - _FULL_EPS:
        return False, f"holdout {candidate['holdout']} < 1.0 (généralisation cassée) -> REVERT"
    return True, "capability↑ ET regression==1.0 ET holdout==1.0 -> COMMIT"


def run_gate_check() -> dict:
    """Prouve (déterministe, CI) que le gate BLOQUE chaque type de régression et
    n'accepte QUE la vraie amélioration. C'est la vérification anti-régression :
    tant que ces assertions tiennent, aucun patch régressif ne peut être committé."""
    base = {"capability": 0.80, "regression": 1.0, "holdout": 1.0}
    scenarios = [
        # (nom, candidate, commit_attendu)
        ("amélioration réelle", {"capability": 0.85, "regression": 1.0, "holdout": 1.0}, True),
        ("capability égale (pas de gain)", {"capability": 0.80, "regression": 1.0, "holdout": 1.0}, False),
        ("capability en baisse", {"capability": 0.70, "regression": 1.0, "holdout": 1.0}, False),
        ("régression evals (reg<1.0)", {"capability": 0.90, "regression": 0.95, "holdout": 1.0}, False),
        ("hold-out cassé (gaming/overfit)", {"capability": 0.95, "regression": 1.0, "holdout": 0.5}, False),
    ]
    results = []
    for nom, cand, expected in scenarios:
        commit, reason = gate(base, cand)
        results.append({"scenario": nom, "commit_attendu": expected,
                        "commit_obtenu": commit, "ok": commit == expected, "raison": reason})
    green = all(r["ok"] for r in results)
    return {"mode": "gate-check", "green": green, "results": results}


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(SKILL_ROOT),
                          capture_output=True, text=True, encoding="utf-8")


def sandboxed_apply(apply_cmd: str) -> dict:
    """Enforcement anti-régression : applique un candidat dans un bac à sable git,
    re-mesure, et REVERT si le gate échoue → l'arbre reste propre, aucun patch
    régressif ne survit. Exige un arbre propre au départ.

    Périmètre = `mode-plan/` uniquement (audit #2) : le check de propreté ET le revert
    sont scopés à `-- .` depuis SKILL_ROOT, cohérents entre eux (le dépôt <depot-prive>
    peut avoir d'autres modifs légitimes ailleurs). Le REVERT annule les fichiers
    SUIVIS (`git checkout`) ET supprime les fichiers NON-SUIVIS créés par le patch
    (`git clean -fd`, non-ignorés) — sinon un patch qui *ajoute* un fichier régressif
    survivrait au revert.

    ⚠ SÉCURITÉ (audit #6) : `apply_cmd` est exécuté via `shell=True` — c'est une
    ENTRÉE DE CONFIANCE (le patch écrit par skill-auto-improver), PAS une isolation
    d'exécution. Le bac à sable ne protège que l'arbre git, pas le système. Ne jamais
    passer ici une chaîne d'origine non vérifiée. Ne committe jamais.
    """
    dirty = _git("status", "--porcelain", "--", ".").stdout.strip()
    if dirty:
        return {"error": "SANDBOX_REQUIERT_ARBRE_PROPRE", "dirty": dirty.splitlines()[:10]}
    baseline = measure()
    proc = subprocess.run(apply_cmd, shell=True, cwd=str(SKILL_ROOT),
                          capture_output=True, text=True, encoding="utf-8")
    candidate = measure()
    commit, reason = gate(baseline, candidate)
    result = {"apply_cmd": apply_cmd, "apply_exit": proc.returncode,
              "baseline": baseline, "candidate": candidate,
              "gate": reason, "commit": commit}
    if commit:
        result["action"] = "KEEP (gate OK) — changements laissés pour revue/commit humain"
    else:
        _git("checkout", "--", ".")               # annule les fichiers suivis
        _git("clean", "-fdq", "--", ".")          # supprime les non-suivis créés par le patch
        after = _git("status", "--porcelain", "--", ".").stdout.strip()
        result["action"] = "REVERT (gate KO) — patch annulé"
        result["arbre_propre_apres_revert"] = (after == "")
        if after:
            result["restes_non_suivis"] = after.splitlines()[:10]  # patch a créé des fichiers -> revue manuelle
    return result


def progressive_disclosure_check() -> dict:
    """SKILL.md ≤ 500 lignes (context engineering). Sinon : signaler (pas bloquant)."""
    skill_md = SKILL_ROOT / "SKILL.md"
    n = sum(1 for _ in skill_md.open(encoding="utf-8")) if skill_md.is_file() else 0
    ok = n <= PROGRESSIVE_DISCLOSURE_MAX_LINES
    return {
        "skill_md_lines": n,
        "max": PROGRESSIVE_DISCLOSURE_MAX_LINES,
        "ok": ok,
        "message": (f"SKILL.md = {n} lignes <= {PROGRESSIVE_DISCLOSURE_MAX_LINES} : OK"
                    if ok else
                    f"SKILL.md = {n} lignes > {PROGRESSIVE_DISCLOSURE_MAX_LINES} : "
                    "déplacer du contenu vers references/ (progressive disclosure)"),
    }


def count_open_issues() -> int:
    issues = META_DIR / "issues.md"
    if not issues.is_file():
        return 0
    return len(re.findall(r"^###\s+\d{4}-\d{2}-\d{2}", issues.read_text(encoding="utf-8"), re.M))


def append_audit(date: str, decision: str, baseline: dict, candidate: dict, reason: str) -> None:
    entry = (
        f"\n### {date} — passe auto_improve (dry-run)\n"
        f"- **Issue source** : —  (passe à sec, aucun candidat appliqué)\n"
        f"- **Patch** : aucun (V1 déclencheur manuel)\n"
        f"- **Mesure** : capability {baseline['capability']}→{candidate['capability']} "
        f"| regression {candidate['regression']} | holdout {candidate['holdout']}\n"
        f"- **Décision** : {decision}\n"
        f"- **Raison** : {reason}\n"
    )
    with PROPOSED_FIXES.open("a", encoding="utf-8") as f:
        f.write(entry)


def log_interaction(date: str, report: dict) -> None:
    """Append 1 ligne métadonnées-only à interactions.jsonl (data_model §9).
    Aucun contenu brut : uniquement les scores + la décision de la passe."""
    interactions = META_DIR / "interactions.jsonl"
    line = {
        "date": date,
        "event": "auto_improve_pass",
        "capability": report["baseline"]["capability"],
        "regression": report["baseline"]["regression"],
        "holdout": report["baseline"]["holdout"],
        "decision": report["decision"],
        "open_issues": report["open_issues"],
        "skill_md_lines": report["progressive_disclosure"]["skill_md_lines"],
    }
    with interactions.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="boucle d'auto-amélioration V1 (spec §11)")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="mesure + gate, NE COMMIT RIEN (défaut, seul mode en V1)")
    ap.add_argument("--date", default="unknown", help="date pour l'audit trail")
    ap.add_argument("--no-audit", action="store_true", help="ne pas écrire dans proposed_fixes.md")
    ap.add_argument("--log", action="store_true",
                    help="append 1 ligne métadonnées à interactions.jsonl (utilisé par le cron hebdo)")
    ap.add_argument("--check", action="store_true",
                    help="test anti-régression : le gate bloque-t-il chaque type de régression ? (CI)")
    ap.add_argument("--sandbox-apply", metavar="CMD", default=None,
                    help="applique un candidat (commande shell DE CONFIANCE, shell=True) en bac à "
                         "sable git, mesure, revert+clean si le gate échoue. N'isole PAS l'exécution.")
    ap.add_argument("root", nargs="?", default=None, help="positionnel toléré (run_evals)")
    args = ap.parse_args()

    if args.check:
        rep = run_gate_check()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"[auto_improve] gate-check green={rep['green']}", file=sys.stderr)
        return 0 if rep["green"] else 1

    if args.sandbox_apply:
        rep = sandboxed_apply(args.sandbox_apply)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"[auto_improve] sandbox: {rep.get('action', rep.get('error'))}", file=sys.stderr)
        return 0

    baseline = measure()
    # V1 : aucun candidat n'est appliqué dans une passe à sec -> candidat = baseline.
    candidate = dict(baseline)
    commit, reason = gate(baseline, candidate)
    decision = "COMMIT" if commit else "NO_COMMIT"
    pd = progressive_disclosure_check()

    report = {
        "mode": "dry-run",
        "baseline": baseline,
        "candidate": candidate,
        "decision": decision,
        "gate_reason": reason,
        "open_issues": count_open_issues(),
        "progressive_disclosure": pd,
        "note": "V1 : déclencheur manuel, aucun git touché. Forme-cible : tâche planifiée hebdo.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not args.no_audit and PROPOSED_FIXES.is_file():
        append_audit(args.date, decision, baseline, candidate, reason)
    if args.log and META_DIR.is_dir():
        log_interaction(args.date, report)

    if not pd["ok"]:
        print(f"[auto_improve] ⚠ {pd['message']}", file=sys.stderr)
    print(f"[auto_improve] décision={decision} ; {reason}", file=sys.stderr)
    # Exit 0 : une passe à sec réussie (qui ne commit rien) n'est PAS un échec.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
