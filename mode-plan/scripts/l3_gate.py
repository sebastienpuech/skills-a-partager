#!/usr/bin/env python3
"""l3_gate.py — gate statique de la phase L3 (V2, archi §3, data_model §8).

L3 pousse la frontière du DOMAINE d'un skill stratégique via la chaîne
diagnostic-plafonds -> labo-recherche -> GATE -> application-solutions. Ce script
est le **gate statique** : au moment du plan, le skill cible n'a pas encore de
golden set exécutable, donc une trouvaille du labo n'entre au draft QUE si :

  (a) ANCRÉE : son `passage_source` est réellement présent dans les sources
      rassemblées par le labo (anti-hallucination, via verify_citations.is_anchored).
  (b) EXPRIMABLE : elle porte un `cas_de_test_futur` non vide (le futur cas golden
      §10bis du skill cible — on écrit le test en même temps que la techno).

  décision = "injecter" ssi (a) ET (b) ; sinon "backlog" spéculatif.

Le gate DYNAMIQUE (ré-évaluer contre le golden set réel du skill cible, une fois
construit) est hors scope ici — il s'exécute après le build du skill généré.

Entrées d'un cas : `sources.md` (évidence du labo) + `labo_findings.json`
(data_model §8, + champ `passage_source` par solution). Sortie : `l3_gate.json`.

Usage :
  python l3_gate.py --run --case evals/l3/<case>     # produit l3_gate.json
  python l3_gate.py --check                           # mécanisme (CI) vs expected.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_citations import is_anchored  # noqa: E402  (cœur pur, anti-hallucination)

SKILL_ROOT = Path(__file__).resolve().parent.parent
L3_DIR = SKILL_ROOT / "evals" / "l3"


def _parse_json(text: str):
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


def gate_findings(sources_text: str, findings: dict) -> dict:
    """Applique le gate statique à chaque solution -> injecter | backlog."""
    gated = []
    for sol in findings.get("solutions", []):
        ancree = is_anchored(sol.get("passage_source", ""), [sources_text])
        exprimable = bool((sol.get("cas_de_test_futur") or "").strip())
        decision = "injecter" if (ancree and exprimable) else "backlog"
        if decision == "backlog":
            if not ancree:
                raison = "non ancrée (passage_source absent des sources du labo -> hallucination probable)"
            else:
                raison = "ancrée mais non exprimable en cas golden (cas_de_test_futur vide)"
        else:
            raison = "ancrée ET exprimable en cas golden -> injectable au draft"
        gated.append({
            "solution_id": sol.get("id"), "ancree": ancree,
            "exprimable_en_golden": exprimable, "decision": decision, "raison": raison,
        })
    return {
        "plafond_id": findings.get("plafond_id"),
        "gated": gated,
        "injecter": [g["solution_id"] for g in gated if g["decision"] == "injecter"],
        "backlog": [g["solution_id"] for g in gated if g["decision"] == "backlog"],
    }


def load_case(case_dir: Path):
    sources = (case_dir / "sources.md").read_text(encoding="utf-8") if (case_dir / "sources.md").is_file() else ""
    findings = _parse_json((case_dir / "labo_findings.json").read_text(encoding="utf-8"))
    return sources, findings


def discover_cases(root: Path) -> list[Path]:
    if (root / "labo_findings.json").is_file():
        return [root]
    return [d for d in sorted(root.iterdir())
            if d.is_dir() and (d / "labo_findings.json").is_file()]


def run_check(root: Path) -> dict:
    results = []
    for case_dir in discover_cases(root):
        expected = _parse_json((case_dir / "expected.json").read_text(encoding="utf-8"))
        sources, findings = load_case(case_dir)
        report = gate_findings(sources, findings)
        got = {g["solution_id"]: g["decision"] for g in report["gated"]}
        exp = expected.get("decisions", {})
        ok = got == exp
        results.append({"case": case_dir.name, "got": got, "expected": exp, "ok": ok})
    green = bool(results) and all(r["ok"] for r in results)
    return {"mode": "l3-check", "green": green, "results": results}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="gate statique L3 (archi §3)")
    ap.add_argument("--l3", choices=["on", "off"], default="off",
                    help="phase L3 opt-in (skill stratégique) ; OFF par défaut")
    ap.add_argument("--check", action="store_true", help="mécanisme du gate (CI)")
    ap.add_argument("--run", action="store_true", help="produit l3_gate.json pour un cas")
    ap.add_argument("--case", default=None, help="dossier d'un cas (avec --run)")
    ap.add_argument("--dir", default=str(L3_DIR))
    ap.add_argument("root", nargs="?", default=None, help="positionnel toléré (run_evals)")
    args = ap.parse_args()
    root = Path(args.root) if args.root else Path(args.dir)

    if args.check:
        rep = run_check(root)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"[l3_gate] check green={rep['green']}", file=sys.stderr)
        return 0 if rep["green"] else 1

    if args.run:
        case_dir = Path(args.case) if args.case else root
        sources, findings = load_case(case_dir)
        report = gate_findings(sources, findings)
        out = case_dir / "l3_gate.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"[l3_gate] {len(report['injecter'])} injecter, {len(report['backlog'])} backlog -> {out}",
              file=sys.stderr)
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
