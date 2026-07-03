#!/usr/bin/env python3
"""feasibility_lint.py — Lint de faisabilité déterministe d'un plan (v4.2, audit 2026-07-03, R5/P-002).

La Debate Room critique le TEXTE du plan, jamais sa correspondance au monde : les
divergences réelles observées à l'implémentation (un script planifié avec une capacité
qu'un script Python n'a pas ; un cas golden capability sans verdict humain de référence)
sont invisibles au débat rhétorique. Ce lint attrape ces deux familles AVANT livraison,
en 0 token.

Checks :
  F1. Capacités outillées : un `scripts/*.py` planifié ne peut pas faire de WebSearch /
      web_fetch / navigation / spawn de sous-agents — ce sont des outils de l'agent
      orchestrateur. Toute ligne d'archi/sessions qui associe un .py à une de ces
      capacités est une divergence d'implémentation garantie.
  F2. Prémisses des cas golden : un cas de suite `capability` sans verdict humain de
      référence (`human_reference` / « verdict humain » / « référence humaine ») n'est
      pas scorable — le grader n'aura pas d'ancre.

Fail-closed : fichiers du plan absents -> MISSING_FILES, exit 2 (jamais un PASS vide).

Usage :
  python feasibility_lint.py CHEMIN_DU_PLAN

Codes retour : 0 = conforme ; 1 = alertes ; 2 = fichiers du plan manquants / usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FILES = ["spec_produit.md", "archi.md", "data_model.md"]
OPTIONAL_FILES = ["sessions_claude_code.md"]

# Capacités d'agent qu'un script Python n'a PAS (F1)
AGENT_ONLY_CAPABILITIES = re.compile(
    r"websearch|web_fetch|webfetch|recherche\s+web|navigue|navigation\s+web"
    r"|spawn\w*\s+(de\s+)?sous-agents?|appelle\s+un\s+llm|llm-as-judge",
    re.IGNORECASE,
)
SCRIPT_REF = re.compile(r"[\w/]+\.py\b")

# Marqueurs d'ancrage humain pour les cas capability (F2)
HUMAN_ANCHOR = re.compile(
    r"human_reference|verdict\s+humain|référence\s+humaine|reference\s+humaine"
    r"|verdict\s+de\s+référence", re.IGNORECASE,
)


def check_f1_script_capabilities(files: dict[str, str]) -> list[dict]:
    """F1 : ligne qui associe un script .py à une capacité agent-only."""
    alerts = []
    for fname, text in files.items():
        for i, line in enumerate(text.splitlines(), start=1):
            if SCRIPT_REF.search(line) and AGENT_ONLY_CAPABILITIES.search(line):
                cap = AGENT_ONLY_CAPABILITIES.search(line).group(0)
                alerts.append({
                    "check": "F1",
                    "fichier": fname,
                    "ligne": i,
                    "alerte": f"script .py associé à une capacité d'agent ({cap!r}) — "
                              "un script Python n'a pas cet outil ; prévoir que "
                              "l'ORCHESTRATEUR fasse cette étape et passe le résultat "
                              "au script (ex : --web-results).",
                    "extrait": line.strip()[:160],
                })
    return alerts


def check_f2_capability_premises(files: dict[str, str]) -> list[dict]:
    """F2 : cas golden `capability` sans ancre humaine dans un voisinage de 10 lignes."""
    alerts = []
    spec = files.get("spec_produit.md", "")
    lines = spec.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"\bcapability\b", line, re.IGNORECASE):
            lo, hi = max(0, i - 10), min(len(lines), i + 11)
            window = "\n".join(lines[lo:hi])
            if not HUMAN_ANCHOR.search(window):
                alerts.append({
                    "check": "F2",
                    "fichier": "spec_produit.md",
                    "ligne": i + 1,
                    "alerte": "cas 'capability' sans verdict humain de référence à "
                              "proximité — NON-SCORABLE pour le grader (l'assertion "
                              "n'aura pas d'ancre) ; exiger un human_reference.",
                    "extrait": line.strip()[:160],
                })
    return alerts


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Lint de faisabilité déterministe d'un plan mode-plan "
        "(capacités outillées des scripts planifiés + prémisses des cas golden).",
    )
    ap.add_argument("plan_dir", type=Path, help="Dossier du plan (spec/archi/data_model)")
    args = ap.parse_args()

    if not args.plan_dir.is_dir():
        print(json.dumps({"error": f"not a directory: {args.plan_dir}"}), file=sys.stderr)
        return 2

    missing = [f for f in REQUIRED_FILES if not (args.plan_dir / f).is_file()]
    if missing:
        print(json.dumps({"status": "MISSING_FILES", "missing": missing,
                          "note": "0 fichier analysé ≠ plan faisable (fail-closed)."},
                         indent=2, ensure_ascii=False))
        return 2

    files = {}
    for fname in REQUIRED_FILES + OPTIONAL_FILES:
        path = args.plan_dir / fname
        if path.is_file():
            files[fname] = path.read_text(encoding="utf-8", errors="replace")

    alerts = check_f1_script_capabilities(files) + check_f2_capability_premises(files)
    report = {
        "plan": str(args.plan_dir),
        "fichiers_analyses": sorted(files),
        "alerts_count": len(alerts),
        "alerts": alerts,
        "status": "PASS" if not alerts else "FAIL",
        "note": "lint heuristique (regex) : une alerte = à VÉRIFIER par l'orchestrateur, "
                "pas une preuve ; zéro alerte = les deux familles connues sont couvertes.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not alerts else 1


if __name__ == "__main__":
    sys.exit(main())
