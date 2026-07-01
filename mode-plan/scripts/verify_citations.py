#!/usr/bin/env python3
"""verify_citations.py — vérifieur non-gamable des citations (archi §2.2, ARCH-001).

Post-étape déterministe (0 LLM) de la Debate Room, exécutée APRÈS le Juge. Défenseur
et Juge citent des passages du plan ; RIEN ne vérifiait qu'ils existent (viole le
propre H2 de mode-plan). Ce script ancre chaque citation dans la source réelle via
la fonction de normalisation canonique `_normalize.norm` (source unique).

Contrats amont consommés (ARCH-001) :
  - critics    : `passage_cite`   (dans les critiques[])
  - defenseur  : `passage_qui_repond` (defenses.json)
  - juge       : `passage_verifie` (verdict.json)

Pour chaque citation : `norm(citation) in norm(source_file)` ? Absente -> `non_ancre`
+ action de downgrade (juge CONFIRMÉE->PARTIELLE, ou flag du Défenseur faux TROUVÉ).

Sortie : `citations_report.json` (data_model §3).

Le cœur `is_anchored()` est PUR (norm + substring, aucune I/O) — réutilisé tel quel
par `self_eval_debate.grade()` pour les assertions should-fire ancrées (S2 Défenseur).

Usage :
  python verify_citations.py --case evals/selfeval/S3_citation_inventee
  python verify_citations.py --sources <dir_du_plan> --artifacts <dir_.mode-plan> [--out ...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _normalize import norm  # noqa: E402  (source unique de normalisation)

SKILL_ROOT = Path(__file__).resolve().parent.parent
_ABSENCE_RE = re.compile(r"^\s*aucune?\s+section", re.IGNORECASE)


# --------------------------------------------------------------------------- #
#  Cœur PUR (aucune I/O) — réutilisable par self_eval_debate.grade()
# --------------------------------------------------------------------------- #
def is_anchored(passage: str, source_texts: list[str]) -> bool:
    """Vrai si le passage (normalisé) est un sous-texte d'AU MOINS une source."""
    if not passage:
        return False
    np = norm(passage)
    if not np:
        return False
    return any(np in norm(t) for t in source_texts)


def _is_declared_absence(passage: str, section: str) -> bool:
    """Le critic peut marquer explicitement une absence (section 'ABSENTE' ou
    'aucune section harnais sur Hx') — ce n'est pas une citation à ancrer."""
    if section and norm(section) == norm("ABSENTE"):
        return True
    return bool(passage and _ABSENCE_RE.match(passage))


def extract_citations(agent_outputs: dict) -> list[dict]:
    """Aplati les citations de tous les agents en une liste normalisée.
    Détection par forme de sortie (critiques / defenses / verdicts)."""
    citations: list[dict] = []
    for agent, out in agent_outputs.items():
        if not isinstance(out, dict):
            continue
        if "critiques" in out:  # un critic
            for c in out.get("critiques", []):
                if _is_declared_absence(c.get("passage_cite", ""), c.get("section", "")):
                    continue
                citations.append({
                    "source": agent, "role": "critic",
                    "critique_id": c.get("id"),
                    "passage": c.get("passage_cite", ""),
                    "fichier": c.get("fichier"),
                    "action_si_non_ancre": f"critique {c.get('id')} : passage non ancré (à re-vérifier)",
                })
        elif "defenses" in out:  # le défenseur
            for d in out.get("defenses", []):
                if d.get("verdict_defense") == "PAS_TROUVÉ":
                    continue  # pas de citation attendue
                citations.append({
                    "source": agent, "role": "defenseur",
                    "critique_id": d.get("critique_id"),
                    "passage": d.get("passage_qui_repond", ""),
                    "fichier": None,  # section_qui_repond peut nommer le fichier, on teste toutes les sources
                    "action_si_non_ancre": f"défense {d.get('critique_id')} : faux TROUVÉ -> rétrograder en PAS_TROUVÉ",
                })
        elif "verdicts" in out:  # le juge
            for v in out.get("verdicts", []):
                passage = v.get("passage_verifie")
                if not passage:
                    continue
                verdict = v.get("verdict")
                citations.append({
                    "source": agent, "role": "juge",
                    "critique_id": v.get("critique_id"),
                    "passage": passage,
                    "fichier": None,
                    "action_si_non_ancre": f"verdict {verdict} -> PARTIELLE",
                })
    return citations


