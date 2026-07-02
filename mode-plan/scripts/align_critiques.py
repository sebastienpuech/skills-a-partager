#!/usr/bin/env python3
"""
align_critiques.py — Merge des critiques parallèles en aligned_critiques.json

Lit les 3 fichiers JSON produits par critic-architecte, critic-pragmatiste,
critic-simulateur (Phase 3.1 parallèle), plus critique_harnais.json (v3.3,
optionnel). Déduplique les doublons (même fichier + section), produit un JSON
aligné prêt pour le Défenseur.

Usage:
    python3 align_critiques.py <work_dir>

Attend dans work_dir :
    critique_arch.json
    critique_prag.json
    critique_sim.json
    critique_harnais.json   (v3.3, OPTIONNEL — 4e angle ; absent = comportement v3.2)

Écrit dans work_dir :
    aligned_critiques.json
    align_summary.txt (lecture humaine)
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _normalize import norm  # noqa: E402  (source unique de normalisation, v4.0)


def load_critic(path: Path) -> dict:
    """Load one critic output, tolerant to wrapping markdown fences."""
    text = path.read_text(encoding="utf-8")
    # Strip markdown fences if present
    if text.strip().startswith("```"):
        lines = text.strip().split("\n")
        # remove first and last fence line
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def detect_duplicates(critiques: list[dict]) -> list[tuple[int, int]]:
    """
    Detect critique pairs that target the same (fichier, section).
    v4.0 (archi §2.6) : comparaison via `norm()` sur fichier ET section pour
    rattraper les quasi-doublons ('Garde-fous' vs 'garde fous', accents, casse,
    ponctuation terminale). C'est un sur-ensemble de l'égalité exacte.
    Returns list of (idx_a, idx_b) pairs to flag for the Juge.
    """
    pairs = []
    keys = [
        (norm(c.get("fichier", "")), norm(c.get("section", "")))
        for c in critiques
    ]
    for i in range(len(critiques)):
        for j in range(i + 1, len(critiques)):
            if keys[i] == keys[j]:
                pairs.append((i, j))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description="Align parallel critiques")
    ap.add_argument("work_dir", type=Path)
    args = ap.parse_args()

    expected = ["critique_arch.json", "critique_prag.json", "critique_sim.json"]
    loaded = {}
    for fname in expected:
        p = args.work_dir / fname
        if not p.is_file():
            print(json.dumps({"error": f"missing {fname} in {args.work_dir}"}),
                  file=sys.stderr)
            return 1
        try:
            loaded[fname] = load_critic(p)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"{fname} fails to parse: {e}"}),
                  file=sys.stderr)
            return 1

    # v3.3 — 4e angle harnais, OPTIONNEL et rétro-compatible.
    optional = ["critique_harnais.json"]
    for fname in optional:
        p = args.work_dir / fname
        if p.is_file():
            try:
                loaded[fname] = load_critic(p)
            except json.JSONDecodeError as e:
                print(json.dumps({"warning": f"{fname} fails to parse, skipped: {e}"}),
                      file=sys.stderr)

    aligned = []
    score_local_by_angle = {}
    for fname, data in loaded.items():
        angle = data.get("angle", fname.replace("critique_", "").replace(".json", ""))
        # Audit #5 : un score_local absent OU null (None) ferait planter le calcul
        # pondéré (None * poids -> TypeError). Défaut neutre 5. (0 reste 0, valide.)
        _sl = data.get("score_local")
        score_local_by_angle[angle] = 5 if _sl is None else _sl
        for c in data.get("critiques", []):
            entry = {
                "id": c.get("id", f"{angle.upper()}-???"),
                "angle": angle,
                "fichier": c.get("fichier"),
                "section": c.get("section"),
                "passage_cite": c.get("passage_cite"),
                "critique": c.get("critique"),
                "gravite": c.get("gravite"),
                "patch_propose": c.get("patch_propose"),
            }
            aligned.append(entry)

    duplicates = detect_duplicates(aligned)

    # Score global pondéré (v3.3 : 4 angles si harnais présent, sinon 40/30/30).
    if "harnais" in score_local_by_angle:
        weights = {"architecte": 0.30, "pragmatiste": 0.25,
                   "simulateur": 0.25, "harnais": 0.20}
    else:
        weights = {"architecte": 0.4, "pragmatiste": 0.3, "simulateur": 0.3}
    score_global = sum(
        score_local_by_angle.get(a, 5) * w
        for a, w in weights.items()
    )

    output = {
        "critiques_alignees": aligned,
        "scores_locaux": score_local_by_angle,
        "score_global_pondere": round(score_global, 2),
        "doublons_detectes": [
            {"idx_a": a, "idx_b": b,
             "fichier": aligned[a]["fichier"],
             "section": aligned[a]["section"]}
            for a, b in duplicates
        ],
        "statistiques": {
            "total_critiques": len(aligned),
            "par_angle": {
                a: sum(1 for c in aligned if c["angle"] == a)
                for a in (["architecte", "pragmatiste", "simulateur"]
                          + (["harnais"] if "harnais" in score_local_by_angle else []))
            },
            "par_gravite": {
                g: sum(1 for c in aligned if c["gravite"] == g)
                for g in ["CRITIQUE", "MAJEUR", "MINEUR"]
            },
        },
    }

    out_path = args.work_dir / "aligned_critiques.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    summary = args.work_dir / "align_summary.txt"
    lines = [
        f"Total critiques : {output['statistiques']['total_critiques']}",
        f"Score global pondéré : {output['score_global_pondere']}/10",
        f"Doublons inter-angles : {len(duplicates)}",
        "",
        "Par angle :",
        *[f"  {a}: {n}" for a, n in output["statistiques"]["par_angle"].items()],
        "",
        "Par gravité :",
        *[f"  {g}: {n}" for g, n in output["statistiques"]["par_gravite"].items()],
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": "OK", "output": str(out_path),
                      "stats": output["statistiques"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
