#!/usr/bin/env python3
"""best_of_n.py — module frontière+ V2 : générer N candidats, garder le meilleur.

Opt-in (`--bestofn=on`, OFF par défaut). N'est ADOPTÉ que s'il prouve un gain mesuré
de +0.03 de score capability sur le golden set (règle de fer, spec §4/§10bis, gate D1
data_model §5). En V1 seul le gate « à sec » existait ; ici on câble la génération réelle.

Le module scorer + best-of-N est déterministe. La VARIANCE (indispensable pour que
best-of-N paie) vient soit d'un pool de candidats (mode replay, CI/mécanisme), soit de
vrais agents rédacteurs (mode live, décision d'adoption).

Estimateur (honnête, même échantillons pour les deux) :
  baseline (OFF) = moyenne des scores des candidats (qualité attendue d'un tirage unique)
  candidate (ON) = max des scores (best-of-N)
  gain_oriente   = mean_cas(candidate) - mean_cas(baseline)   [normalisé /10, échelle 0-1]
Adopté ssi gain_oriente >= SEUIL_MIN.

Usage :
  python best_of_n.py --check                 # mécanisme : best-of-N choisit-il le max ? (CI)
  python best_of_n.py --measure --mode replay # baseline/candidate sur le pool -> gate
  python best_of_n.py --measure --mode live   # idem sur les candidats live/ (agents)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _normalize import norm          # noqa: E402  (source unique de normalisation)
from _constants import SEUIL_MIN     # noqa: E402  (seuil d'adoption unique)

SKILL_ROOT = Path(__file__).resolve().parent.parent
SELFEVAL_DIR = SKILL_ROOT / "evals" / "selfeval"

# --------------------------------------------------------------------------- #
#  Rubrique DÉTERMINISTE (0-10) d'une section §10bis (golden set / harnais).
#  Chaque critère = présence d'au moins un mot-clé (sur le texte normalisé).
#  Vérifiable, reproductible, PAS un juge LLM libre.
# --------------------------------------------------------------------------- #
RUBRIC = [
    (2, "signal_de_succes", ["golden set", "signal de succes", "jeu de test"]),
    (2, "verifieur_distinct", ["verifieur", "verification", "verifie"]),
    (2, "rejouable", ["rejouable", "replay", "rejoue", "chaque changement", "re-run"]),
    (2, "assertion_binaire", ["binaire", "pass/fail", "vrai/faux", "assertion"]),
    (1, "anti_gaming", ["gamable", "gaming", "anti-gaming"]),
    (1, "exemple_concret", ["exemple", "payload", "par ex", "e.g"]),
]
RUBRIC_MAX = sum(pts for pts, _, _ in RUBRIC)  # 10


def score_candidate(text: str) -> int:
    """Note 0-10 déterministe d'un candidat via la rubrique."""
    n = norm(text)
    total = 0
    for pts, _key, keywords in RUBRIC:
        if any(norm(kw) in n for kw in keywords):
            total += pts
    return total


def score_breakdown(text: str) -> dict:
    n = norm(text)
    return {key: (pts if any(norm(kw) in n for kw in keywords) else 0)
            for pts, key, keywords in RUBRIC}


def best_of_n(candidates: list[tuple[str, str]]) -> dict:
    """candidates = [(name, text)]. Retourne le meilleur + tous les scores."""
    scored = [{"name": name, "score": score_candidate(text)} for name, text in candidates]
    best = max(scored, key=lambda c: c["score"])
    return {"best": best, "scored": scored}


# --------------------------------------------------------------------------- #
#  Chargement des cas gradués
# --------------------------------------------------------------------------- #
def _parse_json(text: str):
    return json.loads(text)


def discover_bn_cases(root: Path) -> list[Path]:
    out = []
    for d in sorted(root.iterdir()):
        exp = d / "expected.json"
        if d.is_dir() and exp.is_file():
            try:
                if _parse_json(exp.read_text(encoding="utf-8")).get("graded_by") == "best_of_n":
                    out.append(d)
            except json.JSONDecodeError:
                continue
    return out


def load_candidates(case_dir: Path, mode: str) -> list[tuple[str, str]]:
    sub = "live" if mode == "live" else "candidates"
    cdir = case_dir / sub
    if not cdir.is_dir():
        return []
    return [(f.stem, f.read_text(encoding="utf-8")) for f in sorted(cdir.glob("*.md"))]


# --------------------------------------------------------------------------- #
#  Modes
# --------------------------------------------------------------------------- #
def run_check(root: Path) -> dict:
    """Mécanisme (CI) : best-of-N choisit-il bien le candidat au plus haut score
    rubrique, égal à `best_candidate` déclaré dans expected.json ?"""
    results = []
    for case_dir in discover_bn_cases(root):
        expected = _parse_json((case_dir / "expected.json").read_text(encoding="utf-8"))
        cands = load_candidates(case_dir, "replay")
        if not cands:
            results.append({"case": case_dir.name, "ok": False, "raison": "aucun candidat (pool)"})
            continue
        res = best_of_n(cands)
        picked = res["best"]["name"]
        expect = expected.get("best_candidate")
        # OK si le candidat choisi a bien le score max ET correspond au best attendu.
        max_score = res["best"]["score"]
        ties = [c["name"] for c in res["scored"] if c["score"] == max_score]
        ok = (picked == expect) or (expect in ties)
        results.append({"case": case_dir.name, "picked": picked, "expected": expect,
                        "scores": {c["name"]: c["score"] for c in res["scored"]}, "ok": ok})
    green = bool(results) and all(r["ok"] for r in results)
    return {"mode": "check", "green": green, "results": results}


