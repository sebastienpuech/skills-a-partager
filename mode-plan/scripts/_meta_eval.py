#!/usr/bin/env python3
"""_meta_eval.py — grader-of-graders de mode-plan v4.0 (HARN-001, archi §2.4).

« Qui mesure la couche de mesure ? » Sans ça, `self_eval_debate.py` pourrait être
cassé sans qu'on le sache : la mesure ne serait pas elle-même mesurée.

Principe (patch ARCH-R2-004) : `_meta_eval.py` n'a AUCUNE logique de grade propre.
Il pilote `self_eval_debate.py` en boîte noire, de bout en bout, sur des mini-jeux
`evals/selfeval/_meta/<meta_case>/` montés avec des `recorded/` truqués, puis lit le
`selfeval_report.json` RÉEL produit et vérifie que `cases[].pass` vaut bien le verdict
de grader attendu. Ainsi le SEUL chemin de grading testé est celui de production —
impossible qu'un second parseur diverge.

3 polarités obligatoires (HARN-002), vert seulement si les 3 passent :
  - no-fire        -> le grader doit dire fail  (l'agent n'a pas flaggé alors qu'il devait)
  - fire-correct   -> le grader doit dire pass  (l'agent a flaggé comme attendu)
  - faux-positif   -> le grader doit dire fail  (l'agent a flaggé une section interdite)

Chaque `_meta/<meta_case>/` contient un `meta_expected.json` :
  {"expected_grader_verdict": "pass"|"fail", "polarite": "no_fire"|"fire_correct"|"faux_positif"}

Usage : python _meta_eval.py [--meta-dir evals/selfeval/_meta]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS_DIR.parent
SELF_EVAL = SCRIPTS_DIR / "self_eval_debate.py"

REQUIRED_POLARITES = {"no_fire", "fire_correct", "faux_positif"}


def parse_json_tolerant(text: str):
    import re
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        i, j = text.find("{"), text.rfind("}")
        if i != -1 and j != -1 and j > i:
            return json.loads(text[i:j + 1])
        raise


def run_grader_blackbox(meta_case_dir: Path) -> dict:
    """Exécute le VRAI self_eval_debate.py --replay sur le mini-jeu et renvoie
    le case_result produit (boîte noire — aucun grading local)."""
    with tempfile.TemporaryDirectory() as tmp:
        report_path = Path(tmp) / "report.json"
        # sys.executable (jamais 'python3') pour robustesse Windows.
        proc = subprocess.run(
            [sys.executable, str(SELF_EVAL), "--replay",
             "--dir", str(meta_case_dir), "--out", str(report_path)],
            capture_output=True, text=True, encoding="utf-8",
        )
        if not report_path.exists():
            raise RuntimeError(
                f"self_eval_debate n'a produit aucun rapport pour {meta_case_dir.name}\n"
                f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        report = parse_json_tolerant(report_path.read_text(encoding="utf-8"))
    cases = report.get("cases", [])
    if not cases:
        raise RuntimeError(f"aucun cas gradé dans {meta_case_dir.name} (skipped ?)")
    return cases[0]


def evaluate_meta_case(meta_case_dir: Path) -> dict:
    meta_exp = parse_json_tolerant((meta_case_dir / "meta_expected.json").read_text(encoding="utf-8"))
    expected_verdict = meta_exp["expected_grader_verdict"]  # "pass" | "fail"
    polarite = meta_exp.get("polarite")

    case_result = run_grader_blackbox(meta_case_dir)
    obtenu = "pass" if case_result.get("pass") else "fail"
    ok = (obtenu == expected_verdict)
    return {
        "meta_case": meta_case_dir.name,
        "polarite": polarite,
        "expected_grader_verdict": expected_verdict,
        "obtenu": obtenu,
        "ok": ok,
        "case_trace": case_result.get("trace"),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="grader-of-graders (HARN-001, archi §2.4)")
    ap.add_argument("--meta-dir", default=str(SKILL_ROOT / "evals" / "selfeval" / "_meta"))
    args = ap.parse_args()

    meta_dir = Path(args.meta_dir)
    if not meta_dir.exists():
        print(json.dumps({"error": "NO_META_DIR", "path": str(meta_dir)}, ensure_ascii=False))
        return 1

    meta_cases = [d for d in sorted(meta_dir.iterdir())
                  if d.is_dir() and (d / "meta_expected.json").exists()]
    results = [evaluate_meta_case(d) for d in meta_cases]

    covered = {r["polarite"] for r in results if r["polarite"]}
    missing_polarites = REQUIRED_POLARITES - covered
    all_ok = all(r["ok"] for r in results)
    passed = all_ok and not missing_polarites and len(results) >= 3

    report = {
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "polarites_couvertes": sorted(covered),
        "polarites_manquantes": sorted(missing_polarites),
        "green": passed,
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing_polarites:
        print(f"[_meta_eval] polarités manquantes : {sorted(missing_polarites)} "
              f"(HARN-002 exige les 3)", file=sys.stderr)
    print(f"[_meta_eval] {report['passed']}/{report['total']} meta-cas ok, green={passed}",
          file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
