#!/usr/bin/env python3
"""h8_ablation.py — passe H8 d'ablation datée sur le fan-out hérité (archi §2.5).

Solde la dette de non-mesure de v3.6 : AVANT de greffer tout module frontière+, on
mesure enfin si chaque agent hérité (4 critics, Défenseur, Juge, Observateur) mérite
sa place. Pour chaque agent : rejoue le self-golden-set SANS lui (ablation = sortie
vidée) et calcule le **delta orienté** (data_model §5bis, décision D2).

Convention de signe (D2_garder_agent_herite, data_model §5bis) :
  candidate_score = score SANS l'agent (ablaté).
  gain_oriente    = baseline_score - candidate_score   (l'agent fait-il PERDRE si absent ?)
  garder l'agent SSI gain_oriente >= SEUIL_MIN  (sinon : candidat à simplification).
Jamais de comparaison de delta brut : seule `gain_oriente >= seuil` décide.

NE SUPPRIME AUCUN AGENT — produit seulement la recommandation datée dans
`_mode-plan-meta/h8_ablation_<date>.md` (+ un .json machine-lisible).

Usage : python h8_ablation.py [--date 2026-07-01]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _constants import SEUIL_MIN  # noqa: E402  (seuil source unique)
from self_eval_debate import discover_cases, build_report  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parent.parent
SELFEVAL_DIR = SKILL_ROOT / "evals" / "selfeval"
META_DIR = SKILL_ROOT / "_mode-plan-meta"

# Le fan-out hérité de v3.6 (spec §0bis) — l'ordre = ordre du rapport.
HEREDITARY_AGENTS = [
    "critic-architecte",
    "critic-pragmatiste",
    "critic-simulateur",
    "critic-harnais",
    "defenseur",
    "juge",
    "observateur",
]


def score_capability(ablate: str | None) -> float:
    cases = discover_cases(SELFEVAL_DIR, None)
    report = build_report(cases, "replay", "capability", None, ablate=ablate)
    return report["score_capability"]


def d2_decision(baseline: float, candidate: float) -> dict:
    gain_oriente = round(baseline - candidate, 4)
    keep = gain_oriente >= SEUIL_MIN
    if keep:
        decision, raison = "garder", f"l'ablation coûte {gain_oriente} >= {SEUIL_MIN} : agent porteur"
    elif gain_oriente == 0.0:
        decision, raison = "non_exerce", (
            "l'ablation ne coûte rien : agent NON exercé par le corpus actuel "
            "-> étendre le corpus OU candidat à simplification (PAS de suppression)"
        )
    else:
        decision, raison = "simplifier", (
            f"l'ablation ne coûte que {gain_oriente} < {SEUIL_MIN} : contribution trop faible, "
            "candidat à simplification"
        )
    return {
        "decision_type": "D2_garder_agent_herite",
        "baseline_score": baseline,
        "candidate_score": candidate,
        "gain_oriente": gain_oriente,
        "seuil_min": SEUIL_MIN,
        "decision": decision,
        "raison": raison,
    }


def render_md(date_str: str, baseline: float, rows: list[dict]) -> str:
    lines = [
        f"# Passe H8 — ablation du fan-out hérité — {date_str}",
        "",
        "> Généré par `scripts/h8_ablation.py` (archi §2.5, décision D2 data_model §5bis).",
        "> Rejoue le self-golden-set en ablatant chaque agent. **Aucun agent n'est supprimé** —",
        "> seule la recommandation datée est produite. `gain_oriente = baseline - score_sans` ;",
        f"> garder SSI `gain_oriente >= {SEUIL_MIN}`.",
        "",
        f"- **baseline (fan-out complet)** : score_capability = **{baseline}**",
        f"- **seuil d'adoption (source unique `_constants.SEUIL_MIN`)** : {SEUIL_MIN}",
        "",
        "| Agent hérité | score AVEC | score SANS | gain_oriente | décision |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        g = r["gate"]
        lines.append(
            f"| {r['agent']} | {g['baseline_score']} | {g['candidate_score']} "
            f"| {g['gain_oriente']} | **{g['decision']}** |"
        )
    lines += [
        "",
        "## Lecture",
        "- **garder** : l'ablation fait chuter le score d'au moins le seuil → l'agent est porteur, on le garde tel quel.",
        "- **non_exerce** : l'ablation ne change rien car le corpus self-golden-set ne teste pas encore cet agent. "
        "Ce n'est PAS une preuve d'inutilité — c'est un trou de couverture. Action : écrire un cas golden qui l'exerce, "
        "PUIS re-mesurer. En attendant, ne rien supprimer.",
        "- **simplifier** : l'ablation coûte moins que le seuil → contribution faible, candidat à simplification (à confirmer sur un corpus élargi).",
        "",
        "## Détail D2 par agent",
        "```json",
        json.dumps([r["gate"] | {"agent": r["agent"]} for r in rows], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Garde-fou",
        "Cette passe **mesure**, elle ne **modifie** rien. Toute simplification effective d'un agent "
        "passe par une décision séparée (skill-auto-improver / revue humaine), gatée sur ce même seuil "
        "et sur un corpus qui exerce réellement l'agent.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="passe H8 d'ablation (archi §2.5)")
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="date du rapport (défaut: aujourd'hui)")
    ap.add_argument("--out-dir", default=str(META_DIR))
    args = ap.parse_args()

    baseline = score_capability(None)
    rows = []
    for agent in HEREDITARY_AGENTS:
        candidate = score_capability(agent)
        rows.append({"agent": agent, "gate": d2_decision(baseline, candidate)})

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"h8_ablation_{args.date}.md"
    json_path = out_dir / f"h8_ablation_{args.date}.json"
    md_path.write_text(render_md(args.date, baseline, rows), encoding="utf-8")
    json_path.write_text(
        json.dumps({"date": args.date, "baseline_score": baseline,
                    "seuil_min": SEUIL_MIN, "agents": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Résumé console
    print(json.dumps({"date": args.date, "baseline": baseline,
                      "decisions": {r["agent"]: r["gate"]["decision"] for r in rows}},
                     ensure_ascii=False, indent=2))
    print(f"[h8_ablation] baseline={baseline} ; rapport -> {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