def run_measure(root: Path, mode: str) -> dict:
    """baseline (moyenne) vs candidate (best-of-N max) par cas, agrégé -> gate D1."""
    per_case = []
    for case_dir in discover_bn_cases(root):
        cands = load_candidates(case_dir, mode)
        if len(cands) < 2:
            per_case.append({"case": case_dir.name, "skipped": True,
                             "raison": f"<2 candidats en mode {mode} ({len(cands)})"})
            continue
        scored = [score_candidate(t) for _, t in cands]
        baseline = sum(scored) / len(scored)   # OFF ≈ tirage unique attendu
        candidate = max(scored)                # ON  = best-of-N
        per_case.append({
            "case": case_dir.name, "n": len(cands),
            "scores": scored, "baseline": round(baseline, 3), "candidate": candidate,
            "gain": round((candidate - baseline) / RUBRIC_MAX, 4),
        })
    graded = [c for c in per_case if not c.get("skipped")]
    if not graded:
        return {"mode": mode, "error": "aucun cas mesurable", "per_case": per_case}
    baseline_score = round(sum(c["baseline"] for c in graded) / len(graded) / RUBRIC_MAX, 4)
    candidate_score = round(sum(c["candidate"] for c in graded) / len(graded) / RUBRIC_MAX, 4)
    gain_oriente = round(candidate_score - baseline_score, 4)
    return {
        "mode": mode, "n_cas": len(graded),
        "baseline_score": baseline_score, "candidate_score": candidate_score,
        "gain_oriente": gain_oriente, "per_case": per_case,
    }


def build_gate(replay: dict, live: dict | None) -> dict:
    """adoption_gate.json (D1). Décision = mesure LIVE si dispo, sinon replay (illustratif)."""
    decision_source = "live" if (live and "gain_oriente" in live) else "replay"
    m = live if decision_source == "live" else replay
    gain = m["gain_oriente"]
    enabled = gain >= SEUIL_MIN
    return {
        "decision_type": "D1_activer_module",
        "objet": "best_of_n",
        "baseline_score": m["baseline_score"],
        "candidate_score": m["candidate_score"],
        "gain_oriente": gain,
        "seuil_min": SEUIL_MIN,
        "decision": "activer" if enabled else "rejeter",
        "best_of_n_enabled": enabled,
        "raison": (f"gain_oriente {gain} {'>=' if enabled else '<'} {SEUIL_MIN} "
                   f"(mesure {decision_source})"),
        "decision_source": decision_source,
        "note_integrite": ("La décision suit la mesure LIVE (vraie variance de génération). "
                           "La mesure REPLAY (pool d'auteur) est illustrative du mécanisme, "
                           "pas une preuve d'adoption."),
        "mesures": {"replay": replay, "live": live},
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="best-of-N (V2, opt-in)")
    ap.add_argument("--bestofn", choices=["on", "off"], default="off",
                    help="active le module (OFF par défaut = comportement v4.1 strict)")
    ap.add_argument("--check", action="store_true", help="mécanisme : best-of-N choisit le max (CI)")
    ap.add_argument("--measure", action="store_true", help="mesure baseline/candidate -> gate")
    ap.add_argument("--mode", choices=["replay", "live"], default="replay")
    ap.add_argument("--dir", default=str(SELFEVAL_DIR))
    ap.add_argument("--out", default=str(SKILL_ROOT / "_mode-plan-meta" / "adoption_gate.json"))
    ap.add_argument("root", nargs="?", default=None,
                    help="racine des cas (positionnel, ex. fixture run_evals) ; sinon --dir")
    args = ap.parse_args()
    root = Path(args.root) if args.root else Path(args.dir)

    if args.check:
        rep = run_check(root)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"[best_of_n] check green={rep['green']}", file=sys.stderr)
        return 0 if rep["green"] else 1

    if args.measure:
        if args.bestofn != "on":
            print(json.dumps({"skipped": "best-of-N OFF (--bestofn=on pour mesurer)"},
                             ensure_ascii=False))
            return 0
        replay = run_measure(root, "replay")
        live = run_measure(root, "live")
        live = live if "gain_oriente" in live else None
        gate = build_gate(replay, live)
        Path(args.out).write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(gate, ensure_ascii=False, indent=2))
        print(f"[best_of_n] best_of_n_enabled={gate['best_of_n_enabled']} "
              f"gain_oriente={gate['gain_oriente']} (source={gate['decision_source']}) -> {args.out}",
              file=sys.stderr)
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