def build_report(sources: dict[str, str], agent_outputs: dict) -> dict:
    """Construit citations_report.json (data_model §3). `sources` = {fichier -> texte}."""
    all_texts = list(sources.values())
    citations = extract_citations(agent_outputs)
    non_ancrees = []
    ancrees = 0
    for cit in citations:
        # Si un fichier précis est cité et connu, tester d'abord contre lui ;
        # sinon (défenseur/juge) tester contre toutes les sources.
        if cit["fichier"] and cit["fichier"] in sources:
            anchored = is_anchored(cit["passage"], [sources[cit["fichier"]]])
        else:
            anchored = is_anchored(cit["passage"], all_texts)
        if anchored:
            ancrees += 1
        else:
            non_ancrees.append({
                "source": cit["source"],
                "role": cit["role"],
                "critique_id": cit["critique_id"],
                "passage": cit["passage"],
                "fichier": cit["fichier"],
                "action": cit["action_si_non_ancre"],
            })
    total = len(citations)
    return {
        "total_citations": total,
        "ancrees": ancrees,
        "non_ancrees": non_ancrees,
        "taux_ancrage": round(ancrees / total, 4) if total else 1.0,
    }


# --------------------------------------------------------------------------- #
#  Chargement (I/O) — CLI
# --------------------------------------------------------------------------- #
def _parse_json_tolerant(text: str):
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


def load_sources(sources_dir: Path) -> dict[str, str]:
    out = {}
    for name in ("spec_produit.md", "archi.md", "data_model.md"):
        p = sources_dir / name
        if p.exists():
            out[name] = p.read_text(encoding="utf-8")
    return out


def load_recorded_outputs(case_dir: Path) -> dict:
    """Charge les sorties d'agents d'un cas selfeval (recorded/<agent>.json -> .output)."""
    outputs = {}
    rec_dir = case_dir / "recorded"
    if rec_dir.exists():
        for f in sorted(rec_dir.glob("*.json")):
            data = _parse_json_tolerant(f.read_text(encoding="utf-8"))
            outputs[f.stem] = data.get("output", data)
    return outputs


def load_artifacts(artifacts_dir: Path) -> dict:
    """Charge les JSON d'un run réel (.mode-plan/) : critique_*.json, defenses*.json, verdict*.json."""
    outputs = {}
    for f in sorted(artifacts_dir.glob("*.json")):
        name = f.stem
        if not re.search(r"critique|defens|verdict", name, re.IGNORECASE):
            continue
        data = _parse_json_tolerant(f.read_text(encoding="utf-8"))
        outputs[name] = data.get("output", data)
    return outputs


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="vérifieur de citations (archi §2.2)")
    ap.add_argument("--case", default=None, help="dossier d'un cas selfeval (3 md + recorded/)")
    ap.add_argument("--sources", default=None, help="dossier du plan (spec/archi/data_model)")
    ap.add_argument("--artifacts", default=None, help="dossier .mode-plan/ d'un run réel")
    ap.add_argument("--out", default=None, help="chemin de citations_report.json")
    args = ap.parse_args()

    if args.case:
        case_dir = Path(args.case)
        sources = load_sources(case_dir)
        agent_outputs = load_recorded_outputs(case_dir)
        default_out = case_dir / "citations_report.json"
    elif args.sources and args.artifacts:
        sources = load_sources(Path(args.sources))
        agent_outputs = load_artifacts(Path(args.artifacts))
        default_out = Path(args.artifacts) / "citations_report.json"
    else:
        print(json.dumps({"error": "USAGE", "msg": "--case DIR  OU  --sources DIR --artifacts DIR"},
                         ensure_ascii=False))
        return 2

    report = build_report(sources, agent_outputs)
    out_path = Path(args.out) if args.out else default_out
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[verify_citations] {report['ancrees']}/{report['total_citations']} ancrées, "
          f"{len(report['non_ancrees'])} non_ancrées, taux={report['taux_ancrage']} -> {out_path}",
          file=sys.stderr)
    # Exit 0 : le rapport est produit. Le downgrade est une ACTION consommée en aval,
    # pas un échec de script (les non-ancrées sont attendues et gérées).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
